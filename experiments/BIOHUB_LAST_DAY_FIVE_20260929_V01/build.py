"""Five fixed single-factor variants from the exact 0.958 parent; no platform writes."""
from pathlib import Path
import json,hashlib,copy,difflib,ast
P=Path(__file__).resolve().parent;R=P.parents[1];B=R/'experiments/BIOHUB_FINAL_ILP_READMIT_20260928_V01/DIV04_READMIT940';TASK=P.name
raw=(B/'candidate.ipynb').read_bytes();assert hashlib.sha256(raw).hexdigest()=='ac3651a886a11ecab5e89e8e2a80e10f8b4547b7b4775a6a75e437d8e2ea8035'
base=json.loads(raw);assert len(base['cells'])==13
CANDIDATES=[('DIV06_READMIT940',.6,.94,9.),('DIV03_READMIT940',.3,.94,9.),('DIV04_READMIT930',.4,.93,9.),('DIV04_READMIT94625',.4,.94625,9.),('DIV04_READMIT940_RL8',.4,.94,8.)]
for c in base['cells']:ast.parse(''.join(c['source']))
def once(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b,1)
def make(arm,ilp,readmit,relaxed=9.):
 nb=copy.deepcopy(base);s=[''.join(c['source']) for c in nb['cells']]
 for key,old,new in [('ILP_DIVISION_WEIGHT',.4,ilp),('READMIT_MIN_SCORE',.94,readmit),('MOTION_RELINK_RELAXED_UM',9.,relaxed)]:
  if old==new:continue
  s[0]=once(s[0],f'os.environ["BIOHUB_{key}"] = "{old}"',f'os.environ["BIOHUB_{key}"] = "{new}"')
  if key=='MOTION_RELINK_RELAXED_UM':
   s[1]=once(s[1],'_EXPECTED_NUMERIC = {',f'_EXPECTED_NUMERIC = {{\n    "BIOHUB_{key}": {new},')
  else:s[1]=once(s[1],f'"BIOHUB_{key}": {old},',f'"BIOHUB_{key}": {new},')
  s[12]=once(s[12],f'{key} == {old}',f'{key} == {new}')
 s[12]=once(s[12],"_TRIO_ARM = 'DIV04_READMIT940'",f'_TRIO_ARM = {arm!r}')
 s[12]=once(s[12],"task='BIOHUB_FINAL_ILP_READMIT_20260928_V01'",f'task={TASK!r}')
 for c,t in zip(nb['cells'],s):c['source']=t;ast.parse(t)
 m=json.loads((B/'kernel-metadata.json').read_text());slug='biohub-last-'+arm.lower().replace('_','-')+'-20260929';m.update(id='sailorren/'+slug,title=slug)
 return nb,m
if __name__=='__main__':
 assert not (P/'platform_ledger.json').exists(),'Refuse ledger overwrite'
 rows=[]
 for arm,ilp,rd,rl in CANDIDATES:
  d=P/arm;d.mkdir();nb,m=make(arm,ilp,rd,rl);code=json.dumps(nb,ensure_ascii=False,indent=1)+'\n';(d/'candidate.ipynb').write_text(code);(d/'kernel-metadata.json').write_text(json.dumps(m,indent=2)+'\n');h=hashlib.sha256(code.encode()).hexdigest()
  (d/'source.diff').write_text(''.join(difflib.unified_diff('\n'.join(''.join(c['source']) for c in base['cells']).splitlines(True),'\n'.join(c['source'] for c in nb['cells']).splitlines(True),fromfile='DIV04_READMIT940',tofile=arm)))
  (d/'build_receipt.json').write_text(json.dumps({'source_sha256':h,'baseline_sha256':hashlib.sha256(raw).hexdigest(),'ilp':ilp,'readmit':rd,'relaxed':rl},indent=2)+'\n')
  rows.append(dict(candidate_id=arm,effective_config=dict(ilp=ilp,readmit=rd,det=.955,relaxed_um=rl,flow_relaxed=0.,velocity=.5,g1=False),planned_kernel_ref=m['id'],kernel_ref=None,kernel_id=None,version=None,script_version_id=None,submission_id=None,source_sha256=h,status='LOCAL_PREPARED',public_score=None,direct_error=None,events=[]))
 ledger=dict(task_id=TASK,stage='LOCAL_PREPARED',candidates=rows,run_request_count=0,full_run_count=0,accepted_full_run_count=0,formal_request_count=0,engineering_spare_count=0,formal_request_cap=5,maximum_batch_gpu_concurrency=2,final_selection_changed=False)
 (P/'platform_ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
 print('Five fixed candidates prepared; platform writes 0')
