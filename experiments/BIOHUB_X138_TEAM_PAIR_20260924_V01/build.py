"""Build complete no-run private templates; never invokes Kaggle or inference."""
import ast,copy,difflib,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
SRC=ROOT/'research/PUBLIC_0950_20260924/sources/x138/biohub-x138.ipynb'
SHA='6b655e39bbfd2d3d6c762badea69847d3f00f5b548f385cb01b07ee2600fde6d'
INPUTS=[('pilkwang/biohub-tracking-support-pack-50ep-v1',10),('pilkwang/biohub-temporal-unet3d-seed314159-v1',2),('pilkwang/biohub-deepcenter-unet3d-center-prior-v1',5),('anvithpothula/biohub-v1284-head-s075',1)]
KEY='BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT'
RECEIPT='''
# Read-only prediction audit; separate from inherited historical printouts.
import hashlib as _pair_hashlib
from datetime import datetime as _pair_datetime, timezone as _pair_timezone
try:
    def _pair_file(path):
        path = Path(path)
        if not path.is_file():
            return {"path": str(path), "status": "NOT_FOUND"}
        h = _pair_hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                h.update(chunk)
        return {"path": str(path), "bytes": path.stat().st_size, "sha256": h.hexdigest()}
    _pair_stats = globals().get("RUN_STATS_PATH")
    _pair_record = {
        "candidate": X138_TEAM_CANDIDATE,
        "timestamp_utc": _pair_datetime.now(_pair_timezone.utc).isoformat(),
        "velocity_constant": MOTION_RELINK_VELOCITY_WEIGHT,
        "velocity_environment": os.environ.get("BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT"),
        "flow_mode": MOTION_RELINK_FLOW_MODE,
        "head_mode": os.environ.get("V1284_MODE"),
        "head": _pair_file(os.environ.get("V1284_HEAD", "")),
        "csv": _pair_file(SUBMISSION_PATH),
        "run_stats_file": _pair_file(_pair_stats) if _pair_stats else None,
        "run_stats": pd.read_csv(_pair_stats).to_dict(orient="records") if _pair_stats and Path(_pair_stats).is_file() else None,
        "deadline_degraded": globals().get("_deadline_degraded"),
        "deepcenter_loaded": globals().get("_dc_loaded"),
        "secondary_ready": globals().get("_secondary_ready"),
        "module_warnings": "Review original saved logs for LOW-DETECTION DUMP SKIPPED, gap filler idle and repair fallback; not exhaustively captured here.",
        "public": None,
        "note": "Runtime audit only, not a formal score receipt. No predictions changed."
    }
    (WORKING_DIR / "x138_team_receipt.json").write_text(json.dumps(_pair_record, indent=2, default=str))
except Exception as _pair_error:
    print("X138_TEAM_RECEIPT_WARNING", type(_pair_error).__name__, str(_pair_error))
'''
def source(c): return ''.join(c['source'])
def build():
    assert hashlib.sha256(SRC.read_bytes()).hexdigest()==SHA
    original=json.loads(SRC.read_text());assert len(original['cells'])==12
    manifest={'task':'BIOHUB_X138_TEAM_PAIR_20260924_V01','base_commit':'d01c627a3006455d7ac3f4351c76ddf1fd9f4eb2','source_sha256':SHA,'source_license':'Apache-2.0 (live x138 V1 page)','source_author':'Anvith Pothula; original inherited authors retained','historical_reference':{'version':1,'sv':351539814,'public':0.953,'our_reproduction':False},'inputs':[{'ref':r,'version':v,'license':'CC0-1.0','evidence':'x138 V1 Input source details; official dataset metadata'} for r,v in INPUTS],'head_sha256':'625a0d9340f48193f2ec294fc2d81c5bb3c03087eab78ef0ae998a9c4c7da00c','head_bytes':33913,'weight_assertions_retained':{'primary':'12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771','secondary':'9bac2fa0dadc4a6fc1899e0caf187f4b553e0a7cd90ba1261a68b35ffe9e305f','deepcenter':'8040999a92f6b7bbd98fa8cf458141e045c0f9ad7c936bdb3b18e1f7edafe2a0'},'candidates':{}}
    diffs=[]
    for arm,value,slug in [('X0','0.5','biohub-x138-exact-team-20260924'),('X25','0.25','biohub-x138-v025-team-20260924')]:
        nb=copy.deepcopy(original);nb['nbformat_minor']=5;nb['metadata']={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python'}}
        for i,c in enumerate(nb['cells']):
            c['outputs']=[];c['execution_count']=None;c['metadata']={};c['id']=f'x138-code-{i+1:02}'
        s=source(nb['cells'][0]);assert s.count('import os\n')==1
        s=s.replace('import os\n',f'import os\n# Team candidate fixed at build time; before Cell 3 constant initialization.\nX138_TEAM_CANDIDATE = "{arm}"\nos.environ["{KEY}"] = "{value}"\n',1);nb['cells'][0]['source']=s.splitlines(True)
        nb['cells'][-1]['source']=(source(nb['cells'][-1])+RECEIPT).splitlines(True)
        md=f'''# {arm} / {'X138-Exact' if arm=='X0' else 'X138-V025'} — 未运行、未提交

原作者 Anvith Pothula，x138 V1 / SV351539814，Apache-2.0。原版历史Public为0.953；本候选Public未知。保留原作者及源码说明。

本候选固定自身速度外推系数 {value}；有邻域flow时不缩放flow。X0仅显式固定原默认0.5；X25唯一算法差异为0.25。增加本页与只读运行后回执，清理旧执行元数据，其余12个代码单元算法保持原顺序。旧打印中的历史分数/参数不是本次实测。

|输入|固定版本|
|---|---|
'''+''.join(f'|{r}|{v}|\n' for r,v in INPUTS)+'''|biohub-cell-tracking-during-development|比赛输入|

仅本人 Copy & Edit；副本保持Private，选择T4×2、Internet off。四个Dataset与比赛输入不可丢失，不挂旧gate。先回传副本链接和Inputs/Settings截图，本批先不运行／提交。后续用户统一协调后再运行一次Save & Run All，核验submission.csv、x138_team_receipt.json及原日志；不要提交母版。母版None不代表CPU推理方案。
'''
        nb['cells'].insert(0,{'cell_type':'markdown','id':'x138-team-intro','metadata':{},'source':md.splitlines(True)})
        d=OUT/arm;d.mkdir(exist_ok=True);p=d/'candidate.ipynb';p.write_text(json.dumps(nb,ensure_ascii=False,indent=1)+'\n')
        meta={'id':'sailorren/'+slug,'title':slug,'code_file':'candidate.ipynb','language':'python','kernel_type':'notebook','is_private':True,'enable_gpu':False,'enable_tpu':False,'enable_internet':False,'dataset_sources':[f'{r}/{v}' for r,v in INPUTS],'competition_sources':['biohub-cell-tracking-during-development'],'kernel_sources':[]}
        (d/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
        manifest['candidates'][arm]={'slug':meta['id'],'velocity':float(value),'public':None,'execution':'NOT_RUN','submission':'NOT_SUBMITTED','sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'original_code_cells':12,'markdown_cells':1,'platform_settings':'To be read back; desired None/off/offline'}
        for i,(a,b) in enumerate(zip(original['cells'],nb['cells'][1:])):
            diffs+=list(difflib.unified_diff(source(a).splitlines(True),source(b).splitlines(True),fromfile=f'original/cell{i+1}',tofile=f'{arm}/cell{i+1}'))
    (OUT/'candidate_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');(OUT/'source.diff').write_text(''.join(diffs))
if __name__=='__main__':build()
