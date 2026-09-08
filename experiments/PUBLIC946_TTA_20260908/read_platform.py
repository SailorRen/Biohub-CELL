#!/usr/bin/env python3
"""Only read the PUBLIC946 batch's existing Kaggle objects.

Run with network authorization, e.g. --arm B0 [--logs]. No import-time SDK
authentication, notebook saves, submissions, output downloads, or retries.
GetKernel has no ScriptVersionId field: the root reviewer must supply the
fixed-Version UI identity in results.json. Unversioned API input slugs also
need the fixed-Version input_versions_readback described below.

read_snapshot() returns (reviewable_snapshot, raw_artifacts). Only main writes
the raw source/log and merges the selected arm into results.json. It never
marks ordinary output validation passed or declares task completion.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
BATCH = Path(__file__).resolve().parent
RESULTS = BATCH / "results.json"
RAW_ROOT = ROOT / "downloads/PUBLIC946_TTA_20260908"
COMPETITION = "biohub-cell-tracking-during-development"
LOG_LIMIT = 1_000_000


def sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode()).hexdigest()


def source(cell):
    value = cell["source"]
    return value if isinstance(value, str) else "".join(value)


def now_fields():
    now = datetime.now(timezone.utc)
    return {"observed_at_utc": now.isoformat(),
            "observed_at_shanghai": now.astimezone(ZoneInfo("Asia/Shanghai")).isoformat()}


def redact(text):
    """Keep authenticated download URLs and credential-shaped values out of Git."""
    text = str(text)
    text = re.sub(r"https?://[^\s\"']*[?&](?:X-Goog-Signature|X-Amz-Signature|token|access_token)=[^\s\"']+",
                  "[REDACTED_AUTHENTICATED_URL]", text, flags=re.I)
    text = re.sub(r"\b(Bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1[REDACTED]", text, flags=re.I)
    text = re.sub(r"\b((?:KAGGLE_KEY|API_KEY|ACCESS_TOKEN|PASSWORD)\s*[=:]\s*)[^\s,}]+",
                  r"\1[REDACTED]", text, flags=re.I)
    return text


def error_receipt(exc):
    return {"status": "READ_ERROR", "error_type": type(exc).__name__,
            "http_status": getattr(getattr(exc, "response", None), "status_code", None)}


def clean_submission(row):
    return {"id": int(row.ref), "date_utc": str(row.date),
            "read_location": "Kaggle competition submissions API: " + COMPETITION + "; exact submission ID " + str(row.ref),
            "description": redact(row.description or ""),
            "status": str(row.status).split(".")[-1],
            "public_score": row.public_score if row.public_score not in (None, "") else None,
            "private_score": row.private_score if row.private_score not in (None, "") else None,
            "error_description": redact(getattr(row, "error_description", "") or "")}


def dataset_slug(value):
    parts = value.rstrip("/").split("/")
    return "/".join(parts[:-1]) if len(parts) == 3 and parts[-1].isdigit() else value


def remote_binding(arm, entry, kernel):
    """Do not infer SV or input versions from names, hashes, or scores.

    If API input strings omit versions, root may provide entry's
    input_versions_readback = {verified:true, version:N,
      script_version_id:SV, dataset_sources:[three fully versioned strings],
      observed_at_utc:..., source:"Kaggle fixed-Version Inputs UI"}.
    """
    if kernel.get("status") == "READ_ERROR":
        return {"verified": False, "status": "KERNEL_READ_FAILED", "error": kernel}
    local_path = BATCH / arm / "candidate.ipynb"
    metadata_path = BATCH / arm / "kernel-metadata.json"
    local = json.loads(local_path.read_text())
    expected = json.loads(metadata_path.read_text())
    metadata = kernel["metadata"]
    local_cells = [{"cell_type": c["cell_type"], "source_sha256": sha(source(c))}
                   for c in local["cells"]]
    got_cells = kernel.get("cells", [])
    checks = {
        "local_source_matches_frozen_hash": sha(local_path.read_bytes()) == entry.get("source_sha256"),
        "local_metadata_matches_frozen_hash": sha(metadata_path.read_bytes()) == entry.get("metadata_sha256"),
        "local_cells_match_frozen_hashes": [c["source_sha256"] for c in local_cells] == entry.get("cell_source_sha256"),
        "exact_thirteen_code_cells": len(got_cells) == len(local_cells) == 13 and all(c["cell_type"] == "code" for c in got_cells),
        "all_execution_cells_equal": got_cells == local_cells,
        "ref_matches": metadata.get("ref") == entry["ref"] == expected["id"],
        "ordinal_version_matches": entry.get("version") is not None and metadata.get("version") == entry["version"],
        "script_version_id_supplied_by_reviewer": isinstance(entry.get("script_version_id"), int) and entry["script_version_id"] > 0,
        "kernel_id_matches": entry.get("kernel_id") is None or metadata.get("kernel_id") == entry["kernel_id"],
    }
    for name in ("docker_image", "machine_shape", "is_private", "enable_gpu", "enable_internet", "enable_tpu"):
        checks[name + "_matches"] = metadata.get(name) == expected.get(name)
    for name in ("competition_sources", "kernel_sources", "model_sources"):
        checks[name + "_match"] = sorted(metadata.get(name, [])) == sorted(expected.get(name, []))
    wanted_inputs = sorted(expected["dataset_sources"])
    got_inputs = sorted(metadata.get("dataset_sources", []))
    checks["dataset_slugs_match"] = sorted(dataset_slug(x) for x in got_inputs) == sorted(dataset_slug(x) for x in wanted_inputs)
    direct_versions_match = got_inputs == wanted_inputs
    ui = entry.get("input_versions_readback", {})
    reviewer_versions_match = (ui.get("verified") is True and ui.get("version") == entry.get("version")
        and ui.get("script_version_id") == entry.get("script_version_id")
        and sorted(ui.get("dataset_sources", [])) == wanted_inputs
        and bool(ui.get("observed_at_utc")) and bool(ui.get("source")))
    checks["fixed_input_versions_verified"] = direct_versions_match or reviewer_versions_match
    verified = all(checks.values())
    return {"verified": verified, "status": "SOURCE_VERSION_INPUTS_VERIFIED" if verified else "BINDING_EVIDENCE_PENDING_OR_MISMATCH",
            "checks": checks, "unmet_checks": [k for k, value in checks.items() if not value],
            "ref": entry["ref"], "version": entry.get("version"), "script_version_id": entry.get("script_version_id"),
            "script_version_id_provenance": "Root reviewer fixed-Version UI; not exposed by GetKernel",
            "remote_source_sha256": kernel.get("source_sha256"), "remote_source_bytes": kernel.get("source_bytes"),
            "local_source_sha256": sha(local_path.read_bytes()),
            "source_file_bytes_equal": kernel.get("source_sha256") == sha(local_path.read_bytes()),
            "source_cell_hashes": [c["source_sha256"] for c in got_cells],
            "serialization_note": "File byte equality and ordered executable-cell equality are recorded separately; metadata/outputs are not execution source.",
            "input_version_evidence": "GetKernel versioned inputs" if direct_versions_match else (copy.deepcopy(ui) if reviewer_versions_match else "API_INPUT_VERSIONS_NOT_EXPOSED_OR_DIFFERENT"),
            "metadata": metadata, **{k: kernel[k] for k in ("observed_at_utc", "observed_at_shanghai") if k in kernel}}


def read_snapshot(arm, results=None, logs=False, sdk_api=None):
    """One bounded read snapshot. Returns (JSON-safe receipt, raw source/log).

    Passing sdk_api supports local doubles without authenticating. Real calls
    require the caller's explicit network-enabled shell context. Up to five
    submission-list pages are read; partial enumeration is labeled as such.
    """
    if arm not in {"B0", "C1", "C2"}:
        raise ValueError(arm)
    state = results if results is not None else json.loads(RESULTS.read_text())
    entry = state["arms"][arm]
    if sdk_api is None:
        from kaggle import api as sdk_api
    from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest
    from kagglesdk.competitions.types.competition_api_service import ApiGetCompetitionRequest, ApiListSubmissionsRequest
    out = {"operation": "READ_ONLY_BATCH_SNAPSHOT", "arm": arm, "ref": entry["ref"], **now_fields()}
    raw = {}
    try:
        request = ApiGetKernelRequest()
        request.user_name, request.kernel_slug = entry["ref"].split("/")
        with sdk_api.build_kaggle_client() as client:
            response = client.kernels.kernels_api_client.get_kernel(request)
        m = response.metadata
        text = response.blob.source
        raw["source"] = text.encode()
        notebook = json.loads(text)
        out["kernel"] = {"status": "READ_SUCCESS", **now_fields(), "source_sha256": sha(raw["source"]),
            "source_bytes": len(raw["source"]),
            "cells": [{"cell_type": c["cell_type"], "source_sha256": sha(source(c))} for c in notebook["cells"]],
            "metadata": {"ref": m.ref, "kernel_id": m.id, "version": m.current_version_number,
                "is_private": m.is_private, "enable_gpu": m.enable_gpu, "enable_tpu": m.enable_tpu,
                "enable_internet": m.enable_internet, "machine_shape": m.machine_shape, "docker_image": m.docker_image,
                "dataset_sources": list(m.dataset_data_sources or []), "competition_sources": list(m.competition_data_sources or []),
                "kernel_sources": list(m.kernel_data_sources or []), "model_sources": list(m.model_data_sources or [])}}
        out["remote_binding"] = remote_binding(arm, entry, out["kernel"])
    except Exception as exc:
        out["kernel"] = error_receipt(exc)
        out["remote_binding"] = {"verified": False, "status": "KERNEL_READ_OR_BINDING_FAILED"}
    try:
        status = sdk_api.kernels_status(entry["ref"]).to_dict()
        out["ordinary"] = {"status": str(status.get("status", "UNKNOWN")).split(".")[-1].upper(),
                           "failure_message": redact(status.get("failure_message", "") or ""), **now_fields(),
                           "scope": "Latest ordinary run for ref; exact version requires remote_binding",
                           "output_validation": "NOT_PERFORMED_BY_THIS_READER"}
    except Exception as exc:
        out["ordinary_read_error"] = error_receipt(exc)
    if logs:
        try:
            log = sdk_api.kernels_logs(entry["ref"])
            raw["log"] = log if isinstance(log, bytes) else str(log).encode()
            out["log"] = {"status": "READ_SUCCESS", "bytes": len(raw["log"]), "sha256": sha(raw["log"]), **now_fields(),
                          "scope": "Ordinary log; not formal hidden-run output"}
        except Exception as exc:
            out["log"] = error_receipt(exc)
    try:
        request = ApiGetCompetitionRequest()
        request.competition_name = COMPETITION
        with sdk_api.build_kaggle_client() as client:
            competition = client.competitions.competition_api_client.get_competition(request)
        out["competition"] = {key: getattr(competition, key) for key in
            ("ref", "title", "max_daily_submissions", "is_kernels_submissions_only", "submissions_disabled", "user_has_entered")}
    except Exception as exc:
        out["competition"] = error_receipt(exc)
    try:
        quota = sdk_api.quota_view()
        gpu = quota.gpu_quota
        out["gpu_quota"] = {"used_hours": gpu.time_used.total_seconds() / 3600,
            "total_hours": gpu.total_time_allowed.total_seconds() / 3600,
            "remaining_hours": (gpu.total_time_allowed - gpu.time_used).total_seconds() / 3600,
            "refresh_at": str(quota.quota_refresh_time)} if gpu else {"status": "FIELD_UNAVAILABLE"}
    except Exception as exc:
        out["gpu_quota"] = error_receipt(exc)
    try:
        rows, tokens, next_token, complete = [], set(), "", False
        for page_index in range(5):
            request = ApiListSubmissionsRequest()
            request.competition_name = COMPETITION
            request.page = -1
            request.page_token = next_token
            request.page_size = 100
            with sdk_api.build_kaggle_client() as client:
                response = client.competitions.competition_api_client.list_submissions(request)
            rows.extend(clean_submission(x) for x in (response.submissions or []))
            next_token = response.next_page_token or ""
            if not next_token:
                complete = True
                break
            if next_token in tokens:
                break
            tokens.add(next_token)
        unique = {row["id"]: row for row in rows}
        rows = list(unique.values())
        stamp = now_fields()
        today_count = sum(row["date_utc"][:10] == stamp["observed_at_utc"][:10] for row in rows)
        daily = out["competition"].get("max_daily_submissions")
        out["submission_listing"] = {"rows": len(rows), "pages": page_index + 1, "complete": complete, **stamp,
            "utc_day": stamp["observed_at_utc"][:10], "today_observed_count": today_count,
            "remaining_from_complete_listing": max(0, int(daily) - today_count) if complete and daily is not None else None,
            "remaining_provenance": "Computed from current max_daily_submissions minus all observed UTC-today submissions; no separate server remaining-allowance field is exposed; final UI pre-submit allowance is separate.",
            "matched_batch_submissions": {key: [row for row in rows if row["id"] == value.get("submission", {}).get("id")]
                for key, value in state["arms"].items()}}
        scored = []
        for row in rows:
            try:
                score = Decimal(str(row["public_score"]))
                if row["status"] == "COMPLETE" and score.is_finite():
                    scored.append((score, row))
            except InvalidOperation:
                pass
        if scored:
            score, best = max(scored, key=lambda item: item[0])
            out["current_own_best"] = {**best, **stamp, "listing_complete": complete,
                "same_score_submission_ids": sorted(row["id"] for value, row in scored if value == score),
                "interpretation": "CURRENT_OWN_BEST_VERIFIED" if complete else "BEST_AMONG_OBSERVED_SUBMISSIONS_ONLY"}
    except Exception as exc:
        out["submission_listing"] = error_receipt(exc)
    return out, raw


def save_artifacts(arm, snapshot, raw):
    directory = RAW_ROOT / arm
    directory.mkdir(parents=True, exist_ok=True)
    for key, filename in (("source", "remote.ipynb"), ("log", "ordinary.log")):
        if key not in raw:
            continue
        path = directory / filename
        data = raw[key]
        if path.exists() and path.read_bytes() != data:
            previous = path.read_bytes()
            archive = directory / f"previous_{sha(previous)}_{filename}"
            if not archive.exists():
                archive.write_bytes(previous)
        path.write_bytes(data)
        snapshot.setdefault("artifacts", {})[key] = {"path": str(path.relative_to(ROOT)), "bytes": len(data), "sha256": sha(data)}
    if "log" in raw:
        clean = redact(raw["log"].decode("utf-8", errors="replace"))
        safe_bytes = clean.encode()
        truncated = len(safe_bytes) > LOG_LIMIT
        stored = safe_bytes[-LOG_LIMIT:].decode("utf-8", errors="ignore").encode() if truncated else safe_bytes
        tracked = BATCH / arm / "ordinary.log"
        tracked.parent.mkdir(parents=True, exist_ok=True)
        tracked.write_bytes(stored)
        snapshot["log"].update({"tracked_path": str(tracked.relative_to(ROOT)), "stored_bytes": len(stored),
            "stored_sha256": sha(stored), "redacted": safe_bytes != raw["log"], "truncated_tail": truncated,
            "complete_raw_path": str((directory / "ordinary.log").relative_to(ROOT)),
            "summary_tail": stored.decode("utf-8", errors="replace")[-2000:]})


def merge_selected_arm(arm, snapshot):
    """Merge fresh state; preserve other arms and output-verification fields."""
    original = RESULTS.read_bytes()
    state = json.loads(original)
    entry = state["arms"][arm]
    if entry["ref"] != snapshot["ref"]:
        raise RuntimeError("Selected-arm ref changed during the read; raw snapshot retained, no result merge")
    if snapshot.get("kernel", {}).get("status") == "READ_SUCCESS":
        # Allows a reviewer to add precise SV/input UI evidence while the API
        # read runs, without the reader overwriting those independent fields.
        entry["remote_binding"] = remote_binding(arm, entry, snapshot["kernel"])
    elif "remote_binding" in snapshot:
        entry["last_binding_read_error"] = snapshot["remote_binding"]
    if "ordinary" in snapshot:
        entry.setdefault("ordinary", {}).update(snapshot["ordinary"])
        # COMPLETE means run state only; keep the independent verified flag.
        entry["ordinary"].setdefault("verified", False)
    listing = snapshot.get("submission_listing", {})
    matches = listing.get("matched_batch_submissions", {}).get(arm, [])
    if len(matches) == 1 and matches[0]["id"] == entry.get("submission", {}).get("id"):
        entry["submission"].update(matches[0], **{k: listing[k] for k in ("observed_at_utc", "observed_at_shanghai")})
    if snapshot.get("current_own_best", {}).get("listing_complete"):
        state["current_own_best"] = snapshot["current_own_best"]
    entry["last_platform_read"] = {key: value for key, value in snapshot.items() if key != "remote_binding"}
    state["updated_at_utc"] = now_fields()["observed_at_utc"]
    if RESULTS.read_bytes() != original:
        raise RuntimeError("results.json changed before atomic merge; no overwrite; rerun this read only")
    with tempfile.NamedTemporaryFile("w", dir=RESULTS.parent, prefix=".results_read_", suffix=".tmp", delete=False) as handle:
        handle.write(json.dumps(state, ensure_ascii=False, indent=2, default=str) + "\n")
        temporary = Path(handle.name)
    try:
        if RESULTS.read_bytes() != original:
            raise RuntimeError("Concurrent results change detected; refusing replacement")
        temporary.replace(RESULTS)
    finally:
        temporary.unlink(missing_ok=True)
    return entry.get("remote_binding", {})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", choices=("B0", "C1", "C2"), required=True)
    parser.add_argument("--logs", action="store_true")
    args = parser.parse_args()
    snapshot, raw = read_snapshot(args.arm, logs=args.logs)
    save_artifacts(args.arm, snapshot, raw)
    snapshot["remote_binding"] = merge_selected_arm(args.arm, snapshot)
    print(json.dumps(snapshot, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
