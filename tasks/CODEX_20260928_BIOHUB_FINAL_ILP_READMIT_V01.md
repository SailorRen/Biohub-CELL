# Codex：最终冲刺，ILP / readmit 三候选先评分、两次额度后用

任务 ID：BIOHUB_FINAL_ILP_READMIT_20260928_V01
日期：2026-09-28，Asia/Shanghai
仓库：SailorRen/Biohub-CELL
执行分支：codex/final-ilp-readmit-20260928
代码与证据基点：1659cab99bfdca2dde226da350033923d94f3f40
任务路径：tasks/CODEX_20260928_BIOHUB_FINAL_ILP_READMIT_V01.md
初始交付状态：TASK_DEFINED_NOT_EXECUTED

## 1. 本轮目标、预算和边界

承接用户本轮“距离比赛结束还有1天，今天还有5次提交机会”的冲刺要求，采用首批3次、正式出分后最多2次的安排。本文件交付的是可执行任务；不是已启动Codex、已运行Notebook或已有submission的证明。

旧任务BIOHUB_XRL9_TWO_WAVE_20260927_V01已SCORED_ALL、正式5/5；保留旧账本不重置。本任务单独记录本轮新增动作，但用户报告的五次并不证明平台余额。执行前及每次提交前核对真实身份、余额、额度窗口、GPU余额、活动对象和官方截止；相同有效配置已运行或提交则续接，不重复花额度。

本轮范围：首批最多3份、第二批最多2份私有Notebook完整推理及正式提交；不训练、不创建Dataset、不改最终选择、不操作队友账号。不把正常执行本文内候选变成逐份重复申请确认；平台权限和实际额度仍须满足。最多5次正式请求，每个新候选最多1次；失败和响应不明先记账，查清对象前不盲重发，不随平台重置自动增加预算。

计划最多5次完整Save & Run，另共用1次明确工程错误的备用，不做额外GPU诊断或提前跑所有可能分支。静态构建检查可在本地修复；成功评分的配置不重复运行。不因用满五次而重提基线或另换未批准方法。

目标是超过R9D955 / R8D955的正式Public 0.956；同分不算新增提升，不承诺0.959或前百。若接手时另有可核验更高团队成绩，报告同时列该新基准，仍保留0.956对照。

## 2. 证据和生产母版

固定基点必读：
- AGENTS.md。
- reports/20260928_BIOHUB_PUBLIC_UPDATE_AND_RESULTS.md。
- research/PUBLIC_UPDATE_20260928/discussions/743929.json，重点message 3529308。
- experiments/BIOHUB_XRL9_TWO_WAVE_20260927_V01/platform_ledger.json。
- 同实验R9D955/candidate.ipynb、kernel-metadata.json、formal_last_observed.json、deployment_check.json、output_check.json。
- 同实验已存在的构建/检查方法；不要直接启动会覆盖、重跑旧五份的批处理入口。

母版：R9D955，sailorren/biohub-xrl9-r9d955-20260927，V1 / SV353192186，submission 56599964，COMPLETE / 0.956。
源码：experiments/BIOHUB_XRL9_TWO_WAVE_20260927_V01/R9D955/candidate.ipynb。
Git blob SHA1：c456bee508f44992d76c00f9292b0abc321f0bad。
归档源码SHA256：da53daf678724e920403350f4dde0e83b66163ef12d6a0b6efe28b58756c325c。

MEASURED：本队检测阈值0.955→0.950时，relaxed=9的正式分数0.956→0.955；relaxed=8与9、检测均0.955时正式同为0.956。本轮不继续盲降主检测阈值，也不宣称8微米优于9微米。

AUTHOR_CLAIM：讨论743929称，在作者未公开前置后处理、已达0.957的母版上，ILP_DIVISION_WEIGHT 1.2→0.4后0.958，再将READMIT_MIN_SCORE 0.965→0.94后0.959。未取得逐方案submission/SV或完整母版，不能把作者的0.959归属于这两个参数在我们母版上的必然收益，也不能认定readmit单独+0.001。

