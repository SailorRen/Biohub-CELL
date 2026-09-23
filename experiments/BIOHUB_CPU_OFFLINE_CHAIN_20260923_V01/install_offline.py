"""Install only the prepared, hash-verified local wheels; never enable networking."""
import hashlib,importlib.metadata as md,json,subprocess,sys,time
from pathlib import Path
root=Path(sys.argv[1]);started=time.monotonic();manifest=json.loads((root/'bundle_manifest.json').read_text())
for name,meta in manifest['files'].items():
 p=root/name;assert p.stat().st_size==meta['bytes'];assert hashlib.file_digest(open(p,'rb'),'sha256').hexdigest()==meta['sha256'],name
p=subprocess.run([sys.executable,'-m','pip','install','--disable-pip-version-check','--no-index','--find-links',str(root/'wheels'),'-r',str(root/'requirements.lock')],capture_output=True,text=True,timeout=600)
print(p.stdout,p.stderr,flush=True)
r={'status':'INSTALLED' if p.returncode==0 else 'OFFLINE_INSTALL_FAILED','seconds':time.monotonic()-started,'bundle_files_hash_verified':len(manifest['files']),'pip_returncode':p.returncode,'pip_args':['--no-index','--find-links','mounted cpu_bundle/wheels']}
Path('/kaggle/working/offline_install_receipt.json').write_text(json.dumps(r,indent=2)+'\n');p.check_returncode()
