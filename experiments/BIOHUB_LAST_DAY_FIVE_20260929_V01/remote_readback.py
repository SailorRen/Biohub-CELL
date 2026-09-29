"""读取当前已提交 GitHub 原始字节；回执放忽略区，避免递归提交。"""
import json,subprocess,urllib.request,urllib.parse,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;R=P.parents[1]
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/codex/last-day-five-20260929'],cwd=R,text=True).split()[0];assert sha==remote
l=json.loads((P/'platform_ledger.json').read_text());paths=[P/'platform_ledger.json',R/'reports/20260929_BIOHUB_LAST_DAY_FIVE_RESULTS.md']
for a in l['candidates']:
 for f in ['candidate.ipynb','kernel-metadata.json','run_request_receipt.json','formal_request_receipt.json','formal_last_observed.json','output_check.json','deployment_check.json','input_versions_observed.json','runtime_receipt.json','pre_submit_quota.json','pre_submit_api_snapshot.json','ordinary_readback.json']:
  p=P/a['candidate_id']/f
  if p.exists():paths.append(p)
for f in ['final_selection_observed.json','post_submit_quota.json','执行阶段核验.json']:
 if (P/f).exists():paths.append(P/f)
rows=[]
for p in paths:
 rel=str(p.relative_to(R));b=urllib.request.urlopen('https://raw.githubusercontent.com/SailorRen/Biohub-CELL/'+sha+'/'+urllib.parse.quote(rel),timeout=45).read();assert b==p.read_bytes(),rel;rows.append({'path':rel,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
out=R/'.task-verification'/P.name/f'remote-{sha}.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({'at':datetime.now(timezone.utc).isoformat(),'passed':True,'commit':sha,'files':rows},indent=2)+'\n');print('REMOTE_BYTES_PASS',sha,len(rows),out)
