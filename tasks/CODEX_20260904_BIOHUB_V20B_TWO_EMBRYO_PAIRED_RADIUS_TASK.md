# Biohub-CELL V20B 两胚胎配对 safe-div parent radius 任务

任务 ID：`CODEX_20260904_BIOHUB_V20B_TWO_EMBRYO_PAIRED_RADIUS`  
冻结时间：2026-09-04T16:30:00+08:00  
固定起点：`main@48e54c543afaac8ef01b628c8833b89b4fa5d7bc`  
任务分支：`codex/biohub-v20b-two-embryo-radius-20260904`

## 目标与结论边界

本任务执行 R70/R80/R90 三个 safe-division parent radius 单变量 arm，并以
`TWO_EMBRYO_PAIRED_SENSITIVITY_SCREEN` 的证据等级报告 44b6 与 6bba 两个
embryo 的方向一致性。它不是 multi-fold CV、3-fold CV 或 5-fold CV；199 个
field of view 不是 199 个独立 embryo，也不允许用 sample-level 显著性检验
宣称跨胚胎泛化。checkpoint 训练 split 未闭合，整个任务持续保留
`CHECKPOINT_TRAINING_OVERLAP_UNKNOWN`。

V20A 历史不得改写：最终状态继续是
`BLOCKED_INSUFFICIENT_EMBRYO_GROUPS`，R70/R80/R90 继续全部为
`NOT_RUN_HARD_GATE`。V20B 是新合同，不是 V20A 回填。

## 固定基线与身份

- Notebook：`sailorren/biohub-v19c-public0939-sis14-only`
- Version 1 / ScriptVersionId `346969653`
- baseline submission `55978992`
- 历史 Public Score `0.939`（只绑定该 submission）
- V19C source SHA-256 `92bf632410fedc9eb7e0984a20525590b5583d5abb002d8239ff65d9f51fbf57`
- primary checkpoint `12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771`
- secondary checkpoint `9bac2fa0dadc4a6fc1899e0caf187f4b553e0a7cd90ba1261a68b35ffe9e305f`
- DeepCenter checkpoint `8040999a92f6b7bbd98fa8cf458141e045c0f9ad7c936bdb3b18e1f7edafe2a0`
- support-code manifest `978b626d1fd1e7397435a437dfe68691defe1572fc3c20e61012d7c9b52ed029`
- scorer `royerlab/kaggle-cell-tracking-competition@075fc5f5a52d11077f9dc2b074644618f26939e2`

## 样本与 cache 协议

首选且默认要求为全部 199 个 labeled train samples：44b6=71、6bba=128。
Kaggle runtime 必须实际打开每个 image/Zarr、GT GEFF 和 scorer 所需 metadata，
逐样本记录状态。损坏或不可读样本不得静默删除，并须从三臂对称排除；若只剩
一个 embryo，立即 `BLOCKED_VALIDATION_PAYLOAD_OR_RUNTIME`。

固定 anchor 由“不使用结果、每 embryo 内排除 visible test copy 后字典序第一”
选出：`44b6_0c582fdc` 与 `6bba_062c8d37`。detection、association、ILP、edge
filter、motion relink、single-parent repair、single-frame gap 与 gap2 只运行一次；
canonical cache 精确切在 `AFTER_GAP2_BEFORE_ADD_SAFE_DIVISIONS_POSTLINK`。
三臂必须引用同一 cache SHA。每个 anchor 对三臂分别执行 full-path 与 cached
downstream 等价性检查，并在 R70 重复上游运行以检查未显式 seed 的确定性。

## 三个 arm 与唯一变量

- R70：`BIOHUB_SAFE_DIV_MAX_UM=7.0`
- R80：`BIOHUB_SAFE_DIV_MAX_UM=8.0`
- R90：`BIOHUB_SAFE_DIV_MAX_UM=9.0`

除 `safe_div_parent_radius_um` 外，source、checkpoint、support code、input、
scorer 和所有 active parameters 必须逐项一致。cross-arm checker 或 cache
equivalence 任一失败即停止，不得晋升或提交。

## 指标与晋升

