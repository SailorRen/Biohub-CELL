# 2026-09-25 公开方案增量检索

结论：本次覆盖范围内发现新的公开实验代码，但没有找到比已归档 x138 更高、且绑定精确版本正式分数的新完整公开方案。这不是对全部公开区的穷尽证明。

## 范围与证据

只读查看比赛 Code 的 Hotness、Public Score、Recently Created、Recently Run 各首屏20项（有重叠），Discussion 首屏，GitHub `biohub tracking` 按更新时间前15仓库。下载4份 Kaggle 源码做静态解析及比较；新仓库仅针对相关记录和函数深读，没有运行外部代码。没有创建、保存、运行或提交 Kaggle 对象。

- MEASURED：[x138 V1/SV351539814](https://www.kaggle.com/code/anvithpothula/biohub-x138?scriptVersionId=351539814) 今日页面 Public 显示 **0.953**，只有V1。下载SHA256为 `6b655e39bbfd2d3d6c762badea69847d3f00f5b548f385cb01b07ee2600fde6d`，与昨日归档相同。
- SOURCE_CODE_VERIFIED：本次下载 Kunal 的12个非空代码单元与 x138 逐单元AST相同；不应算第二套独立优化。文件哈希不同不代表算法不同；此项不验证镜像、输入、权重或运行等价。
- MEASURED：[optimized-biohub-max-score 最新V4/SV352554580](https://www.kaggle.com/code/amanatar/optimized-biohub-max-score?scriptVersionId=352554580) 页面明确报错；0.910属于V1/SV338260673，不能给新V4背书。其新源码有指标导向扫描及时间控制，尚不能列为成功方法。

## 今天新出现的实质方向

固定源码：[kito c2534353](https://github.com/kito2718/kaggle_Biohub-Cell_Tracking_During_Development/tree/c2534353f19ab31da03fa2f49bdd823116543bd6)。读取 README、summary相关章节和048/049针对性源码；不是全仓审计。

1. **049：低密度孤立边界节点坐标校准。** SOURCE_CODE_VERIFIED：排除高密度样本，对孤立节点使用原图局部亮度峰更新坐标。重要限制：文档说上下边界，但实际更新分支仅处理 `zi >= 57`，并含 `64`、`61` 等固定Z位置；并非通用上下边界校准。不能照搬其“零风险”表述。
2. **048：3D形态关联成本。** SOURCE_CODE_VERIFIED：在关联成本加入体积、亮度、形状差异，默认权重0.30。作者报告4胚GT 0.89404→0.89365，轻微下降；不能只看“新算法”就优先投入。
3. **043c：Hermite 2–4帧断轨补全。** AUTHOR_CLAIM：summary记录独立实验正在评分；此次未读该版本完整实现，未确认新Public。

[作者实验记录固定版](https://github.com/kito2718/kaggle_Biohub-Cell_Tracking_During_Development/blob/c2534353f19ab31da03fa2f49bdd823116543bd6/s7_summary/s7_summary.md) 中049局部指标0.89404→0.89492（+0.00088）、048提交56536655、049提交56538283均是 **AUTHOR_CLAIM**，记录状态PENDING。本次未独立登录对方提交历史，不把它们说成当前已受理或得分。作者050 DivNet记录严重负结果并暂缓提交；同样不是独立复现。

## 排除的“新高分”线索

- [Junhao exp064 固定记录](https://github.com/JunhaoLiXD/Biohub_Cell_Tracking/blob/e8f233cddecde45e66d75ab5f39878541a54fce7/experiments/exp_064_x138_verbatim_repro/experiment.json)：全读experiment.json及review.md。原样复现x138，作者记录56535761尚PENDING。文中0.956是原作者榜上成绩，不能归到公开x138或这次复现。README局部指标0.953587也不是Public。
- [pathik README](https://github.com/pathik1511/biohub-cell-tracking/blob/196d2e358faa8efacd7c3630e6cdc2fb747a877b/README.md)：README_ONLY；最新更新为排名徽章，竞争方案明确未公开。
- [alvaro RESULTS](https://github.com/alvaromendizabal/biohub-cell-tracking-during-development/blob/0676d815383b63605b6d5afc9aa6f74002763219/RESULTS.md)：全读结果记录；多帧关联还在数据准备，核心新代码未发布。当前是负面实验经验，不是可直接使用的高分实现。
- [公开讨论742266](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/742266)：作者报告十次小改动未成功、局部指标改善也曾导致Public下降。属于COMMUNITY_REPORT，不能推广成任何改动都无效；未发现可绑定精确版本的新高分代码。

## 对本队的含义（INFERENCE）

优先取得现有X0/X25的正式结果；仅凭本轮信息，没有理由另开大量阈值微调。边界校准是最值得进一步源码审查的新增方向，但其固定尺寸假设、与x138已有V1284坐标校准的交互、以及正式成绩都未解决。暂不直接叠加。若X0复现失败，应先解释输入、环境或运行降级差异，不能把新补丁当成补救证据。

本轮没有修改母版、原提交账本、最终选择或任何运行配置。来源清单及字节哈希在 `research/20260925_public_update/source_checks.json`。只证明检索和静态观察，不证明独立复现或提分。
