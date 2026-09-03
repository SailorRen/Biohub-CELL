# 历史 Kaggle 相似比赛与赛后方案深读

## 结论

共发现 10 个候选历史比赛，逐维比较见 `16_similar_kaggle_competitions.csv`。其中 6 个完成“官方比赛页 + 可绑定的官方 writeup/作者 discussion”深读，合计 12 个 `FULL_PAGE_BODY_READ`。最接近当前任务的两个历史子问题是 CZII 和 BYU 的 3D 点检测；最接近实例分离的是 DSB 2018 与 Sartorius；HPA 和 Recursion 主要提供多通道、弱标签与批次/域鲁棒性经验。六者都没有同时解决 3D+time、细胞分裂、稀疏 GEFF 图、当前图指标与节点总量处罚。

所有页面级时间、bytes 和 SHA-256 固化在 `evidence/browser_reddit_science_history_reads.jsonl`。下面的排名和分数只在能绑定到 Kaggle 官方 writeup/作者身份时报告；页面侧栏出现的无关动态数值没有被当作历史比赛分数。

## 1. 权威排名与分数账本

| 比赛 | 深读身份 | 权威排名 | 可绑定分数 | 证据边界 |
|---|---|---:|---|---|
| 2018 Data Science Bowl | 官方比赛页 + Kaggle Solution Writeup | 1st | `UNKNOWN` | writeup 明确标注 1st；未获得可绑定最终 LB 分数 |
| Sartorius Cell Instance Segmentation | 官方比赛页 + Kaggle Solution Writeup | 1st | 本地 COCO AP `0.396` | 作者明确称其为 validation metric，不是 LB 分数 |
| CZII CryoET Object Identification | 官方比赛页 + 1st-place 作者 discussion | 1st | 组件/单折示例约 `0.740`、`0.752` LB | 不是最终团队分数，不升级为 final score |
| BYU Flagellar Motors 2025 | 官方比赛页 + Kaggle Solution Writeup | 2nd | public `0.86734`; private `0.87656` | 作者称与第一名同分，Kaggle 按提交时间破同分；另报低算力 private `0.86392` |
| HPA Single Cell Classification | 官方比赛页 + Kaggle Solution Writeup | 1st | private `0.555`（简单双模型）；`0.566`（六模型） | 作者 writeup 绑定的 private-LB 值 |
| Recursion Cellular Image Classification | 官方比赛页 + Kaggle Solution Writeup | 1st | final private `0.99763`; public `0.99480` | 作者 writeup 绑定；指标是分类准确率，不可与当前分数比较 |

## 2. 2018 Data Science Bowl

任务是异质 2D 显微图像中的 nuclei instance segmentation，提交为 RLE masks，评价在多个 IoU 阈值上平均。第一名方案采用 U-Net 类模型与较深 encoder，将 touching borders 作为辅助目标，使用交叉熵/soft-Dice、分水岭和形态学处理，并以 LightGBM/对象特征过滤假阳性；writeup 还记录了外部 nuclei 数据和任务特定增强。

可迁移：边界显式建模、中心/边界多头、对象级去重和假阳性控制。必须修改：从 2D dense mask 变为各向异性 3D 点或实例；增加跨帧关联和一对二分裂；导出 GEFF；用当前 edge/division metric 与节点数约束调阈值。原样照搬 mask-IoU 后处理会忽略轨迹一致性。

证据：`hist_dsb2018`（15,338 bytes）与 `hist_dsb2018_writeup`（26,835 bytes）。

## 3. Sartorius - Cell Instance Segmentation

任务是 2D phase-contrast 神经细胞实例分割。第一名 writeup 的主干包括 YOLOX bbox、LIVECell 预训练、Mask R-CNN 与 UPerNet 集成、bbox×mask 重新打分、重叠消解和小对象过滤。作者报告本地 COCO AP 0.396；这不是 Kaggle leaderboard 分数。

可迁移：多尺度实例分离、bbox/mask confidence 校准、overlap cleanup。必须修改：3D 体积模型、z/y/x 物理尺度、跨帧 association、division candidates、GEFF 和 node-count calibration。该任务无时间维和分裂，不能用其 AP 作为当前模型排序依据。

证据：`hist_sartorius`（8,222 bytes）与 `hist_sartorius_writeup`（12,188 bytes）。

## 4. CZII - CryoET Object Identification

任务是在 3D cryo-electron tomography 中输出带类别的 x/y/z 点，F-beta-4 强调召回。第一名作者公开的 detection 部分包含 3D U-Net/heatmap segmentation 与 SegResNet、DynUNet 点检测集成、体积 tiling、NMS 和 TensorRT 加速。作者写出若干组件/单折 LB 示例，但未在所读页面中提供可安全绑定的最终团队分数，因此 final score 保持 `UNKNOWN`。

