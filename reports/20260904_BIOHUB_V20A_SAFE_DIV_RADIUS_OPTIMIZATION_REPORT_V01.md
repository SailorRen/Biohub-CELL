# Biohub V20A safe-div parent radius 单变量优化审计报告

生成日期：2026-09-04（Asia/Shanghai）

任务：`CODEX_20260904_BIOHUB_V20A_SAFE_DIV_RADIUS`

基线：`main@f4af9bc5bbdf79e478e1ccba9897c632fd68c659` / ScriptVersionId `346969653`

## 结论

**最终域状态：`BLOCKED_INSUFFICIENT_EMBRYO_GROUPS`。**

已完整枚举 Kaggle 比赛文件列表：125 页、24,886 条唯一文件元数据、199 个带标签 train stems。199/199 在元数据层面具有配对 `.zarr`、`.geff` 及必需 schema paths。但依照官方规则以 folder name 第一段作为 embryo ID 分组后，只得到 `44b6`（71 样本）和 `6bba`（128 样本）两组。冻结合同要求至少 3 个有效 embryo groups，因此在任何候选运行之前 fail closed。

R70、R80、R90 均为 `NOT_RUN_HARD_GATE`；没有可用 fold，没有新的 sample/fold/prefix 指标或 paired delta，也没有 selected radius。Kaggle Notebook Version、SaveKernel、Notebook run、competition submission、status poll 和 retry 计数均为 0。submission ID 和当前 Public Score 均为 `null`；30 分钟监控为 `NOT_APPLICABLE_NO_SUBMISSION`。

这不是对 8.0 或 9.0 µm 的负面实验结论：它们没有被运行。只能说，在用户预注册的 embryo-disjoint 晋升标准下，当前训练集的独立 embryo 数不足以产生允许候选实验的证据。

## 一页结果表

| 项目 | 结果 | 证据边界 |
|---|---|---|
| 有结构可用的 labeled train samples | 199 | `HOST_CONFIRMED_METADATA_ONLY`；未下载 GEFF 内容 |
| 有效 embryo groups | 2 | `44b6=71`，`6bba=128` |
| 合同最低要求 | 3 | 运行前冻结 |
| frozen folds | 0 / `null` | 硬门失败，未创建 fold |
| R70 / R80 / R90 | 全部 `NOT_RUN` | 不是 0 分，也不是缺失运行 |
| selected radius | `null` | no promotion |
| Kaggle Version / submission | 0 / 0 | 没有平台写入 |
| submission ID / Public Score | `null` / `null` | 本任务没有提交 |
| retry / status polls | 0 / 0 | 没有后台监控 |

## 1. 实际读取了哪些固定资料

下表文件都已在固定起点上完整读取，而不是只看摘要。逐文件回读清单保存在 `experiments/V20A/preflight_and_read_scope.json`。

| 文件 | SHA-256 |
|---|---|
| `AGENTS.md` | `3d93338818c2e4ecbaad66a77abc47b9512c0e19fecdf0499868e11a27cdadcf` |
| `governance/CURRENT_PROJECT_CONTEXT.json` | `6a9b84bacbb52b9128d98856d3573342f8f5e44d4fa39477375d41e93829ecfc` |
| V19C optimization report | `a4033313b87e0a6b1876e17996f484a61637b4696c59967a552267d7336013a1` |
| `05_optimization_opportunities.csv` | `45ddae00221d71719a04c8ff9bca0c996875e0987ddf011cc76209cdb02a1368` |
| `06_prioritized_optimization_plan.md` | `0703866348c15ea947df272caa493bc1fd0dc7b5cb602aa0054abf24570e8246` |
| `07_risks_and_unknowns.md` | `51982a4baedab1a8d5c5bbe058e4a0452ef901f4e53b60324e4b6b058e160373` |
| optimization `audit_summary.json` | `327d9a368d99076c8fcd216df299f1f323a81e4b3d71d723081095949dd4ece3` |
| V19C `validator_results.csv` | `ca444b158cb19f8dfc182e38fcd3aab7f2a05eb81d7fa52399ba0eeda5b303fe` |
| resolved runtime integrity receipt | `ae41130ee035d3ddcbaf2d0977f721429a52ffda8133fe1b877f51de5926278d` |
| guard report | `b5d3c53c932fe5811fadd190695b1dc3313248840b23b358b02b67d2969218b2` |
| V19C `run_stats.csv` | `469016975e85dc954275241ce3a5f363d47abe78f661a59ba564911c69cd8adf` |
| copy audit source manifest | `315b7fc77cec3c4058d5c8381dcc19e3431399175f99cc52e25eb4d0f2d91c90` |
| optimization audit source manifest | `718e95da10d4170aac29dff93ec514f47966be0191faf923d3ff08041a332c4c` |

