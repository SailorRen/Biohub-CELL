#!/usr/bin/env python3
"""Collect and fail-close the read-only Kaggle prewrite facts for Biohub V20B.

This command intentionally performs no SaveKernel, Dataset, Model, or submission
write.  It authenticates once, reads the current principal/quota/object identities,
and writes a small redacted JSON receipt.  Authentication secrets are never read
into the receipt or printed by this script.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "CODEX_20260904_BIOHUB_V20B_TWO_EMBRYO_PAIRED_RADIUS"
PRINCIPAL = "sailorren"
COMPETITION = "biohub-cell-tracking-during-development"
VALIDATION_REF = "sailorren/biohub-v20b-two-embryo-radius-validation"
PRODUCTION_REF = "sailorren/biohub-v20b-two-embryo-radius-production"
BASELINE_REF = "sailorren/biohub-v19c-public0939-sis14-only"
EXPECTED_DATASETS = (
    ("pilkwang/biohub-deepcenter-unet3d-center-prior-v1", 5),
    ("pilkwang/biohub-temporal-unet3d-seed314159-v1", 2),
    ("pilkwang/biohub-tracking-support-pack-50ep-v1", 10),
)


class PrewriteError(RuntimeError):
    """Raised when a frozen prewrite assertion does not hold."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PrewriteError(message)


def iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return str(value)


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def quota_payload(response: Any) -> dict[str, Any]:
    gpu = response.gpu_quota
    require(gpu is not None, "GPU quota response is absent")
    used = gpu.time_used.total_seconds() / 3600.0
    total = gpu.total_time_allowed.total_seconds() / 3600.0
    return {
        "used_hours": round(used, 6),
        "remaining_hours": round(max(0.0, total - used), 6),
        "total_hours": round(total, 6),
        "refresh_at_utc": iso(response.quota_refresh_time),
    }


