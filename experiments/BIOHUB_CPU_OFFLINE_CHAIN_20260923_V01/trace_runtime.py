"""Small receipts; full reference tensors are temporary and never notebook Output."""
import hashlib,json,time,resource
from pathlib import Path
import numpy as np

def compare(a,b):
 if a.shape!=b.shape:return {'shape_reference':list(a.shape),'shape_candidate':list(b.shape),'allclose':False,'reason':'SHAPE_DIFFERENCE'}
 mx=total=rm=rt=0.;finite=True;close=True;a=a.ravel();b=b.ravel()
 for i in range(0,a.size,1048576):
  x=a[i:i+1048576].astype('float64');y=b[i:i+1048576].astype('float64');d=np.abs(x-y);r=d/np.maximum(np.abs(x),1e-12)
  finite &= bool(np.isfinite(x).all() and np.isfinite(y).all());close &= bool(np.allclose(x,y,atol=1e-4,rtol=1e-3,equal_nan=False));mx=max(mx,float(d.max(initial=0)));total+=float(d.sum());rm=max(rm,float(r.max(initial=0)));rt+=float(r.sum())
 return {'elements':a.size,'finite':finite,'allclose':close,'max_abs_error':mx,'mean_abs_error':total/max(a.size,1),'max_relative_error':rm,'mean_relative_error':rt/max(a.size,1),'relative_denominator_floor':1e-12,'atol':1e-4,'rtol':1e-3,'equal_nan':False}
class Trace:
 def __init__(self,arm,root):
  self.arm=arm;self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True);self.cache=Path('/tmp/cpu_chain_comparison');self.cache.mkdir(exist_ok=True);self.start=time.monotonic();self.calls={};self.fallback=0
 def event(self,stage,**kw):
  row={'arm':self.arm,'stage':stage,'elapsed_seconds':time.monotonic()-self.start,'peak_rss_kib_process_lifetime':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,**kw}
  with (self.root/'events.jsonl').open('a') as f:f.write(json.dumps(row,allow_nan=False,default=str)+'\n')
  print('CHAIN',json.dumps(row,allow_nan=False,default=str),flush=True)
 def tensor(self,key,value,threshold=None):
  a=value.detach().cpu().numpy() if hasattr(value,'detach') else np.asarray(value);f=self.cache/(key+'.npy');info={'key':key,'shape':list(a.shape),'dtype':str(a.dtype),'finite':bool(np.isfinite(a).all())}
  if self.arm=='reference':np.save(f,a);info['status']='REFERENCE_SAVED_TMP'
  elif f.exists():
   b=np.load(f,mmap_mode='r');info['comparison']=compare(b,a)
   if threshold is not None and b.shape==a.shape:info['threshold_changes']=int(np.count_nonzero((b>threshold)!=(a>threshold)));info['threshold']=threshold
  else:info['status']='UNMATCHED_CANDIDATE_CALL'
  self.event('numeric',**info)
 def window(self,frames,features,det,secondary):
  key='window_'+str(frames[0]);self.tensor(key+'_primary_features',features)
  for i,x in enumerate(det):self.tensor(key+'_det_'+str(i),x,float(np.log(.960/(1-.960)))) # logits decision also compared through actual coordinates
  if secondary is not None:self.tensor(key+'_secondary_features',secondary)
  self.event('window_completed',frames=list(frames))
 def edges(self,frames,src,tgt,coords,probs,threshold):
  key='edges_'+str(frames[0]);self.tensor(key+'_src_coords',coords[src]);self.tensor(key+'_tgt_coords',coords[tgt]);self.tensor(key+'_probabilities',probs,threshold)
 def wrap(self,name,fn):
  def wrapped(*a,**kw):
   t=time.monotonic();result=fn(*a,**kw);sec=time.monotonic()-t;c=self.calls.setdefault(name,{'calls':0,'seconds':0.,'input_shapes':[]});c['calls']+=1;c['seconds']+=sec
   if a and hasattr(a[0],'shape'):
    shape=list(a[0].shape)
    if shape not in c['input_shapes']:c['input_shapes'].append(shape)
   return result
  return wrapped
