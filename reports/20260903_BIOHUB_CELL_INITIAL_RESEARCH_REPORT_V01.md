# Biohub-CELL 第一轮公开资料研究报告 V01

- 任务：`CODEX_20260903_BIOHUB_CELL_INITIAL_RECON_V01`
- 研究日期：2026-09-03
- 阶段：`RESEARCH_ONLY`
- 终态门禁：机器验收、GitHub main 同步及 13 个权威远端文件 SHA-256 回读
- 证据索引：`research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/00_source_manifest.jsonl`
- 结论矩阵：`research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/19_claims_evidence_matrix.csv`

## 1. Executive Summary

本轮建立了独立公开仓库 `SailorRen/Biohub-CELL`，并在禁止 Kaggle 写入、禁止训练、禁止大型数据下载的边界内完成第一轮公开资料取证。实际研究覆盖 Kaggle 官方比赛入口、Code、Discussion、Leaderboard、公开 Dataset，GitHub 代码生态，Reddit、科学来源及历史 Kaggle 比赛。搜索卡片只用于发现；页面正文、线程、Notebook 源码和固定 Git commit 采用不同的 `read_status`，不能相互替代。

已验证的核心事实是：任务要求从 3D+time 显微影像构建含细胞节点、时序边和分裂拓扑的谱系图；官方分数为 `adjusted_edge_jaccard + 0.1 * division_jaccard`。当前最可审计的工程分解是“3D 节点检测 → 物理距离候选 → 时序/分裂边评分 → greedy、Hungarian 或全局优化 → GEFF/CSV 校验”。这只是来源支持的候选分解，不是已证明更优的模型。本轮没有训练、推理、内部 CV 或新 submission，因此没有自有 baseline 分数，也没有任何性能提升结论。（`OFFICIAL_KAGGLE_CLAIM_001`、`OFFICIAL_KAGGLE_CLAIM_002`、`GH-CL-001`）

评分历史存在必须保留的风险边界：Competition Host 已确认 Division Jaccard 漏洞、补丁和全量重算，Kaggle Staff 随后确认重算完成；但参赛者报告部分公开 Notebook 页面仍可能显示补丁前 Best Score。本轮 30 本源码深读无法把页面卡片分数绑定到具体 `ScriptVersionId` 或 submission，因此这些分数不得当成当前有效成绩。（`CLM_DISC_METRIC_PATCH`、`CLM_DISC_RESCORE_COMPLETE`、`CLM_DISC_NOTEBOOK_STALE_RISK`）

## 2. 本轮实际读取范围

统一清单包含 647 条互不重复的 source 记录：157 条 `FULL_*`，249 条 `METADATA_ONLY`，223 条 `TITLE_SNIPPET_ONLY`，以及单独标识的目标文件阅读、README 阅读、部分线程、阻断和限流。其中 176 条 GitHub 仓库只是从已固化查询页派生的仓库标题/链接，逐条进入 manifest 但不升级为 README 或源码已读。实际深读包括：7 个强制 Kaggle 浏览器入口、8 个官方 API 正文页、30 本 Notebook 的完整当前源码、30 个 Kaggle 讨论线程、15 个 GitHub 仓库的全部相关人类可读源码、4 个 GitHub 仓库的目标文件、28 个 Kaggle Dataset 页面、6 个 Reddit 线程、15 个科学/一手目标范围页面，以及 6 个历史比赛的官方页与权威赛后材料。

“全文/源码已读”只描述本轮观测范围。它不意味着页面永久不变、代码已运行、方法已复现、许可证允许再分发、外部数据已获准或动态分数仍然有效。源码和网页正文没有整份复制进仓库；证据保存 URL、时间、字节数、SHA-256、短摘录与原创摘要。

## 3. 搜索覆盖统计

