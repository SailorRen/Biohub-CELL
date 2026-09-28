# CELL 0
!pip install --no-index --find-links /kaggle/input/datasets/sarveshchhetri/zarr-offline-wheel/wheels/kaggle/working/wheels zarr

# CELL 1
import os
import glob
from pathlib import Path

import numpy as np
import pandas as pd
import networkx as nx
from scipy.ndimage import gaussian_filter, maximum_filter
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree

try:
    import zarr
except ImportError as e:
    raise ImportError(
        'zarr is required to read the competition data. Run `!pip install zarr` '
        'in a cell above this one, then restart the kernel and re-run.'
    ) from e

RNG = np.random.default_rng(0)

# CELL 2
VOXEL_UM = np.array([1.625, 0.40625, 0.40625])   # (z, y, x) microns per voxel

# Detection (tighter spatial resolution, generous intensity pool)
XY_BIN          = 2        # increased resolution (was 4) to better separate dense cells
SMOOTH_SIGMA    = 1.5      # slightly heavier blur to prevent split peaks
PEAK_MIN_SEP    = 3
NMS_RADIUS_UM   = 5.0      # physical cell radius suppression
THRESH_Q        = 0.88     # static generous pool (temporal filter handles the noise)

# Linking & divisions
# NOTE: 7.0 um here is a *reused* value, not a re-derivation — it's the radius the
# scorer uses to match a predicted node to a GT node on the SAME frame, which is a
# different quantity from "how far can a real cell move in one timestep" (what this
# gate actually controls). It's a reasonable, safe starting point, but if you have
# time, calibrate it from the real displacement distribution in the training .geff
# files (see the optional local-validation section below) rather than trusting the
# coincidence that both numbers are "7".
LINK_GATE_UM    = 7.0
USE_VELOCITY    = True
ENABLE_DIVISIONS = True
DIV_GATE_UM     = 6.0      # radius to catch the second daughter cell
MAX_CHILDREN    = 2        # a cell divides into at most 2 daughters — cap it

# Graph pruning (the "secret sauce")
# A component of size 1-2 is almost certainly a noise blip that contributes zero
# edges either way (so pruning it is pure upside: it only helps the mild
# over-prediction penalty). A component of size 3-4 might still contain a couple of
# genuinely correct edges near a clip boundary or the very start/end of the movie —
# pruning those trades away real recall for very little benefit, since the metric
# barely penalizes unmatched predicted nodes. Start conservative and use the local
# validation section to check whether raising this to 5 actually helps your held-out
# edge Jaccard, rather than assuming it does.
MIN_TRACK_LENGTH = 3

SUBMISSION_COLUMNS = ['dataset', 'row_type', 'node_id', 't', 'z', 'y', 'x', 'source_id', 'target_id']

# CELL 3
def locate_competition_root():
    candidates = [
        Path('/kaggle/input/biohub-cell-tracking-during-development'),
        Path('/kaggle/input/competitions/biohub-cell-tracking-during-development'),
    ]
    for c in candidates:
        if (c / 'test').is_dir():
            return c / 'train', c / 'test'
    hits = glob.glob('/kaggle/input/**/test', recursive=True)
    if hits:
        root = Path(hits[0]).parent
        return root / 'train', root / 'test'
    raise FileNotFoundError('Could not locate competition data.')

TRAIN_DIR, TEST_DIR = locate_competition_root()
test_movies = sorted(p.stem for p in TEST_DIR.glob('*.zarr'))
train_movies_all = sorted(p.stem for p in TRAIN_DIR.glob('*.zarr')) if TRAIN_DIR.is_dir() else []

_ZARR_CACHE = {}
def _movie_array(zarr_path):
    if zarr_path not in _ZARR_CACHE:
        _ZARR_CACHE[zarr_path] = zarr.open(str(zarr_path), mode='r')['0']
    return _ZARR_CACHE[zarr_path]

def read_frame(zarr_path, t):
    return np.asarray(_movie_array(zarr_path)[t])

def num_frames(zarr_path):
    return _movie_array(zarr_path).shape[0]

