#!/usr/bin/env python3
"""Build the immutable pre-run V20B task and experiment freeze artifacts.

This script is intentionally local-only.  It reads the already audited V20A
metadata inventory and identities, validates their hashes, and creates the six
files that must be committed before any V20B arm or Kaggle write is allowed.
It never imports the Kaggle SDK and never contacts an external service.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


TASK_ID = "CODEX_20260904_BIOHUB_V20B_TWO_EMBRYO_PAIRED_RADIUS"
BASE_COMMIT = "48e54c543afaac8ef01b628c8833b89b4fa5d7bc"
BASE_SOURCE_SHA256 = "92bf632410fedc9eb7e0984a20525590b5583d5abb002d8239ff65d9f51fbf57"
V20A_INVENTORY_SHA256 = "0696842719c579bab6afb4dacd5982ac185dd2a5642cf48facfe25128da7360a"
V20A_CONTRACT_SHA256 = "85f78b97015fa2d16cf4ab8fa6c8526fe8cc302da81d215a886940316daa3c68"
FROZEN_AT = "2026-09-04T16:30:00+08:00"


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def pretty_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def read_samples(project: Path) -> tuple[list[dict[str, Any]], dict[str, int], list[str]]:
    inventory = project / "experiments/V20A/frozen_embryo_inventory.csv"
    if sha256_file(inventory) != V20A_INVENTORY_SHA256:
        raise RuntimeError("V20A inventory SHA-256 drift")
    rows = list(csv.DictReader(inventory.open(encoding="utf-8", newline="")))
    selected = [row for row in rows if row["included_in_frozen_inventory"] == "true"]
    if len(selected) != 199:
        raise RuntimeError(f"expected 199 frozen samples, found {len(selected)}")
    counts = Counter(row["embryo_group"] for row in selected)
    if dict(sorted(counts.items())) != {"44b6": 71, "6bba": 128}:
        raise RuntimeError(f"unexpected embryo counts: {dict(counts)}")
    samples = []
    for row in selected:
        stem = row["stem"]
        embryo = row["embryo_group"]
        samples.append(
            {
                "sample_id": stem,
                "embryo_id": embryo,
                "expected_image_path": f"train/{stem}.zarr",
                "expected_gt_path": f"train/{stem}.geff",
                "metadata_eligibility": row["official_scorer_eligibility"],
                "visible_test_copy": row["visible_test_copy"] == "true",
                "pre_run_payload_status": "NOT_YET_READ",
                "include_in_all_arms": True,
                "arm_symmetric_exclusion_required": True,
            }
        )
    samples.sort(key=lambda row: row["sample_id"])
    anchors = []
    for embryo in ("44b6", "6bba"):
        eligible = [
            row["sample_id"]
            for row in samples
            if row["embryo_id"] == embryo and not row["visible_test_copy"]
        ]
        if not eligible:
            raise RuntimeError(f"no non-test-copy anchor available for {embryo}")
        anchors.append(eligible[0])
    return samples, dict(sorted(counts.items())), anchors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path("."))
    args = parser.parse_args()
    project = args.project_root.resolve()

    v20a_contract_path = project / "experiments/V20A/contract.json"
    if sha256_file(v20a_contract_path) != V20A_CONTRACT_SHA256:
        raise RuntimeError("V20A contract SHA-256 drift")
    v20a = json.loads(v20a_contract_path.read_text(encoding="utf-8"))
    samples, embryo_counts, anchors = read_samples(project)
    sample_rows_sha = sha256_bytes(canonical_bytes(samples))

    read_scope = {
        "AGENTS.md": "3d93338818c2e4ecbaad66a77abc47b9512c0e19fecdf0499868e11a27cdadcf",
        "governance/CURRENT_PROJECT_CONTEXT.json": "6a9b84bacbb52b9128d98856d3573342f8f5e44d4fa39477375d41e93829ecfc",
        "reports/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_REPORT_V01.md": "a4033313b87e0a6b1876e17996f484a61637b4696c59967a552267d7336013a1",
        "reports/20260904_BIOHUB_V20A_SAFE_DIV_RADIUS_OPTIMIZATION_REPORT_V01.md": "a70e787312a497bf9f76c25f45fe7db31b1bdb0a2f98d2d84f70e8b22dad130e",
        "experiments/V20A/contract.json": V20A_CONTRACT_SHA256,
        "experiments/V20A/frozen_split.json": "9185ef6812363d82bfc20a694f9de27cee00a5901071e0684c053bc7de004de8",
        "experiments/V20A/frozen_embryo_inventory.csv": V20A_INVENTORY_SHA256,
        "experiments/V20A/promotion_decision.json": "3ca4fb98ba825454a564bc8598af87be31f1aad491d1e839b8877429dc9ed1e4",
        "experiments/V20A/safe_div_parent_radius_call_chain.md": "59976a5d2249209bf20e8e01ecb241ad577f0abe29bd66c27be98ca255505ac3",
        "experiments/V20A/verify_resolved_config.py": "65d2229ba16130db9c07e53e8173d876b7e82007ffabd29c289c184acd5e70ec",
        "research/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_V01/05_optimization_opportunities.csv": "45ddae00221d71719a04c8ff9bca0c996875e0987ddf011cc76209cdb02a1368",
        "research/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_V01/07_risks_and_unknowns.md": "51982a4baedab1a8d5c5bbe058e4a0452ef901f4e53b60324e4b6b058e160373",
        "research/20260904_BIOHUB_V19C_COPY_AUDIT_V01/evidence/validator_results.csv": "ca444b158cb19f8dfc182e38fcd3aab7f2a05eb81d7fa52399ba0eeda5b303fe",
        "research/20260904_BIOHUB_V19C_COPY_AUDIT_V01/evidence/bidirectional_production_runtime_integrity.json": "ae41130ee035d3ddcbaf2d0977f721429a52ffda8133fe1b877f51de5926278d",
        "research/20260904_BIOHUB_V19C_COPY_AUDIT_V01/evidence/dual_seed_frame_retention_guard_report.json": "b5d3c53c932fe5811fadd190695b1dc3313248840b23b358b02b67d2969218b2",
        "research/20260904_BIOHUB_V19C_COPY_AUDIT_V01/evidence/run_stats.csv": "469016975e85dc954275241ce3a5f363d47abe78f661a59ba564911c69cd8adf",
    }
    for relative, expected in read_scope.items():
        actual = sha256_file(project / relative)
        if actual != expected:
            raise RuntimeError(f"preflight read-scope SHA drift: {relative}")

    identities = json.loads(
        json.dumps(v20a["experiment_freeze"]["identities"], ensure_ascii=False)
    )
    active_parameters = json.loads(
        json.dumps(v20a["experiment_freeze"]["active_parameters"], ensure_ascii=False)
    )
    active_parameters["safe_div_parent_radius_um"] = "ARM_VALUE_ONLY"

    sample_manifest = {
        "schema_version": "1.0",
        "task_id": TASK_ID,
        "status": "FROZEN_METADATA_IDENTITY_PENDING_KAGGLE_PAYLOAD_READ",
        "frozen_at_asia_shanghai": FROZEN_AT,
        "selection_protocol": "ALL_STRUCTURALLY_ELIGIBLE_LABELED_TRAIN_SAMPLES",
        "sample_count": len(samples),
        "embryo_count": 2,
        "embryo_sample_counts": embryo_counts,
        "sample_rows_canonical_sha256": sample_rows_sha,
        "source_inventory": {
            "path": "experiments/V20A/frozen_embryo_inventory.csv",
            "sha256": V20A_INVENTORY_SHA256,
            "evidence_boundary": "HOST_CONFIRMED_METADATA_ONLY",
        },
        "anchors": {
            "selection_rule": "LEXICOGRAPHIC_FIRST_WITHIN_EMBRYO_EXCLUDING_VISIBLE_TEST_COPY",
            "outcome_data_used": False,
            "sample_ids": anchors,
        },
        "exclusion_policy": {
            "allow_only": "PAYLOAD_CORRUPT_OR_PLATFORM_UNREADABLE_BEFORE_ARM_RESULTS",
            "same_sample_excluded_from_all_arms": True,
            "single_embryo_remaining_blocks_promotion_and_submission": True,
            "silent_exclusion_forbidden": True,
        },
        "samples": samples,
    }

    write_budget = {
        "schema_version": "1.0",
        "task_id": TASK_ID,
        "status": "FROZEN_UNUSED",
        "limits": {
            "validation_save_kernel": 1,
            "production_save_kernel": 1,
            "save_kernel_total": 2,
            "notebook_runs_total": 2,
            "formal_competition_submission": 1,
            "retry": 0,
            "duplicate_submission": 0,
            "dataset_write": 0,
            "model_write": 0,
        },
        "conditional_rules": {
            "production_and_submission_allowed_decisions": [
                "PROMOTE_R80_FOR_KAGGLE_TEST",
                "PROMOTE_R90_FOR_KAGGLE_TEST",
            ],
            "no_unique_candidate_means_production_and_submission_zero": True,
            "any_platform_write_error_means_no_retry": True,
        },
        "monitoring": {
            "maximum_minutes_after_submission_id": 30,
            "suggested_offsets_minutes": [0, 5, 10, 15, 20, 25, 30],
            "background_sleep_or_cron": False,
            "future_score_read_requires_explicit_user_request": True,
        },
    }

    platform_ledger = {
        "schema_version": "1.0",
        "task_id": TASK_ID,
        "status": "PRE_RUN_ZERO_WRITES",
        "counts": {
            "validation_save_kernel": 0,
            "production_save_kernel": 0,
            "save_kernel_total": 0,
            "notebook_run": 0,
            "competition_submit": 0,
            "submission_status_poll": 0,
            "retry": 0,
            "duplicate_submit": 0,
            "dataset_write": 0,
            "model_write": 0,
            "unauthorized_kaggle_write": 0,
        },
        "events": [],
        "read_only_preflight": {
            "principal": "sailorren",
            "baseline_kernel_status": "KernelWorkerStatus.COMPLETE",
            "gpu_quota_used_hours": 5.55,
            "gpu_quota_remaining_hours": 24.45,
            "quota_refresh_at_utc": "2026-09-05T00:00:00Z",
            "dataset_identity_check": "PASS_UNCHANGED",
            "competition_full_metadata_refresh": "PARTIAL_READ_FAILED_SSL_EOF_AT_PAGE_31_NO_RETRY",
            "fallback_identity": "V20A_SAME_DAY_125_PAGE_24886_PATH_FREEZE",
        },
    }

    evidence_boundary = {
        "schema_version": "1.0",
        "task_id": TASK_ID,
        "experiment_label": "TWO_EMBRYO_PAIRED_SENSITIVITY_SCREEN",
        "allowed_fact_classes": [
            "OFFICIAL_FACT",
            "HOST_CONFIRMED",
            "SOURCE_CODE_VERIFIED",
            "MEASURED",
            "AUTHOR_CLAIM",
            "COMMUNITY_REPORT",
            "INFERENCE",
            "UNKNOWN",
        ],
        "historical_invariants": {
            "v20a_domain_status": "BLOCKED_INSUFFICIENT_EMBRYO_GROUPS",
            "v20a_arm_statuses": {
                "R70": "NOT_RUN_HARD_GATE",
                "R80": "NOT_RUN_HARD_GATE",
                "R90": "NOT_RUN_HARD_GATE",
            },
            "v20a_files_must_not_be_modified": True,
            "v20b_is_new_contract_not_v20a_backfill": True,
        },
        "biological_independence": {
            "independent_embryo_strata": ["44b6", "6bba"],
            "field_of_view_count_is_not_embryo_count": True,
            "multi_fold_cv_claim_allowed": False,
            "sample_level_significance_for_cross_embryo_generalization_allowed": False,
            "sample_independence_claim_allowed": False,
        },
        "checkpoint_overlap": {
            "status": "CHECKPOINT_TRAINING_OVERLAP_UNKNOWN",
            "must_remain_explicit": True,
        },
        "offline_result_scope": "KAGGLE_TEST_CANDIDATE_SELECTION_ONLY",
        "hidden_test_gain_evidence": "NEW_KAGGLE_SUBMISSION_PUBLIC_SCORE_ONLY",
        "score_prediction_allowed": False,
        "historical_other_notebook_submission_56002593": "OUT_OF_SCOPE_NOT_V20B_EVIDENCE",
        "delivery_completion_is_performance_improvement": False,
    }

    contract = {
        "schema_version": "1.0",
        "task_id": TASK_ID,
        "goal": (
            "Run the preregistered R70/R80/R90 safe-division parent-radius-only "
            "screen on both labeled embryos with one shared post-gap pre-division "
            "cache, promote only a unique rule-compliant Kaggle test candidate, "
            "and conditionally create at most one production version and one submission."
        ),
        "scope": {
            "in_scope": [
                "Freeze and validate all 199 labeled train sample identities",
                "One validation Notebook Version with full payload read and shared upstream cache",
                "R70=7.0, R80=8.0, R90=9.0 with parent radius as the sole algorithm variable",
                "Two-embryo per-stratum, embryo-equal macro, pooled micro and paired-sample metrics",
                "Anchor full-run/cache equivalence and repeated-R70 determinism checks",
                "Conditional one production Notebook Version and one formal competition submission",
                "At most 30 minutes of post-submission health monitoring",
                "Reports, deterministic verification, GitHub push and authoritative blob readback",
            ],
            "out_of_scope": [
                "Training or fine-tuning",
                "Checkpoint replacement",
                "Any non-radius algorithm change",
                "Sample or embryo identity special cases",
                "Sample-level significance claims or CV claims",
                "Kaggle Dataset or Model writes",
                "Any retry or duplicate submission",
                "Waiting about ten hours for a Public Score",
                "Publishing raw data, weights, submission.csv, credentials or unlicensed full source to GitHub",
            ],
        },
        "freeze": {"require_git_tracked": True},
        "authorization": {
            "source": "user_attachment_d4ef009e-1c3b-4635-8c72-03c28a078eac",
            "notebook_write": "CONDITIONALLY_AUTHORIZED_WITHIN_FROZEN_BUDGET",
            "competition_submission": "AUTHORIZED_ONLY_AFTER_UNIQUE_OFFLINE_WINNER",
            "training": False,
            "dataset_write": False,
            "model_write": False,
        },
        "experiment_freeze": {
            "base_git": {
                "repository": "SailorRen/Biohub-CELL",
                "branch": "main",
                "commit": BASE_COMMIT,
                "task_branch": "codex/biohub-v20b-two-embryo-radius-20260904",
            },
            "baseline": {
                "competition": "biohub-cell-tracking-during-development",
                "notebook_ref": "sailorren/biohub-v19c-public0939-sis14-only",
                "version_number": 1,
                "script_version_id": 346969653,
                "submission_id": 55978992,
                "historical_public_score": 0.939,
                "score_scope": "OBSERVED_HISTORICAL_PUBLIC_SCORE_ONLY",
            },
            "identities": identities,
            "active_parameters": active_parameters,
            "arms": {
                "R70": {"safe_div_parent_radius_um": 7.0, "role": "control"},
                "R80": {"safe_div_parent_radius_um": 8.0, "role": "candidate"},
                "R90": {"safe_div_parent_radius_um": 9.0, "role": "candidate"},
            },
            "sample_manifest": {
                "path": "experiments/V20B/sample_manifest.json",
                "sample_count": 199,
                "embryo_sample_counts": embryo_counts,
                "sample_rows_canonical_sha256": sample_rows_sha,
                "anchor_sample_ids": anchors,
            },
            "cache_boundary": {
                "single_execution_stages": [
                    "detection",
                    "association",
                    "ILP",
                    "edge_filter",
                    "motion_relink",
                    "single_parent_repair",
                    "single_frame_gap",
                    "gap2_recovery",
                ],
                "cache_capture_point": "AFTER_GAP2_BEFORE_ADD_SAFE_DIVISIONS_POSTLINK",
                "same_cache_sha_required_for_all_arms": True,
                "cache_content": ["canonical nodes", "canonical edges", "pre-division stats"],
            },
            "comparison_tolerances": {
                "reported_score_absolute": 0.0001,
                "strict_positive_epsilon": 1e-12,
                "graph_coordinate_absolute": 1e-9,
                "runtime_equivalence_relative": 0.20,
                "material_embryo_division_jaccard_drop": 0.0001,
                "material_frame_cap_saturation_rate_increase": 0.005,
            },
            "determinism": {
                "global_random_seed_status": "UNKNOWN_NOT_EXPLICIT_IN_SOURCE",
                "r70_anchor_upstream_repetitions": 2,
                "exact_pre_division_topology_required": True,
                "shared_cache_required_if_upstream_repeat_drifts": True,
                "unexplained_drift_decision": "BLOCKED_RUNTIME_NONDETERMINISM",
            },
            "runtime_budget": {
                "validation_wall_clock_seconds_max": 39600,
                "production_wall_clock_seconds_max": 2700,
                "all_199_samples_preferred_and_required_unless_symmetric_payload_exclusion": True,
                "minimum_embryos_after_exclusion": 2,
            },
            "promotion_rule": {
                "screen_name": "TWO_EMBRYO_PAIRED_SENSITIVITY_SCREEN",
                "candidate_order": ["R80", "R90"],
                "required_gates": [
                    "each embryo official score noninferior to R70 within 0.0001",
                    "at least one embryo official score strictly improves",
                    "embryo-equal macro official score strictly improves",
                    "pooled micro official score is noninferior to R70 within 0.0001",
                    "pooled division Jaccard strictly improves",
                    "no embryo division Jaccard materially declines beyond 0.0001",
                    "division FP increase is compensated by new TP and official total gain",
                    "all topology and schema checks pass",
                    "cap saturation does not materially worsen",
                    "node-count penalty has no unexplained degradation",
                    "benefit is not entirely driven by one sample",
                    "all source/cache/checkpoint/input/support/scorer identities match",
                    "only parent radius differs",
                    "runtime is within frozen budget",
                ],
                "tie_break_order": [
                    "maximin embryo official-score delta",
                    "embryo-equal macro delta",
                    "pooled micro delta",
                    "pooled division Jaccard",
                    "fewer added division false positives",
                    "lower cap saturation",
                    "shorter runtime",
                ],
                "allowed_decisions": [
                    "PROMOTE_R80_FOR_KAGGLE_TEST",
                    "PROMOTE_R90_FOR_KAGGLE_TEST",
                    "NO_PROMOTION_KEEP_V19C_R70",
                    "NO_UNIQUE_WINNER_NO_SUBMISSION",
                    "BLOCKED_BASELINE_REPRODUCTION",
                    "BLOCKED_VALIDATION_PAYLOAD_OR_RUNTIME",
                    "BLOCKED_CACHE_EQUIVALENCE",
                    "BLOCKED_RUNTIME_NONDETERMINISM",
                    "BLOCKED_CONFIG_IDENTITY",
                    "BLOCKED_PLATFORM_ERROR",
                ],
            },
            "write_budget_path": "experiments/V20B/write_budget.json",
            "platform_write_ledger_path": "experiments/V20B/platform_write_ledger.json",
            "submission_monitor_minutes": 30,
            "wait_for_public_score": False,
            "future_score_read_requires_explicit_user_request": True,
            "read_scope_sha256": read_scope,
        },
        "acceptance": [
            {
                "id": "task-record",
                "type": "file",
                "required": True,
                "path": "tasks/CODEX_20260904_BIOHUB_V20B_TWO_EMBRYO_PAIRED_RADIUS_TASK.md",
                "min_bytes": 4000,
                "contains_all": [
                    TASK_ID,
                    "TWO_EMBRYO_PAIRED_SENSITIVITY_SCREEN",
                    "CHECKPOINT_TRAINING_OVERLAP_UNKNOWN",
                    "BLOCKED_INSUFFICIENT_EMBRYO_GROUPS",
                ],
            },
            {
                "id": "sample-manifest",
                "type": "json",
                "required": True,
                "path": "experiments/V20B/sample_manifest.json",
                "assertions": [
                    {"pointer": "/sample_count", "op": "equals", "value": 199},
                    {"pointer": "/embryo_count", "op": "equals", "value": 2},
                    {"pointer": "/sample_rows_canonical_sha256", "op": "equals", "value": sample_rows_sha},
                ],
            },
            {
                "id": "evidence-boundary",
                "type": "json",
                "required": True,
                "path": "experiments/V20B/evidence_boundary.json",
                "assertions": [
                    {"pointer": "/experiment_label", "op": "equals", "value": "TWO_EMBRYO_PAIRED_SENSITIVITY_SCREEN"},
                    {"pointer": "/checkpoint_overlap/status", "op": "equals", "value": "CHECKPOINT_TRAINING_OVERLAP_UNKNOWN"},
                    {"pointer": "/historical_invariants/v20a_domain_status", "op": "equals", "value": "BLOCKED_INSUFFICIENT_EMBRYO_GROUPS"},
                ],
            },
            {
                "id": "write-budget",
                "type": "json",
                "required": True,
                "path": "experiments/V20B/write_budget.json",
                "assertions": [
                    {"pointer": "/limits/save_kernel_total", "op": "equals", "value": 2},
                    {"pointer": "/limits/formal_competition_submission", "op": "equals", "value": 1},
                    {"pointer": "/limits/retry", "op": "equals", "value": 0},
                    {"pointer": "/limits/dataset_write", "op": "equals", "value": 0},
                    {"pointer": "/limits/model_write", "op": "equals", "value": 0},
                ],
            },
            {
                "id": "resolved-config-checker-self-test",
                "type": "command",
                "required": True,
                "argv": ["python3", "-B", "experiments/V20B/verify_resolved_config.py", "--self-test"],
                "cwd": ".",
                "expected_exit": 0,
                "stdout_contains_all": ["V20B_RESOLVED_CONFIG_SELF_TEST_PASS"],
                "timeout_seconds": 120,
            },
            {
                "id": "v20b-domain-verifier",
                "type": "command",
                "required": True,
                "argv": ["python3", "-B", "scripts/verify_v20b_two_embryo_radius.py", "--project-root", ".", "--verify-only"],
                "cwd": ".",
                "expected_exit": 0,
                "stdout_contains_all": ["V20B_LOCAL_EVIDENCE_PASS", "V20B_TWO_EMBRYO_RADIUS_VERIFICATION_PASS"],
                "timeout_seconds": 600,
            },
            {
                "id": "v20a-history-regression",
                "type": "command",
                "required": True,
                "argv": ["python3", "scripts/verify_v20a_safe_div_radius.py", "--project-root", ".", "--verify-only"],
                "cwd": ".",
                "expected_exit": 0,
                "stdout_contains_all": ["V20A_LOCAL_EVIDENCE_PASS", "V20A_SAFE_DIV_RADIUS_VERIFICATION_PASS"],
                "timeout_seconds": 300,
            },
            {
                "id": "final-report",
                "type": "file",
                "required": True,
                "path": "reports/20260904_BIOHUB_V20B_TWO_EMBRYO_PAIRED_RADIUS_REPORT_V01.md",
                "min_bytes": 8000,
                "contains_all": [
                    "最终领域状态",
                    "44b6",
                    "6bba",
                    "R70",
                    "R80",
                    "R90",
                    "Public Score",
                    "CHECKPOINT_TRAINING_OVERLAP_UNKNOWN",
                ],
            },
            {
                "id": "final-html-report",
                "type": "file",
                "required": True,
                "path": "reports/20260904_BIOHUB_V20B_TWO_EMBRYO_PAIRED_RADIUS_REPORT_V01.html",
                "min_bytes": 10000,
                "contains_all": ["Biohub V20B", "TWO_EMBRYO_PAIRED_SENSITIVITY_SCREEN"],
            },
            {
                "id": "final-verification-receipt",
                "type": "json",
                "required": True,
                "path": "reports/20260904_BIOHUB_V20B_TWO_EMBRYO_PAIRED_RADIUS_VERIFY.json",
                "assertions": [
                    {"pointer": "/status", "op": "not_empty"},
                    {"pointer": "/domain_status", "op": "not_empty"},
                    {"pointer": "/summary/failed", "op": "equals", "value": 0},
                ],
            },
            {
                "id": "git-clean-and-remote-head",
                "type": "git",
                "required": True,
                "repository": ".",
                "require_commit": True,
                "require_clean": True,
                "require_remote": True,
                "remote": "origin",
                "require_remote_head": True,
            },
        ],
    }

    task_markdown = f"""# Biohub-CELL V20B 两胚胎配对 safe-div parent radius 任务

