"""Executed only in the diagnostic notebook, after audited frozen definitions.
All three arms use identical ordered input copies. No training, no PP search.
"""
import copy,hashlib,json,collections
CACHE=WORKING_DIR/'sprint_cache';CACHE.mkdir(exist_ok=True)
ART=WORKING_DIR/'sprint_small';ART.mkdir(exist_ok=True)
def digest_bytes(b):return hashlib.sha256(b).hexdigest()
def graph_hash(nodes,edges):
 return digest_bytes(json.dumps([list(nodes.items()),edges],allow_nan=False,separators=(',',':')).encode())
def edge_set(edges):return {(int(e['source_id']),int(e['target_id'])) for e in edges}
def write_json(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def clean(x):
 if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [clean(v) for v in x]
 if isinstance(x,np.generic):return clean(x.item())
 if isinstance(x,float) and not math.isfinite(x):return None
 return x
# Only saved inference parameters are loaded. Hash ties to exact Division V1.
weight_paths=list(Path('/kaggle/input').rglob('division_gate_weights.json'))
weight_paths=[p for p in weight_paths if hashlib.sha256(p.read_bytes()).hexdigest()==EXPECTED_WEIGHT_SHA]
assert len(weight_paths)==1,('EXACT_SAVED_WEIGHTS_REQUIRED',len(weight_paths))
PAYLOAD=json.loads(weight_paths[0].read_text());assert set(PAYLOAD['held_out'])=={'44b6','6bba'}
source_root=weight_paths[0].parent
training_receipt=json.loads((source_root/'division_training_receipt.json').read_text())
assert training_receipt['weights_sha256']==EXPECTED_WEIGHT_SHA
for fold in training_receipt['folds']:
 assert fold['held_out_embryo'] not in fold['training_embryos']
LINEAGE=[]
for root in [source_root,ARTIFACTS,SECONDARY_ARTIFACTS]:
 for path in Path(root).rglob('*split*.json'):
  b=path.read_bytes();LINEAGE.append({'path':str(path),'sha256':digest_bytes(b),'metadata':json.loads(b)})
write_json(ART/'upstream_split_manifests.json',LINEAGE)
# Explicit embryo selection, never infer validation from TEST_DIR.
GROUPS={stem:stem.split('_')[0] for stem in FIXED_STEMS}
def score_pair(snapshot,parent,c1,c2,dataset):
 nodes,out_edges=snapshot
 out={u:[int(e['target_id']) for e in es] for u,es in out_edges.items() if u in (c1,c2)}
 coords=context(nodes,out,parent,c1,c2)
 if coords is None:return None
 model=PAYLOAD['held_out'][GROUPS[dataset]]
 return float(predict(model,pair_features(coords)))
# Persist the actual old DeepCenter heatmaps; no altered gate or detector.
original_heatmap=deepcenter_heatmap_for_frame
HEATMAP_READS=HEATMAP_COMPUTES=0
def cached_heatmap(dataset,t,detector_bundle,frame_cache,heatmap_cache):
 global HEATMAP_READS,HEATMAP_COMPUTES
 p=CACHE/f'{dataset}_{t}_deepcenter.npy'
 if p.exists():HEATMAP_READS+=1;return np.load(p,allow_pickle=False)
 h=original_heatmap(dataset,t,detector_bundle,frame_cache,heatmap_cache)
 if h is None:raise RuntimeError('DEEPCENTER_HEATMAP_MISSING')
 np.save(p,h,allow_pickle=False);HEATMAP_COMPUTES+=1;return h
deepcenter_heatmap_for_frame=cached_heatmap
original_refine=refine_synthetic_midpoint
REFINEMENT_CACHE={}
def cached_refine(dataset,t,midpoint,frame_cache,stats):
 key=(dataset,int(t),tuple(midpoint))
 if key in REFINEMENT_CACHE:
  value,delta=REFINEMENT_CACHE[key]
  for k,v in delta.items():stats[k]=stats.get(k,0)+v
  return value
 before=dict(stats);value=original_refine(dataset,t,midpoint,frame_cache,stats)
 REFINEMENT_CACHE[key]=(value,{k:v-before.get(k,0) for k,v in stats.items() if v!=before.get(k,0)})
 return value
refine_synthetic_midpoint=cached_refine
ORIGINAL_SAFE_DIV=add_safe_divisions_postlink
exec(PATCHED_SAFE_DIV,globals())
PATCHED_SAFE_DIV_FUNCTION=add_safe_divisions_postlink
STAGES={};ACTIVE_ARM=None
def capture_safe_div(nodes,edges,stats,**kw):
 dataset=kw['dataset'];before=graph_hash(nodes,edges)
 fn=ORIGINAL_SAFE_DIV if ACTIVE_ARM=='A0_repeat' else PATCHED_SAFE_DIV_FUNCTION
 result=fn(nodes,edges,stats,**kw)
 STAGES[(dataset,ACTIVE_ARM)]={'input_hash':before,'nodes':copy.deepcopy(nodes),'edges':copy.deepcopy(result),'graph_hash':graph_hash(nodes,result)}
 return result
add_safe_divisions_postlink=capture_safe_div
TEST_DIR=COMP_DIR/'train';TRAIN_DIR=TEST_DIR
for k,v in FROZEN_CONFIG.items():globals()[k]=v
assert DEEPCENTER_VETO_DETECTOR is not None
ALL_ROWS={arm:[] for arm in ['A0','A0_repeat','G1','R1']};EVENTS=[];DECISIONS=[];RECEIPTS=[];SAVED={}
for sample_index,stem in enumerate(FIXED_STEMS):
 candidates=list((source_root/'tracking_repo/predictions').rglob(stem+'.geff'))
 assert len(candidates)==1,('CACHED_PREDICTION_REQUIRED',stem,len(candidates))
 gt_path=TRAIN_DIR/(stem+'.geff');gt=graph_from_geff(gt_path);gt_nodes,gt_edges=graph_to_plain(gt)
 total=read_estimated_true_node_count(gt_path);assert total is not None
 raw=graph_from_geff(candidates[0]);nodes={int(r['node_id']):{'node_id':int(r['node_id']),'t':int(r['t']),'z':float(r['z']),'y':float(r['y']),'x':float(r['x'])} for r in raw.node_attrs().iter_rows(named=True)}
 edges=[{'source_id':int(r['source_id']),'target_id':int(r['target_id']),'edge_prob':None if r.get('edge_prob') is None else float(r['edge_prob'])} for r in raw.edge_attrs().iter_rows(named=True)]
 raw_hash=graph_hash(nodes,edges);sample_outputs={}
 for arm in ALL_ROWS:
  ACTIVE_ARM=arm;SPRINT_POLICY=ProposalPolicy('A0' if arm=='A0_repeat' else arm,score_pair)
  output_nodes,output_edges,stats=filter_output_graph(copy.deepcopy(nodes),copy.deepcopy(edges),dataset=stem,deepcenter_bundle=DEEPCENTER_VETO_DETECTOR)
  assert graph_hash(nodes,edges)==raw_hash,'SHARED_MUTABLE_INPUT'
  plain=nodes_by_id_to_plain(output_nodes);es=[(e['source_id'],e['target_id']) for e in output_edges]
  row=score_sample(plain,es,gt_nodes,gt_edges,total);row.update(stem=stem,embryo=GROUPS[stem],arm=arm)
  ALL_ROWS[arm].append(row);sample_outputs[arm]=(output_nodes,output_edges);DECISIONS.extend(SPRINT_POLICY.rows)
  stage=STAGES[(stem,arm)];sp=score_sample(nodes_by_id_to_plain(stage['nodes']),[(e['source_id'],e['target_id']) for e in stage['edges']],gt_nodes,gt_edges,total)
  RECEIPTS.append({'sample':stem,'arm':arm,'raw_hash':raw_hash,'safe_div_input_hash':stage['input_hash'],'safe_div_hash':stage['graph_hash'],'final_hash':graph_hash(output_nodes,output_edges),'safe_div_metrics':sp,'stats':stats,'classifier_calls':sum(r['learned_score'] is not None for r in SPRINT_POLICY.rows),'abstain':sum(r['abstain'] for r in SPRINT_POLICY.rows),'fallback_frames':SPRINT_POLICY.frame_fallbacks})
  # Actual ordered graph snapshots remain Kaggle-only, not copied to GitHub.
  write_json(CACHE/f'{stem}_{arm}_graph.json',{'nodes':list(output_nodes.items()),'edges':output_edges})
 assert graph_hash(*sample_outputs['A0'])==graph_hash(*sample_outputs['A0_repeat']),'A0_NOT_REPEATABLE_OR_PATCH_OFF_DRIFT'
 assert len({STAGES[(stem,a)]['input_hash'] for a in ALL_ROWS})==1,'PRE_SAFE_DIV_DRIFT'
 sets={a:{(r['frame'],r['parent'],r['child2']) for r in DECISIONS if r['dataset']==stem and r['arm']==a} for a in ['A0','G1','R1']}
 assert sets['A0']==sets['G1']==sets['R1'],'ELIGIBLE_CANDIDATE_SET_CHANGED'
 for arm in ['G1','R1']:
  for stage_name in ['safe_div','final']:
   aa=STAGES[(stem,'A0')] if stage_name=='safe_div' else {'nodes':sample_outputs['A0'][0],'edges':sample_outputs['A0'][1]}
   bb=STAGES[(stem,arm)] if stage_name=='safe_div' else {'nodes':sample_outputs[arm][0],'edges':sample_outputs[arm][1]}
   for change,changed_edges in [('added',edge_set(bb['edges'])-edge_set(aa['edges'])),('lost',edge_set(aa['edges'])-edge_set(bb['edges']))]:
    for parent,child in sorted(changed_edges):
     EVENTS.append({'sample':stem,'embryo':GROUPS[stem],'arm':arm,'stage':stage_name,'change':change,'parent':parent,'child':child,'category':'无法可靠判定','annotation_support':'UNKNOWN: event attribution requires reliable official branch matching; aggregate scored independently','causal_scope':'combined ordering/competition or filter consequence, not independent factor attribution'})
 write_json(ART/'progress.json',{'completed_samples':sample_index+1,'total_samples':8,'latest':stem,'first_fixed_sample_integration_passed':True})
 print('SPRINT_SAMPLE_COMPLETE',stem,flush=True)
SUMMARY={a:aggregate_official(rows) for a,rows in ALL_ROWS.items()}
BY_GROUP={a:{g:aggregate_official([r for r in rows if r['embryo']==g]) for g in ['44b6','6bba']} for a,rows in ALL_ROWS.items()}
variation=abs(SUMMARY['A0']['score']-SUMMARY['A0_repeat']['score'])
passes={a:SUMMARY[a]['score']-SUMMARY['A0']['score']>variation and all(BY_GROUP[a][g]['score']>=BY_GROUP['A0'][g]['score'] for g in GROUPS.values()) and any(e['arm']==a for e in EVENTS) for a in ['G1','R1']}
qualified=[a for a in ['G1','R1'] if passes[a]];winner=max(qualified,key=lambda a:(SUMMARY[a]['score'],a=='G1')) if qualified else None
write_json(ART/'diagnostic_results.json',clean({'status':'EVALUATED','samples':FIXED_STEMS,'summary':SUMMARY,'by_embryo':BY_GROUP,'per_sample':ALL_ROWS,'repeat_variation':variation,'pass':passes,'selected':winner,'training_calls':0,'heatmap_computes':HEATMAP_COMPUTES,'heatmap_disk_reads':HEATMAP_READS,'upstream_lineage':'see upstream_split_manifests.json; no full-pipeline independence claim'}))
write_json(ART/'stages.json',clean(RECEIPTS));write_json(ART/'candidate_decisions.json',clean(DECISIONS));write_json(ART/'changed_edges.json',EVENTS)
write_json(CACHE/'refinement_cache.json',[{'key':list(k),'value':v} for k,v in REFINEMENT_CACHE.items()])
print('SPRINT_DIAGNOSTIC_COMPLETE',winner,flush=True)
