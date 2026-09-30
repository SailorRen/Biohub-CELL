"""固定 HOCT 0.2.0 的最小观测适配；保持预测与求解参数。

仅在 Kaggle 调用。恢复所有临时包装；部分求解不能产生可删集合。
"""
import math
import time
import traceback
from contextlib import contextmanager
import numpy as np
from hoct_guard import digest


class InterfaceError(RuntimeError):
    """确定性接口错误；不能按求解重试或空覆盖成功处理。"""
    def __init__(self, message, observation=None):
        super().__init__('INTERFACE_ERROR: ' + message)
        self.observation = observation or {}


def required_attrs(graph, kind, fields, location):
    actual = None
    try:
        frame = getattr(graph, kind + '_attrs')(attr_keys=fields)
        actual = list(frame.columns)
        missing = [f for f in fields if f not in actual]
        if missing:
            raise KeyError(missing)
        return frame
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        raise InterfaceError(f'{location}: required={fields!r}; actual={actual!r}; {exc}') from exc


def initial_candidate_ids(graph):
    return set(map(int, required_attrs(graph, 'edge', ['edge_id'], 'initial_candidates')['edge_id'].to_list()))


@contextmanager
def temporary_observers(solver_class, api, solver_hook, predict_hook):
    old_solver, old_predict = solver_class._solve, api.model_predict
    solver_class._solve, api.model_predict = solver_hook, predict_hook
    try:
        yield
    finally:
        solver_class._solve, api.model_predict = old_solver, old_predict


def map_endpoints(graph, labels, ids_by_frame, chunk_start, location):
    import tracksdata as td
    mapping = {}
    used = set()
    # Exact label-mask identity avoids nearest-centroid guesses after overlap.
    for row in required_attrs(graph, 'node', ['node_id', 't', td.DEFAULT_ATTR_KEYS.MASK], location).iter_rows(named=True):
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
            raise InterfaceError(location + ': DUPLICATE_ENDPOINT_MAPPING')
        used.add(pid)
        mapping[int(row['node_id'])] = pid
    return mapping


def collect_mapped_edges(graph, solution, initial_edges, labels, ids_by_frame,
                         raster, chunk_start, chunk_end, solve_complete):
    import tracksdata as td
    if not solve_complete:
        raise RuntimeError('INCOMPLETE_SOLVE')
    mapping = map_endpoints(graph, labels, ids_by_frame, chunk_start, 'candidate_mapping')
    solution_mapping = map_endpoints(solution, labels, ids_by_frame, chunk_start, 'solution_mapping')
    covered = set()
    for row in required_attrs(graph, 'edge', ['edge_id', 'source_id', 'target_id', 'similarity'], 'candidate_coverage').iter_rows(named=True):
        u, v = int(row['source_id']), int(row['target_id'])
        score = float(row['similarity'])
        if (int(row['edge_id']) in initial_edges and math.isfinite(score) and score >= 0
                and u in mapping and v in mapping
                and chunk_start <= raster[mapping[u]][0] < chunk_end):
            covered.add((mapping[u], mapping[v]))
    selected = set()
    for row in required_attrs(solution, 'edge', ['source_id', 'target_id'], 'selected_edges').iter_rows(named=True):
        u, v = int(row['source_id']), int(row['target_id'])
        if u in solution_mapping and v in solution_mapping and chunk_start <= raster[solution_mapping[u]][0] < chunk_end:
            selected.add((solution_mapping[u], solution_mapping[v]))
    return covered, selected, dict(mapped_nodes=len(mapping), candidate_edges=len(initial_edges), evaluated_edges=len(covered))


def observe_chunk(model, labels, images, ids_by_frame, raster, chunk_start, chunk_end):
    import hoct._api as api
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
        captured['initial_edges'] = initial_candidate_ids(ds.graph)
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

    stage = 'predict_and_solve'
    try:
        with temporary_observers(ILPSolver, api, observed_solve, observed_predict):
            with torch.inference_mode():
                solution = api.predict(CheckedModel(), labels=labels, images=images,
                    scale=(1.0, 1.625, .40625, .40625), max_delta_t=1,
                    tiling_scheme=TilingScheme(tile_shape=(5,32,128,128), overlap_shape=(1,8,16,16)))
            if not statuses:
                raise RuntimeError('SOLVER_STATUS_UNOBSERVED')
            stage = 'endpoint_mapping_and_coverage'
            covered, selected, receipt = collect_mapped_edges(
                captured['graph'], solution, captured['initial_edges'], labels,
                ids_by_frame, raster, chunk_start, chunk_end, solve_complete=True)
            return covered, selected, dict(receipt, statuses=statuses)
    except (InterfaceError, KeyError, AttributeError, TypeError, IndexError, ValueError) as exc:
        observation = dict(stage=stage, statuses=statuses or None,
                           solver_calls_observed=len(statuses) if statuses else None)
        if isinstance(exc, InterfaceError):
            exc.observation.update(observation)
            raise
        raise InterfaceError(f'{stage}: {type(exc).__name__}: {exc}', observation) from exc
    except RuntimeError as exc:
        exc.observation = dict(stage=stage, statuses=statuses or None,
                               solver_calls_observed=len(statuses) if statuses else None)
        raise


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
        except InterfaceError as exc:
            ev.update(reason=str(exc), status='INTERFACE_ERROR', traceback=traceback.format_exc(),
                      observation=exc.observation, complete=False, covered=[], selected=[])
            ev['attempts'].append(dict(chunks=n_chunks, status='INTERFACE_ERROR', receipts=receipts,
                                       observation=exc.observation))
            break
        except RuntimeError as exc:
            ev['reason'] = type(exc).__name__ + ':' + str(exc)[:200]
            ev['attempts'].append(dict(chunks=n_chunks, status=ev['reason'], receipts=receipts,
                                       observation=getattr(exc, 'observation', None), traceback=traceback.format_exc()))
            import torch
            torch.cuda.empty_cache()
    ev['seconds'] = time.monotonic() - begun
    return ev


def stop_on_interface_error(evidence, persist):
    """诊断循环的唯一快速停止判定；先保存原始错误和已观察证据。"""
    if evidence.get('status') == 'INTERFACE_ERROR':
        persist(evidence)
        return True
    return False
