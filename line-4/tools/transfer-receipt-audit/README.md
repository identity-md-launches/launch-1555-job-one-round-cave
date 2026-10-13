# Transfer-receipt audit

Compare a saved bounded Ethereum ERC-20 Transfer window with the receipts of
its observed transactions. The tool revalidates the original raw logs, reads
each receipt once, checks enclosing block/transaction metadata, and compares
every Transfer from the selected token. Missing, extra and conflicting events
are retained separately. A null receipt is unavailable, never a matching empty
result. ZTO is the real demonstration token; IMD captures also work. Python's
standard library is the only dependency.

From the repository root, one command runs **offline** on retained real data:

```sh
python3 -B line-4/tools/transfer-receipt-audit/audit.py --demo
```

Tried **2026-10-13 at 11:31:23 UTC** against
`https://ethereum-rpc.publicnode.com`: mainnet chain ID matched; the receipt of
`0x0757a1c85a155860a1d17ef7ad80b8efb6529bc6266edbee40c56d99bf7e7553`
matched all **three ZTO transfers** in the retained **26177298–26177309**
window, at log indexes **642, 644 and 645**. Its **15 logs** include **12 other
events**, which are counted but not interpreted. The returned block number was
decoded to decimal and confirmed as **26177309**, transaction index **238**;
the returned block hash matches the capture. `observations.json` retains the
actual selected public receipt fields and **all receipt logs** in provider
order; unused receipt fields (gas, bloom, etc.) are omitted. `live-report.json`
retains the comparison and those observations. No receipt was fabricated.

Explicitly request another public read for a saved capture:

```sh
python3 -B line-4/tools/transfer-receipt-audit/audit.py --capture line-4/tools/transfer-crosscheck/publicnode.json --live
```

`--rpc https://eth.drpc.org` selects another public endpoint. The separate
transport allows only `eth_chainId` and `eth_getTransactionReceipt`, uses its
own User-Agent, disables proxy discovery and redirects, and leaves the older
tools' method permissions unchanged. There are at most **33 requests**: one
chain ID read and one per observed transaction, capped at **32 transactions**.
Invalid captures and excessive transaction counts fail before any network
read. Each response is capped at **1 MiB**, each receipt at **1,024 logs**, and
each log's data at **64 KiB**. Total retained evidence is capped at **16 MiB**.
No retry, polling or partial successful report occurs after an RPC failure.

Replay the saved observations against the capture:

```sh
python3 -B line-4/tools/transfer-receipt-audit/audit.py --capture line-4/tools/transfer-crosscheck/publicnode.json --evidence line-4/tools/transfer-receipt-audit/observations.json
```

For your own live report, save its `evidence` object as the observations file,
and keep the original capture. Both inputs use the existing bounded strict
workspace reader: regular files only, no symlink components or traversal,
strict UTF-8 JSON, duplicate/non-finite rejection, and at most 64 nesting levels.
Receipt replay validates all log metadata, topics, data, unique ordered log
indexes and explicit `removed=false`; a failed receipt cannot contain logs.
Input confinement requires POSIX no-follow support. Keep the sibling
`transfer-transaction-groups`, `transfer-crosscheck`, `erc20-transfer-window`,
`strict-rpc-json` and `bounded-capture-reader` folders with this tool.

Exit **0** means every planned receipt and transfer matches. Exit **1** means
conflicting, unavailable or `not_checked` observations. Empty captures are
`not_checked`, because there is no transaction to look up. Exit **2** means
invalid input or a failed public read. Conflicts take precedence over
unavailability in the overall status, while all per-transaction verdicts remain
visible. JSON goes to stdout; diagnostics go to stderr. The tool writes no
files and never reads a key, wallet, secret or environment variable, signs or
submits a transaction, deploys, pays or sends an external message.

This compares **provider-reported fields**, not cryptographic receipt proofs.
It can detect missing transfers *inside an already observed transaction*;
it cannot find a transaction omitted entirely from the capture, prove that an
empty window has no events, or establish consensus, finality, complete history,
balances, swaps, prices or activity in the supplied ZTO/IMD pool. Sequential
reads are not atomic. A changed receipt alone does not establish a reorganization.
Replay checks dated evidence, not current chain state.

All **33 focused tests passed**: socket-disabled real-data replay, extra/missing
events, changed amounts/senders, moved receipts, failed/null receipts, metadata
contradictions, strict types and resource limits, normalized hex, duplicate
capture delivery, multiple transactions, error precedence, exact public read
calls, bounded strict RPC envelopes, allowlist enforcement, pre-network capture
validation and CLI exit behavior. Mutations occur only in tests and are
explicitly synthetic. Run:

```sh
python3 -B line-4/tools/transfer-receipt-audit/test_audit.py
```
