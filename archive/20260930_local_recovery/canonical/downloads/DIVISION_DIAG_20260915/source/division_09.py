






from scipy.optimize import linear_sum_assignment


def match_nodes_bipartite(pred_nodes: dict, gt_nodes: dict, max_dist: float = 7.0):
    pred_by_t: dict[int, list[int]] = {}
    for pid, (t, *_r) in pred_nodes.items():
        pred_by_t.setdefault(int(t), []).append(pid)
    gt_by_t: dict[int, list[int]] = {}
    for gid, (t, *_r) in gt_nodes.items():
        gt_by_t.setdefault(int(t), []).append(gid)

    pred_to_gt: dict[int, int] = {}
    gt_to_pred: dict[int, int] = {}
    for t, p_ids in pred_by_t.items():
        g_ids = gt_by_t.get(t, [])
        if not g_ids:
            continue
        voxel_scale = np.array(VOXEL_SCALE_UM, dtype=float)
        p_pos = np.array([pred_nodes[p][1:] for p in p_ids], dtype=float) * voxel_scale
        g_pos = np.array([gt_nodes[g][1:] for g in g_ids], dtype=float) * voxel_scale
        diff = p_pos[:, None, :] - g_pos[None, :, :]
        cost = np.sqrt((diff ** 2).sum(axis=-1))
        BIG = 1e6
        cost_gated = np.where(cost <= max_dist, cost, BIG)
        row_ind, col_ind = linear_sum_assignment(cost_gated)
        for r, c in zip(row_ind, col_ind):
            if cost_gated[r, c] >= BIG:
                continue
            pred_to_gt[p_ids[r]] = g_ids[c]
            gt_to_pred[g_ids[c]] = p_ids[r]
    return pred_to_gt, gt_to_pred


def compute_edge_confusion(pred_edges, gt_edges, pred_to_gt, gt_to_pred):
    gt_edge_set = set(gt_edges)
    gt_outgoing: dict[int, set[int]] = {}
    gt_incoming_source: dict[int, int] = {}
    for s, t in gt_edge_set:
        gt_outgoing.setdefault(s, set()).add(t)
        gt_incoming_source[t] = s

    tp = 0
    fp = 0
    matched_gt_edges = set()
    for s, t in pred_edges:
        ms = pred_to_gt.get(s)
        mt = pred_to_gt.get(t)
        is_tp = ms is not None and mt is not None and mt in gt_outgoing.get(ms, ())
        if is_tp:
            tp += 1
            matched_gt_edges.add((ms, mt))
            continue
        is_fp = (mt is not None and mt in gt_incoming_source) or (
            ms is not None and bool(gt_outgoing.get(ms))
        )
        if is_fp:
            fp += 1
    fn = len(gt_edge_set - matched_gt_edges)
    return tp, fp, fn


def edge_jaccard(tp: int, fp: int, fn: int) -> float:
    denom = tp + fp + fn
    return tp / denom if denom else 0.0


def adjusted_jaccard(jaccard: float, t_pred: int, t_true, a: float = 0.1) -> float:
    if not t_true or t_true <= 0:
        return jaccard
    return max(0.0, jaccard * (1.0 - a * (t_pred - t_true) / t_true))


