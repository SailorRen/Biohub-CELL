#!/usr/bin/env python3
"""Fail-closed schema and evidence checks for the GitHub staging fragment."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parents[3]

INVENTORY_FIELDS = [
    "source_id", "owner_repo", "url", "description", "relation_to_competition",
    "stars", "forks", "default_branch", "latest_commit_sha", "latest_commit_date",
    "license", "archived", "file_count", "read_status", "files_actually_read",
    "evidence_path", "notes",
]
METHOD_FIELDS = [
    "source_id", "owner_repo", "commit_sha", "detection", "segmentation", "tracking",
    "division", "optimization", "data_loading", "evaluation", "submission_conversion",
    "dependencies", "license", "files_read", "transfer_notes",
]
CLAIM_FIELDS = [
    "claim_id", "report_section", "claim_text", "claim_type", "source_ids",
    "evidence_paths", "direct_or_inference", "confidence", "conflict_present",
    "conflict_notes",
]
QUERY_FIELDS = [
    "query_id", "category", "platform", "query", "sort_order", "result_page",
    "reported_total", "actually_obtained", "unique_after_dedupe", "deep_read_count",
    "access_time_utc", "access_time_singapore", "status", "evidence_path", "notes",
]
MANIFEST_FIELDS = {
    "source_id", "source_type", "platform", "title", "author", "url", "query",
    "sort_order", "result_page", "result_rank", "access_time_utc",
    "access_time_singapore", "read_status", "bytes_observed", "sha256", "version_id",
    "commit_sha", "license", "evidence_path", "factual_use_allowed", "notes",
}
MANIFEST_STATUS_ALLOWLIST = {
    "FULL_PAGE_BODY_READ", "FULL_THREAD_READ", "PARTIAL_THREAD_READ",
    "FULL_NOTEBOOK_SOURCE_AND_OUTPUTS_READ", "FULL_NOTEBOOK_SOURCE_READ",
    "NOTEBOOK_SOURCE_PARTIAL", "FULL_RELEVANT_REPO_SOURCE_READ", "TARGET_FILES_READ",
    "README_ONLY", "METADATA_ONLY", "TITLE_SNIPPET_ONLY", "BLOCKED", "RATE_LIMITED",
    "LOGIN_REQUIRED", "DELETED", "NOT_FOUND", "UNKNOWN",
}
CLAIM_TYPE_ALLOWLIST = {
    "OFFICIAL_FACT", "HOST_CONFIRMED", "SOURCE_CODE_VERIFIED", "MEASURED",
    "AUTHOR_CLAIM", "COMMUNITY_REPORT", "INFERENCE", "UNKNOWN",
}
HEX40 = re.compile(r"[0-9a-f]{40}\Z")


def read_csv(name: str) -> tuple[list[str], list[dict]]:
    with (ROOT / name).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def resolve_evidence(value: str) -> bool:
    return bool(value) and (PROJECT_ROOT / value).is_file()


def main() -> None:
    checks: dict[str, object] = {}
    inv_header, inventory = read_csv("11_github_repository_inventory.csv")
    method_header, methods = read_csv("13_github_code_method_matrix.csv")
    claim_header, claims = read_csv("19_claims_evidence_matrix.github_fragment.csv")
    query_header, queries = read_csv("21_search_query_log.github_fragment.csv")
    manifest = [json.loads(line) for line in (ROOT / "00_source_manifest.github_fragment.jsonl").read_text(encoding="utf-8").splitlines() if line]
    deep = [json.loads(path.read_text(encoding="utf-8")) for path in sorted((ROOT / "evidence").glob("*/repo_evidence.json"))]

    checks["inventory_header_exact"] = inv_header == INVENTORY_FIELDS
    checks["method_header_exact"] = method_header == METHOD_FIELDS
    checks["claims_header_exact"] = claim_header == CLAIM_FIELDS
    checks["query_header_exact"] = query_header == QUERY_FIELDS
    checks["inventory_rows"] = len(inventory)
    checks["method_rows"] = len(methods)
    checks["claims_rows"] = len(claims)
    checks["query_rows"] = len(queries)
    checks["manifest_rows"] = len(manifest)
    checks["query_categories"] = sorted({row["category"] for row in queries})
    checks["query_categories_exact"] = set(checks["query_categories"]) == {"github_repository", "github_code"}
    checks["query_paths_resolve"] = all(resolve_evidence(row["evidence_path"]) for row in queries)
    checks["claim_types"] = sorted({row["claim_type"] for row in claims})
    checks["claim_types_allowlisted"] = all(row["claim_type"] in CLAIM_TYPE_ALLOWLIST for row in claims)
    checks["claim_paths_resolve"] = all(
        all(resolve_evidence(path) for path in row["evidence_paths"].split(";") if path)
        for row in claims
    )
    checks["manifest_fields_exact"] = all(set(row) == MANIFEST_FIELDS for row in manifest)
    checks["manifest_statuses"] = sorted({row["read_status"] for row in manifest})
    checks["manifest_statuses_allowlisted"] = all(row["read_status"] in MANIFEST_STATUS_ALLOWLIST for row in manifest)
    checks["manifest_paths_resolve"] = all(resolve_evidence(row["evidence_path"]) for row in manifest)
    checks["inventory_paths_resolve"] = all(resolve_evidence(row["evidence_path"]) for row in inventory)
    checks["deep_repository_count"] = len(deep)
    checks["full_relevant_repository_count"] = sum(row["read_status"] == "FULL_RELEVANT_REPO_SOURCE_READ" for row in deep)
    checks["target_files_repository_count"] = sum(row["read_status"] == "TARGET_FILES_READ" for row in deep)
    checks["files_fully_read_count"] = sum(row["files_actually_read_count"] for row in deep)
    checks["deep_read_error_count"] = sum(len(row["read_errors"]) for row in deep)
    checks["all_deep_commits_40_hex"] = all(HEX40.fullmatch(row["fixed_commit_sha"]) for row in deep)
    checks["all_method_commits_40_hex"] = all(HEX40.fullmatch(row["commit_sha"]) for row in methods)
    checks["full_rows_have_complete_selection_and_no_errors"] = all(
        row["relevant_source_selection_coverage"] == 1.0 and not row["read_errors"]
        for row in deep if row["read_status"] == "FULL_RELEVANT_REPO_SOURCE_READ"
    )
    checks["all_deep_files_lists_nonempty"] = all(row["files_actually_read"] for row in deep)
    checks["official_start_repo_present_and_full"] = any(
        row["repo"] == "royerlab/kaggle-cell-tracking-competition"
        and row["read_status"] == "FULL_RELEVANT_REPO_SOURCE_READ"
        for row in deep
    )
    checks["alias_11_equal"] = (ROOT / "11_github_repository_inventory.csv").read_bytes() == (ROOT / "github_repository_inventory.csv").read_bytes()
    checks["alias_12_equal"] = (ROOT / "12_github_deep_read.md").read_bytes() == (ROOT / "github_deep_read.md").read_bytes()
    checks["alias_13_equal"] = (ROOT / "13_github_code_method_matrix.csv").read_bytes() == (ROOT / "github_code_method_matrix.csv").read_bytes()
    checks["alias_manifest_equal"] = (ROOT / "00_source_manifest.github_fragment.jsonl").read_bytes() == (ROOT / "source_manifest.github.jsonl").read_bytes()
    checks["alias_claims_equal"] = (ROOT / "19_claims_evidence_matrix.github_fragment.csv").read_bytes() == (ROOT / "claims_evidence_matrix.github.csv").read_bytes()
    checks["alias_query_equal"] = (ROOT / "21_search_query_log.github_fragment.csv").read_bytes() == (ROOT / "search_query_log.github.csv").read_bytes()

    boolean_checks = {key: value for key, value in checks.items() if isinstance(value, bool)}
    passed = all(boolean_checks.values()) and len(inventory) == 195 and len(methods) == 19 and len(manifest) == 64 and checks["full_relevant_repository_count"] >= 15
    artifact_hashes = {}
    for name in [
        "00_source_manifest.github_fragment.jsonl", "11_github_repository_inventory.csv",
        "12_github_deep_read.md", "13_github_code_method_matrix.csv",
        "19_claims_evidence_matrix.github_fragment.csv", "20_access_failures.github_fragment.md",
        "21_search_query_log.github_fragment.csv",
    ]:
        data = (ROOT / name).read_bytes()
        artifact_hashes[name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    receipt = {
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if passed else "FAIL",
        "checks": checks,
        "artifact_hashes": artifact_hashes,
        "scope": "github_ecosystem staging only; no runtime/training/submission verification",
    }
    (ROOT / "github_ecosystem_verification.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, ensure_ascii=False))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
