# Codex：最后一天五候选，滚动同批送评

任务 ID：BIOHUB_LAST_DAY_FIVE_20260929_V01
日期：2026-09-29，Asia/Shanghai（与 Asia/Singapore 同为 UTC+8）
仓库：SailorRen/Biohub-CELL
执行分支：codex/last-day-five-20260929
固定代码与证据基点：d5bb9763dc4cb85defa18f001cc2ec6f1c0ab871
任务路径：tasks/CODEX_20260929_BIOHUB_LAST_DAY_FIVE_V01.md
交付初态：TASK_DEFINED_NOT_EXECUTED

## 1. 本轮目标与时间

承接用户本轮“最新最高0.958，今天还有5次提交，比赛还有1天”的冲刺要求。以正式Public超过0.958为目标，固定以下五个新配置，尽早滚动运行和提交；不是再等待一轮正式结果后才设计最后两份。任务文件入库不表示Codex已经启动或Kaggle已经提交。

本轮核对到的官方Overview时间表：2026-09-29 23:59 UTC，即上海2026-09-30 07:59。9月29日10:46时约余21小时13分，而非完整24小时。接手先核对官方当前截止、实际额度窗口和GPU资源。约8小时只是既往评分经验，不能保证；不要新增“必须截止前完成评分”的未经核实官方规则。
官方来源：https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/

本轮计划新增至多5次正式请求、5次完整普通运行，另至多1次明确工程错误的运行备用。旧两波和旧ILP/readmit任务的5/5记录原样保留；新任务单独记账，不把额度重置当无限授权。模型训练、Dataset写入、最终选择变更、队友账号操作均为0。本轮既定候选不逐份重复申请相同执行授权，仍须遵守平台权限和实际余额。

## 2. 唯一生产母版与现有证据

母版：DIV04_READMIT940，V1 / SV353458552 / submission 56626891，正式COMPLETE / Public 0.958。
Notebook：sailorren/biohub-final-div04-readmit940-20260928。
源码：experiments/BIOHUB_FINAL_ILP_READMIT_20260928_V01/DIV04_READMIT940/candidate.ipynb。
源码SHA256：ac3651a886a11ecab5e89e8e2a80e10f8b4547b7b4775a6a75e437d8e2ea8035。

另一份并列最佳DIV04_READMIT9525：V1 / SV353559196 / submission 56638061 / Public 0.958，只作为已测对照和保留候选，不重跑、不假定其更优。

必要读取：AGENTS.md；reports/20260929_正式结果与最新公开情报.md；旧ILP/readmit实验的platform_ledger.json、上述母版的全部代码单元、kernel-metadata.json、formal_last_observed.json、输入/输出验收，以及已存在的构建和检查脚本。不要执行会覆盖或重新提交旧批次的批处理入口。

已测事实（9月29日10:12上海的归档正式回执）：

| ILP权重 | readmit阈值 | Public | 已测对象 |
|---:|---:|---:|---|
| 0.2 | 0.940 | 0.957 | DIV02_READMIT940 |
| 0.4 | 0.940 | 0.958 | 母版 |
| 1.2 | 0.940 | 0.957 | READMIT940 |
| 0.4 | 0.9525 | 0.958 | DIV04_READMIT9525 |
| 0.4 | 0.965 | 0.956 | DIV04 |

这些是单次显示Public，不证明全局最优、单调性、隐藏图相同或Private收益。ILP/readmit组合已在本队实测有效，后续优先依本队证据，不再依作者0.959声明推算分数。

## 3. 五份固定候选，各相对母版只改一个因素

| 优先序 | 候选ID | ILP权重 | readmit阈值 | relaxed μm | 相对母版唯一算法改动 |
|---:|---|---:|---:|---:|---|
| 1 | DIV06_READMIT940 | 0.6 | 0.940 | 9.0 | ILP 0.4→0.6 |
| 2 | DIV03_READMIT940 | 0.3 | 0.940 | 9.0 | ILP 0.4→0.3 |
| 3 | DIV04_READMIT930 | 0.4 | 0.930 | 9.0 | readmit 0.940→0.930 |
| 4 | DIV04_READMIT94625 | 0.4 | 0.94625 | 9.0 | readmit 0.940→0.94625 |
| 5 | DIV04_READMIT940_RL8 | 0.4 | 0.940 | 8.0 | relaxed 9.0→8.0 |

选择理由均为INFERENCE，收益均为UNKNOWN：0.3/0.6分别检查已测最好0.4两侧的邻近值，0.2退分不证明0.3无收益；0.93检验更低readmit边界，可能增加误补；0.94625是两个并列最佳阈值0.94和0.9525的中点，不是精确估计的最优点；8 μm在旧0.956母版上曾与9 μm同分，本次只检验与已生效ILP/readmit的交互，不能当作既有提分设置。

不构建第六份，不把新0.6与新0.93再合成额外候选，不为了等首批结果而暂扣最后两次。本次不搜索整个网格。即使先收到较早候选的分数，仍只完成未提交的固定名单，不借此追加预算或新算法。

## 4. 最小修改与工程检查

五份独立复制母版。定点修改已有BIOHUB_ILP_DIVISION_WEIGHT、BIOHUB_READMIT_MIN_SCORE或BIOHUB_MOTION_RELINK_RELAXED_UM赋值，必须先于常量消费；同步对应守卫、末尾只读断言和候选ID。禁止全局替换0.4、0.94、9.0等数字；禁止删除守卫来通过检查。

