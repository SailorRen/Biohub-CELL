#!/usr/bin/env python3
"""Fail-closed resolved-config and shared-cache verifier for V20B.

The verifier consumes three runtime evidence sets, one for each of R70/R80/R90.
It does not run inference or contact Kaggle.  Each evidence set consists of:

* a canonical resolved receipt captured after every override and before inference;
* an active-config dump from the same capture point; and
* a receipt captured at the actual safe-division function call.

The canonical receipt must contain a ``pre_division_cache`` object with this
shape (all SHA-256 values are lowercase hexadecimal):

```
{
  "status": "COMPLETE",
  "sample_count": 2,
  "identity_binding_sha256": "...",
  "pre_division_config_sha256": "...",
  "manifest_sha256": "...",
  "entries": [
    {
      "sample_id": "44b6_example",
      "embryo_id": "44b6",
      "source_sha256": "...",
      "checkpoints": {"primary_sha256": "..."},
      "support_code_manifest_sha256": "...",
      "input_identity": {"sample_payload_sha256": "..."},
      "pre_division_config_sha256": "...",
      "graph_count": 1,
      "node_count": 1,
      "edge_count": 0,
      "cache_sha256": "..."
    }
  ]
}
```

``manifest_sha256`` is recomputed from entries sorted by ``sample_id``.
``identity_binding_sha256`` binds the complete frozen identity object, while
``pre_division_config_sha256`` binds every active parameter except the sole
downstream arm variable ``safe_div_parent_radius_um``.  The normalized cache
object must then be byte-identical across all three arms.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any


TASK_ID = "CODEX_20260904_BIOHUB_V20B_TWO_EMBRYO_PAIRED_RADIUS"
RADIUS_KEY = "safe_div_parent_radius_um"
ALLOWED_ARMS = {"R70": 7.0, "R80": 8.0, "R90": 9.0}
ALLOWED_EMBRYOS = {"44b6", "6bba"}
POST_OVERRIDE_PHASE = "AFTER_ALL_OVERRIDES_BEFORE_INFERENCE"
POST_OVERRIDE_SOURCE = "POST_OVERRIDE_RUNTIME_STATE"
CALL_CAPTURE_PHASE = "AT_SAFE_DIVISION_CALL"

REQUIRED_PARAMETERS = {
    "detector_threshold",
    "secondary_detection_weight",
    "retention_threshold",
    "edge_threshold",
    "secondary_edge_weight",
    "bidirectional_weight",
    "fusion_mode",
    "gap_close_distance_um",
    "minimum_track_length",
    RADIUS_KEY,
    "safe_div_sister_radius_um",
    "safe_div_divergence_um",
    "deepcenter_enabled",
    "deepcenter_gap_threshold",
    "deepcenter_safe_div_threshold",
    "safe_div_frame_cap",
    "safe_div_global_cap",
    "ilp_enabled",
    "ilp_edge_weight",
    "ilp_appearance_weight",
    "ilp_disappearance_weight",
    "ilp_division_weight",
    "random_seed",
}
REQUIRED_IDENTITY_KEYS = {
    "base_source_sha256",
    "support_code_manifest_sha256",
    "checkpoints",
    "input_datasets",
    "scorer",
}
CALL_PARAMETER_KEYS = (
    RADIUS_KEY,
    "safe_div_sister_radius_um",
    "safe_div_divergence_um",
    "safe_div_frame_cap",
    "safe_div_global_cap",
    "deepcenter_enabled",
    "deepcenter_safe_div_threshold",
)
REQUIRED_CACHE_ENTRY_KEYS = {
    "sample_id",
    "embryo_id",
    "source_sha256",
    "checkpoints",
    "support_code_manifest_sha256",
    "input_identity",
    "pre_division_config_sha256",
    "graph_count",
    "node_count",
    "edge_count",
    "cache_sha256",
}

HEX_SHA256 = re.compile(r"[0-9a-f]{64}")
HEX_GIT_COMMIT = re.compile(r"[0-9a-f]{40}")
PROHIBITED_KEY = re.compile(
    r"(?:password|passwd|secret|credential|api[_-]?key|access[_-]?token|"
    r"refresh[_-]?token|cookie)",
    re.IGNORECASE,
)
PROHIBITED_VALUE = re.compile(
    r"(?:/Users/|\\Users\\|\.kaggle/|kaggle\.json|"
    r"X-Amz-(?:Credential|Signature)|gh[pousr]_[A-Za-z0-9]{20,}|"
    r"Bearer\s+[A-Za-z0-9._~-]{16,})",
    re.IGNORECASE,
)


class ConfigError(RuntimeError):
    """Raised when any required identity or runtime invariant is not proven."""


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise ConfigError(f"{label} must be a JSON object")
    return value


def compare_exact(actual: Any, expected: Any, label: str) -> None:
    if canonical_json(actual) != canonical_json(expected):
        raise ConfigError(f"{label} differs from frozen/canonical value")


def require_sha256(value: Any, label: str) -> str:
    text = str(value)
    if not HEX_SHA256.fullmatch(text):
        raise ConfigError(f"{label} is not a lowercase SHA-256")
    return text


def validate_declared_hashes(value: Any, pointer: str) -> None:
    """Reject malformed values for every field explicitly named as SHA-256."""

    if isinstance(value, dict):
        for key, child in value.items():
            child_pointer = f"{pointer}/{key}"
            if str(key).lower().endswith("sha256"):
                require_sha256(child, child_pointer)
            else:
                validate_declared_hashes(child, child_pointer)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_declared_hashes(child, f"{pointer}/{index}")


def walk_sensitive(value: Any, pointer: str = "") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_pointer = f"{pointer}/{key}"
            if PROHIBITED_KEY.search(str(key)):
                findings.append(f"prohibited key at {child_pointer}")
            findings.extend(walk_sensitive(child, child_pointer))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(walk_sensitive(child, f"{pointer}/{index}"))
    elif isinstance(value, str) and PROHIBITED_VALUE.search(value):
        findings.append(f"prohibited value at {pointer}")
    return findings


def frozen_contract_parts(
    contract: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if contract.get("task_id") != TASK_ID:
        raise ConfigError("contract task_id does not identify V20B")
    frozen = contract.get("experiment_freeze")
    if not isinstance(frozen, dict):
        raise ConfigError("contract lacks experiment_freeze")

    identities = frozen.get("identities")
    if not isinstance(identities, dict):
        raise ConfigError("contract lacks frozen identities")
    missing_identities = sorted(REQUIRED_IDENTITY_KEYS - identities.keys())
    if missing_identities:
        raise ConfigError(f"contract identities missing: {missing_identities}")
    validate_declared_hashes(identities, "/contract/experiment_freeze/identities")
    scorer_commit = identities.get("scorer", {}).get("commit")
    if not HEX_GIT_COMMIT.fullmatch(str(scorer_commit)):
        raise ConfigError("contract scorer commit is not a full Git commit")

    parameters = frozen.get("active_parameters")
    if not isinstance(parameters, dict):
        raise ConfigError("contract lacks frozen active_parameters")
    missing_parameters = sorted(REQUIRED_PARAMETERS - parameters.keys())
    if missing_parameters:
        raise ConfigError(f"contract active_parameters missing: {missing_parameters}")
    if parameters.get(RADIUS_KEY) != "ARM_VALUE_ONLY":
        raise ConfigError(f"contract {RADIUS_KEY} must be ARM_VALUE_ONLY")

    arms = frozen.get("arms")
    if not isinstance(arms, dict) or set(arms) != set(ALLOWED_ARMS):
        raise ConfigError("contract must freeze exactly R70/R80/R90")
    for arm, radius in ALLOWED_ARMS.items():
        if not isinstance(arms[arm], dict) or arms[arm].get(RADIUS_KEY) != radius:
            raise ConfigError(f"contract arm value mismatch for {arm}")
    return parameters, identities


def expected_parameters_for_arm(
    frozen_parameters: dict[str, Any], arm: str
) -> dict[str, Any]:
    expected = copy.deepcopy(frozen_parameters)
    expected[RADIUS_KEY] = ALLOWED_ARMS[arm]
    return expected


def validate_identity_shape(identities: dict[str, Any]) -> None:
    require_sha256(identities.get("base_source_sha256"), "base source")
    require_sha256(
        identities.get("support_code_manifest_sha256"), "support-code manifest"
    )
    checkpoints = identities.get("checkpoints")
    if not isinstance(checkpoints, dict) or not checkpoints:
        raise ConfigError("checkpoint identity map is empty")
    for key, digest in checkpoints.items():
        require_sha256(digest, f"checkpoint {key}")
    datasets = identities.get("input_datasets")
    if not isinstance(datasets, list) or not datasets:
        raise ConfigError("input Dataset identity list is empty")
    scorer = identities.get("scorer")
    if not isinstance(scorer, dict) or not scorer:
        raise ConfigError("scorer identity is empty")


def validate_cache(
    cache: Any,
    parameters: dict[str, Any],
    identities: dict[str, Any],
    arm: str,
) -> dict[str, Any]:
    if not isinstance(cache, dict):
        raise ConfigError(f"{arm} pre_division_cache must be an object")
    if cache.get("status") != "COMPLETE":
        raise ConfigError(f"{arm} pre-division cache is not COMPLETE")

    entries = cache.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ConfigError(f"{arm} pre-division cache entries are empty")
    if cache.get("sample_count") != len(entries):
        raise ConfigError(f"{arm} cache sample_count differs from entries")

    identity_sha = canonical_sha256(identities)
    if cache.get("identity_binding_sha256") != identity_sha:
        raise ConfigError(f"{arm} cache identity binding differs from runtime identities")
    invariant_parameters = copy.deepcopy(parameters)
    invariant_parameters.pop(RADIUS_KEY, None)
    invariant_sha = canonical_sha256(invariant_parameters)
    if cache.get("pre_division_config_sha256") != invariant_sha:
        raise ConfigError(f"{arm} cache pre-division config binding is stale")

    normalized_entries: list[dict[str, Any]] = []
    seen_samples: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ConfigError(f"{arm} cache entry {index} must be an object")
        missing = sorted(REQUIRED_CACHE_ENTRY_KEYS - entry.keys())
        if missing:
            raise ConfigError(f"{arm} cache entry {index} missing: {missing}")
        sample_id = entry.get("sample_id")
        embryo_id = entry.get("embryo_id")
        if not isinstance(sample_id, str) or not sample_id:
            raise ConfigError(f"{arm} cache entry {index} has no sample_id")
        if sample_id in seen_samples:
            raise ConfigError(f"{arm} cache contains duplicate sample {sample_id}")
        seen_samples.add(sample_id)
        if embryo_id not in ALLOWED_EMBRYOS or not sample_id.startswith(f"{embryo_id}_"):
            raise ConfigError(f"{arm} cache sample/embryo identity mismatch: {sample_id}")
        if entry.get("source_sha256") != identities.get("base_source_sha256"):
            raise ConfigError(f"{arm} cache source identity mismatch for {sample_id}")
        compare_exact(
            entry.get("checkpoints"),
            identities.get("checkpoints"),
            f"{arm} cache checkpoints for {sample_id}",
        )
        if entry.get("support_code_manifest_sha256") != identities.get(
            "support_code_manifest_sha256"
        ):
            raise ConfigError(f"{arm} cache support-code mismatch for {sample_id}")
        input_identity = entry.get("input_identity")
        if not isinstance(input_identity, (dict, str)) or not input_identity:
            raise ConfigError(f"{arm} cache input identity is empty for {sample_id}")
        validate_declared_hashes(input_identity, f"/{arm}/cache/{sample_id}/input_identity")
        if entry.get("pre_division_config_sha256") != invariant_sha:
            raise ConfigError(f"{arm} cache config mismatch for {sample_id}")
        for count_key in ("graph_count", "node_count", "edge_count"):
            count = entry.get(count_key)
            if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                raise ConfigError(
                    f"{arm} cache {count_key} invalid for {sample_id}: {count!r}"
                )
        require_sha256(entry.get("cache_sha256"), f"{arm} cache SHA for {sample_id}")
        normalized_entries.append(copy.deepcopy(entry))

    normalized_entries.sort(key=lambda row: row["sample_id"])
    manifest_sha = canonical_sha256(normalized_entries)
    if cache.get("manifest_sha256") != manifest_sha:
        raise ConfigError(f"{arm} cache manifest SHA does not match its entries")

    return {
        "status": "COMPLETE",
        "sample_count": len(normalized_entries),
        "identity_binding_sha256": identity_sha,
        "pre_division_config_sha256": invariant_sha,
        "manifest_sha256": manifest_sha,
        "entries": normalized_entries,
    }


def validate_outputs(outputs: Any, arm: str) -> None:
    if not isinstance(outputs, list) or not outputs:
        raise ConfigError(f"{arm} receipt must contain output hashes")
    paths: set[str] = set()
    for index, output in enumerate(outputs):
        if not isinstance(output, dict):
            raise ConfigError(f"{arm} output {index} must be an object")
        path = output.get("path")
        if not isinstance(path, str) or not path or path in paths:
            raise ConfigError(f"{arm} output path {index} is missing or duplicated")
        paths.add(path)
        require_sha256(output.get("sha256"), f"{arm} output SHA at {index}")


def verify_arm(
    arm: str,
    receipt: dict[str, Any],
    active: dict[str, Any],
    call_receipt: dict[str, Any],
    frozen_parameters: dict[str, Any],
    frozen_identities: dict[str, Any],
) -> dict[str, Any]:
    required_top = {
        "schema_version",
        "task_id",
        "arm",
        "status",
        "capture_phase",
        "canonical_source",
        "parameters",
        "identities",
        "pre_division_cache",
        "hardware",
        "runtime",
        "outputs",
    }
    missing_top = sorted(required_top - receipt.keys())
    if missing_top:
        raise ConfigError(f"{arm} receipt missing top-level fields: {missing_top}")
    if receipt.get("task_id") != TASK_ID or receipt.get("arm") != arm:
        raise ConfigError(f"{arm} receipt task/arm identity mismatch")
    if receipt.get("status") != "RUN_COMPLETE":
        raise ConfigError(f"{arm} receipt is not RUN_COMPLETE")
    if receipt.get("capture_phase") != POST_OVERRIDE_PHASE:
        raise ConfigError(f"{arm} receipt was not captured after all overrides")
    if receipt.get("canonical_source") != POST_OVERRIDE_SOURCE:
        raise ConfigError(f"{arm} receipt is not canonical post-override state")

    parameters = receipt.get("parameters")
    if not isinstance(parameters, dict):
        raise ConfigError(f"{arm} parameters must be an object")
    expected_parameters = expected_parameters_for_arm(frozen_parameters, arm)
    compare_exact(parameters, expected_parameters, f"{arm} active parameters vs contract")
    if parameters.get(RADIUS_KEY) != ALLOWED_ARMS[arm]:
        raise ConfigError(f"{arm} and parent-radius value disagree")

    if active.get("task_id") != TASK_ID or active.get("arm") != arm:
        raise ConfigError(f"{arm} active-config task/arm identity mismatch")
    if active.get("capture_phase") != POST_OVERRIDE_PHASE:
        raise ConfigError(f"{arm} active-config capture phase is stale")
    compare_exact(parameters, active.get("parameters"), f"{arm} active-config dump")

    identities = receipt.get("identities")
    if not isinstance(identities, dict):
        raise ConfigError(f"{arm} identities must be an object")
    missing_identities = sorted(REQUIRED_IDENTITY_KEYS - identities.keys())
    if missing_identities:
        raise ConfigError(f"{arm} receipt identities missing: {missing_identities}")
    validate_identity_shape(identities)
    validate_declared_hashes(identities, f"/{arm}/identities")
    compare_exact(identities, frozen_identities, f"{arm} artifact identities")

    if call_receipt.get("task_id") != TASK_ID or call_receipt.get("arm") != arm:
        raise ConfigError(f"{arm} call receipt task/arm identity mismatch")
    if call_receipt.get("capture_phase") != CALL_CAPTURE_PHASE:
        raise ConfigError(f"{arm} call receipt was not captured at the function call")
    call_parameters = call_receipt.get("safe_division_function_arguments")
    if not isinstance(call_parameters, dict):
        raise ConfigError(f"{arm} call receipt lacks safe-division arguments")
    expected_call = {key: parameters[key] for key in CALL_PARAMETER_KEYS}
    compare_exact(call_parameters, expected_call, f"{arm} safe-division call parameters")

    if not isinstance(receipt.get("hardware"), dict) or not receipt["hardware"]:
        raise ConfigError(f"{arm} hardware identity is empty")
    if not isinstance(receipt.get("runtime"), dict) or not receipt["runtime"]:
        raise ConfigError(f"{arm} runtime identity is empty")
    validate_outputs(receipt.get("outputs"), arm)
    cache = validate_cache(receipt.get("pre_division_cache"), parameters, identities, arm)

    sensitive_findings: list[str] = []
    for label, value in (
        ("receipt", receipt),
        ("active_config", active),
        ("call_receipt", call_receipt),
    ):
        sensitive_findings.extend(
            f"{label}: {finding}" for finding in walk_sensitive(value)
        )
    if sensitive_findings:
        raise ConfigError("; ".join(sensitive_findings))

    return {
        "arm": arm,
        "canonical_receipt_sha256": canonical_sha256(receipt),
        "parameters": copy.deepcopy(parameters),
        "identities": copy.deepcopy(identities),
        "pre_division_cache": cache,
    }


def verify_all(
    receipts: dict[str, dict[str, Any]],
    active_configs: dict[str, dict[str, Any]],
    call_receipts: dict[str, dict[str, Any]],
    contract: dict[str, Any],
) -> dict[str, Any]:
    expected_arms = set(ALLOWED_ARMS)
    for label, mapping in (
        ("receipts", receipts),
        ("active configs", active_configs),
        ("call receipts", call_receipts),
    ):
        if set(mapping) != expected_arms:
            raise ConfigError(f"{label} must contain exactly R70/R80/R90")

    frozen_parameters, frozen_identities = frozen_contract_parts(contract)
    results = {
        arm: verify_arm(
            arm,
            receipts[arm],
            active_configs[arm],
            call_receipts[arm],
            frozen_parameters,
            frozen_identities,
        )
        for arm in ALLOWED_ARMS
    }

    baseline = results["R70"]
    baseline_invariant = copy.deepcopy(baseline["parameters"])
    baseline_invariant.pop(RADIUS_KEY)
    baseline_cache = baseline["pre_division_cache"]
    baseline_identities = baseline["identities"]
    for arm in ("R80", "R90"):
        invariant = copy.deepcopy(results[arm]["parameters"])
        invariant.pop(RADIUS_KEY)
        compare_exact(invariant, baseline_invariant, f"{arm} non-radius parameters")
        compare_exact(results[arm]["identities"], baseline_identities, f"{arm} identities")
        compare_exact(
            results[arm]["pre_division_cache"],
            baseline_cache,
            f"{arm} shared pre-division cache",
        )

    return {
        "status": "PASS",
        "task_id": TASK_ID,
        "arms": {
            arm: {
                RADIUS_KEY: ALLOWED_ARMS[arm],
                "canonical_receipt_sha256": results[arm][
                    "canonical_receipt_sha256"
                ],
            }
            for arm in ALLOWED_ARMS
        },
        "shared_pre_division_cache_manifest_sha256": baseline_cache[
            "manifest_sha256"
        ],
        "checks": [
            "frozen_contract_identity",
            "post_override_capture",
            "active_config_identity",
            "actual_safe_division_call_identity",
            "source_checkpoint_support_input_scorer_identity",
            "cross_arm_only_parent_radius_differs",
            "shared_pre_division_cache_identity",
            "output_sha256",
            "sensitive_material_scan",
        ],
    }


def arm_mapping(specs: list[str], label: str) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for spec in specs:
        explicit_arm: str | None = None
        path_text = spec
        if "=" in spec:
            candidate, path_text = spec.split("=", 1)
            if candidate not in ALLOWED_ARMS:
                raise ConfigError(f"invalid {label} arm prefix: {candidate}")
            explicit_arm = candidate
        value = load_object(Path(path_text), f"{label} {path_text}")
        arm = explicit_arm or value.get("arm")
        if arm not in ALLOWED_ARMS:
            raise ConfigError(f"cannot identify arm for {label} {path_text}")
        if value.get("arm") != arm:
            raise ConfigError(f"{label} path prefix and object arm disagree: {path_text}")
        if arm in mapping:
            raise ConfigError(f"duplicate {label} for {arm}")
        mapping[arm] = value
    return mapping


def make_self_test_bundle() -> tuple[
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, Any],
]:
    identities = {
        "base_source_sha256": "a" * 64,
        "support_code_manifest_sha256": "b" * 64,
        "checkpoints": {
            "primary_sha256": "c" * 64,
            "secondary_sha256": "d" * 64,
            "deepcenter_sha256": "e" * 64,
        },
        "input_datasets": [
            {
                "ref": "owner/data",
                "version": 1,
                "canonical_file_metadata_sha256": "f" * 64,
            }
        ],
        "scorer": {"commit": "1" * 40, "metrics_sha256": "2" * 64},
    }
    frozen_parameters = {name: 0 for name in REQUIRED_PARAMETERS}
    frozen_parameters.update(
        {
            RADIUS_KEY: "ARM_VALUE_ONLY",
            "safe_div_sister_radius_um": 14.0,
            "safe_div_divergence_um": 2.25,
            "safe_div_frame_cap": 0.0076,
            "safe_div_global_cap": 0.00375,
            "deepcenter_enabled": True,
            "deepcenter_safe_div_threshold": 0.12,
            "fusion_mode": "harmonic_probability",
            "random_seed": "UNKNOWN_NOT_EXPLICIT_IN_SOURCE",
        }
    )
    contract = {
        "schema_version": "1.0",
        "task_id": TASK_ID,
        "experiment_freeze": {
            "identities": identities,
            "active_parameters": frozen_parameters,
            "arms": {
                arm: {RADIUS_KEY: radius, "role": "control" if arm == "R70" else "candidate"}
                for arm, radius in ALLOWED_ARMS.items()
            },
        },
    }

    identity_binding_sha = canonical_sha256(identities)
    invariant_parameters = copy.deepcopy(frozen_parameters)
    invariant_parameters.pop(RADIUS_KEY)
    invariant_sha = canonical_sha256(invariant_parameters)
    entries = []
    for index, (sample_id, embryo_id) in enumerate(
        (("44b6_anchor", "44b6"), ("6bba_anchor", "6bba")), start=3
    ):
        entries.append(
            {
                "sample_id": sample_id,
                "embryo_id": embryo_id,
                "source_sha256": identities["base_source_sha256"],
                "checkpoints": identities["checkpoints"],
                "support_code_manifest_sha256": identities[
                    "support_code_manifest_sha256"
                ],
                "input_identity": {"sample_payload_sha256": str(index) * 64},
                "pre_division_config_sha256": invariant_sha,
                "graph_count": 1,
                "node_count": index,
                "edge_count": index - 1,
                "cache_sha256": str(index + 2) * 64,
            }
        )
    entries.sort(key=lambda row: row["sample_id"])
    cache = {
        "status": "COMPLETE",
        "sample_count": len(entries),
        "identity_binding_sha256": identity_binding_sha,
        "pre_division_config_sha256": invariant_sha,
        "manifest_sha256": canonical_sha256(entries),
        "entries": entries,
    }

    receipts: dict[str, dict[str, Any]] = {}
    active_configs: dict[str, dict[str, Any]] = {}
    call_receipts: dict[str, dict[str, Any]] = {}
    output_digests = {"R70": "7" * 64, "R80": "8" * 64, "R90": "9" * 64}
    for arm, radius in ALLOWED_ARMS.items():
        parameters = copy.deepcopy(frozen_parameters)
        parameters[RADIUS_KEY] = radius
        receipts[arm] = {
            "schema_version": "1.0",
            "task_id": TASK_ID,
            "arm": arm,
            "status": "RUN_COMPLETE",
            "capture_phase": POST_OVERRIDE_PHASE,
            "canonical_source": POST_OVERRIDE_SOURCE,
            "parameters": parameters,
            "identities": copy.deepcopy(identities),
            "pre_division_cache": copy.deepcopy(cache),
            "hardware": {"accelerator": "self-test"},
            "runtime": {"duration_seconds": 1},
            "outputs": [
                {"path": f"outputs/{arm}.json", "sha256": output_digests[arm]}
            ],
        }
        active_configs[arm] = {
            "schema_version": "1.0",
            "task_id": TASK_ID,
            "arm": arm,
            "capture_phase": POST_OVERRIDE_PHASE,
            "parameters": copy.deepcopy(parameters),
        }
        call_receipts[arm] = {
            "schema_version": "1.0",
            "task_id": TASK_ID,
            "arm": arm,
            "capture_phase": CALL_CAPTURE_PHASE,
            "safe_division_function_arguments": {
                key: parameters[key] for key in CALL_PARAMETER_KEYS
            },
        }
    return receipts, active_configs, call_receipts, contract


def self_test() -> None:
    receipts, active_configs, call_receipts, contract = make_self_test_bundle()
    result = verify_all(receipts, active_configs, call_receipts, contract)
    if result.get("status") != "PASS":
        raise ConfigError("positive self-test failed")

    negative_cases: list[
        tuple[
            str,
            dict[str, dict[str, Any]],
            dict[str, dict[str, Any]],
            dict[str, dict[str, Any]],
            dict[str, Any],
        ]
    ] = []

    changed_cache = copy.deepcopy(receipts)
    changed_cache["R90"]["pre_division_cache"]["entries"][0]["cache_sha256"] = "0" * 64
    changed_cache["R90"]["pre_division_cache"]["manifest_sha256"] = canonical_sha256(
        sorted(
            changed_cache["R90"]["pre_division_cache"]["entries"],
            key=lambda row: row["sample_id"],
        )
    )
    negative_cases.append(
        (
            "cross-arm cache drift",
            changed_cache,
            copy.deepcopy(active_configs),
            copy.deepcopy(call_receipts),
            copy.deepcopy(contract),
        )
    )

    changed_parameter = copy.deepcopy(receipts)
    changed_active = copy.deepcopy(active_configs)
    changed_contract = copy.deepcopy(contract)
    changed_parameter["R80"]["parameters"]["detector_threshold"] = 0.5
    changed_active["R80"]["parameters"]["detector_threshold"] = 0.5
    negative_cases.append(
        (
            "non-radius parameter drift",
            changed_parameter,
            changed_active,
            copy.deepcopy(call_receipts),
            changed_contract,
        )
    )

    wrong_identity = copy.deepcopy(receipts)
    wrong_identity["R80"]["identities"]["base_source_sha256"] = "0" * 64
    negative_cases.append(
        (
            "source identity drift",
            wrong_identity,
            copy.deepcopy(active_configs),
            copy.deepcopy(call_receipts),
            copy.deepcopy(contract),
        )
    )

    wrong_call = copy.deepcopy(call_receipts)
    wrong_call["R80"]["safe_division_function_arguments"][RADIUS_KEY] = 9.0
    negative_cases.append(
        (
            "function-call drift",
            copy.deepcopy(receipts),
            copy.deepcopy(active_configs),
            wrong_call,
            copy.deepcopy(contract),
        )
    )

    invalid_output = copy.deepcopy(receipts)
    invalid_output["R70"]["outputs"][0]["sha256"] = "not-a-sha"
    negative_cases.append(
        (
            "invalid output SHA",
            invalid_output,
            copy.deepcopy(active_configs),
            copy.deepcopy(call_receipts),
            copy.deepcopy(contract),
        )
    )

    sensitive = copy.deepcopy(receipts)
    sensitive["R70"]["runtime"]["credential_path"] = "/Users/example/.kaggle/kaggle.json"
    negative_cases.append(
        (
            "sensitive material",
            sensitive,
            copy.deepcopy(active_configs),
            copy.deepcopy(call_receipts),
            copy.deepcopy(contract),
        )
    )

    for label, case_receipts, case_active, case_calls, case_contract in negative_cases:
        try:
            verify_all(case_receipts, case_active, case_calls, case_contract)
        except ConfigError:
            continue
        raise ConfigError(f"negative self-test did not fail closed: {label}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", action="append", default=[], metavar="[ARM=]PATH")
    parser.add_argument(
        "--active-config", action="append", default=[], metavar="[ARM=]PATH"
    )
    parser.add_argument(
        "--call-receipt", action="append", default=[], metavar="[ARM=]PATH"
    )
    parser.add_argument("--contract")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        print("V20B_RESOLVED_CONFIG_SELF_TEST_PASS")
        return 0
    if not args.contract:
        parser.error("--contract is required unless --self-test is used")

    contract = load_object(Path(args.contract), "contract")
    result = verify_all(
        arm_mapping(args.receipt, "receipt"),
        arm_mapping(args.active_config, "active config"),
        arm_mapping(args.call_receipt, "call receipt"),
        contract,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("V20B_RESOLVED_CONFIG_PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ConfigError as exc:
        print(f"V20B_RESOLVED_CONFIG_FAIL: {exc}")
        raise SystemExit(1)
