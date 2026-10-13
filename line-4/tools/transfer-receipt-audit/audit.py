#!/usr/bin/env python3
"""Compare a bounded saved ERC-20 window with public transaction receipts."""
import argparse
import datetime as dt
import importlib.util
import json
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "groups_for_receipt_audit", HERE.parent / "transfer-transaction-groups" / "groups.py")
groups = importlib.util.module_from_spec(spec)
spec.loader.exec_module(groups)
window, reader = groups.window, groups.reader
MAX_TRANSACTIONS = 32
MAX_RECEIPT_LOGS = 1024
MAX_REPLY_BYTES = 1024 * 1024
MAX_EVIDENCE_BYTES = 16 * 1024 * 1024
RECEIPT_FIELDS = ("transactionHash", "transactionIndex", "blockNumber", "blockHash", "status", "logs")
LOG_FIELDS = ("address", "topics", "data", "blockNumber", "blockHash",
              "transactionHash", "transactionIndex", "logIndex", "removed")
LIMITATIONS = (
    "Provider-reported receipts are compared with saved provider logs, not proved "
    "against a receipts root or consensus. Matching only covers transactions "
    "already present in the capture; entirely omitted transactions and empty "
    "windows are not checked. Other token/event logs are counted, not interpreted. "
    "This is not a completeness, balance, swap, price, pool activity or finality "
    "proof. Sequential reads are not atomic. Replay is dated evidence, not a "
    "fresh read. A conflict alone does not establish a reorganization."
)


def plan(capture):
    checked = groups.report(capture)
    if checked["observed_transaction_count"] > MAX_TRANSACTIONS:
        raise window.RpcError("receipt audit is limited to 32 observed transactions")
    return checked


def receipt_rpc(endpoint, method, params):
    """A separate two-method allowlist; ancestor transport permissions stay intact."""
    if method not in {"eth_chainId", "eth_getTransactionReceipt"}:
        raise window.RpcError("receipt transport permits only chain ID and receipt reads")
    window.validate_endpoint(endpoint)
    request = urllib.request.Request(endpoint, data=json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        separators=(",", ":")).encode(), headers={
            "Content-Type": "application/json",
            "User-Agent": "Pepeolithic-Transfer-Receipt-Audit/1.0 (public read only)"}, method="POST")
    try:
        with window.public_opener().open(request, timeout=25) as response:
            raw = response.read(MAX_REPLY_BYTES + 1)
        return window.strict_rpc.decode_reply(raw, max_bytes=MAX_REPLY_BYTES)
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise window.RpcError("receipt RPC failed: " + str(exc)) from exc


def receipt_view(receipt, tx):
    """Validate all enclosing/log metadata, retaining the public comparison fields."""
    if receipt is None:
        return None
    if type(receipt) is not dict:
        raise window.RpcError("receipt must be an object or null")
    result = {key: receipt.get(key) for key in RECEIPT_FIELDS}
    result["transactionHash"] = window.hex_bytes(result["transactionHash"], 32, "receipt transaction")
    if result["transactionHash"] != tx:
        raise window.RpcError("receipt returned for the wrong requested transaction")
    result["blockHash"] = window.hex_bytes(result["blockHash"], 32, "receipt block hash")
    for field in ("transactionIndex", "blockNumber", "status"):
        result[field] = hex(window.quantity(result[field], "receipt " + field))
    if result["status"] not in {"0x0", "0x1"}:
        raise window.RpcError("receipt status must be 0 or 1")
    logs = result["logs"]
    if type(logs) is not list or len(logs) > MAX_RECEIPT_LOGS:
        raise window.RpcError("receipt logs must be a list with at most 1024 entries")
    if result["status"] == "0x0" and logs:
        raise window.RpcError("failed receipt cannot contain logs")
    normalized = []
    previous = -1
    for log in logs:
        if type(log) is not dict or log.get("removed") is not False:
            raise window.RpcError("receipt log requires an object and explicit removed=false")
        item = {key: log.get(key) for key in LOG_FIELDS}
        for key, size in (("address", 20), ("blockHash", 32), ("transactionHash", 32)):
            item[key] = window.hex_bytes(item[key], size, "receipt log " + key)
        for key in ("blockNumber", "transactionIndex", "logIndex"):
            item[key] = hex(window.quantity(item[key], "receipt log " + key))
        for key in ("blockNumber", "blockHash", "transactionHash", "transactionIndex"):
            if item[key] != result[key]:
                raise window.RpcError("receipt log disagrees with enclosing " + key)
        index = int(item["logIndex"], 16)
        if index <= previous:
            raise window.RpcError("receipt log indexes must be strictly increasing and unique")
        previous = index
        topics = item["topics"]
        if type(topics) is not list or len(topics) > 4:
            raise window.RpcError("receipt log requires at most four topics")
        item["topics"] = [window.hex_bytes(topic, 32, "receipt log topic") for topic in topics]
        data = item["data"]
        if (type(data) is not str or len(data) > 2 + 65536 * 2
                or re.fullmatch(r"0x(?:[0-9a-fA-F]{2})*", data) is None):
            raise window.RpcError("receipt log data must be even hex bytes, at most 64 KiB")
        item["data"] = data.lower()
        normalized.append(item)
    result["logs"] = normalized
    return result


