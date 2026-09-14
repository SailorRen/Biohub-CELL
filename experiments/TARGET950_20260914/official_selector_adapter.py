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
