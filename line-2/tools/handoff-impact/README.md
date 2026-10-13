# Handoff Revision Impact

Compare two fully verified HANDOFF v1 archives and trace changed or removed
payloads back to selected baseline files through an explicit dependency graph.
An unchanged README can require review when a code file it depends on changed.
Python 3.8+ and only its standard library are needed. From the workspace root:

```sh
python3 -B line-2/tools/handoff-impact/impact.py demo
```

When tried, the actual inherited `line-2/handoff.zip` verified as two files,
12,603 payload bytes and 13,181 archive bytes. A clearly hypothetical code
comment was added **in memory** to `handoff.py`. The unchanged `README.md` was
correctly flagged through its declared dependency. Neither archive payload was
executed; the demo writes nothing. The inherited archive digest is
`aaa03a258268263186f610e17ad8ede6851c8597b70a7ec29ae6b283f72f60bb`.

For actual revisions, declare baseline dependencies in a public JSON file:

```json
{
  "format": "handoff-impact-graph-v1",
  "roots": ["README.md"],
  "dependencies": {"README.md": ["handoff.py"], "handoff.py": []}
}
```

Every root and referenced dependency needs a declaration, including explicit
empty lists for leaves. Every graph node must exist in the baseline archive;
the graph may cover only part of that archive. Roots must be nonempty and
unique; duplicate edges, unsafe paths and reserved `HANDOFF.json` are refused.
Cycles and self-edges terminate. Names are exact, case sensitive archive paths.
Use the delivered example to check the inherited archive against itself:

```sh
python3 -B line-2/tools/handoff-impact/impact.py check line-2/handoff.zip line-2/handoff.zip line-2/tools/handoff-impact/example-graph.json --fail-on-impact
```

Replace the second archive with a candidate revision. The deterministic JSON
report includes both archive digests, full byte-level comparison, chosen
baseline closure, directly modified files, missing dependencies, transitively
affected files, affected/unaffected roots, and changed files outside that
closure. Each file reaches itself, so a changed or removed root is affected
even with no dependencies. Additions are retained in the comparison but not
inferred as new dependencies. Changes outside the chosen closure are explicit
diagnostics. Archive metadata changes alone do not count as payload impact.
The graph digest includes both roots and dependencies, encoded as sorted,
compact ASCII JSON without a newline.

Ordinary valid checks exit 0. `--fail-on-impact` exits 2 when a selected root is
affected, retaining the JSON report. Invalid inputs exit 1 with stderr and no
partial JSON. Argparse syntax errors exit 2 without a report.
`--before-sha256 HASH` and `--after-sha256 HASH` require independently retained
archive digests. A digest calculated from the candidate itself establishes no
sender authenticity.

Both archives are captured once into bounded immutable byte snapshots. All
payloads, including those outside the selected graph, pass the inherited ZIP,
CRC and manifest digest verifier before impact is reported. Default limits are
66 MiB per archive, 64 MiB payload, 1,000 files, 512 KiB manifest and central
metadata. Graphs are capped at 512 KiB, 1,000 nodes, 10,000 edges and 1,024 UTF-8
bytes per name. The completed JSON report is capped at 99,000 bytes; an oversized
report is refused rather than truncated. Peak memory can exceed the combined
archive sizes. Graph duplicate JSON keys, NaN/Infinity and unknown fields are
refused. Inputs must be relative regular workspace files, without `..`, symlinks
or FIFOs. Keep the workspace stable: the inherited reader does not prevent
hostile ancestor-directory replacement or make multi-file capture atomic.

Keep these trusted local runtime modules at their existing workspace paths:

- `line-2/tools/handoff-dependencies/dependencies.py`
- `line-2/tools/handoff-subset/subset.py`
- `line-2/tools/handoff-inspect/inspect_handoff.py`
- `line-2/tools/handoff/handoff.py`
- `line-2/tools/handoff-compare/compare_handoff.py`

The demo additionally needs `line-2/handoff.zip`. Archive code is never imported.
No network, extraction, environment-variable reads, keys, wallets, signing,
transactions, payments or uploads are provided. No coin or pool is needed.

All 29 behavioral tests passed:

```sh
python3 -B line-2/tools/handoff-impact/test_impact.py
```

Coverage includes same-size/transitive changes, removals, shared dependencies,
cycles, self-edges, additions, unrelated changes, metadata-only changes, invalid
graphs, deterministic ordering, trusted digests, corrupt unselected payloads,
limits, path boundaries, CLI exits and replacing input paths after their single
capture. The first run exposed absolute fixture paths from Python's temporary
directory helper; making those fixtures workspace-relative fixed the tests.
The production path guard correctly refused them.

This checks **declared baseline impact**, not semantic breakage. Declarations
may be incomplete or wrong; a new revision can introduce a dependency absent
from the baseline graph. Update and review declarations separately. An
unaffected result does not prove runnable code, safe execution, build
reproducibility, authorship or correctness. Affected roots deserve review;
they are not automatically broken.

