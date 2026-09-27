# Biohub 公开区更新与本队最新成绩（2026-09-27）

采集时间：2026-09-27 12:04–12:10，中国上海时区。任务 `BIOHUB_PUBLIC_UPDATE_20260927_V01`，分支 `codex/public-update-20260927`。本轮仅研究与报告：Kaggle 写入、训练、推理、运行、正式提交、最终选择变更均为 **0**。

## 结论

**本队已从 XR0 的 0.953 提升至 XRL9 的 0.955，当前第 225 / 3941 名；本轮检索尚未发现有准确版本成绩支持、且超过 0.955 的新公开方案。** 榜首已达 0.978，前 100 名显示门槛升至 0.957，仍有 0.002 的显示分差。不能把高排名队伍的分数归因于其未公开方法，也不能把 Notebook 的宣传文字当作正式分数。

最重要的新源码发现是：**Aman 最新 V6 虽普通运行成功，实际四个可见视频均因未定义变量触发修复回退，最终分裂数均为 0**。它不是可直接替换当前最佳候选的已验证高分实现。

INFERENCE：后续如另行授权，优先围绕本队已有实测支持的连接距离与检测召回做小范围、可归因验证；不因“0.965+”文字标签迁移整份公开代码，不恢复旧自动选择器。本轮没有构建或启动任何下一批候选。

## 本队成绩：正式分数与版本

最新两份由官方 `get_submission` 在本轮刷新，均为 `COMPLETE`、无直接错误。前四份使用仓库已归档的精确回执，没有复跑或重提。分差均以 XR0 0.953 为基准，是显示精度下的单次 Public 观察。

| 候选 | 改动摘要 | Version / SV | submission ID | Public | ΔXR0 | 证据时间 / 类型 |
|---|---|---|---|---:|---:|---|
| XR0 | 原 x138 复现 | V1 / 352643547 | 56546951 | 0.953 | 0.000 | 09-26 14:02 归档；MEASURED |
| XV25 | 无 flow 自身速度权重 0.25 | V1 / 352908214 | 56573059 | 0.953 | 0.000 | 09-26 23:21 归档；MEASURED |
| XG95 | 冻结 G1 分裂过滤 0.95 | V1 / 352908258 | 56573089 | 0.929 | -0.024 | 09-26 23:21 归档；MEASURED |
| XV25G95 | 上述两项组合 | V1 / 352913254 | 56573515 | 0.952 | -0.001 | 09-26 23:21 归档；MEASURED |
| **XD960** | 主检测阈值及守卫 0.960；readmit 仍 0.965 | **V1 / 353050916** | **56585147** | **0.954** | **+0.001** | **本轮官方 API 刷新；MEASURED** |
| **XRL9** | 原 motion relink relaxed 距离 10→9 μm | **V1 / 353050971** | **56587392** | **0.955** | **+0.002** | **本轮官方 API 刷新；MEASURED** |

