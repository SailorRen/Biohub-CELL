"""Only the two-wave postprocessing changes and small audit helpers. No inference."""
import math
from collections import Counter


def scored_probability(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        value = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(value):
        return None
    if value < 0.0 or value > 1.0:
        value = 1.0 / (1.0 + math.exp(-max(-20.0, min(20.0, value))))
    return max(0.0, min(1.0, value))


def prune_leaves(nodes, edges, last_frame, threshold):
    stats = dict(candidates=0, division_exempt=0, missing_score_exempt=0,
                 final_frame_exempt=0, deleted=0, deleted_ids=[],
                 last_frame=last_frame, threshold=threshold)
    if threshold is None:
        stats['skipped'] = 'DISABLED'
        return nodes, edges, stats
    if last_frame is None:
        stats['skipped'] = 'TRUE_LAST_FRAME_UNAVAILABLE'
        return nodes, edges, stats
    out = Counter(int(e['source_id']) for e in edges)
    incoming = {}
    for e in edges:
        incoming.setdefault(int(e['target_id']), []).append(e)
    remove = set()
    for node_id, node in nodes.items():
        inc = incoming.get(node_id, [])
        if out[node_id] or len(inc) != 1:
            continue
        stats['candidates'] += 1
        e = inc[0]
        if int(node['t']) >= last_frame:
            stats['final_frame_exempt'] += 1
        elif out[int(e['source_id'])] != 1:
            stats['division_exempt'] += 1
        elif e.get('_wave_model_probability') is None:
            stats['missing_score_exempt'] += 1
        elif e['_wave_model_probability'] < threshold:
            remove.add(node_id)
    stats['deleted'] = len(remove)
    stats['deleted_ids'] = sorted(remove)[:20]
    return ({i:n for i,n in nodes.items() if i not in remove},
            [e for e in edges if int(e['source_id']) not in remove and int(e['target_id']) not in remove], stats)


def invariant_graph(nodes, edges):
    """ID-independent exact rooted-forest encoding with rounded CSV coordinates."""
    children = {i:[] for i in nodes}
    parents = set()
    for e in edges:
        s,t = int(e['source_id']),int(e['target_id'])
        children[s].append(t); parents.add(t)
    # Children always occur later in time; bottom-up encoding also handles duplicate coordinates.
    import hashlib,json
    labels = {}
    for i in sorted(nodes, key=lambda i:int(nodes[i]['t']), reverse=True):
        n = nodes[i]
        value = [int(n['t']),*[max(0,int(round(float(n[k])))) for k in ('z','y','x')],sorted(labels[c] for c in children[i])]
        labels[i] = hashlib.sha256(json.dumps(value,separators=(',',':')).encode()).hexdigest()
    return sorted(labels[i] for i in nodes if i not in parents)
