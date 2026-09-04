#!/usr/bin/env python3
"""Deterministically verify the V20A hard-stop evidence and GitHub delivery."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


TASK_ID = "CODEX_20260904_BIOHUB_V20A_SAFE_DIV_RADIUS"
DOMAIN_STATUS = "BLOCKED_INSUFFICIENT_EMBRYO_GROUPS"
BASE_COMMIT = "f4af9bc5bbdf79e478e1ccba9897c632fd68c659"
CONTRACT_SHA256 = "85f78b97015fa2d16cf4ab8fa6c8526fe8cc302da81d215a886940316daa3c68"
INVENTORY_SHA256 = "0696842719c579bab6afb4dacd5982ac185dd2a5642cf48facfe25128da7360a"
SPLIT_JSON_SHA256 = "9185ef6812363d82bfc20a694f9de27cee00a5901071e0684c053bc7de004de8"
SPLIT_CSV_SHA256 = "9b78064ee23c5d557df6549adda241180dd23b71a30434dfc99777c4558d132e"
COMPETITION_FILE_METADATA_SHA256 = (
    "260313bb5f12accebd9a70c0b0be43c659090de81f1839c7d06971b11bde3dc6"
)
SCORER_COMMIT = "075fc5f5a52d11077f9dc2b074644618f26939e2"
REPORT_MD = "reports/20260904_BIOHUB_V20A_SAFE_DIV_RADIUS_OPTIMIZATION_REPORT_V01.md"
REPORT_HTML = "reports/20260904_BIOHUB_V20A_SAFE_DIV_RADIUS_OPTIMIZATION_REPORT_V01.html"
REPORT_ARTIFACT = (
    "reports/20260904_BIOHUB_V20A_SAFE_DIV_RADIUS_OPTIMIZATION_REPORT_V01.artifact.json"
)
VERIFY_REPORT = "reports/20260904_BIOHUB_V20A_SAFE_DIV_RADIUS_OPTIMIZATION_VERIFY.json"

READ_SCOPE_HASHES = {
    "AGENTS.md": "3d93338818c2e4ecbaad66a77abc47b9512c0e19fecdf0499868e11a27cdadcf",
    "governance/CURRENT_PROJECT_CONTEXT.json": "6a9b84bacbb52b9128d98856d3573342f8f5e44d4fa39477375d41e93829ecfc",
    "reports/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_REPORT_V01.md": "a4033313b87e0a6b1876e17996f484a61637b4696c59967a552267d7336013a1",
    "research/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_V01/05_optimization_opportunities.csv": "45ddae00221d71719a04c8ff9bca0c996875e0987ddf011cc76209cdb02a1368",
    "research/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_V01/06_prioritized_optimization_plan.md": "0703866348c15ea947df272caa493bc1fd0dc7b5cb602aa0054abf24570e8246",
    "research/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_V01/07_risks_and_unknowns.md": "51982a4baedab1a8d5c5bbe058e4a0452ef901f4e53b60324e4b6b058e160373",
    "research/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_V01/audit_summary.json": "327d9a368d99076c8fcd216df299f1f323a81e4b3d71d723081095949dd4ece3",
    "research/20260904_BIOHUB_V19C_COPY_AUDIT_V01/evidence/validator_results.csv": "ca444b158cb19f8dfc182e38fcd3aab7f2a05eb81d7fa52399ba0eeda5b303fe",
    "research/20260904_BIOHUB_V19C_COPY_AUDIT_V01/evidence/bidirectional_production_runtime_integrity.json": "ae41130ee035d3ddcbaf2d0977f721429a52ffda8133fe1b877f51de5926278d",
    "research/20260904_BIOHUB_V19C_COPY_AUDIT_V01/evidence/dual_seed_frame_retention_guard_report.json": "b5d3c53c932fe5811fadd190695b1dc3313248840b23b358b02b67d2969218b2",
    "research/20260904_BIOHUB_V19C_COPY_AUDIT_V01/evidence/run_stats.csv": "469016975e85dc954275241ce3a5f363d47abe78f661a59ba564911c69cd8adf",
    "research/20260904_BIOHUB_V19C_COPY_AUDIT_V01/00_source_manifest.jsonl": "315b7fc77cec3c4058d5c8381dcc19e3431399175f99cc52e25eb4d0f2d91c90",
    "research/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_V01/00_source_manifest.jsonl": "718e95da10d4170aac29dff93ec514f47966be0191faf923d3ff08041a332c4c",
}

ZERO_LEDGER_KEYS = (
    "dataset_create_or_update",
    "model_create_or_update",
    "notebook_create",
    "save_kernel",
    "notebook_run",
    "competition_submit",
    "retry",
    "duplicate_submit",
    "cancel",
    "delete",
    "submission_status_poll",
    "unauthorized_kaggle_write",
)

SECRET_PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "signed_url": re.compile(r"X-Amz-(?:Credential|Signature)="),
    "bearer_token": re.compile(r"Bearer\s+[A-Za-z0-9._~-]{20,}"),
    "kaggle_key": re.compile(r'"key"\s*:\s*"[0-9a-fA-F]{32,}"'),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} is not a JSON object")
    return value


def run(argv: list[str], cwd: Path, *, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        argv,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {argv!r}\n"
            + result.stderr.decode("utf-8", errors="replace")
        )
    return result


class Checks:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    def add(self, check_id: str, passed: bool, detail: Any) -> None:
        self.rows.append(
            {"id": check_id, "status": "PASS" if passed else "FAIL", "detail": detail}
        )

    def require(self, check_id: str, condition: bool, detail: Any) -> None:
        self.add(check_id, bool(condition), detail)

    @property
    def failed(self) -> int:
        return sum(row["status"] != "PASS" for row in self.rows)

    @property
    def passed(self) -> int:
        return sum(row["status"] == "PASS" for row in self.rows)


def check_read_scope(root: Path, checks: Checks) -> None:
    mismatches = []
    for rel, expected in READ_SCOPE_HASHES.items():
        path = root / rel
        actual = sha256_file(path) if path.is_file() else None
        if actual != expected:
            mismatches.append({"path": rel, "expected": expected, "actual": actual})
    checks.require("fixed_read_scope_hashes", not mismatches, mismatches or "13/13 match")


def check_contract_and_freeze(root: Path, checks: Checks) -> None:
    contract = root / "experiments/V20A/contract.json"
    checks.require(
        "contract_sha256",
        contract.is_file() and sha256_file(contract) == CONTRACT_SHA256,
        sha256_file(contract) if contract.is_file() else "missing",
    )
    receipt = load_json(root / "experiments/V20A/contract_freeze_receipt.json")
    checks.require(
        "contract_pre_run_freeze",
        receipt.get("contract_sha256") == CONTRACT_SHA256
        and receipt.get("candidate_run_count_before_freeze") == 0
        and receipt.get("kaggle_write_count_before_freeze") == 0,
        receipt,
    )
    state_path = root / f".task-verification/{TASK_ID}/state.json"
    state = load_json(state_path) if state_path.is_file() else {}
    checks.require(
        "independent_prepare_state",
        state.get("contract_sha256") == CONTRACT_SHA256
        and state.get("task_id") == TASK_ID,
        {"status": state.get("status"), "contract_sha256": state.get("contract_sha256")},
    )


def check_inventory_and_split(root: Path, checks: Checks) -> None:
    exp = root / "experiments/V20A"
    inventory_path = exp / "frozen_embryo_inventory.csv"
    split_csv_path = exp / "frozen_split.csv"
    split_json_path = exp / "frozen_split.json"
    with inventory_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    eligible = [
        row
        for row in rows
        if row.get("included_in_frozen_inventory") == "true"
        and row.get("official_scorer_eligibility") == "ELIGIBLE_METADATA_SCHEMA_PRESENT"
    ]
    groups = Counter(row["embryo_group"] for row in eligible)
    inventory_ok = (
        sha256_file(inventory_path) == INVENTORY_SHA256
        and len(rows) == 199
        and len(eligible) == 199
        and groups == Counter({"44b6": 71, "6bba": 128})
        and all(row.get("required_metadata_paths_present") == "true" for row in eligible)
    )
    checks.require(
        "full_train_inventory",
        inventory_ok,
        {"rows": len(rows), "eligible": len(eligible), "groups": dict(groups)},
    )

    split = load_json(split_json_path)
    split_ok = (
        sha256_file(split_json_path) == SPLIT_JSON_SHA256
        and sha256_file(split_csv_path) == SPLIT_CSV_SHA256
        and split.get("status") == DOMAIN_STATUS
        and split.get("effective_embryo_group_count") == 2
        and split.get("fold_count") is None
        and split.get("folds") == []
        and split.get("candidate_runs_allowed") is False
        and split.get("kaggle_submission_allowed") is False
        and split.get("test_identity_used_for_split") is False
    )
    checks.require("frozen_split_hard_stop", split_ok, split)
    with split_csv_path.open(newline="", encoding="utf-8") as handle:
        split_rows = list(csv.DictReader(handle))
    assignment_ok = len(split_rows) == 199 and all(
        row.get("fold") == "NOT_ASSIGNED"
        and row.get("assignment_status") == DOMAIN_STATUS
        for row in split_rows
    )
    checks.require("no_fold_assignments", assignment_ok, f"rows={len(split_rows)}")

    receipt = load_json(exp / "competition_file_inventory_receipt.json")
    receipt_ok = (
        receipt.get("unique_file_metadata_rows") == 24886
        and receipt.get("pages_read") == 125
        and receipt.get("eligible_train_stem_count") == 199
        and receipt.get("embryo_group_count") == 2
        and receipt.get("canonical_file_metadata_sha256")
        == COMPETITION_FILE_METADATA_SHA256
        and receipt.get("image_or_geff_payload_download_count") == 0
        and receipt.get("raw_payload_persisted") is False
    )
    checks.require("competition_inventory_receipt", receipt_ok, receipt)


def check_identities(root: Path, checks: Checks) -> None:
    exp = root / "experiments/V20A"
    scorer = load_json(exp / "scorer_identity.json")
    scorer_ok = (
        scorer.get("commit") == SCORER_COMMIT
        and scorer.get("cli_summary_output_precision", {}).get("format") == ".4f"
        and scorer.get("cli_summary_output_precision", {}).get(
            "maximum_comparison_tolerance"
        )
        == 0.0001
    )
    checks.require("official_scorer_identity", scorer_ok, scorer)

    inputs = load_json(exp / "input_dataset_identities.json")
    records = inputs.get("records", [])
    expected = {
        "pilkwang/biohub-deepcenter-unet3d-center-prior-v1": (
            11061989,
            5,
            "89f363d37bb6e5e710c8aeaac32d8985f9cbc49477e156732291c238b3a5638f",
        ),
        "pilkwang/biohub-temporal-unet3d-seed314159-v1": (
            11184174,
            2,
            "9bd5b1a2ae2db31d1895f69d708648afc27f973bc419bef9c1917808e65ded1a",
        ),
        "pilkwang/biohub-tracking-support-pack-50ep-v1": (
            10999845,
            10,
            "ded6cc4648111c3ca1434b9708404ffdb0083132e3e49687b69b4cf85d1e07fe",
        ),
    }
    actual = {
        row.get("ref"): (
            row.get("dataset_id"),
            row.get("current_version_number"),
            row.get("canonical_file_metadata_sha256"),
        )
        for row in records
    }
    checks.require(
        "input_dataset_identities",
        actual == expected
        and inputs.get("payload_download_count") == 0
        and inputs.get("write_count") == 0,
        actual,
    )


def check_decision_and_writes(root: Path, checks: Checks) -> None:
    exp = root / "experiments/V20A"
    decision = load_json(exp / "promotion_decision.json")
    decision_ok = (
        decision.get("decision") == DOMAIN_STATUS
        and decision.get("selected_arm") is None
        and decision.get("selected_radius_um") is None
        and decision.get("baseline_reproduction") == "NOT_RUN_HARD_GATE"
        and all(value == "NOT_RUN_HARD_GATE" for value in decision["candidate_results"].values())
        and decision.get("kaggle_notebook_version_created") is False
        and decision.get("kaggle_submission_created") is False
        and decision.get("submission_id") is None
        and decision.get("submission_public_score") is None
        and decision.get("retry_count") == 0
    )
    checks.require("promotion_decision_recomputed", decision_ok, decision)

    no_run = load_json(exp / "no_run_manifest.json")
    no_run_ok = no_run.get("status") == DOMAIN_STATUS and all(
        no_run.get("arms", {}).get(arm, {}).get("status") == "NOT_RUN_HARD_GATE"
        for arm in ("R70", "R80", "R90")
    )
    checks.require("all_arms_not_run", no_run_ok, no_run)

    ledger = load_json(exp / "platform_write_ledger.json")
    counts = ledger.get("counts", {})
    zero_ok = all(counts.get(key) == 0 for key in ZERO_LEDGER_KEYS) and ledger.get("events") == []
    checks.require("platform_zero_writes", zero_ok, counts)
    budget = load_json(exp / "write_budget.json")
    limits = budget.get("limits", {})
    budget_ok = (
        limits.get("validation_notebook_versions") == 3
        and limits.get("production_notebook_versions") == 1
        and limits.get("save_kernel_total") == 4
        and limits.get("formal_competition_submissions") == 1
        and limits.get("submission_retries") == 0
        and budget.get("conditional_authority", {}).get("writes_currently_allowed") is False
    )
    checks.require("write_budget_frozen_and_unspent", budget_ok, limits)

    forbidden_existing = []
    patterns = (
        "canonical_resolved_config_R*.json",
        "per_sample_metrics_R*.csv",
        "per_fold_metrics_R*.csv",
        "per_prefix_metrics_R*.csv",
        "division_confusion_R*.json",
        "topology_validation_R*.json",
        "runtime_receipt_R*.json",
        "artifact_manifest_R*.json",
        "paired_deltas_by_*.csv",
        "aggregate_comparison.csv",
        "kaggle_submission_receipt.json",
        "kaggle_status_history_30m.jsonl",
    )
    for pattern in patterns:
        forbidden_existing.extend(str(path.relative_to(root)) for path in exp.glob(pattern))
    checks.require(
        "forbidden_run_artifacts_absent",
        not forbidden_existing,
        forbidden_existing or "no arm/submission/poll outputs",
    )

    health = load_json(exp / "kaggle_30m_health_summary.json")
    health_ok = (
        health.get("status") == "NOT_RUN_NO_SUBMISSION"
        and health.get("poll_count") == 0
        and health.get("submission_id") is None
        and health.get("public_score") is None
        and health.get("background_monitor_process_created") is False
    )
    checks.require("monitoring_not_started", health_ok, health)


def check_reports_and_checker(root: Path, checks: Checks) -> None:
    md_path = root / REPORT_MD
    html_path = root / REPORT_HTML
    artifact_path = root / REPORT_ARTIFACT
    md = md_path.read_text(encoding="utf-8") if md_path.is_file() else ""
    html = html_path.read_text(encoding="utf-8") if html_path.is_file() else ""
    required_md = (
        DOMAIN_STATUS,
        "44b6",
        "6bba",
        "R70",
        "R80",
        "R90",
        "NOT_RUN",
        "Public Score",
        "UNKNOWN_NOT_EXPLICIT_IN_SOURCE",
    )
    checks.require(
        "markdown_report",
        len(md.encode("utf-8")) >= 9000 and all(value in md for value in required_md),
        {"bytes": len(md.encode("utf-8")), "required_terms": len(required_md)},
    )
    checks.require(
        "portable_html_report",
        len(html.encode("utf-8")) >= 50000
        and DOMAIN_STATUS in html
        and "Portable artifact delivery" in html,
        {"bytes": len(html.encode("utf-8"))},
    )
    artifact = load_json(artifact_path) if artifact_path.is_file() else {}
    artifact_ok = (
        artifact.get("surface") == "report"
        and artifact.get("manifest", {}).get("surface") == "report"
        and artifact.get("snapshot", {}).get("status") == "ready"
        and bool(artifact.get("sources"))
    )
    checks.require("canonical_report_artifact", artifact_ok, {"surface": artifact.get("surface")})

    result = run(
        [sys.executable, "experiments/V20A/verify_resolved_config.py", "--self-test"],
        root,
        check=False,
    )
    checker_ok = result.returncode == 0 and b"V20A_RESOLVED_CONFIG_SELF_TEST_PASS" in result.stdout
    checks.require(
        "resolved_config_checker_self_test",
        checker_ok,
        {
            "returncode": result.returncode,
            "stdout": result.stdout.decode("utf-8", errors="replace").strip(),
        },
    )


def relevant_delivery_files(root: Path) -> list[str]:
    result = run(
        [
            "git",
            "ls-files",
            "--",
            "experiments/V20A",
            "tasks/CODEX_20260904_BIOHUB_V20A_SAFE_DIV_RADIUS_TASK.md",
            "reports/20260904_BIOHUB_V20A_SAFE_DIV_RADIUS_OPTIMIZATION_REPORT_V01*",
            "scripts/*v20a*",
        ],
        root,
    )
    return sorted(result.stdout.decode("utf-8").splitlines())


def check_secrets(root: Path, checks: Checks) -> None:
    hits: list[dict[str, str]] = []
    paths = relevant_delivery_files(root)
    for rel in paths:
        text = (root / rel).read_text(encoding="utf-8", errors="replace")
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                hits.append({"path": rel, "pattern": name})
    checks.require("sensitive_material_scan", not hits, hits or f"{len(paths)} tracked files clean")


def check_git_lineage(root: Path, checks: Checks) -> None:
    ancestor = run(
        ["git", "merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"], root, check=False
    )
    checks.require("base_commit_ancestor", ancestor.returncode == 0, BASE_COMMIT)


def check_remote(root: Path, checks: Checks) -> dict[str, Any]:
    run(["git", "fetch", "origin", "main"], root)
    local_head = run(["git", "rev-parse", "HEAD"], root).stdout.decode().strip()
    remote_tracking = run(["git", "rev-parse", "origin/main"], root).stdout.decode().strip()
    ls_remote_text = run(
        ["git", "ls-remote", "--heads", "origin", "refs/heads/main"], root
    ).stdout.decode()
    rows = [line.split() for line in ls_remote_text.splitlines() if line.strip()]
    ls_remote_head = rows[0][0] if len(rows) == 1 else None
    ahead_behind = (
        run(["git", "rev-list", "--left-right", "--count", "HEAD...origin/main"], root)
        .stdout.decode()
        .strip()
        .split()
    )
    clean = not run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"], root
    ).stdout.strip()
    identity_ok = (
        local_head == remote_tracking == ls_remote_head
        and ahead_behind == ["0", "0"]
        and clean
    )
    checks.require(
        "git_local_remote_identity",
        identity_ok,
        {
            "local_head": local_head,
            "origin_main": remote_tracking,
            "ls_remote_main": ls_remote_head,
            "ahead_behind": ahead_behind,
            "clean": clean,
        },
    )

    mismatches = []
    files = relevant_delivery_files(root)
    for rel in files:
        local = (root / rel).read_bytes()
        head_blob = run(["git", "show", f"{local_head}:{rel}"], root).stdout
        remote_blob = run(["git", "show", f"{remote_tracking}:{rel}"], root).stdout
        if local != head_blob or local != remote_blob:
            mismatches.append(rel)
    checks.require(
        "fixed_commit_blob_readback",
        not mismatches and bool(files),
        {"files_checked": len(files), "mismatches": mismatches},
    )
    return {
        "local_head": local_head,
        "origin_main": remote_tracking,
        "ls_remote_main": ls_remote_head,
        "ahead": int(ahead_behind[0]) if len(ahead_behind) == 2 else None,
        "behind": int(ahead_behind[1]) if len(ahead_behind) == 2 else None,
        "clean": clean,
        "files_checked": len(files),
    }


def verify(root: Path, remote_readback: bool) -> dict[str, Any]:
    checks = Checks()
    remote: dict[str, Any] | None = None
    guarded = (
        check_read_scope,
        check_contract_and_freeze,
        check_inventory_and_split,
        check_identities,
        check_decision_and_writes,
        check_reports_and_checker,
        check_secrets,
        check_git_lineage,
    )
    for func in guarded:
        try:
            func(root, checks)
        except Exception as exc:  # fail closed and retain the exact failed stage
            checks.add(func.__name__, False, f"{type(exc).__name__}: {exc}")
    if remote_readback:
        try:
            remote = check_remote(root, checks)
        except Exception as exc:
            checks.add("remote_readback_exception", False, f"{type(exc).__name__}: {exc}")

    now = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")
    return {
        "schema_version": "1.0",
        "task_id": TASK_ID,
        "status": "PASS" if checks.failed == 0 else "FAIL",
        "verification_scope": (
            "LOCAL_EVIDENCE_AND_REMOTE_FIXED_COMMIT_READBACK"
            if remote_readback
            else "LOCAL_EVIDENCE_ONLY"
        ),
        "domain_status": DOMAIN_STATUS,
        "verified_at_asia_shanghai": now,
        "summary": {"passed": checks.passed, "failed": checks.failed},
        "checks": checks.rows,
        "remote": remote,
        "interpretation": (
            "PASS verifies the hard-stop evidence and delivery mechanics only; it does not "
            "verify an arm run, Kaggle runtime, submission, score, or performance gain."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--remote-readback", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    report = verify(root, args.remote_readback)
    if args.write_report:
        path = root / VERIFY_REPORT
        path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    if report["status"] == "PASS":
        print("V20A_LOCAL_EVIDENCE_PASS")
        if args.remote_readback:
            print("V20A_REMOTE_READBACK_PASS")
        print("V20A_SAFE_DIV_RADIUS_VERIFICATION_PASS")
        return 0
    print("V20A_SAFE_DIV_RADIUS_VERIFICATION_FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
