"""固定 HOCT 0.2.0 的最小观测适配；保持预测与求解参数。

仅在 Kaggle 调用。恢复所有临时包装；部分求解不能产生可删集合。
"""
import math
import time
import numpy as np
from hoct_guard import digest


def observe_chunk(model, labels, images, ids_by_frame, raster, chunk_start, chunk_end):
    import hoct._api as api
    import hoct.inference._predict as inference
    import tracksdata as td
    from tracksdata.solvers import ILPSolver
    from ilpy import SolverStatus
    from tracksdata.functional import TilingScheme
    import torch

    original_solver = ILPSolver._solve
    original_predict = api.model_predict
    captured = {}
    statuses = []

    def observed_solve(self):
        answer = original_solver(self)
        statuses.append(str(answer.status))
        if answer.status != SolverStatus.OPTIMAL:
            raise RuntimeError('INCOMPLETE_SOLVE:' + str(answer.status))
        return answer

    def observed_predict(m, ds, **kwargs):
        # Record graph before the solver may append tracklet-bridging edges.
        captured['initial_edges'] = set(map(int, ds.graph.edge_attrs(attr_keys=[])['edge_id'].to_list()))
        captured['graph'] = ds.graph
        return original_predict(m, ds, **kwargs)

    class CheckedModel:
        def eval(self):
            model.eval()
            return self

        def parameters(self):
            return model.parameters()

        def forward(self, features, node_pos, edge_pos, edges, node_mask, edge_mask):
            for x in (features[node_mask], node_pos[node_mask], edge_pos[edge_mask]):
                if not torch.isfinite(x).all():
                    raise RuntimeError('NONFINITE_MODEL_INPUT')
            output = model.forward(features, node_pos, edge_pos, edges, node_mask, edge_mask)
            if not torch.isfinite(output[0][edge_mask]).all() or not torch.isfinite(output[3][node_mask]).all():
                raise RuntimeError('NONFINITE_MODEL_OUTPUT')
            return output

    ILPSolver._solve = observed_solve
    api.model_predict = observed_predict
    try:
        with torch.inference_mode():
            solution = api.predict(CheckedModel(), labels=labels, images=images,
                scale=(1.0, 1.625, .40625, .40625), max_delta_t=1,
                tiling_scheme=TilingScheme(tile_shape=(5,32,128,128), overlap_shape=(1,8,16,16)))
        if not statuses:
            raise RuntimeError('SOLVER_STATUS_UNOBSERVED')
        graph = captured['graph']
        mapping = {}
        used = set()
        # Exact label-mask identity avoids nearest-centroid guesses after overlap.
        for row in graph.node_attrs(attr_keys=['t', td.DEFAULT_ATTR_KEYS.MASK]).iter_rows(named=True):
            tt = int(row['t'])
            mask = row[td.DEFAULT_ATTR_KEYS.MASK]
            box = np.asarray(mask.bbox, dtype=int)
            crop = labels[tt][tuple(slice(int(a), int(b)) for a, b in zip(box[:3], box[3:]))]
            vals = np.unique(crop[np.asarray(mask.mask, dtype=bool)])
            if len(vals) != 1 or int(vals[0]) <= 0:
                continue
            index = int(vals[0]) - 1
            frame_ids = ids_by_frame.get(tt + chunk_start, [])
            if not 0 <= index < len(frame_ids):
                continue
            pid = frame_ids[index]
            if pid in used:
                raise RuntimeError('DUPLICATE_ENDPOINT_MAPPING')
            used.add(pid)
            mapping[int(row['node_id'])] = pid
        covered = set()
        for row in graph.edge_attrs(attr_keys=['similarity']).iter_rows(named=True):
            u, v = int(row['source_id']), int(row['target_id'])
            score = float(row['similarity'])
            if (int(row['edge_id']) in captured['initial_edges'] and math.isfinite(score) and score >= 0
                    and u in mapping and v in mapping
                    and chunk_start <= raster[mapping[u]][0] < chunk_end):
                covered.add((mapping[u], mapping[v]))
        selected = set()
        for row in solution.edge_attrs(attr_keys=[]).iter_rows(named=True):
            u, v = int(row['source_id']), int(row['target_id'])
            if u in mapping and v in mapping and chunk_start <= raster[mapping[u]][0] < chunk_end:
                selected.add((mapping[u], mapping[v]))
        return covered, selected, dict(statuses=statuses, mapped_nodes=len(mapping),
             candidate_edges=len(captured['initial_edges']), evaluated_edges=len(covered))
    finally:
        ILPSolver._solve = original_solver
        api.model_predict = original_predict


def observe_video(video, nodes, edges, model, volume, rasterize, start_time, deadline_s=36000):
    """沿用 1/2/4 块重试；每次必须全部块成功。900 秒只是估时门。"""
    begun = time.monotonic()
    ev = dict(video=video, input_hash=digest([video, list(nodes.items()), edges]), complete=False,
              covered=[], selected=[], attempts=[])
    estimate = 9 * len(nodes) / 1000 + 10
    ev['estimate_s'] = estimate
    if estimate > 900 or begun - start_time + estimate > deadline_s:
        ev['reason'] = 'BUDGET_ESTIMATE'
        return ev
    ids = sorted(nodes)
    det = np.array([[nodes[i][k] for k in ['t','z','y','x']] for i in ids], dtype=float)
    raster = {i: row for i, row in zip(ids, det)}
    ids_by_frame = {}
    for i in ids:
        ids_by_frame.setdefault(int(nodes[i]['t']), []).append(i)
    labels = rasterize(det, volume.shape)
    ev['lost_sphere_nodes'] = sum(len(v) - len(set(map(int, np.unique(labels[t]))) - {0}) for t, v in ids_by_frame.items())
    T = labels.shape[0]
    for n_chunks in (1, 2, 4):
        if time.monotonic() - start_time + estimate > deadline_s:
            ev['reason'] = 'BUDGET_RETRY'
            break
        covered, selected, receipts = set(), set(), []
        starts = [round(i*T/n_chunks) for i in range(n_chunks)] + [T]
        try:
            for a,b in zip(starts[:-1], starts[1:]):
                if time.monotonic() - start_time >= deadline_s:
                    raise RuntimeError('DEADLINE_BEFORE_CHUNK')
                c,s,r = observe_chunk(model, labels[a:min(T,b+1)], volume[a:min(T,b+1)], ids_by_frame, raster, a,b)
                covered.update(c); selected.update(s); receipts.append(r)
            ev.update(complete=True, covered=sorted(covered), selected=sorted(selected), reason='COMPLETE', chunks=n_chunks)
            ev['attempts'].append(dict(chunks=n_chunks, status='COMPLETE', receipts=receipts))
            break
        except RuntimeError as exc:
            ev['reason'] = type(exc).__name__ + ':' + str(exc)[:200]
            ev['attempts'].append(dict(chunks=n_chunks, status=ev['reason']))
            import torch
            torch.cuda.empty_cache()
    ev['seconds'] = time.monotonic() - begun
    return ev