- 官方/Kaggle Code：5 种排序、20 个指定关键词；观察 460 个卡片出现，按 `owner/slug` 去重得到 194 本 Notebook，深读 30 本、覆盖 25 位作者。（`OFFICIAL_KAGGLE_CLAIM_015`、`OFFICIAL_KAGGLE_CLAIM_016`）
- Kaggle Discussion：3 页 hotness 清单及 28 个关键词检索；发现 73 个唯一主题，深读 30 个。
- GitHub：Repository Search、Code Search 和网页搜索共记录 57 次查询；仓库清单 195 个，固定 commit 深读 19 个，其中 15 个满足 `FULL_RELEVANT_REPO_SOURCE_READ`。大型 Code Search 只读取首屏，不能声称穷尽 GitHub。（`GH-CL-014`、`GH-CL-015`）
- Reddit：8 次 native search、9 次 `site:reddit.com` 查询；深读 6 个线程，其中 5 个完整、1 个部分。直接命中当前比赛的 Reddit 线程为 1 个。
- 科学来源与历史比赛：9 组科学检索、16 个历史比赛关键词；历史候选 10 个，深读 6 个。
- Kaggle Datasets：20 个关键词各检索两页，记录 40 次查询并发现 185 个去重候选；35 个进入清单，28 个页面正文实读。

全部查询的入口、词、排序、分页、可见返回量、去重口径、深读数、时间和证据路径位于 `21_search_query_log.csv`。未暴露总量时明确写 `UNKNOWN` 或“not exposed”，不以搜索摘要推定总数。

## 4. 官方比赛规则和时间线

官方页面确认主办方为 Biohub SF。比赛 2026-06-29 开始；报名截止和组队合并截止均为 2026-09-22 23:59 UTC；最终提交截止为 2026-09-29 23:59 UTC。总奖金 60,000 美元。团队最多 5 人，每日最多 5 次 submission，最多选择 2 个 final submissions；CPU 与 GPU Notebook 均最多 12 小时，推理时 internet disabled。规则允许免费、公开、合理可获得的外部数据和预训练模型，但具体资产仍需逐项审核；获奖者代码许可要求为 MIT。（`OFFICIAL_KAGGLE_CLAIM_011`、`OFFICIAL_KAGGLE_CLAIM_012`、`OFFICIAL_KAGGLE_CLAIM_013`）

只读页面显示当前账户此前已接受规则。这是本任务开始前已存在的账户状态，本轮没有执行规则接受、报名或组队。页面还显示既有排行榜行和计分中指示；它们没有被本轮创建，也尚未绑定到经审计的 Notebook version 或 submission，不计作本项目 baseline。

## 5. 数据结构和规模

Data 页面在抓取时显示 24,886 files、87.61 GB、CC0: Public Domain。本轮只读 API 在第 28 页遇到 HTTP 429，此前取得 5,400 条文件元数据，因此文件级清单是 `5,400/24,886` 的部分覆盖，不是全量；没有下载图像块或完整比赛数据。（`OFFICIAL_KAGGLE_CLAIM_008`、`OFFICIAL_KAGGLE_CLAIM_009`）

官方说明和可见元数据表明：影像为 Zarr v3，主要数组路径 `0/`，维度顺序 `(T,Z,Y,X)`；典型 shape `(100,64,256,256)`、`uint16`、chunk `(1,64,256,256)`，使用 blosc/zstd。训练与测试按 embryo 隔离；可见 test 是运行占位数据，Notebook 重跑时由更大的隐藏 test 替换。（`OFFICIAL_KAGGLE_CLAIM_005`、`OFFICIAL_KAGGLE_CLAIM_007`、`CLM_DISC_DUMMY_PUBLIC_TEST`）

文件路径体现 sample key 与 Zarr/GEFF 成员结构，但 19,486 条未取回的文件元数据、完整样本目录数和完整文件大小分布仍未观测；不得由已取回 5,400 条外推全量组成。

## 6. submission.csv 与 GEFF 图结构

官方字段为 `id,dataset,row_type,node_id,t,z,y,x,source_id,target_id`，每个 test dataset 都必须在 submission 中出现。node 行和 edge 行的非适用字段用 `-1`。GEFF 基于 Zarr 图结构，核心包括 `nodes/ids`、`nodes/props/{t,z,y,x}/values` 与形状为 `(N,2)` 的 `edges/ids`；`estimated_number_of_nodes` 指样本真实总细胞数的估计，而不是稀疏标注节点数。（`OFFICIAL_KAGGLE_CLAIM_006`、`OFFICIAL_KAGGLE_CLAIM_010`）

