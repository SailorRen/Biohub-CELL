#!/usr/bin/env python3
"""Execute the actual expanded predictor's TTA and association code on CPU.

Run from the repository root. On the present macOS conda environment use:
DYLD_LIBRARY_PATH=/opt/anaconda3/envs/ml/lib python3 experiments/PUBLIC946_TTA_20260908/tests/test_tta_transforms.py

Transform/inverse expressions and executable blocks are extracted from the
candidate implementation, not reimplemented here. UNet weights and the edge
transformer are small deterministic doubles; encode, indexing and predict_edges
are the real support-code methods. This is not a pretrained GPU or score test.
"""
from __future__ import annotations

import ast
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import sys
import textwrap
import time
import tempfile
import traceback
from types import SimpleNamespace
from datetime import datetime, timezone

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[3]
BATCH = ROOT / "experiments/PUBLIC946_TTA_20260908"
SUPPORT = ROOT / "downloads/PUBLIC946_TTA_20260908/support_v10/repo"
sys.path.insert(0, str(BATCH))


def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def compile_expr(node):
    return compile(ast.fix_missing_locations(ast.Expression(copy.deepcopy(node))), "actual_candidate_expression", "eval")


def encoding_block(source):
    marker = "        from public946_runtime import (" if "        from public946_runtime import (" in source else "        unet_out, det_logits = model.encode(imgs)"
    start = source.index(marker)
    end = source.index("        del imgs\n", start)
    return textwrap.dedent(source[start:end])


def association_block(source):
    start = source.index("            unet_feat_src = model._index_features(")
    end = source.index("            raw = edge_logits_pair[0]", start)
    end += len("            raw = edge_logits_pair[0]")
    return textwrap.dedent(source[start:end])


class ProbeSubstitution(ast.NodeTransformer):
    """Project one real aggregation expression onto one tensor operand."""
    def __init__(self, name):
        self.name = name

    def visit_Subscript(self, node):
        if isinstance(node.value, ast.Name) and node.value.id == self.name:
            return ast.Name(id="probe", ctx=ast.Load())
        return self.generic_visit(node)

    def visit_Name(self, node):
        if node.id == self.name:
            return ast.Name(id="probe", ctx=ast.Load())
        return node


def is_spatial_call(node):
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in {"flip", "transpose", "rot90"}


def inverse_for(tree, name):
    candidates = []
    for node in ast.walk(tree):
        if is_spatial_call(node) and any(isinstance(n, ast.Name) and n.id == name for n in ast.walk(node)):
            candidates.append(node)
    assert candidates, f"No actual inverse expression for {name}"
    node = max(candidates, key=lambda n: len(list(ast.walk(n))))
    return ProbeSubstitution(name).visit(copy.deepcopy(node))


def actual_views(block, role):
    """Unroll only literal augmentation loops; use actual input and inverse AST."""
    tree = ast.parse(block)
    assignments = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            assignments[node.targets[0].id] = node.value
    result = []
    model_name = "model" if role == "primary" else "secondary_model"

    def visit(nodes, loop_values):
        for node in nodes:
            if isinstance(node, ast.For):
                if isinstance(node.target, ast.Name) and node.target.id in {"dims", "_k"}:
                    for value in ast.literal_eval(node.iter):
                        visit(node.body, {**loop_values, node.target.id: value})
                else:
                    visit(node.body, loop_values)
            elif isinstance(node, ast.If):
                visit(node.body, loop_values)
                visit(node.orelse, loop_values)
            elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                fn = node.value.func
                if not (isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name) and fn.value.id == model_name and fn.attr == "encode"):
                    continue
                input_name = node.value.args[0].id
                feature_name, detection_name = [n.id for n in node.targets[0].elts]
                identity = input_name == "imgs"
                transform = ast.Name(id="imgs", ctx=ast.Load()) if identity else assignments[input_name]
                inverse = ast.Name(id="probe", ctx=ast.Load()) if identity else inverse_for(tree, detection_name)
                feature_inverse = None
                if identity:
                    feature_inverse = inverse
                elif feature_name != "_":
                    feature_inverse = inverse_for(tree, feature_name)
                result.append({"input": input_name, "feature": feature_name, "detection": detection_name,
                               "loops": loop_values.copy(), "transform_ast": transform,
                               "inverse_ast": inverse, "feature_inverse_ast": feature_inverse})
    visit(tree.body, {})
    assert len(result) == 8, (role, len(result))
    return result


