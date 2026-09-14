#!/usr/bin/env python3
"""Actual tiny-graph comparisons against the pinned official full chain.

Run with the existing task-local scorer environment. No Notebook top level,
model, competition dataset, Kaggle API or Git operation is executed.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import platform
import sys
import time
import types
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl
import tracksdata as td
from scipy.optimize import linear_sum_assignment

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASELINE_SHA = "bb6dbf2766fff1b4f7d1c96f3c1145c700d4d44e4695d924c7be8ccbe1b07af7"
OFFICIAL_HASHES = {
    "metrics.py": "cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444",
    "division_metrics.py": "0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9",
}
SCALE = (1.625, 0.40625, 0.40625)
FUNCTIONS = {
    "match_nodes_bipartite", "compute_edge_confusion", "edge_jaccard", "adjusted_jaccard",
    "weakly_connected_components", "compute_division_confusion", "decompose_errors",
    "score_sample", "aggregate_official",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_official():
    folder = HERE / "vendor/official_075fc5"
    for name, expected in OFFICIAL_HASHES.items():
        if digest(folder / name) != expected:
            raise RuntimeError(f"Official source checksum mismatch: {name}")
    package = types.ModuleType("target950_test_official")
    package.__path__ = [str(folder)]
    sys.modules[package.__name__] = package
    name = package.__name__ + ".metrics"
    spec = importlib.util.spec_from_file_location(name, folder / "metrics.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_scope(notebook, official):
    if digest(notebook) != BASELINE_SHA:
        raise RuntimeError("Unexpected Forge947 baseline source")
    cells = json.loads(notebook.read_bytes())["cells"]
    cell8 = "".join(cells[8]["source"])
    functions = [n for n in ast.parse(cell8).body if isinstance(n, ast.FunctionDef) and n.name in FUNCTIONS]
    assert {n.name for n in functions} == FUNCTIONS
    scope = {"np": np, "linear_sum_assignment": linear_sum_assignment,
             "VOXEL_SCALE_UM": SCALE, "VALIDATOR_MATCH_RADIUS_UM": 7.0,
             "VALIDATOR_NODE_COUNT_PENALTY_A": 0.1, "VALIDATOR_DIVISION_WEIGHT": 0.1,
             "OFFICIAL_METRICS": official}
    exec(compile(ast.Module(body=functions, type_ignores=[]), "Forge947_original_cell8_functions", "exec"), scope)
    adapter = HERE / "official_selector_adapter.py"
    exec(compile(adapter.read_text(), str(adapter), "exec"), scope)
    receipt = scope["install_official_selector"](scope)
    return scope, cells, receipt


def direct_graph(nodes, edges):
    """Independent simple builder using single-node/edge API, not the adapter."""
    graph = td.graph.InMemoryGraph()
    for key in ("z", "y", "x"):
        graph.add_node_attr_key(key, pl.Float64, 0.0)
    remap = {}
    for node_id, (t, z, y, x) in nodes.items():
        remap[node_id] = graph.add_node({"t": int(t), "z": float(z), "y": float(y), "x": float(x)})
    for source, target in edges:
        graph.add_edge(remap[source], remap[target], {})
    return graph


def direct_chain(metrics, pn, pe, gn, ge, n_total, repair_edgeless_recall=False):
    pred, gt = direct_graph(pn, pe), direct_graph(gn, ge)
    result = metrics.evaluate(pred, gt, scale=SCALE, max_distance=7.0)
    if repair_edgeless_recall and not pe:
        from tracksdata.metrics import DistanceMatching
        pred.match(gt, matching=DistanceMatching(scale=SCALE, max_distance=7.0))
    row = metrics.per_sample_metrics(result, n_total, metrics.node_recall(pred, gt))
    return row, metrics.summarise([row])


def division_fixtures():
    # Extract only the immutable hand-built synthetic fixtures from the earlier
    # diagnostic, without importing its main, graph scans, writes or executions.
    path = ROOT / "experiments/LINEFIT_BOUNDARY_20260909/scorer_diagnostic.py"
    nodes = [n for n in ast.parse(path.read_text()).body
             if isinstance(n, ast.FunctionDef) and n.name in {"graph", "fixtures"}]
    scope = {"SCALE": SCALE}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "original_synthetic_fixture_definitions", "exec"), scope)
    values = scope["fixtures"]()

    def plain(spec):
        # Use widely separated, nonconsecutive IDs to catch accidental ID reuse.
        ids = {name: 17 + 23 * index for index, name in enumerate(spec["nodes_t_y_um"])}
        ns = {ids[name]: (int(t), 0.0, y / SCALE[1], 0.0)
              for name, (t, y) in spec["nodes_t_y_um"].items()}
        es = [(ids[a], ids[b]) for a, b in spec["edges"]]
        return ns, es

    return [(item, *plain(item["pred"]), *plain(item["gt"])) for item in values["cases"]], values


def selector_fragments(cells):
    """Compile actual original cell10 selection statements, not a rewrite."""
    tree = ast.parse("".join(cells[10]["source"]))
    blocks = []
    for node in tree.body:
        if isinstance(node, ast.If) and any(isinstance(n, ast.Assign) and
                any(isinstance(t, ast.Name) and t.id == "base_summary" for t in n.targets)
                for n in node.body):
            blocks = node.body
            break
    selected = []
    for node in blocks:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, (ast.Name, ast.Tuple)) and
            (getattr(target, "id", None) in {"ranked"} or
             isinstance(target, ast.Tuple) and any(getattr(x, "id", None) == "best_label" for x in target.elts))
            for target in node.targets
        ):
            selected.append(node)
        if isinstance(node, ast.If) and any(isinstance(n, ast.Assign) and
                any(getattr(t, "id", None) == "selected_label" for t in n.targets) for n in node.body):
            selected.append(node)
    if len(selected) != 3:
        raise RuntimeError("Unable to uniquely extract original final selector")
    return compile(ast.Module(body=selected, type_ignores=[]), "original_cell10_final_selector", "exec")


def clean(value):
    if isinstance(value, float) and not math.isfinite(value):
        return "NaN" if math.isnan(value) else str(value)
    if isinstance(value, dict):
        return {str(key): clean(v) for key, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [clean(v) for v in value]
    if isinstance(value, np.generic):
        return clean(value.item())
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--notebook", type=Path, default=HERE / "baseline/candidate.ipynb")
    parser.add_argument("--output", type=Path, default=Path("/private/tmp/target950_selector_tests.json"))
    args = parser.parse_args()
    started = time.perf_counter()
    metrics = load_official()
    scope, cells, installation = load_scope(args.notebook, metrics)
    checks, results = [], []

    def check(label, actual, expected):
        if isinstance(actual, float) and isinstance(expected, (int, float)):
            ok = (math.isnan(actual) and math.isnan(expected)) or math.isclose(actual, expected, rel_tol=1e-11, abs_tol=1e-12)
        else:
            ok = actual == expected
        checks.append({"id": label, "actual": clean(actual), "expected": clean(expected),
                       "status": "PASS" if ok else "FAIL"})

    def raises(label, fn, error):
        try:
            fn()
        except error as exc:
            checks.append({"id": label, "status": "PASS", "exception": type(exc).__name__, "message": str(exc)})
        except Exception as exc:
            checks.append({"id": label, "status": "FAIL", "unexpected_exception": type(exc).__name__, "message": str(exc)})
        else:
            checks.append({"id": label, "status": "FAIL", "message": "Expected exception was not raised"})

    def compare(label, pn, pe, gn, ge, n_total, empty_recall=False):
        before = copy.deepcopy((pn, pe, gn, ge))
        row = scope["score_sample"](pn, pe, gn, ge, n_total)
        summary = scope["aggregate_official"]([row])
        direct, direct_summary = direct_chain(metrics, pn, pe, gn, ge, n_total, empty_recall)
        for key in metrics.METRIC_COLUMNS:
            check(label + ".row." + key, row[key], direct[key])
        for key in ("score", "adj_edge_jaccard", "division_tp", "division_fp", "division_fn", "n", "n_adj"):
            check(label + ".summary." + key, summary[key], direct_summary[key])
        check(label + ".selector_alias", summary["proxy_score"], direct_summary["score"])
        check(label + ".input_unmodified", (pn, pe, gn, ge), before)
        check(label + ".error_provenance", "unchanged_forge947_cell8_proxy" in row["error_decomposition_provenance"], True)
        results.append({"id": label, "official_summary": direct_summary, "adapter_summary": summary})
        return row, summary

    cases, fixture_inputs = division_fixtures()
    good_rows = []
    for item, pn, pe, gn, ge in cases:
        row, summary = compare(item["id"], pn, pe, gn, ge, item["n_total"])
        oc = [row[key] for key in ("edge_tp", "edge_fp", "edge_fn", "div_tp", "div_fp", "div_fn")]
        pc = [row["legacy_proxy_" + key] for key in ("edge_tp", "edge_fp", "edge_fn", "div_tp", "div_fp", "div_fn")]
        check(item["id"] + ".known_official_counts", oc, item["expected_official_counts"])
        check(item["id"] + ".known_legacy_counterexample", pc, item["expected_proxy_counts"])
        good_rows.append(row)

    straight = {101: (0, 0., 0., 0.), 903: (1, 0., 0., 0.), 8001: (2, 0., 0., 0.)}
    straight_edges = [(101, 903), (903, 8001)]
    row, summary = compare("straight_no_divisions", straight, straight_edges, straight, straight_edges, 3)
    check("no_divisions_term_dropped", summary["score"], 1.0)
    check("no_divisions_jaccard_nan", math.isnan(summary["division_jaccard"]), True)
    stable = scope["score_sample"](copy.deepcopy(straight), list(straight_edges),
                                   copy.deepcopy(straight), list(straight_edges), 3)
    check("same_graph_hash_stable", stable["input_pred_graph_sha256"], row["input_pred_graph_sha256"])
    check("same_gt_hash_stable", stable["input_gt_graph_sha256"], row["input_gt_graph_sha256"])
    check("identical_pred_gt_hashes", row["input_pred_graph_sha256"], row["input_gt_graph_sha256"])
    check("graph_hash_sha256_length", len(row["input_pred_graph_sha256"]), 64)
    check("graph_hash_same_input_provenance", row["input_graph_provenance"],
          "same_plain_graph_received_by_legacy_proxy_and_official_adapter")
    check("hash_records_n_total", row["input_n_total"], 3.)
    check("hash_records_scale", row["input_scale_zyx_um"], SCALE)
    check("hash_records_radius", row["input_match_radius_um"], 7.)
    moved = dict(straight)
    moved[101] = (0, .125, 0., 0.)
    moved_row = scope["score_sample"](moved, straight_edges, straight, straight_edges, 3)
    check("coordinate_change_changes_pred_hash", moved_row["input_pred_graph_sha256"] != row["input_pred_graph_sha256"], True)
    check("coordinate_change_preserves_gt_hash", moved_row["input_gt_graph_sha256"], row["input_gt_graph_sha256"])
    reverse_nodes = dict(reversed(list(straight.items())))
    order_row = scope["score_sample"](reverse_nodes, straight_edges, straight, straight_edges, 3)
    check("node_insertion_order_is_hashed", order_row["input_pred_graph_sha256"] != row["input_pred_graph_sha256"], True)
    order_row = scope["score_sample"](straight, list(reversed(straight_edges)), straight, straight_edges, 3)
    check("edge_order_is_hashed", order_row["input_pred_graph_sha256"] != row["input_pred_graph_sha256"], True)
    numeric_types = {np.int64(k): (np.int64(t), np.float64(z), np.float32(y), np.float64(x))
                     for k, (t, z, y, x) in straight.items()}
    numeric_row = scope["score_sample"](numeric_types, straight_edges, straight, straight_edges, np.float64(3))
    check("hash_normalizes_python_numeric_types", numeric_row["input_pred_graph_sha256"], row["input_pred_graph_sha256"])
    check("repeated_official_and_proxy_leave_nodes_unchanged", straight,
          {101: (0, 0., 0., 0.), 903: (1, 0., 0., 0.), 8001: (2, 0., 0., 0.)})
    check("repeated_official_and_proxy_leave_edges_unchanged", straight_edges, [(101, 903), (903, 8001)])
    compare("duplicate_edges", straight, straight_edges * 2, straight, straight_edges, 3)
    compare("nonconsecutive_and_backward_edges", straight, straight_edges + [(101, 8001), (8001, 101)], straight, straight_edges, 3)
    inflated = dict(straight)
    inflated.update({20000 + i: (0, 0., 1000. + i * 100, 0.) for i in range(3)})
    ir, isum = compare("isolated_nodes_penalty", inflated, straight_edges, straight, straight_edges, 3)
    check("isolated_nodes_preserved", ir["num_pred_nodes"], 6)
    check("isolated_nodes_adjusted", isum["score"], 0.9)

    shifted_ok = {key: (t, z + 4, y, x) for key, (t, z, y, x) in straight.items()}
    shifted_bad = {key: (t, z + 5, y, x) for key, (t, z, y, x) in straight.items()}
    _, within = compare("z_scale_6p5um", shifted_ok, straight_edges, straight, straight_edges, 3)
    _, outside = compare("z_scale_8p125um", shifted_bad, straight_edges, straight, straight_edges, 3)
    check("anisotropic_scale_inside", within["score"], 1.0)
    check("anisotropic_scale_outside", outside["score"], 0.0)

    raises("direct_official_empty_recall_bug", lambda: direct_chain(metrics, {}, [], straight, straight_edges, 3), KeyError)
    raises("direct_official_isolated_recall_bug", lambda: direct_chain(metrics, straight, [], straight, straight_edges, 3), KeyError)
    erow, empty = compare("empty_prediction_explicit_match", {}, [], straight, straight_edges, 3, True)
    irow, isolated = compare("edgeless_prediction_explicit_match", straight, [], straight, straight_edges, 3, True)
    check("empty_prediction_recall", erow["node_recall"], 0.0)
    check("empty_prediction_score", empty["score"], 0.0)
    check("edgeless_prediction_recall", irow["node_recall"], 1.0)
    check("edgeless_prediction_score", isolated["score"], 0.0)

    for value in (None, 0, -1, float("nan"), float("inf"), True):
        raises("invalid_n_total_" + str(value), lambda v=value: scope["score_sample"](straight, straight_edges, straight, straight_edges, v), ValueError)
    raises("empty_gt_fail_closed", lambda: scope["score_sample"](straight, straight_edges, {}, [], 3), ValueError)
    raises("fractional_frame_rejected", lambda: scope["score_sample"]({7: (.5, 0., 0., 0.)}, [], straight, straight_edges, 3), ValueError)
    raises("nonfinite_coordinate_rejected", lambda: scope["score_sample"]({7: (0, 0., float("nan"), 0.)}, [], straight, straight_edges, 3), ValueError)
    raises("dangling_edge_rejected", lambda: scope["score_sample"](straight, [(101, 999999)], straight, straight_edges, 3), ValueError)
    raises("no_double_installation", lambda: scope["install_official_selector"](scope), RuntimeError)

    mixed_rows = [good_rows[0], ir, row]
    mixed = scope["aggregate_official"](mixed_rows)
    direct = metrics.summarise(mixed_rows)
    check("weighted_full_chain", mixed["score"], direct["score"])
    bad_row = dict(row)
    bad_row.update(metrics.nan_metrics_row())
    nan_mixed = scope["aggregate_official"]([row, bad_row])
    check("official_nan_row_skip_count", nan_mixed["official_rows_skipped"], 1)
    check("official_nan_row_skip_score", nan_mixed["score"], metrics.summarise([row, bad_row])["score"])
    adj_nan = dict(row, adj_edge_jaccard=float("nan"))
    am = scope["aggregate_official"]([row, adj_nan])
    check("official_nan_adjustment_skip_count", am["official_adjusted_rows_used"], 1)
    check("official_nan_adjustment_score", am["score"], metrics.summarise([row, adj_nan])["score"])
    raises("all_nan_fail_closed", lambda: scope["aggregate_official"]([bad_row]), ValueError)
    raises("all_adj_nan_fail_closed", lambda: scope["aggregate_official"]([adj_nan]), ValueError)
    raises("empty_aggregate_fail_closed", lambda: scope["aggregate_official"]([]), ValueError)
    raises("legacy_row_cannot_enter_official_aggregate", lambda: scope["aggregate_official"]([scope["legacy_score_sample"](straight, straight_edges, straight, straight_edges, 3)]), ValueError)
    isolated_only = scope["score_sample"](straight, [], straight, [], 3)
    raises("no_edge_mass_aggregate_fail_closed", lambda: scope["aggregate_official"]([isolated_only]), ValueError)

    selector = selector_fragments(cells)
    base = {"proxy_score": .75, "adjusted_edge_jaccard": .70}
    for name, candidate, expected in [
        ("margin_equal_pass", {"proxy_score": .75 + .001, "adjusted_edge_jaccard": .70}, "c"),
        ("margin_below_fail", {"proxy_score": np.nextafter(.75 + .001, -np.inf), "adjusted_edge_jaccard": .70}, "base"),
        ("adj_loss_equal_pass", {"proxy_score": .8, "adjusted_edge_jaccard": .70 - .0005}, "c"),
        ("adj_loss_below_fail", {"proxy_score": .8, "adjusted_edge_jaccard": np.nextafter(.70 - .0005, -np.inf)}, "base"),
        ("score_tie_keeps_base", dict(base), "base"),
    ]:
        local = {"PP_RESULTS": {"base": base, "c": candidate}, "base_summary": base,
                 "PP_SELECT_MARGIN": .001, "PP_MAX_ADJ_LOSS": .0005,
                 "PP_CANDIDATES": {"c": {"MOTION_RELINK_TIGHT_UM": 5.5}},
                 "selected_label": "base", "selected_config": {}}
        exec(selector, local)
        check("original_selector." + name, local["selected_label"], expected)

    # A 1000-node / 980-edge graph: 20 separate 50-frame straight tracks.
    large_nodes = {500003 + t * 1009 + chain * 1000003:
                   (t, 0., chain * 30 / SCALE[1], 0.)
                   for chain in range(20) for t in range(50)}
    large_edges = [(500003 + t * 1009 + chain * 1000003,
                    500003 + (t + 1) * 1009 + chain * 1000003)
                   for chain in range(20) for t in range(49)]
    bulk_counts = {"nodes": 0, "edges": 0}
    original_nodes, original_edges = td.graph.InMemoryGraph.bulk_add_nodes, td.graph.InMemoryGraph.bulk_add_edges

    def count_nodes(self, values, *a, **kw):
        if len(values) == 1000:
            bulk_counts["nodes"] += 1
        return original_nodes(self, values, *a, **kw)

    def count_edges(self, values, *a, **kw):
        if len(values) == 980:
            bulk_counts["edges"] += 1
        return original_edges(self, values, *a, **kw)

    large_started = time.perf_counter()
    td.graph.InMemoryGraph.bulk_add_nodes = count_nodes
    td.graph.InMemoryGraph.bulk_add_edges = count_edges
    try:
        large_row = scope["score_sample"](large_nodes, large_edges, large_nodes, large_edges, 1000)
    finally:
        td.graph.InMemoryGraph.bulk_add_nodes = original_nodes
        td.graph.InMemoryGraph.bulk_add_edges = original_edges
    large_summary = scope["aggregate_official"]([large_row])
    large_seconds = time.perf_counter() - large_started
    check("large_1000_nodes", large_row["num_pred_nodes"], 1000)
    check("large_980_tp_edges", large_row["edge_tp"], 980)
    check("large_score", large_summary["score"], 1.0)
    check("large_bulk_node_calls_used", bulk_counts["nodes"] >= 2, True)
    check("large_bulk_edge_calls_used", bulk_counts["edges"] >= 2, True)

    result = {
        "status": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL",
        "evidence_class": "MEASURED", "executed": True,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "script_sha256": digest(Path(__file__)),
        "adapter_sha256": digest(HERE / "official_selector_adapter.py"),
        "baseline_sha256": digest(args.notebook), "official_source_sha256": OFFICIAL_HASHES,
        "runtime": {"python": platform.python_version(), "executable": sys.executable,
                    "dependencies": {name: importlib.metadata.version(name) for name in ("tracksdata", "polars", "numpy", "scipy", "rustworkx")}},
        "installation": installation, "checks": checks,
        "check_summary": {"total": len(checks), "passed": sum(c["status"] == "PASS" for c in checks),
                          "failed": sum(c["status"] == "FAIL" for c in checks)},
        "case_results": results, "fixture_inputs": fixture_inputs,
        "large_graph": {"nodes": 1000, "edges": 980, "seconds": large_seconds, "bulk_calls": bulk_counts},
        "total_seconds": time.perf_counter() - started,
        "limits": ["Synthetic local execution only; no production graph rescore or Kaggle formal score.",
                   "Official source identity does not establish the private deployed Kaggle scorer identity.",
                   "Existing local venv differs from Kaggle NumPy/SciPy versions; not a bytewise runtime reproduction.",
                   "Edgeless predictions require explicit official node matching after evaluate to obtain recall.",
                   "Nonfinite aggregate or missing n_total raises; no proxy fallback.",
                   "Runtime smoke uses 1000 nodes; full 8-FOV automatic selection runtime remains NOT_RUN."],
    }
    args.output.write_text(json.dumps(clean(result), indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "checks": result["check_summary"],
                      "output": str(args.output), "seconds": result["total_seconds"],
                      "large_seconds": large_seconds}))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        raise SystemExit(main())