def read_ground_truth(geff_path):
    """Read a training-set lineage graph (GEFF format) into node/edge frames.
    Only used by the optional local-validation section below."""
    g = zarr.open_group(str(geff_path), mode='r')
    node_ids = np.asarray(g['nodes/ids'][:]).astype(np.int64)
    coords = {k: np.asarray(g[f'nodes/props/{k}/values'][:]) for k in ('t', 'z', 'y', 'x')}
    nodes = pd.DataFrame({'node_id': node_ids, **coords})
    edge_ids = np.asarray(g['edges/ids'][:])
    edges = pd.DataFrame({'source_id': edge_ids[:, 0].astype(np.int64),
                           'target_id': edge_ids[:, 1].astype(np.int64)}) if edge_ids.size else \
             pd.DataFrame(columns=['source_id', 'target_id'])
    return nodes, edges

# CELL 4
def _normalize_frame(volume, lo_pct=1.0, hi_pct=99.5):
    """Per-frame background normalization so the quantile threshold behaves
    consistently across movies/frames with different absolute brightness -- cheap
    and makes THRESH_Q mean roughly the same thing everywhere."""
    lo, hi = np.percentile(volume, [lo_pct, hi_pct])
    if hi <= lo:
        return np.zeros_like(volume, dtype=np.float32)
    return np.clip((volume.astype(np.float32) - lo) / (hi - lo), 0.0, 1.0)

