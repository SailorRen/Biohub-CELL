"""独立 Kaggle 子进程；父进程按全局截止时间执行硬终止。"""
import json
import resource
import sys
import time
import traceback
from pathlib import Path
import numpy as np
import zarr
import torch
from hoct import load_model
from hoct_observer import observe_video, InterfaceError
from source_helpers import _hv_rasterize_spheres

if __name__ == '__main__':
    job = json.loads(Path(sys.argv[1]).read_text())
    started = time.monotonic()
    result = dict(video=job['video'], input_hash=job['input_hash'], complete=False, covered=[], selected=[])
    try:
        v = json.loads(Path(job['graph']).read_text())
        nodes = {int(i): n for i,n in v['nodes']}
        volume = np.asarray(zarr.open(Path(job['train_dir'])/(job['video']+'.zarr')/'0', mode='r'))
        model = load_model(job['weights'], device='cuda')
        result = observe_video(job['video'],nodes,v['edges'],model,volume,_hv_rasterize_spheres,
                               job['start_monotonic'],job['deadline_s'])
    except Exception as exc:
        result['reason'] = type(exc).__name__ + ':' + str(exc)[:300]
        result['traceback'] = traceback.format_exc()
        result['status'] = 'INTERFACE_ERROR' if isinstance(exc, (InterfaceError, KeyError, AttributeError, TypeError, IndexError)) else 'WORKER_ERROR'
        result['observation'] = getattr(exc, 'observation', None)
        traceback.print_exc()
    result.update(seconds_total=time.monotonic()-started,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  peak_cuda_bytes=torch.cuda.max_memory_allocated())
    Path(job['result']).write_text(json.dumps(result,allow_nan=False)+'\n')
