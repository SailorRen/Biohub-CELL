"""One preparation process; a parent enforces the 1800 second session budget."""
import hashlib,importlib.metadata as md,json,os,shutil,subprocess,sys,time,traceback
from pathlib import Path
from urllib.parse import urlparse,unquote
ROOT=Path('/kaggle/working/cpu_bundle');START=time.monotonic()
def sha(p):return hashlib.file_digest(open(p,'rb'),'sha256').hexdigest()
def record(stage,**kw):
 d={'stage':stage,'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'elapsed_seconds':time.monotonic()-START,**kw};(ROOT/(stage+'.json')).write_text(json.dumps(d,indent=2)+'\n');print('BUNDLE',json.dumps(d),flush=True)
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=max(1,1800-(time.monotonic()-START)));print(p.stdout[-10000:],p.stderr[-5000:],flush=True);p.check_returncode();return p
try:
 assert not (ROOT/'preparation_started.json').exists(),'Duplicate preparation prohibited'
 record('preparation_started',status='STARTED')
 support=Path('/kaggle/input/datasets/pilkwang/biohub-tracking-support-pack-50ep-v1')
 if not support.exists():support=Path('/kaggle/input/biohub-tracking-support-pack-50ep-v1')
 assert (support/'wheels').is_dir()
 from packaging.utils import parse_wheel_filename
 from packaging.tags import sys_tags
 tags=set(sys_tags());available={}
 for p in sorted((support/'wheels').glob('*.whl')):
  name,ver,_,wtags=parse_wheel_filename(p.name)
  if wtags & tags:available.setdefault(str(name),[]).append((str(ver),p))
 assert all(len({v for v,p in entries})==1 for entries in available.values()),'Ambiguous support wheel versions'
 constraints=[name+'=='+entries[0][0] for name,entries in available.items() if name not in ['numpy','torch']]
 constraints+=['numpy=='+md.version('numpy'),'torch=='+md.version('torch')]
 (ROOT/'support_constraints.txt').write_text('\n'.join(constraints)+'\n')
 specs=json.loads((ROOT/'dependency_specs.json').read_text())
 run([sys.executable,'-m','pip','install','--disable-pip-version-check','--no-index','--find-links',str(support/'wheels'),'-c',str(ROOT/'support_constraints.txt'),'--report',str(ROOT/'support_install_report.json'),*specs])
 wheels=ROOT/'wheels';wheels.mkdir(exist_ok=True)
 report=json.loads((ROOT/'support_install_report.json').read_text())
 selected=[]
 for row in report['install']:
  src=Path(unquote(urlparse(row['download_info']['url']).path));assert src.is_file() and support in src.parents
  shutil.copy2(src,wheels/src.name);selected.append(row['metadata']['name']+'=='+row['metadata']['version'])
 # One fixed official-PyPI supplement. Dependencies are fixed as well; no environment-wide upgrade.
 run([sys.executable,'-m','pip','download','--disable-pip-version-check','--index-url','https://pypi.org/simple','--only-binary=:all:','--no-deps','-d',str(wheels),'openvino==2026.4.0','openvino-telemetry==2025.2.0'])
 selected+=['openvino==2026.4.0','openvino-telemetry==2025.2.0']
 (ROOT/'requirements.lock').write_text('\n'.join(sorted(selected))+'\n')
 run([sys.executable,'-m','pip','install','--disable-pip-version-check','--no-index','--find-links',str(wheels),'-r',str(ROOT/'requirements.lock')])
 # Import-only full-chain dependency check; no hidden training/prediction entrypoint.
 check=run([sys.executable,'-c','import torch,numpy,zarr,polars,tracksdata,pyscipopt,geff,ilpy,blosc2,openvino; import json; print(json.dumps({k:__import__(k).__version__ for k in ["torch","numpy","zarr","polars","openvino"]}))'])
 record('environment',versions=json.loads(check.stdout.strip().splitlines()[-1]),installed_specs=selected,network_isolation='NOT_VERIFIED_PREPARATION_ONLINE')
 run([sys.executable,str(ROOT/'convert_bundle.py')])
 manifest={p.relative_to(ROOT).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='bundle_manifest.json'}
 (ROOT/'bundle_manifest.json').write_text(json.dumps({'files':manifest,'status':'PREPARED_NOT_OFFLINE_VERIFIED'},indent=2)+'\n')
 record('preparation_complete',status='PREPARED',files=len(manifest),total_bytes=sum(v['bytes'] for v in manifest.values()))
except BaseException as e:
 record('preparation_error',status='STOPPED_ERROR',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc());raise
