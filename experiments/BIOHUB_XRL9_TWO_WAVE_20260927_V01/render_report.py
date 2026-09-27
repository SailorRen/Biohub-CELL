"""Render exact local evidence status; never infer a missing score."""
import json
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;l=json.loads((P/'platform_ledger.json').read_text());r=P.parents[1]/'reports/20260927_BIOHUB_XRL9_TWO_WAVE_RESULTS.md'
s=['# XRL9 两波正式评分执行记录','',f"状态：{l['stage']}；报告生成时间 {datetime.now(timezone.utc).isoformat()}（UTC）。",'', '任务交付 commit：`ffd6a3b6036037c76372787b487f6d800454e8e4`；原文 SHA256：`aa66741012266c7e0c30d186f2ac2819206cfa567e4b0ae0591bad15c4908d6d`。','', 'MEASURED 基线 XRL9：Public 0.955，submission 56587392，V1 / SV353050971。新候选只有正式 Public 才用于比较。', '', '| 候选 | DET / relaxed µm | Version / SV | submission ID | 状态 | Public | Δ XRL9 | Δ R9D955 0.956 | 请求时间 UTC | 最后观测 UTC | 直接错误 |','|---|---|---|---|---|---|---|---|---|---|---|']
for a in l['wave1']+l['wave2']:
 v=a.get('public_score');delta=f'{float(v)-.955:+.4f}' if v is not None else 'UNKNOWN';cfg=a['effective_config'];name=a['candidate_id'];ref=a.get('kernel_ref');name=f'[{name}](https://www.kaggle.com/code/{ref})' if a.get('version') and ref else name
 vals=[name,f"{cfg['det']} / {cfg['relaxed_um']}",f"{a.get('version')} / {a.get('script_version_id')}",a.get('submission_id'),a['status'],v,delta,(f'{float(v)-.956:+.4f}' if v is not None else 'UNKNOWN'),a.get('requested_at'),a.get('observed_at'),a.get('direct_error') or ('未返回错误' if a.get('status')=='SCORED' else 'UNKNOWN')]
 s.append('| '+' | '.join('UNKNOWN' if x is None else str(x).replace('|','/') for x in vals)+' |')
s+=['',f"预算：已发送 Save & Run 请求 {l['full_run_count']}（含明确失败）；实际受理完整运行 {l.get('accepted_full_run_count',0)}；工程备用 {l['engineering_spare_count']}/1；正式请求 {l['formal_request_count']}/5。第二波最多 2，首批正式结果齐备之前不启动。",'', '三份候选已通过 27 项小型检查：完整 Notebook/13 代码单元、AST、允许差异、参数消费、实际 support 动态补丁、缓存先于 head。冻结源码 commit `00a930ffe17bbda213397a438bc3fd45a0ea4cc0`，32/32 文件远端逐字节回读通过。静态检查不等于运行通过或正式得分。','', '输入冻结 primary V10、secondary V2、DeepCenter V5、head V1，Private、T4×2、Internet off。三份已受理运行 API 回读源码一致、GPU enabled、原镜像摘要一致；界面通用镜像标题为 Latest，实际摘要另存 ordinary_readback.json。实际挂载版本与完整输出在每份 deployment_check.json / output_check.json 中验收后才提交。','', '平台已明确返回批处理 GPU 并发上限 2。第三份初次请求被拒绝，无 Version/SV；失败不退账。单对象读取返回 HTTP 500，不作为不存在的证明；随后本人完整 Notebook 列表未发现第三份。空槽后允许使用一次工程备用恢复同一冻结配置。','', '额度启动前：正式剩余 5 / 19h 重置；GPU UI 已用 01:43 / 30h，API 总额 21600s 且 used 字符串格式异常。按较小总额估计约剩 4h17，不把估计说成精确余额。每次正式请求前另刷新实际额度。','', '第二批决策（WAVE2_SCORE_FIRST_V02）：按用户固定任务 74ffade，以 R9D955 V1/SV353192186、submission 56599964、Public 0.956 为母版，独立构建 R9D950（DET .950 / relaxed 9）和 R8D955（DET .955 / relaxed 8）。不叠加其他算法；比较基准 .956，仍保留 .955 对照。启动前归档正式余额2；GPU页面已用02:36/30h，接口总额6h存在口径差异，保守估计余3h23。冻结源码和回执先远端回读，再启动两份GPU普通运行；各自验收后立即正式提交，不等首份Public。','', '不改最终选择、不修改旧账本、不新增训练或 Dataset。CSV、图、原始数据、权重和凭据不入 GitHub。']
s+=['', '持续等待方式：已授权当前聊天值守 biohub；运行条件为本地电脑与应用保持运行。历史后台拒绝已被后续明确授权与实际创建回执替代。','', '## 第二波当前执行状态','']
for a in l['wave2']:
 arm=a['candidate_id'];out=P/arm/'output_check.json';dep=P/arm/'deployment_check.json'
 op=json.loads(out.read_text()).get('status') if out.exists() else 'UNKNOWN'
 dp=json.loads(dep.read_text()).get('passed') if dep.exists() else 'UNKNOWN'
 s.append(f"{arm}：普通运行 {a.get('ordinary_status',{}).get('status','UNKNOWN')}；输出验收 {op}；部署验收 {dp}；正式ID {a.get('submission_id') or 'UNKNOWN'}；正式状态 {a.get('formal_status','UNKNOWN')}；Public {a.get('public_score') or 'UNKNOWN'}。")
s+=['','两份已通过实际 CSV 覆盖、坐标/时序/图结构、参数消费检查；repair_fallback=0、deadline_degraded=0。实际 Inputs 为 primary V10、secondary V2、DeepCenter V5、head V1，原镜像摘要及主权重哈希核对通过，运行日志和回执证明 T4×2。','', '普通预算6/6、工程备用1/1已用尽。已有正式ID只查询，不重提；响应不明先核对对象。两份正式Public齐备前不开展下一轮分析，不修改最终选择。冻结代码61103113bf333fb7586488103d710c938e92a3d5已9/9远端回读。正式受理不等于评分成功；完整任务尚待终态回收。']
r.write_text('\n'.join(s)+'\n')
