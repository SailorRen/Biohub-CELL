"""Execute the real extracted B0/candidate linefit functions on small graphs."""
from __future__ import annotations

import copy
import hashlib
import json
import platform
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from build_candidate import BASE, HERE, build, source
from linefit_patch import DIAGNOSTIC_KEYS, function_span, patch_cell


SCALE = [1.625, 0.40625, 0.40625]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def coordinate_bytes(nodes: dict) -> bytes:
    return np.asarray([[nodes[k][c] for c in ("z", "y", "x")] for k in sorted(nodes)], dtype="<f8").tobytes()


def node(t, z, y, x, label="preserve"):
    return {"t": t, "z": z, "y": y, "x": x, "label": label,
            "metadata": {"kept": [True, 3, "unchanged"]}}


def chain(curved=False, size=9):
    nodes = {i: node(i, 2 + .13 * i, 7 + (.21 * i * i if curved else .8 * i),
                     3 + (.13 * i ** 3 if curved else .4 * i)) for i in range(size)}
    edges = [{"source_id": i, "target_id": i + 1, "edge_prob": .91, "tag": "keep"} for i in range(size - 1)]
    return nodes, edges


def fork():
    nodes = {-2: node(-2, 4, 5, 6), -1: node(-1, 4.2, 5.6, 6.5),
             0: node(0, 4.4, 6.0, 7.2)}
    edges = [{"source_id": -2, "target_id": -1, "edge_prob": .92},
             {"source_id": -1, "target_id": 0, "edge_prob": .93}]
    for branch, sign in [(10, 1), (20, -1)]:
        prev = 0
        for t in range(1, 5):
            key = branch + t
            nodes[key] = node(t, 4.4 + .12 * t ** 2, 6 + sign * .17 * t ** 2,
                              7.2 + sign * .11 * t ** 3, label=f"branch-{branch}")
            edges.append({"source_id": prev, "target_id": key, "edge_prob": .94})
            prev = key
    return nodes, edges


def compile_function(text):
    _, _, body = function_span(text)
    namespace = {"np": np, "OUTPUT_LINEFIT_SMOOTH": True,
                 "OUTPUT_LINEFIT_WEIGHT": .8, "OUTPUT_LINEFIT_WINDOW": 2,
                 "VOXEL_SCALE_UM": SCALE}
    exec(compile(body, "<actual-notebook-linefit-function>", "exec"), namespace)
    return namespace["linefit_smooth_output_graph"], namespace


def run(text, nodes, edges, overrides=None):
    function, namespace = compile_function(text)
    namespace.update(overrides or {})
    before = copy.deepcopy(nodes)
    work = copy.deepcopy(nodes)
    edge_work = copy.deepcopy(edges)
    edge_before = copy.deepcopy(edge_work)
    stats = {"linefit_skipped_nodes": 0, "linefit_smoothed_nodes": 0}
    actual = function(work, edge_work, stats)
    assert actual is work, "Function changed object-return contract"
    assert edge_work == edge_before, "Edges or edge attributes changed"
    assert set(actual) == set(before), "Node ids changed"
    for k in actual:
        assert {c: v for c, v in actual[k].items() if c not in ("z", "y", "x")} == {
            c: v for c, v in before[k].items() if c not in ("z", "y", "x")}, "Noncoordinate node field changed"
    return actual, stats