格式正确与图预测正确是两个门槛。GEFF、tracksdata 和官方 CSV 转换代码提供 schema、验证及 round-trip 线索，但只有在固定小样本上通过本比赛官方 scorer、悬空 edge 检查、ID 唯一性检查和每个 dataset 覆盖检查后，才能称为可提交产物；本轮没有生成 `submission.csv`。（`GH-CL-005`、`GH-CL-006`）

## 7. 官方评分实现

总分为：

`score = adjusted_edge_jaccard + 0.1 * division_jaccard`

节点先按物理尺度后的质心距离做最优二分匹配，最大距离为 7.0 µm；体素尺度为 `z=1.625`、`y=x=0.40625 µm/voxel`。预测 edge 的两端都匹配到真值 edge 两端才计为 TP；基础 Edge Jaccard 为 `TP/(TP+FP+FN)`，并按每个样本的 `TP+FP+FN` 聚合，同时考虑预测总节点与 `estimated_number_of_nodes` 的调整。真值分裂以出度至少 2 定义；Division Jaccard 跨样本 micro-average。官方说明总分可以超过 1.0。（`OFFICIAL_KAGGLE_CLAIM_002`、`OFFICIAL_KAGGLE_CLAIM_003`、`OFFICIAL_KAGGLE_CLAIM_004`）

这意味着检测阈值、重复节点、孤立节点、错误边与错误分裂会通过不同路径影响分数。任何离线代理指标都必须与冻结版官方 scorer 同时报告，不能用 segmentation IoU、CTC TRA 或单独 detection recall 替代本比赛得分。

## 8. 评分补丁和旧分数风险

Host 帖 `KDISC_727154` 确认 Division Jaccard 曾存在 exploit，补丁已发布并将重算所有 submission；Kaggle Staff 帖 `KDISC_728324` 后续确认重算完成。源码深读还验证了一个公开 Notebook 中存在 negative-time/out-of-volume hub 与 forks 的 exploit 注释，但“源码含该逻辑”不证明任何页面分数或当前榜单分数来自该逻辑。（`CLM_DISC_METRIC_PATCH`、`CLM_DISC_RESCORE_COMPLETE`、`OFFICIAL_KAGGLE_CLAIM_019`）

本轮同时观测到 Code 卡片最高显示值高于当时 Leaderboard 第一名。参赛者帖称公开 Notebook 页面仍可能残留补丁前 Best Score，但未获 Host 确认。30 本 GetKernel 当前源码均未暴露可绑定的 `ScriptVersionId`，页面分数也不能绑定具体 submission。因此：Leaderboard 只作为抓取时动态快照；Notebook 卡片分数只记作页面显示值；二者不得做版本级性能比较。

## 9. 当前 Leaderboard 快照

2026-09-03T08:32:44.130Z 的已登录浏览器快照显示 3,032 支队伍，Public/Private 约 29%/71%。rank 1、5、10、25、50、100 的 Public 分数分别为 0.963、0.955、0.949、0.944、0.940、0.937；rank 1–2 同为 0.963，25–31 同为 0.944，50–55 同为 0.940，64–99 同为 0.938。（`OFFICIAL_KAGGLE_CLAIM_014`）

这些都是动态观察值，不是比赛终榜。Overview 稍早显示 3,029 Teams，与稍后 Leaderboard 的 3,032 不冲突，反映抓取时点不同。本轮看到的账户既有 0.885 行和计分中状态没有版本绑定，不属于本任务结果。

## 10. 官方 baseline

getting-started Notebook 的当前源码使用平滑/阈值与 connected components 提取节点，再用相邻帧 Hungarian 匹配并写出提交结构；该源码逻辑已逐 cell 检查，但输出单元为空，本轮没有运行或复现它。（`OFFICIAL_KAGGLE_CLAIM_017`）

官方组织方仓库提供更完整的候选链：TemporalUNet3D 中心概率、SimpleNodeTransformer 相邻帧边评分、greedy/ILP 图求解、稀疏标注评价以及 GEFF/CSV 转换。固定 commit 的相关源文件已读取，但没有下载数据、权重或执行训练，因此“官方 baseline”是代码身份与结构结论，不是已验证分数。（`GH-CL-001`、`GH-CL-002`、`GH-CL-003`、`GH-CL-004`）

