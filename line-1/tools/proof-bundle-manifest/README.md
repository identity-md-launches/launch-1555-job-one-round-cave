# Proof bundle manifest

Make a compact, reproducible inventory for a portable ZTO observation: the
saved snapshot, its account proof, and the saved runtime-code response. Before
printing anything it invokes Line 1's offline code-proof verifier, then records
the exact byte count and SHA-256 of each of the three files. This lets a worker
compare a handed-off bundle before using it, without asking an RPC provider
again. It uses only Python's standard library and does not install anything.

From the repository root, run the retained offline demonstration:

```sh
python3 -B line-1/tools/proof-bundle-manifest/proof_bundle_manifest.py demo
```

The command printed a verified manifest for the retained real ZTO observation:
block `26182473`, code length `1287` bytes, and three exact file digests. The
demo opened no network connection. Exit 0 means the three files agree relative
to the supplied state root; exit 1 means invalid evidence and prints no partial
JSON report.

Run the regression checks with:

```sh
python3 -B -m unittest discover -s line-1/tools/proof-bundle-manifest -p 'test_*.py' -v
```

To inspect another compatible local bundle, use:

```sh
python3 -B line-1/tools/proof-bundle-manifest/proof_bundle_manifest.py check SNAPSHOT.json ACCOUNT-PROOF.json CODE-BUNDLE.json
```

All input reads use the ancestor verifier's bounded, workspace-confined regular
file reader and reject oversized or malformed JSON. This is an offline check:
it makes no network calls, executes no bytecode, signs nothing, and sends no
transaction. As with its ancestor, a self-consistent fabricated header/proof
can pass; this does not establish consensus, finality, contract safety, source
equivalence, proxy targets, balances, supply, or present-chain state.
