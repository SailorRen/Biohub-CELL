"""PUBLIC946 最后只读审计；在原版全部选参及重写结束后调用。

Notebook 最后单元嵌入本文件后调用 public946_final_audit(globals())。
只新增小型 JSON 回执，不更改配置、预测、模型、随机状态或 submission。
本文件的 --self-test 使用同一 CSV 校验函数，不加载模型。
"""

import csv as _fa_csv
import hashlib as _fa_hashlib
import importlib.metadata as _fa_metadata
import json as _fa_json
import math as _fa_math
import os as _fa_os
import platform as _fa_platform
from collections import Counter as _fa_Counter
from datetime import datetime as _fa_datetime, timezone as _fa_timezone
from pathlib import Path as _fa_Path


_FA_COLUMNS = ["id", "dataset", "row_type", "node_id", "t", "z", "y", "x", "source_id", "target_id"]
_FA_PP_KEYS = """
OUTPUT_EDGE_MAX_UM OUTPUT_ENFORCE_NEXT_FRAME OUTPUT_SINGLE_PARENT_REPAIR
OUTPUT_SINGLE_CHILD_REPAIR OUTPUT_PRUNE_ISOLATED OUTPUT_MOTION_RELINK
MOTION_RELINK_TIGHT_UM MOTION_RELINK_RELAXED_UM MOTION_RELINK_VELOCITY_WEIGHT
MOTION_RELINK_LEARNED_BONUS MOTION_RELINK_MAX_FRAME_NODES
OUTPUT_DIVISION_GEOMETRY_FILTER DIV_PARENT_MAX_UM DIV_SISTER_MAX_UM
DIV_DROP_TO_SINGLE_IF_BAD OUTPUT_GAP_CLOSE GAP_CLOSE_MAX_GAP GAP_CLOSE_UM
GAP_DENSITY_ADAPTIVE GAP_DENSITY_REFERENCE_UM GAP_DENSITY_GAIN
GAP_DENSITY_MAX_STEP_DELTA_UM GAP_DENSITY_NEIGHBORS GAP_CLOSE_REUSE_EXISTING
GAP_CLOSE_REUSE_UM GAP_CLOSE_MAX_ADDED_FRAC GAP_CLOSE_MAX_ADDED_ABS
GAP_REFINE_SYNTHETIC GAP_REFINE_WIN_Z GAP_REFINE_WIN_YX GAP_REFINE_MAX_SHIFT_UM
OUTPUT_FILTER_SHORT_TRACKS OUTPUT_MIN_TRACK_LEN OUTPUT_KEEP_DIVISION_COMPONENTS
ADAPTIVE_SHORT_TRACK_RESCUE SHORT_TRACK_RESCUE_TRIGGER_REMOVED_FRAC
SHORT_TRACK_RESCUE_MIN_LEN SHORT_TRACK_RESCUE_MIN_MEAN_EDGE_PROB
SHORT_TRACK_RESCUE_MAX_MEAN_EDGE_DIST_UM SHORT_TRACK_RESCUE_MAX_NODES_FRAC
SHORT_TRACK_RESCUE_MAX_NODES_ABS OUTPUT_LINEFIT_SMOOTH OUTPUT_LINEFIT_WEIGHT
OUTPUT_LINEFIT_WINDOW OUTPUT_GAP2_RECOVERY GAP2_MAX_TOTAL_UM GAP2_MAX_STEP_UM
GAP2_MAX_LINKS_FRAC GAP2_MAX_LINKS_ABS GAP2_REQUIRE_CONTEXT GAP2_FRAME_FRAC_CAP
OUTPUT_SAFE_DIVISIONS SAFE_DIV_MAX_UM SAFE_DIV_SISTER_MAX_UM
SAFE_DIV_SISTER_SYMMETRY_TAU SAFE_DIV_EXISTING_CHILD_MAX_UM SAFE_DIV_FRAME_FRAC_CAP
SAFE_DIV_GLOBAL_FRAC_CAP SAFE_DIV_DIVERGE_UM SAFE_DIV_REQUIRE_DIVERGENCE
SAFE_DIV_REQUIRE_MUTUAL_NN USE_DEEPCENTER_VETO REQUIRE_DEEPCENTER_VETO
DEEPCENTER_GAP_VETO DEEPCENTER_SAFE_DIV_VETO DEEPCENTER_GAP_THRESHOLD
DEEPCENTER_EXPECTED_EPOCH DEEPCENTER_GAP_CONFIRM_MIN_SPAN_UM
DEEPCENTER_SAFE_DIV_THRESHOLD DEEPCENTER_SCORE_WIN_Z DEEPCENTER_SCORE_WIN_YX
DEEPCENTER_SCORE_CACHE_MAX_FRAMES VOXEL_SCALE_UM
""".split()
_FA_ENV_KEYS = """
BIOHUB_EDGE_FEATURE_TTA BIOHUB_SECONDARY_EDGE_FEATURE_TTA
BIOHUB_SECONDARY_DETECTION_WEIGHT BIOHUB_SECONDARY_EDGE_WEIGHT
BIOHUB_SECONDARY_LINK_MODE BIOHUB_SECONDARY_MIX_TEMPERATURE
BIOHUB_SECONDARY_LOW_MARGIN_MAX BIOHUB_DUAL_SEED_EDGE_THRESHOLD
BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT BIOHUB_BIDIRECTIONAL_FUSION_MODE
BIOHUB_DUAL_SEED_MIN_CANDIDATE_RETENTION BIOHUB_RETENTION_GUARD
BIOHUB_DET_THRESHOLD BIOHUB_UNET_BATCH_SIZE
BIOHUB_VALIDATOR_ENABLE BIOHUB_VALIDATOR_N_PER_TYPE
PYTHONHASHSEED CUBLAS_WORKSPACE_CONFIG CUDA_VISIBLE_DEVICES
OMP_NUM_THREADS MKL_NUM_THREADS
""".split()
_FA_DEPENDENCIES = """
torch torchvision numpy scipy pandas polars tracksdata zarr pyscipopt geff
geff-spec ilpy blosc2 dask imagecodecs pyarrow rustworkx sqlalchemy donfig numcodecs
""".split()


