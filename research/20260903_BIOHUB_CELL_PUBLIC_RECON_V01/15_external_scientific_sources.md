# 外部科学来源：细胞跟踪、谱系图与斑马鱼发育

## 结论

本轮成功读取了 15 个权威或一手目标范围页面（13 个 `FULL_PAGE_BODY_READ`、2 个 GitHub `README_ONLY`），另有 3 次受阻访问。能够稳健迁移到当前比赛的是问题分解与工程约束：3D 检测、跨帧关联、分裂拓扑、图数据结构、物理坐标和内存受限求解。没有任何外部来源证明某一方法在本比赛的 adjusted edge Jaccard、division Jaccard、节点总量处罚与 12 小时离线 Notebook 约束下更优；因此这里只列候选验证方向，不作分数承诺。

页面级字节数、SHA-256、UTC/新加坡时间和读取状态位于 `evidence/browser_reddit_science_history_reads.jsonl`。所有社区说法均与官方/论文事实分开。

## 1. Cell Tracking Challenge（CTC）

实际读取页面：

- 数据集说明：`ctc_datasets`，2,586 bytes，`FULL_PAGE_BODY_READ`。
- 评估方法：`ctc_evaluation`，5,632 bytes，`FULL_PAGE_BODY_READ`。
- 标注说明：`ctc_annotations`，3,321 bytes，`FULL_PAGE_BODY_READ`。
- 历史与出版物：`ctc_history`，8,004 bytes，`FULL_PAGE_BODY_READ`。
- 持续更新的 Cell Tracking Benchmark：`ctc_results`，1,950 bytes，`FULL_PAGE_BODY_READ`。
- 十年客观评测论文：`ctc_nature_methods`，102,248 bytes，`FULL_PAGE_BODY_READ`。

已验证事实：CTC 同时覆盖 2D/3D time-lapse 数据；技术指标将 detection、tracking/linking、segmentation 分开，TRA/DET/LNK 基于图编辑代价归一化，BIO 汇总完整轨迹、轨迹片段、分支正确性和细胞周期等生物学量，OP_CTB 组合 SEG 与 TRA。Gold tracking annotation 强调完整实例覆盖，gold segmentation 强调较小区域中的高质量轮廓，silver annotation 扩大覆盖但质量边界不同。CTC 还明确列出数据使用条件；“公开可见”不能自动推导为可在 Kaggle 中用于训练。

对当前比赛的含义：

- 有用：将 node detection、edge linking、division topology 分开诊断；按 embryo/volume 做分组验证；分别记录技术和谱系错误。
- 必须修改：当前输出是 GEFF 图而不是 dense segmentation；当前指标不是 CTC TRA/DET/OP_CTB；节点数处罚和 7 µm 匹配条件需要单独校准。
- 未证明：CTC 排名不能映射成本比赛分数；CTC 数据能否作为外部训练数据必须重新核对许可和比赛规则。

## 2. Zebrahub 与 Biohub/Royer Group

`zebrahub_pubmed` 是已发表 Cell 论文的 PubMed 页面，正文摘要实际读取 8,513 bytes。摘要表明该工作把单细胞测序和光片显微谱系重建结合成发育图谱。`biohub_royer` 是 Biohub 的 Royer Group 研究页，实际读取 2,609 bytes，将 Zebrahub、光片显微、发育生物学、成像与图像分析置于同一研究脉络。

这能确认生物学和成像背景，但不能确认 Kaggle 外部数据资格。尤其是任何自称“Zebrahub 实标签裁块”的 Dataset，都可能与当前训练/测试来源重合；在来源时间、样本身份、许可和规则全部闭合前必须 `DO_NOT_USE_PENDING_RULE_REVIEW`。

访问状态：初始 `https://www.czbiohub.org/royer/` 路由超时（`biohub_royer_initial`），随后 `https://biohub.org/royer/` 成功。bioRxiv 的两个路由均只显示安全验证页（`biorxiv_zebrahub_full`、`biorxiv_zebrahub_abs`），未把验证页误标为论文正文；已发表版本的 PubMed 摘要用于事实核对。

## 3. Ultrack

`ultrack_docs` 全文读取 40,865 bytes。官方文档呈现的工作流是：从分割假设生成候选、构建跨时关联、全局求解，再导出/后处理；支持 2D/3D、大数据和数据库后端，并展示斑马鱼等使用情境。