此外，已读取 V19C 固定 Notebook 完整容器（213,952 bytes，12 cells，其中 10 code cells 全部 AST parse 通过），SHA-256 为 `92bf632410fedc9eb7e0984a20525590b5583d5abb002d8239ff65d9f51fbf57`。已读取完整运行日志（111,209 bytes，622 events），SHA-256 为 `a3d3de4a9644f943f37a4804740cd4c44ed0d658d76a47df62a1793fb868634d`。由于第三方许可证血缘未完全闭合，本报告只保存身份、哈希和原创分析，不向公开 GitHub 复制完整源码或 checkpoint。

## 2. Git 和 Kaggle 基线身份

Git 任务前预检已执行 fetch、status、branch、HEAD、origin/main 和 `ls-remote`。当时工作树干净，`main`、`origin/main` 与远端 `refs/heads/main` 均为 `f4af9bc5bbdf79e478e1ccba9897c632fd68c659`，ahead/behind=`0/0`。固定 commit 在远端存在，当时无主线分歧，也无需建立独立 worktree。

Kaggle 基线为 `sailorren/biohub-v19c-public0939-sis14-only`，Version 1，ScriptVersionId `346969653`，baseline submission `55978992`。已观测的 `0.939` 只绑定为该 submission 的历史 Public Score；不表示 private/final score，也不声称全局 leaderboard 最优。

合同在任何 arm 运行之前提交于 Git，freeze commit 为 `0feb0e4b7f09b390b5ff1397ac672993fd9482a4`，独立验收工具记录的 contract SHA-256 为 `85f78b97015fa2d16cf4ab8fa6c8526fe8cc302da81d215a886940316daa3c68`。元数据 inventory 在合同 prepare 前已读取，但任何 R70/R80/R90 候选、Kaggle 写入或 submission 都没有在冻结前发生。

## 3. frozen split 如何建立

枚举器仅通过 Kaggle API 读取 competition file metadata，page size=200，共 125 页。24,886 个路径在去重后唯一，canonical file-metadata SHA-256 为 `260313bb5f12accebd9a70c0b0be43c659090de81f1839c7d06971b11bde3dc6`。未持久化 pagination token，未保存 raw file list，未下载 image/GEFF/Zarr payload。

筛选粒度是每个 train stem。一个 stem 需同时出现 train image `.zarr`、GT `.geff`以及 scorer 所需的 nodes/edges 基础 metadata paths，才记为 `ELIGIBLE_METADATA_SCHEMA_PRESENT`。全部 199 个 train stems 都符合该结构门。这是可核验的元数据结论，不代表已实际读取每个 GEFF 内容；`estimated_number_of_nodes` 内容也仍是 `UNKNOWN_NOT_DOWNLOADED`。

官方数据说明指定 folder name 模式为 `{embryo_id}_{field_of_view}`，第一段是 embryo，多个 samples 可共享 embryo，train/test embryo-disjoint。按该规则分组后仅有两组。由于硬门明确规定有效 group 少于 3 即停止，没有构造 K=2，也没有把 199 个 field of view 错当成 199 个独立 embryos。

输出哈希：

- inventory CSV: `0696842719c579bab6afb4dacd5982ac185dd2a5642cf48facfe25128da7360a`
- frozen split JSON: `9185ef6812363d82bfc20a694f9de27cee00a5901071e0684c053bc7de004de8`
- frozen split CSV: `9b78064ee23c5d557df6549adda241180dd23b71a30434dfc99777c4558d132e`

## 4. 是否存在 embryo leakage

没有创建 fold，所以不存在可以被声称为“通过”的 fold-level leakage 检查。正确状态是 `NOT_EVALUABLE_NO_FOLDS_CREATED`。这不等于发现了 leakage；也不等于无 leakage 已验证。