任务 ID：`{TASK_ID}`  
冻结时间：{FROZEN_AT}  
固定起点：`main@{BASE_COMMIT}`  
任务分支：`codex/biohub-v20b-two-embryo-radius-20260904`

## 目标与结论边界

本任务执行 R70/R80/R90 三个 safe-division parent radius 单变量 arm，并以
`TWO_EMBRYO_PAIRED_SENSITIVITY_SCREEN` 的证据等级报告 44b6 与 6bba 两个
embryo 的方向一致性。它不是 multi-fold CV、3-fold CV 或 5-fold CV；199 个
field of view 不是 199 个独立 embryo，也不允许用 sample-level 显著性检验
宣称跨胚胎泛化。checkpoint 训练 split 未闭合，整个任务持续保留
`CHECKPOINT_TRAINING_OVERLAP_UNKNOWN`。

V20A 历史不得改写：最终状态继续是
`BLOCKED_INSUFFICIENT_EMBRYO_GROUPS`，R70/R80/R90 继续全部为
`NOT_RUN_HARD_GATE`。V20B 是新合同，不是 V20A 回填。

## 固定基线与身份

- Notebook：`sailorren/biohub-v19c-public0939-sis14-only`
- Version 1 / ScriptVersionId `346969653`
- baseline submission `55978992`
- 历史 Public Score `0.939`（只绑定该 submission）
- V19C source SHA-256 `{BASE_SOURCE_SHA256}`
- primary checkpoint `12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771`
- secondary checkpoint `9bac2fa0dadc4a6fc1899e0caf187f4b553e0a7cd90ba1261a68b35ffe9e305f`
- DeepCenter checkpoint `8040999a92f6b7bbd98fa8cf458141e045c0f9ad7c936bdb3b18e1f7edafe2a0`
- support-code manifest `978b626d1fd1e7397435a437dfe68691defe1572fc3c20e61012d7c9b52ed029`
- scorer `royerlab/kaggle-cell-tracking-competition@075fc5f5a52d11077f9dc2b074644618f26939e2`

