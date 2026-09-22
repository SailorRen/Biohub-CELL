"""Rebuild from the SHA-pinned D960 source downloaded from GitHub; never launches."""
import ast,copy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parents[1]/'source/D960/candidate.ipynb'
EXPECTED='b12568e27ea5a8c66942a6301c2c80d037fdffe43f338a23a86266f80a02d192'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
original=json.loads(SOURCE.read_text(encoding='utf-8'))
def source(c):return ''.join(c['source'])
def replace(s,a,b):
    assert s.count(a)==1,(a,s.count(a))
    return s.replace(a,b)
support=(ROOT/'patch_support.py').read_text(encoding='utf-8')
addon='''
_wave_last_frames = {}
def wave_last_frame(dataset):
    key = str(Path(TEST_DIR).resolve()), dataset
    if key not in _wave_last_frames:
        try:
            # Original read_test_frame uses this exact input and TZYX time indexing.
            path = TEST_DIR / f"{dataset}.zarr" / "0" / "zarr.json"
            meta = json.loads(path.read_text())
            shape = meta['shape']
            assert len(shape) == 4 and int(shape[0]) > 0
            dims = meta.get('dimension_names')
            assert dims is None or dims[0] in ('t','time')
            _wave_last_frames[key] = int(shape[0]) - 1
        except (OSError, ValueError, KeyError, TypeError, AssertionError):
            _wave_last_frames[key] = None
    return _wave_last_frames[key]
'''
results={}
for arm,velocity,leaf,slug in [('A',.25,None,'biohub-d960-v025-20260922'),('B',.5,.30,'biohub-d960-l030p-20260922')]:
    nb=copy.deepcopy(original)
    ss=[source(c) for c in nb['cells']]
    ss[0]+='\n# Two-wave candidate; set before configuration initialization.\n'+f'os.environ["BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT"] = "{velocity}"\nWAVE_ARM = {arm!r}\nWAVE_EXPECTED_VELOCITY = {velocity!r}\nWAVE_LEAF_THRESHOLD = {leaf!r}\n'
    s=ss[5]
    s=replace(s,'def motion_relink_edges(',support+'\n'+addon+'\ndef motion_relink_edges(')
    s=replace(s,'                predicted = source_pos + MOTION_RELINK_VELOCITY_WEIGHT * (source_pos - prev_pos)',
        '                stats["wave_velocity_consumed"] = float(MOTION_RELINK_VELOCITY_WEIGHT)\n                stats["wave_velocity_calls"] = stats.get("wave_velocity_calls", 0) + 1\n                predicted = source_pos + MOTION_RELINK_VELOCITY_WEIGHT * (source_pos - prev_pos)')
    s=replace(s,'                "motion_relinked": 1,','                "_wave_model_probability": scored_probability(learned_edge_probs[(source_id, target_id)]) if (source_id, target_id) in learned_edge_probs else None,\n                "motion_relinked": 1,')
    s=replace(s,'    for edge in raw_edges:\n','    for edge in raw_edges:\n        edge["_wave_model_probability"] = scored_probability(edge.get("edge_prob"))\n')
    s=replace(s,'    nodes_by_id = linefit_smooth_output_graph(nodes_by_id, edges, stats)',
        '    nodes_by_id, edges, leaf_stats = prune_leaves(nodes_by_id, edges, wave_last_frame(dataset) if WAVE_LEAF_THRESHOLD is not None else None, WAVE_LEAF_THRESHOLD)\n    stats["wave_leaf"] = leaf_stats\n    nodes_by_id = linefit_smooth_output_graph(nodes_by_id, edges, stats)')
    tree=ast.parse(s)
    execnode=next(n for n in tree.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='exec' and len(n.value.args)>1 and ast.unparse(n.value.args[1])=='_trio.__dict__')
    runtime=execnode.value.args[0].value
    runtime=runtime.replace("'score_trio'","'two_wave'")
    runtime=replace(runtime,"        calls.append(row);append(root/'postprocess_calls.jsonl',row)",'''        old_velocity = g['MOTION_RELINK_VELOCITY_WEIGHT']; old_leaf = g['WAVE_LEAF_THRESHOLD']
        # Evidence replay on the same raw graph, no second inference and no output reuse.
        try:
            g['MOTION_RELINK_VELOCITY_WEIGHT'] = .5; g['WAVE_LEAF_THRESHOLD'] = None
            baseline = original(copy.deepcopy(nodes),copy.deepcopy(edges),**kw)
        finally:
            g['MOTION_RELINK_VELOCITY_WEIGHT'] = old_velocity; g['WAVE_LEAF_THRESHOLD'] = old_leaf
        row['baseline_replay_velocity'] = .5
        row['baseline_replay_leaf'] = None
        row['baseline_invariant_sha256'] = digest(g['invariant_graph'](baseline[0],baseline[1]))
        row['candidate_invariant_sha256'] = digest(g['invariant_graph'](result[0],result[1]))
        row['actual_effect'] = row['baseline_invariant_sha256'] != row['candidate_invariant_sha256']
        row['wave_arm'] = g['WAVE_ARM']
        calls.append(row);append(root/'postprocess_calls.jsonl',row)''')
    runtime=replace(runtime,"    save(root/'production_receipt.json',receipt)",'''    assert g['MOTION_RELINK_VELOCITY_WEIGHT'] == g['WAVE_EXPECTED_VELOCITY']
    assert before['MOTION_RELINK_VELOCITY_WEIGHT'] == g['WAVE_EXPECTED_VELOCITY']
    assert all(r['stats'].get('wave_velocity_calls',0)>0 and r['stats']['wave_velocity_consumed']==g['WAVE_EXPECTED_VELOCITY'] for r in latest.values()), 'VELOCITY_NOT_CONSUMED'
    receipt.update(task_id='BIOHUB_TWO_WAVE_20260922_V01',arm=g['WAVE_ARM'],mother='D960',
        leaf_threshold=g['WAVE_LEAF_THRESHOLD'],velocity=g['WAVE_EXPECTED_VELOCITY'],
        same_run_comparison={s:{k:r[k] for k in ['baseline_invariant_sha256','candidate_invariant_sha256','actual_effect']} for s,r in latest.items()},
        has_effect=any(r['actual_effect'] for r in latest.values()),
        comparison_limit='Same raw inference, same selected configuration; candidate-disabled CPU replay, not an independent formal baseline.',
        velocity_consumed={s:{k:v for k,v in r['stats'].items() if k.startswith('wave_')} for s,r in latest.items()})
    save(root/'production_receipt.json',receipt)''')
    lines=s.splitlines(keepends=True)
    lines[execnode.lineno-1:execnode.end_lineno]=['exec('+repr(runtime)+', _trio.__dict__)\n']
    ss[5]=''.join(lines)
    # Preserved D960 checker constants are intentionally invoked as D960; final receipt binds A/B.
    ss[13]=ss[13].replace("'D960'","'D960'")
    for c,txt in zip(nb['cells'],ss):
        ast.parse(txt)
        c['source']=txt.splitlines(keepends=True);c['outputs']=[];c['execution_count']=None
    dest=ROOT/arm;dest.mkdir(exist_ok=True)
    raw=(json.dumps(nb,ensure_ascii=False,indent=1)+'\n').encode()
    (dest/'candidate.ipynb').write_bytes(raw)
    meta=json.loads((SOURCE.parent/'kernel-metadata.json').read_text())
    meta.update(id='sailorren/'+slug,title=slug)
    (dest/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
    results[arm]={'notebook_sha256':hashlib.sha256(raw).hexdigest(),'slug':meta['id'],'velocity':velocity,'leaf_threshold':leaf,'code_ast':'PASS','changed_cells':[i for i,(a,b) in enumerate(zip(original['cells'],nb['cells'])) if source(a)!=source(b)]}
plan={'task_id':'BIOHUB_TWO_WAVE_20260922_V01','source_commit':'1cf89f1f9380f005d98e9cb15ca9f5d80c4ebaca','source_sha256':EXPECTED,'candidates':results,'C_D':'WAITING_FOR_WAVE1','resource_policy':'Prioritize A; B only when live quota and active-job requirements permit.','budgets':{'notebooks':4,'save_and_run':5,'formal_submissions':4}}
(ROOT/'batch_plan.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
print(json.dumps(plan,indent=2))
