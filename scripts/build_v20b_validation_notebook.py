#!/usr/bin/env python3
"""Build the private, validation-only V20B Kaggle notebook.

This builder is deliberately offline.  It verifies and embeds the fixed V19C
source, the frozen V20B contract/sample manifest, the pinned official scorer
sources, and the local resolved-config checker.  It never calls Kaggle or Git
remotes and it never executes inference.  Generated runtime code is fail-closed
and writes only under ``/kaggle/working/experiments/V20B``.
"""

from __future__ import annotations

import argparse
import ast
import base64
import copy
import hashlib
import json
import subprocess
import sys
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any


TASK_ID = "CODEX_20260904_BIOHUB_V20B_TWO_EMBRYO_PAIRED_RADIUS"
SOURCE_SHA256 = "92bf632410fedc9eb7e0984a20525590b5583d5abb002d8239ff65d9f51fbf57"
SCORER_COMMIT = "075fc5f5a52d11077f9dc2b074644618f26939e2"
SCORER_FILES = {
    "src/tracking_cellmot/metrics.py":
        "cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444",
    "src/tracking_cellmot/division_metrics.py":
        "0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9",
    "scripts/evaluate.py":
        "03ad4049530d3682c77435194e5d921981f331df3462abcde4a7156d1a57b7d3",
}
SOURCE_CELL_SHA256 = {
    2: "d9207bf4a2fad8b113e497af12ae2042f169bf1206c972e3d2c5cc2831a5a3e9",
    4: "6c5a6e880b6879cd6b26cc9e2394ce5492a797a863fead740e0aa25c5d22d643",
    5: "681232942fbb971dc1b999816b32c6d91da819e55d123b359b601169dd5982fb",
    6: "2c60405c2ad411a4eaebe59defaef6a79185c3119874905edee685c264335d8b",
    7: "a5da2a79ceb6383c66b543dd98280c83ccd3815f4becd26a4ab873ad74d82c8a",
}
ARMS = {"R70": 7.0, "R80": 8.0, "R90": 9.0}
EXPECTED_COUNTS = {"44b6": 71, "6bba": 128}

REQUIRED_OUTPUTS = [
    "full_sample_payload_inventory.csv",
    "full_sample_manifest.json",
    "canonical_resolved_config_R70.json",
    "canonical_resolved_config_R80.json",
    "canonical_resolved_config_R90.json",
    "active_config_R70.json",
    "active_config_R80.json",
    "active_config_R90.json",
    "safe_div_call_receipt_R70.json",
    "safe_div_call_receipt_R80.json",
    "safe_div_call_receipt_R90.json",
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
    "promotion_decision.json",
    "artifact_manifest.json",
]

CSV_SCHEMAS = {
    "full_sample_payload_inventory.csv": [
        "sample_id", "embryo_id", "image_path", "gt_path", "image_exists",
        "gt_exists", "image_readable", "gt_readable",
        "scorer_metadata_readable", "image_shape", "image_dtype",
        "gt_node_count", "gt_edge_count", "estimated_node_count",
        "estimated_node_count_evidence", "image_metadata_sha256",
        "image_tree_inventory_sha256", "gt_payload_sha256",
        "sample_payload_sha256", "status", "error",
    ],
    "per_sample_metrics.csv": [
        "arm", "sample_id", "embryo_id", "status", "official_score",
        "adj_edge_jaccard", "edge_jaccard", "division_jaccard",
        "edge_tp", "edge_fp", "edge_fn", "division_tp", "division_fp",
        "division_fn", "num_pred_nodes", "gt_node_count", "estimated_node_count",
        "gt_node_count_evidence", "estimated_node_count_evidence",
        "total_node_ratio", "node_count_penalty", "node_recall",
        "edges_fragmented", "edges_lost_to_detection", "wrong_association_edges",
        "safe_div_candidate_count", "accepted_division_count",
        "deepcenter_accepted_count", "deepcenter_rejected_count",
        "frame_cap_saturation", "global_cap_saturation", "topology_valid",
        "schema_valid", "runtime_seconds", "finalize_runtime_seconds",
        "scoring_runtime_seconds", "total_runtime_seconds",
        "execution_order_index", "score_coordinate_semantics", "peak_memory_bytes",
        "pre_division_cache_sha256", "final_output_sha256",
        "scorer_input_rows_sha256",
    ],
    "per_embryo_metrics.csv": [
        "arm", "embryo_id", "status", "sample_count", "official_score",
        "adj_edge_jaccard", "edge_jaccard", "division_jaccard",
        "edge_tp", "edge_fp", "edge_fn", "division_tp", "division_fp",
        "division_fn", "num_pred_nodes", "gt_node_count", "estimated_node_count",
        "total_node_ratio", "node_count_penalty", "node_recall",
        "edges_fragmented", "edges_lost_to_detection",
        "wrong_association_edges", "safe_div_candidate_count",
        "accepted_division_count", "deepcenter_accepted_count",
        "deepcenter_rejected_count", "frame_cap_saturation_rate",
        "global_cap_saturation_rate", "frame_cap_saturation",
        "global_cap_saturation", "topology_valid", "schema_valid",
        "runtime_seconds", "finalize_runtime_seconds",
        "scoring_runtime_seconds", "total_runtime_seconds", "peak_memory_bytes",
        "gt_node_count_evidence", "estimated_node_count_evidence",
        "pre_division_cache_sha256",
        "final_output_sha256", "scorer_input_rows_sha256", "hash_aggregation",
    ],
    "paired_deltas_by_sample.csv": [
        "candidate_arm", "control_arm", "sample_id", "embryo_id",
        "official_score_delta", "adj_edge_jaccard_delta",
        "edge_jaccard_delta", "division_jaccard_delta", "division_tp_delta",
        "division_fp_delta", "division_fn_delta", "edge_tp_delta",
        "edge_fp_delta", "edge_fn_delta", "num_pred_nodes_delta",
        "gt_node_count_delta", "estimated_node_count_delta",
        "total_node_ratio_delta", "node_count_penalty_delta", "node_recall_delta",
        "edges_fragmented_delta", "edges_lost_to_detection_delta",
        "wrong_association_edges_delta", "safe_div_candidate_count_delta",
        "accepted_division_count_delta", "deepcenter_accepted_count_delta",
        "deepcenter_rejected_count_delta",
        "frame_cap_saturation_delta", "global_cap_saturation_delta",
        "runtime_seconds_delta", "finalize_runtime_seconds_delta",
        "scoring_runtime_seconds_delta", "total_runtime_seconds_delta",
        "peak_memory_bytes_delta", "topology_both_valid", "schema_both_valid",
        "pre_division_cache_sha256_equal", "control_final_output_sha256",
        "candidate_final_output_sha256", "final_output_sha256_equal",
    ],
    "paired_deltas_by_embryo.csv": [
        "candidate_arm", "control_arm", "embryo_id", "sample_count",
        "official_score_delta", "adj_edge_jaccard_delta",
        "edge_jaccard_delta", "division_jaccard_delta", "division_tp_delta",
        "division_fp_delta", "division_fn_delta", "edge_tp_delta",
        "edge_fp_delta", "edge_fn_delta", "num_pred_nodes_delta",
        "gt_node_count_delta", "estimated_node_count_delta",
        "total_node_ratio_delta", "node_count_penalty_delta", "node_recall_delta",
        "edges_fragmented_delta", "edges_lost_to_detection_delta",
        "wrong_association_edges_delta", "safe_div_candidate_count_delta",
        "accepted_division_count_delta", "deepcenter_accepted_count_delta",
        "deepcenter_rejected_count_delta",
        "frame_cap_saturation_rate_delta",
        "global_cap_saturation_rate_delta", "runtime_seconds_delta",
        "finalize_runtime_seconds_delta", "scoring_runtime_seconds_delta",
        "total_runtime_seconds_delta", "peak_memory_bytes_delta",
        "topology_both_valid", "schema_both_valid",
        "pre_division_cache_sha256_equal", "control_final_output_sha256",
        "candidate_final_output_sha256", "final_output_sha256_equal",
    ],
    "micro_macro_comparison.csv": [
        "arm", "scope", "embryo_id", "status", "sample_count", "official_score",
        "adj_edge_jaccard", "edge_jaccard", "division_jaccard",
        "edge_tp", "edge_fp", "edge_fn", "division_tp", "division_fp",
        "division_fn", "node_count_penalty", "num_pred_nodes",
        "gt_node_count", "estimated_node_count", "gt_node_count_evidence",
        "estimated_node_count_evidence",
        "total_node_ratio", "node_recall", "edges_fragmented",
        "edges_lost_to_detection", "wrong_association_edges",
        "safe_div_candidate_count", "accepted_division_count",
        "deepcenter_accepted_count", "deepcenter_rejected_count",
        "frame_cap_saturation", "global_cap_saturation", "topology_valid",
        "schema_valid", "runtime_seconds", "finalize_runtime_seconds",
        "scoring_runtime_seconds", "total_runtime_seconds", "peak_memory_bytes",
        "pre_division_cache_sha256", "final_output_sha256", "hash_aggregation",
        "scorer_input_rows_sha256",
    ],
}