可迁移部分是候选图和全局一致性求解；必须修改的是稀疏点监督、当前 GEFF 字段、分裂约束、节点总量与运行时预算。文档能力不是本比赛测量值；只有 embryo-disjoint 本地 CV 或真实 Kaggle submission 才能比较。

## 4. Trackastra

`trackastra_arxiv` 全文读取 3,289 bytes；摘要描述在时间窗口内用 Transformer 建模成对关联并处理分裂，输入前提是已有实例分割或检测。`trackastra_github` 仅将实际读取范围标为 `README_ONLY`（6,279 bytes）；README 展示 2D/3D 数组接口、预训练模型以及 greedy、greedy-with-division 和 ILP 等跟踪模式。

可迁移部分是关联评分和分裂候选；必须另做 3D 点检测、物理距离门控、GEFF 转换、node-count calibration 与 12 小时离线打包。Kaggle 上的 Trackastra 权重镜像仍需逐个核对上游版本、模型许可和发布时间，不能仅凭 Dataset 页面许可字段决定使用。

## 5. GEFF 与 tracksdata

`geff_spec` 全文读取 17,949 bytes。规范使用 Zarr 组织图，包含 node/edge IDs、属性组、轴与元数据；这直接对应当前 submission 的结构正确性，但不决定图中节点和边是否正确。

`tracksdata_github` 的实际范围是仓库 README（3,198 bytes），介绍图表示、RustWorkX/SQL 后端、神经网络/ILP 工具和 CTC 格式互操作。它是实现候选，不是现成的当前比赛方案。后续需要固定版本、读取实际源码、跑小型 round-trip 和官方 scorer 才能把“可导出”升级为“符合本比赛 schema”。

## 6. image.sc / ELEPHANT

`image_sc_elephant` 全文读取主题及当前可见回复（2,550 bytes）。主题介绍 3D+time 谱系标注、深度学习、人工校正和增量学习的一体化平台。这说明交互式纠错和稀疏标注循环在科学工作流中存在，但 image.sc 帖子属于作者/社区说明，不是当前比赛效果证据。

## 7. Temporal Affinity Fields

`staf_arxiv` 全文读取 2,510 bytes。原始 Recurrent Spatio-Temporal Affinity Fields 论文针对多人 2D 姿态视频跟踪，而非细胞或谱系。调查结果仅支持“跨时间关联场”是一种可类比的表示；不支持把 STAF 原方法或其人体姿态指标直接迁移到 3D 胚胎细胞。

如果后续探索 affinity field，至少需要证明：输出在各向异性 3D 体素和物理坐标中定义；能表达一对二分裂；从场到 GEFF edge 的解码受节点数约束；在 embryo-disjoint CV 中相对距离/Hungarian/ILP 基线有真实增益。

## 8. 证据到实验的最小闭环

| 来源证明的内容 | 当前比赛尚未证明 | 后续验证 |
|---|---|---|
| CTC：检测、关联和生物学质量需分开测 | CTC 指标优化会改善当前 edge/division Jaccard | 同一 embryo split 上同时跑官方 scorer 与诊断指标 |
| Ultrack：候选图和全局求解可扩展到 3D | 在稀疏点、节点处罚和 12h 下优于简单关联 | 固定检测节点，对比 Hungarian、greedy、ILP；记录运行时和节点数 |
| Trackastra：时间窗口关联可处理分裂 | 预训练权重适合当前斑马鱼域 | 冻结检测，做 embryo-disjoint 关联消融，并核对许可/来源 |
| GEFF：图 schema 有明确规范 | 任意 tracksdata/GEFF 导出都满足比赛细节 | 小型 round-trip、官方 scorer、孤立/悬空 edge 检查 |
| Zebrahub：成像与谱系背景高度相关 | 任一公开镜像可合法用于训练 | 建立样本身份、发布日期、许可与规则四联表；未闭合即禁用 |

## 9. 明确边界

- 本轮没有下载 CTC、Zebrahub 或任何 Kaggle Dataset 的大型内容。
- 本轮没有训练、推理或提交，因此所有算法优劣均为未观测。
- 页面/README 自述只支持“作者或发布者如此说明”，除非另有官方规范或论文交叉验证。
- 所有 Dataset 候选默认 `rule_eligibility_checked=false`，并标为 `DO_NOT_USE_PENDING_RULE_REVIEW`。
