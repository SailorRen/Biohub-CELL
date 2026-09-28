import json,subprocess,base64,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
selected={'OpenKaggle__biohub-cell-tracking-research':['README.md','CAMPAIGN.md','decisions/BH-0005-min-track-length.md'],'canakbass__biohub-cell-tracking':['README.md','STATE.md'],'alvaromendizabal__biohub-cell-tracking-during-development':['README.md','RESULTS.md','FRONTIER.md','REPRODUCIBILITY.md'],'kito2718__kaggle_Biohub-Cell_Tracking_During_Development':['s7_summary/s8_summary2.md','working/s8_064_global_association/s8_064_global_association.ipynb'],'Beiciccc__biohub-cell-tracking-development':['README.md','docs/experiment_log.md'],'royerlab__kaggle-cell-tracking-competition':['README.md','metrics.md','src/tracking_cellmot/division_metrics.py']}
manifest=[]
for name,files in selected.items():
 d=P/'github'/name;repo=json.loads((d/'repo.json').read_text())['full_name'];sha=json.loads((d/'commit.json').read_text())['sha'];tree={x['path']:x for x in json.loads((d/'tree.json').read_text())['tree']}
 for path in files:
  x=tree[path];r=json.loads(subprocess.check_output(['gh','api',f'repos/{repo}/git/blobs/{x["sha"]}'],text=True));b=base64.b64decode(r['content']);assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['sha'];dest=d/'files'/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b);manifest.append({'repo':repo,'branch':json.loads((d/'repo.json').read_text())['default_branch'],'commit':sha,'path':path,'blob':x['sha'],'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'local_path':str(dest.relative_to(P))});print(repo,path,len(b),flush=True)
(P/'github_file_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
