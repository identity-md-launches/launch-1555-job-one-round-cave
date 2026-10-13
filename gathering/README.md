# Gathering 21

[REPORT.md](REPORT.md) covers the four lines, the duplicate-key flaw found in
Line 1's original offline reader, and finite real Ethereum trials. No line
folders were changed. [COINS.md](COINS.md) says none.

The new [proof manifest handoff](../shared/proof-handoff/README.md) joins
Line 1's exact evidence inventory to Line 2's content contracts:

```sh
python3 -B shared/proof-handoff/manifest_handoff.py demo
```

All 64 line suites (**901 tests**) and 65 offline line trials passed. The
shared proof kit passed **28 tests**, including seven new integration checks.
Its copied-folder demo and both native content-contract checks also passed.
Receipts are under `checks/round-21/`.

`python3 -B gathering/check_round21.py` repeats the line suites and 61 demos
in a scratch mirror. `try_round21.py` adds four offline commands, four finite
public-read trials and the duplicate-key regression. It does not poll.
`python3 -B gathering/check_round21_deliverable.py` verifies image bytes,
record shape, source preservation, scope, provenance and gallery coverage.

**Three Kept Together** adds a charcoal loop around red ochre, yellow ochre
and chalk pebbles to vacant lower rock. The installed image tool made the
pigment insert; its white backdrop was omitted during composition. The named
output is `artifacts/gathering/wall-v22.png`; `wall.png` is identical.
Both are **1254×1254 RGB PNGs**. `dist/gathering/21.json` binds the actual PNG
digest; `21.jpg` is a **512×512 baseline JPEG**, 70,592 bytes.

Only **4,729 pixels** changed, all inside `(480,1145), 215×65`. All ancestral
paintings, Pepe, rock and framing elsewhere are pixel-identical. Both Pepe
hands retain five digits: four fingers and a thumb. No new hands or text were
added. No known unmet visual requirement; inherited rock has a photographic
texture retained as required. Exact prompt and method are in
[IMAGE-PROMPT-21.md](IMAGE-PROMPT-21.md); review metadata is in
`checks/round-21/image-preservation.json`. Final PNG and JPEG were inspected.

The self-contained HTML/CSS [gallery](../dist/index.html) lists all **185
records**, by wall and newest first, using existing thumbnails and artifact
links. This is a later gathering; no new placeholder set is needed.
Runtime tools use the standard library, without installation.
