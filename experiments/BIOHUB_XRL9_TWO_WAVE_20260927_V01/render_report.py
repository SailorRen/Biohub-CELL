"""Render exact local evidence status; never infer a missing score."""
import json
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;l=json.loads((P/'platform_ledger.json').read_text());r=P.parents[1]/'reports/20260927_BIOHUB_XRL9_TWO_WAVE_RESULTS.md'
s=['# XRL9 两波正式评分执行记录','',f"状态：{l['stage']}；报告生成时间 {datetime.now(timezone.utc).isoformat()}（UTC）。",'', '任务交付 commit：`ffd6a3b6036037c76372787b487f6d800454e8e4`；原文 SHA256：`aa66741012266c7e0c30d186f2ac2819206cfa567e4b0ae0591bad15c4908d6d`。','', 'MEASURED 基线 XRL9：Public 0.955，submission 56587392，V1 / SV353050971。新候选只有正式 Public 才用于比较。', '', '| 候选 | DET / relaxed µm | Version / SV | submission ID | 状态 | Public | Δ XRL9 | 请求时间 UTC | 最后观测 UTC | 直接错误 |','|---|---|---|---|---|---|---|---|---|---|']
for a in l['wave1']+l['wave2']:
 v=a.get('public_score');delta=f'{float(v)-.955:+.4f}' if v is not None else 'UNKNOWN';cfg=a['effective_config'];name=a['candidate_id'];ref=a.get('kernel_ref');name=f'[{name}](https://www.kaggle.com/code/{ref})' if a.get('version') and ref else name
 vals=[name,f"{cfg['det']} / {cfg['relaxed_um']}",f"{a.get('version')} / {a.get('script_version_id')}",a.get('submission_id'),a['status'],v,delta,a.get('requested_at'),a.get('observed_at'),a.get('direct_error') or ('未返回错误' if a.get('status')=='SCORED' else 'UNKNOWN')]
 s.append('| '+' | '.join('UNKNOWN' if x is None else str(x).replace('|','/') for x in vals)+' |')
s+=['',f"预算：已发送 Save & Run 请求 {l['full_run_count']}（含明确失败）；实际受理完整运行 {l.get('accepted_full_run_count',0)}；工程备用 {l['engineering_spare_count']}/1；正式请求 {l['formal_request_count']}/5。第二波最多 2，首批正式结果齐备之前不启动。",'', '三份候选已通过 27 项小型检查：完整 Notebook/13 代码单元、AST、允许差异、参数消费、实际 support 动态补丁、缓存先于 head。冻结源码 commit `00a930ffe17bbda213397a438bc3fd45a0ea4cc0`，32/32 文件远端逐字节回读通过。静态检查不等于运行通过或正式得分。','', '输入冻结 primary V10、secondary V2、DeepCenter V5、head V1，Private、T4×2、Internet off。三份已受理运行 API 回读源码一致、GPU enabled、原镜像摘要一致；界面通用镜像标题为 Latest，实际摘要另存 ordinary_readback.json。实际挂载版本与完整输出在每份 deployment_check.json / output_check.json 中验收后才提交。','', '平台已明确返回批处理 GPU 并发上限 2。第三份初次请求被拒绝，无 Version/SV；失败不退账。单对象读取返回 HTTP 500，不作为不存在的证明；随后本人完整 Notebook 列表未发现第三份。空槽后允许使用一次工程备用恢复同一冻结配置。','', '额度启动前：正式剩余 5 / 19h 重置；GPU UI 已用 01:43 / 30h，API 总额 21600s 且 used 字符串格式异常。按较小总额估计约剩 4h17，不把估计说成精确余额。每次正式请求前另刷新实际额度。','', '第二批决策：尚未作出；首批三个正式终态已齐备，R9D955 0.956、另两份 0.955。本轮用户要求读取结果与公开区报告，未启动第二波。后续按原任务范围决策；没有有效分数的错误不当作低分。','', '不改最终选择、不修改旧账本、不新增训练或 Dataset。CSV、图、原始数据、权重和凭据不入 GitHub。']
c=P/'continuation_receipt.json'
if c.exists():
 cr=json.loads(c.read_text());s+=['', '持续等待方式：'+cr['status']+'。历史后台调度请求未获自动审批通过，未创建监控。本次前台只读查询已收齐首波分数；该历史拒绝不代表提交仍在评分。']
r.write_text('\n'.join(s)+'\n')