可确认的边界是：同一 embryo group 没有被分到多个 folds，因为根本没有 fold assignment；test IDs、test stems 和公开测试视频身份没有作为 split 设计输入。`frozen_split.csv` 中每个样本的 fold 都是 `NOT_ASSIGNED`，而不是一个伪造的空 fold。

## 5. canonical config 如何校验

合同冻结了 V19C 的 active parameters、三个 checkpoint SHA、support-code manifest SHA、三个 Kaggle input Dataset 的 ID/version/file-metadata SHA、competition file-metadata SHA 和 scorer identity。唯一可变字段是 `safe_div_parent_radius_um`，且仅可为 R70=7.0、R80=8.0、R90=9.0。

`experiments/V20A/verify_resolved_config.py` 实现了 fail-closed checker。它要求 canonical receipt 必须在所有环境变量、默认值、dynamic patch 和 runtime override 生效后、推理前捕获；必须与 active-config dump 和 safe-division 实际函数调用参数分别严格匹配。它还检查源、checkpoint、support、input、scorer、hardware、runtime 和 output hashes，并拒绝敏感键、本机私有路径、credential-bearing URL 或用 Markdown/普通 log print 代替 canonical runtime state。

本次硬门发生在 arm runtime 之前，所以 canonical runtime receipt 实际状态是 `NOT_CREATED_NO_ARM_RUNTIME`。为避免伪造，本任务只对 checker 执行正例和三类反例 self-test（缺字段、函数参数漂移、敏感路径）；self-test PASS 证明 checker 行为，不证明 R70/R80/R90 的 config identity。

一个重要 `UNKNOWN`：V19C 源码中没有显式设置全局 random seed。因此合同如实冻结为 `UNKNOWN_NOT_EXPLICIT_IN_SOURCE`，不根据 secondary Dataset slug 中的 `seed314159` 推断整条推理链的随机性已被固定。即使未来 embryo gate 解决，也应在新合同中先闭合这个身份缺口。

## 6. R70 是否复现

**没有。状态是 `NOT_RUN_HARD_GATE`，不是 PASS，也不是 `BLOCKED_BASELINE_REPRODUCTION`。**

原因是 embryo-count gate 在控制组运行前已终止任务，所以没有进入基线复现阶段。旧 V19C 审计中可回读的四样本值是 adjusted edge Jaccard `0.9214`、division Jaccard `0.2000`、proxy score `0.9414`，division TP/FP/FN=`1/0/4`，edge TP/FP/FN=`2192/104/101`，fragmented/lost/wrong=`56/45/0`。

这些值只是“历史已观测并已回读”，不是本次复现值。它们来自两个 prefix 中各两个 division-enriched samples，使用 estimated node counts，不是冻结的 embryo-disjoint multi-fold 协议；因此不能替代本次 R70 复现。

## 7. 三个 arm 的唯一差异

设计层面唯一差异已预注册：

| arm | `BIOHUB_SAFE_DIV_MAX_UM` | 角色 | 实际状态 |
|---|---:|---|---|
| R70 | 7.0 | control | `NOT_RUN_HARD_GATE` |
| R80 | 8.0 | candidate | `NOT_RUN_HARD_GATE` |
| R90 | 9.0 | candidate | `NOT_RUN_HARD_GATE` |

detector threshold、secondary detection/edge weight、retention、edge threshold、bidirectional fusion、gap、ILP、sister radius、divergence、DeepCenter、division caps、minimum track length、short-track rescue/filter、checkpoint、model、data、input 和其他后处理参数都冻结不变。但由于 arm 没有运行，“实际 runtime 只差 parent radius”并没有被 canonical receipts 验证；不把设计意图写成实际运行事实。

静态全源调用链检查显示，parent radius 仅在 safe-division 函数中对 unclaimed candidate 的 parent distance 施加门限，不参与 detection、association 和 pre-division graph。该结论属于 `SOURCE_CODE_VERIFIED`，详细位置见 `experiments/V20A/safe_div_parent_radius_call_chain.md`。

## 8. 是否使用 cache，cache 为何安全

