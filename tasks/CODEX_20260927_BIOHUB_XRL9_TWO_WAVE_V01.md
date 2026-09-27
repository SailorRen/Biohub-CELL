# Codex 执行任务：XRL9 三候选先评分，出分后再用两次额度

任务 ID：BIOHUB_XRL9_TWO_WAVE_20260927_V01  
仓库：SailorRen/Biohub-CELL  
执行分支：codex/xrl9-two-wave-20260927  
固定代码与证据基点：0c50eda41f4cecf6b423b88f7100276c8cfb75e8  
任务文件：tasks/CODEX_20260927_BIOHUB_XRL9_TWO_WAVE_V01.md  
日期：2026-09-27，Asia/Shanghai。

## 1. 用户授权与目标

用户本轮明确要求：还有约两天时间，今天还有五次提交机会；先设计并提交二至三个方案，评分约需八小时，正式结果出来后再优化并使用剩余额度。执行优先，不另做大规模调研或验证框架。

本任务授权 Codex 实际构建、私有 Notebook GPU 推理、必要检查、正式提交和结果回收，不是只准备母版。首批计划三个候选、最多三次正式请求；首批出分后第二批最多两个新候选、两次正式请求；本任务累计正式请求上限五次，不随日额度重置增加。首批未用满的额度不自动扩大第二批上限。无需再次申请这些范围内的执行授权。

用户报告的五次为规划上限，启动前及每次正式请求前核对平台实际余额、额度窗口、身份与活动对象。平台不允许的操作不得执行。上一批 LAST_TWO 已消耗的两次不混入新任务，也不能把旧余额当作当前余额。

提分比较基准为 XRL9：sailorren/biohub-xr0-xrl9-last-two-20260926，V1 / SV353050971，submission 56587392，归档 COMPLETE / Public 0.955。不重跑或重提基线，不自动改变最终选择。

交付任务文件不等于候选已构建、已运行、已提交或已评分。Chat 当前没有 Kaggle 执行或 Codex 启动入口；由 Codex 接手实际执行。本文件初始状态为 TASK_DEFINITION_NOT_EXECUTED。

## 2. 已有证据与必要读取

以下来源均取固定基点，禁止用可变 Latest 替代：

- AGENTS.md。
- reports/20260927_BIOHUB_PUBLIC_UPDATE_AND_RESULTS.md。
- reports/20260926_BIOHUB_XR0_LAST_TWO_RESULTS.md。
- experiments/BIOHUB_XR0_LAST_TWO_20260926_V01/XRL9/candidate.ipynb、kernel-metadata.json：生产母版及部署输入。
- 同批 XD960/source.diff 及 candidate.ipynb：只复用主检测阈值和对应守卫的修改方法。
- 同批 build.py、check_build.py、check_output.py 与 platform_ledger.json：复用构建、检查和真实版本记录。

Chat 已读取两份结果/情报报告、旧 SCORE_FIRST_V02、build.py 和 check_build.py；不将这些读取冒充新候选完整源码检查或运行验收。Codex 必须读取母版全部代码单元并检查生成的新候选。

旧调度参考：b05a5e115111cfae66424f0b2e7eac09c1b914b8 下 tasks/CODEX_20260927_BIOHUB_XR0_LAST_TWO_SCORE_FIRST_V02.md。仅复用必要工程措施；新批预算和后续出分执行以本文件为准，不延续旧批的两次预算或禁止下一轮条款。

| 已评分对象 | 主检测阈值 | relaxed 距离 | 准确 submission | Public |
|---|---:|---:|---:|---:|
| XR0 | 0.965 | 10.0 μm | 56546951 | 0.953 |
| XD960 | 0.960 | 10.0 μm | 56585147 | 0.954 |
| XRL9 | 0.965 | 9.0 μm | 56587392 | 0.955 |

MEASURED：上述独立修改分别取得单次可观察 Public 提升，不证明可加和、参数趋势单调或私榜收益。INFERENCE：据此优先检验组合和邻近一步的延伸；新候选分数均为 UNKNOWN。不把 Aman 的标题成绩、异常回退或旧 G1 试验当作新候选依据。

## 3. 第一批：三个固定候选

三份独立从 XRL9 构建，不把尚未评分的新候选依次叠加成不可归因的多模块方案。

| 候选 ID | 简称 | BIOHUB_DET_THRESHOLD及对应守卫 | BIOHUB_MOTION_RELINK_RELAXED_UM | 相对 XRL9 的唯一算法改动 |
|---|---|---:|---:|---|
| R9D960 | A：已有效设置组合 | 0.960 | 9.0 | 检测阈值 0.965→0.960 |
| R8D965 | B：关联再收紧一步 | 0.965 | 8.0 | relaxed 距离 9.0→8.0 μm |
| R9D955 | C：检测阈值再降低一步 | 0.955 | 9.0 | 检测阈值 0.965→0.955 |

