# Codex 执行任务：G1 分裂阈值双候选平台验证

- task_id：`BIOHUB_DIVGATE_PAIR_20260920_V01`
- 日期：2026-09-20；所有显示时间同时记录 UTC 与 Asia/Shanghai。
- 仓库：`SailorRen/Biohub-CELL`；比赛：`biohub-cell-tracking-during-development`。
- 新执行分支：`codex/divgate-pair-20260920`。
- 正式任务路径：`tasks/CODEX_20260920_BIOHUB_DIVGATE_PAIR_V01.md`。
- 实验目录：`experiments/BIOHUB_DIVGATE_PAIR_20260920_V01/`。
- 报告路径：`reports/20260920_BIOHUB_DIVGATE_PAIR_V01.md`。
- 本文件是执行指令，不是已运行、已上传、已同步 GitHub 或已取得分数的证明。

## 1. 用户授权与本批目标

用户已明确要求：在现有 V1 等待 Kaggle 结果期间，根据 9 月 20 日情报，让 Codex 上传 2—3 个方案进行平台测算或跑分。本任务据此选择 **两个可归因的正式候选**，不为了凑第三个引入未闭合的新模型。

实际开发、保存并运行两个独立私有 Kaggle Notebook；普通运行完成且工程检查通过后，分别发起正式 competition submission。不要只生成方案、上传源码或完成本地诊断就结束。

两个候选不等待 V1 的结果，也不互相等待 Public 分数。保留 G1 作为本批比较母版；V1 出分仅附记，不临时替换母版或追加组合。

### 独立增量预算

| 操作 | 本批上限 | 说明 |
|---|---:|---|
| 新私有 Notebook | 2 | A18、B22 各一个；不是创建两个重复 Version |
| Save & Run 请求 | 3 | 两个生产运行 + 一个共享工程修复备用；失败、超时请求也登记 |
| 正式 submission 请求 | 2 | 每候选最多一次；不得盲目重试或把失败预算自动补回 |
| 新训练 / fit / 微调 | 0 | 复用 G1 已有冻结模型 |
| Dataset 创建或更新 | 0 | 只读挂载已有、已验证的输入和 Notebook 输出 |
| 修改最终选择 | 0 | 本批仅取得比较证据 |
| 修改、取消、重提 V1/F1 | 0 | 不占用其原有预算，不覆盖其工件 |
| 自动合并 main / 其他仓库写入 | 0 | 仅推送本任务分支 |

每次平台写入前核查实际账号、比赛、剩余提交额度、计算额度及并发槽位。不硬编码每日上限、不绕过平台限制、不取消已有任务腾位置。额度不足时按 **A18 → B22** 顺序使用实际可用额度；剩余标记 `BLOCKED_QUOTA`，禁止增加预算或跨日自动续跑。

## 2. 先读取固定证据，建立独立工作区

先读取 `AGENTS.md` 及路径范围内的有效执行规则。不得覆盖、stash、reset、清理用户未提交工作，不切换或修改正在使用的 F1 工作区。优先建立单独 git worktree。

### 固定研究版本

`6ec61f54cd5fb5b93fe7cd1dbc37b01a8e41bc57`

必读：

- `research/PUBLIC_INTEL_20260918/update_20260920/交给Chat.md`
- `research/PUBLIC_INTEL_20260918/update_20260920/最新公开情报.md`
- `research/PUBLIC_INTEL_20260918/update_20260920/公开权重训练覆盖核查.json`

### G1 母版

已归档绑定：submission `56270217`，Notebook V1 / ScriptVersionId `350197436`，Public `0.948`。这是既有观测，不是本任务新查分；执行时用本账号回读绑定及状态。

代码固定提交：`e9c7c63b896812660a78ec55fc3284c10f85e776`

必读：