## 样本与 cache 协议

首选且默认要求为全部 199 个 labeled train samples：44b6=71、6bba=128。
Kaggle runtime 必须实际打开每个 image/Zarr、GT GEFF 和 scorer 所需 metadata，
逐样本记录状态。损坏或不可读样本不得静默删除，并须从三臂对称排除；若只剩
一个 embryo，立即 `BLOCKED_VALIDATION_PAYLOAD_OR_RUNTIME`。

固定 anchor 由“不使用结果、每 embryo 内排除 visible test copy 后字典序第一”
选出：`{anchors[0]}` 与 `{anchors[1]}`。detection、association、ILP、edge
filter、motion relink、single-parent repair、single-frame gap 与 gap2 只运行一次；
canonical cache 精确切在 `AFTER_GAP2_BEFORE_ADD_SAFE_DIVISIONS_POSTLINK`。
三臂必须引用同一 cache SHA。每个 anchor 对三臂分别执行 full-path 与 cached
downstream 等价性检查，并在 R70 重复上游运行以检查未显式 seed 的确定性。

## 三个 arm 与唯一变量

- R70：`BIOHUB_SAFE_DIV_MAX_UM=7.0`
- R80：`BIOHUB_SAFE_DIV_MAX_UM=8.0`
- R90：`BIOHUB_SAFE_DIV_MAX_UM=9.0`