def main():
    build_receipt = build()
    baseline = json.loads((BASE / "candidate.ipynb").read_text())
    candidate = json.loads((HERE / "candidate.ipynb").read_text())
    old = source(baseline["cells"][5])
    new = source(candidate["cells"][5])
    pure, _ = patch_cell(old, observations=False)
    cases = []

    def check(name, callback):
        started = time.perf_counter()
        try:
            detail = callback() or {}
            cases.append({"name": name, "status": "PASS", "detail": detail,
                          "seconds": time.perf_counter() - started})
        except Exception as exc:
            cases.append({"name": name, "status": "FAIL", "error": repr(exc),
                          "traceback": traceback.format_exc(),
                          "seconds": time.perf_counter() - started})

    def no_fork_equal(curved, size):
        nodes, edges = chain(curved, size)
        b, bs = run(old, nodes, edges)
        c, cs = run(new, nodes, edges)
        assert coordinate_bytes(b) == coordinate_bytes(c), "No-fork output not bitwise equal to B0"
        assert all(cs[k] == bs[k] for k in bs)
        assert all(cs[k] == 0 for k in DIAGNOSTIC_KEYS)
        return {"nodes": size, "coordinate_bytes_equal": True,
                "coordinate_sha256": digest(coordinate_bytes(c))}

    for curved in [False, True]:
        for size in [1, 2, 3, 9]:
            check(f"{'curved' if curved else 'straight'}_chain_{size}_bitwise_B0", lambda curved=curved, size=size: no_fork_equal(curved, size))

    def daughters_independent_of_parent():
        nodes, edges = fork()
        changed = copy.deepcopy(nodes)
        for k in [-2, -1, 0]:
            changed[k]["x"] += 71.0
            changed[k]["y"] -= 33.0
        a, stats = run(new, nodes, edges)
        b, _ = run(new, changed, edges)
        daughter_ids = sorted(k for k in nodes if k > 0)
        assert coordinate_bytes({k: a[k] for k in daughter_ids}) == coordinate_bytes({k: b[k] for k in daughter_ids})
        original_a, _ = run(old, nodes, edges)
        original_b, _ = run(old, changed, edges)
        assert coordinate_bytes({k: original_a[k] for k in daughter_ids}) != coordinate_bytes({k: original_b[k] for k in daughter_ids}), "Fixture must expose B0 cross-boundary influence"
        return {"daughter_nodes": len(daughter_ids), "candidate_invariant": True,
                "B0_fixture_sensitive": True, "actual_counters": stats}
    check("fork_daughters_ignore_parent_side_perturbation", daughters_independent_of_parent)

    def parents_independent_of_daughters():
        nodes, edges = fork()
        changed = copy.deepcopy(nodes)
        for k in changed:
            if k > 0:
                changed[k]["z"] += 123.0
                changed[k]["x"] -= 37.0
        a, _ = run(new, nodes, edges)
        b, _ = run(new, changed, edges)
        parent_ids = [-2, -1, 0]
        assert coordinate_bytes({k: a[k] for k in parent_ids}) == coordinate_bytes({k: b[k] for k in parent_ids})
        return {"candidate_parent_side_invariant": True, "forward_traversal_unchanged": True}
    check("fork_parent_side_ignores_daughter_perturbation", parents_independent_of_daughters)

    def observations_are_pure():
        nodes, edges = fork()
        a, sa = run(pure, nodes, edges)
        random_state = np.random.get_state()
        b, sb = run(new, nodes, edges)
        after_state = np.random.get_state()
        assert coordinate_bytes(a) == coordinate_bytes(b)
        assert all(sb[k] == sa[k] for k in sa)
        assert random_state[0] == after_state[0] and np.array_equal(random_state[1], after_state[1]) and random_state[2:] == after_state[2:]
        assert sb["linefit_boundary_nodes"] == 4
        assert sb["linefit_boundary_backward_stops"] == 4
        assert sb["linefit_boundary_smoothed_nodes"] == 4
        expected = [float(np.linalg.norm((np.array([b[k][c] for c in ("z", "y", "x")]) - np.array([nodes[k][c] for c in ("z", "y", "x")])) * np.asarray(SCALE))) for k in [11, 12, 21, 22]]
        assert abs(sb["linefit_boundary_shift_um_sum"] - sum(expected)) < 1e-12
        assert abs(sb["linefit_boundary_shift_um_max"] - max(expected)) < 1e-12
        return {"audited_vs_unaudited_coordinate_bytes_equal": True,
                "numpy_rng_unchanged": True, "counters": sb,
                "movement_scope": "candidate output versus original graph input"}
    check("observation_purity_and_physical_movement_counters", observations_are_pure)

    def polyfit_not_duplicated():
        nodes, edges = fork()
        real = np.polyfit
        counts = []
        try:
            for text in [pure, new]:
                current_count = [0]
                def counted(*args, **kwargs):
                    current_count[0] += 1
                    return real(*args, **kwargs)
                np.polyfit = counted
                run(text, nodes, edges)
                counts.append(current_count[0])
        finally:
            np.polyfit = real
        assert counts[0] == counts[1] and counts[0] > 0
        return {"algorithm_polyfit_calls": counts[0], "observed_polyfit_calls": counts[1], "extra_old_algorithm_runs": 0}
    check("no_duplicate_linefit_execution_for_diagnostics", polyfit_not_duplicated)

    def incomplete_fork():
        nodes = {0: node(0, 3, 4, 5), 1: node(1, 4, 6, 7), 2: node(1, 5, 7, 9)}
        edges = [{"source_id": 0, "target_id": 1}, {"source_id": 0, "target_id": 2}]
        actual, stats = run(new, nodes, edges)
        assert actual == nodes
        assert stats["linefit_boundary_nodes"] == 2
        assert stats["linefit_boundary_smoothed_nodes"] == 0
        assert stats["linefit_boundary_shift_um_sum"] == 0
        return {"blocked_nodes": 2, "smoothed_blocked_nodes": 0,
                "demonstrates_blocked_does_not_mean_changed": True}
    check("short_fork_neighborhood_records_no_invented_displacement", incomplete_fork)

    def nonconsecutive_edges():
        nodes, edges = chain(True, 7)
        nodes[90] = node(90, 900, 900, 900)
        extra = edges + [{"source_id": 2, "target_id": 90}, {"source_id": 1, "target_id": 999}, {"source_id": 5, "target_id": 2}]
        a, _ = run(new, nodes, edges)
        b, stats = run(new, nodes, extra)
        assert coordinate_bytes(a) == coordinate_bytes(b)
        assert stats["linefit_boundary_nodes"] == 0
        return {"nonconsecutive_backward_and_missing_endpoint_edges_ignored": True}
    check("nonconsecutive_edges_do_not_create_false_fork", nonconsecutive_edges)

    def disabled(overrides, no_edges=False):
        nodes, edges = fork()
        edges = [] if no_edges else edges
        b, _ = run(old, nodes, edges, overrides)
        c, stats = run(new, nodes, edges, overrides)
        assert b == c == nodes
        assert all(stats[k] == 0 for k in DIAGNOSTIC_KEYS)
        return {"input_unchanged": True}
    for label, overrides, no_edges in [
        ("flag", {"OUTPUT_LINEFIT_SMOOTH": False}, False),
        ("zero_weight", {"OUTPUT_LINEFIT_WEIGHT": 0.0}, False),
        ("negative_weight", {"OUTPUT_LINEFIT_WEIGHT": -1.0}, False),
        ("zero_window", {"OUTPUT_LINEFIT_WINDOW": 0}, False),
        ("no_edges", {}, True),
    ]:
        check(f"disabled_{label}", lambda overrides=overrides, no_edges=no_edges: disabled(overrides, no_edges))

    def identity():
        assert [i for i, (a, b) in enumerate(zip(baseline["cells"], candidate["cells"])) if a != b] == [5]
        assert build_receipt["all_other_cells_and_notebook_metadata_equal"]
        assert build_receipt["patch"]["only_function_changed"]
        assert sum(r["category"] == "algorithm" for r in build_receipt["patch"]["replacements"]) == 1
        assert new.count("_linefit_shift_um =") == 1
        return {"changed_cells": [5], "algorithm_replacement_count": 1,
                "observation_replacement_count": 4,
                "metadata_changed_keys": ["id", "title"],
                "original_13_cells_preserved": True}
    check("notebook_identity_and_single_algorithm_change", identity)

    payload = {
        "task_id": "LINEFIT_BOUNDARY_20260909",
        "status": "PASS" if all(r["status"] == "PASS" for r in cases) else "FAIL",
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "runtime": {"python": sys.version, "executable": sys.executable,
                    "platform": platform.platform(), "numpy": np.__version__},
        "scope": "CPU synthetic execution of real extracted notebook functions; no models, real graphs or Kaggle runs",
        "candidate_notebook_sha256": build_receipt["candidate_notebook_sha256"],
        "baseline_notebook_sha256": build_receipt["baseline_notebook_sha256"],
        "source_hashes": {p.name: digest(p.read_bytes()) for p in
                          [HERE / "build_candidate.py", HERE / "linefit_patch.py", Path(__file__), HERE / "candidate.ipynb"]},
        "tests": cases, "passed": sum(r["status"] == "PASS" for r in cases),
        "total": len(cases),
        "actual_model_inference": "NOT_RUN", "kaggle_writes": 0,
        "score_claim": "UNKNOWN; synthetic pass does not imply formal score gain",
    }
    (HERE / "tests.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