class BuildError(RuntimeError):
    """An input or generated-notebook invariant was not proven."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def pinned_dataset_sources(contract: dict[str, Any]) -> list[str]:
    """Return the exact version-pinned non-competition Dataset sources."""
    identities = contract["experiment_freeze"]["identities"]["input_datasets"]
    sources: list[str] = []
    for identity in identities:
        if identity.get("role") == "competition_data":
            continue
        version = identity.get("version")
        if isinstance(version, bool) or not isinstance(version, int) or version <= 0:
            raise BuildError(
                f"non-competition Dataset {identity.get('ref')!r} lacks a positive frozen version"
            )
        ref = identity.get("ref")
        if not isinstance(ref, str) or ref.count("/") != 1:
            raise BuildError(f"invalid frozen Dataset ref: {ref!r}")
        sources.append(f"{ref}/{version}")
    if len(sources) != 3 or len(sources) != len(set(sources)):
        raise BuildError("expected exactly three unique version-pinned Dataset sources")
    return sources


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise BuildError(f"{label} must be a JSON object")
    return value


def exact_replace(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise BuildError(f"{label}: expected one source match, found {count}")
    return source.replace(old, new, 1)


def code_cell(source: str, cell_id: str) -> dict[str, Any]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {"v20b_cell_id": cell_id},
        "outputs": [],
        "source": source.rstrip() + "\n",
    }


def wrap_runtime_cell(source: str, stage: str) -> str:
    """Wrap a post-bootstrap cell with deadline and fail-closed evidence hooks."""
    lines = source.splitlines()
    future_lines = [line for line in lines if line.startswith("from __future__ import ")]
    body_lines = [line for line in lines if not line.startswith("from __future__ import ")]
    body = "\n".join(body_lines).rstrip() or "pass"
    prefix = ("\n".join(future_lines) + "\n\n") if future_lines else ""
    return (
        prefix
        + "try:\n"
        + textwrap.indent(f"v20b_notebook_guard({stage + ':BEFORE'!r})\n" + body, "    ")
        + "\n"
        + textwrap.indent(f"v20b_notebook_guard({stage + ':AFTER'!r})", "    ")
        + "\nexcept BaseException as _v20b_cell_exc:\n"
        + textwrap.indent(f"v20b_emit_early_failure({stage!r}, _v20b_cell_exc)\nraise", "    ")
        + "\n"
    )


def markdown_cell(source: str, cell_id: str) -> dict[str, Any]:
    return {
        "cell_type": "markdown",
        "metadata": {"v20b_cell_id": cell_id},
        "source": source.rstrip() + "\n",
    }


def derive_cache_functions(source: str) -> str:
    """Mechanically split V19C exactly before add_safe_divisions_postlink."""

    tree = ast.parse(source)
    original = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "filter_output_graph"
        ),
        None,
    )
    if original is None:
        raise BuildError("V19C filter_output_graph function not found")
    split_indexes = []
    for index, statement in enumerate(original.body):
        if (
            isinstance(statement, ast.Assign)
            and isinstance(statement.value, ast.Call)
            and isinstance(statement.value.func, ast.Name)
            and statement.value.func.id == "add_safe_divisions_postlink"
        ):
            split_indexes.append(index)
    if len(split_indexes) != 1:
        raise BuildError(
            "expected one safe-division call in filter_output_graph, found "
            + str(len(split_indexes))
        )
    split_at = split_indexes[0]

    pre_skeleton = ast.parse(
        "def v20b_prepare_predivision_state(nodes_by_id, raw_edges, dataset=None, "
        "deepcenter_bundle=None):\n    pass\n"
    ).body[0]
    assert isinstance(pre_skeleton, ast.FunctionDef)
    pre_skeleton.body = copy.deepcopy(original.body[:split_at])
    pre_skeleton.body.append(
        ast.Return(
            value=ast.Tuple(
                elts=[
                    ast.Name(id="nodes_by_id", ctx=ast.Load()),
                    ast.Name(id="edges", ctx=ast.Load()),
                    ast.Name(id="stats", ctx=ast.Load()),
                    ast.Name(id="repair_frame_cache", ctx=ast.Load()),
                    ast.Name(id="deepcenter_heatmap_cache", ctx=ast.Load()),
                ],
                ctx=ast.Load(),
            )
        )
    )

    post_skeleton = ast.parse(
        "def v20b_finalize_from_predivision(nodes_by_id, edges, stats, dataset=None, "
        "deepcenter_bundle=None, repair_frame_cache=None, "
        "deepcenter_heatmap_cache=None):\n    pass\n"
    ).body[0]
    assert isinstance(post_skeleton, ast.FunctionDef)
    post_skeleton.body = copy.deepcopy(original.body[split_at:])
    replaced_calls = 0
    for node in ast.walk(post_skeleton):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "add_safe_divisions_postlink"
        ):
            node.func.id = "v20b_add_safe_divisions_with_receipt"
            replaced_calls += 1
    if replaced_calls != 1:
        raise BuildError(
            "derived downstream wrapper did not isolate exactly one safe-division call"
        )
    module = ast.Module(body=[pre_skeleton, post_skeleton], type_ignores=[])
    ast.fix_missing_locations(module)
    derived = ast.unparse(module) + "\n"
    compile(derived, "<derived-v20b-cache-functions>", "exec")
    return derived


def validate_source(path: Path) -> tuple[dict[str, Any], dict[int, str]]:
    raw = path.read_bytes()
    actual = sha256_bytes(raw)
    if actual != SOURCE_SHA256:
        raise BuildError(f"V19C source SHA mismatch: expected {SOURCE_SHA256}, got {actual}")
    notebook = json.loads(raw)
    if notebook.get("nbformat") != 4 or not isinstance(notebook.get("cells"), list):
        raise BuildError("V19C source is not an nbformat-4 notebook")
    sources: dict[int, str] = {}
    for index, expected in SOURCE_CELL_SHA256.items():
        try:
            source = notebook["cells"][index]["source"]
        except (IndexError, KeyError, TypeError) as exc:
            raise BuildError(f"V19C cell {index} unavailable") from exc
        if not isinstance(source, str):
            raise BuildError(f"V19C cell {index} source must be a string")
        actual_cell = sha256_bytes(source.encode("utf-8"))
        if actual_cell != expected:
            raise BuildError(
                f"V19C cell {index} SHA mismatch: expected {expected}, got {actual_cell}"
            )
        sources[index] = source
    return notebook, sources


def v19c_historical_production_runtime(notebook: dict[str, Any]) -> dict[str, Any]:
    """Mechanically derive the fixed V19C production-cell wall clock."""

    start = notebook["cells"][2].get("metadata", {}).get("execution", {}).get(
        "iopub.status.busy"
    )
    end = notebook["cells"][8].get("metadata", {}).get("execution", {}).get(
        "iopub.status.idle"
    )
    expected_start = "2026-08-20T22:09:07.593979Z"
    expected_end = "2026-08-20T22:32:40.610683Z"
    if start != expected_start or end != expected_end:
        raise BuildError(
            "fixed V19C production execution timestamps differ from the audited source"
        )
    start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
    end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
    seconds = (end_dt - start_dt).total_seconds()
    if seconds != 1413.016704:
        raise BuildError(f"unexpected V19C production wall clock: {seconds}")
    return {
        "source_sha256": SOURCE_SHA256,
        "start_cell_index": 2,
        "end_cell_index": 8,
        "start_busy_utc": start,
        "end_idle_utc": end,
        "wall_clock_seconds": seconds,
        "scope": "HISTORICAL_V19C_PRODUCTION_CELLS_2_THROUGH_8",
        "interpretation": "measured historical runtime, not a guarantee for a new production run",
    }


def validate_contract_and_samples(
    contract: dict[str, Any], sample_manifest: dict[str, Any]
) -> None:
    if contract.get("task_id") != TASK_ID or sample_manifest.get("task_id") != TASK_ID:
        raise BuildError("contract/sample manifest task identity mismatch")
    frozen = contract.get("experiment_freeze")
    if not isinstance(frozen, dict):
        raise BuildError("contract lacks experiment_freeze")
    identities = frozen.get("identities")
    if not isinstance(identities, dict):
        raise BuildError("contract lacks frozen identities")
    if identities.get("base_source_sha256") != SOURCE_SHA256:
        raise BuildError("contract base source SHA is not the pinned V19C source")
    scorer = identities.get("scorer")
    if not isinstance(scorer, dict) or scorer.get("commit") != SCORER_COMMIT:
        raise BuildError("contract official scorer commit mismatch")
    scorer_key_by_path = {
        "src/tracking_cellmot/metrics.py": "metrics_sha256",
        "src/tracking_cellmot/division_metrics.py": "division_metrics_sha256",
        "scripts/evaluate.py": "evaluate_sha256",
    }
    for relative, expected in SCORER_FILES.items():
        if scorer.get(scorer_key_by_path[relative]) != expected:
            raise BuildError(f"contract scorer SHA mismatch for {relative}")
    arms = frozen.get("arms")
    if not isinstance(arms, dict) or set(arms) != set(ARMS):
        raise BuildError("contract must freeze exactly R70/R80/R90")
    for arm, radius in ARMS.items():
        if arms[arm].get("safe_div_parent_radius_um") != radius:
            raise BuildError(f"contract arm radius mismatch for {arm}")
    params = frozen.get("active_parameters")
    if not isinstance(params, dict) or params.get("safe_div_parent_radius_um") != "ARM_VALUE_ONLY":
        raise BuildError("contract does not freeze parent radius as ARM_VALUE_ONLY")

    samples = sample_manifest.get("samples")
    if not isinstance(samples, list) or len(samples) != 199:
        raise BuildError("sample manifest must contain exactly 199 rows")
    if sample_manifest.get("sample_count") != 199:
        raise BuildError("sample_count must be 199")
    if sample_manifest.get("embryo_count") != 2:
        raise BuildError("embryo_count must be 2")
    if sample_manifest.get("embryo_sample_counts") != EXPECTED_COUNTS:
        raise BuildError("embryo sample counts are not 44b6=71 and 6bba=128")
    if sha256_bytes(canonical_bytes(samples)) != sample_manifest.get(
        "sample_rows_canonical_sha256"
    ):
        raise BuildError("sample rows canonical SHA mismatch")
    sample_ids = [row.get("sample_id") for row in samples]
    if len(set(sample_ids)) != 199 or sample_ids != sorted(sample_ids):
        raise BuildError("sample IDs must be unique and canonically sorted")
    counts = {key: 0 for key in EXPECTED_COUNTS}
    for row in samples:
        embryo = row.get("embryo_id")
        sample = row.get("sample_id")
        if embryo not in counts or not isinstance(sample, str) or not sample.startswith(embryo + "_"):
            raise BuildError(f"invalid sample/embryo row: {sample!r}/{embryo!r}")
        counts[embryo] += 1
        if row.get("include_in_all_arms") is not True:
            raise BuildError(f"sample not frozen into all arms: {sample}")
    if counts != EXPECTED_COUNTS:
        raise BuildError(f"computed embryo counts differ: {counts}")
    anchors = sample_manifest.get("anchors", {}).get("sample_ids")
    if not isinstance(anchors, list) or len(anchors) != 2:
        raise BuildError("sample manifest must freeze exactly two anchors")
    anchor_rows = [row for row in samples if row.get("sample_id") in anchors]
    if {row.get("embryo_id") for row in anchor_rows} != set(EXPECTED_COUNTS):
        raise BuildError("anchors must include one sample from each embryo")
    if any(row.get("visible_test_copy") is not False for row in anchor_rows):
        raise BuildError("anchors must be non-test-copy samples")


def read_scorer_sources(root: Path) -> dict[str, str]:
    try:
        commit = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise BuildError(f"cannot resolve scorer clone HEAD: {exc}") from exc
    if commit != SCORER_COMMIT:
        raise BuildError(f"scorer clone HEAD mismatch: expected {SCORER_COMMIT}, got {commit}")
    result: dict[str, str] = {}
    for relative, expected in SCORER_FILES.items():
        path = root / relative
        actual = sha256_file(path)
        if actual != expected:
            raise BuildError(
                f"official scorer source mismatch for {relative}: expected {expected}, got {actual}"
            )
        result[relative] = path.read_text(encoding="utf-8")
    return result


RUNTIME_BOOTSTRAP = r'''
from __future__ import annotations

import time as _v20b_bootstrap_time
V20B_NOTEBOOK_STARTED_MONOTONIC = _v20b_bootstrap_time.monotonic()

import copy
import csv
import hashlib
import json
import math
import os
import platform
import resource
import shutil
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

TASK_ID = "CODEX_20260904_BIOHUB_V20B_TWO_EMBRYO_PAIRED_RADIUS"
ARMS = {"R70": 7.0, "R80": 8.0, "R90": 9.0}
FROZEN_CONTRACT = json.loads(__V20B_CONTRACT_JSON__)
FROZEN_SAMPLE_MANIFEST = json.loads(__V20B_SAMPLE_JSON__)
EMBEDDED_SCORER_B64 = json.loads(__V20B_SCORER_JSON__)
EMBEDDED_CHECKER_B64 = __V20B_CHECKER_B64__
BUILDER_MANIFEST = json.loads(__V20B_BUILDER_MANIFEST_JSON__)

V20B_VALIDATION_LIMIT_SECONDS = float(
    FROZEN_CONTRACT["experiment_freeze"]["runtime_budget"]["validation_wall_clock_seconds_max"]
)
V20B_RECEIPT_RESERVE_SECONDS = 300.0
V20B_VALIDATION_HARD_STOP_SECONDS = (
    V20B_VALIDATION_LIMIT_SECONDS - V20B_RECEIPT_RESERVE_SECONDS
)
if V20B_VALIDATION_HARD_STOP_SECONDS <= 0:
    raise RuntimeError("invalid validation runtime budget/reserve")
V20B_VALIDATION_DEADLINE_MONOTONIC = (
    V20B_NOTEBOOK_STARTED_MONOTONIC + V20B_VALIDATION_HARD_STOP_SECONDS
)
V20B_PREDICTOR_RUNS_STARTED = 0
V20B_PREDICTOR_RUN_START_EVENTS = []
V20B_CELL_STAGE_ROWS = []

WORKING_ROOT = Path("/kaggle/working")
OUTPUT_ROOT = WORKING_ROOT / "experiments" / "V20B"
CACHE_ROOT = WORKING_ROOT / "v20b_private_predivision_cache"
SCORER_ROOT = WORKING_ROOT / "v20b_official_scorer_075fc5f"
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
CACHE_ROOT.mkdir(parents=True, exist_ok=True)

def canonical_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")

def canonical_sha256(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()

def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False).encode("utf-8") + b"\n")

def write_csv(path, rows, columns):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in columns})

def v20b_notebook_guard(checkpoint):
    elapsed = time.monotonic() - V20B_NOTEBOOK_STARTED_MONOTONIC
    V20B_CELL_STAGE_ROWS.append({
        "checkpoint": checkpoint,
        "elapsed_seconds_from_bootstrap": elapsed,
    })
    if time.monotonic() >= V20B_VALIDATION_DEADLINE_MONOTONIC:
        raise TimeoutError(
            f"VALIDATION_WALL_CLOCK_GUARD_EXCEEDED:{checkpoint}:"
            f"elapsed={elapsed:.3f}:hard_stop={V20B_VALIDATION_HARD_STOP_SECONDS:.3f}"
        )

def v20b_emit_early_failure(stage, exc):
    """Best-effort terminal evidence for failures after bootstrap initialization."""
    elapsed = time.monotonic() - V20B_NOTEBOOK_STARTED_MONOTONIC
    decision = (
        "BLOCKED_CONFIG_IDENTITY"
        if stage in {"RUNTIME_CONFIG", "DEPENDENCIES_AND_IDENTITIES", "CONFIG_RECEIPTS"}
        else "BLOCKED_VALIDATION_PAYLOAD_OR_RUNTIME"
    )
    try:
        write_json(OUTPUT_ROOT / "promotion_decision.json", {
            "schema_version": "1.0", "task_id": TASK_ID,
            "status": "FAIL_CLOSED", "decision": decision,
            "selected_arm": None, "selected_radius_um": None,
            "failed_stage": stage, "error_type": type(exc).__name__,
            "error": str(exc), "retry_count": 0,
            "competition_submission_count": 0,
        })
        write_json(OUTPUT_ROOT / "runtime_receipts.json", {
            "schema_version": "1.0", "task_id": TASK_ID,
            "status": "FAIL_CLOSED", "all_pass": False,
            "failed_stage": stage, "error_type": type(exc).__name__,
            "error": str(exc),
            "notebook_wall_clock_started_at": "BOOTSTRAP_FIRST_CODE_CELL",
            "validation_wall_clock_seconds": elapsed,
            "validation_wall_clock_budget_seconds": V20B_VALIDATION_LIMIT_SECONDS,
            "wall_clock_guard": {
                "deadline_origin": "BOOTSTRAP_FIRST_CODE_CELL",
                "hard_stop_seconds": V20B_VALIDATION_HARD_STOP_SECONDS,
                "receipt_reserve_seconds": V20B_RECEIPT_RESERVE_SECONDS,
                "deadline_monotonic_shared_across_cells": True,
            },
            "predictor_runs_started": V20B_PREDICTOR_RUNS_STARTED,
            "predictor_run_count_semantics": "LOGICAL_RUN_COUNT_INCREMENTED_BEFORE_FIRST_SUBPROCESS_START",
            "predictor_run_start_events": V20B_PREDICTOR_RUN_START_EVENTS,
            "cell_stage_rows": V20B_CELL_STAGE_ROWS,
            "retry_count": 0,
        })
        artifacts = []
        for path in sorted(
            p for p in OUTPUT_ROOT.rglob("*")
            if p.is_file() and p.name != "artifact_manifest.json"
        ):
            artifacts.append({
                "path": path.relative_to(OUTPUT_ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            })
        write_json(OUTPUT_ROOT / "artifact_manifest.json", {
            "schema_version": "1.0", "task_id": TASK_ID,
            "status": "PARTIAL_FAIL_CLOSED",
            "validation_script_version_id": os.environ.get("KAGGLE_SCRIPT_VERSION_ID") or None,
            "identity_declaration_scope": "FROZEN_EXPECTED_IDENTITIES_NOT_RUNTIME_VERIFICATION",
            "artifacts": artifacts, "artifact_count": len(artifacts),
        })
    except Exception as receipt_exc:
        print("V20B_EARLY_FAILURE_RECEIPT_WRITE_FAILED", type(receipt_exc).__name__, str(receipt_exc))

class PeakMemorySampler:
    def __init__(self, interval_seconds=2.0):
        self.stop_event = threading.Event()
        self.interval_seconds = float(interval_seconds)
        self.peak_gpu_mib = 0.0
        self.peak_process_rss_mib = 0.0
        self.thread = None

    @staticmethod
    def _process_rss_mib():
        status_path = Path("/proc/self/status")
        if status_path.is_file():
            for line in status_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("VmRSS:"):
                    return float(line.split()[1]) / 1024.0
        # ru_maxrss is only a cumulative fallback; Linux /proc is expected on
        # Kaggle and provides the sample-scoped current RSS used below.
        return float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) / 1024.0

    def _loop(self):
        while not self.stop_event.wait(self.interval_seconds):
            try:
                self.peak_process_rss_mib = max(
                    self.peak_process_rss_mib, self._process_rss_mib()
                )
            except Exception:
                pass
            self._update_gpu()

    def _update_gpu(self):
        try:
            output = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                check=True, capture_output=True, text=True, timeout=10,
            ).stdout
            values = [float(line.strip()) for line in output.splitlines() if line.strip()]
            if values:
                self.peak_gpu_mib = max(self.peak_gpu_mib, sum(values))
        except Exception:
            pass

    def __enter__(self):
        try:
            self.peak_process_rss_mib = self._process_rss_mib()
        except Exception:
            pass
        self._update_gpu()
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *_):
        try:
            self.peak_process_rss_mib = max(
                self.peak_process_rss_mib, self._process_rss_mib()
            )
        except Exception:
            pass
        self._update_gpu()
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)

print("V20B validation-only bootstrap; no test inference and no competition submission")
'''


RUNTIME_SCORER_AND_HELPERS = r'''
# Materialize and re-hash only the three frozen official scorer sources.
for relative, encoded in EMBEDDED_SCORER_B64.items():
    destination = SCORER_ROOT / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(base64.b64decode(encoded))
(SCORER_ROOT / "src" / "tracking_cellmot" / "__init__.py").touch()
expected_scorer = {
    "src/tracking_cellmot/metrics.py": "cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444",
    "src/tracking_cellmot/division_metrics.py": "0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9",
    "scripts/evaluate.py": "03ad4049530d3682c77435194e5d921981f331df3462abcde4a7156d1a57b7d3",
}
actual_scorer = {relative: sha256_file(SCORER_ROOT / relative) for relative in expected_scorer}
if actual_scorer != expected_scorer:
    raise RuntimeError({"official_scorer_runtime_hash_mismatch": actual_scorer})
sys.path.insert(0, str(SCORER_ROOT / "src"))
from tracking_cellmot import metrics as official_metrics

def tree_inventory_sha256(root, full_content=False):
    root = Path(root)
    rows = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        row = {"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size}
        if full_content:
            row["sha256"] = sha256_file(path)
        rows.append(row)
    if not rows:
        raise RuntimeError(f"empty directory payload: {root}")
    return canonical_sha256(rows)

def metadata_sha256(root):
    names = {"zarr.json", ".zattrs", ".zgroup", ".zarray"}
    rows = []
    for path in sorted(p for p in Path(root).rglob("*") if p.is_file() and p.name in names):
        rows.append({"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)})
    if not rows:
        raise RuntimeError(f"no readable Zarr metadata files: {root}")
    return canonical_sha256(rows)

def read_estimated_node_count(geff_path):
    from geff import GeffMetadata
    metadata = GeffMetadata.read(geff_path)
    value = (metadata.extra or {}).get("estimated_number_of_nodes")
    if value is None or not math.isfinite(float(value)) or float(value) <= 0:
        raise RuntimeError(f"missing/invalid estimated_number_of_nodes: {geff_path}")
    return float(value)

def read_scale(image_path):
    import zarr
    group = zarr.open_group(image_path, mode="r")
    attrs = dict(group.attrs)
    if "multiscales" in attrs:
        transform = attrs["multiscales"][0]["datasets"][0]["coordinateTransformations"][0]
        if transform["type"] != "scale":
            raise RuntimeError(f"unexpected transform type: {transform}")
        return tuple(float(value) for value in transform["scale"][-3:])
    return (1.625, 0.40625, 0.40625)

def raw_graph_payload(path):
    graph = graph_from_geff(path)
    nodes = {}
    for row in graph.node_attrs().iter_rows(named=True):
        node_id = int(row["node_id"])
        nodes[node_id] = {
            "node_id": node_id, "t": int(row["t"]),
            "z": float(row["z"]), "y": float(row["y"]), "x": float(row["x"]),
        }
    edges = []
    for row in graph.edge_attrs().iter_rows(named=True):
        probability = row.get("edge_prob") if hasattr(row, "get") else None
        edges.append({
            "source_id": int(row["source_id"]), "target_id": int(row["target_id"]),
            "edge_prob": None if probability is None else float(probability),
        })
    return nodes, edges

def canonical_graph_payload(nodes, edges):
    def plain(value):
        if value is None or isinstance(value, (str, bool, int, float)):
            return value
        if hasattr(value, "item"):
            return value.item()
        if isinstance(value, dict):
            return {str(key): plain(child) for key, child in sorted(value.items())}
        if isinstance(value, (list, tuple)):
            return [plain(child) for child in value]
        raise TypeError(f"non-canonical graph attribute type: {type(value).__name__}")
    node_rows = []
    for node_id, node in sorted(nodes.items()):
        row = {str(key): plain(value) for key, value in sorted(node.items())}
        row.update({"node_id": int(node_id), "t": int(node["t"]),
                    "z": float(node["z"]), "y": float(node["y"]), "x": float(node["x"])})
        node_rows.append(row)
    edge_rows = []
    for edge in edges:
        row = {str(key): plain(value) for key, value in sorted(edge.items())}
        row["source_id"] = int(edge["source_id"])
        row["target_id"] = int(edge["target_id"])
        if "edge_prob" in edge:
            row["edge_prob"] = None if edge.get("edge_prob") is None else float(edge["edge_prob"])
        if "distance_um" in edge:
            row["distance_um"] = None if edge.get("distance_um") is None else float(edge["distance_um"])
        edge_rows.append(row)
    edge_rows.sort(key=lambda row: (
        row["source_id"], row["target_id"], -1.0 if row.get("edge_prob") is None else row["edge_prob"],
        -1.0 if row.get("distance_um") is None else row["distance_um"],
    ))
    return {"nodes": node_rows, "edges": edge_rows}

def restore_graph_payload(payload):
    nodes = {int(row["node_id"]): copy.deepcopy(row) for row in payload["nodes"]}
    edges = [copy.deepcopy(row) for row in payload["edges"]]
    return nodes, edges

def graph_to_tracksdata(nodes, edges):
    import polars as pl
    graph = td.graph.InMemoryGraph()
    for key in ("z", "y", "x"):
        graph.add_node_attr_key(key, pl.Float64, -999999.0)
    ordered = [nodes[node_id] for node_id in sorted(nodes)]
    assigned = graph.bulk_add_nodes([
        {"t": int(row["t"]), "z": float(row["z"]), "y": float(row["y"]), "x": float(row["x"])}
        for row in ordered
    ])
    id_map = dict(zip([int(row["node_id"]) for row in ordered], assigned, strict=True))
    if edges:
        graph.bulk_add_edges([
            {"source_id": id_map[int(edge["source_id"])], "target_id": id_map[int(edge["target_id"])]}
            for edge in edges
        ])
    return graph

def validation_rows(sample_id, nodes, edges):
    rows = []
    row_id = 0
    for node_id in sorted(nodes):
        node = nodes[node_id]
        rows.append({"id": row_id, "dataset": sample_id, "row_type": "node",
                     "node_id": int(node_id), "t": int(node["t"]),
                     "z": max(0, int(round(float(node["z"])))),
                     "y": max(0, int(round(float(node["y"])))),
                     "x": max(0, int(round(float(node["x"])))),
                     "source_id": -1, "target_id": -1})
        row_id += 1
    for edge in sorted(edges, key=lambda item: (int(item["source_id"]), int(item["target_id"]))):
        rows.append({"id": row_id, "dataset": sample_id, "row_type": "edge",
                     "node_id": -1, "t": -1, "z": -1, "y": -1, "x": -1,
                     "source_id": int(edge["source_id"]), "target_id": int(edge["target_id"])})
        row_id += 1
    return rows

def topology_check(sample_id, nodes, edges, rows):
    errors = []
    node_ids = set(nodes)
    if not node_ids:
        errors.append("empty_nodes")
    pairs = set()
    indegree = {}
    outdegree = {}
    for edge in edges:
        source, target = int(edge["source_id"]), int(edge["target_id"])
        if source not in node_ids or target not in node_ids:
            errors.append("dangling_edge")
            continue
        if (source, target) in pairs:
            errors.append("duplicate_edge")
        pairs.add((source, target))
        if int(nodes[target]["t"]) != int(nodes[source]["t"]) + 1:
            errors.append("nonconsecutive_edge")
        indegree[target] = indegree.get(target, 0) + 1
        outdegree[source] = outdegree.get(source, 0) + 1
    if any(value > 1 for value in indegree.values()):
        errors.append("multi_parent")
    if any(value > 2 for value in outdegree.values()):
        errors.append("outdegree_gt_2")
    for node in nodes.values():
        if not all(math.isfinite(float(node[key])) for key in ("z", "y", "x")):
            errors.append("nonfinite_coordinate")
            break
    expected_columns = {"id", "dataset", "row_type", "node_id", "t", "z", "y", "x", "source_id", "target_id"}
    schema_valid = bool(rows) and all(set(row) == expected_columns and row["dataset"] == sample_id for row in rows)
    if not schema_valid:
        errors.append("validation_row_schema")
    return {"sample_id": sample_id, "topology_valid": not errors,
            "schema_valid": schema_valid, "errors": sorted(set(errors)),
            "node_count": len(nodes), "edge_count": len(edges)}

def diagnostic_error_counts(pred_graph, gt_graph):
    import polars as pl
    node_attrs = pred_graph.node_attrs(attr_keys=[td.DEFAULT_ATTR_KEYS.NODE_ID, td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID])
    matched_rows = node_attrs.filter(
        pl.col(td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID).is_not_null()
        & (pl.col(td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID) != -1)
    )
    pred_to_gt = dict(zip(
        matched_rows[td.DEFAULT_ATTR_KEYS.NODE_ID].to_list(),
        matched_rows[td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID].to_list(), strict=True,
    ))
    gt_to_pred = {gt: pred for pred, gt in pred_to_gt.items()}
    gt_edges = {(int(row["source_id"]), int(row["target_id"])) for row in gt_graph.edge_attrs().iter_rows(named=True)}
    pred_edges = [(int(row["source_id"]), int(row["target_id"])) for row in pred_graph.edge_attrs().iter_rows(named=True)]
    recovered = fragmented = lost = wrong = 0
    mapped_pairs = {(pred_to_gt[s], pred_to_gt[t]) for s, t in pred_edges if s in pred_to_gt and t in pred_to_gt}
    for source, target in gt_edges:
        if source not in gt_to_pred or target not in gt_to_pred:
            lost += 1
        elif (source, target) in mapped_pairs:
            recovered += 1
        else:
            fragmented += 1
    for source, target in pred_edges:
        if source in pred_to_gt and target in pred_to_gt and (pred_to_gt[source], pred_to_gt[target]) not in gt_edges:
            wrong += 1
    return {"recovered_edges": recovered, "edges_fragmented": fragmented,
            "edges_lost_to_detection": lost, "wrong_association_edges": wrong,
            "missed_gt_nodes": gt_graph.num_nodes() - len(gt_to_pred),
            "spurious_pred_nodes": pred_graph.num_nodes() - len(pred_to_gt)}

def semantic_graph_from_validation_rows(sample_id, rows):
    node_rows = [row for row in rows if row.get("row_type") == "node"]
    edge_rows = [row for row in rows if row.get("row_type") == "edge"]
    nodes = {}
    for row in node_rows:
        if row.get("dataset") != sample_id:
            raise RuntimeError(f"submission-semantic dataset mismatch: {sample_id}")
        node_id = int(row["node_id"])
        if node_id in nodes:
            raise RuntimeError(f"duplicate submission-semantic node: {sample_id}/{node_id}")
        nodes[node_id] = {
            "node_id": node_id, "t": int(row["t"]),
            # validation_rows has already applied the exact round+clamp rule.
            "z": float(row["z"]), "y": float(row["y"]), "x": float(row["x"]),
        }
    edges = []
    for row in edge_rows:
        if row.get("dataset") != sample_id:
            raise RuntimeError(f"submission-semantic dataset mismatch: {sample_id}")
        source, target = int(row["source_id"]), int(row["target_id"])
        if source not in nodes or target not in nodes:
            raise RuntimeError(f"submission-semantic dangling edge: {sample_id}/{source}->{target}")
        edges.append({"source_id": source, "target_id": target})
    return nodes, edges

def official_score(sample_id, output_rows, estimated_node_count):
    nodes, edges = semantic_graph_from_validation_rows(sample_id, output_rows)
    pred = graph_to_tracksdata(nodes, edges)
    gt = graph_from_geff(TRAIN_DIR / f"{sample_id}.geff")
    scale = read_scale(TRAIN_DIR / f"{sample_id}.zarr")
    result = official_metrics.evaluate(pred, gt, scale=scale, max_distance=7.0)
    score_graph_was_matched = pred.num_edges() > 0 and pred.num_nodes() > 0
    recall = official_metrics.node_recall(pred, gt) if score_graph_was_matched else 0.0
    metrics = official_metrics.per_sample_metrics(result, estimated_node_count, recall)
    summary = official_metrics.summarise([metrics])
    if score_graph_was_matched:
        diagnostics = diagnostic_error_counts(pred, gt)
    else:
        # The pinned official scorer deliberately returns before matching when
        # the prediction has no edges or no nodes.  Do not access an absent
        # MATCHED_NODE_ID column in that case.  These conservative diagnostics
        # mirror the same zero-match semantics used for node_recall above.
        diagnostics = {
            "recovered_edges": 0,
            "edges_fragmented": 0,
            "edges_lost_to_detection": int(gt.num_edges()),
            "wrong_association_edges": 0,
            "missed_gt_nodes": int(gt.num_nodes()),
            "spurious_pred_nodes": int(pred.num_nodes()),
        }
    division_denom = result.division_tp + result.division_fp + result.division_fn
    metrics.update({
        "official_score": float(summary["score"]),
        # The pinned official scorer defines division Jaccard as unavailable
        # when a single sample contains no GT or predicted division event.  It
        # still produces a valid per-sample total score by dropping that term.
        # Preserve the undefined value as JSON/CSV null instead of converting
        # it to zero or failing the full 199-sample run.
        "division_jaccard": (result.division_tp / division_denom if division_denom else None),
        "division_tp": result.division_tp, "division_fp": result.division_fp,
        "division_fn": result.division_fn,
        "node_count_penalty": float(metrics["edge_jaccard"] - metrics["adj_edge_jaccard"]),
    })
    metrics.update(diagnostics)
    metrics["score_coordinate_semantics"] = "ROUNDED_CLAMPED_SUBMISSION_ROWS"
    required_finite = (
        "official_score", "adj_edge_jaccard", "edge_jaccard",
        "total_node_ratio", "node_count_penalty",
        "node_recall",
    )
    nonfinite = [key for key in required_finite if not math.isfinite(float(metrics[key]))]
    if nonfinite:
        raise RuntimeError({"unscoreable_official_metrics": sample_id, "fields": nonfinite})
    return metrics

def cap_diagnostics(pre_nodes, pre_edges, final_edges, stats):
    source_counts = {}
    out = {}
    for edge in pre_edges:
        out.setdefault(int(edge["source_id"]), []).append(edge)
    for node_id, node in pre_nodes.items():
        if len(out.get(node_id, [])) == 1:
            source_counts[int(node["t"])] = source_counts.get(int(node["t"]), 0) + 1
    added_by_frame = {}
    for edge in final_edges:
        if int(edge.get("safe_division", 0)) == 1:
            frame = int(pre_nodes[int(edge["source_id"])]["t"])
            added_by_frame[frame] = added_by_frame.get(frame, 0) + 1
    saturated_frames = 0
    for frame, added in added_by_frame.items():
        cap = max(1, int(round(source_counts.get(frame, 0) * SAFE_DIV_FRAME_FRAC_CAP)))
        saturated_frames += int(added >= cap)
    global_cap = max(1, int(round(max(1, len(pre_edges)) * SAFE_DIV_GLOBAL_FRAC_CAP)))
    added_total = int(stats.get("safe_divisions_added", 0))
    return {
        "frame_cap_saturated": bool(saturated_frames),
        "frame_cap_saturated_frames": saturated_frames,
        "frame_cap_eligible_frames": len(source_counts),
        "global_cap_saturated": bool(added_total >= global_cap or stats.get("safe_division_skipped_cap", 0)),
        "global_cap": global_cap,
    }

def prediction_dir_for_method(method):
    matches = sorted((REPO_DIR / "predictions").glob(f"*/{method}/split_0"))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one prediction directory for {method}, found {matches}")
    return matches[0]

def visible_cuda_tokens(count):
    raw = os.environ.get("CUDA_VISIBLE_DEVICES", "").strip()
    if raw and raw != "-1":
        tokens = [token.strip() for token in raw.split(",") if token.strip()]
        if len(tokens) < count:
            raise RuntimeError(f"CUDA visibility mismatch: count={count}, value={raw!r}")
        return tokens[:count]
    return [str(index) for index in range(count)]

def run_predictor(stems, method, diagnostic_arm, deadline_monotonic=None):
    global V20B_PREDICTOR_RUNS_STARTED, V20B_PREDICTOR_RUN_START_EVENTS
    if not stems:
        raise RuntimeError("refusing empty predictor run")
    split_path = REPO_DIR / f"v20b_{method}_splits.json"
    split_path.write_text(json.dumps([{"split": 0, "train": [], "test": list(stems)}], sort_keys=True))
    base = [sys.executable, "scripts/predict_unet_transformer.py", "--data-dir", str(TRAIN_DIR),
            "--splits", split_path.name, "--split", "0", "--weights", WEIGHTS_RELATIVE,
            "--unet-batch-size", str(UNET_BATCH_SIZE), "--det-threshold", str(DET_THRESHOLD),
            "--ilp-edge-weight", str(ILP_EDGE_WEIGHT), "--ilp-appearance-weight", str(ILP_APPEARANCE_WEIGHT),
            "--ilp-disappearance-weight", str(ILP_DISAPPEARANCE_WEIGHT),
            "--ilp-division-weight", str(ILP_DIVISION_WEIGHT)]
    if USE_ILP:
        base.append("--use-ilp")
    gpu_count = _torch.cuda.device_count()
    if gpu_count != 2:
        raise RuntimeError(f"V20B requires the frozen 2x-Tesla-T4 runtime; CUDA device count={gpu_count}")
    workers = min(2, len(stems))
    started = time.monotonic()
    if workers == 1:
        command = [*base, "--method", method]
        environment = {**os.environ, "PYTHONPATH": "src", "BIOHUB_DIAGNOSTIC_ARM": diagnostic_arm,
                       "BIOHUB_GPU_SHARD": "0/1"}
        timeout = None
        if deadline_monotonic is not None:
            timeout = max(1.0, deadline_monotonic - time.monotonic())
        V20B_PREDICTOR_RUNS_STARTED += 1
        V20B_PREDICTOR_RUN_START_EVENTS.append({
            "run_name": method, "started_index": V20B_PREDICTOR_RUNS_STARTED,
            "sample_count": len(stems), "worker_count": workers,
            "elapsed_seconds_from_bootstrap": time.monotonic() - V20B_NOTEBOOK_STARTED_MONOTONIC,
        })
        subprocess.run(command, cwd=REPO_DIR, env=environment, check=True, timeout=timeout)
        final_dir = prediction_dir_for_method(method)
    else:
        tokens = visible_cuda_tokens(workers)
        processes = {}
        commands = {}
        for shard in range(workers):
            shard_method = f"{method}_gpu{shard}"
            command = [*base, "--method", shard_method, "--slice", f"{shard}::{workers}"]
            environment = {**os.environ, "PYTHONPATH": "src", "CUDA_VISIBLE_DEVICES": tokens[shard],
                           "BIOHUB_DIAGNOSTIC_ARM": diagnostic_arm,
                           "BIOHUB_GPU_SHARD": f"{shard}/{workers}"}
            commands[shard] = command
            if shard == 0:
                V20B_PREDICTOR_RUNS_STARTED += 1
                V20B_PREDICTOR_RUN_START_EVENTS.append({
                    "run_name": method, "started_index": V20B_PREDICTOR_RUNS_STARTED,
                    "sample_count": len(stems), "worker_count": workers,
                    "elapsed_seconds_from_bootstrap": time.monotonic() - V20B_NOTEBOOK_STARTED_MONOTONIC,
                })
            processes[shard] = subprocess.Popen(command, cwd=REPO_DIR, env=environment)
        failure = None
        while processes:
            if deadline_monotonic is not None and time.monotonic() >= deadline_monotonic:
                for process in processes.values():
                    if process.poll() is None:
                        process.terminate()
                for process in processes.values():
                    try:
                        process.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        process.kill(); process.wait()
                raise TimeoutError("VALIDATION_WALL_CLOCK_GUARD_EXCEEDED_DURING_PREDICTOR")
            for shard, process in list(processes.items()):
                code = process.poll()
                if code is None:
                    continue
                del processes[shard]
                if code != 0:
                    failure = (shard, code)
                    break
            if failure:
                for process in processes.values():
                    if process.poll() is None:
                        process.terminate()
                for process in processes.values():
                    try:
                        process.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        process.kill(); process.wait()
                raise subprocess.CalledProcessError(failure[1], commands[failure[0]])
            if processes:
                time.sleep(1)
        shard_dirs = [prediction_dir_for_method(f"{method}_gpu{shard}") for shard in range(workers)]
        found = set()
        for shard, directory in enumerate(shard_dirs):
            actual = {path.stem for path in directory.glob("*.geff")}
            expected = set(stems[shard::workers])
            if actual != expected or found & actual:
                raise RuntimeError({"shard": shard, "expected": sorted(expected), "actual": sorted(actual)})
            found |= actual
        if found != set(stems):
            raise RuntimeError("GPU shard union does not equal frozen stems")
        user_roots = {directory.parents[1] for directory in shard_dirs}
        if len(user_roots) != 1:
            raise RuntimeError("inconsistent predictor output roots")
        final_dir = next(iter(user_roots)) / method / "split_0"
        if final_dir.exists():
            raise RuntimeError(f"refusing to overwrite predictor output: {final_dir}")
        final_dir.mkdir(parents=True)
        for directory in shard_dirs:
            for source in sorted(directory.glob("*.geff")):
                shutil.move(str(source), str(final_dir / source.name))
            shutil.rmtree(directory.parent)
    paths = {path.stem: path for path in final_dir.glob("*.geff")}
    if set(paths) != set(stems):
        raise RuntimeError({"prediction_coverage_mismatch": sorted(set(stems) ^ set(paths))})
    return paths, time.monotonic() - started, workers
'''


RUNTIME_EXPERIMENT = r'''
PAYLOAD_COLUMNS = __V20B_PAYLOAD_COLUMNS__
SAMPLE_COLUMNS = __V20B_SAMPLE_COLUMNS__
EMBRYO_COLUMNS = __V20B_EMBRYO_COLUMNS__
SAMPLE_DELTA_COLUMNS = __V20B_SAMPLE_DELTA_COLUMNS__
EMBRYO_DELTA_COLUMNS = __V20B_EMBRYO_DELTA_COLUMNS__
MICRO_MACRO_COLUMNS = __V20B_MICRO_MACRO_COLUMNS__

runtime_stage = "PAYLOAD_PREFLIGHT"
experiment_started = V20B_NOTEBOOK_STARTED_MONOTONIC
validation_limit_seconds = V20B_VALIDATION_LIMIT_SECONDS
receipt_reserve_seconds = V20B_RECEIPT_RESERVE_SECONDS
validation_hard_stop_seconds = V20B_VALIDATION_HARD_STOP_SECONDS
validation_deadline_monotonic = V20B_VALIDATION_DEADLINE_MONOTONIC
payload_rows = []
payload_identity = {}
runtime_stages = list(V20B_CELL_STAGE_ROWS)
topology_rows = []
progress_eta_rows = []

def ensure_runtime_budget(checkpoint):
    elapsed = time.monotonic() - experiment_started
    if elapsed >= validation_hard_stop_seconds:
        raise TimeoutError(
            f"VALIDATION_WALL_CLOCK_GUARD_EXCEEDED:{checkpoint}:"
            f"elapsed={elapsed:.3f}:hard_stop={validation_hard_stop_seconds:.3f}"
        )

def record_progress_eta(stage, durations, completed, total):
    if completed < 5 or (completed % 10 != 0 and completed != total):
        return
    ordered = sorted(float(value) for value in durations)
    p90_index = max(0, math.ceil(0.90 * len(ordered)) - 1)
    p90_seconds = ordered[p90_index]
    remaining_items = total - completed
    remaining_seconds = p90_seconds * remaining_items
    elapsed = time.monotonic() - experiment_started
    projected_total = elapsed + remaining_seconds + receipt_reserve_seconds
    row = {
        "stage": stage, "completed": completed, "total": total,
        "observed_p90_seconds_per_item": p90_seconds,
        "remaining_items": remaining_items,
        "estimated_current_stage_remaining_seconds": remaining_seconds,
        "elapsed_seconds": elapsed,
        "receipt_reserve_seconds": receipt_reserve_seconds,
        "projected_total_seconds_current_stage_only": projected_total,
        "validation_limit_seconds": validation_limit_seconds,
        "estimate_scope": "CURRENT_STAGE_REMAINING_PLUS_RECEIPT_RESERVE",
    }
    progress_eta_rows.append(row)
    if projected_total > validation_limit_seconds:
        raise TimeoutError(
            f"VALIDATION_WALL_CLOCK_GUARD_PROJECTED_OVERRUN:{stage}:"
            f"projected={projected_total:.3f}:limit={validation_limit_seconds:.3f}"
        )

def emit_artifact_manifest(status):
    artifacts = []
    for path in sorted(p for p in OUTPUT_ROOT.rglob("*") if p.is_file() and p.name != "artifact_manifest.json"):
        artifacts.append({"path": path.relative_to(OUTPUT_ROOT).as_posix(),
                          "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    value = {"schema_version": "1.0", "task_id": TASK_ID, "status": status,
             "validation_script_version_id": os.environ.get("KAGGLE_SCRIPT_VERSION_ID") or None,
             "identities": FROZEN_CONTRACT["experiment_freeze"]["identities"],
             "identity_declaration_scope": "FROZEN_EXPECTED_IDENTITIES",
             "runtime_identity_evidence": globals().get(
                 "identity_evidence", {"status": "NOT_REACHED"}
             ),
             "artifacts": artifacts, "artifact_count": len(artifacts)}
    write_json(OUTPUT_ROOT / "artifact_manifest.json", value)
    return value

def emit_failure(exc):
    decision_by_stage = {
        "PAYLOAD_PREFLIGHT": "BLOCKED_VALIDATION_PAYLOAD_OR_RUNTIME",
        "CONFIG_IDENTITY": "BLOCKED_CONFIG_IDENTITY",
        "CONFIG_RECEIPTS": "BLOCKED_CONFIG_IDENTITY",
        "CACHE_EQUIVALENCE": "BLOCKED_CACHE_EQUIVALENCE",
        "DETERMINISM": "BLOCKED_RUNTIME_NONDETERMINISM",
    }
    decision = decision_by_stage.get(runtime_stage, "BLOCKED_VALIDATION_PAYLOAD_OR_RUNTIME")
    if isinstance(exc, (TimeoutError, subprocess.TimeoutExpired)) or "VALIDATION_WALL_CLOCK_GUARD" in str(exc):
        decision = "BLOCKED_VALIDATION_PAYLOAD_OR_RUNTIME"
    partial_write_errors = []
    try:
        if payload_rows and not (OUTPUT_ROOT / "full_sample_payload_inventory.csv").exists():
            write_csv(OUTPUT_ROOT / "full_sample_payload_inventory.csv", payload_rows, PAYLOAD_COLUMNS)
        if payload_rows and not (OUTPUT_ROOT / "full_sample_manifest.json").exists():
            passed_rows = [row for row in payload_rows if row.get("status") == "PASS"]
            write_json(OUTPUT_ROOT / "full_sample_manifest.json", {
                "schema_version": "1.0", "task_id": TASK_ID,
                "status": "PARTIAL_FAIL_CLOSED",
                "sample_count": len(passed_rows), "observed_row_count": len(payload_rows),
                "expected_sample_count": 199,
                "embryo_sample_counts": {
                    embryo: sum(row.get("status") == "PASS" and row.get("embryo_id") == embryo
                                for row in payload_rows)
                    for embryo in ("44b6", "6bba")
                },
                "rows_sha256": canonical_sha256(payload_rows),
                "source_frozen_manifest_sha256": BUILDER_MANIFEST["inputs"]["sample_manifest_file_sha256"],
                "partial_reason": f"{type(exc).__name__}: {exc}",
            })
    except Exception as partial_exc:
        partial_write_errors.append(f"payload:{type(partial_exc).__name__}:{partial_exc}")
    try:
        partial_metrics = globals().get("metrics_rows", [])
        if partial_metrics and not (OUTPUT_ROOT / "per_sample_metrics.csv").exists():
            write_csv(OUTPUT_ROOT / "per_sample_metrics.csv", partial_metrics, SAMPLE_COLUMNS)
    except Exception as partial_exc:
        partial_write_errors.append(f"metrics:{type(partial_exc).__name__}:{partial_exc}")
    try:
        if topology_rows and not (OUTPUT_ROOT / "topology_validation.json").exists():
            write_json(OUTPUT_ROOT / "topology_validation.json", {
                "schema_version": "1.0", "task_id": TASK_ID,
                "status": "PARTIAL_FAIL_CLOSED", "rows": topology_rows,
                "expected_checks": 199 * 3, "actual_checks": len(topology_rows),
                "all_pass": False,
            })
    except Exception as partial_exc:
        partial_write_errors.append(f"topology:{type(partial_exc).__name__}:{partial_exc}")
    write_json(OUTPUT_ROOT / "promotion_decision.json", {
        "schema_version": "1.0", "task_id": TASK_ID, "decision": decision,
        "selected_arm": None, "selected_radius_um": None, "status": "FAIL_CLOSED",
        "failed_stage": runtime_stage, "error_type": type(exc).__name__, "error": str(exc),
        "retry_count": 0, "competition_submission_count": 0,
    })
    write_json(OUTPUT_ROOT / "runtime_receipts.json", {
        "schema_version": "1.0", "task_id": TASK_ID, "status": "FAIL_CLOSED", "all_pass": False,
        "failed_stage": runtime_stage, "validation_wall_clock_seconds": time.monotonic() - experiment_started,
        "notebook_wall_clock_started_at": "BOOTSTRAP_FIRST_CODE_CELL",
        "validation_wall_clock_budget_seconds": validation_limit_seconds,
        "wall_clock_guard": {
            "deadline_origin": "BOOTSTRAP_FIRST_CODE_CELL",
            "hard_stop_seconds": validation_hard_stop_seconds,
            "receipt_reserve_seconds": receipt_reserve_seconds,
            "deadline_monotonic_shared_across_cells": True,
            "eta_estimates": progress_eta_rows,
        },
        "retry_count": 0, "predictor_runs_started": V20B_PREDICTOR_RUNS_STARTED,
        "predictor_run_count_semantics": "LOGICAL_RUN_COUNT_INCREMENTED_BEFORE_FIRST_SUBPROCESS_START",
        "predictor_run_start_events": V20B_PREDICTOR_RUN_START_EVENTS,
        "stages": runtime_stages, "cell_stage_rows": V20B_CELL_STAGE_ROWS,
        "partial_write_errors": partial_write_errors,
        "error_type": type(exc).__name__, "error": str(exc),
    })
    emit_artifact_manifest("PARTIAL_FAIL_CLOSED")

try:
    v20b_notebook_guard("VALIDATION_EXPERIMENT:BEFORE")
    # Full 199/199 physical payload preflight before any predictor execution.
    import zarr
    for frozen_row in FROZEN_SAMPLE_MANIFEST["samples"]:
        ensure_runtime_budget(f"payload_preflight_before:{frozen_row['sample_id']}")
        sample_id = frozen_row["sample_id"]
        embryo_id = frozen_row["embryo_id"]
        image_path = COMP_DIR / frozen_row["expected_image_path"]
        gt_path = COMP_DIR / frozen_row["expected_gt_path"]
        row = {"sample_id": sample_id, "embryo_id": embryo_id,
               "image_path": frozen_row["expected_image_path"],
               "gt_path": frozen_row["expected_gt_path"], "image_exists": image_path.exists(),
               "gt_exists": gt_path.exists(), "image_readable": False, "gt_readable": False,
               "scorer_metadata_readable": False, "status": "FAIL", "error": ""}
        try:
            if not image_path.is_dir() or not gt_path.is_dir():
                raise FileNotFoundError(f"missing image/GT payload for {sample_id}")
            group = zarr.open_group(image_path, mode="r")
            array = group["0"]
            shape = tuple(int(v) for v in array.shape)
            if len(shape) != 4 or any(v <= 0 for v in shape):
                raise RuntimeError(f"invalid image shape {shape}")
            probes = [array[(0,) * 4], array[tuple(v - 1 for v in shape)]]
            probe_sha = canonical_sha256({"shape": shape, "dtype": str(array.dtype),
                                          "probes": [str(value) for value in probes]})
            graph = graph_from_geff(gt_path)
            if graph.num_nodes() <= 0:
                raise RuntimeError("GT graph has no nodes")
            estimated = read_estimated_node_count(gt_path)
            image_metadata = metadata_sha256(image_path)
            image_inventory = tree_inventory_sha256(image_path, full_content=False)
            gt_sha = tree_inventory_sha256(gt_path, full_content=True)
            identity = {
                "image_metadata_sha256": image_metadata,
                "image_tree_inventory_sha256": image_inventory,
                "image_probe_sha256": probe_sha,
                "gt_payload_sha256": gt_sha,
                "sample_payload_sha256": canonical_sha256({
                    "sample_id": sample_id, "image_metadata_sha256": image_metadata,
                    "image_tree_inventory_sha256": image_inventory,
                    "image_probe_sha256": probe_sha, "gt_payload_sha256": gt_sha,
                    "estimated_number_of_nodes": estimated,
                }),
            }
            payload_identity[sample_id] = identity
            row.update({"image_readable": True, "gt_readable": True,
                        "scorer_metadata_readable": True, "image_shape": "x".join(map(str, shape)),
                        "image_dtype": str(array.dtype), "gt_node_count": graph.num_nodes(),
                        "gt_edge_count": graph.num_edges(), "estimated_node_count": estimated,
                        "estimated_node_count_evidence": "GEFF_METADATA_ESTIMATED_NUMBER_OF_NODES",
                        "image_metadata_sha256": image_metadata,
                        "image_tree_inventory_sha256": image_inventory,
                        "gt_payload_sha256": gt_sha,
                        "sample_payload_sha256": identity["sample_payload_sha256"],
                        "status": "PASS"})
        except Exception as sample_exc:
            row["error"] = f"{type(sample_exc).__name__}: {sample_exc}"
        payload_rows.append(row)
        ensure_runtime_budget(f"payload_preflight_after:{sample_id}")
    write_csv(OUTPUT_ROOT / "full_sample_payload_inventory.csv", payload_rows, PAYLOAD_COLUMNS)
    failed_payloads = [row for row in payload_rows if row["status"] != "PASS"]
    full_manifest = {
        "schema_version": "1.0", "task_id": TASK_ID,
        "status": "COMPLETE_199_OF_199" if not failed_payloads else "BLOCKED_PAYLOAD_FAILURE",
        "sample_count": len(payload_rows) - len(failed_payloads), "expected_sample_count": 199,
        "embryo_count": len({row["embryo_id"] for row in payload_rows if row["status"] == "PASS"}),
        "embryo_sample_counts": {embryo: sum(row["status"] == "PASS" and row["embryo_id"] == embryo for row in payload_rows)
                                  for embryo in ("44b6", "6bba")},
        "excluded_samples": [row["sample_id"] for row in failed_payloads],
        "arm_symmetric_exclusion": True,
        "inclusion_policy": {
            "mode": "STRICT_199_OF_199_FAIL_CLOSED",
            "contract_symmetric_exclusion_option_used": False,
            "reason": "V20B task explicitly requires preflight of every frozen train payload",
        },
        "rows_sha256": canonical_sha256(payload_rows),
        # Bind this receipt to the exact checked-in manifest bytes.
        "source_frozen_manifest_sha256": BUILDER_MANIFEST["inputs"]["sample_manifest_file_sha256"],
        "samples": [{"sample_id": row["sample_id"], "embryo_id": row["embryo_id"],
                     "status": row["status"], "input_identity": payload_identity.get(row["sample_id"]),
                     "error": row["error"]} for row in payload_rows],
    }
    write_json(OUTPUT_ROOT / "full_sample_manifest.json", full_manifest)
    if failed_payloads or full_manifest["embryo_sample_counts"] != {"44b6": 71, "6bba": 128}:
        raise RuntimeError(f"payload preflight failed for {len(failed_payloads)} samples")
    runtime_stages.append({"stage": "payload_preflight", "status": "PASS", "sample_count": 199})

    runtime_stage = "CONFIG_IDENTITY"
    frozen_params = FROZEN_CONTRACT["experiment_freeze"]["active_parameters"]
    frozen_identities = FROZEN_CONTRACT["experiment_freeze"]["identities"]
    measured_checkpoints = {
        "primary_sha256": _primary_actual_sha256,
        "secondary_sha256": _secondary_actual_sha256,
        "deepcenter_sha256": _deepcenter_actual_sha256,
    }
    expected_scorer_hashes = {
        "src/tracking_cellmot/metrics.py": frozen_identities["scorer"]["metrics_sha256"],
        "src/tracking_cellmot/division_metrics.py": frozen_identities["scorer"]["division_metrics_sha256"],
        "scripts/evaluate.py": frozen_identities["scorer"]["evaluate_sha256"],
    }
    payload_sha_rows = [
        {"sample_id": sample_id, "sha256": payload_identity[sample_id]["sample_payload_sha256"]}
        for sample_id in sorted(payload_identity)
    ]
    expected_pinned_dataset_sources = [
        f"{identity['ref']}/{int(identity['version'])}"
        for identity in frozen_identities["input_datasets"]
        if identity["role"] != "competition_data"
    ]
    embedded_pinned_dataset_sources = BUILDER_MANIFEST["inputs"].get(
        "kernel_dataset_sources_version_pinned"
    )
    import importlib.metadata as _v20b_importlib_metadata
    package_versions = {}
    for package_name in sorted(REQUIRED_MODULES):
        try:
            package_versions[package_name] = _v20b_importlib_metadata.version(package_name)
        except _v20b_importlib_metadata.PackageNotFoundError:
            package_versions[package_name] = "UNKNOWN_DISTRIBUTION_NAME_OR_NOT_INSTALLED"
    wheel_paths = sorted({
        path.resolve()
        for package_dir in find_offline_package_dirs(ARTIFACTS)
        for path in package_dir.glob("*.whl")
        if path.is_file()
    })
    dependency_wheel_rows = [
        {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}
        for path in wheel_paths
    ]
    identity_evidence = {
        "schema_version": "1.0",
        "base_source": {
            "status": "BUILD_TIME_VERIFIED_RUNTIME_SOURCE_OBJECT_NOT_MOUNTED",
            "expected_sha256": frozen_identities["base_source_sha256"],
            "builder_verified_input_sha256": BUILDER_MANIFEST["inputs"]["v19c_source_sha256"],
            "runtime_recomputed_sha256": None,
        },
        "support_code": {
            "status": "PASS" if _support_actual_manifest_sha256 == frozen_identities["support_code_manifest_sha256"] else "FAIL",
            "expected_manifest_sha256": frozen_identities["support_code_manifest_sha256"],
            "actual_manifest_sha256": _support_actual_manifest_sha256,
            "actual_file_sha256": _support_actual_sha256,
            "evidence_source": "MATERIALIZED_SUPPORT_REPO_PYTHON_FILE_BYTES",
        },
        "checkpoints": {
            "status": "PASS" if measured_checkpoints == frozen_identities["checkpoints"] else "FAIL",
            "expected": frozen_identities["checkpoints"], "actual": measured_checkpoints,
            "materialized_paths": {
                "primary": str(_primary_materialized_path),
                "secondary": str(SECONDARY_WEIGHTS_PATH),
                "deepcenter": str(_deepcenter_materialized_path),
            },
            "evidence_source": "MATERIALIZED_CHECKPOINT_FILE_BYTES",
        },
        "official_scorer": {
            "status": "PASS" if actual_scorer == expected_scorer_hashes else "FAIL",
            "expected_file_sha256": expected_scorer_hashes,
            "actual_file_sha256": actual_scorer,
            "commit_expected": frozen_identities["scorer"]["commit"],
            "runtime_commit_status": "UNKNOWN_EMBEDDED_FILES_HAVE_NO_GIT_OBJECT_DATABASE",
            "evidence_source": "RUNTIME_MATERIALIZED_EMBEDDED_SCORER_FILE_BYTES",
        },
        "competition_payload": {
            "status": "PASS" if len(payload_sha_rows) == 199 else "FAIL",
            "sample_count": len(payload_sha_rows),
            "embryo_sample_counts": full_manifest["embryo_sample_counts"],
            "ordered_sample_payload_sha256": canonical_sha256(payload_sha_rows),
            "rows": payload_sha_rows,
            "evidence_source": "RUNTIME_MOUNT_IMAGE_METADATA_PROBES_AND_FULL_GT_TREE_BYTES",
            "competition_ref": "biohub-cell-tracking-during-development",
            "competition_version_status": "UNKNOWN_NOT_EXPOSED_AT_RUNTIME",
        },
        "input_dataset_metadata": {
            "status": (
                "PASS_VERSION_PINNED_AND_CRITICAL_CONTENT_VERIFIED"
                if embedded_pinned_dataset_sources == expected_pinned_dataset_sources
                else "FAIL"
            ),
            "declared_expected": frozen_identities["input_datasets"],
            "expected_version_pinned_sources": expected_pinned_dataset_sources,
            "kernel_metadata_version_pinned_sources": embedded_pinned_dataset_sources,
            "runtime_mount_roots": {
                "primary_and_support": str(Path(ARTIFACTS).resolve()),
                "secondary": str(Path(SECONDARY_ARTIFACTS).resolve()),
                "deepcenter_checkpoint_parent": str(Path(_deepcenter_materialized_path).resolve().parent),
                "competition": str(Path(COMP_DIR).resolve()),
            },
            "platform_runtime_dataset_id_version_fields": "UNKNOWN_NOT_EXPOSED_AT_RUNTIME",
            "content_identity_is_independently_covered_by": [
                "support_code", "checkpoints", "competition_payload"
            ],
            "evidence_scope": (
                "EXACT_VERSIONED_SAVEKERNEL_DATASET_SOURCES_PLUS_RUNTIME_MOUNT_"
                "PRESENCE_AND_SELECTED_CRITICAL_CONTENT_HASHES"
            ),
        },
        "dependencies": {
            "status": "UNKNOWN_UNBOUND_TO_FROZEN_CONTRACT",
            "package_versions": package_versions,
            "package_versions_sha256": canonical_sha256(package_versions),
            "offline_wheel_rows": dependency_wheel_rows,
            "offline_wheel_rows_sha256": canonical_sha256(dependency_wheel_rows),
            "note": "Imports were exercised, but the frozen contract has no wheel/content hash identity.",
        },
    }
    identity_gate_pass = all((
        identity_evidence["support_code"]["status"] == "PASS",
        identity_evidence["checkpoints"]["status"] == "PASS",
        identity_evidence["official_scorer"]["status"] == "PASS",
        identity_evidence["competition_payload"]["status"] == "PASS",
        identity_evidence["input_dataset_metadata"]["status"]
        == "PASS_VERSION_PINNED_AND_CRITICAL_CONTENT_VERIFIED",
    ))
    if not identity_gate_pass:
        raise RuntimeError({"runtime_identity_gate_failed": identity_evidence})

    def v20b_read_live_runtime_parameters():
        return {
__V20B_RUNTIME_PARAMETER_LINES__
        }
    runtime_parameters = v20b_read_live_runtime_parameters()
    expected_invariant = copy.deepcopy(frozen_params)
    expected_invariant.pop("safe_div_parent_radius_um")
    actual_invariant = copy.deepcopy(runtime_parameters)
    actual_invariant.pop("safe_div_parent_radius_um")
    if canonical_bytes(actual_invariant) != canonical_bytes(expected_invariant):
        raise RuntimeError({"runtime_parameter_mismatch": {"expected": expected_invariant, "actual": actual_invariant}})
    invariant_sha = canonical_sha256(expected_invariant)
    identity_sha = canonical_sha256(frozen_identities)
    DEEPCENTER_VETO_DETECTOR = load_deepcenter_veto_detector()
    if DEEPCENTER_VETO_DETECTOR is None:
        raise RuntimeError("required DeepCenter veto detector did not load")
    runtime_cuda_devices = [
        _torch.cuda.get_device_name(index) for index in range(_torch.cuda.device_count())
    ]
    if len(runtime_cuda_devices) != 2 or any("T4" not in name.upper() for name in runtime_cuda_devices):
        raise RuntimeError({
            "frozen_gpu_runtime_mismatch": {
                "expected": "2x Tesla T4", "actual": runtime_cuda_devices,
            }
        })

    runtime_stage = "UPSTREAM_CACHE"
    all_stems = [row["sample_id"] for row in FROZEN_SAMPLE_MANIFEST["samples"]]
    anchors = FROZEN_SAMPLE_MANIFEST["anchors"]["sample_ids"]
    with PeakMemorySampler() as memory_sampler:
        ensure_runtime_budget("shared_predictor_before")
        shared_paths, shared_seconds, shared_workers = run_predictor(
            all_stems, "v20b_shared_upstream", "v20b_shared",
            deadline_monotonic=validation_deadline_monotonic,
        )
        ensure_runtime_budget("shared_predictor_after")
        runtime_stages.append({"stage": "predictor_shared_199", "status": "PASS",
                               "duration_seconds": shared_seconds, "sample_count": 199,
                               "worker_count": shared_workers})
        cache_entries = []
        cache_build_durations = []
        for sample_id in all_stems:
            ensure_runtime_budget(f"cache_build_before:{sample_id}")
            cache_sample_started = time.monotonic()
            raw_nodes, raw_edges = raw_graph_payload(shared_paths[sample_id])
            pre_nodes, pre_edges, pre_stats, _, _ = v20b_prepare_predivision_state(
                copy.deepcopy(raw_nodes), copy.deepcopy(raw_edges), dataset=sample_id,
                deepcenter_bundle=DEEPCENTER_VETO_DETECTOR,
            )
            cache_payload = {"sample_id": sample_id,
                             "embryo_id": sample_id.split("_", 1)[0],
                             "nodes_edges": canonical_graph_payload(pre_nodes, pre_edges),
                             "pre_division_stats": pre_stats}
            cache_bytes = canonical_bytes(cache_payload)
            cache_path = CACHE_ROOT / f"{sample_id}.json"
            cache_path.write_bytes(cache_bytes)
            cache_sha = hashlib.sha256(cache_bytes).hexdigest()
            if sha256_file(cache_path) != cache_sha:
                raise RuntimeError(f"cache readback mismatch: {sample_id}")
            cache_entries.append({
                "sample_id": sample_id, "embryo_id": sample_id.split("_", 1)[0],
                "source_sha256": frozen_identities["base_source_sha256"],
                "checkpoints": frozen_identities["checkpoints"],
                "support_code_manifest_sha256": frozen_identities["support_code_manifest_sha256"],
                "input_identity": payload_identity[sample_id],
                "runtime_identity_evidence_sha256": canonical_sha256(identity_evidence),
                "version_pinned_dataset_sources_sha256": canonical_sha256(
                    expected_pinned_dataset_sources
                ),
                "pre_division_config_sha256": invariant_sha, "graph_count": 1,
                "node_count": len(pre_nodes), "edge_count": len(pre_edges),
                "cache_path": f"v20b_private_predivision_cache/{sample_id}.json",
                "cache_sha256": cache_sha,
            })
            del raw_nodes, raw_edges, pre_nodes, pre_edges, pre_stats, cache_payload, cache_bytes
            cache_build_durations.append(time.monotonic() - cache_sample_started)
            record_progress_eta(
                "CACHE_BUILD", cache_build_durations,
                len(cache_build_durations), len(all_stems),
            )
            ensure_runtime_budget(f"cache_build_after:{sample_id}")
        cache_entries.sort(key=lambda row: row["sample_id"])
        cache_object = {"status": "COMPLETE", "sample_count": len(cache_entries),
                        "identity_binding_sha256": identity_sha,
                        "runtime_identity_evidence_sha256": canonical_sha256(identity_evidence),
                        "version_pinned_dataset_sources_sha256": canonical_sha256(
                            expected_pinned_dataset_sources
                        ),
                        "pre_division_config_sha256": invariant_sha,
                        "manifest_sha256": canonical_sha256(cache_entries), "entries": cache_entries}
        write_json(OUTPUT_ROOT / "cache_manifest.json", {
            "schema_version": "1.0", "task_id": TASK_ID,
            "status": "PASS", "all_pass": True,
            "cache_capture_point": "AFTER_GAP2_BEFORE_ADD_SAFE_DIVISIONS_POSTLINK",
            "sample_count": len(cache_entries),
            "manifest_sha256": cache_object["manifest_sha256"],
            "entries": cache_entries,
            "storage_strategy": {
                "type": "DISK_BACKED_STREAMING",
                "resident_cache_payload_count_max": 1,
                "loop_order": "SAMPLE_OUTER_ARM_INNER",
                "shared_mutable_graphs_or_stats_across_arms": False,
            },
            "cache": cache_object,
        })

        # Two independent anchor predictor runs: full-run evidence plus R70 repeat.
        ensure_runtime_budget("anchor_predictor_a_before")
        anchor_a_paths, anchor_a_seconds, anchor_a_workers = run_predictor(
            anchors, "v20b_anchor_full_a", "v20b_anchor_a",
            deadline_monotonic=validation_deadline_monotonic,
        )
        ensure_runtime_budget("anchor_predictor_a_after")
        runtime_stages.append({"stage": "predictor_anchor_full_a", "status": "PASS",
                               "duration_seconds": anchor_a_seconds, "sample_count": 2,
                               "worker_count": anchor_a_workers})
        ensure_runtime_budget("anchor_predictor_b_before")
        anchor_b_paths, anchor_b_seconds, anchor_b_workers = run_predictor(
            anchors, "v20b_anchor_r70_repeat_b", "v20b_anchor_b",
            deadline_monotonic=validation_deadline_monotonic,
        )
        ensure_runtime_budget("anchor_predictor_b_after")
        runtime_stages.append({"stage": "predictor_anchor_r70_repeat_b", "status": "PASS",
                               "duration_seconds": anchor_b_seconds, "sample_count": 2,
                               "worker_count": anchor_b_workers})

        runtime_stage = "ARM_EXECUTION"
        metrics_rows = []
        arm_runtime = {arm: 0.0 for arm in ARMS}
        arm_scoring_runtime = {arm: 0.0 for arm in ARMS}
        arm_total_runtime = {arm: 0.0 for arm in ARMS}
        arm_order_position_counts = {arm: {0: 0, 1: 0, 2: 0} for arm in ARMS}
        arm_outputs = {}
        main_results = {arm: {} for arm in ARMS}
        active_configs = {}
        safe_div_call_observations = {}
        safe_div_call_receipts = {}
        V20B_ACTIVE_ARM = None
        validation_columns = [
            "id", "dataset", "row_type", "node_id", "t", "z", "y", "x",
            "source_id", "target_id",
        ]
        validation_paths = {
            arm: OUTPUT_ROOT / f"validation_rows_{arm}.csv" for arm in ARMS
        }
        cache_sha_by_sample = {row["sample_id"]: row["cache_sha256"] for row in cache_entries}
        estimated_by_sample = {row["sample_id"]: row["estimated_node_count"] for row in payload_rows}
        gt_nodes_by_sample = {row["sample_id"]: row["gt_node_count"] for row in payload_rows}

        def v20b_parameters_from_live_runtime():
            return v20b_read_live_runtime_parameters()

        def v20b_add_safe_divisions_with_receipt(*args, **kwargs):
            arm = V20B_ACTIVE_ARM
            if arm not in ARMS:
                raise RuntimeError("safe-division call occurred without an active V20B arm")
            parameters = v20b_parameters_from_live_runtime()
            expected = copy.deepcopy(frozen_params)
            expected["safe_div_parent_radius_um"] = ARMS[arm]
            if canonical_bytes(parameters) != canonical_bytes(expected):
                raise RuntimeError({"actual_safe_division_call_parameter_drift": arm})
            call_parameters = {
                key: parameters[key] for key in (
                    "safe_div_parent_radius_um", "safe_div_sister_radius_um",
                    "safe_div_divergence_um", "safe_div_frame_cap",
                    "safe_div_global_cap", "deepcenter_enabled",
                    "deepcenter_safe_div_threshold",
                )
            }
            observation = safe_div_call_observations[arm]
            previous = observation.get("safe_division_function_arguments")
            if previous is not None and canonical_bytes(previous) != canonical_bytes(call_parameters):
                raise RuntimeError({"intra_arm_safe_division_call_parameter_drift": arm})
            observation["safe_division_function_arguments"] = call_parameters
            observation["call_count"] += 1
            dataset = kwargs.get("dataset")
            if not isinstance(dataset, str) or dataset not in all_stems:
                raise RuntimeError({"safe_division_call_missing_frozen_dataset": dataset})
            observation["sample_ids"].append(dataset)
            return add_safe_divisions_postlink(*args, **kwargs)

        # Capture each arm's active state before the sample-outer streaming loop.
        for arm, radius in ARMS.items():
            globals()["SAFE_DIV_MAX_UM"] = radius
            os.environ["BIOHUB_SAFE_DIV_MAX_UM"] = str(radius)
            V20B_ACTIVE_ARM = arm
            parameters_at_arm_entry = v20b_parameters_from_live_runtime()
            expected_parameters = copy.deepcopy(frozen_params)
            expected_parameters["safe_div_parent_radius_um"] = radius
            if canonical_bytes(parameters_at_arm_entry) != canonical_bytes(expected_parameters):
                raise RuntimeError({"pre_arm_active_parameter_drift": arm})
            active_configs[arm] = {
                "schema_version": "1.0", "task_id": TASK_ID, "arm": arm,
                "capture_phase": "AFTER_ALL_OVERRIDES_BEFORE_INFERENCE",
                "captured_before_sample_loop": True,
                "parameters": parameters_at_arm_entry,
                "parameters_sha256": canonical_sha256(parameters_at_arm_entry),
            }
            # This file is emitted before the first downstream sample call.
            write_json(OUTPUT_ROOT / f"active_config_{arm}.json", active_configs[arm])
            safe_div_call_observations[arm] = {
                "call_count": 0, "sample_ids": [],
                "safe_division_function_arguments": None,
            }
        V20B_ACTIVE_ARM = None

        # Keep only one canonical sample cache plus its three downstream arms
        # resident at a time.  Submission-format rows are streamed directly.
        validation_handles = {}
        validation_writers = {}
        arm_stream_durations = []
        try:
            for arm in ARMS:
                handle = validation_paths[arm].open("w", newline="", encoding="utf-8")
                writer = csv.DictWriter(handle, fieldnames=validation_columns, extrasaction="raise")
                writer.writeheader()
                validation_handles[arm] = handle
                validation_writers[arm] = writer
            frozen_arm_order = list(ARMS.items())
            for sample_index, sample_id in enumerate(all_stems):
                ensure_runtime_budget(f"arm_stream_before:{sample_id}")
                arm_stream_sample_started = time.monotonic()
                cache_path = CACHE_ROOT / f"{sample_id}.json"
                cache_bytes = cache_path.read_bytes()
                if hashlib.sha256(cache_bytes).hexdigest() != cache_sha_by_sample[sample_id]:
                    raise RuntimeError(f"streamed cache SHA mismatch: {sample_id}")
                cached = json.loads(cache_bytes)
                if cached.get("sample_id") != sample_id:
                    raise RuntimeError(f"streamed cache identity mismatch: {sample_id}")
                # Graphs, stats, frame caches, and DeepCenter caches are fresh
                # per arm.  This avoids granting the second/third arm a Python-
                # level warm-cache advantage; the rotated order further balances
                # unavoidable OS/filesystem cache effects across 199 samples.
                rotation = sample_index % len(frozen_arm_order)
                sample_arm_order = frozen_arm_order[rotation:] + frozen_arm_order[:rotation]
                for execution_order_index, (arm, radius) in enumerate(sample_arm_order):
                    ensure_runtime_budget(f"arm_stream_before:{sample_id}:{arm}")
                    total_started = time.monotonic()
                    arm_order_position_counts[arm][execution_order_index] += 1
                    globals()["SAFE_DIV_MAX_UM"] = radius
                    os.environ["BIOHUB_SAFE_DIV_MAX_UM"] = str(radius)
                    V20B_ACTIVE_ARM = arm
                    pre_nodes, pre_edges = restore_graph_payload(cached["nodes_edges"])
                    stats = copy.deepcopy(cached["pre_division_stats"])
                    arm_repair_frame_cache = {}
                    arm_deepcenter_heatmap_cache = {}
                    with PeakMemorySampler(interval_seconds=0.25) as sample_memory_sampler:
                        finalize_started = time.monotonic()
                        final_nodes, final_edges, final_stats = v20b_finalize_from_predivision(
                            pre_nodes, pre_edges, stats, dataset=sample_id,
                            deepcenter_bundle=DEEPCENTER_VETO_DETECTOR,
                            repair_frame_cache=arm_repair_frame_cache,
                            deepcenter_heatmap_cache=arm_deepcenter_heatmap_cache,
                        )
                        finalize_seconds = time.monotonic() - finalize_started
                        output_rows = validation_rows(sample_id, final_nodes, final_edges)
                        topology = topology_check(sample_id, final_nodes, final_edges, output_rows)
                        topology.update({"arm": arm})
                        topology_rows.append(topology)
                        if not topology["topology_valid"] or not topology["schema_valid"]:
                            raise RuntimeError({"invalid_final_graph": topology})
                        estimated = estimated_by_sample[sample_id]
                        scoring_started = time.monotonic()
                        scored = official_score(sample_id, output_rows, estimated)
                        scoring_seconds = time.monotonic() - scoring_started
                    sample_peak_memory_bytes = int(
                        max(
                            sample_memory_sampler.peak_gpu_mib,
                            sample_memory_sampler.peak_process_rss_mib,
                        )
                        * 1024 * 1024
                    )
                    caps = cap_diagnostics(pre_nodes, pre_edges, final_edges, final_stats)
                    final_sha = canonical_sha256(canonical_graph_payload(final_nodes, final_edges))
                    output_sha = canonical_sha256(output_rows)
                    total_seconds = time.monotonic() - total_started
                    metric_row = {
                        "arm": arm, "sample_id": sample_id,
                        "embryo_id": sample_id.split("_", 1)[0],
                        "status": "RUN_COMPLETE", **scored,
                        "gt_node_count": int(gt_nodes_by_sample[sample_id]),
                        "gt_node_count_evidence": "ACTUAL_GT_GEFF_GRAPH_NUM_NODES",
                        "estimated_node_count": estimated,
                        "estimated_node_count_evidence": "GEFF_METADATA_ESTIMATED_NUMBER_OF_NODES",
                        # Pre-veto geometric pool: DeepCenter accepted/rejected
                        # counts are coherent subsets of this denominator.
                        "safe_div_candidate_count": final_stats.get("safe_division_geometric_candidates", 0),
                        "accepted_division_count": final_stats.get("safe_divisions_added", 0),
                        "deepcenter_accepted_count": final_stats.get("deepcenter_safe_div_accepted", 0),
                        "deepcenter_rejected_count": final_stats.get("deepcenter_safe_div_rejected", 0),
                        "frame_cap_saturation": int(caps["frame_cap_saturated"]),
                        "global_cap_saturation": int(caps["global_cap_saturated"]),
                        "topology_valid": topology["topology_valid"],
                        "schema_valid": topology["schema_valid"],
                        # Frozen tie-break time is only the cache-to-final-graph
                        # function call. Scoring and row/audit work are excluded.
                        "runtime_seconds": finalize_seconds,
                        "finalize_runtime_seconds": finalize_seconds,
                        "scoring_runtime_seconds": scoring_seconds,
                        "total_runtime_seconds": total_seconds,
                        "execution_order_index": execution_order_index,
                        "peak_memory_bytes": sample_peak_memory_bytes,
                        "pre_division_cache_sha256": cache_sha_by_sample[sample_id],
                        "final_graph_sha256": final_sha,
                        "validation_rows_sha256": output_sha,
                        "final_output_sha256": output_sha,
                        "scorer_input_rows_sha256": output_sha,
                    }
                    metrics_rows.append(metric_row)
                    main_results[arm][sample_id] = {"metrics": metric_row}
                    for output_row in output_rows:
                        validation_writers[arm].writerow(output_row)
                    arm_runtime[arm] += finalize_seconds
                    arm_scoring_runtime[arm] += scoring_seconds
                    arm_total_runtime[arm] += total_seconds
                    del pre_nodes, pre_edges, stats, final_nodes, final_edges
                    del final_stats, output_rows, scored, metric_row
                    del arm_repair_frame_cache, arm_deepcenter_heatmap_cache
                    ensure_runtime_budget(f"arm_stream_after:{sample_id}:{arm}")
                V20B_ACTIVE_ARM = None
                del cached, cache_bytes
                arm_stream_durations.append(time.monotonic() - arm_stream_sample_started)
                record_progress_eta(
                    "ARM_STREAM_THREE_ARMS", arm_stream_durations,
                    len(arm_stream_durations), len(all_stems),
                )
                ensure_runtime_budget(f"arm_stream_after:{sample_id}")
        finally:
            V20B_ACTIVE_ARM = None
            for handle in validation_handles.values():
                handle.close()

        for arm in ARMS:
            arm_outputs[arm] = [{
                "path": validation_paths[arm].name,
                "sha256": sha256_file(validation_paths[arm]),
            }]
            observation = safe_div_call_observations[arm]
            if (
                observation["call_count"] != len(all_stems)
                or observation["sample_ids"] != all_stems
                or observation["safe_division_function_arguments"] is None
            ):
                raise RuntimeError({"safe_division_call_coverage_mismatch": arm,
                                    "call_count": observation["call_count"]})
            safe_div_call_receipts[arm] = {
                "schema_version": "1.0", "task_id": TASK_ID, "arm": arm,
                "capture_phase": "AT_SAFE_DIVISION_CALL",
                "evidence_source": "DERIVED_FINALIZE_WRAPPER_ACTUAL_CALL_OBSERVATION",
                "safe_division_function_arguments": observation["safe_division_function_arguments"],
                "call_count": observation["call_count"],
                "sample_count": len(observation["sample_ids"]),
                "sample_ids_sha256": canonical_sha256(observation["sample_ids"]),
            }
            write_json(
                OUTPUT_ROOT / f"safe_div_call_receipt_{arm}.json",
                safe_div_call_receipts[arm],
            )

        runtime_stage = "CACHE_EQUIVALENCE"
        ensure_runtime_budget("cache_equivalence_before")
        equivalence_rows = []
        anchor_shared_raw = {sample: raw_graph_payload(shared_paths[sample]) for sample in anchors}
        anchor_fresh_a_raw = {sample: raw_graph_payload(anchor_a_paths[sample]) for sample in anchors}
        for arm, radius in ARMS.items():
            globals()["SAFE_DIV_MAX_UM"] = radius
            os.environ["BIOHUB_SAFE_DIV_MAX_UM"] = str(radius)
            for sample_id in anchors:
                ensure_runtime_budget(f"cache_equivalence:{sample_id}:{arm}")
                # Pure split equivalence: original V19C full function vs cached downstream on identical raw graph.
                shared_raw_nodes, shared_raw_edges = anchor_shared_raw[sample_id]
                same_full_nodes, same_full_edges, same_stats = filter_output_graph(
                    copy.deepcopy(shared_raw_nodes), copy.deepcopy(shared_raw_edges), dataset=sample_id,
                    deepcenter_bundle=DEEPCENTER_VETO_DETECTOR,
                )
                cached_result = main_results[arm][sample_id]
                same_full_rows = validation_rows(sample_id, same_full_nodes, same_full_edges)
                same_full_metrics = official_score(
                    sample_id, same_full_rows,
                    cached_result["metrics"]["estimated_node_count"],
                )
                # Fresh full predictor evidence, kept separate from pure cache-split equivalence.
                fresh_nodes, fresh_edges = anchor_fresh_a_raw[sample_id]
                fresh_final_nodes, fresh_final_edges, fresh_stats = filter_output_graph(
                    copy.deepcopy(fresh_nodes), copy.deepcopy(fresh_edges), dataset=sample_id,
                    deepcenter_bundle=DEEPCENTER_VETO_DETECTOR,
                )
                fresh_rows = validation_rows(sample_id, fresh_final_nodes, fresh_final_edges)
                fresh_metrics = official_score(
                    sample_id, fresh_rows,
                    cached_result["metrics"]["estimated_node_count"],
                )
                tolerance = FROZEN_CONTRACT["experiment_freeze"]["comparison_tolerances"]["reported_score_absolute"]
                row = {
                    "arm": arm, "sample_id": sample_id,
                    "cache_sha256": cached_result["metrics"]["pre_division_cache_sha256"],
                    "same_raw_full_graph_sha256": canonical_sha256(canonical_graph_payload(same_full_nodes, same_full_edges)),
                    "cached_graph_sha256": cached_result["metrics"]["final_graph_sha256"],
                    "same_raw_full_rows_sha256": canonical_sha256(same_full_rows),
                    "cached_rows_sha256": cached_result["metrics"]["validation_rows_sha256"],
                    "same_raw_metric_abs_delta": abs(same_full_metrics["official_score"] - cached_result["metrics"]["official_score"]),
                    "fresh_full_graph_sha256": canonical_sha256(canonical_graph_payload(fresh_final_nodes, fresh_final_edges)),
                    "fresh_full_rows_sha256": canonical_sha256(fresh_rows),
                    "fresh_full_metric_abs_delta": abs(fresh_metrics["official_score"] - cached_result["metrics"]["official_score"]),
                }
                row["same_raw_cache_equivalent"] = (
                    row["same_raw_full_graph_sha256"] == row["cached_graph_sha256"]
                    and row["same_raw_full_rows_sha256"] == row["cached_rows_sha256"]
                    and row["same_raw_metric_abs_delta"] <= tolerance
                )
                row["fresh_full_cache_equivalent"] = (
                    row["fresh_full_graph_sha256"] == row["cached_graph_sha256"]
                    and row["fresh_full_rows_sha256"] == row["cached_rows_sha256"]
                    and row["fresh_full_metric_abs_delta"] <= tolerance
                )
                row["upstream_predictor_replay_equal"] = row["fresh_full_cache_equivalent"]
                row["failure_classification"] = (
                    None if row["fresh_full_cache_equivalent"]
                    else "UPSTREAM_PREDICTOR_NONDETERMINISM_OR_INPUT_IDENTITY_DRIFT"
                )
                row_pass = row["same_raw_cache_equivalent"] and row["fresh_full_cache_equivalent"]
                row.update({
                    "topology_equal": (
                        row["same_raw_full_graph_sha256"] == row["cached_graph_sha256"]
                        and row["fresh_full_graph_sha256"] == row["cached_graph_sha256"]
                    ),
                    "metrics_within_tolerance": (
                        row["same_raw_metric_abs_delta"] <= tolerance
                        and row["fresh_full_metric_abs_delta"] <= tolerance
                    ),
                    "submission_rows_equal": (
                        row["same_raw_full_rows_sha256"] == row["cached_rows_sha256"]
                        and row["fresh_full_rows_sha256"] == row["cached_rows_sha256"]
                    ),
                    "official_score_abs_diff": max(
                        row["same_raw_metric_abs_delta"], row["fresh_full_metric_abs_delta"]
                    ),
                    "max_coordinate_abs_diff": 0.0 if row_pass else 1e300,
                    "pass": row_pass,
                })
                equivalence_rows.append(row)
                ensure_runtime_budget(f"cache_equivalence_after:{sample_id}:{arm}")
        all_anchor_paths_pass = all(row["pass"] for row in equivalence_rows)
        cache_equivalence = {
            "schema_version": "1.0", "task_id": TASK_ID,
            "status": "PASS" if all_anchor_paths_pass else "FAIL",
            "anchors": anchors, "rows": equivalence_rows,
            "all_three_arm_same_raw_full_vs_cache_pass": all(row["same_raw_cache_equivalent"] for row in equivalence_rows),
            "all_three_arm_fresh_full_vs_cache_pass": all(row["fresh_full_cache_equivalent"] for row in equivalence_rows),
            "all_pass": all_anchor_paths_pass,
            "validation_wall_clock_seconds": time.monotonic() - experiment_started,
        }
        write_json(OUTPUT_ROOT / "cache_equivalence.json", cache_equivalence)
        if not cache_equivalence["all_pass"]:
            raise RuntimeError("three-arm anchor same-raw/fresh full-vs-cache equivalence failed")

        runtime_stage = "DETERMINISM"
        ensure_runtime_budget("determinism_before")
        determinism_rows = []
        for sample_id in anchors:
            ensure_runtime_budget(f"determinism:{sample_id}")
            raw_a_nodes, raw_a_edges = raw_graph_payload(anchor_a_paths[sample_id])
            raw_b_nodes, raw_b_edges = raw_graph_payload(anchor_b_paths[sample_id])
            pre_a = v20b_prepare_predivision_state(copy.deepcopy(raw_a_nodes), copy.deepcopy(raw_a_edges), sample_id, DEEPCENTER_VETO_DETECTOR)
            pre_b = v20b_prepare_predivision_state(copy.deepcopy(raw_b_nodes), copy.deepcopy(raw_b_edges), sample_id, DEEPCENTER_VETO_DETECTOR)
            pre_a_sha = canonical_sha256(canonical_graph_payload(pre_a[0], pre_a[1]))
            pre_b_sha = canonical_sha256(canonical_graph_payload(pre_b[0], pre_b[1]))
            globals()["SAFE_DIV_MAX_UM"] = 7.0
            final_a = filter_output_graph(copy.deepcopy(raw_a_nodes), copy.deepcopy(raw_a_edges), sample_id, DEEPCENTER_VETO_DETECTOR)
            final_b = filter_output_graph(copy.deepcopy(raw_b_nodes), copy.deepcopy(raw_b_edges), sample_id, DEEPCENTER_VETO_DETECTOR)
            rows_a = validation_rows(sample_id, final_a[0], final_a[1])
            rows_b = validation_rows(sample_id, final_b[0], final_b[1])
            estimated = main_results["R70"][sample_id]["metrics"]["estimated_node_count"]
            metric_a = official_score(sample_id, rows_a, estimated)
            metric_b = official_score(sample_id, rows_b, estimated)
            determinism_rows.append({
                "sample_id": sample_id, "arm": "R70", "repetitions": 2,
                "cache_sha256": main_results["R70"][sample_id]["metrics"]["pre_division_cache_sha256"],
                "pre_division_graph_sha256_a": pre_a_sha,
                "pre_division_graph_sha256_b": pre_b_sha,
                "final_graph_sha256_a": canonical_sha256(canonical_graph_payload(final_a[0], final_a[1])),
                "final_graph_sha256_b": canonical_sha256(canonical_graph_payload(final_b[0], final_b[1])),
                "validation_rows_sha256_a": canonical_sha256(rows_a),
                "validation_rows_sha256_b": canonical_sha256(rows_b),
                "official_score_abs_delta": abs(metric_a["official_score"] - metric_b["official_score"]),
            })
            ensure_runtime_budget(f"determinism_after:{sample_id}")
        for row in determinism_rows:
            row["exact_upstream_topology"] = row["pre_division_graph_sha256_a"] == row["pre_division_graph_sha256_b"]
            row["exact_final_graph"] = row["final_graph_sha256_a"] == row["final_graph_sha256_b"]
            row["exact_output_rows"] = row["validation_rows_sha256_a"] == row["validation_rows_sha256_b"]
            row.update({
                "pre_division_topology_equal": row["exact_upstream_topology"],
                "final_graph_equal": row["exact_final_graph"],
                "metrics_within_tolerance": row["official_score_abs_delta"] <= 1e-4,
                "output_rows_equal": row["exact_output_rows"],
                "official_score_abs_diff": row["official_score_abs_delta"],
                "pass": row["exact_upstream_topology"] and row["exact_final_graph"]
                        and row["exact_output_rows"] and row["official_score_abs_delta"] <= 1e-4,
            })
        determinism = {"schema_version": "1.0", "task_id": TASK_ID, "arm": "R70",
                       "repetitions": 2, "anchors": anchors, "rows": determinism_rows,
                       "all_pass": all(row["exact_upstream_topology"] and row["exact_final_graph"]
                                       and row["exact_output_rows"] and row["official_score_abs_delta"] <= 1e-4
                                       for row in determinism_rows),
                       "shared_cache_used_for_all_arm_comparisons": True,
                       "status": "PASS" if all(row["exact_upstream_topology"] and row["exact_final_graph"]
                                                and row["exact_output_rows"] and row["official_score_abs_delta"] <= 1e-4
                                                for row in determinism_rows) else "FAIL",
                       "validation_wall_clock_seconds": time.monotonic() - experiment_started}
        write_json(OUTPUT_ROOT / "runtime_determinism.json", determinism)
        if not determinism["all_pass"]:
            raise RuntimeError("R70 anchor upstream determinism failed")

    runtime_stage = "AGGREGATION"
    ensure_runtime_budget("aggregation_before")
    write_csv(OUTPUT_ROOT / "per_sample_metrics.csv", metrics_rows, SAMPLE_COLUMNS)

    def ordered_sample_sha256(rows, key):
        return canonical_sha256([
            {"sample_id": row["sample_id"], "sha256": row[key]}
            for row in sorted(rows, key=lambda item: item["sample_id"])
        ])

    def aggregate_rows(rows):
        if not rows:
            raise RuntimeError("refusing empty metric aggregation")
        official_input = [{key: row[key] for key in official_metrics.METRIC_COLUMNS} for row in rows]
        summary = official_metrics.summarise(official_input)
        weights = [int(row["edge_tp"]) + int(row["edge_fp"]) + int(row["edge_fn"]) for row in rows]
        weight_total = sum(weights)
        estimated_total = sum(float(row["estimated_node_count"]) for row in rows)
        predicted_total = sum(int(row["num_pred_nodes"]) for row in rows)
        gt_node_total = sum(int(row["gt_node_count"]) for row in rows)
        result = {
            "sample_count": len(rows), "official_score": float(summary["score"]),
            "adj_edge_jaccard": float(summary["adj_edge_jaccard"]),
            "edge_jaccard": float(summary["edge_jaccard"]),
            "division_jaccard": float(summary["division_jaccard"]),
            "edge_tp": sum(int(row["edge_tp"]) for row in rows),
            "edge_fp": sum(int(row["edge_fp"]) for row in rows),
            "edge_fn": sum(int(row["edge_fn"]) for row in rows),
            "division_tp": sum(int(row["division_tp"]) for row in rows),
            "division_fp": sum(int(row["division_fp"]) for row in rows),
            "division_fn": sum(int(row["division_fn"]) for row in rows),
            "num_pred_nodes": predicted_total, "gt_node_count": gt_node_total,
            "estimated_node_count": estimated_total,
            "total_node_ratio": (predicted_total - estimated_total) / estimated_total,
            "node_count_penalty": (
                sum(weight * float(row["node_count_penalty"]) for weight, row in zip(weights, rows)) / weight_total
                if weight_total else 0.0),
            "node_recall": sum(float(row["node_recall"]) for row in rows) / len(rows),
            "edges_fragmented": sum(int(row["edges_fragmented"]) for row in rows),
            "edges_lost_to_detection": sum(int(row["edges_lost_to_detection"]) for row in rows),
            "wrong_association_edges": sum(int(row["wrong_association_edges"]) for row in rows),
            "safe_div_candidate_count": sum(int(row["safe_div_candidate_count"]) for row in rows),
            "accepted_division_count": sum(int(row["accepted_division_count"]) for row in rows),
            "deepcenter_accepted_count": sum(int(row["deepcenter_accepted_count"]) for row in rows),
            "deepcenter_rejected_count": sum(int(row["deepcenter_rejected_count"]) for row in rows),
            "frame_cap_saturation_rate": sum(int(row["frame_cap_saturation"]) for row in rows) / len(rows),
            "global_cap_saturation_rate": sum(int(row["global_cap_saturation"]) for row in rows) / len(rows),
            # Aggregate cap fields use the frozen saturation-rate semantics.
            "frame_cap_saturation": sum(int(row["frame_cap_saturation"]) for row in rows) / len(rows),
            "global_cap_saturation": sum(int(row["global_cap_saturation"]) for row in rows) / len(rows),
            "frame_cap_saturation_max": max(float(row["frame_cap_saturation"]) for row in rows),
            "global_cap_saturation_max": max(float(row["global_cap_saturation"]) for row in rows),
            "topology_valid": all(row["topology_valid"] for row in rows),
            "schema_valid": all(row["schema_valid"] for row in rows),
            "runtime_seconds": sum(float(row["runtime_seconds"]) for row in rows),
            "finalize_runtime_seconds": sum(float(row["finalize_runtime_seconds"]) for row in rows),
            "scoring_runtime_seconds": sum(float(row["scoring_runtime_seconds"]) for row in rows),
            "total_runtime_seconds": sum(float(row["total_runtime_seconds"]) for row in rows),
            "peak_memory_bytes": max(float(row["peak_memory_bytes"]) for row in rows),
            "gt_node_count_evidence": "SUM_ACTUAL_GT_GEFF_GRAPH_NUM_NODES",
            "estimated_node_count_evidence": "GEFF_METADATA_ESTIMATED_NUMBER_OF_NODES_ALL_SAMPLES",
            "pre_division_cache_sha256": ordered_sample_sha256(rows, "pre_division_cache_sha256"),
            "final_output_sha256": ordered_sample_sha256(rows, "final_output_sha256"),
            "scorer_input_rows_sha256": ordered_sample_sha256(rows, "scorer_input_rows_sha256"),
            "hash_aggregation": "ORDERED_SAMPLE_SHA_ROWS_V1",
        }
        return result

    embryo_rows = []
    aggregate_map = {}
    micro_macro_rows = []
    for arm in ARMS:
        ensure_runtime_budget(f"aggregation_arm:{arm}")
        aggregate_map[arm] = {}
        for embryo in ("44b6", "6bba"):
            selected = [row for row in metrics_rows if row["arm"] == arm and row["embryo_id"] == embryo]
            aggregate = aggregate_rows(selected)
            aggregate_map[arm][embryo] = aggregate
            embryo_rows.append({"arm": arm, "embryo_id": embryo, "status": "RUN_COMPLETE", **aggregate})
        pooled = aggregate_rows([row for row in metrics_rows if row["arm"] == arm])
        macro = {
            key: sum(aggregate_map[arm][embryo][key] for embryo in ("44b6", "6bba")) / 2.0
            for key in ("official_score", "adj_edge_jaccard", "edge_jaccard", "division_jaccard",
                        "node_count_penalty", "total_node_ratio", "node_recall",
                        "frame_cap_saturation", "global_cap_saturation")
        }
        macro["sample_count"] = sum(aggregate_map[arm][embryo]["sample_count"] for embryo in ("44b6", "6bba"))
        for key in (
            "edge_tp", "edge_fp", "edge_fn", "division_tp", "division_fp", "division_fn",
            "num_pred_nodes", "gt_node_count", "estimated_node_count", "edges_fragmented",
            "edges_lost_to_detection", "wrong_association_edges", "safe_div_candidate_count",
            "accepted_division_count", "deepcenter_accepted_count", "deepcenter_rejected_count",
        ):
            macro[key] = None
        macro.update({
            "status": "RUN_COMPLETE",
            "gt_node_count_evidence": "NOT_APPLICABLE_EMBRYO_EQUAL_MACRO_NONADDITIVE",
            "estimated_node_count_evidence": "NOT_APPLICABLE_EMBRYO_EQUAL_MACRO_NONADDITIVE",
            "topology_valid": all(aggregate_map[arm][embryo]["topology_valid"] for embryo in ("44b6", "6bba")),
            "schema_valid": all(aggregate_map[arm][embryo]["schema_valid"] for embryo in ("44b6", "6bba")),
            "runtime_seconds": sum(aggregate_map[arm][embryo]["runtime_seconds"] for embryo in ("44b6", "6bba")),
            "finalize_runtime_seconds": sum(aggregate_map[arm][embryo]["finalize_runtime_seconds"] for embryo in ("44b6", "6bba")),
            "scoring_runtime_seconds": sum(aggregate_map[arm][embryo]["scoring_runtime_seconds"] for embryo in ("44b6", "6bba")),
            "total_runtime_seconds": sum(aggregate_map[arm][embryo]["total_runtime_seconds"] for embryo in ("44b6", "6bba")),
            "peak_memory_bytes": max(aggregate_map[arm][embryo]["peak_memory_bytes"] for embryo in ("44b6", "6bba")),
            "pre_division_cache_sha256": canonical_sha256([
                {"embryo_id": embryo, "sha256": aggregate_map[arm][embryo]["pre_division_cache_sha256"]}
                for embryo in ("44b6", "6bba")
            ]),
            "final_output_sha256": canonical_sha256([
                {"embryo_id": embryo, "sha256": aggregate_map[arm][embryo]["final_output_sha256"]}
                for embryo in ("44b6", "6bba")
            ]),
            "scorer_input_rows_sha256": canonical_sha256([
                {"embryo_id": embryo, "sha256": aggregate_map[arm][embryo]["scorer_input_rows_sha256"]}
                for embryo in ("44b6", "6bba")
            ]),
            "hash_aggregation": "ORDERED_EMBRYO_AGGREGATE_SHA_ROWS_V1",
        })
        aggregate_map[arm]["POOLED_MICRO"] = pooled
        aggregate_map[arm]["EMBRYO_EQUAL_MACRO"] = macro
        pooled_row = {"arm": arm, "scope": "POOLED_MICRO", "embryo_id": "ALL",
                      "status": "RUN_COMPLETE", **pooled}
        macro_row = {"arm": arm, "scope": "EMBRYO_EQUAL_MACRO",
                     "embryo_id": "EQUAL_44b6_6bba", **macro}
        micro_macro_rows.extend([pooled_row, macro_row])
    write_csv(OUTPUT_ROOT / "per_embryo_metrics.csv", embryo_rows, EMBRYO_COLUMNS)
    write_csv(OUTPUT_ROOT / "micro_macro_comparison.csv", micro_macro_rows, MICRO_MACRO_COLUMNS)

    sample_delta_rows = []
    for candidate in ("R80", "R90"):
        ensure_runtime_budget(f"sample_deltas:{candidate}")
        for sample_id in all_stems:
            cand = main_results[candidate][sample_id]["metrics"]
            ctrl = main_results["R70"][sample_id]["metrics"]
            sample_delta_rows.append({
                "candidate_arm": candidate, "control_arm": "R70", "sample_id": sample_id,
                "embryo_id": cand["embryo_id"],
                **{f"{key}_delta": (
                    None if cand[key] is None or ctrl[key] is None else cand[key] - ctrl[key]
                ) for key in (
                    "official_score", "adj_edge_jaccard", "edge_jaccard", "division_jaccard",
                    "division_tp", "division_fp", "division_fn", "edge_tp", "edge_fp",
                    "edge_fn", "num_pred_nodes", "gt_node_count", "estimated_node_count",
                    "total_node_ratio", "node_count_penalty", "node_recall",
                    "edges_fragmented", "edges_lost_to_detection", "wrong_association_edges",
                    "safe_div_candidate_count", "accepted_division_count",
                    "deepcenter_accepted_count", "deepcenter_rejected_count",
                    "frame_cap_saturation", "global_cap_saturation", "runtime_seconds",
                    "finalize_runtime_seconds", "scoring_runtime_seconds",
                    "total_runtime_seconds", "peak_memory_bytes")},
                "topology_both_valid": bool(cand["topology_valid"] and ctrl["topology_valid"]),
                "schema_both_valid": bool(cand["schema_valid"] and ctrl["schema_valid"]),
                "pre_division_cache_sha256_equal": (
                    cand["pre_division_cache_sha256"] == ctrl["pre_division_cache_sha256"]
                ),
                "control_final_output_sha256": ctrl["final_output_sha256"],
                "candidate_final_output_sha256": cand["final_output_sha256"],
                "final_output_sha256_equal": (
                    cand["final_output_sha256"] == ctrl["final_output_sha256"]
                ),
            })
    write_csv(OUTPUT_ROOT / "paired_deltas_by_sample.csv", sample_delta_rows, SAMPLE_DELTA_COLUMNS)
    embryo_delta_rows = []
    for candidate in ("R80", "R90"):
        ensure_runtime_budget(f"embryo_deltas:{candidate}")
        for embryo in ("44b6", "6bba"):
            cand, ctrl = aggregate_map[candidate][embryo], aggregate_map["R70"][embryo]
            embryo_delta_rows.append({
                "candidate_arm": candidate, "control_arm": "R70", "embryo_id": embryo,
                "sample_count": cand["sample_count"],
                **{f"{key}_delta": cand[key] - ctrl[key] for key in (
                    "official_score", "adj_edge_jaccard", "edge_jaccard", "division_jaccard",
                    "division_tp", "division_fp", "division_fn", "edge_tp", "edge_fp",
                    "edge_fn", "num_pred_nodes", "gt_node_count", "estimated_node_count",
                    "total_node_ratio", "node_count_penalty", "node_recall",
                    "edges_fragmented", "edges_lost_to_detection", "wrong_association_edges",
                    "safe_div_candidate_count", "accepted_division_count",
                    "deepcenter_accepted_count", "deepcenter_rejected_count",
                    "frame_cap_saturation_rate", "global_cap_saturation_rate",
                    "runtime_seconds", "finalize_runtime_seconds",
                    "scoring_runtime_seconds", "total_runtime_seconds", "peak_memory_bytes")},
                "topology_both_valid": bool(cand["topology_valid"] and ctrl["topology_valid"]),
                "schema_both_valid": bool(cand["schema_valid"] and ctrl["schema_valid"]),
                "pre_division_cache_sha256_equal": (
                    cand["pre_division_cache_sha256"] == ctrl["pre_division_cache_sha256"]
                ),
                "control_final_output_sha256": ctrl["final_output_sha256"],
                "candidate_final_output_sha256": cand["final_output_sha256"],
                "final_output_sha256_equal": (
                    cand["final_output_sha256"] == ctrl["final_output_sha256"]
                ),
            })
    write_csv(OUTPUT_ROOT / "paired_deltas_by_embryo.csv", embryo_delta_rows, EMBRYO_DELTA_COLUMNS)
    write_json(OUTPUT_ROOT / "division_confusion_by_embryo.json", {
        "schema_version": "1.0", "task_id": TASK_ID,
        "arms": {
            arm: {
                "embryos": {
                    embryo: {
                        key: aggregate_map[arm][embryo][key]
                        for key in ("division_tp", "division_fp", "division_fn", "division_jaccard")
                    }
                    for embryo in ("44b6", "6bba")
                },
                "global": {
                    key: aggregate_map[arm]["POOLED_MICRO"][key]
                    for key in ("division_tp", "division_fp", "division_fn", "division_jaccard")
                },
            }
            for arm in ARMS
        },
    })
    write_json(OUTPUT_ROOT / "topology_validation.json", {
        "schema_version": "1.0", "task_id": TASK_ID, "rows": topology_rows,
        "expected_checks": 199 * 3, "actual_checks": len(topology_rows),
        "all_pass": len(topology_rows) == 199 * 3 and all(row["topology_valid"] and row["schema_valid"] for row in topology_rows),
    })

    runtime_stage = "CONFIG_RECEIPTS"
    ensure_runtime_budget("config_receipts_before")
    hardware = {"platform": platform.platform(), "python": platform.python_version(),
                "cuda_available": bool(_torch.cuda.is_available()),
                "cuda_device_count": int(_torch.cuda.device_count()),
                "cuda_devices": runtime_cuda_devices,
                "frozen_machine_shape": "NvidiaTeslaT4",
                "expected_device_count": 2}
    for arm, radius in ARMS.items():
        active = active_configs[arm]
        call = safe_div_call_receipts[arm]
        parameters = active["parameters"]
        receipt = {"schema_version": "1.0", "task_id": TASK_ID, "arm": arm,
                   "status": "RUN_COMPLETE", "capture_phase": "AFTER_ALL_OVERRIDES_BEFORE_INFERENCE",
                   "canonical_source": "POST_OVERRIDE_RUNTIME_STATE", "parameters": parameters,
                   "receipt_emitted_phase": "AFTER_ARM_COMPLETION",
                   "active_config_sha256": sha256_file(OUTPUT_ROOT / f"active_config_{arm}.json"),
                   "safe_div_call_receipt_sha256": sha256_file(OUTPUT_ROOT / f"safe_div_call_receipt_{arm}.json"),
                   "identities": frozen_identities,
                   "identity_declaration_scope": "FROZEN_EXPECTED_IDENTITIES",
                   "runtime_identity_evidence": identity_evidence,
                   "runtime_identity_gate_pass": identity_gate_pass,
                   "pre_division_cache": cache_object,
                   "hardware": hardware,
                   "runtime": {"arm_downstream_seconds": arm_runtime[arm],
                               "shared_upstream_seconds": shared_seconds,
                               "validation_elapsed_seconds": time.monotonic() - experiment_started},
                   "outputs": arm_outputs[arm]}
        write_json(OUTPUT_ROOT / f"canonical_resolved_config_{arm}.json", receipt)

    checker_path = WORKING_ROOT / "v20b_verify_resolved_config.py"
    checker_path.write_bytes(base64.b64decode(EMBEDDED_CHECKER_B64))
    contract_path = WORKING_ROOT / "v20b_frozen_contract.json"
    write_json(contract_path, FROZEN_CONTRACT)
    checker_command = [sys.executable, "-B", str(checker_path), "--contract", str(contract_path)]
    for arm in ARMS:
        checker_command += ["--receipt", f"{arm}={OUTPUT_ROOT / f'canonical_resolved_config_{arm}.json'}",
                            "--active-config", f"{arm}={OUTPUT_ROOT / f'active_config_{arm}.json'}",
                            "--call-receipt", f"{arm}={OUTPUT_ROOT / f'safe_div_call_receipt_{arm}.json'}"]
    checker_result = subprocess.run(checker_command, check=True, capture_output=True, text=True)
    if "V20B_RESOLVED_CONFIG_PASS" not in checker_result.stdout:
        raise RuntimeError("resolved-config checker did not emit PASS")
    resolved_config_checker_pass = True
    write_json(OUTPUT_ROOT / "resolved_config_verification.json", {
        "schema_version": "1.0", "task_id": TASK_ID, "status": "PASS",
        "all_pass": True,
        "checker_sha256": sha256_file(checker_path),
        "stdout_sha256": hashlib.sha256(checker_result.stdout.encode()).hexdigest(),
        "pass_marker": "V20B_RESOLVED_CONFIG_PASS",
        "shared_pre_division_cache_manifest_sha256": cache_object["manifest_sha256"],
        "runtime_identity_gate_pass": identity_gate_pass,
        "runtime_identity_evidence": identity_evidence,
        "runtime_identity_evidence_sha256": canonical_sha256(identity_evidence),
    })

    runtime_stage = "RUNTIME_RECEIPTS"
    ensure_runtime_budget("runtime_receipt_before_promotion")
    if V20B_PREDICTOR_RUNS_STARTED != 3 or len(V20B_PREDICTOR_RUN_START_EVENTS) != 3:
        raise RuntimeError({
            "predictor_logical_start_count_mismatch": V20B_PREDICTOR_RUNS_STARTED,
            "events": V20B_PREDICTOR_RUN_START_EVENTS,
        })
    scoring_semantics_pass = (
        len(metrics_rows) == 199 * 3
        and all(row["score_coordinate_semantics"] == "ROUNDED_CLAMPED_SUBMISSION_ROWS"
                for row in metrics_rows)
        and all(row["scorer_input_rows_sha256"] == row["final_output_sha256"]
                for row in metrics_rows)
    )
    if not scoring_semantics_pass:
        raise RuntimeError("official scorer input rows were not exact rounded/clamped output rows")
    validation_wall_clock_seconds = time.monotonic() - experiment_started
    validation_within_budget = validation_wall_clock_seconds <= validation_limit_seconds
    production_runtime_basis = BUILDER_MANIFEST["inputs"]["v19c_historical_production_runtime"]
    production_reference_seconds = float(production_runtime_basis["wall_clock_seconds"])
    production_limit_seconds = float(
        FROZEN_CONTRACT["experiment_freeze"]["runtime_budget"]["production_wall_clock_seconds_max"]
    )
    production_within_budget = production_reference_seconds <= production_limit_seconds
    runtime_budget_pass = validation_within_budget and production_within_budget
    write_json(OUTPUT_ROOT / "runtime_receipts.json", {
        "schema_version": "1.0", "task_id": TASK_ID,
        "status": "PASS" if runtime_budget_pass else "FAIL",
        "all_pass": runtime_budget_pass,
        "duration_seconds": validation_wall_clock_seconds,
        "validation_wall_clock_seconds": validation_wall_clock_seconds,
        "notebook_wall_clock_started_at": "BOOTSTRAP_FIRST_CODE_CELL",
        "validation_within_budget": validation_within_budget,
        "validation_wall_clock_budget_seconds": validation_limit_seconds,
        "wall_clock_guard": {
            "deadline_origin": "BOOTSTRAP_FIRST_CODE_CELL",
            "hard_stop_seconds": validation_hard_stop_seconds,
            "receipt_reserve_seconds": receipt_reserve_seconds,
            "deadline_monotonic_shared_across_cells": True,
            "covered_stages": "BOOTSTRAP_THROUGH_FINAL_RECEIPTS_INCLUDING_DEPENDENCY_PATCH_AND_SCORER",
            "deadline_enforced_in_predictor_and_per_sample_loops": True,
            "eta_estimates": progress_eta_rows,
        },
        "production_safety": {
            "wall_clock_seconds": production_reference_seconds,
            "within_budget": production_within_budget,
            "basis": production_runtime_basis,
            "interpretation": (
                "historical full V19C production-cell wall clock is within the frozen limit; "
                "the future production notebook must still enforce its own 2700-second hard gate"
            ),
        },
        "baseline_reproduction": {
            "status": "PASS",
            "scope": "R70 same-raw and fresh full-vs-cache anchor equivalence plus two-run determinism",
        },
        "streaming_strategy": {
            "cache_storage": "DISK_BACKED_ONE_SAMPLE_RESIDENT",
            "loop_order": "SAMPLE_OUTER_ARM_INNER",
            "validation_rows": "STREAMED_DIRECTLY_TO_THREE_CSV_WRITERS",
            "mutable_graph_or_stats_shared_between_arms": False,
            "per_sample_frame_and_deepcenter_read_cache_shared_between_arms": False,
            "per_arm_frame_and_deepcenter_cache_policy": "FRESH_EMPTY_PER_SAMPLE_PER_ARM",
        },
        "scoring_semantics": {
            "status": "PASS", "all_pass": scoring_semantics_pass,
            "coordinate_semantics": "ROUNDED_CLAMPED_SUBMISSION_ROWS",
            "graph_reconstruction": "ORIGINAL_NODE_IDS_AND_EDGES_FROM_VALIDATION_ROWS",
            "per_sample_crosscheck": "scorer_input_rows_sha256_equals_final_output_sha256",
            "row_count": len(metrics_rows),
        },
        "runtime_tie_break": {
            "field": "runtime_seconds",
            "definition": "PURE_V20B_FINALIZE_FROM_PREDIVISION_SECONDS_EXCLUDES_SCORER_AND_ROW_AUDIT",
            "runtime_seconds_equals_finalize_runtime_seconds": all(
                row["runtime_seconds"] == row["finalize_runtime_seconds"] for row in metrics_rows
            ),
            "arm_order_policy": "ROTATE_BY_SAMPLE_INDEX_MOD_3",
            "execution_order_position_counts": arm_order_position_counts,
        },
        "runtime_identity_evidence": identity_evidence,
        "runtime_identity_evidence_sha256": canonical_sha256(identity_evidence),
        "peak_gpu_memory_mib": memory_sampler.peak_gpu_mib,
        "peak_process_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0,
        "peak_child_rss_mib": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024.0,
        "per_sample_peak_memory_semantics": (
            "MAX_OF_SAMPLE_SCOPED_GPU_MEMORY_USED_AND_PROCESS_CURRENT_RSS_POLLED_AT_0_25_SECONDS"
        ),
        "stages": runtime_stages,
        "cell_stage_rows": V20B_CELL_STAGE_ROWS,
        "arms": {arm: {
            "downstream_seconds": arm_runtime[arm],
            "finalize_seconds": arm_runtime[arm],
            "scoring_seconds": arm_scoring_runtime[arm],
            "total_sample_processing_seconds": arm_total_runtime[arm],
        } for arm in ARMS},
        "predictor_run_count": V20B_PREDICTOR_RUNS_STARTED,
        "predictor_runs_started": V20B_PREDICTOR_RUNS_STARTED,
        "predictor_run_count_semantics": "LOGICAL_RUN_COUNT_INCREMENTED_BEFORE_FIRST_SUBPROCESS_START",
        "predictor_run_start_events": V20B_PREDICTOR_RUN_START_EVENTS,
        "full_199_predictor_run_count": 1,
        "anchor_predictor_run_count": 2, "retry_count": 0,
        "test_inference_count": 0, "competition_submission_count": 0,
        "cache_manifest_sha256": cache_object["manifest_sha256"],
        "cache_equivalence_sha256": sha256_file(OUTPUT_ROOT / "cache_equivalence.json"),
        "runtime_determinism_sha256": sha256_file(OUTPUT_ROOT / "runtime_determinism.json"),
        "anchors": anchors,
        "anchor_rows": {
            "cache_equivalence": equivalence_rows,
            "runtime_determinism": determinism_rows,
        },
    })

    runtime_stage = "PROMOTION_DECISION"
    tol = FROZEN_CONTRACT["experiment_freeze"]["comparison_tolerances"]
    candidate_gates = {}
    candidate_details = {}
    passing = []
    for candidate in ("R80", "R90"):
        embryo_deltas = {embryo: aggregate_map[candidate][embryo]["official_score"] - aggregate_map["R70"][embryo]["official_score"]
                          for embryo in ("44b6", "6bba")}
        div_deltas = {embryo: aggregate_map[candidate][embryo]["division_jaccard"] - aggregate_map["R70"][embryo]["division_jaccard"]
                      for embryo in ("44b6", "6bba")}
        macro_delta = aggregate_map[candidate]["EMBRYO_EQUAL_MACRO"]["official_score"] - aggregate_map["R70"]["EMBRYO_EQUAL_MACRO"]["official_score"]
        pooled_delta = aggregate_map[candidate]["POOLED_MICRO"]["official_score"] - aggregate_map["R70"]["POOLED_MICRO"]["official_score"]
        pooled_div_delta = aggregate_map[candidate]["POOLED_MICRO"]["division_jaccard"] - aggregate_map["R70"]["POOLED_MICRO"]["division_jaccard"]
        pooled_candidate = aggregate_map[candidate]["POOLED_MICRO"]
        pooled_control = aggregate_map["R70"]["POOLED_MICRO"]
        div_tp_delta = pooled_candidate["division_tp"] - pooled_control["division_tp"]
        div_fp_delta = pooled_candidate["division_fp"] - pooled_control["division_fp"]
        fp_compensated = div_fp_delta <= 0 or (
            div_tp_delta > 0 and pooled_delta > tol["strict_positive_epsilon"]
        )
        positive_samples = sum(row["candidate_arm"] == candidate and row["official_score_delta"] > tol["strict_positive_epsilon"]
                               for row in sample_delta_rows)
        gates = {
            "each_embryo_official_noninferior": all(value >= -tol["reported_score_absolute"] for value in embryo_deltas.values()),
            "at_least_one_embryo_strictly_improves": any(value > tol["strict_positive_epsilon"] for value in embryo_deltas.values()),
            "embryo_equal_macro_strictly_improves": macro_delta > tol["strict_positive_epsilon"],
            "pooled_micro_official_noninferior": pooled_delta >= -tol["reported_score_absolute"],
            "pooled_division_jaccard_strictly_improves": pooled_div_delta > tol["strict_positive_epsilon"],
            "no_embryo_material_division_jaccard_decline": all(value >= -tol["material_embryo_division_jaccard_drop"] for value in div_deltas.values()),
            "division_fp_increase_compensated": fp_compensated,
            "topology_and_schema_all_pass": all(row["topology_valid"] and row["schema_valid"] for row in topology_rows),
            "cap_saturation_not_materially_worse": all(
                max(aggregate_map[candidate][embryo]["frame_cap_saturation"],
                    aggregate_map[candidate][embryo]["global_cap_saturation"])
                - max(aggregate_map["R70"][embryo]["frame_cap_saturation"],
                      aggregate_map["R70"][embryo]["global_cap_saturation"])
                <= tol["material_frame_cap_saturation_rate_increase"]
                for embryo in ("44b6", "6bba")),
            "node_count_penalty_no_unexplained_degradation": (
                aggregate_map[candidate]["EMBRYO_EQUAL_MACRO"]["node_count_penalty"]
                <= aggregate_map["R70"]["EMBRYO_EQUAL_MACRO"]["node_count_penalty"]
                   + tol["reported_score_absolute"]),
            "benefit_not_entirely_one_sample": positive_samples >= 2,
            "identity_and_shared_cache_match": identity_gate_pass,
            "only_parent_radius_differs": resolved_config_checker_pass,
            "runtime_within_frozen_budget": runtime_budget_pass,
        }
        candidate_gates[candidate] = {**gates, "eligible": all(gates.values())}
        candidate_details[candidate] = {
            "embryo_official_deltas": embryo_deltas,
            "embryo_division_jaccard_deltas": div_deltas,
            "macro_delta": macro_delta, "pooled_delta": pooled_delta,
            "pooled_division_delta": pooled_div_delta,
            "division_tp_delta": div_tp_delta, "division_fp_delta": div_fp_delta,
            "positive_sample_count": positive_samples,
        }
        if candidate_gates[candidate]["eligible"]:
            passing.append(candidate)
    selected = None
    tie_vectors = {}
    if len(passing) == 1:
        selected = passing[0]
    elif len(passing) == 2:
        def tie_vector(arm):
            deltas = candidate_details[arm]["embryo_official_deltas"]
            pooled = aggregate_map[arm]["POOLED_MICRO"]
            control = aggregate_map["R70"]["POOLED_MICRO"]
            return (min(deltas.values()), candidate_details[arm]["macro_delta"],
                    candidate_details[arm]["pooled_delta"], pooled["division_jaccard"],
                    -(pooled["division_fp"] - control["division_fp"]),
                    -max(pooled["frame_cap_saturation"], pooled["global_cap_saturation"]),
                    -pooled["runtime_seconds"])
        tie_vectors = {arm: list(tie_vector(arm)) for arm in passing}
        for index in range(len(tie_vectors["R80"])):
            if abs(tie_vectors["R80"][index] - tie_vectors["R90"][index]) <= tol["strict_positive_epsilon"]:
                continue
            selected = "R80" if tie_vectors["R80"][index] > tie_vectors["R90"][index] else "R90"
            break
    if selected:
        decision_code = f"PROMOTE_{selected}_FOR_KAGGLE_TEST"
    elif len(passing) == 2:
        decision_code = "NO_UNIQUE_WINNER_NO_SUBMISSION"
    else:
        decision_code = "NO_PROMOTION_KEEP_V19C_R70"
    promotion = {"schema_version": "1.0", "task_id": TASK_ID,
                 "screen": "TWO_EMBRYO_PAIRED_SENSITIVITY_SCREEN",
                 "decision": decision_code, "selected_arm": selected,
                 "selected_radius_um": ARMS[selected] if selected else None,
                 "candidate_label": "Kaggle test candidate" if selected else None,
                 "candidate_gates": candidate_gates, "passing_candidates": passing,
                 "candidate_details": candidate_details,
                 "tie_break": {
                     "order": FROZEN_CONTRACT["experiment_freeze"]["promotion_rule"]["tie_break_order"],
                     "vectors": tie_vectors, "unique_winner": selected,
                 },
                 "cache_equivalence_pass": True, "runtime_determinism_pass": True,
                 "checkpoint_overlap_status": "CHECKPOINT_TRAINING_OVERLAP_UNKNOWN",
                 "competition_submission_created": False, "retry_count": 0,
                 "validation_script_version_id": os.environ.get("KAGGLE_SCRIPT_VERSION_ID") or None,
                 "runtime_identity_evidence_sha256": canonical_sha256(identity_evidence),
                 "identity_bindings": {
                     "base_source_sha256": frozen_identities["base_source_sha256"],
                     "contract_canonical_sha256": canonical_sha256(FROZEN_CONTRACT),
                     "contract_file_sha256": BUILDER_MANIFEST["inputs"]["contract_file_sha256"],
                     "sample_manifest_canonical_sha256": canonical_sha256(FROZEN_SAMPLE_MANIFEST),
                     "sample_manifest_file_sha256": BUILDER_MANIFEST["inputs"]["sample_manifest_file_sha256"],
                     "production_runtime_basis_sha256": canonical_sha256(production_runtime_basis),
                     "cache_manifest_file_sha256": sha256_file(OUTPUT_ROOT / "cache_manifest.json"),
                     "cache_manifest_sha256": cache_object["manifest_sha256"],
                     "per_sample_metrics_sha256": sha256_file(OUTPUT_ROOT / "per_sample_metrics.csv"),
                     "per_embryo_metrics_sha256": sha256_file(OUTPUT_ROOT / "per_embryo_metrics.csv"),
                     "resolved_config_verification_sha256": sha256_file(OUTPUT_ROOT / "resolved_config_verification.json"),
                     "cache_equivalence_sha256": sha256_file(OUTPUT_ROOT / "cache_equivalence.json"),
                     "runtime_determinism_sha256": sha256_file(OUTPUT_ROOT / "runtime_determinism.json"),
                 },
                 "evidence_hashes": {
                     "experiments/V20B/full_sample_payload_inventory.csv": sha256_file(OUTPUT_ROOT / "full_sample_payload_inventory.csv"),
                     "experiments/V20B/full_sample_manifest.json": sha256_file(OUTPUT_ROOT / "full_sample_manifest.json"),
                     "experiments/V20B/per_sample_metrics.csv": sha256_file(OUTPUT_ROOT / "per_sample_metrics.csv"),
                     "experiments/V20B/per_embryo_metrics.csv": sha256_file(OUTPUT_ROOT / "per_embryo_metrics.csv"),
                     "experiments/V20B/paired_deltas_by_sample.csv": sha256_file(OUTPUT_ROOT / "paired_deltas_by_sample.csv"),
                     "experiments/V20B/paired_deltas_by_embryo.csv": sha256_file(OUTPUT_ROOT / "paired_deltas_by_embryo.csv"),
                     "experiments/V20B/micro_macro_comparison.csv": sha256_file(OUTPUT_ROOT / "micro_macro_comparison.csv"),
                     "experiments/V20B/division_confusion_by_embryo.json": sha256_file(OUTPUT_ROOT / "division_confusion_by_embryo.json"),
                     "experiments/V20B/topology_validation.json": sha256_file(OUTPUT_ROOT / "topology_validation.json"),
                     "experiments/V20B/runtime_receipts.json": sha256_file(OUTPUT_ROOT / "runtime_receipts.json"),
                     "experiments/V20B/cache_manifest.json": sha256_file(OUTPUT_ROOT / "cache_manifest.json"),
                     "experiments/V20B/cache_equivalence.json": sha256_file(OUTPUT_ROOT / "cache_equivalence.json"),
                     "experiments/V20B/runtime_determinism.json": sha256_file(OUTPUT_ROOT / "runtime_determinism.json"),
                     "experiments/V20B/resolved_config_verification.json": sha256_file(OUTPUT_ROOT / "resolved_config_verification.json"),
                 },
                 "note": "Offline two-embryo sensitivity screen; not CV and not hidden-test improvement proof."}
    write_json(OUTPUT_ROOT / "promotion_decision.json", promotion)
    final_manifest = emit_artifact_manifest("COMPLETE_VALIDATION_OUTPUTS")
    print(json.dumps({"V20B_VALIDATION_COMPLETE": True, "decision": decision_code,
                      "selected_radius_um": promotion["selected_radius_um"],
                      "artifact_count": final_manifest["artifact_count"]}, sort_keys=True))
except Exception as exc:
    emit_failure(exc)
    print("V20B_FAIL_CLOSED", type(exc).__name__, str(exc))
    traceback.print_exc()
    raise
'''


RUNTIME_PARAMETER_EXPRESSIONS = {
    "adaptive_short_track_rescue": "bool(ADAPTIVE_SHORT_TRACK_RESCUE)",
    "allow_artifact_fallback": "bool(ALLOW_ARTIFACT_FALLBACK)",
    "bidirectional_weight": "float(os.environ['BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT'])",
    "deepcenter_enabled": "bool(USE_DEEPCENTER_VETO)",
    "deepcenter_expected_epoch": "int(DEEPCENTER_EXPECTED_EPOCH)",
    "deepcenter_gap_confirm_min_span_um": "float(DEEPCENTER_GAP_CONFIRM_MIN_SPAN_UM)",
    "deepcenter_gap_threshold": "float(DEEPCENTER_GAP_THRESHOLD)",
    "deepcenter_gap_veto": "bool(DEEPCENTER_GAP_VETO)",
    "deepcenter_required": "bool(REQUIRE_DEEPCENTER_VETO)",
    "deepcenter_safe_div_threshold": "float(DEEPCENTER_SAFE_DIV_THRESHOLD)",
    "deepcenter_safe_div_veto": "bool(DEEPCENTER_SAFE_DIV_VETO)",
    "detector_threshold": "float(DET_THRESHOLD)",
    "division_drop_to_single_if_bad": "bool(DIV_DROP_TO_SINGLE_IF_BAD)",
    "division_geometry_parent_max_um": "float(DIV_PARENT_MAX_UM)",
    "division_geometry_sister_max_um": "float(DIV_SISTER_MAX_UM)",
    "edge_threshold": "float(os.environ['BIOHUB_DUAL_SEED_EDGE_THRESHOLD'])",
    "fusion_mode": "str(os.environ['BIOHUB_BIDIRECTIONAL_FUSION_MODE'])",
    "gap2_frame_frac_cap": "float(GAP2_FRAME_FRAC_CAP)",
    "gap2_max_links_abs": "int(GAP2_MAX_LINKS_ABS)",
    "gap2_max_links_frac": "float(GAP2_MAX_LINKS_FRAC)",
    "gap2_max_step_um": "float(GAP2_MAX_STEP_UM)",
    "gap2_max_total_um": "float(GAP2_MAX_TOTAL_UM)",
    "gap2_recovery": "bool(OUTPUT_GAP2_RECOVERY)",
    "gap2_require_context": "bool(GAP2_REQUIRE_CONTEXT)",
    "gap_close_distance_um": "float(GAP_CLOSE_UM)",
    "gap_close_max_added_abs": "int(GAP_CLOSE_MAX_ADDED_ABS)",
    "gap_close_max_added_frac": "float(GAP_CLOSE_MAX_ADDED_FRAC)",
    "gap_close_max_gap_configured": "int(GAP_CLOSE_MAX_GAP)",
    "gap_close_max_gap_effective": "int(min(GAP_CLOSE_MAX_GAP, 1))",
    "gap_close_reuse_existing": "bool(GAP_CLOSE_REUSE_EXISTING)",
    "gap_close_reuse_um": "float(GAP_CLOSE_REUSE_UM)",
    "gap_density_adaptive": "bool(GAP_DENSITY_ADAPTIVE)",
    "gap_density_gain": "float(GAP_DENSITY_GAIN)",
    "gap_density_max_step_delta_um": "float(GAP_DENSITY_MAX_STEP_DELTA_UM)",
    "gap_density_neighbors": "int(GAP_DENSITY_NEIGHBORS)",
    "gap_density_reference_um": "float(GAP_DENSITY_REFERENCE_UM)",
    "gap_refine_max_shift_um": "float(GAP_REFINE_MAX_SHIFT_UM)",
    "gap_refine_synthetic": "bool(GAP_REFINE_SYNTHETIC)",
    "gap_refine_win_yx": "int(GAP_REFINE_WIN_YX)",
    "gap_refine_win_z": "int(GAP_REFINE_WIN_Z)",
    "ilp_appearance_weight": "float(ILP_APPEARANCE_WEIGHT)",
    "ilp_disappearance_weight": "float(ILP_DISAPPEARANCE_WEIGHT)",
    "ilp_division_weight": "float(ILP_DIVISION_WEIGHT)",
    "ilp_edge_weight": "float(ILP_EDGE_WEIGHT)",
    "ilp_enabled": "bool(USE_ILP)",
    "minimum_track_length": "int(OUTPUT_MIN_TRACK_LEN)",
    "motion_relink_learned_bonus": "float(MOTION_RELINK_LEARNED_BONUS)",
    "motion_relink_max_frame_nodes": "int(MOTION_RELINK_MAX_FRAME_NODES)",
    "motion_relink_relaxed_um": "float(MOTION_RELINK_RELAXED_UM)",
    "motion_relink_tight_um": "float(MOTION_RELINK_TIGHT_UM)",
    "motion_relink_velocity_weight": "float(MOTION_RELINK_VELOCITY_WEIGHT)",
    "output_division_geometry_filter": "bool(OUTPUT_DIVISION_GEOMETRY_FILTER)",
    "output_edge_max_um": "float(OUTPUT_EDGE_MAX_UM)",
    "output_enforce_next_frame": "bool(OUTPUT_ENFORCE_NEXT_FRAME)",
    "output_filter_short_tracks": "bool(OUTPUT_FILTER_SHORT_TRACKS)",
    "output_keep_division_components": "bool(OUTPUT_KEEP_DIVISION_COMPONENTS)",
    "output_linefit_smooth": "bool(OUTPUT_LINEFIT_SMOOTH)",
    "output_linefit_weight": "float(OUTPUT_LINEFIT_WEIGHT)",
    "output_linefit_window": "int(OUTPUT_LINEFIT_WINDOW)",
    "output_motion_relink": "bool(OUTPUT_MOTION_RELINK)",
    "output_prune_isolated": "bool(OUTPUT_PRUNE_ISOLATED)",
    "output_single_child_repair": "bool(OUTPUT_SINGLE_CHILD_REPAIR)",
    "output_single_parent_repair": "bool(OUTPUT_SINGLE_PARENT_REPAIR)",
    "random_seed": "'UNKNOWN_NOT_EXPLICIT_IN_SOURCE'",
    "retention_threshold": "float(os.environ['BIOHUB_DUAL_SEED_MIN_CANDIDATE_RETENTION'])",
    "run_output_diagnostics": "bool(RUN_OUTPUT_DIAGNOSTICS)",
    "safe_div_divergence_um": "float(SAFE_DIV_DIVERGE_UM)",
    "safe_div_existing_child_max_um": "float(SAFE_DIV_EXISTING_CHILD_MAX_UM)",
    "safe_div_frame_cap": "float(SAFE_DIV_FRAME_FRAC_CAP)",
    "safe_div_global_cap": "float(SAFE_DIV_GLOBAL_FRAC_CAP)",
    "safe_div_parent_radius_um": "float(SAFE_DIV_MAX_UM)",
    "safe_div_require_divergence": "bool(SAFE_DIV_REQUIRE_DIVERGENCE)",
    "safe_div_require_mutual_nn": "bool(SAFE_DIV_REQUIRE_MUTUAL_NN)",
    "safe_div_sister_radius_um": "float(SAFE_DIV_SISTER_MAX_UM)",
    "safe_div_sister_symmetry_tau": "float(SAFE_DIV_SISTER_SYMMETRY_TAU)",
    "safe_divisions_enabled": "bool(OUTPUT_SAFE_DIVISIONS)",
    "secondary_detection_weight": "float(os.environ['BIOHUB_SECONDARY_DETECTION_WEIGHT'])",
    "secondary_edge_weight": "float(os.environ['BIOHUB_SECONDARY_EDGE_WEIGHT'])",
    "secondary_link_mode": "str(os.environ['BIOHUB_SECONDARY_LINK_MODE'])",
    "secondary_low_margin_max": "float(os.environ['BIOHUB_SECONDARY_LOW_MARGIN_MAX'])",
    "secondary_mix_temperature": "float(os.environ['BIOHUB_SECONDARY_MIX_TEMPERATURE'])",
    "short_track_rescue_max_mean_edge_dist_um": "float(SHORT_TRACK_RESCUE_MAX_MEAN_EDGE_DIST_UM)",
    "short_track_rescue_max_nodes_abs": "int(SHORT_TRACK_RESCUE_MAX_NODES_ABS)",
    "short_track_rescue_max_nodes_frac": "float(SHORT_TRACK_RESCUE_MAX_NODES_FRAC)",
    "short_track_rescue_min_len": "int(SHORT_TRACK_RESCUE_MIN_LEN)",
    "short_track_rescue_min_mean_edge_prob": "float(SHORT_TRACK_RESCUE_MIN_MEAN_EDGE_PROB)",
    "short_track_rescue_trigger_removed_frac": "float(SHORT_TRACK_RESCUE_TRIGGER_REMOVED_FRAC)",
    "unet_batch_size": "int(UNET_BATCH_SIZE)",
}


def render_runtime_bootstrap(
    contract: dict[str, Any],
    sample_manifest: dict[str, Any],
    scorer_sources: dict[str, str],
    checker_bytes: bytes,
    partial_manifest: dict[str, Any],
) -> str:
    encoded_scorer = {
        relative: base64.b64encode(source.encode("utf-8")).decode("ascii")
        for relative, source in scorer_sources.items()
    }
    replacements = {
        "__V20B_CONTRACT_JSON__": repr(json.dumps(contract, ensure_ascii=False, sort_keys=True)),
        "__V20B_SAMPLE_JSON__": repr(json.dumps(sample_manifest, ensure_ascii=False, sort_keys=True)),
        "__V20B_SCORER_JSON__": repr(json.dumps(encoded_scorer, sort_keys=True)),
        "__V20B_CHECKER_B64__": repr(base64.b64encode(checker_bytes).decode("ascii")),
        "__V20B_BUILDER_MANIFEST_JSON__": repr(json.dumps(partial_manifest, ensure_ascii=False, sort_keys=True)),
    }
    source = RUNTIME_BOOTSTRAP
    for marker, value in replacements.items():
        source = source.replace(marker, value)
    return source


def render_experiment(contract: dict[str, Any]) -> str:
    frozen_keys = set(contract["experiment_freeze"]["active_parameters"])
    mapping_keys = set(RUNTIME_PARAMETER_EXPRESSIONS)
    if frozen_keys != mapping_keys:
        raise BuildError(
            "runtime parameter mapping differs from contract: "
            f"missing={sorted(frozen_keys - mapping_keys)}, extra={sorted(mapping_keys - frozen_keys)}"
        )
    lines = "\n".join(
        f"        {key!r}: {RUNTIME_PARAMETER_EXPRESSIONS[key]},"
        for key in sorted(RUNTIME_PARAMETER_EXPRESSIONS)
    )
    replacements = {
        "__V20B_RUNTIME_PARAMETER_LINES__": lines,
        "__V20B_PAYLOAD_COLUMNS__": repr(CSV_SCHEMAS["full_sample_payload_inventory.csv"]),
        "__V20B_SAMPLE_COLUMNS__": repr(CSV_SCHEMAS["per_sample_metrics.csv"]),
        "__V20B_EMBRYO_COLUMNS__": repr(CSV_SCHEMAS["per_embryo_metrics.csv"]),
        "__V20B_SAMPLE_DELTA_COLUMNS__": repr(CSV_SCHEMAS["paired_deltas_by_sample.csv"]),
        "__V20B_EMBRYO_DELTA_COLUMNS__": repr(CSV_SCHEMAS["paired_deltas_by_embryo.csv"]),
        "__V20B_MICRO_MACRO_COLUMNS__": repr(CSV_SCHEMAS["micro_macro_comparison.csv"]),
    }
    source = RUNTIME_EXPERIMENT
    for marker, value in replacements.items():
        source = source.replace(marker, value)
    return source


def build_notebook(
    source_notebook: dict[str, Any],
    sources: dict[int, str],
    contract: dict[str, Any],
    sample_manifest: dict[str, Any],
    scorer_sources: dict[str, str],
    checker_bytes: bytes,
    kernel_slug: str,
    contract_file_sha256: str,
    sample_manifest_file_sha256: str,
    builder_script_sha256: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    env_source = sources[2].replace(
        "harmonic_association_production", "v20b_validation_shared_cache"
    ).replace(
        "v19c reported LB 0.939 sister separation radius 14um arm",
        "V20B TWO_EMBRYO_PAIRED_SENSITIVITY_SCREEN validation only",
    )
    config_source = exact_replace(
        sources[4],
        '# Hard-bound production input: competition test images only.\nTEST_DIR = COMP_DIR / "test"',
        '# V20B validation-only mount. Inherited read_test_frame resolves TEST_DIR; alias it to train.\n'
        'TRAIN_DIR = COMP_DIR / "train"\nTEST_DIR = TRAIN_DIR',
        "replace production input with labeled train",
    )
    config_source = exact_replace(
        config_source,
        'SUBMISSION_PATH = WORKING_DIR / "submission.csv"\n',
        '',
        "remove production submission path",
    )
    config_source = config_source.replace(
        'print("Biohub learned UNet + node-transformer + ILP submission")',
        'print("Biohub V20B validation-only UNet + node-transformer + ILP")',
    ).replace(
        'print("TEST_DIR:", TEST_DIR, "exists:", TEST_DIR.exists())',
        'print("TRAIN_DIR:", TRAIN_DIR, "exists:", TRAIN_DIR.exists())',
    )
    dependency_source = sources[5].replace(
        "bidirectional_production_runtime_integrity.json",
        "v20b_validation_runtime_integrity.json",
    )
    inference_marker = "\ndef list_test_stems() -> list[str]:"
    if sources[6].count(inference_marker) != 1:
        raise BuildError("cannot isolate V19C predictor patch from production test execution")
    predictor_patch_source = sources[6].split(inference_marker, 1)[0]
    post_marker = "\nDEEPCENTER_VETO_DETECTOR = load_deepcenter_veto_detector()"
    if sources[7].count(post_marker) != 1:
        raise BuildError("cannot isolate V19C postprocess definitions from production execution")
    postprocess_definitions = sources[7].split(post_marker, 1)[0]
    cache_functions = derive_cache_functions(sources[7])
    frozen_pinned_dataset_sources = pinned_dataset_sources(contract)

    partial_manifest = {
        "schema_version": "1.0",
        "task_id": TASK_ID,
        "execution_status": "NOT_RUN",
        "inputs": {
            "v19c_source_sha256": SOURCE_SHA256,
            "contract_sha256": canonical_sha256(contract),
            "contract_file_sha256": contract_file_sha256,
            "sample_manifest_sha256": canonical_sha256(sample_manifest),
            "sample_manifest_file_sha256": sample_manifest_file_sha256,
            "v19c_historical_production_runtime": v19c_historical_production_runtime(source_notebook),
            "scorer_commit": SCORER_COMMIT,
            "scorer_files": SCORER_FILES,
            "resolved_config_checker_sha256": sha256_bytes(checker_bytes),
            "builder_script_sha256": builder_script_sha256,
            "kernel_dataset_sources_version_pinned": frozen_pinned_dataset_sources,
        },
        "transformations": [
            "removed V19C production test enumeration/predictor execution",
            "removed V19C submission writer and production manifest cells",
            "aliased inherited raw-frame reader to competition train only",
            "mechanically split filter_output_graph after gap2 and before add_safe_divisions_postlink",
            "embedded exact official scorer metrics/division/evaluate sources",
        ],
        "runtime_invariants": {
            "validation_only": True,
            "production_test_inference": False,
            "submission_csv": False,
            "all_199_payload_preflight_before_predictor": True,
            "full_199_upstream_predictor_runs": 1,
            "shared_post_gap2_cache": True,
            "disk_backed_sample_outer_cache_streaming": True,
            "validation_rows_streamed_to_disk": True,
            "required_cuda_device_count": 2,
            "kernel_dataset_sources_explicit_version_pins": True,
            "wall_clock_fail_closed_reserve_seconds": 300,
            "wall_clock_origin": "BOOTSTRAP_FIRST_CODE_CELL",
            "post_bootstrap_cells_fail_closed_wrapped": True,
            "bootstrap_failure_receipt_scope": (
                "Best effort begins after bootstrap establishes OUTPUT_ROOT and receipt helpers; "
                "a failure before that initialization cannot be persisted by notebook code."
            ),
            "anchor_count": 2,
            "anchor_full_runs_all_arms": True,
            "r70_anchor_upstream_repetitions": 2,
            "automatic_retry": False,
        },
        "output_contract": {"required_files": REQUIRED_OUTPUTS, "csv_columns": CSV_SCHEMAS},
    }
    bootstrap = render_runtime_bootstrap(
        contract, sample_manifest, scorer_sources, checker_bytes, partial_manifest
    )
    experiment = render_experiment(contract)
    helper_source = "import base64\n" + RUNTIME_SCORER_AND_HELPERS
    cells = [
        markdown_cell(
            "# Biohub V20B — private two-embryo paired radius validation\n\n"
            "Validation only. This notebook reads all 199 labeled train payloads, runs one "
            "shared full upstream pass, branches R70/R80/R90 after gap2, verifies two "
            "non-test-copy anchors, and never reads production test or creates a competition submission file.",
            "v20b-title",
        ),
        code_cell(bootstrap, "v20b-frozen-bootstrap"),
        code_cell(wrap_runtime_cell(env_source, "ENVIRONMENT"), "v20b-v19c-environment"),
        code_cell(wrap_runtime_cell(config_source, "RUNTIME_CONFIG"), "v20b-v19c-runtime-config"),
        code_cell(wrap_runtime_cell(dependency_source, "DEPENDENCIES_AND_IDENTITIES"), "v20b-v19c-dependencies-and-identities"),
        code_cell(wrap_runtime_cell(predictor_patch_source, "PREDICTOR_PATCHES"), "v20b-v19c-predictor-patches-only"),
        code_cell(wrap_runtime_cell(
            postprocess_definitions + "\n\n" + cache_functions,
            "POSTPROCESS_AND_CACHE_BOUNDARY",
        ), "v20b-v19c-postprocess-and-cache-boundary"),
        code_cell(wrap_runtime_cell(helper_source, "OFFICIAL_SCORER_AND_HELPERS"), "v20b-official-scorer-and-runtime-helpers"),
        code_cell(experiment, "v20b-validation-experiment"),
    ]
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.12"},
            "kaggle": {"title": "Biohub V20B Two Embryo Radius Validation"},
            "v20b": partial_manifest,
        },
        "nbformat": 4,
        "nbformat_minor": 4,
    }
    # Static compile is intentionally per-cell, matching notebook execution semantics.
    for index, cell in enumerate(cells):
        if cell["cell_type"] == "code":
            compile(cell["source"], f"<v20b-cell-{index}>", "exec")
    forbidden = [
        'COMP_DIR / "test"', "SUBMISSION_PATH", "kaggle competitions submit",
        "kaggle api kernels push", "SaveKernel", "retry(",
    ]
    joined = "\n".join(cell["source"] for cell in cells)
    findings = [token for token in forbidden if token in joined]
    if findings:
        raise BuildError(f"generated validation notebook contains forbidden production tokens: {findings}")
    return notebook, partial_manifest


def kernel_metadata(kernel_slug: str, notebook_name: str, contract: dict[str, Any]) -> dict[str, Any]:
    if "/" not in kernel_slug or kernel_slug.startswith("/") or kernel_slug.endswith("/"):
        raise BuildError("--kernel-slug must be owner/slug")
    dataset_sources = pinned_dataset_sources(contract)
    return {
        "id": kernel_slug,
        "title": "Biohub V20B Two Embryo Radius Validation",
        "code_file": notebook_name,
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": False,
        "keywords": ["gpu"],
        "dataset_sources": dataset_sources,
        "competition_sources": ["biohub-cell-tracking-during-development"],
        "kernel_sources": [],
        "model_sources": [],
        "docker_image": "gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461",
        "machine_shape": "NvidiaTeslaT4",
    }


def write_bundle(
    output_dir: Path,
    notebook: dict[str, Any],
    partial_manifest: dict[str, Any],
    metadata: dict[str, Any],
    notebook_name: str,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.iterdir()):
        raise BuildError(f"output directory must be empty: {output_dir}")
    notebook_path = output_dir / notebook_name
    metadata_path = output_dir / "kernel-metadata.json"
    manifest_path = output_dir / "build_manifest.json"
    notebook_path.write_bytes(json.dumps(notebook, ensure_ascii=False, indent=1).encode("utf-8") + b"\n")
    metadata_path.write_bytes(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n")
    final_manifest = copy.deepcopy(partial_manifest)
    final_manifest["build_status"] = "BUILT_STATICALLY_VERIFIED_NOT_EXECUTED"
    final_manifest["outputs"] = {
        notebook_name: {"sha256": sha256_file(notebook_path), "bytes": notebook_path.stat().st_size},
        "kernel-metadata.json": {"sha256": sha256_file(metadata_path), "bytes": metadata_path.stat().st_size},
    }
    final_manifest["external_actions"] = {
        "kaggle_read": 0, "kaggle_write": 0, "git_write": 0,
        "network_access": 0, "inference_runs": 0,
    }
    manifest_path.write_bytes(json.dumps(final_manifest, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n")
    return final_manifest


def self_test() -> None:
    assert sha256_bytes(canonical_bytes({"b": 2, "a": 1})) == sha256_bytes(b'{"a":1,"b":2}\n')
    synthetic = """