未使用 cache。cache used=`false`，cache SHA=`null`，cache/full-run equivalence=`NOT_RUN`。虽然静态依赖分析支持“上游 detection/association/pre-division graph 理应不随 parent radius 变化”，但合同还要求同一 cache SHA 和至少一样本的 cache/full end-to-end 等价性验证。硬门阻断了这些操作，所以本报告不得声称 cache 安全已验证。

## 9. 每 fold、样本、prefix 的指标

无新指标。由于没有 fold 且三个 arms 均未运行，下列字段在本任务中统一为 `NOT_RUN`：official total score、adjusted edge score/Jaccard、division Jaccard、division TP/FP/FN、node-count adjustment、predicted/true-or-estimated nodes、fragmented/lost/wrong edges、synthetic gap-1/gap-2 nodes、division candidates、DeepCenter accepted/rejected、frame/global cap saturation、topology/schema validity、runtime、peak memory、upstream cache SHA 和 output SHA。

这里没有生成空的 `per_sample_metrics_R*.csv`、`per_fold_metrics_R*.csv` 或 `per_prefix_metrics_R*.csv`，因为空表容易被误读为“运行成功但无样本”。机器可读状态集中在 `experiments/V20A/no_run_manifest.json`。

## 10. paired delta

R70 控制组未运行，R80/R90 也未运行，因此 sample/fold/prefix/aggregate paired deltas 全部 `NOT_RUN`。没有生成 `paired_deltas_by_sample.csv`、`paired_deltas_by_fold.csv`、`paired_deltas_by_prefix.csv` 或 `aggregate_comparison.csv`。不能对未观测值做零填充，也不能用 Kaggle Public Score `0.939` 减未存在的离线分数。

## 11. promotion gate 逐项结果

| gate | 状态 | 说明 |
|---|---|---|
| 至少 3 个有效 embryo groups | **FAIL** | observed=2, required=3 |
| 所有 frozen folds 成功 | `NOT_EVALUATED_HARD_GATE` | 无 folds |
| canonical config 校验 | `NOT_EVALUATED_NO_ARM_RUNTIME` | checker self-test 不是 arm receipt |
| source/checkpoint/support/input identity | `NOT_EVALUATED_NO_ARM_RUNTIME` | 身份已冻结，未在 arm runtime 复核 |
| 唯一改变 parent radius | `NOT_EVALUATED_NO_ARM_RUNTIME` | 只完成静态冻结 |
| fold mean 高于 R70 | `NOT_EVALUATED_NO_FOLDS` | 无指标 |
| fold median 不低于 R70 | `NOT_EVALUATED_NO_FOLDS` | 无指标 |
| worst-prefix 非劣，容差 0.0001 | `NOT_EVALUATED_NO_FOLDS` | 无指标 |
| micro division Jaccard 提升 | `NOT_EVALUATED_NO_RUN` | 无指标 |
| 新增 FP 被 TP/总分补偿 | `NOT_EVALUATED_NO_RUN` | 无混淆矩阵 |
| topology 全部有效 | `NOT_EVALUATED_NO_RUN` | 无输出图 |
| cap saturation 不实质恶化 | `NOT_EVALUATED_NO_RUN` | 无 runtime diagnostics |
| 收益不依赖单样本/prefix | `NOT_EVALUATED_NO_RUN` | 无 paired deltas |
| node-count penalty 无未解释恶化 | `NOT_EVALUATED_NO_RUN` | 无 scorer rows |
| runtime 比赛安全 | `NOT_EVALUATED_NO_RUN` | 无 runtime |
| 可由冻结合同/哈希复现 | `NOT_EVALUATED_NO_RUN` | 实验未执行 |

scorer CLI 汇总以 `.4f` 输出，因此候选运行前已冻结最大数值比较容差为 `0.0001`。本次没有用到容差，也没有在看到结果后放宽。

## 12. 最终选择及原因

没有选择 radius，selected arm/radius 均为 `null`。决策值为允许列表中的 `BLOCKED_INSUFFICIENT_EMBRYO_GROUPS`，原因是前置 split gate 失败，而不是 R80/R90 已证明劣于 R70。

“NO_PROMOTION_KEEP_V19C_R70”也不适用：该决策需要 R70 复现和候选指标，本次在运行前就停止。详细机器可读决策见 `experiments/V20A/promotion_decision.json`。

## 13–18. Kaggle Version、submission、ID、监控、分数与 retry

