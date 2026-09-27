# Biohub-CELL 最新成绩与公开区晚间报告

观测窗口：2026-09-27 21:19 至 21:25（上海）。执行分支：`codex/xrl9-two-wave-20260927`。本轮为结果回收与只读研究；Kaggle 新运行、新正式提交、最终选择修改均为 0。

## 结论

**MEASURED：R9D955 正式 Public 0.956，为本组已核验候选最高分；比 XR0 0.953 高 0.003，比 XRL9 0.955 高 0.001。首波三份正式结果 3/3 COMPLETE，无直接错误。当前团队排名 191 / 3953，较今日中午 225 / 3941 前进 34 位。**

公开区三种排序各 100 条、去重 162 个 Notebook：相比中午样本没有新增对象，有 1 个更新对象。没有核实到新出现且有准确正式分数支持的高分公开方案。这个结论仅覆盖本次样本，不等于全站不存在。

## 我们的正式成绩

以下九份均由官方提交 API 本轮重新读取；全部 COMPLETE。SV 绑定来自既有精确运行回执及提交描述。XR0 owner 为 dongdongjiaqi，其余为 sailorren。最后观测时间见本目录 observation.json / 三份 formal_last_observed.json。

| 候选 | Version / SV | Submission ID | Public | Δ XR0 | Δ XRL9 | 提交时间（上海） |
|---|---|---|---:|---:|---:|---|
| XR0 | V1 / 352643547 | 56546951 | 0.953 | +0.000 | -0.002 | 09-25 17:25:57 |
| XV25 | V1 / 352908214 | 56573059 | 0.953 | +0.000 | -0.002 | 09-26 15:31:40 |
| XG95 | V1 / 352908258 | 56573089 | 0.929 | -0.024 | -0.026 | 09-26 15:32:41 |
| XV25G95 | V1 / 352913254 | 56573515 | 0.952 | -0.001 | -0.003 | 09-26 15:51:48 |
| XD960 | V1 / 353050916 | 56585147 | 0.954 | +0.001 | -0.001 | 09-27 01:22:55 |
| XRL9 | V1 / 353050971 | 56587392 | 0.955 | +0.002 | +0.000 | 09-27 03:33:36 |
| R9D960 | V1 / 353188100 | 56599443 | 0.955 | +0.002 | +0.000 | 09-27 13:55:59 |
| R8D965 | V1 / 353188155 | 56599380 | 0.955 | +0.002 | +0.000 | 09-27 13:53:07 |
| R9D955 | V1 / 353192186 | 56599964 | 0.956 | +0.003 | +0.001 | 09-27 14:08:34 |

本轮三份分别为：R9D960（检测 0.960、relaxed 9 µm）、R8D965（0.965、8 µm）、R9D955（0.955、9 µm）。三个普通运行与输出验收证据保存在对应实验目录；此处的提升依据是正式 Public，而非普通运行成功。

## 排行榜与目标差距

[官方排行榜](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/leaderboard)；API 前 200 行与浏览器团队行交叉核对。分数为页面三位小数，达到同一显示分数不保证同名次。

| 名次 | 中午显示分 | 晚间显示分 | 比我们 0.956 高 |
|---|---:|---:|---:|
| 1 | 0.978 | 0.978 | 0.022 |
| 50 | 0.962 | 0.963 | 0.007 |
| 75 | 0.959 | 0.960 | 0.004 |
| 100 | 0.957 | 0.959 | 0.003 |
| 150 | 0.956 | 0.956 | 0.000 |
| 200 | 0.955 | 0.955 | -0.001 |

OFFICIAL_FACT：Public 约占测试数据 29%，Private 占 71%。当前页面奖牌图标不是最终获奖结论。前三名仍为 yu4u 0.978、Sergio Alvarez 0.975、Gabriel 0.975；排行榜高分本身不证明对应源码已经公开。

## 公开代码更新

### 新近更新：m-toshi desu V6

