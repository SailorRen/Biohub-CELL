"""Only transplant exact formal F1 flow into frozen D960; retain existing receipts."""
import ast,copy,difflib,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent; R=P.parents[1]; T=P.parent/'BIOHUB_SCORE_TRIO_20260921_V01'
def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
base=subprocess.check_output(['git','show','1cf89f1f9380f005d98e9cb15ca9f5d80c4ebaca:experiments/BIOHUB_SCORE_TRIO_20260921_V01/D960/candidate.ipynb'],cwd=R)
assert sha(base)=='b12568e27ea5a8c66942a6301c2c80d037fdffe43f338a23a86266f80a02d192'
nb=json.loads(base);out=copy.deepcopy(nb);src=''.join(nb['cells'][5]['source']);flow=(P/'flow_patch.py').read_text();motion=next(ast.get_source_segment(src,n) for n in ast.parse(src).body if isinstance(n,ast.FunctionDef) and n.name=='motion_relink_edges')
f1=json.loads(Path('/private/tmp/df960-private/f1_platform.ipynb').read_text());f1src=''.join(f1['cells'][5]['source'])
f1motion=next(ast.get_source_segment(f1src,n) for n in ast.parse(f1src).body if isinstance(n,ast.FunctionDef) and n.name=='motion_relink_edges');assert motion==f1motion
embedded=[n.args[0].value for n in ast.walk(ast.parse(f1src)) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='exec' and n.args and isinstance(n.args[0],ast.Constant) and isinstance(n.args[0].value,str) and 'neighbour_predictions' in n.args[0].value];assert embedded==[flow]
inject="\nimport types as _f1_types\n_f1_module=_f1_types.ModuleType('flow_patch')\nexec("+repr(flow)+",_f1_module.__dict__)\nF1_CONFIG=_f1_module.CONFIG\nF1_ORIGINAL_MOTION=_f1_module.install(globals(),"+repr(motion)+")\n"
assert src.count('write_test_submission("base")')==1
out['cells'][5]['source']=src.replace('write_test_submission("base")',inject+'\nwrite_test_submission("base")')
# Compact measurement around each test postprocess call, without changing flow implementation.
audit='''
_df_original_filter=filter_output_graph
_df_test_dir=TEST_DIR
_df_flow_calls=[]
def _df_filter(nodes,edges,**kw):
    start=len(F1_CALLS)
    result=_df_original_filter(nodes,edges,**kw)
    if TEST_DIR==_df_test_dir:
        rows=F1_CALLS[start:]
        _df_flow_calls.append(dict(stem=kw['dataset'],enabled=F1_ENABLED,config=dict(F1_CONFIG),motion_calls=len(rows),predictions=sum(r['prediction_count'] for r in rows)))
    return result
filter_output_graph=_df_filter
'''
out['cells'][5]['source']=out['cells'][5]['source'].replace('write_test_submission("base")',audit+'\nwrite_test_submission("base")')
finish='''
assert F1_ENABLED and F1_CALLS and _df_flow_calls, 'DF960_FLOW_NOT_ACTIVE'
assert F1_CONFIG == dict(k=12,radius_um=40.0,exclude_um=1.5,min_global_seeds=4,iterations=1)
_df_latest={r['stem']:r for r in _df_flow_calls}
assert set(_df_latest)==set(test_stems)
assert all(r['enabled'] and r['motion_calls']>0 for r in _df_latest.values())
_df_receipt=dict(arm='DF960',flow_patch_sha256=FLOW_PATCH_SHA256,flow_config=F1_CONFIG,flow_test_calls=_df_flow_calls,final_flow_calls=_df_latest,
    final_csv_sha256=_trio.sha(SUBMISSION_PATH),det_threshold=DET_THRESHOLD,selected_label=selected_label,selected_config=selected_config,
    source='F1 V1 SV351084196 + D960 V1 SV351441983',training_calls=0)
_trio.save(WORKING_DIR/'df960_flow_receipt.json',_df_receipt)
print('DF960_FINAL',_df_receipt['final_csv_sha256'],flush=True)
'''
out['cells'][-1]['source']=''.join(out['cells'][-1]['source'])+'\nFLOW_PATCH_SHA256='+repr(sha(flow.encode()))+'\n'+finish
for c in out['cells']:ast.parse(''.join(c['source']))
assert all(out['cells'][i]==nb['cells'][i] for i in range(len(nb['cells'])) if i not in [5,13])
d=P/'DF960';d.mkdir(exist_ok=True);save(d/'candidate.ipynb',out)
meta=json.loads((T/'D960/kernel-metadata.json').read_text());meta.update(id='sailorren/biohub-df960-flow-20260921',title='Biohub DF960 Flow 20260921');save(d/'kernel-metadata.json',meta)
prior=json.loads((T/'batch_manifest.json').read_text());candidate=copy.deepcopy(prior['candidates']['D960']);candidate.update(ref=meta['id'],notebook_sha256=sha((d/'candidate.ipynb').read_bytes()),metadata_sha256=sha((d/'kernel-metadata.json').read_bytes()),change={'F1_FLOW':True},changed_original_cells=[5,13])
save(P/'batch_manifest.json',dict(task_id='BIOHUB_DF960_20260921_V01',task_commit='ed143c02ddf97f9dd6e75ab256bf41383e4e4256',candidates={'DF960':candidate},weights=prior['weights'],official_reader_sha256=prior['official_reader_sha256'],flow_patch_sha256=sha(flow.encode()),f1_source_sha256=sha(Path('/private/tmp/df960-private/f1_platform.ipynb').read_bytes()),f1_sv=351084196,d960_source_sha256=sha(base),budgets=dict(new_private_notebooks=1,save_and_run=2,formal_submission=1,training=0,dataset_write=0,final_selection_change=0)))
(P/'source.diff').write_text(''.join(difflib.unified_diff(src.splitlines(True),out['cells'][5]['source'].splitlines(True),fromfile='D960_cell5',tofile='DF960_cell5')))
print('DF960 built; changed cells 5/13 only; exact F1 motion and patch verified')
