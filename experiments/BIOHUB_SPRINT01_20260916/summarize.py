"""Turn actual immutable diagnostic receipts into reviewable paired candidate rows."""
import collections,csv,json
from pathlib import Path
P=Path(__file__).resolve().parent;O=P/'output_v1'
read=lambda n:json.loads((O/n).read_text())
d=read('diagnostic_results.json');rows=read('candidate_decisions.json');stages=read('stages.json');events=read('changed_edges.json')
replay=json.loads((P/'reconstructed_stages.json').read_text())
trace={(r['dataset'],r['frame'],r['parent'],r['child1'],r['child2'],r['arm']):r for r in replay['decisions']}
for r in rows:
 q=trace[(r['dataset'],r['frame'],r['parent'],r['child1'],r['child2'],r['arm'])]
 for k in ['selected','accepted_before_sort','rank']:assert r.get(k)==q.get(k)
 r.update({k:q.get(k) for k in ['selection_reason','frame_cap','global_cap']})
by={}
for r in rows:
 key=(r['dataset'],r['frame'],r['parent'],r['child1'],r['child2']);assert r['arm'] not in by.setdefault(key,{})
 by[key][r['arm']]=r
out=[]
for key,arms in by.items():
 assert set(arms)=={'A0','G1','R1'}
 base=arms['A0'];ds,t,p,c1,c2=key
 for arm in ['G1','R1']:
  r=arms[arm];assert r['learned_score'] is None or r['abstain']==False
  status='LEARNED_FILTER_REJECT' if not r['accepted_before_sort'] else 'SELECTED' if r['selected'] else 'COMPETITION_OR_CAP'
  out.append({'sample':ds,'embryo':ds.split('_')[0],'frame':t,'parent':p,'child1':c1,'child2':c2,'arm':arm,'old_eligible':True,'old_reason':'all original eligibility rules and DeepCenter passed','mutual_nn':True,'divergence':True,'symmetry':True,'DeepCenter':True,'old_selected':base['selected'],'new_eligible':r['accepted_before_sort'],'new_reason':r['selection_reason'],'old_selection_reason':base['selection_reason'],'frame_cap':base['frame_cap'],'global_cap':base['global_cap'],'new_selected':r['selected'],'classifier_score':r['learned_score'],'held_out_model':ds.split('_')[0],'context_complete':not r['abstain'],'abstain':r['abstain'],'old_rank':base.get('rank'),'new_rank':r.get('rank'),'direct_filter_change':not r['accepted_before_sort'],'rank_change':base.get('rank')!=r.get('rank'),'selected_change':base['selected']!=r['selected'],'annotation':'see event_attribution.json and safe_event_attribution.json; unassessed forks remain UNKNOWN','scope':'same eligible snapshot; subsequent short-track/smoothing effects reported separately'})
with (P/'candidate_diff.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(out[0]),lineterminator='\n');w.writeheader();w.writerows(out)
summary={}
for arm in ['A0','G1','R1']:
 rr=[r for r in rows if r['arm']==arm];ss=[s for s in stages if s['arm']==arm]
 summary[arm]={'eligible_before_learning':len(rr),'classifier_calls':sum(r['learned_score'] is not None for r in rr),'abstain':sum(r['abstain'] for r in rr),'filtered':sum(not r['accepted_before_sort'] for r in rr),'selected':sum(r['selected'] for r in rr),'competition_or_cap':sum(r['accepted_before_sort'] and not r['selected'] for r in rr),'fallback_frames':sum(len(s['fallback_frames']) for s in ss),'global_cap_break_counter':sum(s['stats']['safe_division_skipped_cap'] for s in ss),'selection_reasons':replay['selection_counts'][arm],'limitations':'replayed from exact cached pre-safe graph; selected flags and stage hashes equal actual cloud run'}
(P/'candidate_summary.json').write_text(json.dumps({'arms':summary,'paired_rows':len(out),'direct_filter_changes':sum(r['direct_filter_change'] for r in out),'selected_changes':{a:sum(r['selected_change'] for r in out if r['arm']==a) for a in ['G1','R1']},'stage_edge_changes':{a:{stage:{c:sum(e['arm']==a and e['stage']==stage and e['change']==c for e in events) for c in ['added','lost']} for stage in ['safe_div','final']} for a in ['G1','R1']}},ensure_ascii=False,indent=2)+'\n')
print('CANDIDATE_PAIRS_WRITTEN',len(out))
