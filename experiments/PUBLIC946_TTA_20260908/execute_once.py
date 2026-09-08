#!/usr/bin/env python3
"""PUBLIC946 专用一次性写入口：冻结校验、实时只读门禁、先落账、零重试。

仅支持各 arm 的初次 save 和唯一 submit；共享工程修复必须另行只读定位，
此入口不提供自动修复、重发或更改最终提交选择。所有外部调用仅在 main 内。
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import math
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = P.parents[1]
MANIFEST = P / "manifest.json"
RESULTS = P / "results.json"
LEDGER = P / "write_ledger.json"
COMPETITION = "biohub-cell-tracking-during-development"
TASK = "PUBLIC946_TTA_20260908"


def now():
    return datetime.now(timezone.utc).isoformat()


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode()).hexdigest()


def atomic_write(path, value):
    data = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
    fd, temporary = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def safe_error(exc):
    return {"error_type": type(exc).__name__,
            "http_status": getattr(getattr(exc, "response", None), "status_code", None)}


def safe_text(value):
    text = str(value or "")[:2000]
    text = re.sub(r"https?://[^\s]+", "[URL_REDACTED]", text)
    return re.sub(r"(?i)(token|cookie|authorization|credential|signature|secret)([\s=:]+)[^\s,;]+", r"\1\2[REDACTED]", text)


def normalized_ref(value):
    return str(value or "").removeprefix("https://www.kaggle.com/code/").rstrip("/")


def normalized_cells(notebook):
    return [(cell["cell_type"], cell["source"] if isinstance(cell["source"], str) else "".join(cell["source"]))
            for cell in notebook["cells"]]


def submitted_source_hash(notebook):
    # Exact serialization used by the installed kernels_push SDK. This is
    # distinct from the frozen on-disk Notebook byte hash.
    notebook = json.loads(json.dumps(notebook))
    for cell in notebook["cells"]:
        if "outputs" in cell and cell["cell_type"] == "code":
            cell["outputs"] = []
        if isinstance(cell.get("source"), list):
            cell["source"] = "".join(cell["source"])
    return sha(json.dumps(notebook))


def local_gate(arm, action, expected_manifest_sha):
    manifest_bytes = MANIFEST.read_bytes()
    require(sha(manifest_bytes) == expected_manifest_sha, "Frozen manifest SHA mismatch")
    manifest = json.loads(manifest_bytes)
    require(manifest["task_id"] == TASK and manifest["frozen"] is True, "Task manifest is not frozen")
    require(set(manifest["arms"]) == {"B0", "C1", "C2"}, "Unexpected arm set")
    require(len({x["ref"] for x in manifest["arms"].values()}) == 3, "Candidate refs are not unique")
    require(manifest["budget_limits"] == {"new_notebooks": 3, "save_requests": 4,
        "submission_requests": 3, "shared_repairs": 1, "per_object_submission": 1}, "Budget drift")
    for relative, digest in manifest["frozen_files"].items():
        path = (ROOT / relative).resolve()
        require(path.is_relative_to(ROOT), "Frozen path outside repository")
        require(sha(path.read_bytes()) == digest, "Frozen file differs: " + relative)
    results = json.loads(RESULTS.read_text())
    ledger = json.loads(LEDGER.read_text())
    require(results["task_id"] == ledger["task_id"] == TASK, "State task identity mismatch")
    candidate = results["arms"][arm]
    frozen = manifest["arms"][arm]
    for key in ("ref", "source_sha256", "metadata_sha256"):
        require(candidate[key] == frozen[key], "Mutable candidate identity drift: " + key)
    require(candidate["ref"].startswith("sailorren/"), "Wrong candidate owner")
    code_bytes = (P / arm / "candidate.ipynb").read_bytes()
    metadata_bytes = (P / arm / "kernel-metadata.json").read_bytes()
    require(sha(code_bytes) == frozen["source_sha256"], "Candidate source hash mismatch")
    require(sha(metadata_bytes) == frozen["metadata_sha256"], "Candidate metadata hash mismatch")
    notebook, metadata = json.loads(code_bytes), json.loads(metadata_bytes)
    require(metadata["id"] == candidate["ref"] and metadata["code_file"] == "candidate.ipynb", "Metadata points elsewhere")
    require(metadata["is_private"] is True and metadata["enable_gpu"] is True and metadata["enable_internet"] is False, "Private/GPU/offline metadata drift")
    require(metadata["competition_sources"] == [COMPETITION] and not metadata.get("kernel_sources") and not metadata.get("model_sources"), "Unexpected external input type")
    for key in ("dataset_sources", "machine_shape", "docker_image", "enable_tpu", "docker_image_pinning_type"):
        require(metadata.get(key) == manifest["fixed_inputs"].get(key), "Fixed input/runtime mismatch: " + key)
    require([sha(s) for _, s in normalized_cells(notebook)] == frozen["cell_source_sha256"], "Cell execution source mismatch")
    for key, maximum in (("save_requests", 4), ("submission_requests", 3), ("repair_requests", 1)):
        require(type(ledger[key]) is int and 0 <= ledger[key] <= maximum, "Invalid ledger count: " + key)
    saves = [op for op in ledger["operations"] if op.get("action") == "SaveKernel"]
    submits = [op for op in ledger["operations"] if op.get("action") == "CreateCodeSubmission"]
    require(len(saves) == ledger["save_requests"] and len(submits) == ledger["submission_requests"], "Request counters differ from operations")
    require(all(op.get("arm") in {"B0", "C1", "C2"} for op in saves + submits), "Unrecognized ledger arm")
    require(not any(op.get("arm") == arm for op in (saves if action == "save" else submits)), "This arm/action was already attempted; read-only reconciliation required")
    if action == "save":
        require(ledger["save_requests"] < 4 and candidate.get("version") is None and candidate.get("kernel_id") is None, "Initial save budget or identity gate failed")
        if arm != "B0":
            require(results["arms"]["B0"]["ordinary"]["verified"] is True, "B0 ordinary run must be verified first")
    else:
        require(ledger["submission_requests"] < 3 and candidate["submission"].get("id") is None, "Formal submission budget/identity gate failed")
        require(candidate["ordinary"]["verified"] is True and candidate["ordinary"].get("final_audit_verified") is True, "Final ordinary output audit not verified")
        require(candidate["remote_binding"]["verified"] is True, "Remote source/version binding not verified")
        require(type(candidate.get("version")) is int and candidate["version"] > 0, "Missing exact ordinal Version")
        require(type(candidate.get("script_version_id")) is int and candidate["script_version_id"] > 0, "Missing exact ScriptVersionId")
        require(any(op.get("arm") == arm and op.get("response", {}).get("version_number") == candidate["version"] for op in saves), "Version is not bound to this arm's save receipt")
    return manifest, results, ledger, notebook, metadata


def live_preflight(api, arm, action, manifest, candidate, notebook):
    from kagglesdk.competitions.types.competition_api_service import ApiGetCompetitionRequest
    from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest
    out = {"observed_at_utc": now(), "principal": api.get_config_value(api.CONFIG_NAME_USER)}
    require(out["principal"] == "sailorren", "Wrong authenticated Kaggle account")
    request = ApiGetCompetitionRequest()
    request.competition_name = COMPETITION
    with api.build_kaggle_client() as client:
        competition = client.competitions.competition_api_client.get_competition(request)
    out["competition"] = {key: getattr(competition, key) for key in (
        "max_daily_submissions", "submissions_disabled", "user_has_entered", "is_kernels_submissions_only")}
    require(out["competition"]["user_has_entered"] is True and out["competition"]["submissions_disabled"] is False, "Competition entry/submission availability gate failed")
    require(out["competition"]["is_kernels_submissions_only"] is True, "Wrong competition submission mode")
    quota = api.quota_view()
    gpu = quota.gpu_quota
    require(gpu is not None, "GPU quota could not be read")
    remaining_hours = (gpu.total_time_allowed - gpu.time_used).total_seconds() / 3600
    require(math.isfinite(remaining_hours), "Invalid GPU quota")
    out["gpu_quota"] = {"used_hours": gpu.time_used.total_seconds() / 3600,
        "total_hours": gpu.total_time_allowed.total_seconds() / 3600,
        "remaining_hours": remaining_hours, "refresh_at": str(quota.quota_refresh_time)}
    if action == "save":
        require(remaining_hours > 0, "No GPU time remains")
    rows = api.competition_submissions(COMPETITION, page_size=100) or []
    today = out["observed_at_utc"][:10]
    today_rows = [row for row in rows if str(row.date).startswith(today)]
    maximum = out["competition"]["max_daily_submissions"]
    require(type(maximum) is int and maximum > 0, "Daily submission limit unavailable")
    require(len(rows) < 100 or any(str(row.date)[:10] < today for row in rows), "Submission page may omit today's rows")
    out["today_utc"] = today
    out["today_submission_ids"] = [int(row.ref) for row in today_rows]
    out["today_submission_count"] = len(today_rows)
    out["submission_remaining"] = max(0, maximum - len(today_rows))
    if action == "submit":
        require(out["submission_remaining"] > 0, "No formal submission quota remains")
        marker = f"{TASK} {arm} |"
        require(not any(marker in (row.description or "") for row in rows), "An existing task submission was found; do not repeat")
    request = ApiGetKernelRequest()
    request.user_name, request.kernel_slug = candidate["ref"].split("/")
    try:
        with api.build_kaggle_client() as client:
            kernel = client.kernels.kernels_api_client.get_kernel(request)
    except Exception as exc:
        error = safe_error(exc)
        out["kernel_get"] = error
        require(action == "save" and error["http_status"] in (403, 404), "Kernel identity query failed; read-only reconcile required")
        own = api.kernels_list(mine=True, search="biohub-946-", page_size=100) or []
        refs = [normalized_ref(item.ref) for item in own]
        out["own_exact_ref_matches"] = [ref for ref in refs if ref == candidate["ref"]]
        require(len(own) < 100 and not out["own_exact_ref_matches"], "Existing candidate ref or incomplete own-kernel listing")
        historical = json.loads((P / "preflight.json").read_text())["browser_readback"]["duplicate_refs"][arm]
        require(historical == "We can't find that page.", "No frozen browser absence corroboration")
        out["absence_evidence"] = "Live authenticated own-kernel list with no exact match plus frozen direct-browser missing page; 403 alone not absence"
    else:
        require(action == "submit", "Candidate ref already exists; initial save must not overwrite it")
        m = kernel.metadata
        require(normalized_ref(m.ref) == candidate["ref"], "Live kernel ref mismatch")
        require(m.current_version_number == candidate["version"] and m.id == candidate["kernel_id"], "Live current version/kernel ID changed")
        require(m.is_private is True and m.enable_gpu is True and m.enable_internet is False, "Live runtime privacy/GPU/internet changed")
        remote_source = kernel.blob.source
        require(normalized_cells(json.loads(remote_source)) == normalized_cells(notebook), "Live executed source differs from exact candidate")
        out["kernel_get"] = {"ref": m.ref, "kernel_id": m.id, "version": m.current_version_number,
            "remote_source_sha256": sha(remote_source), "cell_sources_equal": True,
            "script_version_id_from_verified_binding": candidate["script_version_id"]}
    out["status"] = "PASS"
    return out



@contextmanager
def single_write_transport(api, action, operation):
    """One instance-local SDK client context, zero retry/redirect replay.

    Installed kernels_push/competition_submit_code each call the generated SDK
    exactly once (no with_retry decorator). Also force the requests adapter to
    zero retries and block redirect replay, with a second-send hard guard.
    Account configuration and global SDK classes are never changed.
    """
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    original_builder = api.build_kaggle_client
    expected_path = ("/kernels.KernelsApiService/SaveKernel" if action == "save"
                     else "/competitions.CompetitionApiService/CreateCodeSubmission")
    sent = {"count": 0}
    operation["transport"] = {"max_retries": 0, "allow_redirects": False, "max_write_sends": 1}

    def builder():
        client = original_builder()
        http = client.http_client()
        http._verbose = False
        http._init_session()
        session = http._session
        retry = Retry(total=0, connect=0, read=0, redirect=0, status=0, other=0)
        session.mount("https://", HTTPAdapter(max_retries=retry))
        session.mount("http://", HTTPAdapter(max_retries=retry))
        original_send = session.send

        def send(request, **kwargs):
            require(request.method == "POST" and request.url.endswith(expected_path), "Unexpected write transport destination")
            require(sent["count"] == 0, "Second write transport send forbidden")
            sent["count"] += 1
            operation["transport"]["send_calls"] = sent["count"]
            kwargs["allow_redirects"] = False
            kwargs.setdefault("timeout", (20, 300))
            response = original_send(request, **kwargs)
            require(not 300 <= response.status_code < 400, "Write redirect requires read-only reconciliation")
            return response

        session.send = send
        return client

    api.build_kaggle_client = builder
    try:
        yield
    finally:
        api.build_kaggle_client = original_builder
        operation["transport"]["send_calls"] = sent["count"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["save", "submit"])
    parser.add_argument("--arm", choices=["B0", "C1", "C2"], required=True)
    parser.add_argument("--manifest-sha256", required=True)
    args = parser.parse_args()
    require(re.fullmatch(r"[0-9a-f]{64}", args.manifest_sha256) is not None, "Invalid fixed manifest hash")
    lock_name = Path(tempfile.gettempdir()) / ("public946_write_" + sha(str(P))[:16] + ".lock")
    with lock_name.open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        manifest, results, ledger, notebook, metadata = local_gate(args.arm, args.action, args.manifest_sha256)
        candidate = results["arms"][args.arm]
        # kaggle import authenticates via a read-only token introspection.
        from kaggle import api
        try:
            preflight = live_preflight(api, args.arm, args.action, manifest, candidate, notebook)
        except Exception as exc:
            event = {"action": "ReadOnlyPreflight", "arm": args.arm, "at_utc": now(),
                "status": "BLOCKED_NO_WRITE_REQUEST", **safe_error(exc)}
            ledger["operations"].append(event)
            atomic_write(LEDGER, ledger)
            print(json.dumps(event, ensure_ascii=False, indent=2))
            return 2
        require(preflight["today_utc"] == now()[:10], "UTC date changed during preflight; no request sent")
        # Recheck all frozen bytes immediately before booking the request.
        local_gate(args.arm, args.action, args.manifest_sha256)
        counter = "save_requests" if args.action == "save" else "submission_requests"
        ledger[counter] += 1
        operation = {"action": "SaveKernel" if args.action == "save" else "CreateCodeSubmission",
            "arm": args.arm, "ref": candidate["ref"], "attempt": 1, "at_utc": now(),
            "status": "ATTEMPTED", "manifest_sha256": args.manifest_sha256,
            "source_sha256": candidate["source_sha256"], "metadata_sha256": candidate["metadata_sha256"],
            "submitted_source_sha256": submitted_source_hash(notebook), "preflight": preflight,
            "quota_remaining_before": preflight["submission_remaining"]}
        if args.action == "submit":
            operation.update(version=candidate["version"], script_version_id=candidate["script_version_id"])
            operation["description"] = (f"{TASK} {args.arm} | V{candidate['version']} | "
                f"SV{candidate['script_version_id']} | SHA256 {operation['submitted_source_sha256']}")
        ledger["operations"].append(operation)
        atomic_write(LEDGER, ledger)  # Durable request budget consumed before SDK call.
        try:
            if args.action == "save":
                with single_write_transport(api, args.action, operation):
                    response = api.kernels_push(str(P / args.arm))
                receipt = {"ref": normalized_ref(getattr(response, "ref", "")),
                    "version_number": int(getattr(response, "version_number", 0)),
                    "kernel_id": int(getattr(response, "kernel_id", 0)),
                    "error": safe_text(getattr(response, "error", ""))}
                for key in ("invalid_dataset_sources", "invalid_competition_sources", "invalid_kernel_sources", "invalid_model_sources"):
                    receipt[key] = [safe_text(item) for item in (getattr(response, key, None) or [])]
                operation["response"] = receipt
                accepted = not receipt["error"] and receipt["version_number"] > 0 and receipt["kernel_id"] > 0
                if accepted:
                    candidate.update(version=receipt["version_number"], kernel_id=receipt["kernel_id"],
                        submitted_source_sha256=operation["submitted_source_sha256"])
                    candidate["ordinary"].update(status="REQUEST_ACCEPTED_STATUS_PENDING", verified=False)
                candidate["write_status"] = "ORDINARY_REQUESTED_READBACK_REQUIRED" if accepted else "SAVE_RESPONSE_REQUIRES_READBACK"
            else:
                with single_write_transport(api, args.action, operation):
                    response = api.competition_submit_code(file_name="submission.csv", message=operation["description"],
                        competition=COMPETITION, kernel=candidate["ref"], kernel_version=candidate["version"], quiet=True)
                receipt = {"id": int(getattr(response, "ref", 0)), "ref": int(getattr(response, "ref", 0)), "message": safe_text(getattr(response, "message", ""))}
                operation["response"] = receipt
                accepted = receipt["id"] > 0
                if accepted:
                    candidate["submission"].update(id=receipt["id"], status="REQUEST_ACCEPTED_STATUS_PENDING",
                        public_score=None, description=operation["description"], requested_at_utc=operation["at_utc"])
                candidate["write_status"] = "FORMAL_REQUESTED_READBACK_REQUIRED" if accepted else "FORMAL_RESPONSE_REQUIRES_READBACK"
            operation.update(status="RESPONSE_RECEIVED_READBACK_REQUIRED", completed_at_utc=now())
        except BaseException as exc:
            operation.update(status="WRITE_OUTCOME_UNKNOWN_READ_ONLY_RECONCILE_REQUIRED", completed_at_utc=now(), **safe_error(exc))
            candidate["write_status"] = "WRITE_OUTCOME_UNKNOWN_READ_ONLY_RECONCILE_REQUIRED"
        finally:
            # Receipt first: a failure updating results cannot erase a request
            # or enable a retry. Never print raw response objects/exceptions.
            atomic_write(LEDGER, ledger)
            results["updated_at_utc"] = now()
            atomic_write(RESULTS, results)
            print(json.dumps(operation, ensure_ascii=False, indent=2))
        return 0 if operation["status"] == "RESPONSE_RECEIVED_READBACK_REQUIRED" else 3


if __name__ == "__main__":
    raise SystemExit(main())