def detect_frame(volume):
    small = _normalize_frame(volume[:, ::XY_BIN, ::XY_BIN])
    smoothed = gaussian_filter(small, sigma=SMOOTH_SIGMA)

    footprint_size = (max(1, PEAK_MIN_SEP // 2), PEAK_MIN_SEP, PEAK_MIN_SEP)
    local_max = maximum_filter(smoothed, size=footprint_size) == smoothed

    nonzero = smoothed[smoothed > 0]
    if nonzero.size == 0:
        return np.empty((0, 3), dtype=np.int64)

    cutoff = np.quantile(nonzero, THRESH_Q)
    mask = local_max & (smoothed > cutoff)
    zz, yy, xx = np.nonzero(mask)
    scores = smoothed[zz, yy, xx]

    coords_voxel = np.stack([zz, yy * XY_BIN, xx * XY_BIN], axis=1)

    # NMS
    coords_um = coords_voxel * VOXEL_UM
    order = np.argsort(-scores)
    tree = cKDTree(coords_um)
    keep = np.ones(len(coords_voxel), dtype=bool)

    for i in order:
        if not keep[i]:
            continue
        nearby = tree.query_ball_point(coords_um[i], r=NMS_RADIUS_UM)
        for j in nearby:
            if j != i and scores[j] <= scores[i]:
                keep[j] = False

    coords_voxel, scores = coords_voxel[keep], scores[keep]
    order = np.argsort(-scores)
    return coords_voxel[order]

# CELL 5
def link_frames(prev_um, curr_um, prev_velocity=None):
    if len(prev_um) == 0 or len(curr_um) == 0:
        return []

    predicted = prev_um + prev_velocity if (USE_VELOCITY and prev_velocity is not None) else prev_um

    # 1-to-1 Hungarian matching (normal continuations)
    cost = np.linalg.norm(predicted[:, None, :] - curr_um[None, :, :], axis=2)
    cost_opt = cost.copy()
    cost_opt[cost > LINK_GATE_UM] = 1e6

    row_ind, col_ind = linear_sum_assignment(cost_opt)
    pairs = [(int(i), int(j)) for i, j in zip(row_ind, col_ind) if cost_opt[i, j] < 1e6]

    # Heuristic division pass: give an already-matched parent a *second* child.
    # Fixed vs. the original: (1) only searches among already-matched parents, so a
    # real nearby parent is never skipped in favor of a closer non-candidate that
    # then fails the "is it matched" check; (2) gates against the parent's raw last
    # position (prev_um), not its velocity-extrapolated one, since a daughter
    # diverges from where the parent actually was, not from where it's predicted to
    # drift; (3) caps children at MAX_CHILDREN.
    if ENABLE_DIVISIONS and pairs:
        children_count = {}
        for i, _ in pairs:
            children_count[i] = children_count.get(i, 0) + 1
        matched_curr = {j for _, j in pairs}
        matched_prev_idx = np.array(sorted(children_count))

        unassigned_curr = [j for j in range(len(curr_um)) if j not in matched_curr]
        for j in unassigned_curr:
            dist_to_matched = np.linalg.norm(prev_um[matched_prev_idx] - curr_um[j], axis=1)
            k = int(np.argmin(dist_to_matched))
            best_prev = int(matched_prev_idx[k])
            if dist_to_matched[k] < DIV_GATE_UM and children_count[best_prev] < MAX_CHILDREN:
                pairs.append((best_prev, j))
                children_count[best_prev] += 1

    return pairs

# CELL 6
def track_movie(zp, dataset_name):
    T = num_frames(zp)
    all_nodes, all_edges = [], []
    next_id = 1
    prev_ids, prev_um, prev_velocity = None, None, None

    for t in range(T):
        vol = read_frame(zp, t)
        coords = detect_frame(vol)

        ids = np.arange(next_id, next_id + len(coords))
        next_id += len(coords)
        coords_um = coords * VOXEL_UM

        for node_id, (z, y, x) in zip(ids, coords):
            all_nodes.append({'dataset': dataset_name, 'row_type': 'node', 'node_id': int(node_id),
                               't': t, 'z': int(z), 'y': int(y), 'x': int(x),
                               'source_id': -1, 'target_id': -1})

        if prev_ids is not None:
            pairs = link_frames(prev_um, coords_um, prev_velocity)
            for i, j in pairs:
                all_edges.append({'dataset': dataset_name, 'row_type': 'edge', 'node_id': -1,
                                   't': -1, 'z': -1, 'y': -1, 'x': -1,
                                   'source_id': int(prev_ids[i]), 'target_id': int(ids[j])})
            if USE_VELOCITY and pairs:
                matched_prev = np.array([i for i, _ in pairs])
                matched_curr = np.array([j for _, j in pairs])

                # Deduplicate current targets so velocity arrays match cleanly in division cases
                unique_curr, unique_idx = np.unique(matched_curr, return_index=True)
                unique_prev = matched_prev[unique_idx]

                prev_velocity = np.zeros_like(coords_um)
                prev_velocity[unique_curr] = coords_um[unique_curr] - prev_um[unique_prev]
            else:
                prev_velocity = None

        prev_ids, prev_um = ids, coords_um

    nodes_df = pd.DataFrame(all_nodes)
    edges_df = pd.DataFrame(all_edges) if all_edges else pd.DataFrame(
        columns=['dataset', 'row_type', 'node_id', 't', 'z', 'y', 'x', 'source_id', 'target_id'])

    # Short-track graph pruning (was left unfinished in the original -- this is the
    # part that actually builds the graph, drops short-lived components, and
    # returns the result; previously the function stopped after `G.add_nodes_from`
    # and never returned anything at all).
    if len(nodes_df) > 0:
        G = nx.Graph()
        G.add_nodes_from(nodes_df.node_id)
        G.add_edges_from(zip(edges_df.source_id, edges_df.target_id))

        min_len = min(MIN_TRACK_LENGTH, T)  # a movie shorter than the threshold would else lose everything
        keep_ids = set()
        for component in nx.connected_components(G):
            if len(component) >= min_len:
                keep_ids |= component

        nodes_df = nodes_df[nodes_df.node_id.isin(keep_ids)]
        edges_df = edges_df[edges_df.source_id.isin(keep_ids) & edges_df.target_id.isin(keep_ids)]

    stats = {'name': dataset_name, 'T': T, 'nodes': len(nodes_df), 'edges': len(edges_df),
              'cells_per_frame': len(nodes_df) / T if T else 0.0}
    return nodes_df, edges_df, stats

# CELL 7
def _match_nodes_per_t(pred_t, pred_um, gt_t, gt_um, max_dist=7.0):
    match = {}
    if len(pred_t) == 0 or len(gt_t) == 0:
        return match
    for t in np.unique(np.concatenate([pred_t, gt_t])):
        p_idx = np.where(pred_t == t)[0]
        g_idx = np.where(gt_t == t)[0]
        if len(p_idx) == 0 or len(g_idx) == 0:
            continue
        cost = np.linalg.norm(pred_um[p_idx][:, None, :] - gt_um[g_idx][None, :, :], axis=2)
        gated = cost.copy()
        gated[gated > max_dist] = 1e6
        row, col = linear_sum_assignment(gated)
        for r, c in zip(row, col):
            if gated[r, c] < 1e6:
                match[p_idx[r]] = g_idx[c]
    return match

def _score_edges_locally(pred_edges, match_p2g, gt_edges_set, gt_targets_with_parent, gt_sources_with_child):
    tp = fp = 0
    matched_gt_edges = set()
    for ps, pt in pred_edges:
        gs, gtt = match_p2g.get(ps), match_p2g.get(pt)
        if gs is not None and gtt is not None and (gs, gtt) in gt_edges_set:
            tp += 1
            matched_gt_edges.add((gs, gtt))
            continue
        if (gtt is not None and gtt in gt_targets_with_parent) or (gs is not None and gs in gt_sources_with_child):
            fp += 1
    fn = len(gt_edges_set) - len(matched_gt_edges)
    return tp, fp, fn

def score_movie_locally(nodes_df, edges_df, gt_nodes, gt_edges):
    pred_t = nodes_df['t'].to_numpy()
    pred_um = nodes_df[['z', 'y', 'x']].to_numpy() * VOXEL_UM
    pred_row_of_id = {nid: i for i, nid in enumerate(nodes_df.node_id.to_numpy())}

    gt_t = gt_nodes['t'].to_numpy()
    gt_um = gt_nodes[['z', 'y', 'x']].to_numpy() * VOXEL_UM
    gt_row_of_id = {nid: i for i, nid in enumerate(gt_nodes.node_id.to_numpy())}

    match_p2g = _match_nodes_per_t(pred_t, pred_um, gt_t, gt_um)

    gt_edges_set, gt_targets_with_parent, gt_sources_with_child = set(), set(), set()
    for _, row in gt_edges.iterrows():
        if row.source_id not in gt_row_of_id or row.target_id not in gt_row_of_id:
            continue
        s, t_ = gt_row_of_id[row.source_id], gt_row_of_id[row.target_id]
        gt_edges_set.add((s, t_))
        gt_targets_with_parent.add(t_)
        gt_sources_with_child.add(s)

    pred_edges = [(pred_row_of_id[s], pred_row_of_id[t_])
                  for s, t_ in zip(edges_df.source_id, edges_df.target_id)
                  if s in pred_row_of_id and t_ in pred_row_of_id]

    return _score_edges_locally(pred_edges, match_p2g, gt_edges_set, gt_targets_with_parent, gt_sources_with_child)

_rng_split = np.random.default_rng(0)
_val_movies = _rng_split.permutation(train_movies_all).tolist()[:max(1, len(train_movies_all) // 4)] \
    if train_movies_all else []

if _val_movies:
    tot_tp = tot_fp = tot_fn = 0
    for name in _val_movies:
        geff_path = TRAIN_DIR / f'{name}.geff'
        if not geff_path.exists():
            continue
        gt_nodes, gt_edges = read_ground_truth(geff_path)
        nodes_df, edges_df, _ = track_movie(TRAIN_DIR / f'{name}.zarr', name)
        tp, fp, fn = score_movie_locally(nodes_df, edges_df, gt_nodes, gt_edges)
        tot_tp, tot_fp, tot_fn = tot_tp + tp, tot_fp + fp, tot_fn + fn
        print(f'  {name}: TP={tp} FP={fp} FN={fn}')
    denom = tot_tp + tot_fp + tot_fn
    print(f'\nheld-out edge Jaccard: {(tot_tp / denom if denom else 0.0):.4f}')
else:
    print('No training .geff ground truth found -- skipping local validation (this is fine for a test-only run).')

# CELL 8
parts = []
run_stats = []

for name in test_movies:
    zp = TEST_DIR / f'{name}.zarr'
    if not (zp / '0' / 'zarr.json').exists():
        continue
    nodes_df, edges_df, stats = track_movie(zp, name)
    run_stats.append(stats)
    parts += [nodes_df, edges_df]
    print(f"  {name}: T={stats['T']} nodes={stats['nodes']} edges={stats['edges']} cells/frame={stats['cells_per_frame']:.1f}")

submission = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=SUBMISSION_COLUMNS)
submission = submission[SUBMISSION_COLUMNS]
submission.index.name = 'id'
submission.to_csv('submission.csv')

print(f'\nWrote submission.csv: {len(submission)} rows')
pd.DataFrame(run_stats)

# CELL 9
# sanity checks -- cheap to run, catches a broken submission before you spend it
nodes_only = submission[submission.row_type == 'node']
edges_only = submission[submission.row_type == 'edge']

assert (edges_only[['node_id', 't', 'z', 'y', 'x']] == -1).all().all(), 'edge rows must blank out node fields'

for ds, g in submission.groupby('dataset'):
    node_ids = set(g[g.row_type == 'node'].node_id)
    e = g[g.row_type == 'edge']
    assert (set(e.source_id) | set(e.target_id)).issubset(node_ids), f'dangling edge reference in {ds}'
    assert g[g.row_type == 'node'].node_id.is_unique, f'duplicate node_id in {ds}'

print('all checks passed')