def _fa_require(condition, message):
    if not condition:
        raise RuntimeError("PUBLIC946_FINAL_AUDIT: " + str(message))


def _fa_sha(path):
    digest = _fa_hashlib.sha256()
    with _fa_Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fa_integer(value, context):
    try:
        parsed = int(value)
    except (ValueError, TypeError):
        raise RuntimeError("PUBLIC946_FINAL_AUDIT: invalid integer " + context) from None
    return parsed


def public946_audit_csv(path, expected_test_stems, train_stems=()):
    """复核原导出器/最后审计约束；不要求图数、行数、连通或全节点非孤立。

    坐标为有限、非负数；节点/时间/引用为整数。父子相邻帧、最大入度 1
    与最大出度 2 直接沿用母版 cells 6/10；不添加分裂几何或距离阈值。
    """
    expected = sorted(str(item) for item in expected_test_stems)
    _fa_require(len(expected) == len(set(expected)), "duplicate test enumeration")
    groups, semantic_seen, row_count = {}, set(), 0
    with _fa_Path(path).open(newline="") as handle:
        reader = _fa_csv.DictReader(handle)
        _fa_require(reader.fieldnames == _FA_COLUMNS, "CSV columns/order differ")
        for row_count, row in enumerate(reader, 1):
            _fa_require(None not in row and all(value is not None for value in row.values()), "malformed CSV row")
            _fa_require(_fa_integer(row["id"], "id") == row_count - 1, "row IDs not contiguous")
            _fa_require(row["row_type"] in {"node", "edge"}, "unexpected row_type")
            semantic = tuple(row[key] for key in _FA_COLUMNS if key != "id")
            _fa_require(semantic not in semantic_seen, "duplicate row excluding row id")
            semantic_seen.add(semantic)
            group = groups.setdefault(row["dataset"], {"nodes": {}, "edges": [], "frame_counts": _fa_Counter()})
            if row["row_type"] == "node":
                node_id = _fa_integer(row["node_id"], "node_id")
                t = _fa_integer(row["t"], "node time")
                _fa_require(t >= 0, "negative node time")
                _fa_require(node_id not in group["nodes"], "duplicate node id within dataset")
                for key in ("z", "y", "x"):
                    try:
                        coordinate = float(row[key])
                    except (ValueError, TypeError):
                        raise RuntimeError("PUBLIC946_FINAL_AUDIT: invalid coordinate") from None
                    _fa_require(_fa_math.isfinite(coordinate) and coordinate >= 0, "nonfinite/negative coordinate")
                group["nodes"][node_id] = t
                group["frame_counts"][t] += 1
            else:
                group["edges"].append((_fa_integer(row["source_id"], "source_id"), _fa_integer(row["target_id"], "target_id")))
    _fa_require(row_count > 0, "empty output")
    _fa_require(sorted(groups) == expected, {"expected_test": expected, "actual": sorted(groups)})
    unexpected_train = sorted(set(groups) & (set(train_stems) - set(expected)))
    _fa_require(not unexpected_train, {"unexpected_train_output": unexpected_train})
    topology = {}
    for dataset, group in sorted(groups.items()):
        nodes, edges = group["nodes"], group["edges"]
        _fa_require(bool(nodes), dataset + ": no nodes")
        _fa_require(len(edges) == len(set(edges)), dataset + ": duplicate edge")
        incoming, outgoing = _fa_Counter(), _fa_Counter()
        for source, target in edges:
            _fa_require(source in nodes and target in nodes, dataset + ": dangling edge")
            _fa_require(nodes[target] == nodes[source] + 1, dataset + ": edge time is not next frame")
            incoming[target] += 1
            outgoing[source] += 1
        max_in, max_out = max(incoming.values(), default=0), max(outgoing.values(), default=0)
        _fa_require(max_in <= 1 and max_out <= 2, dataset + ": invalid lineage degree")
        topology[dataset] = {
            "nodes": len(nodes), "edges": len(edges), "max_indegree": max_in,
            "max_outdegree": max_out, "division_parents": sum(count == 2 for count in outgoing.values()),
            "frame_counts": [[t, count] for t, count in sorted(group["frame_counts"].items())],
        }
    return {
        "status": "PASS", "stage": "after_original_selection_and_final_rewrite",
        "schema": _FA_COLUMNS, "integer_fields": ["id", "node_id", "t", "source_id", "target_id"],
        "coordinate_contract": "finite_nonnegative_numeric_on_node_rows",
        "rows": row_count, "nodes": sum(item["nodes"] for item in topology.values()),
        "edges": sum(item["edges"] for item in topology.values()),
        "sha256": _fa_sha(path), "bytes": _fa_Path(path).stat().st_size,
        "expected_test_datasets": expected, "actual_datasets": sorted(groups),
        "unexpected_train_output": unexpected_train, "topology": topology,
        "checks": ["columns", "integer_ids_and_times", "finite_coordinates", "test_coverage", "no_train_only_output", "no_duplicate_rows_or_nodes_or_edges", "endpoint_references", "next_frame_edges", "max_indegree_1_outdegree_2"],
    }


