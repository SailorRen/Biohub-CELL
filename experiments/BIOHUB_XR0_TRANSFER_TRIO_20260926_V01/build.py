"""Frozen XR0 two-factor transfer. Only gate filtering and no-flow velocity vary."""
import ast,copy,difflib,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent; R=P.parents[1]
baseline=json.loads((R/'experiments/BIOHUB_XR0_XD960_SCORE_PAIR_20260925_V01/XR0/candidate.ipynb').read_text())
base=[copy.deepcopy(c) for c in baseline['cells'] if c['cell_type']=='code']; assert len(base)==12
texts=[''.join(c['source']) for c in base]
# Keep original frozen inference text in a private namespace, so no XR0 globals are replaced.
inference=(R/'experiments/BIOHUB_SPRINT01_20260916/saved_inference.py').read_text()
gate_setup='''
import hashlib as _trio_hashlib
_TRIO_GATE_SHA = '0a1f9b93bb529e70f4f7c2ba0907eea8b4cecd2befccc8ba1fb75e569edf77a0'
_trio_gate_files = list(Path('/kaggle/input').rglob('division_gate_weights.json'))
_trio_gate_files = [p for p in _trio_gate_files if _trio_hashlib.sha256(p.read_bytes()).hexdigest() == _TRIO_GATE_SHA]
assert len(_trio_gate_files) == 1, 'TRIO_EXACT_GATE_WEIGHT_REQUIRED'
_trio_gate_model = json.loads(_trio_gate_files[0].read_text())['final']
assert np.asarray(_trio_gate_model['mean']).shape == (10,)
assert np.asarray(_trio_gate_model['scale']).shape == (10,)
assert np.asarray(_trio_gate_model['coefficients']).shape == (21,)
assert np.isfinite(np.asarray(_trio_gate_model['coefficients'])).all()
assert (np.asarray(_trio_gate_model['scale']) > 0).all()
_trio_inference = {}
exec(__FROZEN_INFERENCE__, _trio_inference)
assert tuple(VOXEL_SCALE_UM) == (1.625, 0.40625, 0.40625)
print('TRIO_GATE_LOADED', _TRIO_GATE_SHA, 'final', flush=True)
_TRIO_GATE_SAMPLES = []
def _trio_g1_accept_score(score):
    if score is not None and not np.isfinite(score):
        raise RuntimeError('TRIO_NONFINITE_GATE_SCORE')
    return not (score is not None and score < 0.95)
def _trio_g1_admit(nodes, outgoing, parent, child1, child2, stats, dataset):
    stats['trio_g1_candidates'] = stats.get('trio_g1_candidates', 0) + 1
    out = {u: [int(e['target_id']) for e in outgoing.get(u, [])] for u in (child1, child2)}
    coords = _trio_inference['context'](nodes, out, parent, child1, child2)
    score = None if coords is None else float(_trio_inference['predict'](_trio_gate_model, _trio_inference['pair_features'](coords)))
    accepted = _trio_g1_accept_score(score)
    key = 'trio_g1_abstain' if score is None else 'trio_g1_finite_scores'
    stats[key] = stats.get(key, 0) + 1
    if not accepted:
        stats['trio_g1_rejected'] = stats.get('trio_g1_rejected', 0) + 1
    if len(_TRIO_GATE_SAMPLES) < 20:
        _TRIO_GATE_SAMPLES.append(dict(dataset=dataset, parent=int(parent), child1=int(child1), child2=int(child2), score=score, accepted=accepted))
    return accepted
'''.replace('__FROZEN_INFERENCE__',repr(inference))
for arm,vel,gate in [('XV25',.25,False),('XG95',.5,True),('XV25G95',.25,True)]:
 d=P/arm;d.mkdir(exist_ok=True);s=texts.copy()
 s[0]+='\n# Frozen transfer batch: configure before original globals are initialized.\nos.environ["BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT"] = '+repr(str(vel))+'\n'
 # Original main weights remain asserted. Verify head bytes at its actual mounted path.
 anchor='_trial_source ='
 idx=s[4].index(anchor)
 s[4]=s[4][:idx]+'''import hashlib as _trio_hh
assert _myhead[0].stat().st_size == 33913, 'TRIO_HEAD_SIZE'
assert _trio_hh.sha256(_myhead[0].read_bytes()).hexdigest() == '625a0d9340f48193f2ec294fc2d81c5bb3c03087eab78ef0ae998a9c4c7da00c', 'TRIO_HEAD_HASH'
print('TRIO_HEAD_VERIFIED', str(_myhead[0]), '625a0d9340f48193f2ec294fc2d81c5bb3c03087eab78ef0ae998a9c4c7da00c', flush=True)
'''+s[4][idx:]
 # Counters only at actual consumption sites; original expressions retained verbatim.
 a='                predicted_arr[i] = source_pos + MOTION_RELINK_VELOCITY_WEIGHT * (source_pos - prev_pos)'
 assert s[5].count(a)==1
 s[5]=s[5].replace(a,a+'\n                stats["trio_velocity_consumed"] = stats.get("trio_velocity_consumed", 0) + 1\n                stats["trio_velocity_weight"] = MOTION_RELINK_VELOCITY_WEIGHT')
 a='                predicted_arr[i] = source_pos\n';assert s[5].count(a)==1
 s[5]=s[5].replace(a,a+'                stats["trio_no_flow_no_history"] = stats.get("trio_no_flow_no_history", 0) + 1\n')
 # Explicit zeros initialized when the real graph processor is called (not missing-field assumptions).
 name='def filter_output_graph('
 fn=next(n for n in ast.parse(s[5]).body if isinstance(n,ast.FunctionDef) and n.name=='filter_output_graph')
 # Add counters at motion entry to retain original stats dict initialization.
 fnm=next(n for n in ast.parse(s[5]).body if isinstance(n,ast.FunctionDef) and n.name=='motion_relink_edges')
 lines=s[5].splitlines(True); pos=fnm.body[0].lineno-1
 lines[pos:pos]=['    stats.setdefault("trio_velocity_consumed", 0)\n','    stats.setdefault("trio_no_flow_no_history", 0)\n','    stats["trio_velocity_weight"] = MOTION_RELINK_VELOCITY_WEIGHT\n']
 s[5]=''.join(lines)
 if gate:
  fn=next(n for n in ast.parse(s[5]).body if isinstance(n,ast.FunctionDef) and n.name=='add_safe_divisions_postlink')
  old=ast.get_source_segment(s[5],fn);new=old
  a='                proposals.append((score, source_id, candidate_id, parent_dist, sister_dist))';assert new.count(a)==1
  new=new.replace(a,'                if _trio_g1_admit(nodes_by_id, out_by_source, source_id, existing_child_id, candidate_id, stats, dataset):\n    '+a)
  lines=new.splitlines(True); fn2=ast.parse(new).body[0];pos=fn2.body[0].lineno-1
  lines[pos:pos]=['    for _trio_key in ("trio_g1_candidates", "trio_g1_finite_scores", "trio_g1_rejected", "trio_g1_abstain"):\n','        stats.setdefault(_trio_key, 0)\n']
  s[5]=s[5].replace(old,''.join(lines),1)
  assert s[5].count('write_test_submission("base")')==1
  s[5]=s[5].replace('write_test_submission("base")',gate_setup+'\nwrite_test_submission("base")')
 nb={'nbformat':4,'nbformat_minor':5,'metadata':copy.deepcopy(baseline['metadata']),'cells':[]}
 for i,code in enumerate(s):
  ast.parse(code);nb['cells'].append(dict(cell_type='code',source=code,metadata={},execution_count=None,outputs=[],id=f'trio-{i:02}'))
 end=(P/'runtime_receipt.py').read_text().replace('__ARM__',repr(arm)).replace('__VEL__',repr(vel)).replace('__GATE__',repr(gate))
 ast.parse(end);nb['cells'].append(dict(cell_type='code',source=end,metadata={},execution_count=None,outputs=[],id='trio-receipt'))
 (d/'candidate.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=1)+'\n')
 diff=''.join(''.join(difflib.unified_diff(texts[i].splitlines(True),s[i].splitlines(True),fromfile=f'XR0/cell{i+1}',tofile=f'{arm}/cell{i+1}')) for i in range(12))
 (d/'source.diff').write_text(diff)
 meta=json.loads((R/'experiments/BIOHUB_XR0_XD960_SCORE_PAIR_20260925_V01/XR0/kernel-metadata.json').read_text())
 slug=f'biohub-xr0-{arm.lower()}-20260926';meta.update(id='sailorren/'+slug,title=slug,kernel_sources=['sailorren/biohub-division-train-20260914/1'] if gate else [])
 (d/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
 (d/'build_receipt.json').write_text(json.dumps({'arm':arm,'velocity':vel,'g1':gate,'g1_threshold':.95 if gate else None,'source_sha256':hashlib.sha256((d/'candidate.ipynb').read_bytes()).hexdigest(),'unchanged_original_cells':[i+1 for i in range(12) if s[i]==texts[i]],'algorithm_changes':['no_flow_velocity']*(vel==.25)+['frozen_G1_proposal_filter']*gate,'runtime_additions':'head hash; consumption counters; CSV and light receipt; no extra inference'},indent=2)+'\n')
 print('BUILT',arm)
