"""恢复固定3条边的标注辅助反事实。仅CPU图评分；--verify重新计算并比对。"""
import copy,hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2];B=P.parent;D=B/'diagnostic_rerun'
sys.path.insert(0,str(D))
from recompute import clean,plain,delta,load_official,load_scope,read_gt
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if __name__=='__main__':
 c=json.loads((P/'contract.json').read_text())
 for name,h in c['input_hashes'].items():assert sha(R/name)==h,name
 platform=json.loads((D/'diagnostic_platform.json').read_text());prior=json.loads((D/'verification.json').read_text());samples=json.loads((B/'contract.json').read_text())['samples'];raw=(R/platform['log']['local_path']).parent
 metrics=load_official();scope,_,_=load_scope(R/'experiments/TARGET950_20260914/baseline/candidate.ipynb',metrics)
 rows=copy.deepcopy(prior['per_sample']['H1']);checks=[];changed=[]
 for s in samples:
  stem=s['stem'];bp=R/s['cache_path'];hp=raw/'s02_cache'/f'{stem}_H1_graph.json'
  assert sha(bp)==s['cache_sha256'];f=next(f for f in platform['collected'] if f['local_path']==str(hp.relative_to(R)));assert sha(hp)==f['sha256']
  wanted={(e['source'],e['target']) for e in c['edges'] if e['stem']==stem}
  if not wanted:
   checks.append(dict(stem=stem,changed=False,score_reused_from_hash_verified_final_graph=True));continue
  b=json.loads(bp.read_text());h=json.loads(hp.read_text());assert b['nodes']==h['nodes']
  pair=lambda e:(int(e['source_id']),int(e['target_id']))
  bs={pair(e) for e in b['edges']};hs={pair(e) for e in h['edges']};assert wanted<=bs-hs
  target=hs|wanted
  # Keep original B0 order and attributes; change only membership of the three edges.
  edited=dict(nodes=copy.deepcopy(h['nodes']),edges=[copy.deepcopy(e) for e in b['edges'] if pair(e) in target])
  assert [e for e in edited['edges'] if pair(e) not in wanted]==h['edges']
  assert {pair(e) for e in edited['edges']}-hs==wanted and hs<={pair(e) for e in edited['edges']}
  pn,pe=plain(edited);gn,ge=read_gt(stem);row=scope['score_sample'](pn,pe,gn,ge,s['n_total']);row.update(stem=stem,embryo=s['embryo'])
  assert row['input_gt_graph_sha256']==s['gt_input_hash']
  oldrow=next(r for r in rows if r['stem']==stem);rows[rows.index(oldrow)]=row
  changes=dict(stem=stem,restored=sorted(wanted),before_sha256=sha(hp),after_graph_sha256=hashlib.sha256(json.dumps(edited,allow_nan=False).encode()).hexdigest(),nodes_unchanged=True,only_fixed_edges_restored=True)
  checks.append(changes);changed.append(dict(stem=stem,before=oldrow,after=row,delta=delta(oldrow,row)))
  print('SCORED',stem,'restored',len(wanted),flush=True)
 def agg(rs):
  a=scope['aggregate_official'](rs);a.update({k:sum(r[k] for r in rs) for k in ['edge_tp','edge_fp','edge_fn']});return a
 summary={g:agg([r for r in rows if g=='ALL' or r['embryo']==g]) for g in ['ALL','44b6','6bba']}
 result=clean(dict(status='ORACLE_COUNTERFACTUAL_MEASURED',label_assisted=True,public_score=None,production_eligible=False,restored_edges=c['edges'],checks=checks,changed_samples=changed,per_sample=rows,summary=summary,versus_H1={g:delta(prior['local_summary']['H1'][g],v) for g,v in summary.items()},versus_G1={g:delta(prior['local_summary']['B0'][g],v) for g,v in summary.items()},remaining_deletions=440-len(c['edges']),note='Only 3 known correct edges restored using validation labels; not a deployable selection rule or a rigorous upper bound. Other 425 unknown deleted edges remain unknown.'))
 if '--verify' in sys.argv:
  assert result==json.loads((P/'results.json').read_text());print('INDEPENDENT_RECOMPUTE_MATCH')
 else:(P/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
 print(json.dumps({g:dict(score=v['score'],edge_tp=v['edge_tp'],edge_fp=v['edge_fp'],edge_fn=v['edge_fn']) for g,v in summary.items()}))
