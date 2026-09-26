"""Download only existing exact-version ordinary outputs; no platform mutations."""
import json,sys,hashlib
from pathlib import Path
from datetime import datetime,timezone
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest,ApiGetKernelSessionStatusRequest
P=Path(__file__).resolve().parent;arm=sys.argv[1];a=json.loads((P/'platform_ledger.json').read_text())['candidates'][arm]
owner,slug=a['slug'].split('/');D=Path('/private/tmp')/('last-two-output-'+arm)
with api.build_kaggle_client() as c:
 q=ApiGetKernelRequest();q.user_name=owner;q.kernel_slug=slug
 m=c.kernels.kernels_api_client.get_kernel(q).metadata.to_dict();assert m['currentVersionNumber']==a['version']
 q=ApiGetKernelSessionStatusRequest();q.user_name=owner;q.kernel_slug=slug
 assert c.kernels.kernels_api_client.get_kernel_session_status(q).to_dict()['status']=='COMPLETE'
files,token=api.kernels_output(a['slug'],str(D),file_pattern=r'(^|/)(submission\.csv|last_two_receipt\.json|run_stats\.csv|ppsweep_selected\.json|runtime_integrity[^/]*\.json)$',page_size=100)
assert not token
receipt={'at':datetime.now(timezone.utc).isoformat(),'version':a['version'],'sv':a['sv'],'files':[{'name':Path(f).name,'bytes':Path(f).stat().st_size,'sha256':hashlib.sha256(Path(f).read_bytes()).hexdigest()} for f in files]}
(P/arm/'output_download_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
