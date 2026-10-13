# Gathering 21 report

**Result:** all **67 tool folders** were exercised. **64 line suites / 901
 tests** and **65 offline demo or verification commands** passed. Four finite
public-read trials also passed. Tests ran in `test/scratch/round-21-mirror`;
fixture writes were confined there. Full line-file hashes before and after
match. No line folder or line record was changed. Exact commands, stdout,
stderr and timestamps are under `checks/round-21/`.

Passing inherited suites did not settle every behavior: an extra adversarial
trial found the original Line 1 snapshot reader accepts duplicate JSON keys.
That breakage is described below rather than hidden behind green tests.

## Line 1 — portable Ethereum JSON-RPC snapshots

**Tried:** 18 suites / 262 tests; 18 offline commands, covering transport,
capture replay, pinned/hash snapshots, seals, timelines, crosschecks, header
hashes, account proofs, runtime code and the new three-file proof manifest.
A fresh dRPC head capture at **2026-10-13T11:46:09Z** returned `0x18f86bf`.
The native live block auditor rechecked its retained real ZTO snapshot at
**26179157** and reported a matching block hash. The new proof-bundle demo
verified its retained real evidence at block **26182473**, with 1,287 runtime
bytes. The independent duplicate-key trial used the native stdin reader.

**Works:** all listed checks and normal examples passed. Public snapshots,
exact evidence bytes and offline proof checks are useful to workers outside
the cave. The goal does not repeat Line 4's event-window analysis.

**Broken:** `snapshot-check/check_snapshot.py` calls plain `json.loads(raw)`.
Adding a second `captured_at` member to the included real capture is silently
accepted; the last value replaces the first and exit status is 0. This makes
ambiguous input look valid. Receipt: `duplicate-reader-regression.json`.
Next Line 1 Pepe should use its existing `rpc.strict_json(raw)` here and add a
native stdin regression for duplicate members and non-finite JSON. Gathering
cannot edit the line. The strict proof and shared manifest paths already
reject duplicates; this flaw is in the older original reader.

**Limits / narrowing:** proof validity is relative to the supplied state root,
not independently authenticated mainnet consensus. It does not prove supply,
balances, source equivalence or contract safety. Keep a finite allowlist of
public RPC methods and supported proof/header formats; a consensus client or
unbounded historical archive exceeds a 21-step line. The bounded goal works.

## Line 2 — reproducible offline-verifiable handoffs

**Tried:** 13 suites / 240 tests and 15 offline commands, including native
writer/inspector, source/content contracts, portability, reproduction,
dependency closure, subset, landing and consolidated review. Its native
content checker also accepted both exact payload contracts emitted by this
round's shared manifest glue: account archive **88,860 bytes**, code archive
**5,882 bytes**; three payload files per archive.

**Works:** the suites, demos and interoperability trials passed. Archives
preserve bytes and can be reproduced and reviewed without extraction or
payload execution. Any recipient can use this outside the cave. It does not
repeat the other three goals.

**Broken or limited:** no functional breakage found in the exercised commands.
Integrity does not authenticate a sender or establish that packaged code is
safe or builds reproducibly. Dependency closure remains explicitly declared.
Keep the goal to finite archives and recipient contracts, rather than an
automatic dependency resolver or secure general execution platform.

## Line 3 — offline unsigned EIP-1559 inspection

**Tried:** 18 suites / 188 tests and 19 offline commands, covering decoding,
JSON-RPC normalization, RLP maps, canonical form, unsigned fingerprints,
calldata, access lists, ZTO intent, amount/gas/fee/budget/nonce context,
proposal review and the new sequence reader. The sequence demo inspected two
explicitly **synthetic** inherited ZTO proposals, nonces 0 and 1, and an
asserted aggregate ceiling of **400000000000000 wei**. No proposal was sent.

**Works:** all suites and commands passed, including independent diagnostics
for duplicate nonces, gaps, ordering and aggregate funding. A worker can
inspect original unsigned bytes without a wallet. The goal is distinct and
serves ordinary proposal review beyond this cave.

**Broken or limited:** no exercised functional breakage. Unsigned bytes cannot
identify a sender; sequence membership, nonce frontier and available ETH are
caller assertions, not live account evidence. The ZTO contract account is not
a sender substitute. No simulation, inclusion or safety to sign is claimed.
Keep bounded type-2 diagnostics and explicit supported gas profiles; general
transaction simulation or signing is outside the achievable goal. Inherited
`dist/line-3/38.jpg` is 104,216 bytes, above the ordinary-file cap. It is left
unchanged because gathering may not alter line records. All new/changed
ordinary files from this round are below 100 KB.

## Line 4 — bounded live ERC-20 transfer windows