def apply_view(view, tensor, inverse=False, feature=False):
    key = "feature_inverse_ast" if feature else "inverse_ast"
    expr = view[key] if inverse else view["transform_ast"]
    assert expr is not None
    return eval(compile_expr(expr), {"torch": torch, "imgs": tensor, "probe": tensor, **view["loops"]})


def transformation_checks(sources):
    rows = []
    layouts = [(3, 5), (5, 5), (2, 3, 4, 5, 7), (2, 3, 2, 4, 3, 5), (2, 3, 2, 4, 7, 11)]
    for arm, source in sources.items():
        block = encoding_block(source)
        for role in ("primary", "secondary"):
            views = actual_views(block, role)
            for shape in layouts:
                x = torch.arange(np.prod(shape), dtype=torch.int64).reshape(shape)
                transformed = []
                for view in views:
                    augmented = apply_view(view, x)
                    restored = apply_view(view, augmented, inverse=True)
                    assert torch.equal(restored, x), (arm, role, shape, view["input"])
                    assert augmented.shape[:-2] == x.shape[:-2]
                    # Every leading index keeps its own set of spatial labels.
                    assert torch.equal(torch.sort(augmented.reshape(*shape[:-2], -1), dim=-1).values,
                                       torch.sort(x.reshape(*shape[:-2], -1), dim=-1).values)
                    if view["feature_inverse_ast"] is not None:
                        assert torch.equal(apply_view(view, augmented, inverse=True, feature=True), x)
                    transformed.append(augmented)
                groups = []
                for index, value in enumerate(transformed):
                    match = next((g for g in groups if value.shape == transformed[g[0]].shape and torch.equal(value, transformed[g[0]])), None)
                    if match is None:
                        groups.append([index])
                    else:
                        match.append(index)
                unique = 8 if arm == "C1" else 7
                assert len(groups) == unique, (arm, role, shape, groups)
                if arm != "C1":
                    assert [g for g in groups if len(g) > 1] == [[1, 7]]
                rows.append({"arm": arm, "role": role, "shape": list(shape), "passes": 8,
                             "unique": len(groups), "duplicate_groups_zero_based": [g for g in groups if len(g) > 1],
                             "all_inverse_exact": True, "leading_axes_preserved": True,
                             "feature_inverse_checks": sum(v["feature_inverse_ast"] is not None for v in views)})
    # 5x5 has no swapped-shape distinction: uniqueness is proven by index maps.
    return rows


def load_real_methods():
    source = (SUPPORT / "scripts/train_unet_transformer.py").read_text()
    tree = ast.parse(source)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "UNetNodeTransformer")
    methods = {}
    for name in ("encode", "_index_features", "predict_edges"):
        node = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == name)
        namespace = {"torch": torch}
        exec(compile(ast.Module(body=[copy.deepcopy(node)], type_ignores=[]), str(SUPPORT / "scripts/train_unet_transformer.py"), "exec"), namespace)
        methods[name] = namespace[name]
    return methods


REAL = load_real_methods()


class SmallModel:
    _index_features = REAL["_index_features"]

    def __init__(self, role, uniform_features=False):
        self.role = role
        self.training = False
        self.uniform_features = uniform_features
        self.inputs, self.features, self.feature_copies = [], [], []
        self.raw_logits, self.logit_copies, self.edge_calls = [], [], []

    def unet(self, window):
        # Input layout is verified against the real encode method: B,W,1,Z,Y,X.
        h, w = window.shape[-2:]
        if self.uniform_features:
            base = torch.ones_like(window) * 2
        else:
            xx = torch.arange(w, dtype=window.dtype).view(*([1] * (window.ndim - 1)), w)
            yy = torch.arange(h, dtype=window.dtype).view(*([1] * (window.ndim - 2)), h, 1)
            base = window * (1 + xx / 9) + yy / 13
        role_scale = 0.83 if self.role == "secondary" else 1.0
        return torch.cat((base * role_scale, base.square() * 0.1 + 0.7), dim=2)

    def detect_head(self, feature):
        return feature[:, :1] * 0.3 + feature[:, 1:2] * 0.7

    def encode(self, imgs):
        self.inputs.append(imgs.clone())
        feature, logits = REAL["encode"](self, imgs)
        self.features.append(feature)
        self.feature_copies.append(feature.clone())
        self.raw_logits.extend(logits)
        self.logit_copies.extend(x.clone() for x in logits)
        return feature, logits

    def transformer(self, src, tgt, *args):
        return torch.einsum("bnc,bmc->bnm", src, tgt) * 0.002

    def predict_edges(self, src, tgt, *args):
        self.edge_calls.append((src.clone(), tgt.clone()))
        return REAL["predict_edges"](self, src, tgt, *args)


