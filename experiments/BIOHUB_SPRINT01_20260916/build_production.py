"""Build only the already-qualified winner; original Forge selector and all inference cells retained."""
import ast,hashlib,json,difflib
from pathlib import Path
from division_patch import patch_safe_div
P=Path(__file__).resolve().parent;R=P.parents[1];D=P/'own';D.mkdir(exist_ok=True)
results=json.loads((P/'output_v1/diagnostic_results.json').read_text());arm=results['selected'];assert arm in ['G1','R1'] and results['pass'][arm]
rules=json.loads((P/'selection_rules.json').read_text());nb=json.loads((R/'experiments/TARGET950_20260914/baseline/candidate.ipynb').read_text());base=[''.join(c['source']) for c in nb['cells']]
assert len(base)==12 and all(c['cell_type']=='code' for c in nb['cells'])
s=base[5];old=next(ast.get_source_segment(s,n) for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='add_safe_divisions_postlink')
patched=patch_safe_div(old);s=s.replace(old,old+'\n_sprint_original_safe_div=add_safe_divisions_postlink\n'+patched+'\n_sprint_patched_safe_div=add_safe_divisions_postlink\n')
setup=(P/'saved_inference.py').read_text()+'\n'+(P/'division_patch.py').read_text()+'\nSPRINT_ARM='+repr(arm)+'\nVALIDATION_EMBRYO_MAP='+repr({stem:stem.split('_')[0] for stem in rules['samples']})+'\nSPRINT_PP_KEYS='+repr(list(rules['configuration']))+'\n'+(P/'production_module.py').read_text()+'\n'
assert s.count('write_test_submission("base")')==1;s=s.replace('write_test_submission("base")',setup+'\nwrite_test_submission("base")')
nb['cells'][5]['source']=s
receipt_code='''
_sprint_test_calls=[r for r in SPRINT_CALLS if r['model']=='final']
assert _sprint_test_calls and sum(r['classifier_calls'] for r in _sprint_test_calls)>0,'SPRINT_NOT_USED'
assert any(r['added_edges'] or r['lost_edges'] for r in _sprint_test_calls),'SPRINT_NO_ORDINARY_GRAPH_CHANGE'
_sprint_receipt={'arm':SPRINT_ARM,'weight_sha256':_SPRINT_WEIGHT_SHA,'training_calls':0,'selected_label':selected_label,'selected_config':selected_config,'calls':len(SPRINT_CALLS),'test_calls':len(_sprint_test_calls),'test_datasets':sorted({r['dataset'] for r in _sprint_test_calls}),'classifier_calls':sum(r['classifier_calls'] for r in _sprint_test_calls),'changed_calls':sum(bool(r['added_edges'] or r['lost_edges']) for r in _sprint_test_calls),'submission_sha256':_sprint_hashlib.sha256(SUBMISSION_PATH.read_bytes()).hexdigest(),'run_stats_sha256':_sprint_hashlib.sha256(RUN_STATS_PATH.read_bytes()).hexdigest(),'hidden_configuration':'UNKNOWN'}
(WORKING_DIR/'sprint_production_receipt.json').write_text(_sprint_json.dumps(_sprint_receipt,indent=2)+'\\n')
print('SPRINT_PRODUCTION_COMPLETE',_sprint_receipt,flush=True)
'''
nb['cells'].append({'cell_type':'code','execution_count':None,'metadata':{},'outputs':[],'source':receipt_code})
for c in nb['cells']:ast.parse(''.join(c['source']));c['outputs']=[];c['execution_count']=None
assert all(''.join(nb['cells'][i]['source'])==base[i] for i in range(12) if i!=5)
(D/'candidate.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=1)+'\n')
meta=json.loads((P/'kernel-metadata.json').read_text());meta.update(id='sailorren/biohub-sprint01-own-'+arm.lower()+'-20260916',title='Biohub Sprint01 '+arm+' Frozen Inference 20260916',code_file='candidate.ipynb');(D/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
(D/'production.diff').write_text(''.join(difflib.unified_diff(base[5].splitlines(True),s.splitlines(True),fromfile='Forge947_cell5',tofile='Sprint01_'+arm+'_cell5')))
x={'arm':arm,'source_sha256':hashlib.sha256((D/'candidate.ipynb').read_bytes()).hexdigest(),'unchanged_original_cells':[i for i in range(12) if i!=5],'modified_original_cells':[5],'added_cells':['runtime_receipt'],'original_selector_unchanged':True,'production_config':'original Forge automatic selector retained; not frozen diagnostic tight55','weight_sha256':'0a1f9b93bb529e70f4f7c2ba0907eea8b4cecd2befccc8ba1fb75e569edf77a0'};(D/'build_receipt.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps(x))