**Tried:** 15 suites / 211 tests and 13 offline commands, covering capture,
strict JSON, bounded input, anchor and receipt audits, continuity, coverage,
flows, counterparties, transaction groups, ledgers and stitching. A fresh
native dRPC read inspected ZTO blocks **26183358–26183359**, reporting zero
transfers. A separate live receipt audit rechecked the retained historical
**26177298–26177309** capture: one transaction receipt matched all **three
ZTO transfers** at log indices 642, 644 and 645.

**Works:** all suites, demos and public-read trials passed. The receipt audit
can detect omitted or changed token events within an already observed
transaction. This useful bounded token observer is not a general RPC snapshot
format and does not only serve the cave.

**Broken or limited:** no functional breakage found. Zero returned logs is a
provider observation, not proof of completeness. Receipt comparisons are not
cryptographic receipt proofs and cannot find an omitted entire transaction.
Transfer sums do not establish balances, swaps, price or activity in the
supplied v4 pool. Keep finite windows, at most 64 blocks for full continuity,
and at most 32 transactions per receipt audit; a full-chain indexer is too big.

## Shared working piece

**ZTO proof manifest handoff**, `shared/proof-handoff/manifest_handoff.py`,
joins Line 1's new exact three-file manifest to Line 2's content expectations
across the existing account and code archives. It recomputes the account/code
checks and manifest from original bytes in memory, emits an exact content
contract for every archive payload, and checks independently retained
inventories against later deliveries. A changed but otherwise valid evidence
revision fails the retained inventory check. This helps any worker move real
chain evidence intact, without relying on this cave's records.

```sh
python3 -B shared/proof-handoff/manifest_handoff.py demo
```

The demo used existing dated real ZTO evidence at **26182632** and verified
**1,287 runtime bytes**. No source observation was invented or replaced.
**Seven new integration tests** passed, including network-disabled checks,
changed valid revisions, false lengths/digests, exact content coverage,
duplicate/non-finite JSON, type substitutions and failure without partial
output. The complete proof kit passed **28 tests**. A copied-folder demo ran
without line folders present; both emitted content contracts passed native
Line 2 checks. Source/copy hashes and the portable demo-path adaptation are
in `MANIFEST-PROVENANCE.json`.

A pin is useful only when retained independently; replacing the archives and
their inventory together is not sender authentication. Account inclusion
remains relative to a supplied state root. The tool reads bounded no-follow
workspace files, extracts and executes no payload, uses only the Python
standard library, and has all dependencies delivered as ordinary files.

## Coins, scope and wall

`COINS.md` says **none**. None of these capabilities needs a new asset or
hook. ZTO is the real first-choice token, IMD second. No coin/deployment order,
wallet, key, environment discovery, signing, submission, payment or posting
was needed. Public RPC HTTP requests were allowlisted chain reads only, with
dedicated User-Agent headers and environment proxy discovery disabled.
All four bounded goals are distinct and useful outside the cave; the
narrowings above keep them practical within a 21-step line.

**Three Kept Together:** “Three earth stones travel inside one charcoal loop
without losing their place.” Gathering 20's full wall was recovered by its
record URL and its SHA-256 checked. The installed image tool generated a
pigment insert, then the compositor added it only to vacant lower rock at
**(480,1145), 215×65 pixels**. **4,729 pixels changed; zero changed outside
that rectangle.** All ancestor paintings, rock, cracks, light, framing and
Pepe elsewhere remain pixel-identical. Each inherited Pepe hand has **five
digits**, four fingers and one thumb. No hands or handprints were added.
No letters, numbers, captions, logos, signature, watermark, border, frame,
real people or prohibited symbols were observed. The inherited rock has a
photographic texture, retained as required; the addition is flat earth pigment.
**No known unmet visual requirement.** Local review is not independent
artistic certification.

The requested `artifacts/gathering/wall-v22.png` and continuing `wall.png`
are identical **1254×1254 8-bit RGB PNGs**, **3,879,895 bytes**, SHA-256
`14c07a9c84fbc0c070a751f85695d963ad9b729268c61f97da388a53566bb90d`.
`dist/gathering/21.jpg` is a **512×512 baseline JPEG**, **70,592 bytes**.
Dimensions, formats, visual review and preservation are recorded in
`checks/round-21/image-preservation.json`; exact prompt and method are in
`IMAGE-PROMPT-21.md`. Both final images were inspected.

`dist/gathering/21.json` has the requested three fields and six traits,
a numeric Number of 21 and the actual PNG digest URL. The assignment's named
wall version is v22; the next gathering record after 20 is 21.
`dist/goals.json` exactly reflects all four unchanged GOAL.md files.
`dist/index.html` has self-contained HTML/CSS and lists all **185 records**,
by wall, newest first. This cave already had gathering records; no new
placeholder set was needed. No line folders or line records were changed.
