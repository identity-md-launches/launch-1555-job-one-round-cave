"""Behavioral checks for exact evidence pins across two real ZTO archives."""
import copy
import hashlib
import io
import json
from pathlib import Path
import socket
import unittest
from unittest.mock import patch

import manifest_handoff as tool


class ManifestHandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        here = Path(tool.__file__).resolve().parent / 'examples'
        cls.account = (here / 'zto-proof.zip').read_bytes()
        cls.code = (here / 'zto-code-extension.zip').read_bytes()
        cls.inventory = tool.inventory(cls.account, cls.code)
        cls.raw = tool.extension.canonical(cls.inventory)

    def test_real_evidence_without_network_or_extraction(self):
        with patch.object(socket, 'socket', side_effect=AssertionError('network')), \
             patch.object(tool.zipfile.ZipFile, 'extract', side_effect=AssertionError('extract')), \
             patch.object(tool.zipfile.ZipFile, 'extractall', side_effect=AssertionError('extractall')):
            result = tool.check(self.account, self.code, self.raw)
        self.assertTrue(result['verified'])
        self.assertEqual(result['inventory_sha256'], hashlib.sha256(self.raw).hexdigest())
        self.assertFalse(result['network_used'])
        self.assertFalse(result['payloads_extracted_or_executed'])
        self.assertEqual(self.inventory['manifest']['runtime_code_bytes'], 1287)

    def test_valid_changed_revision_does_not_match_retained_pin(self):
        with tool.zipfile.ZipFile(io.BytesIO(self.code)) as archive:
            bundle = json.loads(archive.read(tool.extension.CODE))
        bundle['captured_at'] = '2026-10-13T10:41:48Z'
        changed = tool.extension.build(self.account, tool.extension.canonical(bundle))
        self.assertTrue(tool.inventory(self.account, changed)['verified'])
        with self.assertRaises(ValueError):
            tool.check(self.account, changed, self.raw)

    def test_false_file_digest_or_size_rejected(self):
        for field, value in [('sha256', 'f' * 64), ('bytes', 1)]:
            changed = copy.deepcopy(self.inventory)
            changed['manifest']['files'][0][field] = value
            with self.assertRaises(ValueError):
                tool.check(self.account, self.code, tool.extension.canonical(changed))

    def test_content_contract_covers_every_archive_payload(self):
        for data, row in zip((self.account, self.code), self.inventory['archives']):
            contract = row['content_expectation']
            self.assertTrue(contract['exact'])
            with tool.zipfile.ZipFile(io.BytesIO(data)) as archive:
                self.assertEqual({item['path'] for item in contract['files']},
                                 set(archive.namelist()) - {'HANDOFF.json'})
                for item in contract['files']:
                    raw = archive.read(item['path'])
                    self.assertEqual(item['bytes'], len(raw))
                    self.assertEqual(item['sha256'], hashlib.sha256(raw).hexdigest())

    def test_duplicate_and_nonfinite_json_rejected(self):
        for raw in (b'{"verified":true,"verified":false}', b'{"verified":NaN}'):
            with self.assertRaises(ValueError):
                tool.check(self.account, self.code, raw)

    def test_json_type_substitution_rejected(self):
        changed = copy.deepcopy(self.inventory)
        changed['verified'] = 1
        with self.assertRaises(ValueError):
            tool.check(self.account, self.code, tool.extension.canonical(changed))

    def test_cli_failure_has_no_partial_result(self):
        with patch.object(tool, 'read_workspace', side_effect=ValueError('invalid')), \
             patch.object(tool.sys, 'stdout', new_callable=io.StringIO) as output, \
             patch.object(tool.sys, 'stderr', new_callable=io.StringIO):
            self.assertEqual(tool.main(['inventory', 'bad.zip', 'bad.zip']), 1)
        self.assertEqual(output.getvalue(), '')


if __name__ == '__main__':
    unittest.main()