def public946_postprocess_configuration(namespace):
    base_sweep = dict(namespace["PP_BASE_CONFIG"])
    selected = dict(namespace["selected_config"])
    _fa_require(set(selected) <= set(namespace["PP_SWEEP_KEYS"]), "selected non-sweep key")
    # Exactly mirrors pp_apply's type conversion. pp_restore has already restored globals.
    typed = {key: type(base_sweep[key])(value) for key, value in selected.items()}
    _fa_require(all(namespace[key] == value for key, value in base_sweep.items()), "sweep globals not restored")
    base = {key: namespace[key] for key in _FA_PP_KEYS}
    _fa_require(set(base_sweep) <= set(base), "PP whitelist omits a sweepable key")
    base.update(base_sweep)
    final = {**base, **typed}
    return {
        "selected_label": namespace["selected_label"], "selected_overrides": selected,
        "typed_overrides_actually_applied": typed, "base_configuration": base,
        "effective_final_configuration": final,
        "configured_gap_close_max_gap": final["GAP_CLOSE_MAX_GAP"],
        "clamped_gap_close_max_gap": min(final["GAP_CLOSE_MAX_GAP"], 1),
        "resolution": "PP_BASE_CONFIG plus selected_config converted exactly as pp_apply; globals restored after final write",
    }


