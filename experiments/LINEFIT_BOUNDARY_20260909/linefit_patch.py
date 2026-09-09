"""Single authorized linefit change; optional observation-only counters.

This module does not import or execute the Kaggle notebook or model code.
"""
from __future__ import annotations

import ast
import hashlib


FUNCTION_NAME = "linefit_smooth_output_graph"
DIAGNOSTIC_KEYS = (
    "linefit_boundary_backward_stops",
    "linefit_boundary_nodes",
    "linefit_boundary_smoothed_nodes",
    "linefit_boundary_shift_um_sum",
    "linefit_boundary_shift_um_max",
)


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def function_span(source: str) -> tuple[int, int, str]:
    definitions = [node for node in ast.parse(source).body
                   if isinstance(node, ast.FunctionDef) and node.name == FUNCTION_NAME]
    if len(definitions) != 1:
        raise ValueError(f"Expected exactly one {FUNCTION_NAME} definition")
    node = definitions[0]
    lines = source.splitlines(keepends=True)
    start = sum(map(len, lines[:node.lineno - 1]))
    end = sum(map(len, lines[:node.end_lineno]))
    return start, end, source[start:end]


def patch_cell(source: str, *, observations: bool = True) -> tuple[str, dict]:
    start, end, original = function_span(source)
    function = original
    replacements = []

    def replace(label: str, old: str, new: str, category: str) -> None:
        nonlocal function
        count = function.count(old)
        if count != 1:
            raise ValueError(f"{label}: expected one anchor, found {count}")
        function = function.replace(old, new, 1)
        replacements.append({"label": label, "category": category,
                             "matches": count, "before_sha256": sha256(old),
                             "after_sha256": sha256(new)})

    replace(
        "stop_backward_traversal_before_fork_parent",
        "            current = prev_ids[0]\n"
        "            if current not in original_pos:\n",
        "            prev_id = prev_ids[0]\n"
        "            if len(successor.get(prev_id, [])) != 1:\n"
        "                break\n"
        "            current = prev_id\n"
        "            if current not in original_pos:\n",
        "algorithm",
    )
    algorithm_function = function

    if observations:
        replace(
            "initialize_observation_counters",
            '    """Smooth linear track interiors without changing graph topology."""\n',
            '    """Smooth linear track interiors without changing graph topology."""\n'
            '    stats["linefit_boundary_backward_stops"] = 0\n'
            '    stats["linefit_boundary_nodes"] = 0\n'
            '    stats["linefit_boundary_smoothed_nodes"] = 0\n'
            '    stats["linefit_boundary_shift_um_sum"] = 0.0\n'
            '    stats["linefit_boundary_shift_um_max"] = 0.0\n',
            "observation_only",
        )
        replace(
            "initialize_per_node_boundary_flag",
            "        neighbourhood: list[tuple[int, int]] = [(0, node_id)]\n",
            "        neighbourhood: list[tuple[int, int]] = [(0, node_id)]\n"
            "        _linefit_boundary_stopped = False\n",
            "observation_only",
        )
        replace(
            "count_boundary_stop_once_per_node",
            "            if len(successor.get(prev_id, [])) != 1:\n"
            "                break\n",
            "            if len(successor.get(prev_id, [])) != 1:\n"
            '                stats["linefit_boundary_backward_stops"] += 1\n'
            '                stats["linefit_boundary_nodes"] += 1\n'
            "                _linefit_boundary_stopped = True\n"
            "                break\n",
            "observation_only",
        )
        replace(
            "measure_actual_candidate_movement_of_boundary_nodes",
            "        updated_pos[node_id] = (1.0 - weight) * original_pos[node_id] + weight * fitted\n",
            "        updated_pos[node_id] = (1.0 - weight) * original_pos[node_id] + weight * fitted\n"
            "        if _linefit_boundary_stopped:\n"
            '            stats["linefit_boundary_smoothed_nodes"] += 1\n'
            "            _linefit_shift_um = float(np.linalg.norm(\n"
            "                (updated_pos[node_id] - original_pos[node_id])\n"
            "                * np.asarray(VOXEL_SCALE_UM, dtype=np.float64)\n"
            "            ))\n"
            '            stats["linefit_boundary_shift_um_sum"] += _linefit_shift_um\n'
            '            stats["linefit_boundary_shift_um_max"] = max(\n'
            '                stats["linefit_boundary_shift_um_max"], _linefit_shift_um\n'
            "            )\n",
            "observation_only",
        )

    patched = source[:start] + function + source[end:]
    ast.parse(patched)
    return patched, {
        "function": FUNCTION_NAME,
        "only_function_changed": patched[:start] == source[:start]
        and patched[start + len(function):] == source[end:],
        "original_function_sha256": sha256(original),
        "algorithm_function_sha256": sha256(algorithm_function),
        "candidate_function_sha256": sha256(function),
        "replacements": replacements,
        "diagnostic_keys": list(DIAGNOSTIC_KEYS) if observations else [],
        "movement_scope": "candidate output minus input position, physical micrometers; not a B0 prediction difference",
        "boundary_nodes_scope": "nodes whose backward neighborhood hits a fork; not necessarily nodes with changed final coordinates",
        "baseline_algorithm_rerun_inside_candidate": False,
    }
