import json
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;R=P.parents[1];l=json.loads((P/'platform_ledger.json').read_text())
s='''# 最后一天五候选执行记录

任务 BIOHUB_LAST_DAY_FIVE_20260929_V01；固定任务提交 d97e29c72f223169af6fc62c3ab74d2a47b5e09e；分支 codex/last-day-five-20260929。
母版 DIV04_READMIT940 / V1 / SV353458552 / submission 56626891 / Public 0.958；SHA256 ac3651a886a11ecab5e89e8e2a80e10f8b4547b7b4775a6a75e437d8e2ea8035。

五份均独立从唯一母版生成；除单因素配置、对应守卫断言、候选与任务回执标识外，保留其余代码。0.94625 全精度保留；RL8 两种 flow 路径通过实际函数合成检查。构建检查 60 项，readmit 合成检查 5 份；全部 13 单元已读取/AST 检查，2—11 单元与母版字节相同，未重做科学效果验证。普通运行完成后仍须验证实际输出与挂载。

## 当前状态
'''
s+=f"观察：{datetime.now(timezone.utc).isoformat()}（UTC）。stage={l['stage']}。普通请求 {l['run_request_count']}/5，正式请求 {l['formal_request_count']}/5，工程备用 {l['engineering_spare_count']}/1。\n\n"
s+='|候选|ILP/readmit/relaxed|Version|SV|submission|普通状态|正式状态|Public|Δ0.958|\n|---|---|---|---|---|---|---|---|---|\n'
for a in l['candidates']:
 c=a['effective_config'];score=a['public_score'];delta=f'{float(score)-.958:+.3f}' if score else 'UNKNOWN'
 s+='|'+ '|'.join(str(v) for v in [a['candidate_id'],f"{c['ilp']}/{c['readmit']}/{c['relaxed_um']}",a['version'],a['script_version_id'],a['submission_id'],a.get('ordinary_status',{}).get('status','NOT_REQUESTED'),a.get('formal_status',a['status'] if a.get('submission_id') else 'NOT_SUBMITTED'),score,delta])+'|\n'
s+='''
## 实时资源与排重

首次页面读取显示 sailorren、正式余额 5 次、约 21 小时后重置；截止上海 2026-09-30 07:59。活动事件为 0。GPU 页面 04:49 / 30 hrs，官方 SDK 原始 timedelta 总额 108000 秒、已用 17356.864 秒、预留 0 秒。SDK to_dict() 的 timedelta 序列化丢失 days，误显示 totalTimeAllowed=21600s；必须用 total_seconds()，保留原响应和规范化数值，不虚构资源。

API 已分页枚举本人 131 个 Notebook，其中 60 个 Biohub 源码逐项读取配置；团队完整提交 66 项，无下一页。五个固定新配置未发现已有本人对象，团队近期记录未见本批对象。精确配置/输入/源码列表见 preflight.json；每次发送另作即时排重与资源核对。最多两普通槽，正式请求不串行等 Public。

## 最终选择与边界

本轮初读平台显示手动选择 **0/2**，手动选中 submission ID 列表为空；页面说明不足两份时 Kaggle 自动选高分，不能据此预填具体自动选择 ID。56626891 和 56638061 的两个 0.958 对象继续保留。只读核对，不勾选或取消。

旧两批 5/5 账本保持原字节；旧 ILP 批前两次未逐次刷新 GPU 余额缺口保留，本轮每次正式请求重新读取 GPU 与正式余额。新模型训练、Dataset 写入、最终选择修改均为 0。无自动后台调度、无第六算法候选。UNKNOWN/null 不冒充已受理或低分；超过 0.958 才是新增 Public 提升，不保证 Private。
'''
(R/'reports/20260929_BIOHUB_LAST_DAY_FIVE_RESULTS.md').write_text(s)
