"""Render measured state; never infer a score from ordinary completion."""
import json
from decimal import Decimal
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = P.parents[1]
s = json.loads((P / 'results.json').read_text())
m = json.loads((P / 'manifest.json').read_text())
l = json.loads((P / 'write_ledger.json').read_text())
f = s['formal']; baseline = s.get('baseline_latest', {})
scored = f.get('status') == 'COMPLETE' and f.get('public_score') is not None
delta = str(Decimal(f['public_score']) - Decimal(baseline['public_score'])) if scored and baseline.get('status') == 'COMPLETE' and baseline.get('public_score') else 'UNKNOWN'
best = s.get('own_best_before_submission', s.get('current_own_best', {}))
best_delta = str(Decimal(f['public_score']) - Decimal(best['public_score'])) if scored and best.get('public_score') else 'UNKNOWN'
summary = json.loads((P / 'ordinary_summary.json').read_text()) if (P / 'ordinary_summary.json').exists() else {}
selected = summary.get('actual_postprocess', {}).get('selected_label', 'UNKNOWN')
selection_comparison = ('普通运行与B0同选tight55。' if selected == 'tight55' else
                        '普通选择尚未取得。' if selected == 'UNKNOWN' else
                        '普通运行选择与B0的tight55不同；这是保留原自动选择器后产生的实际结果，不能把最终差值单独归因于坐标平滑而排除后处理选择变化。')
