"""Two genuine sequential short chains, no selector and no formal submission."""
import ast,csv,hashlib,importlib.util,json,os,resource,shutil,sys,time,traceback
from pathlib import Path
HERE=Path(__file__).parent;ROOT=Path('/kaggle/working/cpu_offline_chain');ROOT.mkdir(exist_ok=True)
sys.path.insert(0,str(HERE/'source'));sys.path.insert(0,str(HERE))
from trace_runtime import Trace

def sha(p):return hashlib.file_digest(open(p,'rb'),'sha256').hexdigest()
def mount(owner,slug,kind='datasets'):
 paths=[Path('/kaggle/input')/kind/owner/slug,Path('/kaggle/input')/slug]
 return next(p for p in paths if p.is_dir())
def main():
 import torch,numpy as np,openvino as ov,tracksdata as td
 torch.set_grad_enabled(False);torch.set_num_threads(2);torch.set_num_interop_threads(1);torch.set_float32_matmul_precision('highest');torch.backends.mha.set_fastpath_enabled(False)
 for name in ['matmul','conv','rnn']:
  backend=getattr(torch.backends.mkldnn,name,None)
  if backend is not None and hasattr(backend,'fp32_precision'):backend.fp32_precision='ieee'
 assert not torch.cuda.is_available()
 bundle=Path(os.environ['CPU_BUNDLE']);sample=json.loads((bundle/'sample_manifest.json').read_text());assert sample['frames']==list(range(16))
 primary=mount('pilkwang','biohub-tracking-support-pack-50ep-v1');secondary=mount('pilkwang','biohub-temporal-unet3d-seed314159-v1');dc=mount('pilkwang','biohub-deepcenter-unet3d-center-prior-v1');gate=mount('sailorren','biohub-division-train-20260914','kernels')
 weights={'primary':primary/'weights/unet_transformer/split_0/edge_predictor_best.pth','secondary':secondary/'weights/unet_transformer/split_0/edge_predictor_best.pth','deepcenter':dc/'weights/full_frame_center/best.pt'}
 expected={'primary':'12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771','secondary':'9bac2fa0dadc4a6fc1899e0caf187f4b553e0a7cd90ba1261a68b35ffe9e305f','deepcenter':'8040999a92f6b7bbd98fa8cf458141e045c0f9ad7c936bdb3b18e1f7edafe2a0'}
 for k,p in weights.items():assert sha(p)==expected[k],k
 for n,h in json.loads((HERE/'source_hashes.json').read_text()).items():assert sha(primary/'repo'/n)==h
 repo=Path('/tmp/cpu_chain_repo');shutil.copytree(primary/'repo',repo)
 shutil.copy2(HERE/'source/predict_unet_transformer.py',repo/'scripts/predict_unet_transformer.py')
 sys.path.insert(0,str(repo/'src'));sys.path.insert(0,str(repo/'scripts'))
 import predict_unet_transformer as pred
 results={}
 for arm in ['reference','cpu']:
  tr=Trace(arm,ROOT/arm);pred.TRACE=tr;arm_start=time.monotonic()
  g={'__name__':'diagnostic_configuration'}
  for i in [1,2,3]:exec(compile((HERE/f'source/config_{i}.py').read_text(),f'config_{i}','exec'),g)
  os.environ.update(BIOHUB_EDGE_FEATURE_TTA='1',BIOHUB_SECONDARY_EDGE_FEATURE_TTA='1',BIOHUB_SECONDARY_EDGE_FEATURE_TTA_WEIGHT='0.75',BIOHUB_GPU_SHARD=arm)
  g.update(REPO_DIR=Path('/tmp')/('chain_'+arm),WORKING_DIR=ROOT/arm,SUBMISSION_PATH=ROOT/('diagnostic_reference.csv' if arm=='reference' else 'diagnostic_cpu.csv'),RUN_STATS_PATH=ROOT/arm/'run_stats.csv',GATE_ROOT=gate,EXACT_DC_WEIGHT=weights['deepcenter'],test_stems=[sample['video']],_trio_rescue_rows=[])
  tr.event('configuration',selector_mode='FIXED_DIAGNOSTIC_CONFIG',config=g['CONFIG_DISPLAY'],weights=expected,threads=torch.get_num_threads(),interop=torch.get_num_interop_threads(),cpu_max=Path('/sys/fs/cgroup/cpu.max').read_text().strip(),memory_max=Path('/sys/fs/cgroup/memory.max').read_text().strip(),affinity=len(os.sched_getaffinity(0)),cpu_model=next(x for x in Path('/proc/cpuinfo').read_text().splitlines() if x.startswith('model name')))
  t=time.monotonic();model,W,ds=pred.load_model(weights['primary'],torch.device('cpu'));model.float();second,W2,ds2=pred.load_model(weights['secondary'],torch.device('cpu'));second.float();assert W==W2==2 and ds==ds2==(1,4,4)
  tr.event('dual_model_loaded',seconds=time.monotonic()-t)
  original_encode=model.encode
  if arm=='cpu':
   core=ov.Core();t=time.monotonic();ir=core.read_model(bundle/'encoder.xml');cm=core.compile_model(ir,'CPU',{'INFERENCE_PRECISION_HINT':'f32','INFERENCE_NUM_THREADS':2,'NUM_STREAMS':1,'PERFORMANCE_HINT':'LATENCY'})
   properties={k:str(cm.get_property(k)) for k in ['INFERENCE_PRECISION_HINT','INFERENCE_NUM_THREADS','NUM_STREAMS','PERFORMANCE_HINT']};assert 'float32' in properties['INFERENCE_PRECISION_HINT'] or 'f32' in properties['INFERENCE_PRECISION_HINT']
   shape=list(cm.input().shape);tr.event('offline_IR_loaded_compiled',seconds=time.monotonic()-t,properties=properties,input_shape=shape,constant_types=sorted({str(n.get_output_element_type(0)) for n in ir.get_ops() if n.get_type_name()=='Constant'}))
   def encode(x):
    if list(x.shape)!=shape:
     tr.fallback+=1;tr.event('shape_fallback',actual=list(x.shape),compiled=shape);return original_encode(x)
    vals=cm([x.detach().numpy()]);outputs=[torch.from_numpy(vals[o].copy()) for o in cm.outputs];return outputs[0],outputs[1:]
   model.encode=encode
  model.encode=tr.wrap('primary_encode',model.encode);model.predict_edges=tr.wrap('primary_association_forward_reverse',model.predict_edges)
  second.encode=tr.wrap('secondary_encode',second.encode);second.predict_edges=tr.wrap('secondary_association',second.predict_edges)
  exec(compile((HERE/'source/postprocess.py').read_text(),'postprocess.py','exec'),g)
  t=time.monotonic();g['DEEPCENTER_VETO_DETECTOR']=g['load_deepcenter_veto_detector']();tr.event('deepcenter_loaded',seconds=time.monotonic()-t)
  dm=g['DEEPCENTER_VETO_DETECTOR']['model'];dm.forward=tr.wrap('deepcenter_forward',dm.forward)
  for name in ['motion_relink_edges','close_single_frame_gaps','recover_strict_gap2','add_safe_divisions_postlink','filter_short_track_components','prune_leaves','linefit_smooth_output_graph','deepcenter_score_point','_sprint_score']:
   if name in g:g[name]=tr.wrap(name,g[name])
  original_dc=g['deepcenter_score_point']
  def dc_score(*args,**kw):
   value=original_dc(*args,**kw)
   if value is not None:
    key='dc_'+hashlib.sha256(json.dumps([args[0],args[1],args[2]],default=str).encode()).hexdigest()[:20]
    tr.tensor(key,np.asarray([value]));tr.event('deepcenter_decision',key=key,score=value,gap_pass=value>=g['DEEPCENTER_GAP_THRESHOLD'],division_pass=value>=g['DEEPCENTER_SAFE_DIV_THRESHOLD'])
   return value
  g['deepcenter_score_point']=dc_score
  original_gate=g['_sprint_score']
  def gate_score(*args,**kw):
   value=original_gate(*args,**kw)
   if value is not None:
    key='gate_'+hashlib.sha256(json.dumps(args[1:],default=str).encode()).hexdigest()[:20];tr.tensor(key,np.asarray([value]),.95)
   return value
  g['_sprint_score']=gate_score
  t=time.monotonic();cfg=pred.PredictConfig(det_threshold=.960,use_ilp=True,ilp_edge_weight=-1.,ilp_appearance_weight=0.,ilp_disappearance_weight=2.,ilp_division_weight=1.2,threshold=.48)
  coords,edges=pred.predict_video(model,g['TEST_DIR']/(sample['video']+'.zarr'),torch.device('cpu'),cfg=cfg,window_size=W,max_frames=16,unet_batch_size=4,downsample=ds,secondary_model=second,secondary_edge_weight=.15,secondary_detection_weight=.80,secondary_link_mode='low_margin_consensus',secondary_mix_temperature=1.,secondary_low_margin_max=.35)
  g['predict_seconds']=time.monotonic()-t;tr.tensor('final_detections',coords);tr.event('dual_inference_completed',seconds=g['predict_seconds'],nodes=len(coords),edges=len(edges),calls=tr.calls)
  t=time.monotonic();graph=pred.build_graph(coords,edges)
  if graph.num_edges()>0:
   solver=td.solvers.ILPSolver(edge_weight=cfg.ilp_edge_weight*td.EdgeAttr('edge_prob'),appearance_weight=cfg.ilp_appearance_weight,disappearance_weight=cfg.ilp_disappearance_weight,division_weight=cfg.ilp_division_weight)
   graph=solver.solve(graph);tr.event('ILP',status='EXECUTED',seconds=time.monotonic()-t)
  else:tr.event('ILP',status='NOT_TRIGGERED_NO_EDGES')
  folder=g['REPO_DIR']/'predictions'/arm/'unet_transformer/split_0';folder.mkdir(parents=True);pred.save_graph(graph,folder/(sample['video']+'.geff'))
  t=time.monotonic();g['write_test_submission']('FIXED_DIAGNOSTIC_CONFIG');tr.event('postprocess_and_csv',seconds=time.monotonic()-t,calls=tr.calls,gate=g['SPRINT_CALLS'],rescue=g['_trio_rescue_rows'])
  from diagnostic_validate import validate
  check=validate(g['SUBMISSION_PATH'],sample);results[arm]={'check':check,'seconds':time.monotonic()-arm_start,'calls':tr.calls,'shape_fallbacks':tr.fallback};tr.event('arm_completed',**results[arm])
  for extra in sample['additional_native_shape_window']:
   import zarr
   path=g['TEST_DIR']/(extra['video']+'.zarr');zg=zarr.open_group(str(path),mode='r');arr=zg['0'];target=[-(-v//d) for v,d in zip(arr.shape[1:],ds)];quant=zg.attrs['image_statistics']['quantiles'];lo=float(quant['0.001']);hi=float(quant['0.999'])
   x=torch.stack([pred._load_frame(arr,i,target,ds) for i in [0,1]]);x=((x-lo)/(hi-lo+1e-6)).clamp(0).unsqueeze(0).float().contiguous()
   t=time.monotonic();feat,dets=model.encode(x);tr.tensor('additional_native_features',feat)
   for i,det in enumerate(dets):tr.tensor('additional_native_det_'+str(i),det)
   tr.event('native_shape_window',video=extra['video'],raw_shape=list(arr.shape),input_shape=list(x.shape),seconds=time.monotonic()-t,shape_fallbacks=tr.fallback,note='shape-keyed PT fallback does not verify OpenVINO conditional-shape generalization')
  results[arm]['shape_fallbacks']=tr.fallback
  del model,second,graph,dm
 results['final_graph_equal']=results['reference']['check']['id_independent_sha256']==results['cpu']['check']['id_independent_sha256']
 results['status']='SHORT_CHAIN_EXECUTED_CHECK_NUMERIC_EVENTS';results['limitations']=['full selector NOT_VALIDATED','GPU equivalence NOT_VALIDATED','full video and hidden test timing NOT_VALIDATED','formal submission NOT_RUN'];(ROOT/'result.json').write_text(json.dumps(results,indent=2)+'\n')
if __name__=='__main__':
 try:main()
 except BaseException as e:
  (ROOT/'error.json').write_text(json.dumps({'status':'STOPPED_ERROR','error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()},indent=2)+'\n');raise
