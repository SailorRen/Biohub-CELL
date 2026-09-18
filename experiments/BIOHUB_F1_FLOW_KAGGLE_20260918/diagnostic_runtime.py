"""Kaggle-only paired postprocessing of fixed pre-motion upstream graphs."""
import copy, collections, hashlib, json, time, resource, importlib.metadata
assert Path('/kaggle/input').is_dir(), 'CLOUD_ONLY'
ART=WORKING_DIR/'f1_small';ART.mkdir(exist_ok=True)
CACHE=WORKING_DIR/'f1_cache';CACHE.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def gh(n,e):return hashlib.sha256(json.dumps([list(n.items()),e],allow_nan=False,separators=(',',':')).encode()).hexdigest()
def clean(x):
 if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [clean(v) for v in x]
 if isinstance(x,np.generic):return clean(x.item())
 if isinstance(x,float) and not math.isfinite(x):return None
 return x
def save(name,x):(ART/name).write_text(json.dumps(clean(x),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def es(e):return {(int(r['source_id']),int(r['target_id'])) for r in e}
def valid(n,e):
 inc=collections.Counter();out=collections.Counter()
 assert all(np.isfinite([r['z'],r['y'],r['x']]).all() and r['node_id']==i for i,r in n.items())
 assert len(es(e))==len(e),'DUPLICATE_EDGE'
 for s,t in es(e):
  assert s in n and t in n and int(n[t]['t'])==int(n[s]['t'])+1,'EDGE_ENDPOINT_OR_TIME'
  inc[t]+=1;out[s]+=1
 assert max(inc.values(),default=0)<=1 and max(out.values(),default=0)<=2,'GRAPH_DEGREE'

TEST_DIR=COMP_DIR/'train';TRAIN_DIR=TEST_DIR
globals().update(FROZEN_CONFIG)
assert _sprint_model_key(FIXED_STEMS[0])=='44b6'
assert _sprint_model_key(FIXED_STEMS[-1])=='6bba'
source_root=_sprint_paths[0].parent
assert torch.cuda.is_available(),'GPU_REQUIRED'
torch.cuda.reset_peak_memory_stats()
versions={n:importlib.metadata.version(n) for n in ['tracksdata','polars','numpy','scipy','torch','geff','zarr']}
schema={k:getattr(td.DEFAULT_ATTR_KEYS,k) for k in ['NODE_ID','EDGE_SOURCE','EDGE_TARGET','T']}
assert schema==dict(NODE_ID='node_id',EDGE_SOURCE='source_id',EDGE_TARGET='target_id',T='t'),schema
modules={n:sha(Path(__import__(n).__file__)) for n in ['tracksdata','polars','numpy','scipy']}
save('runtime_start.json',dict(versions=versions,module_hashes=modules,schema=schema,gpu=torch.cuda.get_device_name(),
    free_disk_bytes=shutil.disk_usage(WORKING_DIR).free,config=FROZEN_CONFIG,flow_config=F1_CONFIG,
    weight_sha256=_runtime_integrity_receipt['checkpoint_sha256'],division_sha256=_SPRINT_WEIGHT_SHA,
    scorer_hashes=_official_file_hashes,training_calls=0,upstream_inference_calls=0))

# Verify every pre-motion graph file against the already archived cloud output manifest.
checked=[]
for item in RAW_MANIFEST:
 p=source_root/item['name'];assert p.is_file(),('CACHE_FILE_MISSING',item['name'])
 assert sha(p)==item['sha256'],('CACHE_HASH_MISMATCH',item['name'])
 checked.append({'name':item['name'],'sha256':item['sha256']})
save('input_hashes.json',checked)

# DeepCenter heatmaps are shared on disk without keeping all frames in memory.
original_heatmap=deepcenter_heatmap_for_frame
heatmap_computes=heatmap_reads=0
def cached_heatmap(dataset,t,bundle,frames,cache):
 global heatmap_computes,heatmap_reads
 p=CACHE/f'{dataset}_{t}_deepcenter.npy'
 if p.exists():heatmap_reads+=1;return np.load(p,allow_pickle=False)
 h=original_heatmap(dataset,t,bundle,frames,cache)
 assert h is not None,'MISSING_HEATMAP'
 np.save(p,h,allow_pickle=False);heatmap_computes+=1;return h
deepcenter_heatmap_for_frame=cached_heatmap
original_refine=refine_synthetic_midpoint;refine_cache={}
def cached_refine(dataset,t,midpoint,frames,stats):
 key=(dataset,int(t),tuple(midpoint))
 if key not in refine_cache:
  before=dict(stats);value=original_refine(dataset,t,midpoint,frames,stats)
  refine_cache[key]=(value,{k:v-before.get(k,0) for k,v in stats.items() if v!=before.get(k,0)})
  return value
 value,delta=refine_cache[key]
 for k,v in delta.items():stats[k]=stats.get(k,0)+v
 return value
refine_synthetic_midpoint=cached_refine

ROWS={a:[] for a in ['B0','B0_repeat','F1_off','F1']};RECEIPTS=[];EVENTS=[];USAGE=[];MOTION={}
f1_motion=motion_relink_edges
def capture_motion(n,stats,probs=None):
 result=(F1_ORIGINAL_MOTION if ACTIVE_ARM in ['B0','B0_repeat'] else f1_motion)(n,stats,probs)
 MOTION[ACTIVE_ARM]=copy.deepcopy(result)
 return result
motion_relink_edges=capture_motion
for index,stem in enumerate(FIXED_STEMS):
 start=time.monotonic();refine_cache.clear()
 paths=list((source_root/'tracking_repo/predictions').rglob(stem+'.geff'))
 assert len(paths)==1,('CACHE_STAGE_MISSING',stem)
 raw=graph_from_geff(paths[0]);rn=raw.node_attrs();re=raw.edge_attrs()
 assert {'node_id','t','z','y','x'}<=set(rn.columns)
 assert {'source_id','target_id','edge_prob'}<=set(re.columns)
 nodes={int(r['node_id']):{k:int(r[k]) if k in ['node_id','t'] else float(r[k]) for k in ['node_id','t','z','y','x']} for r in rn.iter_rows(named=True)}
 edges=[dict(source_id=int(r['source_id']),target_id=int(r['target_id']),edge_prob=None if r['edge_prob'] is None else float(r['edge_prob'])) for r in re.iter_rows(named=True)]
 raw_hash=gh(nodes,edges);assert raw_hash==EXPECTED_RAW_HASHES[stem],('RAW_STAGE_MISMATCH',stem)
 gtpath=TRAIN_DIR/(stem+'.geff');gt=graph_from_geff(gtpath);gn,ge=graph_to_plain(gt)
 total=read_estimated_true_node_count(gtpath);assert total is not None
 outputs={};statuses={};hashes={};motion_hashes={}
 for arm in ROWS:
  ACTIVE_ARM=arm;F1_ENABLED=arm=='F1';F1_CALLS.clear()
  before=time.monotonic()
  n,e,stats=filter_output_graph(copy.deepcopy(nodes),copy.deepcopy(edges),dataset=stem,deepcenter_bundle=DEEPCENTER_VETO_DETECTOR)
  post_seconds=time.monotonic()-before;valid(n,e)
  assert gh(nodes,edges)==raw_hash,'SHARED_INPUT_MUTATED'
  score_start=time.monotonic()
  row=score_sample(nodes_by_id_to_plain(n),[(r['source_id'],r['target_id']) for r in e],gn,ge,total)
  row.update(stem=stem,embryo=stem.split('_')[0],arm=arm)
  row['score']=aggregate_official([row])['score']
  ROWS[arm].append(row);statuses[arm]=dict(F1_EDGE_STATUS);outputs[arm]=(n,e)
  hashes[arm]=gh(n,e);motion_hashes[arm]=gh(nodes,MOTION[arm])
  RECEIPTS.append(dict(stem=stem,arm=arm,raw_hash=raw_hash,final_hash=hashes[arm],motion_hash=motion_hashes[arm],
      post_seconds=post_seconds,score_seconds=time.monotonic()-score_start,stats=stats,
      nodes=len(n),edges=len(e),classifier_model=_sprint_model_key(stem)))
  if arm=='F1':
   for call in F1_CALLS:
    for usage in call['frames']:USAGE.append(dict(stem=stem,**usage))
  (CACHE/f'{stem}_{arm}_graph.json').write_text(json.dumps(dict(nodes=list(n.items()),edges=e),allow_nan=False))
 assert hashes['B0']==hashes['B0_repeat']==hashes['F1_off'],'REPEAT_OR_OFF_MISMATCH'
 assert abs(ROWS['B0'][-1]['score']-ROWS['B0_repeat'][-1]['score'])<=1e-10
 for stage in ['motion','final']:
  a=MOTION['B0'] if stage=='motion' else outputs['B0'][1]
  b=MOTION['F1'] if stage=='motion' else outputs['F1'][1]
  for kind,changed,arm in [('added',es(b)-es(a),'F1'),('removed',es(a)-es(b),'B0')]:
   for s,t in sorted(changed):EVENTS.append(dict(stem=stem,stage=stage,change=kind,source_id=s,target_id=t,
       attribution=statuses[arm].get((s,t),'UNKNOWN') if stage=='final' else 'UNKNOWN',
       attribution_scope='official final matched-edge mask and sparse pred_valid' if stage=='final' else 'motion stage not independently scored'))
 save('progress.json',dict(completed=index+1,total=8,stem=stem,elapsed_seconds=time.monotonic()-start))
 print('F1_SAMPLE_COMPLETE',stem,ROWS['B0'][-1]['score'],ROWS['F1'][-1]['score'],flush=True)

summary={a:aggregate_official(rows) for a,rows in ROWS.items()}
groups={a:{g:aggregate_official([r for r in rows if r['embryo']==g]) for g in ['44b6','6bba']} for a,rows in ROWS.items()}
delta={k:summary['F1'][k]-summary['B0'][k] for k in ['score','adj_edge_jaccard','division_jaccard','edge_tp','edge_fp','edge_fn','division_tp','division_fp','division_fn']}
group_delta={g:groups['F1'][g]['score']-groups['B0'][g]['score'] for g in ['44b6','6bba']}
changed=any(r['final_hash']!=next(z['final_hash'] for z in RECEIPTS if z['stem']==r['stem'] and z['arm']=='B0') for r in RECEIPTS if r['arm']=='F1')
dominated=delta['score'] < -1e-10 and all(d < -1e-10 for d in group_delta.values()) and delta['adj_edge_jaccard']<=1e-10 and delta['division_jaccard']<=1e-10
status='NO_EFFECT' if not changed else 'DIAGNOSTIC_DOMINATED' if dominated else 'DIAGNOSTIC_FAVORABLE' if delta['score']>1e-10 and all(d>=-1e-10 for d in group_delta.values()) else 'DIAGNOSTIC_MIXED_EXPLORATORY'
assert sum(r['flow_nodes'] for r in USAGE)>0,'SILENT_ALL_FALLBACK'
save('results.json',dict(status=status,summary=summary,by_embryo=groups,delta=delta,embryo_delta=group_delta,
    graph_changed=changed,production_allowed=status in ['DIAGNOSTIC_FAVORABLE','DIAGNOSTIC_MIXED_EXPLORATORY'],
    repeat_and_off_equal=True,samples=FIXED_STEMS,training_calls=0,upstream_inference_calls=0,
    heatmap_computes=heatmap_computes,heatmap_reads=heatmap_reads,
    peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),peak_memory_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    full_pipeline_independent_validation=False))
save('stages.json',RECEIPTS)
pd.DataFrame([r for rows in ROWS.values() for r in rows]).to_csv(ART/'per_view.csv',index=False)
pd.DataFrame(EVENTS).to_csv(ART/'edge_changes.csv',index=False)
pd.DataFrame(USAGE).to_csv(ART/'flow_usage.csv',index=False)
print('F1_DIAGNOSTIC_COMPLETE',status,delta,flush=True)
