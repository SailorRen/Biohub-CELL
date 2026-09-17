"""仅更新既有对象一次；先持久化预算，无自动重试。"""
import fcntl,hashlib,json,os,sys,subprocess
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;R=P.parents[2]
sys.path.insert(0,str(R/'experiments/TARGET950_RUN_20260914'))
from kaggle_io import kernel,old
from kaggle import api
from kagglesdk.competitions.types.competition_api_service import ApiGetCompetitionRequest
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def event(**v):
    with (P/'request_ledger.jsonl').open('a') as f:
        f.write(json.dumps(dict(at_utc=datetime.now(timezone.utc).isoformat(),**v))+'\n');f.flush();os.fsync(f.fileno())
if __name__=='__main__':
    with (R/'downloads/BIOHUB_SPRINT02_HOCT_20260917/write.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (P/'request_ledger.jsonl').read_text().strip(),'ALREADY_RESERVED_READ_ONLY'
        assert subprocess.check_output(['git','branch','--show-current'],cwd=R).decode().strip()=='codex/sprint02-hoct-20260917'
        contract=json.loads((P/'run_contract.json').read_text())
        for name,digest in contract['frozen_files'].items():assert sha(R/name)==digest,name
        checkpoint=json.loads((R/'downloads/BIOHUB_SPRINT02_HOCT_20260917/rerun_prewrite_remote.json').read_text())
        assert checkpoint['status']=='REMOTE_BYTES_VERIFIED'
        assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()==checkpoint['commit']
        for row in checkpoint['files']:assert sha(R/row['path'])==row['remote_sha256'],row['path']
        assert api.get_config_value(api.CONFIG_NAME_USER)=='sailorren'
        ref=contract['ref'];k,source=kernel(api,ref)
        previous=json.loads((P/'preflight.json').read_text())['kernel']
        assert k==previous,'TARGET_CHANGED_NO_WRITE'
        status=str(api.kernels_status(ref).to_dict()['status']).split('.')[-1].upper()
        assert status=='COMPLETE' and k['kernel_id']==134683728 and k['version']==1
        q=ApiGetCompetitionRequest();q.competition_name='biohub-cell-tracking-during-development'
        with api.build_kaggle_client() as c:comp=c.competitions.competition_api_client.get_competition(q)
        assert comp.user_has_entered
        quota=api.quota_view().gpu_quota
        remaining=(quota.total_time_allowed-quota.time_used).total_seconds()/3600
        assert remaining>=10,'INSUFFICIENT_GPU_BUDGET'
        meta=json.loads((P/'kernel-metadata.json').read_text())
        assert meta['id']==ref and meta['code_file']=='diagnostic_launch.ipynb'
        event(state='ATTEMPT_RESERVED',task_id=contract['task_id'],counted=1,ref=ref,previous_kernel=k,
              source_sha256=sha(P/'diagnostic_launch.ipynb'),metadata_sha256=sha(P/'kernel-metadata.json'),gpu_remaining_hours=remaining)
        op={}
        try:
            with old.single_write_transport(api,'save',op):
                response=api.kernels_push(str(P),timeout='43200',acc='NvidiaTeslaT4')
            fields=response.to_dict()
            safe={n:v for n,v in fields.items() if n.lower() in ('ref','url','versionnumber','version_number','kernelid','kernel_id','scriptversionid','script_version_id','error','title') or n.startswith('invalid')}
            event(state='RESPONSE_RECEIVED_READBACK_REQUIRED',response=safe,transport=op)
            print(json.dumps(safe))
        except BaseException as e:
            event(state='UNCERTAIN_OR_FAILED_NO_RETRY',error_type=type(e).__name__,transport=op)
            raise
