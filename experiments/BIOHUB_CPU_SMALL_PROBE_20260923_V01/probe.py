"""Bounded real-input diagnostic only. Never execute the production notebook."""
import ast, contextlib, hashlib, importlib.util, json, math, os, resource, subprocess, sys, time, traceback
from pathlib import Path
ROOT=Path('/kaggle/working/cpu_small_probe'); ROOT.mkdir(exist_ok=True)
START=time.monotonic(); DEADLINE=START+45*60

def receipt(stage, **data):
    data.update(stage=stage,utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),elapsed_seconds=time.monotonic()-START,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    p=ROOT/(stage+'.json'); tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n');tmp.replace(p)
    print('RECEIPT',json.dumps(data,allow_nan=False),flush=True)
    return data

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def guard():
    if time.monotonic()>=DEADLINE:raise TimeoutError('45 minute conversion/testing budget exhausted')

def select_defs(path,names,namespace):
    tree=ast.parse(path.read_text());nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
    assert {n.name for n in nodes}==set(names)
    # Exact function/class AST; excludes all training and full-video entrypoints.
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),namespace)

def main():
    import numpy as np, torch, torch.nn as nn, torch.nn.functional as F, zarr, openvino as ov
    from torch.utils.checkpoint import checkpoint as grad_ckpt
    from collections.abc import Sequence
    torch.set_grad_enabled(False);torch.set_default_dtype(torch.float32)
    threads=int(os.environ['PROBE_THREADS']);torch.set_num_threads(threads);torch.set_num_interop_threads(1)
    torch.set_float32_matmul_precision('highest')
    # Tracing-compatible eager attention path, equally used by PT reference and conversion.
    torch.backends.mha.set_fastpath_enabled(False)
    for name in ['matmul','conv','rnn']:
        backend=getattr(torch.backends.mkldnn,name,None)
        if backend is not None and hasattr(backend,'fp32_precision'):backend.fp32_precision='ieee'
    assert not torch.cuda.is_available(), 'CPU session required'
    support=Path('/kaggle/input/datasets/pilkwang/biohub-tracking-support-pack-50ep-v1')
    repo=support/'repo'; weights=support/'weights/unet_transformer/split_0/edge_predictor_best.pth'
    expected=json.loads((ROOT/'source_hashes.json').read_text())
    actual={n:sha(repo/n) for n in expected}; assert actual==expected, 'support source checksum mismatch'
    t=time.monotonic();wh=sha(weights);assert wh=='12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771'
    ns={'torch':torch,'nn':nn,'F':F,'np':np,'Path':Path,'json':json,'math':math,'Sequence':Sequence,'grad_ckpt':grad_ckpt,'_grad_ckpt':grad_ckpt,'_POS_EMBED_DIM':8,'DEFAULT_SCALE':(1.625,.40625,.40625)}
    select_defs(repo/'src/biohub_tracking/models/temporal_unet.py',['_conv_block','_TemporalAttention','TemporalUNet3D'],ns)
    select_defs(repo/'src/biohub_tracking/models/simple_node_transformer.py',['CrossAttentionBlock','SimpleNodeTransformer'],ns)
    select_defs(repo/'scripts/train_unet_transformer.py',['UNetNodeTransformer','extract_pos_features'],ns)
    ns['_DEFAULT_CONFIG']={'unet_out_channels':32,'unet_layers':[32,64,128],'downsample':[1,4,4],'window_size':2}
    select_defs(repo/'scripts/predict_unet_transformer.py',['load_model','_load_frame','pool_kernel_from_um','_detect_cells_pooled'],ns)
    select_defs(repo/'src/biohub_tracking/io.py',['_parse_scale'],ns)
    model,W,ds=ns['load_model'](weights,torch.device('cpu'));model.float();assert W==2 and ds==(1,4,4)
    receipt('01_model_loaded',weight_sha256=wh,source_sha256=actual,load_hash_build_seconds=time.monotonic()-t,window=W,downsample=ds,actual_batch=1,original_cli_unet_batch_size=4,cli_batch_note='original predict_video encodes one window; argument unused',torch=torch.__version__,openvino=ov.__version__,threads=torch.get_num_threads(),interop=torch.get_num_interop_threads(),cuda_available=False,parameter_dtypes=sorted({str(p.dtype) for p in model.parameters()}))
    comp=next(p for p in [Path('/kaggle/input/competitions/biohub-cell-tracking-during-development'),Path('/kaggle/input/biohub-cell-tracking-during-development')] if p.exists())
    movies=sorted((comp/'test').glob('*.zarr'),key=lambda p:p.stem);assert movies
    movie=movies[0];g=zarr.open_group(str(movie),mode='r'); arr=g['0'];attrs=dict(g.attrs);scale=ns['_parse_scale'](attrs);q=attrs['image_statistics']['quantiles'];ql=float(q['0.001']);qh=float(q['0.999']);shape=list(arr.shape);target=[-(-s//d) for s,d in zip(shape[1:],ds)];assert shape[0]>=W
    starts=list(range(0,shape[0]-W+1,max(W-1,1))); selected=[starts[0],starts[len(starts)//2]];assert selected[0]!=selected[1]
    pool=ns['pool_kernel_from_um'](3.0,tuple(s*d for s,d in zip(scale,ds))) # actual PredictConfig default, not weight config pool=5
    receipt('02_samples_frozen',video=movie.stem,public_video_count=len(movies),raw_shape=shape,window_starts=selected,frame_indices=[[s,s+1] for s in selected],target_spatial_shape=target,normalization={'q001':ql,'q999':qh,'formula':'((x-q001)/(q999-q001+1e-6)).clamp(0)'},scale=scale,pool_kernel=pool,det_threshold=.960,edge_threshold=.48,actual_batch=1,tta='NOT_RUN: single encode module only',reverse_time='NOT_RUN')
    xs=[];t=time.monotonic()
    for s in selected:
        x=torch.stack([ns['_load_frame'](arr,i,target,ds) for i in range(s,s+W)])
        x=((x-ql)/(qh-ql+1e-6)).clamp(0).unsqueeze(0).float().contiguous();assert list(x.shape)==[1,W,*target];xs.append(x)
    receipt('03_real_inputs_loaded',seconds=time.monotonic()-t,shapes=[list(x.shape) for x in xs],dtypes=[str(x.dtype) for x in xs],finite=[bool(torch.isfinite(x).all()) for x in xs],input_sha256=[hashlib.sha256(x.numpy().tobytes()).hexdigest() for x in xs])
    class Encoder(nn.Module):
        def __init__(self,m):super().__init__();self.m=m;self.calls=0
        def forward(self,x):
            self.calls+=1
            feat,det=self.m.encode(x)
            return (feat,*det)
    enc=Encoder(model).eval();pt=[];pt_times=[]
    for i,x in enumerate(xs):
        guard();t=time.monotonic();out=tuple(y.detach().numpy().copy() for y in enc(x));sec=time.monotonic()-t;pt.append(out);pt_times.append(sec)
        receipt('04_pt_window_'+str(i),seconds=sec,output_shapes=[list(y.shape) for y in out],finite=[bool(np.isfinite(y).all()) for y in out],dtypes=[str(y.dtype) for y in out],first_inference=i==0)
    guard();t=time.monotonic();before=enc.calls
    converted=ov.convert_model(enc,example_input=xs[0],input=list(xs[0].shape))
    conversion_seconds=time.monotonic()-t
    receipt('05_converted',seconds=conversion_seconds,example_input_window=selected[0],tracing_forward_calls=enc.calls-before,outputs=len(converted.outputs))
    assert len(converted.outputs)==3
    t=time.monotonic();ov.save_model(converted,ROOT/'encoder.xml',compress_to_fp16=False)
    receipt('06_saved',seconds=time.monotonic()-t,compress_to_fp16=False,xml_bytes=(ROOT/'encoder.xml').stat().st_size,bin_bytes=(ROOT/'encoder.bin').stat().st_size,xml_sha256=sha(ROOT/'encoder.xml'),bin_sha256=sha(ROOT/'encoder.bin'))
    del converted
    core=ov.Core();t=time.monotonic();reloaded=core.read_model(ROOT/'encoder.xml');reload_seconds=time.monotonic()-t
    const_types=sorted({str(n.get_output_element_type(0)) for n in reloaded.get_ops() if n.get_type_name()=='Constant'})
    assert all('float16' not in x and 'bfloat16' not in x and x not in ['f16','bf16'] for x in const_types)
    opts={'INFERENCE_PRECISION_HINT':'f32','INFERENCE_NUM_THREADS':threads,'NUM_STREAMS':1,'PERFORMANCE_HINT':'LATENCY'}
    t=time.monotonic();cm=core.compile_model(reloaded,'CPU',opts);compile_seconds=time.monotonic()-t
    props={k:str(cm.get_property(k)) for k in opts};assert 'f32' in props['INFERENCE_PRECISION_HINT'] or 'float32' in props['INFERENCE_PRECISION_HINT']
    receipt('07_reloaded_compiled',reload_seconds=reload_seconds,compile_seconds=compile_seconds,device='CPU',requested=opts,actual_properties=props,constant_types=const_types,output_types=[str(x.get_element_type()) for x in reloaded.outputs],offline_reload='local IR read/compile; network isolation NOT_VERIFIED')
    def infer_ov(x):
        outputs=cm([x.numpy()]);return tuple(outputs[o].copy() for o in cm.outputs)
    def compare(a,b):
        assert a.shape==b.shape
        maximum=0.;total=0.;relmax=0.;reltotal=0.;close=True;finite=True
        aa=a.ravel();bb=b.ravel()
        for start in range(0,aa.size,1048576):
            av=aa[start:start+1048576].astype(np.float64);bv=bb[start:start+1048576].astype(np.float64);diff=np.abs(av-bv);rel=diff/np.maximum(np.abs(av),1e-12)
            finite=finite and bool(np.isfinite(av).all() and np.isfinite(bv).all());close=close and bool(np.allclose(av,bv,atol=1e-4,rtol=1e-3,equal_nan=False));maximum=max(maximum,float(diff.max()));total+=float(diff.sum());relmax=max(relmax,float(rel.max()));reltotal+=float(rel.sum())
        return {'shape':list(a.shape),'finite':finite,'max_abs_error':maximum,'mean_abs_error':total/aa.size,'max_relative_error':relmax,'mean_relative_error':reltotal/aa.size,'relative_denominator_floor':1e-12,'allclose':close,'atol':1e-4,'rtol':1e-3,'equal_nan':False}
    ov_times=[];ov_outs=[];all_ok=True;decisions=[]
    for i,x in enumerate(xs):
        guard();t=time.monotonic();o=infer_ov(x);sec=time.monotonic()-t;ov_outs.append(o);ov_times.append(sec)
        comparisons=[compare(a,b) for a,b in zip(pt[i],o)];all_ok=all_ok and all(v['allclose'] and v['finite'] for v in comparisons)
        coords=[]
        for j in range(W):
            c=ns['_detect_cells_pooled'](torch.from_numpy(pt[i][j+1][0]),selected[i]+j,.960,pool);d=ns['_detect_cells_pooled'](torch.from_numpy(o[j+1][0]),selected[i]+j,.960,pool)
            cs={tuple(v) for v in c.tolist()};dsset={tuple(v) for v in d.tolist()};coords.append({'frame':selected[i]+j,'pytorch_nodes':len(c),'openvino_nodes':len(d),'coordinates_equal':cs==dsset,'only_pytorch':len(cs-dsset),'only_openvino':len(dsset-cs)})
        decisions.append(coords);receipt('08_comparison_window_'+str(i),seconds=sec,first_inference=i==0,comparisons=comparisons,detection_decisions=coords)
    # First call per backend is the sole warm-up; sample1 is timed call1.
    timing={'pytorch':{'first_and_warmup_seconds':pt_times[0],'timed_seconds':[pt_times[1]],'warmups':1},'openvino':{'first_and_warmup_seconds':ov_times[0],'timed_seconds':[ov_times[1]],'warmups':1}}
    if all_ok:
        for backend,func in [('pytorch',lambda x:enc(x)),('openvino',infer_ov)]:
            estimate=max(pt_times if backend=='pytorch' else ov_times)
            for _ in range(2):
                if DEADLINE-time.monotonic()<estimate*1.5+90:break
                guard();t=time.monotonic();out=func(xs[1]);timing[backend]['timed_seconds'].append(time.monotonic()-t);del out
    receipt('09_timing',backends=timing,threads=threads,batch=1,conversion_tracing_excluded=True)
    association={'status':'NOT_RUN_NUMERIC_GATE_FAILED' if not all_ok else 'NOT_RUN_TIME_BUDGET'}
    if all_ok and DEADLINE-time.monotonic()>90:
        # Exactly one genuine adjacent frame pair, same real PT detections for feature comparison.
        c=[]
        for j in range(W):c.append(ns['_detect_cells_pooled'](torch.from_numpy(pt[1][j+1][0]),j,.960,pool))
        if any(len(v)==0 for v in c):association={'status':'NOT_RUN_NO_REAL_NODES','node_counts':[len(v) for v in c]}
        else:
            coords=[torch.from_numpy(v[:,1:].astype(np.float32)).unsqueeze(0) for v in c];mask=[torch.ones(1,len(v),dtype=torch.bool) for v in c];pos=[torch.from_numpy(ns['extract_pos_features'](v,(W,*target))).unsqueeze(0) for v in c];ds_t=torch.tensor(ds,dtype=torch.float32)
            probs=[];secs=[]
            for features in [pt[1][0],ov_outs[1][0]]:
                guard();t=time.monotonic();f=torch.from_numpy(features);indexed=[model._index_features(f[:,j],coords[j],mask[j]) for j in range(W)];raw=model.predict_edges(indexed[0],indexed[1],coords[0]*ds_t,coords[1]*ds_t,pos[0],pos[1],mask[0],mask[1])[0];probs.append(torch.softmax(raw,dim=0).numpy());secs.append(time.monotonic()-t)
            association={'status':'EXECUTED_PYTORCH_CPU_ONE_PAIR_TWO_FEATURE_SOURCES','node_counts':[len(v) for v in c],'probabilities':compare(*probs),'threshold':.48,'threshold_decisions_changed':int(np.count_nonzero((probs[0]>.48)!=(probs[1]>.48))),'seconds':secs,'bidirectional_fusion':'NOT_RUN','secondary':'NOT_RUN','note':'same genuine PT nodes/masks; encoder decision differences reported separately; original direct predict_edges only'}
    receipt('10_association',**association)
    receipt('11_complete',status='CORE_ENCODER_SMALL_SAMPLE_PASS' if all_ok else 'NUMERICAL_GATE_FAILED',allclose=all_ok,detection_decisions_changed=any(not x['coordinates_equal'] for row in decisions for x in row),association_status=association['status'],not_tested=['GPU equivalence','D4 TTA','reverse-time fusion','secondary','DeepCenter','gate','full selector','full-video graph optimization','competition scoring'],full_cpu='NOT_VERIFIED',formal_submission='NOT_RUN')

if __name__=='__main__':
    try:main()
    except BaseException as e:
        receipt('99_error',status='STOPPED_ERROR',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc()[-16000:]);raise
