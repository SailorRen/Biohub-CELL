"""Bounded CPU scoring of frozen final graphs only; no Notebook execution."""
import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','POLARS_MAX_THREADS','VECLIB_MAXIMUM_THREADS','NUMBA_NUM_THREADS']:
 os.environ[key]='2'
import argparse,collections,copy,csv,hashlib,importlib,importlib.metadata,json,math,resource,shutil,signal,sys,tempfile,time
from pathlib import Path
P=Path(__file__).resolve().parent;E=P.parent;ROOT=E.parents[1]
D=ROOT/'downloads/F1_CACHE_RESCORE_20260919'
GTBASE=Path('/Users/sailor/kaggle/项目/Biohub - CELL/downloads/BIOHUB_SPRINT01_20260916/gt')
VENDOR=ROOT/'experiments/TARGET950_20260914/vendor'
sys.path.insert(0,str(VENDOR))
import polars as pl
import tracksdata as td
import psutil
from official_075fc5 import metrics
from threadpoolctl import threadpool_limits
threadpool_limits(limits=2)
SCALE=(1.625,.40625,.40625);RADIUS=7.
SCORER={'metrics.py':'cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444','division_metrics.py':'0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def clean(x):
 if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [clean(v) for v in x]
 if isinstance(x,float) and not math.isfinite(x):return None
 return x
def atomic(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp')
 with tmp.open('w') as f:json.dump(clean(obj),f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(tmp,path)
def new_graph(nodes,edges):
 g=td.graph.InMemoryGraph()
 for k in ['z','y','x']:g.add_node_attr_key(k,pl.Float64,0.)
 ids=list(nodes);attrs=[dict(t=int(nodes[i][0]),z=float(nodes[i][1]),y=float(nodes[i][2]),x=float(nodes[i][3])) for i in ids]
 internal=list(g.bulk_add_nodes(attrs));remap=dict(zip(ids,internal,strict=True));assert len(set(internal))==len(ids)
 g.bulk_add_edges([dict(source_id=remap[s],target_id=remap[t]) for s,t in edges])
 assert list(g.node_ids())==internal,'BACKEND_ORDER_CHANGED'
 return g,dict(zip(internal,ids,strict=True))
def load_prediction(path):
 raw=json.loads(path.read_text());pairs=raw['nodes'];assert all(type(i)==int for i,r in pairs)
 nodes=dict(pairs);assert len(nodes)==len(pairs),'DUPLICATE_NODE'
 edges=raw['edges'];edgepairs=[(r['source_id'],r['target_id']) for r in edges]
 assert len(edgepairs)==len(set(edgepairs)),'DUPLICATE_EDGE'
 inc=collections.Counter();out=collections.Counter()
 for i,r in pairs:
  assert r['node_id']==i and type(r['t'])==int and 0<=r['t']<2**31
  assert all(math.isfinite(r[k]) for k in ['z','y','x'])
 for s,t in edgepairs:
  assert s in nodes and t in nodes and nodes[t]['t']==nodes[s]['t']+1
  inc[t]+=1;out[s]+=1
 assert max(inc.values(),default=0)<=1 and max(out.values(),default=0)<=2
 ordered=hashlib.sha256(json.dumps([list(nodes.items()),edges],allow_nan=False,separators=(',',':')).encode()).hexdigest()
 plain={i:(r['t'],float(r['z']),float(r['y']),float(r['x'])) for i,r in pairs}
 return plain,edgepairs,ordered

def plain_sha(nodes,edges):
 obj={'nodes':[[int(i),int(v[0]),*[float(x) for x in v[1:]]] for i,v in nodes.items()],'edges':[[int(s),int(t)] for s,t in edges]}
 return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
def recursive(x,key):
 if isinstance(x,dict):
  if key in x:return x[key]
  for v in x.values():
   y=recursive(v,key)
   if y is not None:return y
 elif isinstance(x,list):
  for v in x:
   y=recursive(v,key)
   if y is not None:return y
 return None
def read_gt(stem):
 src=GTBASE/(stem+'.geff')
 # Exactly the previously hash-verified IndexedRX reader; synthetic missing
 # structural groups are added in a temporary copy, never to source arrays.
 with tempfile.TemporaryDirectory(prefix='f1-gt-',dir=D) as tmp:
  dst=Path(tmp)/src.name;shutil.copytree(src,dst)
  for name in ['nodes','edges','nodes/props',*['nodes/props/'+k for k in ['t','z','y','x']]]:
   (dst/name/'zarr.json').write_text(json.dumps({'zarr_format':3,'node_type':'group','attributes':{}}))
  graph=td.graph.IndexedRXGraph.from_geff(dst)[0]
  nodes={int(r['node_id']):(int(r['t']),float(r['z']),float(r['y']),float(r['x'])) for r in graph.node_attrs().iter_rows(named=True)}
  edges=[(int(r['source_id']),int(r['target_id'])) for r in graph.edge_attrs().iter_rows(named=True)]
 total=float(recursive(json.loads((src/'zarr.json').read_text()),'estimated_number_of_nodes'));assert math.isfinite(total) and total>0
 old=json.loads((E.parent/'BIOHUB_SPRINT01_20260916/gt_reader_integrity.json').read_text())['rows']
 assert plain_sha(nodes,edges)==next(r['hash'] for r in old if r['sample']==stem),'GT_ORDER_MISMATCH'
 return nodes,edges,total

def aggregate(rows):
 assert rows
 for r in rows:
  for key in metrics.METRIC_COLUMNS:assert key in r and r[key] is not None and math.isfinite(r[key]),'INVALID_REQUIRED_FIELD_'+key
 result=metrics.summarise(rows)
 assert result['n']==result['n_adj']==len(rows)
 assert math.isfinite(result['score'])
 return dict(official=result,counts={k:sum(r[k] for r in rows) for k in metrics.COUNT_COLUMNS},weight=sum(r['edge_tp']+r['edge_fp']+r['edge_fn'] for r in rows))
def score(nodes,edges,gn,ge,total,event_pairs):
 pred,idback=new_graph(nodes,list(edges));gt,_=new_graph(gn,list(ge));before_ids=list(pred.node_ids())
 er=metrics.evaluate(pred,gt,scale=SCALE,max_distance=RADIUS)
 if pred.num_edges()==0:
  from tracksdata.metrics import DistanceMatching
  pred.match(gt,matching=DistanceMatching(scale=SCALE,max_distance=RADIUS))
 assert list(pred.node_ids())==before_ids and len(idback)==len(nodes),'ATTRIBUTION_ID_MAP_CHANGED'
 row=metrics.per_sample_metrics(er,n_total=total,node_recall=metrics.node_recall(pred,gt));row['score']=aggregate([row])['official']['score']
 row.update(n_total=total,weight=er.edge_tp+er.edge_fp+er.edge_fn)
 statuses={p:'UNKNOWN' for p in event_pairs}
 if pred.num_edges():
  for item in metrics._evaluate_matched_graph(pred,gt).iter_rows(named=True):
   pair=(idback[item['source_id']],idback[item['target_id']])
   if pair in statuses:statuses[pair]='TP' if item[td.DEFAULT_ATTR_KEYS.MATCHED_EDGE_MASK] else 'FP' if item['pred_valid'] else 'UNKNOWN'
 return row,[dict(source_id=s,target_id=t,attribution=statuses[s,t]) for s,t in sorted(event_pairs)]
def checkpoint(path,fingerprint,compute):
 if path.exists():
  c=json.loads(path.read_text());assert c['fingerprint']==fingerprint,'CHECKPOINT_HASH_MISMATCH'
  assert c['status']=='SCORED_LOG_VERIFIED' and abs(c['log_delta'])<=1e-10
  aggregate([c['metrics']]);return c,True
 c=compute();c.update(fingerprint=fingerprint,status='SCORED_LOG_VERIFIED');assert abs(c['log_delta'])<=1e-10,'LOG_SCORE_MISMATCH'
 atomic(path,c);return c,False

def self_test():
 import warnings
 with warnings.catch_warnings():
  warnings.simplefilter('ignore')
  rows=[metrics.per_sample_metrics(metrics.EvaluationResult(2,1,0,0,0,0,3),3,1.),metrics.per_sample_metrics(metrics.EvaluationResult(80,10,10,0,0,0,100),120,1.)]
  direct=metrics.summarise(rows);out=aggregate(rows);assert 'edge_tp' not in direct and out['official']['score']==direct['score'] and out['counts']['edge_tp']==82
  assert math.isnan(direct['division_jaccard']) and direct['score']==direct['adj_edge_jaccard']
  assert abs(direct['score']-(3*rows[0]['adj_edge_jaccard']+100*rows[1]['adj_edge_jaccard'])/103)<1e-15
  bad=copy.deepcopy(rows);del bad[0]['edge_tp']
  try:aggregate(bad)
  except AssertionError:pass
  else:raise AssertionError('MISSING_FIELD_NOT_REJECTED')
  with tempfile.TemporaryDirectory() as tdpath:
   p=Path(tdpath)/'checkpoint.json';f={'test_hash':'one'};calls=[]
   def calc():calls.append(1);return dict(metrics=rows[0],log_delta=0)
   checkpoint(p,f,calc);_,reused=checkpoint(p,f,calc);assert reused and len(calls)==1
   try:checkpoint(p,{'test_hash':'two'},calc)
   except AssertionError:pass
   else:raise AssertionError('BAD_CHECKPOINT_ACCEPTED')
  n={17:(0,0.,0.,0.),31:(1,0.,0.,0.)};m,_=score(n,[(17,31)],n,[(17,31)],2,{(17,31)});assert m['score']==1.
 return {'schema_adapter_preserves_score':True,'missing_required_field_rejected':True,'own_weights_and_no_divisions':True,'checkpoint_reuse_and_hash_rejection':True,'nonconsecutive_id_roundtrip':True}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--test',action='store_true');ap.add_argument('--pilot',action='store_true');args=ap.parse_args()
 for name,h in SCORER.items():assert sha(VENDOR/'official_075fc5'/name)==h
 assert importlib.metadata.version('tracksdata')=='0.1.0rc6.dev3+g980c2d30a'
 assert {k:getattr(td.DEFAULT_ATTR_KEYS,k) for k in ['NODE_ID','EDGE_SOURCE','EDGE_TARGET','T']}==dict(NODE_ID='node_id',EDGE_SOURCE='source_id',EDGE_TARGET='target_id',T='t')
 if args.test:atomic(P/'tests.json',self_test());print('TESTS_PASS');return
 freeze=json.loads((P/'script_freeze.json').read_text());assert freeze['restore_scores_sha256']==sha(Path(__file__))
 manifest=json.loads((P/'input_manifest.json').read_text())
 if args.pilot:
  pilot=json.loads((P/'pilot_input_binding.json').read_text());assert pilot['status']=='PILOT_BOUND_CACHE_BYTES_VERIFIED' and pilot['script_version_id']==351058693
  assert all(r in manifest['predictions'] for r in pilot['predictions'])
 else:assert manifest['status']=='BOUND_CACHE_BYTES_VERIFIED'
 assert sum(r['bytes'] for r in manifest['predictions'])+manifest['gt_reused_bytes']<2*1024**3
 for r in manifest['gt']:
  fp=GTBASE/Path(r['source']).relative_to('train');assert sha(fp)==r['sha256']
 available=psutil.virtual_memory().available;budget=min(4*1024**3,int(available*.5));proc=psutil.Process();start=time.monotonic();peak=proc.memory_info().rss
 def guard(*_):
  nonlocal peak
  peak=max(peak,proc.memory_info().rss)
  if peak>budget:raise MemoryError('SCORING_RSS_BUDGET_EXCEEDED')
 signal.signal(signal.SIGALRM,guard);signal.setitimer(signal.ITIMER_REAL,.2,.2)
 env={k:importlib.metadata.version(k) for k in ['tracksdata','polars','numpy','scipy','geff','zarr','rustworkx']}
 atomic(P/'resource_start.json',dict(available_bytes=available,budget_bytes=budget,max_cpu_threads=2,versions=env,started_at_utc=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()))
 samples=json.loads((E/'contract.json').read_text())['samples'];logrows=json.loads((E/'recovery_20260919/failure_analysis.json').read_text())['per_view_log_scores']
 allc=[]
 try:
  for stem in samples[:1] if args.pilot else samples:
   graphs={};rawhash={}
   for arm in ['B0','B0_repeat','F1_off','F1']:
    name=f'f1_cache/{stem}_{arm}_graph.json';p=D/name;ref=next(r for r in manifest['predictions'] if r['name']==name)
    assert p.stat().st_size==ref['bytes'] and sha(p)==ref['sha256'];rawhash[arm]=ref['sha256'];graphs[arm]=load_prediction(p)
   assert graphs['B0'][2]==graphs['B0_repeat'][2]==graphs['F1_off'][2],'OFF_REPEAT_NOT_EQUIVALENT'
   gn,ge,total=read_gt(stem);gt_hash=plain_sha(gn,ge)
   removed=set(graphs['B0'][1])-set(graphs['F1'][1]);added=set(graphs['F1'][1])-set(graphs['B0'][1]);base=None
   for arm in ['B0','F1','B0_repeat','F1_off']:
    n,e,gh=graphs[arm];logarm=arm if arm in ['B0','F1'] else 'B0';logval=float(next(r[logarm] for r in logrows if r['stem']==stem))
    fp=dict(script_sha256=freeze['restore_scores_sha256'],pred_bytes_sha256=rawhash[arm],ordered_graph_sha256=gh,gt_plain_sha256=gt_hash,gt_byte_hashes=[r['sha256'] for r in manifest['gt'] if stem+'.geff/' in r['source']],scorer=SCORER,versions=env,n_total=total,scale=SCALE,radius=RADIUS)
    # JSON representation is frozen to the same list/tuple shape as stored.
    fp=json.loads(json.dumps(fp))
    def compute():
     started=time.monotonic();reuse=arm!='B0' and gh==graphs['B0'][2]
     if reuse:
      row=copy.deepcopy(base['metrics']);events=[]
     else:row,events=score(n,e,gn,ge,total,removed if arm=='B0' else added)
     return dict(stem=stem,arm=arm,metrics=row,log_score=logval,log_delta=row['score']-logval,graph_legal=True,repeat_and_off_equal=True,attribution_bijection_verified=True,events=events,changed_edges=len(removed if arm=='B0' else added) if arm in ['B0','F1'] else 0,reuse_of=f'{stem}_B0' if reuse else None,execution='GRAPH_EQUIVALENCE_REUSE' if reuse else 'LOCAL_CPU_OFFICIAL_SCORING',elapsed_seconds=time.monotonic()-started)
    c,reused=checkpoint(P/'checkpoints'/f'{stem}_{arm}.json',fp,compute)
    if arm=='B0':base=c
    allc.append(c);guard();print('CHECKPOINT',stem,arm,c['metrics']['score'],'RESUME' if reused else c['execution'],flush=True)
   del graphs,gn,ge
  atomic(P/'resource_result.json',dict(status='PILOT_COMPLETE' if args.pilot else 'SCORING_COMPLETE',startup_available_bytes=available,budget_bytes=budget,peak_rss_bytes=max(peak,resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),elapsed_seconds=time.monotonic()-start,processes=1,max_cpu_threads=2))
 except Exception as ex:
  atomic(P/'resource_result.json',dict(status='BLOCKED',error_type=type(ex).__name__,error=str(ex),peak_rss_bytes=peak,budget_bytes=budget,elapsed_seconds=time.monotonic()-start));raise
 finally:signal.setitimer(signal.ITIMER_REAL,0)
if __name__=='__main__':main()
