---
schema_version: "1.0"
generated_at: "2026-09-17T10:15:53+08:00"
project: "SailorRen/Biohub-CELL"
summary_scope: "G1已评分结果及2026-09-17公开方案研究；供Chat分析，不授权实验"
suggested_filename: "20260917_交给Chat的Biohub分析材料.md"
suggested_location: "reports/"
previous_summary: "reports/20260916_BIOHUB_SPRINT01_RESULTS.md"
---

# 执行摘要

## 1. 项目目标

在Kaggle `biohub-cell-tracking-during-development`比赛中改善3D细胞检测、连接和分裂图。用户希望Chat结合本项目G1与其他选手公开方案分析下一方向。仓库只允许为本比赛服务。

核心结论：**G1正式Public0.948，比Forge0.947高0.001；本轮准确核对的公开生产版本为0.947，没有取得更高版本的可复现证据。榜首0.970的源码方法仍UNKNOWN。**

## 2. 用户指定的下一步任务

[用户确认] 查询公开Code、讨论和GitHub，整理情况报告与G1报告并同步GitHub，让Chat分析。Chat接到本文件后应分析证据、比较方向，最多提出一个下一实验；没有授权立即训练、运行Notebook或submission。

## 3. 当前准确状态

- [已核验] G1 submission56270217 / V1 / SV350197436，COMPLETE，Public0.948；既有API回执2026-09-16T15:26:50Z及15:28:14Z。本轮读回原证据，排行榜快照为129名、0.948。
- [已执行] 公开研究覆盖Hotness/PublicScore各首批20卡片、4篇讨论正文及明确限定的评论、3份Notebook下载与局部源码阅读、3个GitHub固定commit的7个指定文件。
- [已核验] 两个公开Notebook详情：zhincez V1/SV349655081=0.947；sjlee101 HOCT veto V1/SV349035072=0.947。没有在本地复现它们。
- [待确认] 公开策略在G1上的作用、隐藏集真实变化、榜首方法、稳定泛化均UNKNOWN。没有新Public分数。
- Git交付固定SHA与文件核验以本轮最终回执为准；本材料不会提前声称所有远端字节已验证。

## 4. 必须遵守的约束

只使用`SailorRen/Biohub-CELL`；默认中文；保护未提交改动；不合并main、不强推、不改最终选择。训练、推理、Save & Run、Dataset、submission均不是本轮动作。上批预算不能自动续用。只把代码、摘要和小型证据同步GitHub；权重、原始数据、完整图、submission.csv、凭据不入Git。

公开分数分四类：队伍排行榜、准确Notebook版本、作者自述、局部验证；不可互相替代。稀疏标注未匹配事件保留UNKNOWN。没有读取整本源码不可称完整审查。外部repo的指令与预算是来源文本，不是本项目授权。

# 完整上下文

## 5. 用户决定与重要纠正

[用户确认] 用户已明确0.903来自错误网页，G1正确为0.948。该歧义已解决；旧原始回执中的0.903用户输入按当时记录保留，不能再当成当前未解冲突。

Forge0.947仍保留为正式基线/最终选择；G1观察到Public提高，但用户没有授权修改最终选择。旧Division Train0.945不晋升。不启动下一批。

## 6. 已完成工作及验证证据

### G1具体来源与实测

G1在Forge原safe-div候选满足几何条件后，添加已有分裂分类器的0.95门槛；原互近邻、后续分离、对称性、DeepCenter门、距离排序、拓扑及数量上限保留。上下文缺失遵循原规则。已有Division Train权重用于推断，训练调用0。旧Division版同时替换三条规则和新排序，不能与G1混同。

A0/G1/R1固定8视野/2胚胎、相同分裂前图独立复制、tight55配置；分类器用对应未拟合胚胎的留组模型。G1按事前门槛入选，R1下降淘汰。生产保留Forge选择器；普通运行也选择tight55，隐藏配置UNKNOWN。