## 11. Kaggle 公开代码方法分类

30 本源码的语义扫描显示：阈值检测 30/30、图关联 26/30、Hungarian 25/30、division 逻辑 25/30、node-count calibration 24/30、track filtering 23/30、gap closing 22/30、ILP/Motile 信号 21/30、3D U-Net 信号 19/30、DoG/LoG 17/30；Trackastra、Cellpose、watershed 各只在少数源码出现。分类是源码 token/结构证据，不是方法质量排序。

所有 30 本当前源码合计 3,022,497 bytes、122 个 markdown cells、218 个 code cells；218 个 code cells 全部检查并逐 cell 固化 SHA-256。GetKernel 响应中的 output-bearing cell 为 0，所以不能确认训练真实发生、推理完成、运行时间、产物存在或作者分数已复现。（`OFFICIAL_KAGGLE_CLAIM_016`）

## 12. 高相关公开 Notebook 深度比较

源码层可区分五类：简单阈值/connected-component + 最近邻或 Hungarian；3D U-Net heatmap + 运动门限；学习型节点/边评分 + ILP；Trackastra 或 Cellpose 等外部组件；以及显式面向 metric 的 node/division 后处理。Trackastra 候选源码确实包含 DoG/local maxima、watershed、graph transformer 与轨迹过滤，但其页面分数、当前版本和实际离线运行成功没有闭环。（`OFFICIAL_KAGGLE_CLAIM_018`）

`07_kaggle_method_comparison.csv` 逐本记录 detection、segmentation、node extraction、temporal linking、optimization、division、过滤、node-count、外部资产、CV、运行时、许可、失败和 evidence IDs。凡许可证未暴露，源码只保留哈希和原创摘要，不保存完整内容；凡分数未绑定 `ScriptVersionId/submission`，`current_verified_public_score` 保持未知。

## 13. 公开讨论中的官方确认

实际完整读取 30 个线程和所有当前可加载评论。Host/Kaggle Staff 的高价值确认包括：Division metric exploit 与补丁/重算；公开 test 只是运行占位样本、隐藏 test 更大且与公开 train 无重叠；公开 Zebrahub 数据和资源可使用且 Host 称与隐藏 test 无重叠；Zarr 有多语言实现；官方 Discord 不由 Host/Staff 持续监控，重要信息应留在比赛论坛。（`CLM_DISC_METRIC_PATCH`、`CLM_DISC_RESCORE_COMPLETE`、`CLM_DISC_DUMMY_PUBLIC_TEST`、`CLM_DISC_ZEBRAHUB_ALLOWED`）

普通参赛者关于 CV/LB、数据错误、计分时延、手工标注合法性和个人分数的回复只记作 `COMMUNITY_REPORT`、`AUTHOR_CLAIM` 或 `UNKNOWN`。特别是手工标注外部数据的问题没有 Host 回复，不能据此决定规则。（`CLM_DISC_CV_RISK`、`CLM_DISC_HAND_LABEL_UNKNOWN`）

## 14. GitHub 代码生态

GitHub 清单发现 195 个去重仓库，19 个固定 branch 与 40 位 commit 做深读，1165 个相关人类可读文件被完整读取并哈希；其中 15 个仓库满足冻结的“全部相关源码已读”定义，4 个仅为目标文件阅读。该定义不包含二进制、生成目录和托管自动化，也不代表运行或复现。

职责边界清楚：GEFF 负责 Zarr 图交换/schema/验证；tracksdata 负责图结构、候选边与 greedy/ILP 等基础能力；Ultrack 从分割候选与时序/重叠约束建立全局优化；Trackastra 从实例 mask 或检测产生学习型关联；Cellpose、3DeeCellTracker、btrack、ByoTrack、ELEPHANT 是前端或跟踪组件。所有组件都需要当前比赛的稀疏标签、物理距离、division、node-count、GEFF 和离线 12 小时适配。（`GH-CL-005` 至 `GH-CL-010`）

参赛者仓库展示 DoG+CNN+min-cost-flow、Cellpose+Motile、heatmap+LAP/Ultrack、cross-attention+min-cost-flow 等路线；README 分数没有独立复跑。固定 tree 中无许可证的仓库不复制源码。（`GH-CL-012`、`GH-CL-013`）