除 `safe_div_parent_radius_um` 外，source、checkpoint、support code、input、
scorer 和所有 active parameters 必须逐项一致。cross-arm checker 或 cache
equivalence 任一失败即停止，不得晋升或提交。

## 指标与晋升

每个 sample、每个 embryo、embryo-equal macro 与 pooled micro 都必须报告
official total、adjusted edge、division Jaccard、TP/FP/FN、node-count penalty、
predicted/estimated nodes、错误分解、safe-div/DeepCenter/cap/topology/schema、
runtime、peak memory、cache SHA 与输出 SHA。候选需同时满足两个 embryo 非劣、
至少一个严格改善、macro 严格改善、micro 非劣、pooled division Jaccard 改善，
并通过全部风险门。若两候选都通过，严格按合同 tie-break 形成唯一胜者；仍相同
则 `NO_UNIQUE_WINNER_NO_SUBMISSION`。

离线晋升只能称为 “Kaggle test candidate”，不能称为已证明提分、预计高于
0.939 或新最佳方案。最终提分证据只能来自新的具体 Kaggle submission Public
Score。

## 外部写入预算与停止条件

用户本任务仅在上述门禁内授权：validation SaveKernel<=1、production
SaveKernel<=1、SaveKernel total<=2、formal submission<=1；retry=0、duplicate=0、
Dataset/Model write=0。没有唯一候选时 production 和 submission 必须为 0；任一
平台写错误不得自动重试。