公开原帖：https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/743929
本次Chat网页读取未取得原帖正文；以上来自固定GitHub中的原始讨论归档，不冒充再次实时读取。Chat已核对母版前两单元的设置：ILP=1.2、readmit=0.965、DET=0.955、relaxed=9.0；未审查全部单元或运行新候选。Codex须完整读取母版并核实实际消费链。

## 3. 首批冻结三个候选

三份均独立从上述R9D955构建，保留相同输入、模型及其余参数。

| 候选ID | ILP_DIVISION_WEIGHT | READMIT_MIN_SCORE | 相对母版改动 |
|---|---:|---:|---|
| DIV04 | 0.4 | 0.965 | 只改ILP分裂成本权重 |
| READMIT940 | 1.2 | 0.940 | 只改端点附近补回检测的最低分数 |
| DIV04_READMIT940 | 0.4 | 0.940 | 仅组合上述两项 |

基线归档为1.2 / 0.965 / Public 0.956，不重新提交。三个候选分别检验两项独立作用和交互；第三份不是声称两个收益可加和。优先把组合及DIV04送入两个可用普通运行槽位，空出槽位后立即运行READMIT940；也可按现有同配置对象续接。不要同时试第三个GPU槽位。

固定不变：BIOHUB_DET_THRESHOLD及守卫0.955、BIOHUB_MOTION_RELINK_RELAXED_UM=9.0、FLOW_RELAXED_UM=0、READMIT_RADIUS_UM=4、LOWDET_THRESHOLD=0.3、tight=5.5、flow tight=7.0、velocity=0.5、learned bonus=1.0、DeepCenter安全分裂阈值=0.25、G1/validator关闭。所有主副模型、权重、head、TTA、融合、ILP其他权重、gapfill、几何分裂规则、短轨、linefit、导出和运行时限保护均保留。

定点修改已有BIOHUB_ILP_DIVISION_WEIGHT / BIOHUB_READMIT_MIN_SCORE赋值；不能全局替换1.2、0.965或0.94。同步更新末尾回执中原有readmit==0.965等对应断言，添加必要只读配置核验，不删检查，不改主检测阈值。ILP成本不是DeepCenter分裂阈值；两者不得混淆。

## 4. 必要检查，不以代理分数拦截正式验证

复用已有Notebook/嵌入代码语法、允许diff、配置消费顺序和实际support动态补丁检查。重点追踪：
- ILP权重从环境变量到配置/命令，再到实际ILP求解调用；确认无硬编码1.2覆盖。仅打印环境变量不够。
- readmit在实际函数中使用本候选阈值，保留低阈检测缓存、空间半径、去重和端点约束；不能误变成全图放宽检测。区分读取阈值、候选通过和最终新增节点；正常零新增不是工程故障。
- 原缓存补丁仍先于head；守卫和只读回执正确适配本候选。需要小型计数即可，不新增逐边大日志或完整验证器。

不建立新CV、训练、全网调研、人工病例审查或阈值网格作为提交门槛。普通输出无变化不能直接断言隐藏无变化；明确未消费参数或异常回退则不冒充有效候选。

沿用母版Private、T4×2、Internet off、kernel_sources为空及比赛输入。四项冻结Dataset：pilkwang/biohub-tracking-support-pack-50ep-v1 V10；pilkwang/biohub-temporal-unet3d-seed314159-v1 V2；pilkwang/biohub-deepcenter-unet3d-center-prior-v1 V5；anvithpothula/biohub-v1284-head-s075 V1。精确挂载配置从母版metadata继承，不能静默使用Latest。
成功镜像摘要：37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461。
保留原主权重断言；head为33913字节、SHA256 625a0d9340f48193f2ec294fc2d81c5bb3c03087eab78ef0ae998a9c4c7da00c。

实际CUDA、挂载、有效配置和完整输出在每份普通运行内验收。覆盖全部实际测试对象，检查真实CSV字段、坐标、时序、唯一性及拓扑，记录直接错误、repair_fallback和deadline_degraded；缺失统计为UNKNOWN，不填0。有效输出通过必要检查即提交其精确Version/SV，不等另一份普通运行结束，更不等第一份Public。

