#!/usr/bin/env python3
"""Deterministically verify the V20B two-embryo parent-radius experiment.

The verifier is deliberately independent from the Kaggle runtime notebook.  It
recomputes payload coverage, official metrics, paired deltas, promotion gates,
the winner tie-break, platform-write budgets, and terminal-state consistency
from the small evidence files copied into experiments/V20B.

It never contacts Kaggle and never changes Git.  The only default write is the
machine-readable verification receipt required by the frozen contract.  Report
files are read and checked, never generated unless a future explicit mode is
added.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


TASK_ID = "CODEX_20260904_BIOHUB_V20B_TWO_EMBRYO_PAIRED_RADIUS"
SCREEN_NAME = "TWO_EMBRYO_PAIRED_SENSITIVITY_SCREEN"
CONTRACT_SHA256 = "ea46844436142e61c3bc570b4e616531b69eca2cbc609935cf84ce768d41a40b"
FROZEN_SAMPLE_MANIFEST_SHA256 = (
    "7b028996131fc189f8a480b8e1c01f26f72131877758680af9ed1b7c9edce842"
)
FROZEN_EVIDENCE_BOUNDARY_SHA256 = (
    "48fc1b23c0930e05c0371d9d6d0a85dd595bb440c85b11aff5910d589c7d548f"
)
FROZEN_WRITE_BUDGET_SHA256 = (
    "2ee55ca9d1a39b077d116800f0af7240780cdc56e68d22ffb973e632f9ec8186"
)
PRODUCTION_RUNTIME_BASIS_SHA256 = (
    "cc5aeab06c29afcead83a6c79809d74eef061acb2060057c3f2f697f2af03e0c"
)
VALIDATION_BUILDER_SHA256 = (
    "5f01fed4eda31d2095f1cd5791fe2ccb1a55d149c9b54c18720051b7a154b9e3"
)
VALIDATION_NOTEBOOK_SHA256 = (
    "8bea7c6c7bdd147a116603337421a1035073679799b72991bd7b045ee245d67f"
)
VALIDATION_BUILD_MANIFEST_SHA256 = (
    "cbfbab546c56814859e4773fc8bdd7ce2ed80513bd83b4148af85464fddb00a9"
)
VALIDATION_KERNEL_METADATA_SHA256 = (
    "5efb62aa4009201d50e97a64bcc480c5d458692e46f97a28d54baf91580f267d"
)

EXPERIMENT_DIR = Path("experiments/V20B")
CONTRACT_PATH = EXPERIMENT_DIR / "contract.json"
FROZEN_SAMPLE_MANIFEST_PATH = EXPERIMENT_DIR / "sample_manifest.json"
EVIDENCE_BOUNDARY_PATH = EXPERIMENT_DIR / "evidence_boundary.json"
WRITE_BUDGET_PATH = EXPERIMENT_DIR / "write_budget.json"
PLATFORM_LEDGER_PATH = EXPERIMENT_DIR / "platform_write_ledger.json"
PAYLOAD_INVENTORY_PATH = EXPERIMENT_DIR / "full_sample_payload_inventory.csv"
FULL_SAMPLE_MANIFEST_PATH = EXPERIMENT_DIR / "full_sample_manifest.json"
PER_SAMPLE_PATH = EXPERIMENT_DIR / "per_sample_metrics.csv"
PER_EMBRYO_PATH = EXPERIMENT_DIR / "per_embryo_metrics.csv"
PAIRED_SAMPLE_PATH = EXPERIMENT_DIR / "paired_deltas_by_sample.csv"
PAIRED_EMBRYO_PATH = EXPERIMENT_DIR / "paired_deltas_by_embryo.csv"
MICRO_MACRO_PATH = EXPERIMENT_DIR / "micro_macro_comparison.csv"
DIVISION_CONFUSION_PATH = EXPERIMENT_DIR / "division_confusion_by_embryo.json"
TOPOLOGY_PATH = EXPERIMENT_DIR / "topology_validation.json"
RUNTIME_PATH = EXPERIMENT_DIR / "runtime_receipts.json"
ARTIFACT_MANIFEST_PATH = EXPERIMENT_DIR / "artifact_manifest.json"
CACHE_MANIFEST_PATH = EXPERIMENT_DIR / "cache_manifest.json"
CACHE_EQUIVALENCE_PATH = EXPERIMENT_DIR / "cache_equivalence.json"
DETERMINISM_PATH = EXPERIMENT_DIR / "runtime_determinism.json"
RESOLVED_CONFIG_VERIFICATION_PATH = EXPERIMENT_DIR / "resolved_config_verification.json"
PROMOTION_PATH = EXPERIMENT_DIR / "promotion_decision.json"
SUBMISSION_RECEIPT_PATH = EXPERIMENT_DIR / "kaggle_submission_receipt.json"
STATUS_HISTORY_PATH = EXPERIMENT_DIR / "kaggle_status_history_30m.jsonl"
HEALTH_SUMMARY_PATH = EXPERIMENT_DIR / "kaggle_30m_health_summary.json"
VALIDATION_BUILDER_PATH = Path("scripts/build_v20b_validation_notebook.py")
FINAL_REPORT_BUILDER_PATH = Path("scripts/build_v20b_final_report.py")
TASK_RECORD_PATH = Path(
    "tasks/CODEX_20260904_BIOHUB_V20B_TWO_EMBRYO_PAIRED_RADIUS_TASK.md"
)
VALIDATION_TERMINAL_RECEIPT_PATH = (
    EXPERIMENT_DIR / "kaggle_validation_terminal_receipt.json"
)
FAILURE_DIAGNOSIS_PATH = EXPERIMENT_DIR / "failure_diagnosis.json"
VALIDATION_LOG_PATH = EXPERIMENT_DIR / "kaggle_validation_v1_log.txt"

PROMOTION_EVIDENCE_PATHS = {
    str(EXPERIMENT_DIR / name)
    for name in (
        "full_sample_payload_inventory.csv",
        "full_sample_manifest.json",
        "per_sample_metrics.csv",
        "per_embryo_metrics.csv",
        "paired_deltas_by_sample.csv",
        "paired_deltas_by_embryo.csv",
        "micro_macro_comparison.csv",
        "division_confusion_by_embryo.json",
        "topology_validation.json",
        "runtime_receipts.json",
        "cache_manifest.json",
        "cache_equivalence.json",
        "runtime_determinism.json",
        "resolved_config_verification.json",
    )
}

REPORT_MD_PATH = Path(
    "reports/20260904_BIOHUB_V20B_TWO_EMBRYO_PAIRED_RADIUS_REPORT_V01.md"
)
REPORT_HTML_PATH = Path(
    "reports/20260904_BIOHUB_V20B_TWO_EMBRYO_PAIRED_RADIUS_REPORT_V01.html"
)
VERIFY_REPORT_PATH = Path(
    "reports/20260904_BIOHUB_V20B_TWO_EMBRYO_PAIRED_RADIUS_VERIFY.json"
)

ARMS: dict[str, float] = {"R70": 7.0, "R80": 8.0, "R90": 9.0}
CANDIDATES = ("R80", "R90")
EMBRYOS = ("44b6", "6bba")
EXPECTED_EMBRYO_COUNTS = {"44b6": 71, "6bba": 128}
EXPECTED_SAMPLE_COUNT = 199
ANCHORS = ("44b6_0c582fdc", "6bba_062c8d37")
VALIDATION_ROW_COLUMNS = (
    "id",
    "dataset",
    "row_type",
    "node_id",
    "t",
    "z",
    "y",
    "x",
    "source_id",
    "target_id",
)
PAYLOAD_COLUMNS = (
    "sample_id",
    "embryo_id",
    "image_path",
    "gt_path",
    "image_exists",
    "gt_exists",
    "image_readable",
    "gt_readable",
    "scorer_metadata_readable",
    "image_shape",
    "image_dtype",
    "gt_node_count",
    "gt_edge_count",
    "estimated_node_count",
    "estimated_node_count_evidence",
    "image_metadata_sha256",
    "image_tree_inventory_sha256",
    "gt_payload_sha256",
    "sample_payload_sha256",
    "status",
    "error",
)
PER_SAMPLE_COLUMNS = (
    "arm",
    "sample_id",
    "embryo_id",
    "status",
    "official_score",
    "adj_edge_jaccard",
    "edge_jaccard",
    "division_jaccard",
    "edge_tp",
    "edge_fp",
    "edge_fn",
    "division_tp",
    "division_fp",
    "division_fn",
    "num_pred_nodes",
    "gt_node_count",
    "estimated_node_count",
    "gt_node_count_evidence",
    "estimated_node_count_evidence",
    "total_node_ratio",
    "node_count_penalty",
    "node_recall",
    "edges_fragmented",
    "edges_lost_to_detection",
    "wrong_association_edges",
    "safe_div_candidate_count",
    "accepted_division_count",
    "deepcenter_accepted_count",
    "deepcenter_rejected_count",
    "frame_cap_saturation",
    "global_cap_saturation",
    "topology_valid",
    "schema_valid",
    "runtime_seconds",
    "finalize_runtime_seconds",
    "scoring_runtime_seconds",
    "total_runtime_seconds",
    "execution_order_index",
    "score_coordinate_semantics",
    "peak_memory_bytes",
    "pre_division_cache_sha256",
    "final_output_sha256",
    "scorer_input_rows_sha256",
)
PER_EMBRYO_COLUMNS = (
    "arm",
    "embryo_id",
    "status",
    "sample_count",
    "official_score",
    "adj_edge_jaccard",
    "edge_jaccard",
    "division_jaccard",
    "edge_tp",
    "edge_fp",
    "edge_fn",
    "division_tp",
    "division_fp",
    "division_fn",
    "num_pred_nodes",
    "gt_node_count",
    "estimated_node_count",
    "total_node_ratio",
    "node_count_penalty",
    "node_recall",
    "edges_fragmented",
    "edges_lost_to_detection",
    "wrong_association_edges",
    "safe_div_candidate_count",
    "accepted_division_count",
    "deepcenter_accepted_count",
    "deepcenter_rejected_count",
    "frame_cap_saturation_rate",
    "global_cap_saturation_rate",
    "frame_cap_saturation",
    "global_cap_saturation",
    "topology_valid",
    "schema_valid",
    "runtime_seconds",
    "finalize_runtime_seconds",
    "scoring_runtime_seconds",
    "total_runtime_seconds",
    "peak_memory_bytes",
    "gt_node_count_evidence",
    "estimated_node_count_evidence",
    "pre_division_cache_sha256",
    "final_output_sha256",
    "scorer_input_rows_sha256",
    "hash_aggregation",
)
PAIRED_SAMPLE_COLUMNS = (
    "candidate_arm",
    "control_arm",
    "sample_id",
    "embryo_id",
    "official_score_delta",
    "adj_edge_jaccard_delta",
    "edge_jaccard_delta",
    "division_jaccard_delta",
    "division_tp_delta",
    "division_fp_delta",
    "division_fn_delta",
    "edge_tp_delta",
    "edge_fp_delta",
    "edge_fn_delta",
    "num_pred_nodes_delta",
    "gt_node_count_delta",
    "estimated_node_count_delta",
    "total_node_ratio_delta",
    "node_count_penalty_delta",
    "node_recall_delta",
    "edges_fragmented_delta",
    "edges_lost_to_detection_delta",
    "wrong_association_edges_delta",
    "safe_div_candidate_count_delta",
    "accepted_division_count_delta",
    "deepcenter_accepted_count_delta",
    "deepcenter_rejected_count_delta",
    "frame_cap_saturation_delta",
    "global_cap_saturation_delta",
    "runtime_seconds_delta",
    "finalize_runtime_seconds_delta",
    "scoring_runtime_seconds_delta",
    "total_runtime_seconds_delta",
    "peak_memory_bytes_delta",
    "topology_both_valid",
    "schema_both_valid",
    "pre_division_cache_sha256_equal",
    "control_final_output_sha256",
    "candidate_final_output_sha256",
    "final_output_sha256_equal",
)
PAIRED_EMBRYO_COLUMNS = (
    "candidate_arm",
    "control_arm",
    "embryo_id",
    "sample_count",
    "official_score_delta",
    "adj_edge_jaccard_delta",
    "edge_jaccard_delta",
    "division_jaccard_delta",
    "division_tp_delta",
    "division_fp_delta",
    "division_fn_delta",
    "edge_tp_delta",
    "edge_fp_delta",
    "edge_fn_delta",
    "num_pred_nodes_delta",
    "gt_node_count_delta",
    "estimated_node_count_delta",
    "total_node_ratio_delta",
    "node_count_penalty_delta",
    "node_recall_delta",
    "edges_fragmented_delta",
    "edges_lost_to_detection_delta",
    "wrong_association_edges_delta",
    "safe_div_candidate_count_delta",
    "accepted_division_count_delta",
    "deepcenter_accepted_count_delta",
    "deepcenter_rejected_count_delta",
    "frame_cap_saturation_rate_delta",
    "global_cap_saturation_rate_delta",
    "runtime_seconds_delta",
    "finalize_runtime_seconds_delta",
    "scoring_runtime_seconds_delta",
    "total_runtime_seconds_delta",
    "peak_memory_bytes_delta",
    "topology_both_valid",
    "schema_both_valid",
    "pre_division_cache_sha256_equal",
    "control_final_output_sha256",
    "candidate_final_output_sha256",
    "final_output_sha256_equal",
)
MICRO_MACRO_COLUMNS = (
    "arm",
    "scope",
    "embryo_id",
    "status",
    "sample_count",
    "official_score",
    "adj_edge_jaccard",
    "edge_jaccard",
    "division_jaccard",
    "edge_tp",
    "edge_fp",
    "edge_fn",
    "division_tp",
    "division_fp",
    "division_fn",
    "node_count_penalty",
    "num_pred_nodes",
    "gt_node_count",
    "estimated_node_count",
    "gt_node_count_evidence",
    "estimated_node_count_evidence",
    "total_node_ratio",
    "node_recall",
    "edges_fragmented",
    "edges_lost_to_detection",
    "wrong_association_edges",
    "safe_div_candidate_count",
    "accepted_division_count",
    "deepcenter_accepted_count",
    "deepcenter_rejected_count",
    "frame_cap_saturation",
    "global_cap_saturation",
    "topology_valid",
    "schema_valid",
    "runtime_seconds",
    "finalize_runtime_seconds",
    "scoring_runtime_seconds",
    "total_runtime_seconds",
    "peak_memory_bytes",
    "pre_division_cache_sha256",
    "final_output_sha256",
    "hash_aggregation",
    "scorer_input_rows_sha256",
)
SCORE_COORDINATE_SEMANTICS = "ROUNDED_CLAMPED_SUBMISSION_ROWS"
SAMPLE_HASH_AGGREGATION = "ORDERED_SAMPLE_SHA_ROWS_V1"
EMBRYO_HASH_AGGREGATION = "ORDERED_EMBRYO_AGGREGATE_SHA_ROWS_V1"
RUNTIME_TIE_BREAK_DEFINITION = (
    "PURE_V20B_FINALIZE_FROM_PREDIVISION_SECONDS_EXCLUDES_SCORER_AND_ROW_AUDIT"
)
PREDICTOR_RUN_SEMANTICS = "LOGICAL_RUN_COUNT_INCREMENTED_BEFORE_FIRST_SUBPROCESS_START"
CONFIG_FAILURE_STAGES = frozenset(
    {
        "CONFIG_IDENTITY",
        "CONFIG_RECEIPTS",
        "RUNTIME_CONFIG",
        "DEPENDENCIES_AND_IDENTITIES",
    }
)

PROMOTION_DECISIONS = {
    "PROMOTE_R80_FOR_KAGGLE_TEST",
    "PROMOTE_R90_FOR_KAGGLE_TEST",
}
NO_SUBMISSION_DECISIONS = {
    "NO_PROMOTION_KEEP_V19C_R70",
    "NO_UNIQUE_WINNER_NO_SUBMISSION",
}
BLOCKED_DECISIONS = {
    "BLOCKED_BASELINE_REPRODUCTION",
    "BLOCKED_VALIDATION_PAYLOAD_OR_RUNTIME",
    "BLOCKED_CACHE_EQUIVALENCE",
    "BLOCKED_RUNTIME_NONDETERMINISM",
    "BLOCKED_CONFIG_IDENTITY",
    "BLOCKED_PLATFORM_ERROR",
}
ALLOWED_DECISIONS = PROMOTION_DECISIONS | NO_SUBMISSION_DECISIONS | BLOCKED_DECISIONS

LEDGER_COUNT_SEMANTICS = "PHYSICAL_API_CALL_COUNTED_AT_STARTED_BEFORE_INVOCATION"
LEDGER_OPERATION_COUNTERS = {
    "VALIDATION_SAVE_KERNEL": frozenset(
        {"validation_save_kernel", "save_kernel_total", "notebook_run"}
    ),
    "PRODUCTION_SAVE_KERNEL": frozenset(
        {"production_save_kernel", "save_kernel_total", "notebook_run"}
    ),
    "COMPETITION_SUBMIT": frozenset({"competition_submit"}),
    "SUBMISSION_STATUS_POLL": frozenset({"submission_status_poll"}),
}
VALIDATION_BUNDLE_PROVENANCE = {
    "validation_builder_sha256": VALIDATION_BUILDER_SHA256,
    "validation_notebook_sha256": VALIDATION_NOTEBOOK_SHA256,
    "validation_build_manifest_sha256": VALIDATION_BUILD_MANIFEST_SHA256,
    "validation_kernel_metadata_sha256": VALIDATION_KERNEL_METADATA_SHA256,
}
SUBMISSION_TERMINAL_STATUSES = {
    "COMPLETED_VERIFIED_SCORE_PENDING",
    "COMPLETED_VERIFIED_EARLY_SCORE_OBSERVED",
    "SUBMISSION_ACCEPTED_RUNTIME_UNVERIFIED_SCORE_PENDING",
    "BLOCKED_PLATFORM_ERROR",
}
SUCCESS_TEXT = {
    "PASS",
    "PASSED",
    "COMPLETE",
    "COMPLETED",
    "RUN_COMPLETE",
    "READABLE",
    "INCLUDED",
    "OK",
    "VALID",
}
TASK_STATE_ACCEPTED_STATUSES = {
    "PLANNED",
    "CLAIMED_COMPLETE",
    "VERIFYING",
    "COMPLETED_VERIFIED",
}
FAIL_TEXT = {
    "FAIL",
    "FAILED",
    "ERROR",
    "BLOCKED",
    "CORRUPT",
    "UNREADABLE",
    "EXCLUDED",
}

HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
HEX_GIT_COMMIT = re.compile(r"^[0-9a-f]{40}$")
SECRET_PATTERNS = {
    "private_key": re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.IGNORECASE
    ),
    "github_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "signed_url": re.compile(r"X-Amz-(?:Credential|Signature)=", re.IGNORECASE),
    "bearer_token": re.compile(r"\bBearer\s+[A-Za-z0-9._~-]{20,}", re.IGNORECASE),
    "jwt": re.compile(r"\beyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]*\b"),
    "kaggle_key": re.compile(r'"key"\s*:\s*"[0-9a-fA-F]{32,}"'),
    "access_token_value": re.compile(
        r'"(?:access[_-]?token|refresh[_-]?token)"\s*:\s*"[^"]+"',
        re.IGNORECASE,
    ),
    "credential_path": re.compile(
        r"(?:/Users/[^/\s]+/\.kaggle/|\\Users\\[^\\\s]+\\\.kaggle\\|kaggle\.json)",
        re.IGNORECASE,
    ),
}

RESOLVED_CONFIG_CHECKER_PATH = "experiments/V20B/verify_resolved_config.py"
RESOLVED_CONFIG_CHECKER_SHA256 = (
    "9acf46b55fe4c1601cd151c3cbb52de9a6c1e221d7cf5493342a7289b37c9121"
)
KNOWN_NEGATIVE_SELF_TEST_CREDENTIAL_FIXTURE = (
    "/Users/example/" + ".kaggle/" + "kaggle" + ".json"
)


class EvidenceError(RuntimeError):
    """Raised when evidence is missing, malformed, or internally inconsistent."""


def redact_frozen_negative_self_test_fixture(
    *, relative_path: str, file_sha256: str, text_value: str
) -> tuple[str, int]:
    """Redact one frozen negative-test literal without weakening the general scan."""
    if (
        relative_path != RESOLVED_CONFIG_CHECKER_PATH
        or file_sha256 != RESOLVED_CONFIG_CHECKER_SHA256
    ):
        return text_value, 0
    occurrence_count = text_value.count(KNOWN_NEGATIVE_SELF_TEST_CREDENTIAL_FIXTURE)
    if occurrence_count != 1:
        raise EvidenceError(
            "frozen resolved-config checker no longer has exactly one known "
            "negative self-test credential fixture"
        )
    return (
        text_value.replace(
            KNOWN_NEGATIVE_SELF_TEST_CREDENTIAL_FIXTURE,
            "<KNOWN_NEGATIVE_SELF_TEST_FIXTURE_REDACTED>",
        ),
        1,
    )


@dataclass
class StageEvidence:
    outcome: str
    detail: dict[str, Any]


class Checks:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    def add(self, check_id: str, passed: bool, detail: Any) -> None:
        self.rows.append(
            {
                "id": check_id,
                "status": "PASS" if passed else "FAIL",
                "detail": sanitise_detail(detail),
            }
        )

    def require(self, check_id: str, condition: bool, detail: Any) -> None:
        self.add(check_id, bool(condition), detail)

    @property
    def passed(self) -> int:
        return sum(row["status"] == "PASS" for row in self.rows)

    @property
    def failed(self) -> int:
        return sum(row["status"] != "PASS" for row in self.rows)


def sanitise_detail(value: Any) -> Any:
    """Keep receipts useful without copying secrets or very large payloads."""

    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in value.items():
            if re.search(
                r"(?:password|passwd|secret|credential|api[_-]?key|"
                r"access[_-]?token|refresh[_-]?token|cookie)",
                str(key),
                re.IGNORECASE,
            ):
                result[str(key)] = "<redacted>"
            else:
                result[str(key)] = sanitise_detail(child)
        return result
    if isinstance(value, list):
        if len(value) > 30:
            return [sanitise_detail(item) for item in value[:30]] + [
                f"<{len(value) - 30} more>"
            ]
        return [sanitise_detail(item) for item in value]
    if isinstance(value, str):
        text = value
        for pattern in SECRET_PATTERNS.values():
            if pattern.search(text):
                return "<redacted-sensitive-value>"
        return text if len(text) <= 1000 else text[:1000] + "<truncated>"
    return value


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path, label: str | None = None) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"cannot read {label or path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EvidenceError(f"{label or path} must contain a JSON object")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise EvidenceError(f"cannot read {path}: {exc}") from exc
    for lineno, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise EvidenceError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise EvidenceError(f"{path}:{lineno}: JSONL row is not an object")
        rows.append(value)
    return rows


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise EvidenceError(f"{path} has no CSV header")
            if len(reader.fieldnames) != len(set(reader.fieldnames)):
                raise EvidenceError(f"{path} contains duplicate CSV columns")
            rows = [dict(row) for row in reader]
    except OSError as exc:
        raise EvidenceError(f"cannot read {path}: {exc}") from exc
    return list(reader.fieldnames), rows


def require_keys(value: Mapping[str, Any], keys: Iterable[str], label: str) -> None:
    missing = sorted(set(keys) - set(value))
    if missing:
        raise EvidenceError(f"{label} missing fields: {missing}")


def require_sha256(value: Any, label: str) -> str:
    text = str(value)
    if not HEX_SHA256.fullmatch(text):
        raise EvidenceError(f"{label} is not a lowercase SHA-256")
    return text


def parse_bool(value: Any, label: str) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "pass", "passed", "valid", "ok"}:
        return True
    if text in {"false", "0", "no", "fail", "failed", "invalid"}:
        return False
    raise EvidenceError(f"{label} is not a strict boolean: {value!r}")


def parse_int(value: Any, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool):
        raise EvidenceError(f"{label} must be an integer")
    try:
        number = int(str(value))
    except (TypeError, ValueError) as exc:
        raise EvidenceError(f"{label} is not an integer: {value!r}") from exc
    if str(value).strip() not in {str(number), f"+{number}"} and not isinstance(
        value, int
    ):
        try:
            if float(str(value)) != number:
                raise EvidenceError(f"{label} is not an exact integer: {value!r}")
        except ValueError as exc:
            raise EvidenceError(f"{label} is not an integer: {value!r}") from exc
    if number < minimum:
        raise EvidenceError(f"{label} is below {minimum}: {number}")
    return number


def parse_float(
    value: Any,
    label: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
    allow_none: bool = False,
) -> float | None:
    if value is None or (
        isinstance(value, str) and value.strip().lower() in {"", "null", "none", "nan"}
    ):
        if allow_none:
            return None
        raise EvidenceError(f"{label} is missing")
    if isinstance(value, bool):
        raise EvidenceError(f"{label} must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise EvidenceError(f"{label} is not numeric: {value!r}") from exc
    if not math.isfinite(number):
        if allow_none and math.isnan(number):
            return None
        raise EvidenceError(f"{label} is not finite: {value!r}")
    if minimum is not None and number < minimum:
        raise EvidenceError(f"{label} is below {minimum}: {number}")
    if maximum is not None and number > maximum:
        raise EvidenceError(f"{label} is above {maximum}: {number}")
    return number


def first_present(row: Mapping[str, Any], aliases: Sequence[str], label: str) -> Any:
    for key in aliases:
        if key in row:
            return row[key]
    raise EvidenceError(f"{label} missing aliases {list(aliases)}")


def optional_present(
    row: Mapping[str, Any], aliases: Sequence[str], default: Any = None
) -> Any:
    for key in aliases:
        if key in row:
            return row[key]
    return default


def close_enough(actual: float, expected: float, tolerance: float) -> bool:
    return math.isclose(actual, expected, rel_tol=0.0, abs_tol=tolerance)


def status_is_success(value: Any) -> bool:
    text = str(value).strip().upper()
    return text in SUCCESS_TEXT or text.startswith(
        ("PASS_", "COMPLETE_", "RUN_COMPLETE")
    )


def status_is_failure(value: Any) -> bool:
    text = str(value).strip().upper()
    return (
        text in FAIL_TEXT
        or text.startswith(("BLOCKED_", "FAIL_", "FAILED_", "ERROR_"))
        or "FAIL_CLOSED" in text
    )


def jaccard(tp: int, fp: int, fn: int) -> float | None:
    denominator = tp + fp + fn
    return tp / denominator if denominator > 0 else None


def official_sample_metrics(
    edge_tp: int,
    edge_fp: int,
    edge_fn: int,
    division_tp: int,
    division_fp: int,
    division_fn: int,
    num_pred_nodes: int,
    estimated_node_count: float,
) -> dict[str, float | None]:
    edge = jaccard(edge_tp, edge_fp, edge_fn)
    division = jaccard(division_tp, division_fp, division_fn)
    if estimated_node_count <= 0:
        ratio = None
    else:
        ratio = (num_pred_nodes - estimated_node_count) / estimated_node_count
    adjusted = (
        max(0.0, edge * (1.0 - 0.1 * ratio))
        if edge is not None and ratio is not None
        else None
    )
    score = (
        None
        if adjusted is None
        else adjusted
        if division is None
        else adjusted + 0.1 * division
    )
    penalty = None if edge is None or adjusted is None else edge - adjusted
    return {
        "edge_jaccard": edge,
        "division_jaccard": division,
        "total_node_ratio": ratio,
        "adj_edge_jaccard": adjusted,
        "official_score": score,
        "node_count_penalty": penalty,
    }


def ordered_sample_sha256(rows: Sequence[Mapping[str, Any]], field: str) -> str:
    return canonical_sha256(
        [
            {"sample_id": str(row["sample_id"]), "sha256": row[field]}
            for row in sorted(rows, key=lambda item: str(item["sample_id"]))
        ]
    )


def ordered_embryo_sha256(
    rows: Sequence[tuple[str, Mapping[str, Any]]], field: str
) -> str:
    return canonical_sha256(
        [{"embryo_id": embryo, "sha256": row[field]} for embryo, row in rows]
    )


def aggregate_metric_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise EvidenceError("cannot aggregate an empty metric row set")
    count_fields = (
        "edge_tp",
        "edge_fp",
        "edge_fn",
        "division_tp",
        "division_fp",
        "division_fn",
        "num_pred_nodes",
        "gt_node_count",
    )
    totals = {key: sum(int(row[key]) for row in rows) for key in count_fields}
    weights = [
        int(row["edge_tp"]) + int(row["edge_fp"]) + int(row["edge_fn"]) for row in rows
    ]
    weighted_rows = [
        (weight, float(row["adj_edge_jaccard"]))
        for weight, row in zip(weights, rows)
        if row.get("adj_edge_jaccard") is not None
    ]
    total_weight = sum(weight for weight, _ in weighted_rows)
    adjusted = (
        sum(weight * value for weight, value in weighted_rows) / total_weight
        if total_weight > 0
        else None
    )
    edge = jaccard(totals["edge_tp"], totals["edge_fp"], totals["edge_fn"])
    division = jaccard(
        totals["division_tp"], totals["division_fp"], totals["division_fn"]
    )
    score = (
        None
        if adjusted is None
        else adjusted
        if division is None
        else adjusted + 0.1 * division
    )
    node_recall_values = [
        float(row["node_recall"]) for row in rows if row.get("node_recall") is not None
    ]
    estimated_total = sum(float(row["estimated_node_count"]) for row in rows)
    penalties = [
        (weight, float(row["node_count_penalty"]))
        for weight, row in zip(weights, rows)
        if row.get("node_count_penalty") is not None
    ]
    penalty_weight = sum(weight for weight, _ in penalties)
    result: dict[str, Any] = {
        **totals,
        "sample_count": len(rows),
        "edge_jaccard": edge,
        "division_jaccard": division,
        "adj_edge_jaccard": adjusted,
        "official_score": score,
        "node_count_penalty": (
            sum(weight * value for weight, value in penalties) / penalty_weight
            if penalty_weight > 0
            else None
        ),
        "node_recall": (
            sum(node_recall_values) / len(node_recall_values)
            if node_recall_values
            else None
        ),
        "estimated_node_count": estimated_total,
        "total_node_ratio": (
            (totals["num_pred_nodes"] - estimated_total) / estimated_total
            if estimated_total > 0
            else None
        ),
        "runtime_seconds": sum(float(row["runtime_seconds"]) for row in rows),
        "finalize_runtime_seconds": sum(
            float(row["finalize_runtime_seconds"]) for row in rows
        ),
        "scoring_runtime_seconds": sum(
            float(row["scoring_runtime_seconds"]) for row in rows
        ),
        "total_runtime_seconds": sum(
            float(row["total_runtime_seconds"]) for row in rows
        ),
        "peak_memory_bytes": max(float(row["peak_memory_bytes"]) for row in rows),
        # Per-sample values are saturation indicators/rates.  Their aggregate
        # is the sample saturation rate, not max(any saturated sample), because
        # the frozen tolerance is explicitly a rate increase.
        "frame_cap_saturation": sum(float(row["frame_cap_saturation"]) for row in rows)
        / len(rows),
        "global_cap_saturation": sum(
            float(row["global_cap_saturation"]) for row in rows
        )
        / len(rows),
        "topology_valid": all(bool(row["topology_valid"]) for row in rows),
        "schema_valid": all(bool(row["schema_valid"]) for row in rows),
        "estimated_node_count_evidence": (
            "GEFF_METADATA_ESTIMATED_NUMBER_OF_NODES_ALL_SAMPLES"
        ),
        "gt_node_count_evidence": "SUM_ACTUAL_GT_GEFF_GRAPH_NUM_NODES",
        "pre_division_cache_sha256": ordered_sample_sha256(
            rows, "pre_division_cache_sha256"
        ),
        "final_output_sha256": ordered_sample_sha256(rows, "final_output_sha256"),
        "scorer_input_rows_sha256": ordered_sample_sha256(
            rows, "scorer_input_rows_sha256"
        ),
        "hash_aggregation": SAMPLE_HASH_AGGREGATION,
    }
    result["frame_cap_saturation_rate"] = result["frame_cap_saturation"]
    result["global_cap_saturation_rate"] = result["global_cap_saturation"]
    for key in (
        "edges_fragmented",
        "edges_lost_to_detection",
        "wrong_association_edges",
        "safe_div_candidate_count",
        "accepted_division_count",
        "deepcenter_accepted_count",
        "deepcenter_rejected_count",
    ):
        result[key] = sum(int(row[key]) for row in rows)
    return result


def check_contract_and_frozen_inputs(
    root: Path, checks: Checks
) -> tuple[dict[str, Any], dict[str, Any]]:
    contract_path = root / CONTRACT_PATH
    actual_contract_sha = (
        sha256_file(contract_path) if contract_path.is_file() else None
    )
    checks.require(
        "frozen_contract_sha256",
        actual_contract_sha == CONTRACT_SHA256,
        {"expected": CONTRACT_SHA256, "actual": actual_contract_sha},
    )
    contract = load_json(contract_path, "V20B contract")
    checks.require(
        "frozen_contract_identity",
        contract.get("task_id") == TASK_ID
        and contract.get("experiment_freeze", {})
        .get("promotion_rule", {})
        .get("screen_name")
        == SCREEN_NAME
        and set(
            contract.get("experiment_freeze", {})
            .get("promotion_rule", {})
            .get("allowed_decisions", [])
        )
        == ALLOWED_DECISIONS,
        {
            "task_id": contract.get("task_id"),
            "screen_name": contract.get("experiment_freeze", {})
            .get("promotion_rule", {})
            .get("screen_name"),
        },
    )

    state_path = root / f".task-verification/{TASK_ID}/state.json"
    state = load_json(state_path, "frozen task state")
    state_head = state.get("baseline", {}).get("head")
    state_ok = (
        state.get("task_id") == TASK_ID
        and state.get("contract_sha256") == CONTRACT_SHA256
        and state.get("status") in TASK_STATE_ACCEPTED_STATUSES
        and state.get("baseline", {}).get("contract_tracked") is True
        and state.get("baseline", {}).get("contract_matches_head") is True
        and HEX_GIT_COMMIT.fullmatch(str(state_head)) is not None
    )
    checks.require(
        "contract_pre_run_prepare_state",
        state_ok,
        {
            "status": state.get("status"),
            "contract_sha256": state.get("contract_sha256"),
            "freeze_head": state_head,
            "prepared_at": state.get("prepared_at"),
        },
    )

    frozen_files = {
        FROZEN_SAMPLE_MANIFEST_PATH: FROZEN_SAMPLE_MANIFEST_SHA256,
        EVIDENCE_BOUNDARY_PATH: FROZEN_EVIDENCE_BOUNDARY_SHA256,
        WRITE_BUDGET_PATH: FROZEN_WRITE_BUDGET_SHA256,
    }
    mismatches = []
    for relative, expected in frozen_files.items():
        path = root / relative
        actual = sha256_file(path) if path.is_file() else None
        if actual != expected:
            mismatches.append(
                {"path": str(relative), "expected": expected, "actual": actual}
            )
    checks.require(
        "frozen_control_files_sha256",
        not mismatches,
        mismatches or f"{len(frozen_files)}/{len(frozen_files)} match",
    )
    builder_path = root / VALIDATION_BUILDER_PATH
    actual_builder_sha = sha256_file(builder_path) if builder_path.is_file() else None
    checks.require(
        "frozen_validation_builder_sha256",
        actual_builder_sha == VALIDATION_BUILDER_SHA256,
        {"expected": VALIDATION_BUILDER_SHA256, "actual": actual_builder_sha},
    )

    read_scope = contract.get("experiment_freeze", {}).get("read_scope_sha256", {})
    if not isinstance(read_scope, dict) or not read_scope:
        raise EvidenceError("contract read_scope_sha256 is absent")
    read_mismatches = []
    for relative, expected in sorted(read_scope.items()):
        path = root / relative
        actual = sha256_file(path) if path.is_file() else None
        if actual != expected:
            read_mismatches.append(
                {"path": relative, "expected": expected, "actual": actual}
            )
    checks.require(
        "frozen_read_scope_sha256",
        not read_mismatches,
        read_mismatches or f"{len(read_scope)}/{len(read_scope)} match",
    )

    frozen_manifest = load_json(root / FROZEN_SAMPLE_MANIFEST_PATH)
    frozen_samples = frozen_manifest.get("samples")
    if not isinstance(frozen_samples, list):
        raise EvidenceError("frozen sample manifest samples must be a list")
    canonical_rows = sorted(frozen_samples, key=lambda row: row.get("sample_id", ""))
    sample_ids = [row.get("sample_id") for row in canonical_rows]
    counts = Counter(row.get("embryo_id") for row in canonical_rows)
    sample_manifest_ok = (
        frozen_manifest.get("task_id") == TASK_ID
        and frozen_manifest.get("sample_count") == EXPECTED_SAMPLE_COUNT
        and frozen_manifest.get("embryo_count") == 2
        and frozen_manifest.get("embryo_sample_counts") == EXPECTED_EMBRYO_COUNTS
        and counts == Counter(EXPECTED_EMBRYO_COUNTS)
        and len(sample_ids) == len(set(sample_ids)) == EXPECTED_SAMPLE_COUNT
        and frozen_manifest.get("sample_rows_canonical_sha256")
        == canonical_sha256(canonical_rows)
        and tuple(frozen_manifest.get("anchors", {}).get("sample_ids", [])) == ANCHORS
        and frozen_manifest.get("anchors", {}).get("outcome_data_used") is False
    )
    checks.require(
        "frozen_sample_identity",
        sample_manifest_ok,
        {
            "samples": len(sample_ids),
            "unique_samples": len(set(sample_ids)),
            "embryos": dict(counts),
            "anchors": frozen_manifest.get("anchors", {}).get("sample_ids"),
        },
    )

    boundary = load_json(root / EVIDENCE_BOUNDARY_PATH)
    history = boundary.get("historical_invariants", {})
    boundary_ok = (
        boundary.get("task_id") == TASK_ID
        and boundary.get("experiment_label") == SCREEN_NAME
        and boundary.get("checkpoint_overlap", {}).get("status")
        == "CHECKPOINT_TRAINING_OVERLAP_UNKNOWN"
        and history.get("v20a_domain_status") == "BLOCKED_INSUFFICIENT_EMBRYO_GROUPS"
        and history.get("v20a_arm_statuses")
        == {arm: "NOT_RUN_HARD_GATE" for arm in ARMS}
        and history.get("v20a_files_must_not_be_modified") is True
        and boundary.get("delivery_completion_is_performance_improvement") is False
        and boundary.get("score_prediction_allowed") is False
    )
    checks.require("evidence_boundary", boundary_ok, boundary)
    return contract, frozen_manifest


def validate_payload_evidence(
    root: Path,
    frozen_manifest: Mapping[str, Any],
) -> StageEvidence:
    inventory_path = root / PAYLOAD_INVENTORY_PATH
    manifest_path = root / FULL_SAMPLE_MANIFEST_PATH
    if not inventory_path.is_file() or not manifest_path.is_file():
        return StageEvidence(
            "MISSING",
            {
                "inventory_exists": inventory_path.is_file(),
                "manifest_exists": manifest_path.is_file(),
            },
        )

    headers, rows = load_csv(inventory_path)
    if tuple(headers) != PAYLOAD_COLUMNS:
        raise EvidenceError("payload inventory schema/order mismatch")
    frozen_rows = frozen_manifest.get("samples", [])
    frozen_by_id = {row["sample_id"]: row for row in frozen_rows}
    if len(rows) != EXPECTED_SAMPLE_COUNT:
        raise EvidenceError(
            f"payload inventory has {len(rows)} rows, expected {EXPECTED_SAMPLE_COUNT}"
        )
    seen: set[str] = set()
    included: set[str] = set()
    excluded: set[str] = set()
    normalized_rows: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []
    for index, raw in enumerate(rows, 2):
        sample_id = raw.get("sample_id", "")
        embryo = raw.get("embryo_id", "")
        if sample_id not in frozen_by_id:
            raise EvidenceError(f"payload row {index} has unknown sample {sample_id!r}")
        if sample_id in seen:
            raise EvidenceError(f"payload inventory duplicates {sample_id}")
        seen.add(sample_id)
        frozen = frozen_by_id[sample_id]
        if embryo != frozen.get("embryo_id") or not sample_id.startswith(f"{embryo}_"):
            raise EvidenceError(f"payload sample/embryo mismatch for {sample_id}")
        if raw.get("image_path") != frozen.get("expected_image_path"):
            raise EvidenceError(f"payload image path drift for {sample_id}")
        if raw.get("gt_path") != frozen.get("expected_gt_path"):
            raise EvidenceError(f"payload GT path drift for {sample_id}")
        flags = {
            key: parse_bool(raw[key], f"{sample_id}.{key}")
            for key in (
                "image_exists",
                "gt_exists",
                "image_readable",
                "gt_readable",
                "scorer_metadata_readable",
            )
        }
        readable = all(flags.values())
        status = raw.get("status", "").strip().upper()
        error = raw.get("error", "").strip()
        if readable:
            if not status_is_success(status):
                raise EvidenceError(
                    f"{sample_id} is readable but status is not successful: {status}"
                )
            if error:
                raise EvidenceError(f"{sample_id} is readable but has an error")
            if not raw.get("image_shape") or not raw.get("image_dtype"):
                raise EvidenceError(f"{sample_id} lacks image shape/dtype")
            parse_int(raw["gt_node_count"], f"{sample_id}.gt_node_count")
            parse_int(raw["gt_edge_count"], f"{sample_id}.gt_edge_count")
            parse_float(
                raw["estimated_node_count"],
                f"{sample_id}.estimated_node_count",
                minimum=0.0,
            )
            if not raw.get("estimated_node_count_evidence"):
                raise EvidenceError(f"{sample_id} lacks estimated-node-count evidence")
            for key in (
                "image_metadata_sha256",
                "image_tree_inventory_sha256",
                "gt_payload_sha256",
                "sample_payload_sha256",
            ):
                require_sha256(raw[key], f"{sample_id}.{key}")
            included.add(sample_id)
        else:
            if not status_is_failure(status):
                raise EvidenceError(
                    f"{sample_id} is unreadable but status is not failure: {status}"
                )
            if not error:
                raise EvidenceError(f"{sample_id} is excluded without a concrete error")
            excluded.add(sample_id)
            errors.append({"sample_id": sample_id, "status": status, "error": error})
        normalized_rows.append({key: raw.get(key, "") for key in headers})

    if seen != set(frozen_by_id):
        raise EvidenceError("payload inventory does not cover the frozen sample set")
    included_counts = Counter(frozen_by_id[sample]["embryo_id"] for sample in included)
    both_embryos = all(included_counts.get(embryo, 0) > 0 for embryo in EMBRYOS)

    full_manifest = load_json(manifest_path)
    require_keys(
        full_manifest,
        {
            "schema_version",
            "task_id",
            "status",
            "sample_count",
            "embryo_count",
            "embryo_sample_counts",
            "excluded_samples",
            "rows_sha256",
            "source_frozen_manifest_sha256",
            "samples",
        },
        "full sample manifest",
    )
    manifest_samples = full_manifest["samples"]
    if not isinstance(manifest_samples, list) or len(manifest_samples) != len(rows):
        raise EvidenceError("full sample manifest samples do not cover inventory rows")
    manifest_by_id: dict[str, Mapping[str, Any]] = {}
    for entry in manifest_samples:
        if not isinstance(entry, dict) or not entry.get("sample_id"):
            raise EvidenceError("full sample manifest contains invalid sample entry")
        sample_id = str(entry["sample_id"])
        if sample_id in manifest_by_id:
            raise EvidenceError(f"full sample manifest duplicates {sample_id}")
        manifest_by_id[sample_id] = entry
    if set(manifest_by_id) != set(frozen_by_id):
        raise EvidenceError("full sample manifest sample identities drifted")

    excluded_declared: set[str] = set()
    if not isinstance(full_manifest["excluded_samples"], list):
        raise EvidenceError("full sample manifest excluded_samples must be a list")
    for entry in full_manifest["excluded_samples"]:
        sample_id = entry if isinstance(entry, str) else entry.get("sample_id")
        if not isinstance(sample_id, str):
            raise EvidenceError("invalid excluded_samples entry")
        excluded_declared.add(sample_id)
    if excluded_declared != excluded:
        raise EvidenceError(
            "full sample manifest exclusions differ from payload inventory"
        )

    for sample_id, entry in manifest_by_id.items():
        embryo = frozen_by_id[sample_id]["embryo_id"]
        if entry.get("embryo_id") != embryo:
            raise EvidenceError(f"full manifest embryo mismatch for {sample_id}")
        included_value = optional_present(
            entry,
            ("included_in_all_arms", "include_in_all_arms", "included"),
            sample_id not in excluded,
        )
        if parse_bool(included_value, f"{sample_id}.included") != (
            sample_id in included
        ):
            raise EvidenceError(f"full sample manifest inclusion drift for {sample_id}")
        arms_value = optional_present(entry, ("arms", "included_arms"), None)
        if arms_value is not None:
            if isinstance(arms_value, dict):
                arm_presence = {
                    arm
                    for arm, arm_value in arms_value.items()
                    if parse_bool(arm_value, f"{sample_id}.{arm}")
                }
            elif isinstance(arms_value, list):
                arm_presence = set(str(value) for value in arms_value)
            else:
                raise EvidenceError(f"{sample_id} has malformed arms field")
            expected_arms = set(ARMS) if sample_id in included else set()
            if arm_presence != expected_arms:
                raise EvidenceError(
                    f"{sample_id} is not symmetrically included/excluded"
                )

    rows_sorted = sorted(normalized_rows, key=lambda row: row["sample_id"])
    # The runtime builder hashes its pre-CSV typed rows.  Recreate that exact
    # representation for the all-readable path instead of trusting a declared
    # hash.  The raw-CSV canonical hash and file hash remain accepted for other
    # producers whose manifest documents either convention.
    typed_rows: list[dict[str, Any]] = []
    for row in rows_sorted:
        typed: dict[str, Any] = dict(row)
        for key in (
            "image_exists",
            "gt_exists",
            "image_readable",
            "gt_readable",
            "scorer_metadata_readable",
        ):
            typed[key] = parse_bool(row[key], f"typed payload.{key}")
        for key in ("gt_node_count", "gt_edge_count"):
            if row[key] != "":
                typed[key] = int(parse_int(row[key], f"typed payload.{key}"))
        if row["estimated_node_count"] != "":
            typed["estimated_node_count"] = float(
                parse_float(
                    row["estimated_node_count"],
                    "typed payload.estimated_node_count",
                )
            )
        typed_rows.append(typed)
    accepted_row_hashes = {
        canonical_sha256(rows_sorted),
        canonical_sha256(typed_rows),
        sha256_file(inventory_path),
    }
    included_count_map = {
        embryo: int(included_counts.get(embryo, 0)) for embryo in EMBRYOS
    }
    declared_sample_count = parse_int(
        full_manifest.get("sample_count"), "full manifest sample_count"
    )
    declared_embryo_count = parse_int(
        full_manifest.get("embryo_count"), "full manifest embryo_count"
    )
    full_manifest_ok = (
        full_manifest.get("task_id") == TASK_ID
        and declared_sample_count == len(included)
        and declared_embryo_count
        == sum(included_count_map[embryo] > 0 for embryo in EMBRYOS)
        and full_manifest.get("embryo_sample_counts") == included_count_map
        and full_manifest.get("rows_sha256") in accepted_row_hashes
        and full_manifest.get("source_frozen_manifest_sha256")
        == sha256_file(root / FROZEN_SAMPLE_MANIFEST_PATH)
    )
    if not full_manifest_ok:
        raise EvidenceError("full sample manifest top-level identity mismatch")

    declared_status = str(full_manifest.get("status", "")).upper()
    declared_success = status_is_success(declared_status)
    declared_failure = status_is_failure(declared_status)
    if not declared_success and not declared_failure:
        raise EvidenceError(f"payload manifest status is ambiguous: {declared_status}")
    if not both_embryos and not declared_failure:
        raise EvidenceError(
            f"payload evidence lacks two embryos but manifest status is {declared_status}"
        )
    if declared_failure and not excluded:
        raise EvidenceError("payload manifest declares failure without a failed sample")
    if excluded and declared_success:
        symmetric = optional_present(
            full_manifest,
            ("arm_symmetric_exclusion", "symmetric_exclusion"),
            None,
        )
        if symmetric is None or not parse_bool(symmetric, "arm_symmetric_exclusion"):
            raise EvidenceError(
                "successful exclusions lack symmetric-exclusion receipt"
            )
    expected_outcome = "PASS" if both_embryos and declared_success else "FAIL"
    return StageEvidence(
        expected_outcome,
        {
            "frozen_samples": EXPECTED_SAMPLE_COUNT,
            "readable_samples": len(included),
            "excluded_samples": len(excluded),
            "included_embryo_counts": dict(sorted(included_counts.items())),
            "both_embryos_present": both_embryos,
            "explicit_errors": errors,
            "included_sample_ids": sorted(included),
            "excluded_sample_ids": sorted(excluded),
            "inventory_sha256": sha256_file(inventory_path),
            "manifest_sha256": sha256_file(manifest_path),
        },
    )


def stage_declared_outcome(value: Mapping[str, Any], label: str) -> str:
    explicit = optional_present(value, ("all_pass", "passed", "valid"), None)
    if explicit is not None:
        return "PASS" if parse_bool(explicit, f"{label}.all_pass") else "FAIL"
    status = optional_present(value, ("status", "result", "outcome"), None)
    if status_is_success(status):
        return "PASS"
    if status_is_failure(status):
        return "FAIL"
    raise EvidenceError(f"{label} has no unambiguous PASS/FAIL status")


def evidence_rows(value: Mapping[str, Any], label: str) -> list[dict[str, Any]]:
    for key in ("rows", "checks", "entries", "samples"):
        candidate = value.get(key)
        if isinstance(candidate, list):
            if not all(isinstance(row, dict) for row in candidate):
                raise EvidenceError(f"{label}.{key} contains a non-object row")
            return list(candidate)
    raise EvidenceError(f"{label} has no rows/checks/entries list")


def frozen_version_pinned_dataset_sources(
    contract: Mapping[str, Any],
) -> list[str]:
    identities = contract["experiment_freeze"]["identities"]["input_datasets"]
    sources: list[str] = []
    for identity in identities:
        if identity.get("role") == "competition_data":
            continue
        ref = identity.get("ref")
        version = identity.get("version")
        if (
            not isinstance(ref, str)
            or ref.count("/") != 1
            or isinstance(version, bool)
            or not isinstance(version, int)
            or version <= 0
        ):
            raise EvidenceError("frozen input Dataset source is not version pinned")
        sources.append(f"{ref}/{version}")
    if len(sources) != 3 or len(set(sources)) != 3:
        raise EvidenceError("expected exactly three version-pinned Dataset sources")
    return sources


def validate_runtime_identity_evidence(
    root: Path,
    contract: Mapping[str, Any],
    included_sample_ids: set[str],
) -> StageEvidence:
    required_paths = (
        RUNTIME_PATH,
        FULL_SAMPLE_MANIFEST_PATH,
        PAYLOAD_INVENTORY_PATH,
        CACHE_MANIFEST_PATH,
        RESOLVED_CONFIG_VERIFICATION_PATH,
        PROMOTION_PATH,
        ARTIFACT_MANIFEST_PATH,
    )
    missing = [str(path) for path in required_paths if not (root / path).is_file()]
    missing.extend(
        str(EXPERIMENT_DIR / f"canonical_resolved_config_{arm}.json")
        for arm in ARMS
        if not (
            root / EXPERIMENT_DIR / f"canonical_resolved_config_{arm}.json"
        ).is_file()
    )
    if missing:
        return StageEvidence("MISSING", {"missing": sorted(missing)})

    runtime = load_json(root / RUNTIME_PATH)
    evidence = runtime.get("runtime_identity_evidence")
    if not isinstance(evidence, dict):
        raise EvidenceError("runtime receipt lacks runtime_identity_evidence")
    evidence_sha = canonical_sha256(evidence)
    if runtime.get("runtime_identity_evidence_sha256") != evidence_sha:
        raise EvidenceError("runtime identity evidence SHA is stale")
    if evidence.get("schema_version") != "1.0":
        raise EvidenceError("runtime identity evidence schema_version mismatch")

    frozen_identities = contract["experiment_freeze"]["identities"]
    base = evidence.get("base_source")
    if not isinstance(base, dict) or (
        base.get("status") != "BUILD_TIME_VERIFIED_RUNTIME_SOURCE_OBJECT_NOT_MOUNTED"
        or base.get("expected_sha256") != frozen_identities["base_source_sha256"]
        or base.get("builder_verified_input_sha256")
        != frozen_identities["base_source_sha256"]
        or base.get("runtime_recomputed_sha256") is not None
    ):
        raise EvidenceError("base-source identity evidence contradicts the freeze")

    support = evidence.get("support_code")
    if not isinstance(support, dict) or (
        support.get("status") != "PASS"
        or support.get("expected_manifest_sha256")
        != frozen_identities["support_code_manifest_sha256"]
        or support.get("actual_manifest_sha256")
        != frozen_identities["support_code_manifest_sha256"]
    ):
        raise EvidenceError("runtime support-code identity did not match")
    require_sha256(support.get("actual_file_sha256"), "runtime support code file")

    checkpoints = evidence.get("checkpoints")
    if not isinstance(checkpoints, dict) or (
        checkpoints.get("status") != "PASS"
        or checkpoints.get("expected") != frozen_identities["checkpoints"]
        or checkpoints.get("actual") != frozen_identities["checkpoints"]
    ):
        raise EvidenceError("runtime checkpoint identities did not match")

    scorer = evidence.get("official_scorer")
    frozen_scorer = frozen_identities["scorer"]
    expected_scorer_files = {
        "src/tracking_cellmot/metrics.py": frozen_scorer["metrics_sha256"],
        "src/tracking_cellmot/division_metrics.py": frozen_scorer[
            "division_metrics_sha256"
        ],
        "scripts/evaluate.py": frozen_scorer["evaluate_sha256"],
    }
    if not isinstance(scorer, dict) or (
        scorer.get("status") != "PASS"
        or scorer.get("expected_file_sha256") != expected_scorer_files
        or scorer.get("actual_file_sha256") != expected_scorer_files
        or scorer.get("commit_expected") != frozen_scorer["commit"]
    ):
        raise EvidenceError("runtime official-scorer identity did not match")

    inventory_headers, inventory_rows = load_csv(root / PAYLOAD_INVENTORY_PATH)
    if tuple(inventory_headers) != PAYLOAD_COLUMNS:
        raise EvidenceError("identity check saw a noncanonical payload inventory")
    payload_sha_by_sample: dict[str, str] = {}
    inventory_identity_by_sample: dict[str, dict[str, str]] = {}
    for row in inventory_rows:
        sample_id = str(row.get("sample_id", ""))
        if sample_id in payload_sha_by_sample:
            raise EvidenceError(f"payload identity duplicates {sample_id}")
        values = {
            key: require_sha256(row.get(key), f"payload identity {sample_id}.{key}")
            for key in (
                "image_metadata_sha256",
                "image_tree_inventory_sha256",
                "gt_payload_sha256",
                "sample_payload_sha256",
            )
        }
        payload_sha_by_sample[sample_id] = values["sample_payload_sha256"]
        inventory_identity_by_sample[sample_id] = values
    if set(payload_sha_by_sample) != included_sample_ids:
        raise EvidenceError("runtime payload identity coverage is not exact")

    full_manifest = load_json(root / FULL_SAMPLE_MANIFEST_PATH)
    manifest_identity_by_sample: dict[str, Mapping[str, Any]] = {}
    for entry in evidence_rows(full_manifest, "full sample manifest"):
        sample_id = str(entry.get("sample_id", ""))
        identity = entry.get("input_identity")
        if sample_id in manifest_identity_by_sample or not isinstance(identity, dict):
            raise EvidenceError(
                f"full manifest input identity malformed for {sample_id}"
            )
        for key, expected in inventory_identity_by_sample.get(sample_id, {}).items():
            if identity.get(key) != expected:
                raise EvidenceError(
                    f"full manifest input identity drift for {sample_id}.{key}"
                )
        manifest_identity_by_sample[sample_id] = identity
    if set(manifest_identity_by_sample) != included_sample_ids:
        raise EvidenceError("full manifest input identities do not cover 199 samples")

    payload = evidence.get("competition_payload")
    expected_payload_rows = [
        {"sample_id": sample_id, "sha256": payload_sha_by_sample[sample_id]}
        for sample_id in sorted(payload_sha_by_sample)
    ]
    if not isinstance(payload, dict) or (
        payload.get("status") != "PASS"
        or payload.get("sample_count") != EXPECTED_SAMPLE_COUNT
        or payload.get("embryo_sample_counts") != EXPECTED_EMBRYO_COUNTS
        or payload.get("competition_ref") != "biohub-cell-tracking-during-development"
        or payload.get("rows") != expected_payload_rows
        or payload.get("ordered_sample_payload_sha256")
        != canonical_sha256(expected_payload_rows)
    ):
        raise EvidenceError("competition payload identity evidence is stale")

    pinned_sources = frozen_version_pinned_dataset_sources(contract)
    pinned_sources_sha = canonical_sha256(pinned_sources)
    datasets = evidence.get("input_dataset_metadata")
    if not isinstance(datasets, dict) or (
        datasets.get("status") != "PASS_VERSION_PINNED_AND_CRITICAL_CONTENT_VERIFIED"
        or datasets.get("declared_expected") != frozen_identities["input_datasets"]
        or datasets.get("expected_version_pinned_sources") != pinned_sources
        or datasets.get("kernel_metadata_version_pinned_sources") != pinned_sources
        or datasets.get("content_identity_is_independently_covered_by")
        != ["support_code", "checkpoints", "competition_payload"]
    ):
        raise EvidenceError("runtime Dataset source/content identity did not match")
    mount_roots = datasets.get("runtime_mount_roots")
    if (
        not isinstance(mount_roots, dict)
        or set(mount_roots)
        != {
            "primary_and_support",
            "secondary",
            "deepcenter_checkpoint_parent",
            "competition",
        }
        or not all(
            isinstance(value, str) and value.startswith("/")
            for value in mount_roots.values()
        )
    ):
        raise EvidenceError("runtime Dataset mount-root evidence is malformed")

    cache_manifest = load_json(root / CACHE_MANIFEST_PATH)
    cache_object = cache_manifest.get("cache")
    if not isinstance(cache_object, dict):
        raise EvidenceError("cache manifest lacks canonical cache object")
    if cache_manifest.get("entries") != cache_object.get("entries") or (
        cache_manifest.get("manifest_sha256") != cache_object.get("manifest_sha256")
    ):
        raise EvidenceError("cache manifest top-level/cache object copies drifted")
    for label, cache_value in (
        ("cache manifest cache", cache_object),
        *(
            (
                f"canonical config {arm} cache",
                load_json(
                    root / EXPERIMENT_DIR / f"canonical_resolved_config_{arm}.json"
                ).get("pre_division_cache"),
            )
            for arm in ARMS
        ),
    ):
        if not isinstance(cache_value, dict) or (
            cache_value.get("runtime_identity_evidence_sha256") != evidence_sha
            or cache_value.get("version_pinned_dataset_sources_sha256")
            != pinned_sources_sha
        ):
            raise EvidenceError(f"{label} runtime identity binding drifted")
        entries = cache_value.get("entries")
        if not isinstance(entries, list) or len(entries) != EXPECTED_SAMPLE_COUNT:
            raise EvidenceError(f"{label} does not contain 199 cache entries")
        for entry in entries:
            sample_id = str(entry.get("sample_id", ""))
            if (
                entry.get("runtime_identity_evidence_sha256") != evidence_sha
                or entry.get("version_pinned_dataset_sources_sha256")
                != pinned_sources_sha
                or entry.get("input_identity")
                != manifest_identity_by_sample.get(sample_id)
            ):
                raise EvidenceError(f"{label} entry identity drift for {sample_id}")

    crosslink_objects: list[tuple[str, Mapping[str, Any]]] = []
    for arm in ARMS:
        receipt = load_json(
            root / EXPERIMENT_DIR / f"canonical_resolved_config_{arm}.json"
        )
        if receipt.get("runtime_identity_gate_pass") is not True:
            raise EvidenceError(f"canonical config {arm} runtime identity gate failed")
        crosslink_objects.append((f"canonical config {arm}", receipt))
    resolved = load_json(root / RESOLVED_CONFIG_VERIFICATION_PATH)
    if (
        resolved.get("runtime_identity_gate_pass") is not True
        or resolved.get("runtime_identity_evidence_sha256") != evidence_sha
        or resolved.get("checker_sha256")
        != sha256_file(
            root
            / RESOLVED_CONFIG_VERIFICATION_PATH.parent
            / "verify_resolved_config.py"
        )
    ):
        raise EvidenceError("resolved-config runtime identity/checker binding drifted")
    crosslink_objects.append(("resolved config verification", resolved))
    artifact_manifest = load_json(root / ARTIFACT_MANIFEST_PATH)
    if (
        artifact_manifest.get("identities") != frozen_identities
        or artifact_manifest.get("identity_declaration_scope")
        != "FROZEN_EXPECTED_IDENTITIES"
    ):
        raise EvidenceError("artifact manifest frozen identity declaration drifted")
    crosslink_objects.extend(
        (("runtime receipts", runtime), ("artifact manifest", artifact_manifest))
    )
    for label, value in crosslink_objects:
        if value.get("runtime_identity_evidence") != evidence:
            raise EvidenceError(f"{label} embeds different runtime identity evidence")
        declared_sha = value.get("runtime_identity_evidence_sha256")
        if declared_sha is not None and declared_sha != evidence_sha:
            raise EvidenceError(f"{label} runtime identity SHA drifted")

    promotion = load_json(root / PROMOTION_PATH)
    if promotion.get("runtime_identity_evidence_sha256") != evidence_sha:
        raise EvidenceError("promotion runtime identity SHA drifted")
    candidate_gates = promotion.get("candidate_gates")
    if not isinstance(candidate_gates, dict):
        raise EvidenceError("promotion candidate gates are absent")
    for candidate in CANDIDATES:
        declared = candidate_gates.get(candidate)
        gates = declared.get("gates", declared) if isinstance(declared, dict) else None
        if (
            not isinstance(gates, dict)
            or gates.get("identity_and_shared_cache_match") is not True
        ):
            raise EvidenceError(f"promotion {candidate} identity gate is not true")
    return StageEvidence(
        "PASS",
        {
            "runtime_identity_evidence_sha256": evidence_sha,
            "version_pinned_dataset_sources": pinned_sources,
            "version_pinned_dataset_sources_sha256": pinned_sources_sha,
            "payload_sample_count": len(payload_sha_by_sample),
        },
    )


def validate_config_and_shared_cache(
    root: Path,
    contract: Mapping[str, Any],
    included_sample_ids: set[str],
) -> StageEvidence:
    receipt_paths = {
        arm: root / EXPERIMENT_DIR / f"canonical_resolved_config_{arm}.json"
        for arm in ARMS
    }
    active_paths = {
        arm: root / EXPERIMENT_DIR / f"active_config_{arm}.json" for arm in ARMS
    }
    call_paths = {
        arm: root / EXPERIMENT_DIR / f"safe_div_call_receipt_{arm}.json" for arm in ARMS
    }
    all_paths = [*receipt_paths.values(), *active_paths.values(), *call_paths.values()]
    missing = [str(path.relative_to(root)) for path in all_paths if not path.is_file()]
    if missing:
        return StageEvidence("MISSING", {"missing": missing})

    command = [
        sys.executable,
        "-B",
        str(root / EXPERIMENT_DIR / "verify_resolved_config.py"),
        "--contract",
        str(root / CONTRACT_PATH),
    ]
    for arm in ARMS:
        command.extend(["--receipt", f"{arm}={receipt_paths[arm]}"])
        command.extend(["--active-config", f"{arm}={active_paths[arm]}"])
        command.extend(["--call-receipt", f"{arm}={call_paths[arm]}"])
    completed = subprocess.run(
        command,
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=120,
    )
    stdout = completed.stdout.decode("utf-8", errors="replace")
    stderr = completed.stderr.decode("utf-8", errors="replace")
    if completed.returncode != 0:
        return StageEvidence(
            "FAIL",
            {
                "checker_returncode": completed.returncode,
                "stdout_tail": stdout[-1200:],
                "stderr_tail": stderr[-1200:],
            },
        )
    if "V20B_RESOLVED_CONFIG_PASS" not in stdout:
        raise EvidenceError("resolved-config checker returned 0 without PASS token")

    receipts = {arm: load_json(receipt_paths[arm]) for arm in ARMS}
    r70_cache = receipts["R70"].get("pre_division_cache")
    if not isinstance(r70_cache, dict):
        raise EvidenceError("R70 canonical receipt lacks pre_division_cache")
    cache_entries = r70_cache.get("entries")
    if not isinstance(cache_entries, list):
        raise EvidenceError("R70 cache entries are absent")
    cache_by_sample: dict[str, str] = {}
    for entry in cache_entries:
        if not isinstance(entry, dict):
            raise EvidenceError("R70 cache contains a non-object entry")
        sample_id = str(entry.get("sample_id", ""))
        if sample_id in cache_by_sample:
            raise EvidenceError(f"R70 cache duplicates {sample_id}")
        cache_by_sample[sample_id] = require_sha256(
            entry.get("cache_sha256"), f"R70 cache {sample_id}"
        )
    if set(cache_by_sample) != included_sample_ids:
        raise EvidenceError(
            "shared cache sample set differs from readable/included payload set"
        )

    cache_manifest_path = root / CACHE_MANIFEST_PATH
    if not cache_manifest_path.is_file():
        raise EvidenceError("cache_manifest.json is missing")
    cache_manifest = load_json(cache_manifest_path)
    cache_outcome = stage_declared_outcome(cache_manifest, "cache manifest")
    if cache_outcome != "PASS":
        return StageEvidence(
            "FAIL",
            {
                "checker": "PASS",
                "cache_manifest_status": cache_manifest.get("status"),
            },
        )
    manifest_entries = evidence_rows(cache_manifest, "cache manifest")
    if cache_manifest.get("manifest_sha256") != canonical_sha256(manifest_entries):
        raise EvidenceError("cache manifest entries SHA is stale")
    if r70_cache.get("manifest_sha256") != cache_manifest.get("manifest_sha256"):
        raise EvidenceError("canonical config/cache manifest SHA differs")
    manifest_by_sample: dict[str, Mapping[str, Any]] = {}
    capture_point = optional_present(
        cache_manifest,
        ("cache_capture_point", "capture_point"),
        None,
    )
    expected_capture = (
        contract.get("experiment_freeze", {})
        .get("cache_boundary", {})
        .get("cache_capture_point")
    )
    if capture_point != expected_capture:
        raise EvidenceError("cache manifest capture point differs from contract")
    for entry in manifest_entries:
        sample_id = str(entry.get("sample_id", ""))
        embryo = str(entry.get("embryo_id", ""))
        if sample_id in manifest_by_sample:
            raise EvidenceError(f"cache manifest duplicates {sample_id}")
        if embryo not in EMBRYOS or not sample_id.startswith(f"{embryo}_"):
            raise EvidenceError(f"cache manifest embryo mismatch for {sample_id}")
        manifest_by_sample[sample_id] = entry
        manifest_sha = require_sha256(
            first_present(
                entry,
                ("cache_sha256", "pre_division_cache_sha256"),
                f"cache manifest {sample_id}",
            ),
            f"cache manifest {sample_id}",
        )
        if cache_by_sample.get(sample_id) != manifest_sha:
            raise EvidenceError(f"cache manifest SHA drift for {sample_id}")
    if set(manifest_by_sample) != included_sample_ids:
        raise EvidenceError("cache manifest does not cover included samples exactly")

    verification_path = root / RESOLVED_CONFIG_VERIFICATION_PATH
    if not verification_path.is_file():
        raise EvidenceError("resolved_config_verification.json is missing")
    verification = load_json(verification_path)
    if stage_declared_outcome(verification, "resolved config verification") != "PASS":
        return StageEvidence(
            "FAIL",
            {
                "checker": "PASS",
                "runtime_verification": verification.get("status"),
            },
        )
    if verification.get("task_id") != TASK_ID:
        raise EvidenceError("resolved config verification task_id mismatch")
    verification_cache_sha = optional_present(
        verification,
        (
            "shared_pre_division_cache_manifest_sha256",
            "cache_manifest_sha256",
        ),
        None,
    )
    if verification_cache_sha is not None:
        require_sha256(verification_cache_sha, "resolved config shared cache")
        if verification_cache_sha != r70_cache.get("manifest_sha256"):
            raise EvidenceError("resolved config verification cache SHA is stale")
    return StageEvidence(
        "PASS",
        {
            "checker_returncode": completed.returncode,
            "arms": list(ARMS),
            "sample_count": len(cache_by_sample),
            "cache_manifest_sha256": r70_cache.get("manifest_sha256"),
            "cache_by_sample": cache_by_sample,
            "receipt_sha256": {arm: sha256_file(receipt_paths[arm]) for arm in ARMS},
        },
    )


def validate_cache_equivalence(
    root: Path,
    cache_by_sample: Mapping[str, str] | None,
    contract: Mapping[str, Any],
) -> StageEvidence:
    path = root / CACHE_EQUIVALENCE_PATH
    if not path.is_file():
        return StageEvidence("MISSING", {"path": str(CACHE_EQUIVALENCE_PATH)})
    value = load_json(path)
    if value.get("task_id") != TASK_ID:
        raise EvidenceError("cache equivalence task_id mismatch")
    outcome = stage_declared_outcome(value, "cache equivalence")
    rows = evidence_rows(value, "cache equivalence")
    expected_pairs = {(arm, anchor) for arm in ARMS for anchor in ANCHORS}
    seen: set[tuple[str, str]] = set()
    failed_rows: list[dict[str, Any]] = []
    score_tolerance = float(
        contract["experiment_freeze"]["comparison_tolerances"][
            "reported_score_absolute"
        ]
    )
    coordinate_tolerance = float(
        contract["experiment_freeze"]["comparison_tolerances"][
            "graph_coordinate_absolute"
        ]
    )
    for index, row in enumerate(rows):
        arm = str(row.get("arm", ""))
        sample_id = str(row.get("sample_id", row.get("anchor_sample_id", "")))
        pair = (arm, sample_id)
        if pair in seen:
            raise EvidenceError(f"cache equivalence duplicates {pair}")
        seen.add(pair)
        if pair not in expected_pairs:
            raise EvidenceError(f"cache equivalence has unexpected row {pair}")
        same_graph = require_sha256(
            row.get("same_raw_full_graph_sha256"),
            f"cache equivalence {pair}.same graph",
        )
        cached_graph = require_sha256(
            row.get("cached_graph_sha256"), f"cache equivalence {pair}.cached graph"
        )
        same_rows = require_sha256(
            row.get("same_raw_full_rows_sha256"), f"cache equivalence {pair}.same rows"
        )
        cached_rows = require_sha256(
            row.get("cached_rows_sha256"), f"cache equivalence {pair}.cached rows"
        )
        topology_equal = same_graph == cached_graph
        output_rows_equal = same_rows == cached_rows
        score_diffs = [
            float(
                parse_float(
                    first_present(
                        row,
                        (
                            "same_raw_metric_abs_delta",
                            "official_score_abs_diff",
                            "score_abs_diff",
                            "metric_abs_diff",
                        ),
                        f"cache equivalence {pair}",
                    ),
                    f"cache equivalence {pair}.same_raw_metric_abs_delta",
                    minimum=0.0,
                )
            )
        ]
        fresh_graph_sha = require_sha256(
            row.get("fresh_full_graph_sha256"),
            f"cache equivalence {pair}.fresh graph",
        )
        fresh_rows_sha = require_sha256(
            row.get("fresh_full_rows_sha256"),
            f"cache equivalence {pair}.fresh rows",
        )
        fresh_diff = parse_float(
            row.get("fresh_full_metric_abs_delta"),
            f"cache equivalence {pair}.fresh metric delta",
            minimum=0.0,
        )
        if fresh_diff is None:
            raise EvidenceError(f"cache equivalence {pair} fresh metric delta is null")
        topology_equal = topology_equal and fresh_graph_sha == cached_graph
        output_rows_equal = output_rows_equal and fresh_rows_sha == cached_rows
        score_diffs.append(float(fresh_diff))
        if parse_bool(
            row.get("fresh_full_cache_equivalent"),
            f"cache equivalence {pair}.fresh_full_cache_equivalent",
        ) != (
            fresh_graph_sha == cached_graph
            and fresh_rows_sha == cached_rows
            and float(fresh_diff) <= score_tolerance
        ):
            raise EvidenceError(f"cache equivalence {pair} fresh-full flag is stale")
        metrics_equal = all(diff <= score_tolerance for diff in score_diffs)
        derived = {
            "topology_equal": topology_equal,
            "metrics_within_tolerance": metrics_equal,
            "submission_rows_equal": output_rows_equal,
        }
        for canonical, aliases in (
            ("topology_equal", ("topology_equal", "topology_identical")),
            ("metrics_within_tolerance", ("metrics_within_tolerance", "metric_equal")),
            (
                "submission_rows_equal",
                (
                    "submission_rows_equal",
                    "output_rows_equal",
                    "submission_format_rows_equal",
                ),
            ),
        ):
            declared_flag = optional_present(row, aliases, None)
            if (
                declared_flag is not None
                and parse_bool(declared_flag, f"cache equivalence {pair}.{canonical}")
                != derived[canonical]
            ):
                raise EvidenceError(
                    f"cache equivalence {pair}.{canonical} boolean contradicts SHA/delta evidence"
                )
        row_pass = all(derived.values())
        declared_pass = optional_present(
            row, ("pass", "passed", "equivalent", "same_raw_cache_equivalent"), None
        )
        if (
            declared_pass is not None
            and parse_bool(declared_pass, f"cache equivalence row {index}.pass")
            != row_pass
        ):
            raise EvidenceError(f"cache equivalence {pair} pass flag is stale")
        coordinate_diff = parse_float(
            optional_present(
                row,
                ("max_coordinate_abs_diff", "coordinate_abs_diff"),
                0.0,
            ),
            f"cache equivalence {pair}.coordinate_abs_diff",
            minimum=0.0,
        )
        if coordinate_diff is None or coordinate_diff > coordinate_tolerance:
            row_pass = False
        cache_sha = optional_present(
            row,
            ("cache_sha256", "pre_division_cache_sha256"),
            None,
        )
        cache_sha = require_sha256(cache_sha, f"cache equivalence {pair}.cache_sha256")
        if cache_by_sample is not None and cache_by_sample.get(sample_id) != cache_sha:
            row_pass = False
        if not row_pass:
            failed_rows.append({"arm": arm, "sample_id": sample_id})

    if outcome == "PASS":
        if value.get("all_three_arm_fresh_full_vs_cache_pass") is not True:
            raise EvidenceError(
                "cache equivalence lacks the mandatory fresh-full all-arm PASS"
            )
        if seen != expected_pairs:
            raise EvidenceError(f"cache equivalence coverage differs: {len(seen)}/6")
        if failed_rows:
            raise EvidenceError(
                "cache equivalence declares PASS but contains failed rows"
            )
    elif not failed_rows and seen == expected_pairs:
        raise EvidenceError(
            "cache equivalence declares failure without a failed anchor/arm row"
        )
    return StageEvidence(
        outcome,
        {
            "rows": len(rows),
            "expected_rows": len(expected_pairs),
            "failed_rows": failed_rows,
            "sha256": sha256_file(path),
        },
    )


def validate_runtime_determinism(
    root: Path,
    cache_by_sample: Mapping[str, str] | None,
    contract: Mapping[str, Any],
) -> StageEvidence:
    path = root / DETERMINISM_PATH
    if not path.is_file():
        return StageEvidence("MISSING", {"path": str(DETERMINISM_PATH)})
    value = load_json(path)
    if value.get("task_id") != TASK_ID:
        raise EvidenceError("runtime determinism task_id mismatch")
    outcome = stage_declared_outcome(value, "runtime determinism")
    rows = evidence_rows(value, "runtime determinism")
    expected = set(ANCHORS)
    seen: set[str] = set()
    failed_rows: list[str] = []
    score_tolerance = float(
        contract["experiment_freeze"]["comparison_tolerances"][
            "reported_score_absolute"
        ]
    )
    repetitions_required = int(
        contract["experiment_freeze"]["determinism"]["r70_anchor_upstream_repetitions"]
    )
    for index, row in enumerate(rows):
        sample_id = str(row.get("sample_id", row.get("anchor_sample_id", "")))
        arm = str(row.get("arm", "R70"))
        if sample_id in seen:
            raise EvidenceError(f"determinism duplicates {sample_id}")
        seen.add(sample_id)
        if sample_id not in expected or arm != "R70":
            raise EvidenceError(
                f"determinism has unexpected sample/arm: {sample_id}/{arm}"
            )
        repetitions = parse_int(
            optional_present(
                row,
                ("repetitions", "run_count"),
                optional_present(value, ("repetitions", "run_count"), 0),
            ),
            f"determinism {sample_id}.repetitions",
        )
        pre_a = require_sha256(
            row.get("pre_division_graph_sha256_a"),
            f"determinism {sample_id}.pre_division_graph_sha256_a",
        )
        pre_b = require_sha256(
            row.get("pre_division_graph_sha256_b"),
            f"determinism {sample_id}.pre_division_graph_sha256_b",
        )
        final_a = require_sha256(
            row.get("final_graph_sha256_a"),
            f"determinism {sample_id}.final_graph_sha256_a",
        )
        final_b = require_sha256(
            row.get("final_graph_sha256_b"),
            f"determinism {sample_id}.final_graph_sha256_b",
        )
        rows_a = require_sha256(
            optional_present(
                row,
                ("validation_rows_sha256_a", "output_rows_sha256_a"),
                None,
            ),
            f"determinism {sample_id}.output_rows_sha256_a",
        )
        rows_b = require_sha256(
            optional_present(
                row,
                ("validation_rows_sha256_b", "output_rows_sha256_b"),
                None,
            ),
            f"determinism {sample_id}.output_rows_sha256_b",
        )
        metric_diff = parse_float(
            optional_present(
                row,
                (
                    "official_score_abs_diff",
                    "official_score_abs_delta",
                    "metric_abs_diff",
                ),
                None,
            ),
            f"determinism {sample_id}.metric_abs_diff",
            minimum=0.0,
        )
        derived = {
            "pre_division_topology_equal": pre_a == pre_b,
            "final_graph_equal": final_a == final_b,
            "metrics_within_tolerance": metric_diff is not None
            and metric_diff <= score_tolerance,
            "output_rows_equal": rows_a == rows_b,
        }
        for canonical, aliases in (
            (
                "pre_division_topology_equal",
                (
                    "pre_division_topology_equal",
                    "pre_division_graph_sha_equal",
                    "exact_upstream_topology",
                ),
            ),
            (
                "final_graph_equal",
                ("final_graph_equal", "output_graph_equal", "exact_final_graph"),
            ),
            (
                "metrics_within_tolerance",
                ("metrics_within_tolerance", "metric_equal"),
            ),
            (
                "output_rows_equal",
                (
                    "output_rows_equal",
                    "submission_rows_equal",
                    "exact_output_rows",
                ),
            ),
        ):
            declared_flag = optional_present(row, aliases, None)
            if (
                declared_flag is not None
                and parse_bool(declared_flag, f"determinism {sample_id}.{canonical}")
                != derived[canonical]
            ):
                raise EvidenceError(
                    f"determinism {sample_id}.{canonical} contradicts hashes/delta"
                )
        row_pass = repetitions >= repetitions_required and all(derived.values())
        declared_pass = optional_present(row, ("pass", "passed"), None)
        if (
            declared_pass is not None
            and parse_bool(declared_pass, f"determinism {sample_id}.pass") != row_pass
        ):
            raise EvidenceError(f"determinism {sample_id} pass flag is stale")
        cache_sha = require_sha256(
            optional_present(row, ("cache_sha256", "pre_division_cache_sha256"), None),
            f"determinism {sample_id}.cache_sha256",
        )
        if cache_by_sample is not None and cache_by_sample.get(sample_id) != cache_sha:
            row_pass = False
        if not row_pass:
            failed_rows.append(sample_id)

    if outcome == "PASS":
        if seen != expected:
            raise EvidenceError("determinism does not cover both frozen anchors")
        if failed_rows:
            raise EvidenceError(
                "runtime determinism declares PASS with failed anchor rows"
            )
    elif not failed_rows and seen == expected:
        raise EvidenceError(
            "runtime determinism declares failure without a failed anchor"
        )
    return StageEvidence(
        outcome,
        {
            "anchors": sorted(seen),
            "failed_anchors": failed_rows,
            "sha256": sha256_file(path),
        },
    )


METRIC_ALIASES: dict[str, tuple[str, ...]] = {
    "official_score": ("official_score", "official_total_score", "score"),
    "adj_edge_jaccard": (
        "adj_edge_jaccard",
        "adjusted_edge_jaccard",
        "adjusted_edge_score",
    ),
    "edge_jaccard": ("edge_jaccard", "edge_score"),
    "division_jaccard": ("division_jaccard", "div_jaccard"),
    "edge_tp": ("edge_tp",),
    "edge_fp": ("edge_fp",),
    "edge_fn": ("edge_fn",),
    "division_tp": ("division_tp", "div_tp"),
    "division_fp": ("division_fp", "div_fp"),
    "division_fn": ("division_fn", "div_fn"),
    "num_pred_nodes": ("num_pred_nodes", "predicted_node_count", "t_pred"),
    "gt_node_count": ("gt_node_count",),
    "estimated_node_count": (
        "estimated_node_count",
        "gt_estimated_node_count",
        "t_true",
    ),
    "total_node_ratio": ("total_node_ratio", "node_count_ratio"),
    "node_count_penalty": (
        "node_count_penalty",
        "node_count_adjustment",
    ),
    "node_recall": ("node_recall",),
    "edges_fragmented": ("edges_fragmented", "fragmented_edges"),
    "edges_lost_to_detection": (
        "edges_lost_to_detection",
        "lost_to_detection_edges",
    ),
    "wrong_association_edges": ("wrong_association_edges",),
    "safe_div_candidate_count": (
        "safe_div_candidate_count",
        "safe_division_candidate_count",
    ),
    "accepted_division_count": (
        "accepted_division_count",
        "safe_div_accepted_count",
    ),
    "deepcenter_accepted_count": (
        "deepcenter_accepted_count",
        "deepcenter_safe_div_accepted_count",
    ),
    "deepcenter_rejected_count": (
        "deepcenter_rejected_count",
        "deepcenter_safe_div_rejected_count",
    ),
    "frame_cap_saturation": (
        "frame_cap_saturation",
        "frame_cap_saturation_rate",
    ),
    "global_cap_saturation": (
        "global_cap_saturation",
        "global_cap_saturation_rate",
    ),
    "runtime_seconds": ("runtime_seconds", "wall_clock_seconds"),
    "finalize_runtime_seconds": ("finalize_runtime_seconds",),
    "scoring_runtime_seconds": ("scoring_runtime_seconds",),
    "total_runtime_seconds": ("total_runtime_seconds",),
    "peak_memory_bytes": (
        "peak_memory_bytes",
        "peak_memory_peak_bytes",
    ),
    "pre_division_cache_sha256": (
        "pre_division_cache_sha256",
        "cache_sha256",
    ),
    "final_output_sha256": (
        "final_output_sha256",
        "output_sha256",
    ),
    "scorer_input_rows_sha256": ("scorer_input_rows_sha256",),
    "execution_order_index": ("execution_order_index",),
    "score_coordinate_semantics": ("score_coordinate_semantics",),
}

INTEGER_METRICS = {
    "edge_tp",
    "edge_fp",
    "edge_fn",
    "division_tp",
    "division_fp",
    "division_fn",
    "num_pred_nodes",
    "gt_node_count",
    "edges_fragmented",
    "edges_lost_to_detection",
    "wrong_association_edges",
    "safe_div_candidate_count",
    "accepted_division_count",
    "deepcenter_accepted_count",
    "deepcenter_rejected_count",
}

RATIO_METRICS = {
    "edge_jaccard",
    "division_jaccard",
    "node_recall",
    "frame_cap_saturation",
    "global_cap_saturation",
}


def metric_raw(row: Mapping[str, Any], field: str, label: str) -> Any:
    return first_present(row, METRIC_ALIASES[field], f"{label}.{field}")


def validation_row_hashes(
    root: Path, expected_samples: set[str]
) -> dict[tuple[str, str], str]:
    result: dict[tuple[str, str], str] = {}
    for arm in ARMS:
        path = root / EXPERIMENT_DIR / f"validation_rows_{arm}.csv"
        if not path.is_file():
            raise EvidenceError(f"validation rows are missing for {arm}")
        headers, raw_rows = load_csv(path)
        if tuple(headers) != VALIDATION_ROW_COLUMNS:
            raise EvidenceError(f"validation rows {arm} schema/order mismatch")
        grouped: dict[str, list[dict[str, Any]]] = {}
        closed_samples: set[str] = set()
        active_sample: str | None = None
        for index, raw in enumerate(raw_rows, 2):
            label = f"validation rows {arm}:{index}"
            sample_id = str(raw.get("dataset", ""))
            if sample_id not in expected_samples:
                raise EvidenceError(f"{label} has unexpected dataset {sample_id!r}")
            if sample_id != active_sample:
                if sample_id in closed_samples:
                    raise EvidenceError(
                        f"validation rows {arm}/{sample_id} are not contiguous"
                    )
                if active_sample is not None:
                    closed_samples.add(active_sample)
                active_sample = sample_id
            row = {
                "id": parse_int(raw.get("id"), f"{label}.id"),
                "dataset": sample_id,
                "row_type": str(raw.get("row_type", "")),
                "node_id": parse_int(
                    raw.get("node_id"), f"{label}.node_id", minimum=-1
                ),
                "t": parse_int(raw.get("t"), f"{label}.t", minimum=-1),
                "z": parse_int(raw.get("z"), f"{label}.z", minimum=-1),
                "y": parse_int(raw.get("y"), f"{label}.y", minimum=-1),
                "x": parse_int(raw.get("x"), f"{label}.x", minimum=-1),
                "source_id": parse_int(
                    raw.get("source_id"), f"{label}.source_id", minimum=-1
                ),
                "target_id": parse_int(
                    raw.get("target_id"), f"{label}.target_id", minimum=-1
                ),
            }
            sample_rows = grouped.setdefault(sample_id, [])
            if row["id"] != len(sample_rows):
                raise EvidenceError(
                    f"validation rows {arm}/{sample_id} IDs are not contiguous from zero"
                )
            if row["row_type"] == "node":
                if row["node_id"] < 0 or row["t"] < 0:
                    raise EvidenceError(f"{label} node identity/time is negative")
                if min(row[axis] for axis in ("z", "y", "x")) < 0:
                    raise EvidenceError(f"{label} node coordinates are not clamped")
                if (row["source_id"], row["target_id"]) != (-1, -1):
                    raise EvidenceError(f"{label} node edge placeholders are invalid")
            elif row["row_type"] == "edge":
                if tuple(row[key] for key in ("node_id", "t", "z", "y", "x")) != (
                    -1,
                    -1,
                    -1,
                    -1,
                    -1,
                ):
                    raise EvidenceError(f"{label} edge node placeholders are invalid")
                if (
                    row["source_id"] < 0
                    or row["target_id"] < 0
                    or row["source_id"] == row["target_id"]
                ):
                    raise EvidenceError(f"{label} edge endpoints are invalid")
            else:
                raise EvidenceError(f"{label} has invalid row_type")
            sample_rows.append(row)
        if set(grouped) != expected_samples:
            raise EvidenceError(
                f"validation rows {arm} sample coverage mismatch: "
                f"{len(grouped)}/{len(expected_samples)}"
            )
        for sample_id, rows in grouped.items():
            nodes: dict[int, int] = {}
            edge_pairs: set[tuple[int, int]] = set()
            indegree: Counter[int] = Counter()
            outdegree: Counter[int] = Counter()
            for row in rows:
                if row["row_type"] == "node":
                    node_id = int(row["node_id"])
                    if node_id in nodes:
                        raise EvidenceError(
                            f"validation rows {arm}/{sample_id} duplicate node {node_id}"
                        )
                    nodes[node_id] = int(row["t"])
            if not nodes:
                raise EvidenceError(f"validation rows {arm}/{sample_id} have no nodes")
            for row in rows:
                if row["row_type"] != "edge":
                    continue
                pair = (int(row["source_id"]), int(row["target_id"]))
                if pair in edge_pairs:
                    raise EvidenceError(
                        f"validation rows {arm}/{sample_id} duplicate edge {pair}"
                    )
                edge_pairs.add(pair)
                source, target = pair
                if source not in nodes or target not in nodes:
                    raise EvidenceError(
                        f"validation rows {arm}/{sample_id} contain a dangling edge"
                    )
                if nodes[target] != nodes[source] + 1:
                    raise EvidenceError(
                        f"validation rows {arm}/{sample_id} contain a non-next-frame edge"
                    )
                outdegree[source] += 1
                indegree[target] += 1
            if max(outdegree.values(), default=0) > 2:
                raise EvidenceError(
                    f"validation rows {arm}/{sample_id} outdegree exceeds two"
                )
            if max(indegree.values(), default=0) > 1:
                raise EvidenceError(
                    f"validation rows {arm}/{sample_id} indegree exceeds one"
                )
            result[(arm, sample_id)] = canonical_sha256(rows)
    return result


def validate_validation_rows(
    root: Path, expected_samples: set[str]
) -> tuple[StageEvidence, dict[tuple[str, str], str]]:
    hashes = validation_row_hashes(root, expected_samples)
    expected_count = len(ARMS) * len(expected_samples)
    if len(hashes) != expected_count:
        raise EvidenceError(
            f"validation-row sample coverage mismatch: {len(hashes)}/{expected_count}"
        )
    return (
        StageEvidence(
            "PASS",
            {
                "score_coordinate_semantics": SCORE_COORDINATE_SEMANTICS,
                "sample_hash_count": len(hashes),
                "file_sha256": {
                    arm: sha256_file(
                        root / EXPERIMENT_DIR / f"validation_rows_{arm}.csv"
                    )
                    for arm in ARMS
                },
            },
        ),
        hashes,
    )


def normalize_sample_metric_row(
    raw: Mapping[str, Any],
    index: int,
    *,
    expected_samples: set[str],
    frozen_embryo_by_sample: Mapping[str, str],
    cache_by_sample: Mapping[str, str] | None,
    validation_hashes: Mapping[tuple[str, str], str] | None,
    score_tolerance: float,
) -> dict[str, Any]:
    label = f"per-sample row {index}"
    arm = str(raw.get("arm", ""))
    sample_id = str(raw.get("sample_id", raw.get("stem", "")))
    embryo = str(raw.get("embryo_id", raw.get("embryo", "")))
    if arm not in ARMS:
        raise EvidenceError(f"{label} has invalid arm {arm!r}")
    if sample_id not in expected_samples:
        raise EvidenceError(f"{label} has unexpected sample {sample_id!r}")
    if embryo != frozen_embryo_by_sample.get(sample_id):
        raise EvidenceError(f"{label} embryo mismatch for {sample_id}")
    if "status" not in raw or not status_is_success(raw["status"]):
        raise EvidenceError(f"{label} is not RUN_COMPLETE/PASS")

    result: dict[str, Any] = {
        "arm": arm,
        "sample_id": sample_id,
        "embryo_id": embryo,
        "status": str(raw["status"]),
    }
    for field in INTEGER_METRICS:
        result[field] = parse_int(metric_raw(raw, field, label), f"{label}.{field}")
    if result["gt_node_count"] <= 0:
        raise EvidenceError(f"{label} has no positive actual GT node count")
    if raw.get("gt_node_count_evidence") != "ACTUAL_GT_GEFF_GRAPH_NUM_NODES":
        raise EvidenceError(f"{label} GT node-count evidence drifted")
    if (
        raw.get("estimated_node_count_evidence")
        != "GEFF_METADATA_ESTIMATED_NUMBER_OF_NODES"
    ):
        raise EvidenceError(f"{label} estimated node-count evidence drifted")
    result["gt_node_count_evidence"] = raw["gt_node_count_evidence"]
    result["estimated_node_count_evidence"] = raw["estimated_node_count_evidence"]
    result["estimated_node_count"] = parse_float(
        metric_raw(raw, "estimated_node_count", label),
        f"{label}.estimated_node_count",
        minimum=0.0,
    )
    if result["estimated_node_count"] is None or result["estimated_node_count"] <= 0:
        raise EvidenceError(f"{label} has no positive estimated node count")
    division_denominator = (
        result["division_tp"] + result["division_fp"] + result["division_fn"]
    )
    for field in (
        "official_score",
        "adj_edge_jaccard",
        "edge_jaccard",
        "division_jaccard",
        "total_node_ratio",
        "node_count_penalty",
        "node_recall",
        "frame_cap_saturation",
        "global_cap_saturation",
        "runtime_seconds",
        "finalize_runtime_seconds",
        "scoring_runtime_seconds",
        "total_runtime_seconds",
        "peak_memory_bytes",
    ):
        minimum = (
            0.0 if field not in {"total_node_ratio", "node_count_penalty"} else None
        )
        maximum = (
            1.0
            if field in RATIO_METRICS
            else 1.2
            if field in {"official_score", "adj_edge_jaccard"}
            else None
        )
        result[field] = parse_float(
            metric_raw(raw, field, label),
            f"{label}.{field}",
            minimum=minimum,
            maximum=maximum,
            allow_none=field == "division_jaccard" and division_denominator == 0,
        )
    topology_value = first_present(
        raw, ("topology_valid", "topology_pass"), f"{label}.topology_valid"
    )
    schema_value = first_present(
        raw, ("schema_valid", "schema_pass"), f"{label}.schema_valid"
    )
    result["topology_valid"] = parse_bool(topology_value, f"{label}.topology_valid")
    result["schema_valid"] = parse_bool(schema_value, f"{label}.schema_valid")
    result["execution_order_index"] = parse_int(
        metric_raw(raw, "execution_order_index", label),
        f"{label}.execution_order_index",
    )
    if result["execution_order_index"] not in {0, 1, 2}:
        raise EvidenceError(f"{label}.execution_order_index is outside 0..2")
    score_semantics = str(metric_raw(raw, "score_coordinate_semantics", label))
    if score_semantics != SCORE_COORDINATE_SEMANTICS:
        raise EvidenceError(f"{label} scoring coordinate semantics drifted")
    result["score_coordinate_semantics"] = score_semantics
    cache_sha = require_sha256(
        metric_raw(raw, "pre_division_cache_sha256", label),
        f"{label}.pre_division_cache_sha256",
    )
    output_sha = require_sha256(
        metric_raw(raw, "final_output_sha256", label),
        f"{label}.final_output_sha256",
    )
    scorer_input_sha = require_sha256(
        metric_raw(raw, "scorer_input_rows_sha256", label),
        f"{label}.scorer_input_rows_sha256",
    )
    if cache_by_sample is not None and cache_by_sample.get(sample_id) != cache_sha:
        raise EvidenceError(f"{label} cache SHA differs from canonical cache")
    result["pre_division_cache_sha256"] = cache_sha
    result["final_output_sha256"] = output_sha
    result["scorer_input_rows_sha256"] = scorer_input_sha
    expected_validation_sha = (
        validation_hashes.get((arm, sample_id))
        if validation_hashes is not None
        else None
    )
    if expected_validation_sha is not None and (
        output_sha != expected_validation_sha
        or scorer_input_sha != expected_validation_sha
    ):
        raise EvidenceError(
            f"{label} scorer/output SHA is not the actual rounded/clamped validation rows"
        )
    if scorer_input_sha != output_sha:
        raise EvidenceError(f"{label} scorer input differs from final output rows")
    if not close_enough(
        float(result["runtime_seconds"]),
        float(result["finalize_runtime_seconds"]),
        1e-9,
    ):
        raise EvidenceError(f"{label} runtime tie-break is not finalize-only")
    if float(result["total_runtime_seconds"]) + 1e-9 < (
        float(result["finalize_runtime_seconds"])
        + float(result["scoring_runtime_seconds"])
    ):
        raise EvidenceError(
            f"{label} total runtime is smaller than measured components"
        )

    recomputed = official_sample_metrics(
        result["edge_tp"],
        result["edge_fp"],
        result["edge_fn"],
        result["division_tp"],
        result["division_fp"],
        result["division_fn"],
        result["num_pred_nodes"],
        float(result["estimated_node_count"]),
    )
    for field in (
        "edge_jaccard",
        "division_jaccard",
        "total_node_ratio",
        "adj_edge_jaccard",
        "official_score",
        "node_count_penalty",
    ):
        expected = recomputed[field]
        actual = result[field]
        if expected is None:
            if field == "division_jaccard" and actual is None:
                continue
            raise EvidenceError(f"{label} has invalid undefined official {field}")
        if actual is None:
            raise EvidenceError(f"{label}.{field} must be finite")
        if not close_enough(float(actual), float(expected), score_tolerance):
            raise EvidenceError(
                f"{label}.{field} mismatch: declared={actual}, recomputed={expected}"
            )
    if result["accepted_division_count"] > result["safe_div_candidate_count"]:
        raise EvidenceError(f"{label} accepts more safe divisions than candidates")
    if (
        result["deepcenter_accepted_count"] + result["deepcenter_rejected_count"]
        > result["safe_div_candidate_count"]
    ):
        raise EvidenceError(f"{label} DeepCenter counts exceed safe-div candidates")
    return result


def validate_per_sample_metrics(
    root: Path,
    included_sample_ids: set[str],
    frozen_manifest: Mapping[str, Any],
    cache_by_sample: Mapping[str, str] | None,
    validation_hashes: Mapping[tuple[str, str], str],
    contract: Mapping[str, Any],
) -> tuple[StageEvidence, list[dict[str, Any]]]:
    path = root / PER_SAMPLE_PATH
    if not path.is_file():
        return StageEvidence("MISSING", {"path": str(PER_SAMPLE_PATH)}), []
    headers, rows = load_csv(path)
    if tuple(headers) != PER_SAMPLE_COLUMNS:
        raise EvidenceError("per_sample_metrics.csv schema/order mismatch")
    score_tolerance = float(
        contract["experiment_freeze"]["comparison_tolerances"][
            "reported_score_absolute"
        ]
    )
    frozen_embryo_by_sample = {
        row["sample_id"]: row["embryo_id"] for row in frozen_manifest.get("samples", [])
    }
    payload_headers, payload_rows = load_csv(root / PAYLOAD_INVENTORY_PATH)
    if tuple(payload_headers) != PAYLOAD_COLUMNS:
        raise EvidenceError("per-sample metrics saw a noncanonical payload inventory")
    payload_counts = {
        str(row["sample_id"]): {
            "gt_node_count": parse_int(
                row.get("gt_node_count"),
                f"payload {row.get('sample_id')}.gt_node_count",
            ),
            "estimated_node_count": parse_float(
                row.get("estimated_node_count"),
                f"payload {row.get('sample_id')}.estimated_node_count",
                minimum=0.0,
            ),
        }
        for row in payload_rows
    }
    expected_keys = {
        (arm, sample_id) for arm in ARMS for sample_id in included_sample_ids
    }
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for index, raw in enumerate(rows, 2):
        row = normalize_sample_metric_row(
            raw,
            index,
            expected_samples=included_sample_ids,
            frozen_embryo_by_sample=frozen_embryo_by_sample,
            cache_by_sample=cache_by_sample,
            validation_hashes=validation_hashes,
            score_tolerance=score_tolerance,
        )
        key = (row["arm"], row["sample_id"])
        if key in seen:
            raise EvidenceError(f"per-sample metrics duplicate {key}")
        payload_count = payload_counts.get(row["sample_id"])
        if (
            payload_count is None
            or row["gt_node_count"] != payload_count["gt_node_count"]
            or not close_enough(
                float(row["estimated_node_count"]),
                float(payload_count["estimated_node_count"]),
                score_tolerance,
            )
        ):
            raise EvidenceError(
                f"per-sample GT/estimated node evidence drift for {key}"
            )
        seen.add(key)
        normalized.append(row)
    if seen != expected_keys:
        missing = sorted(expected_keys - seen)
        extra = sorted(seen - expected_keys)
        raise EvidenceError(
            f"per-sample metric coverage mismatch: missing={missing[:10]}, extra={extra[:10]}"
        )
    topology_ok = all(
        row["topology_valid"] and row["schema_valid"] for row in normalized
    )
    expected_order_counts = {
        "R70": {0: 67, 1: 66, 2: 66},
        "R80": {0: 66, 1: 67, 2: 66},
        "R90": {0: 66, 1: 66, 2: 67},
    }
    actual_order_counts = {
        arm: dict(
            sorted(
                Counter(
                    row["execution_order_index"]
                    for row in normalized
                    if row["arm"] == arm
                ).items()
            )
        )
        for arm in ARMS
    }
    if len(included_sample_ids) == EXPECTED_SAMPLE_COUNT and (
        actual_order_counts != expected_order_counts
    ):
        raise EvidenceError(
            "per-sample execution order does not match rotation-by-sample-index"
        )
    return (
        StageEvidence(
            # A candidate topology failure is a valid measured result: it must
            # fail that candidate's promotion gate, not make the metrics file
            # unverifiable.  R70 failures are handled by terminal-state logic.
            "PASS",
            {
                "rows": len(normalized),
                "expected_rows": len(expected_keys),
                "sample_count_per_arm": len(included_sample_ids),
                "topology_and_schema_all_pass": topology_ok,
                "execution_order_position_counts": actual_order_counts,
                "sha256": sha256_file(path),
            },
        ),
        normalized,
    )


def compare_number(
    raw: Mapping[str, Any],
    field: str,
    expected: float | int | None,
    label: str,
    tolerance: float,
) -> None:
    actual = parse_float(
        metric_raw(raw, field, label),
        f"{label}.{field}",
        allow_none=expected is None,
    )
    if expected is None:
        if actual is not None:
            raise EvidenceError(f"{label}.{field} should be null")
        return
    if actual is None or not close_enough(float(actual), float(expected), tolerance):
        raise EvidenceError(
            f"{label}.{field} mismatch: declared={actual}, recomputed={expected}"
        )


def validate_per_embryo_metrics(
    root: Path,
    sample_rows: Sequence[Mapping[str, Any]],
    contract: Mapping[str, Any],
) -> tuple[StageEvidence, dict[tuple[str, str], dict[str, Any]]]:
    path = root / PER_EMBRYO_PATH
    if not path.is_file():
        return StageEvidence("MISSING", {"path": str(PER_EMBRYO_PATH)}), {}
    headers, rows = load_csv(path)
    if tuple(headers) != PER_EMBRYO_COLUMNS:
        raise EvidenceError("per_embryo_metrics.csv schema/order mismatch")
    tolerance = float(
        contract["experiment_freeze"]["comparison_tolerances"][
            "reported_score_absolute"
        ]
    )
    expected_keys = {(arm, embryo) for arm in ARMS for embryo in EMBRYOS}
    declared: dict[tuple[str, str], dict[str, Any]] = {}
    recomputed: dict[tuple[str, str], dict[str, Any]] = {}
    for arm, embryo in sorted(expected_keys):
        source = [
            row
            for row in sample_rows
            if row["arm"] == arm and row["embryo_id"] == embryo
        ]
        aggregate = aggregate_metric_rows(source)
        if aggregate["division_jaccard"] is None:
            raise EvidenceError(
                f"per-embryo {(arm, embryo)} division_jaccard is undefined: "
                "aggregate division TP+FP+FN is zero"
            )
        recomputed[(arm, embryo)] = aggregate
    for index, raw in enumerate(rows, 2):
        arm = str(raw.get("arm", ""))
        embryo = str(raw.get("embryo_id", raw.get("embryo", "")))
        key = (arm, embryo)
        if key not in expected_keys or key in declared:
            raise EvidenceError(f"invalid/duplicate per-embryo row {key}")
        if "status" in raw and not status_is_success(raw["status"]):
            raise EvidenceError(f"per-embryo row {key} is not complete")
        expected = recomputed[key]
        actual_count = parse_int(
            first_present(raw, ("sample_count", "n"), f"per-embryo {key}"),
            f"per-embryo {key}.sample_count",
        )
        if actual_count != expected["sample_count"]:
            raise EvidenceError(f"per-embryo sample count mismatch for {key}")
        for field in (
            "official_score",
            "adj_edge_jaccard",
            "edge_jaccard",
            "division_jaccard",
            "estimated_node_count",
            "total_node_ratio",
            "node_count_penalty",
            "node_recall",
            "frame_cap_saturation",
            "global_cap_saturation",
            "runtime_seconds",
            "finalize_runtime_seconds",
            "scoring_runtime_seconds",
            "total_runtime_seconds",
            "peak_memory_bytes",
        ):
            compare_number(raw, field, expected[field], f"per-embryo {key}", tolerance)
        for rate_field, source_field in (
            ("frame_cap_saturation_rate", "frame_cap_saturation"),
            ("global_cap_saturation_rate", "global_cap_saturation"),
        ):
            declared_rate = parse_float(
                raw.get(rate_field), f"per-embryo {key}.{rate_field}", minimum=0.0
            )
            if declared_rate is None or not close_enough(
                float(declared_rate), float(expected[source_field]), tolerance
            ):
                raise EvidenceError(f"per-embryo {key}.{rate_field} mismatch")
        for field in INTEGER_METRICS:
            if field not in expected:
                continue
            actual = parse_int(
                metric_raw(raw, field, f"per-embryo {key}"), f"{key}.{field}"
            )
            if actual != expected[field]:
                raise EvidenceError(
                    f"per-embryo {key}.{field} mismatch: {actual}!={expected[field]}"
                )
        for field in ("topology_valid", "schema_valid"):
            declared_flag = parse_bool(
                first_present(raw, (field,), f"per-embryo {key}"),
                f"per-embryo {key}.{field}",
            )
            expected_flag = all(
                bool(row[field])
                for row in sample_rows
                if row["arm"] == arm and row["embryo_id"] == embryo
            )
            if declared_flag != expected_flag:
                raise EvidenceError(f"per-embryo {key}.{field} mismatch")
        if (
            raw.get("estimated_node_count_evidence")
            != expected["estimated_node_count_evidence"]
        ):
            raise EvidenceError(
                f"per-embryo {key} estimated-node-count evidence drifted"
            )
        if raw.get("gt_node_count_evidence") != expected["gt_node_count_evidence"]:
            raise EvidenceError(f"per-embryo {key} GT node-count evidence drifted")
        if raw.get("hash_aggregation") != SAMPLE_HASH_AGGREGATION:
            raise EvidenceError(f"per-embryo {key} hash aggregation drifted")
        for field in (
            "pre_division_cache_sha256",
            "final_output_sha256",
            "scorer_input_rows_sha256",
        ):
            actual_sha = require_sha256(raw.get(field), f"per-embryo {key}.{field}")
            if actual_sha != expected[field]:
                raise EvidenceError(f"per-embryo {key}.{field} mismatch")
        declared[key] = dict(raw)
    if set(declared) != expected_keys:
        raise EvidenceError("per-embryo metrics do not contain exactly six rows")
    return (
        StageEvidence(
            "PASS",
            {
                "rows": len(declared),
                "sha256": sha256_file(path),
            },
        ),
        recomputed,
    )


def macro_and_micro(
    embryo_metrics: Mapping[tuple[str, str], Mapping[str, Any]],
    sample_rows: Sequence[Mapping[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    macro_fields = (
        "official_score",
        "adj_edge_jaccard",
        "edge_jaccard",
        "division_jaccard",
        "node_count_penalty",
        "total_node_ratio",
        "node_recall",
        "frame_cap_saturation",
        "global_cap_saturation",
    )
    for arm in ARMS:
        embryos = [embryo_metrics[(arm, embryo)] for embryo in EMBRYOS]
        for embryo, row in zip(EMBRYOS, embryos):
            if row.get("division_jaccard") is None:
                raise EvidenceError(
                    f"per-embryo {(arm, embryo)} division_jaccard must be finite"
                )
        macro = {
            field: sum(float(row[field]) for row in embryos) / len(embryos)
            for field in macro_fields
        }
        macro["sample_count"] = sum(int(row["sample_count"]) for row in embryos)
        for field in (
            "edge_tp",
            "edge_fp",
            "edge_fn",
            "division_tp",
            "division_fp",
            "division_fn",
            "num_pred_nodes",
            "gt_node_count",
            "estimated_node_count",
            "edges_fragmented",
            "edges_lost_to_detection",
            "wrong_association_edges",
            "safe_div_candidate_count",
            "accepted_division_count",
            "deepcenter_accepted_count",
            "deepcenter_rejected_count",
        ):
            macro[field] = None
        macro.update(
            {
                "status": "RUN_COMPLETE",
                "estimated_node_count_evidence": (
                    "NOT_APPLICABLE_EMBRYO_EQUAL_MACRO_NONADDITIVE"
                ),
                "gt_node_count_evidence": (
                    "NOT_APPLICABLE_EMBRYO_EQUAL_MACRO_NONADDITIVE"
                ),
                "topology_valid": all(bool(row["topology_valid"]) for row in embryos),
                "schema_valid": all(bool(row["schema_valid"]) for row in embryos),
                "runtime_seconds": sum(
                    float(row["runtime_seconds"]) for row in embryos
                ),
                "finalize_runtime_seconds": sum(
                    float(row["finalize_runtime_seconds"]) for row in embryos
                ),
                "scoring_runtime_seconds": sum(
                    float(row["scoring_runtime_seconds"]) for row in embryos
                ),
                "total_runtime_seconds": sum(
                    float(row["total_runtime_seconds"]) for row in embryos
                ),
                "peak_memory_bytes": max(
                    float(row["peak_memory_bytes"]) for row in embryos
                ),
                "pre_division_cache_sha256": ordered_embryo_sha256(
                    list(zip(EMBRYOS, embryos)), "pre_division_cache_sha256"
                ),
                "final_output_sha256": ordered_embryo_sha256(
                    list(zip(EMBRYOS, embryos)), "final_output_sha256"
                ),
                "scorer_input_rows_sha256": ordered_embryo_sha256(
                    list(zip(EMBRYOS, embryos)), "scorer_input_rows_sha256"
                ),
                "hash_aggregation": EMBRYO_HASH_AGGREGATION,
            }
        )
        result[(arm, "EMBRYO_EQUAL_MACRO")] = macro
        pooled_rows = [row for row in sample_rows if row["arm"] == arm]
        pooled = aggregate_metric_rows(pooled_rows)
        if pooled["division_jaccard"] is None:
            raise EvidenceError(
                f"pooled-micro {arm} division_jaccard is undefined: "
                "aggregate division TP+FP+FN is zero"
            )
        result[(arm, "POOLED_MICRO")] = pooled
    return result


def normalize_scope(value: Any) -> str:
    text = str(value).strip().upper().replace("-", "_").replace(" ", "_")
    aliases = {
        "MACRO": "EMBRYO_EQUAL_MACRO",
        "EMBRYO_MACRO": "EMBRYO_EQUAL_MACRO",
        "EMBRYO_EQUAL": "EMBRYO_EQUAL_MACRO",
        "MICRO": "POOLED_MICRO",
        "GLOBAL": "POOLED_MICRO",
        "POOLED": "POOLED_MICRO",
    }
    return aliases.get(text, text)


def validate_micro_macro(
    root: Path,
    aggregates: Mapping[tuple[str, str], Mapping[str, Any]],
    contract: Mapping[str, Any],
) -> StageEvidence:
    path = root / MICRO_MACRO_PATH
    if not path.is_file():
        return StageEvidence("MISSING", {"path": str(MICRO_MACRO_PATH)})
    headers, rows = load_csv(path)
    if tuple(headers) != MICRO_MACRO_COLUMNS:
        raise EvidenceError("micro_macro_comparison.csv schema/order mismatch")
    tolerance = float(
        contract["experiment_freeze"]["comparison_tolerances"][
            "reported_score_absolute"
        ]
    )
    expected_keys = set(aggregates)
    seen: set[tuple[str, str]] = set()
    for index, raw in enumerate(rows, 2):
        arm = str(raw.get("arm", ""))
        scope = normalize_scope(raw.get("scope", raw.get("aggregation", "")))
        key = (arm, scope)
        if key not in expected_keys or key in seen:
            raise EvidenceError(f"invalid/duplicate micro-macro row {key}")
        expected = aggregates[key]
        if not status_is_success(raw.get("status")):
            raise EvidenceError(f"micro-macro {key} is not complete")
        expected_embryo = "ALL" if scope == "POOLED_MICRO" else "EQUAL_44b6_6bba"
        if raw.get("embryo_id") != expected_embryo:
            raise EvidenceError(f"micro-macro {key} embryo scope marker drifted")
        count = parse_int(
            first_present(raw, ("sample_count", "n"), f"micro-macro {key}"),
            f"micro-macro {key}.sample_count",
        )
        if count != expected["sample_count"]:
            raise EvidenceError(f"micro-macro sample count mismatch for {key}")
        for field in (
            "official_score",
            "adj_edge_jaccard",
            "edge_jaccard",
            "division_jaccard",
            "node_count_penalty",
            "estimated_node_count",
            "total_node_ratio",
            "node_recall",
            "frame_cap_saturation",
            "global_cap_saturation",
            "runtime_seconds",
            "finalize_runtime_seconds",
            "scoring_runtime_seconds",
            "total_runtime_seconds",
            "peak_memory_bytes",
        ):
            compare_number(raw, field, expected[field], f"micro-macro {key}", tolerance)
        for field in INTEGER_METRICS:
            expected_value = expected.get(field)
            actual_raw = metric_raw(raw, field, f"micro-macro {key}")
            if expected_value is None:
                if str(actual_raw).strip().lower() not in {"", "none", "null", "nan"}:
                    raise EvidenceError(f"micro-macro {key}.{field} should be null")
            else:
                actual = parse_int(
                    metric_raw(raw, field, f"micro-macro {key}"), f"{key}.{field}"
                )
                if actual != expected_value:
                    raise EvidenceError(f"micro-macro {key}.{field} mismatch")
        for field in ("topology_valid", "schema_valid"):
            if parse_bool(raw.get(field), f"micro-macro {key}.{field}") != bool(
                expected[field]
            ):
                raise EvidenceError(f"micro-macro {key}.{field} mismatch")
        if (
            raw.get("estimated_node_count_evidence")
            != expected["estimated_node_count_evidence"]
        ):
            raise EvidenceError(
                f"micro-macro {key} estimated-node-count evidence drifted"
            )
        if raw.get("gt_node_count_evidence") != expected["gt_node_count_evidence"]:
            raise EvidenceError(f"micro-macro {key} GT node-count evidence drifted")
        expected_aggregation = (
            SAMPLE_HASH_AGGREGATION
            if scope == "POOLED_MICRO"
            else EMBRYO_HASH_AGGREGATION
        )
        if raw.get("hash_aggregation") != expected_aggregation:
            raise EvidenceError(f"micro-macro {key} hash aggregation drifted")
        for field in (
            "pre_division_cache_sha256",
            "final_output_sha256",
            "scorer_input_rows_sha256",
        ):
            actual_sha = require_sha256(raw.get(field), f"micro-macro {key}.{field}")
            if actual_sha != expected[field]:
                raise EvidenceError(f"micro-macro {key}.{field} mismatch")
        seen.add(key)
    if seen != expected_keys:
        raise EvidenceError(
            "micro_macro_comparison.csv must contain six arm/scope rows"
        )
    return StageEvidence("PASS", {"rows": len(seen), "sha256": sha256_file(path)})


def delta_column(raw: Mapping[str, Any], field: str, label: str) -> float:
    aliases: tuple[str, ...] = (
        f"delta_{field}",
        f"{field}_delta",
        f"delta_candidate_vs_control_{field}",
    )
    if field in {"frame_cap_saturation", "global_cap_saturation"}:
        aliases += (f"{field}_rate_delta",)
    return float(parse_float(first_present(raw, aliases, label), f"{label}.{field}"))


def nullable_delta_column(
    raw: Mapping[str, Any], field: str, label: str
) -> float | None:
    aliases: tuple[str, ...] = (
        f"delta_{field}",
        f"{field}_delta",
        f"delta_candidate_vs_control_{field}",
    )
    return parse_float(
        first_present(raw, aliases, label),
        f"{label}.{field}",
        allow_none=True,
    )


def validate_nullable_delta(
    raw: Mapping[str, Any],
    field: str,
    candidate_value: float | None,
    control_value: float | None,
    label: str,
    tolerance: float,
) -> None:
    actual = nullable_delta_column(raw, field, label)
    if candidate_value is None or control_value is None:
        if actual is not None:
            raise EvidenceError(
                f"{label}.{field} delta must be null when either arm is undefined"
            )
        return
    expected = float(candidate_value) - float(control_value)
    if actual is None or not close_enough(actual, expected, tolerance):
        raise EvidenceError(f"{label}.{field} delta mismatch")


def validate_paired_deltas(
    root: Path,
    sample_rows: Sequence[Mapping[str, Any]],
    embryo_metrics: Mapping[tuple[str, str], Mapping[str, Any]],
    contract: Mapping[str, Any],
) -> tuple[StageEvidence, dict[tuple[str, str], float]]:
    sample_path = root / PAIRED_SAMPLE_PATH
    embryo_path = root / PAIRED_EMBRYO_PATH
    if not sample_path.is_file() or not embryo_path.is_file():
        return (
            StageEvidence(
                "MISSING",
                {
                    "sample_exists": sample_path.is_file(),
                    "embryo_exists": embryo_path.is_file(),
                },
            ),
            {},
        )
    tolerance = float(
        contract["experiment_freeze"]["comparison_tolerances"][
            "reported_score_absolute"
        ]
    )
    sample_index = {(row["arm"], row["sample_id"]): row for row in sample_rows}
    included = {row["sample_id"] for row in sample_rows if row["arm"] == "R70"}
    sample_headers, sample_delta_rows = load_csv(sample_path)
    if tuple(sample_headers) != PAIRED_SAMPLE_COLUMNS:
        raise EvidenceError("paired_deltas_by_sample.csv schema/order mismatch")
    expected_sample_keys = {
        (candidate, sample_id) for candidate in CANDIDATES for sample_id in included
    }
    seen_sample: set[tuple[str, str]] = set()
    official_sample_deltas: dict[tuple[str, str], float] = {}
    for index, raw in enumerate(sample_delta_rows, 2):
        candidate = str(
            raw.get("candidate_arm", raw.get("arm", raw.get("candidate", "")))
        )
        control = str(raw.get("control_arm", "R70"))
        sample_id = str(raw.get("sample_id", raw.get("stem", "")))
        embryo = str(raw.get("embryo_id", raw.get("embryo", "")))
        key = (candidate, sample_id)
        if key not in expected_sample_keys or key in seen_sample or control != "R70":
            raise EvidenceError(f"invalid/duplicate paired-sample row {key}")
        candidate_row = sample_index[(candidate, sample_id)]
        control_row = sample_index[("R70", sample_id)]
        if embryo != control_row["embryo_id"]:
            raise EvidenceError(f"paired-sample embryo mismatch for {key}")
        for field in (
            "official_score",
            "adj_edge_jaccard",
            "edge_jaccard",
            "node_count_penalty",
        ):
            expected = float(candidate_row[field]) - float(control_row[field])
            actual = delta_column(raw, field, f"paired-sample {key}")
            if not close_enough(actual, expected, tolerance):
                raise EvidenceError(f"paired-sample {key}.{field} delta mismatch")
            if field == "official_score":
                official_sample_deltas[key] = expected
        validate_nullable_delta(
            raw,
            "division_jaccard",
            candidate_row["division_jaccard"],
            control_row["division_jaccard"],
            f"paired-sample {key}",
            tolerance,
        )
        for field in (
            "division_tp",
            "division_fp",
            "division_fn",
            "edge_tp",
            "edge_fp",
            "edge_fn",
            "num_pred_nodes",
            "gt_node_count",
            "edges_fragmented",
            "edges_lost_to_detection",
            "wrong_association_edges",
            "safe_div_candidate_count",
            "accepted_division_count",
            "deepcenter_accepted_count",
            "deepcenter_rejected_count",
        ):
            expected_int = int(candidate_row[field]) - int(control_row[field])
            actual_int = delta_column(raw, field, f"paired-sample {key}")
            if not close_enough(actual_int, expected_int, 0.0):
                raise EvidenceError(f"paired-sample {key}.{field} delta mismatch")
        for field in (
            "estimated_node_count",
            "total_node_ratio",
            "node_recall",
            "frame_cap_saturation",
            "global_cap_saturation",
            "runtime_seconds",
            "finalize_runtime_seconds",
            "scoring_runtime_seconds",
            "total_runtime_seconds",
            "peak_memory_bytes",
        ):
            expected = float(candidate_row[field]) - float(control_row[field])
            actual = delta_column(raw, field, f"paired-sample {key}")
            if not close_enough(actual, expected, tolerance):
                raise EvidenceError(f"paired-sample {key}.{field} delta mismatch")
        for field in ("topology_valid", "schema_valid"):
            expected_flag = bool(candidate_row[field] and control_row[field])
            declared_flag = parse_bool(
                raw.get(f"{field.removesuffix('_valid')}_both_valid"),
                f"paired-sample {key}.{field}",
            )
            if declared_flag != expected_flag:
                raise EvidenceError(f"paired-sample {key}.{field} flag mismatch")
        cache_equal = (
            candidate_row["pre_division_cache_sha256"]
            == control_row["pre_division_cache_sha256"]
        )
        if (
            parse_bool(
                raw.get("pre_division_cache_sha256_equal"),
                f"paired-sample {key}.pre_division_cache_sha256_equal",
            )
            != cache_equal
            or not cache_equal
        ):
            raise EvidenceError(f"paired-sample {key} did not share the cache")
        control_output = require_sha256(
            raw.get("control_final_output_sha256"),
            f"paired-sample {key}.control_final_output_sha256",
        )
        candidate_output = require_sha256(
            raw.get("candidate_final_output_sha256"),
            f"paired-sample {key}.candidate_final_output_sha256",
        )
        if (
            control_output != control_row["final_output_sha256"]
            or candidate_output != candidate_row["final_output_sha256"]
            or parse_bool(
                raw.get("final_output_sha256_equal"),
                f"paired-sample {key}.final_output_sha256_equal",
            )
            != (candidate_output == control_output)
        ):
            raise EvidenceError(f"paired-sample {key} output SHA binding drifted")
        seen_sample.add(key)
    if seen_sample != expected_sample_keys:
        raise EvidenceError("paired sample deltas do not cover both candidates")

    embryo_headers, embryo_delta_rows = load_csv(embryo_path)
    if tuple(embryo_headers) != PAIRED_EMBRYO_COLUMNS:
        raise EvidenceError("paired_deltas_by_embryo.csv schema/order mismatch")
    expected_embryo_keys = {
        (candidate, embryo) for candidate in CANDIDATES for embryo in EMBRYOS
    }
    seen_embryo: set[tuple[str, str]] = set()
    for index, raw in enumerate(embryo_delta_rows, 2):
        candidate = str(
            raw.get("candidate_arm", raw.get("arm", raw.get("candidate", "")))
        )
        control = str(raw.get("control_arm", "R70"))
        embryo = str(raw.get("embryo_id", raw.get("embryo", "")))
        key = (candidate, embryo)
        if key not in expected_embryo_keys or key in seen_embryo or control != "R70":
            raise EvidenceError(f"invalid/duplicate paired-embryo row {key}")
        candidate_row = embryo_metrics[(candidate, embryo)]
        control_row = embryo_metrics[("R70", embryo)]
        declared_count = parse_int(
            first_present(raw, ("sample_count", "n"), f"paired-embryo {key}"),
            f"paired-embryo {key}.sample_count",
        )
        if (
            declared_count != candidate_row["sample_count"]
            or declared_count != control_row["sample_count"]
        ):
            raise EvidenceError(f"paired-embryo {key} sample count mismatch")
        for field in (
            "official_score",
            "adj_edge_jaccard",
            "edge_jaccard",
            "division_jaccard",
            "node_count_penalty",
        ):
            expected = float(candidate_row[field]) - float(control_row[field])
            actual = delta_column(raw, field, f"paired-embryo {key}")
            if not close_enough(actual, expected, tolerance):
                raise EvidenceError(f"paired-embryo {key}.{field} delta mismatch")
        for field in (
            "division_tp",
            "division_fp",
            "division_fn",
            "edge_tp",
            "edge_fp",
            "edge_fn",
            "num_pred_nodes",
            "gt_node_count",
            "edges_fragmented",
            "edges_lost_to_detection",
            "wrong_association_edges",
            "safe_div_candidate_count",
            "accepted_division_count",
            "deepcenter_accepted_count",
            "deepcenter_rejected_count",
        ):
            expected_int = int(candidate_row[field]) - int(control_row[field])
            actual_int = delta_column(raw, field, f"paired-embryo {key}")
            if not close_enough(actual_int, expected_int, 0.0):
                raise EvidenceError(f"paired-embryo {key}.{field} delta mismatch")
        for field in (
            "estimated_node_count",
            "total_node_ratio",
            "node_recall",
            "frame_cap_saturation",
            "global_cap_saturation",
            "runtime_seconds",
            "finalize_runtime_seconds",
            "scoring_runtime_seconds",
            "total_runtime_seconds",
            "peak_memory_bytes",
        ):
            expected = float(candidate_row[field]) - float(control_row[field])
            actual = delta_column(raw, field, f"paired-embryo {key}")
            if not close_enough(actual, expected, tolerance):
                raise EvidenceError(f"paired-embryo {key}.{field} delta mismatch")
        for field in ("topology_valid", "schema_valid"):
            expected_flag = bool(candidate_row[field] and control_row[field])
            declared_flag = parse_bool(
                raw.get(f"{field.removesuffix('_valid')}_both_valid"),
                f"paired-embryo {key}.{field}",
            )
            if declared_flag != expected_flag:
                raise EvidenceError(f"paired-embryo {key}.{field} flag mismatch")
        cache_equal = (
            candidate_row["pre_division_cache_sha256"]
            == control_row["pre_division_cache_sha256"]
        )
        if (
            parse_bool(
                raw.get("pre_division_cache_sha256_equal"),
                f"paired-embryo {key}.pre_division_cache_sha256_equal",
            )
            != cache_equal
            or not cache_equal
        ):
            raise EvidenceError(f"paired-embryo {key} did not share the cache")
        control_output = require_sha256(
            raw.get("control_final_output_sha256"),
            f"paired-embryo {key}.control_final_output_sha256",
        )
        candidate_output = require_sha256(
            raw.get("candidate_final_output_sha256"),
            f"paired-embryo {key}.candidate_final_output_sha256",
        )
        if (
            control_output != control_row["final_output_sha256"]
            or candidate_output != candidate_row["final_output_sha256"]
            or parse_bool(
                raw.get("final_output_sha256_equal"),
                f"paired-embryo {key}.final_output_sha256_equal",
            )
            != (candidate_output == control_output)
        ):
            raise EvidenceError(f"paired-embryo {key} output SHA binding drifted")
        seen_embryo.add(key)
    if seen_embryo != expected_embryo_keys:
        raise EvidenceError("paired embryo deltas do not cover four comparisons")
    return (
        StageEvidence(
            "PASS",
            {
                "sample_rows": len(seen_sample),
                "embryo_rows": len(seen_embryo),
                "sample_sha256": sha256_file(sample_path),
                "embryo_sha256": sha256_file(embryo_path),
            },
        ),
        official_sample_deltas,
    )


def validate_division_confusion(
    root: Path,
    embryo_metrics: Mapping[tuple[str, str], Mapping[str, Any]],
    aggregates: Mapping[tuple[str, str], Mapping[str, Any]],
    contract: Mapping[str, Any],
) -> StageEvidence:
    path = root / DIVISION_CONFUSION_PATH
    if not path.is_file():
        return StageEvidence("MISSING", {"path": str(DIVISION_CONFUSION_PATH)})
    value = load_json(path)
    if value.get("task_id") != TASK_ID:
        raise EvidenceError("division confusion task_id mismatch")
    arms_value = value.get("arms")
    if not isinstance(arms_value, dict) or set(arms_value) != set(ARMS):
        raise EvidenceError("division confusion must contain exactly three arms")
    tolerance = float(
        contract["experiment_freeze"]["comparison_tolerances"][
            "reported_score_absolute"
        ]
    )
    comparisons = 0
    for arm in ARMS:
        arm_value = arms_value[arm]
        if not isinstance(arm_value, dict):
            raise EvidenceError(f"division confusion {arm} must be an object")
        embryo_value = arm_value.get("embryos", arm_value)
        if not isinstance(embryo_value, dict):
            raise EvidenceError(f"division confusion {arm}.embryos is malformed")
        for embryo in EMBRYOS:
            declared = embryo_value.get(embryo)
            if not isinstance(declared, dict):
                raise EvidenceError(f"division confusion lacks {arm}/{embryo}")
            expected = embryo_metrics[(arm, embryo)]
            for field in ("division_tp", "division_fp", "division_fn"):
                actual = parse_int(
                    first_present(
                        declared,
                        METRIC_ALIASES[field],
                        f"division confusion {arm}/{embryo}",
                    ),
                    f"division confusion {arm}/{embryo}.{field}",
                )
                if actual != expected[field]:
                    raise EvidenceError(
                        f"division confusion {arm}/{embryo}.{field} mismatch"
                    )
            actual_jaccard = parse_float(
                first_present(
                    declared,
                    METRIC_ALIASES["division_jaccard"],
                    f"division confusion {arm}/{embryo}",
                ),
                f"division confusion {arm}/{embryo}.division_jaccard",
            )
            if not close_enough(
                float(actual_jaccard),
                float(expected["division_jaccard"]),
                tolerance,
            ):
                raise EvidenceError(
                    f"division confusion {arm}/{embryo} Jaccard mismatch"
                )
            comparisons += 1
        pooled = optional_present(arm_value, ("global", "pooled_micro", "pooled"), None)
        if not isinstance(pooled, dict):
            raise EvidenceError(f"division confusion lacks {arm} pooled/global")
        expected_pooled = aggregates[(arm, "POOLED_MICRO")]
        for field in ("division_tp", "division_fp", "division_fn"):
            actual = parse_int(
                first_present(
                    pooled,
                    METRIC_ALIASES[field],
                    f"division confusion {arm}/pooled",
                ),
                f"division confusion {arm}/pooled.{field}",
            )
            if actual != expected_pooled[field]:
                raise EvidenceError(f"division confusion {arm}/pooled.{field} mismatch")
        actual_jaccard = parse_float(
            first_present(
                pooled,
                METRIC_ALIASES["division_jaccard"],
                f"division confusion {arm}/pooled",
            ),
            f"division confusion {arm}/pooled.division_jaccard",
        )
        if not close_enough(
            float(actual_jaccard),
            float(expected_pooled["division_jaccard"]),
            tolerance,
        ):
            raise EvidenceError(f"division confusion {arm}/pooled mismatch")
        comparisons += 1
    return StageEvidence(
        "PASS",
        {"comparisons": comparisons, "sha256": sha256_file(path)},
    )


def validate_topology_evidence(
    root: Path,
    included_sample_ids: set[str],
    sample_rows: Sequence[Mapping[str, Any]],
) -> StageEvidence:
    path = root / TOPOLOGY_PATH
    if not path.is_file():
        return StageEvidence("MISSING", {"path": str(TOPOLOGY_PATH)})
    value = load_json(path)
    if value.get("task_id") != TASK_ID:
        raise EvidenceError("topology validation task_id mismatch")
    declared_outcome = stage_declared_outcome(value, "topology validation")
    rows = evidence_rows(value, "topology validation")
    expected = {(arm, sample) for arm in ARMS for sample in included_sample_ids}
    metric_index = {
        (str(row["arm"]), str(row["sample_id"])): row for row in sample_rows
    }
    seen: set[tuple[str, str]] = set()
    failed: list[tuple[str, str]] = []
    for index, row in enumerate(rows):
        arm = str(row.get("arm", ""))
        sample_id = str(row.get("sample_id", row.get("stem", "")))
        key = (arm, sample_id)
        if key not in expected or key in seen:
            raise EvidenceError(f"invalid/duplicate topology row {key}")
        topology_ok = parse_bool(
            first_present(
                row,
                ("topology_valid", "topology_pass"),
                f"topology row {index}",
            ),
            f"topology {key}",
        )
        schema_ok = parse_bool(
            first_present(
                row,
                ("schema_valid", "schema_pass"),
                f"topology row {index}",
            ),
            f"schema {key}",
        )
        row_ok = topology_ok and schema_ok
        if "pass" in row:
            if parse_bool(row["pass"], f"topology {key}.pass") != row_ok:
                raise EvidenceError(f"topology composite pass drift for {key}")
        metric_row = metric_index.get(key)
        if metric_row is None:
            raise EvidenceError(f"topology evidence has no metric row for {key}")
        if (
            bool(metric_row["topology_valid"]) != topology_ok
            or bool(metric_row["schema_valid"]) != schema_ok
        ):
            raise EvidenceError(f"topology evidence differs from metrics for {key}")
        if not row_ok:
            failed.append(key)
        seen.add(key)
    if seen != expected:
        raise EvidenceError("topology evidence coverage differs from metrics")
    computed_outcome = "PASS" if not failed else "FAIL"
    if declared_outcome != computed_outcome:
        raise EvidenceError("topology all_pass/status does not match its rows")
    return StageEvidence(
        computed_outcome,
        {
            "rows": len(rows),
            "failed_rows": [list(key) for key in failed],
            "sha256": sha256_file(path),
        },
    )


def nested_value(value: Mapping[str, Any], paths: Sequence[Sequence[str]]) -> Any:
    for path in paths:
        current: Any = value
        for key in path:
            if not isinstance(current, dict) or key not in current:
                current = None
                break
            current = current[key]
        if current is not None:
            return current
    return None


def validate_runtime_receipts(
    root: Path,
    contract: Mapping[str, Any],
    sample_rows: Sequence[Mapping[str, Any]],
) -> StageEvidence:
    path = root / RUNTIME_PATH
    if not path.is_file():
        return StageEvidence("MISSING", {"path": str(RUNTIME_PATH)})
    value = load_json(path)
    if value.get("schema_version") != "1.0" or value.get("task_id") != TASK_ID:
        raise EvidenceError("runtime receipts task_id mismatch")
    declared_outcome = stage_declared_outcome(value, "runtime receipts")
    validation_seconds = parse_float(
        nested_value(
            value,
            (
                ("validation", "wall_clock_seconds"),
                ("validation", "runtime_seconds"),
                ("budget", "validation_wall_clock_seconds"),
                ("validation_wall_clock_seconds",),
            ),
        ),
        "runtime validation wall clock",
        minimum=0.0,
        allow_none=True,
    )
    production_seconds = parse_float(
        nested_value(
            value,
            (
                ("production_safety", "wall_clock_seconds"),
                ("production_safety", "estimated_seconds"),
                ("budget", "production_wall_clock_seconds"),
                ("production_wall_clock_seconds",),
            ),
        ),
        "runtime production wall clock/reference",
        minimum=0.0,
        allow_none=True,
    )
    validation_limit = float(
        contract["experiment_freeze"]["runtime_budget"][
            "validation_wall_clock_seconds_max"
        ]
    )
    production_limit = float(
        contract["experiment_freeze"]["runtime_budget"][
            "production_wall_clock_seconds_max"
        ]
    )
    if (
        parse_float(
            value.get("validation_wall_clock_budget_seconds"),
            "runtime validation budget declaration",
            minimum=0.0,
        )
        != validation_limit
    ):
        raise EvidenceError("runtime validation budget declaration drifted")
    guard = value.get("wall_clock_guard")
    if not isinstance(guard, dict):
        raise EvidenceError("runtime wall-clock guard receipt is absent")
    hard_stop = validation_limit - 300.0
    if (
        value.get("notebook_wall_clock_started_at") != "BOOTSTRAP_FIRST_CODE_CELL"
        or guard.get("deadline_origin") != "BOOTSTRAP_FIRST_CODE_CELL"
        or parse_float(
            guard.get("hard_stop_seconds"),
            "runtime hard stop",
            minimum=0.0,
        )
        != hard_stop
        or parse_float(
            guard.get("receipt_reserve_seconds"),
            "runtime receipt reserve",
            minimum=0.0,
        )
        != 300.0
        or parse_bool(
            guard.get("deadline_monotonic_shared_across_cells"),
            "runtime shared monotonic deadline",
        )
        is not True
    ):
        raise EvidenceError("runtime bootstrap/deadline/reserve semantics drifted")
    validation_within = (
        validation_seconds is not None and validation_seconds <= validation_limit
    )
    production_within = (
        production_seconds is not None and production_seconds <= production_limit
    )
    declared_validation = nested_value(
        value,
        (
            ("validation", "within_budget"),
            ("budget", "validation_within_budget"),
            ("validation_within_budget",),
        ),
    )
    if (
        declared_validation is not None
        and parse_bool(declared_validation, "runtime validation_within_budget")
        != validation_within
    ):
        raise EvidenceError("runtime validation budget boolean is stale")
    declared_production = nested_value(
        value,
        (
            ("production_safety", "within_budget"),
            ("budget", "production_within_budget"),
            ("production_within_budget",),
        ),
    )
    if (
        declared_production is not None
        and parse_bool(declared_production, "runtime production_within_budget")
        != production_within
    ):
        raise EvidenceError("runtime production budget boolean is stale")

    baseline_value = nested_value(
        value,
        (
            ("baseline_reproduction", "status"),
            ("baseline_reproduction_status",),
        ),
    )
    if status_is_success(baseline_value):
        baseline_outcome = "PASS"
    elif status_is_failure(baseline_value):
        baseline_outcome = "FAIL"
    else:
        baseline_outcome = "MISSING"

    if declared_outcome != "PASS":
        return StageEvidence(
            "FAIL",
            {
                "declared_outcome": declared_outcome,
                "failed_stage": value.get("failed_stage"),
                "validation_wall_clock_seconds": validation_seconds,
                "validation_limit_seconds": validation_limit,
                "hard_stop_seconds": hard_stop,
                "receipt_reserve_seconds": 300.0,
                "baseline_reproduction": baseline_outcome,
                "sha256": sha256_file(path),
            },
        )

    if (
        guard.get("covered_stages")
        != ("BOOTSTRAP_THROUGH_FINAL_RECEIPTS_INCLUDING_DEPENDENCY_PATCH_AND_SCORER")
        or guard.get("deadline_enforced_in_predictor_and_per_sample_loops") is not True
    ):
        raise EvidenceError("runtime deadline coverage receipt drifted")
    expected_cell_checkpoints = [
        f"{stage}:{position}"
        for stage in (
            "ENVIRONMENT",
            "RUNTIME_CONFIG",
            "DEPENDENCIES_AND_IDENTITIES",
            "PREDICTOR_PATCHES",
            "POSTPROCESS_AND_CACHE_BOUNDARY",
            "OFFICIAL_SCORER_AND_HELPERS",
        )
        for position in ("BEFORE", "AFTER")
    ] + ["VALIDATION_EXPERIMENT:BEFORE"]
    cell_rows = value.get("cell_stage_rows")
    if (
        not isinstance(cell_rows, list)
        or [
            row.get("checkpoint") if isinstance(row, dict) else None
            for row in cell_rows
        ]
        != expected_cell_checkpoints
    ):
        raise EvidenceError("runtime cell-stage coverage/order is incomplete")
    cell_elapsed = [
        float(
            parse_float(
                row.get("elapsed_seconds_from_bootstrap"),
                f"runtime cell stage {index}.elapsed",
                minimum=0.0,
            )
        )
        for index, row in enumerate(cell_rows)
    ]
    if cell_elapsed != sorted(cell_elapsed) or any(
        elapsed > validation_limit for elapsed in cell_elapsed
    ):
        raise EvidenceError("runtime cell-stage elapsed times are invalid")
    runtime_stages = value.get("stages")
    required_runtime_stages = {
        "payload_preflight",
        "predictor_shared_199",
        "predictor_anchor_full_a",
        "predictor_anchor_r70_repeat_b",
    }
    if not isinstance(runtime_stages, list) or not required_runtime_stages.issubset(
        {
            str(row.get("stage"))
            for row in runtime_stages
            if isinstance(row, dict) and status_is_success(row.get("status"))
        }
    ):
        raise EvidenceError("runtime stage receipts are incomplete")

    production_safety = value.get("production_safety")
    if not isinstance(production_safety, dict):
        raise EvidenceError("runtime production-safety receipt is absent")
    production_basis = production_safety.get("basis")
    if (
        not isinstance(production_basis, dict)
        or canonical_sha256(production_basis) != PRODUCTION_RUNTIME_BASIS_SHA256
    ):
        raise EvidenceError("runtime production basis hash drifted")
    if production_seconds != parse_float(
        production_basis.get("wall_clock_seconds"),
        "runtime production basis wall clock",
        minimum=0.0,
    ):
        raise EvidenceError("runtime production seconds differ from frozen basis")

    scoring = value.get("scoring_semantics")
    if not isinstance(scoring, dict) or (
        scoring.get("status") != "PASS"
        or scoring.get("all_pass") is not True
        or scoring.get("coordinate_semantics") != SCORE_COORDINATE_SEMANTICS
        or scoring.get("graph_reconstruction")
        != "ORIGINAL_NODE_IDS_AND_EDGES_FROM_VALIDATION_ROWS"
        or scoring.get("per_sample_crosscheck")
        != "scorer_input_rows_sha256_equals_final_output_sha256"
        or scoring.get("row_count") != EXPECTED_SAMPLE_COUNT * len(ARMS)
    ):
        raise EvidenceError("runtime scorer/submission-row semantics drifted")
    if len(sample_rows) != EXPECTED_SAMPLE_COUNT * len(ARMS) or any(
        row.get("score_coordinate_semantics") != SCORE_COORDINATE_SEMANTICS
        or row.get("scorer_input_rows_sha256") != row.get("final_output_sha256")
        for row in sample_rows
    ):
        raise EvidenceError("runtime scoring receipt contradicts per-sample evidence")

    tie_break = value.get("runtime_tie_break")
    expected_order_counts = {
        "R70": {"0": 67, "1": 66, "2": 66},
        "R80": {"0": 66, "1": 67, "2": 66},
        "R90": {"0": 66, "1": 66, "2": 67},
    }
    if not isinstance(tie_break, dict) or (
        tie_break.get("field") != "runtime_seconds"
        or tie_break.get("definition") != RUNTIME_TIE_BREAK_DEFINITION
        or tie_break.get("runtime_seconds_equals_finalize_runtime_seconds") is not True
        or tie_break.get("arm_order_policy") != "ROTATE_BY_SAMPLE_INDEX_MOD_3"
        or tie_break.get("execution_order_position_counts") != expected_order_counts
    ):
        raise EvidenceError("runtime tie-break definition/order receipt drifted")
    sample_order_counts = {
        arm: {
            str(position): sum(
                row["arm"] == arm and row["execution_order_index"] == position
                for row in sample_rows
            )
            for position in range(3)
        }
        for arm in ARMS
    }
    if sample_order_counts != expected_order_counts:
        raise EvidenceError("runtime order receipt contradicts per-sample evidence")
    streaming = value.get("streaming_strategy")
    if not isinstance(streaming, dict) or (
        streaming.get("loop_order") != "SAMPLE_OUTER_ARM_INNER"
        or streaming.get("mutable_graph_or_stats_shared_between_arms") is not False
        or streaming.get(
            "per_sample_frame_and_deepcenter_read_cache_shared_between_arms"
        )
        is not False
        or streaming.get("per_arm_frame_and_deepcenter_cache_policy")
        != "FRESH_EMPTY_PER_SAMPLE_PER_ARM"
    ):
        raise EvidenceError("runtime arm-isolation/cache policy drifted")
    if value.get("per_sample_peak_memory_semantics") != (
        "MAX_OF_SAMPLE_SCOPED_GPU_MEMORY_USED_AND_PROCESS_CURRENT_RSS_POLLED_AT_0_25_SECONDS"
    ):
        raise EvidenceError("per-sample peak-memory semantics are not sample scoped")

    if (
        parse_int(value.get("predictor_run_count"), "predictor_run_count") != 3
        or parse_int(value.get("predictor_runs_started"), "predictor_runs_started") != 3
        or value.get("predictor_run_count_semantics") != PREDICTOR_RUN_SEMANTICS
        or parse_int(
            value.get("full_199_predictor_run_count"),
            "full_199_predictor_run_count",
        )
        != 1
        or parse_int(
            value.get("anchor_predictor_run_count"), "anchor_predictor_run_count"
        )
        != 2
    ):
        raise EvidenceError("predictor logical-run count receipt drifted")
    predictor_events = value.get("predictor_run_start_events")
    expected_runs = (
        ("v20b_shared_upstream", 199),
        ("v20b_anchor_full_a", 2),
        ("v20b_anchor_r70_repeat_b", 2),
    )
    if not isinstance(predictor_events, list) or len(predictor_events) != 3:
        raise EvidenceError("predictor STARTED event count is not exactly three")
    predictor_elapsed: list[float] = []
    for index, (event, (run_name, sample_count)) in enumerate(
        zip(predictor_events, expected_runs), 1
    ):
        if not isinstance(event, dict) or (
            event.get("run_name") != run_name
            or event.get("started_index") != index
            or event.get("sample_count") != sample_count
            or event.get("worker_count") != 2
        ):
            raise EvidenceError(f"predictor STARTED event {index} drifted")
        predictor_elapsed.append(
            float(
                parse_float(
                    event.get("elapsed_seconds_from_bootstrap"),
                    f"predictor event {index}.elapsed",
                    minimum=0.0,
                )
            )
        )
    if predictor_elapsed != sorted(predictor_elapsed):
        raise EvidenceError("predictor STARTED events are not chronological")
    for field in (
        "retry_count",
        "test_inference_count",
        "competition_submission_count",
    ):
        if parse_int(value.get(field), f"runtime {field}") != 0:
            raise EvidenceError(f"runtime {field} is not zero")
    cache_manifest = load_json(root / CACHE_MANIFEST_PATH)
    if value.get("cache_manifest_sha256") != cache_manifest.get("manifest_sha256"):
        raise EvidenceError("runtime cache manifest binding drifted")
    for field, relative in (
        ("cache_equivalence_sha256", CACHE_EQUIVALENCE_PATH),
        ("runtime_determinism_sha256", DETERMINISM_PATH),
    ):
        if value.get(field) != sha256_file(root / relative):
            raise EvidenceError(f"runtime {field} binding drifted")

    arms = value.get("arms")
    if not isinstance(arms, dict) or set(arms) != set(ARMS):
        raise EvidenceError("runtime arm summary coverage drifted")
    for arm in ARMS:
        arm_rows = [row for row in sample_rows if row["arm"] == arm]
        declared_arm = arms[arm]
        if not isinstance(declared_arm, dict):
            raise EvidenceError(f"runtime arm summary malformed for {arm}")
        for key, sample_key in (
            ("downstream_seconds", "runtime_seconds"),
            ("finalize_seconds", "finalize_runtime_seconds"),
            ("scoring_seconds", "scoring_runtime_seconds"),
            ("total_sample_processing_seconds", "total_runtime_seconds"),
        ):
            declared_number = parse_float(
                declared_arm.get(key), f"runtime {arm}.{key}", minimum=0.0
            )
            expected_number = sum(float(row[sample_key]) for row in arm_rows)
            if declared_number is None or not close_enough(
                float(declared_number), expected_number, 1e-6
            ):
                raise EvidenceError(f"runtime {arm}.{key} aggregate drifted")

    # The runtime estimate and the frozen validation plan are for the observed
    # dual-T4 shape.  A one-GPU execution is a different capacity regime and
    # cannot inherit the 11-hour safety claim.
    hardware_rows: list[dict[str, Any]] = []
    for arm in ARMS:
        config_path = root / EXPERIMENT_DIR / f"canonical_resolved_config_{arm}.json"
        if not config_path.is_file():
            continue
        config = load_json(config_path)
        hardware = config.get("hardware")
        if not isinstance(hardware, dict):
            raise EvidenceError(f"canonical config {arm} lacks hardware receipt")
        cuda_available = parse_bool(
            hardware.get("cuda_available"), f"canonical config {arm}.cuda_available"
        )
        device_count = parse_int(
            hardware.get("cuda_device_count"),
            f"canonical config {arm}.cuda_device_count",
        )
        hardware_rows.append(
            {
                "arm": arm,
                "cuda_available": cuda_available,
                "cuda_device_count": device_count,
                "cuda_devices": hardware.get("cuda_devices"),
            }
        )
    hardware_ok = (
        len(hardware_rows) == len(ARMS)
        and all(row["cuda_available"] for row in hardware_rows)
        and all(row["cuda_device_count"] >= 2 for row in hardware_rows)
        and len({row["cuda_device_count"] for row in hardware_rows}) == 1
    )

    computed_outcome = (
        "PASS" if validation_within and production_within and hardware_ok else "FAIL"
    )
    if computed_outcome != "PASS":
        raise EvidenceError(
            "runtime receipts declare PASS without both frozen runtime budgets"
        )
    return StageEvidence(
        computed_outcome,
        {
            "declared_outcome": declared_outcome,
            "validation_wall_clock_seconds": validation_seconds,
            "validation_limit_seconds": validation_limit,
            "validation_within_budget": validation_within,
            "production_wall_clock_seconds": production_seconds,
            "production_limit_seconds": production_limit,
            "production_within_budget": production_within,
            "baseline_reproduction": baseline_outcome,
            "hardware_dual_gpu_requirement_pass": hardware_ok,
            "hardware": hardware_rows,
            "sha256": sha256_file(path),
        },
    )


def validate_failure_receipts(root: Path, decision: str | None) -> StageEvidence:
    if decision not in (BLOCKED_DECISIONS - {"BLOCKED_PLATFORM_ERROR"}):
        return StageEvidence("PASS", {"status": "NOT_APPLICABLE"})
    promotion = load_json(root / PROMOTION_PATH, "blocked promotion decision")
    runtime = load_json(root / RUNTIME_PATH, "blocked runtime receipt")
    manifest = load_json(root / ARTIFACT_MANIFEST_PATH, "partial artifact manifest")
    if (
        promotion.get("schema_version") != "1.0"
        or runtime.get("schema_version") != "1.0"
    ):
        raise EvidenceError("blocked receipts schema_version mismatch")
    if promotion.get("task_id") != TASK_ID or runtime.get("task_id") != TASK_ID:
        raise EvidenceError("blocked receipts task_id mismatch")
    if not status_is_failure(promotion.get("status")) or not status_is_failure(
        runtime.get("status")
    ):
        raise EvidenceError("blocked receipts do not declare FAIL_CLOSED")
    if runtime.get("all_pass") is not False:
        raise EvidenceError("blocked runtime receipt all_pass must be false")
    if (
        promotion.get("selected_arm") is not None
        or promotion.get("selected_radius_um") is not None
    ):
        raise EvidenceError("blocked promotion selected an arm/radius")
    stage = str(promotion.get("failed_stage", ""))
    if not stage or runtime.get("failed_stage") != stage:
        raise EvidenceError("blocked promotion/runtime failed_stage mismatch")
    if promotion.get("error_type") != runtime.get("error_type") or promotion.get(
        "error"
    ) != runtime.get("error"):
        raise EvidenceError("blocked promotion/runtime exception evidence mismatch")
    if not promotion.get("error_type") or not promotion.get("error"):
        raise EvidenceError("blocked receipt lacks concrete exception evidence")
    for label, value in (("promotion", promotion), ("runtime", runtime)):
        if parse_int(value.get("retry_count"), f"blocked {label}.retry_count") != 0:
            raise EvidenceError(f"blocked {label} retry_count is not zero")
    if (
        parse_int(
            promotion.get("competition_submission_count"),
            "blocked promotion competition_submission_count",
        )
        != 0
    ):
        raise EvidenceError(
            "blocked promotion competition submission count is not zero"
        )
    predictor_count = parse_int(
        runtime.get("predictor_runs_started"), "blocked predictor_runs_started"
    )
    events = runtime.get("predictor_run_start_events")
    if (
        predictor_count > 3
        or not isinstance(events, list)
        or len(events) != predictor_count
        or runtime.get("predictor_run_count_semantics") != PREDICTOR_RUN_SEMANTICS
    ):
        raise EvidenceError("blocked predictor STARTED evidence is inconsistent")
    if decision == "BLOCKED_CONFIG_IDENTITY":
        expected_stage = stage in CONFIG_FAILURE_STAGES
    elif decision == "BLOCKED_CACHE_EQUIVALENCE":
        expected_stage = stage == "CACHE_EQUIVALENCE"
    elif decision == "BLOCKED_RUNTIME_NONDETERMINISM":
        expected_stage = stage == "DETERMINISM"
    elif decision == "BLOCKED_BASELINE_REPRODUCTION":
        expected_stage = stage == "BASELINE_REPRODUCTION"
    else:
        timeout_override = promotion.get("error_type") in {
            "TimeoutError",
            "TimeoutExpired",
        } or "VALIDATION_WALL_CLOCK_GUARD" in str(promotion.get("error"))
        expected_stage = stage not in {
            "CACHE_EQUIVALENCE",
            "DETERMINISM",
            "BASELINE_REPRODUCTION",
        } and (stage not in CONFIG_FAILURE_STAGES or timeout_override)
    if not expected_stage:
        raise EvidenceError(f"blocked decision {decision} contradicts stage {stage}")

    cell_rows = runtime.get("cell_stage_rows")
    if not isinstance(cell_rows, list) or not all(
        isinstance(row, dict)
        and isinstance(row.get("checkpoint"), str)
        and parse_float(
            row.get("elapsed_seconds_from_bootstrap"),
            "blocked cell-stage elapsed",
            minimum=0.0,
        )
        is not None
        for row in cell_rows
    ):
        raise EvidenceError("blocked runtime lacks valid cell-stage receipts")
    elapsed = [float(row["elapsed_seconds_from_bootstrap"]) for row in cell_rows]
    if elapsed != sorted(elapsed):
        raise EvidenceError("blocked cell-stage receipts are not chronological")

    if (
        manifest.get("schema_version") != "1.0"
        or manifest.get("status") != "PARTIAL_FAIL_CLOSED"
    ):
        raise EvidenceError("blocked artifact manifest is not PARTIAL_FAIL_CLOSED")
    entries = manifest.get("artifacts")
    if not isinstance(entries, list):
        raise EvidenceError("blocked artifact manifest entries are absent")
    by_path = {
        str(entry.get("path")): entry for entry in entries if isinstance(entry, dict)
    }
    for name, relative in (
        ("promotion_decision.json", PROMOTION_PATH),
        ("runtime_receipts.json", RUNTIME_PATH),
    ):
        entry = by_path.get(name)
        if not isinstance(entry, dict) or (
            entry.get("sha256") != sha256_file(root / relative)
            or entry.get("bytes") != (root / relative).stat().st_size
        ):
            raise EvidenceError(f"blocked artifact manifest does not bind {name}")
    return StageEvidence(
        "PASS",
        {
            "decision": decision,
            "failed_stage": stage,
            "predictor_runs_started": predictor_count,
            "promotion_sha256": sha256_file(root / PROMOTION_PATH),
            "runtime_sha256": sha256_file(root / RUNTIME_PATH),
        },
    )


PROMOTION_GATE_IDS = (
    "each_embryo_official_noninferior",
    "at_least_one_embryo_strictly_improves",
    "embryo_equal_macro_strictly_improves",
    "pooled_micro_official_noninferior",
    "pooled_division_jaccard_strictly_improves",
    "no_embryo_material_division_jaccard_decline",
    "division_fp_increase_compensated",
    "topology_and_schema_all_pass",
    "cap_saturation_not_materially_worse",
    "node_count_penalty_no_unexplained_degradation",
    "benefit_not_entirely_one_sample",
    "identity_and_shared_cache_match",
    "only_parent_radius_differs",
    "runtime_within_frozen_budget",
)

TIE_BREAK_LABELS = (
    "maximin embryo official-score delta",
    "embryo-equal macro delta",
    "pooled micro delta",
    "pooled division Jaccard",
    "fewer added division false positives",
    "lower cap saturation",
    "shorter runtime",
)
TIE_BREAK_FIELDS = (
    "maximin_embryo_official_score_delta",
    "embryo_equal_macro_delta",
    "pooled_micro_delta",
    "pooled_division_jaccard",
    "negative_added_division_fp",
    "negative_cap_saturation",
    "negative_runtime_seconds",
)


def compute_promotion(
    embryo_metrics: Mapping[tuple[str, str], Mapping[str, Any]],
    aggregates: Mapping[tuple[str, str], Mapping[str, Any]],
    sample_rows: Sequence[Mapping[str, Any]],
    official_sample_deltas: Mapping[tuple[str, str], float],
    *,
    identity_ok: bool,
    topology_ok: bool,
    runtime_ok: bool,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    tolerances = contract["experiment_freeze"]["comparison_tolerances"]
    score_tol = float(tolerances["reported_score_absolute"])
    strict_eps = float(tolerances["strict_positive_epsilon"])
    division_drop_tol = float(tolerances["material_embryo_division_jaccard_drop"])
    cap_tol = float(tolerances["material_frame_cap_saturation_rate_increase"])
    candidate_results: dict[str, dict[str, Any]] = {}
    passing: list[str] = []
    for candidate in CANDIDATES:
        embryo_score_delta = {
            embryo: float(embryo_metrics[(candidate, embryo)]["official_score"])
            - float(embryo_metrics[("R70", embryo)]["official_score"])
            for embryo in EMBRYOS
        }
        embryo_division_delta = {
            embryo: float(embryo_metrics[(candidate, embryo)]["division_jaccard"])
            - float(embryo_metrics[("R70", embryo)]["division_jaccard"])
            for embryo in EMBRYOS
        }
        macro_delta = float(
            aggregates[(candidate, "EMBRYO_EQUAL_MACRO")]["official_score"]
        ) - float(aggregates[("R70", "EMBRYO_EQUAL_MACRO")]["official_score"])
        micro_delta = float(
            aggregates[(candidate, "POOLED_MICRO")]["official_score"]
        ) - float(aggregates[("R70", "POOLED_MICRO")]["official_score"])
        pooled_division_delta = float(
            aggregates[(candidate, "POOLED_MICRO")]["division_jaccard"]
        ) - float(aggregates[("R70", "POOLED_MICRO")]["division_jaccard"])
        div_tp_delta = int(
            aggregates[(candidate, "POOLED_MICRO")]["division_tp"]
        ) - int(aggregates[("R70", "POOLED_MICRO")]["division_tp"])
        div_fp_delta = int(
            aggregates[(candidate, "POOLED_MICRO")]["division_fp"]
        ) - int(aggregates[("R70", "POOLED_MICRO")]["division_fp"])
        candidate_rows = [row for row in sample_rows if row["arm"] == candidate]
        positive_samples = sum(
            official_sample_deltas.get((candidate, row["sample_id"]), 0.0) > strict_eps
            for row in candidate_rows
        )
        candidate_topology = all(
            row["topology_valid"] and row["schema_valid"] for row in candidate_rows
        )
        cap_increase_by_embryo = {}
        for embryo in EMBRYOS:
            candidate_cap = max(
                float(embryo_metrics[(candidate, embryo)]["frame_cap_saturation"]),
                float(embryo_metrics[(candidate, embryo)]["global_cap_saturation"]),
            )
            control_cap = max(
                float(embryo_metrics[("R70", embryo)]["frame_cap_saturation"]),
                float(embryo_metrics[("R70", embryo)]["global_cap_saturation"]),
            )
            cap_increase_by_embryo[embryo] = candidate_cap - control_cap
        candidate_penalty = float(
            aggregates[(candidate, "EMBRYO_EQUAL_MACRO")]["node_count_penalty"]
        )
        control_penalty = float(
            aggregates[("R70", "EMBRYO_EQUAL_MACRO")]["node_count_penalty"]
        )
        gates = {
            "each_embryo_official_noninferior": all(
                delta >= -score_tol for delta in embryo_score_delta.values()
            ),
            "at_least_one_embryo_strictly_improves": any(
                delta > strict_eps for delta in embryo_score_delta.values()
            ),
            "embryo_equal_macro_strictly_improves": macro_delta > strict_eps,
            "pooled_micro_official_noninferior": micro_delta >= -score_tol,
            "pooled_division_jaccard_strictly_improves": (
                pooled_division_delta > strict_eps
            ),
            "no_embryo_material_division_jaccard_decline": all(
                delta >= -division_drop_tol for delta in embryo_division_delta.values()
            ),
            "division_fp_increase_compensated": (
                div_fp_delta <= 0 or (div_tp_delta > 0 and micro_delta > strict_eps)
            ),
            "topology_and_schema_all_pass": topology_ok and candidate_topology,
            "cap_saturation_not_materially_worse": all(
                delta <= cap_tol for delta in cap_increase_by_embryo.values()
            ),
            # This is a conservative, fully mechanical interpretation of the
            # contract's "no unexplained degradation" language.
            "node_count_penalty_no_unexplained_degradation": (
                candidate_penalty <= control_penalty + score_tol
            ),
            "benefit_not_entirely_one_sample": positive_samples >= 2,
            "identity_and_shared_cache_match": identity_ok,
            "only_parent_radius_differs": identity_ok,
            "runtime_within_frozen_budget": runtime_ok,
        }
        eligible = all(gates.values())
        if eligible:
            passing.append(candidate)
        tie_break = {
            "maximin_embryo_official_score_delta": min(embryo_score_delta.values()),
            "embryo_equal_macro_delta": macro_delta,
            "pooled_micro_delta": micro_delta,
            "pooled_division_jaccard": float(
                aggregates[(candidate, "POOLED_MICRO")]["division_jaccard"]
            ),
            "negative_added_division_fp": -div_fp_delta,
            "negative_cap_saturation": -max(
                float(aggregates[(candidate, "POOLED_MICRO")]["frame_cap_saturation"]),
                float(aggregates[(candidate, "POOLED_MICRO")]["global_cap_saturation"]),
            ),
            "negative_runtime_seconds": -float(
                aggregates[(candidate, "POOLED_MICRO")]["runtime_seconds"]
            ),
        }
        candidate_results[candidate] = {
            "eligible": eligible,
            "gates": gates,
            "embryo_official_score_delta": embryo_score_delta,
            "embryo_division_jaccard_delta": embryo_division_delta,
            "embryo_equal_macro_delta": macro_delta,
            "pooled_micro_delta": micro_delta,
            "pooled_division_jaccard_delta": pooled_division_delta,
            "division_tp_delta": div_tp_delta,
            "division_fp_delta": div_fp_delta,
            "positive_sample_count": positive_samples,
            "cap_increase_by_embryo": cap_increase_by_embryo,
            "tie_break": tie_break,
        }

    if not passing:
        decision = "NO_PROMOTION_KEEP_V19C_R70"
        selected = None
    elif len(passing) == 1:
        selected = passing[0]
        decision = f"PROMOTE_{selected}_FOR_KAGGLE_TEST"
    else:
        left = candidate_results["R80"]["tie_break"]
        right = candidate_results["R90"]["tie_break"]
        selected = None
        for field in TIE_BREAK_FIELDS:
            left_value = float(left[field])
            right_value = float(right[field])
            if abs(left_value - right_value) <= strict_eps:
                continue
            selected = "R80" if left_value > right_value else "R90"
            break
        decision = (
            f"PROMOTE_{selected}_FOR_KAGGLE_TEST"
            if selected is not None
            else "NO_UNIQUE_WINNER_NO_SUBMISSION"
        )
    return {
        "decision": decision,
        "selected_arm": selected,
        "selected_radius_um": ARMS[selected] if selected else None,
        "passing_candidates": passing,
        "candidate_results": candidate_results,
    }


def validate_declared_promotion(
    root: Path,
    recomputed: Mapping[str, Any] | None,
) -> tuple[StageEvidence, dict[str, Any]]:
    path = root / PROMOTION_PATH
    if not path.is_file():
        return (
            StageEvidence("MISSING", {"path": str(PROMOTION_PATH)}),
            {},
        )
    value = load_json(path)
    decision = value.get("decision")
    if value.get("task_id") != TASK_ID or decision not in ALLOWED_DECISIONS:
        raise EvidenceError("promotion decision task/status is outside contract")
    selected = value.get("selected_arm")
    selected_radius = value.get("selected_radius_um")
    if decision in PROMOTION_DECISIONS:
        expected_selected = "R80" if decision.startswith("PROMOTE_R80") else "R90"
        if selected != expected_selected or not close_enough(
            float(parse_float(selected_radius, "selected radius")),
            ARMS[expected_selected],
            0.0,
        ):
            raise EvidenceError("promotion selected arm/radius contradict decision")
    elif decision != "BLOCKED_PLATFORM_ERROR":
        if selected is not None or selected_radius is not None:
            raise EvidenceError("non-promotion decision has a selected arm/radius")

    # `evidence_hashes` alone is the file-integrity map.  Semantic identities
    # belong in `identity_bindings`; treating their labels as filesystem paths
    # would make every valid receipt fail spuriously.
    evidence_hashes = value.get("evidence_hashes")
    hashes_required = decision not in BLOCKED_DECISIONS or recomputed is not None
    if hashes_required and (
        not isinstance(evidence_hashes, dict) or not evidence_hashes
    ):
        raise EvidenceError("promotion decision lacks evidence_hashes")
    if evidence_hashes is None:
        evidence_hashes = {}
    if not isinstance(evidence_hashes, dict):
        raise EvidenceError("promotion evidence_hashes must be an object")
    if hashes_required and not PROMOTION_EVIDENCE_PATHS.issubset(evidence_hashes):
        raise EvidenceError(
            "promotion evidence_hashes lacks frozen 14-path coverage: "
            f"{sorted(PROMOTION_EVIDENCE_PATHS - set(evidence_hashes))}"
        )
    stale_hashes = []
    for relative, expected in evidence_hashes.items():
        if (
            not isinstance(relative, str)
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
        ):
            raise EvidenceError("promotion evidence hash has unsafe path")
        require_sha256(expected, f"promotion evidence {relative}")
        target = root / relative
        actual = sha256_file(target) if target.is_file() else None
        if actual != expected:
            stale_hashes.append(
                {"path": relative, "expected": expected, "actual": actual}
            )
    if stale_hashes:
        raise EvidenceError(f"promotion evidence hashes are stale: {stale_hashes}")

    if hashes_required:
        identity_bindings = value.get("identity_bindings")
        if not isinstance(identity_bindings, dict):
            raise EvidenceError("promotion decision lacks identity_bindings")
        contract_value = load_json(root / CONTRACT_PATH)
        frozen_samples = load_json(root / FROZEN_SAMPLE_MANIFEST_PATH)
        cache_manifest = load_json(root / CACHE_MANIFEST_PATH)
        expected_bindings = {
            "base_source_sha256": contract_value["experiment_freeze"]["identities"][
                "base_source_sha256"
            ],
            "contract_canonical_sha256": canonical_sha256(contract_value),
            "contract_file_sha256": sha256_file(root / CONTRACT_PATH),
            "sample_manifest_canonical_sha256": canonical_sha256(frozen_samples),
            "sample_manifest_file_sha256": sha256_file(
                root / FROZEN_SAMPLE_MANIFEST_PATH
            ),
            "production_runtime_basis_sha256": PRODUCTION_RUNTIME_BASIS_SHA256,
            "cache_manifest_file_sha256": sha256_file(root / CACHE_MANIFEST_PATH),
            "cache_manifest_sha256": cache_manifest.get("manifest_sha256"),
            "per_sample_metrics_sha256": sha256_file(root / PER_SAMPLE_PATH),
            "per_embryo_metrics_sha256": sha256_file(root / PER_EMBRYO_PATH),
            "resolved_config_verification_sha256": sha256_file(
                root / RESOLVED_CONFIG_VERIFICATION_PATH
            ),
            "cache_equivalence_sha256": sha256_file(root / CACHE_EQUIVALENCE_PATH),
            "runtime_determinism_sha256": sha256_file(root / DETERMINISM_PATH),
        }
        missing_bindings = sorted(set(expected_bindings) - set(identity_bindings))
        if missing_bindings:
            raise EvidenceError(
                f"promotion identity_bindings missing: {missing_bindings}"
            )
        for key, expected in expected_bindings.items():
            require_sha256(expected, f"expected promotion binding {key}")
            actual = require_sha256(
                identity_bindings.get(key), f"promotion identity binding {key}"
            )
            if actual != expected:
                raise EvidenceError(f"promotion identity binding drift for {key}")
        for key, digest in identity_bindings.items():
            if not re.fullmatch(r"[a-z0-9_]+_sha256", str(key)):
                raise EvidenceError(f"unsafe promotion identity binding key: {key!r}")
            require_sha256(digest, f"promotion identity binding {key}")
        if value.get("cache_equivalence_pass") is not True:
            raise EvidenceError(
                "promotion top-level cache_equivalence_pass is not true"
            )
        if value.get("runtime_determinism_pass") is not True:
            raise EvidenceError(
                "promotion top-level runtime_determinism_pass is not true"
            )
        if (
            value.get("checkpoint_overlap_status")
            != "CHECKPOINT_TRAINING_OVERLAP_UNKNOWN"
        ):
            raise EvidenceError("promotion checkpoint-overlap boundary drifted")
        if value.get("screen", value.get("screen_name")) != SCREEN_NAME:
            raise EvidenceError("promotion screen identity mismatch")

    if recomputed is not None:
        comparison_decision = decision
        if decision == "BLOCKED_PLATFORM_ERROR":
            comparison_decision = optional_present(
                value,
                ("offline_decision", "pre_platform_decision"),
                None,
            )
            if comparison_decision not in PROMOTION_DECISIONS:
                raise EvidenceError(
                    "platform-blocked promotion lacks the unique offline decision"
                )
        if comparison_decision != recomputed["decision"]:
            raise EvidenceError(
                f"promotion decision differs from recomputation: "
                f"{comparison_decision}!={recomputed['decision']}"
            )
        if selected != recomputed["selected_arm"]:
            raise EvidenceError("promotion selected arm differs from recomputation")
        candidate_gates = value.get("candidate_gates")
        if not isinstance(candidate_gates, dict):
            raise EvidenceError("promotion decision lacks candidate_gates")
        for candidate in CANDIDATES:
            declared = candidate_gates.get(candidate)
            if not isinstance(declared, dict):
                raise EvidenceError(f"promotion gates missing {candidate}")
            declared_gates = declared.get("gates", declared)
            if not isinstance(declared_gates, dict):
                raise EvidenceError(f"promotion gates {candidate}.gates is malformed")
            computed_gates = recomputed["candidate_results"][candidate]["gates"]
            for gate_id in PROMOTION_GATE_IDS:
                if gate_id not in declared_gates:
                    raise EvidenceError(
                        f"promotion gates {candidate} missing {gate_id}"
                    )
                if (
                    parse_bool(
                        declared_gates[gate_id], f"promotion {candidate}.{gate_id}"
                    )
                    != computed_gates[gate_id]
                ):
                    raise EvidenceError(
                        f"promotion gate drift for {candidate}.{gate_id}"
                    )
            eligible_value = optional_present(
                declared, ("eligible", "all_pass", "passed"), None
            )
            if (
                eligible_value is not None
                and parse_bool(eligible_value, f"promotion {candidate}.eligible")
                != recomputed["candidate_results"][candidate]["eligible"]
            ):
                raise EvidenceError(f"promotion eligible flag drift for {candidate}")
        if value.get("passing_candidates") != recomputed["passing_candidates"]:
            raise EvidenceError("promotion passing_candidates is stale")
        tie_break = value.get("tie_break")
        if not isinstance(tie_break, dict):
            raise EvidenceError("promotion decision lacks tie_break evidence")
        if tuple(tie_break.get("order", ())) != TIE_BREAK_LABELS:
            raise EvidenceError("promotion tie-break order differs from contract")
        if tie_break.get("unique_winner") != recomputed["selected_arm"]:
            raise EvidenceError("promotion tie-break unique winner is stale")
        vectors = tie_break.get("vectors")
        if not isinstance(vectors, dict):
            raise EvidenceError("promotion tie-break vectors are malformed")
        expected_vector_arms = (
            set(CANDIDATES) if len(recomputed["passing_candidates"]) == 2 else set()
        )
        if set(vectors) != expected_vector_arms:
            raise EvidenceError("promotion tie-break vector arm set is stale")
        for candidate in expected_vector_arms:
            declared_vector = vectors[candidate]
            expected_vector = [
                recomputed["candidate_results"][candidate]["tie_break"][field]
                for field in TIE_BREAK_FIELDS
            ]
            if not isinstance(declared_vector, list) or len(declared_vector) != len(
                expected_vector
            ):
                raise EvidenceError(
                    f"promotion tie-break vector malformed for {candidate}"
                )
            for actual, expected in zip(declared_vector, expected_vector):
                actual_number = parse_float(actual, f"promotion tie-break {candidate}")
                if actual_number is None or not close_enough(
                    float(actual_number), float(expected), 1e-12
                ):
                    raise EvidenceError(
                        f"promotion tie-break vector drift for {candidate}"
                    )
        if decision == "BLOCKED_PLATFORM_ERROR":
            reason = optional_present(
                value,
                ("reason", "decision_reason", "blocking_reason", "error"),
                None,
            )
            failed = optional_present(
                value,
                ("failed_gate_ids", "blocking_checks", "failed_checks"),
                None,
            )
            failed_stage = optional_present(value, ("failed_stage",), None)
            if not reason or not (
                (isinstance(failed, list) and failed) or failed_stage
            ):
                raise EvidenceError(
                    "platform-blocked decision lacks reason/failed checks"
                )
    elif decision not in BLOCKED_DECISIONS:
        raise EvidenceError(
            "non-blocked promotion decision cannot be verified without metrics"
        )
    else:
        reason = optional_present(
            value,
            ("reason", "decision_reason", "blocking_reason", "error"),
            None,
        )
        failed = optional_present(
            value,
            ("failed_gate_ids", "blocking_checks", "failed_checks"),
            None,
        )
        failed_stage = optional_present(value, ("failed_stage",), None)
        if not reason or not ((isinstance(failed, list) and failed) or failed_stage):
            raise EvidenceError(
                "blocked decision lacks a reason and explicit failed checks"
            )
    return (
        StageEvidence(
            "PASS",
            {
                "decision": decision,
                "selected_arm": selected,
                "selected_radius_um": selected_radius,
                "sha256": sha256_file(path),
            },
        ),
        value,
    )


RUNTIME_ARTIFACT_NAMES = {
    "full_sample_payload_inventory.csv",
    "full_sample_manifest.json",
    "cache_manifest.json",
    "cache_equivalence.json",
    "runtime_determinism.json",
    "resolved_config_verification.json",
    "per_sample_metrics.csv",
    "per_embryo_metrics.csv",
    "paired_deltas_by_sample.csv",
    "paired_deltas_by_embryo.csv",
    "micro_macro_comparison.csv",
    "division_confusion_by_embryo.json",
    "topology_validation.json",
    "runtime_receipts.json",
    "promotion_decision.json",
    *(f"canonical_resolved_config_{arm}.json" for arm in ARMS),
    *(f"active_config_{arm}.json" for arm in ARMS),
    *(f"safe_div_call_receipt_{arm}.json" for arm in ARMS),
    *(f"validation_rows_{arm}.csv" for arm in ARMS),
}


def validate_artifact_manifest(
    root: Path,
    *,
    require_complete: bool,
    expected_validation_script_version: Any = None,
) -> StageEvidence:
    path = root / ARTIFACT_MANIFEST_PATH
    if not path.is_file():
        return StageEvidence("MISSING", {"path": str(ARTIFACT_MANIFEST_PATH)})
    value = load_json(path)
    if value.get("schema_version") != "1.0" or value.get("task_id") != TASK_ID:
        raise EvidenceError("artifact manifest task_id mismatch")
    expected_status = (
        "COMPLETE_VALIDATION_OUTPUTS" if require_complete else "PARTIAL_FAIL_CLOSED"
    )
    if value.get("status") != expected_status:
        raise EvidenceError(
            f"artifact manifest status mismatch: {value.get('status')} != {expected_status}"
        )
    entries = optional_present(value, ("artifacts", "files", "entries"), None)
    if not isinstance(entries, list) or not entries:
        raise EvidenceError("artifact manifest has no artifact rows")
    if parse_int(
        value.get("artifact_count"), "artifact manifest artifact_count"
    ) != len(entries):
        raise EvidenceError("artifact manifest artifact_count is stale")
    seen_paths: set[Path] = set()
    verified: list[dict[str, Any]] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise EvidenceError(f"artifact manifest row {index} is not an object")
        relative_text = str(optional_present(entry, ("path", "relative_path"), ""))
        relative = Path(relative_text)
        if not relative_text or relative.is_absolute() or ".." in relative.parts:
            raise EvidenceError(f"artifact manifest has unsafe path {relative_text!r}")
        if len(relative.parts) == 1:
            canonical_relative = EXPERIMENT_DIR / relative
        elif relative.parts[:2] == EXPERIMENT_DIR.parts:
            canonical_relative = relative
        else:
            raise EvidenceError(
                f"artifact manifest path is outside canonical runtime root: {relative_text}"
            )
        target = root / canonical_relative
        if canonical_relative == ARTIFACT_MANIFEST_PATH:
            raise EvidenceError("artifact manifest must not self-hash")
        if canonical_relative in seen_paths:
            raise EvidenceError(f"artifact manifest duplicates {canonical_relative}")
        seen_paths.add(canonical_relative)
        expected_sha = require_sha256(
            entry.get("sha256"), f"artifact {canonical_relative}"
        )
        expected_bytes = parse_int(
            entry.get("bytes"), f"artifact {canonical_relative}.bytes"
        )
        actual_sha = sha256_file(target) if target.is_file() else None
        actual_bytes = target.stat().st_size if target.is_file() else None
        if actual_sha != expected_sha or actual_bytes != expected_bytes:
            raise EvidenceError(
                f"artifact manifest drift for {canonical_relative}: "
                f"sha={actual_sha}, bytes={actual_bytes}"
            )
        verified.append(
            {
                "path": str(canonical_relative),
                "sha256": actual_sha,
                "bytes": actual_bytes,
            }
        )
    expected_runtime_paths = {EXPERIMENT_DIR / name for name in RUNTIME_ARTIFACT_NAMES}
    existing_runtime = {
        EXPERIMENT_DIR / name
        for name in RUNTIME_ARTIFACT_NAMES
        if (root / EXPERIMENT_DIR / name).is_file()
    }
    if not existing_runtime.issubset(seen_paths):
        raise EvidenceError(
            "artifact manifest omits present runtime artifacts: "
            f"{sorted(map(str, existing_runtime - seen_paths))}"
        )
    if not seen_paths.issubset(expected_runtime_paths):
        raise EvidenceError(
            "artifact manifest contains an unexpected runtime path: "
            f"{sorted(map(str, seen_paths - expected_runtime_paths))}"
        )
    if require_complete and seen_paths != expected_runtime_paths:
        raise EvidenceError(
            "complete run artifact manifest is incomplete: "
            f"{sorted(map(str, expected_runtime_paths - seen_paths))}"
        )
    if not require_complete and not {
        PROMOTION_PATH,
        RUNTIME_PATH,
    }.issubset(seen_paths):
        raise EvidenceError(
            "partial artifact manifest lacks promotion/runtime receipts"
        )
    script_version = value.get("validation_script_version_id")
    if (
        script_version not in (None, "")
        and expected_validation_script_version not in (None, "")
        and str(script_version) != str(expected_validation_script_version)
    ):
        raise EvidenceError("artifact manifest validation ScriptVersionId drifted")
    return StageEvidence(
        "PASS",
        {
            "artifact_count": len(verified),
            "complete_required": require_complete,
            "manifest_sha256": sha256_file(path),
            "validation_script_version_id": script_version,
        },
    )


def validate_write_budget_and_ledger(
    root: Path, promotion_decision: str | None
) -> tuple[StageEvidence, dict[str, Any]]:
    budget_path = root / WRITE_BUDGET_PATH
    ledger_path = root / PLATFORM_LEDGER_PATH
    if not budget_path.is_file() or not ledger_path.is_file():
        return (
            StageEvidence(
                "MISSING",
                {
                    "budget_exists": budget_path.is_file(),
                    "ledger_exists": ledger_path.is_file(),
                },
            ),
            {},
        )
    budget = load_json(budget_path)
    ledger = load_json(ledger_path)
    if budget.get("task_id") != TASK_ID or ledger.get("task_id") != TASK_ID:
        raise EvidenceError("write budget/ledger task_id mismatch")
    limits = budget.get("limits")
    counts_raw = ledger.get("counts")
    events = ledger.get("events")
    if not isinstance(limits, dict) or not isinstance(counts_raw, dict):
        raise EvidenceError("write budget/ledger counts are malformed")
    if not isinstance(events, list) or not all(isinstance(row, dict) for row in events):
        raise EvidenceError("platform ledger events must be an object list")
    if ledger.get("count_semantics") != LEDGER_COUNT_SEMANTICS:
        raise EvidenceError(
            "platform ledger does not freeze STARTED-before-invocation count semantics"
        )
    expected_limits = {
        "validation_save_kernel": 1,
        "production_save_kernel": 1,
        "save_kernel_total": 2,
        "notebook_runs_total": 2,
        "formal_competition_submission": 1,
        "retry": 0,
        "duplicate_submission": 0,
        "dataset_write": 0,
        "model_write": 0,
    }
    if any(limits.get(key) != expected for key, expected in expected_limits.items()):
        raise EvidenceError("write budget limits differ from frozen contract")
    required_count_keys = {
        "validation_save_kernel",
        "production_save_kernel",
        "save_kernel_total",
        "notebook_run",
        "competition_submit",
        "submission_status_poll",
        "retry",
        "duplicate_submit",
        "dataset_write",
        "model_write",
        "unauthorized_kaggle_write",
    }
    missing = sorted(required_count_keys - set(counts_raw))
    if missing:
        raise EvidenceError(f"platform ledger counts missing keys: {missing}")
    counts = {
        key: int(parse_int(counts_raw[key], f"ledger.{key}"))
        for key in required_count_keys
    }
    bounds = {
        "validation_save_kernel": 1,
        "production_save_kernel": 1,
        "save_kernel_total": 2,
        "notebook_run": 2,
        "competition_submit": 1,
        "retry": 0,
        "duplicate_submit": 0,
        "dataset_write": 0,
        "model_write": 0,
        "unauthorized_kaggle_write": 0,
    }
    over = {key: counts[key] for key, limit in bounds.items() if counts[key] > limit}
    if over:
        raise EvidenceError(f"Kaggle write budget exceeded: {over}")
    if counts["save_kernel_total"] != (
        counts["validation_save_kernel"] + counts["production_save_kernel"]
    ):
        raise EvidenceError("save_kernel_total does not equal validation + production")
    if counts["notebook_run"] != counts["save_kernel_total"]:
        raise EvidenceError("notebook_run and save_kernel_total counts differ")

    started_by_attempt: dict[str, Mapping[str, Any]] = {}
    result_by_attempt: dict[str, Mapping[str, Any]] = {}
    recomputed_counts: Counter[str] = Counter()
    previous_timestamp: datetime | None = None
    for index, event in enumerate(events):
        attempt_id = str(event.get("attempt_id", "")).strip()
        operation = str(event.get("operation", "")).strip().upper()
        phase = str(event.get("phase", "")).strip().upper()
        label = f"ledger event {index}"
        if not attempt_id:
            raise EvidenceError(f"{label} has no attempt_id")
        if operation not in LEDGER_OPERATION_COUNTERS:
            raise EvidenceError(f"{label} has unknown operation {operation!r}")
        if phase == "STARTED":
            if attempt_id in started_by_attempt:
                raise EvidenceError(f"duplicate STARTED event for {attempt_id}")
            timestamp = parse_timestamp(
                event.get("invoked_at_utc"), f"{label}.invoked_at_utc"
            )
            if previous_timestamp is not None and timestamp < previous_timestamp:
                raise EvidenceError(
                    "platform ledger STARTED events are not chronological"
                )
            previous_timestamp = timestamp
            target = str(event.get("target", "")).strip()
            if not target:
                raise EvidenceError(f"{label} STARTED event has no target")
            counter_keys = event.get("counter_keys")
            if (
                not isinstance(counter_keys, list)
                or not all(isinstance(key, str) for key in counter_keys)
                or len(counter_keys) != len(set(counter_keys))
            ):
                raise EvidenceError(f"{label}.counter_keys is malformed")
            actual_keys = frozenset(counter_keys)
            expected_keys = LEDGER_OPERATION_COUNTERS[operation]
            if actual_keys != expected_keys:
                raise EvidenceError(
                    f"{label} operation/counter mapping mismatch: "
                    f"{sorted(actual_keys)} != {sorted(expected_keys)}"
                )
            if not any(str(key).startswith("pre_call_") for key in event):
                raise EvidenceError(f"{label} lacks a pre_call_* snapshot")
            for key in counter_keys:
                recomputed_counts[key] += 1
            started_by_attempt[attempt_id] = event
        elif phase == "RESULT":
            if attempt_id in result_by_attempt:
                raise EvidenceError(f"duplicate RESULT event for {attempt_id}")
            if attempt_id not in started_by_attempt:
                raise EvidenceError(f"{label} RESULT precedes its STARTED event")
            if "counter_keys" in event and event["counter_keys"] not in (None, []):
                raise EvidenceError(f"{label} RESULT event must not increment counters")
            outcome = str(event.get("outcome", "")).strip()
            if not outcome:
                raise EvidenceError(f"{label} RESULT event has no outcome")
            returned = any(
                event.get(key) not in (None, "")
                for key in ("returned_version", "returned_id", "returned_status")
            )
            if not returned and event.get("error_class_if_any") in (None, ""):
                raise EvidenceError(
                    f"{label} RESULT has neither returned evidence nor error class"
                )
            result_by_attempt[attempt_id] = event
        else:
            raise EvidenceError(f"{label} has invalid phase {phase!r}")
    if set(started_by_attempt) != set(result_by_attempt):
        raise EvidenceError(
            "each platform-call STARTED event must have exactly one matching RESULT"
        )
    for attempt_id, started_event in started_by_attempt.items():
        result_event = result_by_attempt[attempt_id]
        if (
            str(result_event.get("operation", "")).strip().upper()
            != str(started_event.get("operation", "")).strip().upper()
        ):
            raise EvidenceError(f"ledger operation drift within attempt {attempt_id}")
    validation_attempts = [
        attempt_id
        for attempt_id, event in started_by_attempt.items()
        if str(event.get("operation", "")).strip().upper() == "VALIDATION_SAVE_KERNEL"
    ]
    if len(validation_attempts) != counts["validation_save_kernel"]:
        raise EvidenceError("validation SaveKernel attempt count drifted")
    validation_script_version: Any = None
    if validation_attempts:
        validation_attempt = validation_attempts[0]
        started_event = started_by_attempt[validation_attempt]
        result_event = result_by_attempt[validation_attempt]
        for field, expected in VALIDATION_BUNDLE_PROVENANCE.items():
            started_digest = require_sha256(
                started_event.get(field), f"validation STARTED {field}"
            )
            result_digest = require_sha256(
                result_event.get(field), f"validation RESULT {field}"
            )
            if started_digest != expected or result_digest != expected:
                raise EvidenceError(f"validation bundle provenance drift for {field}")
        validation_script_version = result_event.get("returned_version")
        if validation_script_version in (None, "") and result_event.get(
            "error_class_if_any"
        ) in (None, ""):
            raise EvidenceError(
                "validation SaveKernel RESULT lacks version or platform error"
            )
    recomputed_all = {
        key: int(recomputed_counts.get(key, 0)) for key in required_count_keys
    }
    if counts != recomputed_all:
        raise EvidenceError(
            f"ledger counters differ from STARTED events: "
            f"declared={counts}, recomputed={recomputed_all}"
        )
    if promotion_decision in NO_SUBMISSION_DECISIONS or promotion_decision in {
        "BLOCKED_BASELINE_REPRODUCTION",
        "BLOCKED_VALIDATION_PAYLOAD_OR_RUNTIME",
        "BLOCKED_CACHE_EQUIVALENCE",
        "BLOCKED_RUNTIME_NONDETERMINISM",
        "BLOCKED_CONFIG_IDENTITY",
    }:
        if counts["production_save_kernel"] or counts["competition_submit"]:
            raise EvidenceError(
                "non-promoted/early-blocked result consumed production or submission"
            )
    platform_error = any(
        str(event.get("outcome", "")).strip().upper()
        in {"ERROR", "FAILED", "FAILURE", "EXCEPTION", "BLOCKED_PLATFORM_ERROR"}
        or event.get("error_class_if_any") not in (None, "")
        for event in result_by_attempt.values()
    )
    return (
        StageEvidence(
            "PASS",
            {
                "counts": counts,
                "event_count": len(events),
                "started_attempt_count": len(started_by_attempt),
                "platform_error_evidenced": platform_error,
                "ledger_status": ledger.get("status"),
                "ledger_sha256": sha256_file(ledger_path),
            },
        ),
        {
            "counts": counts,
            "events": events,
            "platform_error": platform_error,
            "validation_script_version_id": validation_script_version,
            "validation_bundle_provenance": (
                dict(VALIDATION_BUNDLE_PROVENANCE) if validation_attempts else None
            ),
        },
    )


def validate_validation_bundle_provenance(
    root: Path,
    promotion: Mapping[str, Any],
    ledger_info: Mapping[str, Any],
    *,
    require_completed_validation: bool,
) -> StageEvidence:
    actual_builder_sha = sha256_file(root / VALIDATION_BUILDER_PATH)
    if actual_builder_sha != VALIDATION_BUILDER_SHA256:
        raise EvidenceError("local validation builder differs from frozen provenance")
    counts = ledger_info.get("counts")
    if not isinstance(counts, dict):
        raise EvidenceError("validation provenance lacks ledger counts")
    validation_count = int(counts.get("validation_save_kernel", -1))
    provenance = ledger_info.get("validation_bundle_provenance")
    script_version = ledger_info.get("validation_script_version_id")
    if require_completed_validation:
        if validation_count != 1 or provenance != VALIDATION_BUNDLE_PROVENANCE:
            raise EvidenceError(
                "completed validation is not bound to the frozen SaveKernel bundle"
            )
        if script_version in (None, ""):
            raise EvidenceError("completed validation lacks a ScriptVersionId")
        declared_script_version = promotion.get("validation_script_version_id")
        if declared_script_version not in (None, "") and str(
            declared_script_version
        ) != str(script_version):
            raise EvidenceError(
                "promotion validation ScriptVersionId differs from platform ledger"
            )
    elif validation_count == 1 and provenance != VALIDATION_BUNDLE_PROVENANCE:
        raise EvidenceError("validation SaveKernel provenance is incomplete")
    return StageEvidence(
        "PASS",
        {
            "required": require_completed_validation,
            "validation_save_kernel_count": validation_count,
            "validation_script_version_id": script_version,
            "bundle_sha256": (
                dict(VALIDATION_BUNDLE_PROVENANCE) if validation_count == 1 else None
            ),
        },
    )


def parse_timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceError(f"{label} timestamp is absent")
    text = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise EvidenceError(f"{label} timestamp is invalid") from exc


def submission_id_from(value: Mapping[str, Any]) -> Any:
    return optional_present(
        value,
        ("submission_id", "submissionId", "ref"),
        None,
    )


def validate_submission_and_monitoring(
    root: Path,
    promotion: Mapping[str, Any],
    ledger_info: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> tuple[StageEvidence, dict[str, Any]]:
    counts = ledger_info.get("counts", {})
    submit_count = int(counts.get("competition_submit", 0))
    production_count = int(counts.get("production_save_kernel", 0))
    poll_count = int(counts.get("submission_status_poll", 0))
    platform_error = bool(ledger_info.get("platform_error", False))
    decision = str(promotion.get("decision", ""))
    offline_decision = str(
        optional_present(
            promotion,
            ("offline_decision", "pre_platform_decision"),
            decision,
        )
    )
    selected = promotion.get("selected_arm")
    if offline_decision in PROMOTION_DECISIONS and selected is None:
        selected = "R80" if "R80" in offline_decision else "R90"

    receipt_path = root / SUBMISSION_RECEIPT_PATH
    history_path = root / STATUS_HISTORY_PATH
    health_path = root / HEALTH_SUMMARY_PATH
    if submit_count == 0:
        if receipt_path.exists() or history_path.exists():
            raise EvidenceError(
                "submission evidence exists although submit count is zero"
            )
        if poll_count != 0:
            raise EvidenceError(
                "submission polls exist although no submission ID exists"
            )
        if offline_decision in PROMOTION_DECISIONS:
            if not platform_error:
                raise EvidenceError(
                    "unique offline winner has no submission and no platform error"
                )
            if health_path.is_file():
                health = load_json(health_path)
                health_status = str(health.get("status", ""))
                if (
                    health.get("task_id") != TASK_ID
                    or health_status != "BLOCKED_PLATFORM_ERROR"
                ):
                    raise EvidenceError(
                        "zero-submit platform health status is inconsistent"
                    )
            return (
                StageEvidence(
                    "PASS",
                    {
                        "submitted": False,
                        "domain_status": "BLOCKED_PLATFORM_ERROR",
                        "poll_count": 0,
                        "public_score": None,
                    },
                ),
                {
                    "domain_status": "BLOCKED_PLATFORM_ERROR",
                    "submitted": False,
                    "submission_id": None,
                    "public_score": None,
                },
            )
        if health_path.exists():
            health = load_json(health_path)
            health_status = str(health.get("status", ""))
            if health.get("task_id") != TASK_ID or health_status not in {
                "NOT_APPLICABLE_NO_SUBMISSION",
                decision,
            }:
                raise EvidenceError("no-submission health receipt is inconsistent")
            if submission_id_from(health) is not None:
                raise EvidenceError(
                    "no-submission health receipt contains submission ID"
                )
        return (
            StageEvidence(
                "PASS",
                {
                    "submitted": False,
                    "domain_status": decision,
                    "poll_count": 0,
                    "public_score": None,
                },
            ),
            {
                "domain_status": decision,
                "submitted": False,
                "submission_id": None,
                "public_score": None,
            },
        )

    if offline_decision not in PROMOTION_DECISIONS:
        raise EvidenceError("submission was created without a unique offline winner")
    if production_count != 1:
        raise EvidenceError("submission requires exactly one production SaveKernel")
    if not receipt_path.is_file():
        if not platform_error or poll_count != 0 or history_path.exists():
            raise EvidenceError(
                "submission count is one but submission receipt is absent"
            )
        if health_path.is_file():
            health = load_json(health_path)
            if (
                health.get("task_id") != TASK_ID
                or health.get("status") != "BLOCKED_PLATFORM_ERROR"
            ):
                raise EvidenceError("failed submit call health receipt is inconsistent")
        return (
            StageEvidence(
                "PASS",
                {
                    "submitted": False,
                    "submit_call_count": 1,
                    "domain_status": "BLOCKED_PLATFORM_ERROR",
                    "submission_id": None,
                    "failure_evidence": "platform ledger event",
                },
            ),
            {
                "domain_status": "BLOCKED_PLATFORM_ERROR",
                "submitted": False,
                "submission_id": None,
                "public_score": None,
            },
        )
    receipt = load_json(receipt_path)
    if receipt.get("task_id") != TASK_ID:
        raise EvidenceError("submission receipt task_id mismatch")
    expected_arm = "R80" if "R80" in offline_decision else "R90"
    expected_radius = ARMS[expected_arm]
    receipt_arm = optional_present(receipt, ("selected_arm", "arm"), selected)
    receipt_radius = parse_float(
        first_present(
            receipt,
            ("selected_radius_um", "safe_div_parent_radius_um"),
            "submission receipt",
        ),
        "submission selected radius",
    )
    if receipt_arm != expected_arm or not close_enough(
        float(receipt_radius), expected_radius, 0.0
    ):
        raise EvidenceError("submission arm/radius differs from offline decision")
    baseline = contract["experiment_freeze"]["baseline"]
    identities = contract["experiment_freeze"]["identities"]
    if (
        optional_present(receipt, ("principal", "kaggle_principal"), None)
        != "sailorren"
    ):
        raise EvidenceError("submission principal is not sailorren")
    if (
        optional_present(receipt, ("competition", "competition_ref"), None)
        != baseline["competition"]
    ):
        raise EvidenceError("submission competition identity mismatch")
    source_sha = require_sha256(
        first_present(
            receipt, ("source_sha256", "base_source_sha256"), "submission receipt"
        ),
        "submission source SHA",
    )
    if source_sha != identities["base_source_sha256"]:
        raise EvidenceError("submission source SHA differs from frozen V19C source")
    description = str(receipt.get("description", ""))
    description_lower = description.lower()
    required_description = (
        "v20b",
        "safe-div parent radius",
        str(baseline["script_version_id"]),
        source_sha[:8].lower(),
        "two-embryo paired screen winner",
    )
    if any(term not in description_lower for term in required_description):
        raise EvidenceError("submission description lacks frozen provenance terms")
    if parse_int(receipt.get("write_count"), "submission.write_count") != 1:
        raise EvidenceError("submission receipt write_count is not one")
    if parse_int(receipt.get("retry_count"), "submission.retry_count") != 0:
        raise EvidenceError("submission receipt retry_count is not zero")
    duplicate_gate = nested_value(
        receipt,
        (
            ("pre_submit_gates", "duplicate"),
            ("duplicate_gate",),
            ("duplicate_gate_status",),
        ),
    )
    if not status_is_success(duplicate_gate) and duplicate_gate is not True:
        raise EvidenceError("submission duplicate gate is not PASS")
    identity_gate = nested_value(
        receipt,
        (
            ("pre_submit_gates", "identity"),
            ("identity_gate",),
            ("identity_gate_status",),
        ),
    )
    if not status_is_success(identity_gate) and identity_gate is not True:
        raise EvidenceError("submission identity gate is not PASS")
    output_nonempty = nested_value(
        receipt,
        (
            ("pre_submit_gates", "output_nonempty"),
            ("output_nonempty",),
            ("submission_row_count",),
            ("output_rows",),
            ("submission_csv_bytes",),
        ),
    )
    if isinstance(output_nonempty, bool):
        output_ok = output_nonempty
    else:
        output_ok = parse_int(output_nonempty, "submission output size") > 0
    if not output_ok:
        raise EvidenceError("submission output is not evidenced as non-empty")
    created = parse_timestamp(
        first_present(receipt, ("created_at", "submitted_at"), "submission receipt"),
        "submission created_at",
    )
    submission_id = submission_id_from(receipt)
    if submission_id in {None, ""}:
        if not platform_error:
            raise EvidenceError(
                "submit call has no submission ID and no platform error"
            )
        if health_path.is_file():
            health = load_json(health_path)
            if health.get("status") != "BLOCKED_PLATFORM_ERROR":
                raise EvidenceError(
                    "failed submission call is not BLOCKED_PLATFORM_ERROR"
                )
        return (
            StageEvidence(
                "PASS",
                {
                    "submitted": False,
                    "submit_call_count": 1,
                    "domain_status": "BLOCKED_PLATFORM_ERROR",
                    "submission_id": None,
                },
            ),
            {
                "domain_status": "BLOCKED_PLATFORM_ERROR",
                "submitted": False,
                "submission_id": None,
                "public_score": None,
            },
        )
    if not history_path.is_file() or not health_path.is_file():
        raise EvidenceError("successful submission lacks 30-minute evidence")
    history = load_jsonl(history_path)
    if len(history) != poll_count or not history:
        raise EvidenceError("status-history rows differ from ledger poll count")
    elapsed_values: list[float] = []
    last_score: float | None = None
    fatal_seen = False
    for index, row in enumerate(history):
        if row.get("task_id", TASK_ID) != TASK_ID:
            raise EvidenceError(f"status row {index} task_id mismatch")
        if str(submission_id_from(row)) != str(submission_id):
            raise EvidenceError(f"status row {index} submission ID mismatch")
        elapsed_raw = optional_present(row, ("elapsed_minutes", "t_plus_minutes"), None)
        if elapsed_raw is None:
            observed = parse_timestamp(
                first_present(
                    row,
                    ("observed_at", "checked_at", "timestamp"),
                    f"status row {index}",
                ),
                f"status row {index}",
            )
            elapsed = (observed - created).total_seconds() / 60.0
        else:
            elapsed = float(
                parse_float(elapsed_raw, f"status row {index}.elapsed", minimum=0.0)
            )
        if elapsed < -1e-9 or elapsed > 30.5:
            raise EvidenceError("submission monitoring exceeded frozen 30 minutes")
        if elapsed_values and elapsed + 1e-9 < elapsed_values[-1]:
            raise EvidenceError("submission status history is not chronological")
        elapsed_values.append(elapsed)
        score_raw = optional_present(row, ("public_score", "publicScore"), None)
        score = parse_float(
            score_raw, f"status row {index}.public_score", allow_none=True
        )
        if score is not None:
            last_score = float(score)
        row_text = json.dumps(row, ensure_ascii=False).upper()
        fatal_seen = fatal_seen or any(
            token in row_text
            for token in ("TRACEBACK", "EXCEPTION", "FATAL", "FAILED", "OOM")
        )
    health = load_json(health_path)
    health_status = str(health.get("status", ""))
    if (
        health.get("task_id") != TASK_ID
        or health_status not in SUBMISSION_TERMINAL_STATUSES
    ):
        raise EvidenceError("30-minute health status is outside frozen states")
    if str(submission_id_from(health)) != str(submission_id):
        raise EvidenceError("health-summary submission ID mismatch")
    stopped = optional_present(
        health,
        ("monitoring_stopped", "monitor_stopped", "stopped_after_window"),
        None,
    )
    if stopped is None or not parse_bool(stopped, "health.monitoring_stopped"):
        raise EvidenceError("30-minute monitoring is not explicitly stopped")
    score_raw = optional_present(health, ("public_score", "publicScore"), None)
    health_score = parse_float(score_raw, "health.public_score", allow_none=True)
    if (
        health_score is not None
        and last_score is not None
        and not close_enough(float(health_score), last_score, 1e-12)
    ):
        raise EvidenceError("health Public Score differs from status history")
    if health_status == "COMPLETED_VERIFIED_EARLY_SCORE_OBSERVED":
        if health_score is None and last_score is None:
            raise EvidenceError("early-score status has no observed Public Score")
    elif health_status != "BLOCKED_PLATFORM_ERROR":
        if health_score is not None or last_score is not None:
            raise EvidenceError("score-pending status contains a Public Score")
        if fatal_seen:
            raise EvidenceError("score-pending status hides a fatal log signal")
        next_action = optional_present(health, ("next_action",), None)
        if next_action != "WAIT_FOR_USER_SCORE_READ_REQUEST":
            raise EvidenceError("score-pending health receipt has wrong next_action")
        if (
            health_status == "COMPLETED_VERIFIED_SCORE_PENDING"
            and elapsed_values[-1] < 29.0
        ):
            raise EvidenceError(
                "score-pending monitoring stopped before the 30-minute window"
            )
    elif not fatal_seen and not platform_error:
        raise EvidenceError("BLOCKED_PLATFORM_ERROR has no concrete error evidence")
    public_score = health_score if health_score is not None else last_score
    return (
        StageEvidence(
            "PASS",
            {
                "submitted": True,
                "submission_id": submission_id,
                "poll_count": poll_count,
                "last_elapsed_minutes": elapsed_values[-1],
                "domain_status": health_status,
                "public_score": public_score,
                "receipt_sha256": sha256_file(receipt_path),
                "history_sha256": sha256_file(history_path),
                "health_sha256": sha256_file(health_path),
            },
        ),
        {
            "domain_status": health_status,
            "submitted": True,
            "submission_id": submission_id,
            "public_score": public_score,
        },
    )


def require_terms(text: str, groups: Sequence[Sequence[str]], label: str) -> None:
    lower = text.lower()
    missing = [
        list(group)
        for group in groups
        if not any(term.lower() in lower for term in group)
    ]
    if missing:
        raise EvidenceError(f"{label} lacks required subjects: {missing}")


def validate_final_report_builder(
    root: Path,
    *,
    domain_status: str,
    promotion_decision: str,
    submitted: bool,
) -> StageEvidence:
    builder_path = root / FINAL_REPORT_BUILDER_PATH
    if not builder_path.is_file():
        return StageEvidence("MISSING", {"path": FINAL_REPORT_BUILDER_PATH.as_posix()})
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(builder_path),
            "--project-root",
            str(root),
            "--check-only",
        ],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=180,
    )
    stdout = completed.stdout.decode("utf-8", errors="replace")
    if completed.returncode != 0:
        raise EvidenceError(
            "final report builder rejected terminal evidence "
            f"with return code {completed.returncode}"
        )
    lines = [line for line in stdout.splitlines() if line.strip()]
    if len(lines) != 2 or lines[1] != "V20B_FINAL_REPORT_BUILD_PASS":
        raise EvidenceError("final report builder emitted an unexpected receipt")
    try:
        receipt = json.loads(lines[0])
    except json.JSONDecodeError as exc:
        raise EvidenceError("final report builder receipt is not valid JSON") from exc
    expected = {
        "status": "REPORT_INPUTS_VALIDATED",
        "domain_status": domain_status,
        "promotion_decision": promotion_decision,
        "submitted": submitted,
        "written": False,
    }
    if not isinstance(receipt, dict) or any(
        receipt.get(key) != value for key, value in expected.items()
    ):
        raise EvidenceError(
            "final report builder receipt disagrees with terminal state"
        )
    report_hashes = {
        "markdown_sha256": sha256_file(root / REPORT_MD_PATH),
        "html_sha256": sha256_file(root / REPORT_HTML_PATH),
    }
    if any(receipt.get(key) != value for key, value in report_hashes.items()):
        raise EvidenceError("final report builder hashes disagree with report files")
    return StageEvidence(
        "PASS",
        {
            "builder_sha256": sha256_file(builder_path),
            **report_hashes,
            "terminal_failure_evidence_checked": True,
            "written": False,
        },
    )


def validate_reports_and_secrets(
    root: Path,
    *,
    domain_status: str,
    promotion_decision: str,
    submission: Mapping[str, Any],
) -> tuple[StageEvidence, StageEvidence]:
    md_path = root / REPORT_MD_PATH
    html_path = root / REPORT_HTML_PATH
    if not md_path.is_file() or not html_path.is_file():
        return (
            StageEvidence(
                "MISSING",
                {
                    "markdown_exists": md_path.is_file(),
                    "html_exists": html_path.is_file(),
                },
            ),
            StageEvidence("MISSING", {"reason": "reports unavailable for secret scan"}),
        )
    md = md_path.read_text(encoding="utf-8")
    html = html_path.read_text(encoding="utf-8")
    if md_path.stat().st_size < 8000 or html_path.stat().st_size < 10000:
        raise EvidenceError("V20B Markdown/HTML report is below frozen byte minimum")
    common_groups = (
        (TASK_ID,),
        (SCREEN_NAME,),
        ("CHECKPOINT_TRAINING_OVERLAP_UNKNOWN",),
        ("BLOCKED_INSUFFICIENT_EMBRYO_GROUPS",),
        ("44b6",),
        ("6bba",),
        ("R70",),
        ("R80",),
        ("R90",),
        ("199",),
        ("cache", "缓存"),
        ("paired", "配对"),
        ("embryo-equal macro", "embryo equal macro"),
        ("pooled micro",),
        ("division tp",),
        ("division fp",),
        ("division fn",),
        ("topology",),
        ("node-count", "node count", "节点数"),
        ("notebook version",),
        ("submission",),
        ("public score",),
        ("retry",),
        (promotion_decision,),
        (domain_status,),
    )
    require_terms(md, common_groups, "Markdown report")
    require_terms(
        html,
        (("Biohub V20B",), (SCREEN_NAME,), (domain_status,), (promotion_decision,)),
        "HTML report",
    )
    if submission.get("submitted"):
        submission_id = str(submission.get("submission_id"))
        if submission_id not in md or submission_id not in html:
            raise EvidenceError("reports omit the created submission ID")
    stop_message = "已按用户要求在 30 分钟后停止监控，等待用户后续通知读取分数。"
    if submission.get("submitted") and stop_message not in md:
        raise EvidenceError(
            "Markdown report omits the required monitoring-stop statement"
        )
    report_stage = StageEvidence(
        "PASS",
        {
            "markdown_bytes": md_path.stat().st_size,
            "html_bytes": html_path.stat().st_size,
            "markdown_sha256": sha256_file(md_path),
            "html_sha256": sha256_file(html_path),
        },
    )

    scan_paths: set[Path] = {
        md_path,
        html_path,
        root / TASK_RECORD_PATH,
        root / Path("scripts/verify_v20b_two_embryo_radius.py"),
        root / FINAL_REPORT_BUILDER_PATH,
    }
    experiment_root = root / EXPERIMENT_DIR
    if experiment_root.is_dir():
        scan_paths.update(path for path in experiment_root.rglob("*") if path.is_file())
    forbidden = [
        str(path.relative_to(root))
        for path in scan_paths
        if path.name.lower() == "submission.csv"
        or path.suffix.lower() in {".pt", ".pth", ".ckpt", ".safetensors"}
    ]
    findings: list[dict[str, Any]] = []
    scanned = 0
    known_fixture_redactions = 0
    text_suffixes = {
        ".json",
        ".jsonl",
        ".csv",
        ".md",
        ".html",
        ".py",
        ".txt",
        ".toml",
        ".yaml",
        ".yml",
    }
    for path in sorted(scan_paths):
        if not path.is_file() or path.suffix.lower() not in text_suffixes:
            continue
        try:
            text_value = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        scanned += 1
        relative_path = path.relative_to(root).as_posix()
        text_value, redaction_count = redact_frozen_negative_self_test_fixture(
            relative_path=relative_path,
            file_sha256=sha256_file(path),
            text_value=text_value,
        )
        known_fixture_redactions += redaction_count
        for pattern_name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text_value):
                findings.append({"path": relative_path, "pattern": pattern_name})
    if known_fixture_redactions != 1:
        raise EvidenceError(
            "secret scan did not redact exactly one frozen negative self-test fixture"
        )
    if findings or forbidden:
        raise EvidenceError(
            f"secret/forbidden artifact scan failed: findings={findings}, forbidden={forbidden}"
        )
    return report_stage, StageEvidence(
        "PASS",
        {
            "files_scanned": scanned,
            "findings": 0,
            "forbidden_artifacts": 0,
            "known_negative_self_test_fixture_redactions": known_fixture_redactions,
        },
    )


def stage_dict(stage: StageEvidence) -> dict[str, Any]:
    return {"outcome": stage.outcome, "detail": sanitise_detail(stage.detail)}


def relevant_input_hashes(root: Path) -> dict[str, str]:
    paths = {
        CONTRACT_PATH,
        FROZEN_SAMPLE_MANIFEST_PATH,
        EVIDENCE_BOUNDARY_PATH,
        WRITE_BUDGET_PATH,
        PLATFORM_LEDGER_PATH,
        ARTIFACT_MANIFEST_PATH,
        PROMOTION_PATH,
        REPORT_MD_PATH,
        REPORT_HTML_PATH,
        VALIDATION_BUILDER_PATH,
        FINAL_REPORT_BUILDER_PATH,
        TASK_RECORD_PATH,
        VALIDATION_TERMINAL_RECEIPT_PATH,
        FAILURE_DIAGNOSIS_PATH,
        VALIDATION_LOG_PATH,
        Path("scripts/verify_v20b_two_embryo_radius.py"),
    }
    paths.update(EXPERIMENT_DIR / name for name in RUNTIME_ARTIFACT_NAMES)
    paths.update({SUBMISSION_RECEIPT_PATH, STATUS_HISTORY_PATH, HEALTH_SUMMARY_PATH})
    return {
        str(relative): sha256_file(root / relative)
        for relative in sorted(paths, key=str)
        if (root / relative).is_file()
    }


def verify(root: Path) -> tuple[dict[str, Any], int]:
    root = root.resolve()
    checks = Checks()
    stages: dict[str, StageEvidence] = {}
    errors: dict[str, str] = {}

    try:
        contract, frozen_manifest = check_contract_and_frozen_inputs(root, checks)
    except Exception as exc:
        checks.require("frozen_inputs_parse", False, str(exc))
        receipt = {
            "schema_version": "1.0",
            "task_id": TASK_ID,
            "status": "VERIFICATION_FAILED",
            "domain_status": "UNKNOWN",
            "summary": {"passed": checks.passed, "failed": checks.failed},
            "checks": checks.rows,
            "stages": {},
            "input_sha256": relevant_input_hashes(root),
        }
        return receipt, 1

    promotion_raw: dict[str, Any] = {}
    declared_decision: str | None = None
    try:
        promotion_raw = load_json(root / PROMOTION_PATH)
        declared_decision = str(promotion_raw.get("decision", ""))
    except Exception as exc:
        errors["promotion_read"] = str(exc)

    def run(name: str, fn: Any) -> Any:
        try:
            result = fn()
            stage = result[0] if isinstance(result, tuple) else result
            if not isinstance(stage, StageEvidence):
                raise EvidenceError(f"{name} returned no StageEvidence")
            stages[name] = stage
            return result
        except Exception as exc:
            stages[name] = StageEvidence("FAIL", {"error": str(exc)})
            errors[name] = str(exc)
            return None

    payload_result = run(
        "payload", lambda: validate_payload_evidence(root, frozen_manifest)
    )
    payload = (
        payload_result
        if isinstance(payload_result, StageEvidence)
        else stages["payload"]
    )
    included = (
        set(payload.detail.get("included_sample_ids", []))
        if payload.outcome == "PASS"
        else set()
    )
    anchors_included = set(ANCHORS).issubset(included)

    config_result = (
        run(
            "config_and_shared_cache",
            lambda: validate_config_and_shared_cache(root, contract, included),
        )
        if payload.outcome == "PASS"
        else None
    )
    if config_result is None and "config_and_shared_cache" not in stages:
        stages["config_and_shared_cache"] = StageEvidence(
            "NOT_RUN", {"reason": "payload not PASS"}
        )
    config = stages["config_and_shared_cache"]
    cache_by_sample = (
        config.detail.get("cache_by_sample") if config.outcome == "PASS" else None
    )

    validation_hashes: dict[tuple[str, str], str] = {}
    validation_rows_result = (
        run(
            "validation_rows",
            lambda: validate_validation_rows(root, included),
        )
        if config.outcome == "PASS"
        else None
    )
    if isinstance(validation_rows_result, tuple):
        validation_hashes = validation_rows_result[1]
    elif "validation_rows" not in stages:
        stages["validation_rows"] = StageEvidence(
            "NOT_RUN", {"reason": "config/cache identity not PASS"}
        )

    cache_result = (
        run(
            "cache_equivalence",
            lambda: validate_cache_equivalence(root, cache_by_sample, contract),
        )
        if config.outcome == "PASS" or (root / CACHE_EQUIVALENCE_PATH).is_file()
        else None
    )
    if cache_result is None and "cache_equivalence" not in stages:
        stages["cache_equivalence"] = StageEvidence(
            "NOT_RUN", {"reason": "config/cache identity not PASS"}
        )
    determinism_result = (
        run(
            "runtime_determinism",
            lambda: validate_runtime_determinism(root, cache_by_sample, contract),
        )
        if config.outcome == "PASS" or (root / DETERMINISM_PATH).is_file()
        else None
    )
    if determinism_result is None and "runtime_determinism" not in stages:
        stages["runtime_determinism"] = StageEvidence(
            "NOT_RUN", {"reason": "config/cache identity not PASS"}
        )

    sample_rows: list[dict[str, Any]] = []
    sample_result = (
        run(
            "per_sample_metrics",
            lambda: validate_per_sample_metrics(
                root,
                included,
                frozen_manifest,
                cache_by_sample,
                validation_hashes,
                contract,
            ),
        )
        if config.outcome == "PASS" and validation_hashes
        else None
    )
    if isinstance(sample_result, tuple):
        sample_rows = sample_result[1]
    elif "per_sample_metrics" not in stages:
        stages["per_sample_metrics"] = StageEvidence(
            "NOT_RUN", {"reason": "config/cache identity not PASS"}
        )

    embryo_metrics: dict[tuple[str, str], dict[str, Any]] = {}
    aggregates: dict[tuple[str, str], dict[str, Any]] = {}
    official_deltas: dict[tuple[str, str], float] = {}
    if sample_rows:
        embryo_result = run(
            "per_embryo_metrics",
            lambda: validate_per_embryo_metrics(root, sample_rows, contract),
        )
        if isinstance(embryo_result, tuple):
            embryo_metrics = embryo_result[1]
            aggregates = macro_and_micro(embryo_metrics, sample_rows)
            run("micro_macro", lambda: validate_micro_macro(root, aggregates, contract))
            paired_result = run(
                "paired_deltas",
                lambda: validate_paired_deltas(
                    root, sample_rows, embryo_metrics, contract
                ),
            )
            if isinstance(paired_result, tuple):
                official_deltas = paired_result[1]
            run(
                "division_confusion",
                lambda: validate_division_confusion(
                    root, embryo_metrics, aggregates, contract
                ),
            )
        else:
            for name in ("micro_macro", "paired_deltas", "division_confusion"):
                stages[name] = StageEvidence(
                    "NOT_RUN", {"reason": "per-embryo metrics not PASS"}
                )
        run(
            "topology",
            lambda: validate_topology_evidence(root, included, sample_rows),
        )
    else:
        for name in (
            "per_embryo_metrics",
            "micro_macro",
            "paired_deltas",
            "division_confusion",
            "topology",
        ):
            stages[name] = StageEvidence(
                "NOT_RUN", {"reason": "per-sample metrics unavailable"}
            )
    run("runtime", lambda: validate_runtime_receipts(root, contract, sample_rows))
    identity_result = (
        run(
            "runtime_identity",
            lambda: validate_runtime_identity_evidence(root, contract, included),
        )
        if (
            payload.outcome == "PASS"
            and declared_decision
            not in (BLOCKED_DECISIONS - {"BLOCKED_PLATFORM_ERROR"})
        )
        else None
    )
    if identity_result is None and "runtime_identity" not in stages:
        stages["runtime_identity"] = StageEvidence(
            "NOT_RUN", {"reason": "full successful identity chain not expected"}
        )

    metric_stage_names = (
        "per_sample_metrics",
        "per_embryo_metrics",
        "micro_macro",
        "paired_deltas",
        "division_confusion",
    )
    metric_complete = all(stages[name].outcome == "PASS" for name in metric_stage_names)
    baseline_pass = stages["runtime"].detail.get("baseline_reproduction") == "PASS"
    r70_topology_pass = bool(sample_rows) and all(
        row["topology_valid"] and row["schema_valid"]
        for row in sample_rows
        if row["arm"] == "R70"
    )
    topology_evidence_present = (
        stages["topology"].outcome in {"PASS", "FAIL"} and "topology" not in errors
    )
    core_complete = (
        payload.outcome == "PASS"
        and anchors_included
        and config.outcome == "PASS"
        and stages["cache_equivalence"].outcome == "PASS"
        and stages["runtime_determinism"].outcome == "PASS"
        and stages["validation_rows"].outcome == "PASS"
        and metric_complete
        and topology_evidence_present
        and r70_topology_pass
        and stages["runtime"].outcome == "PASS"
        and stages["runtime_identity"].outcome == "PASS"
        and baseline_pass
    )

    recomputed: dict[str, Any] | None = None
    if metric_complete and embryo_metrics and aggregates and official_deltas:
        identity_ok = (
            config.outcome == "PASS"
            and stages["cache_equivalence"].outcome == "PASS"
            and stages["runtime_determinism"].outcome == "PASS"
            and stages["runtime_identity"].outcome == "PASS"
        )
        recomputed = compute_promotion(
            embryo_metrics,
            aggregates,
            sample_rows,
            official_deltas,
            identity_ok=identity_ok,
            topology_ok=topology_evidence_present and r70_topology_pass,
            runtime_ok=stages["runtime"].outcome == "PASS" and baseline_pass,
            contract=contract,
        )
    promotion_for_validation = (
        recomputed
        if declared_decision not in (BLOCKED_DECISIONS - {"BLOCKED_PLATFORM_ERROR"})
        else None
    )
    promotion_result = run(
        "promotion",
        lambda: validate_declared_promotion(root, promotion_for_validation),
    )
    if isinstance(promotion_result, tuple):
        promotion_raw = promotion_result[1]
        declared_decision = str(promotion_raw.get("decision", ""))
    run(
        "failure_receipts",
        lambda: validate_failure_receipts(root, declared_decision),
    )

    ledger_result = run(
        "write_budget_and_ledger",
        lambda: validate_write_budget_and_ledger(root, declared_decision),
    )
    ledger_info = ledger_result[1] if isinstance(ledger_result, tuple) else {}
    run(
        "validation_bundle_provenance",
        lambda: validate_validation_bundle_provenance(
            root,
            promotion_raw,
            ledger_info,
            require_completed_validation=core_complete,
        ),
    )
    submission_result = (
        run(
            "submission_and_monitoring",
            lambda: validate_submission_and_monitoring(
                root, promotion_raw, ledger_info, contract
            ),
        )
        if ledger_info and promotion_raw
        else None
    )
    if isinstance(submission_result, tuple):
        submission_info = submission_result[1]
    else:
        submission_info = {
            "domain_status": declared_decision or "UNKNOWN",
            "submitted": False,
            "submission_id": None,
            "public_score": None,
        }
        if "submission_and_monitoring" not in stages:
            stages["submission_and_monitoring"] = StageEvidence(
                "NOT_RUN", {"reason": "promotion or ledger unavailable"}
            )
    domain_status = str(
        submission_info.get("domain_status") or declared_decision or "UNKNOWN"
    )

    terminal_ok = False
    terminal_reason = "unrecognized or unsupported terminal combination"
    decision = declared_decision
    if decision in NO_SUBMISSION_DECISIONS or decision in PROMOTION_DECISIONS:
        terminal_ok = (
            core_complete
            and recomputed is not None
            and (recomputed["decision"] == decision)
        )
        if decision in PROMOTION_DECISIONS:
            terminal_ok = (
                terminal_ok and stages["submission_and_monitoring"].outcome == "PASS"
            )
            if domain_status == "BLOCKED_PLATFORM_ERROR":
                terminal_ok = bool(terminal_ok and ledger_info.get("platform_error"))
        else:
            terminal_ok = bool(
                terminal_ok
                and not submission_info.get("submitted")
                and domain_status == decision
            )
        terminal_reason = "complete offline recomputation and conditional platform path"
    elif decision == "BLOCKED_CONFIG_IDENTITY":
        failed_stage = optional_present(promotion_raw, ("failed_stage",), None)
        preceding_payload_ok = (
            payload.outcome == "PASS"
            if failed_stage in {"CONFIG_IDENTITY", "CONFIG_RECEIPTS"}
            else payload.outcome != "PASS"
        )
        terminal_ok = (
            preceding_payload_ok
            and config.outcome != "PASS"
            and failed_stage in CONFIG_FAILURE_STAGES
            and stages["failure_receipts"].outcome == "PASS"
        )
        terminal_reason = "config/shared identity did not pass"
    elif decision == "BLOCKED_CACHE_EQUIVALENCE":
        terminal_ok = (
            payload.outcome == "PASS"
            and config.outcome in {"PASS", "MISSING"}
            and stages["cache_equivalence"].outcome != "PASS"
            and optional_present(promotion_raw, ("failed_stage",), None)
            == "CACHE_EQUIVALENCE"
            and stages["failure_receipts"].outcome == "PASS"
        )
        terminal_reason = "anchor full-vs-cache equivalence did not pass"
    elif decision == "BLOCKED_RUNTIME_NONDETERMINISM":
        terminal_ok = (
            payload.outcome == "PASS"
            and config.outcome in {"PASS", "MISSING"}
            and stages["cache_equivalence"].outcome == "PASS"
            and stages["runtime_determinism"].outcome != "PASS"
            and optional_present(promotion_raw, ("failed_stage",), None)
            == "DETERMINISM"
            and stages["failure_receipts"].outcome == "PASS"
        )
        terminal_reason = "repeated R70 anchor evidence did not pass"
    elif decision == "BLOCKED_BASELINE_REPRODUCTION":
        terminal_ok = (
            baseline_pass is False
            and stages["runtime"].outcome in {"PASS", "FAIL"}
            and stages["failure_receipts"].outcome == "PASS"
        )
        terminal_reason = "R70 baseline reproduction explicitly failed"
    elif decision == "BLOCKED_VALIDATION_PAYLOAD_OR_RUNTIME":
        terminal_ok = (
            stages["failure_receipts"].outcome == "PASS"
            and stages["runtime"].outcome == "FAIL"
        )
        terminal_reason = (
            "payload, scoring, topology, anchor, or runtime evidence did not pass"
        )
    elif decision == "BLOCKED_PLATFORM_ERROR":
        # A platform error can occur while creating the validation version, the
        # conditional production version, or the submission.  Later artifacts
        # cannot be required when the platform failed before they could exist.
        # If offline metrics do exist, their declared offline decision is still
        # checked strictly by validate_declared_promotion above.
        offline_consistent = recomputed is None or recomputed[
            "decision"
        ] == optional_present(
            promotion_raw,
            ("offline_decision", "pre_platform_decision"),
            recomputed["decision"],
        )
        terminal_ok = (
            domain_status == "BLOCKED_PLATFORM_ERROR"
            and bool(ledger_info.get("platform_error"))
            and offline_consistent
        )
        terminal_reason = "write ledger records a no-retry platform failure"
    checks.require(
        "terminal_state_consistency",
        terminal_ok,
        {
            "declared_decision": decision,
            "domain_status": domain_status,
            "core_complete": core_complete,
            "reason": terminal_reason,
        },
    )

    complete_artifacts = core_complete
    run(
        "artifact_manifest",
        lambda: validate_artifact_manifest(
            root,
            require_complete=complete_artifacts,
            expected_validation_script_version=ledger_info.get(
                "validation_script_version_id"
            ),
        ),
    )
    run(
        "final_report_builder",
        lambda: validate_final_report_builder(
            root,
            domain_status=domain_status,
            promotion_decision=decision or "UNKNOWN",
            submitted=bool(submission_info.get("submitted")),
        ),
    )
    reports_result = run(
        "reports_and_secrets",
        lambda: validate_reports_and_secrets(
            root,
            domain_status=domain_status,
            promotion_decision=decision or "UNKNOWN",
            submission=submission_info,
        ),
    )
    if isinstance(reports_result, tuple):
        stages["reports"] = reports_result[0]
        stages["secret_scan"] = reports_result[1]
        del stages["reports_and_secrets"]
    else:
        stages["reports"] = stages.pop("reports_and_secrets")
        stages["secret_scan"] = StageEvidence(
            "FAIL", {"reason": "report/scan validation failed"}
        )

    mandatory = [
        "promotion",
        "failure_receipts",
        "write_budget_and_ledger",
        "validation_bundle_provenance",
        "submission_and_monitoring",
        "artifact_manifest",
        "final_report_builder",
        "reports",
        "secret_scan",
    ]
    if decision in (NO_SUBMISSION_DECISIONS | PROMOTION_DECISIONS) or (
        decision == "BLOCKED_PLATFORM_ERROR" and recomputed is not None
    ):
        mandatory.extend(
            [
                "payload",
                "config_and_shared_cache",
                "cache_equivalence",
                "runtime_determinism",
                "validation_rows",
                "per_sample_metrics",
                "per_embryo_metrics",
                "micro_macro",
                "paired_deltas",
                "division_confusion",
                "topology",
                "runtime",
                "runtime_identity",
            ]
        )
    for name in mandatory:
        checks.require(
            f"{name}_verified",
            stages[name].outcome == "PASS",
            stage_dict(stages[name]),
        )
    checks.require(
        "no_unhandled_evidence_errors",
        not {
            name: message
            for name, message in errors.items()
            if name in mandatory or (core_complete and name != "topology")
        },
        errors,
    )
    status = "COMPLETED_VERIFIED" if checks.failed == 0 else "VERIFICATION_FAILED"
    receipt = {
        "schema_version": "1.0",
        "task_id": TASK_ID,
        "status": status,
        "domain_status": domain_status,
        "promotion_decision": decision,
        "selected_arm": promotion_raw.get("selected_arm"),
        "selected_radius_um": promotion_raw.get("selected_radius_um"),
        "submission": sanitise_detail(submission_info),
        "platform_counts": sanitise_detail(ledger_info.get("counts", {})),
        "offline_recomputation": sanitise_detail(recomputed),
        "stages": {name: stage_dict(stage) for name, stage in sorted(stages.items())},
        "summary": {"passed": checks.passed, "failed": checks.failed},
        "checks": checks.rows,
        "input_sha256": relevant_input_hashes(root),
        "timestamp_policy": "OMITTED_FOR_DETERMINISTIC_RECEIPT",
    }
    return receipt, 0 if checks.failed == 0 else 1


def synthetic_metric_row(arm: str, sample_id: str, embryo: str) -> dict[str, Any]:
    division = (2, 1, 0) if arm == "R80" else (1, 1, 1)
    official = official_sample_metrics(90, 5, 5, *division, 100, 100.0)
    return {
        "arm": arm,
        "sample_id": sample_id,
        "embryo_id": embryo,
        "status": "RUN_COMPLETE",
        **official,
        "edge_tp": 90,
        "edge_fp": 5,
        "edge_fn": 5,
        "division_tp": division[0],
        "division_fp": division[1],
        "division_fn": division[2],
        "num_pred_nodes": 100,
        "gt_node_count": 100,
        "gt_node_count_evidence": "ACTUAL_GT_GEFF_GRAPH_NUM_NODES",
        "estimated_node_count": 100.0,
        "estimated_node_count_evidence": ("GEFF_METADATA_ESTIMATED_NUMBER_OF_NODES"),
        "node_recall": 1.0,
        "edges_fragmented": 0,
        "edges_lost_to_detection": 0,
        "wrong_association_edges": 0,
        "safe_div_candidate_count": 2,
        "accepted_division_count": 1,
        "deepcenter_accepted_count": 1,
        "deepcenter_rejected_count": 1,
        "frame_cap_saturation": 0.0,
        "global_cap_saturation": 0.0,
        "runtime_seconds": 1.0,
        "finalize_runtime_seconds": 1.0,
        "scoring_runtime_seconds": 0.25,
        "total_runtime_seconds": 1.5,
        "execution_order_index": 0,
        "score_coordinate_semantics": SCORE_COORDINATE_SEMANTICS,
        "peak_memory_bytes": 1024.0,
        "topology_valid": True,
        "schema_valid": True,
        "pre_division_cache_sha256": "1" * 64,
        "final_output_sha256": ("2" if arm == "R70" else "3" if arm == "R80" else "4")
        * 64,
        "scorer_input_rows_sha256": (
            "2" if arm == "R70" else "3" if arm == "R80" else "4"
        )
        * 64,
    }


def self_test() -> None:
    redacted, redaction_count = redact_frozen_negative_self_test_fixture(
        relative_path=RESOLVED_CONFIG_CHECKER_PATH,
        file_sha256=RESOLVED_CONFIG_CHECKER_SHA256,
        text_value=KNOWN_NEGATIVE_SELF_TEST_CREDENTIAL_FIXTURE,
    )
    if redaction_count != 1 or any(
        pattern.search(redacted) for pattern in SECRET_PATTERNS.values()
    ):
        raise AssertionError("frozen negative self-test fixture redaction failed")
    for wrong_path, wrong_sha in (
        ("experiments/V20B/other.py", RESOLVED_CONFIG_CHECKER_SHA256),
        (RESOLVED_CONFIG_CHECKER_PATH, "0" * 64),
    ):
        unredacted, redaction_count = redact_frozen_negative_self_test_fixture(
            relative_path=wrong_path,
            file_sha256=wrong_sha,
            text_value=KNOWN_NEGATIVE_SELF_TEST_CREDENTIAL_FIXTURE,
        )
        if redaction_count != 0 or not SECRET_PATTERNS["credential_path"].search(
            unredacted
        ):
            raise AssertionError("secret fixture redaction scope widened")
    extra_credential = "/Users/real/" + ".kaggle/" + "other" + ".json"
    partially_redacted, redaction_count = redact_frozen_negative_self_test_fixture(
        relative_path=RESOLVED_CONFIG_CHECKER_PATH,
        file_sha256=RESOLVED_CONFIG_CHECKER_SHA256,
        text_value=(KNOWN_NEGATIVE_SELF_TEST_CREDENTIAL_FIXTURE + extra_credential),
    )
    if redaction_count != 1 or not SECRET_PATTERNS["credential_path"].search(
        partially_redacted
    ):
        raise AssertionError("fixture redaction concealed a separate credential path")
    try:
        redact_frozen_negative_self_test_fixture(
            relative_path=RESOLVED_CONFIG_CHECKER_PATH,
            file_sha256=RESOLVED_CONFIG_CHECKER_SHA256,
            text_value=KNOWN_NEGATIVE_SELF_TEST_CREDENTIAL_FIXTURE * 2,
        )
    except EvidenceError:
        pass
    else:
        raise AssertionError("duplicate frozen fixture did not fail closed")
    for name, columns in {
        "payload": PAYLOAD_COLUMNS,
        "per_sample": PER_SAMPLE_COLUMNS,
        "per_embryo": PER_EMBRYO_COLUMNS,
        "paired_sample": PAIRED_SAMPLE_COLUMNS,
        "paired_embryo": PAIRED_EMBRYO_COLUMNS,
        "micro_macro": MICRO_MACRO_COLUMNS,
    }.items():
        if len(columns) != len(set(columns)):
            raise AssertionError(f"duplicate frozen CSV column in {name}")
    for name, digest in VALIDATION_BUNDLE_PROVENANCE.items():
        require_sha256(digest, f"self-test provenance {name}")
    sample_pairs = (
        ("44b6_fixture_a", "44b6"),
        ("44b6_fixture_b", "44b6"),
        ("6bba_fixture_a", "6bba"),
        ("6bba_fixture_b", "6bba"),
    )
    rows = [
        synthetic_metric_row(arm, sample_id, embryo)
        for arm in ARMS
        for sample_id, embryo in sample_pairs
    ]
    embryo_metrics = {
        (arm, embryo): aggregate_metric_rows(
            [row for row in rows if row["arm"] == arm and row["embryo_id"] == embryo]
        )
        for arm in ARMS
        for embryo in EMBRYOS
    }
    aggregates = macro_and_micro(embryo_metrics, rows)
    deltas = {
        (candidate, sample_id): next(
            row["official_score"]
            for row in rows
            if row["arm"] == candidate and row["sample_id"] == sample_id
        )
        - next(
            row["official_score"]
            for row in rows
            if row["arm"] == "R70" and row["sample_id"] == sample_id
        )
        for candidate in CANDIDATES
        for sample_id, _ in sample_pairs
    }
    contract = {
        "experiment_freeze": {
            "comparison_tolerances": {
                "reported_score_absolute": 0.0001,
                "strict_positive_epsilon": 1e-12,
                "material_embryo_division_jaccard_drop": 0.0001,
                "material_frame_cap_saturation_rate_increase": 0.005,
                "graph_coordinate_absolute": 1e-9,
            },
            "determinism": {"r70_anchor_upstream_repetitions": 2},
        }
    }
    result = compute_promotion(
        embryo_metrics,
        aggregates,
        rows,
        deltas,
        identity_ok=True,
        topology_ok=True,
        runtime_ok=True,
        contract=contract,
    )
    if result["decision"] != "PROMOTE_R80_FOR_KAGGLE_TEST":
        raise AssertionError(f"unique-winner fixture failed: {result['decision']}")

    tied_rows = [dict(row) for row in rows]
    for row in tied_rows:
        if row["arm"] == "R90":
            replacement = synthetic_metric_row(
                "R80", row["sample_id"], row["embryo_id"]
            )
            replacement["arm"] = "R90"
            row.update(replacement)
    tied_embryos = {
        (arm, embryo): aggregate_metric_rows(
            [
                row
                for row in tied_rows
                if row["arm"] == arm and row["embryo_id"] == embryo
            ]
        )
        for arm in ARMS
        for embryo in EMBRYOS
    }
    tied_aggregates = macro_and_micro(tied_embryos, tied_rows)
    tied_deltas = {
        (candidate, sample_id): next(
            row["official_score"]
            for row in tied_rows
            if row["arm"] == candidate and row["sample_id"] == sample_id
        )
        - next(
            row["official_score"]
            for row in tied_rows
            if row["arm"] == "R70" and row["sample_id"] == sample_id
        )
        for candidate in CANDIDATES
        for sample_id, _ in sample_pairs
    }
    tied = compute_promotion(
        tied_embryos,
        tied_aggregates,
        tied_rows,
        tied_deltas,
        identity_ok=True,
        topology_ok=True,
        runtime_ok=True,
        contract=contract,
    )
    if tied["decision"] != "NO_UNIQUE_WINNER_NO_SUBMISSION":
        raise AssertionError(f"tie fixture failed: {tied['decision']}")

    undefined_division_raw = synthetic_metric_row("R70", "44b6_no_division", "44b6")
    undefined_division_raw.update(
        official_sample_metrics(90, 5, 5, 0, 0, 0, 100, 100.0)
    )
    undefined_division_raw.update(
        {
            "division_tp": 0,
            "division_fp": 0,
            "division_fn": 0,
            "division_jaccard": "",
        }
    )
    normalized_undefined = normalize_sample_metric_row(
        undefined_division_raw,
        2,
        expected_samples={"44b6_no_division"},
        frozen_embryo_by_sample={"44b6_no_division": "44b6"},
        cache_by_sample={"44b6_no_division": "1" * 64},
        validation_hashes={
            ("R70", "44b6_no_division"): undefined_division_raw["final_output_sha256"]
        },
        score_tolerance=0.0001,
    )
    if normalized_undefined["division_jaccard"] is not None:
        raise AssertionError("zero-denominator sample division_jaccard was not null")
    if not close_enough(
        float(normalized_undefined["official_score"]),
        float(normalized_undefined["adj_edge_jaccard"]),
        0.0001,
    ):
        raise AssertionError("zero-denominator sample official score is incorrect")
    nan_division_raw = dict(undefined_division_raw)
    nan_division_raw["division_jaccard"] = "NaN"
    if (
        normalize_sample_metric_row(
            nan_division_raw,
            3,
            expected_samples={"44b6_no_division"},
            frozen_embryo_by_sample={"44b6_no_division": "44b6"},
            cache_by_sample={"44b6_no_division": "1" * 64},
            validation_hashes={
                ("R70", "44b6_no_division"): nan_division_raw["final_output_sha256"]
            },
            score_tolerance=0.0001,
        )["division_jaccard"]
        is not None
    ):
        raise AssertionError("NaN sample division_jaccard was not normalized to null")
    invalid_division_raw = dict(undefined_division_raw)
    invalid_division_raw["division_jaccard"] = "0"
    try:
        normalize_sample_metric_row(
            invalid_division_raw,
            4,
            expected_samples={"44b6_no_division"},
            frozen_embryo_by_sample={"44b6_no_division": "44b6"},
            cache_by_sample={"44b6_no_division": "1" * 64},
            validation_hashes={
                ("R70", "44b6_no_division"): invalid_division_raw["final_output_sha256"]
            },
            score_tolerance=0.0001,
        )
    except EvidenceError:
        pass
    else:
        raise AssertionError(
            "zero-denominator sample accepted a numeric division_jaccard"
        )
    stale_scorer_input = dict(undefined_division_raw)
    stale_scorer_input["scorer_input_rows_sha256"] = "9" * 64
    try:
        normalize_sample_metric_row(
            stale_scorer_input,
            5,
            expected_samples={"44b6_no_division"},
            frozen_embryo_by_sample={"44b6_no_division": "44b6"},
            cache_by_sample={"44b6_no_division": "1" * 64},
            validation_hashes={
                ("R70", "44b6_no_division"): undefined_division_raw[
                    "final_output_sha256"
                ]
            },
            score_tolerance=0.0001,
        )
    except EvidenceError:
        pass
    else:
        raise AssertionError("stale scorer-input row SHA did not fail closed")
    validate_nullable_delta(
        {"division_jaccard_delta": ""},
        "division_jaccard",
        None,
        0.5,
        "paired-sample nullable fixture",
        0.0001,
    )
    validate_nullable_delta(
        {"division_jaccard_delta": "NaN"},
        "division_jaccard",
        0.5,
        None,
        "paired-sample NaN fixture",
        0.0001,
    )
    try:
        validate_nullable_delta(
            {"division_jaccard_delta": "0"},
            "division_jaccard",
            None,
            0.5,
            "paired-sample invalid nullable fixture",
            0.0001,
        )
    except EvidenceError:
        pass
    else:
        raise AssertionError(
            "paired sample accepted numeric division delta with undefined arm"
        )
    validate_nullable_delta(
        {"division_jaccard_delta": "0.25"},
        "division_jaccard",
        0.75,
        0.5,
        "paired-sample finite fixture",
        0.0001,
    )

    invalid_embryos = {key: dict(value) for key, value in embryo_metrics.items()}
    invalid_embryos[("R70", "44b6")]["division_jaccard"] = None
    try:
        macro_and_micro(invalid_embryos, rows)
    except EvidenceError:
        pass
    else:
        raise AssertionError(
            "undefined per-embryo division_jaccard did not fail closed"
        )

    with tempfile.TemporaryDirectory(prefix="v20b-verifier-") as temp_dir:
        temp_root = Path(temp_dir)
        fixture = temp_root / "fixture.csv"
        with fixture.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=("sample_id", "arm"))
            writer.writeheader()
            writer.writerow({"sample_id": "44b6_fixture_a", "arm": "R70"})
        headers, loaded = load_csv(fixture)
        if headers != ["sample_id", "arm"] or loaded[0]["arm"] != "R70":
            raise AssertionError("synthetic CSV fixture read failed")
        experiment = temp_root / EXPERIMENT_DIR
        experiment.mkdir(parents=True)
        (temp_root / WRITE_BUDGET_PATH).write_text(
            json.dumps(
                {
                    "task_id": TASK_ID,
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
                }
            ),
            encoding="utf-8",
        )
        ledger_counts = {
            "validation_save_kernel": 1,
            "production_save_kernel": 0,
            "save_kernel_total": 1,
            "notebook_run": 1,
            "competition_submit": 0,
            "submission_status_poll": 0,
            "retry": 0,
            "duplicate_submit": 0,
            "dataset_write": 0,
            "model_write": 0,
            "unauthorized_kaggle_write": 0,
        }
        provenance_started = {
            "attempt_id": "validation-fixture",
            "operation": "VALIDATION_SAVE_KERNEL",
            "phase": "STARTED",
            "invoked_at_utc": "2026-09-04T00:00:00Z",
            "target": "sailorren/biohub-v20b-two-embryo-radius-validation",
            "counter_keys": [
                "validation_save_kernel",
                "save_kernel_total",
                "notebook_run",
            ],
            "pre_call_counts": dict(ledger_counts),
            **VALIDATION_BUNDLE_PROVENANCE,
        }
        provenance_result = {
            "attempt_id": "validation-fixture",
            "operation": "VALIDATION_SAVE_KERNEL",
            "phase": "RESULT",
            "outcome": "SUCCESS",
            "returned_version": 123,
            **VALIDATION_BUNDLE_PROVENANCE,
        }
        (temp_root / PLATFORM_LEDGER_PATH).write_text(
            json.dumps(
                {
                    "task_id": TASK_ID,
                    "count_semantics": LEDGER_COUNT_SEMANTICS,
                    "counts": ledger_counts,
                    "events": [provenance_started, provenance_result],
                }
            ),
            encoding="utf-8",
        )
        _, provenance_info = validate_write_budget_and_ledger(
            temp_root, "NO_PROMOTION_KEEP_V19C_R70"
        )
        if (
            provenance_info["validation_bundle_provenance"]
            != VALIDATION_BUNDLE_PROVENANCE
            or provenance_info["validation_script_version_id"] != 123
        ):
            raise AssertionError("validation bundle provenance fixture failed")
        stale_result = dict(provenance_result)
        stale_result["validation_notebook_sha256"] = "0" * 64
        (temp_root / PLATFORM_LEDGER_PATH).write_text(
            json.dumps(
                {
                    "task_id": TASK_ID,
                    "count_semantics": LEDGER_COUNT_SEMANTICS,
                    "counts": ledger_counts,
                    "events": [provenance_started, stale_result],
                }
            ),
            encoding="utf-8",
        )
        try:
            validate_write_budget_and_ledger(temp_root, "NO_PROMOTION_KEEP_V19C_R70")
        except EvidenceError:
            pass
        else:
            raise AssertionError("stale validation notebook provenance passed")
        cache_by_sample = {ANCHORS[0]: "a" * 64, ANCHORS[1]: "b" * 64}
        equivalence_rows = []
        for arm in ARMS:
            for sample_id in ANCHORS:
                digest = ("c" if sample_id == ANCHORS[0] else "d") * 64
                row_digest = ("e" if sample_id == ANCHORS[0] else "f") * 64
                equivalence_rows.append(
                    {
                        "arm": arm,
                        "sample_id": sample_id,
                        "cache_sha256": cache_by_sample[sample_id],
                        "same_raw_full_graph_sha256": digest,
                        "cached_graph_sha256": digest,
                        "same_raw_full_rows_sha256": row_digest,
                        "cached_rows_sha256": row_digest,
                        "same_raw_metric_abs_delta": 0.0,
                        "same_raw_cache_equivalent": True,
                        "fresh_full_graph_sha256": digest,
                        "fresh_full_rows_sha256": row_digest,
                        "fresh_full_metric_abs_delta": 0.0,
                        "fresh_full_cache_equivalent": True,
                    }
                )
        legacy_rows = []
        for row in equivalence_rows:
            legacy = dict(row)
            for field in (
                "fresh_full_graph_sha256",
                "fresh_full_rows_sha256",
                "fresh_full_metric_abs_delta",
                "fresh_full_cache_equivalent",
            ):
                legacy.pop(field)
            legacy_rows.append(legacy)
        (temp_root / CACHE_EQUIVALENCE_PATH).write_text(
            json.dumps(
                {
                    "task_id": TASK_ID,
                    "status": "PASS",
                    "all_pass": True,
                    "all_three_arm_fresh_full_vs_cache_pass": True,
                    "rows": legacy_rows,
                }
            ),
            encoding="utf-8",
        )
        try:
            validate_cache_equivalence(temp_root, cache_by_sample, contract)
        except EvidenceError:
            pass
        else:
            raise AssertionError("legacy cache evidence without fresh-full passed")
        (temp_root / CACHE_EQUIVALENCE_PATH).write_text(
            json.dumps(
                {
                    "task_id": TASK_ID,
                    "status": "PASS",
                    "all_pass": True,
                    "all_three_arm_fresh_full_vs_cache_pass": True,
                    "rows": equivalence_rows,
                }
            ),
            encoding="utf-8",
        )
        cache_stage = validate_cache_equivalence(temp_root, cache_by_sample, contract)
        if cache_stage.outcome != "PASS":
            raise AssertionError("synthetic cache-equivalence fixture failed")
        determinism_rows = []
        for sample_id in ANCHORS:
            digest = ("1" if sample_id == ANCHORS[0] else "2") * 64
            final_digest = ("3" if sample_id == ANCHORS[0] else "4") * 64
            output_digest = ("5" if sample_id == ANCHORS[0] else "6") * 64
            determinism_rows.append(
                {
                    "sample_id": sample_id,
                    "arm": "R70",
                    "cache_sha256": cache_by_sample[sample_id],
                    "pre_division_graph_sha256_a": digest,
                    "pre_division_graph_sha256_b": digest,
                    "final_graph_sha256_a": final_digest,
                    "final_graph_sha256_b": final_digest,
                    "validation_rows_sha256_a": output_digest,
                    "validation_rows_sha256_b": output_digest,
                    "official_score_abs_delta": 0.0,
                    "exact_upstream_topology": True,
                    "exact_final_graph": True,
                    "exact_output_rows": True,
                }
            )
        (temp_root / DETERMINISM_PATH).write_text(
            json.dumps(
                {
                    "task_id": TASK_ID,
                    "status": "PASS",
                    "all_pass": True,
                    "repetitions": 2,
                    "rows": determinism_rows,
                }
            ),
            encoding="utf-8",
        )
        determinism_stage = validate_runtime_determinism(
            temp_root, cache_by_sample, contract
        )
        if determinism_stage.outcome != "PASS":
            raise AssertionError("synthetic determinism fixture failed")
    print("V20B_TWO_EMBRYO_RADIUS_SELF_TEST_PASS")


def write_verification_receipt(path: Path, receipt: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.is_file() and path.read_text(encoding="utf-8") == rendered:
        return
    path.write_text(rendered, encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument(
        "--verification-json",
        default=str(VERIFY_REPORT_PATH),
        help="verification JSON path, relative to project root unless absolute",
    )
    parser.add_argument("--no-write-verification-json", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        self_test()
        return 0
    root = Path(args.project_root).resolve()
    receipt, exit_code = verify(root)
    if not args.no_write_verification_json:
        destination = Path(args.verification_json)
        if not destination.is_absolute():
            destination = root / destination
        write_verification_receipt(destination, receipt)
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "domain_status": receipt["domain_status"],
                "passed": receipt["summary"]["passed"],
                "failed": receipt["summary"]["failed"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    if exit_code == 0:
        print("V20B_LOCAL_EVIDENCE_PASS")
        print("V20B_TWO_EMBRYO_RADIUS_VERIFICATION_PASS")
    else:
        print("V20B_TWO_EMBRYO_RADIUS_VERIFICATION_FAIL", file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
