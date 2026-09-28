"""从冻结 R9D955 构建三份候选；仅定点参数、断言和只读计数。不可覆盖已有运行。"""
from pathlib import Path
import json,hashlib,copy,difflib,ast
P=Path(__file__).resolve().parent;R=P.parents[1];B=R/'experiments/BIOHUB_XRL9_TWO_WAVE_20260927_V01/R9D955';TASK=P.name
raw=(B/'candidate.ipynb').read_bytes();assert hashlib.sha256(raw).hexdigest()=='da53daf678724e920403350f4dde0e83b66163ef12d6a0b6efe28b58756c325c'
base=json.loads(raw);assert len(base['cells'])==13
for c in base['cells']:ast.parse(''.join(c['source']))
def once(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b,1)
def make(arm,ilp,readmit):
 nb=copy.deepcopy(base);s=[''.join(c['source']) for c in nb['cells']]
 s[0]=once(s[0],'os.environ["BIOHUB_ILP_DIVISION_WEIGHT"] = "1.2"',f'os.environ["BIOHUB_ILP_DIVISION_WEIGHT"] = "{ilp}"')
 s[0]=once(s[0],'os.environ["BIOHUB_READMIT_MIN_SCORE"] = "0.965"',f'os.environ["BIOHUB_READMIT_MIN_SCORE"] = "{readmit}"')
 s[1]=once(s[1],'_EXPECTED_NUMERIC = {',f'_EXPECTED_NUMERIC = {{\n    "BIOHUB_ILP_DIVISION_WEIGHT": {ilp},\n    "BIOHUB_READMIT_MIN_SCORE": {readmit},')
 anchor="    '            _ilp_t0 = _ilp_time.time()\\n'"
 proof="    '            print(f\"FINAL_ILP_CONSUMED {name} division_weight={cfg.ilp_division_weight}\", flush=True)\\n'\n"
 s[4]=once(s[4],anchor,proof+anchor)
 a='    if READMIT_RADIUS_UM <= 0:\n        return nodes_by_id'
 b='    stats["final_readmit_calls"] = stats.get("final_readmit_calls", 0) + 1\n    stats["final_readmit_threshold"] = READMIT_MIN_SCORE\n    stats.setdefault("final_readmit_passed", 0)\n'+a
 s[5]=once(s[5],a,b)
 a='            keep = (d <= READMIT_RADIUS_UM) & (peaks["score"] >= READMIT_MIN_SCORE)'
 s[5]=once(s[5],a,a+'\n            stats["final_readmit_passed"] += int(keep.sum())')
 s[12]=once(s[12],"_TRIO_ARM = 'R9D955'",f'_TRIO_ARM = {arm!r}')
 s[12]=once(s[12],'assert DET_THRESHOLD == 0.955 and READMIT_MIN_SCORE == 0.965',f'assert DET_THRESHOLD == 0.955 and READMIT_MIN_SCORE == {readmit}\nassert ILP_DIVISION_WEIGHT == {ilp}')
 s[12]=once(s[12],"task='BIOHUB_XRL9_TWO_WAVE_20260927_V01'",f'task={TASK!r}')
 s[12]=once(s[12],'det=DET_THRESHOLD,relaxed=', 'ilp=ILP_DIVISION_WEIGHT,readmit=READMIT_MIN_SCORE,det=DET_THRESHOLD,relaxed=')
 for c,t in zip(nb['cells'],s):c['source']=t;ast.parse(t)
 m=json.loads((B/'kernel-metadata.json').read_text());slug='biohub-final-'+arm.lower().replace('_','-')+'-20260928';m.update(id='sailorren/'+slug,title=slug)
 return nb,m
if __name__=='__main__':
 assert not (P/'platform_ledger.json').exists(),'账本已存在，拒绝覆盖'
 rows=[]
 for arm,ilp,rd in [('DIV04_READMIT940',.4,.94),('DIV04',.4,.965),('READMIT940',1.2,.94)]:
  D=P/arm;D.mkdir();nb,m=make(arm,ilp,rd);code=json.dumps(nb,ensure_ascii=False,indent=1)+'\n';(D/'candidate.ipynb').write_text(code);(D/'kernel-metadata.json').write_text(json.dumps(m,indent=2)+'\n')
  (D/'source.diff').write_text(''.join(difflib.unified_diff(''.join(''.join(c['source']) for c in base['cells']).splitlines(True),''.join(c['source'] for c in nb['cells']).splitlines(True),fromfile='R9D955',tofile=arm)))
  h=hashlib.sha256(code.encode()).hexdigest();(D/'build_receipt.json').write_text(json.dumps({'source_sha256':h,'baseline_sha256':hashlib.sha256(raw).hexdigest(),'ilp':ilp,'readmit':rd},indent=2)+'\n')
  rows.append(dict(candidate_id=arm,effective_config=dict(ilp=ilp,readmit=rd,det=.955,relaxed_um=9.,flow_relaxed=0.,velocity=.5,g1=False),planned_kernel_ref=m['id'],kernel_ref=None,kernel_id=None,version=None,script_version_id=None,submission_id=None,source_sha256=h,status='LOCAL_PREPARED',public_score=None,direct_error=None,events=[]))
 ledger=dict(task_id=TASK,stage='LOCAL_PREPARED',first_wave=[r['candidate_id'] for r in rows],second_wave=[],wave1=rows,wave2=[],run_request_count=0,full_run_count=0,accepted_full_run_count=0,formal_request_count=0,engineering_spare_count=0,formal_request_cap=5,maximum_batch_gpu_concurrency=2,final_selection_changed=False)
 (P/'platform_ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')
 print('三份静态候选已构建，无 Kaggle 写入')
