"""Independent stdlib CSV validation adapted from the existing two-wave checker."""
import argparse,csv,hashlib,json,math,re
from collections import Counter
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('arm',choices=['XV25','XG95','XV25G95']);p.add_argument('directory');a=p.parse_args()
P=Path(__file__).resolve().parent;D=Path(a.directory)
r=json.loads((D/'trio_receipt.json').read_text());assert r['task']=='BIOHUB_XR0_TRANSFER_TRIO_20260926_V01' and r['arm']==a.arm
vel=.5 if a.arm=='XG95' else .25;gate=a.arm!='XV25'
assert r['velocity']==vel and r['g1']==gate and r['csv_validation']=='PASS'
assert r['head_sha256']=='625a0d9340f48193f2ec294fc2d81c5bb3c03087eab78ef0ae998a9c4c7da00c'
assert r['cuda_devices'] and all('T4' in d for d in r['cuda_devices'])
if gate:assert r['gate_sha256']=='0a1f9b93bb529e70f4f7c2ba0907eea8b4cecd2befccc8ba1fb75e569edf77a0' and r['g1_threshold']==.95
cols=['id','dataset','row_type','node_id','t','z','y','x','source_id','target_id'];groups={};n=0
with (D/'submission.csv').open(newline='') as f:
 rd=csv.DictReader(f);assert rd.fieldnames==cols
 for row in rd:
  for k in cols:
   if k not in ['dataset','row_type']: assert re.fullmatch(r'-?\d+',row[k]);row[k]=int(row[k])
  assert row['id']==n;n+=1;ns,es=groups.setdefault(row['dataset'],({},[]))
  if row['row_type']=='node':
   assert row['node_id'] not in ns and min(row[k] for k in ['node_id','t','z','y','x'])>=0
   assert row['source_id']==row['target_id']==-1
   ns[row['node_id']]={k:row[k] for k in ['t','z','y','x']}
  else:
   assert row['row_type']=='edge' and all(row[k]==-1 for k in ['node_id','t','z','y','x'])
   es.append((row['source_id'],row['target_id']))
assert set(groups)==set(r['expected_samples']) and n==r['csv_rows']
summary={}
for stem,(ns,es) in groups.items():
 assert ns and len(es)==len(set(es));inc=Counter();out=Counter()
 for u,v in es:
  assert u in ns and v in ns and ns[v]['t']==ns[u]['t']+1
  inc[v]+=1;out[u]+=1
 assert max(inc.values(),default=0)<=1 and max(out.values(),default=0)<=2
 summary[stem]={'nodes':len(ns),'edges':len(es)}
assert summary==r['graphs']
h=hashlib.sha256((D/'submission.csv').read_bytes()).hexdigest();assert h==r['csv_sha256']
for s in r['stats']:
 assert s['repair_fallback']==0 and s['deadline_degraded']==0
 assert s['trio_velocity_weight']==vel and math.isfinite(s['trio_velocity_consumed'])
 if gate:
  assert s['trio_g1_candidates']==s['trio_g1_finite_scores']+s['trio_g1_abstain']
  assert s['trio_g1_rejected']<=s['trio_g1_finite_scores']
# Zero consumption may be valid with complete flow coverage; the exact branch and live counters remain required.
# A zero admitted/rejected count is allowed; actual injection + telemetry are verified separately.
result={'arm':a.arm,'status':'PASS','csv_rows':n,'csv_sha256':h,'graphs':summary,'velocity_consumed':sum(s['trio_velocity_consumed'] for s in r['stats']),'repair_fallback':0,'deadline_degraded':0,'gate_candidates':sum(s['trio_g1_candidates'] for s in r['stats']) if gate else None,'gate_finite_scores':sum(s['trio_g1_finite_scores'] for s in r['stats']) if gate else None,'gate_rejected':sum(s['trio_g1_rejected'] for s in r['stats']) if gate else None}
(P/a.arm/'output_check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