@contextlib.contextmanager
def task_environment():
    updates = {"BIOHUB_EDGE_FEATURE_TTA": "1", "BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT": "0.15",
               "BIOHUB_DUAL_SEED_MIN_CANDIDATE_RETENTION": "0.90"}
    previous = {k: os.environ.get(k) for k in updates}
    os.environ.update(updates)
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def run_encoding_and_association(source, uniform_secondary=False, audited=None):
    primary = SmallModel("primary")
    secondary = SmallModel("secondary", uniform_features=uniform_secondary)
    shape = (1, 2, 4, 5, 7)
    images = torch.arange(np.prod(shape), dtype=torch.float32).reshape(shape) / 100
    ns = {"torch": torch, "os": os, "json": json, "Path": Path,
          "imgs": images, "model": primary, "secondary_model": secondary,
          "cfg": SimpleNamespace(det_tta=True, det_threshold=0.965), "W": 2,
          "secondary_detection_weight": 0.80, "frame_indices": [0, 1],
          "secondary_link_mode": "low_margin_consensus", "secondary_edge_weight": 0.15,
          "seen_frames": {0, 1}, "pool_k": (1, 1, 1),
          # Keep the real frame-retention arithmetic but avoid I/O and real peak detection.
          "_detect_cells_pooled": lambda *args: [0, 1], "ds_path": Path("synthetic.zarr")}
    capture = io.StringIO()
    with task_environment(), contextlib.redirect_stdout(capture):
        exec(compile(encoding_block(audited or source), "actual_expanded_encoding_block", "exec"), ns)
        views = actual_views(encoding_block(source), "secondary")
        # Reference uses the actual inverse expressions and the already produced
        # feature tensors, with a fresh out-of-place sum for alias detection.
        average = secondary.feature_copies[0].clone()
        for view, tensor in zip(views[1:], secondary.feature_copies[1:]):
            average = average + apply_view(view, tensor, inverse=True)
        average = average / 8
        ns.update({"f_idx": 0, "n_src": 3, "n_tgt": 3,
                   "p_coords_src": torch.tensor([[[0, 0, 0], [1, 2, 3], [2, 4, 6]]], dtype=torch.float32),
                   "p_coords_tgt": torch.tensor([[[0, 1, 1], [1, 3, 4], [3, 4, 6]]], dtype=torch.float32),
                   "p_mask_src": torch.ones((1, 3), dtype=torch.bool),
                   "p_mask_tgt": torch.ones((1, 3), dtype=torch.bool),
                   "p_pos_src": torch.zeros((1, 3, 2)), "p_pos_tgt": torch.zeros((1, 3, 2)),
                   "ds_arr_t": torch.tensor((1, 4, 4)), "secondary_link_mode": "low_margin_consensus",
                   "secondary_edge_weight": 0.15, "secondary_low_margin_max": 0.35,
                   "secondary_mix_temperature": 1.0})
        exec(compile(association_block(audited or source), "actual_expanded_association_block", "exec"), ns)
        if audited:
            ns["_p946_end"](ns["_p946_context"])
    assert len(primary.inputs) == len(secondary.inputs) == 8
    for model in (primary, secondary):
        assert all(torch.equal(a, b) for a, b in zip(model.features, model.feature_copies)), "raw encode feature was mutated"
        assert all(torch.equal(a, b) for a, b in zip(model.raw_logits, model.logit_copies)), "raw detection logits were mutated"
    assert len(primary.edge_calls) == 2 and len(secondary.edge_calls) == (2 if audited else 1)
    for frame, coords, mask, sampled in (
        (0, ns["p_coords_src"], ns["p_mask_src"], secondary.edge_calls[0][0]),
        (1, ns["p_coords_tgt"], ns["p_mask_tgt"], secondary.edge_calls[0][1]),
    ):
        expected = REAL["_index_features"](secondary, ns["secondary_unet_out"][:, frame], coords, mask)
        assert torch.equal(expected, sampled), "average bypassed actual secondary association"
    assert all(torch.isfinite(ns[n]).all() for n in ("unet_out", "secondary_unet_out", "edge_logits_pair"))
    assert ns["secondary_unet_out"].dtype == torch.float32
    assert ns["secondary_unet_out"].device.type == "cpu"
    return {"namespace": ns, "primary": primary, "secondary": secondary, "reference_average": average,
            "stdout": capture.getvalue(), "shape": shape}