def _fa_runtime_environment(namespace):
    dependencies = {}
    for package in _FA_DEPENDENCIES:
        try:
            dependencies[package] = _fa_metadata.version(package)
        except _fa_metadata.PackageNotFoundError:
            dependencies[package] = "UNKNOWN_NOT_INSTALLED_AS_DISTRIBUTION"
    result = {
        "python": _fa_platform.python_version(), "platform": _fa_platform.platform(),
        "dependencies": dependencies,
        "environment_whitelist": {key: _fa_os.environ.get(key) for key in _FA_ENV_KEYS},
        "inference_configuration": {key: namespace[key] for key in (
            "DET_THRESHOLD", "UNET_BATCH_SIZE", "USE_ILP", "ILP_EDGE_WEIGHT",
            "ILP_APPEARANCE_WEIGHT", "ILP_DISAPPEARANCE_WEIGHT", "ILP_DIVISION_WEIGHT", "SLICE")},
        "production_predict_seconds": namespace.get("predict_seconds"),
        "validation_predict_seconds": namespace.get("predict_val_seconds"),
        "worker_precision_and_peak_memory": "See worker runtime smoke; notebook process is not predictor worker",
    }
    torch = namespace.get("_torch", namespace.get("torch"))
    if torch is not None:
        result["notebook_process_torch"] = {
            "scope": "notebook_process_only_not_predictor_workers",
            "version": str(torch.__version__), "cuda_runtime": torch.version.cuda,
            "default_dtype": str(torch.get_default_dtype()), "initial_seed": int(torch.initial_seed()),
            "deterministic_algorithms": bool(torch.are_deterministic_algorithms_enabled()),
            "cudnn_benchmark": bool(torch.backends.cudnn.benchmark),
            "cudnn_deterministic": bool(torch.backends.cudnn.deterministic),
            "matmul_allow_tf32": bool(torch.backends.cuda.matmul.allow_tf32),
            "cudnn_allow_tf32": bool(torch.backends.cudnn.allow_tf32),
            "gpus": [{"index": idx, "name": torch.cuda.get_device_name(idx),
                      "total_memory_bytes": int(torch.cuda.get_device_properties(idx).total_memory),
                      "notebook_process_peak_allocated_bytes": int(torch.cuda.max_memory_allocated(idx)),
                      "notebook_process_peak_reserved_bytes": int(torch.cuda.max_memory_reserved(idx))}
                     for idx in range(torch.cuda.device_count())],
        }
    return result


