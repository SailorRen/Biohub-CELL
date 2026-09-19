"""Rebuild gate and auditable small reports solely from verified checkpoints."""
from restore_scores import P,E,ROOT,sha,atomic,aggregate
import json,csv,hashlib,collections

def main():
 c=json.loads((E/'contract.json').read_text());m=json.loads((P/'input_manifest.json').read_text());assert m['status']=='BOUND_CACHE_BYTES_VERIFIED' and len(m['predictions'])==32
 amendment=json.loads((P/'contract_amendment.json').read_text());assert sha(E/'contract.json')==amendment['original_contract_sha256']
 assert sha(E/'flow_patch.py')==c['source_hashes']['patch_sha256'] and sha(E/'production/candidate.ipynb')==c['source_hashes']['production_sha256']
 frozen=json.loads((P/'script_freeze.json').read_text());assert sha(P/'restore_scores.py')==frozen['restore_scores_sha256']
 rows={a:[] for a in ['B0','F1']};checks=[];events=[];changed=[];reused=[]
 for stem in c['samples']:
  arms={}
  for arm in ['B0','B0_repeat','F1_off','F1']:
   p=P/'checkpoints'/f'{stem}_{arm}.json';a=json.loads(p.read_text());assert a['status']=='SCORED_LOG_VERIFIED' and abs(a['log_delta'])<=c['epsilon'] and a['graph_legal']
   assert a['fingerprint']['script_sha256']==frozen['restore_scores_sha256']
   ref=next(r for r in m['predictions'] if r['name']==f'f1_cache/{stem}_{arm}_graph.json');assert a['fingerprint']['pred_bytes_sha256']==ref['sha256']
   arms[arm]=a
   if a['reuse_of']:reused.append(dict(stem=stem,arm=arm,reuse_of=a['reuse_of']))
  assert arms['B0']['fingerprint']['ordered_graph_sha256']==arms['B0_repeat']['fingerprint']['ordered_graph_sha256']==arms['F1_off']['fingerprint']['ordered_graph_sha256']
  for arm in ['B0','F1']:
   a=arms[arm];rows[arm].append(dict(a['metrics'],stem=stem,embryo=stem.split('_')[0],arm=arm));checks.append(dict(stem=stem,arm=arm,score=a['metrics']['score'],log_score=a['log_score'],delta=a['log_delta'],pass_tolerance=True,checkpoint_sha256=sha(P/'checkpoints'/f'{stem}_{arm}.json')))
   events.extend(dict(stem=stem,change='removed' if arm=='B0' else 'added',**e) for e in a['events'])
  if arms['B0']['fingerprint']['ordered_graph_sha256']!=arms['F1']['fingerprint']['ordered_graph_sha256']:changed.append(stem)
 overall={a:aggregate(r) for a,r in rows.items()};groups={a:{g:aggregate([r for r in rr if r['embryo']==g]) for g in ['44b6','6bba']} for a,rr in rows.items()}
 assert all(v['official']['n']==v['official']['n_adj']==8 for v in overall.values())
 assert all(v['official']['n']==v['official']['n_adj']==4 for gs in groups.values() for v in gs.values())
 delta={k:overall['F1']['official'][k]-overall['B0']['official'][k] for k in ['score','adj_edge_jaccard','division_jaccard']}
 gd={g:groups['F1'][g]['official']['score']-groups['B0'][g]['official']['score'] for g in ['44b6','6bba']}
 eps=c['epsilon'];dom=delta['score']<-eps and all(d<-eps for d in gd.values()) and delta['adj_edge_jaccard']<=eps and delta['division_jaccard']<=eps
 status='NO_EFFECT' if not changed else 'DIAGNOSTIC_DOMINATED' if dom else 'DIAGNOSTIC_FAVORABLE' if delta['score']>eps and all(d>=-eps for d in gd.values()) else 'DIAGNOSTIC_MIXED_EXPLORATORY'
 result=dict(status=status,summary=overall,by_embryo=groups,delta=delta,embryo_delta=gd,changed_views=changed,graph_changed=bool(changed),repeat_and_off_equal=True,samples=c['samples'],production_allowed=status in c['production_allowed'],counts_provenance='Recomputed from final graphs; not recovered original process memory',independent_generalization_validation=False,event_counts={kind:dict(collections.Counter(e['attribution'] for e in events if e['change']==kind)) for kind in ['added','removed']})
 atomic(P/'results.json',result)
 with (P/'per_view.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows['B0'][0]));w.writeheader();w.writerows(rows['B0']+rows['F1'])
 with (P/'final_edge_changes.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=['stem','change','source_id','target_id','attribution']);w.writeheader();w.writerows(events)
 failure=json.loads((E/'recovery_20260919/failure_analysis.json').read_text());assert failure['weights_config_scorer_hash_verified'] and failure['input_hashes_verified']==264 and failure['completed_views']==8
 assert json.loads((E/'diagnostic/progress.json').read_text())['completed']==8
 # Exact archived diagnostic source and pure F1 patch inspected: one deterministic
 # neighbour prior; no random/timeout fallback branch. Only archived error is edge_tp.
 assert sha(E/'diagnostic/candidate.ipynb')==c['source_hashes']['diagnostic_sha256']
 logs=json.loads((E/'diagnostic/log_20260919T130712Z.txt').read_text());text=''.join(r['data'] for r in logs)
 assert "KeyError: 'edge_tp'" in text and text.count('F1_SAMPLE_COMPLETE')==8
 for forbidden in ['TimeoutError:','MemoryError:','CUDA out of memory','F1_NONFINITE','F1_SEED_ENDPOINT']:
  assert forbidden not in text
 resource=json.loads((P/'resource_result.json').read_text());resource['pilot']=json.loads((P/'pilot_resource_result.json').read_text());assert resource['status']=='SCORING_COMPLETE' and resource['peak_rss_bytes']<=resource['budget_bytes']<=4*1024**3
 receipt=dict(status='CACHE_RESCORE_VERIFIED',source=json.loads((E/'diagnostic/version_binding.json').read_text()),source_worker_status='ERROR',recovery_execution='LOCAL_CPU_SCORING_ONLY',cloud_diagnostic_reruns=0,model_inference_calls=0,training_calls=0,flow_effect_evidence='FROZEN_SOURCE_PLUS_FINAL_GRAPH_CHANGE' if changed else 'NO_FINAL_GRAPH_CHANGE',old_SILENT_ALL_FALLBACK_assertion_executed=False,log_comparisons=checks,graph_equivalence_reuses=reused,not_recoverable={k:'NOT_RECOVERABLE_FROM_FINAL_GRAPHS' for k in amendment['nonrecoverable']},runtime_inputs_configs_verified=True,known_error='Original worker KeyError edge_tp retained; summary schema repaired outside vendor',resources=resource,hashes={n:sha(P/n) for n in ['input_manifest.json','restore_scores.py','script_freeze.json','results.json','per_view.csv','final_edge_changes.csv']},production_gate=status,production_allowed=result['production_allowed'])
 atomic(P/'receipt.json',receipt);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
