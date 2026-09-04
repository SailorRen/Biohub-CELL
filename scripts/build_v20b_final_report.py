#!/usr/bin/env python3
"""Build deterministic V20B Markdown and HTML reports from frozen evidence.

This builder is intentionally fail-closed.  It does not contact Kaggle, does not
inspect Git, and does not create the independent VERIFY receipt.  The latter is
owned by ``verify_v20b_two_embryo_radius.py`` after it has checked these reports.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


TASK_ID = "CODEX_20260904_BIOHUB_V20B_TWO_EMBRYO_PAIRED_RADIUS"
SCREEN_NAME = "TWO_EMBRYO_PAIRED_SENSITIVITY_SCREEN"
OVERLAP_STATUS = "CHECKPOINT_TRAINING_OVERLAP_UNKNOWN"
V20A_STATUS = "BLOCKED_INSUFFICIENT_EMBRYO_GROUPS"
REPORT_MD = Path("reports/20260904_BIOHUB_V20B_TWO_EMBRYO_PAIRED_RADIUS_REPORT_V01.md")
REPORT_HTML = Path(
    "reports/20260904_BIOHUB_V20B_TWO_EMBRYO_PAIRED_RADIUS_REPORT_V01.html"
)
EXPERIMENT_DIR = Path("experiments/V20B")
ARMS = ("R70", "R80", "R90")
CANDIDATES = ("R80", "R90")
EMBRYOS = ("44b6", "6bba")
EXPECTED_EMBRYO_COUNTS = {"44b6": 71, "6bba": 128}
EXPECTED_SAMPLE_COUNT = 199
STOP_MESSAGE = "已按用户要求在 30 分钟后停止监控，等待用户后续通知读取分数。"

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

COMPLETE_RUNTIME_ARTIFACTS = {
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

LEDGER_COUNTERS = {
    "VALIDATION_SAVE_KERNEL": {
        "validation_save_kernel",
        "save_kernel_total",
        "notebook_run",
    },
    "PRODUCTION_SAVE_KERNEL": {
        "production_save_kernel",
        "save_kernel_total",
        "notebook_run",
    },
    "COMPETITION_SUBMIT": {"competition_submit"},
    "SUBMISSION_STATUS_POLL": {"submission_status_poll"},
}
COUNT_LIMITS: dict[str, int | None] = {
    "validation_save_kernel": 1,
    "production_save_kernel": 1,
    "save_kernel_total": 2,
    "notebook_run": 2,
    "competition_submit": 1,
    # The contract suggests seven offsets but requires reporting the actual
    # count; it does not freeze a seven-call ceiling.
    "submission_status_poll": None,
    "retry": 0,
    "duplicate_submit": 0,
    "dataset_write": 0,
    "model_write": 0,
    "unauthorized_kaggle_write": 0,
}


class ReportError(RuntimeError):
    """Raised when evidence is absent, malformed, or internally inconsistent."""


@dataclass
class ReportModel:
    contract: dict[str, Any]
    boundary: dict[str, Any]
    promotion: dict[str, Any]
    runtime: dict[str, Any]
    ledger: dict[str, Any]
    counts: dict[str, int]
    decision: str
    offline_decision: str
    domain_status: str
    selected_arm: str | None
    selected_radius_um: float | None
    submitted: bool
    submission_id: Any
    public_score: float | None
    monitor_status: str
    validation_version: Any
    validation_script_version_id: Any
    production_version: Any
    production_script_version_id: Any
    payload_rows: list[dict[str, str]]
    per_sample_rows: list[dict[str, str]]
    per_embryo_rows: list[dict[str, str]]
    paired_sample_rows: list[dict[str, str]]
    paired_embryo_rows: list[dict[str, str]]
    micro_macro_rows: list[dict[str, str]]
    input_hashes: dict[str, str]
    blocked_stage: str | None
    validation_terminal: dict[str, Any]
    failure_diagnosis: dict[str, Any]


def reject_nonfinite_json(token: str) -> None:
    raise ReportError(f"JSON contains non-finite numeric token: {token}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ReportError(f"required JSON is absent: {path}")
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), parse_constant=reject_nonfinite_json
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReportError(f"cannot parse JSON {path}: {type(exc).__name__}") from exc
    if not isinstance(value, dict):
        raise ReportError(f"JSON root is not an object: {path}")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise ReportError(f"required JSONL is absent: {path}")
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line, parse_constant=reject_nonfinite_json)
        except json.JSONDecodeError as exc:
            raise ReportError(f"invalid JSONL row {index}: {path}") from exc
        if not isinstance(row, dict):
            raise ReportError(f"JSONL row {index} is not an object: {path}")
        rows.append(row)
    return rows


def load_csv_exact(path: Path, columns: Sequence[str]) -> list[dict[str, str]]:
    if not path.is_file():
        raise ReportError(f"required CSV is absent: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(columns):
            raise ReportError(
                f"CSV schema/order mismatch for {path}: {reader.fieldnames!r}"
            )
        rows = list(reader)
    if any(None in row for row in rows):
        raise ReportError(f"CSV has fields beyond its header: {path}")
    return rows


def require_task(value: Mapping[str, Any], label: str) -> None:
    if value.get("task_id") != TASK_ID:
        raise ReportError(f"{label} task_id mismatch")


def require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ReportError(f"{label} is not an object")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ReportError(f"{label} is not a list")
    return value


def as_int(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise ReportError(f"{label} is boolean, not integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ReportError(f"{label} is not an integer") from exc
    if isinstance(value, float) and value != parsed:
        raise ReportError(f"{label} is not an exact integer")
    if isinstance(value, str) and value.strip() != str(parsed):
        raise ReportError(f"{label} is not a canonical integer")
    return parsed


def as_float(value: Any, label: str, *, allow_none: bool = False) -> float | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        if allow_none:
            return None
        raise ReportError(f"{label} is absent")
    if isinstance(value, bool):
        raise ReportError(f"{label} is boolean, not numeric")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ReportError(f"{label} is not numeric") from exc
    if not math.isfinite(parsed):
        if allow_none and isinstance(value, str) and value.strip().lower() == "nan":
            return None
        raise ReportError(f"{label} is non-finite")
    return parsed


def as_bool(value: Any, label: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1"}:
            return True
        if lowered in {"false", "0"}:
            return False
    raise ReportError(f"{label} is not boolean")


def first_nonempty(value: Mapping[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        if value.get(key) not in (None, ""):
            return value[key]
    return None


def safe_relative(root: Path, raw: Any) -> tuple[Path, str]:
    text = str(raw or "")
    relative = Path(text)
    if not text or relative.is_absolute() or ".." in relative.parts:
        raise ReportError(f"unsafe artifact path: {text!r}")
    if len(relative.parts) == 1:
        relative = EXPERIMENT_DIR / relative
    elif relative.parts[:2] != EXPERIMENT_DIR.parts:
        raise ReportError(f"artifact path leaves experiments/V20B: {text!r}")
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ReportError(f"artifact resolves outside project: {text!r}") from exc
    return candidate, relative.as_posix()


def validate_contract_and_boundary(
    contract: Mapping[str, Any], boundary: Mapping[str, Any]
) -> None:
    require_task(contract, "contract")
    require_task(boundary, "evidence boundary")
    freeze = require_dict(contract.get("experiment_freeze"), "experiment_freeze")
    if freeze.get("submission_monitor_minutes") != 30:
        raise ReportError("contract monitoring window is not 30 minutes")
    if freeze.get("future_score_read_requires_explicit_user_request") is not True:
        raise ReportError("future score read is not explicit-user-request only")
    if boundary.get("experiment_label") != SCREEN_NAME:
        raise ReportError("evidence boundary screen mismatch")
    checkpoint = require_dict(boundary.get("checkpoint_overlap"), "checkpoint_overlap")
    if checkpoint.get("status") != OVERLAP_STATUS:
        raise ReportError("checkpoint overlap status was weakened")
    historical = require_dict(
        boundary.get("historical_invariants"), "historical_invariants"
    )
    if historical.get("v20a_domain_status") != V20A_STATUS:
        raise ReportError("V20A historical status drifted")
    expected = {arm: "NOT_RUN_HARD_GATE" for arm in ARMS}
    if historical.get("v20a_arm_statuses") != expected:
        raise ReportError("V20A historical arm statuses drifted")
    if boundary.get("delivery_completion_is_performance_improvement") is not False:
        raise ReportError("delivery/performance evidence boundary was weakened")


def validate_ledger(ledger: Mapping[str, Any]) -> tuple[dict[str, int], dict[str, Any]]:
    require_task(ledger, "platform ledger")
    if (
        ledger.get("count_semantics")
        != "PHYSICAL_API_CALL_COUNTED_AT_STARTED_BEFORE_INVOCATION"
    ):
        raise ReportError("platform ledger count semantics mismatch")
    raw_counts = require_dict(ledger.get("counts"), "ledger counts")
    missing = sorted(set(COUNT_LIMITS) - set(raw_counts))
    if missing:
        raise ReportError(f"ledger count keys are absent: {missing}")
    counts = {
        key: as_int(raw_counts[key], f"ledger counts.{key}") for key in COUNT_LIMITS
    }
    for key, limit in COUNT_LIMITS.items():
        if counts[key] < 0 or (limit is not None and counts[key] > limit):
            raise ReportError(f"ledger count {key}={counts[key]} exceeds [0,{limit}]")
    if counts["save_kernel_total"] != (
        counts["validation_save_kernel"] + counts["production_save_kernel"]
    ):
        raise ReportError("save_kernel_total does not equal validation+production")
    if counts["notebook_run"] != counts["save_kernel_total"]:
        raise ReportError("notebook_run does not equal SaveKernel total")

    events = require_list(ledger.get("events"), "ledger events")
    started: dict[str, dict[str, Any]] = {}
    results: dict[str, dict[str, Any]] = {}
    recomputed = {key: 0 for key in COUNT_LIMITS}
    for index, raw_event in enumerate(events):
        event = require_dict(raw_event, f"ledger event {index}")
        attempt = str(event.get("attempt_id", "")).strip()
        operation = str(event.get("operation", "")).strip().upper()
        phase = str(event.get("phase", "")).strip().upper()
        if not attempt or operation not in LEDGER_COUNTERS:
            raise ReportError(f"ledger event {index} lacks a valid attempt/operation")
        if phase == "STARTED":
            if attempt in started:
                raise ReportError(f"duplicate STARTED event: {attempt}")
            counter_keys = event.get("counter_keys")
            if (
                not isinstance(counter_keys, list)
                or set(counter_keys) != LEDGER_COUNTERS[operation]
            ):
                raise ReportError(f"counter mapping mismatch for {attempt}")
            if not any(str(key).startswith("pre_call_") for key in event):
                raise ReportError(f"STARTED event lacks pre_call snapshot: {attempt}")
            for key in counter_keys:
                recomputed[key] += 1
            started[attempt] = event
        elif phase == "RESULT":
            if attempt in results or attempt not in started:
                raise ReportError(f"unpaired or duplicate RESULT event: {attempt}")
            if event.get("counter_keys") not in (None, []):
                raise ReportError(f"RESULT event increments counters: {attempt}")
            if not str(event.get("outcome", "")).strip():
                raise ReportError(f"RESULT event lacks outcome: {attempt}")
            results[attempt] = event
        else:
            raise ReportError(f"invalid ledger phase for {attempt}: {phase}")
    if set(started) != set(results):
        raise ReportError("not every STARTED event has exactly one RESULT")
    if counts != recomputed:
        raise ReportError(
            f"ledger counts are stale: declared={counts}, actual={recomputed}"
        )
    return counts, {"started": started, "results": results}


def result_for_operation(
    ledger_pairs: Mapping[str, Any], operation: str
) -> dict[str, Any] | None:
    started = ledger_pairs["started"]
    results = ledger_pairs["results"]
    attempts = [
        attempt
        for attempt, event in started.items()
        if str(event.get("operation", "")).upper() == operation
    ]
    if not attempts:
        return None
    if len(attempts) != 1:
        raise ReportError(f"more than one {operation} attempt")
    return results[attempts[0]]


def ledger_has_platform_error(ledger_pairs: Mapping[str, Any]) -> bool:
    for event in ledger_pairs["results"].values():
        outcome = str(event.get("outcome", "")).upper()
        if event.get("error_class_if_any") not in (None, "") or outcome in {
            "ERROR",
            "FAILED",
            "FAILURE",
            "EXCEPTION",
            "BLOCKED_PLATFORM_ERROR",
        }:
            return True
    return False


def validate_artifact_manifest(
    root: Path, manifest: Mapping[str, Any], *, complete: bool
) -> dict[str, str]:
    require_task(manifest, "artifact manifest")
    expected_status = (
        "COMPLETE_VALIDATION_OUTPUTS" if complete else "PARTIAL_FAIL_CLOSED"
    )
    if manifest.get("status") != expected_status:
        raise ReportError(
            f"artifact manifest status {manifest.get('status')!r} != {expected_status!r}"
        )
    entries = manifest.get("artifacts", manifest.get("files", manifest.get("entries")))
    rows = require_list(entries, "artifact manifest entries")
    if as_int(manifest.get("artifact_count"), "artifact_count") != len(rows):
        raise ReportError("artifact_count is stale")
    seen: dict[str, str] = {}
    names: set[str] = set()
    for index, raw_entry in enumerate(rows):
        entry = require_dict(raw_entry, f"artifact manifest row {index}")
        path, relative = safe_relative(
            root, entry.get("path", entry.get("relative_path"))
        )
        if relative in seen or not path.is_file():
            raise ReportError(f"duplicate or absent artifact: {relative}")
        expected_sha = str(entry.get("sha256", ""))
        expected_bytes = as_int(entry.get("bytes"), f"artifact bytes {relative}")
        actual_sha = sha256_file(path)
        if actual_sha != expected_sha or path.stat().st_size != expected_bytes:
            raise ReportError(f"artifact manifest drift: {relative}")
        seen[relative] = actual_sha
        names.add(Path(relative).name)
    if complete and names != COMPLETE_RUNTIME_ARTIFACTS:
        raise ReportError(
            "complete artifact set mismatch: "
            f"missing={sorted(COMPLETE_RUNTIME_ARTIFACTS - names)}, "
            f"extra={sorted(names - COMPLETE_RUNTIME_ARTIFACTS)}"
        )
    if not complete and not {
        "promotion_decision.json",
        "runtime_receipts.json",
    }.issubset(names):
        raise ReportError("partial artifact manifest lacks failure receipts")
    return seen


def validate_promotion(
    promotion: Mapping[str, Any], *, complete: bool
) -> tuple[str, str, str | None, float | None]:
    require_task(promotion, "promotion decision")
    decision = str(promotion.get("decision", ""))
    if decision not in ALLOWED_DECISIONS:
        raise ReportError(f"unsupported promotion decision: {decision!r}")
    offline_decision = str(
        promotion.get(
            "offline_decision", promotion.get("pre_platform_decision", decision)
        )
    )
    if offline_decision not in ALLOWED_DECISIONS:
        raise ReportError(f"unsupported offline decision: {offline_decision!r}")
    selected = promotion.get("selected_arm")
    radius_raw = promotion.get("selected_radius_um")
    radius = as_float(radius_raw, "selected radius", allow_none=True)
    selection_decision = (
        offline_decision if decision == "BLOCKED_PLATFORM_ERROR" else decision
    )
    if selection_decision in PROMOTION_DECISIONS:
        expected = "R80" if "R80" in selection_decision else "R90"
        expected_radius = 8.0 if expected == "R80" else 9.0
        if selected != expected or radius != expected_radius:
            raise ReportError("promotion decision/selected arm/radius mismatch")
        if promotion.get("candidate_label") not in (None, "Kaggle test candidate"):
            raise ReportError("promotion candidate label overclaims evidence")
    elif selected is not None or radius is not None:
        raise ReportError("non-promotion decision contains selected arm/radius")
    if complete:
        if promotion.get("screen") != SCREEN_NAME:
            raise ReportError("promotion screen mismatch")
        if promotion.get("checkpoint_overlap_status") != OVERLAP_STATUS:
            raise ReportError("promotion checkpoint-overlap status mismatch")
        if promotion.get("cache_equivalence_pass") is not True:
            raise ReportError("promotion does not bind passing cache equivalence")
        if promotion.get("runtime_determinism_pass") is not True:
            raise ReportError("promotion does not bind runtime determinism")
        gates = require_dict(promotion.get("candidate_gates"), "candidate_gates")
        passing = require_list(
            promotion.get("passing_candidates"), "passing_candidates"
        )
        recomputed_passing: list[str] = []
        for candidate in CANDIDATES:
            row = require_dict(gates.get(candidate), f"candidate_gates.{candidate}")
            booleans = [
                value
                for key, value in row.items()
                if key != "eligible" and isinstance(value, bool)
            ]
            if not booleans:
                raise ReportError(f"candidate {candidate} has no boolean gates")
            eligible = all(booleans)
            if row.get("eligible") is not eligible:
                raise ReportError(f"candidate {candidate} eligible flag is stale")
            if eligible:
                recomputed_passing.append(candidate)
        if passing != recomputed_passing:
            raise ReportError("passing_candidates differs from candidate gates")
        if selection_decision in PROMOTION_DECISIONS and selected not in passing:
            raise ReportError("selected candidate did not pass all frozen gates")
        if selection_decision == "NO_PROMOTION_KEEP_V19C_R70" and passing:
            raise ReportError("no-promotion decision has passing candidates")
        if selection_decision == "NO_UNIQUE_WINNER_NO_SUBMISSION" and passing != [
            "R80",
            "R90",
        ]:
            raise ReportError(
                "no-unique decision does not have both passing candidates"
            )
    return decision, offline_decision, selected, radius


def require_json_pass(path: Path, *, allow_failure: bool = False) -> dict[str, Any]:
    value = load_json(path)
    require_task(value, path.name)
    passed = value.get("all_pass") is True or str(value.get("status", "")).upper() in {
        "PASS",
        "COMPLETE",
        "RUN_COMPLETE",
    }
    if not passed and not allow_failure:
        raise ReportError(f"{path.name} is not a passing receipt")
    return value


def validate_complete_tables(
    root: Path, contract: Mapping[str, Any]
) -> tuple[
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
]:
    frozen = load_json(root / EXPERIMENT_DIR / "sample_manifest.json")
    full_manifest = load_json(root / EXPERIMENT_DIR / "full_sample_manifest.json")
    require_task(frozen, "frozen sample manifest")
    require_task(full_manifest, "full sample manifest")
    if (
        frozen.get("sample_count") != EXPECTED_SAMPLE_COUNT
        or frozen.get("embryo_sample_counts") != EXPECTED_EMBRYO_COUNTS
    ):
        raise ReportError("frozen sample manifest does not contain 71+128 samples")
    if (
        full_manifest.get("status") != "COMPLETE_199_OF_199"
        or full_manifest.get("sample_count") != EXPECTED_SAMPLE_COUNT
        or full_manifest.get("embryo_count") != 2
        or full_manifest.get("embryo_sample_counts") != EXPECTED_EMBRYO_COUNTS
        or full_manifest.get("excluded_samples") != []
    ):
        raise ReportError("full payload manifest is not COMPLETE_199_OF_199")

    frozen_rows = require_list(frozen.get("samples"), "frozen samples")
    frozen_by_id: dict[str, str] = {}
    for index, raw in enumerate(frozen_rows):
        row = require_dict(raw, f"frozen sample {index}")
        sample_id = str(row.get("sample_id", ""))
        embryo_id = str(row.get("embryo_id", ""))
        if not sample_id or embryo_id not in EMBRYOS or sample_id in frozen_by_id:
            raise ReportError("frozen sample identities are malformed or duplicated")
        frozen_by_id[sample_id] = embryo_id
    if len(frozen_by_id) != EXPECTED_SAMPLE_COUNT:
        raise ReportError("frozen sample identity count is not 199")

    payload = load_csv_exact(
        root / EXPERIMENT_DIR / "full_sample_payload_inventory.csv", PAYLOAD_COLUMNS
    )
    per_sample = load_csv_exact(
        root / EXPERIMENT_DIR / "per_sample_metrics.csv", PER_SAMPLE_COLUMNS
    )
    per_embryo = load_csv_exact(
        root / EXPERIMENT_DIR / "per_embryo_metrics.csv", PER_EMBRYO_COLUMNS
    )
    paired_sample = load_csv_exact(
        root / EXPERIMENT_DIR / "paired_deltas_by_sample.csv",
        PAIRED_SAMPLE_COLUMNS,
    )
    paired_embryo = load_csv_exact(
        root / EXPERIMENT_DIR / "paired_deltas_by_embryo.csv",
        PAIRED_EMBRYO_COLUMNS,
    )
    micro_macro = load_csv_exact(
        root / EXPERIMENT_DIR / "micro_macro_comparison.csv", MICRO_MACRO_COLUMNS
    )

    if len(payload) != 199 or len(per_sample) != 597:
        raise ReportError("payload/per-sample row counts are not 199/597")
    if len(per_embryo) != 6 or len(paired_sample) != 398:
        raise ReportError("per-embryo/paired-sample row counts are not 6/398")
    if len(paired_embryo) != 4 or len(micro_macro) != 6:
        raise ReportError("paired-embryo/micro-macro row counts are not 4/6")

    payload_ids: set[str] = set()
    for row in payload:
        sample_id = row["sample_id"]
        if (
            sample_id in payload_ids
            or frozen_by_id.get(sample_id) != row["embryo_id"]
            or row["status"] != "PASS"
            or not all(
                as_bool(row[key], f"payload {sample_id}.{key}")
                for key in (
                    "image_exists",
                    "gt_exists",
                    "image_readable",
                    "gt_readable",
                    "scorer_metadata_readable",
                )
            )
        ):
            raise ReportError(f"payload evidence is incomplete for {sample_id!r}")
        payload_ids.add(sample_id)
    if payload_ids != set(frozen_by_id):
        raise ReportError("payload IDs differ from the frozen 199-sample set")

    expected_sample_keys = {
        (arm, sample_id) for arm in ARMS for sample_id in frozen_by_id
    }
    sample_map: dict[tuple[str, str], dict[str, str]] = {}
    for row in per_sample:
        key = (row["arm"], row["sample_id"])
        if (
            key in sample_map
            or key not in expected_sample_keys
            or row["embryo_id"] != frozen_by_id[row["sample_id"]]
            or row["status"] != "RUN_COMPLETE"
            or not as_bool(row["topology_valid"], f"per-sample {key} topology")
            or not as_bool(row["schema_valid"], f"per-sample {key} schema")
        ):
            raise ReportError(f"per-sample evidence is malformed for {key}")
        as_float(row["official_score"], f"per-sample {key} official score")
        sample_map[key] = row
    if set(sample_map) != expected_sample_keys:
        raise ReportError("per-sample arm/sample coverage is incomplete")

    expected_embryo_keys = {(arm, embryo) for arm in ARMS for embryo in EMBRYOS}
    embryo_map: dict[tuple[str, str], dict[str, str]] = {}
    for row in per_embryo:
        key = (row["arm"], row["embryo_id"])
        if key in embryo_map or key not in expected_embryo_keys:
            raise ReportError(f"per-embryo key is malformed: {key}")
        if (
            as_int(row["sample_count"], f"per-embryo {key} sample count")
            != EXPECTED_EMBRYO_COUNTS[key[1]]
        ):
            raise ReportError(f"per-embryo sample count mismatch: {key}")
        if (
            row["status"] != "RUN_COMPLETE"
            or not as_bool(row["topology_valid"], f"per-embryo {key} topology")
            or not as_bool(row["schema_valid"], f"per-embryo {key} schema")
        ):
            raise ReportError(f"per-embryo status/schema/topology failed: {key}")
        embryo_map[key] = row
    if set(embryo_map) != expected_embryo_keys:
        raise ReportError("per-embryo coverage is incomplete")

    delta_sample_keys: set[tuple[str, str]] = set()
    for row in paired_sample:
        key = (row["candidate_arm"], row["sample_id"])
        if (
            key in delta_sample_keys
            or key[0] not in CANDIDATES
            or key[1] not in frozen_by_id
            or row["control_arm"] != "R70"
            or row["embryo_id"] != frozen_by_id[key[1]]
        ):
            raise ReportError(f"paired-sample identity mismatch: {key}")
        candidate = sample_map[(key[0], key[1])]
        control = sample_map[("R70", key[1])]
        expected = as_float(
            candidate["official_score"], "candidate official"
        ) - as_float(control["official_score"], "control official")
        observed = as_float(row["official_score_delta"], "paired official delta")
        if abs(observed - expected) > 1e-9:
            raise ReportError(f"paired-sample official delta is stale: {key}")
        for key_name in (
            "topology_both_valid",
            "schema_both_valid",
            "pre_division_cache_sha256_equal",
        ):
            if not as_bool(row[key_name], f"paired-sample {key}.{key_name}"):
                raise ReportError(f"paired-sample invariant failed: {key}.{key_name}")
        delta_sample_keys.add(key)
    if delta_sample_keys != {
        (candidate, sample_id) for candidate in CANDIDATES for sample_id in frozen_by_id
    }:
        raise ReportError("paired-sample coverage is incomplete")

    delta_embryo_keys: set[tuple[str, str]] = set()
    for row in paired_embryo:
        key = (row["candidate_arm"], row["embryo_id"])
        if (
            key in delta_embryo_keys
            or key
            not in {
                (candidate, embryo) for candidate in CANDIDATES for embryo in EMBRYOS
            }
            or row["control_arm"] != "R70"
        ):
            raise ReportError(f"paired-embryo identity mismatch: {key}")
        candidate = embryo_map[key]
        control = embryo_map[("R70", key[1])]
        expected = as_float(
            candidate["official_score"], "candidate embryo official"
        ) - as_float(control["official_score"], "control embryo official")
        observed = as_float(row["official_score_delta"], "paired embryo official delta")
        if abs(observed - expected) > 1e-9:
            raise ReportError(f"paired-embryo official delta is stale: {key}")
        delta_embryo_keys.add(key)
    if len(delta_embryo_keys) != 4:
        raise ReportError("paired-embryo coverage is incomplete")

    expected_scopes = {
        (arm, scope) for arm in ARMS for scope in ("EMBRYO_EQUAL_MACRO", "POOLED_MICRO")
    }
    observed_scopes = {(row["arm"], row["scope"]) for row in micro_macro}
    if observed_scopes != expected_scopes:
        raise ReportError("micro/macro scope coverage is incomplete")

    for name in (
        "cache_manifest.json",
        "cache_equivalence.json",
        "runtime_determinism.json",
        "resolved_config_verification.json",
        "runtime_receipts.json",
    ):
        require_json_pass(root / EXPERIMENT_DIR / name)
    topology = require_json_pass(root / EXPERIMENT_DIR / "topology_validation.json")
    if (
        as_int(topology.get("expected_checks"), "topology expected_checks") != 597
        or as_int(topology.get("actual_checks"), "topology actual_checks") != 597
    ):
        raise ReportError("topology validation does not cover 597 arm/sample checks")
    division = load_json(root / EXPERIMENT_DIR / "division_confusion_by_embryo.json")
    require_task(division, "division confusion")
    if set(require_dict(division.get("arms"), "division arms")) != set(ARMS):
        raise ReportError("division confusion does not cover all arms")

    runtime = load_json(root / EXPERIMENT_DIR / "runtime_receipts.json")
    baseline = require_dict(
        runtime.get("baseline_reproduction"), "baseline reproduction"
    )
    if baseline.get("status") != "PASS":
        raise ReportError("R70 bounded baseline reproduction is not PASS")
    if (
        as_int(
            runtime.get("predictor_runs_started", runtime.get("predictor_run_count")),
            "predictor_runs_started",
        )
        != 3
    ):
        raise ReportError("validation predictor logical run count is not three")
    if as_int(runtime.get("retry_count"), "runtime retry_count") != 0:
        raise ReportError("validation runtime retry count is not zero")

    tolerance = float(
        contract["experiment_freeze"]["comparison_tolerances"][
            "reported_score_absolute"
        ]
    )
    if tolerance != 0.0001:
        raise ReportError("reported score tolerance drifted")
    return (
        payload,
        per_sample,
        per_embryo,
        paired_sample,
        paired_embryo,
        micro_macro,
    )


def validate_promotion_hashes(root: Path, promotion: Mapping[str, Any]) -> None:
    hashes = require_dict(promotion.get("evidence_hashes"), "promotion evidence_hashes")
    required = {
        f"experiments/V20B/{name}"
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
    if set(hashes) != required:
        raise ReportError("promotion evidence_hashes path set mismatch")
    for relative, expected in hashes.items():
        path, canonical = safe_relative(root, relative)
        if canonical != relative or not path.is_file() or sha256_file(path) != expected:
            raise ReportError(f"promotion evidence hash drift: {relative}")


def validate_submission_path(
    root: Path,
    contract: Mapping[str, Any],
    promotion: Mapping[str, Any],
    decision: str,
    offline_decision: str,
    selected_arm: str | None,
    selected_radius: float | None,
    counts: Mapping[str, int],
    ledger_pairs: Mapping[str, Any],
) -> dict[str, Any]:
    experiment = root / EXPERIMENT_DIR
    receipt_path = experiment / "kaggle_submission_receipt.json"
    history_path = experiment / "kaggle_status_history_30m.jsonl"
    health_path = experiment / "kaggle_30m_health_summary.json"
    platform_error = ledger_has_platform_error(ledger_pairs)
    validation_result = result_for_operation(ledger_pairs, "VALIDATION_SAVE_KERNEL")
    production_result = result_for_operation(ledger_pairs, "PRODUCTION_SAVE_KERNEL")
    validation_version = (
        first_nonempty(
            validation_result,
            ("notebook_version", "returned_notebook_version", "returned_version"),
        )
        if validation_result
        else None
    )
    production_version = (
        first_nonempty(production_result, ("notebook_version", "returned_version"))
        if production_result
        else None
    )
    validation_script_id = (
        first_nonempty(
            validation_result,
            ("script_version_id", "returned_script_version_id", "ScriptVersionId"),
        )
        if validation_result
        else None
    ) or first_nonempty(promotion, ("validation_script_version_id",))
    production_script_id = (
        first_nonempty(
            production_result,
            ("script_version_id", "returned_script_version_id", "ScriptVersionId"),
        )
        if production_result
        else None
    )

    if counts["validation_save_kernel"] != 1:
        raise ReportError(
            "terminal report requires exactly one validation SaveKernel call"
        )
    if counts["retry"] != 0:
        raise ReportError("retry count is not zero")

    if counts["competition_submit"] == 0:
        if (
            receipt_path.exists()
            or history_path.exists()
            or counts["submission_status_poll"]
        ):
            raise ReportError("submission evidence/polls exist with zero submit calls")
        if offline_decision in PROMOTION_DECISIONS and not platform_error:
            raise ReportError("unique winner has no submission and no platform error")
        if (
            offline_decision not in PROMOTION_DECISIONS
            and counts["production_save_kernel"]
        ):
            raise ReportError("non-promoted result consumed a production SaveKernel")
        monitor_status = "NOT_APPLICABLE_NO_SUBMISSION"
        if health_path.is_file():
            health = load_json(health_path)
            require_task(health, "no-submission health summary")
            observed = str(health.get("status", ""))
            allowed = {"NOT_APPLICABLE_NO_SUBMISSION", decision}
            if observed not in allowed:
                raise ReportError("no-submission health summary is inconsistent")
            monitor_status = observed
        domain_status = (
            "BLOCKED_PLATFORM_ERROR"
            if offline_decision in PROMOTION_DECISIONS and platform_error
            else decision
        )
        return {
            "domain_status": domain_status,
            "submitted": False,
            "submission_id": None,
            "public_score": None,
            "monitor_status": monitor_status,
            "validation_version": validation_version,
            "validation_script_version_id": validation_script_id,
            "production_version": production_version,
            "production_script_version_id": production_script_id,
        }

    if counts["competition_submit"] != 1 or offline_decision not in PROMOTION_DECISIONS:
        raise ReportError("submission count/unique-winner decision is inconsistent")
    if counts["production_save_kernel"] != 1:
        raise ReportError("a submission requires one production SaveKernel")
    if not receipt_path.is_file():
        if (
            not platform_error
            or history_path.exists()
            or counts["submission_status_poll"]
        ):
            raise ReportError(
                "submit call lacks both receipt and platform-error evidence"
            )
        return {
            "domain_status": "BLOCKED_PLATFORM_ERROR",
            "submitted": False,
            "submission_id": None,
            "public_score": None,
            "monitor_status": "NOT_APPLICABLE_SUBMISSION_ID_NOT_CREATED",
            "validation_version": validation_version,
            "validation_script_version_id": validation_script_id,
            "production_version": production_version,
            "production_script_version_id": production_script_id,
        }

    receipt = load_json(receipt_path)
    require_task(receipt, "submission receipt")
    submission_id = first_nonempty(receipt, ("submission_id", "submissionId", "ref"))
    if submission_id is None:
        if not platform_error:
            raise ReportError("submission receipt lacks an ID and platform error")
        return {
            "domain_status": "BLOCKED_PLATFORM_ERROR",
            "submitted": False,
            "submission_id": None,
            "public_score": None,
            "monitor_status": "NOT_APPLICABLE_SUBMISSION_ID_NOT_CREATED",
            "validation_version": validation_version,
            "validation_script_version_id": validation_script_id,
            "production_version": production_version,
            "production_script_version_id": production_script_id,
        }
    baseline = contract["experiment_freeze"]["baseline"]
    identities = contract["experiment_freeze"]["identities"]
    receipt_arm = first_nonempty(receipt, ("selected_arm", "arm"))
    receipt_radius = as_float(
        first_nonempty(receipt, ("selected_radius_um", "safe_div_parent_radius_um")),
        "submission radius",
    )
    if receipt_arm != selected_arm or receipt_radius != selected_radius:
        raise ReportError("submission arm/radius differs from promotion")
    if first_nonempty(receipt, ("principal", "kaggle_principal")) != "sailorren":
        raise ReportError("submission principal is not sailorren")
    if (
        first_nonempty(receipt, ("competition", "competition_ref"))
        != baseline["competition"]
    ):
        raise ReportError("submission competition identity mismatch")
    if (
        first_nonempty(receipt, ("source_sha256", "base_source_sha256"))
        != identities["base_source_sha256"]
    ):
        raise ReportError("submission source SHA mismatch")
    if as_int(receipt.get("write_count"), "submission write_count") != 1:
        raise ReportError("submission write_count is not one")
    if as_int(receipt.get("retry_count"), "submission retry_count") != 0:
        raise ReportError("submission retry_count is not zero")
    description = str(receipt.get("description", "")).lower()
    for term in (
        "v20b",
        "safe-div parent radius",
        str(baseline["script_version_id"]),
        str(identities["base_source_sha256"])[:8],
        "two-embryo paired screen winner",
    ):
        if term not in description:
            raise ReportError("submission description lacks frozen provenance")

    if not history_path.is_file() or not health_path.is_file():
        raise ReportError("submission ID exists without monitoring evidence")
    history = load_jsonl(history_path)
    if len(history) != counts["submission_status_poll"] or not history:
        raise ReportError("history rows differ from ledger poll count")
    previous = -1.0
    last_score: float | None = None
    for index, row in enumerate(history):
        if str(first_nonempty(row, ("submission_id", "submissionId", "ref"))) != str(
            submission_id
        ):
            raise ReportError(f"status row {index} submission ID mismatch")
        elapsed = as_float(
            first_nonempty(row, ("elapsed_minutes", "t_plus_minutes")),
            f"status row {index} elapsed_minutes",
        )
        if elapsed < previous or elapsed > 30.5:
            raise ReportError(
                "monitoring history is nonmonotonic or exceeds 30 minutes"
            )
        previous = elapsed
        score = as_float(
            first_nonempty(row, ("public_score", "publicScore")),
            f"status row {index} public score",
            allow_none=True,
        )
        if score is not None:
            last_score = score

    health = load_json(health_path)
    require_task(health, "30-minute health summary")
    if str(first_nonempty(health, ("submission_id", "submissionId", "ref"))) != str(
        submission_id
    ):
        raise ReportError("health summary submission ID mismatch")
    monitor_status = str(health.get("status", ""))
    allowed_health = {
        "COMPLETED_VERIFIED_SCORE_PENDING",
        "COMPLETED_VERIFIED_EARLY_SCORE_OBSERVED",
        "SUBMISSION_ACCEPTED_RUNTIME_UNVERIFIED_SCORE_PENDING",
        "BLOCKED_PLATFORM_ERROR",
    }
    if monitor_status not in allowed_health:
        raise ReportError(f"unsupported monitoring terminal status: {monitor_status}")
    if health.get("monitoring_stopped") is not True:
        raise ReportError("health summary does not state monitoring_stopped=true")
    health_score = as_float(
        first_nonempty(health, ("public_score", "publicScore")),
        "health public score",
        allow_none=True,
    )
    public_score = health_score if health_score is not None else last_score
    if monitor_status == "COMPLETED_VERIFIED_SCORE_PENDING" and previous < 29.0:
        raise ReportError("score-pending monitoring stopped before 30 minutes")
    production_script_id = (
        first_nonempty(
            receipt,
            ("script_version_id", "ScriptVersionId", "production_script_version_id"),
        )
        or production_script_id
    )
    production_version = (
        first_nonempty(receipt, ("notebook_version", "production_notebook_version"))
        or production_version
    )
    return {
        "domain_status": monitor_status,
        "submitted": True,
        "submission_id": submission_id,
        "public_score": public_score,
        "monitor_status": monitor_status,
        "validation_version": validation_version,
        "validation_script_version_id": validation_script_id,
        "production_version": production_version,
        "production_script_version_id": production_script_id,
    }


def validate_terminal_failure_evidence(
    root: Path,
    contract: Mapping[str, Any],
    promotion: Mapping[str, Any],
    runtime: Mapping[str, Any],
    counts: Mapping[str, int],
    platform: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    terminal_path = root / EXPERIMENT_DIR / "kaggle_validation_terminal_receipt.json"
    diagnosis_path = root / EXPERIMENT_DIR / "failure_diagnosis.json"
    if not terminal_path.exists() and not diagnosis_path.exists():
        if promotion.get("decision") == "BLOCKED_VALIDATION_PAYLOAD_OR_RUNTIME":
            raise ReportError("blocked validation lacks terminal receipt and diagnosis")
        return {}, {}
    if not terminal_path.is_file() or not diagnosis_path.is_file():
        raise ReportError("terminal validation receipt/diagnosis pair is incomplete")
    terminal = load_json(terminal_path)
    diagnosis = load_json(diagnosis_path)
    require_task(terminal, "validation terminal receipt")
    require_task(diagnosis, "failure diagnosis")
    failure = require_dict(terminal.get("failure"), "terminal failure")
    notebook = require_dict(terminal.get("notebook"), "terminal notebook")
    terminal_platform = require_dict(terminal.get("platform"), "terminal platform")
    runtime_failure = require_dict(
        diagnosis.get("runtime_failure"), "diagnosed runtime failure"
    )
    root_cause = require_dict(diagnosis.get("root_cause"), "diagnosed root cause")
    evidence = require_dict(
        diagnosis.get("evidence_boundary"), "diagnosed evidence boundary"
    )
    write_boundary = require_dict(
        terminal.get("write_boundary"), "terminal write boundary"
    )

    expected_failure = {
        "decision": promotion.get("decision"),
        "failed_stage": promotion.get("failed_stage"),
        "error_type": promotion.get("error_type"),
        "error": promotion.get("error"),
    }
    if any(failure.get(key) != value for key, value in expected_failure.items()):
        raise ReportError("terminal failure differs from promotion receipt")
    if any(
        runtime.get(key) != promotion.get(key)
        for key in ("failed_stage", "error_type", "error")
    ):
        raise ReportError("runtime failure differs from promotion receipt")
    if any(
        runtime_failure.get(key) != promotion.get(key)
        for key in ("failed_stage", "error_type", "error")
    ):
        raise ReportError("diagnosed failure differs from promotion receipt")
    if diagnosis.get("terminal_domain_status") != promotion.get("decision"):
        raise ReportError("failure diagnosis terminal status mismatch")
    if diagnosis.get(
        "status"
    ) != "ROOT_CAUSE_IDENTIFIED_NO_RETRY" or not root_cause.get("code"):
        raise ReportError("failure diagnosis lacks a frozen no-retry root cause")
    if terminal_platform.get("worker_status") != "KernelWorkerStatus.ERROR":
        raise ReportError("blocked validation terminal worker is not ERROR")
    if failure.get("arm_metrics_produced") is not False:
        raise ReportError("terminal receipt does not deny arm metric production")
    if failure.get("unique_offline_winner_evaluated") is not False:
        raise ReportError("terminal receipt incorrectly evaluated an offline winner")
    if evidence.get("unique_offline_winner") is not None:
        raise ReportError("diagnosis invents an offline winner")
    if any(evidence.get(f"{arm}_metrics") != "NOT_RUN" for arm in ARMS):
        raise ReportError("diagnosis arm metrics are not all NOT_RUN")
    if (
        evidence.get("production_notebook_allowed") is not False
        or evidence.get("formal_submission_allowed") is not False
    ):
        raise ReportError("diagnosis incorrectly allows production/submission")
    for terminal_key, ledger_key in (
        ("validation_save_kernel", "validation_save_kernel"),
        ("production_save_kernel", "production_save_kernel"),
        ("save_kernel_total", "save_kernel_total"),
        ("notebook_run", "notebook_run"),
        ("competition_submit", "competition_submit"),
        ("dataset_write", "dataset_write"),
        ("model_write", "model_write"),
        ("duplicate_submit", "duplicate_submit"),
        ("retry", "retry"),
    ):
        if (
            as_int(write_boundary.get(terminal_key), f"terminal write {terminal_key}")
            != counts[ledger_key]
        ):
            raise ReportError(f"terminal write boundary differs for {terminal_key}")

    notebook_version = first_nonempty(notebook, ("notebook_version", "version"))
    script_version_id = first_nonempty(
        notebook, ("script_version_id", "ScriptVersionId")
    )
    if str(notebook_version) != str(platform.get("validation_version")):
        raise ReportError("terminal Notebook Version differs from ledger")
    if as_int(script_version_id, "validation ScriptVersionId") <= 0:
        raise ReportError("terminal validation ScriptVersionId is invalid")
    if str(script_version_id) != str(platform.get("validation_script_version_id")):
        raise ReportError("terminal validation ScriptVersionId differs from ledger")
    if str(runtime_failure.get("script_version_id")) != str(script_version_id):
        raise ReportError("diagnosed validation ScriptVersionId mismatch")
    if str(runtime_failure.get("notebook_version")) != str(notebook_version):
        raise ReportError("diagnosed validation Notebook Version mismatch")
    if as_int(
        failure.get("predictor_runs_started"), "terminal predictor runs"
    ) != as_int(runtime.get("predictor_runs_started"), "runtime predictor runs"):
        raise ReportError("terminal/runtime predictor run count mismatch")
    internal_seconds = as_float(
        failure.get("validation_wall_clock_seconds"), "terminal validation seconds"
    )
    runtime_seconds = as_float(
        runtime.get("validation_wall_clock_seconds"), "runtime validation seconds"
    )
    if abs(internal_seconds - runtime_seconds) > 1e-9:
        raise ReportError("terminal/runtime wall-clock seconds mismatch")
    source_comparison = require_dict(
        diagnosis.get("source_comparison"), "diagnosed source comparison"
    )
    source_sha = source_comparison.get("v19c_source_notebook_sha256")
    if source_sha != contract["experiment_freeze"]["identities"]["base_source_sha256"]:
        raise ReportError("failure diagnosis V19C source SHA mismatch")

    download = require_dict(terminal.get("download"), "terminal filtered download")
    if download.get("large_cache_or_prediction_downloaded") is not False:
        raise ReportError("terminal receipt indicates a large output download")
    for raw_file in require_list(download.get("files"), "terminal downloaded files"):
        entry = require_dict(raw_file, "terminal downloaded file")
        path, relative = safe_relative(root, entry.get("path"))
        if (
            not path.is_file()
            or path.stat().st_size
            != as_int(entry.get("bytes"), f"terminal file bytes {relative}")
            or sha256_file(path) != entry.get("sha256")
        ):
            raise ReportError(f"terminal downloaded file hash drift: {relative}")
    platform["validation_version"] = notebook_version
    platform["validation_script_version_id"] = script_version_id
    return terminal, diagnosis


def collect_input_hashes(
    root: Path, manifest_hashes: Mapping[str, str]
) -> dict[str, str]:
    names = {
        "contract.json",
        "sample_manifest.json",
        "evidence_boundary.json",
        "write_budget.json",
        "platform_write_ledger.json",
        "promotion_decision.json",
        "runtime_receipts.json",
        "artifact_manifest.json",
        "kaggle_submission_receipt.json",
        "kaggle_status_history_30m.jsonl",
        "kaggle_30m_health_summary.json",
        "kaggle_validation_terminal_receipt.json",
        "failure_diagnosis.json",
        "kaggle_validation_v1_log.txt",
    }
    result = dict(manifest_hashes)
    for name in names:
        relative = EXPERIMENT_DIR / name
        path = root / relative
        if path.is_file():
            result[relative.as_posix()] = sha256_file(path)
    return dict(sorted(result.items()))


def load_and_validate(root: Path) -> ReportModel:
    root = root.resolve()
    contract = load_json(root / EXPERIMENT_DIR / "contract.json")
    boundary = load_json(root / EXPERIMENT_DIR / "evidence_boundary.json")
    promotion = load_json(root / EXPERIMENT_DIR / "promotion_decision.json")
    runtime = load_json(root / EXPERIMENT_DIR / "runtime_receipts.json")
    ledger = load_json(root / EXPERIMENT_DIR / "platform_write_ledger.json")
    budget = load_json(root / EXPERIMENT_DIR / "write_budget.json")
    manifest = load_json(root / EXPERIMENT_DIR / "artifact_manifest.json")
    validate_contract_and_boundary(contract, boundary)
    require_task(runtime, "runtime receipts")
    require_task(budget, "write budget")
    limits = require_dict(budget.get("limits"), "write budget limits")
    if any(
        limits.get(key) != expected
        for key, expected in {
            "validation_save_kernel": 1,
            "production_save_kernel": 1,
            "save_kernel_total": 2,
            "notebook_runs_total": 2,
            "formal_competition_submission": 1,
            "retry": 0,
            "duplicate_submission": 0,
            "dataset_write": 0,
            "model_write": 0,
        }.items()
    ):
        raise ReportError("write budget differs from frozen limits")
    counts, ledger_pairs = validate_ledger(ledger)

    provisional_decision = str(promotion.get("decision", ""))
    provisional_offline = str(
        promotion.get(
            "offline_decision",
            promotion.get("pre_platform_decision", provisional_decision),
        )
    )
    offline_complete = provisional_offline in (
        PROMOTION_DECISIONS | NO_SUBMISSION_DECISIONS
    )
    decision, offline_decision, selected, selected_radius = validate_promotion(
        promotion, complete=offline_complete
    )
    manifest_hashes = validate_artifact_manifest(
        root, manifest, complete=offline_complete
    )

    payload_rows: list[dict[str, str]] = []
    per_sample_rows: list[dict[str, str]] = []
    per_embryo_rows: list[dict[str, str]] = []
    paired_sample_rows: list[dict[str, str]] = []
    paired_embryo_rows: list[dict[str, str]] = []
    micro_macro_rows: list[dict[str, str]] = []
    if offline_complete:
        (
            payload_rows,
            per_sample_rows,
            per_embryo_rows,
            paired_sample_rows,
            paired_embryo_rows,
            micro_macro_rows,
        ) = validate_complete_tables(root, contract)
        validate_promotion_hashes(root, promotion)
    elif str(promotion.get("status", "")).upper() not in {"FAIL_CLOSED", "BLOCKED"}:
        raise ReportError("blocked decision lacks a FAIL_CLOSED promotion receipt")
    elif decision != "BLOCKED_PLATFORM_ERROR":
        if (
            str(runtime.get("status", "")).upper() != "FAIL_CLOSED"
            or runtime.get("all_pass") is not False
            or runtime.get("failed_stage") != promotion.get("failed_stage")
            or as_int(runtime.get("retry_count"), "blocked runtime retry_count") != 0
            or as_int(
                promotion.get("competition_submission_count"),
                "blocked promotion competition_submission_count",
            )
            != 0
        ):
            raise ReportError("blocked promotion/runtime failure receipts disagree")

    platform = validate_submission_path(
        root,
        contract,
        promotion,
        decision,
        offline_decision,
        selected,
        selected_radius,
        counts,
        ledger_pairs,
    )
    validation_terminal, failure_diagnosis = validate_terminal_failure_evidence(
        root, contract, promotion, runtime, counts, platform
    )
    return ReportModel(
        contract=contract,
        boundary=boundary,
        promotion=promotion,
        runtime=runtime,
        ledger=ledger,
        counts=counts,
        decision=decision,
        offline_decision=offline_decision,
        domain_status=platform["domain_status"],
        selected_arm=selected,
        selected_radius_um=selected_radius,
        submitted=platform["submitted"],
        submission_id=platform["submission_id"],
        public_score=platform["public_score"],
        monitor_status=platform["monitor_status"],
        validation_version=platform["validation_version"],
        validation_script_version_id=platform["validation_script_version_id"],
        production_version=platform["production_version"],
        production_script_version_id=platform["production_script_version_id"],
        payload_rows=payload_rows,
        per_sample_rows=per_sample_rows,
        per_embryo_rows=per_embryo_rows,
        paired_sample_rows=paired_sample_rows,
        paired_embryo_rows=paired_embryo_rows,
        micro_macro_rows=micro_macro_rows,
        input_hashes=collect_input_hashes(root, manifest_hashes),
        blocked_stage=(
            str(promotion.get("failed_stage"))
            if promotion.get("failed_stage") not in (None, "")
            else None
        ),
        validation_terminal=validation_terminal,
        failure_diagnosis=failure_diagnosis,
    )


def display(value: Any) -> str:
    if value is None or value == "":
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def number(value: Any, digits: int = 8) -> str:
    parsed = as_float(value, "report numeric value", allow_none=True)
    if parsed is None:
        return "null"
    if abs(parsed) >= 1_000_000:
        return f"{parsed:.3f}"
    rendered = f"{parsed:.{digits}f}".rstrip("0").rstrip(".")
    return "0" if rendered in {"-0", ""} else rendered


def md_cell(value: Any) -> str:
    return (
        display(value)
        .replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\r", " ")
        .replace("\n", "<br>")
    )


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    lines = [
        "| " + " | ".join(md_cell(value) for value in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend(
        "| " + " | ".join(md_cell(value) for value in row) + " |" for row in rows
    )
    return "\n".join(lines)


def html_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    head = "".join(f"<th>{html.escape(display(value))}</th>" for value in headers)
    body = "".join(
        "<tr>"
        + "".join(f"<td>{html.escape(display(value))}</td>" for value in row)
        + "</tr>"
        for row in rows
    )
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def arm_statuses(model: ReportModel) -> dict[str, str]:
    result: dict[str, str] = {}
    diagnosed_boundary = model.failure_diagnosis.get("evidence_boundary")
    if not isinstance(diagnosed_boundary, dict):
        diagnosed_boundary = {}
    for arm in ARMS:
        rows = [row for row in model.per_sample_rows if row.get("arm") == arm]
        if len(rows) == EXPECTED_SAMPLE_COUNT and all(
            row.get("status") == "RUN_COMPLETE" for row in rows
        ):
            result[arm] = "RUN_COMPLETE_199_OF_199"
        elif rows:
            statuses = sorted({row.get("status", "UNKNOWN") for row in rows})
            result[arm] = f"PARTIAL_{len(rows)}_ROWS_{'+'.join(statuses)}"
        elif diagnosed_boundary.get(f"{arm}_metrics") not in (None, ""):
            result[arm] = str(diagnosed_boundary[f"{arm}_metrics"])
        else:
            result[arm] = "NOT_AVAILABLE_VALIDATION_BLOCKED"
    return result


def embryo_metric_rows(model: ReportModel) -> list[list[Any]]:
    index = {(row["arm"], row["embryo_id"]): row for row in model.per_embryo_rows}
    rows: list[list[Any]] = []
    for arm in ARMS:
        for embryo in EMBRYOS:
            row = index.get((arm, embryo))
            if row is None:
                rows.append([arm, embryo, "NOT_AVAILABLE", "null"] + ["null"] * 10)
                continue
            rows.append(
                [
                    arm,
                    embryo,
                    row["status"],
                    row["sample_count"],
                    number(row["official_score"]),
                    number(row["division_jaccard"]),
                    row["division_tp"],
                    row["division_fp"],
                    row["division_fn"],
                    number(row["node_count_penalty"]),
                    number(row["frame_cap_saturation_rate"]),
                    number(row["global_cap_saturation_rate"]),
                    row["topology_valid"],
                    number(row["runtime_seconds"], 3),
                ]
            )
    return rows


EMBRYO_HEADERS = (
    "arm",
    "embryo",
    "status",
    "samples",
    "offline official score",
    "division Jaccard",
    "division TP",
    "division FP",
    "division FN",
    "node-count penalty",
    "frame cap rate",
    "global cap rate",
    "topology valid",
    "runtime seconds",
)


def macro_micro_rows(model: ReportModel) -> list[list[Any]]:
    result: list[list[Any]] = []
    for row in sorted(
        model.micro_macro_rows,
        key=lambda item: (ARMS.index(item["arm"]), item["scope"]),
    ):
        result.append(
            [
                row["arm"],
                row["scope"],
                row["sample_count"],
                number(row["official_score"]),
                number(row["adj_edge_jaccard"]),
                number(row["division_jaccard"]),
                number(row["node_count_penalty"]),
                row["topology_valid"],
                row["schema_valid"],
                number(row["runtime_seconds"], 3),
            ]
        )
    if not result:
        for arm in ARMS:
            for scope in ("EMBRYO_EQUAL_MACRO", "POOLED_MICRO"):
                result.append([arm, scope, "null"] + ["null"] * 7)
    return result


MACRO_HEADERS = (
    "arm",
    "scope",
    "samples",
    "offline official score",
    "adjusted edge Jaccard",
    "division Jaccard",
    "node-count penalty",
    "topology valid",
    "schema valid",
    "runtime seconds",
)


def candidate_gate_rows(model: ReportModel) -> list[list[Any]]:
    gates = model.promotion.get("candidate_gates")
    if not isinstance(gates, dict):
        return [
            [candidate, "NOT_AVAILABLE_VALIDATION_BLOCKED", "null"]
            for candidate in CANDIDATES
        ]
    rows: list[list[Any]] = []
    for candidate in CANDIDATES:
        candidate_gates = gates.get(candidate)
        if not isinstance(candidate_gates, dict):
            rows.append([candidate, "NOT_AVAILABLE", "null"])
            continue
        for gate, passed in candidate_gates.items():
            rows.append([candidate, gate, display(passed)])
    return rows


def sample_delta_rows(model: ReportModel) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for row in sorted(
        model.paired_sample_rows,
        key=lambda item: (CANDIDATES.index(item["candidate_arm"]), item["sample_id"]),
    ):
        rows.append(
            [
                row["candidate_arm"],
                row["sample_id"],
                row["embryo_id"],
                number(row["official_score_delta"]),
                number(row["adj_edge_jaccard_delta"]),
                number(row["division_jaccard_delta"]),
                number(row["division_tp_delta"], 3),
                number(row["division_fp_delta"], 3),
                number(row["division_fn_delta"], 3),
                number(row["node_count_penalty_delta"]),
                number(row["frame_cap_saturation_delta"]),
                number(row["global_cap_saturation_delta"]),
                row["topology_both_valid"],
                row["schema_both_valid"],
                row["pre_division_cache_sha256_equal"],
            ]
        )
    return rows


SAMPLE_DELTA_HEADERS = (
    "candidate",
    "sample",
    "embryo",
    "official score delta",
    "adjusted edge delta",
    "division Jaccard delta",
    "division TP delta",
    "division FP delta",
    "division FN delta",
    "node-count penalty delta",
    "frame cap delta",
    "global cap delta",
    "topology both valid",
    "schema both valid",
    "shared cache SHA equal",
)


def embryo_delta_rows(model: ReportModel) -> list[list[Any]]:
    result: list[list[Any]] = []
    for row in sorted(
        model.paired_embryo_rows,
        key=lambda item: (CANDIDATES.index(item["candidate_arm"]), item["embryo_id"]),
    ):
        result.append(
            [
                row["candidate_arm"],
                row["embryo_id"],
                row["sample_count"],
                number(row["official_score_delta"]),
                number(row["division_jaccard_delta"]),
                number(row["division_tp_delta"], 3),
                number(row["division_fp_delta"], 3),
                number(row["division_fn_delta"], 3),
                number(row["node_count_penalty_delta"]),
                number(row["frame_cap_saturation_rate_delta"]),
                number(row["global_cap_saturation_rate_delta"]),
            ]
        )
    if not result:
        return [
            [candidate, embryo, "null"] + ["null"] * 8
            for candidate in CANDIDATES
            for embryo in EMBRYOS
        ]
    return result


EMBRYO_DELTA_HEADERS = (
    "candidate",
    "embryo",
    "samples",
    "official score delta",
    "division Jaccard delta",
    "division TP delta",
    "division FP delta",
    "division FN delta",
    "node-count penalty delta",
    "frame cap rate delta",
    "global cap rate delta",
)


def scope_score(model: ReportModel, arm: str, scope: str) -> float | None:
    for row in model.micro_macro_rows:
        if row.get("arm") == arm and row.get("scope") == scope:
            return as_float(
                row.get("official_score"), f"{arm}/{scope} score", allow_none=True
            )
    return None


def macro_micro_direction_answer(model: ReportModel) -> str:
    if not model.micro_macro_rows:
        return "验证在聚合阶段前已阻断，embryo-equal macro 与 pooled micro 均无可用结果，不能判断方向是否一致。"
    details: list[str] = []
    r70_macro = scope_score(model, "R70", "EMBRYO_EQUAL_MACRO")
    r70_micro = scope_score(model, "R70", "POOLED_MICRO")
    if r70_macro is None or r70_micro is None:
        raise ReportError("R70 macro/micro score is absent")
    for candidate in CANDIDATES:
        candidate_macro = scope_score(model, candidate, "EMBRYO_EQUAL_MACRO")
        candidate_micro = scope_score(model, candidate, "POOLED_MICRO")
        if candidate_macro is None or candidate_micro is None:
            raise ReportError(f"{candidate} macro/micro score is absent")
        macro_delta = candidate_macro - r70_macro
        micro_delta = candidate_micro - r70_micro
        same_direction = (macro_delta >= 0 and micro_delta >= 0) or (
            macro_delta <= 0 and micro_delta <= 0
        )
        details.append(
            f"{candidate}: macro delta={number(macro_delta)}, pooled micro delta={number(micro_delta)}, "
            f"方向一致={display(same_direction)}"
        )
    return (
        "；".join(details)
        + "。方向一致只描述这两种聚合口径，不构成统计显著性或跨胚胎泛化证明。"
    )


def production_na_label(model: ReportModel) -> str:
    if model.decision == "NO_UNIQUE_WINNER_NO_SUBMISSION":
        return "NOT_APPLICABLE_NO_UNIQUE_OFFLINE_WINNER"
    if model.offline_decision == "NO_PROMOTION_KEEP_V19C_R70":
        return "NOT_APPLICABLE_NO_PROMOTION"
    if model.offline_decision in BLOCKED_DECISIONS:
        return "NOT_APPLICABLE_VALIDATION_BLOCKED"
    return "NOT_APPLICABLE_PLATFORM_WRITE_FAILED"


def question_answers(model: ReportModel) -> list[tuple[str, str]]:
    full_payload = len(model.payload_rows) == 199 and all(
        row.get("status") == "PASS" for row in model.payload_rows
    )
    cache_pass = model.promotion.get("cache_equivalence_pass") is True
    baseline = model.runtime.get("baseline_reproduction")
    baseline_status = (
        baseline.get("status") if isinstance(baseline, dict) else "NOT_AVAILABLE"
    )
    selected = display(model.selected_arm)
    radius = number(model.selected_radius_um)
    submission_id = display(model.submission_id)
    public_score = number(model.public_score)
    arm_status = arm_statuses(model)
    production_state = (
        f"CREATED, Notebook Version={display(model.production_version)}, "
        f"ScriptVersionId={display(model.production_script_version_id)}"
        if model.production_version is not None
        or model.production_script_version_id is not None
        else production_na_label(model)
    )
    notebook_answer = (
        f"validation：Notebook Version={display(model.validation_version)}，"
        f"ScriptVersionId={display(model.validation_script_version_id)}；"
        f"production：{production_state}。"
    )
    gaps = [
        f"{OVERLAP_STATUS}：checkpoint 训练集合与 split 未闭合",
        "仅有两个训练胚胎，199 个 field of view 不是 199 个独立生物重复",
        "离线 official scorer 结果不是 hidden-test Public Score，也不证明 Kaggle 提分",
    ]
    if model.public_score is None:
        gaps.append(
            "新的 V20B Public Score 当前为 null；没有观察到的分数就没有性能提升证据"
        )
    if not model.submitted:
        gaps.append("本路径没有创建带 submission ID 的 V20B 正式提交")
    if model.blocked_stage:
        gaps.append(f"验证或平台路径在阶段 {model.blocked_stage} fail-closed")
    root_cause = model.failure_diagnosis.get("root_cause")
    if isinstance(root_cause, dict) and root_cause.get("code"):
        gaps.append(
            f"已定位运行根因 {root_cause['code']}；冻结 retry=0 不授权修复后重跑"
        )

    candidate_text = (
        f"有唯一 Kaggle test candidate：{selected}，parent radius={radius} µm。"
        if model.selected_arm
        else f"没有唯一 Kaggle test candidate；decision={model.decision}，selected radius=null。"
    )
    submission_text = (
        f"是；只观察到一个带 ID 的 V20B submission，submission ID={submission_id}。"
        if model.submitted
        else "否；没有带 submission ID 的 V20B 正式 submission。"
    )
    monitoring_text = (
        f"{model.monitor_status}；poll count={model.counts['submission_status_poll']}。{STOP_MESSAGE}"
        if model.submitted
        else (
            f"{model.monitor_status}；poll count=0。监控不适用、未来读分仍须用户明确通知。"
        )
    )
    return [
        (
            "V20A 为什么停止",
            f"V20A 的冻结领域状态保持为 {V20A_STATUS}，因为当时合同要求至少 3 个 embryo groups；实际只有 44b6 与 6bba 两组。因此 V20A 的 R70/R80/R90 都保持 NOT_RUN_HARD_GATE，V20B 没有回填或改写这段历史。",
        ),
        (
            "V20B 为什么允许两个 embryo 的配对敏感性实验",
            "V20B 是新冻结合同，把目标限定为 TWO_EMBRYO_PAIRED_SENSITIVITY_SCREEN：同一批 199 个样本在共享 pre-division cache 下只改变 safe-div parent radius，并分别保留 44b6 与 6bba 两个报告层。它允许做方向一致性和敏感性筛选，但不把两组扩写成多折验证。",
        ),
        (
            "为什么本实验不是 CV",
            "没有训练/验证折轮换、没有 held-out fold，也没有 3-fold 或 5-fold；两个 embryo 都是训练侧带标签数据上的配对评估。每个 embryo 内的 field of view 也不是独立生物重复，因此不得称为 CV 或以 sample-level 显著性推断跨胚胎泛化。",
        ),
        (
            "checkpoint overlap 为什么仍是 UNKNOWN",
            f"当前证据只固定了 checkpoint SHA，没有闭合 checkpoint 的训练样本和 split；因此必须持续写 {OVERLAP_STATUS}，不能从文件 hash 推断训练重叠不存在。",
        ),
        (
            "是否实际读取全部 199 个 payload",
            (
                "是。full_sample_payload_inventory.csv 有 199 行 PASS：44b6 为 71/71、6bba 为 128/128；每行同时记录 image/Zarr、GT GEFF 与 scorer metadata 的实际可读状态。"
                if full_payload
                else "否或未能证明。完整 199 个 payload 的 PASS 证据不存在，报告不把文件名枚举当作 payload 读取。"
            ),
        ),
        (
            "cache 是否通过完整运行等价性验证",
            (
                "是。两个 anchor 上 R70/R80/R90 的 same-raw full、fresh full 与 cached downstream 证据均绑定共享 pre-division cache；promotion receipt 标记 cache_equivalence_pass=true。"
                if cache_pass
                else "否或未到达；cache equivalence 没有 PASS，所以不得晋升或提交。"
            ),
        ),
        (
            "R70 是否复现",
            (
                "否。R70 metrics=NOT_RUN；运行在 PREDICTOR_PATCHES、predictor subprocess 启动前 fail-closed，因此没有 R70 复现证据。"
                if arm_status["R70"] == "NOT_RUN"
                else f"R70 bounded reproduction status={baseline_status}。这里的复现范围仅是两个 anchor 的 full/cache 等价和 R70 两次确定性检查；它不是把训练侧离线分数与历史 Kaggle Public Score 0.939 直接相等，也不是 hidden-test 复现。"
            ),
        ),
        (
            "R80/R90 相对 R70 的每 sample 和每 embryo delta",
            f"逐 sample 配对表共有 {len(model.paired_sample_rows)} 行，逐 embryo 配对表共有 {len(model.paired_embryo_rows)} 行；完整数值列于附录 A/B。没有用 pooled 结果替代两个 embryo 的独立 delta。arm 状态为 R70={arm_status['R70']}、R80={arm_status['R80']}、R90={arm_status['R90']}。",
        ),
        (
            "embryo-equal macro 与 pooled micro 是否一致",
            macro_micro_direction_answer(model),
        ),
        (
            "division TP/FP/FN 如何变化",
            "R80/R90 相对 R70 的 division TP、FP、FN 变化分别按 44b6、6bba 列于附录 B，逐 sample 变化列于附录 A；主表同时给出每个 arm 的绝对 confusion counts。晋升 gate 还要求 FP 增长必须由新增 TP 与 official total gain 补偿。",
        ),
        (
            "是否出现 cap、topology 或 node-count 风险",
            (
                "未评估：三个 arm 的 metrics 均为 NOT_RUN，所以 cap、topology 与 node-count 风险都是 NOT_AVAILABLE，而不是 PASS。运行失败本身发生在指标生成之前。"
                if not model.per_sample_rows
                else "风险不凭摘要猜测：主表和附录报告 frame/global cap、topology/schema 与 node-count penalty；candidate_gates 中 cap_saturation_not_materially_worse、topology_and_schema_all_pass、node_count_penalty_no_unexplained_degradation 的逐项结果列于下方。任何 gate=false 都不能被总体 pooled 分数覆盖。"
            ),
        ),
        (
            "是否有唯一 Kaggle test candidate",
            candidate_text
            + " 离线候选措辞仅为 Kaggle test candidate，不表示已证明提分、预计高于 0.939 或新最佳。",
        ),
        ("是否创建 Notebook Version", notebook_answer),
        ("是否创建 submission", submission_text),
        ("submission ID", f"submission ID={submission_id}。未创建时严格写 null。"),
        ("30 分钟状态", monitoring_text),
        (
            "Public Score 当前值或 null",
            f"V20B 当前 Public Score={public_score}。历史 V19C Public Score=0.939 仅绑定 baseline submission 55978992，不得代填到 V20B。",
        ),
        (
            "retry 是否为 0",
            f"是；ledger retry={model.counts['retry']}，validation/production/submission 任一路径均禁止自动重试。duplicate_submit={model.counts['duplicate_submit']}。",
        ),
        ("未解决的证据缺口", "；".join(gaps) + "。"),
        (
            "后续必须由用户显式通知读取分数",
            "是。未来任何 Public Score 回读都需要用户新的明确通知；本任务不后台 sleep、不建 cron、不等待约 10 小时，也不因 pending 或无分数创建新 Version/重复提交。",
        ),
    ]


def overview_rows(model: ReportModel) -> list[list[Any]]:
    platform = model.validation_terminal.get("platform")
    worker_status = (
        platform.get("worker_status") if isinstance(platform, dict) else None
    )
    return [
        ["task_id", TASK_ID],
        ["screen", SCREEN_NAME],
        ["报告构建状态", "EVIDENCE_ASSEMBLED_PENDING_INDEPENDENT_VERIFIER"],
        ["最终领域状态", model.domain_status],
        ["offline promotion decision", model.offline_decision],
        ["terminal promotion decision", model.decision],
        ["selected arm", display(model.selected_arm)],
        ["selected radius um", number(model.selected_radius_um)],
        ["submitted", display(model.submitted)],
        ["submission ID", display(model.submission_id)],
        ["Public Score", number(model.public_score)],
        ["validation worker status", display(worker_status)],
        ["checkpoint overlap", OVERLAP_STATUS],
    ]


def count_rows(model: ReportModel) -> list[list[Any]]:
    labels = (
        ("validation SaveKernel", "validation_save_kernel"),
        ("production SaveKernel", "production_save_kernel"),
        ("SaveKernel total", "save_kernel_total"),
        ("Kaggle Notebook platform run", "notebook_run"),
        ("formal competition submission", "competition_submit"),
        ("submission status poll", "submission_status_poll"),
        ("retry", "retry"),
        ("duplicate submission", "duplicate_submit"),
        ("Dataset write", "dataset_write"),
        ("Model write", "model_write"),
        ("unauthorized Kaggle write", "unauthorized_kaggle_write"),
    )
    return [[label, model.counts[key]] for label, key in labels]


def notebook_rows(model: ReportModel) -> list[list[Any]]:
    production_status = (
        "CREATED_OR_RETURNED"
        if model.production_version is not None
        or model.production_script_version_id is not None
        else production_na_label(model)
    )
    return [
        [
            "historical V19C baseline",
            "1",
            "346969653",
            "55978992",
            "0.939",
            "OBSERVED_HISTORICAL_ONLY",
        ],
        [
            "V20B validation",
            display(model.validation_version),
            display(model.validation_script_version_id),
            "null",
            "null",
            "VALIDATION_EVIDENCE_ONLY",
        ],
        [
            "V20B production",
            display(model.production_version),
            display(model.production_script_version_id),
            display(model.submission_id),
            number(model.public_score),
            production_status,
        ],
    ]


def failure_detail_rows(model: ReportModel) -> list[list[Any]]:
    if not model.validation_terminal and not model.failure_diagnosis:
        return [["failure path", "NOT_APPLICABLE_NO_VALIDATION_FAILURE"]]
    terminal_failure = model.validation_terminal.get("failure")
    terminal_platform = model.validation_terminal.get("platform")
    root_cause = model.failure_diagnosis.get("root_cause")
    diagnosis_boundary = model.failure_diagnosis.get("evidence_boundary")
    if not isinstance(terminal_failure, dict):
        terminal_failure = {}
    if not isinstance(terminal_platform, dict):
        terminal_platform = {}
    if not isinstance(root_cause, dict):
        root_cause = {}
    if not isinstance(diagnosis_boundary, dict):
        diagnosis_boundary = {}
    return [
        ["worker status", display(terminal_platform.get("worker_status"))],
        ["failed stage", display(terminal_failure.get("failed_stage"))],
        ["error type", display(terminal_failure.get("error_type"))],
        ["observed error", display(terminal_failure.get("error"))],
        [
            "internal wall-clock seconds",
            number(terminal_failure.get("validation_wall_clock_seconds"), 6),
        ],
        [
            "platform log runtime seconds",
            number(terminal_failure.get("platform_log_runtime_seconds"), 3),
        ],
        [
            "authenticated UI runtime",
            display(terminal_platform.get("authenticated_ui_runtime")),
        ],
        [
            "predictor runs started",
            display(terminal_failure.get("predictor_runs_started")),
        ],
        [
            "payload preflight completed",
            display(diagnosis_boundary.get("payload_preflight_completed")),
        ],
        ["R70 metrics", display(diagnosis_boundary.get("R70_metrics"))],
        ["R80 metrics", display(diagnosis_boundary.get("R80_metrics"))],
        ["R90 metrics", display(diagnosis_boundary.get("R90_metrics"))],
        ["root-cause code", display(root_cause.get("code"))],
        ["root-cause summary", display(root_cause.get("summary"))],
    ]


NOTEBOOK_HEADERS = (
    "object",
    "Notebook Version",
    "ScriptVersionId",
    "submission ID",
    "Public Score",
    "evidence status",
)


FROZEN_GATE_ROWS = (
    ("两个 embryo official score 均不劣于 R70", "容差 0.0001；不得只看 pooled"),
    ("至少一个 embryo 严格改善", "strict positive epsilon=1e-12"),
    ("embryo-equal macro 严格改善", "两个 embryo 等权，防止 128 样本组压过 71 样本组"),
    ("pooled micro 不劣", "容差 0.0001；仅为并行聚合口径"),
    ("pooled division Jaccard 严格改善", "不能只用 division recall"),
    ("任一 embryo division Jaccard 无实质下降", "最大允许下降 0.0001"),
    ("division FP 增长被补偿", "需要新增 TP 且 official total gain 为正"),
    ("topology 与 schema 全部通过", "597 个 arm/sample 检查"),
    ("cap saturation 无实质恶化", "frame/global cap 均纳入"),
    ("node-count penalty 无无法解释恶化", "不能被总体分数掩盖"),
    ("收益不完全由单 sample 驱动", "至少两个正向 sample"),
    (
        "source/cache/checkpoint/input/support/scorer identity 一致",
        "共享 upstream cache",
    ),
    ("唯一变化为 parent radius", "R70=7.0、R80=8.0、R90=9.0"),
    ("runtime 在冻结预算内", "validation 39600 秒；production 2700 秒"),
)

METRIC_ROWS = tuple(
    (index, name, scope)
    for index, (name, scope) in enumerate(
        (
            ("official total score", "sample / embryo / global"),
            ("adjusted edge score/Jaccard", "sample / embryo / global"),
            ("division Jaccard", "sample / embryo / global"),
            ("division TP、FP、FN", "sample / embryo / global"),
            ("node-count adjustment/penalty", "sample / embryo / global"),
            ("predicted node count", "sample / embryo / global"),
            ("GT/estimated node count 与证据等级", "sample / embryo / global"),
            ("edge TP、FP、FN", "sample / embryo / global"),
            ("fragmented edges", "sample / embryo / global"),
            ("lost-to-detection edges", "sample / embryo / global"),
            ("wrong-association edges", "sample / embryo / global"),
            ("safe-division candidate count", "sample / embryo / global"),
            ("accepted division count", "sample / embryo / global"),
            ("DeepCenter accepted/rejected count", "sample / embryo / global"),
            ("frame cap saturation", "sample / embryo / global"),
            ("global cap saturation", "sample / embryo / global"),
            ("topology validity", "sample / embryo / global"),
            ("schema validity", "sample / embryo / global"),
            ("runtime", "sample / embryo / global"),
            ("peak memory", "sample / embryo / global"),
            ("pre-division cache SHA", "sample / embryo / global"),
            ("final output SHA", "sample / embryo / global"),
        ),
        1,
    )
)


def render_markdown(model: ReportModel) -> str:
    answers = question_answers(model)
    if len(answers) != 20:
        raise ReportError("report does not contain exactly twenty answers")
    lines = [
        "# Biohub V20B 两胚胎配对 safe-div parent radius 实验报告 V01",
        "",
        "> 结论边界：本报告汇总冻结证据，但不自行授予 `COMPLETED_VERIFIED`。只有独立领域验证器在读取本报告、重算 promotion、检查秘密与写入预算后，才可在冻结合同范围内给出交付核验状态。交付核验不等于性能提升。",
        "",
        "## 结论先行",
        "",
        markdown_table(("字段", "观察值"), overview_rows(model)),
        "",
        f"最终领域状态为 `{md_cell(model.domain_status)}`，离线 decision 为 `{md_cell(model.offline_decision)}`。selected radius={md_cell(number(model.selected_radius_um))}。V20B 的离线结果只属于 `{SCREEN_NAME}`；如果产生候选，也只能称为 **Kaggle test candidate**。新的 Kaggle Public Score 才可能提供 hidden-test 性能证据，当前值为 `{md_cell(number(model.public_score))}`。",
        "",
        "## 证据边界与历史不变量",
        "",
        f"V20A 为什么停止：其冻结状态仍为 `{V20A_STATUS}`，R70/R80/R90 均为 `NOT_RUN_HARD_GATE`。V20B 是新合同，不是对 V20A 的历史回填。V20B 允许两个 embryo 层的配对敏感性筛选，是因为比较发生在同一批样本与同一 upstream cache 上，但这不会增加独立 embryo 数量。",
        "",
        f"199 个 structurally eligible labeled train samples 分属 44b6（71）与 6bba（128）。199 个 field of view 不等于 199 个独立 embryo；两个 embryo 内部样本也不能被当作相互独立的生物重复。本实验不是 CV、不是 3-fold/5-fold，不使用 sample-level 显著性宣称跨胚胎泛化。checkpoint 训练数据与 split 未闭合，故证据状态持续为 `{OVERLAP_STATUS}`。",
        "",
        "离线 official score 是固定 scorer 在训练侧带标签数据上的度量，不是 Kaggle Public Score。历史 0.939 只绑定 V19C Version 1 / ScriptVersionId 346969653 / submission 55978992；页面历史分数不得代填为 V20B 分数。",
        "",
        "## 平台对象与版本链",
        "",
        markdown_table(NOTEBOOK_HEADERS, notebook_rows(model)),
        "",
        "## Validation 终态与失败诊断",
        "",
        markdown_table(("字段", "权威观察或冻结诊断"), failure_detail_rows(model)),
        "",
        "失败诊断用于解释为什么 validation fail-closed，不把未运行的 payload、cache、R70/R80/R90 指标补写为 PASS。静态 `--validate-only` 通过只证明构建侧检查，不证明动态 patch chain 能在 Kaggle 固定 support source 上成功应用。冻结 `retry=0` 控制后续行为：根因已定位也不授权第二次 SaveKernel。",
        "",
        "## 平台写入与轮询精确计数",
        "",
        markdown_table(("操作", "物理调用计数"), count_rows(model)),
        "",
        "`notebook_run` 指 Kaggle Notebook 平台 run，与 validation 内部的 predictor logical runs、full/cache 比较不是同一个计数。ledger 采用 `PHYSICAL_API_CALL_COUNTED_AT_STARTED_BEFORE_INVOCATION`，错误也消耗对应物理调用预算；任何错误均不得 retry。",
        "",
        "## 两个 embryo 的独立结果",
        "",
        markdown_table(EMBRYO_HEADERS, embryo_metric_rows(model)),
        "",
        "表内 official score 是离线 scorer 结果。44b6 与 6bba 始终分开陈述，不能只以 199 样本 pooled 总和替代，因为 6bba 的 128 个样本会压过 44b6 的 71 个样本。",
        "",
        "## embryo-equal macro 与 pooled micro",
        "",
        markdown_table(MACRO_HEADERS, macro_micro_rows(model)),
        "",
        "embryo-equal macro 对 44b6 与 6bba 等权；pooled micro 汇总全部 sample。两者并列是为了揭示样本数不平衡，不代表两次独立复现，也不构成 CV。",
        "",
        "## 冻结晋升 gate 的实际结果",
        "",
        markdown_table(("candidate", "gate", "result"), candidate_gate_rows(model)),
        "",
        "### 预注册 gate 定义",
        "",
        markdown_table(("gate", "冻结解释"), FROZEN_GATE_ROWS),
        "",
        "promotion decision 必须可由指标机器重算。若只有一个 candidate 通过则选择；若两个都通过，依次按 maximin embryo delta、macro、micro、division Jaccard、较少新增 FP、较低 cap saturation、较短 runtime 判定；仍相同则 `NO_UNIQUE_WINNER_NO_SUBMISSION`。",
        "",
        "## 用户要求的 20 个问题逐项回答",
        "",
    ]
    for index, (question, answer) in enumerate(answers, 1):
        lines.extend([f"### Q{index}. {question}", "", answer, ""])

    lines.extend(
        [
            "## 必报 22 类指标覆盖说明",
            "",
            markdown_table(("序号", "指标", "报告层级"), METRIC_ROWS),
            "",
            "数值主表只展示决策所需摘要；逐 sample 的 paired delta 在附录 A，逐 embryo delta 在附录 B。原始完整 metric CSV、runtime receipts、cache SHA 与 final output SHA 保留为机器证据。本报告不复制 raw image、GT、模型权重或 submission.csv。",
            "",
            "## 附录 A：R80/R90 相对 R70 的逐 sample paired delta",
            "",
        ]
    )
    sample_rows = sample_delta_rows(model)
    if sample_rows:
        lines.extend([markdown_table(SAMPLE_DELTA_HEADERS, sample_rows), ""])
    else:
        lines.extend(
            [
                "`NOT_AVAILABLE_VALIDATION_BLOCKED`：验证在逐 sample paired delta 产物形成前 fail-closed，不能从部分日志推算或填补数值。",
                "",
            ]
        )
    lines.extend(
        [
            "## 附录 B：R80/R90 相对 R70 的逐 embryo paired delta",
            "",
            markdown_table(EMBRYO_DELTA_HEADERS, embryo_delta_rows(model)),
            "",
            "## 附录 C：报告输入的 SHA-256",
            "",
            markdown_table(
                ("repository-relative artifact", "SHA-256"),
                [[path, digest] for path, digest in model.input_hashes.items()],
            ),
            "",
            "这些 hash 证明本报告读取的本地证据字节；它们不单独证明 Kaggle 远端对象、Public Score 或 GitHub 交付。远端对象与 GitHub fixed-commit blob 必须由各自权威回读另行验证。",
            "",
            "## 终态解释与明确未声明事项",
            "",
            "- `EVIDENCE_ASSEMBLED_PENDING_INDEPENDENT_VERIFIER` 只表示报告构建器完成了严格输入检查与渲染，不是领域验证器结论。",
            "",
            "- 即使最终 VERIFY JSON 为 `COMPLETED_VERIFIED`，其含义也仅是冻结合同内的交付与证据链通过；不能改写为模型性能提升。",
            "",
            "- `CHECKPOINT_TRAINING_OVERLAP_UNKNOWN` 仍是未解决证据缺口；两个训练 embryo 的结果不证明 hidden test 提分。",
            "",
            "- Public Score 为 `null` 时必须原样保留，不能用 0、历史 0.939、离线 proxy 或预测值替代。",
            "",
            "- 若没有 submission，30 分钟监控为 `NOT_APPLICABLE_NO_SUBMISSION`；不得虚构已经监控。未来读分仍须用户明确通知。",
            "",
            "- 若有 submission，本报告只记录冻结 30 分钟窗口内的观察值；不会后台 sleep、创建 cron、等待约 10 小时、重提或另存 Version。",
            "",
        ]
    )
    if model.submitted:
        lines.extend([STOP_MESSAGE, ""])
    else:
        lines.extend(["监控不适用、未来读分仍须用户明确通知。", ""])
    return "\n".join(lines)


def render_html(model: ReportModel) -> str:
    answers = question_answers(model)
    samples = sample_delta_rows(model)
    answer_html = "".join(
        "<li><h3>Q{}．{}</h3><p>{}</p></li>".format(
            index,
            html.escape(question),
            html.escape(answer),
        )
        for index, (question, answer) in enumerate(answers, 1)
    )
    sample_html = (
        html_table(SAMPLE_DELTA_HEADERS, samples)
        if samples
        else '<p class="na">NOT_AVAILABLE_VALIDATION_BLOCKED：没有可安全报告的逐 sample delta。</p>'
    )
    stop = STOP_MESSAGE if model.submitted else "监控不适用、未来读分仍须用户明确通知。"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Biohub V20B 两胚胎配对 safe-div parent radius 报告</title>
  <style>
    :root {{ color-scheme: light; --ink:#172235; --muted:#5d6b82; --line:#d9e0ea; --paper:#fff; --accent:#0b6e75; --soft:#eef7f7; --warn:#8a4b08; }}
    * {{ box-sizing:border-box; }} body {{ margin:0; background:#f3f6fa; color:var(--ink); font:15px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
    main {{ width:min(1500px,96vw); margin:28px auto; background:var(--paper); padding:clamp(22px,4vw,58px); box-shadow:0 12px 40px #17223518; border-radius:18px; }}
    h1 {{ line-height:1.15; font-size:clamp(28px,4vw,48px); margin:0 0 12px; }} h2 {{ margin-top:44px; padding-top:12px; border-top:2px solid var(--line); }} h3 {{ margin-bottom:6px; }}
    .lead {{ font-size:18px; color:var(--muted); max-width:1000px; }} .boundary {{ border-left:5px solid var(--accent); background:var(--soft); padding:16px 20px; border-radius:8px; }}
    .status {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:12px; margin:22px 0; }} .card {{ border:1px solid var(--line); border-radius:12px; padding:14px; }} .card small {{ color:var(--muted); display:block; }} .card strong {{ overflow-wrap:anywhere; }}
    .table-wrap {{ overflow:auto; margin:14px 0 24px; border:1px solid var(--line); border-radius:10px; }} table {{ border-collapse:collapse; width:100%; min-width:720px; }} th,td {{ padding:8px 10px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; white-space:nowrap; }} th {{ position:sticky; top:0; background:#edf3f7; z-index:1; }} tr:nth-child(even) td {{ background:#fafcfe; }}
    ol.qa {{ padding-left:24px; }} ol.qa li {{ margin:18px 0; padding:4px 16px 12px; border-left:3px solid var(--line); }} .na {{ color:var(--warn); font-weight:650; }} code {{ background:#eef1f5; padding:2px 5px; border-radius:4px; }} footer {{ margin-top:42px; color:var(--muted); border-top:1px solid var(--line); padding-top:18px; }}
    @media print {{ body {{ background:#fff; }} main {{ width:100%; margin:0; padding:18px; box-shadow:none; }} th {{ position:static; }} details {{ display:block; }} }}
  </style>
</head>
<body><main>
  <h1>Biohub V20B 两胚胎配对 safe-div parent radius 实验报告 V01</h1>
  <p class="lead">{html.escape(SCREEN_NAME)}。本页是冻结证据的确定性 HTML 视图，不把离线 proxy、历史分数与新的 Kaggle Public Score 混为一谈。</p>
  <div class="boundary"><strong>结论边界：</strong>报告构建状态为 EVIDENCE_ASSEMBLED_PENDING_INDEPENDENT_VERIFIER。最终领域状态为 <code>{html.escape(model.domain_status)}</code>，promotion decision 为 <code>{html.escape(model.decision)}</code>。独立 verifier 尚须检查报告、秘密扫描与全部证据后，才可给出合同范围内的交付状态；交付 COMPLETED_VERIFIED 不等于性能提升。</div>
  <div class="status">
    <div class="card"><small>最终领域状态</small><strong>{html.escape(model.domain_status)}</strong></div>
    <div class="card"><small>selected arm / radius</small><strong>{html.escape(display(model.selected_arm))} / {html.escape(number(model.selected_radius_um))}</strong></div>
    <div class="card"><small>submission ID</small><strong>{html.escape(display(model.submission_id))}</strong></div>
    <div class="card"><small>Public Score</small><strong>{html.escape(number(model.public_score))}</strong></div>
  </div>

  <h2>状态总览</h2>{html_table(("字段", "观察值"), overview_rows(model))}
  <h2>证据边界</h2>
  <p>V20A 保持 {html.escape(V20A_STATUS)}，R70/R80/R90 均保持 NOT_RUN_HARD_GATE。V20B 是新的两胚胎配对敏感性合同，不回填 V20A。199 个 field of view 只属于 44b6（71）和 6bba（128）两个 embryo 层，不能称为 CV 或 199 个独立生物重复。</p>
  <p>checkpoint 训练数据与 split 未闭合，因此状态持续为 <code>{html.escape(OVERLAP_STATUS)}</code>。离线 official score 不是 Kaggle Public Score；历史 0.939 只绑定 V19C baseline。</p>
  <h2>Notebook、submission 与分数链</h2>{html_table(NOTEBOOK_HEADERS, notebook_rows(model))}
  <h2>Validation 终态与失败诊断</h2>{html_table(("字段", "权威观察或冻结诊断"), failure_detail_rows(model))}
  <p>诊断解释 fail-closed 原因，但不把未运行 payload、cache 或 R70/R80/R90 metrics 写成 PASS。retry=0 不授权修复后重跑。</p>
  <h2>平台写入与轮询计数</h2>{html_table(("操作", "物理调用计数"), count_rows(model))}
  <p>notebook_run 是 Kaggle 平台 run，不等于 validation 内部 predictor logical runs。retry 必须为 0，Dataset/Model write 必须为 0。</p>
  <h2>每个 embryo 的离线结果</h2>{html_table(EMBRYO_HEADERS, embryo_metric_rows(model))}
  <h2>embryo-equal macro 与 pooled micro</h2>{html_table(MACRO_HEADERS, macro_micro_rows(model))}
  <h2>candidate gates</h2>{html_table(("candidate", "gate", "result"), candidate_gate_rows(model))}
  <h3>预注册 gate 定义</h3>{html_table(("gate", "冻结解释"), FROZEN_GATE_ROWS)}
  <h2>20 个问题逐项回答</h2><ol class="qa">{answer_html}</ol>
  <h2>22 类指标覆盖</h2>{html_table(("序号", "指标", "报告层级"), METRIC_ROWS)}
  <h2>附录 A：逐 sample paired delta</h2>{sample_html}
  <h2>附录 B：逐 embryo paired delta</h2>{html_table(EMBRYO_DELTA_HEADERS, embryo_delta_rows(model))}
  <h2>附录 C：输入 SHA-256</h2>{html_table(("repository-relative artifact", "SHA-256"), [[path, digest] for path, digest in model.input_hashes.items()])}
  <h2>明确未声明事项</h2>
  <p>本报告不声称两个训练 embryo 能证明 hidden-test 提分；不把 delivery COMPLETED_VERIFIED 写成性能提升；不把 Public Score null 改写为 0、0.939 或预测分数；不把文件存在等同于远端对象或 GitHub fixed-commit blob 回读。</p>
  <p class="boundary">{html.escape(stop)}</p>
  <footer>task_id={html.escape(TASK_ID)} · deterministic report · timestamp policy: omitted</footer>
</main></body></html>
"""


