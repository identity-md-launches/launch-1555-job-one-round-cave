#!/usr/bin/env python3
"""Real retained observations; mutations below are synthetic adversarial tests."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import socket
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("receipt_audit_under_test", HERE / "audit.py")
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def flip(value):
    return value[:-1] + ("1" if value[-1] == "0" else "0")


class ReceiptAuditTests(unittest.TestCase):
    def setUp(self):
        self.capture = a.reader.read_capture(HERE.parent / "transfer-crosscheck" / "publicnode.json")
        self.evidence = a.reader.read_capture(HERE / "observations.json")
        self.receipt = self.evidence["observations"][0]["receipt"]

    def report(self):
        return a.report(self.capture, self.evidence)

    def token_logs(self):
        return [log for log in self.receipt["logs"] if
                log["address"] == self.capture["token_address"] and log["topics"]
                and log["topics"][0] == a.window.TRANSFER_TOPIC]

    def rebuild(self, logs):
        # Mutate a real capture only inside tests, recomputing its producer fields.
        self.capture["raw_logs"] = logs
        events, duplicate = a.window.validate_logs(logs, self.capture["decimals"],
            self.capture["token_address"], self.capture["from_block"], self.capture["to_block"])
        self.capture["transfers"] = events
        self.capture["transfer_count"] = len(events)
        self.capture["duplicate_count"] = duplicate

    def test_real_demo_has_no_network(self):
        output = io.StringIO()
        with patch.object(socket, "socket", side_effect=AssertionError("network forbidden")):
            with contextlib.redirect_stdout(output):
                self.assertEqual(a.main(["--demo"]), 0)
        r = json.loads(output.getvalue())
        self.assertEqual(r["status"], "matching")
        self.assertEqual(r["matching_transfer_count"], 3)
        self.assertEqual(r["transactions"][0]["receipt_log_count"], 15)
        self.assertEqual(r["transactions"][0]["other_log_count"], 12)

    def test_no_mutation(self):
        before = copy.deepcopy((self.capture, self.evidence))
        self.report()
        self.assertEqual((self.capture, self.evidence), before)

    def test_missing_receipt_unavailable(self):
        self.evidence["observations"][0]["receipt"] = None
        r = self.report()
        self.assertEqual(r["status"], "unavailable")
        self.assertEqual(r["matching_transfer_count"], 0)
        self.assertEqual(r["counts"]["unavailable"], 1)

    def test_missing_transfer(self):
        log = self.token_logs()[0]
        self.receipt["logs"].remove(log)
        row = self.report()["transactions"][0]
        self.assertEqual(row["status"], "conflicting")
        self.assertEqual(row["missing_log_indexes"], [int(log["logIndex"], 16)])
        self.assertEqual(len(row["matching_log_indexes"]), 2)

    def test_extra_transfer_in_existing_transaction(self):
        self.rebuild(self.capture["raw_logs"][1:])
        row = self.report()["transactions"][0]
        self.assertEqual(row["status"], "conflicting")
        self.assertEqual(len(row["extra_transfers"]), 1)
        self.assertEqual(row["extra_transfers"][0]["log_index"], 642)

    def test_changed_transfer_value(self):
        self.token_logs()[0]["data"] = flip(self.token_logs()[0]["data"])
        row = self.report()["transactions"][0]
        self.assertEqual(row["status"], "conflicting")
        self.assertEqual(len(row["conflicting_transfers"]), 1)
        self.assertNotEqual(row["conflicting_transfers"][0]["saved"]["raw_value"],
                            row["conflicting_transfers"][0]["observed"]["raw_value"])

    def test_changed_sender(self):
        log = self.token_logs()[0]
        log["topics"][1] = flip(log["topics"][1])
        self.assertEqual(len(self.report()["transactions"][0]["conflicting_transfers"]), 1)

    def test_receipt_moved_to_new_block(self):
        for container in [self.receipt] + self.receipt["logs"]:
            container["blockNumber"] = hex(int(container["blockNumber"], 16) + 1)
            container["blockHash"] = flip(container["blockHash"])
        row = self.report()["transactions"][0]
        self.assertEqual(row["metadata_conflicts"], ["block", "block_hash"])
        self.assertEqual(len(row["conflicting_transfers"]), 3)

    def test_transaction_index_conflict(self):
        for container in [self.receipt] + self.receipt["logs"]:
            container["transactionIndex"] = hex(int(container["transactionIndex"], 16) + 1)
        self.assertEqual(self.report()["transactions"][0]["metadata_conflicts"], ["transaction_index"])

    def test_failed_receipt_has_missing_events(self):
        self.receipt["status"] = "0x0"
        self.receipt["logs"] = []
        row = self.report()["transactions"][0]
        self.assertEqual(row["metadata_conflicts"], ["execution_status"])
        self.assertEqual(row["missing_log_indexes"], [642, 644, 645])

    def test_failed_receipt_with_logs_rejected(self):
        self.receipt["status"] = "0x0"
        with self.assertRaises(a.window.RpcError):
            self.report()

    def test_wrong_requested_transaction_rejected(self):
        self.receipt["transactionHash"] = flip(self.receipt["transactionHash"])
        with self.assertRaises(a.window.RpcError):
            self.report()

    def test_every_log_metadata_checked(self):
        for key in ("blockNumber", "blockHash", "transactionHash", "transactionIndex"):
            with self.subTest(key=key):
                original = self.receipt["logs"][0][key]
                self.receipt["logs"][0][key] = flip(original)
                with self.assertRaises(a.window.RpcError):
                    self.report()
                self.receipt["logs"][0][key] = original

    def test_duplicate_and_reversed_receipt_logs_rejected(self):
        old = copy.deepcopy(self.receipt["logs"])
        for logs in ([old[0]] + old, list(reversed(old))):
            self.receipt["logs"] = logs
            with self.assertRaises(a.window.RpcError):
                self.report()

    def test_removed_or_missing_flag_rejected(self):
        for value in (None, True, 0, 1, "false"):
            self.receipt["logs"][0]["removed"] = value
            with self.assertRaises(a.window.RpcError):
                self.report()

    def test_hex_and_receipt_types_rejected(self):
        for field, values in (("status", [True, 1.0, "0x01", "0x2"]),
                              ("blockNumber", [True, 1.0, "0x00", "0x-1"]),
                              ("logs", [{}, None, "logs"])):
            original = self.receipt[field]
            for value in values:
                with self.subTest(field=field, value=value):
                    self.receipt[field] = value
                    with self.assertRaises(a.window.RpcError):
                        self.report()
            self.receipt[field] = original

    def test_log_data_topics_and_budget(self):
        log = self.receipt["logs"][0]
        for key, values in (("data", ["0x1", "0xzz", "0x" + "aa" * 65537]),
                            ("topics", [None, {}, [a.window.TRANSFER_TOPIC] * 5])):
            original = log[key]
            for value in values:
                log[key] = value
                with self.assertRaises(a.window.RpcError):
                    self.report()
            log[key] = original
        self.receipt["logs"] = [log] * 1025
        with self.assertRaises(a.window.RpcError):
            self.report()

    def test_malformed_target_transfer_rejected(self):
        self.token_logs()[0]["topics"].pop()
        with self.assertRaises(a.window.RpcError):
            self.report()

    def test_other_event_same_token_counted_only(self):
        log = self.token_logs()[0]
        log["topics"][0] = flip(log["topics"][0])
        row = self.report()["transactions"][0]
        self.assertEqual(row["other_log_count"], 13)
        self.assertEqual(row["missing_log_indexes"], [642])

    def test_empty_capture_not_checked(self):
        self.rebuild([])
        self.evidence["observations"] = []
        r = self.report()
        self.assertEqual(r["status"], "not_checked")
        self.assertEqual(r["transaction_count"], 0)

    def test_capture_duplicates_normalized(self):
        self.rebuild(self.capture["raw_logs"] + self.capture["raw_logs"])
        self.assertEqual(self.report()["matching_transfer_count"], 3)

    def test_invalid_saved_summary_fails_before_network(self):
        self.capture["transfers"][0]["block"] = float(self.capture["transfers"][0]["block"])
        with patch.object(a, "receipt_rpc", side_effect=AssertionError("network called")):
            with self.assertRaises(a.window.RpcError):
                a.collect(self.capture)

    def test_transaction_limit_before_network(self):
        checked = a.groups.report(self.capture)
        checked["observed_transaction_count"] = 33
        with patch.object(a.groups, "report", return_value=checked):
            with patch.object(a, "receipt_rpc", side_effect=AssertionError("network called")):
                with self.assertRaises(a.window.RpcError):
                    a.collect(self.capture)

    def test_collect_exact_reads_and_decoded_block_number(self):
        tx = self.receipt["transactionHash"]
        with patch.object(a, "receipt_rpc", side_effect=["0x1", self.receipt]) as call:
            observed = a.collect(self.capture)
        self.assertEqual(call.call_args_list[0].args, (a.window.DEFAULT_RPC, "eth_chainId", []))
        self.assertEqual(call.call_args_list[1].args, (a.window.DEFAULT_RPC, "eth_getTransactionReceipt", [tx]))
        self.assertEqual(call.call_count, 2)
        self.assertEqual(int(observed["observations"][0]["receipt"]["blockNumber"], 16), 26177309)
        self.assertEqual(a.report(self.capture, observed)["status"], "matching")

    def test_wrong_chain_stops_before_receipts(self):
        with patch.object(a, "receipt_rpc", return_value="0x2") as call:
            with self.assertRaises(a.window.RpcError):
                a.collect(self.capture)
        self.assertEqual(call.call_count, 1)

    def test_network_error_no_partial_stdout(self):
        output = io.StringIO()
        with patch.object(a, "receipt_rpc", side_effect=["0x1", a.window.RpcError("failure")]):
            with contextlib.redirect_stdout(output):
                with self.assertRaises(a.window.RpcError):
                    a.main(["--capture", str(HERE.parent / "transfer-crosscheck" / "publicnode.json"), "--live"])
        self.assertEqual(output.getvalue(), "")

    def test_transport_rejects_other_methods_before_open(self):
        with patch.object(a.window, "public_opener", side_effect=AssertionError("opened transport")):
            for method in ("eth_sendRawTransaction", "eth_call", "eth_getLogs"):
                with self.assertRaises(a.window.RpcError):
                    a.receipt_rpc(a.window.DEFAULT_RPC, method, [])

    def test_transport_read_bound_headers_and_rpc_envelope(self):
        class Response:
            def __init__(self, raw):
                self.raw = raw
                self.requested = None
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self, count):
                self.requested = count
                return self.raw[:count]
        response = Response(b'{"jsonrpc":"2.0","id":1,"result":null}')
        opener = unittest.mock.Mock()
        opener.open.return_value = response
        with patch.object(a.window, "public_opener", return_value=opener):
            self.assertIsNone(a.receipt_rpc(a.window.DEFAULT_RPC, "eth_getTransactionReceipt",
                                           [self.receipt["transactionHash"]]))
        self.assertEqual(response.requested, a.MAX_REPLY_BYTES + 1)
        request = opener.open.call_args.args[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertIn("Pepeolithic-Transfer-Receipt-Audit", request.get_header("User-agent"))
        self.assertEqual(json.loads(request.data)["method"], "eth_getTransactionReceipt")
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 25)
        for raw in (b'x' * (a.MAX_REPLY_BYTES + 1),
                    b'{"jsonrpc":"2.0","id":1,"result":null,"result":null}',
                    b'{"jsonrpc":"2.0","id":2,"result":null}',
                    b'{"jsonrpc":"2.0","id":1,"error":{"code":-1,"message":"no"}}'):
            opener.open.return_value = Response(raw)
            with patch.object(a.window, "public_opener", return_value=opener):
                with self.assertRaises(a.window.RpcError):
                    a.receipt_rpc(a.window.DEFAULT_RPC, "eth_chainId", [])

    def test_two_transactions_and_conflict_precedence(self):
        # Explicit synthetic second transaction within the same real block.
        log = copy.deepcopy(self.capture["raw_logs"][-1])
        log["transactionHash"] = flip(log["transactionHash"])
        log["transactionIndex"] = hex(int(log["transactionIndex"], 16) + 1)
        log["logIndex"] = hex(int(log["logIndex"], 16) + 1)
        self.rebuild(self.capture["raw_logs"] + [log])
        second = {"transactionHash": log["transactionHash"], "transactionIndex": log["transactionIndex"],
                  "blockNumber": log["blockNumber"], "blockHash": log["blockHash"],
                  "status": "0x1", "logs": [log]}
        self.evidence["observations"].append({"requested_transaction_hash": log["transactionHash"],
                                             "receipt": second})
        self.assertEqual(self.report()["matching_transfer_count"], 4)
        self.evidence["observations"][1]["receipt"] = None
        self.token_logs()[0]["data"] = flip(self.token_logs()[0]["data"])
        r = self.report()
        self.assertEqual(r["status"], "conflicting")
        self.assertEqual(r["counts"], {"matching": 0, "conflicting": 1, "unavailable": 1})

    def test_uppercase_hex_fields_normalize(self):
        for container in [self.receipt] + self.receipt["logs"]:
            for key in ("transactionHash", "blockHash", "blockNumber", "transactionIndex", "logIndex", "address", "data"):
                if key in container:
                    container[key] = "0x" + container[key][2:].upper()
            if "topics" in container:
                container["topics"] = ["0x" + topic[2:].upper() for topic in container["topics"]]
        self.assertEqual(self.report()["status"], "matching")

    def test_evidence_schema_order_and_timestamp(self):
        for key, values in (("chain_id", [True, 1.0, 2]), ("schema_version", [True, 1.0, 2]),
                            ("observed_at", [None, "today", "2026-10-13T11:31:23"]),
                            ("rpc", [None, "https://user:secret@example.com"]),
                            ("observations", [[], [self.evidence["observations"][0]] * 2])):
            original = self.evidence[key]
            for value in values:
                with self.subTest(key=key):
                    self.evidence[key] = value
                    with self.assertRaises(a.window.RpcError):
                        self.report()
            self.evidence[key] = original
        self.evidence["observations"][0]["requested_transaction_hash"] = flip(self.receipt["transactionHash"])
        with self.assertRaises(a.window.RpcError):
            self.report()

    def test_null_receipt_cli_exit_one(self):
        self.evidence["observations"][0]["receipt"] = None
        with patch.object(a.reader, "read_capture", side_effect=[self.capture, self.evidence]):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(a.main(["--demo"]), 1)

    def test_demo_refuses_live_flags(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as exc:
                a.main(["--demo", "--live"])
        self.assertEqual(exc.exception.code, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