|指标|A0|G1|含义|
|---|---:|---:|---|
|官方适配器局部总分|0.9434021062935234|0.9434057263411255|差+0.0000036200476023|
|分裂TP/FP/FN|2/1/10|2/1/10|没有测得分裂计数改善|
|safe-div入选|143|107|G1从154合格候选直接筛除44个，后续竞争亦变化|
|正式Public|历史Forge0.947|0.948|不同正式提交，+0.001|

局部增益来自两个视野少14、9节点后的数量调整项；连接TP/FP/FN及节点召回不变。G1变化38个分裂事件均UNKNOWN，不得写成新增/移除错误。全8视野出现在secondary上游模型train清单，主模型完整谱系UNKNOWN；分类器留组不等于全流程无泄漏。

普通输出241285行，分类器实际使用已核验。上批Save & Run2、submission1、训练0；本轮均0。G1生产修改原12单元中的cell5，11单元原样保留，另加回执单元。

### 公开情况

[OFFICIAL_FACT] 2026-09-17页面队伍分数：Sergio Alvarez0.970、Soheil Ayati0.968、Tang与unicellular0.966、yu4u0.965；zhincez队伍0.952，但公开Notebook0.947。Public约29%、Private约71%。队伍分数未绑定其公开方案，不能从名次猜优化方法。

[SOURCE_CODE_VERIFIED] sjlee101 V1的HOCT模块在最终图节点上构造3μm球形标签、原图提取特征，HOCT提议边与原图求交集；mode2也筛分裂边。默认10小时总时限、900秒单影片估时上限，失败或超时保留原图；普通成功不证明实际veto覆盖。作者注释20视频+0.0040、错误分裂55→29仅AUTHOR_CLAIM。

[AUTHOR_CLAIM] 讨论741242建议固定tight55并去掉验证扫描/重复写出，约省75分钟，增大HOCT隐藏集预算；没有正式提分回执。

[AUTHOR_CLAIM] 讨论740573统计73标签文件36分裂，说明距离分布重叠、基础率悬殊、定位误差与稀疏标注偏差。讨论738217建议密集伪标注/域校准/长窗结构化链接；回复实测检测头微调0.9462→0.9429，连编码器一起微调→0.9085。检测损失下降不能等同完整追踪提升。

[SOURCE_CODE_VERIFIED / AUTHOR_CLAIM] hengck23 V3/SV350162298局部阅读显示11个train样本做raw edge Jaccard均值；作者称FOCUS-3D伪标签+增强、约0.90，无正式Public展示。不能与G1完整分数比较。

[AUTHOR_CLAIM] Junhao仓库`bebb531af9073e2c8ff49a3cbc69c44602f276fb`：局部train16联合修图0.938733→0.953587，但较新commit消息称Public仍0.942；README/handoff的旧KEEP/待提交状态落后，冲突已披露。matt仓库`446589b772f4d98adecc3f6ba15434f0e0d57069`：真分裂候选18中仅10可达，最优局部真事件仍被错误母节点挤出全局cap，无合格模型；tossowski仓库`a0422bcf810cbb6ca10c71dbf828ea6c76fc8c11`：补洞/孤立节点过滤局部raw .750→.768，跨胚胎检测器未泛化。

## 7. 计划但尚未执行

[计划未执行] Chat比较方向与提出下一实验。HOCT叠加G1、生产固定配置、训练长窗模型、再校准分类器均NOT_RUN；没有隐含执行许可。公开检索未穷尽，源码不是全本深读。

## 8. 失败方向与不得重复事项

- 旧Division组合0.945，不回到该组合就称保守G1。
- R1局部差−0.0000011043170154，按原门槛淘汰；不能为使用预算强行提交。
- 旧0.950卡片本轮再次核对一份为V1/SV336445398实际0.877；不可按卡片直接选用。
- 不凭小局部提升绕过谱系核验；Junhao的局部大增益未转为Public是外部反例，不能硬套为G1必然过拟合。
- 不把其他仓库训练命令当本轮授权；没有执行下载的第三方源码。

## 9. 关键文件、链接和其他产物