| 问题 | 回答 |
|---|---|
| 是否创建 validation Notebook Version | 否，count=0 |
| 是否创建 production Notebook Version | 否，count=0 |
| SaveKernel / Notebook run | 0 / 0 |
| Notebook Version / ScriptVersionId | `null` / `null`（没有 V20A 版本） |
| 是否创建 formal competition submission | 否，count=0 |
| submission ID | `null` |
| 30 分钟状态历史 | 未创建；没有 submission 可轮询 |
| 30 分钟最终状态 | `NOT_APPLICABLE_NO_SUBMISSION` |
| Public Score | `null`；不是 PENDING submission score，而是无 submission |
| retry | 0 |
| 后台轮询进程 | 未创建 |

`experiments/V20A/kaggle_30m_health_summary.json` 保存上述不适用状态。没有创建 `kaggle_status_history_30m.jsonl`，因为合同明确规定监控起点是获得正式 submission ID；本任务从未获得该 ID。

## 19. 尚未验证的事项

1. `UNKNOWN`：199 个 GEFF payload 的内容级可读性和 `estimated_number_of_nodes`；本轮未下载 87.6 GB 比赛 payload。但这个未知不能解决第三个 embryo 缺失，因为全部 train paths 只有两种 prefix。
2. `NOT_RUN`：R70 四样本与冻结协议复现。
3. `NOT_RUN`：R80/R90 离线推理、scoring 和 paired comparison。
4. `NOT_RUN`：canonical arm receipt、actual function-call receipt、hardware/runtime/output identity。
5. `UNKNOWN_NOT_EXPLICIT_IN_SOURCE`：全局 random seed。
6. `NOT_RUN`：cache 内容 SHA 和 cache/full-run 等价性。
7. `NOT_RUN`：所有新指标、promotion gates 与 unique-winner tie-break。
8. `NOT_RUN`：Kaggle principal/quota/duplicate/output schema 提交前门；无唯一离线胜者，不得进入该阶段。
9. `NOT_RUN`：Kaggle worker health、submission acceptance 和 Public Score。
10. `UNKNOWN`：在不更改用户冻结的最少 3-group 规则时，是否存在许可清晰、与比赛目标匹配、带 GT 的第三个独立 embryo 数据源。

## 20. 后续必须由用户显式触发读取分数

本任务没有 submission，因此没有可读取的 V20A score。不会留下 sleep、cron、后台 shell、浏览器轮询或监控进程。如果未来用户在另一个明确授权的任务中解决数据独立性、生成唯一离线胜者并创建 submission，后续 Public Score 回收仍必须由用户显式发起，不能从本任务自动延伸。

## scorer、checkpoint 与 input 身份

官方 scorer 冻结在 `royerlab/kaggle-cell-tracking-competition@075fc5f5a52d11077f9dc2b074644618f26939e2`。`metrics.py`、`division_metrics.py` 和 `evaluate.py` SHA-256 分别为 `cfdd596e…`、`0635c386…`、`03ad4049…`。代码定义 total score 为 adjusted edge Jaccard + `0.1 * division Jaccard`，CLI summary 以 4 位小数输出。

三个 checkpoint SHA-256：

- primary: `12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771`
- secondary: `9bac2fa0dadc4a6fc1899e0caf187f4b553e0a7cd90ba1261a68b35ffe9e305f`
- DeepCenter: `8040999a92f6b7bbd98fa8cf458141e045c0f9ad7c936bdb3b18e1f7edafe2a0`

support code 13 个 Python files 的 manifest SHA-256 为 `978b626d1fd1e7397435a437dfe68691defe1572fc3c20e61012d7c9b52ed029`。三个 Kaggle input Datasets 的当前身份是 deepcenter Dataset ID 11061989 V5、secondary ID 11184174 V2、primary/support ID 10999845 V10；该 API 不暴露 DatasetVersionId，因此字段如实保存为 `UNKNOWN_NOT_EXPOSED_BY_LIST_API`，同时用各 Dataset 文件元数据 canonical SHA 进行补强。

## 数据品质和鲁棒性验证