[XD960 精确版本](https://www.kaggle.com/code/sailorren/biohub-xr0-xd960-last-two-20260926?scriptVersionId=353050916)、[XRL9 精确版本](https://www.kaggle.com/code/sailorren/biohub-xr0-xrl9-last-two-20260926?scriptVersionId=353050971)、[团队正式提交页](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/submissions)。XR0 owner 为 dongdongjiaqi，其余五份 owner 为 sailorren。

官方 API 提交日期：XD960 为 **09-27 01:22:55.373**，XRL9 为 **09-27 03:33:36.883**（上海）；此前报告记录的是请求发起时间 01:22:53 / 03:33:35，两者含义不同。

本队结果依据：[最后两候选报告](20260926_BIOHUB_XR0_LAST_TWO_RESULTS.md)、[三方案报告](20260926_BIOHUB_XR0_TRANSFER_TRIO_RESULTS.md)，归档基点 `99ee6c561d2afbc01a6afe4779849eec51814069`。本轮 API 原始小型证据见 `research/PUBLIC_UPDATE_20260927/submission_56585147.json`、`submission_56587392.json`。

MEASURED：XRL9 本次比 XD960 高 0.001；两项修改分别有效，不证明组合可加和。XV25 未显示收益，G1 两份未超过母版。UNKNOWN：隐藏测试分项、G1 退分机制、私榜收益和跨胚胎稳定性；本轮不做因果归因，不改变 A 或当前最终选择。

## 排行榜与剩余时间

OFFICIAL_FACT：官方 API 前 400 行与实时页面确认本队 **225 名 / 0.955 / 56 entries**，页面总队数 3941。09-26 14:02 的已归档快照为 **453 / 3922、0.953**；本次相较该快照上升 228 位。两个不同时间点的排名变化包含竞争者变化，不能全归因于一次修改。

| 显示排名 | 本次分数 | 09-26 14:02 快照 | 相对本队 0.955 差距 |
|---|---:|---:|---:|
| 1：yu4u | 0.978 | — | 0.023 |
| 2：Sergio Alvarez | 0.975 | — | 0.020 |
| 3：Gabriel | 0.975 | — | 0.020 |
| 50 | 0.962 | 0.960 | 0.007 |
| 75 | 0.959 | 0.958 | 0.004 |
| 100 | 0.957 | 0.956 | 0.002 |
| 150 | 0.956 | 0.955 | 0.001 |
| 200 | 0.955 | 0.954 | 0.000 |

同一显示分数有大量并列，达到 0.957 不保证进入前 100；平台的显示精度与同分排序仍有影响。页面当前在本队行显示铜牌标记，这不是最终奖牌保证。

OFFICIAL_FACT：Public 使用约 **29%** 测试数据，Private 使用余下 **71%**。官方最终提交截止为 **2026-09-29 23:59 UTC，即上海 09-30 07:59**；本次采集时约余 67 小时 49 分钟。来源：[排行榜](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/leaderboard)、[官方时间表](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/overview/timeline)。证据：`leaderboard.json`、`leaderboard_page2.json`、`timeline.json`、`platform_observations.json`。

## 公开代码区：两份更新，一份不变

按 `scoreDescending`、`dateRun`、`dateCreated` 各读取前 100 条，合计 **162 个不同 ref**。与 09-26 同范围快照相比，没有新增 ref；有两份最近运行时间变化：Aman 与 Robust。目录排序仅用于发现来源，不能证明最高 Public 或算法优劣。

| 公开代码 | 当前版本 / SV | 本次页面成绩 | 源码与运行判断 |
|---|---|---|---|
| [Aman optimized-biohub-max-score](https://www.kaggle.com/code/amanatar/optimized-biohub-max-score?scriptVersionId=353147685) | **V6 / 353147685** | **当前 Public UNKNOWN**；Best 为 V4 / 352554580 的 **0.953** | 今日更新；16m41s、T4×2，普通完成但四份 repair fallback |
| [Robust 3D Cell Tracking](https://www.kaggle.com/code/sarveshchhetri/robust-3d-cell-tracking?scriptVersionId=352988018) | **V8 / 352988018** | **0.429**；历史 V7 / 351910842 为 0.432 | 昨日更新；19m43s，非 GPU 模型方案；挂载一个 Private Dataset |
| [Harmonic Fusion V3](https://www.kaggle.com/code/raunakdey07/biohub-harmonic-fusion-v3?scriptVersionId=352639153) | **V5 / 352639153** | **0.953** | 12 个代码单元与昨日采集完全一致，无新算法变化 |

SOURCE_CODE_VERIFIED：三份完整源码均已获取，所有 **34 个非空代码单元**完成逐单元静态解析；Robust 的一条 `!pip` 仅识别为 Notebook shell 指令，未执行。Aman 另有一个空代码单元。这里的 `FULL_NOTEBOOK_SOURCE_STATIC_CHECKED` 不等于动态补丁或模型运行验收。本轮没有执行任何下载代码。

### Aman V6 的有用线索与明确缺陷

与原 x138 的完整 diff 已归档，主要实质改动：检测阈值 0.960；gap 距离 5.0→5.8；flow 邻域 K 12→16、半径 40→48 μm、Z 权重 1→0.40；候选保留率 0.90→0.75；分裂距离、cap 与短轨救回放宽；新增多帧分裂发散判据；检测融合先用均值/标准差调整 secondary，再取 primary 与线性融合的逐元素最大值。

SOURCE_CODE_VERIFIED：所谓“quantile-consensus”实际新增实现使用 **mean/std**，不是分位数校准。新增 `SAFE_DIV_HORIZON_FRAMES`、`SAFE_DIV_HORIZON_DIVERGE_UM` 仅设置了环境变量/展示字段，却没有给实际使用的同名 Python 变量赋值。

MEASURED（公开普通运行日志）：四份可见测试均报 `NameError: name 'SAFE_DIV_HORIZON_FRAMES' is not defined`，随后写出基础过滤后的 ILP 图；最终日志显示四份 `division_parents=0`。这是有明确异常证据的回退，不能与“正常情况下没有合格新增分裂”混同。页面成功状态只说明 Notebook 走完了带异常回退的路径。其 `fallback_frames=0` 是检测融合保留率回退指标，也不能用来否认图修复回退。

UNKNOWN：V6 是否已正式提交、准确 submission ID 及 Public 均未在当前公开页确认。不能称为 `SCORE_PENDING`，也不能把代码内“0.965+”当作成绩。V4 的 0.953 与其普通运行失败记录并存，报告保留两者，不自行解释隐藏评分情况。

INFERENCE：多帧分裂和检测融合可作为技术研究线索，但在修复后的真实输出及正式评分证据出现前，不宜整份移植；它同时改动很多因素，无法把任何潜在收益归因于某一个参数。

### Robust V8 与 Harmonic Fusion V3

SOURCE_CODE_VERIFIED：Robust 完整 10 单元采用强度归一化、Gaussian/local-max 检测、5 μm NMS、速度外推 Hungarian 连接、第二子节点近邻规则、最小连通分量过滤；不是新的高分学习模型。其本地辅助评分只有 edge confusion，不等于完整官方总分；数据输入还包含未公开依赖。0.429 的正式页面成绩不支持替代 XR0 系列。

SOURCE_CODE_VERIFIED：Harmonic Fusion V3 的 12 单元与昨日快照逐字节相同，当前仍为 0.953。其“Record Edition”等文字和新增投票不构成方法进展。我们已验证的 0.955 高于此版本显示分数 0.002。

## 讨论区：新增内容不等于新增可复现方案

读取 new / active 各第一页，目录显示全区 121 主题；深读 6 个主题、共 **35 个正文/回复对象**（含嵌套回复）。以下明确区分新信息与既有背景。

- **新增截止时间问题**：[743765](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/743765)。询问截止后仍在评分的提交是否有效。当前唯一回复来自参赛者 Satwik，页面无 Host 标识；“必须截止前完成”的说法归为 **COMMUNITY_REPORT**，不是官方新政策。正式规则解释仍为 UNKNOWN，不据此改写官方时间表。
- **标注噪声讨论有新回复**：[742942](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/742942)。新增内容包括分裂坐标/女儿节点缺失的观察、辅助标注工具截图，以及追问具体训练样例。均为 **COMMUNITY_REPORT**；本轮未独立检验图片或统计噪声比例，没有主持方统一更正或可复现提分配方。
- **Public/Private 分布讨论有补充**：[743006](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/743006)。回复建议按胚胎而非短时间片评估，并引用旧 Host 链接；本轮未重新深读被引用 Host 正文，相关分布结论不升级为 HOST_CONFIRMED。Public 29% / Private 71% 的比例已独立从官方榜页核实；比例本身不证明成像条件变化。
- **十次单变量失败帖**：[742266](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/742266)。新回复主要追问，未公开新的可运行配方。既有回复称训练重训并非全部增益来源，并建议检查局部收益是否仅来自一两个异常视频；均为 **COMMUNITY_REPORT**，不能推断榜首的主要算法。
- **八次失败试验帖**：[743222](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/743222)。仍为作者实验自述，未新增回复。其旧基线降低检测阈值失败，不足以反驳我们在 XR0 上 XD960 的 +0.001 实测；不同母版、选择器与输出路径不能横向当成同一受控实验。其关于训练数据暴露、自动选择器改变隐藏运行配置的提醒有研究价值，数值归为 **AUTHOR_CLAIM**。
- **询问前 100 方法帖**：[742169](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/742169)。新回复称卡在 0.957 并求建议，没有具体算法、源码或正式回执；不列作已验证方案。

## 对后续方向的判断（仅分析，未执行）

| 优先级 | 方向 | 支持依据 | 尚缺证据 |
|---|---|---|---|
| 1 | 保留 XRL9 0.955 作为后续研究对照，围绕连接距离做可归因验证 | 本队单次正式 +0.002，直接强于纯公开标题线索 | 隐藏图分项、稳定性；并非自动最终选择 |
| 2 | 检测召回与连接约束的交互 | XD960 单项 +0.001、XRL9 单项 +0.002 | 组合可能互相抵消；没有组合已提分证据，不自动创建候选 |
| 3 | 多帧分裂上下文、检测融合校准 | Aman V6 存在具体源码实现入口 | 目前有真实回退故障且无当前 Public；需先证明模块正常再谈收益 |
| 暂缓 | 再次直接移植 G1、无 flow 速度 0.25、Robust 整套或旧自动选择器 | 本队 G1/速度试验未超过母版；Robust 明显低分 | 不因社区文字或训练集代理分将其升级 |

全部优先级属于 **INFERENCE**。本报告不提出已经证明可达 0.957/0.96 的方案，不新增训练、完整 CV、阈值网格或正式提交。分裂、检测、边连接谁是隐藏集主瓶颈仍为 UNKNOWN。

## 覆盖与交付边界

本轮范围已达到新冻结合同的小型研究要求：三种代码目录各 100、162 ref 去重；排行榜前 400 与本队 UI；6 讨论/35 消息；3 完整 Notebook/34 非空单元静态检查；2 份最新正式提交 API 刷新。没有穷尽全区、未深读所有 121 讨论、未审查讨论附件图片、未更新外链 GitHub 项目；不宣称“全网无更高分方法”。

代码目录的 lastRunTime 与 `get_kernel` 的 metadata.lastRunTime 有不一致，原值保留；版本使用当前页面 Version、Copy & Edit 的精确 SV 与同次 SDK 当前版本共同绑定，不据后者时间字段推断新旧。原始 Notebook SHA256、逐单元检查、与 x138/昨日 diff、目录和讨论证据均在 `research/PUBLIC_UPDATE_20260927/`，无模型权重、CSV、原始数据或凭据入库。

冻结合同：`tasks/CODEX_20260927_PUBLIC_UPDATE_ACCEPTANCE.json`，SHA256 `61437822835489068360a76bfdf1504ffbdbdeb9cec34a52ce6baaaf9dc9ae5d`。自动验收检查报告、覆盖字段、干净 Git 与权威远端 HEAD；来源语义/优化判断保留 manual 门，因此验收框架预期为 `NEEDS_HUMAN_REVIEW`，不得写成全项目 `COMPLETED_VERIFIED`。历史初始全量研究合同不修改。固定内容 commit、关键文件逐字节远端回读与最终验收结果见同目录交付回执 `delivery_receipt.json`。