这是最强的 detection 迁移证据：3D heatmap/blob target、滑窗、重叠融合、物理尺度 NMS 和加速都值得本地测量。必须增加时间窗口、edge scoring、division topology 和 GEFF；阈值应优化当前 adjusted edge/division Jaccard，而不是只追逐 F-beta recall。

证据：`hist_czii`（7,372 bytes）与 `hist_czii_writeup`（18,733 bytes）。

## 5. BYU - Locating Bacterial Flagellar Motors 2025

任务是 3D tomogram 的存在性判断与单点定位，评价组合分类 F-score 和距离定位。第二名团队使用 3D nnU-Net blob/EDT regression、重采样、cropping、sliding-window Gaussian importance 与 NMS。最终单 checkpoint 由作者绑定到 public 0.86734/private 0.87656；同分因提交时间列第二。作者同时明确指出内部验证与榜单差距、阈值优化预算不等，低算力锚点 private 0.86392 不宜与最终模型作严格消融结论。

可迁移：各向异性 3D blob regression、滑窗拼接、峰值抑制和推理资源核算。必须修改：每帧多细胞、连续时间、多父子边、一对二分裂、GEFF 与完整 12h end-to-end 预算。单点任务的存在性头不能表达密集谱系图。

证据：`hist_byu`（6,479 bytes）与 `hist_byu_writeup`（21,016 bytes）。

## 6. Human Protein Atlas - Single Cell Classification

任务是四通道 confocal 图像的逐细胞多标签分类，弱 image-level labels 与 segmentation 共同参与。第一名 writeup 使用 FCAN/PuzzleCAM 与 cell-level Swin、模型加权和边界细胞置信度后处理；作者报告简单组合 private 0.555 和六模型 private 0.566。

可迁移：多通道归一化、弱标签学习、边界不完整对象的置信度处理。必须修改：目标从分类变为 3D 点检测与图关联；引入时间、分裂和 GEFF。HPA writeup 对公开测试图像与公开 HPA 数据的重合做过特别处理，这反而提醒当前任务必须按 embryo identity 审计外部数据重合。

证据：`hist_hpa`（9,486 bytes）与 `hist_hpa_writeup`（6,803 bytes）。

## 7. Recursion Cellular Image Classification

任务是多通道细胞图像的 1,108 类扰动分类，核心困难包括实验批次与 cell-type domain shift。第一名方案使用通道归一化、DenseNet、mixup/cutmix、实验/细胞类型条件、TTA、渐进式 pseudo-labeling 和 assignment。作者绑定的最终值是 private 0.99763/public 0.99480。

可迁移：按 embryo/source 分组验证、通道归一化和域鲁棒增强。不能迁移：利用测试分配结构的 pseudo-label/assignment 或任何已知 batch leak；分类准确率也不对应图边质量。当前比赛应把 test-derived 信息、submission 反推产物和 current-test mirror 全部 fail-closed。

证据：`hist_recursion`（7,441 bytes）与 `hist_recursion_writeup`（21,021 bytes）。

## 8. 其余候选

另列入四个 3D/生物医学分割候选：SenNet + HOA 3D vasculature、HuBMAP + HPA Human Body、HuBMAP Kidney、HuBMAP Human Vasculature。它们仅完成候选发现，`read_status=TITLE_SNIPPET_ONLY`、`deep_read=false`；所有 metric、rank 和 score 均保持 `UNKNOWN`，不以标题推定相似性或赛后成绩。

## 9. 面向当前比赛的组合式适配

候选执行链只能作为待验证设计：

1. 用 CZII/BYU 风格 3D heatmap/blob detector 产生每帧节点，所有距离转为 µm。
2. 用简单 Hungarian/greedy 建立可复现基线，再比较 Trackastra/Ultrack 类窗口关联或全局求解。
3. 对 division 单独建候选与约束，禁止只靠最近邻复制一对一逻辑。
4. 在 GEFF round-trip 后使用官方当前 scorer；同时记录 edge、division、节点数、孤立节点与运行时。
5. split 必须按 embryo/volume 隔离；阈值只在本地 CV 调整，避免 leaderboard-specific overfit。
6. 推理全程离线，模型、wheels 和许可在冻结清单中；12 小时内包含 I/O、检测、关联、导出与校验。

在取得上述同协议测量前，不能评价 DSB、Sartorius、CZII、BYU、HPA 或 Recursion 方法对当前比赛的相对优劣。
