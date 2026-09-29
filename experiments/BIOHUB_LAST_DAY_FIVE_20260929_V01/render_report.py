import json
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
P=Path(__file__).resolve().parent;R=P.parents[1];l=json.loads((P/'platform_ledger.json').read_text())
s='''# 最后一天五候选执行记录

任务 BIOHUB_LAST_DAY_FIVE_20260929_V01；固定任务提交 d97e29c72f223169af6fc62c3ab74d2a47b5e09e；分支 codex/last-day-five-20260929。
母版 DIV04_READMIT940 / V1 / SV353458552 / submission 56626891 / Public 0.958；SHA256 ac3651a886a11ecab5e89e8e2a80e10f8b4547b7b4775a6a75e437d8e2ea8035。

五份均独立从唯一母版生成；除单因素配置、对应守卫断言、候选与任务回执标识外，保留其余代码。0.94625 全精度保留；RL8 两种 flow 路径通过实际函数合成检查。构建检查 60 项，readmit 合成检查 5 份；全部 13 单元已读取/AST 检查，2—11 单元与母版字节相同，未重做科学效果验证。五份普通运行的实际输出与挂载均已验证。

## 当前状态
'''
s+=f"观察：{datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()}（上海）。stage={l['stage']}。普通请求 {l['run_request_count']}/5，正式请求 {l['formal_request_count']}/5，工程备用 {l['engineering_spare_count']}/1。\n\n"
if (P/'执行阶段核验.json').exists():
 v=json.loads((P/'执行阶段核验.json').read_text());s+=f"执行阶段核验 {v['execution_checks']}：五份普通 COMPLETE、五份输出和部署检查通过、五次正式请求已受理，工程备用 0。正式终态见下表；本批预算已用完，不新增运行或提交。\n\n"
s+='|候选|ILP/readmit/relaxed|Version|SV|submission|普通状态|正式状态|Public|Δ0.958|\n|---|---|---|---|---|---|---|---|---|\n'
for a in l['candidates']:
 c=a['effective_config'];score=a['public_score'];delta=f'{float(score)-.958:+.3f}' if score else 'UNKNOWN'
 s+='|'+ '|'.join(str(v) for v in [a['candidate_id'],f"{c['ilp']}/{c['readmit']}/{c['relaxed_um']}",a['version'],a['script_version_id'],a['submission_id'],a.get('ordinary_status',{}).get('status','NOT_REQUESTED'),a.get('formal_status',a['status'] if a.get('submission_id') else 'NOT_SUBMITTED'),score,delta])+'|\n'
if l['stage']=='SCORED_ALL':
 s+='\n五份正式结果均为 COMPLETE（MEASURED）：DIV06 为 0.957，比母版低 0.001；其余四份均为 0.958，显示持平。本批没有新增 Public 提升。结合原母版与 DIV04_READMIT9525，目前这些已测对象中共六份并列 0.958；无法凭三位显示分数区分其 Private 优劣，不自动变更最终选择。\n'
s+='''
## 实时资源与排重

首次页面读取显示 sailorren、正式余额 5 次、约 21 小时后重置；截止上海 2026-09-30 07:59。活动事件为 0。GPU 页面 04:49 / 30 hrs，官方 SDK 原始 timedelta 总额 108000 秒、已用 17356.864 秒、预留 0 秒。SDK to_dict() 的 timedelta 序列化丢失 days，误显示 totalTimeAllowed=21600s；必须用 total_seconds()，保留原响应和规范化数值，不虚构资源。

API 已分页枚举本人 131 个 Notebook，其中 60 个 Biohub 源码逐项读取配置；团队完整提交 66 项，无下一页。五个固定新配置未发现已有本人对象，团队近期记录未见本批对象。精确配置/输入/源码列表见 preflight.json；每次发送另作即时排重与资源核对。最多两普通槽，正式请求不串行等 Public。

## 最终选择与边界

本轮初读平台显示手动选择 **0/2**，手动选中 submission ID 列表为空；页面说明不足两份时 Kaggle 自动选高分，不能据此预填具体自动选择 ID。56626891 和 56638061 的两个 0.958 对象继续保留。只读核对，不勾选或取消。

旧两批 5/5 账本保持原字节；旧 ILP 批前两次未逐次刷新 GPU 余额缺口保留，本轮每次正式请求重新读取 GPU 与正式余额。新模型训练、Dataset 写入、最终选择修改均为 0。无自动后台调度、无第六算法候选。UNKNOWN/null 不冒充已受理或低分；超过 0.958 才是新增 Public 提升，不保证 Private。
'''
if (P/'final_selection_observed.json').exists():
 f=json.loads((P/'final_selection_observed.json').read_text());s+=f"\n最终选择最近只读复核：{f['observed_at']}；手动 {f['manual_selected_count']}/{f['maximum']}；手动 ID {f['manual_selected_submission_ids']}；自动具体 ID UNKNOWN；未修改。\n"
if (P/'score_recovery_notes.json').exists():
 n=json.loads((P/'score_recovery_notes.json').read_text());s+=f"\n出分回收补充（{n['observed_at']}）：本轮新正式请求 0。用户报告当前额度为 0；上次平台实读也为 0。浏览器连接初始化失败，当前最终选择未能重新读取，记为 UNKNOWN；上方 0/2 仅为其所列时间的历史观察，未修改最终选择。\n"
if (P/'competition_last_observed.json').exists():
 d=json.loads((P/'competition_last_observed.json').read_text());s+=f"\n官方 API 当前截止复核：{d['competition']['deadline']}，即上海 2026-09-30 07:59；读取时间 {d['observed_at']}；maxDailySubmissions={d['competition']['maxDailySubmissions']}。平台每日上限不等于本批仍有预算，本批 5/5 已用完。\n"
(R/'reports/20260929_BIOHUB_LAST_DAY_FIVE_RESULTS.md').write_text(s)
