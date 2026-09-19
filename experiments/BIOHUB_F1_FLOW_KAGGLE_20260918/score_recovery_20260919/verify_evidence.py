"""Independent arithmetic/hash audit without executing recovery scorer."""
import json,hashlib,csv,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;E=P.parent
j=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=j(P/'receipt.json');v=j(P/'results.json');c=j(E/'contract.json');freeze=j(P/'script_freeze.json');m=j(P/'input_manifest.json')
assert r['status']=='CACHE_RESCORE_VERIFIED' and sha(P/'restore_scores.py')==freeze['restore_scores_sha256']
for name,h in r['hashes'].items():assert sha(P/name)==h
assert len(m['predictions'])==32 and len({x['name'] for x in m['predictions']})==32
assert m['identity_before']==m['identity_after'] and m['source']['script_version_id']==351058693
log=j(E/'recovery_20260919/failure_analysis.json')['per_view_log_scores'];counts=['edge_tp','edge_fp','edge_fn','division_tp','division_fp','division_fn','num_pred_nodes']
for arm in ['B0','F1']:
 rows=[]
 for stem in c['samples']:
  a=j(P/'checkpoints'/f'{stem}_{arm}.json');row=a['metrics'];rows.append(dict(row,stem=stem))
  assert a['fingerprint']['script_sha256']==freeze['restore_scores_sha256'] and abs(row['score']-float(next(x[arm] for x in log if x['stem']==stem)))<=1e-10
  assert a['fingerprint']['pred_bytes_sha256']==next(x['sha256'] for x in m['predictions'] if x['name']==f'f1_cache/{stem}_{arm}_graph.json')
 for group,selected,out in [('all',rows,v['summary'][arm])]+[(g,[x for x in rows if x['stem'].startswith(g)],v['by_embryo'][arm][g]) for g in ['44b6','6bba']]:
  totals={k:sum(x[k] for x in selected) for k in counts};assert out['counts']==totals
  weights=[x['edge_tp']+x['edge_fp']+x['edge_fn'] for x in selected]
  adj=sum(w*x['adj_edge_jaccard'] for w,x in zip(weights,selected))/sum(weights)
  div=totals['division_tp']/(totals['division_tp']+totals['division_fp']+totals['division_fn'])
  assert abs(out['official']['score']-(adj+.1*div))<=1e-15 and out['official']['n']==out['official']['n_adj']==len(selected)
  assert out['weight']==sum(weights)
for stem in c['samples']:
 a=[j(P/'checkpoints'/f'{stem}_{arm}.json') for arm in ['B0','B0_repeat','F1_off']]
 assert len({x['fingerprint']['ordered_graph_sha256'] for x in a})==1
 assert all(x['metrics']==a[0]['metrics'] for x in a)
for fn in ['flow_patch.py','diagnostic/candidate.ipynb','production/candidate.ipynb']:
 key={'flow_patch.py':'patch_sha256','diagnostic/candidate.ipynb':'diagnostic_sha256','production/candidate.ipynb':'production_sha256'}[fn];assert sha(E/fn)==c['source_hashes'][key]
subprocess.run(['/opt/anaconda3/envs/ml/bin/python3',str(E/'recovery_20260919/verify_recovery.py')],check=True)
out=dict(status='EVIDENCE_VERIFIED',log_values_verified=16,checkpoints_verified=32,independent_weighted_arithmetic=True,science_unchanged=True,source_worker_status='ERROR',production_gate=v['status'])
(P/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
