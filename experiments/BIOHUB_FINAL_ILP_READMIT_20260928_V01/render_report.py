"""只将准确账本状态渲染为报告，未知值不填零。"""
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
P=Path(__file__).resolve().parent;R=P.parents[1];l=json.loads((P/'platform_ledger.json').read_text());r=R/'reports/20260928_BIOHUB_FINAL_ILP_READMIT_RESULTS.md';base=r.read_text().split('\n## 当前平台状态')[0]
base=base.replace('状态：LOCAL_PREPARED，尚无本批运行或正式请求。','初始状态：LOCAL_PREPARED；当前状态以文末动态表格及账本为准。')
s=['','## 当前平台状态','',f"观测记录汇总时间：{datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()}；阶段 {l['stage']}。",'', '|候选|ILP / readmit|Version / SV|submission|普通运行|正式状态|Public|Δ0.956|','|---|---|---|---|---|---|---|---|']
for a in l['wave1']+l['wave2']:
 cfg=a['effective_config'];v=a.get('public_score');vals=[a['candidate_id'],f"{cfg['ilp']} / {cfg['readmit']}",f"{a.get('version')} / {a.get('script_version_id')}",a.get('submission_id'),a.get('ordinary_status',{}).get('status',a['status']),a.get('formal_status'),v,None if v is None else f'{float(v)-.956:+.3f}'];s.append('| '+' | '.join('UNKNOWN' if x is None else str(x) for x in vals)+' |')
s+=['',f"本批普通请求 {l['run_request_count']}，已受理 {l['accepted_full_run_count']}；正式请求 {l['formal_request_count']}/5；工程备用 {l['engineering_spare_count']}/1。旧批次 5/5 不变。",'', 'PENDING / UNKNOWN 不代表低分或零分。第一批未取得全部正式终态前，第二批不冻结、不运行。没有后台调度；本会话内继续执行，若中断按账本精确 ID 续接。']
if (P/'gpu_quota_after_first_two_formal.json').exists(): s+=['', '流程审计：前两次正式请求均刷新了正式余额、账号、截止时间和去重，但 GPU 额度最近一次刷新在 READMIT940 普通运行前，未分别在两次正式请求前即时刷新。后续已补入独立 GPU 额度回读；该历史缺口不追溯标记为通过。']
if l.get('second_wave_decision'):s+=['',json.dumps(l['second_wave_decision'],ensure_ascii=False)]
r.write_text(base+'\n'.join(s)+'\n')
