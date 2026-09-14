"""Task-local API operations. No submission listing or score query exists here."""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

P=Path(__file__).resolve().parent
ROOT=P.parents[1]
RAW=ROOT/'downloads/DIVISION_TRAIN_20260914'
REF='sailorren/biohub-division-train-20260914'
COMP='biohub-cell-tracking-during-development'
TASK='DIVISION_TRAIN_20260914'
spec=importlib.util.spec_from_file_location('single_transport',ROOT/'experiments/PUBLIC946_TTA_20260908/execute_once.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
put,require,sha=helper.atomic_write,helper.require,helper.sha
now=lambda:datetime.now(timezone.utc).isoformat()


def local_gate():
    manifest=json.loads((P/'manifest.json').read_text())
    for path,digest in manifest['files'].items():
        require(sha((ROOT/path).read_bytes())==digest,'Frozen source changed: '+path)
    return manifest


def preflight(api):
    from kagglesdk.competitions.types.competition_api_service import ApiGetCompetitionRequest
    req=ApiGetCompetitionRequest();req.competition_name=COMP
    with api.build_kaggle_client() as c:r=c.competitions.competition_api_client.get_competition(req)
    q=api.quota_view();g=q.gpu_quota
    out={'task_id':TASK,'observed_at_utc':now(),'principal':api.get_config_value(api.CONFIG_NAME_USER),
         'user_has_entered':r.user_has_entered,'submissions_disabled':r.submissions_disabled,
         'code_only':r.is_kernels_submissions_only,'max_daily_submissions':r.max_daily_submissions,
         'gpu_remaining_seconds':(g.total_time_allowed-g.time_used-g.time_reserved).total_seconds() if g else None,
         'submission_scores_queried':False}
    put(P/'platform_preflight.json',out)
    require(out['principal']=='sailorren' and out['user_has_entered'] and not out['submissions_disabled'] and out['code_only'],'Platform/account unavailable')
    return out


def kernel(api):
    from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest
    req=ApiGetKernelRequest();req.user_name,req.kernel_slug=REF.split('/')
    with api.build_kaggle_client() as c:r=c.kernels.kernels_api_client.get_kernel(req)
    source=r.blob.source;meta=r.metadata;remote=json.loads(source)
    local=json.loads((P/'candidate.ipynb').read_text())
    for cell in local['cells']:cell['source']=''.join(cell['source'])
    require(remote==local,'Entire remote notebook differs from local SDK object')
    ref=str(meta.ref).removeprefix('https://www.kaggle.com').removeprefix('/code/')
    require(ref==REF,'Unexpected canonical Notebook')
    out={'task_id':TASK,'observed_at_utc':now(),'ref':ref,'kernel_id':int(meta.id),
         'version':int(meta.current_version_number),'remote_source_sha256':sha(source),
         'local_source_sha256':sha((P/'candidate.ipynb').read_bytes()),'source_equal':True,
         'is_private':meta.is_private,'enable_gpu':meta.enable_gpu,'enable_internet':meta.enable_internet,
         'datasets':list(meta.dataset_data_sources or []),'docker_image':meta.docker_image}
    require(out['is_private'] and out['enable_gpu'] and not out['enable_internet'],'Runtime flags changed')
    put(P/'kernel_identity.json',out)
    return out


def ordinary(api):
    identity=kernel(api);r=api.kernels_status(REF)
    result={'task_id':TASK,'observed_at_utc':now(),'identity':identity,
            'status':str(r.status).split('.')[-1].upper(),'failure_message':helper.safe_text(r.failure_message),
            'formal_score_read':False}
    put(P/'ordinary_latest.json',result)
    return result


def collect(api):
    before=ordinary(api)
    # Log/output collection is ordinary-run evidence, never formal submission status.
    RAW.mkdir(parents=True,exist_ok=True)
    names=['division_training_receipt.json','division_runtime_audit.json','division_gate_weights.json',
           'official_selector_audit.json','bidirectional_production_runtime_integrity.json',
           'ppsweep_selected.json','ppsweep_results.csv','validator_results.csv','run_stats.csv','submission.csv']
    import re
    pattern=r'(^|/)('+('|'.join(re.escape(n) for n in names))+')$'
    files,token=api.kernels_output(REF,path=str(RAW),file_pattern=pattern,force=True,quiet=True,page_size=100)
    require(not token,'Output inventory pagination incomplete')
    logs=list(RAW.glob('*.log'))
    if logs:
        lines=logs[0].read_text(errors='replace').splitlines()
        selected=[helper.safe_text(l) for l in lines if any(k in l for k in ['DIVISION_TRAIN','Traceback','Error','TRAINING_','Prediction completed','SECONDARY_EDGE_TTA_ACTIVE'])]
        put(P/'ordinary_log_excerpt.json',{'observed_at_utc':now(),'status':before['status'],'lines':selected[-30:],'log_sha256':sha(logs[0].read_bytes())})
    if before['status']!='COMPLETE':return {'status':before['status'],'outputs_present':[Path(f).name for f in files],'formal_score_read':False}
    require(all((RAW/n).is_file() for n in names),'Completed output files missing')
    after=kernel(api);require(before['identity']['remote_source_sha256']==after['remote_source_sha256'],'Source changed during collection')
    train=json.loads((RAW/names[0]).read_text());audit=json.loads((RAW/names[1]).read_text())
    require(train['training_completed'] and not train['embryo_overlap'],'Training evidence unavailable')
    require(train['weights_sha256']==audit['weights_sha256']==sha((RAW/names[2]).read_bytes()),'Trained weight hash mismatch')
    require(audit['module_sha256']==sha((P/'division_model.py').read_bytes()),'Trained module mismatch')
    require(audit['counts']['learned_division_scored']>0,'Trained gate was not used')
    weights=json.loads((RAW/names[2]).read_text())
    require(set(weights['held_out'])==set(train['embryo_groups']) and len(train['embryo_groups'])>=2,'Fold evidence missing')
    for fold in train['folds']:
        require(fold['held_out_embryo'] not in fold['training_embryos'] and fold['fit']['converged'],'Held-out split invalid')
    spec=importlib.util.spec_from_file_location('ordinary_validator',ROOT/'experiments/TARGET950_RUN_20260914/collect_output.py')
    validator=importlib.util.module_from_spec(spec);spec.loader.exec_module(validator)
    stats=validator.read_csv(RAW/'run_stats.csv');scorer=json.loads((RAW/'official_selector_audit.json').read_text())
    verified=validator.validate_bundle(RAW,[r['dataset'] for r in stats],scorer['validator_stems'])
    for name in names:
        if name in ('division_gate_weights.json','submission.csv'):continue
        (P/name).write_bytes((RAW/name).read_bytes())
    put(P/'training_receipt.json',train)
    receipt={'task_id':TASK,'ordinary_verified':True,'identity':after,'training_weights_sha256':train['weights_sha256'],
             'validator':verified,'runtime_audit':audit,'observed_at_utc':now(),'formal_score_read':False}
    put(P/'ordinary_receipt.json',receipt)
    return {'ordinary_verified':True,'training_weights_sha256':train['weights_sha256'],'counts':audit['counts'],'selected':audit['selected_label']}


def write(api,action):
    with (P/'operation.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        manifest=local_gate();pre=preflight(api)
        ledger=json.loads((P/'write_ledger.json').read_text()) if (P/'write_ledger.json').exists() else {'task_id':TASK,'operations':[]}
        require(not any(o['action']==action for o in ledger['operations']),'Operation already attempted; read-only reconcile required')
        if action=='save':
            require(pre['gpu_remaining_seconds']>=8100,'Insufficient live GPU time for frozen timeout')
            matches=api.kernels_list(mine=True,search='biohub-division-train-20260914',page_size=100) or []
            require(len(matches)<100 and not any('biohub-division-train-20260914' in str(k.ref) for k in matches),'Notebook identity already exists')
        else:
            identity=kernel(api);ordinary_receipt=json.loads((P/'ordinary_receipt.json').read_text())
            require(ordinary_receipt['ordinary_verified'] and ordinary_receipt['identity']['version']==identity['version'],'No verified ordinary result')
            binding=json.loads((P/'version_binding.json').read_text())
            require(binding['version']==identity['version'] and binding['kernel_id']==identity['kernel_id'] and binding['script_version_id']>0,'Missing exact ScriptVersion binding')
            quota=json.loads((P/'submission_quota_receipt.json').read_text())
            age=(datetime.now(timezone.utc)-datetime.fromisoformat(quota['observed_at_utc'])).total_seconds()
            require(0<=age<300 and quota['remaining']>0 and quota['source']=='Kaggle submission dialog','No fresh submission quota evidence')
        op={'action':action,'attempted_at_utc':now(),'status':'WRITE_ATTEMPT_RESERVED','candidate_sha256':manifest['candidate_sha256']}
        ledger['operations'].append(op);put(P/'write_ledger.json',ledger)
        try:
            with helper.single_write_transport(api,action,op):
                if action=='save':
                    r=api.kernels_push(str(P),timeout='8100',acc='NvidiaTeslaT4')
                    op['response']={k:getattr(r,k) for k in ('ref','url','version_number','kernel_id','error','invalid_dataset_sources','invalid_competition_sources','invalid_kernel_sources','invalid_model_sources')}
                    require(not r.error and r.kernel_id>0 and r.version_number==1,'Unexpected SaveKernel response')
                    require(not any(op['response'][k] for k in op['response'] if k.startswith('invalid_')),'Invalid input source')
                else:
                    description=f"{TASK} | V{identity['version']} | SV{binding['script_version_id']} | SHA256 {manifest['candidate_sha256']}"
                    r=api.competition_submit_code('submission.csv',description,COMP,REF,identity['version'],quiet=True)
                    op['response']={'submission_id':int(r.ref),'message':helper.safe_text(r.message),'description':description}
                    require(int(r.ref)>0,'Submission ID missing')
            op['status']='RESPONSE_RECEIVED_READBACK_REQUIRED'
        except BaseException as exc:
            op.update(status='WRITE_OUTCOME_UNKNOWN_READ_ONLY_RECONCILE_REQUIRED',**helper.safe_error(exc))
        finally:
            op['returned_at_utc']=now();put(P/'write_ledger.json',ledger)
        return op


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['preflight','save','ordinary','collect','submit']);args=parser.parse_args()
    from kaggle import api
    result=write(api,args.action) if args.action in ('save','submit') else globals()[args.action](api)
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str))

if __name__=='__main__':main()
