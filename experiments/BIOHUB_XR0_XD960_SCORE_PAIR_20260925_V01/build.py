"""Exact source rebuild; no inference, platform writes, or algorithm additions."""
import copy, hashlib, json, difflib
from pathlib import Path
P=Path(__file__).resolve().parent; ROOT=P.parents[1]
SRC=ROOT/'research/PUBLIC_0950_20260924/sources/x138/biohub-x138.ipynb'
sha=lambda x:hashlib.sha256(x).hexdigest()
assert sha(SRC.read_bytes())=='6b655e39bbfd2d3d6c762badea69847d3f00f5b548f385cb01b07ee2600fde6d'
original=json.loads(SRC.read_text()); codes=[c for c in original['cells'] if c['cell_type']=='code' and ''.join(c['source']).strip()]; assert len(codes)==12
old=json.loads((ROOT/'experiments/BIOHUB_X138_TEAM_PAIR_20260924_V01/candidate_manifest.json').read_text())
manifest={'task':P.name,'source_sha256':sha(SRC.read_bytes()),'development_base':'6205f21d9366abcc7d39d34f41dc609eb10fc77b','research_base':'8ce433abbbbab610e5f985aac67c41479c1b3cb3','source_base':'d01c627a3006455d7ac3f4351c76ddf1fd9f4eb2','inputs':old['inputs'],'head_sha256':old['head_sha256'],'head_bytes':old['head_bytes'],'weight_assertions_retained':old['weight_assertions_retained'],'candidates':{}}
diffs=[]
for arm,threshold in [('XR0','0.965'),('XD960','0.960')]:
 d=P/arm;d.mkdir(exist_ok=True);nb=copy.deepcopy(original);nb['nbformat']=4;nb['nbformat_minor']=5;nb['metadata']={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python'},'accelerator':'GPU'}
 nb['cells']=copy.deepcopy(codes)
 if arm=='XD960':
  for idx,a,b in [(0,'os.environ["BIOHUB_DET_THRESHOLD"] = "0.965"','os.environ["BIOHUB_DET_THRESHOLD"] = "0.960"'),(1,'"BIOHUB_DET_THRESHOLD": 0.965,','"BIOHUB_DET_THRESHOLD": 0.960,')]:
   s=''.join(nb['cells'][idx]['source']);assert s.count(a)==1;nb['cells'][idx]['source']=s.replace(a,b,1)
 for i,c in enumerate(nb['cells']):
  c['source']=''.join(c['source']);c['metadata']={};c['execution_count']=None;c['outputs']=[];c['id']=f'x138-cell-{i+1:02}'
  diffs+=list(difflib.unified_diff(''.join(codes[i]['source']).splitlines(True),c['source'].splitlines(True),fromfile=f'original/cell{i+1}',tofile=f'{arm}/cell{i+1}'))
 intro=f'''# {arm}：正式评分候选（尚未运行、未提交）
原作者 Anvith Pothula，x138 V1 / SV351539814，Apache-2.0。保留全部12个原始代码单元；XR0代码逐字节等于原版，XD960仅原Cell1检测阈值及Cell2对应守卫改为0.960。旧源码历史打印不是本次实测。

有效参数：DET_THRESHOLD={threshold}；velocity=0.5；DeepCenter safe-div=0.25；validator=0；flow=seed；READMIT_MIN_SCORE=0.965。

固定Inputs：primary V10、secondary V2、DeepCenter V5、head V1及比赛。Private / T4×2 / Internet off。禁止使用Latest代替固定版本，不挂kernel_sources或旧gate。

队友本人 Copy & Edit → 核对固定Inputs和GPU → Save & Run All一次 → 回传精确Version/SV和日志/输出验收 → 合格后从该版本Submit to Competition一次。XR0普通完整GPU通过后立即推进XD960，无需等XR0正式分数。共同错误明确时停止第二份。正式重提0；共用有证据工程修复运行最多1次。切勿从None版本直接提交。

输出验收覆盖真实CSV、全部当次test、坐标/时间/父子图、原三个权重哈希、head与低阈缓存实际生效、repair_fallback及deadline_degraded。缺失字段=UNKNOWN；合理零新增不等于模块失效。保留A及最终选择。
'''
 nb['cells'].insert(0,{'cell_type':'markdown','metadata':{},'id':'score-pair-guide','source':intro})
 data=(json.dumps(nb,ensure_ascii=False,indent=1)+'\n').encode();(d/'candidate.ipynb').write_bytes(data)
 meta=json.loads((SRC.parent/'kernel-metadata.json').read_text());meta.pop('id_no',None);meta.update(id=f'sailorren/biohub-x138-{arm.lower()}-score-20260925',title=f'biohub-x138-{arm.lower()}-score-20260925',code_file='candidate.ipynb',is_private=True,enable_gpu=True,enable_internet=False,dataset_sources=[x['ref']+'/'+str(x['version']) for x in old['inputs']],kernel_sources=[])
 (d/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
 manifest['candidates'][arm]={'slug':meta['id'],'notebook_sha256':sha(data),'code_cell_sha256':[sha(c['source'].encode()) for c in nb['cells'] if c['cell_type']=='code'],'threshold':float(threshold),'velocity':0.5,'readmit_min_score':0.965,'kernel':None,'owner':None,'version':None,'sv':None,'submission_id':None,'public':None,'execution':'NOT_RUN','deployment':'NOT_CREATED','requested_metadata':meta}
(P/'source.diff').write_text(''.join(diffs));(P/'candidate_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Built XR0 exact + XD960 two-line diff')