def validate_rendered(markdown: str, html_text: str, model: ReportModel) -> None:
    md_bytes = len(markdown.encode("utf-8"))
    html_bytes = len(html_text.encode("utf-8"))
    if md_bytes < 8000 or html_bytes < 10000:
        raise ReportError(
            f"rendered reports are below frozen byte minimum: md={md_bytes}, html={html_bytes}"
        )
    required_md = (
        TASK_ID,
        SCREEN_NAME,
        OVERLAP_STATUS,
        V20A_STATUS,
        "最终领域状态",
        "44b6",
        "6bba",
        "R70",
        "R80",
        "R90",
        "199",
        "cache",
        "paired",
        "embryo-equal macro",
        "pooled micro",
        "division TP",
        "division FP",
        "division FN",
        "topology",
        "node-count",
        "Notebook Version",
        "submission",
        "Public Score",
        "retry",
        model.decision,
        model.domain_status,
    )
    missing = [term for term in required_md if term not in markdown]
    if missing:
        raise ReportError(f"Markdown omits frozen terms: {missing}")
    for term in ("Biohub V20B", SCREEN_NAME, model.domain_status, model.decision):
        if term not in html_text:
            raise ReportError(f"HTML omits frozen term: {term}")
    if markdown.count("### Q") != 20:
        raise ReportError("Markdown does not contain exactly 20 numbered answers")
    if model.submitted:
        submission_id = str(model.submission_id)
        if submission_id not in markdown or submission_id not in html_text:
            raise ReportError("reports omit the created submission ID")
        if STOP_MESSAGE not in markdown:
            raise ReportError("Markdown omits the mandatory monitoring-stop statement")
    else:
        if "监控不适用、未来读分仍须用户明确通知。" not in markdown:
            raise ReportError("no-submission report omits the monitoring N/A statement")


