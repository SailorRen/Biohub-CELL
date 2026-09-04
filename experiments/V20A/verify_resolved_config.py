#!/usr/bin/env python3
"""Fail-closed canonical resolved-configuration verifier for V20A.

No arm was run in this task because the embryo-count gate failed.  This checker
is therefore delivered and self-tested for a future authorized run, but it does
not manufacture a runtime receipt for R70/R80/R90.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path
from typing import Any


ALLOWED_ARMS = {"R70": 7.0, "R80": 8.0, "R90": 9.0}
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
    "safe_div_parent_radius_um",
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
PROHIBITED_KEY = re.compile(
    r"(?:password|passwd|secret|api[_-]?key|access[_-]?token|refresh[_-]?token|cookie)",
    re.IGNORECASE,
)
PROHIBITED_VALUE = re.compile(
    r"(?:/Users/|\\Users\\|\.kaggle/|kaggle\.json|X-Amz-(?:Credential|Signature)|"
    r"gh[pousr]_[A-Za-z0-9]{20,}|Bearer\s+[A-Za-z0-9._~-]{16,})",
    re.IGNORECASE,
)


class ConfigError(RuntimeError):
    pass


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise ConfigError(f"{label} must be a JSON object")
    return value


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


def compare_exact(actual: Any, expected: Any, label: str) -> None:
    if canonical_json(actual) != canonical_json(expected):
        raise ConfigError(f"{label} differs from frozen/active value")


def verify(
    receipt: dict[str, Any],
    active: dict[str, Any],
    call_receipt: dict[str, Any],
    contract: dict[str, Any],
) -> dict[str, Any]:
    required_top = {
        "schema_version",
        "arm",
        "status",
        "capture_phase",
        "canonical_source",
        "parameters",
        "identities",
        "hardware",
        "runtime",
        "outputs",
    }
    missing_top = sorted(required_top - receipt.keys())
    if missing_top:
        raise ConfigError(f"receipt missing top-level fields: {missing_top}")
    arm = receipt["arm"]
    if arm not in ALLOWED_ARMS:
        raise ConfigError(f"unknown arm: {arm}")
    if receipt["status"] != "RUN_COMPLETE":
        raise ConfigError("receipt is not a completed runtime capture")
    if receipt["capture_phase"] != "AFTER_ALL_OVERRIDES_BEFORE_INFERENCE":
        raise ConfigError("receipt was not captured after all runtime overrides")
    if receipt["canonical_source"] != "POST_OVERRIDE_RUNTIME_STATE":
        raise ConfigError("stale Markdown/log print cannot be a canonical source")

    parameters = receipt["parameters"]
    if not isinstance(parameters, dict):
        raise ConfigError("parameters must be an object")
    missing_parameters = sorted(REQUIRED_PARAMETERS - parameters.keys())
    if missing_parameters:
        raise ConfigError(f"receipt missing active parameters: {missing_parameters}")
    if parameters["safe_div_parent_radius_um"] != ALLOWED_ARMS[arm]:
        raise ConfigError("arm and parent-radius value disagree")
    compare_exact(parameters, active.get("parameters"), "active parameters")

    identities = receipt["identities"]
    if not isinstance(identities, dict):
        raise ConfigError("identities must be an object")
    missing_identities = sorted(REQUIRED_IDENTITY_KEYS - identities.keys())
    if missing_identities:
        raise ConfigError(f"receipt missing identities: {missing_identities}")
    frozen = contract.get("experiment_freeze", {})
    expected_identities = frozen.get("identities")
    if not isinstance(expected_identities, dict):
        raise ConfigError("contract lacks frozen identity map")
    compare_exact(identities, expected_identities, "artifact identities")

    call_parameters = call_receipt.get("safe_division_function_arguments")
    if not isinstance(call_parameters, dict):
        raise ConfigError("call receipt lacks safe-division function arguments")
    expected_call = {
        "safe_div_parent_radius_um": parameters["safe_div_parent_radius_um"],
        "safe_div_sister_radius_um": parameters["safe_div_sister_radius_um"],
        "safe_div_divergence_um": parameters["safe_div_divergence_um"],
        "safe_div_frame_cap": parameters["safe_div_frame_cap"],
        "safe_div_global_cap": parameters["safe_div_global_cap"],
        "deepcenter_enabled": parameters["deepcenter_enabled"],
        "deepcenter_safe_div_threshold": parameters[
            "deepcenter_safe_div_threshold"
        ],
    }
    compare_exact(call_parameters, expected_call, "actual safe-division call parameters")

    if not receipt["hardware"] or not receipt["runtime"]:
        raise ConfigError("hardware/runtime identity is empty")
    outputs = receipt["outputs"]
    if not isinstance(outputs, list) or not outputs:
        raise ConfigError("receipt must contain output hashes")
    for index, output in enumerate(outputs):
        if not isinstance(output, dict) or not re.fullmatch(
            r"[0-9a-f]{64}", str(output.get("sha256", ""))
        ):
            raise ConfigError(f"invalid output SHA-256 at outputs/{index}")

    findings = walk_sensitive(receipt)
    if findings:
        raise ConfigError("; ".join(findings))
    return {
        "status": "PASS",
        "arm": arm,
        "canonical_receipt_sha256": hashlib.sha256(canonical_json(receipt)).hexdigest(),
        "checks": [
            "required_fields",
            "post_override_capture",
            "active_parameter_identity",
            "function_call_identity",
            "source_checkpoint_support_input_scorer_identity",
            "hardware_runtime_output_identity",
            "sensitive_material_scan",
        ],
    }


def self_test() -> None:
    identities = {
        "base_source_sha256": "a" * 64,
        "support_code_manifest_sha256": "b" * 64,
        "checkpoints": {"primary": "c" * 64},
        "input_datasets": [{"ref": "owner/data", "version": 1}],
        "scorer": {"commit": "d" * 40, "sha256": "e" * 64},
    }
    parameters = {name: 0 for name in REQUIRED_PARAMETERS}
    parameters.update(
        {
            "safe_div_parent_radius_um": 8.0,
            "safe_div_sister_radius_um": 14.0,
            "safe_div_divergence_um": 2.25,
            "safe_div_frame_cap": 0.0076,
            "safe_div_global_cap": 0.00375,
            "deepcenter_enabled": True,
            "deepcenter_safe_div_threshold": 0.12,
            "random_seed": "UNKNOWN_NOT_EXPLICIT_IN_SOURCE",
        }
    )
    receipt = {
        "schema_version": "1.0",
        "arm": "R80",
        "status": "RUN_COMPLETE",
        "capture_phase": "AFTER_ALL_OVERRIDES_BEFORE_INFERENCE",
        "canonical_source": "POST_OVERRIDE_RUNTIME_STATE",
        "parameters": parameters,
        "identities": identities,
        "hardware": {"accelerator": "self-test"},
        "runtime": {"started_at": "self-test", "duration_seconds": 1},
        "outputs": [{"path": "output.json", "sha256": "f" * 64}],
    }
    active = {"parameters": parameters}
    call = {
        "safe_division_function_arguments": {
            key: parameters[key]
            for key in (
                "safe_div_parent_radius_um",
                "safe_div_sister_radius_um",
                "safe_div_divergence_um",
                "safe_div_frame_cap",
                "safe_div_global_cap",
                "deepcenter_enabled",
                "deepcenter_safe_div_threshold",
            )
        }
    }
    contract = {"experiment_freeze": {"identities": identities}}
    result = verify(receipt, active, call, contract)
    if result["status"] != "PASS":
        raise ConfigError("positive self-test failed")

    negative_cases = []
    missing = json.loads(json.dumps(receipt))
    del missing["parameters"]["detector_threshold"]
    negative_cases.append((missing, active, call, contract))
    wrong_call = json.loads(json.dumps(call))
    wrong_call["safe_division_function_arguments"]["safe_div_parent_radius_um"] = 9.0
    negative_cases.append((receipt, active, wrong_call, contract))
    sensitive = json.loads(json.dumps(receipt))
    sensitive["hardware"]["credential"] = "/Users/example/.kaggle/kaggle.json"
    negative_cases.append((sensitive, active, call, contract))
    for case in negative_cases:
        try:
            verify(*case)
        except ConfigError:
            continue
        raise ConfigError("negative self-test did not fail closed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt")
    parser.add_argument("--active-config")
    parser.add_argument("--call-receipt")
    parser.add_argument("--contract")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        print("V20A_RESOLVED_CONFIG_SELF_TEST_PASS")
        return 0
    required = {
        "--receipt": args.receipt,
        "--active-config": args.active_config,
        "--call-receipt": args.call_receipt,
        "--contract": args.contract,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        parser.error("missing required arguments: " + ", ".join(missing))
    result = verify(
        load_object(Path(args.receipt), "receipt"),
        load_object(Path(args.active_config), "active config"),
        load_object(Path(args.call_receipt), "call receipt"),
        load_object(Path(args.contract), "contract"),
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("V20A_RESOLVED_CONFIG_PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ConfigError as exc:
        print(f"V20A_RESOLVED_CONFIG_FAIL: {exc}")
        raise SystemExit(1)
