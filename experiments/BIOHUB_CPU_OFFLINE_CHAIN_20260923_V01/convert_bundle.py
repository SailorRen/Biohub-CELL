"""Bounded real-input diagnostic only. Never execute the production notebook."""
import ast, contextlib, hashlib, importlib.util, json, math, os, resource, subprocess, sys, time, traceback
from pathlib import Path
ROOT=Path('/kaggle/working/cpu_bundle'); ROOT.mkdir(exist_ok=True)
START=time.monotonic(); DEADLINE=START+1800

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
    threads=2;torch.set_num_threads(threads);torch.set_num_interop_threads(1)
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
    W=2;ds=(1,4,4)
    comp=next(p for p in [Path('/kaggle/input/competitions/biohub-cell-tracking-during-development'),Path('/kaggle/input/biohub-cell-tracking-during-development')] if p.exists())
    movies=sorted((comp/'test').glob('*.zarr'),key=lambda p:p.stem);assert movies
    movie=movies[0];g=zarr.open_group(str(movie),mode='r'); arr=g['0'];attrs=dict(g.attrs);scale=ns['_parse_scale'](attrs);q=attrs['image_statistics']['quantiles'];ql=float(q['0.001']);qh=float(q['0.999']);shape=list(arr.shape);target=[-(-s//d) for s,d in zip(shape[1:],ds)];assert shape[0]>=W
    assert movie.stem=='44b6_0113de3b'
    selected=[0]
    other=[]
    for path in movies[1:]:
        shape2=list(zarr.open_group(str(path),mode='r')['0'].shape)
        if shape2[1:]!=shape[1:]:
            other=[{'video':path.stem,'raw_shape':shape2,'window':[0,1]}];break
    manifest={'video':movie.stem,'raw_shape':shape,'frames':list(range(16)), 'original_last_frame':shape[0]-1,'segment_end_is_true_end':False,'coordinate_mapping':'identity original frame and voxel coordinates','window':W,'downsample':list(ds),'batch':1,'selector_mode':'FIXED_DIAGNOSTIC_CONFIG','additional_native_shape_window':other,'shape_generalization':'SELECTED_NOT_RUN' if other else 'SHAPE_GENERALIZATION_NOT_COVERED','context':{'minimum_track':6,'rescue_minimum':4,'window':2,'smoothing_radius':2,'segment_length':16},'boundary_effect':'truncation can affect future association, division, rescue and smoothing; original last-frame protection remains true video end'}
    (ROOT/'sample_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    receipt('02_samples_frozen',**manifest)
    model,W,ds=ns['load_model'](weights,torch.device('cpu'));model.float();assert W==2 and ds==(1,4,4)
    receipt('01_model_loaded',weight_sha256=wh,source_sha256=actual,load_hash_build_seconds=time.monotonic()-t,window=W,downsample=ds,actual_batch=1,original_cli_unet_batch_size=4,cli_batch_note='original predict_video encodes one window; argument unused',torch=torch.__version__,openvino=ov.__version__,threads=torch.get_num_threads(),interop=torch.get_num_interop_threads(),cuda_available=False,parameter_dtypes=sorted({str(p.dtype) for p in model.parameters()}))
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
    enc=Encoder(model).eval()
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
    outputs=cm([xs[0].numpy()])
    receipt('08_reload_inference',output_shapes=[list(outputs[o].shape) for o in cm.outputs],finite=[bool(np.isfinite(outputs[o]).all()) for o in cm.outputs],note='preparation connected session; NOT an offline proof')
    runtime=cm.get_runtime_model()
    execution_precisions={}
    for op in runtime.get_ops():
        info=op.get_rt_info()
        if 'runtimePrecision' in info:
            k=str(info['runtimePrecision']);execution_precisions[k]=execution_precisions.get(k,0)+1
    receipt('09_precision',execution_precisions=execution_precisions)

if __name__=='__main__':
    try:main()
    except BaseException as e:
        receipt('99_error',error=str(e),traceback=traceback.format_exc());raise