[精确 V6 / SV353197576](https://www.kaggle.com/code/mtoshidesu/testbiohub-lf-dctta020-sectta1?scriptVersionId=353197576)。页面显示普通运行成功，T4×2，2h13m10s；当前 V6 正式 Public 为 UNKNOWN。Best Score 0.947 属于 V2 / SV349927817，不能移植给 V6。

SOURCE_CODE_VERIFIED（定向检查）：取得完整 45 个代码单元，检查配置、消费位置和末尾选择器。检测阈值 0.965，DeepCenter 分裂阈值 0.20、TTA 打开；secondary edge-feature TTA 权重实际设为 1.0；motion relaxed 默认 10 µm、velocity 0.5。标题或注释的“三分之四强度”不能覆盖实际赋值。

源码默认启用 validator，对七个后处理参数候选及组合做代理分数选择，并可能重写 submission.csv。该机制与我们冻结 XR0 的关闭自动选择器不同。V6 的具体实际胜出配置、正式提交及收益没有核实，不能据普通运行成功引入。没有本地缓存其前版本完整源码，本轮不宣称上述每一项都是 V6 新改动。

### 三份重点旧方案

| 方案 | 当前源码回读 | 已有准确分数证据 | 判断 |
|---|---|---|---|
| [Aman optimized](https://www.kaggle.com/code/amanatar/optimized-biohub-max-score?scriptVersionId=353147685) | V6，与中午逐字节一致 | V6 Public UNKNOWN；V4/SV352554580 为 0.953 | 中午日志已有 SAFE_DIV_HORIZON_FRAMES 未定义、repair_fallback 证据；不能按标题当高分升级 |
| [Robust 3D](https://www.kaggle.com/code/sarveshchhetri/robust-3d-cell-tracking?scriptVersionId=352988018) | V8，与中午逐字节一致 | 中午核实 V8 0.429 | 无新增收益证据 |
| [Harmonic Fusion](https://www.kaggle.com/code/raunakdey07/biohub-harmonic-fusion-v3?scriptVersionId=352639153) | V5，与中午逐字节一致 | 中午核实 V5 0.953 | 已被本组正式 0.956 超过 |

这三份的分数引用今日中午精确版本读回，不冒充晚间再次读取页面分数；晚间刷新的是完整源码一致性。详见[中午报告](20260927_BIOHUB_PUBLIC_UPDATE_AND_RESULTS.md)。

## 讨论区

读取 new、active 两个目录各 20 条；目录总计 121 个主题。六个重点主题按 message ID 对齐后，正文均与中午一致；差异只有排序和投票数，没有新增正文。

- [十次失败实验](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/742266)：COMMUNITY_REPORT，作者称训练视频的离线改进未转化为 Public，节点数与排名变化相关；不是我们模型的因果结论。
- [八次失败实验](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/743222)：AUTHOR_CLAIM，旧母版阈值 0.960 退分与我们的 XR0/XRL9 正式结果不矛盾；基线和后处理不同。不能泛化为“检测阈值 0.965 已全局最优”。
- [标注问题](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/742942)：COMMUNITY_REPORT，参赛者举出标注疑点；本轮未独立核验图像，不据此断言隐藏集有同类错误。
- [Public/Private 分割](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/743006)：COMMUNITY_REPORT，回复引用主办方旧帖并建议按 embryo 留出；本轮未追读被引用原帖，不升级为 HOST_CONFIRMED。
- [前百方法讨论](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/742169)：没有新增可复现配方。
- [截止时仍在评分](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/743765)：仍无核实的主办方回复；普通用户答复不当作截止规则。

## 基于结果的判断

1. MEASURED：固定 relaxed=9 时，检测 0.965→0.960 为 0.955→0.955，进一步到 0.955 得 0.956；显示分数支持这次较低阈值候选，但不能证明分数单调或 Private 必然提升。
2. MEASURED：检测保持 0.965，relaxed 9→8 没有显示分提升。XD960 单独 +0.001 与 XRL9 单独 +0.002 也未在 R9D960 上相加。
3. INFERENCE：若后续续接冻结两波任务，应优先依其检测方向规则决策；当前证据不足以转向 G1、叠加未验证公开补丁或恢复自动选择器。第二波尚未构建或启动，本报告不替代第二波执行。
4. 当前 0.956 到前百显示线尚差 0.003；不能承诺靠剩余两个候选进入前百。

## 交付与范围

两波任务首批状态更新为 WAVE1_SCORED：3/3 有正式有效 Public；累计正式请求仍为 3/5。工程备用已用 1/1，剩余最多两份并不等于实时额度充足。未刷新 GPU 余额，因为本轮没有启动运行。原最终选择未改变。

证据：`research/PUBLIC_UPDATE_20260927_EVENING/`；原任务账本：`experiments/BIOHUB_XRL9_TWO_WAVE_20260927_V01/platform_ledger.json`；正式任务结果：[执行记录](20260927_BIOHUB_XRL9_TWO_WAVE_RESULTS.md)。

覆盖限制：抽样目录不等于全站穷尽；新 V6 取得完整源码但只定向审查配置和选择器，不标记 FULL_NOTEBOOK_SOURCE_REVIEWED；未执行任何外部源码或动态补丁，未开展 CV。搜索引擎索引存在延迟，当前结论以 Kaggle 实时 API、页面和固定源码为依据。验收针对本次有界报告，不声称整个历史项目合同完成。
