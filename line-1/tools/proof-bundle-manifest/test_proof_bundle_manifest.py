import copy
import io
import json
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

import proof_bundle_manifest as tool


class ManifestTests(unittest.TestCase):
    def test_retained_bundle_is_offline_and_bound(self):
        with patch.object(socket, 'socket', side_effect=AssertionError('offline')):
            result = tool.manifest(tool.DEMO_SNAPSHOT, tool.DEMO_PROOF, tool.DEMO_CODE)
        self.assertTrue(result['verified'])
        self.assertFalse(result['network_used'])
        self.assertEqual(result['token'], tool.code.ZTO)
        self.assertEqual(result['runtime_code_bytes'], 1287)
        self.assertEqual([entry['name'] for entry in result['files']],
                         ['snapshot', 'account_proof', 'code_bundle'])
        self.assertTrue(all(len(entry['sha256']) == 64 for entry in result['files']))

    def test_changed_code_bundle_is_rejected(self):
        bundle = tool._loaded(tool.DEMO_CODE)[1]
        changed = copy.deepcopy(bundle)
        changed['result'] = changed['result'][:-2] + '00'
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile('w', suffix='.json', dir=scratch, delete=False) as handle:
            json.dump(changed, handle)
            path = Path(handle.name)
        self.addCleanup(path.unlink)
        with self.assertRaises(ValueError):
            tool.manifest(tool.DEMO_SNAPSHOT, tool.DEMO_PROOF, path)

    def test_cli_emits_one_valid_report_without_network(self):
        with patch.object(socket, 'socket', side_effect=AssertionError('offline')), \
                patch.object(sys, 'argv', ['proof_bundle_manifest.py', 'demo']), \
                patch.object(sys, 'stdout', new_callable=io.StringIO) as output:
            self.assertEqual(tool.main(), 0)
        self.assertTrue(json.loads(output.getvalue())['verified'])

    def test_cli_failure_does_not_emit_partial_json(self):
        with patch.object(sys, 'argv', ['proof_bundle_manifest.py', 'demo']), \
                patch.object(tool, 'manifest', side_effect=ValueError('bad')), \
                patch.object(sys, 'stdout', new_callable=io.StringIO) as output, \
                patch.object(sys, 'stderr', new_callable=io.StringIO) as error:
            self.assertEqual(tool.main(), 1)
        self.assertEqual(output.getvalue(), '')
        self.assertIn('no result emitted', error.getvalue())


if __name__ == '__main__':
    unittest.main()