def public946_final_audit(namespace):
    working = _fa_Path(namespace["WORKING_DIR"])
    expected = sorted(path.name[:-5] for path in _fa_Path(namespace["TEST_DIR"]).iterdir() if path.name.endswith(".zarr"))
    _fa_require(expected == sorted(namespace["test_stems"]), "current test list differs from prediction enumeration")
    train_dir = _fa_Path(namespace["TRAIN_DIR"])
    train_stems = sorted(path.name[:-5] for path in train_dir.iterdir() if path.name.endswith(".zarr")) if train_dir.exists() else []
    _fa_require(namespace["CSV_COLUMNS"] == _FA_COLUMNS, "source CSV schema differs")
    submission = public946_audit_csv(namespace["SUBMISSION_PATH"], expected, train_stems)
    pp = public946_postprocess_configuration(namespace)
    selected_path = _fa_Path(namespace["PP_SELECTED_PATH"])
    selected_receipt = _fa_json.loads(selected_path.read_text())
    _fa_require(selected_receipt["selected"] == pp["selected_label"] and selected_receipt["overrides"] == pp["selected_overrides"], "selected PP receipt differs")
    with _fa_Path(namespace["RUN_STATS_PATH"]).open(newline="") as handle:
        stats = list(_fa_csv.DictReader(handle))
    _fa_require(sorted(row["dataset"] for row in stats) == expected, "final run_stats datasets differ")
    for row in stats:
        graph = submission["topology"][row["dataset"]]
        _fa_require(int(row["nodes"]) == graph["nodes"] and int(row["edges"]) == graph["edges"], "final stats counts differ")
        _fa_require(row["experiment_tag"] == str(namespace["EXPERIMENT_TAG"]) + ":" + pp["selected_label"], "stats tag is not selected PP output")
    integrity_path = _fa_Path(namespace["_runtime_integrity_receipt_path"])
    integrity = _fa_json.loads(integrity_path.read_text())
    _fa_require(integrity == namespace["_runtime_integrity_receipt"], "runtime integrity receipt differs from original in-memory guard")
    actual_checkpoints = {key: _fa_sha(path) for key, path in integrity["materialized_paths"].items()}
    _fa_require(actual_checkpoints == integrity["checkpoint_sha256"], "actual checkpoints changed after original guard")
    repo = _fa_Path(namespace["REPO_DIR"])
    patched_support = {path.relative_to(repo).as_posix(): _fa_sha(path) for path in sorted(repo.rglob("*.py"))}
    base_guard_path = working / "dual_seed_frame_retention_guard_report.json"
    base_guard = _fa_json.loads(base_guard_path.read_text())
    result = {
        "task": "PUBLIC946_TTA_20260908", "status": "FINAL_OUTPUT_AUDIT_PASS",
        "observed_at_utc": _fa_datetime.now(_fa_timezone.utc).isoformat(),
        "submission": submission, "postprocess": pp,
        "pre_selection_output": {"receipt": base_guard_path.name, "receipt_sha256": _fa_sha(base_guard_path),
                                 "submission": base_guard["submission"], "configuration_fields_are_historical_not_authoritative": True},
        "assets": {"original_guard_receipt_sha256": _fa_sha(integrity_path),
                   "checkpoint_actual_sha256_after_run": actual_checkpoints,
                   "support_python_before_patch_sha256": integrity["support_repo_python_sha256"],
                   "support_python_before_patch_manifest_sha256": integrity["support_repo_python_manifest_sha256"],
                   "support_python_after_patch_sha256": patched_support,
                   "guard_ground_truth_scope": "original pre-patch integrity stage only; later original train GT validator and selection do run"},
        "small_receipts": {path.name: {"sha256": _fa_sha(path), "bytes": path.stat().st_size}
                           for path in [selected_path, _fa_Path(namespace["RUN_STATS_PATH"]), integrity_path, base_guard_path]},
        "runtime": _fa_runtime_environment(namespace),
        "formal_hidden_run_output": "UNKNOWN_UNLESS_THIS_RECEIPT_IS_RETRIEVED_FROM_THE_BOUND_FORMAL_RUN",
        "formal_score": "NOT_OBSERVED_BY_NOTEBOOK_AUDIT",
    }
    target = working / "public946_final_audit.json"
    target.write_text(_fa_json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
    print("PUBLIC946_FINAL_AUDIT_PASS", _fa_json.dumps({"receipt": target.name, "sha256": submission["sha256"], "rows": submission["rows"], "selected": pp["selected_label"]}, sort_keys=True))
    return result


def public946_final_audit_self_test():
    """真实执行 CSV 审计的正反例；所有合成文件只存在临时目录。"""
    import copy
    import tempfile
    valid = [
        [0, "test_a", "node", 10, 0, 1, 2, 3, -1, -1],
        [1, "test_a", "node", 11, 1, 1, 2, 4, -1, -1],
        [2, "test_a", "node", 12, 1, 2, 2, 4, -1, -1],
        [3, "test_a", "edge", -1, -1, -1, -1, -1, 10, 11],
        [4, "test_a", "edge", -1, -1, -1, -1, -1, 10, 12],
        [5, "test_b", "node", 10, 7, 0.5, 0, 0, -1, -1],
    ]
    cases = []
    def check(label, rows, should_pass, columns=None, expected=None):
        with tempfile.TemporaryDirectory(prefix="public946_audit_") as temp:
            path = _fa_Path(temp) / "synthetic.csv"
            with path.open("w", newline="") as handle:
                writer = _fa_csv.writer(handle)
                writer.writerow(columns or _FA_COLUMNS)
                writer.writerows(rows)
            try:
                result = public946_audit_csv(path, expected or ["test_a", "test_b"], ["train_only"])
                passed, reason = True, None
            except RuntimeError as error:
                passed, reason = False, str(error)
            _fa_require(passed == should_pass, {"test": label, "actual_pass": passed, "expected_pass": should_pass})
            cases.append({"case": label, "expected_accept": should_pass, "actual_accept": passed, "status": "PASS", "rejection": reason})
    check("division_plus_isolated_node_and_reused_id_across_datasets", valid, True)
    for label, idx, column, value in [
        ("nonfinite_coordinate", 0, 5, "nan"), ("negative_coordinate", 0, 6, -1),
        ("fractional_time", 0, 4, "0.5"), ("duplicate_node_id", 1, 3, 10),
        ("dangling_endpoint", 3, 9, 999), ("backward_edge", 3, 8, 11),
        ("nonconsecutive_time", 1, 4, 2), ("invalid_row_type", 0, 2, "other"),
        ("noncontiguous_row_id", 0, 0, 99), ("train_only_output", 5, 1, "train_only"),
    ]:
        rows = copy.deepcopy(valid)
        rows[idx][column] = value
        check(label, rows, False)
    rows = copy.deepcopy(valid)
    rows.append([len(rows), *rows[3][1:]])
    check("duplicate_semantic_edge_row", rows, False)
    rows = copy.deepcopy(valid)
    rows.extend([[6, "test_a", "node", 13, 0, 1, 3, 3, -1, -1], [7, "test_a", "edge", -1, -1, -1, -1, -1, 13, 11]])
    check("multi_parent", rows, False)
    rows = copy.deepcopy(valid)
    rows.extend([[6, "test_a", "node", 13, 1, 1, 3, 3, -1, -1], [7, "test_a", "edge", -1, -1, -1, -1, -1, 10, 13]])
    check("outdegree_three", rows, False)
    check("schema_order", valid, False, columns=["dataset", "id", *_FA_COLUMNS[2:]])
    check("missing_test_dataset", valid, False, expected=["test_a", "test_b", "test_c"])
    # pp_restore has restored 6.0 even though the final output used 5.5.
    namespace = {key: 1.0 for key in _FA_PP_KEYS}
    namespace.update(MOTION_RELINK_TIGHT_UM=6.0, GAP_CLOSE_MAX_GAP=2)
    namespace.update(
        PP_BASE_CONFIG={"MOTION_RELINK_TIGHT_UM": 6.0},
        PP_SWEEP_KEYS=["MOTION_RELINK_TIGHT_UM"],
        selected_config={"MOTION_RELINK_TIGHT_UM": "5.5"}, selected_label="synthetic_selected",
    )
    resolved = public946_postprocess_configuration(namespace)
    _fa_require(resolved["effective_final_configuration"]["MOTION_RELINK_TIGHT_UM"] == 5.5, "selected config resolution test")
    _fa_require(resolved["base_configuration"]["MOTION_RELINK_TIGHT_UM"] == 6.0, "base config resolution test")
    _fa_require(namespace["MOTION_RELINK_TIGHT_UM"] == 6.0, "audit altered globals")
    _fa_require(resolved["configured_gap_close_max_gap"] == 2 and resolved["clamped_gap_close_max_gap"] == 1, "original clamp test")
    return {
        "status": "PASS", "scope": "actual shared CSV/config validators; no models or platform calls", "cases": cases,
        "postprocess_configuration_test": {"status": "PASS", "base_global_unchanged": 6.0, "selected_final_typed_value": 5.5, "configured_gap": 2, "original_clamp": 1},
    }


if __name__ == "__main__" and "--self-test" in __import__("sys").argv:
    print(_fa_json.dumps(public946_final_audit_self_test(), indent=2, sort_keys=True))
