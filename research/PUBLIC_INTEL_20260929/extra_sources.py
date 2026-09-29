import json,subprocess,base64,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;heads={x['repo']:x for x in json.loads((P/'heads.json').read_text())};out=json.loads((P/'github_file_manifest.json').read_text())
selection={'royerlab/kaggle-cell-tracking-competition':['scripts/csv_to_geffs.py'],'kito2718/kaggle_Biohub-Cell_Tracking_During_Development':['s7_summary/s8_summary3.md'],'drosadocastro-bit/Atabey':['V28_KAGGLE_RESULT.md','V29A_RESULTS.md'],'MapleBadger666/biohub-cell-tracking':['docs/VALIDATION.md','src/biohub_cell_tracking/frozen_v9.py'],'pathik1511/biohub-cell-tracking':['src/biohub/link.py','src/biohub/metric.py']}
for repo,paths in selection.items():
 h=heads[repo]
 for path in paths:
  r=json.loads(subprocess.check_output(['gh','api','repos/'+repo+'/contents/'+path+'?ref='+h['commit']],text=True));data=base64.b64decode(r['content']);fp=P/'github'/repo.replace('/','__')/'files'/path;fp.parent.mkdir(parents=True,exist_ok=True);fp.write_bytes(data);out.append({'repo':repo,'branch':h['branch'],'commit':h['commit'],'path':path,'blob':r['sha'],'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'local_path':str(fp.relative_to(P)),'changed_head':h['changed']});print(repo,path,len(data),flush=True)
(P/'github_file_manifest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