- `experiments/BIOHUB_SPRINT01_20260916/own/candidate.ipynb`：完整读取全部代码单元。
- `experiments/BIOHUB_SPRINT01_20260916/own/kernel-metadata.json`
- `experiments/BIOHUB_SPRINT01_20260916/build_production.py`
- `experiments/BIOHUB_SPRINT01_20260916/production_module.py`
- 该目录下绑定实际权重、版本及缓存的既有回执。

G1 Notebook 预期 SHA-256（此前 F1 构建器所冻结）：
`de010e6ba142be0e01000093e061ef7d3388ddaa411185b40d26c63a3febe731`

已冻结 division gate 权重 SHA-256：
`0a1f9b93bb529e70f4f7c2ba0907eea8b4cecd2befccc8ba1fb75e569edf77a0`

若不匹配，定位真实对应关系，不得自行用“最新文件”替换。新分支以可核验的 G1 固定版本为基础；研究文件可从固定研究提交按需读取或复制，不整体合并其他实验分支。

### V1/F1 状态隔离

已回读 F1 分支快照：`8f18a8dd83146d6399b296ff54c4176c300724b5`。

只读参考：

- `experiments/BIOHUB_F1_FLOW_KAGGLE_20260918/contract.json`
- `experiments/BIOHUB_F1_FLOW_KAGGLE_20260918/formal_score.json`
- `experiments/BIOHUB_F1_FLOW_KAGGLE_20260918/build.py`

注意：该 GitHub 快照中的正式提交回执仍是 `NOT_RUN`，不能拿它否定用户后来报告的 V1 等待状态，也不能把旧诊断 V1/SV351058693 误当成新的正式提交。执行起始做一次平台只读核对，记录当前 V1 到底是 Notebook 运行等待还是 submission 评分等待，以及真实 ID。查不到写 `UNKNOWN`；只要已能隔离现有作业且新操作身份、额度明确，不因此阻断两个新候选。

### 官方评分依据

官方仓库：`royerlab/kaggle-cell-tracking-competition`
固定参考提交：`075fc5f5a52d11077f9dc2b074644618f26939e2`
必读 `metrics.md`、最终 CSV 往返说明和实际评分入口；执行时确认适用版本并冻结版本/依赖哈希。两候选使用同一版本。

## 3. 两个候选：只改最终生产阶段一个参数

| 候选 | 显式改变 | 不变部分 | 要检验的假设（不是预期实得分） |
|---|---|---|---|
| A18 | 最终 `DEEPCENTER_SAFE_DIV_THRESHOLD = 0.18` | 完整 G1 及其原始选参结果 | 更宽松的中心支持门槛能否补回部分被拒绝的真分裂，且收益超过新增错误 |
| B22 | 最终 `DEEPCENTER_SAFE_DIV_THRESHOLD = 0.22` | 完整 G1 及其原始选参结果 | 更严格的中心支持门槛能否减少误分裂，且收益超过漏检 |

G1 初始对应值为 `0.20`。这是 DeepCenter 对 safe-division 的中心支持门槛，**不是**学习型 division gate 的分类阈值、检测阈值、分裂半径或 ILP 权重。

0.18/0.22 是围绕 0.20 的预先指定小范围对照，并受到情报中公开阈值扫描计划的启发；没有证据证明它们会提分。公共实验计划不能写成已验证方法。

保留所有原模型、权重、检测/TTA、关联、分裂几何约束、数量上限、G1 学习筛选、gap 处理、短轨规则及模型加载路径。不得叠加 F1 邻域运动补偿、HOCT、新 MLP/XGBoost、重训或额外参数扫描。

### 关键实现：先让 G1 选参，再覆盖最终一个坐标

不要直接修改最前面的环境变量后重跑选参。那样可能连带改变其他选参结果，无法清楚归因。

推荐保持 G1 原始所有推理和选择单元完整执行；在原始最终输出及 G1 回执生成后，追加一个短小生产阶段：