A 检验 XD960 的检测设置能否与 XRL9 互补；B 沿已验证 10→9 的方向试一个等步长邻点；C 与 A 在相同 9 μm 下形成 0.965/0.960/0.955 的检测阈值比较。B 的 8.0 与 C 的 0.955 均没有既有正式提分证据；这两个是明确的探索值，不宣称更低必然更好。C 中的 0.955 是参数，不是预测 Public。

修改要求：

- A/C 只定点修改 Cell1 的主检测环境变量与 Cell2 对应守卫；同步修改只读运行回执中的阈值断言。不能全局替换所有 0.965。
- B 在常量消费前将已有 BIOHUB_MOTION_RELINK_RELAXED_UM 的 9.0 改为 8.0；同步只读回执断言，不另加重复赋值掩盖原设置。
- 三份 BIOHUB_READMIT_MIN_SCORE 继续为 0.965；FLOW_RELAXED_UM=0，按原公式继承各自 relaxed 距离。有 flow 和无 flow 的配置/消费路径都检查。
- 继续保持 tight=5.5、flow tight=7.0、velocity=0.5、learned bonus=1.0、DeepCenter 安全分裂阈值=0.25、G1/validator 关闭。
- 不把参数改动实现为最终边长度硬删除；保留原匹配成本、候选准入、Hungarian、排序、cap、图修复及导出。
- 完整保留原模型、head、主副融合、TTA、ILP、flow、readmit、gapfill、分裂、短轨过滤、linefit、运行时限保护。低阈缓存补丁必须仍先于 head；遥测不得改变预测。

## 4. 部署、检查与首批调度

沿用母版成功环境：Private、T4×2、Internet off、kernel_sources 为空，挂本比赛及以下冻结输入：

- pilkwang/biohub-tracking-support-pack-50ep-v1 V10。
- pilkwang/biohub-temporal-unet3d-seed314159-v1 V2。
- pilkwang/biohub-deepcenter-unet3d-center-prior-v1 V5。
- anvithpothula/biohub-v1284-head-s075 V1。

原成功镜像摘要：37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461。保留三个主权重原断言；head 为 33913 字节、SHA256 625a0d9340f48193f2ec294fc2d81c5bb3c03087eab78ef0ae998a9c4c7da00c。实际镜像、CUDA、挂载与哈希在候选正式普通运行内验收，不额外启动 GPU 探针；无法继承时记录问题，不静默换环境。

接手先查询同配置的既有 Notebook、运行及团队 submission，按有效源码参数、输入和准确版本去重。已有对象续接并回收，不因新任务名重跑；已评分同配置只取结果。不能仅靠可见 CSV 相同认定隐藏预测重复，也不能靠 GitHub 没有文件认定平台没有提交。

仅做必要检查：Notebook/嵌入代码语法、允许 diff、配置消费顺序、原 support 上的真实补丁锚点，以及普通输出完整性。复用旧检查器并正确更新候选枚举和期望值，不能让旧 .965/9.0 断言误伤新配置；不得删掉检查以求通过。无需独立 CV、局部 GT 提分、逐病例报告或新的大规模搜索作为提交前置。

普通运行必须完成全部实际发现测试对象，验证 CSV 字段、坐标、时序、唯一性和父子拓扑；记录实际参数、repair_fallback、deadline_degraded、直接错误。缺失统计记 UNKNOWN，不当作 0；异常回退或未消费新参数的输出不得当成有效候选提交。正常零触发与异常回退必须区分。

优先顺序 A→B→C；按实际可用 GPU 并发运行，不占用或取消其他任务。每份普通输出通过必要检查就立即提交其准确 Version/SV，不等其他普通运行结束，更不等上一份正式 Public。目标是让首批三个尽早进入评分队列。

若第三份确实被额度或运行故障阻断，允许首批实际只提交两份，真实记录原因；不要为凑三份临时发明替代算法。工程备用只用于明确错误的最小修复。

## 5. 出分后再决定第二批，最多两次

八小时是用户提供的预计评分时长，不是完成承诺，也不是第二批自动启动的时钟条件。第二批前必须取得首批所有已受理对象的终态；未提交对象标 NOT_SUBMITTED，不虚构待分。PENDING 时不使用预留额度；ERROR 不是低分，也不据此推断方向无效。

