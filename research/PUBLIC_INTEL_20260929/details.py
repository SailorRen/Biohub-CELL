import json,subprocess,base64,hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from kaggle import api
P=Path(__file__).resolve().parent;O=P.parent/'PUBLIC_INTEL_20260928_RESULTS';S='biohub-cell-tracking-during-development'
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def gh(path):return json.loads(subprocess.check_output(['gh','api',path],text=True))
old=json.loads((O/'github_file_manifest.json').read_text());repos=list(dict.fromkeys(x['repo'] for x in old))+['pathik1511/biohub-cell-tracking','MapleBadger666/biohub-cell-tracking']
def repo_read(repo):
 d=P/'github'/repo.replace('/','__');m=gh('repos/'+repo);b=m['default_branch'];cm=gh('repos/'+repo+'/commits/'+b);sha=cm['sha'];prev=next((x['commit'] for x in old if x['repo']==repo),None)
 h={'repo':repo,'branch':b,'commit':sha,'date':cm['commit']['committer']['date'],'message':cm['commit']['message'],'previous_commit':prev,'changed':sha!=prev,'observed_at':datetime.now(timezone.utc).isoformat()};save(d/'head.json',h)
 paths=[x['path'] for x in old if x['repo']==repo]
 if not paths:paths=['README.md']
 if 'Junhao' in repo:paths+=['STATE.json']
 if h['changed']:
  tr=gh('repos/'+repo+'/git/trees/'+sha+'?recursive=1');save(d/'text_tree.json',{'truncated':tr.get('truncated'),'tree':[x for x in tr['tree'] if x['type']=='blob' and (x['path'].endswith('.md') or x['path'].endswith('STATE.json'))]})
 out=[]
 for path in paths:
  try:
   r=gh('repos/'+repo+'/contents/'+path+'?ref='+sha);data=base64.b64decode(r['content']);fp=d/'files'/path;fp.parent.mkdir(parents=True,exist_ok=True);fp.write_bytes(data)
   out.append({'repo':repo,'branch':b,'commit':sha,'path':path,'blob':r['sha'],'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'local_path':str(fp.relative_to(P)),'changed_head':h['changed']})
  except Exception as e:save(d/('error_'+Path(path).name+'.json'),{'path':path,'error':str(e)})
 print('repo',repo,sha,h['changed'],flush=True);return h,out
with ThreadPoolExecutor(max_workers=4) as ex:r=list(ex.map(repo_read,repos))
save(P/'heads.json',[x[0] for x in r]);save(P/'github_file_manifest.json',[f for x in r for f in x[1]])
for tid in [744093,743929,743006,732103,743765,742169,742266]:
 r=api.competition_list_topic_messages(S,tid,page_size=100);save(P/'discussions'/f'{tid}.json',r.to_dict());print('topic',tid,flush=True)
