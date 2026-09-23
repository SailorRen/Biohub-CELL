import importlib.util,json,os,platform,resource,subprocess,sys,time,traceback
from pathlib import Path
ROOT=Path('/kaggle/working/cpu_small_probe');ROOT.mkdir(exist_ok=True)
START=time.monotonic();DEADLINE=START+900

def record(status,**kw):
 d={'status':status,'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'seconds':time.monotonic()-START,**kw};(ROOT/'00_environment.json').write_text(json.dumps(d,indent=2)+'\n');print('ENVIRONMENT',json.dumps(d),flush=True)
def pip(args):
 r=subprocess.run([sys.executable,'-m','pip','install','--disable-pip-version-check',*args],capture_output=True,text=True,timeout=max(1,DEADLINE-time.monotonic()));print(r.stdout[-6000:],r.stderr[-3000:],flush=True);r.check_returncode()
try:
 record('PREPARING')
 support=Path('/kaggle/input/datasets/pilkwang/biohub-tracking-support-pack-50ep-v1')
 import torch,numpy
 try:
  import zarr
  zarr_ok=int(zarr.__version__.split('.')[0])>=3
 except ImportError:zarr_ok=False
 offline_install=not zarr_ok
 if offline_install:pip(['--no-index','--no-deps','--find-links',str(support/'wheels'),'zarr>=3','donfig','numcodecs','google-crc32c','typing-extensions','packaging'])
 online_install=importlib.util.find_spec('openvino') is None
 if online_install:pip(['--index-url','https://pypi.org/simple','openvino'])
 # Fresh interpreter below will use newly installed packages.
 check=subprocess.run([sys.executable,'-c','import torch,numpy,zarr,openvino; print(torch.__version__,numpy.__version__,zarr.__version__,openvino.__version__)'],capture_output=True,text=True,timeout=max(1,DEADLINE-time.monotonic()));check.check_returncode()
 def read(p):
  q=Path(p);return q.read_text().strip() if q.exists() else 'NOT_OBSERVED'
 cpu_model=next((x.split(':',1)[1].strip() for x in read('/proc/cpuinfo').splitlines() if x.startswith('model name')),'UNKNOWN')
 record('PREPARED',versions_raw=check.stdout.strip(),python=sys.version,cpu_model=cpu_model,logical_cpus=os.cpu_count(),affinity_cpus=len(os.sched_getaffinity(0)),threads=int(os.environ['PROBE_THREADS']),memory_cgroup_v2=read('/sys/fs/cgroup/memory.max'),memory_cgroup_v1=read('/sys/fs/cgroup/memory/memory.limit_in_bytes'),cpu_max=read('/sys/fs/cgroup/cpu.max'),meminfo=read('/proc/meminfo').splitlines()[:3],peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,online_pypi_install_requests=int(online_install),offline_install_requests=int(offline_install),network_isolation='NOT_VERIFIED')
except BaseException as e:
 record('PREPARATION_FAILED',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc()[-10000:]);raise
