# CODEX_20260904_BIOHUB_V20A_SAFE_DIV_RADIUS

## 结论先行

本任务以 `main@f4af9bc5bbdf79e478e1ccba9897c632fd68c659` 和 V19C ScriptVersionId `346969653` 为固定起点，预注册仅比较 safe-div parent radius `7.0/8.0/9.0 µm`。候选执行前的 embryo-disjoint 硬门已发现：完整 Kaggle competition file metadata 中 199 个带标签 train stems 仅有 `44b6` 和 `6bba` 两个 embryo prefixes，低于最少 3 组。因此终态必须是 `BLOCKED_INSUFFICIENT_EMBRYO_GROUPS`；R70、R80、R90 全部 `NOT_RUN`，Kaggle Notebook/SaveKernel/submission 全部为 0。

## 目标

1. 在任何候选运行前冻结项目、源码、checkpoint、support code、input Dataset、scorer、active parameters、fold 规则、数值容差、晋升门和平台写入预算。
2. 枚举全部有配对 image/GT 结构的 labeled train samples，按官方定义中 folder name 第一段 embryo ID 分组，确定是否可创建至少 3 组的 embryo-disjoint CV。
3. 只在该门通过时执行 R70 复现，再条件式执行 R80/R90；仅当一个唯一候选通过全部离线晋升门时，才允许一次正式 submission。
4. 本次已在第 2 步 fail closed，因此后续范围限于保存阻断证据、决策、验证报告、Git 交付和固定 commit 远端回读。

## 固定基线

- GitHub repository: `SailorRen/Biohub-CELL`
- branch: `main`
- base commit: `f4af9bc5bbdf79e478e1ccba9897c632fd68c659`
- preflight live `origin/main`: `f4af9bc5bbdf79e478e1ccba9897c632fd68c659`
- Kaggle Notebook: `sailorren/biohub-v19c-public0939-sis14-only`
- version: `1`
- ScriptVersionId: `346969653`
- source SHA-256: `92bf632410fedc9eb7e0984a20525590b5583d5abb002d8239ff65d9f51fbf57`
- baseline submission ID: `55978992`
- historical observed Public Score: `0.939`

`0.939` 仅是与上述版本/提交绑定的历史 Public Score，不是 private score、final score 或全局最优证据。

## 已读取范围

已逐文件读取 `AGENTS.md`、当前项目上下文、V19C 优化审计报告、机会表、优先级计划、风险/未知、audit summary、validator results、runtime integrity receipt、guard report、run statistics 与两份 source manifest。各文件 SHA-256 冻结于 `experiments/V20A/preflight_and_read_scope.json`。

V19C 实际 Notebook 容器为 213,952 bytes、12 cells（10 code + 2 Markdown），10 个 code cells 均已检查并通过 AST parse。完整运行日志为 111,209 bytes、622 events，runtime error events 为 0。公开仓库不保存许可证血缘未完全闭合的第三方完整 Notebook 源码、checkpoint 或大体积数据。

## Git 安全预检

任务开始时执行 fetch/status/branch/HEAD/origin/main/ls-remote 检查。当时工作树干净，local HEAD、origin/main 和 `refs/heads/main` 都是固定 commit，ahead/behind 为 `0/0`，所以不需要独立 worktree。不存在需要 stash、reset、覆盖或删除的用户改动。

## embryo-disjoint 硬门

使用 Kaggle 只读 competition-list-files 接口，每页 200 条，读取 125 页，去重后完整获得 24,886 条文件元数据，总字节数 87,609,892,618，canonical metadata SHA-256 为 `260313bb5f12accebd9a70c0b0be43c659090de81f1839c7d06971b11bde3dc6`。未下载 image、GEFF 或 Zarr payload。

枚举结果是 199 个 train stems，199/199 均在官方列表中具有配对 `.zarr`、`.geff` 及必需 metadata paths。按官方定义的第一个 underscore-delimited segment 分组后：

- `44b6`: 71 samples
- `6bba`: 128 samples
- effective embryo groups: 2
- minimum required: 3