def kernel_rows(items: list[Any] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in items or []:
        if item is None:
            continue
        rows.append(
            {
                "ref": item.ref,
                "title": item.title,
                "current_version_number": item.current_version_number,
                "last_run_time_utc": iso(item.last_run_time),
                "is_private": item.is_private,
                "enable_gpu": item.enable_gpu,
                "enable_internet": item.enable_internet,
            }
        )
    return sorted(rows, key=lambda row: row["ref"])


def read_pinned_dataset_inventory(api: Any, ref: str, version: int) -> tuple[list[dict[str, Any]], int]:
    files: list[dict[str, Any]] = []
    page_token: str | None = None
    seen_tokens: set[str] = set()
    page_count = 0
    while True:
        response = api.dataset_list_files(
            f"{ref}/{version}", page_token=page_token, page_size=100
        )
        require(not response.error_message, f"exact Dataset version unreadable: {ref}/{version}")
        page_count += 1
        files.extend(
            {
                "name": item.name,
                "total_bytes": item.total_bytes,
            }
            for item in (response.files or [])
            if item is not None
        )
        next_token = response.next_page_token or None
        if next_token is None:
            break
        require(next_token not in seen_tokens, f"Dataset pagination token repeated: {ref}/{version}")
        require(page_count < 100, f"Dataset pagination exceeded 100 pages: {ref}/{version}")
        seen_tokens.add(next_token)
        page_token = next_token
    files.sort(key=lambda row: row["name"])
    require(files, f"exact Dataset version has no readable file inventory: {ref}/{version}")
    require(
        len({row["name"] for row in files}) == len(files),
        f"duplicate file name in pinned Dataset inventory: {ref}/{version}",
    )
    return files, page_count


def collect(args: argparse.Namespace) -> dict[str, Any]:
    # The public package authenticates during this import.  Keep it here so one
    # process performs exactly one authentication flow for the whole receipt.
    from kaggle import api  # type: ignore[import-not-found]  # noqa: PLC0415

    principal = api.get_config_value(api.CONFIG_NAME_USER)
    quota = quota_payload(api.quota_view())

    dataset_rows: list[dict[str, Any]] = []
    for ref, version in EXPECTED_DATASETS:
        owner, slug = ref.split("/", 1)
        listed = api.dataset_list(search=slug, user=owner, page=1) or []
        exact_listed = [
            item for item in listed if item is not None and item.ref == ref
        ]
        require(len(exact_listed) == 1, f"canonical Dataset match count is not one: {ref}")
        current_version = exact_listed[0].current_version_number
        require(
            isinstance(current_version, int) and current_version >= version,
            f"canonical Dataset current version is below pinned version: {ref}/{version}",
        )
        files, page_count = read_pinned_dataset_inventory(api, ref, version)
        dataset_rows.append(
            {
                "ref": ref,
                "pinned_version": version,
                "current_version_number": current_version,
                "identity_method": "EXACT_DATASET_LIST_MATCH_PLUS_PINNED_VERSION_FILE_INVENTORY",
                "status": "PINNED_VERSION_READABLE",
                "pinned_version_inventory_pages": page_count,
                "pinned_version_file_count": len(files),
                "pinned_version_file_inventory_sha256": sha256_json(files),
            }
        )

    comp_response = api.competitions_list(
        group="all", search=COMPETITION, page=1, page_size=100
    )
    competitions = [item for item in (comp_response.competitions or []) if item is not None]
    exact_competitions = [item for item in competitions if item.ref == COMPETITION]
    competition_rows = [
        {
            "ref": item.ref,
            "title": item.title,
            "deadline_utc": iso(item.deadline),
            "max_daily_submissions": item.max_daily_submissions,
            "is_kernels_submissions_only": item.is_kernels_submissions_only,
            "submissions_disabled": item.submissions_disabled,
            "user_has_entered": item.user_has_entered,
        }
        for item in exact_competitions
    ]

    validation_rows = kernel_rows(
        api.kernels_list(
            user=PRINCIPAL,
            search=VALIDATION_REF.split("/", 1)[1],
            page=1,
            page_size=100,
        )
    )
    production_rows = kernel_rows(
        api.kernels_list(
            user=PRINCIPAL,
            search=PRODUCTION_REF.split("/", 1)[1],
            page=1,
            page_size=100,
        )
    )
    exact_validation = [row for row in validation_rows if row["ref"] == VALIDATION_REF]
    exact_production = [row for row in production_rows if row["ref"] == PRODUCTION_REF]

    baseline_status = api.kernels_status(BASELINE_REF)
    submissions = api.competition_submissions(COMPETITION, page_size=100) or []
    v20b_submissions = [
        {
            "submission_id": item.ref,
            "date_utc": iso(item.date),
            "status": str(item.status),
            "description_sha256": hashlib.sha256(item.description.encode("utf-8")).hexdigest(),
        }
        for item in submissions
        if item is not None and "V20B" in item.description
    ]

    receipt = {
        "schema_version": "1.0",
        "task_id": TASK_ID,
        "operation": "READ_ONLY_KAGGLE_PREWRITE",
        "phase": args.phase,
        "observed_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "principal": principal,
        "gpu_quota": quota,
        "minimum_gpu_hours_required": args.minimum_gpu_hours,
        "datasets": dataset_rows,
        "competition_exact_matches": competition_rows,
        "validation_kernel_exact_matches": exact_validation,
        "production_kernel_exact_matches": exact_production,
        "baseline_kernel": {
            "ref": BASELINE_REF,
            "status": str(baseline_status.status),
            "failure_message": baseline_status.failure_message or None,
        },
        "v20b_submission_matches": v20b_submissions,
        "external_write_counts": {
            "save_kernel": 0,
            "dataset_write": 0,
            "model_write": 0,
            "competition_submission": 0,
        },
    }

    require(principal == PRINCIPAL, f"principal mismatch: {principal!r}")
    require(
        quota["remaining_hours"] >= args.minimum_gpu_hours,
        "insufficient current GPU quota for the frozen phase",
    )
    require(len(exact_competitions) == 1, "canonical competition match count must equal 1")
    competition = competition_rows[0]
    require(competition["submissions_disabled"] is False, "competition submissions are disabled")
    require(competition["user_has_entered"] is True, "principal is not entered in competition")
    require(
        all(row["status"] == "PINNED_VERSION_READABLE" for row in dataset_rows),
        "one or more pinned Dataset identities are not readable",
    )
    require(str(baseline_status.status).endswith("COMPLETE"), "V19C baseline is not COMPLETE")
    require(not baseline_status.failure_message, "V19C baseline has a failure message")
    require(not v20b_submissions, "a V20B competition submission already exists")

    if args.phase == "validation":
        require(not exact_validation, "validation kernel slug already exists")
        require(not exact_production, "production kernel slug already exists before validation")
    elif args.phase == "production":
        require(len(exact_validation) == 1, "validation kernel exact match count must equal 1")
        require(not exact_production, "production kernel slug already exists")
    else:
        require(len(exact_validation) == 1, "validation kernel exact match count must equal 1")
        require(len(exact_production) == 1, "production kernel exact match count must equal 1")

    receipt["status"] = "PASS"
    return receipt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("validation", "production", "submission"), required=True)
    parser.add_argument("--minimum-gpu-hours", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        receipt = collect(args)
    except Exception as exc:  # one-shot command: record and stop, never retry
        receipt = {
            "schema_version": "1.0",
            "task_id": TASK_ID,
            "operation": "READ_ONLY_KAGGLE_PREWRITE",
            "phase": args.phase,
            "observed_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "status": "FAIL",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "external_write_counts": {
                "save_kernel": 0,
                "dataset_write": 0,
                "model_write": 0,
                "competition_submission": 0,
            },
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
        print(f"V20B_KAGGLE_PREWRITE_FAIL {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print("V20B_KAGGLE_PREWRITE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
