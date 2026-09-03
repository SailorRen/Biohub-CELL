#!/usr/bin/env python3
"""Deterministic verifier for the INITIAL_RECON_V01 research bundle.

The default mode writes the required JSON report. ``--verify-only`` never writes.
``--remote-readback`` additionally downloads the required files from GitHub's
authoritative contents API and compares their SHA-256 digests with local files.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote


RESEARCH_REL = Path("research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01")
VERIFY_REL = Path("reports/20260903_BIOHUB_CELL_INITIAL_RESEARCH_VERIFY.json")

REQUIRED_FILES = [
    Path("AGENTS.md"),
    Path("README.md"),
    Path(".gitignore"),
    Path("governance/CURRENT_PROJECT_CONTEXT.json"),
    Path("governance/EXTERNAL_ACTION_LEDGER.json"),
    Path("tasks/CODEX_20260903_BIOHUB_CELL_INITIAL_RECON_TASK.md"),
    RESEARCH_REL / "00_source_manifest.jsonl",
    RESEARCH_REL / "01_official_competition.md",
    RESEARCH_REL / "02_official_data_inventory.csv",
    RESEARCH_REL / "03_official_rules_and_metric.md",
    RESEARCH_REL / "04_leaderboard_snapshot.csv",
    RESEARCH_REL / "05_kaggle_code_inventory.csv",
    RESEARCH_REL / "06_kaggle_code_deep_read.md",
    RESEARCH_REL / "07_kaggle_method_comparison.csv",
    RESEARCH_REL / "08_kaggle_discussion_inventory.csv",
    RESEARCH_REL / "09_kaggle_discussion_deep_read.md",
    RESEARCH_REL / "10_host_clarifications.md",
    RESEARCH_REL / "11_github_repository_inventory.csv",
    RESEARCH_REL / "12_github_deep_read.md",
    RESEARCH_REL / "13_github_code_method_matrix.csv",
    RESEARCH_REL / "14_reddit_and_web_inventory.csv",
    RESEARCH_REL / "15_external_scientific_sources.md",
    RESEARCH_REL / "16_similar_kaggle_competitions.csv",
    RESEARCH_REL / "17_historical_solution_research.md",
    RESEARCH_REL / "18_kaggle_datasets_inventory.csv",
    RESEARCH_REL / "19_claims_evidence_matrix.csv",
    RESEARCH_REL / "20_access_failures.md",
    RESEARCH_REL / "21_search_query_log.csv",
    Path("reports/20260903_BIOHUB_CELL_INITIAL_RESEARCH_REPORT_V01.md"),
    Path("reports/completion_claim.json"),
    Path("scripts/verify_research_bundle.py"),
]

CSV_REQUIRED_COLUMNS: dict[Path, set[str]] = {
    RESEARCH_REL / "02_official_data_inventory.csv": {
        "source_id", "path", "item_type", "size_bytes", "format", "read_status", "notes"
    },
    RESEARCH_REL / "04_leaderboard_snapshot.csv": {
        "snapshot_time_utc", "rank", "team_count", "public_score", "read_status", "source_id", "notes"
    },
    RESEARCH_REL / "05_kaggle_code_inventory.csv": {
        "source_id", "owner", "notebook_title", "notebook_slug", "url", "current_version",
        "script_version_id", "created_at", "updated_at", "votes", "comments",
        "page_displayed_score", "score_source", "accelerator", "runtime", "internet_setting",
        "input_datasets", "output_files", "license", "read_status", "source_saved",
        "source_sha256", "source_bytes", "markdown_cells", "code_cells", "output_cells",
        "all_code_cells_checked", "relevance", "current_score_verified", "stale_score_risk", "notes"
    },
    RESEARCH_REL / "07_kaggle_method_comparison.csv": {
        "source_id", "detection", "segmentation", "node_extraction", "temporal_linking",
        "assignment_optimization", "division_detection", "track_filtering", "node_count_calibration",
        "external_model_data", "cv_design", "reported_local_score", "current_verified_public_score",
        "runtime", "reproducibility", "license", "known_failure", "evidence_source_ids"
    },
    RESEARCH_REL / "08_kaggle_discussion_inventory.csv": {
        "source_id", "discussion_id", "title", "author", "author_role", "created_at", "updated_at",
        "votes", "comment_count", "url", "topic", "read_status", "first_post_read",
        "comments_loaded", "comments_total", "host_reply_present", "evidence_path", "notes"
    },
    RESEARCH_REL / "11_github_repository_inventory.csv": {
        "source_id", "owner_repo", "url", "description", "relation_to_competition", "stars", "forks",
        "default_branch", "latest_commit_sha", "latest_commit_date", "license", "archived", "file_count",
        "read_status", "files_actually_read", "evidence_path", "notes"
    },
    RESEARCH_REL / "13_github_code_method_matrix.csv": {
        "source_id", "owner_repo", "commit_sha", "detection", "segmentation", "tracking",
        "division", "optimization", "data_loading", "evaluation", "submission_conversion",
        "dependencies", "license", "files_read", "transfer_notes"
    },
    RESEARCH_REL / "14_reddit_and_web_inventory.csv": {
        "source_id", "platform", "title", "author", "url", "created_at", "score", "comment_count",
        "topic", "read_status", "comments_loaded", "comments_total", "evidence_path", "notes"
    },
    RESEARCH_REL / "16_similar_kaggle_competitions.csv": {
        "source_id", "competition", "url", "microscopy", "spatial_dimensions", "time_dimension",
        "task_type", "cell_division", "sparse_labels", "output_type", "metric", "data_scale",
        "compute", "external_data", "post_competition_solution", "transferability",
        "required_changes", "incompatibilities", "deep_read", "read_status", "evidence_path"
    },
    RESEARCH_REL / "18_kaggle_datasets_inventory.csv": {
        "source_id", "owner_dataset", "url_ref", "title", "created_at", "updated_at", "size", "license",
        "usability", "votes", "download_count", "files", "file_formats", "microscopy_type", "species",
        "dimensions", "time_dimension", "labels", "relevance", "possible_use", "rule_eligibility_checked",
        "leakage_risk", "compatibility", "read_status", "evidence_path", "notes"
    },
    RESEARCH_REL / "19_claims_evidence_matrix.csv": {
        "claim_id", "report_section", "claim_text", "claim_type", "source_ids", "evidence_paths",
        "direct_or_inference", "confidence", "conflict_present", "conflict_notes"
    },
    RESEARCH_REL / "21_search_query_log.csv": {
        "query_id", "category", "platform", "query", "sort_order", "result_page", "reported_total",
        "actually_obtained", "unique_after_dedupe", "deep_read_count", "access_time_utc",
        "access_time_singapore", "status", "evidence_path", "notes"
    },
}

ALLOWED_READ_STATUSES = {
    "FULL_PAGE_BODY_READ", "FULL_THREAD_READ", "PARTIAL_THREAD_READ",
    "FULL_NOTEBOOK_SOURCE_AND_OUTPUTS_READ", "FULL_NOTEBOOK_SOURCE_READ",
    "NOTEBOOK_SOURCE_PARTIAL", "FULL_RELEVANT_REPO_SOURCE_READ", "TARGET_FILES_READ",
    "README_ONLY", "METADATA_ONLY", "TITLE_SNIPPET_ONLY", "BLOCKED", "RATE_LIMITED",
    "LOGIN_REQUIRED", "DELETED", "NOT_FOUND", "UNKNOWN",
}

FULL_STATUSES = {s for s in ALLOWED_READ_STATUSES if s.startswith("FULL_")}
NOTEBOOK_FULL = {"FULL_NOTEBOOK_SOURCE_AND_OUTPUTS_READ", "FULL_NOTEBOOK_SOURCE_READ"}
BLOCK_STATUSES = {"BLOCKED", "RATE_LIMITED", "LOGIN_REQUIRED", "DELETED", "NOT_FOUND", "UNKNOWN"}

REMOTE_READBACK_FILES = [
    Path("AGENTS.md"),
    Path("README.md"),
    Path("governance/CURRENT_PROJECT_CONTEXT.json"),
    RESEARCH_REL / "00_source_manifest.jsonl",
    RESEARCH_REL / "03_official_rules_and_metric.md",
    RESEARCH_REL / "05_kaggle_code_inventory.csv",
    RESEARCH_REL / "08_kaggle_discussion_inventory.csv",
    RESEARCH_REL / "11_github_repository_inventory.csv",
    RESEARCH_REL / "16_similar_kaggle_competitions.csv",
    RESEARCH_REL / "18_kaggle_datasets_inventory.csv",
    RESEARCH_REL / "19_claims_evidence_matrix.csv",
    Path("reports/20260903_BIOHUB_CELL_INITIAL_RESEARCH_REPORT_V01.md"),
    VERIFY_REL,
]


@dataclass
class Check:
    check_id: str
    status: str
    details: dict[str, Any]


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def split_multi(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"[;|]", value or "") if item.strip()]


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[0-9a-f]{64}", value))


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "pass"}


def run_git(root: Path, argv: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *argv], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)


def verify_remote_readback(root: Path) -> tuple[bool, dict[str, Any]]:
    local_head = run_git(root, ["rev-parse", "HEAD"])
    remote_head = run_git(root, ["ls-remote", "origin", "refs/heads/main"])
    if local_head.returncode or remote_head.returncode:
        return False, {
            "reason": "git_head_read_failed",
            "local_exit": local_head.returncode,
            "remote_exit": remote_head.returncode,
        }
    local_sha = local_head.stdout.decode().strip()
    remote_line = remote_head.stdout.decode().strip()
    remote_sha = remote_line.split()[0] if remote_line else ""
    if local_sha != remote_sha:
        return False, {"reason": "head_mismatch", "local_head": local_sha, "remote_head": remote_sha}

    matches = 0
    failures: list[dict[str, str]] = []
    for rel in REMOTE_READBACK_FILES:
        local_path = root / rel
        if not local_path.is_file():
            failures.append({"path": rel.as_posix(), "reason": "local_missing"})
            continue
        api_path = quote(rel.as_posix(), safe="/")
        cmd = [
            "gh", "api", "-H", "Accept: application/vnd.github.raw+json",
            f"repos/SailorRen/Biohub-CELL/contents/{api_path}?ref=main",
        ]
        proc = subprocess.run(cmd, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
        if proc.returncode:
            failures.append({"path": rel.as_posix(), "reason": "remote_fetch_failed", "exit": str(proc.returncode)})
            continue
        local_digest = digest_file(local_path)
        remote_digest = digest_bytes(proc.stdout)
        if local_digest != remote_digest:
            failures.append({"path": rel.as_posix(), "reason": "sha256_mismatch"})
            continue
        matches += 1
    return not failures and matches == len(REMOTE_READBACK_FILES), {
        "local_head": local_sha,
        "remote_head": remote_sha,
        "matched": matches,
        "expected": len(REMOTE_READBACK_FILES),
        "failures": failures,
    }


def build_checks(root: Path, include_remote: bool) -> tuple[list[Check], dict[str, Any]]:
    checks: list[Check] = []

    def add(check_id: str, passed: bool, **details: Any) -> None:
        checks.append(Check(check_id, "PASS" if passed else "FAIL", details))

    missing = [p.as_posix() for p in REQUIRED_FILES if not (root / p).is_file()]
    empty = [p.as_posix() for p in REQUIRED_FILES if (root / p).is_file() and (root / p).stat().st_size == 0]
    add("required_files_present_nonempty", not missing and not empty, missing=missing, empty=empty,
        required=len(REQUIRED_FILES))

    csv_rows: dict[Path, list[dict[str, str]]] = {}
    csv_errors: list[dict[str, Any]] = []
    for rel, required_columns in CSV_REQUIRED_COLUMNS.items():
        path = root / rel
        if not path.is_file():
            csv_errors.append({"path": rel.as_posix(), "reason": "missing"})
            continue
        try:
            fields, rows = load_csv(path)
            csv_rows[rel] = rows
            absent = sorted(required_columns - set(fields))
            if absent or not rows:
                csv_errors.append({"path": rel.as_posix(), "missing_columns": absent, "data_rows": len(rows)})
        except Exception as exc:  # noqa: BLE001
            csv_errors.append({"path": rel.as_posix(), "reason": type(exc).__name__})
    add("csv_headers_and_data_rows", not csv_errors, errors=csv_errors, files=len(CSV_REQUIRED_COLUMNS))

    manifest_path = root / RESEARCH_REL / "00_source_manifest.jsonl"
    manifest: list[dict[str, Any]] = []
    manifest_errors: list[dict[str, Any]] = []
    if manifest_path.is_file():
        for lineno, raw_line in enumerate(manifest_path.read_text(encoding="utf-8").splitlines(), start=1):
            if not raw_line.strip():
                continue
            try:
                row = json.loads(raw_line)
                if not isinstance(row, dict):
                    raise TypeError("record_not_object")
                manifest.append(row)
            except Exception as exc:  # noqa: BLE001
                manifest_errors.append({"line": lineno, "reason": type(exc).__name__})
    else:
        manifest_errors.append({"reason": "missing"})
    ids = [str(row.get("source_id", "")) for row in manifest]
    duplicates = sorted({item for item in ids if item and ids.count(item) > 1})
    missing_ids = sum(not item for item in ids)
    add("source_manifest_valid_jsonl_unique_ids", bool(manifest) and not manifest_errors and not duplicates and not missing_ids,
        records=len(manifest), parse_errors=manifest_errors, duplicate_ids=duplicates, missing_ids=missing_ids)

    status_errors: list[dict[str, Any]] = []
    evidence_errors: list[dict[str, Any]] = []
    full_errors: list[dict[str, Any]] = []
    for row in manifest:
        sid = str(row.get("source_id", ""))
        status = row.get("read_status")
        if status not in ALLOWED_READ_STATUSES:
            status_errors.append({"source_id": sid, "status": status})
        evidence_path = str(row.get("evidence_path", "")).strip()
        if not evidence_path or not (root / evidence_path).is_file():
            evidence_errors.append({"source_id": sid, "evidence_path": evidence_path or None})
        if status in FULL_STATUSES:
            try:
                observed = int(row.get("bytes_observed", 0))
            except (TypeError, ValueError):
                observed = 0
            if observed <= 0 or not is_sha256(row.get("sha256")):
                full_errors.append({"source_id": sid, "bytes_observed": observed,
                                    "sha256_valid": is_sha256(row.get("sha256"))})
    add("manifest_read_status_allowlist", not status_errors, errors=status_errors)
    add("manifest_evidence_paths_exist", bool(manifest) and not evidence_errors, errors=evidence_errors)
    add("full_reads_have_bytes_and_sha256", not full_errors, errors=full_errors)

    notebook_rows = csv_rows.get(RESEARCH_REL / "05_kaggle_code_inventory.csv", [])
    nb_full = [r for r in notebook_rows if r.get("read_status") in NOTEBOOK_FULL]
    nb_errors = []
    for row in nb_full:
        if not is_sha256(row.get("source_sha256")):
            nb_errors.append({"source_id": row.get("source_id"), "reason": "invalid_source_sha256"})
            continue
        try:
            cells_ok = int(row.get("code_cells", "")) >= 0 and int(row.get("markdown_cells", "")) >= 0 \
                and int(row.get("output_cells", "")) >= 0 and int(row.get("source_bytes", "")) > 0
        except (TypeError, ValueError):
            cells_ok = False
        if not cells_ok or not truthy(row.get("all_code_cells_checked")):
            nb_errors.append({"source_id": row.get("source_id"), "reason": "missing_cell_audit"})
    nb_min_ok = len(nb_full) >= 30 or (0 < len(notebook_rows) < 30 and len(nb_full) == len(notebook_rows))
    add("kaggle_notebook_deep_read_minimum", nb_min_ok and not nb_errors,
        discovered=len(notebook_rows), full_source_reads=len(nb_full), errors=nb_errors)

    discussion_rows = csv_rows.get(RESEARCH_REL / "08_kaggle_discussion_inventory.csv", [])
    thread_reads = [r for r in discussion_rows if r.get("read_status") in {"FULL_THREAD_READ", "PARTIAL_THREAD_READ"}]
    discussion_min_ok = len(thread_reads) >= 30 or (0 < len(discussion_rows) < 30 and len(thread_reads) == len(discussion_rows))
    thread_field_errors = [r.get("source_id") for r in thread_reads if not r.get("comments_loaded") or not r.get("comments_total")]
    add("kaggle_discussion_deep_read_minimum", discussion_min_ok and not thread_field_errors,
        discovered=len(discussion_rows), deep_reads=len(thread_reads), missing_comment_counts=thread_field_errors)

    github_rows = csv_rows.get(RESEARCH_REL / "11_github_repository_inventory.csv", [])
    github_deep = [r for r in github_rows if r.get("read_status") == "FULL_RELEVANT_REPO_SOURCE_READ"]
    gh_min_ok = len(github_deep) >= 15 or (0 < len(github_rows) < 15 and len(github_deep) == len(github_rows))
    gh_errors = [r.get("source_id") for r in github_deep
                 if not re.fullmatch(r"[0-9a-f]{40}", r.get("latest_commit_sha", ""))
                 or len(split_multi(r.get("files_actually_read", ""))) < 2]
    add("github_repository_deep_read_minimum", gh_min_ok and not gh_errors,
        discovered=len(github_rows), deep_reads=len(github_deep), invalid_deep_records=gh_errors)

    dataset_rows = csv_rows.get(RESEARCH_REL / "18_kaggle_datasets_inventory.csv", [])
    dataset_deep = [r for r in dataset_rows if r.get("read_status") == "FULL_PAGE_BODY_READ"]
    dataset_min_ok = len(dataset_deep) >= 25 or (0 < len(dataset_rows) < 25 and len(dataset_deep) == len(dataset_rows))
    add("kaggle_dataset_page_read_minimum", dataset_min_ok,
        discovered=len(dataset_rows), full_page_reads=len(dataset_deep))

    similar_rows = csv_rows.get(RESEARCH_REL / "16_similar_kaggle_competitions.csv", [])
    similar_deep = [r for r in similar_rows if truthy(r.get("deep_read"))]
    add("similar_kaggle_competition_minimum", len(similar_rows) >= 8 and len(similar_deep) >= 5,
        candidates=len(similar_rows), deep_reads=len(similar_deep))

    official_full = [r for r in manifest if r.get("source_type") == "official_competition_page"
                     and r.get("platform") == "Kaggle" and r.get("read_status") == "FULL_PAGE_BODY_READ"]
    add("official_competition_pages_read", len(official_full) >= 7, full_page_reads=len(official_full), required=7)

    query_rows = csv_rows.get(RESEARCH_REL / "21_search_query_log.csv", [])
    categories = {r.get("category", "") for r in query_rows}
    required_categories = {
        "official", "kaggle_code", "kaggle_discussion", "github_repository", "github_code",
        "reddit_native", "reddit_site_search", "scientific_web", "similar_kaggle", "kaggle_datasets",
    }
    query_evidence_missing = [r.get("query_id") for r in query_rows
                              if not r.get("evidence_path") or not (root / r["evidence_path"]).is_file()]
    add("required_search_categories_and_evidence", required_categories.issubset(categories) and not query_evidence_missing,
        present=sorted(categories), missing=sorted(required_categories - categories),
        query_count=len(query_rows), missing_evidence=query_evidence_missing)

    manifest_ids = {str(row.get("source_id")) for row in manifest}
    claim_rows = csv_rows.get(RESEARCH_REL / "19_claims_evidence_matrix.csv", [])
    claim_errors = []
    allowed_claim_types = {
        "OFFICIAL_FACT", "HOST_CONFIRMED", "SOURCE_CODE_VERIFIED", "MEASURED", "AUTHOR_CLAIM",
        "COMMUNITY_REPORT", "INFERENCE", "UNKNOWN",
    }
    for row in claim_rows:
        claim_id = row.get("claim_id")
        source_ids = split_multi(row.get("source_ids", ""))
        evidence_paths = split_multi(row.get("evidence_paths", ""))
        missing_sources = [sid for sid in source_ids if sid not in manifest_ids]
        missing_evidence = [p for p in evidence_paths if not (root / p).is_file()]
        if not source_ids or missing_sources or not evidence_paths or missing_evidence \
                or row.get("claim_type") not in allowed_claim_types:
            claim_errors.append({"claim_id": claim_id, "missing_sources": missing_sources,
                                 "missing_evidence": missing_evidence,
                                 "claim_type": row.get("claim_type")})
    add("claims_have_manifest_sources_and_evidence", bool(claim_rows) and not claim_errors,
        claims=len(claim_rows), errors=claim_errors)

    failures_path = root / RESEARCH_REL / "20_access_failures.md"
    blocked_records = [r for r in manifest if r.get("read_status") in BLOCK_STATUSES]
    failure_text = failures_path.read_text(encoding="utf-8") if failures_path.is_file() else ""
    missing_failure_mentions = [str(r.get("source_id")) for r in blocked_records
                                if str(r.get("source_id")) not in failure_text]
    add("access_failures_recorded", failures_path.is_file() and not missing_failure_mentions,
        blocked_records=len(blocked_records), missing_mentions=missing_failure_mentions)

    prohibited_suffixes = {
        ".zarr", ".geff", ".tif", ".tiff", ".zip", ".tar", ".gz", ".7z",
        ".pt", ".pth", ".ckpt", ".onnx",
    }
    prohibited_names = {"submission.csv", "kaggle.json"}
    oversized = []
    prohibited = []
    secret_named = []
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts or ".task-verification" in path.parts:
            continue
        rel = path.relative_to(root).as_posix()
        if path.stat().st_size > 20 * 1024 * 1024:
            oversized.append({"path": rel, "bytes": path.stat().st_size})
        if path.name.lower() in prohibited_names or path.suffix.lower() in prohibited_suffixes \
                or rel.lower().endswith(".ome.zarr"):
            prohibited.append(rel)
        lower_name = path.name.lower()
        if lower_name.startswith(".env") or lower_name.startswith("cookies"):
            secret_named.append(rel)
    add("no_large_or_prohibited_artifacts", not oversized and not prohibited and not secret_named,
        oversized=oversized, prohibited=prohibited, secret_named=secret_named)

    placeholder_words = ["TO" + "DO", "T" + "BD", "PLACE" + "HOLDER", "待" + "补充"]
    placeholder_hits = []
    excluded = {
        Path("tasks/CODEX_20260903_BIOHUB_CELL_INITIAL_RECON_TASK.md"),
        Path("tasks/CODEX_20260903_BIOHUB_CELL_INITIAL_RECON_CONTRACT.json"),
        Path("scripts/verify_research_bundle.py"),
    }
    # Scan canonical deliverables, not quoted/source evidence.  A source excerpt
    # may legitimately contain one of these tokens and must not be rewritten or
    # misrepresented merely to satisfy the verifier.
    for rel_path in REQUIRED_FILES:
        path = root / rel_path
        if not path.is_file():
            continue
        if rel_path in excluded:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        # Match Latin markers as tokens rather than substrings.  Repository
        # evidence legitimately contains names such as ``mastodon``; treating
        # the embedded letters "todo" as an unfinished-work marker is a false
        # positive.  The Chinese marker is matched exactly.
        found = []
        for word in placeholder_words:
            if word == "待补充":
                matched = word in text
            else:
                matched = bool(re.search(rf"(?<![A-Za-z0-9_]){re.escape(word)}(?![A-Za-z0-9_])", text,
                                         flags=re.IGNORECASE))
            if matched:
                found.append(word)
        if found:
            placeholder_hits.append({"path": rel_path.as_posix(), "tokens": found})
    add("no_placeholder_tokens_in_deliverables", not placeholder_hits, hits=placeholder_hits)

    try:
        ledger = json.loads((root / "governance/EXTERNAL_ACTION_LEDGER.json").read_text(encoding="utf-8"))
        zero_fields = {
            "kaggle_submission_count": ledger.get("kaggle_submission_count"),
            "kaggle_notebook_write_count": ledger.get("kaggle_notebook_write_count"),
            "training_task_count": ledger.get("training_task_count"),
            "kaggle_dataset_create_count": ledger.get("kaggle_dataset_create_count"),
            "competition_join_or_rule_accept_count": ledger.get("competition_join_or_rule_accept_count"),
            "large_dataset_download_count": ledger.get("large_dataset_download_count"),
        }
        add("forbidden_external_actions_zero", all(value == 0 for value in zero_fields.values()), **zero_fields)
    except Exception as exc:  # noqa: BLE001
        add("forbidden_external_actions_zero", False, reason=type(exc).__name__)

    if include_remote:
        remote_ok, remote_details = verify_remote_readback(root)
        add("github_authoritative_remote_readback", remote_ok, **remote_details)

    counts = {
        "manifest_records": len(manifest),
        "full_read": sum(r.get("read_status") in FULL_STATUSES for r in manifest),
        "metadata_only": sum(r.get("read_status") == "METADATA_ONLY" for r in manifest),
        "title_snippet_only": sum(r.get("read_status") == "TITLE_SNIPPET_ONLY" for r in manifest),
        "blocked": sum(r.get("read_status") == "BLOCKED" for r in manifest),
        "not_found": sum(r.get("read_status") == "NOT_FOUND" for r in manifest),
        "notebook_discovered": len(notebook_rows),
        "notebook_deep_reads": len(nb_full),
        "discussion_discovered": len(discussion_rows),
        "discussion_deep_reads": len(thread_reads),
        "github_repositories_discovered": len(github_rows),
        "github_repositories_deep_reads": len(github_deep),
        "kaggle_datasets": len(dataset_rows),
        "kaggle_datasets_full_page_reads": len(dataset_deep),
        "similar_competitions": len(similar_rows),
        "similar_competitions_deep_reads": len(similar_deep),
        "official_pages_full_reads": len(official_full),
        "reddit_hits": sum(r.get("platform", "").lower() == "reddit"
                           for r in csv_rows.get(RESEARCH_REL / "14_reddit_and_web_inventory.csv", [])),
    }
    return checks, counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--remote-readback", action="store_true")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()

    checks, counts = build_checks(root, include_remote=args.remote_readback)
    passed = sum(check.status == "PASS" for check in checks)
    failed = sum(check.status == "FAIL" for check in checks)
    status = "PASS" if failed == 0 else "FAIL"
    report = {
        "schema_version": "1.0",
        "task_id": "CODEX_20260903_BIOHUB_CELL_INITIAL_RECON_V01",
        "status": status,
        "summary": {"passed": passed, "failed": failed, "total": len(checks)},
        "counts": counts,
        "checks": [asdict(check) for check in checks],
    }

    if not args.verify_only:
        output = root / VERIFY_REL
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if status == "PASS":
        print("LOCAL_BUNDLE_PASS")
        if args.remote_readback:
            print("REMOTE_READBACK_PASS")
        print("VERIFICATION_PASS")
        return 0
    print(f"VERIFICATION_FAIL failed={failed}")
    for check in checks:
        if check.status == "FAIL":
            print(f"FAIL {check.check_id}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
