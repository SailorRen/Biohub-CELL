"""Regenerate this task's report from actual receipts; pending work stays PARTIAL."""
import collections,json
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];load=lambda n:json.loads((P/n).read_text())
d=load('output_v1/diagnostic_results.json');m=load('verified_metrics.json');cs=load('candidate_summary.json');ev=load('event_attribution.json');sel=load('selection_verified.json');ledger=load('ledger.json');binding=load('own_version_binding.json')
ordinary=load('own_ordinary_verified.json') if (P/'own_ordinary_verified.json').exists() else None
formal=load('formal_latest.json') if (P/'formal_latest.json').exists() else None
formal_status=formal['status'] if formal else 'NOT_RUN'
score=formal.get('public_score') if formal else None
sid=formal.get('submission_id') if formal else None
status='PARTIAL' if not formal else 'SCORE_PENDING' if formal_status in ['PENDING','RUNNING','PENDING_READBACK'] else 'PLATFORM_ERROR' if formal_status not in ['COMPLETE'] else 'EVALUATED'
result={'task_id':'BIOHUB_SPRINT01_20260916','status':status,'required_computations_complete':bool(formal and ordinary and formal_status=='COMPLETE'),'diagnosis_status':'EXECUTED_VERIFIED_8_FIELDS_2_EMBRYOS','own':{'selected':'G1','ordinary_status':ordinary['status'] if ordinary else 'RUNNING','binding':binding,'formal_submission_id':sid,'formal_status':formal_status,'public_score':score},'public':{'status':'NO_VERIFIED_PUBLIC_CANDIDATE','formal_submission_id':None,'public_score':None},'historical_baseline':{'name':'Forge','submission_id':56160258,'version':1,'script_version_id':348960877,'public_score':.947,'scope':'archived 2026-09-15, not live re-read this batch'},'requests':dict(collections.Counter(r['action'] for r in ledger['requests'])),'training_calls':0,'dataset_writes':0,'final_selection_changes':0,'diagnostic_summary':d['summary'],'diagnostic_delta':sel['arms'],'formal_improvement':None if score is None else float(score)>.947,'delivery_status':'PENDING_FIXED_COMMIT_READBACK','unknowns':['hidden formal postprocess configuration','full primary-model training lineage'],'source_bounds':'8 repeatedly used FOVs; only 2 embryos; all eight listed in secondary upstream model training manifest; no full pipeline independent validation claim'}
(P/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
lines=['# BIOHUB-CELL 冲刺第一批结果','',f'**当前批次状态：{status}。** 固定 8 视野 A0/G1/R1 配对诊断已实际完成并本地独立复算；G1 按预设规则入选，R1 淘汰，公开路线没有合格候选。G1 生产普通运行状态为 '+result['own']['ordinary_status']+f'；正式状态 {formal_status}，submission {sid if sid else "未执行"}，Public {score if score is not None else "null"}。仍保留 Forge 0.947，最终选择未修改。','', '## 关键结论','',
'1. 使用已保存的两个留组分类器，无训练/重新拟合；诊断 V1/SV350191694、kernel134548482 实际运行 1789.4 秒成功，499 项输出完整分页回收。原预测图复用；补算 432 张原冻结 DeepCenter 热图，磁盘缓存读取 4040 次。',
'2. A0 重复图哈希及分数一致，波动 0。G1 总分增加 0.0000036200476023，44b6 增加 0.0000139670393317，6bba 不变；符合事先冻结的严格大于规则。R1 总分减少 0.0000011043170154，淘汰。未因增益很小而事后更换门槛，也不把它称统计显著。',
'3. 三者分裂 TP/FP/FN 都是 2/1/10；连接 TP/FP/FN 和节点召回也不变。G1 在两个视野少保留 14、9 个节点，节点数量调整项改变；这解释本批受控诊断的微小分数差，不证明分裂正确率提升。',
'4. 官方分裂匹配器对变化事件未给出可靠 TP/FP 归属：G1 38 条分裂替换/移除记录、R1 2 条记录均为 UNKNOWN。未标注事件没有当作负例。',
'5. **尚不能确定下一修改点。** 当前证据支持“筛选影响后续短轨迹和数量项”，不支持继续删除几何门、调阈值或重训。本批不启动第二批。','', '## 四流程结果表','', '|流程|真实执行|诊断官方整体分数|调整后连接项|分裂 TP/FP/FN|正式身份 / Public|决定|','|---|---|---:|---:|---|---|---|']
for arm in ['A0','G1','R1']:
 s=d['summary'][arm];formal_cell=f'{sid or "未提交"} / {score if score is not None else "null"}' if arm=='G1' else '无本批正式提交'
 lines.append(f'|{arm}|8/8 视野|{s["score"]:.12f}|{s["adj_edge_jaccard"]:.12f}|{s["division_tp"]}/{s["division_fp"]}/{s["division_fn"]}|{formal_cell}|'+('原规则诊断基准' if arm=='A0' else '预设规则入选；正式结果单列' if arm=='G1' else '下降，淘汰')+'|')
lines+=['|P1|未运行|—|—|—|未提交 / null|NO_VERIFIED_PUBLIC_CANDIDATE|','', '诊断分数与 Kaggle Public 完全分栏；A0 不是本批重新提交的 Forge。历史 Forge 为 submission56160258 / V1 / SV348960877 / Public0.947。历史 Division0.945 不晋升；本批不声称解释其隐藏 -0.002。','', '### 按胚胎及视野（最终后处理）','', '|范围|A0|G1|R1|G1−A0|R1−A0|','|---|---:|---:|---:|---:|---:|']
for name in ['44b6','6bba',*d['samples']]:
 key='by_embryo' if name in ['44b6','6bba'] else 'by_sample';v=[m[a]['final'][key][name]['score'] for a in ['A0','G1','R1']]
 lines.append(f'|{name}|{v[0]:.12f}|{v[1]:.12f}|{v[2]:.12f}|{v[1]-v[0]:+.12f}|{v[2]-v[0]:+.12f}|')
lines+=['','每个阶段/胚胎/视野的 TP/FP/FN、有效评分行数 n/n_adj 和整体聚合见 `verified_metrics.json`；原始实际评分行及完整输入哈希见 `output_v1/diagnostic_results.json`、`stages.json`。8/8 已执行，排除视野 0；safe-div 与最终图各自保留哈希和新增/丢失边。','', '## 候选与后续影响','', '|流程|原合格候选|分类器调用|学习筛除|最终 safe-div 入选|竞争或 cap 未选|abstain / 帧回退|','|---|---:|---:|---:|---:|---:|---|']
for arm,v in cs['arms'].items():lines.append(f'|{arm}|{v["eligible_before_learning"]}|{v["classifier_calls"]}|{v["filtered"]}|{v["selected"]}|{v["competition_or_cap"]}|{v["abstain"]} / {v["fallback_frames"]}|')
lines+=['','- `candidate_diff.csv` 有 308 条同候选配对记录，原资格集合全部一致；G1 44 次直接筛除，入选变化 38 次；R1 入选变化 2 次。互近邻、后续间距增长、对称性及 DeepCenter 原门均保留。',
'- G1：safe-div 相对 A0 新增 1 边、丢失 37 边；最终新增 5 边、丢失 59 边。R1：safe-div 新增/丢失各 1 边；最终新增 5、丢失 1 边。额外差异来自后续处理，不等于相同数量的分裂事件。',
'- 复用 697 个已有缓存文件进行本地纯 CPU 图重放，24/24 份分裂前/后图哈希与云端精确一致。逐候选选择循环与原 selected 标记一致：A0/R1 各 11 个因帧 cap 未选，G1 为 3 个；源/目标竞争及全局 cap 均 0。G1 另 44 个由学习筛选拒绝。原日志 `deepcenter_rejected` 是差值合计，不能替代独立 DC 计数。',
'- `event_attribution.json` 使用未经修改的官方 `score_divisions`、同顺序同精度输入，在本地复算 24 份最终图并核对完整指标。38/2 条变化事件均不在可靠 TP/FP 集合，保留 UNKNOWN；不是自制 proxy。',
'- 本地重建的 safe-div 图经精确哈希验证后，另用官方匹配器复算 24 份图；`safe_event_attribution.json` 同样得到 G1 38/R1 2 条 UNKNOWN 事件。阶段分开保存。补充重放的 A0 最终图字节哈希与云端不相同，具体差异尚未归因，未用于筛选或最终评分；最终评分使用原云端图且已独立复算。组合连锁变化不能拆成独立因果贡献。','', '## 输入、模型与泄漏边界','',
'- 使用 controlled_config 的 tight55 全部 20 项参数，阈值固定 0.95，无自动诊断选参；A0/G1/R1 各用有序原图的独立深拷贝。原公共前处理、DC、间隙插点、拓扑、短轨迹、平滑均实际执行。',
'- 分类器按真实胚胎显式映射到 held_out[44b6]/held_out[6bba]，运行时核对该胚胎不在拟合组；未用 final 评价训练标注。冻结权重 SHA256：`0a1f9b93bb529e70f4f7c2ba0907eea8b4cecd2befccc8ba1fb75e569edf77a0`。',
'- **上游非独立：**实际 secondary split_manifest 的 train 列表包含全部 8 视野，前四个还同时出现在 test 列表。主模型完整训练谱系未取得。不能扩大为全流程无泄漏；本批分类器留组隔离不等于上游隔离。',
'- 当前官方 metrics.py/division_metrics.py 与固定075fc5哈希一致；原官方适配器保留，legacy proxy 字段仅为诊断。GEFF 通过原 IndexedRXGraph 顺序读取，8/8 GT 输入哈希与历史回执一致；直接数组顺序的初次比对失败另保留，未用于评分。','', '## 生产与正式评分','',
f'- G1 实际对象：`{binding["canonical_ref"]}`，kernel{binding["kernel_id"]} / V{binding["version"]} / SV{binding["script_version_id"]}。完整远端代码单元已回读一致。平台按标题生成实际 slug；保留请求 slug 与实际 slug，不重复创建。',
'- Forge 原 12 个单元中的 11 个逐字节不变，只修改 cell5 分裂部分并加末尾回执。原检测/关联/自动选择器及所有原参数保持不变；诊断固定 tight55 没有强加到生产。生产测试使用已有 final，原验证视野使用显式留组模型。',
'- 原规则同输入重放只作审计，不参与生产输出。普通输出必须证明实际分类器调用和图变化，再校验所有测试 dataset 的 CSV、时限/离线条件，才允许唯一自有正式请求。']
if ordinary:lines.append('- 已验证普通输出：'+str(ordinary['csv']['rows'])+' 行；实际选择 '+ordinary['production_receipt']['selected_label']+'，配置 '+json.dumps(ordinary['production_receipt']['selected_config'])+'。普通与隐藏配置分开，隐藏配置仍 UNKNOWN。')
lines += [f'- 正式状态：{formal_status}；submission：{sid or "null"}；Public：{score if score is not None else "null"}。当前未据普通 COMPLETE 宣称提分。','', '## 公开路线','',
'在60分钟主动检索上限内结束（保守计时上界25分钟），查看当前 Public Score 和 Recently Run 列表、两篇相关讨论、HOCT 作者仓库固定 commit `2ccc5040823bc944ab67790abd1f56eea7cd4f05` 的 README 和模型注册表。未发现可绑定当前准确版本且高于0.947的可复现来源，深读入围 Notebook 0/2，P1 不创建、不提交。',
'5 张卡片的 0.950/0.963 线索在详情页分别核对为 V1/SV336602985=0.885、335859069=0.877、336445398=0.877、337000331=0.877、336441527=0.877。讨论中的局部成绩/口述成绩按 AUTHOR_CLAIM；HOCT 有现成权重注册但无合格更强 Kaggle 版本绑定。读取范围和来源详见 `public_screening.json`，没有把部分渲染源代码说成整本深读。','', '## 请求预算与证据存放','',
f'- 实际 Save & Run：{result["requests"].get("SaveAndRun",0)}/4；正式 submission：{result["requests"].get("Submission",0)}/2；公开路线两类均0。训练/fit/优化器更新0，Dataset写入0，最终选择修改0。失败请求也计入ledger；只读或本地写前门禁停止不算已发平台写请求。',
'- 原始标注、完整预测图、权重、submission.csv 均不入 Git；位于 Kaggle 私有输入/输出或本地 `downloads/BIOHUB_SPRINT01_20260916/` 忽略目录。Git只保存代码、配置、来源/哈希、候选及小型回执。无签名下载URL或凭据。',
'- 启动基点 a1c5859a933e2f71269fc225bc9bbc55851cc860；当时 origin/main 为 a123f0ad7f8808b44909d4c5fab48caf5147b50c，未重置main。任务分支 codex/sprint01-20260916；初始工作区干净，仅本批文件被修改。',
'- 指令按附件原字节保存；复现命令见 `运行说明.md`。本地测试、完整源码回读、评分回执及冻结选择分别举证。GitHub交付目前等待本批固定commit SHA256回读，不能以报告存在当作整体完成。',
'- 本报告仅描述本批实际证据，不改写上一轮 PARTIAL/BLOCKED 历史；没有新证据不启动下一批。','']
(R/'reports/20260916_BIOHUB_SPRINT01_RESULTS.md').write_text('\n'.join(lines))
print(status)
