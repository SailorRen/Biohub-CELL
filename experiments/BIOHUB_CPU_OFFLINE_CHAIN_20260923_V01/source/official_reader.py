def build_graph_from_rows(
    node_rows: pl.DataFrame,
    edge_rows: pl.DataFrame,
) -> td.graph.InMemoryGraph:
    """Rebuild a tracksdata graph from one dataset's node and edge rows.

    tracksdata assigns fresh node ids, so CSV ``node_id``s are remapped when
    adding edges (matching is spatial, not by id).
    """
    graph = td.graph.InMemoryGraph()
    for key in ("z", "y", "x"):
        graph.add_node_attr_key(key, pl.Float64, -999999.0)

    assigned = graph.bulk_add_nodes(
        node_rows.select(
            pl.col("t").cast(pl.Int64),
            pl.col("z").cast(pl.Float64),
            pl.col("y").cast(pl.Float64),
            pl.col("x").cast(pl.Float64),
        ).to_dicts()
    )
    id_map = dict(zip(node_rows["node_id"].to_list(), assigned, strict=True))

    if edge_rows.height:
        graph.bulk_add_edges(
            [
                {"source_id": id_map[s], "target_id": id_map[t]}
                for s, t in zip(
                    edge_rows["source_id"].to_list(), edge_rows["target_id"].to_list(), strict=True
                )
            ]
        )

    return graph