1. 记录 G1 原始 `selected_label`、`selected_config`、完整 resolved config；保留原始最终 CSV 的私有副本及哈希。
2. 从原始母版基准配置与 `selected_config` 恢复原本最终有效配置。母版最终 safe-division 门槛必须核验为 0.20，否则报配置不符，不自行偏移试验中心。
3. 深拷贝该配置，仅把 `DEEPCENTER_SAFE_DIV_THRESHOLD` 改为 A18 或 B22 的冻结值。
4. 从同一份**未经后处理的预测图**重新执行完整、原版后处理和原版 CSV 写出。不要在已经改过的最终图上再补一遍分裂；不要直接改 CSV 增加边。
5. 最终 `submission.csv` 必须是本候选输出，不能被后续 G1 单元覆盖。追加回执必须在所有写出之后生成，并记录最终文件哈希和真实生效阈值。

这里的“选参不变”指两臂均按原版 G1、0.20 的逻辑先选参；候选诊断结果不参与这一步，不重新选择其他配置。继承的 G1 proxy 仅为维持原生产行为，不得给它重新贴上“独立官方验证”的标签。

新 Notebook 拟用独立 slug（创建前查重，不覆盖已有同名对象）：

- `sailorren/biohub-g1-divgate018-20260920`
- `sailorren/biohub-g1-divgate022-20260920`

## 4. 最小工程验收与真实测算

### 本地只做短测试，不运行大模型

冻结源文件/配置、解析全部代码单元，检查单点差异；使用小型人工图测试阈值覆盖、关回 0.20 的等价性、复制隔离、最终写出顺序及评分汇总的字段结构。人工图只作工程测试，不混入比赛输出或效果证据。

尤其增加回归测试：`edge_tp/edge_fp/edge_fn` 从逐视野记录提取，不假定整体摘要含这些字段；字段缺失不得静默填 0。覆盖“部分视野已成功、最后汇总失败”时仍能保留逐视野产物。

### 不为前置诊断另开一轮排队

两个 Notebook 各自完成“原 G1 推理 → 单参数最终输出 → 同源小样本测算与回执”，按平台实际可用并发尽早分别 Save & Run。不要等待 A18 出 Public 后才启动 B22，也不要先排一个独立诊断 Notebook，等它结束后才排生产。

每个 Notebook 内原始模型预测只生成一次；后处理对照复用同一输入。已有原始缓存只在样本、生成代码、输入、权重和阶段哈希均吻合时复用；最终图缓存不能冒充原始图。不新建 Dataset，不下载原始比赛影像到本地。

在原 G1 已有验证预测可用时，复用固定 8 视野作母版/候选配对测算：

`44b6_12dfb391`、`44b6_267148e4`、`44b6_2a2eff9f`、`44b6_341df25f`、
`6bba_062c8d37`、`6bba_07e24132`、`6bba_085bf656`、`6bba_09961292`。

禁止为追求样本数量额外重跑全训练集。若这 8 个视野的缓存不可用、同源性无法核实或辅助评价失败，明确记录缺口，优先保存两个合法生产输出。仅辅助评价缺口不自动否决正式探索性提交；图/身份/配置/最终文件完整性失败才阻断。

### 评价只读取最终序列化对象

对训练视野，走与生产相同的完整后处理和 CSV 导出，再按官方 CSV 读取/往返路径构造评分图。比较的是这个图，不是导出之前的 GEFF 或另一个内存对象。

不得把 Notebook 里命名为 `aggregate_official` 的自写函数视为官方实现。官方分裂判定要求局部有向拓扑、不同子分支等条件；只看弱连通分量不等价。使用冻结的实际官方评分入口，不另写“近似官方评分器”。

记录逐视野的 edge TP/FP/FN、adjusted edge Jaccard、division TP/FP/FN、节点/边/分裂数和最终图哈希；按官方口径汇总，并给出两个胚胎分组结果。不把 8 个视野当成 8 个独立胚胎，不做虚假的显著性声明。