每个 sample、每个 embryo、embryo-equal macro 与 pooled micro 都必须报告
official total、adjusted edge、division Jaccard、TP/FP/FN、node-count penalty、
predicted/estimated nodes、错误分解、safe-div/DeepCenter/cap/topology/schema、
runtime、peak memory、cache SHA 与输出 SHA。候选需同时满足两个 embryo 非劣、
至少一个严格改善、macro 严格改善、micro 非劣、pooled division Jaccard 改善，
并通过全部风险门。若两候选都通过，严格按合同 tie-break 形成唯一胜者；仍相同
则 `NO_UNIQUE_WINNER_NO_SUBMISSION`。

离线晋升只能称为 “Kaggle test candidate”，不能称为已证明提分、预计高于
0.939 或新最佳方案。最终提分证据只能来自新的具体 Kaggle submission Public
Score。

## 外部写入预算与停止条件

用户本任务仅在上述门禁内授权：validation SaveKernel<=1、production
SaveKernel<=1、SaveKernel total<=2、formal submission<=1；retry=0、duplicate=0、
Dataset/Model write=0。没有唯一候选时 production 和 submission 必须为 0；任一
平台写错误不得自动重试。

提交后从 submission ID 创建成功起最多监控 30 分钟；不使用后台 sleep、cron
或长期轮询，不等待约 10 小时后的分数。30 分钟后必须停止，并等待用户显式通知
后才可再次读取分数。

## 完成证据

完成声明要求：合同先于 arm 冻结并提交；sample payload 状态齐全；canonical
config、cache equivalence、determinism、promotion 重算、写入预算、秘密扫描、
Git clean、local/remote/GitHub HEAD 一致及固定 commit blob 回读全部通过。交付
`COMPLETED_VERIFIED` 只说明合同范围内的机械和证据核验，不自动等于性能提升。

## 前置实际读取与当前观测

所有固定材料已经完整读取并由 `contract.json` 的 `read_scope_sha256` 逐项冻结。
当前 principal 为 `sailorren`；CLI 权威 quota 输出为 used 5.55h、remaining
24.45h/30h。V19C 当前 `COMPLETE`。不同 Notebook 的 submission `56002593=0.940`
属于范围外历史状态，不是 V20B 基线或结果。比赛元数据刷新在第 31 页发生一次
SSL EOF，依 `retry=0` 未重试；V20B 使用同日已冻结的 125 页/24,886 路径身份，
并把 Kaggle mount 内 199/199 payload 实读作为更强的运行门。

## 执行终态（2026-09-04）

唯一一次 validation SaveKernel 已创建私有 Notebook Version 1 / ScriptVersionId
`347223762`，随后 Kaggle worker
终态为 `KernelWorkerStatus.ERROR`。运行在 `PREDICTOR_PATCHES` 阶段 fail-closed：
`Calibrated dual-seed patch 2 expected one match, found 0`。墙钟收据为
223.33421959 秒，`predictor_runs_started=0`；因此 199 个 payload 的实读门、两个
anchor 的 determinism/cache equivalence、R70/R80/R90 指标和唯一胜者裁决均未执行。

根因已定位为 validation builder 的 try-guard 机械缩进改变了继承 V19C 单元中
triple-quoted TTA patch sentinel 的字符串内容。V19C sentinel 为 436 bytes、SHA-256
`7d08c964ec364537dc3fb5b2c2d6e705050c2a45f198e904e329f5eb218678ab`；V20B 生成值为
472 bytes、SHA-256
`58dc628c13139db2e55577a5faad48373576e7970599f2ce42d138fe74d8c537`，9 个续行均多
4 个前导空格。故首次 TTA replacement 未发生，后续要求 `_nv` 的 dual-seed
replacement 2 必然匹配 0 次。静态 `--validate-only` 未执行这条动态 patch 链，
所以此前 PASS 不等于平台运行可执行性。

冻结 `retry=0` 已生效：validation SaveKernel=1、notebook run=1、production
SaveKernel=0、formal submission=0、Dataset write=0、Model write=0、retry=0。
最终领域状态为 `BLOCKED_VALIDATION_PAYLOAD_OR_RUNTIME`，selected radius=`null`，
Public Score=`null`。没有 submission，因此 30 分钟提交监控不适用；未来也没有
本任务分数可读取。V20A 的 `BLOCKED_INSUFFICIENT_EMBRYO_GROUPS` 与三个
`NOT_RUN_HARD_GATE` 历史状态保持不变。
