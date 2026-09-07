"""V21A 专用写入口；先落账再调用，任何响应错误均不重试。"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

P = Path(__file__).resolve().parent
E = P / "evidence.json"


def now():
    return datetime.now(timezone.utc).isoformat()


def persist(e):
    temporary = E.with_suffix(".tmp")
    temporary.write_text(json.dumps(e, ensure_ascii=False, indent=2, default=str) + "\n")
    temporary.replace(E)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["save", "submit"])
    args = parser.parse_args()
    e = json.loads(E.read_text())
    c = e["candidate"]
    ledger = e["write_ledger"]
    assert c["ref"] == "sailorren/biohub-v21a-parent9-dc026"
    assert hashlib.sha256((P / "candidate.ipynb").read_bytes()).hexdigest() == c["file_sha256"]
    assert hashlib.sha256((P / "kernel-metadata.json").read_bytes()).hexdigest() == c["metadata_sha256"]
    from kaggle import api
    assert api.get_config_value(api.CONFIG_NAME_USER) == "sailorren"
    if args.action == "save":
        # This initial entry point deliberately has no automatic repair branch.
        assert ledger["save_requests"] == 0 and not ledger["actual_versions"]
        assert e["preflight"]["status"] == "PASS"
        ledger["save_requests"] += 1
        operation = {"action": "SaveKernel", "attempt": 1, "at_utc": now(), "status": "ATTEMPTED", "source_sha256": c["submitted_source_sha256"]}
    else:
        assert ledger["submission_requests"] == 0
        assert c["ordinary"]["verified"] is True
        assert c["remote_binding"]["verified"] is True
        assert c["version"] in ledger["actual_versions"] and c["script_version_id"]
        ledger["submission_requests"] += 1
        operation = {"action": "CreateCodeSubmission", "attempt": 1, "at_utc": now(), "status": "ATTEMPTED", "version": c["version"], "script_version_id": c["script_version_id"], "source_sha256": c["submitted_source_sha256"]}
    ledger["operations"].append(operation)
    persist(e)
    try:
        if args.action == "save":
            response = api.kernels_push(str(P))
        else:
            response = api.competition_submit_code(
                file_name="submission.csv",
                message=f"V21A parent9 dc026 | Version {c['version']} | SV {c['script_version_id']} | SHA256 {c['submitted_source_sha256']}",
                competition="biohub-cell-tracking-during-development",
                kernel=c["ref"], kernel_version=c["version"], quiet=True,
            )
        receipt = response.to_dict()
        operation.update(status="RESPONSE_RECEIVED", response=receipt, completed_at_utc=now())
        if args.action == "save" and not receipt.get("error"):
            c["version"] = response.version_number
            c["kernel_id"] = response.kernel_id
            if c["version"]:
                ledger["actual_versions"].append(c["version"])
            e["experiment_status"] = "ORDINARY_REQUESTED"
        elif args.action == "submit":
            c["submission"].update(id=response.ref, status="REQUEST_ACCEPTED_STATUS_PENDING", public_score=None)
            e["experiment_status"] = "FORMAL_REQUESTED"
    except Exception as exc:
        http = getattr(exc, "response", None)
        operation.update(status="RESPONSE_ERROR_READ_ONLY_RECONCILE_REQUIRED", error_type=type(exc).__name__, http_status=getattr(http, "status_code", None), completed_at_utc=now())
        e["experiment_status"] = "WRITE_OUTCOME_REQUIRES_READBACK"
    finally:
        persist(e)
        print(json.dumps(operation, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