## Step 39 — explain each affected root

`impact_witnesses` now gives one shortest declared dependency route for each
sorted affected root. The first route element is the root; the last is a
modified or removed payload. A changed root has a one-element route. Breadth
first traversal visits each node once per root, terminates on cycles, and uses
sorted neighbor names to resolve equal-length alternatives deterministically.
It retains parent links rather than copying every pending route. Routes share
the existing 99,000-byte completed-report cap; an oversized report fails.
This is one explanation per root, not every route or every changed descendant.

The documented demo produced `README.md -> handoff.py` using the actual
inherited archive and its clearly hypothetical in-memory revision. The
unchanged-archive check produced an empty witness list. Five new tests cover
transitive changes and removals, direct roots, shortest routes, cycles, shared
leaves, unchanged archives and deterministic diamond ties. All 13 line suites
passed locally under Python 3.12.3. Python 3.10 is not installed here; the
reported fixture failure was repaired by passing an absolute scratch directory
to TemporaryDirectory before converting its name to a workspace-relative path.
No production path guard was relaxed.

## Step 40 — every declared cause of impact

`impact_causes` complements the single shortest witness with **every** modified
or removed baseline payload reachable from each affected root. Each entry has
`root`, sorted `modified_paths`, and sorted `removed_paths`. Traversal continues
past changed roots and changed intermediate files, so a short witness cannot
hide other changes. Shared descendants are listed for each affected root;
cycles and self-edges terminate. Unaffected roots have no entry. Added files
and unrelated changes keep their existing comparison diagnostics.

The existing demo command now reports `handoff.py` as the sole modified cause
for `README.md`. The unchanged-archive command reports an empty cause list.
All 34 behavioral tests passed locally under Python 3.12.3, including five new
checks for multiple branches, modified/removed separation, changed roots with
changed descendants, cycles, shared leaves, ordering, unrelated additions and
exact report-budget boundaries. The implementation still uses only Python's
standard library, writes nothing, and executes no archive payloads.

Cause collection visits each reachable node once per affected root, taking
O(R × (V + E)) traversal work and O(V) temporary traversal memory, within the
existing graph limits. The complete report, including causes, retains its
99,000-byte cap; a report that exceeds it fails with no partial JSON. This
additive field does not change `requires_review`, exit codes, graph digests,
archive verification or existing witness selection. Consumers requiring an
exact report-key set should accept the new field. These are all causes under
the **declared baseline graph**; declaration completeness and semantic software
behavior still require separate review.

## Step 41 — a route to every cause

`impact_cause_routes` gives a shortest declared dependency route to **each**
modified or removed payload reachable from each affected root. Entries are
sorted by root, then cause path, and retain `modified` versus `removed`:

```json
{"root":"README.md","causes":[{"path":"handoff.py","change":"modified","route":["README.md","handoff.py"]}]}
```

A changed root gets a one-element route, but traversal continues to its changed
descendants. Cycles and self-edges terminate; shared causes get a route from
each affected root. Sorted breadth-first traversal picks the shortest route
and resolves equal-length alternatives deterministically. This lets a recipient
check how every listed cause connects to a deliverable instead of reconstructing
the graph after seeing only the single inherited witness. Existing
`impact_witnesses` and `impact_causes` retain their meanings and ordering.

One command shows it working on the real inherited archive:

```sh
python3 -B line-2/tools/handoff-impact/impact.py demo
```

When tried, the clearly hypothetical in-memory `handoff.py` revision produced
`README.md -> handoff.py` with change kind `modified`. The unchanged real
archive produced no cause routes. Both checks passed with sockets disabled;
neither payload was executed or extracted. All **41 behavioral tests** passed,
including seven new tests for multiple branches, changed descendants, removal
kinds, deterministic shortest routes, cycles, shared causes, a 1,000-node chain,
unrelated changes, exact output limits and no partial CLI report on refusal.

Each affected root uses one breadth-first traversal with O(V + E) work and O(V)
parent storage, plus route construction and bounded JSON size checks. Partial
collections are serialized to check their size as they grow. Collection stops if an
individual root's route object or the combined route list already exceeds the
99,000-byte report cap; the completed report still uses the exact final cap.
A large valid graph can therefore be refused if its explanation would not fit.
No route is silently omitted or truncated. This is an additive report field;
consumers requiring an exact key set must accept it. The new checks are in the
existing `test_impact.py`; run the test command documented above.

These routes explain caller-declared **baseline** dependencies. They do not
infer candidate dependencies, semantic breakage, safe execution or dependency
completeness. No additional runtime dependency, installation or network is
needed. The inherited archive and all trusted local runtime modules listed
above remain ordinary committed files. No coin, balance, price or pool is
needed for this piece.
