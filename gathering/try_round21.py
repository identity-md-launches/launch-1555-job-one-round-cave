#!/usr/bin/env python3
"""Finite line CLI trials and an ambiguity regression; public reads only."""
import datetime
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'gathering/checks/round-21'
COMMANDS = [
    ('snapshot-reader', ['line-1/tools/snapshot-check/check_snapshot.py'],
     'line-1/tools/snapshot-check/example-head.json'),
    ('pinned-reader', ['line-1/tools/pinned-snapshot/pinned_snapshot.py', 'inspect'],
     'line-1/tools/pinned-snapshot/example-zto.json'),
    ('sequence-demo', ['line-3/tools/transaction-sequence/sequence.py', '--demo'], None),
    ('receipt-demo', ['line-4/tools/transfer-receipt-audit/audit.py', '--demo'], None),
    ('live-head', ['line-1/tools/rpc-snapshot/rpc_snapshot.py', '--rpc',
                   'https://eth.drpc.org'], None),
    ('live-block-audit', ['line-1/tools/block-audit/block_audit.py', 'demo', '--rpc',
                          'https://eth.drpc.org'], None),
    ('live-window', ['line-4/tools/erc20-transfer-window/transfer_window.py',
                      '--latest-window', '2', '--rpc', 'https://eth.drpc.org'], None),
    ('live-receipt', ['line-4/tools/transfer-receipt-audit/audit.py', '--capture',
                       'line-4/tools/transfer-crosscheck/publicnode.json', '--live',
                       '--rpc', 'https://eth.drpc.org'], None),
]


def run(name, args, raw=None):
    command = ['python3', '-B', *args]
    try:
        result = subprocess.run(command, cwd=ROOT, input=raw, capture_output=True,
                                text=True, timeout=50)
        record = {'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
    except subprocess.TimeoutExpired:
        record = {'exit': 124, 'stdout': '', 'stderr': '50-second trial timeout'}
    record.update(command=command, checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    encoded = json.dumps(record, indent=2) + '\n'
    if len(encoded.encode()) >= 100000:
        raise ValueError('receipt exceeds delivery bound')
    (OUT / (name + '.json')).write_text(encoded)
    print(name, record['exit'], flush=True)
    return record


def main():
    for name, args, source in COMMANDS:
        run(name, args, None if source is None else (ROOT / source).read_text())
    raw = (ROOT / 'line-1/tools/snapshot-check/example-head.json').read_text()
    # Duplicate capture metadata is ambiguous even when the last value is valid.
    duplicate = raw.replace('{', '{"captured_at":"ambiguous earlier value",', 1)
    result = run('duplicate-reader-regression',
                 ['line-1/tools/snapshot-check/check_snapshot.py'], duplicate)
    print('Duplicate-key input accepted by native reader:', result['exit'] == 0)


if __name__ == '__main__':
    main()
