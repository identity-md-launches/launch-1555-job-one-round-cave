#!/usr/bin/env python3
"""Bounded offline nonce and native funding review of unsigned type-2 proposals."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'zto-eip1559-decoder'))
import tx_decode as D

MAX_PROPOSALS = 64
MAX_JSON_CHARS = 1024 * 1024
UINT256_MAX = 2**256 - 1
MAX_USABLE_NONCE = 2**64 - 2
SCHEMA = 'transaction-sequence/v1'
KEYS = {'schema', 'sameSenderAssertion', 'chainId', 'startingNonce', 'balanceWei', 'transactions'}


def decimal(text, name, maximum=UINT256_MAX):
    if (not isinstance(text, str) or len(text) > 78 or
            re.fullmatch(r'0|[1-9][0-9]*', text) is None):
        raise ValueError(name + ' must be canonical nonnegative decimal text')
    value = int(text)
    if value > maximum:
        raise ValueError(name + ' exceeds its integer limit')
    return value


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON member: ' + key)
        result[key] = value
    return result


def review_json(text):
    if not isinstance(text, str) or len(text) > MAX_JSON_CHARS:
        raise ValueError('input exceeds the 1 MiB character limit')
    try:
        doc = json.loads(text, object_pairs_hook=unique_object)
    except (json.JSONDecodeError, RecursionError) as error:
        raise ValueError('invalid JSON input') from error
    return review(doc)


def review(doc):
    """Retain original list order; reject malformed input, report diagnostic failures."""
    if not isinstance(doc, dict) or set(doc) != KEYS or doc['schema'] != SCHEMA:
        raise ValueError('expected exactly the transaction-sequence/v1 input fields')
    if doc['sameSenderAssertion'] is not True:
        raise ValueError('sameSenderAssertion must be true; unsigned bytes cannot identify a sender')
    chain = decimal(doc['chainId'], 'chainId')
    if chain == 0:
        raise ValueError('chainId must be positive')
    start = decimal(doc['startingNonce'], 'startingNonce', MAX_USABLE_NONCE)
    balance = decimal(doc['balanceWei'], 'balanceWei')
    proposals = doc['transactions']
    if not isinstance(proposals, list) or not 1 <= len(proposals) <= MAX_PROPOSALS:
        raise ValueError('transactions must contain 1 to 64 original unsigned envelopes')
    # Bound the aggregate even for callers bypassing JSON parsing.
    if any(not isinstance(p, str) for p in proposals) or sum(map(len, proposals)) > MAX_JSON_CHARS:
        raise ValueError('transaction texts must fit the 1 MiB aggregate limit')
    items, failures, groups = [], [], {}
    total = 0
    def fail(code, indices, **details):
        failures.append({'code': code, 'proposalIndices': indices, **details})
    for index, original in enumerate(proposals):
        try:
            tx = D.decode(original)
        except ValueError as error:
            raise ValueError(f'transactions[{index}]: {error}') from error
        for field in ('chainId', 'nonce', 'maxPriorityFeePerGas', 'maxFeePerGas', 'gasLimit', 'value'):
            if tx[field] > UINT256_MAX:
                raise ValueError(f'transactions[{index}].{field} exceeds uint256')
        raw = bytes.fromhex(original[2:] if original.startswith('0x') else original)
        fingerprint = hashlib.sha256(raw).hexdigest()
        nonce = tx['nonce']
        ceiling = tx['value'] + tx['gasLimit'] * tx['maxFeePerGas']
        total += ceiling
        groups.setdefault(nonce, []).append(index)
        items.append({'index': index, 'envelopeSha256': fingerprint,
                      'chainId': str(tx['chainId']), 'nonce': str(nonce), 'to': tx['to'],
                      'calldataSelector': tx['calldataSelector'], 'valueWei': str(tx['value']),
                      'gasLimit': str(tx['gasLimit']), 'maxFeePerGasWei': str(tx['maxFeePerGas']),
                      'maxPriorityFeePerGasWei': str(tx['maxPriorityFeePerGas']),
                      'valuePlusFeeCapCeilingWei': str(ceiling)})
        if tx['chainId'] != chain:
            fail('chain-mismatch', [index], actualChainId=str(tx['chainId']))
        if nonce > MAX_USABLE_NONCE:
            fail('nonce-out-of-range', [index], nonce=str(nonce))
        if nonce < start:
            fail('nonce-before-start', [index], nonce=str(nonce))
        if tx['maxPriorityFeePerGas'] > tx['maxFeePerGas']:
            fail('priority-fee-exceeds-cap', [index])
        expected = start + index
        if nonce != expected:
            fail('listed-order-nonce-mismatch', [index], expectedNonce=str(expected), actualNonce=str(nonce))
    duplicates = []
    for nonce, indices in sorted(groups.items()):
        if len(indices) > 1:
            same = len({items[i]['envelopeSha256'] for i in indices}) == 1
            duplicates.append({'nonce': str(nonce), 'proposalIndices': indices,
                               'identicalEnvelopeBytes': same})
            fail('duplicate-nonce', indices, nonce=str(nonce))
    gaps, cursor = [], start
    for nonce in sorted(groups):
        if nonce < start:
            continue
        if nonce > cursor:
            gaps.append({'fromNonce': str(cursor), 'toNonceInclusive': str(nonce - 1),
                         'count': str(nonce - cursor)})
        cursor = nonce + 1
    if gaps:
        fail('missing-nonce-ranges', [], ranges=gaps)
    if total > balance:
        fail('insufficient-asserted-balance', [], shortfallWei=str(total - balance))
    return {'schema': 'transaction-sequence-report/v1',
            'assertedContext': {'sameSenderAssertion': True, 'chainId': str(chain),
                                'startingNonce': str(start), 'balanceWei': str(balance)},
            'proposalCount': len(items), 'proposals': items,
            'duplicateNonceGroups': duplicates, 'missingNonceRanges': gaps,
            'allListedProposalsCeilingWei': str(total),
            'coversAllListedCeilings': balance >= total,
            'shortfallWei': str(max(0, total - balance)),
            'surplusWei': str(max(0, balance - total)),
            'passesSequenceChecks': not failures, 'failures': failures,
            'limitations': [
                'Sender identity, starting nonce and available ETH balance are caller assertions, not chain evidence.',
                'Every listed ceiling is added, including duplicates and conflicting alternatives; no replacement is selected.',
                'Ceilings use value + gasLimit * maxFeePerGas, not simulated gas or actual cost; incoming funds are ignored.',
                'Nonce ranges describe gaps only through the highest listed nonce, not an unbounded future sequence.',
                'SHA-256 binds original unsigned bytes; it is not an Ethereum transaction hash or signature.',
                'These checks do not assess intrinsic gas, base fee, calldata safety, contract behavior, inclusion or safety to sign.',
            ]}


def demo():
    # Clearly synthetic proposals at the supplied real ZTO destination, never sent.
    txs = []
    for nonce in (0, 1):
        txs.append('0x02' + D.rlp_encode([1, nonce, 1_000_000_000, 2_000_000_000,
                   100_000, bytes.fromhex(D.ZTO[2:]), 0, bytes.fromhex('18160ddd'), []]).hex())
    return {'schema': SCHEMA, 'sameSenderAssertion': True, 'chainId': '1',
            'startingNonce': '0', 'balanceWei': '400000000000000', 'transactions': txs}


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--demo', action='store_true')
    source.add_argument('--stdin', action='store_true', help='read one strict JSON input object')
    args = parser.parse_args(argv)
    try:
        result = review(demo()) if args.demo else review_json(sys.stdin.read(MAX_JSON_CHARS + 1))
    except (ValueError, UnicodeError) as error:
        print('error: ' + str(error), file=sys.stderr)
        return 2
    if args.demo:
        result['demo'] = 'Synthetic ZTO totalSupply proposals and synthetic account context; never sent.'
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result['passesSequenceChecks'] else 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