def stage_atomic_file(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    )
    staged = Path(handle.name)
    try:
        with handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        staged.unlink(missing_ok=True)
        raise
    return staged


def write_reports(
    md_path: Path,
    html_path: Path,
    markdown: str,
    html_text: str,
    *,
    force: bool,
) -> None:
    if md_path.resolve() == html_path.resolve():
        raise ReportError("Markdown and HTML destinations must differ")
    for path, content in ((md_path, markdown), (html_path, html_text)):
        if path.exists() and path.read_text(encoding="utf-8") != content and not force:
            raise ReportError(
                f"refusing to overwrite differing report without --force: {path}"
            )
    staged_md = stage_atomic_file(md_path, markdown)
    staged_html: Path | None = None
    try:
        staged_html = stage_atomic_file(html_path, html_text)
        os.replace(staged_md, md_path)
        os.replace(staged_html, html_path)
    finally:
        staged_md.unlink(missing_ok=True)
        if staged_html is not None:
            staged_html.unlink(missing_ok=True)


def synthetic_model() -> ReportModel:
    counts = {key: 0 for key in COUNT_LIMITS}
    counts.update(
        {
            "validation_save_kernel": 1,
            "save_kernel_total": 1,
            "notebook_run": 1,
        }
    )
    per_embryo: list[dict[str, str]] = []
    micro_macro: list[dict[str, str]] = []
    for arm_index, arm in enumerate(ARMS):
        for embryo in EMBRYOS:
            per_embryo.append(
                {
                    "arm": arm,
                    "embryo_id": embryo,
                    "status": "RUN_COMPLETE",
                    "sample_count": str(EXPECTED_EMBRYO_COUNTS[embryo]),
                    "official_score": str(0.5 - arm_index * 0.01),
                    "division_jaccard": "0.25",
                    "division_tp": "10",
                    "division_fp": "2",
                    "division_fn": "3",
                    "node_count_penalty": "1.0",
                    "frame_cap_saturation_rate": "0",
                    "global_cap_saturation_rate": "0",
                    "topology_valid": "True",
                    "runtime_seconds": "100",
                }
            )
        for scope in ("EMBRYO_EQUAL_MACRO", "POOLED_MICRO"):
            micro_macro.append(
                {
                    "arm": arm,
                    "scope": scope,
                    "sample_count": "199",
                    "official_score": str(0.5 - arm_index * 0.01),
                    "adj_edge_jaccard": "0.5",
                    "division_jaccard": "0.25",
                    "node_count_penalty": "1.0",
                    "topology_valid": "True",
                    "schema_valid": "True",
                    "runtime_seconds": "200",
                }
            )
    paired_sample: list[dict[str, str]] = []
    for candidate in CANDIDATES:
        for index in range(199):
            embryo = "44b6" if index < 71 else "6bba"
            paired_sample.append(
                {
                    "candidate_arm": candidate,
                    "sample_id": f"{embryo}_fixture_{index:03d}",
                    "embryo_id": embryo,
                    "official_score_delta": "-0.01",
                    "adj_edge_jaccard_delta": "-0.01",
                    "division_jaccard_delta": "0",
                    "division_tp_delta": "0",
                    "division_fp_delta": "0",
                    "division_fn_delta": "0",
                    "node_count_penalty_delta": "0",
                    "frame_cap_saturation_delta": "0",
                    "global_cap_saturation_delta": "0",
                    "topology_both_valid": "True",
                    "schema_both_valid": "True",
                    "pre_division_cache_sha256_equal": "True",
                }
            )
    paired_embryo = [
        {
            "candidate_arm": candidate,
            "embryo_id": embryo,
            "sample_count": str(EXPECTED_EMBRYO_COUNTS[embryo]),
            "official_score_delta": "-0.01",
            "division_jaccard_delta": "0",
            "division_tp_delta": "0",
            "division_fp_delta": "0",
            "division_fn_delta": "0",
            "node_count_penalty_delta": "0",
            "frame_cap_saturation_rate_delta": "0",
            "global_cap_saturation_rate_delta": "0",
        }
        for candidate in CANDIDATES
        for embryo in EMBRYOS
    ]
    return ReportModel(
        contract={},
        boundary={},
        promotion={
            "cache_equivalence_pass": True,
            "candidate_gates": {
                candidate: {
                    "each_embryo_official_noninferior": False,
                    "eligible": False,
                }
                for candidate in CANDIDATES
            },
        },
        runtime={"baseline_reproduction": {"status": "PASS"}},
        ledger={},
        counts=counts,
        decision="NO_PROMOTION_KEEP_V19C_R70",
        offline_decision="NO_PROMOTION_KEEP_V19C_R70",
        domain_status="NO_PROMOTION_KEEP_V19C_R70",
        selected_arm=None,
        selected_radius_um=None,
        submitted=False,
        submission_id=None,
        public_score=None,
        monitor_status="NOT_APPLICABLE_NO_SUBMISSION",
        validation_version="<script>alert(1)</script>",
        validation_script_version_id=123,
        production_version=None,
        production_script_version_id=None,
        payload_rows=[{"status": "PASS"} for _ in range(199)],
        per_sample_rows=[
            {"arm": arm, "status": "RUN_COMPLETE"} for arm in ARMS for _ in range(199)
        ],
        per_embryo_rows=per_embryo,
        paired_sample_rows=paired_sample,
        paired_embryo_rows=paired_embryo,
        micro_macro_rows=micro_macro,
        input_hashes={"experiments/V20B/fixture.json": "a" * 64},
        blocked_stage=None,
        validation_terminal={},
        failure_diagnosis={},
    )


