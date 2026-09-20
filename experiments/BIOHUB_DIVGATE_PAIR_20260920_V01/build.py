"""Deterministic append-only build from fixed G1; no execution or platform writes."""
import ast,hashlib,json,copy,difflib,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
basepath=R/'experiments/BIOHUB_SPRINT01_20260916/own/candidate.ipynb'; b=basepath.read_bytes();assert sha(b)=='de010e6ba142be0e01000093e061ef7d3388ddaa411185b40d26c63a3febe731'
nb=json.loads(b);assert len(nb['cells'])==13
for c in nb['cells']:assert c['cell_type']=='code';ast.parse(''.join(c['source']))
sources={name:(P/'official'/f'{name}.py').read_text() for name in ['metrics','division_metrics']}
converter=(P/'official/csv_to_geffs.py').read_text();func=next(n for n in ast.parse(converter).body if isinstance(n,ast.FunctionDef) and n.name=='build_graph_from_rows');sources['build_graph_from_rows']=ast.get_source_segment(converter,func)+'\n'
hashes={k:sha(v.encode()) for k,v in sources.items()};runtime=(P/'runtime.py').read_text();ast.parse(runtime)
manifest={'task_id':'BIOHUB_DIVGATE_PAIR_20260920_V01','g1_commit':'e9c7c63b896812660a78ec55fc3284c10f85e776','g1_notebook_sha256':sha(b),'runtime_sha256':sha(runtime.encode()),'official_commit':'075fc5f5a52d11077f9dc2b074644618f26939e2','official_hashes':hashes,'source_review':{'status':'FULL_NOTEBOOK_SOURCE_REVIEWED','cells':13,'all_original_cells_unchanged':True,'note':'原始proxy保留，仅为维持选参；新增测算使用官方入口'},'candidates':{}}
for arm,threshold,slug in [('A18',.18,'biohub-g1-divgate018-20260920'),('B22',.22,'biohub-g1-divgate022-20260920')]:
 out=copy.deepcopy(nb)
 source='import types as _dg_types\n_dg = _dg_types.ModuleType("divgate_runtime")\nexec('+repr(runtime)+', _dg.__dict__)\n_dg.run(globals(), '+repr(arm)+', '+repr(threshold)+', '+repr(sources)+', '+repr(hashes)+')\n'
 ast.parse(source);out['cells'].append({'cell_type':'code','execution_count':None,'metadata':{},'outputs':[],'source':source})
 d=P/arm;d.mkdir(exist_ok=True);write(d/'candidate.ipynb',out)
 assert out['cells'][:13]==nb['cells']
 meta=json.loads((basepath.parent/'kernel-metadata.json').read_text());meta.update(id='sailorren/'+slug,title=slug,code_file='candidate.ipynb');write(d/'kernel-metadata.json',meta)
 (d/'production.diff').write_text(''.join(difflib.unified_diff([],source.splitlines(True),fromfile='G1 unchanged original cells',tofile=arm+' added cell13')))
 manifest['candidates'][arm]={'ref':meta['id'],'final_threshold':threshold,'final_config_rule':'deepcopy(PP_BASE_CONFIG) updated by original selected_config, then only DEEPCENTER_SAFE_DIV_THRESHOLD overridden','notebook_sha256':sha((d/'candidate.ipynb').read_bytes()),'metadata_sha256':sha((d/'kernel-metadata.json').read_bytes()),'inputs':{k:meta[k] for k in ['dataset_sources','kernel_sources','competition_sources','docker_image','machine_shape']},'status':'BUILT_NOT_RUN'}
manifest['weights']={'gate':'0a1f9b93bb529e70f4f7c2ba0907eea8b4cecd2befccc8ba1fb75e569edf77a0','primary':'12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771','secondary':'9bac2fa0dadc4a6fc1899e0caf187f4b553e0a7cd90ba1261a68b35ffe9e305f','deepcenter':'8040999a92f6b7bbd98fa8cf458141e045c0f9ad7c936bdb3b18e1f7edafe2a0'}
manifest['V1_read_only']={'kernel_id':134988494,'version':1,'script_version_id':351084196,'submission_id':56375774,'status':'SCORE_PENDING','public':None,'source':'preflight_initial.json'}
write(P/'candidate_manifest.json',manifest);print(json.dumps({'status':'BUILT_NOT_RUN','candidates':{k:v['notebook_sha256'] for k,v in manifest['candidates'].items()}}))