def collect(capture, endpoint=window.DEFAULT_RPC):
    checked = plan(capture)  # All capture and budget checks precede network I/O.
    window.validate_endpoint(endpoint)
    if window.quantity(receipt_rpc(endpoint, "eth_chainId", []), "chain ID") != 1:
        raise window.RpcError("Ethereum mainnet required")
    observations = []
    for transaction in checked["transactions"]:
        tx = transaction["transaction_hash"]
        receipt = receipt_rpc(endpoint, "eth_getTransactionReceipt", [tx])
        observations.append({"requested_transaction_hash": tx, "receipt": receipt_view(receipt, tx)})
    evidence = {"kind": "erc20-transfer-receipt-observations", "schema_version": 1,
                "chain_id": 1, "rpc": endpoint,
                "observed_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
                "observations": observations}
    if len(json.dumps(evidence).encode()) > MAX_EVIDENCE_BYTES:
        raise window.RpcError("receipt evidence exceeds 16 MiB; use fewer transactions")
    return evidence


def report(capture, evidence):
    checked = plan(capture)
    if (type(evidence) is not dict or evidence.get("kind") != "erc20-transfer-receipt-observations"
            or type(evidence.get("schema_version")) is not int or evidence["schema_version"] != 1
            or type(evidence.get("chain_id")) is not int or evidence["chain_id"] != 1):
        raise window.RpcError("mainnet receipt evidence schema 1 required")
    endpoint, timestamp = evidence.get("rpc"), evidence.get("observed_at")
    if type(endpoint) is not str:
        raise window.RpcError("evidence RPC must be a string")
    window.validate_endpoint(endpoint)
    if type(timestamp) is not str or len(timestamp) > 40:
        raise window.RpcError("timezone-aware observation timestamp required")
    try:
        if dt.datetime.fromisoformat(timestamp.replace("Z", "+00:00")).tzinfo is None:
            raise ValueError("missing timezone")
    except ValueError as exc:
        raise window.RpcError("invalid observation timestamp") from exc
    observations = evidence.get("observations")
    if type(observations) is not list or len(observations) != len(checked["transactions"]):
        raise window.RpcError("one ordered receipt observation per planned transaction required")
    rows = []
    for saved, observation in zip(checked["transactions"], observations):
        tx = saved["transaction_hash"]
        if (type(observation) is not dict
                or set(observation) != {"requested_transaction_hash", "receipt"}
                or observation["requested_transaction_hash"] != tx):
            raise window.RpcError("receipt observations must follow the planned transaction order")
        receipt = receipt_view(observation["receipt"], tx)
        row = {"transaction_hash": tx, "saved_block": saved["block"],
               "saved_block_hash": saved["block_hash"], "saved_transaction_index": saved["transaction_index"],
               "saved_transfer_count": saved["transfer_count"], "status": "unavailable",
               "metadata_conflicts": [], "matching_log_indexes": [], "missing_log_indexes": [],
               "extra_transfers": [], "conflicting_transfers": [], "observed_receipt": None,
               "receipt_log_count": None, "other_log_count": None}
        if receipt is not None:
            metadata = {"block": int(receipt["blockNumber"], 16), "block_hash": receipt["blockHash"],
                        "transaction_index": int(receipt["transactionIndex"], 16),
                        "execution_status": int(receipt["status"], 16)}
            row["observed_receipt"] = metadata
            row["metadata_conflicts"] = [key for key in ("block", "block_hash", "transaction_index")
                                         if metadata[key] != saved[key]]
            if metadata["execution_status"] != 1:
                row["metadata_conflicts"].append("execution_status")
            selected = []
            for log in receipt["logs"]:
                if (log["address"] == checked["token_address"] and log["topics"]
                        and log["topics"][0] == window.TRANSFER_TOPIC):
                    selected.append(window.decode_log(log, checked["decimals"], checked["token_address"]))
            row["receipt_log_count"] = len(receipt["logs"])
            row["other_log_count"] = len(receipt["logs"]) - len(selected)
            original = {event["log_index"]: event for event in saved["transfers"]}
            current = {event["log_index"]: event for event in selected}
            row["missing_log_indexes"] = sorted(original.keys() - current.keys())
            row["extra_transfers"] = [current[index] for index in sorted(current.keys() - original.keys())]
            for index in sorted(original.keys() & current.keys()):
                if original[index] == current[index]:
                    row["matching_log_indexes"].append(index)
                else:
                    row["conflicting_transfers"].append({"log_index": index,
                                                       "saved": original[index], "observed": current[index]})
            row["status"] = "conflicting" if any(row[key] for key in (
                "metadata_conflicts", "missing_log_indexes", "extra_transfers", "conflicting_transfers")) else "matching"
        rows.append(row)
    counts = {status: sum(row["status"] == status for row in rows)
              for status in ("matching", "conflicting", "unavailable")}
    status = ("not_checked" if not rows else "conflicting" if counts["conflicting"] else
              "unavailable" if counts["unavailable"] else "matching")
    return {"kind": "erc20-transfer-receipt-audit", "schema_version": 1,
            "read_only": True, "raw_logs_revalidated": True, "status": status,
            "chain_id": 1, "token": checked["token"], "token_address": checked["token_address"],
            "from_block": checked["from_block"], "to_block": checked["to_block"],
            "transfer_count": checked["transfer_count"], "transaction_count": len(rows),
            "matching_transfer_count": sum(len(row["matching_log_indexes"]) for row in rows),
            "counts": counts, "transactions": rows, "rpc": endpoint, "observed_at": timestamp,
            "max_transactions": MAX_TRANSACTIONS, "limitations": LIMITATIONS}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--demo", action="store_true", help="offline replay of real ZTO receipt evidence")
    source.add_argument("--capture", type=Path, help="saved workspace capture")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--live", action="store_true", help="explicitly read public receipts now")
    mode.add_argument("--evidence", type=Path, help="replay receipt observations JSON")
    parser.add_argument("--rpc", help="credential-free public mainnet RPC; live only")
    args = parser.parse_args(argv)
    if args.demo:
        if args.live or args.evidence or args.rpc:
            parser.error("demo uses retained evidence only")
        capture = reader.read_capture(HERE.parent / "transfer-crosscheck" / "publicnode.json")
        evidence = reader.read_capture(HERE / "observations.json", max_bytes=MAX_EVIDENCE_BYTES)
    else:
        if not (args.live or args.evidence) or (args.rpc and not args.live):
            parser.error("choose live or evidence explicitly; rpc requires live")
        capture = reader.read_capture(args.capture)
        evidence = (collect(capture, args.rpc or window.DEFAULT_RPC) if args.live else
                    reader.read_capture(args.evidence, max_bytes=MAX_EVIDENCE_BYTES))
    result = report(capture, evidence)
    result["mode"] = "live" if args.live else "replay"
    result["evidence"] = evidence
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "matching" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, window.RpcError) as exc:
        print("transfer-receipt-audit: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
