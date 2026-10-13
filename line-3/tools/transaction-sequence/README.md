# Transaction sequence reader

Review 1–64 original unsigned EIP-1559 envelopes as an explicitly asserted
single-sender sequence. The tool preserves list order and fingerprints original
bytes, reports every chain mismatch, stale/out-of-range nonce, duplicate nonce,
ordering mismatch, missing nonce range and priority-fee/cap inconsistency, and
compares the sum of **all listed** native-value-plus-fee ceilings with asserted
available ETH. It never selects replacements or discounts conflicting proposals.

From the repository root, one offline command shows it working:

```sh
python3 -B line-3/tools/transaction-sequence/sequence.py --demo
```

The trial passed with two **synthetic** ZTO `totalSupply()` proposals at nonces
0 and 1. Their combined ceiling was exactly **400000000000000 wei**; the
synthetic balance covered it exactly. ZTO is the supplied real Ethereum token
address, but neither these envelopes nor the account context are live chain
observations. Nothing is signed or sent. Fifteen behavioral tests passed,
including a one-wei shortage, conflicting replacements, independent failures,
a huge nonce gap represented by one range, malformed/signed input and bounds.

## Review your own input

Pipe one JSON object to:

```sh
python3 -B line-3/tools/transaction-sequence/sequence.py --stdin
```

The object must have exactly these fields:

- `schema`: `"transaction-sequence/v1"`.
- `sameSenderAssertion`: literal `true`. You assert all envelopes belong to
  the same intended sender; unsigned envelopes cannot prove this.
- `chainId`: positive canonical decimal string, e.g. `"1"` for Ethereum.
- `startingNonce`: canonical decimal string for the first intended nonce,
  at most `18446744073709551614`. Supply the intended account's current
  frontier from context you trust; the tool does not infer latest/pending state.
- `balanceWei`: canonical decimal string for available native ETH, at most
  uint256. Supply the balance available to this whole sequence, accounting
  for any separate commitments yourself.
- `transactions`: a list of original unsigned type-2 hexadecimal envelopes,
  in the order you intend to use them. Each must contain exactly nine fields.

No default account, guessed sender, key or wallet input is used. JSON numbers
are not accepted for context amounts; decimal strings avoid rounding. Duplicate
JSON members and unknown fields are rejected. Each envelope is limited by the
inherited 128 KiB decoder; aggregate transaction text and stdin JSON each have a
1 MiB character bound, and there are at most 64 proposals. Gaps are inclusive
ranges through the highest listed nonce, never expanded into a list of nonces.

Exit status: **0** means these sequence diagnostics pass; **1** means a complete
report contains diagnostic failures; **2** means malformed or unsupported input.
Indices in reports are zero-based. `allListedProposalsCeilingWei` sums
`value + gasLimit * maxFeePerGas` even for duplicates or wrong-chain entries;
when sequence checks fail it is only a conservative total of the listed
proposals, not the cost of an executable sequence. All monetary arithmetic is
exact and may exceed uint256 in intermediate totals.

This is not simulation or safety to sign. Intrinsic gas, current base fee,
contract behavior, calldata safety and inclusion are not assessed; use the
existing `proposal-review` for supported per-envelope gas/fee diagnostics.
Incoming ETH, refunds, token balances and pending replacements are not inferred.
Fingerprints use SHA-256 of unsigned bytes, not Ethereum transaction hashes.

Python standard library only. Reuses the committed sibling
`../zto-eip1559-decoder/tx_decode.py`; keep both folders when copying this tool.
No network, installation or environment variable is needed. Tests:

```sh
python3 -B -m unittest discover -s line-3/tools/transaction-sequence -p 'test_*.py' -v
```

The nonce bound follows [EIP-2681](https://eips.ethereum.org/EIPS/eip-2681):
“Consider any transaction invalid, where the nonce exceeds or equals to
`2^64-1`.” This one bound does not imply the tool validates every Ethereum
protocol rule or a historical fork.