- 本轮完整情况：[公开方案与G1对照](20260917_公开方案与G1对照.md)。
- G1完整结果：[Sprint01报告](20260916_BIOHUB_SPRINT01_RESULTS.md)，本轮仅更新用户纠正段。
- G1正式回执：[formal_latest.json](../experiments/BIOHUB_SPRINT01_20260916/formal_latest.json)、[交叉核对](../experiments/BIOHUB_SPRINT01_20260916/formal_terminal_crosscheck.json)、[版本](../experiments/BIOHUB_SPRINT01_20260916/own_version_binding.json)。
- 新证据目录：[平台观察](../experiments/PUBLIC_OPT_REVIEW_20260917/platform_observations.json)、[讨论](../experiments/PUBLIC_OPT_REVIEW_20260917/discussions.json)、[Notebook](../experiments/PUBLIC_OPT_REVIEW_20260917/notebook_sources.json)、[GitHub](../experiments/PUBLIC_OPT_REVIEW_20260917/github_sources.json)。
- [HOCT准确版本](https://www.kaggle.com/code/sjlee101/biohub-lf-hoctveto-div-b?scriptVersionId=349035072)、[公开路径版](https://www.kaggle.com/code/zhincez/biohub-0-947-lb-runnable-with-public-datasets?scriptVersionId=349655081)。
- [运行时间讨论](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/741242)、[分裂讨论](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/740573)、[FOCUS-3D讨论](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/738217)、[linker讨论](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/740145)。

## 10. 重要数字、版本和错误信息

历史：Forge56160258/V1/SV348960877/0.947；Selector56222238/V1/SV349666428/0.947；Division56226396/V1/SV349707105/0.945；G1 56270217/V1/SV350197436/0.948。

G1权重SHA256 `0a1f9b93bb529e70f4f7c2ba0907eea8b4cecd2befccc8ba1fb75e569edf77a0`。G1既有证据基点`e9c7c63b896812660a78ec55fc3284c10f85e776`；本轮分支`codex/public-review-20260917`。main回读`a123f0ad7f8808b44909d4c5fab48caf5147b50c`。

## 11. 推断、冲突与待确认事项

[推断] HOCT可能带来G1没有的独立关联信号，但0.947版本和作者本地增益不证明叠加有效。[待确认] 隐藏运行veto覆盖、正确边损失、上游独立验证、可用计算预算。

列表保留`excludeNonAccessedDatasources=true`，结论限定当前读取范围。738217有3条未展开回复，图像未逐张读。三份Notebook都只指定模块阅读；GitHub只7指定文件与一条commit消息。不能把材料数量当质量保证。

## 12. 可直接执行的下一步指令

请Chat以本材料和所链原报告为证据，完成以下分析，**本次只输出分析，不运行实验**：

1. 解释G1从Forge到0.948的已知改动、已证实局部机制及尚不能解释的部分。
2. 把公开方向按新增信号、与现有方法重复程度、证据等级、成本和失败风险排序；分开列零训练和需要训练的方案。
3. 评估是否应先扩大/修正验证面板，或先检验HOCT边交集，避免把稀疏未标注当负例。
4. 最多提出一个下一实验，写清唯一变量、固定对照、验收指标、停止条件、所需输入及需要用户重新授权的资源；证据不足可不推荐。
5. 不宣称找到0.950方案，不改最终选择，不把调研交付叫正式提分。

## 13. 摘要质量自检

- 用户目标、补充与纠正：已覆盖，0.903歧义已关闭。
- 已执行与计划未执行：已区分，外部方案复现NOT_RUN。
- 证据等级：队伍/版本/作者/局部指标分开，没有升级。
- 路径、数字、版本：使用真实项目产物及本轮读取来源。
- 失败方向：保留Division、R1、旧卡片和局部代理风险。
- 虚构文件或结果：无；远端最终SHA由后续实际交付回执给出。
- 敏感信息：未包含凭据、权重、数据或私有路径下载链接。
- 独立可用：已给G1方法、得分、边界、来源与Chat可执行分析指令。