## 5. 首批出分后才冻结最后两个候选

首批已受理对象取得终态后，再依据正式Public写第二批决策。PENDING和ERROR不填零或当低分；若有错误，明确有效比较范围。只读回收无需重复运行。等待期间可准备参数化构建器和静态模板，不启动所有可能分支的GPU推理。

以下是决策备选，不是已验证有效配置。根据实际分数、并列情况、剩余时间及排重，只冻结最多两份：

| 首批正式结果 | 第二批优先设计 |
|---|---|
| 组合唯一最高且>0.956 | 从组合出发，分别试ILP=0.2/readmit=0.94，以及ILP=0.4/readmit=0.9525；一份探索分裂成本更低一步，一份缓和补回阈值 |
| DIV04最高且>0.956，组合未超过它 | 保持readmit=0.965，围绕ILP=0.4试0.2与0.8 |
| READMIT940最高且>0.956，组合未超过它 | 保持ILP=1.2，围绕readmit=0.94试0.9525与0.93 |
| 都未超过0.956且有有效分数 | 保留R9D955；可分别试较温和的ILP=0.8/readmit=0.965、ILP=1.2/readmit=0.9525；这只是对大步长不适配的检验，不称为已证实方向 |

并列时不虚构未显示精度，优先较少改动的最佳母版，并根据哪项单因素实际有收益选择适用行；方案和理由在运行前写入报告。可少用，不为填满额度制造副本；不把作者收益当作本队已测方向。第二批配置未正式出分前不得晋级。

第二批冻结后两份同批推进，不等第四份正式分数再设计第五份，避免额外长评分周期。第二批仅限ILP/readmit这两个因素；不临时加入新模型、G1、检测阈值、分裂规则或作者未公开后处理。

## 6. 时间与持续执行

报告归档官方截止：2026-09-29 23:59 UTC，即上海2026-09-30 07:59。按报告9月28日09:45时点约余46小时；不能误写成9月29日白天截止。Chat本次网页未取得官方时间表正文，Codex执行时核对当前官方时间表、额度重置及规则。

约8小时仅是用户历史经验，作者6—11小时也是作者描述；均非保证。保留排队和隐藏重跑余量，不拖到截止边缘；时间不足则停止增加新运行，不宣称截止后完成评分的有效性已经获得官方确认。

后台调度审批不是构建和送评的前置。仅在真实持续会话中合理间隔查询准确submission；会话结束先同步ID和最后状态，恢复时续查，不声称没有进程的后台会自动推进。不得自行创建系统定时器、后台守护程序或新的跨日循环；本文不是持久后台调度授权，也不复活旧任务监控。

## 7. 最少交付

新报告：reports/20260928_BIOHUB_FINAL_ILP_READMIT_RESULTS.md。
新账本：experiments/BIOHUB_FINAL_ILP_READMIT_20260928_V01/platform_ledger.json。
候选目录：同实验下DIV04/、READMIT940/、DIV04_READMIT940/及第二批实际冻结的两份。

只维护一个本批账本，包含task_id、stage、first_wave/second_wave、run_request_count、accepted_full_run_count、formal_request_count、engineering_spare_count。每候选记录配置、源码哈希、准确Kernel/Version/SV/submission、请求与观察时间、普通和正式状态、原精度Public、直接错误、必要输入/输出验收。未发生的ID和分数为null；不得预填受理或完成。

先同步候选及必要检查、回读关键源码，再启动；每个正式请求受理后立即同步ID；首批终态、第二批决策、最终终态及时归档。不等所有评分完成才保存证据。

报告列正式Public相对0.956和当时最佳的差值。>0.956仅说明本次可观察Public提高；同分不证明隐藏图相同或Private更优。输出合法不等于提分。最终选择不变。

只改本任务分支，不合并main、不强推、不覆盖旧实验或用户工作区。GitHub只存任务、代码、配置、小型回执和报告，不存比赛数据、CSV、图、权重或凭据。复用既有验收，提交固定commit及关键文件回读；不新建大合同。任务同步成功不等于执行完成。