提交后从 submission ID 创建成功起最多监控 30 分钟；不使用后台 sleep、cron
或长期轮询，不等待约 10 小时后的分数。30 分钟后必须停止，并等待用户显式通知
后才可再次读取分数。

## 完成证据

完成声明要求：合同先于 arm 冻结并提交；sample payload 状态齐全；canonical
config、cache equivalence、determinism、promotion 重算、写入预算、秘密扫描、
Git clean、local/remote/GitHub HEAD 一致及固定 commit blob 回读全部通过。交付
`COMPLETED_VERIFIED` 只说明合同范围内的机械和证据核验，不自动等于性能提升。

## 前置实际读取与当前观测

所有固定材料已经完整读取并由 `contract.json` 的 `read_scope_sha256` 逐项冻结。
当前 principal 为 `sailorren`；CLI 权威 quota 输出为 used 5.55h、remaining
24.45h/30h。V19C 当前 `COMPLETE`。不同 Notebook 的 submission `56002593=0.940`
属于范围外历史状态，不是 V20B 基线或结果。比赛元数据刷新在第 31 页发生一次
SSL EOF，依 `retry=0` 未重试；V20B 使用同日已冻结的 125 页/24,886 路径身份，
并把 Kaggle mount 内 199/199 payload 实读作为更强的运行门。
"""

    write(
        project / "tasks/CODEX_20260904_BIOHUB_V20B_TWO_EMBRYO_PAIRED_RADIUS_TASK.md",
        task_markdown.encode("utf-8"),
    )
    out = project / "experiments/V20B"
    write(out / "contract.json", pretty_bytes(contract))
    write(out / "write_budget.json", pretty_bytes(write_budget))
    write(out / "platform_write_ledger.json", pretty_bytes(platform_ledger))
    write(out / "sample_manifest.json", pretty_bytes(sample_manifest))
    write(out / "evidence_boundary.json", pretty_bytes(evidence_boundary))
    print(
        json.dumps(
            {
                "status": "V20B_FREEZE_ARTIFACTS_BUILT",
                "task_id": TASK_ID,
                "sample_count": len(samples),
                "embryo_sample_counts": embryo_counts,
                "anchors": anchors,
                "sample_rows_canonical_sha256": sample_rows_sha,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