verdict = ('高于B0' if Decimal(delta) > 0 else '与B0持平' if Decimal(delta) == 0 else '低于B0') if delta != 'UNKNOWN' else '尚不能判断是否提分'
status = '已取得正式终态成绩' if scored else '尚未取得正式终态成绩；本任务未完成'
window = s.get('formal_observation_window', {})
observation_note = (f"正式观察窗口按冻结合同为3小时，起点UTC `{window.get('formal_start_at_utc')}`，计划截止UTC `{window.get('deadline_at_utc')}`；截止边界最后官方快照为UTC `{window.get('last_official_observation_at_utc')}`，状态仍为 `{f['status']}`。最后请求因启动与网络耗时在计划截止后约15秒记录，不继续轮询。当前为 `PARTIAL_SCORE_PENDING`，未作完成声明，分数及两项差值均为null；没有创建自动后续任务或承诺后台完成。" if window.get('status') == 'ENDED_SCORE_PENDING' and not scored else '正式观察以实际平台回执为准。')
validation = json.loads((P / 'final_verification.json').read_text()) if (P / 'final_verification.json').exists() else {}
validation_note = (f"最终冻结验收：{validation.get('passed')}/{validation.get('total')}项通过，状态`{validation.get('status')}`。未通过项：{', '.join(x['id'] for x in validation.get('checks', []) if not x['passed']) or '无'}。缺少正式终态分数时，这表示整体任务尚未验收通过，不表示已通过的20项合成测试失败。详见final_verification.json；成绩链独立状态见score_chain_verification.json。" if validation else '最终验收回执尚未生成。')
text = f'''# LINEFIT_BOUNDARY 单候选实测报告

**{status}。{verdict}。** 本报告的实验状态、成绩比较与 GitHub 交付分别举证。当前记录时间来自下方平台回执，不把普通 COMPLETE、局部测试或 proxy 当正式成绩。

## 冻结对象与授权范围

任务 `LINEFIT_BOUNDARY_20260909`。用户接受上一轮“分裂边界内 linefit”单候选建议，授权实际运行。合同 SHA256：`38ef065b940817d544c3d75de505f955473583a1f9dbf6a7a01019af5fb97bfd`；manifest SHA256：`eb45073c9ab58005c603353d59782b4d6c879b03027c15e27bd91573279cbdda`。

只在 B0 的 linefit 回溯进入前驱前，要求前驱恰有一个后继，阻止跨越分裂父→女儿边。前向逻辑、weight=.8、window=2、模型/权重/输入版本/检测/融合/TTA/ILP/motion/gap/safe-div/短轨和原自动选参器均不变。增加的五项统计不改变预测。13个cell仅cell5的指定函数改变；metadata仅id/title改变。原B0未修改。没有新增训练、Dataset/Model写入、组合候选、扩展参数搜索或比赛最终提交选择改动。B0原有的7项后处理自动比较完整保留，不将作者历史选择写死。

| 对象 | Notebook / Version / ScriptVersionId | submission / 状态 / Public |
|---|---|---|
| B0 | sailorren/biohub-946-b0-repro-20260908 / 1 / 348114666 | 56091397 / {baseline.get('status','UNKNOWN')} / {baseline.get('public_score','UNKNOWN')} |
| 候选 | {s['ref']} / {s.get('version')} / {s.get('script_version_id') or 'UNKNOWN'} | {f.get('id') or '尚未正式提交'} / {f['status']} / {f.get('public_score') if scored else 'null'} |

候选 kernel ID：`{s.get('kernel_id')}`。本地 Notebook SHA256：`{m['candidate_notebook_sha256']}`；实际SDK序列化写入源码 SHA256：`{m['submitted_source_sha256']}`。Kaggle返回JSON排版可能不同，平台字节hash与13cell源hash另存 read 快照及 remote_binding；不混淆文件hash与wire hash。

正式相对B0变化：`{delta}`；相对提交前自有最好成绩 `{best.get('public_score','UNKNOWN')}` 的变化：`{best_delta}`。基线当前读取状态来自本轮官方 submissions API 的 submission56091397，并与浏览器 Version1/SV348114666描述核对，不使用历史标题分数。

## 实际执行与测试

- linefit 合成测试：20/20 PASS，实际执行提取的原函数与候选函数；直/弯无分叉轨道逐字节等同B0、父女儿两侧隔离、旧B0跨边界敏感性正对照、起终点/孤立/非连续边/禁用、拓扑与非坐标字段保持、观测纯度和物理单位。
- 独立候选/写入审阅：24/24 PASS，包含实际无网络mock验证。不明写结果退出3，账本落盘后禁止第二次写；只读TLS每层最多3次、嵌套最坏9次，写传输重试0且send上限1。
- 普通输出独立补充审查：35/35 PASS；10份文件哈希一致，run_stats与运行内审计绑定，12个视频各99个连续唯一窗口，共1188个，四个测试视频统计完整。冻结collector原本没有独立验证完整窗口集合，这一缺口由补充审查闭合；补充回执生成于唯一正式请求之后，不倒写为提交前已取得的检查。系统curl恢复传输另有26/26独立审查通过，冻结19文件未变。
- 官方评分诊断：6合成场景、2图完整聚合、83/83断言 PASS。官方075fc5与B0旧proxy在弱连通单分支、一fork服务多个GT等场景实际出现差异；正常分裂对照一致。它不替换候选的原自动选参器，也不构成真实提分证据。
- 没有取得同一份生产预测图与GT：`NO_SAME_PREDICTION_GRAPHS`。追加只读目录检查实际列出B0的8个后处理前val GEFF路径；源码确认选参使用的后处理图只在内存，当前没有取得配对GT，不能用原始图替代实际选择图。目录枚举因TLS和接口分页问题为PARTIAL，不据此断言完整输出不存在GT。使用固定官方评分器对同一批图重评分后，原PP排序是否改变仍UNKNOWN。诊断隔离环境NumPy/SciPy与Kaggle不同，GEFF CLI I/O未运行；完整实际评分/聚合函数已执行。详见 scorer_diagnostic.json/.md 和 production_graph_availability.json。

唯一保存请求时间为上海 2026-09-09 10:32:38。响应返回 Version1/kernel133664101、空error与空invalid_sources，但相对`/code/`地址触发本地严格ref保护。随后只读 GetKernel核实目标ref、kernelID、Version及13cell源码完全相同，浏览器显示 GPU T4×2运行。没有重复保存或创建修复版本；原不明状态与回读回执均保留。

实际保存请求 `{sum(o['action']=='save' for o in l['operations'])}/1`，正式 submission请求 `{sum(o['action']=='submit' for o in l['operations'])}/1`。任何写入不确定均先只读核验，不自动重发。

## 普通运行与正式结果分离

普通最近状态：`{s['ordinary'].get('last_status')}`，读取时间UTC `{s['ordinary'].get('observed_at_utc','UNKNOWN')}`；输出验收：`{s['ordinary'].get('verified')}`。

回收状态：`{s.get('status','UNKNOWN')}`。普通运行结束后的固定Version、三个输入版本及13cell源码已核对。早前浏览器日志读取遇自动审批超时，API/输出下载另遇TLS连接错误，均保存历史回执。随后以固定Version输入页面及官方API完成身份核对，系统curl在TLS验证开启、无自动重试条件下回读10个小型审计文件，冻结collector完整执行通过。详见readback_interruption.json、fixed_version_ui_receipt.json及curl_collection_receipt.json。下载恢复没有触发Notebook重跑或改变候选。

普通自动后处理选择：`{selected}`，完整实际配置保存在 ordinary_summary.json。正式隐藏运行的后处理选择、分项及Private Score仍为UNKNOWN，不能从普通输出推断。

{selection_comparison} 只有取得正式Public后才可比较；单次结果也只能说明本次正式比较，不能证明稳定泛化收益。

普通边界命中节点数：`{summary.get('boundary_nodes','UNKNOWN')}`；其中实际平滑：`{summary.get('smoothed_boundary_nodes','UNKNOWN')}`；候选相对输入坐标位移总和/最大值：`{summary.get('boundary_shift_um_sum','UNKNOWN')}` / `{summary.get('boundary_shift_um_max','UNKNOWN')}` µm。边界命中不等于最终坐标改变，此位移也不是与B0预测的差值。

正式状态：`{f['status']}`；读取时间UTC：`{f.get('observed_at_utc','UNKNOWN')}`；正式错误说明：`{f.get('error_description','')}`。只有准确绑定的submission为COMPLETE且有数值Public才判断收益；持平/下降也如实交付，不追加实验。

{observation_note}

{validation_note}

## GitHub交付

本轮GitHub交付范围为代码、配置、哈希、合成测试、评分诊断、平台小型回执和本报告，目标仓库为 SailorRen/Biohub-CELL。是否完成须以对应固定提交的远端回读为准。原始源码下载、依赖环境与完整日志留ignored downloads，未提交比赛数据、模型权重或submission.csv。

内容提交与最终回执提交的固定SHA、逐文件远端回读以 delivery_receipt.json及最终交付输出为准。当前文件本身不自证远端完成。冻结合同要求实际正式终态成绩、验收通过、干净Git与GitHub权威远端回读；评分未结束时只记录实际状态，不承诺后台完成。
'''
(ROOT / 'reports/20260909_LINEFIT_BOUNDARY_实测报告.md').write_text(text)