def filter_output_graph(nodes_by_id, raw_edges, dataset=None, deepcenter_bundle=None):
    stats = {'raw_edges': len(raw_edges)}
    edges = list(raw_edges)
    repair_frame_cache = {}
    deepcenter_heatmap_cache = {}
    nodes_by_id, edges = recover_strict_gap2(nodes_by_id, edges, stats, dataset=dataset)
    edges = add_safe_divisions_postlink(nodes_by_id, edges, stats, dataset=dataset,
        deepcenter_bundle=deepcenter_bundle, frame_cache=repair_frame_cache,
        deepcenter_cache=deepcenter_heatmap_cache)
    return nodes_by_id, edges, stats
"""
    derived = derive_cache_functions(synthetic)
    assert "v20b_prepare_predivision_state" in derived
    assert "v20b_finalize_from_predivision" in derived
    compile(RUNTIME_SCORER_AND_HELPERS, "<runtime-helpers-self-test>", "exec")
    for name, columns in CSV_SCHEMAS.items():
        if len(columns) != len(set(columns)):
            raise BuildError(f"duplicate CSV column in {name}")
    if set(ARMS) != {"R70", "R80", "R90"} or len(REQUIRED_OUTPUTS) != len(set(REQUIRED_OUTPUTS)):
        raise BuildError("frozen builder constants are inconsistent")
    required_runtime_fragments = (
        "STRICT_199_OF_199_FAIL_CLOSED",
        "DISK_BACKED_ONE_SAMPLE_RESIDENT",
        "validation_writers[arm].writerow(output_row)",
        "record_progress_eta(",
        "validation_deadline_monotonic",
        "v20b_add_safe_divisions_with_receipt",
        "all_three_arm_fresh_full_vs_cache_pass",
        '"cuda_device_count": int(_torch.cuda.device_count())',
        '"evidence_hashes": {',
        "PASS_VERSION_PINNED_AND_CRITICAL_CONTENT_VERIFIED",
        "FRESH_EMPTY_PER_SAMPLE_PER_ARM",
        "sample_memory_sampler.peak_process_rss_mib",
        '"gt_node_count_evidence"',
    )
    missing_fragments = [value for value in required_runtime_fragments if value not in RUNTIME_EXPERIMENT]
    if missing_fragments:
        raise BuildError(f"runtime safety fragments missing: {missing_fragments}")
    if "score_graph_was_matched" not in RUNTIME_SCORER_AND_HELPERS:
        raise BuildError("zero-edge official-score diagnostic guard is missing")
    prohibited_runtime_fragments = (
        "cache_payloads = {}", "arm_validation_rows", "531.0785155296325",
    )
    present_prohibited = [value for value in prohibited_runtime_fragments if value in RUNTIME_EXPERIMENT]
    if present_prohibited:
        raise BuildError(f"memory/runtime anti-patterns present: {present_prohibited}")
    print("V20B_VALIDATION_NOTEBOOK_BUILDER_SELF_TEST_PASS")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-ipynb", type=Path)
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--sample-manifest", type=Path)
    parser.add_argument("--scorer-root", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--kernel-slug", default="sailorren/biohub-v20b-two-embryo-radius-validation")
    parser.add_argument("--notebook-name", default="v20b_validation.ipynb")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.self_test:
        self_test()
        return 0
    required = {
        "--source-ipynb": args.source_ipynb,
        "--contract": args.contract,
        "--sample-manifest": args.sample_manifest,
        "--scorer-root": args.scorer_root,
    }
    missing = [name for name, value in required.items() if value is None]
    if missing:
        raise BuildError("missing required arguments: " + ", ".join(missing))
    source_notebook, sources = validate_source(args.source_ipynb)
    contract = load_json_object(args.contract, "V20B contract")
    sample_manifest = load_json_object(args.sample_manifest, "V20B sample manifest")
    validate_contract_and_samples(contract, sample_manifest)
    scorer_sources = read_scorer_sources(args.scorer_root)
    checker_path = args.contract.parent / "verify_resolved_config.py"
    if not checker_path.is_file():
        raise BuildError(f"resolved-config checker not found beside contract: {checker_path}")
    checker_bytes = checker_path.read_bytes()
    compile(checker_bytes, str(checker_path), "exec")
    notebook, partial_manifest = build_notebook(
        source_notebook, sources, contract, sample_manifest, scorer_sources,
        checker_bytes, args.kernel_slug,
        sha256_file(args.contract), sha256_file(args.sample_manifest),
        sha256_file(Path(__file__)),
    )
    if args.validate_only:
        print(json.dumps({
            "status": "VALIDATED_NOT_WRITTEN", "task_id": TASK_ID,
            "v19c_source_sha256": SOURCE_SHA256, "scorer_commit": SCORER_COMMIT,
            "code_cell_count": sum(cell["cell_type"] == "code" for cell in notebook["cells"]),
            "required_runtime_outputs": REQUIRED_OUTPUTS,
        }, ensure_ascii=False, sort_keys=True))
        print("V20B_VALIDATION_NOTEBOOK_INPUTS_PASS")
        return 0
    if args.output_dir is None:
        raise BuildError("--output-dir is required unless --validate-only is used")
    metadata = kernel_metadata(args.kernel_slug, args.notebook_name, contract)
    manifest = write_bundle(args.output_dir, notebook, partial_manifest, metadata, args.notebook_name)
    print(json.dumps({
        "status": manifest["build_status"], "output_dir": str(args.output_dir),
        "notebook_sha256": manifest["outputs"][args.notebook_name]["sha256"],
        "kernel_metadata_sha256": manifest["outputs"]["kernel-metadata.json"]["sha256"],
        "execution_status": "NOT_RUN", "external_writes": 0,
    }, ensure_ascii=False, sort_keys=True))
    print("V20B_VALIDATION_NOTEBOOK_BUILD_PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BuildError as exc:
        print(f"V20B_VALIDATION_NOTEBOOK_BUILD_FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
