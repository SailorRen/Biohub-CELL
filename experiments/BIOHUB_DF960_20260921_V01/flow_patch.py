"""F1: one-pass neighbour displacement prior, no labels or model fitting."""
import numpy as np

CONFIG = dict(k=12, radius_um=40.0, exclude_um=1.5, min_global_seeds=4, iterations=1)

def neighbour_predictions(nodes, seed_edges, position_um):
    """Seeds are tight edges from an independent unmodified G1 motion call."""
    by_t = {}
    for edge in seed_edges:
        if edge['motion_pass'] != 'tight':
            continue
        s, d = int(edge['source_id']), int(edge['target_id'])
        assert s in nodes and d in nodes, 'F1_SEED_ENDPOINT'
        t = int(nodes[s]['t'])
        assert int(nodes[d]['t']) == t + 1, 'F1_SEED_TIME'
        pos = position_um(nodes[s])
        delta = position_um(nodes[d]) - pos
        assert np.isfinite(pos).all() and np.isfinite(delta).all(), 'F1_NONFINITE_SEED'
        by_t.setdefault(t, []).append((s, pos, delta))
    times = {int(n['t']) for n in nodes.values()}
    predictions, rows = {}, []
    for t in sorted(times):
        if t+1 not in times:
            continue
        seeds = by_t.get(t, [])
        ids = sorted(i for i,n in nodes.items() if int(n['t']) == t)
        counts, covered = {}, 0
        for node_id in ids:
            pos = position_um(nodes[node_id])
            assert np.isfinite(pos).all(), 'F1_NONFINITE_POSITION'
            neighbours = []
            if len(seeds) >= CONFIG['min_global_seeds']:
                for seed_id, seed_pos, delta in seeds:
                    if seed_id == node_id:
                        continue
                    distance = float(np.linalg.norm(seed_pos-pos))
                    if CONFIG['exclude_um'] < distance <= CONFIG['radius_um']:
                        neighbours.append((distance, seed_id, delta))
                neighbours.sort(key=lambda r:(r[0],r[1]))
                neighbours = neighbours[:CONFIG['k']]
            counts[len(neighbours)] = counts.get(len(neighbours),0)+1
            if neighbours:
                predicted = pos + np.median(np.stack([r[2] for r in neighbours]), axis=0)
                assert np.isfinite(predicted).all(), 'F1_NONFINITE_FLOW'
                predictions[node_id] = predicted
                covered += 1
        rows.append(dict(t=t,seeds=len(seeds),source_nodes=len(ids),flow_nodes=covered,
                         global_seed_fallback=len(ids) if len(seeds)<4 else 0,
                         no_local_fallback=len(ids)-covered if len(seeds)>=4 else 0,
                         neighbour_counts=counts))
    return predictions, rows

def patch_motion_source(original):
    """Change only predicted position; preserve gates, costs and assignments."""
    anchor='            for j, target_id in enumerate(target_ids):'
    assert original.count(anchor)==1
    return original.replace('def motion_relink_edges(', 'def _f1_motion_impl(',1).replace(
        anchor, '            if source_id in F1_PREDICTIONS:\n                predicted = F1_PREDICTIONS[source_id]\n'+anchor,1)

def install(scope, original_source):
    original = scope['motion_relink_edges']
    exec(patch_motion_source(original_source), scope)
    impl = scope['_f1_motion_impl']
    scope['F1_ENABLED'] = True
    scope['F1_CALLS'] = []
    def motion(nodes, stats, learned_edge_probs=None):
        import collections, time
        if not scope['F1_ENABLED']:
            return original(nodes, stats, learned_edge_probs)
        start = time.monotonic()
        seed_stats = collections.defaultdict(int)
        seeds = original(nodes, seed_stats, learned_edge_probs)
        pred, rows = neighbour_predictions(nodes, seeds, scope['_position_um'])
        scope['F1_PREDICTIONS'] = pred
        result = impl(nodes, stats, learned_edge_probs)
        scope['F1_CALLS'].append(dict(frames=rows,seconds=time.monotonic()-start,
                                     seed_stats=dict(seed_stats),prediction_count=len(pred)))
        return result
    scope['motion_relink_edges'] = motion
    return original