def integration_checks(sources):
    runs = {arm: run_encoding_and_association(source) for arm, source in sources.items()}
    b0, c1, c2 = [runs[a] for a in ("B0", "C1", "C2")]
    assert torch.equal(b0["namespace"]["secondary_unet_out"], b0["secondary"].feature_copies[0])
    assert torch.equal(c1["namespace"]["secondary_unet_out"], c1["secondary"].feature_copies[0])
    assert torch.equal(c2["namespace"]["secondary_unet_out"], c2["reference_average"])
    assert torch.equal(b0["namespace"]["unet_out"], c2["namespace"]["unet_out"]), "C2 changed primary features"
    assert all(torch.equal(a, b) for a, b in zip(b0["namespace"]["det_logits"], c2["namespace"]["det_logits"])), "C2 changed detection aggregate"
    assert all(torch.equal(a, b) for a, b in zip(b0["primary"].inputs, c2["primary"].inputs))
    assert all(torch.equal(a, b) for a, b in zip(b0["secondary"].inputs, c2["secondary"].inputs))
    probability_delta = (torch.softmax(c2["namespace"]["secondary_logits_pair"], dim=1) - torch.softmax(b0["namespace"]["secondary_logits_pair"], dim=1)).abs().mean().item()
    assert probability_delta > 0
    zero = run_encoding_and_association(sources["C2"], uniform_secondary=True)
    assert torch.equal(zero["namespace"]["secondary_unet_out"], zero["secondary"].feature_copies[0])
    rows = {}
    for arm, run in runs.items():
        ns = run["namespace"]
        rows[arm] = {"primary_encode_calls": len(run["primary"].inputs),
                     "secondary_encode_calls": len(run["secondary"].inputs),
                     "primary_association_calls": len(run["primary"].edge_calls),
                     "secondary_association_calls": len(run["secondary"].edge_calls),
                     "input_shape": list(run["shape"]), "input_axes": ["batch", "window_time", "Z", "Y", "X"],
                     "feature_shape": list(ns["secondary_unet_out"].shape),
                     "feature_axes": ["batch", "window_time", "channel", "Z", "Y", "X"],
                     "dtype": str(ns["secondary_unet_out"].dtype), "device": str(ns["secondary_unet_out"].device),
                     "secondary_mean_abs_feature_delta": float((ns["secondary_unet_out"] - run["secondary"].feature_copies[0]).abs().mean()),
                     "raw_feature_and_logits_unmutated": True, "actual_coordinate_indexing_consumed": True,
                     "finite": True, "association_mode": "low_margin_consensus", "edge_weight": 0.15}
    return {"arms": rows, "C2_primary_features_equal_B0": True,
            "C2_detection_logits_equal_B0": True, "C2_average_exact": True,
            "C2_secondary_probability_mean_abs_delta": probability_delta,
            "C2_uniform_secondary_zero_delta_allowed": True,
            "limitation": "Deterministic CPU doubles replace pretrained UNet and edge-transformer weights; this proves data flow and arithmetic, not GPU/model quality or score."}


def common_runtime_checks(sources, audited_sources):
    import runtime_audit
    previous_module = sys.modules.get("public946_runtime")
    previous_path = runtime_audit.Path
    previous_arm = os.environ.get("BIOHUB_PUBLIC946_ARM")
    sys.modules["public946_runtime"] = runtime_audit
    rows = {}
    try:
        with tempfile.TemporaryDirectory(prefix="public946_actual_hook_") as directory:
            for arm, source in sources.items():
                runtime_audit._VIDEOS.clear()
                output = Path(directory) / arm
                output.mkdir()
                runtime_audit.Path = lambda value: output if value == "/kaggle/working" else Path(value)
                os.environ["BIOHUB_PUBLIC946_ARM"] = arm
                plain = run_encoding_and_association(source)
                before_rng = torch.random.get_rng_state().clone()
                traced = run_encoding_and_association(source, audited=audited_sources[arm])
                assert torch.equal(before_rng, torch.random.get_rng_state()), "common diagnostic changed RNG state"
                for name in ("unet_out", "secondary_unet_out", "edge_logits_pair"):
                    assert torch.equal(plain["namespace"][name], traced["namespace"][name]), (arm, name)
                assert all(torch.equal(a, b) for a, b in zip(plain["namespace"]["det_logits"], traced["namespace"]["det_logits"]))
                paths = list(output.glob("*.jsonl"))
                assert len(paths) == 1
                records = [json.loads(line) for line in paths[0].read_text().splitlines()]
                assert len(records) == 1
                record = records[0]
                assert record["encode_calls"] == {"primary": 8, "secondary": 8}
                assert record["association"]["diagnostic_encoder_calls"] == 0
                assert record["association"]["diagnostic_edge_head_calls"] == 1
                assert record["association"]["actual_secondary_feature_consumed"] is True
                assert record["association"]["diagnostic_probabilities_used_in_production"] is False
                assert all(v["all_finite"] for v in record["consumed_heatmaps"])
                assert traced["namespace"]["_p946_context"]["base_features"] == {}
                rows[arm] = {"status": "PASS", "prediction_tensors_equal_unaudited": True,
                             "rng_state_unchanged": True, "retained_baseline_features_released": True,
                             "runtime_record": record}
    finally:
        runtime_audit.Path = previous_path
        runtime_audit._VIDEOS.clear()
        if previous_module is None:
            sys.modules.pop("public946_runtime", None)
        else:
            sys.modules["public946_runtime"] = previous_module
        if previous_arm is None:
            os.environ.pop("BIOHUB_PUBLIC946_ARM", None)
        else:
            os.environ["BIOHUB_PUBLIC946_ARM"] = previous_arm
    return rows


