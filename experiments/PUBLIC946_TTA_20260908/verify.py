#!/usr/bin/env python3
"""PUBLIC946 批次只读验收；不运行模型、不写平台、不修改被验收材料。

--local 检查冻结构建和实际本地测试；--final 另检查普通运行、正式成绩、
比较算术和交付证明。缺分不能通过正式结果门禁。JSON 输出由调用者保存。
--remote-receipt 可指向最后固定提交的独立远端回读证明，避免自引用提交。
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = Path(__file__).resolve().parent
TASK = ROOT / "tasks/CODEX_20260908_BIOHUB_PUBLIC946_TTA_OPTIMIZATION_TASK.md"
ARMS = ("B0", "C1", "C2")
PUBLIC_SHA = "521cb97f0f457643379a51b60c4f71e3f4cc7d1823fd98cbb97633ffaa515ec4"
FROZEN_MANIFEST_SHA = "e126e7fff52941518b70a3dc3c8e9523a804f7fcffdd511079c63f6f098831e7"
WEIGHTS = {
    "primary": "12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771",
    "secondary": "9bac2fa0dadc4a6fc1899e0caf187f4b553e0a7cd90ba1261a68b35ffe9e305f",
    "deepcenter": "8040999a92f6b7bbd98fa8cf458141e045c0f9ad7c936bdb3b18e1f7edafe2a0",
}
LIMITS = {"new_notebooks": 3, "save_requests": 4, "submission_requests": 3,
          "shared_repairs": 1, "per_object_submission": 1}


def require(value, message):
    if not value:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def text_source(cell):
    return cell["source"] if isinstance(cell["source"], str) else "".join(cell["source"])


def timestamp(value):
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    require(parsed.tzinfo is not None, "Observation/freeze timestamp lacks timezone")
    return parsed


def artifact(value, arm=None, json_lines=False):
    """Read a named local receipt and verify its stored hash when declared."""
    if isinstance(value, dict) and "path" not in value:
        return value
    path_text = value["path"] if isinstance(value, dict) else value
    path = Path(path_text)
    choices = [path] if path.is_absolute() else [ROOT / path, BATCH / path]
    if arm:
        choices.append(BATCH / arm / path.name)
    found = next((item for item in choices if item.is_file()), None)
    require(found is not None, f"Missing receipt: {path_text}")
    if isinstance(value, dict) and "sha256" in value:
        require(sha(found) == value["sha256"], f"Receipt hash mismatch: {found}")
    if json_lines:
        return [json.loads(line) for line in found.read_text().splitlines() if line.strip()]
    return load(found)


def source_and_build():
    import build_candidates as builder
    from tta_patch import patch_expanded_predictor
    public = builder.load_public()
    receipt = load(BATCH / "build_receipt.json")
    require(receipt["public_ref"] == "redoctopusk/biohub-942tta" and receipt["public_version"] == 1
            and receipt["public_script_version_id"] == 347821442 and receipt["public_sha256"] == PUBLIC_SHA,
            "Frozen public Notebook identity differs")
    require(sha(builder.SUPPORT) == receipt["support_predictor_sha256"], "Support predictor bytes differ")
    expanded, anchors = builder.expand_public_predictor(builder.SUPPORT.read_text(), public)
    require(builder.sha(expanded) == receipt["public_expanded_sha256"], "Public expansion differs")
    require(anchors == receipt["public_patch_anchors"], "Dynamic anchor receipts differ")
    patch_text, runtime = (BATCH / "tta_patch.py").read_text(), (BATCH / "runtime_audit.py").read_text()
    final = (BATCH / "final_audit.py").read_text() + "\npublic946_final_audit(globals())\n"
    require(builder.sha(runtime) == receipt["common_audit"]["runtime_source_sha256"], "Runtime audit hash drift")
    require(builder.sha(final) == receipt["common_audit"]["final_source_sha256"], "Final audit hash drift")
    metadata_common, summaries = None, {}
    for arm in ARMS:
        saved = receipt["arms"][arm]
        candidate_path = BATCH / arm / "candidate.ipynb"
        require(sha(candidate_path) == saved["candidate_sha256"], arm + " candidate hash drift")
        notebook = load(candidate_path)
        require(len(notebook["cells"]) == 13, arm + " cell count differs")
        injection = builder.injection(arm, builder.sha(expanded), patch_text, runtime)
        for index in range(12):
            code = text_source(notebook["cells"][index])
            require(notebook["cells"][index]["cell_type"] == "code", "Cell type changed")
            if index == 4:
                require(code.count(injection) == 1, arm + " common injection mismatch")
                code = code.replace(injection, "", 1)
            require(code == text_source(public["cells"][index]), f"{arm} original cell {index} changed")
            compile(text_source(notebook["cells"][index]), f"{arm}_cell_{index}", "exec")
        require(text_source(notebook["cells"][12]) == final, arm + " common final hook differs")
        algorithm, algorithm_receipt = patch_expanded_predictor(expanded, arm, audit=False)
        _, audit_receipt = patch_expanded_predictor(expanded, arm, audit=True)
        require(algorithm_receipt == saved["algorithm_changes"], arm + " algorithm receipt differs")
        require(audit_receipt == saved["audited_expansion"], arm + " audit receipt differs")
        require(len(algorithm_receipt["replacements"]) == {"B0": 0, "C1": 5, "C2": 10}[arm], "Algorithm whitelist size differs")
        if arm == "B0":
            require(algorithm == expanded, "B0 algorithm is not the complete original")
        tree = ast.parse(algorithm)
        for model in ("model", "secondary_model"):
            count = sum(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and isinstance(node.func.value, ast.Name) and node.func.value.id == model
                        and node.func.attr == "encode" for node in ast.walk(tree))
            require(count == 5, f"{arm} extra/missing encoder call sites")
        meta = load(BATCH / arm / "kernel-metadata.json")
        require(meta["is_private"] is True and meta["enable_gpu"] is True
                and meta["enable_internet"] is False and meta["enable_tpu"] is False,
                arm + " execution metadata drift")
        require(meta["competition_sources"] == ["biohub-cell-tracking-during-development"]
                and not meta["kernel_sources"] and not meta["model_sources"], "Unexpected input source")
        require(len(meta["dataset_sources"]) == 3 and all(re.search(r"/\d+$", item) for item in meta["dataset_sources"]),
                "Three Dataset versions must be fixed")
        common = {key: value for key, value in meta.items() if key not in {"id", "title"}}
        if metadata_common is None:
            metadata_common = common
        require(common == metadata_common, "B0/C1/C2 input or compute metadata differ")
        summaries[arm] = {"candidate_sha256": sha(candidate_path), "ref": meta["id"],
                          "algorithm_sha256": algorithm_receipt["algorithm_sha256"]}
    return {"public_sha256": PUBLIC_SHA, "original_twelve_cells_restored": True, "arms": summaries}


def frozen_manifest():
    require(sha(BATCH / "manifest.json") == FROZEN_MANIFEST_SHA, "Manifest differs from the independently recorded activation hash")
    manifest = load(BATCH / "manifest.json")
    require(manifest["frozen"] is True, "Manifest is not frozen")
    timestamp(manifest["frozen_at_utc"])
    require(manifest["task_sha256"] == sha(TASK), "Task text differs from frozen hash")
    for key, maximum in LIMITS.items():
        require(manifest["budget_limits"][key] == maximum, "Budget ceiling differs: " + key)
    require(set(manifest["arms"]) == set(ARMS), "Frozen object set differs")
    require(bool(manifest["frozen_files"]), "No frozen files")
    for relative, expected in manifest["frozen_files"].items():
        require(sha(ROOT / relative) == expected, "Frozen file drift: " + relative)
    for arm in ARMS:
        meta = load(BATCH / arm / "kernel-metadata.json")
        record = manifest["arms"][arm]
        require(record["source_sha256"] == sha(BATCH / arm / "candidate.ipynb"), arm + " frozen candidate drift")
        require(record["metadata_sha256"] == sha(BATCH / arm / "kernel-metadata.json"), arm + " frozen input drift")
        require(record["ref"] == meta["id"], arm + " frozen ref differs")
    return {"manifest_sha256": sha(BATCH / "manifest.json"), "frozen_at_utc": manifest["frozen_at_utc"],
            "frozen_files_checked": len(manifest["frozen_files"])}


def tests_and_hashes():
    result = load(BATCH / "test_results.json")
    require(result["status"] == "PASS", "Synthetic tests did not pass")
    require(result["test_script_sha256"] == sha(BATCH / "tests/test_tta_transforms.py"), "Test script hash differs")
    for relative, expected in result["source_file_sha256"].items():
        require(sha(ROOT / relative) == expected, "Tested source drift: " + relative)
    checks = result["checks"]
    for key in ("dynamic_expansion", "actual_transform_expressions", "actual_encode_and_association_blocks", "identical_common_runtime_hooks"):
        require(checks[key]["status"] == "PASS", "Required executed test missing/failing: " + key)
    cases = checks["actual_transform_expressions"]["cases"]
    required_shapes = {(3, 5), (5, 5), (2, 3, 4, 5, 7)}
    for arm in ARMS:
        for role in ("primary", "secondary"):
            rows = [row for row in cases if row["arm"] == arm and row["role"] == role]
            require(required_shapes <= {tuple(row["shape"]) for row in rows}, "Missing actual-transform shape case")
            require(all(row["passes"] == 8 and row["unique"] == (8 if arm == "C1" else 7)
                        and row["all_inverse_exact"] and row["leading_axes_preserved"] for row in rows), "Transform/inverse test failed")
        hook = checks["identical_common_runtime_hooks"]["arms"][arm]
        require(hook["prediction_tensors_equal_unaudited"] and hook["rng_state_unchanged"]
                and hook["retained_baseline_features_released"], "Audit no-side-effect test failed")
    actual = checks["actual_encode_and_association_blocks"]
    require(all(actual[key] for key in ("C2_primary_features_equal_B0", "C2_detection_logits_equal_B0", "C2_average_exact", "C2_uniform_secondary_zero_delta_allowed")),
            "C2 reuse/no-pollution/zero-delta checks failed")
    for arm in ARMS:
        observed = actual["arms"][arm]
        require(observed["primary_encode_calls"] == observed["secondary_encode_calls"] == 8,
                "Executed encoding count drift")
        require(observed["raw_feature_and_logits_unmutated"] and observed["actual_coordinate_indexing_consumed"], "Actual feature consumption failed")
    final = load(BATCH / "final_audit_self_test.json")
    require(final["source_sha256"] == sha(BATCH / "final_audit.py") and final["status"] == "PASS", "Final audit self-test source mismatch/failure")
    require(len(final["cases"]) >= 16 and all(row["status"] == "PASS" for row in final["cases"]), "Final schema positive/negative tests missing")
    require(final["postprocess_configuration_test"]["status"] == "PASS"
            and final["whole_hook_synthetic_integration"]["status"] == "PASS", "Final PP/full hook test missing")
    return {"test_results_sha256": sha(BATCH / "test_results.json"), "transform_cases": len(cases),
            "final_csv_cases": len(final["cases"]), "gpu_scope": "NOT_PROVEN_BY_LOCAL_TESTS"}


def budget():
    ledger, manifest = load(BATCH / "write_ledger.json"), load(BATCH / "manifest.json")
    operations = ledger["operations"]
    require(all(item["action"] in {"SaveKernel", "CreateCodeSubmission"} for item in operations), "Unauthorized operation in ledger")
    require(all(item["arm"] in ARMS and item.get("status") for item in operations), "Unknown arm or missing write status")
    for item in operations:
        require(timestamp(item["at_utc"]) >= timestamp(manifest["frozen_at_utc"]), "Write predates manifest freeze")
        require(item["manifest_sha256"] == FROZEN_MANIFEST_SHA, "Write used a different frozen manifest")
    saves = [item for item in operations if item["action"] == "SaveKernel"]
    subs = [item for item in operations if item["action"] == "CreateCodeSubmission"]
    require(ledger["save_requests"] == len(saves) <= 4, "Save request budget/count mismatch")
    require(ledger["submission_requests"] == len(subs) <= 3, "Submission request budget/count mismatch")
    require(0 <= ledger["repair_requests"] <= 1, "Shared repair budget exceeded")
    require(len(saves) <= 3 + ledger["repair_requests"], "Fourth save lacks shared repair accounting")
    require(max(Counter(item["arm"] for item in subs).values(), default=0) <= 1, "An object has multiple formal requests")
    require(max(Counter(item["arm"] for item in saves).values(), default=0) <= 2, "Object saved more than initial plus shared repair")
    for item in subs:
        preflight = item.get("preflight", {})
        remaining = item.get("quota_remaining_before", preflight.get("submission_remaining", 0))
        require(remaining >= 1, "Formal request lacks verified positive live remaining quota")
        require(preflight.get("status") == "PASS" and preflight.get("principal") == "sailorren", "Formal request lacks authorized-account preflight")
        require(timestamp(preflight["observed_at_utc"]) <= timestamp(item["at_utc"]), "Preflight does not precede formal write")
    for key in ("training_requests", "dataset_requests", "model_requests", "final_selection_changes"):
        if key in ledger:
            require(ledger[key] == 0, "Forbidden write counter: " + key)
    return {"save_requests": len(saves), "submission_requests": len(subs), "repair_requests": ledger["repair_requests"],
            "object_refs": {arm: manifest["arms"][arm]["ref"] for arm in ARMS}}


def ordinary_arm(arm, record):
    ordinary = record["ordinary"]
    require(ordinary["status"] == "COMPLETE" and ordinary["verified"] is True, arm + " ordinary not COMPLETE/verified")
    require(record["remote_binding"]["verified"] is True, arm + " source/version not remotely bound")
    require(isinstance(record["version"], int) and record["version"] >= 1
            and isinstance(record["script_version_id"], int) and record["script_version_id"] > 0, arm + " exact Version/SV missing")
    final = artifact(ordinary["final_audit"], arm)
    require(final["status"] == "FINAL_OUTPUT_AUDIT_PASS", arm + " final output audit failed")
    submission = final["submission"]
    require(submission["status"] == "PASS" and submission["stage"] == "after_original_selection_and_final_rewrite", "Wrong output stage")
    require(submission["rows"] == submission["nodes"] + submission["edges"] > 0, "Final rows/counts inconsistent")
    require(submission["expected_test_datasets"] == submission["actual_datasets"] and not submission["unexpected_train_output"], "Final coverage differs")
    require(re.fullmatch(r"[0-9a-f]{64}", submission["sha256"]) is not None, "Final CSV hash missing")
    require(final["assets"]["checkpoint_actual_sha256_after_run"] == WEIGHTS, "Consumed weight hashes differ")
    require(final["assets"]["support_python_before_patch_manifest_sha256"] == "978b626d1fd1e7397435a437dfe68691defe1572fc3c20e61012d7c9b52ed029", "Original support code guard differs")
    support = final["assets"]["support_python_after_patch_sha256"]
    build = load(BATCH / "build_receipt.json")
    require(support["scripts/predict_unet_transformer.py"] == build["arms"][arm]["audited_expansion"]["expanded_sha256"]
            and support["scripts/public946_runtime.py"] == sha(BATCH / "runtime_audit.py"), "Actually executed support patch/runtime source differs")
    actual_config = final["runtime"]["inference_configuration"]
    require(actual_config == {"DET_THRESHOLD": 0.965, "UNET_BATCH_SIZE": 4, "USE_ILP": True,
                              "ILP_EDGE_WEIGHT": -1.0, "ILP_APPEARANCE_WEIGHT": 0.0,
                              "ILP_DISAPPEARANCE_WEIGHT": 2.0, "ILP_DIVISION_WEIGHT": 1.2, "SLICE": ""},
            "Actually executed common inference configuration differs")
    pp = final["postprocess"]
    require(record["actual_postprocess"] == pp, arm + " result PP differs from final audit")
    require(pp["effective_final_configuration"] == {**pp["base_configuration"], **pp["typed_overrides_actually_applied"]}, "Selected PP not reconstructed from base and actual override")
    for key, value in {"GAP_CLOSE_UM": 5.0, "MOTION_RELINK_TIGHT_UM": 6.0,
                       "DEEPCENTER_SAFE_DIV_THRESHOLD": 0.25, "SAFE_DIV_MAX_UM": 9.0,
                       "SAFE_DIV_SISTER_MAX_UM": 14.0}.items():
        require(pp["base_configuration"][key] == value, "Original base PP changed: " + key)
    records = []
    require(ordinary["runtime_files"], arm + " actual runtime logs missing")
    for value in ordinary["runtime_files"]:
        if str(value["path"]).endswith(".jsonl"):
            records.extend(artifact(value, arm, json_lines=True))
        else:
            summary = artifact(value, arm)
            require(summary["status"] == "ACTUAL_GPU_SMOKE_PASS" and summary["all_windows_cuda"] is True,
                    "Runtime summary lacks actual CUDA smoke")
            raw_records = []
            for raw in summary["raw_files"]:
                rows = artifact(raw, arm, json_lines=True)
                require(len(rows) == raw["records"], "Raw runtime file record count mismatch")
                raw_records.extend(rows)
            require(len(raw_records) == summary["windows"], "Runtime summary window count differs")
            require(sorted({row["dataset"] for row in raw_records}) == summary["datasets"], "Runtime summary dataset count differs")
            require([row for row in raw_records if row.get("association")] == summary["association_samples"],
                    "Runtime detailed samples differ from hash-bound raw receipts")
            require(all(row["encode_calls"] == summary["all_windows_encode_calls"]
                        and row["config"] == summary["all_windows_config"]
                        and str(row["input"]["device"]).startswith("cuda") for row in raw_records),
                    "Runtime aggregation differs from actual records")
            records.extend(raw_records)
    production = [item for item in records if item.get("event") == "actual_predictor_window"
                  and Path(item["input_parent"]).name == "test"]
    require(set(item["dataset"] for item in production) == set(submission["expected_test_datasets"]), "GPU runtime does not cover enumerated test")
    keys = [(item["dataset"], item["window_index"]) for item in production]
    require(len(keys) == len(set(keys)), "Duplicate runtime production windows")
    associations = []
    for item in production:
        require(item["arm"] == arm and item["encode_calls"] == {"primary": 8, "secondary": 8}, "Wrong runtime arm or extra encoding")
        require(item["config"] == {"secondary_link_mode": "low_margin_consensus", "secondary_edge_weight": 0.15, "secondary_detection_weight": 0.8}, "Runtime association weights drift")
        require(str(item["input"]["device"]).startswith("cuda"), "CPU fixture cannot prove GPU smoke")
        if item.get("consumed_features"):
            for role in ("primary", "secondary"):
                feature = item["consumed_features"][role]
                require(feature["all_finite"] is True and feature["original_encoded_feature_sample_unchanged"] is True, "Invalid or polluted runtime feature")
        if item.get("association"):
            assoc = item["association"]
            require(assoc["actual_secondary_feature_consumed"] is True and assoc["diagnostic_encoder_calls"] == 0
                    and assoc["diagnostic_edge_head_calls"] == 1 and assoc["diagnostic_probabilities_used_in_production"] is False,
                    "Runtime association path/diagnostic scope failed")
            require(assoc["actual_secondary_logits"]["all_finite"] is True, "Nonfinite actual association logits")
            associations.append(item["dataset"])
    require(associations, arm + " no actual nonempty GPU association example observed")
    require(max(Counter(associations).values()) <= 1, "Excess diagnostic edge-head calls per video")
    for dataset, graph in submission["topology"].items():
        runtime_frames = {int(frame) for item in production if item["dataset"] == dataset for frame in item["frames"]}
        require({int(row[0]) for row in graph["frame_counts"]} <= runtime_frames, "Final node frame lacks production runtime coverage")
    return {"final_sha256": submission["sha256"], "rows": submission["rows"], "selected_pp": pp["selected_label"],
            "runtime_production_windows": len(production), "association_examples": len(associations)}


def formal_arm(arm, record, ledger):
    frozen = load(BATCH / "manifest.json")["arms"][arm]
    require(record["ref"] == frozen["ref"] and record["source_sha256"] == frozen["source_sha256"], "Formal object/source differs from frozen candidate")
    submission = record["submission"]
    require(isinstance(submission["id"], int) and submission["id"] > 0, arm + " formal submission ID missing")
    require(submission["status"] == "COMPLETE", arm + " formal terminal score pending/failed: " + str(submission["status"]))
    require(submission["public_score"] is not None, arm + " formal Public Score missing")
    score = Decimal(str(submission["public_score"]))
    require(score.is_finite(), "Nonfinite formal score")
    require(not submission.get("error_description"), "Formal submission carries an error")
    timestamp(submission["observed_at_utc"])
    require(submission.get("observed_at_shanghai") and submission.get("read_location"), "Formal score lacks read time/location")
    operations = [item for item in ledger["operations"] if item["action"] == "CreateCodeSubmission" and item["arm"] == arm]
    require(len(operations) == 1, "Formal identity lacks its unique request ledger entry")
    operation = operations[0]
    require(operation["ref"] == record["ref"] and operation["version"] == record["version"]
            and operation["script_version_id"] == record["script_version_id"]
            and operation["source_sha256"] == record["source_sha256"], "Formal request is bound to a different source/version")
    require(operation["description"] == submission["description"], "Formal platform description differs from exact request")
    response_id = operation.get("response", {}).get("id")
    require(response_id == submission["id"] or (response_id is None and submission.get("read_only_reconciled") is True),
            "Formal ID differs from response or lacks explicit read-only reconciliation")
    require(operation["submitted_source_sha256"] in submission["description"], "Formal description lacks transmitted source hash")
    binding = record["remote_binding"]
    require(binding["ref"] == record["ref"] and binding["version"] == record["version"]
            and binding["script_version_id"] == record["script_version_id"]
            and binding["local_source_sha256"] == record["source_sha256"]
            and binding["source_cell_hashes"] == record["cell_source_sha256"], "Remote executable/source identity differs")
    require(bool(binding["checks"]) and all(binding["checks"].values()), "Remote source/input/version has unmet checks")
    return {"id": submission["id"], "version": record["version"], "script_version_id": record["script_version_id"],
            "ref": record["ref"], "public_score": str(submission["public_score"])}


def comparisons():
    results = load(BATCH / "results.json")
    require(set(results["arms"]) == set(ARMS), "Result table omits a planned object")
    def score(item):
        return Decimal(str(item["public_score"])) if item["status"] == "COMPLETE" and item["public_score"] is not None else None
    b0 = score(results["arms"]["B0"]["submission"])
    start, current = score(results["own_best_at_start"]), score(results["current_own_best"])
    require(start is not None and current is not None and current >= start, "Current/starting own formal reference invalid")
    for arm, item in results["arms"].items():
        value = score(item["submission"])
        for field, reference in (("delta_vs_B0", b0), ("delta_vs_own_best_at_start", start),
                                 ("delta_vs_current_own_best", current), ("delta_vs_public_0946", Decimal("0.946"))):
            observed = item.get(field)
            if value is None or reference is None:
                require(observed is None, arm + " claims score difference without formal score")
            else:
                require(observed is not None and Decimal(str(observed)) == value - reference, arm + " incorrect/missing delta: " + field)
    return {"own_best_at_start": str(start), "current_own_best": str(current),
            "B0_actual": None if b0 is None else str(b0), "public_reference": "0.946"}


def delivery(remote_receipt=None):
    value = load(Path(remote_receipt)) if remote_receipt else load(BATCH / "results.json")["git_delivery"]
    if "path" in value:
        value = artifact(value)
    commit = value["commit"]
    require(re.fullmatch(r"[0-9a-f]{40}", commit) is not None, "Fixed Git commit missing")
    require(value["remote_head"] == commit, "Authoritative remote HEAD differs")
    require(value["git_status_porcelain"] == "", "Observed worktree is not clean")
    timestamp(value["observed_at_utc"])
    files = value["files"]
    require(bool(files), "No fixed-commit remote file readback")
    observed_paths = set()
    for item in files:
        require(item["local_sha256"] == item["remote_sha256"] == sha(ROOT / item["path"]), "Remote byte/hash mismatch: " + item["path"])
        observed_paths.add(item["path"])
    relative = BATCH.relative_to(ROOT).as_posix()
    required = {TASK.relative_to(ROOT).as_posix(), "reports/20260908_PUBLIC946_TTA_OPTIMIZATION_RESULT.md"}
    required |= {f"{relative}/{name}" for name in ("manifest.json", "results.json", "write_ledger.json", "test_results.json", "verify.py")}
    required |= {f"{relative}/{arm}/{name}" for arm in ARMS for name in ("candidate.ipynb", "kernel-metadata.json")}
    require(required <= observed_paths, "Key delivery files lack remote readback: " + str(sorted(required - observed_paths)))
    return {"commit": commit, "remote_files": len(files), "remote_head_equal": True, "observed_clean": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--local", action="store_true")
    mode.add_argument("--final", action="store_true")
    parser.add_argument("--remote-receipt")
    args = parser.parse_args()
    checks = []
    def check(name, fn, scope="experiment"):
        try:
            detail = fn()
            checks.append({"check": name, "scope": scope, "status": "PASS", "evidence": detail})
        except Exception as error:
            checks.append({"check": name, "scope": scope, "status": "FAIL", "error": f"{type(error).__name__}: {error}"})
    check("source_parent_and_code_differences", source_and_build)
    check("frozen_manifest_and_assets", frozen_manifest)
    check("executed_synthetic_tests", tests_and_hashes)
    check("authorization_write_budget", budget)
    if args.final:
        try:
            results, ledger = load(BATCH / "results.json"), load(BATCH / "write_ledger.json")
        except Exception:
            results, ledger = {"arms": {}}, {}
        for arm in ARMS:
            check(arm + "_final_output_and_gpu_smoke", lambda arm=arm: ordinary_arm(arm, results["arms"][arm]))
            check(arm + "_formal_terminal_score", lambda arm=arm: formal_arm(arm, results["arms"][arm], ledger))
        check("score_comparison_and_boundaries", comparisons)
        check("github_authoritative_remote_delivery", lambda: delivery(args.remote_receipt), "delivery")
    experiment_ok = all(item["status"] == "PASS" for item in checks if item["scope"] == "experiment")
    delivery_ok = args.final and all(item["status"] == "PASS" for item in checks if item["scope"] == "delivery")
    complete = experiment_ok and delivery_ok
    state = "LOCAL_VALIDATED_GPU_AND_FORMAL_NOT_IMPLIED" if args.local and experiment_ok else "BLOCKED_EVIDENCE_CHECKS"
    if args.final:
        pending = any(item.get("submission", {}).get("status") in {"RUNNING", "PENDING"} for item in results.get("arms", {}).values())
        state = "COMPLETED_VERIFIED" if complete else "PARTIAL_SCORE_PENDING" if pending else "PARTIAL_OR_BLOCKED"
    output = {"task_id": "PUBLIC946_TTA_20260908", "observed_at_utc": datetime.now(timezone.utc).isoformat(),
              "mode": "final" if args.final else "local", "status": state, "experiment_checks_pass": experiment_ok,
              "delivery_checks_pass": bool(delivery_ok), "checks": checks,
              "limitations": "File receipts and platform observations are verified separately; no fresh Kaggle or network query is issued by this validator."}
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if (experiment_ok if args.local else complete) else 1


if __name__ == "__main__":
    sys.exit(main())
