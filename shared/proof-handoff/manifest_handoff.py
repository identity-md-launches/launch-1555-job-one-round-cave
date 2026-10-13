#!/usr/bin/env python3
"""Bind two verified HANDOFF archives to Line 1's exact proof-bundle manifest."""
import argparse
import hashlib
import importlib.util
import io
import sys
import zipfile
from pathlib import Path

import code_extension as extension
from workspace_io import read_workspace

HERE = Path(__file__).resolve().parent
BASE = extension.base
spec = importlib.util.spec_from_file_location(
    'shared_proof_bundle_manifest',
    HERE / 'vendor/proof-bundle-manifest/proof_bundle_manifest.py')
manifest_tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manifest_tool)


def inventory(account_archive, code_archive):
    """Verify before opening bounded ZIP payloads; recompute from frozen bytes."""
    verified = extension.inspect_bytes(account_archive, code_archive)
    snapshot, proof = extension.account_payloads(account_archive)
    with zipfile.ZipFile(io.BytesIO(code_archive)) as archive:
        code = archive.read(extension.CODE)
    manifest = manifest_tool.manifest(snapshot, proof, code)
    archives = []
    for name, data, limits in [('account', account_archive, BASE.LIMITS),
                               ('code', code_archive, extension.LIMITS)]:
        receipt = BASE.inspector.inspect_stream(io.BytesIO(data), limits)
        archives.append({
            'name': name, 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest(),
            'content_expectation': {
                'format': 'handoff-content-expectation-v1',
                'exact': True, 'files': receipt['files']},
        })
    result = {
        'schema': 'zto-proof-manifest-handoff/1', 'verified': True,
        'network_used': False, 'payloads_extracted_or_executed': False,
        'manifest': manifest, 'archives': archives,
        'limits': verified['limits'],
        'trust': 'Keep this inventory independently if you want to pin the intended '
                 'revision. A receipt delivered beside replaced archives does not '
                 'authenticate their sender or the supplied mainnet state root.',
    }
    extension.canonical(result)
    return result


def check(account_archive, code_archive, inventory_raw):
    """A validly rehashed but different evidence revision cannot match a pin."""
    expected = BASE.proof.rpc.strict_json(extension.bounded(inventory_raw))
    actual = inventory(account_archive, code_archive)
    # Canonical bytes distinguish bool/int and other JSON type substitutions.
    if extension.canonical(expected) != extension.canonical(actual):
        raise ValueError('inventory differs from recomputed archive evidence')
    return {'schema': 'zto-proof-manifest-handoff-check/1', 'verified': True,
            'inventory_sha256': hashlib.sha256(inventory_raw).hexdigest(),
            'account_archive_sha256': actual['archives'][0]['sha256'],
            'code_archive_sha256': actual['archives'][1]['sha256'],
            'block_number': actual['manifest']['block_number'],
            'network_used': False, 'payloads_extracted_or_executed': False,
            'trust': actual['trust'], 'limits': actual['limits']}


def demo():
    account = read_workspace(str((HERE / 'examples/zto-proof.zip').relative_to(Path.cwd())))
    code = read_workspace(str((HERE / 'examples/zto-code-extension.zip').relative_to(Path.cwd())))
    result = inventory(account, code)
    check(account, code, extension.canonical(result))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('demo')
    for command in ('inventory', 'check'):
        child = sub.add_parser(command)
        child.add_argument('account_archive')
        child.add_argument('code_archive')
        if command == 'check':
            child.add_argument('inventory')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            result = demo()
        else:
            account = read_workspace(args.account_archive)
            code = read_workspace(args.code_archive)
            result = (inventory(account, code) if args.command == 'inventory' else
                      check(account, code, read_workspace(args.inventory)))
        sys.stdout.write(extension.canonical(result).decode('ascii'))
        return 0
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, UnicodeError,
            RecursionError, OverflowError, zipfile.BadZipFile, EOFError):
        print('manifest-handoff: invalid or changed evidence; no result emitted', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