每视野结束立即追加 JSONL/CSV 并保存检查点。统计只保存小型结果；图、影像、权重、完整 submission 留在私有 Kaggle 工件，不入 GitHub。

### 验证独立性与决策

公开 secondary manifest 的 train199/test40、交集40，只证明该归档标识重叠；不能扩张为所有模型都见过全部数据，也不能当成实际训练过程审计。

记录本批所用各权重与这 8 个视野的训练覆盖。可确认重叠标记 `TRAIN_SEEN_DIAGNOSTIC`；覆盖未知标记 `COVERAGE_UNKNOWN`；只有充分证据才标为模型未见。G1 学习 gate 的留胚胎记录不能自动证明其上游模型未见。

本轮不根据这批小样本“本地分必须上涨”选一个才交；两个预冻结候选分别获取平台答案。小样本正收益不证明泛化，负收益也不自动证明 Public 必降。数值异常需要解释并披露，工程/图结构异常必须停止。

## 5. 普通运行后必须执行正式提交

每臂普通运行完成后独立检查：

- 账号、比赛、Notebook Version、ScriptVersionId、源码及依赖都精确绑定；没有加载失败后静默回退。
- 完整输入覆盖、实际推理和最终导出正常；阈值生效回执来自最终写出时刻。
- 同输入上可恢复 0.20 并复现 G1 的规范化最终图；有效配置除目标参数外一致。测试中原始图未被原地改写。
- 最终 CSV 满足官方 schema、样本覆盖、ID/端点一致性、时间方向、单父节点及最多两个子节点等约束；检查空边图不能令验收器自身报错。
- final CSV 往返后的节点、边、坐标、时间和拓扑与实际准备提交的内容一致。
- 记录候选相对 G1 的新增/删除边、分裂变化及 canonical hash。必须比较实际内容，不能只凭行顺序导致的文件哈希不同。

只有少量诊断视野无变化，不足以宣称整个候选无效。若**完整普通生产输出**与 G1 完全相同且无其他真实改动证据，标记 `MEASURED_NO_EFFECT`，不浪费正式提交；不得为了凑数改成更极端的阈值。两候选最终内容相同则去重，记录原因。

通过这些检查且有实际输出差异的候选，使用其真实精确 Notebook Version 发起正式 submission，不能只保存 Notebook。请求前保存源码/配置 commit 和唯一请求记录；网络超时、响应不明确时先只读核对是否已创建 submission，不盲目重发。

优先推进已就绪的候选；一个候选发生独立故障，不阻断另一个。共享工程备用只允许修复明确接口、字段、路径、写出或日志错误；不能改算法、参数、模型、样本或放宽验收后称为工程修复。

## 6. 查分、比较与停止

在本次实际执行会话中读取已创建作业/提交状态并保存。未返回正式分数时状态写 `SCORE_PENDING`；Notebook 尚未结束写 `KERNEL_PENDING` 或 `KERNEL_RUNNING`，不能混称“已在正式评分”。只等待不保证结果在固定小时数内产生。

禁止因结果等待而重复提交。不创建无人值守监控、后台定时器或跨日续跑；会话结束时交付当前真实状态和可直接续读的精确 ID。

报告比较表至少包含 G1、现有 V1（只读附记）、A18、B22，并列出：版本、ScriptVersionId、submission ID、状态、Public、相对 G1 的差值、观测时间、最终图变化和诊断覆盖标签。

正式结果解释：

- 高于可比口径 G1 的 Public：`PUBLIC_IMPROVED`，说明提高多少；不声称 Private 或统计泛化已证实。
- 与 G1 同分：`PUBLIC_TIED`，只表示当前显示精度下未见提升，不等于隐藏预测相同。
- 低于 G1：`PUBLIC_REGRESSED`，不替换 G1。
- 无真实分数：`SCORE_PENDING` / `BLOCKED_*`，不得补填 0 或猜测。

