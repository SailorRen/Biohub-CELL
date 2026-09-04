#!/usr/bin/env python3
"""Build the conditionally authorized private V20B production notebook.

The builder is deliberately offline: it never invokes Kaggle, Git, inference,
or a submission API.  It accepts only the byte-pinned V19C notebook, the
byte-pinned V20B contract, and a fail-closed validation promotion decision.
The generated notebook preserves every V19C source cell except the single
``BIOHUB_SAFE_DIV_MAX_UM`` literal selected by that decision, then appends an
outcome-independent runtime identity and submission topology audit.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


TASK_ID = "CODEX_20260904_BIOHUB_V20B_TWO_EMBRYO_PAIRED_RADIUS"
SCREEN_NAME = "TWO_EMBRYO_PAIRED_SENSITIVITY_SCREEN"
SOURCE_SHA256 = "92bf632410fedc9eb7e0984a20525590b5583d5abb002d8239ff65d9f51fbf57"
CONTRACT_FILE_SHA256 = "ea46844436142e61c3bc570b4e616531b69eca2cbc609935cf84ce768d41a40b"
CONTRACT_CANONICAL_SHA256 = "15c700768f9e3b8e587b80c61b51d38164f33e716ff9629e6f4379a5e92dc16b"
PRODUCTION_RUNTIME_BASIS_SHA256 = "cc5aeab06c29afcead83a6c79809d74eef061acb2060057c3f2f697f2af03e0c"
BASE_GIT_COMMIT = "48e54c543afaac8ef01b628c8833b89b4fa5d7bc"
BASE_NOTEBOOK_REF = "sailorren/biohub-v19c-public0939-sis14-only"
BASE_SCRIPT_VERSION_ID = 346969653
COMPETITION = "biohub-cell-tracking-during-development"
DEFAULT_KERNEL_SLUG = "sailorren/biohub-v20b-two-embryo-radius-production"
VALIDATION_KERNEL_SLUG = "sailorren/biohub-v20b-two-embryo-radius-validation"
DEFAULT_NOTEBOOK_NAME = "v20b_production.ipynb"
PRODUCTION_WALL_CLOCK_MAX_SECONDS = 2700
PRODUCTION_RECEIPT_RESERVE_SECONDS = 30
PRODUCTION_HARD_STOP_SECONDS = (
    PRODUCTION_WALL_CLOCK_MAX_SECONDS - PRODUCTION_RECEIPT_RESERVE_SECONDS
)
FROZEN_DOCKER_IMAGE = (
    "gcr.io/kaggle-private-byod/python@sha256:"
    "37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461"
)
FROZEN_MACHINE_SHAPE = "NvidiaTeslaT4"

PROMOTIONS = {
    "PROMOTE_R80_FOR_KAGGLE_TEST": ("R80", 8.0),
    "PROMOTE_R90_FOR_KAGGLE_TEST": ("R90", 9.0),
}
ARMS = {"R70": 7.0, "R80": 8.0, "R90": 9.0}

SOURCE_CELLS = (
    (0, "markdown", "6fbe3c4f29ec63da7b9b8c030325dc16777a56ccb77452347a7577443440c5ef"),
    (1, "markdown", "376f423e69760fabcc8f829a0e3b2ddc0fcd03ce1d3320893fc7d80ec6ba3f2b"),
    (2, "code", "d9207bf4a2fad8b113e497af12ae2042f169bf1206c972e3d2c5cc2831a5a3e9"),
    (3, "code", "99e830901eddca96d861cbf3f9ed210954e627a6d44c4668fd8b227fa5cba900"),
    (4, "code", "6c5a6e880b6879cd6b26cc9e2394ce5492a797a863fead740e0aa25c5d22d643"),
    (5, "code", "681232942fbb971dc1b999816b32c6d91da819e55d123b359b601169dd5982fb"),
    (6, "code", "2c60405c2ad411a4eaebe59defaef6a79185c3119874905edee685c264335d8b"),
    (7, "code", "a5da2a79ceb6383c66b543dd98280c83ccd3815f4becd26a4ab873ad74d82c8a"),
    (8, "code", "239f51c30606f090e1fbc939a541891cef2dbea45d7b1c4a6fef53352e94759d"),
    (9, "code", "0083b9cd0b94cabba7c28f12bf8d80f6eda4a982d1f6f44ead0975ea0de89e92"),
    (10, "code", "b5d95f2743bc317426eb4bab90da3855450a8a30902a5575e5378afefd8bca2a"),
    (11, "code", "974767da6156ddf12c5b2d1351b13658f160d0b859a36deb9614441c006537ba"),
)

EXPECTED_CHECKPOINTS = {
    "deepcenter": "8040999a92f6b7bbd98fa8cf458141e045c0f9ad7c936bdb3b18e1f7edafe2a0",
    "primary": "12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771",
    "secondary": "9bac2fa0dadc4a6fc1899e0caf187f4b553e0a7cd90ba1261a68b35ffe9e305f",
}
SUPPORT_MANIFEST_SHA256 = "978b626d1fd1e7397435a437dfe68691defe1572fc3c20e61012d7c9b52ed029"
EXPECTED_SUPPORT_FILES = {
    "scripts/augmentations.py": "13db09817bf492f8d0f710a0a4d09776320b262060167055090a303fc6057f4e",
    "scripts/dataspec.py": "e69bf952fb985477ac50ff8598a35020c95d20a035a09b81ab4056e655dd311f",
    "scripts/evaluate.py": "614813cc51c3581c6ccda4bb20725a19da8ecac4a27620654bfca58319cffa3c",
    "scripts/predict_unet_transformer.py": "c44e771ba5980b820f93091e03a303c25dfe8f3232e501f54dc9565731c234b9",
    "scripts/train_unet_transformer.py": "c4f6317736bb3bb1ec8f3f6e9a6d935a463e3f0f1f685481b2d13218d35dc9ea",
    "src/biohub_tracking/__init__.py": "26a18d8da84e40da73281a48ebc3017d847a2e57431ab63e8629d2109e6e8571",
    "src/biohub_tracking/division_metrics.py": "d1cf1e0a43009d02174f1699ce2aa28458a2220ac4b521731d3bcf31cf8c76be",
    "src/biohub_tracking/img_proc.py": "00e8ef0adc8b39f1aaaa547ea6197b906bf9e8c009e339d3e95f8f8dbf31be3f",
    "src/biohub_tracking/io.py": "efae135b088cecaab463d889f16c885ef6da3ad27b0747327d8ddc28d866b7bd",
    "src/biohub_tracking/metrics.py": "31baf45b54c78f68bab4f65dd8f4b38bca702abb644171c6df7c46cdeef55d83",
    "src/biohub_tracking/models/__init__.py": "ab7587ef79856bae50d24b62e5805092d0459ee1c586522b763f9ef70c093e1d",
    "src/biohub_tracking/models/simple_node_transformer.py": "b97209edeb03840e80d903e3e2a8c81c520641c8ef343f6ca2904d0f80db064e",
    "src/biohub_tracking/models/temporal_unet.py": "d809c35d42f504161074ddeaaa7aee5b407e5bca7f9b4e1d5f9b2ff345666cac",
}

EXPECTED_SCORER = {
    "repository": "https://github.com/royerlab/kaggle-cell-tracking-competition",
    "commit": "075fc5f5a52d11077f9dc2b074644618f26939e2",
    "metrics_sha256": "cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444",
    "division_metrics_sha256": "0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9",
    "evaluate_sha256": "03ad4049530d3682c77435194e5d921981f331df3462abcde4a7156d1a57b7d3",
}

EXPECTED_INPUT_DATASETS = [
    {
        "canonical_file_metadata_sha256": "89f363d37bb6e5e710c8aeaac32d8985f9cbc49477e156732291c238b3a5638f",
        "dataset_id": 11061989,
        "dataset_version_id": "UNKNOWN_NOT_EXPOSED_BY_LIST_API",
        "ref": "pilkwang/biohub-deepcenter-unet3d-center-prior-v1",
        "role": "deepcenter",
        "version": 5,
    },
    {
        "canonical_file_metadata_sha256": "9bd5b1a2ae2db31d1895f69d708648afc27f973bc419bef9c1917808e65ded1a",
        "dataset_id": 11184174,
        "dataset_version_id": "UNKNOWN_NOT_EXPOSED_BY_LIST_API",
        "ref": "pilkwang/biohub-temporal-unet3d-seed314159-v1",
        "role": "secondary",
        "version": 2,
    },
    {
        "canonical_file_metadata_sha256": "ded6cc4648111c3ca1434b9708404ffdb0083132e3e49687b69b4cf85d1e07fe",
        "dataset_id": 10999845,
        "dataset_version_id": "UNKNOWN_NOT_EXPOSED_BY_LIST_API",
        "ref": "pilkwang/biohub-tracking-support-pack-50ep-v1",
        "role": "primary_and_support",
        "version": 10,
    },
    {
        "canonical_file_metadata_sha256": "260313bb5f12accebd9a70c0b0be43c659090de81f1839c7d06971b11bde3dc6",
        "ref": COMPETITION,
        "role": "competition_data",
        "version": "UNKNOWN_NOT_EXPOSED_BY_LIST_API",
    },
]

PROMOTION_GATE_KEYS = {
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
}

TIE_BREAK_ORDER = [
    "maximin embryo official-score delta",
    "embryo-equal macro delta",
    "pooled micro delta",
    "pooled division Jaccard",
    "fewer added division false positives",
    "lower cap saturation",
    "shorter runtime",
]

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

SUBMISSION_COLUMNS = [
    "id", "dataset", "row_type", "node_id", "t", "z", "y", "x",
    "source_id", "target_id",
]

HEX64 = re.compile(r"[0-9a-f]{64}\Z")
SAMPLE_ID_PATTERN = re.compile(r"(?:44b6|6bba)_[0-9a-f]{8}", re.IGNORECASE)
KERNEL_SLUG_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*\Z")
RADIUS_LINE_PATTERN = re.compile(
    r'(?m)^([ \t]*os\.environ\["BIOHUB_SAFE_DIV_MAX_UM"\][ \t]*=[ \t]*)'
    r'"7\.0"([ \t]*(?:#.*)?$)'
)


class BuildError(RuntimeError):
    """A frozen input or generated-artifact invariant was not proven."""


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
    return sha256_bytes(canonical_bytes(value))


def pinned_dataset_sources(contract: dict[str, Any]) -> list[str]:
    """Return exact version-pinned non-competition Kaggle Dataset refs."""
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
        raise BuildError("expected exactly three unique version-pinned Dataset refs")
    return sources


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant is forbidden: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_json_object(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(
            raw,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise BuildError(f"cannot parse {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise BuildError(f"{label} must be a JSON object")
    return value


def load_json_object(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise BuildError(f"cannot read {label}: {exc}") from exc
    return parse_json_object(raw, label), raw


def require_hex64(value: Any, label: str) -> str:
    if not isinstance(value, str) or not HEX64.fullmatch(value) or value == "0" * 64:
        raise BuildError(f"{label} must be a nonzero lowercase SHA-256")
    return value


def validate_contract(contract: dict[str, Any], raw: bytes) -> None:
    raw_sha = sha256_bytes(raw)
    if raw_sha != CONTRACT_FILE_SHA256:
        raise BuildError(
            f"V20B contract file SHA mismatch: expected {CONTRACT_FILE_SHA256}, got {raw_sha}"
        )
    canonical_sha = canonical_sha256(contract)
    if canonical_sha != CONTRACT_CANONICAL_SHA256:
        raise BuildError(
            "V20B contract canonical SHA mismatch: expected "
            f"{CONTRACT_CANONICAL_SHA256}, got {canonical_sha}"
        )
    if contract.get("task_id") != TASK_ID or contract.get("schema_version") != "1.0":
        raise BuildError("V20B contract task/schema identity mismatch")
    frozen = contract.get("experiment_freeze")
    if not isinstance(frozen, dict):
        raise BuildError("V20B contract lacks experiment_freeze")
    if frozen.get("base_git") != {
        "repository": "SailorRen/Biohub-CELL",
        "branch": "main",
        "commit": BASE_GIT_COMMIT,
        "task_branch": "codex/biohub-v20b-two-embryo-radius-20260904",
    }:
        raise BuildError("V20B contract base Git identity mismatch")
    baseline = frozen.get("baseline")
    if not isinstance(baseline, dict) or any(
        (
            baseline.get("notebook_ref") != BASE_NOTEBOOK_REF,
            baseline.get("script_version_id") != BASE_SCRIPT_VERSION_ID,
            baseline.get("version_number") != 1,
            baseline.get("competition") != COMPETITION,
        )
    ):
        raise BuildError("V20B contract V19C baseline identity mismatch")
    if frozen.get("arms") != {
        "R70": {"role": "control", "safe_div_parent_radius_um": 7.0},
        "R80": {"role": "candidate", "safe_div_parent_radius_um": 8.0},
        "R90": {"role": "candidate", "safe_div_parent_radius_um": 9.0},
    }:
        raise BuildError("V20B contract arms are not exact R70/R80/R90")
    parameters = frozen.get("active_parameters")
    if not isinstance(parameters, dict):
        raise BuildError("V20B contract lacks active_parameters")
    if parameters.get("safe_div_parent_radius_um") != "ARM_VALUE_ONLY":
        raise BuildError("parent radius is not frozen as ARM_VALUE_ONLY")
    if set(parameters) != set(RUNTIME_PARAMETER_EXPRESSIONS):
        raise BuildError(
            "runtime parameter map differs from frozen contract: "
            f"missing={sorted(set(parameters) - set(RUNTIME_PARAMETER_EXPRESSIONS))}, "
            f"extra={sorted(set(RUNTIME_PARAMETER_EXPRESSIONS) - set(parameters))}"
        )
    identities = frozen.get("identities")
    if not isinstance(identities, dict):
        raise BuildError("V20B contract lacks identities")
    expected_identity = {
        "base_source_sha256": SOURCE_SHA256,
        "checkpoints": {f"{key}_sha256": value for key, value in EXPECTED_CHECKPOINTS.items()},
        "input_datasets": EXPECTED_INPUT_DATASETS,
        "scorer": EXPECTED_SCORER,
        "support_code_manifest_sha256": SUPPORT_MANIFEST_SHA256,
    }
    if identities != expected_identity:
        raise BuildError("V20B frozen source/checkpoint/input/support/scorer identities differ")
    rule = frozen.get("promotion_rule")
    if not isinstance(rule, dict) or any(
        (
            rule.get("screen_name") != SCREEN_NAME,
            rule.get("candidate_order") != ["R80", "R90"],
            rule.get("tie_break_order") != TIE_BREAK_ORDER,
            not set(PROMOTIONS).issubset(set(rule.get("allowed_decisions", []))),
        )
    ):
        raise BuildError("V20B promotion rule mismatch")
    runtime_budget = frozen.get("runtime_budget")
    if not isinstance(runtime_budget, dict) or runtime_budget.get(
        "production_wall_clock_seconds_max"
    ) != PRODUCTION_WALL_CLOCK_MAX_SECONDS:
        raise BuildError("V20B production wall-clock budget mismatch")
    authorization = contract.get("authorization")
    if not isinstance(authorization, dict) or any(
        (
            authorization.get("competition_submission")
            != "AUTHORIZED_ONLY_AFTER_UNIQUE_OFFLINE_WINNER",
            authorization.get("notebook_write")
            != "CONDITIONALLY_AUTHORIZED_WITHIN_FROZEN_BUDGET",
            authorization.get("training") is not False,
            authorization.get("dataset_write") is not False,
            authorization.get("model_write") is not False,
        )
    ):
        raise BuildError("V20B conditional authorization mismatch")


def validate_source(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise BuildError(f"cannot read V19C notebook: {exc}") from exc
    actual = sha256_bytes(raw)
    if actual != SOURCE_SHA256:
        raise BuildError(f"V19C source SHA mismatch: expected {SOURCE_SHA256}, got {actual}")
    notebook = parse_json_object(raw, "V19C notebook")
    cells = notebook.get("cells")
    if notebook.get("nbformat") != 4 or not isinstance(cells, list) or len(cells) != 12:
        raise BuildError("V19C source must be the exact 12-cell nbformat-4 notebook")
    for index, expected_type, expected_hash in SOURCE_CELLS:
        cell = cells[index]
        if not isinstance(cell, dict) or cell.get("cell_type") != expected_type:
            raise BuildError(f"V19C cell {index} type mismatch")
        source = cell.get("source")
        if not isinstance(source, str):
            raise BuildError(f"V19C cell {index} source must be one string")
        actual_hash = sha256_bytes(source.encode("utf-8"))
        if actual_hash != expected_hash:
            raise BuildError(
                f"V19C cell {index} SHA mismatch: expected {expected_hash}, got {actual_hash}"
            )
        if expected_type == "code":
            try:
                compile(source, f"<v19c-cell-{index}>", "exec")
            except SyntaxError as exc:
                raise BuildError(f"V19C cell {index} no longer parses: {exc}") from exc
            if cell.get("outputs"):
                raise BuildError(f"V19C cell {index} unexpectedly contains retained outputs")
    joined = "\n".join(cell["source"] for cell in cells)
    required_source_tokens = {
        "production test input": 'COMP_DIR / "test"',
        "formal submission path": 'SUBMISSION_PATH = WORKING_DIR / "submission.csv"',
        "test enumeration": "def list_test_stems()",
        "safe-division implementation": "def add_safe_divisions_postlink(",
        "safe-division call": "add_safe_divisions_postlink(",
        "output graph filter": "def filter_output_graph(",
        "submission schema guard": "_guard_columns",
        "indegree topology guard": "max_indegree",
        "outdegree topology guard": "max_outdegree",
    }
    missing = [label for label, token in required_source_tokens.items() if token not in joined]
    if missing:
        raise BuildError(f"V19C production/schema/topology source guards missing: {missing}")
    return notebook, raw


def _environment_radius_assignments(source: str) -> list[tuple[int, Any]]:
    tree = ast.parse(source)
    found: list[tuple[int, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        value = node.value
        for target in targets:
            if not isinstance(target, ast.Subscript):
                continue
            owner = target.value
            key = target.slice
            if (
                isinstance(owner, ast.Attribute)
                and isinstance(owner.value, ast.Name)
                and owner.value.id == "os"
                and owner.attr == "environ"
                and isinstance(key, ast.Constant)
                and key.value == "BIOHUB_SAFE_DIV_MAX_UM"
            ):
                found.append((node.lineno, value.value if isinstance(value, ast.Constant) else None))
    return found


def replace_radius_source(source: str, radius: float) -> tuple[str, int]:
    if radius not in (8.0, 9.0):
        raise BuildError(f"production radius must be exactly 8.0 or 9.0, got {radius!r}")
    assignments = _environment_radius_assignments(source)
    if assignments != [(31, "7.0")]:
        raise BuildError(
            "V19C radius assignment must be the sole cell-2 assignment at line 31 with value '7.0'; "
            f"got {assignments}"
        )
    matches = list(RADIUS_LINE_PATTERN.finditer(source))
    if len(matches) != 1:
        raise BuildError(f"expected one exact V19C radius source line, found {len(matches)}")
    replacement = rf'\g<1>"{radius:.1f}"\g<2>'
    modified = RADIUS_LINE_PATTERN.sub(replacement, source, count=1)
    if modified == source:
        raise BuildError("radius substitution made no change")
    if _environment_radius_assignments(modified) != [(31, f"{radius:.1f}")]:
        raise BuildError("modified radius assignment failed AST verification")
    before_lines = source.splitlines(keepends=True)
    after_lines = modified.splitlines(keepends=True)
    differing = [
        index + 1
        for index, (before, after) in enumerate(zip(before_lines, after_lines))
        if before != after
    ]
    if len(before_lines) != len(after_lines) or differing != [31]:
        raise BuildError(f"radius replacement changed unexpected lines: {differing}")
    return modified, 31


def _all_finite(value: Any) -> bool:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return True
    if isinstance(value, int):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(_all_finite(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _all_finite(item) for key, item in value.items())
    return False


def validate_promotion(
    promotion: dict[str, Any], contract: dict[str, Any]
) -> tuple[str, float, dict[str, Any]]:
    if not _all_finite(promotion):
        raise BuildError("promotion decision contains non-finite or unsupported values")
    required_top = {
        "schema_version", "task_id", "screen", "decision", "selected_arm",
        "selected_radius_um", "candidate_label", "candidate_gates",
        "passing_candidates", "cache_equivalence_pass",
        "runtime_determinism_pass", "checkpoint_overlap_status",
        "competition_submission_created", "retry_count", "note", "tie_break",
        "identity_bindings", "evidence_hashes", "candidate_details",
        "validation_script_version_id",
    }
    missing = sorted(required_top - set(promotion))
    if missing:
        raise BuildError(f"promotion decision lacks required fields: {missing}")
    if promotion.get("schema_version") != "1.0" or promotion.get("task_id") != TASK_ID:
        raise BuildError("promotion decision task/schema identity mismatch")
    if promotion.get("screen") != SCREEN_NAME:
        raise BuildError("promotion decision screen mismatch")
    decision = promotion.get("decision")
    if decision not in PROMOTIONS:
        raise BuildError("production build requires exact PROMOTE_R80/R90 decision")
    selected_arm, selected_radius = PROMOTIONS[decision]
    if promotion.get("selected_arm") != selected_arm:
        raise BuildError("promotion decision/selected_arm mapping mismatch")
    radius_value = promotion.get("selected_radius_um")
    if isinstance(radius_value, bool) or not isinstance(radius_value, (int, float)):
        raise BuildError("promotion selected_radius_um must be numeric")
    if float(radius_value) != selected_radius:
        raise BuildError("promotion decision/selected_radius_um mapping mismatch")
    if promotion.get("candidate_label") != "Kaggle test candidate":
        raise BuildError("promotion candidate label mismatch")
    if promotion.get("cache_equivalence_pass") is not True:
        raise BuildError("promotion cache equivalence did not pass")
    if promotion.get("runtime_determinism_pass") is not True:
        raise BuildError("promotion runtime determinism did not pass")
    if promotion.get("checkpoint_overlap_status") != "CHECKPOINT_TRAINING_OVERLAP_UNKNOWN":
        raise BuildError("checkpoint overlap boundary was rewritten")
    if promotion.get("competition_submission_created") is not False:
        raise BuildError("promotion decision indicates a prior competition submission")
    if promotion.get("retry_count") != 0 or isinstance(promotion.get("retry_count"), bool):
        raise BuildError("promotion retry_count must be exactly zero")
    if promotion.get("note") != (
        "Offline two-embryo sensitivity screen; not CV and not hidden-test improvement proof."
    ):
        raise BuildError("promotion evidence-boundary note mismatch")

    candidate_gates = promotion.get("candidate_gates")
    if not isinstance(candidate_gates, dict) or set(candidate_gates) != {"R80", "R90"}:
        raise BuildError("promotion candidate_gates must contain exactly R80 and R90")
    eligible_arms: list[str] = []
    for arm in ("R80", "R90"):
        gates = candidate_gates[arm]
        if not isinstance(gates, dict) or set(gates) != PROMOTION_GATE_KEYS | {"eligible"}:
            raise BuildError(f"promotion gate schema mismatch for {arm}")
        if any(type(gates[key]) is not bool for key in gates):
            raise BuildError(f"promotion gates must be booleans for {arm}")
        recomputed = all(gates[key] for key in PROMOTION_GATE_KEYS)
        if gates["eligible"] is not recomputed:
            raise BuildError(f"promotion eligible flag is stale for {arm}")
        if recomputed:
            eligible_arms.append(arm)
    if promotion.get("passing_candidates") != eligible_arms:
        raise BuildError("promotion passing_candidates differs from recomputed eligible arms")
    if selected_arm not in eligible_arms:
        raise BuildError("selected production arm did not pass every frozen gate")

    tie_break = promotion.get("tie_break")
    if not isinstance(tie_break, dict):
        raise BuildError("promotion tie_break must be an object")
    if tie_break.get("order") != TIE_BREAK_ORDER:
        raise BuildError("promotion tie-break order mismatch")
    if tie_break.get("unique_winner") != selected_arm:
        raise BuildError("promotion tie-break unique_winner mismatch")
    vectors = tie_break.get("vectors")
    if not isinstance(vectors, dict) or not set(vectors).issubset({"R80", "R90"}):
        raise BuildError("promotion tie-break vectors malformed")
    if len(eligible_arms) == 1 and vectors != {}:
        raise BuildError("a sole eligible candidate must not have post-hoc tie-break vectors")
    if len(eligible_arms) == 2:
        if set(vectors) != {"R80", "R90"}:
            raise BuildError("two eligible candidates require both tie-break vectors")
        if any(
            not isinstance(vectors[arm], list)
            or len(vectors[arm]) != len(TIE_BREAK_ORDER)
            or any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in vectors[arm])
            for arm in ("R80", "R90")
        ):
            raise BuildError("promotion tie-break vectors must be seven finite numeric values")
        recomputed_winner = None
        epsilon = contract["experiment_freeze"]["comparison_tolerances"][
            "strict_positive_epsilon"
        ]
        for left, right in zip(vectors["R80"], vectors["R90"]):
            if abs(float(left) - float(right)) <= epsilon:
                continue
            recomputed_winner = "R80" if left > right else "R90"
            break
        if recomputed_winner is None:
            raise BuildError("tied candidates do not yield a unique production winner")
        if recomputed_winner != selected_arm:
            raise BuildError("promotion tie-break winner differs from recomputed vector order")

    candidate_details = promotion.get("candidate_details")
    if not isinstance(candidate_details, dict) or set(candidate_details) != {"R80", "R90"}:
        raise BuildError("promotion candidate_details must contain exactly R80 and R90")

    identity_bindings = promotion.get("identity_bindings")
    if not isinstance(identity_bindings, dict):
        raise BuildError("promotion identity_bindings must be an object")
    expected_identity_binding_keys = {
        "base_source_sha256",
        "contract_canonical_sha256",
        "contract_file_sha256",
        "sample_manifest_canonical_sha256",
        "sample_manifest_file_sha256",
        "production_runtime_basis_sha256",
        "cache_manifest_file_sha256",
        "cache_manifest_sha256",
        "per_sample_metrics_sha256",
        "per_embryo_metrics_sha256",
        "resolved_config_verification_sha256",
        "cache_equivalence_sha256",
        "runtime_determinism_sha256",
    }
    if not expected_identity_binding_keys.issubset(set(identity_bindings)):
        raise BuildError("promotion identity_bindings lacks a required identity")
    for key, value in identity_bindings.items():
        if not isinstance(key, str) or not re.fullmatch(r"[a-z0-9_]+_sha256", key):
            raise BuildError(f"promotion identity binding has an unsafe key: {key!r}")
        require_hex64(value, f"promotion.identity_bindings.{key}")
    if identity_bindings.get("base_source_sha256") != SOURCE_SHA256:
        raise BuildError("promotion base source SHA mismatch")
    expected_contract_sha = canonical_sha256(contract)
    if identity_bindings.get("contract_canonical_sha256") != expected_contract_sha:
        raise BuildError("promotion contract canonical SHA mismatch")
    if identity_bindings.get("contract_file_sha256") != CONTRACT_FILE_SHA256:
        raise BuildError("promotion contract file SHA mismatch")
    if identity_bindings.get("production_runtime_basis_sha256") != (
        PRODUCTION_RUNTIME_BASIS_SHA256
    ):
        raise BuildError("promotion historical production-runtime basis SHA mismatch")
    required_hashes = {
        "sample_manifest_canonical_sha256",
        "sample_manifest_file_sha256",
        "cache_manifest_file_sha256",
        "cache_manifest_sha256",
        "per_sample_metrics_sha256",
        "per_embryo_metrics_sha256",
        "resolved_config_verification_sha256",
        "cache_equivalence_sha256",
        "runtime_determinism_sha256",
    }
    for key in sorted(required_hashes):
        require_hex64(
            identity_bindings.get(key), f"promotion.identity_bindings.{key}"
        )
    evidence_hashes = promotion.get("evidence_hashes")
    expected_evidence_paths = {
        "experiments/V20B/full_sample_payload_inventory.csv",
        "experiments/V20B/full_sample_manifest.json",
        "experiments/V20B/per_sample_metrics.csv",
        "experiments/V20B/per_embryo_metrics.csv",
        "experiments/V20B/paired_deltas_by_sample.csv",
        "experiments/V20B/paired_deltas_by_embryo.csv",
        "experiments/V20B/micro_macro_comparison.csv",
        "experiments/V20B/division_confusion_by_embryo.json",
        "experiments/V20B/topology_validation.json",
        "experiments/V20B/runtime_receipts.json",
        "experiments/V20B/cache_manifest.json",
        "experiments/V20B/cache_equivalence.json",
        "experiments/V20B/runtime_determinism.json",
        "experiments/V20B/resolved_config_verification.json",
    }
    if not isinstance(evidence_hashes, dict) or not expected_evidence_paths.issubset(
        set(evidence_hashes)
    ):
        raise BuildError("promotion evidence_hashes lacks a required artifact path")
    duplicate_bindings = {
        "experiments/V20B/per_sample_metrics.csv": "per_sample_metrics_sha256",
        "experiments/V20B/per_embryo_metrics.csv": "per_embryo_metrics_sha256",
        "experiments/V20B/cache_manifest.json": "cache_manifest_file_sha256",
        "experiments/V20B/cache_equivalence.json": "cache_equivalence_sha256",
        "experiments/V20B/runtime_determinism.json": "runtime_determinism_sha256",
        "experiments/V20B/resolved_config_verification.json":
            "resolved_config_verification_sha256",
    }
    for relative in evidence_hashes:
        path = Path(relative)
        if (
            not isinstance(relative, str)
            or path.is_absolute()
            or ".." in path.parts
            or path.parts[:2] != ("experiments", "V20B")
        ):
            raise BuildError(f"promotion evidence hash has an unsafe path: {relative!r}")
    for path, evidence_key in duplicate_bindings.items():
        if evidence_hashes.get(path) != identity_bindings[evidence_key]:
            raise BuildError(f"promotion duplicate evidence binding mismatch: {path}")
    for key, value in evidence_hashes.items():
        require_hex64(value, f"promotion.evidence_hashes[{key!r}]")
    selected_gate = candidate_gates[selected_arm]
    binding = {
        "schema_version": promotion["schema_version"],
        "task_id": promotion["task_id"],
        "screen": promotion["screen"],
        "decision": decision,
        "selected_arm": selected_arm,
        "selected_radius_um": selected_radius,
        "candidate_label": promotion["candidate_label"],
        "selected_candidate_gates": selected_gate,
        "passing_candidates": eligible_arms,
        "tie_break": copy.deepcopy(tie_break),
        "cache_equivalence_pass": True,
        "runtime_determinism_pass": True,
        "checkpoint_overlap_status": "CHECKPOINT_TRAINING_OVERLAP_UNKNOWN",
        "competition_submission_created": False,
        "retry_count": 0,
        "validation_script_version_id": promotion.get("validation_script_version_id"),
        "identity_bindings": copy.deepcopy(identity_bindings),
        "evidence_hashes": copy.deepcopy(evidence_hashes),
        "note": promotion["note"],
    }
    return selected_arm, selected_radius, binding


RUNTIME_BOOTSTRAP = r'''
# V20B production wall-clock guard: first executable notebook cell.
import json as _v20b_bootstrap_json
import os as _v20b_bootstrap_os
import threading as _v20b_bootstrap_threading
import time as _v20b_bootstrap_time
from datetime import datetime as _V20BBootstrapDateTime
from datetime import timezone as _V20BBootstrapTimezone
from pathlib import Path as _V20BBootstrapPath

_V20B_PRODUCTION_WALL_CLOCK_MAX_SECONDS = __PRODUCTION_WALL_CLOCK_MAX_SECONDS__
_V20B_PRODUCTION_RECEIPT_RESERVE_SECONDS = __PRODUCTION_RECEIPT_RESERVE_SECONDS__
_V20B_PRODUCTION_HARD_STOP_SECONDS = __PRODUCTION_HARD_STOP_SECONDS__
if (
    _V20B_PRODUCTION_HARD_STOP_SECONDS
    != _V20B_PRODUCTION_WALL_CLOCK_MAX_SECONDS
    - _V20B_PRODUCTION_RECEIPT_RESERVE_SECONDS
):
    raise RuntimeError("V20B production wall-clock guard arithmetic mismatch")
if _V20B_PRODUCTION_RECEIPT_RESERVE_SECONDS <= 0:
    raise RuntimeError("V20B production receipt reserve must be positive")
if globals().get("_V20B_PRODUCTION_WATCHDOG_STARTED") is True:
    raise RuntimeError("V20B production wall-clock watchdog was already started")

_V20B_PRODUCTION_WALL_STARTED_MONOTONIC = _v20b_bootstrap_time.monotonic()
_V20B_PRODUCTION_WALL_STARTED_UTC = _V20BBootstrapDateTime.now(
    _V20BBootstrapTimezone.utc
).isoformat().replace("+00:00", "Z")
_V20B_PRODUCTION_WATCHDOG_CANCEL = _v20b_bootstrap_threading.Event()
_V20B_PRODUCTION_WATCHDOG_STARTED = True


def _v20b_bootstrap_write_json(path, value):
    target = _V20BBootstrapPath(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = (_v20b_bootstrap_json.dumps(
        value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False
    ) + "\n").encode("utf-8")
    temporary = target.with_name(target.name + ".tmp")
    with temporary.open("wb") as stream:
        stream.write(payload)
        stream.flush()
        _v20b_bootstrap_os.fsync(stream.fileno())
    temporary.replace(target)


def _v20b_production_watchdog():
    cancelled = _V20B_PRODUCTION_WATCHDOG_CANCEL.wait(
        _V20B_PRODUCTION_HARD_STOP_SECONDS
    )
    if cancelled:
        return
    elapsed = _v20b_bootstrap_time.monotonic() - _V20B_PRODUCTION_WALL_STARTED_MONOTONIC
    failure = {
        "schema_version": "1.0",
        "task_id": __TASK_ID__,
        "status": "FAIL_HARD_STOP_BEFORE_FROZEN_MAXIMUM",
        "started_at_utc": _V20B_PRODUCTION_WALL_STARTED_UTC,
        "elapsed_wall_clock_seconds": elapsed,
        "production_wall_clock_seconds_max": _V20B_PRODUCTION_WALL_CLOCK_MAX_SECONDS,
        "hard_stop_seconds": _V20B_PRODUCTION_HARD_STOP_SECONDS,
        "receipt_reserve_seconds": _V20B_PRODUCTION_RECEIPT_RESERVE_SECONDS,
        "output_files_may_be_partial": True,
        "claims_boundary": (
            "The production notebook exceeded its internal safety deadline; "
            "no output validity or submission-readiness claim is permitted."
        ),
    }
    try:
        output_root = _V20BBootstrapPath("/kaggle/working/experiments/V20B")
        _v20b_bootstrap_write_json(output_root / "production_runtime_guard.json", failure)
        _v20b_bootstrap_write_json(output_root / "production_output_audit.json", failure)
    except Exception as receipt_error:
        print(
            "V20B_PRODUCTION_HARD_STOP_RECEIPT_WRITE_FAILED "
            + type(receipt_error).__name__,
            flush=True,
        )
    print("V20B_PRODUCTION_INTERNAL_HARD_STOP", flush=True)
    _v20b_bootstrap_os._exit(124)


_V20B_PRODUCTION_WATCHDOG_THREAD = _v20b_bootstrap_threading.Thread(
    target=_v20b_production_watchdog,
    name="v20b-production-wall-clock-watchdog",
    daemon=True,
)
_V20B_PRODUCTION_WATCHDOG_THREAD.start()
print("V20B_PRODUCTION_WALL_CLOCK_GUARD_STARTED")
'''


RUNTIME_AUDIT = r'''
# V20B production audit: appended after the unchanged V19C production pipeline.
# The selected arm is frozen by the offline promotion receipt embedded below.
from __future__ import annotations

import csv as _v20b_csv
import hashlib as _v20b_hashlib
import json as _v20b_json
import math as _v20b_math
import os as _v20b_os
import re as _v20b_re
import time as _v20b_time
from collections import defaultdict as _v20b_defaultdict
from pathlib import Path as _V20BPath

_V20B_TASK_ID = __TASK_ID__
_V20B_SELECTED_ARM = __SELECTED_ARM__
_V20B_SELECTED_RADIUS = __SELECTED_RADIUS__
_V20B_SOURCE_SHA256 = __SOURCE_SHA256__
_V20B_CONTRACT_SHA256 = __CONTRACT_SHA256__
_V20B_CONTRACT_FILE_SHA256 = __CONTRACT_FILE_SHA256__
_V20B_PROMOTION_FILE_SHA256 = __PROMOTION_FILE_SHA256__
_V20B_PROMOTION_CANONICAL_SHA256 = __PROMOTION_CANONICAL_SHA256__
_V20B_PARAMETERS = _v20b_json.loads(__PARAMETERS_JSON__)
_V20B_IDENTITIES = _v20b_json.loads(__IDENTITIES_JSON__)
_V20B_PINNED_DATASET_SOURCES = _v20b_json.loads(__PINNED_DATASET_SOURCES_JSON__)
_V20B_PROMOTION = _v20b_json.loads(__PROMOTION_JSON__)
_V20B_SUPPORT_FILES = _v20b_json.loads(__SUPPORT_FILES_JSON__)
_V20B_OUTPUT_ROOT = _V20BPath("/kaggle/working/experiments/V20B")
_V20B_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)


def _v20b_canonical_bytes(value):
    return (_v20b_json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _v20b_sha256_file(path):
    digest = _v20b_hashlib.sha256()
    with _V20BPath(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _v20b_write_json(path, value):
    payload = _v20b_json.dumps(value, ensure_ascii=False, indent=2,
                               sort_keys=True, allow_nan=False).encode("utf-8") + b"\n"
    target = _V20BPath(path)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(target)


def _v20b_validate_runtime_guard():
    required = {
        "_V20B_PRODUCTION_WALL_STARTED_MONOTONIC",
        "_V20B_PRODUCTION_WALL_STARTED_UTC",
        "_V20B_PRODUCTION_WALL_CLOCK_MAX_SECONDS",
        "_V20B_PRODUCTION_HARD_STOP_SECONDS",
        "_V20B_PRODUCTION_RECEIPT_RESERVE_SECONDS",
        "_V20B_PRODUCTION_WATCHDOG_CANCEL",
        "_V20B_PRODUCTION_WATCHDOG_STARTED",
    }
    missing = sorted(name for name in required if name not in globals())
    if missing:
        raise RuntimeError(f"production wall-clock bootstrap state is missing: {missing}")
    if _V20B_PRODUCTION_WATCHDOG_STARTED is not True:
        raise RuntimeError("production wall-clock watchdog did not start")
    if _V20B_PRODUCTION_WALL_CLOCK_MAX_SECONDS != __PRODUCTION_WALL_CLOCK_MAX_SECONDS__:
        raise RuntimeError("production wall-clock maximum differs from frozen contract")
    if _V20B_PRODUCTION_HARD_STOP_SECONDS != __PRODUCTION_HARD_STOP_SECONDS__:
        raise RuntimeError("production hard-stop deadline differs from frozen builder")
    if _V20B_PRODUCTION_RECEIPT_RESERVE_SECONDS != __PRODUCTION_RECEIPT_RESERVE_SECONDS__:
        raise RuntimeError("production receipt reserve differs from frozen builder")
    elapsed = _v20b_time.monotonic() - _V20B_PRODUCTION_WALL_STARTED_MONOTONIC
    if not _v20b_math.isfinite(elapsed) or elapsed < 0:
        raise RuntimeError("production wall-clock elapsed value is invalid")
    if elapsed >= _V20B_PRODUCTION_HARD_STOP_SECONDS:
        raise RuntimeError("production runtime reached the internal hard-stop deadline")
    return {
        "status": "PASS_WITHIN_INTERNAL_HARD_STOP",
        "started_at_utc": _V20B_PRODUCTION_WALL_STARTED_UTC,
        "elapsed_wall_clock_seconds": elapsed,
        "production_wall_clock_seconds_max": _V20B_PRODUCTION_WALL_CLOCK_MAX_SECONDS,
        "hard_stop_seconds": _V20B_PRODUCTION_HARD_STOP_SECONDS,
        "receipt_reserve_seconds": _V20B_PRODUCTION_RECEIPT_RESERVE_SECONDS,
        "watchdog_started": True,
    }


def _v20b_parse_int(value, label):
    text = str(value).strip()
    if not _v20b_re.fullmatch(r"[+-]?\d+(?:\.0+)?", text):
        raise RuntimeError(f"{label} is not an exact integer: {text!r}")
    return int(float(text))


def _v20b_parse_float(value, label):
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"{label} is not numeric") from exc
    if not _v20b_math.isfinite(number):
        raise RuntimeError(f"{label} is non-finite")
    return number


def _v20b_validate_active_parameters():
    actual = {
__RUNTIME_PARAMETER_LINES__
    }
    expected = dict(_V20B_PARAMETERS)
    expected["safe_div_parent_radius_um"] = _V20B_SELECTED_RADIUS
    if _v20b_canonical_bytes(actual) != _v20b_canonical_bytes(expected):
        changed = sorted(key for key in set(actual) | set(expected)
                         if actual.get(key) != expected.get(key)
                         or type(actual.get(key)) is not type(expected.get(key)))
        raise RuntimeError(f"production active parameters differ from freeze: {changed}")
    env_radius = _v20b_os.environ.get("BIOHUB_SAFE_DIV_MAX_UM")
    if env_radius != f"{_V20B_SELECTED_RADIUS:.1f}":
        raise RuntimeError(f"post-override radius environment mismatch: {env_radius!r}")
    if float(SAFE_DIV_MAX_UM) != _V20B_SELECTED_RADIUS:
        raise RuntimeError("post-override SAFE_DIV_MAX_UM mismatch")
    return actual


def _v20b_validate_call_binding(expected_parameters):
    function = globals().get("add_safe_divisions_postlink")
    filter_function = globals().get("filter_output_graph")
    if not callable(function) or not callable(filter_function):
        raise RuntimeError("safe-division production call chain is unavailable")
    required_names = {
        "SAFE_DIV_MAX_UM", "SAFE_DIV_SISTER_MAX_UM", "SAFE_DIV_DIVERGE_UM",
        "SAFE_DIV_FRAME_FRAC_CAP", "SAFE_DIV_GLOBAL_FRAC_CAP",
        "SAFE_DIV_EXISTING_CHILD_MAX_UM", "SAFE_DIV_REQUIRE_DIVERGENCE",
        "SAFE_DIV_REQUIRE_MUTUAL_NN", "SAFE_DIV_SISTER_SYMMETRY_TAU",
        "DEEPCENTER_SAFE_DIV_VETO", "DEEPCENTER_SAFE_DIV_THRESHOLD",
    }
    if not required_names.issubset(set(function.__code__.co_names)):
        raise RuntimeError("safe-division function no longer consumes every frozen call global")
    if "add_safe_divisions_postlink" not in set(filter_function.__code__.co_names):
        raise RuntimeError("filter_output_graph no longer calls add_safe_divisions_postlink")
    call_arguments = {
        "safe_div_parent_radius_um": float(function.__globals__["SAFE_DIV_MAX_UM"]),
        "safe_div_sister_radius_um": float(function.__globals__["SAFE_DIV_SISTER_MAX_UM"]),
        "safe_div_existing_child_max_um": float(
            function.__globals__["SAFE_DIV_EXISTING_CHILD_MAX_UM"]
        ),
        "safe_div_divergence_um": float(function.__globals__["SAFE_DIV_DIVERGE_UM"]),
        "safe_div_require_divergence": bool(
            function.__globals__["SAFE_DIV_REQUIRE_DIVERGENCE"]
        ),
        "safe_div_require_mutual_nn": bool(
            function.__globals__["SAFE_DIV_REQUIRE_MUTUAL_NN"]
        ),
        "safe_div_sister_symmetry_tau": float(
            function.__globals__["SAFE_DIV_SISTER_SYMMETRY_TAU"]
        ),
        "safe_div_frame_cap": float(function.__globals__["SAFE_DIV_FRAME_FRAC_CAP"]),
        "safe_div_global_cap": float(function.__globals__["SAFE_DIV_GLOBAL_FRAC_CAP"]),
        "deepcenter_enabled": bool(function.__globals__["USE_DEEPCENTER_VETO"]),
        "deepcenter_safe_div_veto": bool(
            function.__globals__["DEEPCENTER_SAFE_DIV_VETO"]
        ),
        "deepcenter_safe_div_threshold": float(
            function.__globals__["DEEPCENTER_SAFE_DIV_THRESHOLD"]
        ),
    }
    expected_call = {key: expected_parameters[key] for key in call_arguments}
    if _v20b_canonical_bytes(call_arguments) != _v20b_canonical_bytes(expected_call):
        raise RuntimeError("safe-division function-call globals differ from frozen parameters")
    return call_arguments


def _v20b_validate_integrity():
    receipt_path = _V20BPath("/kaggle/working/bidirectional_production_runtime_integrity.json")
    if not receipt_path.is_file():
        raise RuntimeError("V19C production runtime integrity receipt is missing")
    receipt = _v20b_json.loads(receipt_path.read_text(encoding="utf-8"))
    expected_checkpoints = {
        key.removesuffix("_sha256"): value
        for key, value in _V20B_IDENTITIES["checkpoints"].items()
    }
    if receipt.get("status") != "complete_label_free_runtime_integrity":
        raise RuntimeError("V19C runtime integrity status mismatch")
    if receipt.get("ground_truth_accessed") is not False:
        raise RuntimeError("production integrity receipt indicates ground-truth access")
    if receipt.get("verified_before_dynamic_source_patch") is not True:
        raise RuntimeError("checkpoint/support identity was not verified before dynamic patch")
    if receipt.get("checkpoint_sha256") != expected_checkpoints:
        raise RuntimeError("runtime checkpoint receipt differs from frozen identities")
    if receipt.get("support_repo_python_manifest_sha256") != _V20B_IDENTITIES[
        "support_code_manifest_sha256"
    ]:
        raise RuntimeError("runtime support manifest SHA differs from freeze")
    if receipt.get("support_repo_python_file_count") != len(_V20B_SUPPORT_FILES):
        raise RuntimeError("runtime support file count differs from freeze")
    if receipt.get("support_repo_python_sha256") != _V20B_SUPPORT_FILES:
        raise RuntimeError("runtime support per-file hashes differ from freeze")

    materialized = receipt.get("materialized_paths")
    if not isinstance(materialized, dict) or set(materialized) != set(expected_checkpoints):
        raise RuntimeError("runtime checkpoint materialized_paths schema mismatch")
    checkpoint_observed = {}
    for role, expected_sha in expected_checkpoints.items():
        path = _V20BPath(materialized[role])
        resolved = path.resolve()
        if not str(resolved).startswith(("/kaggle/input/", "/kaggle/working/")):
            raise RuntimeError(f"checkpoint path outside Kaggle roots: {role}")
        if not resolved.is_file():
            raise RuntimeError(f"materialized checkpoint is missing: {role}")
        actual_sha = _v20b_sha256_file(resolved)
        if actual_sha != expected_sha:
            raise RuntimeError(f"materialized checkpoint SHA mismatch: {role}")
        checkpoint_observed[role] = {"path": str(resolved), "sha256": actual_sha}

    support_root = _V20BPath("/kaggle/working/tracking_repo")
    support_observed = {}
    for relative, expected_sha in sorted(_V20B_SUPPORT_FILES.items()):
        path = support_root / relative
        if not path.is_file():
            raise RuntimeError(f"materialized support file is missing: {relative}")
        actual_sha = _v20b_sha256_file(path)
        if actual_sha != expected_sha:
            raise RuntimeError(f"materialized support file SHA mismatch: {relative}")
        support_observed[relative] = actual_sha
    return {
        "receipt_path": str(receipt_path),
        "receipt_sha256": _v20b_sha256_file(receipt_path),
        "checkpoint_files": checkpoint_observed,
        "support_file_count": len(support_observed),
        "support_manifest_sha256": receipt["support_repo_python_manifest_sha256"],
        "ground_truth_accessed": False,
    }


def _v20b_validate_mounts():
    expected_pinned_sources = [
        f"{identity['ref']}/{int(identity['version'])}"
        for identity in _V20B_IDENTITIES["input_datasets"]
        if identity["role"] != "competition_data"
    ]
    if _V20B_PINNED_DATASET_SOURCES != expected_pinned_sources:
        raise RuntimeError("version-pinned production Dataset sources differ from freeze")
    observed = []
    for identity in _V20B_IDENTITIES["input_datasets"]:
        if identity["role"] == "competition_data":
            continue
        owner, slug = identity["ref"].split("/", 1)
        candidates = [
            _V20BPath("/kaggle/input") / slug,
            _V20BPath("/kaggle/input/datasets") / owner / slug,
        ]
        existing = sorted(str(path.resolve()) for path in candidates if path.is_dir())
        if not existing:
            raise RuntimeError(f"frozen Kaggle Dataset mount is absent: {identity['role']}")
        observed.append({
            "identity": identity,
            "version_pinned_kernel_source": f"{identity['ref']}/{int(identity['version'])}",
            "existing_mount_paths": existing,
            "verification_scope": (
                "FROZEN_VERSION_PINNED_KERNEL_REF_PLUS_RUNTIME_MOUNT_PRESENCE_"
                "AND_SELECTED_CRITICAL_CONTENT_HASH"
            ),
        })
    comp_dir = _V20BPath(COMP_DIR).resolve()
    test_dir = _V20BPath(TEST_DIR).resolve()
    if not comp_dir.is_dir() or not test_dir.is_dir() or test_dir.name != "test":
        raise RuntimeError("formal competition test mount is unavailable")
    if comp_dir != test_dir.parent:
        raise RuntimeError("TEST_DIR is not the direct competition test directory")
    competition_identity = next(
        item for item in _V20B_IDENTITIES["input_datasets"]
        if item["role"] == "competition_data"
    )
    observed.append({
        "identity": competition_identity,
        "competition_root": str(comp_dir),
        "test_root": str(test_dir),
        "ground_truth_path_read": False,
        "verification_scope": "FROZEN_COMPETITION_REF_PLUS_RUNTIME_TEST_MOUNT_PRESENCE",
    })
    return observed


def _v20b_validate_run_stats():
    path = _V20BPath("/kaggle/working/run_stats.csv")
    required = {
        "dataset", "safe_division_candidates", "safe_division_geometric_candidates",
        "safe_divisions_added", "safe_division_skipped_cap",
        "safe_division_mutual_nn_rejected", "safe_division_divergence_rejected",
        "safe_division_symmetry_rejected", "deepcenter_safe_div_checked",
        "deepcenter_safe_div_accepted", "deepcenter_safe_div_rejected",
        "deepcenter_safe_div_missing",
    }
    if not path.is_file():
        raise RuntimeError("run_stats.csv is missing")
    rows = []
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = _v20b_csv.DictReader(stream)
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            raise RuntimeError("run_stats.csv lacks safe-division call evidence fields")
        for row_number, row in enumerate(reader, 2):
            dataset = str(row.get("dataset", "")).strip()
            if not dataset:
                raise RuntimeError(f"run_stats row {row_number} has empty dataset")
            counts = {
                key: _v20b_parse_int(row[key], f"run_stats row {row_number} {key}")
                for key in sorted(required - {"dataset"})
            }
            if any(value < 0 for value in counts.values()):
                raise RuntimeError(f"run_stats row {row_number} contains a negative count")
            rows.append({"dataset": dataset, **counts})
    datasets = [row["dataset"] for row in rows]
    if not rows or len(datasets) != len(set(datasets)):
        raise RuntimeError("run_stats must contain one unique row per production dataset")
    return {
        "path": str(path),
        "sha256": _v20b_sha256_file(path),
        "rows": rows,
        "dataset_names": sorted(datasets),
        "call_evidence": "PER_DATASET_SAFE_DIVISION_COUNTERS_EMITTED_BY_FILTER_OUTPUT_GRAPH",
    }


def _v20b_validate_submission(expected_datasets):
    path = _V20BPath("/kaggle/working/submission.csv")
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError("formal competition submission.csv is missing or empty")
    ids = set()
    nodes = {}
    edges = []
    edge_keys = set()
    dataset_counts = _v20b_defaultdict(lambda: {"node_rows": 0, "edge_rows": 0})
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = _v20b_csv.DictReader(stream)
        if reader.fieldnames != __SUBMISSION_COLUMNS__:
            raise RuntimeError(f"submission schema mismatch: {reader.fieldnames}")
        for row_number, row in enumerate(reader, 2):
            if None in row:
                raise RuntimeError(f"submission row {row_number} has surplus columns")
            row_id = _v20b_parse_int(row["id"], f"submission row {row_number} id")
            if row_id < 0 or row_id in ids:
                raise RuntimeError(f"submission row {row_number} has invalid/duplicate id")
            ids.add(row_id)
            dataset = str(row["dataset"]).strip()
            if not dataset:
                raise RuntimeError(f"submission row {row_number} has empty dataset")
            row_type = str(row["row_type"]).strip()
            if row_type == "node":
                node_id = _v20b_parse_int(row["node_id"], f"node row {row_number} node_id")
                timepoint = _v20b_parse_int(row["t"], f"node row {row_number} t")
                coordinates = tuple(
                    _v20b_parse_float(row[key], f"node row {row_number} {key}")
                    for key in ("z", "y", "x")
                )
                source_placeholder = _v20b_parse_int(
                    row["source_id"], f"node row {row_number} source_id"
                )
                target_placeholder = _v20b_parse_int(
                    row["target_id"], f"node row {row_number} target_id"
                )
                if node_id < 0 or timepoint < 0 or min(coordinates) < 0:
                    raise RuntimeError(f"node row {row_number} contains a negative required value")
                if (source_placeholder, target_placeholder) != (-1, -1):
                    raise RuntimeError(f"node row {row_number} has non-sentinel edge fields")
                key = (dataset, node_id)
                if key in nodes:
                    raise RuntimeError(f"duplicate node identity: {key}")
                nodes[key] = timepoint
                dataset_counts[dataset]["node_rows"] += 1
            elif row_type == "edge":
                placeholders = (
                    _v20b_parse_int(row["node_id"], f"edge row {row_number} node_id"),
                    _v20b_parse_int(row["t"], f"edge row {row_number} t"),
                    _v20b_parse_float(row["z"], f"edge row {row_number} z"),
                    _v20b_parse_float(row["y"], f"edge row {row_number} y"),
                    _v20b_parse_float(row["x"], f"edge row {row_number} x"),
                )
                if any(value != -1 for value in placeholders):
                    raise RuntimeError(f"edge row {row_number} has non-sentinel node fields")
                source_id = _v20b_parse_int(
                    row["source_id"], f"edge row {row_number} source_id"
                )
                target_id = _v20b_parse_int(
                    row["target_id"], f"edge row {row_number} target_id"
                )
                if source_id < 0 or target_id < 0 or source_id == target_id:
                    raise RuntimeError(f"edge row {row_number} has invalid endpoints")
                edge_key = (dataset, source_id, target_id)
                if edge_key in edge_keys:
                    raise RuntimeError(f"duplicate edge identity: {edge_key}")
                edge_keys.add(edge_key)
                edges.append(edge_key)
                dataset_counts[dataset]["edge_rows"] += 1
            else:
                raise RuntimeError(f"submission row {row_number} has invalid row_type {row_type!r}")
    if not ids or not nodes or not edges:
        raise RuntimeError("submission must contain nonempty node and edge rows")
    observed_datasets = sorted(dataset_counts)
    if observed_datasets != sorted(expected_datasets):
        raise RuntimeError("submission dataset coverage differs from run_stats")
    indegree = _v20b_defaultdict(int)
    outdegree = _v20b_defaultdict(int)
    for dataset, source_id, target_id in edges:
        source_key = (dataset, source_id)
        target_key = (dataset, target_id)
        if source_key not in nodes or target_key not in nodes:
            raise RuntimeError(f"dangling edge: {dataset}/{source_id}->{target_id}")
        if nodes[target_key] != nodes[source_key] + 1:
            raise RuntimeError(f"non-next-frame edge: {dataset}/{source_id}->{target_id}")
        outdegree[source_key] += 1
        indegree[target_key] += 1
        if outdegree[source_key] > 2:
            raise RuntimeError(f"outdegree exceeds two: {source_key}")
        if indegree[target_key] > 1:
            raise RuntimeError(f"indegree exceeds one: {target_key}")
    topology = {}
    for dataset in observed_datasets:
        dataset_node_keys = [key for key in nodes if key[0] == dataset]
        topology[dataset] = {
            **dataset_counts[dataset],
            "max_indegree": max((indegree[key] for key in dataset_node_keys), default=0),
            "max_outdegree": max((outdegree[key] for key in dataset_node_keys), default=0),
        }
    return {
        "path": str(path),
        "sha256": _v20b_sha256_file(path),
        "bytes": path.stat().st_size,
        "row_count": len(ids),
        "node_row_count": len(nodes),
        "edge_row_count": len(edges),
        "datasets": observed_datasets,
        "columns": __SUBMISSION_COLUMNS__,
        "schema_status": "PASS",
        "topology_status": "PASS",
        "topology": topology,
    }


def _v20b_sensitive_scan(value):
    text = _v20b_json.dumps(value, ensure_ascii=False, sort_keys=True)
    patterns = {
        "aws_access_key": r"AKIA[0-9A-Z]{16}",
        "github_token": r"gh[pousr]_[A-Za-z0-9]{20,}",
        "credential_url": r"https?://[^/\s:@]+:[^@\s]+@",
        "private_home": r"/(?:Users|home)/[^/\s]+/",
        "literal_secret": r"(?i)(?:api[_-]?key|password|secret|token)\s*[:=]\s*['\"][^'\"\n]{8,}",
    }
    findings = [name for name, pattern in patterns.items() if _v20b_re.search(pattern, text)]
    if findings:
        raise RuntimeError(f"sensitive-information scan failed: {findings}")
    return {"status": "PASS", "finding_count": 0, "patterns": sorted(patterns)}


_v20b_failure = None
try:
    _v20b_runtime_guard = _v20b_validate_runtime_guard()
    _v20b_active = _v20b_validate_active_parameters()
    _v20b_call_arguments = _v20b_validate_call_binding(_v20b_active)
    _v20b_integrity = _v20b_validate_integrity()
    _v20b_mounts = _v20b_validate_mounts()
    _v20b_run_stats = _v20b_validate_run_stats()
    _v20b_submission = _v20b_validate_submission(_v20b_run_stats["dataset_names"])
    _v20b_call_receipt = {
        "schema_version": "1.0",
        "task_id": _V20B_TASK_ID,
        "arm": _V20B_SELECTED_ARM,
        "status": "PASS",
        "capture_phase": "POST_EXECUTION_RUNTIME_CALL_BINDING_AUDIT",
        "safe_division_function": "add_safe_divisions_postlink",
        "safe_division_function_arguments": _v20b_call_arguments,
        "call_chain": "filter_output_graph -> add_safe_divisions_postlink",
        "actual_invocation_evidence": _v20b_run_stats,
        "runtime_guard": _v20b_runtime_guard,
    }
    _v20b_canonical = {
        "schema_version": "1.0",
        "task_id": _V20B_TASK_ID,
        "arm": _V20B_SELECTED_ARM,
        "status": "PASS",
        "capture_phase": "AFTER_ALL_ORIGINAL_V19C_CELLS_POST_EXECUTION_REVALIDATION",
        "canonical_source": "POST_OVERRIDE_RUNTIME_STATE",
        "parameters": _v20b_active,
        "identities": _V20B_IDENTITIES,
        "source_lineage": {
            "base_notebook_sha256": _V20B_SOURCE_SHA256,
            "contract_file_sha256": _V20B_CONTRACT_FILE_SHA256,
            "contract_canonical_sha256": _V20B_CONTRACT_SHA256,
        },
        "promotion_binding": {
            "promotion_decision_file_sha256": _V20B_PROMOTION_FILE_SHA256,
            "promotion_decision_canonical_sha256": _V20B_PROMOTION_CANONICAL_SHA256,
            "validated_fields": _V20B_PROMOTION,
        },
        "runtime_integrity": _v20b_integrity,
        "runtime_guard": _v20b_runtime_guard,
        "input_mounts": _v20b_mounts,
        "outputs": {"submission.csv": _v20b_submission},
        "outcome_independence": {
            "selection_source": "FROZEN_OFFLINE_VALIDATION_PROMOTION_DECISION",
            "public_score_read_for_configuration": False,
            "production_output_read_for_configuration": False,
            "production_inference_ground_truth_accessed": False,
            "ground_truth_or_validator_outcomes_used_for_configuration": False,
            "inherited_v19c_post_submission_validator_preserved": True,
            "configuration_mutated_after_selection": False,
            "competition_submit_api_called_by_notebook": False,
        },
    }
    _v20b_runtime_guard = _v20b_validate_runtime_guard()
    _v20b_call_receipt["runtime_guard"] = _v20b_runtime_guard
    _v20b_canonical["runtime_guard"] = _v20b_runtime_guard
    _v20b_scan = _v20b_sensitive_scan(
        {"canonical": _v20b_canonical, "call_receipt": _v20b_call_receipt}
    )
    _v20b_output_audit = {
        "schema_version": "1.0",
        "task_id": _V20B_TASK_ID,
        "status": "PASS",
        "selected_arm": _V20B_SELECTED_ARM,
        "selected_radius_um": _V20B_SELECTED_RADIUS,
        "submission": _v20b_submission,
        "runtime_call_evidence": _v20b_run_stats,
        "runtime_guard": _v20b_runtime_guard,
        "sensitive_information_scan": _v20b_scan,
        "claims_boundary": (
            "Static/runtime identity and output validity only; no Kaggle submission, "
            "acceptance, Public Score, or hidden-test improvement is claimed."
        ),
    }
    _v20b_write_json(
        _V20B_OUTPUT_ROOT / "production_safe_div_call_receipt.json", _v20b_call_receipt
    )
    _v20b_write_json(
        _V20B_OUTPUT_ROOT / "production_canonical_resolved_config.json", _v20b_canonical
    )
    _v20b_write_json(
        _V20B_OUTPUT_ROOT / "production_runtime_guard.json", _v20b_runtime_guard
    )
    _v20b_write_json(
        _V20B_OUTPUT_ROOT / "production_output_audit.json", _v20b_output_audit
    )
    _V20B_PRODUCTION_WATCHDOG_CANCEL.set()
    print("V20B_PRODUCTION_RUNTIME_AUDIT_PASS")
except Exception as _v20b_exc:
    _v20b_started = globals().get("_V20B_PRODUCTION_WALL_STARTED_MONOTONIC")
    _v20b_elapsed = (
        _v20b_time.monotonic() - _v20b_started
        if isinstance(_v20b_started, (int, float))
        else None
    )
    _v20b_failure = {
        "schema_version": "1.0",
        "task_id": _V20B_TASK_ID,
        "status": "FAIL",
        "selected_arm": _V20B_SELECTED_ARM,
        "selected_radius_um": _V20B_SELECTED_RADIUS,
        "error_type": type(_v20b_exc).__name__,
        "error": str(_v20b_exc)[:500],
        "started_at_utc": globals().get("_V20B_PRODUCTION_WALL_STARTED_UTC"),
        "elapsed_wall_clock_seconds": _v20b_elapsed,
        "production_wall_clock_seconds_max": globals().get(
            "_V20B_PRODUCTION_WALL_CLOCK_MAX_SECONDS"
        ),
        "hard_stop_seconds": globals().get("_V20B_PRODUCTION_HARD_STOP_SECONDS"),
        "receipt_reserve_seconds": globals().get(
            "_V20B_PRODUCTION_RECEIPT_RESERVE_SECONDS"
        ),
        "claims_boundary": "No production runtime or submission validity claim is permitted.",
    }
    _v20b_write_json(_V20B_OUTPUT_ROOT / "production_runtime_guard.json", _v20b_failure)
    _v20b_write_json(_V20B_OUTPUT_ROOT / "production_output_audit.json", _v20b_failure)
    _v20b_cancel = globals().get("_V20B_PRODUCTION_WATCHDOG_CANCEL")
    if hasattr(_v20b_cancel, "set"):
        _v20b_cancel.set()
    raise
'''


def render_runtime_bootstrap(contract: dict[str, Any]) -> str:
    runtime_budget = contract["experiment_freeze"]["runtime_budget"]
    if runtime_budget.get(
        "production_wall_clock_seconds_max"
    ) != PRODUCTION_WALL_CLOCK_MAX_SECONDS:
        raise BuildError("production runtime budget differs from frozen contract")
    replacements = {
        "__TASK_ID__": repr(TASK_ID),
        "__PRODUCTION_WALL_CLOCK_MAX_SECONDS__": str(PRODUCTION_WALL_CLOCK_MAX_SECONDS),
        "__PRODUCTION_RECEIPT_RESERVE_SECONDS__": str(PRODUCTION_RECEIPT_RESERVE_SECONDS),
        "__PRODUCTION_HARD_STOP_SECONDS__": str(PRODUCTION_HARD_STOP_SECONDS),
    }
    result = RUNTIME_BOOTSTRAP
    for marker, value in replacements.items():
        if result.count(marker) == 0:
            raise BuildError(f"runtime bootstrap marker absent: {marker}")
        result = result.replace(marker, value)
    leftovers = sorted(set(re.findall(r"__[A-Z][A-Z0-9_]*__", result)))
    if leftovers:
        raise BuildError(f"unresolved runtime bootstrap markers: {leftovers}")
    try:
        compile(result, "<v20b-production-runtime-bootstrap>", "exec")
    except SyntaxError as exc:
        raise BuildError(f"generated production runtime bootstrap does not compile: {exc}") from exc
    if SAMPLE_ID_PATTERN.search(result):
        raise BuildError("generated runtime bootstrap contains a sample/embryo special case")
    return result.rstrip() + "\n"


def render_runtime_audit(
    contract: dict[str, Any],
    selected_arm: str,
    selected_radius: float,
    promotion_binding: dict[str, Any],
    promotion_file_sha256: str,
    promotion_canonical_sha256: str,
) -> str:
    parameter_lines = "\n".join(
        f"        {key!r}: {RUNTIME_PARAMETER_EXPRESSIONS[key]},"
        for key in sorted(RUNTIME_PARAMETER_EXPRESSIONS)
    )
    replacements = {
        "__TASK_ID__": repr(TASK_ID),
        "__SELECTED_ARM__": repr(selected_arm),
        "__SELECTED_RADIUS__": repr(selected_radius),
        "__SOURCE_SHA256__": repr(SOURCE_SHA256),
        "__CONTRACT_SHA256__": repr(canonical_sha256(contract)),
        "__CONTRACT_FILE_SHA256__": repr(CONTRACT_FILE_SHA256),
        "__PROMOTION_FILE_SHA256__": repr(promotion_file_sha256),
        "__PROMOTION_CANONICAL_SHA256__": repr(promotion_canonical_sha256),
        "__PRODUCTION_WALL_CLOCK_MAX_SECONDS__": str(PRODUCTION_WALL_CLOCK_MAX_SECONDS),
        "__PRODUCTION_RECEIPT_RESERVE_SECONDS__": str(PRODUCTION_RECEIPT_RESERVE_SECONDS),
        "__PRODUCTION_HARD_STOP_SECONDS__": str(PRODUCTION_HARD_STOP_SECONDS),
        "__PARAMETERS_JSON__": repr(json.dumps(
            contract["experiment_freeze"]["active_parameters"],
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
        )),
        "__IDENTITIES_JSON__": repr(json.dumps(
            contract["experiment_freeze"]["identities"],
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
        )),
        "__PINNED_DATASET_SOURCES_JSON__": repr(json.dumps(
            pinned_dataset_sources(contract),
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
        )),
        "__PROMOTION_JSON__": repr(json.dumps(
            promotion_binding,
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
        )),
        "__SUPPORT_FILES_JSON__": repr(json.dumps(
            EXPECTED_SUPPORT_FILES, sort_keys=True, allow_nan=False
        )),
        "__SUBMISSION_COLUMNS__": repr(SUBMISSION_COLUMNS),
        "__RUNTIME_PARAMETER_LINES__": parameter_lines,
    }
    result = RUNTIME_AUDIT
    for marker, value in replacements.items():
        if result.count(marker) == 0:
            raise BuildError(f"runtime audit marker absent: {marker}")
        result = result.replace(marker, value)
    leftovers = sorted(set(re.findall(r"__[A-Z][A-Z0-9_]*__", result)))
    if leftovers:
        raise BuildError(f"unresolved runtime audit markers: {leftovers}")
    try:
        compile(result, "<v20b-production-runtime-audit>", "exec")
    except SyntaxError as exc:
        raise BuildError(f"generated production runtime audit does not compile: {exc}") from exc
    if SAMPLE_ID_PATTERN.search(result):
        raise BuildError("generated runtime audit contains a sample/embryo special case")
    return result.rstrip() + "\n"


def _code_cell(source: str, cell_id: str) -> dict[str, Any]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {"v20b_cell_id": cell_id},
        "outputs": [],
        "source": source,
    }


def build_notebook(
    source_notebook: dict[str, Any],
    contract: dict[str, Any],
    selected_arm: str,
    selected_radius: float,
    promotion_binding: dict[str, Any],
    promotion_file_sha256: str,
    promotion_canonical_sha256: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    notebook = copy.deepcopy(source_notebook)
    original_cells = source_notebook["cells"]
    modified_source, changed_line = replace_radius_source(
        original_cells[2]["source"], selected_radius
    )
    notebook["cells"][2]["source"] = modified_source
    bootstrap_source = render_runtime_bootstrap(contract)
    audit_source = render_runtime_audit(
        contract,
        selected_arm,
        selected_radius,
        promotion_binding,
        promotion_file_sha256,
        promotion_canonical_sha256,
    )
    notebook["cells"].insert(
        0,
        _code_cell(
            bootstrap_source,
            "v20b-production-wall-clock-bootstrap",
        ),
    )
    notebook["cells"].append(
        _code_cell(
            audit_source,
            "v20b-production-canonical-and-output-audit",
        )
    )

    if len(notebook["cells"]) != 14:
        raise BuildError(
            "generated production notebook must contain one bootstrap, "
            "12 V19C cells, and one audit cell"
        )
    before_hashes: dict[str, str] = {}
    after_hashes: dict[str, str] = {}
    for index in range(12):
        before = original_cells[index]["source"]
        after = notebook["cells"][index + 1]["source"]
        before_hashes[str(index)] = sha256_bytes(before.encode("utf-8"))
        after_hashes[str(index)] = sha256_bytes(after.encode("utf-8"))
        if index != 2 and before != after:
            raise BuildError(f"V19C source cell {index} changed unexpectedly")
        if original_cells[index].get("cell_type") != notebook["cells"][index + 1].get("cell_type"):
            raise BuildError(f"V19C cell {index} type changed unexpectedly")
        if original_cells[index].get("metadata") != notebook["cells"][index + 1].get("metadata"):
            raise BuildError(f"V19C cell {index} metadata changed unexpectedly")
    changed_cells = [index for index in range(12) if before_hashes[str(index)] != after_hashes[str(index)]]
    if changed_cells != [2]:
        raise BuildError(f"algorithm source changed in unexpected cells: {changed_cells}")
    for index, cell in enumerate(notebook["cells"]):
        if cell.get("cell_type") == "code":
            try:
                compile(cell["source"], f"<v20b-production-cell-{index}>", "exec")
            except SyntaxError as exc:
                raise BuildError(f"generated code cell {index} does not compile: {exc}") from exc

    joined_original = "\n".join(cell["source"] for cell in original_cells)
    joined_generated = "\n".join(cell["source"] for cell in notebook["cells"][1:13])
    for token in (
        'COMP_DIR / "test"', 'SUBMISSION_PATH = WORKING_DIR / "submission.csv"',
        "def list_test_stems()", "_guard_columns", "max_indegree", "max_outdegree",
    ):
        if token not in joined_original or token not in joined_generated:
            raise BuildError(f"formal inference/submission/schema/topology source was not preserved: {token}")
    if joined_original.count('os.environ["BIOHUB_SAFE_DIV_MAX_UM"] = "7.0"') != 1:
        raise BuildError("base notebook radius assignment count is not one")
    expected_new = f'os.environ["BIOHUB_SAFE_DIV_MAX_UM"] = "{selected_radius:.1f}"'
    if joined_generated.count(expected_new) != 1:
        raise BuildError("selected production radius assignment count is not one")

    lineage = {
        "base_notebook": {
            "ref": BASE_NOTEBOOK_REF,
            "version_number": 1,
            "script_version_id": BASE_SCRIPT_VERSION_ID,
            "sha256": SOURCE_SHA256,
            "cell_count": 12,
            "cell_source_sha256": before_hashes,
        },
        "production_notebook": {
            "inherited_cell_count": 12,
            "prepended_wall_clock_bootstrap_cell_count": 1,
            "appended_audit_cell_count": 1,
            "total_cell_count": 14,
            "cell_source_sha256_for_inherited_cells": after_hashes,
            "wall_clock_bootstrap_cell_sha256": sha256_bytes(
                bootstrap_source.encode("utf-8")
            ),
            "audit_cell_sha256": sha256_bytes(audit_source.encode("utf-8")),
        },
        "unique_algorithm_configuration_difference": {
            "cell_index": 2,
            "line_number": changed_line,
            "environment_key": "BIOHUB_SAFE_DIV_MAX_UM",
            "before": "7.0",
            "after": f"{selected_radius:.1f}",
            "contract_parameter": "safe_div_parent_radius_um",
            "changed_inherited_source_cells": [2],
            "changed_inherited_source_line_count": 1,
        },
    }
    return notebook, lineage


def kernel_metadata(
    kernel_slug: str,
    notebook_name: str,
    contract: dict[str, Any],
    selected_arm: str,
) -> dict[str, Any]:
    if not KERNEL_SLUG_PATTERN.fullmatch(kernel_slug):
        raise BuildError("--kernel-slug must be a lowercase owner/slug")
    if kernel_slug in {VALIDATION_KERNEL_SLUG, BASE_NOTEBOOK_REF}:
        raise BuildError("production kernel slug must be independent of validation and V19C")
    if "validation" in kernel_slug.rsplit("/", 1)[1]:
        raise BuildError("production kernel slug must not use a validation slug")
    if Path(notebook_name).name != notebook_name or not notebook_name.endswith(".ipynb"):
        raise BuildError("--notebook-name must be one safe .ipynb basename")
    dataset_sources = pinned_dataset_sources(contract)
    metadata = {
        "id": kernel_slug,
        "title": f"Biohub V20B Radius Production {selected_arm}",
        "code_file": notebook_name,
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": False,
        "dataset_sources": dataset_sources,
        "competition_sources": [COMPETITION],
        "kernel_sources": [],
        "model_sources": [],
        "keywords": ["gpu"],
        "docker_image": FROZEN_DOCKER_IMAGE,
        "machine_shape": FROZEN_MACHINE_SHAPE,
    }
    if metadata["dataset_sources"] != [
        f"{item['ref']}/{item['version']}"
        for item in EXPECTED_INPUT_DATASETS
        if item["role"] != "competition_data"
    ]:
        raise BuildError("kernel metadata version-pinned Dataset refs differ from freeze")
    return metadata


def sensitive_scan(value: Any, label: str) -> dict[str, Any]:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
    patterns = {
        "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
        "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
        "credential_url": re.compile(r"https?://[^/\s:@]+:[^@\s]+@"),
        "private_home": re.compile(r"/(?:Users|home)/[^/\s]+/"),
        "literal_secret": re.compile(
            r"(?:api[_-]?key|password|secret|token)\s*[:=]\s*['\"][^'\"\n]{8,}",
            re.IGNORECASE,
        ),
    }
    findings = sorted(name for name, pattern in patterns.items() if pattern.search(text))
    if findings:
        raise BuildError(f"{label} sensitive-information scan failed: {findings}")
    return {"status": "PASS", "finding_count": 0, "patterns": sorted(patterns)}


def build_manifest_base(
    contract: dict[str, Any],
    contract_raw: bytes,
    promotion: dict[str, Any],
    promotion_raw: bytes,
    promotion_binding: dict[str, Any],
    selected_arm: str,
    selected_radius: float,
    lineage: dict[str, Any],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "task_id": TASK_ID,
        "artifact_role": "CONDITIONALLY_AUTHORIZED_PRODUCTION_NOTEBOOK_BUILD",
        "build_status": "BUILT_STATICALLY_VERIFIED_NOT_EXECUTED",
        "execution_status": "NOT_RUN",
        "platform_status": "NOT_CREATED_BY_THIS_BUILDER",
        "selection": {
            "decision": promotion_binding["decision"],
            "selected_arm": selected_arm,
            "selected_radius_um": selected_radius,
            "selection_source": "FROZEN_OFFLINE_VALIDATION_PROMOTION_DECISION_ONLY",
            "outcome_independent_production_configuration": True,
        },
        "input_hashes": {
            "production_builder_script_sha256": sha256_file(Path(__file__)),
            "v19c_notebook_file_sha256": SOURCE_SHA256,
            "v20b_contract_file_sha256": sha256_bytes(contract_raw),
            "v20b_contract_canonical_sha256": canonical_sha256(contract),
            "validation_promotion_decision_file_sha256": sha256_bytes(promotion_raw),
            "validation_promotion_decision_canonical_sha256": canonical_sha256(promotion),
        },
        "promotion_binding": promotion_binding,
        "source_lineage": lineage,
        "frozen_identities": copy.deepcopy(contract["experiment_freeze"]["identities"]),
        "kernel_metadata_contract": copy.deepcopy(metadata),
        "static_validation": {
            "source_file_sha256": "PASS",
            "all_12_source_cell_hashes_and_types": "PASS",
            "all_inherited_code_cells_ast": "PASS",
            "prepended_wall_clock_bootstrap_ast": "PASS",
            "internal_2670_second_hard_stop_with_30_second_receipt_reserve": "PASS",
            "formal_competition_test_inference_preserved": "PASS",
            "submission_csv_writer_preserved": "PASS",
            "submission_schema_guard_preserved": "PASS",
            "topology_guard_preserved": "PASS",
            "only_parent_radius_changed_in_inherited_source": "PASS",
            "inherited_v19c_post_submission_validator_preserved_but_not_used_for_selection":
                "PASS",
            "appended_runtime_audit_ast": "PASS",
            "appended_sample_or_embryo_special_cases": 0,
        },
        "runtime_audit_contract": {
            "output_root": "/kaggle/working/experiments/V20B",
            "wall_clock": {
                "start_cell_position": 0,
                "production_wall_clock_seconds_max": PRODUCTION_WALL_CLOCK_MAX_SECONDS,
                "internal_hard_stop_seconds": PRODUCTION_HARD_STOP_SECONDS,
                "receipt_reserve_seconds": PRODUCTION_RECEIPT_RESERVE_SECONDS,
                "watchdog_termination_exit_code": 124,
            },
            "required_receipts": [
                "production_safe_div_call_receipt.json",
                "production_canonical_resolved_config.json",
                "production_runtime_guard.json",
                "production_output_audit.json",
            ],
            "submission_path": "/kaggle/working/submission.csv",
            "submission_columns": SUBMISSION_COLUMNS,
            "checks": [
                "post-override full active-parameter identity",
                "safe-division runtime global and per-dataset call evidence",
                "checkpoint content hashes",
                "support-code per-file and manifest identities",
                "frozen version-pinned Dataset refs and runtime mount presence",
                "first-code-cell wall clock start and internal hard-stop receipt",
                "successful elapsed wall clock below the 2670-second hard-stop",
                "submission schema, sentinels, IDs, next-frame edges, indegree and outdegree",
                "output SHA-256 and sensitive-information scan",
            ],
        },
        "authorization_boundary": {
            "training": False,
            "dataset_write": False,
            "model_write": False,
            "kaggle_api_call": False,
            "git_call": False,
            "notebook_source_build_only": True,
            "competition_submission_created_by_notebook": False,
        },
        "external_actions": {
            "kaggle_reads": 0,
            "kaggle_writes": 0,
            "git_reads": 0,
            "git_writes": 0,
            "network_accesses": 0,
            "inference_runs": 0,
            "competition_submissions": 0,
            "retries": 0,
        },
        "claims_boundary": (
            "A local static build is not a Kaggle Notebook Version, completed inference, "
            "competition submission, accepted submission, Public Score, or hidden-test improvement."
        ),
    }


def serialize_json(value: Any, *, indent: int = 2) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        indent=indent,
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8") + b"\n"


def assemble_bundle(
    notebook: dict[str, Any],
    metadata: dict[str, Any],
    manifest_base: dict[str, Any],
    notebook_name: str,
) -> tuple[dict[str, bytes], dict[str, Any]]:
    notebook_bytes = serialize_json(notebook, indent=1)
    metadata_bytes = serialize_json(metadata, indent=2)
    manifest = copy.deepcopy(manifest_base)
    manifest["outputs"] = {
        notebook_name: {
            "bytes": len(notebook_bytes),
            "sha256": sha256_bytes(notebook_bytes),
        },
        "kernel-metadata.json": {
            "bytes": len(metadata_bytes),
            "sha256": sha256_bytes(metadata_bytes),
        },
    }
    scan_scope = {
        "prepended_wall_clock_bootstrap_cell": notebook["cells"][0],
        "appended_audit_cell": notebook["cells"][-1],
        "kernel_metadata": metadata,
        "build_manifest_without_scan": manifest,
    }
    manifest["sensitive_information_scan"] = sensitive_scan(
        scan_scope, "generated production bundle"
    )
    manifest_bytes = serialize_json(manifest, indent=2)
    bundle = {
        notebook_name: notebook_bytes,
        "kernel-metadata.json": metadata_bytes,
        "build_manifest.json": manifest_bytes,
    }
    if set(bundle) != {notebook_name, "kernel-metadata.json", "build_manifest.json"}:
        raise BuildError("production build bundle file set drifted")
    return bundle, manifest


def write_bundle(output_dir: Path, bundle: dict[str, bytes]) -> None:
    if output_dir.exists() and output_dir.is_symlink():
        raise BuildError(f"output directory must not be a symlink: {output_dir}")
    if output_dir.exists() and not output_dir.is_dir():
        raise BuildError(f"output path is not a directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.iterdir()):
        raise BuildError(f"output directory must be empty: {output_dir}")
    for name, payload in bundle.items():
        if Path(name).name != name:
            raise BuildError(f"unsafe output basename: {name}")
        path = output_dir / name
        with path.open("xb") as stream:
            stream.write(payload)
    actual_names = {path.name for path in output_dir.iterdir() if path.is_file()}
    if actual_names != set(bundle):
        raise BuildError(f"written production bundle file set mismatch: {actual_names}")
    for name, payload in bundle.items():
        if sha256_file(output_dir / name) != sha256_bytes(payload):
            raise BuildError(f"written output failed SHA readback: {name}")


def _promotion_fixture(arm: str) -> dict[str, Any]:
    radius = ARMS[arm]
    decision = f"PROMOTE_{arm}_FOR_KAGGLE_TEST"
    gates = {
        candidate: {key: candidate == arm for key in PROMOTION_GATE_KEYS}
        for candidate in ("R80", "R90")
    }
    for candidate in gates:
        gates[candidate]["eligible"] = candidate == arm
    digest = "1" * 64
    return {
        "schema_version": "1.0",
        "task_id": TASK_ID,
        "screen": SCREEN_NAME,
        "decision": decision,
        "selected_arm": arm,
        "selected_radius_um": radius,
        "candidate_label": "Kaggle test candidate",
        "candidate_gates": gates,
        "candidate_details": {
            candidate: {
                "embryo_official_deltas": {},
                "embryo_division_jaccard_deltas": {},
                "macro_delta": 0.0,
                "pooled_delta": 0.0,
                "pooled_division_delta": 0.0,
                "division_tp_delta": 0,
                "division_fp_delta": 0,
                "positive_sample_count": 0,
            }
            for candidate in ("R80", "R90")
        },
        "passing_candidates": [arm],
        "tie_break": {"order": TIE_BREAK_ORDER, "vectors": {}, "unique_winner": arm},
        "cache_equivalence_pass": True,
        "runtime_determinism_pass": True,
        "checkpoint_overlap_status": "CHECKPOINT_TRAINING_OVERLAP_UNKNOWN",
        "competition_submission_created": False,
        "retry_count": 0,
        "validation_script_version_id": 123,
        "identity_bindings": {
            "base_source_sha256": SOURCE_SHA256,
            "contract_canonical_sha256": CONTRACT_CANONICAL_SHA256,
            "contract_file_sha256": CONTRACT_FILE_SHA256,
            "sample_manifest_canonical_sha256": digest,
            "sample_manifest_file_sha256": digest,
            "production_runtime_basis_sha256": PRODUCTION_RUNTIME_BASIS_SHA256,
            "cache_manifest_file_sha256": digest,
            "cache_manifest_sha256": digest,
            "per_sample_metrics_sha256": digest,
            "per_embryo_metrics_sha256": digest,
            "resolved_config_verification_sha256": digest,
            "cache_equivalence_sha256": digest,
            "runtime_determinism_sha256": digest,
        },
        "evidence_hashes": {
            "experiments/V20B/full_sample_payload_inventory.csv": digest,
            "experiments/V20B/full_sample_manifest.json": digest,
            "experiments/V20B/per_sample_metrics.csv": digest,
            "experiments/V20B/per_embryo_metrics.csv": digest,
            "experiments/V20B/paired_deltas_by_sample.csv": digest,
            "experiments/V20B/paired_deltas_by_embryo.csv": digest,
            "experiments/V20B/micro_macro_comparison.csv": digest,
            "experiments/V20B/division_confusion_by_embryo.json": digest,
            "experiments/V20B/topology_validation.json": digest,
            "experiments/V20B/runtime_receipts.json": digest,
            "experiments/V20B/cache_manifest.json": digest,
            "experiments/V20B/cache_equivalence.json": digest,
            "experiments/V20B/runtime_determinism.json": digest,
            "experiments/V20B/resolved_config_verification.json": digest,
        },
        "note": "Offline two-embryo sensitivity screen; not CV and not hidden-test improvement proof.",
    }


def _minimal_contract_for_self_test() -> dict[str, Any]:
    return {
        "experiment_freeze": {
            "active_parameters": {key: None for key in RUNTIME_PARAMETER_EXPRESSIONS},
            "runtime_budget": {
                "production_wall_clock_seconds_max": PRODUCTION_WALL_CLOCK_MAX_SECONDS,
            },
            "identities": {
                "checkpoints": {f"{key}_sha256": value for key, value in EXPECTED_CHECKPOINTS.items()},
                "input_datasets": EXPECTED_INPUT_DATASETS,
                "scorer": EXPECTED_SCORER,
                "support_code_manifest_sha256": SUPPORT_MANIFEST_SHA256,
            },
        }
    }


def self_test() -> None:
    assert canonical_sha256({"b": 2, "a": 1}) == sha256_bytes(b'{"a":1,"b":2}\n')
    synthetic_lines = ["import os\n"] + ["# filler\n"] * 29 + [
        'os.environ["BIOHUB_SAFE_DIV_MAX_UM"] = "7.0"\n'
    ]
    synthetic = "".join(synthetic_lines)
    for radius in (8.0, 9.0):
        replaced, line = replace_radius_source(synthetic, radius)
        assert line == 31
        assert f'BIOHUB_SAFE_DIV_MAX_UM"] = "{radius:.1f}"' in replaced
    duplicate = synthetic + 'os.environ["BIOHUB_SAFE_DIV_MAX_UM"] = "7.0"\n'
    try:
        replace_radius_source(duplicate, 8.0)
    except BuildError:
        pass
    else:
        raise BuildError("duplicate radius self-test did not fail closed")

    # Promotion validation is exercised with the exact canonical contract binding;
    # patch canonical_sha256 only through a wrapper object whose hash field is supplied.
    contract = _minimal_contract_for_self_test()
    for arm in ("R80", "R90"):
        promotion = _promotion_fixture(arm)
        promotion["identity_bindings"]["contract_canonical_sha256"] = canonical_sha256(contract)
        selected, radius, binding = validate_promotion(promotion, contract)
        assert selected == arm and radius == ARMS[arm] and binding["decision"] == promotion["decision"]
    bad = _promotion_fixture("R80")
    bad["identity_bindings"]["contract_canonical_sha256"] = canonical_sha256(contract)
    bad["selected_radius_um"] = 9.0
    try:
        validate_promotion(bad, contract)
    except BuildError:
        pass
    else:
        raise BuildError("promotion radius mismatch self-test did not fail closed")
    bad = _promotion_fixture("R90")
    bad["identity_bindings"]["contract_canonical_sha256"] = canonical_sha256(contract)
    bad["cache_equivalence_pass"] = False
    try:
        validate_promotion(bad, contract)
    except BuildError:
        pass
    else:
        raise BuildError("promotion evidence failure self-test did not fail closed")

    promotion = _promotion_fixture("R80")
    promotion["identity_bindings"]["contract_canonical_sha256"] = canonical_sha256(contract)
    _, _, binding = validate_promotion(promotion, contract)
    contract["experiment_freeze"]["active_parameters"]["safe_div_parent_radius_um"] = "ARM_VALUE_ONLY"
    bootstrap = render_runtime_bootstrap(contract)
    compile(bootstrap, "<v20b-production-bootstrap-self-test>", "exec")
    for token in (
        "_V20B_PRODUCTION_WALL_STARTED_MONOTONIC",
        "_V20B_PRODUCTION_WATCHDOG_CANCEL",
        "_v20b_bootstrap_os._exit(124)",
        "production_runtime_guard.json",
    ):
        if token not in bootstrap:
            raise BuildError(f"runtime bootstrap self-test token missing: {token}")
    audit = render_runtime_audit(
        contract,
        "R80",
        8.0,
        binding,
        "2" * 64,
        "3" * 64,
    )
    compile(audit, "<v20b-production-audit-self-test>", "exec")
    if SAMPLE_ID_PATTERN.search(audit):
        raise BuildError("runtime audit self-test found a sample special case")
    metadata = kernel_metadata(DEFAULT_KERNEL_SLUG, DEFAULT_NOTEBOOK_NAME, contract, "R80")
    assert metadata["is_private"] is True
    assert metadata["enable_gpu"] is True and metadata["enable_internet"] is False
    assert metadata["enable_tpu"] is False
    assert metadata["docker_image"] == FROZEN_DOCKER_IMAGE
    assert metadata["machine_shape"] == FROZEN_MACHINE_SHAPE
    assert metadata["dataset_sources"] == [
        "pilkwang/biohub-deepcenter-unet3d-center-prior-v1/5",
        "pilkwang/biohub-temporal-unet3d-seed314159-v1/2",
        "pilkwang/biohub-tracking-support-pack-50ep-v1/10",
    ]
    assert len(EXPECTED_SUPPORT_FILES) == 13
    assert len(SOURCE_CELLS) == 12 and len(RUNTIME_PARAMETER_EXPRESSIONS) == 88
    print("V20B_PRODUCTION_NOTEBOOK_BUILDER_SELF_TEST_PASS")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-ipynb", type=Path)
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--promotion-decision", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--kernel-slug", default=DEFAULT_KERNEL_SLUG)
    parser.add_argument("--notebook-name", default=DEFAULT_NOTEBOOK_NAME)
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
        "--promotion-decision": args.promotion_decision,
    }
    missing = [name for name, value in required.items() if value is None]
    if missing:
        raise BuildError("missing required arguments: " + ", ".join(missing))

    source_notebook, _source_raw = validate_source(args.source_ipynb)
    contract, contract_raw = load_json_object(args.contract, "V20B contract")
    validate_contract(contract, contract_raw)
    promotion, promotion_raw = load_json_object(
        args.promotion_decision, "V20B validation promotion decision"
    )
    selected_arm, selected_radius, promotion_binding = validate_promotion(
        promotion, contract
    )
    promotion_file_sha = sha256_bytes(promotion_raw)
    promotion_canonical_sha = canonical_sha256(promotion)
    notebook, lineage = build_notebook(
        source_notebook,
        contract,
        selected_arm,
        selected_radius,
        promotion_binding,
        promotion_file_sha,
        promotion_canonical_sha,
    )
    metadata = kernel_metadata(
        args.kernel_slug, args.notebook_name, contract, selected_arm
    )
    manifest_base = build_manifest_base(
        contract,
        contract_raw,
        promotion,
        promotion_raw,
        promotion_binding,
        selected_arm,
        selected_radius,
        lineage,
        metadata,
    )
    bundle, manifest = assemble_bundle(
        notebook, metadata, manifest_base, args.notebook_name
    )
    if args.validate_only:
        print(json.dumps({
            "status": "VALIDATED_NOT_WRITTEN",
            "task_id": TASK_ID,
            "decision": promotion_binding["decision"],
            "selected_arm": selected_arm,
            "selected_radius_um": selected_radius,
            "v19c_source_sha256": SOURCE_SHA256,
            "contract_file_sha256": sha256_bytes(contract_raw),
            "promotion_decision_file_sha256": promotion_file_sha,
            "notebook_sha256": manifest["outputs"][args.notebook_name]["sha256"],
            "external_actions": manifest["external_actions"],
        }, ensure_ascii=False, sort_keys=True))
        print("V20B_PRODUCTION_NOTEBOOK_INPUTS_PASS")
        return 0
    if args.output_dir is None:
        raise BuildError("--output-dir is required unless --validate-only is used")
    write_bundle(args.output_dir, bundle)
    print(json.dumps({
        "status": manifest["build_status"],
        "output_dir": str(args.output_dir),
        "decision": promotion_binding["decision"],
        "selected_arm": selected_arm,
        "selected_radius_um": selected_radius,
        "notebook_sha256": manifest["outputs"][args.notebook_name]["sha256"],
        "kernel_metadata_sha256": manifest["outputs"]["kernel-metadata.json"]["sha256"],
        "execution_status": "NOT_RUN",
        "kaggle_writes": 0,
        "git_writes": 0,
    }, ensure_ascii=False, sort_keys=True))
    print("V20B_PRODUCTION_NOTEBOOK_BUILD_PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BuildError as exc:
        print(f"V20B_PRODUCTION_NOTEBOOK_BUILD_FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