## 15. Reddit 和其他社区情况

两条搜索路径均被执行：Reddit native search 与网页 `site:reddit.com`。深读 6 个线程，当前比赛的直接 Reddit 命中为 1 个。该帖报告 submission 保存/计分等待接近一天；这是单个用户的社区报告，没有平台级官方确认，不能推广为 Kaggle 服务时限。（`community_current_issue`）

其余 Reddit 命中主要涉及一般 Kaggle、3D 显微或细胞数据问题。页面被删除、评论未全加载或搜索未命中均在 manifest/failure ledger 单列，不能改写为“公开社区没有资料”。image.sc 的 ELEPHANT 主题属于作者/社区介绍，也不等于当前比赛效果证据。

## 16. Cell Tracking Challenge、Ultrack、Zebrahub 等相关研究

CTC 把 detection、tracking/linking、segmentation 与生物学质量拆开评估；其 gold/silver 标注在覆盖和质量上有不同权衡。这提供诊断框架，但 CTC 的 DET/TRA/SEG 不能替代当前 adjusted-edge/division 分数。（`ctc_metrics`、`ctc_annotations`）

Ultrack 支持 2D/3D 的分割候选、时序边和全局求解；Trackastra 用 Transformer 预测时序关联并支持分裂；GEFF 定义节点、边、属性和轴元数据；Zebrahub 提供斑马鱼发育、光片成像与谱系重建背景。这些来源证明组件范围和科学背景，不证明当前比赛 CV、运行时或外部数据资格。（`ultrack_scope`、`trackastra_scope`、`geff_structure`、`zebrahub_context`）

Temporal Affinity Fields 的原论文对象是 2D 多人姿态视频，不是 3D 细胞谱系；只能作为表示类比。若探索 affinity field，必须重新定义各向异性 3D 物理坐标、一对二分裂、GEFF 解码及 node-count 约束。

## 17. 类似 Kaggle 历史比赛

列出 10 个候选并深读 6 个：2018 Data Science Bowl、Sartorius Cell Instance Segmentation、CZII CryoET Object Identification、BYU Flagellar Motors 2025、HPA Single Cell Classification、Recursion Cellular Image Classification。CZII/BYU 对 3D point/blob detection 最接近；DSB/Sartorius 对实例分离最接近；HPA/Recursion 对多通道、弱标签与域偏移有启发。没有一个同时覆盖 3D+time、稀疏谱系、division、GEFF 与当前指标。（`history_3d_transfer`）

历史排名/分数只在官方 writeup 或作者身份可绑定时记录。不同比赛指标不可横向比较。迁移至少要加入 temporal linking、division、物理距离、node-count calibration、GEFF 与完整离线运行预算；历史方法不能原样作为当前方案。

## 18. Kaggle Datasets 候选

35 个候选进入清单：28 个页面正文已读取，1 个仅元数据，5 个在细节 API 阶段限流，1 个页面阻断。搜索发现总集合为 185 个去重候选。页面观察包括当前比赛支持包、权重镜像、Zebrahub/细胞跟踪资源及噪声较高的同名结果；标题中的“Biohub”不构成来源或合法性证据。（`dataset_deep_count`）

本轮没有下载 Dataset 内容，也没有创建 Kaggle Dataset。每行都保留 owner/ref、动态元数据、文件线索、许可显示、相关性、泄漏风险和实际读取状态。

## 19. 外部数据合法性和泄漏风险

Host 已明确允许公开 Zebrahub 数据和资源，并称其与隐藏 test 无重叠；这不自动授权任意 Kaggle 镜像、比赛衍生产物或权重包。具体资产仍需验证原始来源、发布时间、样本身份、许可证、所有参赛者可合理获得性、是否来自当前 test/submission 反推，以及是否满足比赛 Reasonableness 条款。（`CLM_DISC_ZEBRAHUB_ALLOWED`）

本轮 35 个 Dataset 候选的 `rule_eligibility_checked` 全为 false，统一 `DO_NOT_USE_PENDING_RULE_REVIEW`。没有任何候选被批准用于训练；公开权重可能覆盖训练胚胎的社区警告也尚未完成逐权重 lineage 审计。（`dataset_eligibility`、`CLM_DISC_CV_RISK`）

