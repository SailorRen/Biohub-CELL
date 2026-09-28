# ILP / readmit 本批执行记录

任务 BIOHUB_FINAL_ILP_READMIT_20260928_V01；任务提交 `6d5a111b80160c0b7f5a302fd50b887a6cdfe322`；执行分支 `codex/final-ilp-readmit-20260928`。

初始状态：LOCAL_PREPARED；当前状态以文末动态表格及账本为准。旧 XRL9 批次 SCORED_ALL / 正式 5/5 保留不动；本批新账本上限正式 5 次、普通运行 5 次及共用工程备用 1 次，任何失败或响应不明先计数后查证，不盲重发。

MEASURED：执行前 Kaggle 账号 sailorren，GPU 总 21600 秒、已用 11836.791 秒、预留 0 秒。提交弹窗显示今日剩余 5 次、重置提示 “in a day”；未取得精确重置秒数，记 UNKNOWN。团队 61 条提交无非终态，最高 Public 0.956。正式提交前重新核验余额。

OFFICIAL_FACT：官方 Timeline API 与页面倒计时均指向 2026-09-29 23:59 UTC，即上海 2026-09-30 07:59。最终选择页面 0/2，未修改。

SOURCE_CODE_VERIFIED：R9D955 完整源码 13 单元已读取并逐单元 AST 检查，SHA256 与任务冻结值一致。ILP 环境变量 → ILP_DIVISION_WEIGHT → --ilp-division-weight → cfg.ilp_division_weight → ILPSolver；readmit 在开放轨迹端点 ±1 帧、4 μm 半径内筛选低阈缓存，保留同帧已有节点距离排重。缓存动态补丁在 head 前执行。原模型、主检测 0.955、relaxed 9、DeepCenter 0.25、输入版本、镜像及输出流程保留。

三份均从冻结 R9D955 独立构建：DIV04 (0.4 / 0.965)、READMIT940 (1.2 / 0.94)、DIV04_READMIT940 (0.4 / 0.94)。允许差异见每份 source.diff；仅两项设置、对应守卫、ILP 消费日志及 readmit 计数、回执身份。36 项静态/动态补丁检查通过；这不是 GPU 运行或正式评分证明。

预定顺序：组合与 DIV04 先进入两个槽位，空出后 READMIT940；每份实际输出和部署检查通过即提交精确版本，不等待其他 Public。首批正式终态前第二批保持未冻结；结果齐备后按任务表最多冻结两份并同批推进。候选输出合法不等于提高 Public；同分不算提升；最终选择不变。

原始回执与本批唯一账本：`experiments/BIOHUB_FINAL_ILP_READMIT_20260928_V01/`。本次未创建定时器或后台守护程序。

## 当前平台状态

观测记录汇总时间：2026-09-28T10:49:05.129949+08:00；阶段 WAVE1_SCORE_PENDING。

|候选|ILP / readmit|Version / SV|submission|普通运行|正式状态|Public|Δ0.956|
|---|---|---|---|---|---|---|---|
| DIV04_READMIT940 | 0.4 / 0.94 | 1 / 353458552 | UNKNOWN | COMPLETE | UNKNOWN | UNKNOWN | UNKNOWN |
| DIV04 | 0.4 / 0.965 | 1 / 353458610 | 56626811 | COMPLETE | SubmissionStatus.PENDING | UNKNOWN | UNKNOWN |
| READMIT940 | 1.2 / 0.94 | 1 / None | UNKNOWN | RUNNING | UNKNOWN | UNKNOWN | UNKNOWN |

本批普通请求 3，已受理 3；正式请求 1/5；工程备用 0/1。旧批次 5/5 不变。

PENDING / UNKNOWN 不代表低分或零分。第一批未取得全部正式终态前，第二批不冻结、不运行。没有后台调度；本会话内继续执行，若中断按账本精确 ID 续接。