- **Grain**：inventory 每行唯一 train stem，split CSV 与之 1:1，没有将文件层粒度误当样本。
- **Uniqueness**：24,886 个路径在分页去重后唯一；脚本遇到重复路径会立即失败。
- **Completeness**：199 train stems 全部进入 inventory，71+128=199，没有按表现删除不利样本或 prefix。
- **Reconciliation**：competition receipt、inventory CSV、split JSON/CSV 与 promotion decision 对 199/2/71/128 四个关键数相互校验，并用内容哈希锁定。
- **Coverage limit**：证据是 Kaggle 权威文件列表的 metadata coverage，不是 87.6 GB payload 内容审计。该限制已明示，且不会将 group 上界从 2 提高到 3。
- **No outcome selection**：split 门在任何 arm result 之前执行，没有观察候选结果，没有删除不利 fold。

## 可优化性判断

从代码机理看，parent radius 是边界清晰的单变量，且历史四样本记录有 division FN=4、FP=0，所以“更宽 parent gate 能否找回真 division”是一个可检验假设。但这只是 `INFERENCE` 和实验优先级理由，不是性能提升证据。

在现有数据上，本任务不能合法回答 R80/R90 是否优于 R70。可行的后续方向只有：（1）找到许可和血缘清晰、与目标分布匹配、带 GT 的第三个独立 embryo；或（2）由用户在一个新任务中明确修订验收协议并承担更弱独立性带来的推断限制。不能在已冻结的本合同内把最低 group 数从 3 改成 2 来迁就数据。

## 平台写入账本

`experiments/V20A/platform_write_ledger.json` 中的 Dataset create/update、Model create/update、Notebook create、SaveKernel、Notebook run、competition_submit、retry、duplicate submit、cancel、delete、status poll 和 unauthorized write 均为 0，events 为空数组。只读操作是 125 页 competition metadata 和 3 个 Dataset identities，payload downloads=0。

预算虽然冻结了 validation versions 最多 3、production version 最多 1、SaveKernel 总数最多 4、formal submission 最多 1 且 retry=0，但这些是上限，不是必须消耗的配额。前置门失败后的正确用量是全部 0。

## 报告形式与图表取舍

本任务同时交付 Markdown 和基于 canonical `artifact.json` 的可移植 HTML。HTML 以指标卡、embryo-group 精确表、arm 状态表和 promotion-gate 表呈现。为满足统一 report artifact 的可视化合同，HTML 另包含一张仅展示 `44b6=71`、`6bba=128` 的简单条形图，并与精确表交叉核对。没有制作分数趋势图，因为没有 arm results；也不用该两类条形图支持任何性能推断。

Portable artifact delivery 使用同一份经验证的 snapshot 同时生成交互阅读器与语义回退内容，不另行维护一套容易漂移的 HTML 结论。

## 验证与 GitHub 交付边界

自定义验证器重算 inventory/group counts、split hashes、scorer/input identities、promotion decision、平台零写入、禁止运行产物不存在、报告完整性、checker self-test、敏感内容扫描与 base-commit lineage。推送后还会以远端 `ls-remote` HEAD 为准，逐文件比较 local bytes、local HEAD blob 和 `origin/main` fixed-commit blob。

远端验证必须发生在本报告被 commit/push 之后，因此报告正文不伪造一个自指的“最终 commit”。最终 Git commit、local/remote HEAD、ahead/behind 和逐 blob 回读结果以推送后的独立验证输出与任务最终回复为准。该交付验证即使 PASS，也只证明硬门证据和 GitHub 交付，不证明 arm 运行、Kaggle runtime、submission、score 或提分。

## 最终结论的证据等级

- `SOURCE_CODE_VERIFIED`：V19C 固定源的 call chain、active parameters 与旧 runtime integrity/validator 文件。
- `HOST_CONFIRMED_METADATA_ONLY`：Kaggle competition/Dataset 文件元数据、199 train stems、两个 prefixes 和 Dataset 版本身份。
- `MEASURED`：历史 V19C 四样本指标和日志统计；非本次 arm 结果。
- `INFERENCE`：parent radius 是边界清晰的待验证优化假设；不推断分数方向或幅度。
- `UNKNOWN`：未下载 payload 的内容级细节、全局 random seed 和未来第三个独立 embryo 来源。
- `NOT_RUN`：R70/R80/R90、fold metrics、paired deltas、promotion、Kaggle Version/submission/monitoring。

本报告的固定决策为：**no promotion, no submission, no score claim**。