def main():
    started = time.perf_counter()
    receipt = {"task_id": "PUBLIC946_TTA_20260908", "observed_at_utc": datetime.now(timezone.utc).isoformat(),
               "status": "RUNNING", "python": sys.version, "torch": torch.__version__, "numpy": np.__version__,
               "platform": platform.platform(), "device": "cpu", "gpu_smoke": "NOT_RUN_LOCAL_CPU_TEST",
               "environment_resolution": {"initial_default_import": "FAILED_DUPLICATE_OPENMP_RUNTIME", "resolution": "Process-only DYLD_LIBRARY_PATH=/opt/anaconda3/envs/ml/lib selects one existing libomp; no packages or global settings changed.", "KMP_DUPLICATE_LIB_OK": "NOT_USED"},
               "checks": {}}
    try:
        from build_candidates import expand_public_predictor
        from tta_patch import patch_expanded_predictor
        original = (SUPPORT / "scripts/predict_unet_transformer.py").read_text()
        assert sha(original) == "c44e771ba5980b820f93091e03a303c25dfe8f3232e501f54dc9565731c234b9"
        expanded, expansion = expand_public_predictor(original)
        sources, audited_sources, patches = {}, {}, {}
        for arm in ("B0", "C1", "C2"):
            sources[arm], patches[arm] = patch_expanded_predictor(expanded, arm, audit=False)
            audited, audited_receipt = patch_expanded_predictor(expanded, arm, audit=True)
            audited_sources[arm] = audited
            compile(sources[arm], f"{arm}_algorithm.py", "exec")
            compile(audited, f"{arm}_actual_runtime.py", "exec")
            patches[arm]["audited_expanded_sha256"] = sha(audited)
            patches[arm]["audited_replacements"] = audited_receipt["replacements"]
        assert sources["B0"] == expanded
        receipt["checks"]["dynamic_expansion"] = {"status": "PASS", "public": expansion, "candidates": patches,
                                                      "B0_algorithm_byte_equal_public_expansion": True, "all_full_predictors_compile": True}
        receipt["checks"]["actual_transform_expressions"] = {"status": "PASS", "cases": transformation_checks(sources)}
        receipt["checks"]["actual_encode_and_association_blocks"] = {"status": "PASS", **integration_checks(sources)}
        receipt["checks"]["identical_common_runtime_hooks"] = {"status": "PASS", "arms": common_runtime_checks(sources, audited_sources)}
        receipt["status"] = "PASS"
    except Exception:
        receipt["status"] = "FAIL"
        receipt["failure"] = traceback.format_exc()
    receipt["seconds"] = time.perf_counter() - started
    receipt["test_script_sha256"] = sha(Path(__file__).read_bytes())
    receipt["source_file_sha256"] = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in
                                    [SUPPORT / "scripts/predict_unet_transformer.py", SUPPORT / "scripts/train_unet_transformer.py", BATCH / "tta_patch.py", BATCH / "runtime_audit.py"] if p.exists()}
    destination = BATCH / "test_results.json"
    destination.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"status": receipt["status"], "seconds": receipt["seconds"], "receipt": str(destination),
                      "checks": {k: v["status"] for k, v in receipt["checks"].items()}, "failure": receipt.get("failure")}, ensure_ascii=False))
    return 0 if receipt["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