这个“2”还是上界：即使某些 payload 最终无法被 scorer 读取，有效 group 只可能减少，不可能从已枚举的所有 train stems 中凭空增加第三个 prefix。test 文件、test stems 和公开测试视频身份没有用于任何 fold 设计或分配。

因硬门失败，`frozen_split.json` 明确保存 `fold_count=null`、`folds=[]`、`NOT_CREATED_HARD_GATE`。不存在可检查的 fold，因此 embryo leakage 状态是 `NOT_EVALUABLE_NO_FOLDS_CREATED`，不写成 PASS。

## 单变量设计（预注册但未运行）

- R70: `BIOHUB_SAFE_DIV_MAX_UM=7.0`
- R80: `BIOHUB_SAFE_DIV_MAX_UM=8.0`
- R90: `BIOHUB_SAFE_DIV_MAX_UM=9.0`

其余 active parameters、checkpoint、support code、input identities 和 scorer 全部冻结在 `experiments/V20A/contract.json`。V19C 源码未显式设置全局 random seed，因此冻结为 `UNKNOWN_NOT_EXPLICIT_IN_SOURCE`，不伪造数值。如果未来新合同允许运行，在运行前还必须先解决该身份为可机器比较的固定值。

`experiments/V20A/verify_resolved_config.py` 要求在所有环境变量、默认值与动态 patch 生效后、推理前捕获唯一 receipt，并对 active config、safe-division 实际函数调用参数、source/checkpoint/support/input/scorer identity、hardware/runtime/output hashes 做严格比对。缺字段、用 Markdown/普通 log print 代替 canonical runtime state、函数调用不一致或出现敏感值都会 fail closed。本次仅运行 checker 的正/反例 self-test，未生成任何伪 runtime receipt。

## 调用链与 cache 边界

静态全源检查表明 parent radius 只在 safe-division 候选的 parent-to-candidate 距离门中影响图行为，不参与上游 detection、association 或 pre-division graph。但静态结论不等于端到端等价性证明。由于 embryo 门先阻断，本任务没有创建或复用 cache，没有 cache SHA，也没有做 cache/full-run 等价核验。详见 `experiments/V20A/safe_div_parent_radius_call_chain.md`。

## 执行与外部操作边界

本任务未执行：

- R70 四样本 smoke 复现；
- R70 embryo-disjoint folds；
- R80/R90 候选；
- training 或 fine-tuning；
- Kaggle Notebook create/save/run/version；
- Dataset/Model create/update；
- competition submission/status polling；
- retry、cancel 或 delete。

因此每 fold、每 sample、每 prefix 的新指标、paired delta、topology/schema、runtime/memory、cache SHA 与输出 SHA 都是 `NOT_RUN`，不用 0、空表或历史 V19C 指标冒充。V19C 四样本历史已观测 TP/FP/FN=`1/0/4`、adjusted edge Jaccard=`0.9214`、division Jaccard=`0.2000`、proxy=`0.9414`，只作旧证据边界，本次没有复现。

## 完成标准

本任务的正确终止不是“实验成功”，而是硬门被真实执行。要交付阻断结论，必须同时满足：

1. 合同在候选运行前被 Git 跟踪并由独立验证器 prepare；
2. 24,886 条文件元数据和 199 样本 inventory/split 哈希自洽；
3. 只有两个 embryo groups 的决策可机器重算；
4. R70/R80/R90、Notebook Version、submission、poll 和 retry 全部为 `NOT_RUN`/0；
5. promotion decision 精确为 `BLOCKED_INSUFFICIENT_EMBRYO_GROUPS`；
6. 敏感材料扫描通过；
7. Markdown 和可移植 HTML 报告产生并经验证；
8. 全部内容推送 GitHub，本地/远端 HEAD 一致、ahead/behind=`0/0`、工作树干净；
9. 固定远端 commit 中的关键文件逐一回读，SHA-256 与本地一致。

域终态保持 `BLOCKED_INSUFFICIENT_EMBRYO_GROUPS`。即使交付机械验证通过，也不得升级为离线实验、配置身份、Kaggle runtime 或 leaderboard 提分已验证。
