"""Read-only source and discussion acquisition. Source is not executed."""
import json,subprocess,hashlib
from pathlib import Path
from kaggle import api
from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest
P=Path(__file__).resolve().parent;S='biohub-cell-tracking-during-development'
def save(path,v):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
for tid in [743929,743006,743222,743765,742169,732103]:
 r=api.competition_list_topic_messages(S,tid,page_size=100);save(P/'discussions'/f'{tid}.json',r.to_dict());print('topic',tid,flush=True)
with api.build_kaggle_client() as c:
 ref='kunaldesale2408/biohub-cell-tracking';q=ApiGetKernelRequest();q.user_name,q.kernel_slug=ref.split('/');r=c.kernels.kernels_api_client.get_kernel(q)
 d=P/'sources'/ref;save(d/'metadata.json',r.metadata.to_dict());(d/'source.ipynb').write_text(r.blob.source);nb=json.loads(r.blob.source);(d/'source.py').write_text('\n\n'.join('# CELL '+str(i)+'\n'+''.join(x['source']) for i,x in enumerate(nb['cells']) if x['cell_type']=='code'));print('source',ref,len(nb['cells']),flush=True)
repos=['OpenKaggle/biohub-cell-tracking-research','canakbass/biohub-cell-tracking','alvaromendizabal/biohub-cell-tracking-during-development','kito2718/kaggle_Biohub-Cell_Tracking_During_Development','Beiciccc/biohub-cell-tracking-development','royerlab/kaggle-cell-tracking-competition']
def gh(path):return json.loads(subprocess.check_output(['gh','api',path],text=True))
for repo in repos:
 d=P/'github'/repo.replace('/','__');m=gh('repos/'+repo);save(d/'repo.json',m);branch=m['default_branch'];cm=gh('repos/'+repo+'/commits/'+branch);save(d/'commit.json',cm);sha=cm['sha'];tree=gh('repos/'+repo+'/git/trees/'+sha+'?recursive=1');save(d/'tree.json',tree)
 print('repo',repo,branch,sha,[(x['path'],x.get('size')) for x in tree['tree'] if x['type']=='blob' and (x['path'].lower().endswith('.md') or 'result' in x['path'].lower())][:35],flush=True)
