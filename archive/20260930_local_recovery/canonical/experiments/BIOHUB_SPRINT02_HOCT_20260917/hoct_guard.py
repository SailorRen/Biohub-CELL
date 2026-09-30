"""H1 的纯图边界；不导入模型、不训练、不读平台。"""
import copy
import hashlib
import json
from collections import Counter


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False,
                                     separators=(',', ':')).encode()).hexdigest()


def apply_guard(video, nodes, edges, evidence=None, enabled=True):
    """证据必须绑定同一视频、同一有序输入及完整求解；缺证据原样返回。"""
    before = digest([video, list(nodes.items()), edges])
    pairs = {(int(e['source_id']), int(e['target_id'])) for e in edges}
    assert len(pairs) == len(edges), 'DUPLICATE_BASE_EDGE'
    assert all(u in nodes and v in nodes for u, v in pairs), 'DANGLING_BASE_EDGE'
    degree = Counter(u for u, _ in pairs)
    protected = {e for e in pairs if degree[e[0]] >= 2}
    covered, selected = set(), set()
    reason = 'DISABLED' if not enabled else 'MISSING_EVIDENCE'
    if enabled and evidence:
        if evidence.get('video') != video or evidence.get('input_hash') != before:
            reason = 'INPUT_OR_VIDEO_MISMATCH'
        elif evidence.get('complete') is not True:
            reason = evidence.get('reason', 'INCOMPLETE_SOLVE')
        else:
            covered = {tuple(e) for e in evidence['covered']} & (pairs - protected)
            selected = {tuple(e) for e in evidence['selected']}
            reason = 'APPLIED'
    deleted = covered - selected
    output = copy.deepcopy([e for e in edges if (int(e['source_id']), int(e['target_id'])) not in deleted])
    output_nodes = copy.deepcopy(nodes)
    after_pairs = {(int(e['source_id']), int(e['target_id'])) for e in output}
    assert protected <= after_pairs <= pairs and pairs - after_pairs == deleted
    assert output_nodes == nodes
    receipt = dict(video=video, input_hash=before, status=reason,
                   nodes=len(nodes), edges_before=len(edges), edges_after=len(output),
                   protected=len(protected), protected_hash=digest(sorted(protected)),
                   anomalous_parents=sum(v > 2 for v in degree.values()),
                   coordinates_hash=digest(list(nodes.items())), covered=len(covered),
                   deleted=len(deleted), uncovered=len(pairs - protected - covered),
                   added_edges=0, invariants_pass=True)
    return output_nodes, output, receipt, sorted(deleted)
