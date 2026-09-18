"""Build and freeze artifacts only; never execute Notebook code locally."""
import ast,hashlib,json,difflib,textwrap
from pathlib import Path
from flow_patch import CONFIG,patch_motion_source
P=Path(__file__).resolve().parent;R=P.parents[1];OLD=P.parent/'BIOHUB_SPRINT01_20260916'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
nb=json.loads((OLD/'own/candidate.ipynb').read_text());base=[''.join(c['source']) for c in nb['cells']]
assert sha(OLD/'own/candidate.ipynb')=='de010e6ba142be0e01000093e061ef7d3388ddaa411185b40d26c63a3febe731'
rules=json.loads((OLD/'selection_rules.json').read_text())
motion=next(ast.get_source_segment(base[5],n) for n in ast.parse(base[5]).body if isinstance(n,ast.FunctionDef) and n.name=='motion_relink_edges')
patch=(P/'flow_patch.py').read_text()
inject="\nimport types as _f1_types\n_f1_module=_f1_types.ModuleType('flow_patch')\nexec("+repr(patch)+",_f1_module.__dict__)\nF1_CONFIG=_f1_module.CONFIG\nF1_ORIGINAL_MOTION=_f1_module.install(globals(),"+repr(motion)+")\n"
post=base[5].replace('write_test_submission("base")',inject)
assert post!=base[5]
scoring=''.join(json.loads((OLD/'diagnostic.ipynb').read_text())['cells'][5]['source'])
anchor='        er = metrics.evaluate(pred, gt, scale=scale, max_distance=radius)'
capture='''
        # Read-only attribution from the exact official matcher, preserving backend order.
        scope['F1_EDGE_STATUS'] = {}
        ordered_ids = list(pred_nodes_plain)
        id_back = dict(zip(list(pred.node_ids()), ordered_ids, strict=True))
        if pred.num_edges():
            for item in metrics._evaluate_matched_graph(pred,gt).iter_rows(named=True):
                pair = (id_back[int(item[td.DEFAULT_ATTR_KEYS.EDGE_SOURCE])],id_back[int(item[td.DEFAULT_ATTR_KEYS.EDGE_TARGET])])
                scope['F1_EDGE_STATUS'][pair] = 'TP' if item[td.DEFAULT_ATTR_KEYS.MATCHED_EDGE_MASK] else ('FP' if item['pred_valid'] else 'UNKNOWN')
'''
assert scoring.count(anchor)==1
scoring=scoring.replace(anchor,anchor+'\n'+capture)
manifest=json.loads((OLD/'replay_cache_manifest.json').read_text())['files']
raw_manifest=[{k:x[k] for k in ['name','sha256']} for x in manifest if x['source_ref']=='sailorren/biohub-division-train-20260914' and x['name'].startswith('tracking_repo/predictions/')]
stages=json.loads((OLD/'output_v1/stages.json').read_text())
raw_hashes={r['sample']:r['raw_hash'] for r in stages}
assert set(raw_hashes)==set(rules['samples']) and raw_manifest
const='FIXED_STEMS='+repr(rules['samples'])+'\nFROZEN_CONFIG='+repr(rules['configuration'])+'\nRAW_MANIFEST='+repr(raw_manifest)+'\nEXPECTED_RAW_HASHES='+repr(raw_hashes)+'\n'
diag=[*base[:4],post,scoring,const+(P/'diagnostic_runtime.py').read_text()]
prod=list(base);prod[5]=base[5].replace('write_test_submission("base")',inject+'\nwrite_test_submission("base")')
prod.append('''
assert F1_ENABLED and F1_CALLS, 'F1_GLOBALLY_DISABLED'
import hashlib
_f1_receipt=dict(status='ORDINARY_OUTPUT_VERIFIED',flow_config=F1_CONFIG,selected_label=selected_label,selected_config=selected_config,
    schema_valid=True,test_stems=test_stems,flow_calls=F1_CALLS,training_calls=0,
    submission_sha256=hashlib.sha256(SUBMISSION_PATH.read_bytes()).hexdigest(),public_score=None)
(WORKING_DIR/'f1_production_receipt.json').write_text(json.dumps(_f1_receipt,indent=2)+'\\n')
''')
for phase,cells in [('diagnostic',diag),('production',prod)]:
 d=P/phase;d.mkdir(exist_ok=True)
 for s in cells:ast.parse(s)
 output=dict(cells=[dict(cell_type='code',source=s,execution_count=None,outputs=[],metadata={}) for s in cells],metadata=nb['metadata'],nbformat=4,nbformat_minor=5)
 write(d/'candidate.ipynb',output)
 meta=json.loads((OLD/'own/kernel-metadata.json').read_text());tag='diag' if phase=='diagnostic' else 'prod'
 meta.update(id=f'sailorren/biohub-f1-flow-{tag}-20260918',title=f'Biohub F1 Flow {tag} 20260918',code_file='candidate.ipynb')
 write(d/'kernel-metadata.json',meta)
(P/'motion.diff').write_text(''.join(difflib.unified_diff(motion.splitlines(True),patch_motion_source(motion).splitlines(True),fromfile='G1_motion',tofile='F1_motion')))
write(P/'build_receipt.json',dict(status='BUILT_NOT_RUN',patch_sha256=sha(P/'flow_patch.py'),diagnostic_sha256=sha(P/'diagnostic/candidate.ipynb'),production_sha256=sha(P/'production/candidate.ipynb'),
  original_production_cells_unchanged=[i for i in range(len(base)) if i!=5],selector_unchanged=True,training_calls=0,raw_manifest_files=len(raw_manifest)))
print((P/'build_receipt.json').read_text())
