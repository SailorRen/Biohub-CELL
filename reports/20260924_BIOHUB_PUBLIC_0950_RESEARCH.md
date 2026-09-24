# Biohub 公开高分方案更新（2026-09-24）

## 结论与证据层级

已找到公开 **0.953** 方案，超过用户当前0.950基准；不是只有标题写高分。两个不同作者的精确Notebook页面均显示Public Score 0.953。它们12个非空代码单元AST一致，属于同一方案家族，不能计为两种独立创新。当前分数为平台页面观察（OFFICIAL_FACT），不是本队复现或因果消融结果。

| 作者/方案 | 精确版本 | 页面Public | 源码覆盖 |
|---|---|---|---|
| [Anvith / x138](https://www.kaggle.com/code/anvithpothula/biohub-x138?scriptVersionId=351539814) | V1 / SV351539814 | 0.953 | 全文件已取得，12代码单元；关键路径定向阅读 |
| [Kunal / Biohub Cell Tracking](https://www.kaggle.com/code/kunaldesale2408/biohub-cell-tracking?scriptVersionId=352321925) | V10 / SV352321925 | 0.953 | 全文件已取得，13代码单元，其中1个空单元；12个有效单元AST与x138一致 |

完整源码取得不等于逐函数审计；本轮没有宣称FULL_NOTEBOOK_SOURCE_READ。源文件SHA256、机器比较结果和官方CLI元数据见同目录evidence.json。下载源码只做解析，没有执行。

## 最新可用性变化

[x138新增坐标头输入](https://www.kaggle.com/datasets/anvithpothula/biohub-v1284-head-s075)：当前页面可见V1、v1284_head.pt、33.91 kB、CC0 Public Domain。作者在x138评论区约10小时前声明已经公开；之前两条评论确实指出私有输入阻止复制。因此旧的“缺私有head”阻断已出现实质变化。尚未下载权重、核验其SHA256或测试挂载；不能声称端到端复现条件全部通过。

## 实际源码中的新方法（SOURCE_CODE_VERIFIED）

1. **学习式坐标精修 + 连续坐标特征采样。** 冻结原编码器，中心及六个轴向邻域特征构成224维输入；224→32→3小MLP预测位移，使用2δ/(1+||δ||)限制位移幅度低于2微米。关联特征采用三线性采样，保留浮点坐标。不是只改velocity。作者代码注释称在20个训练影片/4136配对上训练并有局部距离改善，这只是AUTHOR_CLAIM，不是Public消融证据。
2. **邻域运动场。** 从可靠匹配种子估计邻域位移中位数，默认12邻居、40微米半径，样本不足回退原速度预测，用于关联门控/代价。
3. **恢复真实检测和断轨修复。** 对开放轨端重新接纳被ILP丢弃的高置信检测；从真实低阈值检测池填补最多3帧间隙，默认不生成合成点，新增节点比例上限3%。不能把这简化成任意补点。

重要实现顺序：坐标头补丁须在低阈值检测缓存补丁后应用；原作者注释指出相同锚点替换可能导致gapfill静默失效。本轮仅阅读，未更改。

相对本队A，x138也改变了检测阈值（0.965）、DeepCenter安全分裂阈值（0.25），关闭验证选择器并固定tight55等；不存在“只加head便必然+0.003”的证据。原可见运行约20分28秒、Kunal约23分34秒，均不是隐藏集耗时保证。输入涉及Primary、Secondary、DeepCenter和新head；未使用本队gate Notebook。后续须逐项冻结该方案实际输入版本，不能直接复用A的输入版本假定一致。

## GitHub检索结果与限制

通过GitHub仓库搜索（biohub cell tracking，更新排序，最多30条）、代码搜索0.950/0.953及README的0.95线索检索。未找到能在本次阅读范围内绑定当前≥0.950平台结果的新GitHub独立实现；这不证明整个GitHub不存在。

以下5个仓库完整README已读，固定提交在evidence.json，代码未审计：

- [pathik1511](https://github.com/pathik1511/biohub-cell-tracking)：近期更新，但竞争方案明确私有；公开的是基础设施/基线。
- [kito2718](https://github.com/kito2718/kaggle_Biohub-Cell_Tracking_During_Development)：StarDist/Cellpose与跟踪路线，0.96/0.982是目标，不是当前Public证明。
- [alvaromendizabal](https://github.com/alvaromendizabal/biohub-cell-tracking-during-development)：README报告0.947（56376695）；新方向为冻结编码器、训练多帧关联头，尚无已验证高分。
- [JunhaoLiXD](https://github.com/JunhaoLiXD/Biohub_Cell_Tracking)：README报告0.944（56105868），局部运动改进不能当新Public分数。
- [Caffeinated-Code](https://github.com/Caffeinated-Code/biohub-cell-tracking-learning)：学习用基线，竞争策略未公开。

另做定向README检索，未全读长文，不计深读：naveenlx111-svg/Biohub @2766d038a57e98598d645f5348e95a32824ad0bc 的0.95是目标；Acceleratorer/Biohub-Cell-Tracking-During-Development- @c7c1898997f4156306df0c913e5c83f4cd8457cf 的0.966/0.970包含9月9日旧快照、文件名和未评分候选，不能视为当前高分；sshotanak226-svg/biohub明确区分本地CV和Leaderboard。未获得vietnq仓库README（404），保留缺口。

## 公开讨论与用户截图

- [9月24日标注问题讨论742942](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/742942)：已读正文及3条评论，有选手报告位置/分裂标注错误；属于COMMUNITY_REPORT，无主办方确认或统计复核，不能据此解释本队0.948或修改规则。
- [Luxar/3D Gaussian Splats讨论742777](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/742777)：正文及0评论已读；[官方Luxar](https://github.com/royerlab/luxar)是科学数据可视化工具，不能当作新的0.950跟踪模型。
- Kaggle Code检查默认热门与Public Score排序的可见首屏，未遍历所有页；Discussion检查Recent Comments首屏。没有对榜上所有0.950选手逐一溯源，也不能由同分推断使用同一方案。
- 用户截图两条V0375显示Succeeded/0.948；L020P显示Notebook Threw Exception，没有分数，不能算作0.948失败消融。截图未提供精确submission ID，未伪造。

## 下一步建议（未执行）

优先完整复现固定x138原版，先确认新head及其余输入的精确版本/权限/环境，再考虑独立消融；降低继续velocity/leaf阈值试探的优先级。这是基于公开0.953与另一账号同代码0.953的工程优先级判断（INFERENCE），不是保证本队复现必达同分。保留当前A及最终选择。若以后拆分研究，先处理坐标头与连续特征采样的一致性，避免一次叠加多个未经分离验证的补丁。

## 本轮边界与交付

仅公开资料读取、源码静态比较、研究文档Git同步。Notebook创建/保存、CPU/GPU/Colab会话、推理、训练、提交、共享修改均为0；无权重、原始数据、CSV或凭据入库。隔离分支codex/public-0950-research-20260924，基于7cdcdb43deb333a273ff7621808ab766170937b9；不修改CPU研究分支和原实验账本。结论不代表模型实验完成。
