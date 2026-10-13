import copy
import json
import unittest
import sequence as S


def transaction(nonce=0, chain=1, value=0, cap=2_000_000_000, tip=1_000_000_000):
    return '0x02' + S.D.rlp_encode([chain, nonce, tip, cap, 100_000,
            bytes.fromhex(S.D.ZTO[2:]), value, bytes.fromhex('18160ddd'), []]).hex()


class SequenceTests(unittest.TestCase):
    def doc(self):
        return copy.deepcopy(S.demo())

    def codes(self, result):
        return {f['code'] for f in result['failures']}

    def test_exact_coverage_and_original_order(self):
        doc = self.doc(); before = copy.deepcopy(doc)
        r = S.review(doc)
        self.assertTrue(r['passesSequenceChecks'])
        self.assertEqual(r['allListedProposalsCeilingWei'], '400000000000000')
        self.assertEqual(r['surplusWei'], '0')
        self.assertEqual([p['nonce'] for p in r['proposals']], ['0', '1'])
        self.assertEqual(doc, before)

    def test_one_wei_short_with_value_included(self):
        doc = self.doc(); doc['transactions'][1] = transaction(1, value=1)
        r = S.review(doc)
        self.assertEqual(r['shortfallWei'], '1')
        self.assertIn('insufficient-asserted-balance', self.codes(r))

    def test_duplicates_not_selected_or_discounted(self):
        doc = self.doc(); doc['transactions'][1] = doc['transactions'][0]
        r = S.review(doc)
        self.assertTrue(r['duplicateNonceGroups'][0]['identicalEnvelopeBytes'])
        self.assertEqual(r['allListedProposalsCeilingWei'], '400000000000000')
        self.assertIn('duplicate-nonce', self.codes(r))
        doc['transactions'][1] = transaction(0, value=1)
        self.assertFalse(S.review(doc)['duplicateNonceGroups'][0]['identicalEnvelopeBytes'])

    def test_large_gap_has_one_range(self):
        doc = self.doc(); doc['transactions'][1] = transaction(S.MAX_USABLE_NONCE)
        r = S.review(doc)
        self.assertEqual(r['missingNonceRanges'], [{'fromNonce': '1',
                'toNonceInclusive': str(S.MAX_USABLE_NONCE-1), 'count': str(S.MAX_USABLE_NONCE-1)}])
        self.assertLess(len(json.dumps(r)), 6000)

    def test_reordered_is_not_silently_sorted(self):
        doc = self.doc(); doc['transactions'].reverse()
        r = S.review(doc)
        self.assertEqual([p['nonce'] for p in r['proposals']], ['1', '0'])
        self.assertEqual(r['missingNonceRanges'], [])
        self.assertEqual(len([f for f in r['failures'] if f['code']=='listed-order-nonce-mismatch']), 2)

    def test_asserted_nonzero_start(self):
        doc = self.doc(); doc['startingNonce'] = '12'
        doc['transactions'] = [transaction(12), transaction(13)]
        self.assertTrue(S.review(doc)['passesSequenceChecks'])
        doc['transactions'][0] = transaction(11)
        self.assertIn('nonce-before-start', self.codes(S.review(doc)))

    def test_independent_failures_retained(self):
        doc = self.doc(); doc['balanceWei']='0'
        doc['transactions'][1] = transaction(4, chain=2, cap=1, tip=2)
        self.assertTrue({'chain-mismatch', 'priority-fee-exceeds-cap',
                        'missing-nonce-ranges', 'insufficient-asserted-balance',
                        'listed-order-nonce-mismatch'} <= self.codes(S.review(doc)))

    def test_exhausted_nonce_fails_diagnostic(self):
        doc = self.doc(); doc['transactions'][0] = transaction(2**64-1)
        self.assertIn('nonce-out-of-range', self.codes(S.review(doc)))

    def test_signed_or_malformed_envelope_rejected(self):
        doc = self.doc()
        for malformed in ('0x02c0', '0x03', '0x 02', '0x02' + S.D.rlp_encode([1,0,1,2,21000,b'',0,b'',[],0,0,0]).hex()):
            doc['transactions'][0] = malformed
            with self.assertRaisesRegex(ValueError, r'transactions\[0\]'):
                S.review(doc)

    def test_context_strictness(self):
        for field, value in [('sameSenderAssertion', 1), ('sameSenderAssertion', False),
                             ('chainId', '0'), ('chainId', 1), ('startingNonce', '01'),
                             ('startingNonce', str(2**64-1)), ('balanceWei', '-1'),
                             ('balanceWei', str(2**256))]:
            doc = self.doc(); doc[field] = value
            with self.assertRaises(ValueError): S.review(doc)
        doc=self.doc(); doc['sender']='guessed'
        with self.assertRaises(ValueError): S.review(doc)

    def test_uint256_transaction_bound(self):
        doc=self.doc(); doc['transactions'][0]=transaction(value=2**256)
        with self.assertRaisesRegex(ValueError, 'uint256'): S.review(doc)

    def test_duplicate_json_members_and_bad_json(self):
        text=json.dumps(self.doc())
        for bad in ('{"schema":"a","schema":"b"}', '[', '['*2000, text.replace('"chainId": "1"', '"chainId": NaN')):
            with self.assertRaises(ValueError): S.review_json(bad)

    def test_limits(self):
        for proposals in ([], [transaction()]*65, 'not-list', [True], ['0'*(S.MAX_JSON_CHARS+1)]):
            doc=self.doc(); doc['transactions']=proposals
            with self.assertRaises(ValueError): S.review(doc)
        with self.assertRaises(ValueError): S.review_json(' '*(S.MAX_JSON_CHARS+1))

    def test_fingerprint_normalizes_hex_case_only(self):
        doc=self.doc(); original=doc['transactions'][0]
        r=S.review(doc)
        doc['transactions'][0]='0x'+original[2:].upper()
        self.assertEqual(r['proposals'][0]['envelopeSha256'], S.review(doc)['proposals'][0]['envelopeSha256'])
        doc['transactions'][0]=transaction(value=1)
        self.assertNotEqual(r['proposals'][0]['envelopeSha256'], S.review(doc)['proposals'][0]['envelopeSha256'])

    def test_math_does_not_overflow(self):
        doc=self.doc(); doc['transactions']=[transaction(cap=S.UINT256_MAX, tip=0, value=S.UINT256_MAX)]
        r=S.review(doc)
        self.assertEqual(r['allListedProposalsCeilingWei'], str(100001*S.UINT256_MAX))
        self.assertFalse(r['coversAllListedCeilings'])


if __name__ == '__main__': unittest.main()