已有 0.948 是历史观测；若官方评分口径更新，先回读基线可比分数。无法建立可比性时保留原始分数并标记，不直接相减。任何候选达到 0.950 也不修改最终选择；本批不扩展第三臂、不组合 F1、不自动开展第二轮。

## 7. GitHub 同步与可检索交付

第一步将本任务原文及小型 `contract.json` 保存到新分支并推送、远端回读，然后开始平台写入。任务/代码的 immutable commit 必须早于对应 Save & Run；不得事后伪造“预先冻结”。本轮用户授权覆盖本任务分支内必需的代码、任务、报告和证据同步，不覆盖 main 或其他分支。

沿用仓库可用的同步/验收工具，不新建庞大治理框架。最少交付：

1. 本任务、冻结合同、构建源码、两个 Notebook、各自精确 diff 和短测试结果。
2. `candidate_manifest.json`：母版、所有版本/输入/权重/源码哈希、两个最终配置、当前 V1 只读绑定。
3. `platform_ledger.json`：每次真实 Save & Run/submission 请求、回执、用量、精确 ID、状态和观测时间。
4. `diagnostic_results.jsonl` 与 `summary.json`：已取得的逐视野结果、官方汇总、最终图变化、CSV 往返结果及缺口。尚未执行不得创建伪结果或把空文件标为成功。
5. 指定报告和 `github_readback.json`：固定 commit、新增/修改文件逐字节 SHA-256 回读、remote HEAD、工作树状态、执行前后受保护分支未被本任务改写的证据。

不得入库原始图像、完整预测图、模型权重、submission.csv、凭据或签名 URL。

分别报告 `delivery_status`、`execution_status`、`score_status`。远端文件验证完成不代表两个实验完成，更不代表提分。只有相关证据可检索且本项验收通过，才对该项使用 `COMPLETED_VERIFIED`。

最终回复必须明确：实际启动几个 Notebook、正式提交几次、两个候选各自状态/ID、是否有真实 Public、预算实耗、所有阻断，以及固定 GitHub 报告链接。源代码上传成功不能写成“已跑分完成”。

## 8. 本任务设计来源与读取边界

本任务设计已读取固定情报全文、G1 构建及生产模块、G1 Notebook 的初始化/参数段和最后验证/选择代码段、F1 合同/构建/旧正式回执、官方 `metrics.md`。设计阶段未完整阅读 G1 全部 Notebook 大单元，也未执行模型；因此第 2 节要求执行者完整读取母版后实施，禁止声称设计阶段已完成全源码复现。

来源（均为固定版本）：

- https://github.com/SailorRen/Biohub-CELL/blob/6ec61f54cd5fb5b93fe7cd1dbc37b01a8e41bc57/research/PUBLIC_INTEL_20260918/update_20260920/最新公开情报.md
- https://github.com/SailorRen/Biohub-CELL/blob/e9c7c63b896812660a78ec55fc3284c10f85e776/experiments/BIOHUB_SPRINT01_20260916/build_production.py
- https://github.com/SailorRen/Biohub-CELL/blob/e9c7c63b896812660a78ec55fc3284c10f85e776/experiments/BIOHUB_SPRINT01_20260916/own/candidate.ipynb
- https://github.com/SailorRen/Biohub-CELL/blob/8f18a8dd83146d6399b296ff54c4176c300724b5/experiments/BIOHUB_F1_FLOW_KAGGLE_20260918/build.py
- https://github.com/SailorRen/Biohub-CELL/blob/8f18a8dd83146d6399b296ff54c4176c300724b5/experiments/BIOHUB_F1_FLOW_KAGGLE_20260918/formal_score.json
- https://github.com/royerlab/kaggle-cell-tracking-competition/blob/075fc5f5a52d11077f9dc2b074644618f26939e2/metrics.md
