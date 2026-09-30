"""唯一诊断 Save & Run。账本先落盘；任何未知响应都禁止重发。"""
import fcntl
import hashlib
import json
import os
import re
from pathlib import Path
from datetime import datetime,timezone
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest
P=Path(__file__).resolve().parent;R=P.parents[1]
def now():return datetime.now(timezone.utc).isoformat()
def event(v):
    with (P/'request_ledger.jsonl').open('a') as f:
        f.write(json.dumps(dict(at_utc=now(),**v))+'\n');f.flush();os.fsync(f.fileno())
if __name__=='__main__':
    with (R/'downloads/BIOHUB_SPRINT02_HOCT_20260917/write.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (P/'request_ledger.jsonl').read_text().strip(),'REQUEST_ALREADY_RESERVED_NO_RETRY'
        assert api.get_config_value(api.CONFIG_NAME_USER)=='sailorren'
        pre=json.loads((P/'preflight_api.json').read_text())
        assert pre['competition']['user_has_entered']=='True' and pre['gpu_remaining_hours']>2
        assert (datetime.now(timezone.utc)-datetime.fromisoformat(pre['observed_at_utc'])).total_seconds()<3600
        # Latest receipt stays ignored to avoid a self-referential receipt hash.
        checkpoint=json.loads((R/'downloads/BIOHUB_SPRINT02_HOCT_20260917/prewrite_remote.json').read_text())
        assert checkpoint['status']=='REMOTE_BYTES_VERIFIED'
        sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
        for f in checkpoint['files']:
            assert sha(R/f['path'])==f['remote_sha256'],'PREWRITE_FILE_DRIFT'
        assert not list(api.kernels_list(mine=True,search='Biohub S02 H1 Diagnostic 20260917',page_size=100)), 'TASK_KERNEL_FOUND_READ_BEFORE_WRITE'
        ref=json.loads((P/'diagnostic/kernel-metadata.json').read_text())['id']
        q=ApiGetKernelRequest();q.user_name,q.kernel_slug=ref.split('/')
        try:
            with api.build_kaggle_client() as c:c.kernels.kernels_api_client.get_kernel(q)
        except Exception as e:
            code=getattr(getattr(e,'response',None),'status_code',None)
            ui=json.loads((P/'kernel_absence_ui.json').read_text())
            assert code in (403,404) and ui['ref']==ref and ui['visible_text']=="We can't find that page.",'ABSENCE_UNPROVEN'
            assert (datetime.now(timezone.utc)-datetime.fromisoformat(ui['observed_at_utc'])).total_seconds()<600
        else:raise RuntimeError('EXISTING_TASK_KERNEL_NO_RESAVE')
        source=sha(P/'diagnostic/candidate.ipynb')
        assert source==json.loads((P/'diagnostic/build_receipt.json').read_text())['source_sha256']
        event(dict(action='SaveAndRun',stage='diagnostic',state='ATTEMPT_RESERVED',counted=1,ref=ref,source_sha256=source))
        try:
            response=api.kernels_push(str(P/'diagnostic'),timeout='43200',acc='NvidiaTeslaT4')
            fields=response.to_dict()
            safe={k:v for k,v in fields.items() if k.lower() in ['ref','url','versionnumber','version_number','kernelid','kernel_id','scriptversionid','script_version_id','error','title']}
            event(dict(action='SaveAndRun',stage='diagnostic',state='RESPONSE_RECEIVED_READBACK_REQUIRED',response=safe,response_keys=list(fields)))
            print(json.dumps(safe))
        except Exception as e:
            event(dict(action='SaveAndRun',stage='diagnostic',state='UNCERTAIN_OR_FAILED_NO_RETRY',error_type=type(e).__name__,error=re.sub(r'https?://\S+','[URL]',str(e))[:300]))
            raise