def weakly_connected_components(node_ids, edges):
    parent = {n: n for n in node_ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for s, t in edges:
        if s in parent and t in parent:
            union(s, t)
    return {n: find(n) for n in node_ids}


def compute_division_confusion(pred_nodes, pred_edges, gt_nodes, gt_edges, pred_to_gt, gt_to_pred):
    gt_out: dict[int, set[int]] = {}
    gt_in: dict[int, int] = {}
    for s, t in gt_edges:
        gt_out.setdefault(s, set()).add(t)
        gt_in[t] = s

    pred_out: dict[int, set[int]] = {}
    for s, t in pred_edges:
        pred_out.setdefault(s, set()).add(t)

    pred_node_ids = list(pred_nodes.keys())
    pred_edge_list = list(pred_edges)
    components = weakly_connected_components(pred_node_ids, pred_edge_list)
    fork_components = {
        components[n] for n, outs in pred_out.items() if len(outs) >= 2 and n in components
    }
    gt_division_sources = [s for s, outs in gt_out.items() if len(outs) >= 2]

    def lineage_descendants(root_child: int) -> set[int]:
        seen = {root_child}
        stack = [root_child]
        while stack:
            cur = stack.pop()
            for nxt in gt_out.get(cur, ()):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        return seen

    tp = 0
    fn = 0
    tp_gt_sources: set[int] = set()

    for gsrc in gt_division_sources:
        children = sorted(gt_out[gsrc])
        if len(children) < 2:
            continue
        anchor_candidates = [gsrc]
        if gsrc in gt_in:
            anchor_candidates.append(gt_in[gsrc])
        anchor_pred_nodes = [gt_to_pred[a] for a in anchor_candidates if a in gt_to_pred]

        lineage_hit_components: list[set[int]] = []
        ok = True
        for child in children[:2]:
            lineage = lineage_descendants(child)
            hit_comp_ids = {
                components[p_id]
                for gt_id in lineage
                if (p_id := gt_to_pred.get(gt_id)) is not None and p_id in components
            }
            if not hit_comp_ids:
                ok = False
                break
            lineage_hit_components.append(hit_comp_ids)

        if not ok or not anchor_pred_nodes:
            fn += 1
            continue

        anchor_comp_ids = {components[p] for p in anchor_pred_nodes if p in components}
        if not anchor_comp_ids:
            fn += 1
            continue

        found = any(
            comp_id in lineage_hit_components[0]
            and comp_id in lineage_hit_components[1]
            and comp_id in fork_components
            for comp_id in anchor_comp_ids
        )
        if found:
            tp += 1
            tp_gt_sources.add(gsrc)
        else:
            fn += 1

    fp = 0
    for n, outs in pred_out.items():
        if len(outs) < 2:
            continue
        g = pred_to_gt.get(n)
        if g is None or g not in gt_out or g in tp_gt_sources:
            continue
        fp += 1

    return tp, fp, fn


def decompose_errors(pred_nodes, gt_nodes, pred_edges, gt_edges, pred_to_gt, gt_to_pred):
    """Splits error mass into detection vs. fragmentation vs. wrong-association,
    using the exact same pred_to_gt/gt_to_pred matching compute_edge_confusion
    uses. Division errors are already isolated by compute_division_confusion;
    this covers everything else -- the diagnostic breakdown for deciding
    whether further gains are in detection, linking, or fragmentation."""
    gt_edge_set = set(gt_edges)
    pred_edge_set = set(pred_edges)
    gt_outgoing: dict[int, set[int]] = {}
    for s, t in gt_edge_set:
        gt_outgoing.setdefault(s, set()).add(t)

    missed_gt_nodes = sum(1 for g in gt_nodes if g not in gt_to_pred)
    spurious_pred_nodes = sum(1 for p in pred_nodes if p not in pred_to_gt)

    recovered = fragmented = lost_to_detection = 0
    for gs, gtid in gt_edge_set:
        ps, pt = gt_to_pred.get(gs), gt_to_pred.get(gtid)
        if ps is None or pt is None:
            lost_to_detection += 1
        elif (ps, pt) in pred_edge_set:
            recovered += 1
        else:
            fragmented += 1

    wrong_association = 0
    for ps, pt in pred_edge_set:
        ms, mt = pred_to_gt.get(ps), pred_to_gt.get(pt)
        if ms is not None and mt is not None and mt not in gt_outgoing.get(ms, ()):
            wrong_association += 1

    return {
        "missed_gt_nodes": missed_gt_nodes,
        "spurious_pred_nodes": spurious_pred_nodes,
        "edges_recovered": recovered,
        "edges_fragmented": fragmented,
        "edges_lost_to_detection": lost_to_detection,
        "wrong_association_edges": wrong_association,
    }


def _find_key_recursive(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            found = _find_key_recursive(v, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _find_key_recursive(item, key)
            if found is not None:
                return found
    return None


def read_estimated_true_node_count(geff_path: Path):
    for candidate in (geff_path / "zarr.json", geff_path / ".zattrs"):
        if not candidate.exists():
            continue
        try:
            payload = json.loads(candidate.read_text())
        except Exception:
            continue
        found = _find_key_recursive(payload, "estimated_number_of_nodes")
        if found is not None:
            try:
                return float(found)
            except (TypeError, ValueError):
                continue
    return None


def graph_to_plain(graph):
    nodes: dict[int, tuple] = {}
    for row in graph.node_attrs().iter_rows(named=True):
        node_id = int(row["node_id"])
        nodes[node_id] = (int(row["t"]), float(row["z"]), float(row["y"]), float(row["x"]))
    edges: list[tuple[int, int]] = []
    for row in graph.edge_attrs().iter_rows(named=True):
        edges.append((int(row["source_id"]), int(row["target_id"])))
    return nodes, edges


def nodes_by_id_to_plain(nodes_by_id):
    return {nid: (int(n["t"]), float(n["z"]), float(n["y"]), float(n["x"])) for nid, n in nodes_by_id.items()}


def score_sample(pred_nodes_plain, pred_edges_plain, gt_nodes_plain, gt_edges_plain, t_true):
    p2g, g2p = match_nodes_bipartite(pred_nodes_plain, gt_nodes_plain, max_dist=VALIDATOR_MATCH_RADIUS_UM)
    tp, fp, fn = compute_edge_confusion(pred_edges_plain, gt_edges_plain, p2g, g2p)
    jac = edge_jaccard(tp, fp, fn)
    t_pred = len(pred_nodes_plain)
    adj = adjusted_jaccard(jac, t_pred, t_true, a=VALIDATOR_NODE_COUNT_PENALTY_A)
    div_tp, div_fp, div_fn = compute_division_confusion(
        pred_nodes_plain, pred_edges_plain, gt_nodes_plain, gt_edges_plain, p2g, g2p
    )
    errors = decompose_errors(pred_nodes_plain, gt_nodes_plain, pred_edges_plain, gt_edges_plain, p2g, g2p)
    div_jac = edge_jaccard(div_tp, div_fp, div_fn)
    row = {
        "edge_tp": tp, "edge_fp": fp, "edge_fn": fn, "edge_jaccard": jac,
        "t_pred": t_pred, "t_true": t_true, "adjusted_edge_jaccard": adj,
        "div_tp": div_tp, "div_fp": div_fp, "div_fn": div_fn, "div_jaccard": div_jac,
        "weight": tp + fp + fn,
    }
    row.update(errors)
    return row


def aggregate_official(sample_rows):
    total_w = sum(r["weight"] for r in sample_rows) or 1
    weighted_adj = sum(r["adjusted_edge_jaccard"] * r["weight"] for r in sample_rows) / total_w
    div_tp = sum(r["div_tp"] for r in sample_rows)
    div_fp = sum(r["div_fp"] for r in sample_rows)
    div_fn = sum(r["div_fn"] for r in sample_rows)
    div_jac = edge_jaccard(div_tp, div_fp, div_fn)
    return {
        "adjusted_edge_jaccard": weighted_adj,
        "division_jaccard": div_jac,
        "proxy_score": weighted_adj + VALIDATOR_DIVISION_WEIGHT * div_jac,
        "div_tp": div_tp, "div_fp": div_fp, "div_fn": div_fn,
        "missed_gt_nodes": sum(r["missed_gt_nodes"] for r in sample_rows),
        "spurious_pred_nodes": sum(r["spurious_pred_nodes"] for r in sample_rows),
        "edges_recovered": sum(r["edges_recovered"] for r in sample_rows),
        "edges_fragmented": sum(r["edges_fragmented"] for r in sample_rows),
        "edges_lost_to_detection": sum(r["edges_lost_to_detection"] for r in sample_rows),
        "wrong_association_edges": sum(r["wrong_association_edges"] for r in sample_rows),
    }

# TARGET950: evaluate the same held-out graphs with the fixed public scorer.
# This changes automatic PP selection only. It does not claim the private
# Kaggle deployment is byte-identical or that a higher local score is a gain.
import hashlib as _official_hashlib
import importlib.util as _official_importlib
import sys as _official_sys
_official_files = {'__init__.py': '', 'metrics.py': 'import warnings\nfrom typing import Literal, NamedTuple\n\nimport polars as pl\nimport tracksdata as td\n\n\nclass EvaluationResult(NamedTuple):\n    """Counts returned by :func:`evaluate`."""\n\n    edge_tp: int\n    edge_fp: int\n    edge_fn: int\n    division_tp: int\n    division_fp: int\n    division_fn: int\n    num_pred_nodes: int\n\n\nclass DatasetsResult(NamedTuple):\n    """Cumulative (micro-averaged) Jaccards plus the combined score."""\n\n    edge_jaccard: float\n    division_jaccard: float\n    score: float\n\n\n# Penalty coefficient for the adjusted edge Jaccard:\n#   J_adj = max(0, J · (1 - ADJUSTMENT_ALPHA · total_node_ratio))\nADJUSTMENT_ALPHA: float = 0.1\n\n# Weight of the division Jaccard in the combined run-level score:\n#   score = adj_edge_jaccard + SCORE_DIVISION_WEIGHT · division_jaccard\nSCORE_DIVISION_WEIGHT: float = 0.1\n\nCOUNT_COLUMNS: tuple[str, ...] = (\n    "edge_tp", "edge_fp", "edge_fn",\n    "division_tp", "division_fp", "division_fn",\n    "num_pred_nodes",\n)\nMETRIC_COLUMNS: tuple[str, ...] = COUNT_COLUMNS + (\n    "node_recall", "total_node_ratio", "edge_jaccard", "adj_edge_jaccard",\n)\n\n\ndef _jaccard(tp: int, fp: int, fn: int) -> float:\n    denom = tp + fp + fn\n    return tp / denom if denom > 0 else float("nan")\n\n\n# function is split for easier testing\ndef _evaluate_matched_graph(\n    graph: td.graph.BaseGraph,\n    gt_graph: td.graph.BaseGraph,\n) -> pl.DataFrame:\n    edge_attrs = graph.edge_attrs(attr_keys=[td.DEFAULT_ATTR_KEYS.MATCHED_EDGE_MASK])\n    # Guard against duplicate edges (same source→target pair appearing multiple times).\n    # tracksdata\'s match() inner-join marks all duplicates as matched, which inflates\n    # the intersection count and can push scores above 1.0. Sort matched rows first\n    # so the dedup keeps the matched copy when duplicates disagree on the mask.\n    edge_attrs = edge_attrs.sort(\n        td.DEFAULT_ATTR_KEYS.MATCHED_EDGE_MASK, descending=True,\n    ).unique(\n        subset=[td.DEFAULT_ATTR_KEYS.EDGE_SOURCE, td.DEFAULT_ATTR_KEYS.EDGE_TARGET],\n        keep="first",\n    )\n    node_attrs = graph.node_attrs(\n        attr_keys=[td.DEFAULT_ATTR_KEYS.NODE_ID, td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID, td.DEFAULT_ATTR_KEYS.T]\n    )\n\n    # Drop edges that do not connect consecutive frames, i.e. keep only edges where\n    # t_target == t_source + 1. This removes backward-in-time edges (t_target <= t_source)\n    # and any edge spanning more than a single time step (t_target - t_source > 1).\n    node_times = node_attrs.select(td.DEFAULT_ATTR_KEYS.NODE_ID, td.DEFAULT_ATTR_KEYS.T)\n    edge_attrs = edge_attrs.join(\n        node_times.rename({td.DEFAULT_ATTR_KEYS.T: "_source_t"}),\n        left_on=td.DEFAULT_ATTR_KEYS.EDGE_SOURCE,\n        right_on=td.DEFAULT_ATTR_KEYS.NODE_ID,\n        how="left",\n    ).join(\n        node_times.rename({td.DEFAULT_ATTR_KEYS.T: "_target_t"}),\n        left_on=td.DEFAULT_ATTR_KEYS.EDGE_TARGET,\n        right_on=td.DEFAULT_ATTR_KEYS.NODE_ID,\n        how="left",\n    ).filter(\n        pl.col("_target_t") - pl.col("_source_t") == 1\n    ).drop("_source_t", "_target_t")\n\n    # Collapse merges: when several predicted nodes match the same ground-truth\n    # node, multiple predicted edges can map onto the same ground-truth edge\n    # (identical matched source/target pair). tracksdata marks all of them as\n    # matched, inflating the intersection. Keep only the edge with the lowest\n    # EDGE_ID per matched GT edge and discard the rest with a warning.\n    matched_ids = node_attrs.select(\n        td.DEFAULT_ATTR_KEYS.NODE_ID, td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID\n    )\n    edge_attrs = edge_attrs.join(\n        matched_ids.rename({td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID: "_matched_source"}),\n        left_on=td.DEFAULT_ATTR_KEYS.EDGE_SOURCE,\n        right_on=td.DEFAULT_ATTR_KEYS.NODE_ID,\n        how="left",\n    ).join(\n        matched_ids.rename({td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID: "_matched_target"}),\n        left_on=td.DEFAULT_ATTR_KEYS.EDGE_TARGET,\n        right_on=td.DEFAULT_ATTR_KEYS.NODE_ID,\n        how="left",\n    )\n    # Only edges whose endpoints both match a GT node can collapse onto a GT edge.\n    both_matched = (\n        pl.col("_matched_source").is_not_null()\n        & pl.col("_matched_target").is_not_null()\n        & (pl.col("_matched_source") != -1)\n        & (pl.col("_matched_target") != -1)\n    )\n    edge_attrs = edge_attrs.with_columns(\n        (\n            both_matched\n            & (\n                pl.col(td.DEFAULT_ATTR_KEYS.EDGE_ID)\n                != pl.col(td.DEFAULT_ATTR_KEYS.EDGE_ID)\n                .min()\n                .over("_matched_source", "_matched_target")\n            )\n        ).alias("_is_merge_dup")\n    )\n    n_merge_dropped = int(edge_attrs["_is_merge_dup"].sum())\n    if n_merge_dropped > 0:\n        warnings.warn(\n            f"Dropped {n_merge_dropped} merged edge(s) mapping onto the same "\n            "ground-truth edge; kept the lowest edge id per merge.",\n            stacklevel=2,\n        )\n    edge_attrs = edge_attrs.filter(~pl.col("_is_merge_dup")).drop(\n        "_matched_source", "_matched_target", "_is_merge_dup"\n    )\n\n    # Cap out-degree: a dividing cell has at most two children, so a predicted node\n    # with more than two outgoing edges is biologically invalid. Keep the two edges\n    # with the lowest EDGE_ID per source and drop the rest with a warning.\n    edge_attrs = edge_attrs.with_columns(\n        pl.col(td.DEFAULT_ATTR_KEYS.EDGE_ID)\n        .rank("ordinal")\n        .over(td.DEFAULT_ATTR_KEYS.EDGE_SOURCE)\n        .alias("_out_rank")\n    )\n    n_outdeg_dropped = int((edge_attrs["_out_rank"] > 2).sum())\n    if n_outdeg_dropped > 0:\n        warnings.warn(\n            f"Dropped {n_outdeg_dropped} outgoing edge(s) from nodes with more than "\n            "two children; kept the two lowest edge ids per source.",\n            stacklevel=2,\n        )\n    edge_attrs = edge_attrs.filter(pl.col("_out_rank") <= 2).drop("_out_rank")\n\n    # I\'m assuming valid ground-truth edges are always 100% correct if they have an edge.\n    # Therefore, we don\'t have cases where the cell divided, but not in the ground truth.\n    gt_node_ids = gt_graph.node_ids()\n    gt_node_attrs = pl.DataFrame(\n        {\n            td.DEFAULT_ATTR_KEYS.NODE_ID: gt_node_ids,\n            "out_degree": gt_graph.out_degree(gt_node_ids),\n            "in_degree": gt_graph.in_degree(gt_node_ids),\n        }\n    ).with_columns(\n        (pl.col("out_degree") > 0).alias("out_valid"),\n        (pl.col("in_degree") > 0).alias("in_valid"),\n    )\n\n    # merging ground truth graph into the predicted graph\n    node_attrs = node_attrs.join(\n        gt_node_attrs,\n        left_on=td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID,\n        right_on=td.DEFAULT_ATTR_KEYS.NODE_ID,\n        how="left",\n    ).with_columns(\n        pl.col("out_valid").fill_null(False),\n        pl.col("in_valid").fill_null(False),\n    )\n\n    # merge out valid into source and in valid into target\n    edge_attrs = edge_attrs.join(\n        node_attrs.select(td.DEFAULT_ATTR_KEYS.NODE_ID, "out_valid"),\n        left_on=td.DEFAULT_ATTR_KEYS.EDGE_SOURCE,\n        right_on=td.DEFAULT_ATTR_KEYS.NODE_ID,\n        how="left",\n    ).join(\n        node_attrs.select(td.DEFAULT_ATTR_KEYS.NODE_ID, "in_valid"),\n        left_on=td.DEFAULT_ATTR_KEYS.EDGE_TARGET,\n        right_on=td.DEFAULT_ATTR_KEYS.NODE_ID,\n        how="left",\n    )\n\n    edge_attrs = edge_attrs.with_columns(\n        (pl.col("out_valid") | pl.col("in_valid")).alias("pred_valid"),\n    )\n\n    # sanity check that `pred_valid` is a superset of all matched edges\n    assert edge_attrs.filter(td.DEFAULT_ATTR_KEYS.MATCHED_EDGE_MASK)["pred_valid"].all()\n\n    return edge_attrs\n\n\ndef _compute_score(\n    edge_attrs: pl.DataFrame,\n    gt_num_edges: int,\n    metric: Literal["jaccard", "dice"],\n) -> float:\n    intersection = int(edge_attrs[td.DEFAULT_ATTR_KEYS.MATCHED_EDGE_MASK].sum())\n    n_valid_pred_edges = int(edge_attrs["pred_valid"].sum())\n\n    if metric == "jaccard":\n        num = intersection\n        denom = gt_num_edges + n_valid_pred_edges - intersection\n    elif metric == "dice":\n        num = 2 * intersection\n        denom = gt_num_edges + n_valid_pred_edges\n    else:\n        raise ValueError(f"Invalid metric: {metric}")\n\n    return num / denom if denom > 0 else float("nan")\n\n\ndef _evaluate(\n    graph: td.graph.BaseGraph,\n    gt_graph: td.graph.BaseGraph,\n    metric: Literal["jaccard", "dice"],\n    scale: tuple[float, ...] | None,\n    max_distance: float,\n) -> float:\n    if td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID in graph.node_attr_keys():\n        warnings.warn("Graph already matched, overwriting previous matching.")\n        # Reset matching attributes to defaults before re-matching\n        all_node_ids = graph.node_ids()\n        graph.update_node_attrs(\n            node_ids=all_node_ids,\n            attrs={\n                td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID: -1,\n                td.DEFAULT_ATTR_KEYS.MATCH_SCORE: 0.0,\n            },\n        )\n        all_edge_ids = graph.edge_ids()\n        if len(all_edge_ids) > 0:\n            graph.update_edge_attrs(\n                edge_ids=all_edge_ids,\n                attrs={td.DEFAULT_ATTR_KEYS.MATCHED_EDGE_MASK: False},\n            )\n\n    from tracksdata.metrics import DistanceMatching\n    matching = DistanceMatching(max_distance=max_distance, scale=scale)\n\n    if graph.num_edges() == 0 or graph.num_nodes() == 0:\n        warnings.warn("Predicted graph has no edges or no nodes, returning score 0.0.")\n        return 0.0\n\n    from tracksdata.options import get_options, set_options\n\n    prev_show_progress = get_options().show_progress\n    set_options(show_progress=False)\n    try:\n        with warnings.catch_warnings():\n            from scipy.sparse import SparseEfficiencyWarning\n            warnings.filterwarnings("ignore", category=SparseEfficiencyWarning)\n            graph.match(gt_graph, matching=matching)\n    finally:\n        set_options(show_progress=prev_show_progress)\n\n    edge_attrs = _evaluate_matched_graph(graph, gt_graph)\n\n    return _compute_score(edge_attrs, gt_graph.num_edges(), metric)\n\n\ndef evaluate(\n    graph: td.graph.BaseGraph,\n    gt_graph: td.graph.BaseGraph,\n    scale: tuple[float, ...] | None = None,\n    max_distance: float = 7.0,\n) -> EvaluationResult:\n    """\n    Evaluate a predicted graph against a ground-truth graph using\n    centroid-distance node matching.\n\n    Computes edge TP/FP/FN, division TP/FP/FN (via\n    :func:`tracking_cellmot.division_metrics.evaluate_divisions`), and the\n    total number of predicted nodes (irrespective of matching).\n\n    Parameters\n    ----------\n    graph : tracksdata.graph.BaseGraph\n        The predicted graph. Matching attributes are written onto *graph*\n        as a side effect.\n    gt_graph : tracksdata.graph.BaseGraph\n        The ground truth graph.\n    scale : tuple[float, ...] | None, optional\n        Physical scale for each spatial dimension (e.g., (z, y, x)) to\n        account for anisotropy. If None, assumes isotropic data.\n    max_distance : float, optional\n        Maximum distance between centroids to be considered as a match.\n\n    Returns\n    -------\n    EvaluationResult\n    """\n    from .division_metrics import evaluate_divisions\n\n    # Match graph against gt_graph (in place); discard the returned score.\n    _evaluate(graph, gt_graph, "jaccard", scale, max_distance)\n\n    if graph.num_edges() == 0:\n        edge_tp = 0\n        edge_fp = 0\n        edge_fn = gt_graph.num_edges()\n    else:\n        edge_attrs = _evaluate_matched_graph(graph, gt_graph)\n        edge_tp = int(edge_attrs[td.DEFAULT_ATTR_KEYS.MATCHED_EDGE_MASK].sum())\n        edge_valid_pred = int(edge_attrs["pred_valid"].sum())\n        edge_fp = edge_valid_pred - edge_tp\n        edge_fn = gt_graph.num_edges() - edge_tp\n\n    div = evaluate_divisions(\n        graph, gt_graph, scale=scale, max_distance=max_distance,\n    )\n\n    return EvaluationResult(\n        edge_tp=edge_tp,\n        edge_fp=edge_fp,\n        edge_fn=edge_fn,\n        division_tp=div.tp,\n        division_fp=div.fp,\n        division_fn=div.fn,\n        num_pred_nodes=graph.num_nodes(),\n    )\n\n\ndef evaluate_datasets(\n    graph_pairs: list[tuple[td.graph.BaseGraph, td.graph.BaseGraph]],\n    scale: tuple[float, ...] | None = None,\n    max_distance: float = 7.0,\n) -> DatasetsResult:\n    """Run :func:`evaluate` on each (pred, gt) pair and return cumulative\n    (micro-averaged) edge and division Jaccard.\n\n    Per-pair TP/FP/FN counts are summed across the whole list before the\n    Jaccard is computed, so larger datasets dominate the score naturally.\n\n    Parameters\n    ----------\n    graph_pairs : list of (pred_graph, gt_graph)\n        Predicted / ground-truth graph pairs. Each *pred_graph* is mutated\n        in place by matching (same side effect as :func:`evaluate`).\n    scale : tuple[float, ...] | None, optional\n        Physical voxel scale used for centroid-distance matching.\n    max_distance : float, optional\n        Maximum centroid distance for a match.\n\n    Returns\n    -------\n    DatasetsResult\n        Named tuple with ``edge_jaccard``, ``division_jaccard``, and the\n        combined ``score = edge_jaccard + SCORE_DIVISION_WEIGHT *\n        division_jaccard``. If no divisions exist anywhere in the input\n        the division term is dropped and ``score = edge_jaccard``.\n    """\n    edge_tp = edge_fp = edge_fn = 0\n    div_tp = div_fp = div_fn = 0\n    for pred, gt in graph_pairs:\n        r = evaluate(pred, gt, scale=scale, max_distance=max_distance)\n        edge_tp += r.edge_tp\n        edge_fp += r.edge_fp\n        edge_fn += r.edge_fn\n        div_tp += r.division_tp\n        div_fp += r.division_fp\n        div_fn += r.division_fn\n\n    edge_jaccard = _jaccard(edge_tp, edge_fp, edge_fn)\n    has_divisions = (div_tp + div_fp + div_fn) > 0\n    division_jaccard = _jaccard(div_tp, div_fp, div_fn) if has_divisions else float("nan")\n    score = edge_jaccard + SCORE_DIVISION_WEIGHT * division_jaccard if has_divisions else edge_jaccard\n\n    return DatasetsResult(\n        edge_jaccard=edge_jaccard,\n        division_jaccard=division_jaccard,\n        score=score,\n    )\n\n\ndef _matched_node_ids(graph: td.graph.BaseGraph) -> pl.DataFrame:\n    """Return a DataFrame with NODE_ID and MATCHED_NODE_ID (as Int64) for *graph*."""\n    node_attrs = graph.node_attrs(\n        attr_keys=[td.DEFAULT_ATTR_KEYS.NODE_ID, td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID]\n    )\n    return node_attrs\n\n\ndef node_recall(\n    graph: td.graph.BaseGraph,\n    gt_graph: td.graph.BaseGraph,\n) -> float:\n    """Fraction of GT nodes that were matched by a predicted node.\n\n    The predicted graph must already be matched (e.g. via :func:`evaluate` or\n    ``graph.match``).\n    """\n    node_attrs = _matched_node_ids(graph)\n    matched = node_attrs.filter(\n        pl.col(td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID).is_not_null()\n        & (pl.col(td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID) != -1)\n    )\n    n_matched_gt = matched[td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID].n_unique()\n    return n_matched_gt / gt_graph.num_nodes()\n\n\ndef per_sample_metrics(\n    er: EvaluationResult,\n    n_total: float,\n    node_recall: float,\n) -> dict:\n    """Derive per-sample metric columns from an :class:`EvaluationResult`.\n\n    Computes ``edge_jaccard``, ``total_node_ratio`` (``(N_pred − N_total) / N_total``),\n    and the adjusted edge Jaccard ``J_adj = max(0, J · (1 − α · total_node_ratio))``\n    with α = :data:`ADJUSTMENT_ALPHA`.\n\n    Parameters\n    ----------\n    er\n        Counts for one (pred, gt) pair — see :func:`evaluate`.\n    n_total\n        Target node count (e.g. from the GEFF ``estimated_number_of_nodes``\n        metadata extra). Pass ``float("nan")`` when unavailable; that makes\n        ``total_node_ratio`` and ``adj_edge_jaccard`` also NaN.\n    node_recall\n        Fraction of GT nodes matched by a predicted node.\n\n    Returns\n    -------\n    dict\n        One entry per key in :data:`METRIC_COLUMNS`.\n    """\n    if n_total > 0:\n        total_node_ratio = (er.num_pred_nodes - n_total) / n_total\n    else:\n        total_node_ratio = float("nan")\n\n    edge_denom = er.edge_tp + er.edge_fp + er.edge_fn\n    edge_jaccard = er.edge_tp / edge_denom if edge_denom > 0 else float("nan")\n    if edge_jaccard == edge_jaccard and total_node_ratio == total_node_ratio:\n        adj_edge_jaccard = max(\n            0.0, edge_jaccard * (1 - ADJUSTMENT_ALPHA * total_node_ratio),\n        )\n    else:\n        adj_edge_jaccard = float("nan")\n\n    return {\n        "edge_tp": er.edge_tp, "edge_fp": er.edge_fp, "edge_fn": er.edge_fn,\n        "division_tp": er.division_tp,\n        "division_fp": er.division_fp,\n        "division_fn": er.division_fn,\n        "num_pred_nodes": er.num_pred_nodes,\n        "node_recall": node_recall,\n        "total_node_ratio": total_node_ratio,\n        "edge_jaccard": edge_jaccard,\n        "adj_edge_jaccard": adj_edge_jaccard,\n    }\n\n\ndef nan_metrics_row() -> dict:\n    """Return a dict with every :data:`METRIC_COLUMNS` key set to NaN."""\n    return {col: float("nan") for col in METRIC_COLUMNS}\n\n\ndef summarise(rows: list[dict]) -> dict:\n    """Aggregate per-sample metric rows into a run-level summary.\n\n    - ``edge_jaccard`` / ``division_jaccard``: micro-averaged across valid rows\n      (TP/FP/FN summed, then Jaccard).\n    - ``adj_edge_jaccard``: per-sample adjusted Jaccard weight-averaged by\n      sample size ``w_i = TP_i + FP_i + FN_i``; rows with NaN are skipped.\n    - ``score``: ``adj_edge_jaccard + SCORE_DIVISION_WEIGHT · division_jaccard``.\n\n    Parameters\n    ----------\n    rows\n        Per-sample dicts as produced by :func:`per_sample_metrics`. Rows with\n        NaN ``edge_tp`` are treated as failed evaluations and skipped.\n    """\n    valid = [r for r in rows if r["edge_tp"] == r["edge_tp"]]\n    if not valid:\n        return {\n            "n": 0, "edge_jaccard": float("nan"),\n            "division_jaccard": float("nan"),\n            "division_tp": 0, "division_fp": 0, "division_fn": 0,\n            "node_recall": float("nan"),\n            "adj_edge_jaccard": float("nan"), "n_adj": 0,\n            "score": float("nan"),\n        }\n    totals = {c: sum(r[c] for r in valid) for c in COUNT_COLUMNS}\n\n    adj_rows = [r for r in valid if r["adj_edge_jaccard"] == r["adj_edge_jaccard"]]\n    weights = [r["edge_tp"] + r["edge_fp"] + r["edge_fn"] for r in adj_rows]\n    total_w = sum(weights)\n    if total_w > 0:\n        adj_edge_jaccard = sum(\n            w * r["adj_edge_jaccard"] for w, r in zip(weights, adj_rows)\n        ) / total_w\n    else:\n        adj_edge_jaccard = float("nan")\n\n    division_total = (\n        totals["division_tp"] + totals["division_fp"] + totals["division_fn"]\n    )\n    if division_total == 0:\n        warnings.warn(\n            "No divisions present across any sample in this split; "\n            "dropping division term from the combined score."\n        )\n        division_jaccard = float("nan")\n        score = adj_edge_jaccard\n    else:\n        division_jaccard = _jaccard(\n            totals["division_tp"], totals["division_fp"], totals["division_fn"],\n        )\n        score = adj_edge_jaccard + SCORE_DIVISION_WEIGHT * division_jaccard\n    return {\n        "n": len(valid),\n        "edge_jaccard": _jaccard(\n            totals["edge_tp"], totals["edge_fp"], totals["edge_fn"],\n        ),\n        "division_jaccard": division_jaccard,\n        "division_tp": totals["division_tp"],\n        "division_fp": totals["division_fp"],\n        "division_fn": totals["division_fn"],\n        "node_recall": sum(r["node_recall"] for r in valid) / len(valid),\n        "adj_edge_jaccard": adj_edge_jaccard,\n        "n_adj": len(adj_rows),\n        "score": score,\n    }\n', 'division_metrics.py': 'import warnings\nfrom typing import NamedTuple\n\nimport polars as pl\nimport tracksdata as td\n\n\nclass DivisionCounts(NamedTuple):\n    """Counts for division event evaluation."""\n\n    tp: int\n    fn: int\n    fp: int\n\n\nclass DivisionScores(NamedTuple):\n    """Result of :func:`score_divisions`.\n\n    Attributes\n    ----------\n    scores : dict[int, int]\n        Mapping from GT dividing-node ID to 1 (recovered) or 0 (not).\n    tp_forks : set[int]\n        Predicted dividing nodes paired to GT divisions.\n    fp_forks : set[int]\n        Predicted dividing nodes that were considered for a GT division\n        but did not become a true positive, including local-topology\n        rejects, bipartite leftovers, evaluable spurious forks, malformed\n        local branches, and forks whose branch evidence spans distinct GT\n        components.\n    """\n\n    scores: dict[int, int]\n    tp_forks: set[int]\n    fp_forks: set[int]\n\n\ndef _reset_matching_attrs(graph: td.graph.BaseGraph) -> None:\n    """Reset any pre-existing match attrs in place so a fresh ``.match()`` isn\'t\n    contaminated by stale values carried in from a previous matching pass."""\n    node_keys = graph.node_attr_keys()\n    if td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID in node_keys:\n        node_ids = graph.node_ids()\n        if len(node_ids) > 0:\n            reset: dict = {td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID: -1}\n            if td.DEFAULT_ATTR_KEYS.MATCH_SCORE in node_keys:\n                reset[td.DEFAULT_ATTR_KEYS.MATCH_SCORE] = 0.0\n            graph.update_node_attrs(node_ids=node_ids, attrs=reset)\n    if td.DEFAULT_ATTR_KEYS.MATCHED_EDGE_MASK in graph.edge_attr_keys():\n        edge_ids = graph.edge_ids()\n        if len(edge_ids) > 0:\n            graph.update_edge_attrs(\n                edge_ids=edge_ids,\n                attrs={td.DEFAULT_ATTR_KEYS.MATCHED_EDGE_MASK: False},\n            )\n\n\ndef extract_divisions(\n    graph: td.graph.BaseGraph,\n) -> dict[int, td.graph.BaseGraph]:\n    """Extract individual division events as separate subgraphs.\n\n    Each division event includes the parent of the dividing node, the\n    dividing node, its children, and the grandchildren::\n\n        parent → divider → child1 → grandchild1\n                         → child2 → grandchild2\n\n    Parameters\n    ----------\n    graph : td.graph.BaseGraph\n        The input tracking graph.\n\n    Returns\n    -------\n    dict[int, td.graph.BaseGraph]\n        Mapping from dividing node ID to a subgraph containing the\n        parent, divider, children, and grandchildren.\n    """\n    divisions: dict[int, td.graph.BaseGraph] = {}\n    for div_node in graph.dividing_nodes():\n        parents = graph.predecessors(div_node)\n        children = graph.successors(div_node)\n        grandchildren = [gc for child in children for gc in graph.successors(child)]\n        keep = [*parents, div_node, *children, *grandchildren]\n        divisions[div_node] = graph.filter(node_ids=keep).subgraph()\n    return divisions\n\n\ndef match_divisions(\n    pred_graph: td.graph.BaseGraph,\n    gt_graph: td.graph.BaseGraph,\n    scale: tuple[float, ...] | None = None,\n    max_distance: float = 7.0,\n) -> dict[int, td.graph.BaseGraph]:\n    """Match the predicted graph against each GT division subgraph.\n\n    Extracts division events from *gt_graph* via :func:`extract_divisions`,\n    then runs ``pred_graph.match(gt_div, ...)`` for each one independently.\n    A fresh copy of *pred_graph* is used per division so matchings don\'t\n    interfere.\n\n    Parameters\n    ----------\n    pred_graph : td.graph.BaseGraph\n        The predicted tracking graph.\n    gt_graph : td.graph.BaseGraph\n        The ground-truth tracking graph.\n    scale : tuple[float, ...] | None\n        Physical voxel scale used for centroid-distance matching.\n    max_distance : float\n        Maximum centroid distance for a match.\n\n    Returns\n    -------\n    dict[int, td.graph.BaseGraph]\n        Mapping from GT dividing-node ID to the matched copy of\n        *pred_graph* for that division.\n    """\n    from tracksdata.metrics import DistanceMatching\n\n    matching = DistanceMatching(max_distance=max_distance, scale=scale)\n\n    gt_divisions = extract_divisions(gt_graph)\n    matched: dict[int, td.graph.BaseGraph] = {}\n\n    from tracksdata.options import get_options, set_options\n\n    prev_show_progress = get_options().show_progress\n    set_options(show_progress=False)\n    try:\n        for div_node, gt_div in gt_divisions.items():\n            pred_copy = pred_graph.copy()\n            _reset_matching_attrs(pred_copy)\n            with warnings.catch_warnings():\n                from scipy.sparse import SparseEfficiencyWarning\n\n                warnings.filterwarnings("ignore", category=SparseEfficiencyWarning)\n                pred_copy.match(gt_div, matching=matching)\n            matched[div_node] = pred_copy\n    finally:\n        set_options(show_progress=prev_show_progress)\n\n    return matched\n\n\ndef _match_full(\n    pred_graph: td.graph.BaseGraph,\n    gt_graph: td.graph.BaseGraph,\n    scale: tuple[float, ...] | None,\n    max_distance: float,\n) -> td.graph.BaseGraph:\n    """Match the full pred graph against the full GT graph, return the matched copy."""\n    from tracksdata.metrics import DistanceMatching\n\n    matching = DistanceMatching(max_distance=max_distance, scale=scale)\n\n    pred_copy = pred_graph.copy()\n    _reset_matching_attrs(pred_copy)\n\n    from tracksdata.options import get_options, set_options\n\n    prev_show_progress = get_options().show_progress\n    set_options(show_progress=False)\n    try:\n        with warnings.catch_warnings():\n            from scipy.sparse import SparseEfficiencyWarning\n\n            warnings.filterwarnings("ignore", category=SparseEfficiencyWarning)\n            pred_copy.match(gt_graph, matching=matching)\n    finally:\n        set_options(show_progress=prev_show_progress)\n\n    return pred_copy\n\n\ndef _matched_node_attrs(graph: td.graph.BaseGraph) -> pl.DataFrame:\n    """Return pred/GT node-ID pairs for matched prediction nodes."""\n    node_attrs = graph.node_attrs(\n        attr_keys=[\n            td.DEFAULT_ATTR_KEYS.NODE_ID,\n            td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID,\n        ],\n    )\n    return node_attrs.filter(\n        pl.col(td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID).is_not_null()\n        & (pl.col(td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID) != -1)\n    )\n\n\ndef _matched_division_nodes(\n    matched_attrs: pl.DataFrame,\n    gt_div: td.graph.BaseGraph,\n    divider_id: int,\n) -> tuple[set[int], list[set[int]]] | None:\n    """Group matched pred nodes by their role in a GT division window.\n\n    The parent side contains the GT divider (the parent cell) and its\n    immediate predecessor (the grandparent). Each daughter side contains\n    one GT child and its immediate successors (the grandchildren).\n    """\n    if matched_attrs.is_empty():\n        return None\n\n    node_to_gt = dict(\n        zip(\n            matched_attrs[td.DEFAULT_ATTR_KEYS.NODE_ID].to_list(),\n            matched_attrs[td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID].to_list(),\n            strict=True,\n        )\n    )\n    gt_children = gt_div.successors(divider_id)\n    if len(gt_children) < 2:\n        return None\n\n    gt_parent_ids = {divider_id, *gt_div.predecessors(divider_id)}\n    parent_ids = {pred_id for pred_id, gt_id in node_to_gt.items() if gt_id in gt_parent_ids}\n    daughter_ids = [\n        {pred_id for pred_id, gt_id in node_to_gt.items() if gt_id in {child, *gt_div.successors(child)}}\n        for child in gt_children\n    ]\n    if not parent_ids or sum(bool(ids) for ids in daughter_ids) < 2:\n        return None\n    return parent_ids, daughter_ids\n\n\ndef _is_strongly_connected_division(\n    pred_graph: td.graph.BaseGraph,\n    pred_div: int,\n    parent_ids: set[int],\n    daughter_ids: list[set[int]],\n) -> bool:\n    """Check a predicted division\'s local directed topology.\n\n    The prediction window mirrors :func:`extract_divisions`: an immediate\n    predecessor (grandparent), *pred_div* (parent), its children, and their\n    children (grandchildren). The parent match must be the fork itself or\n    its immediate predecessor. Matches from at least two GT daughter\n    lineages must occur in two distinct predicted child lineages.\n\n    Parameters\n    ----------\n    pred_graph : td.graph.BaseGraph\n        The predicted tracking graph.\n    pred_div : int\n        Candidate predicted dividing node (the parent/fork).\n    parent_ids : set[int]\n        Prediction node IDs matched to the GT parent side (grandparent or\n        dividing parent).\n    daughter_ids : list[set[int]]\n        Prediction node IDs matched to each GT daughter lineage (child or\n        grandchild), grouped by lineage.\n\n    Returns\n    -------\n    bool\n        Whether the local prediction topology connects the parent side to\n        at least two distinct daughter lineages through *pred_div*.\n    """\n    pred_parent_ids = {pred_div, *pred_graph.predecessors(pred_div)}\n    if pred_parent_ids.isdisjoint(parent_ids):\n        return False\n\n    pred_lineages = [{child, *pred_graph.successors(child)} for child in pred_graph.successors(pred_div)]\n    lineage_edges = {\n        gt_lineage: {\n            pred_lineage for pred_lineage, pred_ids in enumerate(pred_lineages) if not matched_ids.isdisjoint(pred_ids)\n        }\n        for gt_lineage, matched_ids in enumerate(daughter_ids)\n    }\n    return len(_bipartite_max_matching(list(lineage_edges), lineage_edges)) >= 2\n\n\ndef _bipartite_max_matching(\n    left: list[int],\n    edges: dict[int, set[int]],\n) -> dict[int, int]:\n    """Maximum-cardinality bipartite matching via DFS augmenting paths.\n\n    *edges* maps each left-side vertex to the set of adjacent right-side\n    vertices. Returns only the matched pairs as a ``left → right`` dict.\n    """\n    match_r: dict[int, int] = {}\n    match_l: dict[int, int] = {}\n\n    def augment(u: int, seen: set[int]) -> bool:\n        for v in edges.get(u, ()):\n            if v in seen:\n                continue\n            seen.add(v)\n            if v not in match_r or augment(match_r[v], seen):\n                match_l[u] = v\n                match_r[v] = u\n                return True\n        return False\n\n    for u in left:\n        augment(u, set())\n\n    return match_l\n\n\ndef score_divisions(\n    pred_graph: td.graph.BaseGraph,\n    gt_graph: td.graph.BaseGraph,\n    scale: tuple[float, ...] | None = None,\n    max_distance: float = 7.0,\n) -> DivisionScores:\n    """Score each GT division: 1 if the prediction recovers it, 0 otherwise.\n\n    For each GT division, the predicted graph is matched against its\n    parent/divider/children/grandchildren window. Candidate pred forks are\n    restricted to the matched parent-side nodes and their immediate\n    successors. A candidate is valid only when its local topology contains\n    a matched parent and matches from two GT daughter lineages on distinct\n    predicted child branches. A fork is rejected when two direct-child\n    branches have nearest matched evidence in distinct reliable GT components.\n    An unmatched child may use unambiguous grandchild evidence as a fallback;\n    matched children take precedence over downstream matches.\n\n    A maximum-cardinality bipartite matching is then computed so each pred\n    fork serves at most one GT division, and each GT division is paired\n    with at most one pred fork. A GT division scores 1 only if paired;\n    rejected candidates and valid candidates left unpaired are returned as\n    false-positive forks.\n\n    Parameters\n    ----------\n    pred_graph : td.graph.BaseGraph\n        The predicted tracking graph.\n    gt_graph : td.graph.BaseGraph\n        The ground-truth tracking graph.\n    scale : tuple[float, ...] | None\n        Physical voxel scale used for centroid-distance matching.\n    max_distance : float\n        Maximum centroid distance for a match.\n\n    Returns\n    -------\n    DivisionScores\n        The per-division scores and the predicted forks classified as true\n        positives or false positives. False-positive forks include local\n        topology rejects, cross-GT-component branches, locally merged branches,\n        evaluable spurious forks, and valid candidates left unmatched by the\n        bipartite pairing.\n    """\n    matched = match_divisions(\n        pred_graph,\n        gt_graph,\n        scale,\n        max_distance,\n    )\n    gt_divisions = extract_divisions(gt_graph)\n    pred_div_nodes = {\n        node_id for node_id in pred_graph.node_ids()\n        if pred_graph.out_degree(node_id) >= 2\n    }\n    evaluable_forks, cross_component_forks, malformed_forks = (\n        _pred_division_fork_sets(pred_graph, gt_graph, scale, max_distance)\n    )\n    invalid_forks = cross_component_forks | malformed_forks\n\n    candidates: dict[int, set[int]] = {}\n    considered: set[int] = set()\n    for div_node, matched_pred in matched.items():\n        matched_nodes = _matched_division_nodes(_matched_node_attrs(matched_pred), gt_divisions[div_node], div_node)\n        if matched_nodes is None:\n            candidates[div_node] = set()\n            continue\n\n        parent_ids, daughter_ids = matched_nodes\n        local_nodes = parent_ids | {\n            successor for parent_id in parent_ids for successor in matched_pred.successors(parent_id)\n        }\n        local_forks = local_nodes & pred_div_nodes\n        considered |= local_forks\n        candidates[div_node] = {\n            pred_div\n            for pred_div in local_forks - invalid_forks\n            if _is_strongly_connected_division(matched_pred, pred_div, parent_ids, daughter_ids)\n        }\n\n    pairing = _bipartite_max_matching(list(candidates), candidates)\n    scores = {div: int(div in pairing) for div in candidates}\n    tp_forks = set(pairing.values())\n    # Use a set union so forks supported by multiple FP rules are counted once.\n    # Invalid forks were excluded from the pairing above and therefore cannot\n    # also be true positives.\n    fp_forks = (considered | evaluable_forks | invalid_forks) - tp_forks\n    return DivisionScores(scores=scores, tp_forks=tp_forks, fp_forks=fp_forks)\n\n\ndef _gt_weak_component_ids(graph: td.graph.BaseGraph) -> dict[int, int]:\n    """Map each GT node to its weakly connected component ID."""\n    component_ids: dict[int, int] = {}\n    for seed in graph.node_ids():\n        if seed in component_ids:\n            continue\n        component_ids[seed] = seed\n        stack = [seed]\n        while stack:\n            current = stack.pop()\n            for neighbor in graph.successors(current) + graph.predecessors(current):\n                if neighbor not in component_ids:\n                    component_ids[neighbor] = seed\n                    stack.append(neighbor)\n    return component_ids\n\n\ndef _branch_component_evidence(\n    graph: td.graph.BaseGraph,\n    pred_div: int,\n    child: int,\n    pred_to_gt: dict[int, int],\n    gt_component: dict[int, int],\n) -> tuple[int | None, bool]:\n    """Return one GT component for a predicted child branch.\n\n    Direct-child evidence takes precedence over grandchildren so downstream\n    errors do not invalidate a correctly matched division. Grandchildren are\n    fallback evidence only when the child is unmatched. The boolean marks a\n    locally merged branch that cannot be assigned uniquely to this fork.\n    """\n    if set(graph.predecessors(child)) != {pred_div}:\n        return None, True\n    if child in pred_to_gt:\n        return gt_component[pred_to_gt[child]], False\n\n    grandchildren = graph.successors(child)\n    if any(set(graph.predecessors(node)) != {child} for node in grandchildren):\n        return None, True\n\n    components = {\n        gt_component[pred_to_gt[node]]\n        for node in grandchildren\n        if node in pred_to_gt\n    }\n    if len(components) == 1:\n        return next(iter(components)), False\n    return None, False\n\n\ndef _pred_division_fork_sets(\n    pred_graph: td.graph.BaseGraph,\n    gt_graph: td.graph.BaseGraph,\n    scale: tuple[float, ...] | None,\n    max_distance: float,\n) -> tuple[set[int], set[int], set[int]]:\n    """Return evaluable, cross-component, and malformed predicted forks.\n\n    Cross-component evidence must come from distinct direct-child branches.\n    A matched child identifies its branch; otherwise an unambiguous matched\n    grandchild may identify it. Merged local branches are malformed.\n    """\n    matched_pred = _match_full(pred_graph, gt_graph, scale, max_distance)\n    matched_attrs = _matched_node_attrs(matched_pred)\n    pred_to_gt = dict(\n        zip(\n            matched_attrs[td.DEFAULT_ATTR_KEYS.NODE_ID].to_list(),\n            matched_attrs[td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID].to_list(),\n            strict=True,\n        )\n    )\n\n    pred_forks = {\n        node_id for node_id in matched_pred.node_ids()\n        if matched_pred.out_degree(node_id) >= 2\n    }\n    evaluable_forks = {\n        pred_id for pred_id in pred_forks\n        if pred_id in pred_to_gt and gt_graph.out_degree(pred_to_gt[pred_id]) >= 1\n    }\n\n    gt_component = _gt_weak_component_ids(gt_graph)\n    cross_component_forks: set[int] = set()\n    malformed_forks: set[int] = set()\n    for pred_id in pred_forks:\n        branch_evidence: list[int] = []\n        for child in matched_pred.successors(pred_id):\n            component, malformed = _branch_component_evidence(\n                matched_pred, pred_id, child, pred_to_gt, gt_component\n            )\n            if malformed:\n                malformed_forks.add(pred_id)\n                break\n            if component is not None:\n                branch_evidence.append(component)\n        else:\n            if len(set(branch_evidence)) >= 2:\n                cross_component_forks.add(pred_id)\n\n    return evaluable_forks, cross_component_forks, malformed_forks\n\n\ndef count_matched_pred_divisions(\n    pred_graph: td.graph.BaseGraph,\n    gt_graph: td.graph.BaseGraph,\n    scale: tuple[float, ...] | None = None,\n    max_distance: float = 7.0,\n) -> int:\n    """Count predicted division nodes whose matched GT node is annotated.\n\n    Matches the full predicted graph against the full GT graph.  Among\n    predicted nodes that were matched to a GT node, counts how many are\n    dividing (out-degree >= 2) in the prediction *and* whose matched GT\n    node has at least one child.  A matched GT node with no children marks\n    the end of the annotation — we can\'t tell whether the cell actually\n    divided there, so such predicted divisions are excluded from the count\n    (and therefore from the FP tally).\n\n    Parameters\n    ----------\n    pred_graph : td.graph.BaseGraph\n        The predicted tracking graph.\n    gt_graph : td.graph.BaseGraph\n        The ground-truth tracking graph.\n    scale : tuple[float, ...] | None\n        Physical voxel scale used for centroid-distance matching.\n    max_distance : float\n        Maximum centroid distance for a match.\n\n    Returns\n    -------\n    int\n        Number of matched predicted division nodes.\n    """\n    evaluable_forks, _, _ = _pred_division_fork_sets(\n        pred_graph, gt_graph, scale, max_distance\n    )\n    return len(evaluable_forks)\n\n\ndef evaluate_divisions(\n    pred_graph: td.graph.BaseGraph,\n    gt_graph: td.graph.BaseGraph,\n    scale: tuple[float, ...] | None = None,\n    max_distance: float = 7.0,\n) -> DivisionCounts:\n    """Compute TP, FN, and FP counts for division events.\n\n    - **TP**: GT divisions correctly recovered in the prediction\n      (matched nodes connected and forking).\n    - **FN**: GT divisions not recovered.\n    - **FP**: Spurious predicted divisions, including forks matched to an\n      annotated GT node, local-topology rejects, bipartite leftovers, and\n      forks whose distinct child branches have nearest matched evidence in\n      distinct GT components, and forks with locally merged branches. Fork IDs\n      are unioned, so a fork supported by multiple rules counts once.\n\n    Parameters\n    ----------\n    pred_graph : td.graph.BaseGraph\n        The predicted tracking graph.\n    gt_graph : td.graph.BaseGraph\n        The ground-truth tracking graph.\n    scale : tuple[float, ...] | None\n        Physical voxel scale used for centroid-distance matching.\n    max_distance : float\n        Maximum centroid distance for a match.\n\n    Returns\n    -------\n    DivisionCounts\n        Named tuple with ``tp``, ``fn``, and ``fp`` fields.\n    """\n    result = score_divisions(\n        pred_graph,\n        gt_graph,\n        scale,\n        max_distance,\n    )\n    tp = sum(result.scores.values())\n    fn = len(result.scores) - tp\n    return DivisionCounts(tp=tp, fn=fn, fp=len(result.fp_forks))\n', 'LICENSE': 'BSD 3-Clause License\n\nCopyright (c) 2026, Thibaut Goldsborough\n\nRedistribution and use in source and binary forms, with or without\nmodification, are permitted provided that the following conditions are met:\n\n1. Redistributions of source code must retain the above copyright notice, this\n   list of conditions and the following disclaimer.\n\n2. Redistributions in binary form must reproduce the above copyright notice,\n   this list of conditions and the following disclaimer in the documentation\n   and/or other materials provided with the distribution.\n\n3. Neither the name of the copyright holder nor the names of its\n   contributors may be used to endorse or promote products derived from\n   this software without specific prior written permission.\n\nTHIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"\nAND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE\nIMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE\nDISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE\nFOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL\nDAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR\nSERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER\nCAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,\nOR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE\nOF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.\n'}
_official_file_hashes = {'__init__.py': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'metrics.py': 'cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444', 'division_metrics.py': '0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9', 'LICENSE': '3910a8b578783928cbbf981c1b204591ab3368e70017dc695d6536f71d272796'}
_official_package_dir = WORKING_DIR / "official_scorer_075fc5"
_official_package_dir.mkdir(parents=True, exist_ok=True)
for _name, _contents in _official_files.items():
    _data = _contents.encode("utf-8")
    if _official_hashlib.sha256(_data).hexdigest() != _official_file_hashes[_name]:
        raise RuntimeError("OFFICIAL_SCORER_PAYLOAD_HASH_MISMATCH: " + _name)
    _target = _official_package_dir / _name
    _target.write_bytes(_data)
    if _official_hashlib.sha256(_target.read_bytes()).hexdigest() != _official_file_hashes[_name]:
        raise RuntimeError("OFFICIAL_SCORER_DISK_HASH_MISMATCH: " + _name)
_official_package_name = "biohub_official_075fc5"
_official_spec = _official_importlib.spec_from_file_location(
    _official_package_name, _official_package_dir / "__init__.py",
    submodule_search_locations=[str(_official_package_dir)],
)
_official_package = _official_importlib.module_from_spec(_official_spec)
_official_sys.modules[_official_package_name] = _official_package
_official_spec.loader.exec_module(_official_package)
_official_metrics_spec = _official_importlib.spec_from_file_location(
    _official_package_name + ".metrics", _official_package_dir / "metrics.py"
)
OFFICIAL_METRICS = _official_importlib.module_from_spec(_official_metrics_spec)
_official_sys.modules[_official_package_name + ".metrics"] = OFFICIAL_METRICS
_official_metrics_spec.loader.exec_module(OFFICIAL_METRICS)

"""Install the frozen official scoring chain after the existing cell 8.

The caller injects OFFICIAL_METRICS (the unmodified 075fc5 module), then calls
install_official_selector(globals()). No model, Notebook top level, data download
or external write is executed by this module. The old proxy remains diagnostic.
"""


def install_official_selector(scope):
    import hashlib
    import json
    import math
    import numbers
    import warnings

    import polars as pl
    import tracksdata as td

    metrics = scope["OFFICIAL_METRICS"]
    if "legacy_score_sample" in scope or "legacy_aggregate_official" in scope:
        raise RuntimeError("Official selector already installed; refusing double wrapping")
    legacy_score = scope["score_sample"]
    legacy_aggregate = scope["aggregate_official"]
    scale = tuple(float(x) for x in scope["VOXEL_SCALE_UM"])
    radius = float(scope["VALIDATOR_MATCH_RADIUS_UM"])
    if len(scale) != 3 or any(not math.isfinite(x) or x <= 0 for x in scale):
        raise ValueError("Official selector requires finite positive ZYX voxel scale")
    if not math.isfinite(radius) or radius <= 0:
        raise ValueError("Official selector requires a finite positive matching radius")
    if float(scope["VALIDATOR_NODE_COUNT_PENALTY_A"]) != metrics.ADJUSTMENT_ALPHA:
        raise ValueError("Node adjustment coefficient differs from frozen official source")
    if float(scope["VALIDATOR_DIVISION_WEIGHT"]) != metrics.SCORE_DIVISION_WEIGHT:
        raise ValueError("Division coefficient differs from frozen official source")
    provenance = "official_075fc5:evaluate->per_sample_metrics->summarise"
    legacy_provenance = "unchanged_forge947_cell8_proxy; independent_global_node_matching"
    error_fields = (
        "missed_gt_nodes", "spurious_pred_nodes", "edges_recovered",
        "edges_fragmented", "edges_lost_to_detection", "wrong_association_edges",
    )

    def input_graph_sha256(nodes, edges):
        # The lists retain input node insertion and edge order because matching
        # ties can depend on that order. Values are plain graph coordinates in
        # voxel units; physical scale and n_total are recorded separately.
        canonical = {
            "nodes": [[int(node_id), int(value[0]), *(float(v) for v in value[1:])]
                      for node_id, value in nodes.items()],
            "edges": [[int(source), int(target)] for source, target in edges],
        }
        data = json.dumps(canonical, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    def new_graph(nodes, edges):
        """Map arbitrary integral input IDs to fresh dense backend IDs in bulk.

        Preserve node insertion and edge order, duplicate edges, isolated nodes,
        and nonconsecutive edges: the official evaluator owns their treatment.
        The backend mutates edge dictionaries, so every dictionary is new.
        """
        graph = td.graph.InMemoryGraph()
        for key in ("z", "y", "x"):
            graph.add_node_attr_key(key, pl.Float64, 0.0)
        node_ids = list(nodes)
        attributes = []
        for node_id in node_ids:
            if isinstance(node_id, bool) or not isinstance(node_id, numbers.Integral):
                raise ValueError("Node IDs must be integers")
            position = nodes[node_id]
            if len(position) != 4:
                raise ValueError("Node values must be (integer_frame, z, y, x)")
            t, z, y, x = position
            if isinstance(t, bool) or not isinstance(t, numbers.Real):
                raise ValueError("Frame must be a numeric integer")
            if not math.isfinite(t) or int(t) != t or not 0 <= t < 2**31:
                raise ValueError("Frame must be a nonnegative Int32 integer")
            coords = tuple(float(v) for v in (z, y, x))
            if not all(math.isfinite(v) for v in coords):
                raise ValueError("Nonfinite spatial coordinate")
            attributes.append(dict(t=int(t), z=coords[0], y=coords[1], x=coords[2]))
        internal_ids = graph.bulk_add_nodes(attributes)
        remap = dict(zip(node_ids, internal_ids, strict=True))
        edge_attributes = []
        for source, target in edges:
            if source not in remap or target not in remap:
                raise ValueError("Dangling edge in scorer input")
            edge_attributes.append(dict(source_id=remap[source], target_id=remap[target]))
        graph.bulk_add_edges(edge_attributes)
        return graph

    def score_sample(pred_nodes_plain, pred_edges_plain, gt_nodes_plain, gt_edges_plain, t_true):
        if t_true is None or isinstance(t_true, bool):
            raise ValueError("Missing or invalid estimated_number_of_nodes; no proxy fallback")
        n_total = float(t_true)
        if not math.isfinite(n_total) or n_total <= 0:
            raise ValueError("estimated_number_of_nodes must be finite and positive")
        if not gt_nodes_plain:
            raise ValueError("Empty GT is unsupported by the frozen official matching chain")
        # Copies isolate official in-place matching from cached input and proxy.
        pred_edges = list(pred_edges_plain)
        gt_edges = list(gt_edges_plain)
        pred = new_graph(pred_nodes_plain, pred_edges)
        gt = new_graph(gt_nodes_plain, gt_edges)
        pred_input_sha256 = input_graph_sha256(pred_nodes_plain, pred_edges)
        gt_input_sha256 = input_graph_sha256(gt_nodes_plain, gt_edges)
        er = metrics.evaluate(pred, gt, scale=scale, max_distance=radius)
        empty_edge_matching = pred.num_edges() == 0
        if empty_edge_matching:
            # evaluate() exits its edge matching early for an edgeless prediction.
            # Its division evaluation matches copies only; node_recall() would
            # otherwise raise KeyError for absent MATCHED_NODE_ID. Apply the same
            # official matcher to this temporary graph solely to obtain recall.
            from tracksdata.metrics import DistanceMatching
            from tracksdata.options import get_options, set_options
            from scipy.sparse import SparseEfficiencyWarning

            progress = get_options().show_progress
            set_options(show_progress=False)
            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=SparseEfficiencyWarning)
                    pred.match(gt, matching=DistanceMatching(scale=scale, max_distance=radius))
            finally:
                set_options(show_progress=progress)
        recall = metrics.node_recall(pred, gt)
        official_row = metrics.per_sample_metrics(er, n_total=n_total, node_recall=recall)
        legacy_row = legacy_score(pred_nodes_plain, pred_edges, gt_nodes_plain, gt_edges, n_total)
        division_total = er.division_tp + er.division_fp + er.division_fn
        row = dict(official_row)
        row.update({
            "adjusted_edge_jaccard": official_row["adj_edge_jaccard"],
            "div_tp": er.division_tp, "div_fp": er.division_fp, "div_fn": er.division_fn,
            "div_jaccard": er.division_tp / division_total if division_total else float("nan"),
            "t_pred": er.num_pred_nodes, "t_true": n_total,
            "weight": er.edge_tp + er.edge_fp + er.edge_fn,
            "metric_provenance": provenance,
            "error_decomposition_provenance": legacy_provenance,
            "official_edgeless_recall_matching": empty_edge_matching,
            "input_pred_graph_sha256": pred_input_sha256,
            "input_gt_graph_sha256": gt_input_sha256,
            "input_graph_hash_schema": "ordered_plain_graph_v1:node_id,t,z,y,x;ordered_source,target;canonical_json_utf8",
            "input_graph_provenance": "same_plain_graph_received_by_legacy_proxy_and_official_adapter",
            "input_n_total": n_total,
            "input_scale_zyx_um": scale,
            "input_match_radius_um": radius,
        })
        # Keep names used by cell9/10 diagnostics, but explicitly retain their
        # legacy provenance; these six fields never enter the official score.
        row.update({key: legacy_row[key] for key in error_fields})
        row.update({"legacy_proxy_" + key: value for key, value in legacy_row.items()})
        return row

    def aggregate_official(sample_rows):
        rows = list(sample_rows)
        if not rows:
            raise ValueError("No validator rows; refusing undefined official selector score")
        for row in rows:
            if row.get("metric_provenance") != provenance:
                raise ValueError("Selector received a row without official scorer provenance")
            if not math.isfinite(float(row["t_true"])) or row["t_true"] <= 0:
                raise ValueError("Invalid node count metadata in official aggregation")
        official = metrics.summarise(rows)
        # Official summarise may skip NaN rows. Preserve and expose those counts,
        # but a nonfinite final score may never participate in Python sorting.
        if not math.isfinite(official["score"]) or not math.isfinite(official["adj_edge_jaccard"]):
            raise ValueError("Official aggregate score is nonfinite; no proxy fallback")
        legacy_rows = [
            {key.removeprefix("legacy_proxy_"): value for key, value in row.items()
             if key.startswith("legacy_proxy_")}
            for row in rows
        ]
        legacy = legacy_aggregate(legacy_rows)
        summary = dict(official)
        summary.update({
            "adjusted_edge_jaccard": official["adj_edge_jaccard"],
            # Historical key required by the unchanged selector in cell10.
            "proxy_score": official["score"],
            "official_score": official["score"],
            "proxy_score_field_semantics": "official_score_alias_for_unchanged_cell10",
            "div_tp": official["division_tp"], "div_fp": official["division_fp"],
            "div_fn": official["division_fn"],
            "metric_provenance": provenance,
            "error_decomposition_provenance": legacy_provenance,
            "official_rows_skipped": len(rows) - official["n"],
            "official_adjusted_rows_used": official["n_adj"],
            "legacy_proxy_score": legacy["proxy_score"],
        })
        summary.update({key: legacy[key] for key in error_fields})
        summary.update({"legacy_proxy_" + key: value for key, value in legacy.items()
                        if key != "proxy_score"})
        return summary

    scope["legacy_score_sample"] = legacy_score
    scope["legacy_aggregate_official"] = legacy_aggregate
    scope["score_sample"] = score_sample
    scope["aggregate_official"] = aggregate_official
    scope["OFFICIAL_SELECTOR_PROVENANCE"] = provenance
    return {"metric_provenance": provenance, "legacy_proxy_preserved": True,
            "graph_builder": "fresh_InMemoryGraph_bulk_add_nodes_bulk_add_edges",
            "nonfinite_final_score": "FAIL_CLOSED", "missing_n_total": "FAIL_CLOSED"}

install_official_selector(globals())

print("TARGET950: selector uses fixed official score; legacy proxy fields are diagnostic only.")
