#!/usr/bin/env python3
"""Make a compact, offline manifest for a ZTO snapshot, account proof and code proof."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
sys.path.insert(0, str(TOOLS / 'code-proof-check'))
try:
    import code_proof_check as code
finally:
    sys.path.pop(0)

SCHEMA = 'pinned-zto-proof-bundle-manifest/1'
DEMO_SNAPSHOT = TOOLS / 'account-proof-check' / 'live-zto.json'
DEMO_PROOF = TOOLS / 'account-proof-check' / 'live-proof.json'
DEMO_CODE = TOOLS / 'code-proof-check' / 'live-code.json'


def _loaded(path):
    """Use the ancestor's bounded, workspace-confined byte reader."""
    raw, value = code.load(path)
    return raw, value


def _item(name, raw):
    return {'name': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def manifest(snapshot_path, account_proof_path, code_bundle_path):
    """Verify all links, then describe the exact three supplied byte streams."""
    snapshot_raw, _ = _loaded(snapshot_path)
    proof_raw, _ = _loaded(account_proof_path)
    code_raw, bundle = _loaded(code_bundle_path)
    verified = code.verify(snapshot_path, account_proof_path, bundle)
    # `verify` binds the proof bytes to the bundle. Bind the other two byte files
    # explicitly here so the manifest remains useful when passed between workers.
    if verified['account_proof_sha256'] != hashlib.sha256(proof_raw).hexdigest():
        raise ValueError('account proof changed while building manifest')
    return {
        'schema': SCHEMA,
        'verified': True,
        'network_used': False,
        'token': verified['token'],
        'block_number': verified['block_number'],
        'block_hash': verified['block_hash'],
        'state_root': verified['state_root'],
        'runtime_code_keccak256': verified['proved_code_hash'],
        'runtime_code_sha256': verified['bytecode_sha256'],
        'runtime_code_bytes': verified['bytecode_bytes'],
        'files': [
            _item('snapshot', snapshot_raw),
            _item('account_proof', proof_raw),
            _item('code_bundle', code_raw),
        ],
        'reported_provenance': verified['reported_provenance'],
        'evidence_limits': (
            'This manifest only summarizes three exact local byte streams after the '
            'ancestor code-proof verifier checks their relationships. It does not add '
            'a trusted mainnet anchor, consensus or finality verification, source-code '
            'equivalence, proxy resolution, storage proof, balances, supply, or current state.'),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('demo', help='offline manifest for retained real ZTO evidence')
    check = sub.add_parser('check', help='offline manifest for three evidence files')
    check.add_argument('snapshot')
    check.add_argument('account_proof')
    check.add_argument('code_bundle')
    args = parser.parse_args()
    try:
        if args.command == 'demo':
            result = manifest(DEMO_SNAPSHOT, DEMO_PROOF, DEMO_CODE)
        else:
            result = manifest(args.snapshot, args.account_proof, args.code_bundle)
        output = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n'
        if len(output.encode('utf-8')) > code.MAX_FILE:
            raise ValueError('output exceeds bound')
    except (ValueError, TypeError, KeyError, OSError, RuntimeError, RecursionError):
        print('proof-bundle-manifest: invalid evidence; no result emitted', file=sys.stderr)
        return 1
    sys.stdout.write(output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