0.94625必须完整写入配置、守卫、运行断言和回执，不能被旧构建器的三位或四位格式化改成其他阈值。复用原ILP实际求解参数和readmit消费计数；RL8保留FLOW_RELAXED_UM=0的原继承公式，并核对有flow和无flow两条路径。

保持DET_THRESHOLD及守卫0.955、readmit半径4 μm、LOWDET_THRESHOLD=0.3、tight=5.5、flow tight=7.0、velocity=0.5、learned bonus=1.0、DeepCenter安全分裂阈值0.25、G1/validator关闭。模型、权重、head、TTA、融合、其他ILP权重、分裂规则、gapfill、短轨、linefit、输出与原时限保护全部保持。

特别保留母版最终坐标导出max(0, int(round(float(node[axis]))))及原内部坐标处理。不改成浮点输出或截断，也不提前整数化内部坐标。公开浮点负结果与线上截断仍是作者报告/未知机制，不能当作修复依据。低阈缓存仍先于head。

沿用母版Private、T4×2、Internet off、kernel_sources为空及比赛输入。冻结Dataset：pilkwang/biohub-tracking-support-pack-50ep-v1/10；pilkwang/biohub-temporal-unet3d-seed314159-v1/2；pilkwang/biohub-deepcenter-unet3d-center-prior-v1/5；anvithpothula/biohub-v1284-head-s075/1。
镜像摘要：37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461。继承原权重和head哈希断言；不静默改输入版本或镜像。

仅复用必要Notebook/嵌入代码语法、允许diff、配置顺序、support补丁检查；普通运行内确认实际CUDA、挂载、参数消费、真实完整CSV字段/坐标/时序/唯一性/拓扑以及错误和降级。缺统计写UNKNOWN，不能当0；异常回退或未消费新参数不能当有效候选。正常零触发不等于故障，可见CSV同样也不等于隐藏预测同样。不把本地GT提分、完整CV、新训练、病例审计、公开区大搜或复杂验收框架放在送评之前。

## 5. 调度：五份滚动送评，不串行等待Public

先按准确有效配置、输入、源码和版本查询本账号/团队已有对象，排除重复；已在运行或已提交就续接，已有同配置有效分数只回收。报告没有新ID不证明平台没有对象。发现重复不临时发明替代算法。

按优先序运行，普通GPU批处理并发最多2且以实时空槽为准。两槽都满就等普通槽位释放，不试第三槽、不取消其他任务。一份普通输出验收通过就立即提交该准确Version/SV，不等其他普通运行结束，不等任何先前候选的正式Public。每次受理立即记录并同步准确ID。

运行前核对实时GPU余额；每次正式请求前刷新实际正式余额和GPU观测并留时间戳，保留旧批次两次GPU未刷新缺口，不能追认。无法精确读到用量时区分UNKNOWN与已知不足，用可核验页面/官方字段补齐，不虚造余额。

单个候选有明确工程错误时，可在本批唯一工程备用内最小修复；不改算法。响应不明先查已有对象，禁止盲重发。一个候选受阻不应阻止其他已通过必要检查的候选在预算内送评。实际资源或截止限制只能完成部分时，按优先序交付真实结果，不为用满而超限。

五次正式请求是硬上限（失败或响应不明也先计数），完整运行请求至多6（5计划+1工程备用），每日重置不增加本任务预算。到官方截止后停止新提交；不声称平台必能在截止前出分。后台调度不是送评前置，不创建新的守护程序、cron或跨日自动实验。会话结束保存准确ID和最后状态，续接只查询已存在的对象。

## 6. 报告、验收与最终选择

新报告：reports/20260929_BIOHUB_LAST_DAY_FIVE_RESULTS.md。
新账本：experiments/BIOHUB_LAST_DAY_FIVE_20260929_V01/platform_ledger.json。
候选目录：同实验下五个候选ID；保留完整源码、source.diff、有效配置、必要检查和小型运行/正式回执。沿用旧验收脚本，不新增大合同。

先同步固定候选及必要检查、回读关键源码再启动；每个实际动作及时保存请求时间、Kernel/Version/SV/submission、状态、观察时间、原精度Public、直接错误与预算。未发生的字段为null，不能预写PENDING或COMPLETE。终态逐项列相对0.958及当时已核验最佳的差值。

>0.958才算本轮新增可观察Public提升；=0.958为显示持平；更低不替换最高方案；ERROR不是低分。所有正式结果齐备或会话结束时，交付真实状态和未完成原因，不将任务交付成功当作实验完成。

现有56626891和56638061两个0.958提交原样保留。本任务可只读核对平台当前最终选择并报告准确ID；“最高分存在”不等于“已经选入最终评审”。不得擅自勾选、取消或变更最终选择；出分后列出可核验候选供用户决定，不保证Private。

只改本任务分支，不合并main、不强推、不覆盖用户工作区、旧源码或旧账本。GitHub仅保存任务、代码、配置、报告、小型回执；不提交比赛数据、CSV、图、权重或凭据。Chat本轮仅读取报告、账本、正式回执、旧构建脚本及metadata，未审查母版全部代码单元或执行模型；Codex接手须完整核对母版和新增源码。