## 20. 当前可复现资源

当前可重复执行的是研究证据与校验流程，而不是模型结果：统一 source manifest、查询日志、claim matrix、Notebook cell 审计、GitHub 固定 tree/commit/文件哈希、页面读取记录、外部操作台账、总装脚本和 bundle verifier。官方仓库与 getting-started Notebook 提供后续最小基线代码身份；本轮未运行它们。

再分发目录为空并附边界说明：没有明确许可证的 Notebook 或网页正文不进入仓库；第三方仓库仅保存 URL、commit、tree、文件哈希、短摘录和原创研究笔记。

## 21. 当前未知事项

- 19,486 条未取回的官方文件元数据及全量目录/大小分布，受 API 429 影响。
- 30 本深读 Notebook 的具体 `ScriptVersionId`、历史版本差异以及页面 Best Score 对应的 submission。
- Notebook 卡片旧分是否已在所有页面刷新；Host/Staff 只确认排行榜重算完成。
- 当前账户既有 0.885 行与计分中对象的确切 version/submission lineage；它们不属于本轮动作。
- 每个外部 Dataset/权重的上游许可证、发布时间、样本去重和规则资格。
- 手工标注外部数据的官方解释。
- 任一候选 detection/linking/division 方法在 embryo-disjoint CV、官方 scorer 和 12 小时离线约束下的效果与运行时。

## 22. 被阻断的来源

统一 manifest 记录 5 条 `BLOCKED` 和 6 条 `RATE_LIMITED`。主要包括：bioRxiv 安全验证页、Biohub 初始旧路由超时、2 个 Dataset 页面正文阻断、5 个 Dataset detail 限流，以及官方 competition file API 第 28 页限流。精确 source ID、URL、证据路径和说明由 `20_access_failures.md` 自动从 manifest 生成。

GitHub 子任务早期隔离上下文中的匿名/默认 CLI 调用曾出现登录或 IP 限流信号；它只描述该隔离调用，不能外推主执行环境。主任务在写入前已独立确认 `gh api user` principal 精确为 `SailorRen`，并成功创建目标仓库。

## 23. 下一阶段建议调查事项

以下都是候选验证，不是模型优劣结论：

1. 冻结官方 scorer commit 和最小 train metadata，建立 GEFF/CSV round-trip、ID、dataset coverage、悬空 edge 与物理坐标单元测试。
2. 先在 embryo-disjoint split 上运行 getting-started/官方 baseline，分别记录 node recall/precision、edge、division、node-count adjustment、总分、I/O 与总运行时；未得到测量前不称 baseline 已建立。
3. 固定同一 detector nodes，仅比较 nearest-neighbor/Hungarian、greedy、Trackastra/Ultrack/ILP 关联，避免 detection 变化混入 tracking 消融。
4. 对 CZII/BYU 风格 3D heatmap/blob detector 做小规模、本地、同协议检测实验；必须加入时间、division 和 GEFF 后才与端到端方法比较。
5. 对每个 Zebrahub、CTC、权重或 Kaggle Dataset 建立上游 URL、许可证、发布日期、样本 ID/hash、规则条款与 Host 说明六联表；任一项不闭合则继续禁用。
6. 单独向 Host 澄清手工标注外部数据和公开 Notebook 旧分刷新状态，不以普通参赛者回复代替规则。
7. 任何未来 Kaggle submission、Notebook Version 或训练都需要用户另行明确授权，并在写入前冻结 identity、quota、版本、重复提交和回收合同。

## 证据状态与本轮外部动作

- 已验证事实：官方规则/数据/metric、Host/Staff 补丁与重算说明、源码结构、搜索及读取计数。
- 合理推断：候选工程分解与历史方法的适配项；尚无性能结论。
- 未观测：本项目训练、CV、推理、可绑定 baseline、真实新 submission 分数。
- 本轮 Kaggle submission：0。
- 本轮 Kaggle Notebook 写入：0。
- 本轮训练任务：0。
- 本轮 Kaggle Dataset 创建：0。
- 本轮规则接受/报名：0。
- 大型数据下载：0。
