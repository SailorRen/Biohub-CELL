# 公开 Notebook 源码刷新与优化线索（2026-09-09）

当前读到的公开代码没有提供已验证超过自有 B0 0.946 的新架构。Harmonic 与 942tta 属于同一执行算法；最新 Lineage Forge 仅把次模型边特征 TTA 设成 0.75 插值，仍显示 0.946。源码更值得处理的结构问题是：**最终 motion 重连会覆盖 ILP 的原始分裂拓扑，再由 safe-div 重建分裂**。这为下一轮提出了明确的机制假设，但未实测，状态 `INFERENCE / NOT_RUN`。

研究只读。没有保存、运行 Notebook、训练、正式提交、Dataset/Model 写入。根负责浏览器 Version/SV/分数观察及最终报告，本文件负责 SDK 公开代码目录与源码。

## 来源覆盖和身份

SDK 按 `dateRun` 和 `voteCount` 各读取第一页 30 项，共 59 个不同 ref；这只是有范围的来源发现，不是公开区完整目录。完整目录与观察时间见同目录 `notebook_findings.json`。列表标题、赞数和末次运行时间不用于证明方法或分数。

| 来源 | API Version / kernel ID | 源码覆盖 | 结论 |
|---|---|---|---|
| [942tta](https://www.kaggle.com/code/redoctopusk/biohub-942tta?scriptVersionId=347821442) | V1 / 133372183 | 12/12 cell 与9月8日已逐cell全读的完整源码及cell哈希一致，本轮 AST、关键源码重核 | 与自有 B0 开发母版一致 |
| [Harmonic Fusion](https://www.kaggle.com/code/flexonafft/biohub-harmonic-fusion?scriptVersionId=347965685) | V29 / 131620291 | 12/12 cell 按完整源hash+cellhash重核原全读；当前浏览器 V29/SV347965685/.946 | 剥离cell0展示docstring后，12cell AST与942tta完全相同 |
| [Lineage Forge](https://www.kaggle.com/code/flexonafft/biohub-lineage-forge-precision-tracking?scriptVersionId=348210665) | V7 / 133330467 | 全部12cell；10cell与全读Harmonic逐字相同，另2cell全部差异读取；动态补丁展开审读 | 当前 V7/SV348210665/.946；次特征TTA 0.75插值 |
| [The metric pays you to delete nodes](https://www.kaggle.com/code/zhincez/the-metric-pays-you-to-delete-nodes) | V4 / 133516745 | 本轮全部9cell全文读取，含1个36行代码cell、8个Markdown cell | 作者的删节点负面实验案例，不是可绑定正式提交的独立评分证据 |
| [run84](https://www.kaggle.com/code/rogerrogerroger3r/biohub-run84) | V1 / 133532578 | 全部10cell已取得及AST检查，但人工仅重点差异审读，明确 `PARTIAL_NOTEBOOK_SOURCE_READ` | relink bonus3/tight7/relaxed11，取消母版PP自动选参；不计入全读最低数 |

两份母版采用 `FULL_NOTEBOOK_SOURCE_REVERIFIED`，明确复用9月8日全读证据，**不声称本轮重新逐字读取八千多行**。Lineage Forge 采用 `FULL_NOTEBOOK_SOURCE_DIFFERENTIAL_READ`，全部代码cell由逐字一致性或完整增量审读覆盖。相同代码家族不能算独立算法证据。

当前原始源码仅保存在 ignored `downloads/20260909_public_research/notebooks/`；每份源SHA、每cell源SHA/AST SHA/行数、API读取时间、逐cell覆盖及浏览器绑定见JSON。

## 当前方案已经包含的部分

942tta/Harmonic/B0 已经具备相同主/次 TemporalUNet3D 权重、DeepCenter epoch2、安全分裂几何门槛、主模型8次pass特征平均、双模型检测融合、主模型正反时间 harmonic 概率融合0.15、次模型 low-margin 共识边融合0.15、ILP、motion重连、gap/gap2、短轨保留/救回、相同的7项PP自动选择。

主/次检测的“8次pass”只有7个不同XY视角，C1修正为8唯一视角后本项目正式0.940。C2对已有次模型encode特征求全均值后正式0.946，按三位显示持平。不能把公开副本标题当新模型，也不能从源码相同推导运行分数自动相同。

## Lineage Forge 增量究竟是什么

相对 Harmonic V29，仅 cell0 文案与 cell4 追加19物理行动态patch变化。补丁 old 字符串47行、new99行；本轮在已冻结 B0 完整展开源码上核得唯一锚点1处，替换后 `compile` 成功（仅静态，不执行模型）。

它复用次模型检测TTA已经计算的特征，逆变换后取8次均值，并写入：

`secondary_features = 0.25 * original_features + 0.75 * tta_mean`

C2则直接用 `tta_mean`，即权重1.0。它保留母版重复XY视角，没有采用C1的修正；检测、主模型、关联融合权重、PP选择都未变化。页面 V7/SV348210665 为0.946，因此目前没有支持“继续扫0.75附近权重可以提分”的正面证据；三位持平也不能证明内部更高精度完全相同。

## motion 与分裂拓扑的结构问题

源码位置：942tta cell5 `motion_relink_edges` 第420–551行，`filter_output_graph` 第1428–1445行。

每帧先做 tight 再做 relaxed 的 Hungarian 一对一匹配。只要 motion 结果非空，后处理直接 `edges = motion_edges`，覆盖经过 ILP 的原边拓扑；原边的概率仅作为新代价中的 learned bonus 输入。原ILP并非完全无效，概率与候选结构仍有间接影响，但已有分裂拓扑不会直接保留。

已有 B0 普通运行四视频的 `run_stats.csv` 显示替换原边 24995/20161/6010/67249 条；最终分裂parent数51/15/9/27，逐项等于 `safe_divisions_added`。这些是普通运行观测，不能当隐藏评分拆解。

safe-div随后只考虑“已有一个女儿的父节点 + 下一帧无父的孤儿”。源码还要求单向最近孤儿、两女儿各有t+2唯一后继、女儿间距增加至少2.25µm，再过DeepCenter与对称性门槛。门槛限制召回是源码事实；直接放宽是否更好是未知。

未来更明确的单机制候选，是保护有图像和多帧证据的高置信ILP分裂，再在剩余节点上做一对一重连。需要维持下一帧、单parent、每parent最多两女儿和谱系连续性；不能只用“分裂数增加”当成功。此候选本轮 `NOT_RUN`。

## 先校验评分诊断，再按错误优化

B0自带手写proxy的division matcher必须先与官方固定实现逐条对齐，根正在整合官方GitHub源码核验。本文件发现的旧validator计数是程序报告，不能直接视为官方TP/FP/FN。

B0选中tight55的8FOV报告 recovered5542、fragmented136、lost-to-detection73、wrong-association0、divisionTP3/FP1/FN9。稀疏标注意味着“未匹配GT预测点”不是真实FP，“wrong-association0”不是没有误关联，8FOV不是8独立胚胎。对齐官方matcher之后，才应逐例分类分裂缺失、重连覆盖、后继缺失或后处理拒绝；有既有预测时先做评分对照，不需要把完整模型重跑设为前置。

## 不追删节点proxy，也不照抄错误归因

[公开负面案例](https://www.kaggle.com/code/zhincez/the-metric-pays-you-to-delete-nodes)作者称：四片训练film上，短轨长度、检测阈值、按类型过滤组合使proxy由0.9368到0.9495，公开分反而由0.938降到0.934。源码/正文确实这么写，但缺submission ID，分类 `AUTHOR_CLAIM`，未独立复现。作者不能确认隐藏评分差异原因，我们也不替作者下结论。

其唯一代码演示拆开 `J` 与 node-count multiplier，方向有价值；但 `compare()` 用 `abs(ΔM)/(abs(ΔJ)+abs(ΔM))` 作为贡献比例，不是 `J*M` 的精确贡献分解，不能照抄为因果百分比。应分别报告raw edge Jaccard、数量乘子和division统计，或使用明确乘积归因。

## 优先顺序（均未在本轮运行）

1. 先对齐官方评分实现和已有预测诊断，保留B0正式0.946事实。
2. 针对已核验的失败事件，设计“保护可靠分裂拓扑”的单机制候选，并保持B0其余设置一致。
3. 查清断轨与检测遗漏的实际位置后再提出局部恢复，避免全局半径和删轨参数搜索。
4. 次特征TTA插值、补齐D4和只改ILP division权重优先级较低：前两者已有本项目/公开持平或下降信号，后者可能被motion重连重置稀释。

新的训练模型或完整多帧tracking架构需要不同开发、验证与计算预算；本次只读研究不自动启动这些工作。运行日志中的 `ACTIVE`、普通 `COMPLETE`、静态compile和proxy改善都不能代替正式提分。