def self_test() -> None:
    model = synthetic_model()
    markdown = render_markdown(model)
    html_text = render_html(model)
    validate_rendered(markdown, html_text, model)
    if "<script>alert(1)</script>" in html_text:
        raise AssertionError("HTML renderer did not escape a dynamic value")
    if "&lt;script&gt;alert(1)&lt;/script&gt;" not in html_text:
        raise AssertionError("HTML escape self-test marker is absent")
    if "NOT_APPLICABLE_NO_PROMOTION" not in markdown:
        raise AssertionError("no-promotion production N/A state is absent")
    if "NOT_APPLICABLE_NO_SUBMISSION" not in markdown:
        raise AssertionError("no-submission monitoring N/A state is absent")
    if STOP_MESSAGE in markdown:
        raise AssertionError(
            "no-submission report fabricated the monitoring-stop claim"
        )
    no_unique = synthetic_model()
    no_unique.decision = "NO_UNIQUE_WINNER_NO_SUBMISSION"
    no_unique.offline_decision = "NO_UNIQUE_WINNER_NO_SUBMISSION"
    no_unique.domain_status = "NO_UNIQUE_WINNER_NO_SUBMISSION"
    no_unique_markdown = render_markdown(no_unique)
    no_unique_html = render_html(no_unique)
    validate_rendered(no_unique_markdown, no_unique_html, no_unique)
    if "NOT_APPLICABLE_NO_UNIQUE_OFFLINE_WINNER" not in no_unique_markdown:
        raise AssertionError("no-unique-winner production N/A state is absent")
    with tempfile.TemporaryDirectory(
        prefix="v20b-report-self-test-", dir="/private/tmp"
    ) as temp:
        root = Path(temp)
        invalid_json = root / "invalid.json"
        invalid_json.write_text('{"value": NaN}\n', encoding="utf-8")
        try:
            load_json(invalid_json)
        except ReportError:
            pass
        else:
            raise AssertionError("non-finite JSON did not fail closed")
        invalid_csv = root / "invalid.csv"
        invalid_csv.write_text("wrong,header\n1,2\n", encoding="utf-8")
        try:
            load_csv_exact(invalid_csv, ("expected", "header"))
        except ReportError:
            pass
        else:
            raise AssertionError("CSV header drift did not fail closed")
        md_path = root / "report.md"
        html_path = root / "report.html"
        write_reports(md_path, html_path, markdown, html_text, force=False)
        if sha256_file(md_path) != hashlib.sha256(markdown.encode()).hexdigest():
            raise AssertionError("atomic Markdown write changed bytes")
        if sha256_file(html_path) != hashlib.sha256(html_text.encode()).hexdigest():
            raise AssertionError("atomic HTML write changed bytes")
    print("V20B_FINAL_REPORT_BUILDER_SELF_TEST_PASS")


def resolve_output(root: Path, raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else root / path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--output-md", default=str(REPORT_MD))
    parser.add_argument("--output-html", default=str(REPORT_HTML))
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        self_test()
        return 0
    root = Path(args.project_root).resolve()
    model = load_and_validate(root)
    markdown = render_markdown(model)
    html_text = render_html(model)
    validate_rendered(markdown, html_text, model)
    md_path = resolve_output(root, args.output_md)
    html_path = resolve_output(root, args.output_html)
    if not args.check_only:
        write_reports(md_path, html_path, markdown, html_text, force=args.force)
    receipt = {
        "status": "REPORT_INPUTS_VALIDATED",
        "domain_status": model.domain_status,
        "promotion_decision": model.decision,
        "selected_arm": model.selected_arm,
        "submitted": model.submitted,
        "markdown_bytes": len(markdown.encode("utf-8")),
        "markdown_sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
        "html_bytes": len(html_text.encode("utf-8")),
        "html_sha256": hashlib.sha256(html_text.encode("utf-8")).hexdigest(),
        "written": not args.check_only,
        "timestamp_policy": "OMITTED_FOR_DETERMINISTIC_REPORT",
    }
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    print("V20B_FINAL_REPORT_BUILD_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