先把准确 ID、终态、正式 Public、相对 XRL9 的差值及错误保存并同步，然后在结果报告的“第二批决策”写清依据、母版、参数、去重和实际剩余额度。冻结第二批源码与 diff 后，在本轮用户授权内继续执行，不重复请求同一范围的许可。

第二批按实际结果选择，不现在假定胜者：

1. 检测设置与 B 都有相对 XRL9 的正式收益：优先将 B 的 8.0 μm 与 A/C 中正式分数更高的检测设置组合；这是新的交互实验，仍不能假定增量相加。
2. 只有检测方向有收益：以 A/C 中最佳实测配置为母版，在已测阈值之间选一个尚未提交的中点，例如 0.9575 或 0.9625；或仅做一次有明确数据理由的关联插值。一次只改一个因素。
3. 只有 B 有收益：优先把已测检测设置与 8.0 μm 交叉验证，或测 8.5 μm 的邻近插值；不要把检测在 9.0 μm 下无收益误当作在 8.0 μm 下必然无收益。
4. 首批有效分数均未超过 0.955：保留 XRL9；剩余额度可用于较强已测方向的 8.5/9.5 μm 邻点（检测仍 0.965），但先排除已有同配置并写清结果支持。无可执行的新候选或证据不足时允许少用，不为用满而重提原版。

两次是上限，不要求用满。第二批仅限同一检测/关联框架内的小范围组合或插值；不得扩展为新训练、G1、多帧分裂、全量参数网格或复制其他整套模型。不能用普通日志、本地代理分、CSV 大小或宣传文字替代正式 Public 来决定方向。

第二批新候选同样尽早完成必要运行后提交，可在冻结方案后同批推进，不必先等第四次约八小时再做第五次。最终比较基准为截至当时所有已评分候选中的最高正式 Public，同时保留相对 XRL9 的差值。显示同分记“未观察到新增提升”，不算提分。

## 6. 总预算、真实等待与退出

本任务计划完整 Save & Run 最多五次（首批三、第二批二），另共用一次工程备用；正式请求最多五次（首批≤三、第二批≤二），每个新候选最多一次。失败和响应不明的正式请求也先记账；响应不明先查对象，禁止盲重发。已受理的准确 submission 只读查状态，不重复提交。

训练、Dataset 写入、最终选择修改、其他账号操作、修改旧母版和旧账本均为零。不得自动突破本任务上限、为新额度窗口再加五次、接受规则、报名或改变共享设置。

等待必须依赖真实可持续的 Codex 执行会话或已实际建立的受支持调度；不能在无执行进程时声称后台正在运行。会话中断先同步准确 ID、最后观察时间和状态；恢复时续查现有对象。Chat 的定时复核若建立，仅检查 GitHub 回执，不等于 Kaggle 查分进程，更不负责自动启动第二批。

归档时间表为 2026-09-29 23:59 UTC，即上海 2026-09-30 07:59；执行时核对官方当前时间表，不拖到截止边缘。截止后不再启动任何正式提交。本授权不保证平台会在约八小时内出分。

## 7. 最少交付与完成判据

结果文件：reports/20260927_BIOHUB_XRL9_TWO_WAVE_RESULTS.md。  
账本文件：experiments/BIOHUB_XRL9_TWO_WAVE_20260927_V01/platform_ledger.json。

每个候选目录只保留完整 ipynb、source.diff、冻结参数/输入、必要检查和小型执行回执。每次受理后立即记准确 Notebook / Kernel / Version / SV / submission ID、请求时间和状态并同步，不能等全批结束才落盘。

账本至少使用 task_id、stage、formal_request_count、planned_reserve=2、wave1、wave2；wave1/wave2 为候选记录数组，每条包括 candidate_id、effective_config、kernel_ref、version、script_version_id、submission_id、requested_at、observed_at、status、public_score、direct_error。未创建字段为 null，不伪造 ID；public_score 保留平台返回精度。stage 区分 PREPARED、WAVE1_SCORE_PENDING、WAVE1_SCORED、WAVE2_SCORE_PENDING、SCORED_ALL、PARTIAL_BLOCKED。

首次首批提交回执、首批终态与第二批决策、最终终态三个节点及时同步本分支；每次固定 commit 并回读任务、报告、账本及关键源码。复用既有检查，不新增庞大冻结合同。

只改本任务分支；不 merge/main、不强推、不覆盖用户工作区，不提交原始比赛数据、模型、图、CSV、凭据。报告列出真实读取范围、实际运行/请求次数、准确正式分数和未知项；没有实际运行或评分则不能声明执行完成。任务交付验收与模型提分结论分开，不将交付成功标为比赛实验 COMPLETED_VERIFIED。
