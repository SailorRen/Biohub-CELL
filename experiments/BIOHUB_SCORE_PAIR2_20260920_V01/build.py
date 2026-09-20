import ast,copy,difflib,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];G1='e9c7c63b896812660a78ec55fc3284c10f85e776'
def fixed(path):return subprocess.check_output(['git','show',G1+':'+path],cwd=R)
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
base=fixed('experiments/BIOHUB_SPRINT01_20260916/own/candidate.ipynb');assert sha(base)=='de010e6ba142be0e01000093e061ef7d3388ddaa411185b40d26c63a3febe731';nb=json.loads(base);assert len(nb['cells'])==13
old=P.parent/'BIOHUB_DIVGATE_PAIR_20260920_V01';prior=json.loads((old/'candidate_manifest.json').read_text());runtime=(P/'runtime.py').read_text();ast.parse(runtime)
raw=(old/'official/csv_to_geffs.py').read_text();fn=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='build_graph_from_rows');reader=ast.get_source_segment(raw,fn)+'\n';rh=sha(reader.encode());assert rh==prior['official_hashes']['build_graph_from_rows']
keys=ast.literal_eval(next(n.value for n in ast.parse(''.join(nb['cells'][9]['source'])).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PP_SWEEP_KEYS' for t in n.targets)))
outmanifest={}
for arm,slug in [('S50','biohub-g1-secondary050-20260920'),('G58','biohub-g1-gap058-20260920')]:
 out=copy.deepcopy(nb)
 if arm=='S50':
  s=''.join(out['cells'][3]['source']);target='os.environ["BIOHUB_SECONDARY_DETECTION_WEIGHT"] = "0.80"';assert s.count(target)==1;s=s.replace(target,target.replace('0.80','0.50'));out['cells'][3]['source']=s
 # Add a measurement to the existing worker retention record, without changing its decision.
 s=''.join(out['cells'][4]['source']);target='                            "minimum_retention": float(minimum_retention),';assert s.count(target)==1;s=s.replace(target,target+'\n                            "secondary_detection_weight": float(secondary_detection_weight),');out['cells'][4]['source']=s
 setup='import types as _pair2_types\n_pair2 = _pair2_types.ModuleType("pair2_runtime")\nexec('+repr(runtime)+', _pair2.__dict__)\n_pair2.install(globals(), '+repr(arm)+', '+repr(keys)+')\n'
 s=''.join(out['cells'][5]['source']);target='write_test_submission("base")';assert s.count(target)==1;out['cells'][5]['source']=s.replace(target,setup+'\n'+target)
 out['cells'].append({'cell_type':'code','execution_count':None,'metadata':{},'outputs':[],'source':'_pair2.finish(globals(), '+repr(arm)+', '+repr(reader)+', '+repr(rh)+')\n'})
 for c in out['cells']:ast.parse(''.join(c['source']))
 d=P/arm;d.mkdir(exist_ok=True);write(d/'candidate.ipynb',out);meta=json.loads(fixed('experiments/BIOHUB_SPRINT01_20260916/own/kernel-metadata.json'));meta.update(id='sailorren/'+slug,title=slug,code_file='candidate.ipynb');write(d/'kernel-metadata.json',meta)
 diff=''.join(difflib.unified_diff('\n'.join(''.join(c['source']) for c in nb['cells']).splitlines(True),'\n'.join(''.join(c['source']) for c in out['cells']).splitlines(True),fromfile='fixed G1',tofile=arm));(d/'source.diff').write_text(diff)
 outmanifest[arm]={'ref':meta['id'],'notebook_sha256':sha((d/'candidate.ipynb').read_bytes()),'metadata_sha256':sha((d/'kernel-metadata.json').read_bytes()),'inputs':prior['candidates']['A18']['inputs'],'change':{'BIOHUB_SECONDARY_DETECTION_WEIGHT':[.8,.5]} if arm=='S50' else {'final GAP_CLOSE_UM':[5.0,5.8]},'changed_original_cells':[3,4,5] if arm=='S50' else [4,5]}
write(P/'build_result.json',{'candidates':outmanifest,'runtime_sha256':sha(runtime.encode()),'official_reader_sha256':rh,'all_code_cells_ast':'PASS','g1_sha256':sha(base)})
print('S50/G58 built from exact G1; all code cells parse')
