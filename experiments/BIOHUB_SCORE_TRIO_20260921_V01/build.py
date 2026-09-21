"""Three frozen single interventions, exact G1 source and existing runtime helpers."""
import ast,copy,difflib,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];G1='e9c7c63b896812660a78ec55fc3284c10f85e776'
def sha(b):return hashlib.sha256(b).hexdigest()
def fixed(p):return subprocess.check_output(['git','show',G1+':'+p],cwd=R)
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def replace(s,a,b):
 assert s.count(a)==1,(a,s.count(a))
 return s.replace(a,b,1)
def assignment(s,name):
 n=next(x for x in ast.parse(s).body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in x.targets))
 return n,ast.literal_eval(n.value)
base=fixed('experiments/BIOHUB_SPRINT01_20260916/own/candidate.ipynb');assert sha(base)=='de010e6ba142be0e01000093e061ef7d3388ddaa411185b40d26c63a3febe731'
nb=json.loads(base);runtime=(P/'runtime.py').read_text();ast.parse(runtime)
prior=json.loads((P.parent/'BIOHUB_DIVGATE_PAIR_20260920_V01/candidate_manifest.json').read_text())
raw=(P.parent/'BIOHUB_DIVGATE_PAIR_20260920_V01/official/csv_to_geffs.py').read_text();fn=next(x for x in ast.parse(raw).body if isinstance(x,ast.FunctionDef) and x.name=='build_graph_from_rows');reader=ast.get_source_segment(raw,fn)+'\n';rh=sha(reader.encode());assert rh==prior['official_hashes']['build_graph_from_rows']
_,keys=assignment(''.join(nb['cells'][9]['source']),'PP_SWEEP_KEYS')
arms={'D960':('biohub-g1-det0960-20260921','BIOHUB_DET_THRESHOLD',.965,.960),'H30':('biohub-g1-harmonic030-20260921','BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT',.15,.30),'R00':('biohub-g1-rescue-trigger000-20260921','SHORT_TRACK_RESCUE_TRIGGER_REMOVED_FRAC',.10,.00)}
manifest={}
for arm,(slug,key,before,after) in arms.items():
 out=copy.deepcopy(nb)
 if arm!='R00':
  s=''.join(out['cells'][0]['source']);s=replace(s,f'os.environ["{key}"] = "'+('0.965' if arm=='D960' else '0.15')+'"',f'os.environ["{key}"] = "'+('0.960' if arm=='D960' else '0.30')+'"');out['cells'][0]['source']=s
  s=''.join(out['cells'][1]['source']);out['cells'][1]['source']=replace(s,f'"{key}": {before}',f'"{key}": {after}')
 s=''.join(out['cells'][4]['source'])
 if arm=='H30':
  s=replace(s,'_bidirectional_weight_guard, 0.15,','_bidirectional_weight_guard, 0.30,')
  s=replace(s,'"expected_bidirectional_weight": 0.15,','"expected_bidirectional_weight": 0.30,')
 s=replace(s,'                            "minimum_retention": float(minimum_retention),','                            "minimum_retention": float(minimum_retention),\n                            "secondary_detection_weight": float(secondary_detection_weight),\n                            "det_threshold": float(cfg.det_threshold),')
 n,bi=assignment(s,'_bi_new')
 hook='''            if not globals().get("_trio_harmonic_recorded", False):
                import json as _trio_json
                from pathlib import Path as _TrioPath
                _TrioPath("/kaggle/working/trio_harmonic_" + str(os.getpid()) + ".json").write_text(_trio_json.dumps({"weight": _bidirectional_weight, "mode": "harmonic_probability"}))
                globals()["_trio_harmonic_recorded"] = True
'''
 bi=replace(bi,'            if _bidirectional_weight > 0.0:\n',hook+'            if _bidirectional_weight > 0.0:\n')
 s=replace(s,ast.get_source_segment(s,n),'_bi_new = '+repr(bi));out['cells'][4]['source']=s
 s=''.join(out['cells'][5]['source'])
 s=replace(s,'    removed_before_rescue = len(nodes_by_id) - len(keep)\n','''    removed_before_rescue = len(nodes_by_id) - len(keep)
    _trio_rescue_row = {"removed_before_rescue": removed_before_rescue, "removed_frac": removed_before_rescue / max(len(nodes_by_id), 1), "threshold": SHORT_TRACK_RESCUE_TRIGGER_REMOVED_FRAC, "triggered": False, "budget": 0, "rescued_nodes": 0}
    _trio_rescue_rows.append(_trio_rescue_row)
''')
 s=replace(s,'            stats["short_track_rescue_triggered"] = 1','            _trio_rescue_row.update(triggered=True, budget=budget)\n            stats["short_track_rescue_triggered"] = 1')
 s=replace(s,'            stats["short_track_rescue_nodes"] = rescued_nodes','            _trio_rescue_row["rescued_nodes"] = rescued_nodes\n            stats["short_track_rescue_nodes"] = rescued_nodes')
 setup='import types as _trio_types\n_trio = _trio_types.ModuleType("trio_runtime")\nexec('+repr(runtime)+', _trio.__dict__)\n_trio.install(globals(), '+repr(arm)+', '+repr(keys)+')\n'
 out['cells'][5]['source']=replace(s,'write_test_submission("base")',setup+'\nwrite_test_submission("base")')
 out['cells'].append({'cell_type':'code','execution_count':None,'metadata':{},'outputs':[],'source':'_trio.finish(globals(), '+repr(arm)+', '+repr(reader)+', '+repr(rh)+')\n'})
 for c in out['cells']:ast.parse(''.join(c['source']))
 d=P/arm;d.mkdir(exist_ok=True);write(d/'candidate.ipynb',out)
 meta=json.loads(fixed('experiments/BIOHUB_SPRINT01_20260916/own/kernel-metadata.json'));meta.update(id='sailorren/'+slug,title=slug,code_file='candidate.ipynb');write(d/'kernel-metadata.json',meta)
 (d/'source.diff').write_text(''.join(difflib.unified_diff('\n'.join(''.join(c['source']) for c in nb['cells']).splitlines(True),'\n'.join(''.join(c['source']) for c in out['cells']).splitlines(True),fromfile='fixed G1',tofile=arm)))
 manifest[arm]={'ref':meta['id'],'notebook_sha256':sha((d/'candidate.ipynb').read_bytes()),'metadata_sha256':sha((d/'kernel-metadata.json').read_bytes()),'inputs':prior['candidates']['A18']['inputs'],'change':{key:[before,after]},'changed_original_cells':[4,5] if arm=='R00' else [0,1,4,5]}
write(P/'build_result.json',{'candidates':manifest,'runtime_sha256':sha(runtime.encode()),'official_reader_sha256':rh,'all_code_cells_ast':'PASS','g1_sha256':sha(base)})
print('D960/H30/R00 built from exact G1')
