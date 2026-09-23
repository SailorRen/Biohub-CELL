"""Build three A-based templates; no platform, inference or old launcher calls."""
import ast,copy,difflib,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'BIOHUB_TWO_WAVE_20260922_V01'
TASK='BIOHUB_A950_THREE_CANDIDATES_20260923_V01'
PARAMS={'V0375':(.375,None),'V025-L020P':(.25,.20),'V025-L030P':(.25,.30)}
def sha(b):return hashlib.sha256(b).hexdigest()
def replace(s,a,b):
 assert s.count(a)==1,(a,s.count(a))
 return s.replace(a,b)
def source(c):return ''.join(c['source'])
def build():
 for a,h in [('A','393dc558654af6abffd8c786a1b8fd4065a58e5c2a6a0ba61af4b9d3b4be40df'),('B','03e4abd5c80b5724b959bc453352524e276bebcf9aa0c2ffa38f22442d3e2ceb')]:assert sha((OLD/a/'candidate.ipynb').read_bytes())==h
 base=json.loads((OLD/'A/candidate.ipynb').read_bytes());b=json.loads((OLD/'B/candidate.ipynb').read_bytes());ss=[source(c) for c in base['cells']]
 assert len(ss)==14 and all(source(c)==ss[i] for i,c in enumerate(b['cells']) if i!=0)
 result={}
 for arm,(velocity,leaf) in PARAMS.items():
  nb=copy.deepcopy(base);texts=ss.copy()
  texts[0]=replace(texts[0],'os.environ["BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT"] = "0.25"',f'os.environ["BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT"] = "{velocity}"')
  texts[0]=replace(texts[0],"WAVE_ARM = 'A'",f'WAVE_ARM = {arm!r}')
  texts[0]=replace(texts[0],'WAVE_EXPECTED_VELOCITY = 0.25',f'WAVE_EXPECTED_VELOCITY = {velocity!r}')
  texts[0]=replace(texts[0],'WAVE_LEAF_THRESHOLD = None',f'WAVE_LEAF_THRESHOLD = {leaf!r}')
  t=ast.parse(texts[5]);n=next(n for n in t.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='exec' and len(n.value.args)>1 and ast.unparse(n.value.args[1])=='_trio.__dict__')
  runtime=n.value.args[0].value
  runtime=replace(runtime,"g['MOTION_RELINK_VELOCITY_WEIGHT'] = .5; g['WAVE_LEAF_THRESHOLD'] = None","g['MOTION_RELINK_VELOCITY_WEIGHT'] = .25; g['WAVE_LEAF_THRESHOLD'] = None")
  runtime=replace(runtime,"row['baseline_replay_velocity'] = .5","row['baseline_replay_velocity'] = .25")
  runtime=replace(runtime,"task_id='BIOHUB_TWO_WAVE_20260922_V01',arm=g['WAVE_ARM'],mother='D960'",f"task_id={TASK!r},arm=g['WAVE_ARM'],mother='A950-V025'")
  runtime=replace(runtime,'Same raw inference, same selected configuration; candidate-disabled CPU replay, not an independent formal baseline.','Same raw inference and candidate-selected downstream configuration; velocity=0.25 leaf=None CPU replay, not independent A production or formal Public.')
  runtime=replace(runtime,"    receipt.update(task_id=", "    assert all(r['stats']['wave_leaf']['threshold'] == g['WAVE_LEAF_THRESHOLD'] for r in latest.values()), 'LEAF_THRESHOLD_NOT_CONSUMED'\n    receipt.update(task_id=")
  lines=texts[5].splitlines(keepends=True);lines[n.lineno-1:n.end_lineno]=['exec('+repr(runtime)+', _trio.__dict__)\n'];texts[5]=''.join(lines)
  for c,s in zip(nb['cells'],texts):ast.parse(s);c.update(source=s.splitlines(keepends=True),outputs=[],execution_count=None)
  nb['cells'].insert(0,{'cell_type':'markdown','metadata':{},'source':[f'# {arm}／未跑分\n复制到本人账号并保持私有；运行需T4×2、Internet关闭。不要直接提交母版。先把副本链接与Input/Settings截图交用户复核。\n'+('L030P须B有效Public≥同窗D960，或L020P有效Public≥同窗A后才运行。\n' if arm=='V025-L030P' else '')]})
  dest=ROOT/arm;dest.mkdir(exist_ok=True);raw=(json.dumps(nb,ensure_ascii=False,indent=1)+'\n').encode();(dest/'candidate.ipynb').write_bytes(raw)
  meta=json.loads((OLD/'A/kernel-metadata.json').read_text());slug='biohub-a950-'+arm.lower()+'-20260923';meta.update(id='sailorren/'+slug,title=slug,enable_gpu=False,machine_shape='None',keywords=[])
  (dest/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
  diff=''.join(difflib.unified_diff(''.join(ss).splitlines(True),''.join(texts).splitlines(True),fromfile='frozen_A',tofile=arm));(dest/'source.diff').write_text(diff)
  info={'arm':arm,'velocity':velocity,'leaf_threshold':leaf,'mother':'frozen A950-V025','notebook_sha256':sha(raw),'code_cell_count':14,'markdown_added':1,'changed_code_cells_zero_based':[i for i in range(14) if ss[i]!=texts[i]],'slug':meta['id'],'selector':'Original seven choices and combination rule unchanged','execution':'NOT_RUN','source_cells_sha256':[sha(s.encode()) for s in texts]};(dest/'parameters.json').write_text(json.dumps(info,indent=2)+'\n');result[arm]=info
 (ROOT/'build_receipt.json').write_text(json.dumps({'task':TASK,'candidates':result,'platform_writes':0},indent=2)+'\n')
 # Identity-only adaptation of the existing actual output checker; structural gates unchanged.
 checker=(OLD/'check_actual_csv.py').read_text().replace("from patch_support import invariant_graph","import sys\nsys.path.insert(0,str(Path(__file__).resolve().parent.parent/'BIOHUB_TWO_WAVE_20260922_V01'))\nfrom patch_support import invariant_graph")
 checker=checker.replace("choices=['A','B']",f'choices={list(PARAMS)!r}').replace("receipt['task_id']=='BIOHUB_TWO_WAVE_20260922_V01'",f"receipt['task_id']=={TASK!r}")
 checker=checker.replace("{'A':.25,'B':.5}",repr({k:v[0] for k,v in PARAMS.items()})).replace("{'A':None,'B':.30}",repr({k:v[1] for k,v in PARAMS.items()}))
 checker=checker.replace("Path(__file__).parent/'known_output_hashes.json'","Path(__file__).parent.parent/'BIOHUB_TWO_WAVE_20260922_V01/known_output_hashes.json'")
 checker=checker.replace('for other in a.other_check:',"for other in [str(Path(__file__).parent.parent/'BIOHUB_TWO_WAVE_20260922_V01/A/formal_precheck.json'),*a.other_check]:")
 (ROOT/'check_actual_csv.py').write_text(checker);ast.parse(checker)
 print(json.dumps(result,indent=2))
if __name__=='__main__':build()
