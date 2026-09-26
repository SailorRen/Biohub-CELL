# 2026-09-26 公开进展与四天优化方案

结论：XR0 已正式取得 **0.953**。当前排名 **453/3922**，不是模型退分，而是0.953附近竞争密集。本轮公开检索未发现已绑定精确版本且高于0.953的完整公开Notebook；这只覆盖下述目录，不是穷尽全网的证明。建议以XR0为新比较基线，先争取0.954，再争取0.956，不再把公开本复制、全局阈值扫描或未经验证的大补丁当成主线。

本轮状态：只读研究及方案交付。Kaggle创建/运行/训练/提交/最终选择变更全部0；新方案收益 **UNKNOWN**。

## 本队事实与排名差距

OFFICIAL_FACT / MEASURED：比赛Submissions页面与官方API一致，队友[XR0 V1/SV352643547](https://www.kaggle.com/code/dongdongjiaqi/biohub-x138-xr0-score-20260925?scriptVersionId=352643547)，Kernel135797557，submission **56546951**，2026-09-25 17:25:57上海提交，Public **0.953**，API COMPLETE且error为空。下载代码的12个代码单元与本任务冻结XR0一致。实际GPU=true / NvidiaTeslaT4 / Internet=false，镜像为用户请求的原版37c64f…。母版镜像与队友运行镜像不能混写。

排行榜此时第50名0.960、第75名0.958、第100名0.956、第150名0.955、第200名0.954；均是三位小数显示值，不能据此保证一个显示分数对应固定名次。当前团队0.953比此前0.950提高0.003。本轮完整正式列表中未见XD960提交；不将其写成失败或已评分。

取得XR0普通运行的run_stats、日志和ppsweep_selected，仅做小文件只读检查：4个当次可见样本均显式记录repair_fallback=0、deadline_degraded=0；最终nodes合计121219、edges117041，readmitted_nodes1337、gapfill_added_nodes110、safe_divisions_added62。flow计数存在实际活动，head日志记录在lowdet补丁之后加载补丁。ppsweep选择base、held_out为空，符合validator=0。计数可能包含多次处理，不当成独立节点覆盖率。

这些是普通运行证据，不是隐藏评分日志；本轮未重新下载和独立审计完整submission.csv，head实际挂载哈希仍不能由补丁日志替代。正式Public已确认与全面输出验收是两个事实。

## 最新公开代码

目录范围：Code官方API按scoreDescending、dateCreated、dateRun各100项，共162个去重对象；浏览器读取Hotness和Public Score首屏。三份重点Notebook完整源码均下载并逐代码单元AST解析，重点差异有额外语义审查。没有执行公开代码。

| 来源 | 精确版本 | 当前事实 | 对本队含义 |
|---|---|---|---|
| [原x138，现更名Biohub 0.953 LB ORIGINAL](https://www.kaggle.com/code/anvithpothula/biohub-0-953-lb-original?scriptVersionId=351539814) | V1 / 351539814 | Public0.953，文件SHA仍6b655e39…，完全等于归档原件 | 标题变化不是新算法 |
| [Raunak Harmonic Fusion V3](https://www.kaggle.com/code/raunakdey07/biohub-harmonic-fusion-v3?scriptVersionId=352639153) | V5 / 352639153 | Public0.953，普通16m48s；12代码单元，规范化后核心Cell2–9 AST一致。其余差异为注释/docstring/打印及time导入位置 | 没发现超越XR0的算法改动 |
| [optimized-biohub-max-score](https://www.kaggle.com/code/amanatar/optimized-biohub-max-score?scriptVersionId=352554580) | V4 / 352554580 | **当前Public0.953，同时普通运行标Error，1h56m53s**；源码打开validator、扩展扫描及二次重写，增加时间门限 | 更新昨日结论：不能再称新V4无分；但它也没有超过XR0，且普通错误需解释，不能照搬 |

optimized默认页会回退V1/338260673并显示该版0.910，而Best Score链接明确指向V4/0.953。本轮分别打开精确版本核对，保留普通Error与Public0.953并存，不猜测原因。官方API metadata.lastRunTime与页面/提交日期存在不一致，时间结论采用提交条目和现场页面，不用它反推实际运行日期。

## 讨论区增量与反证

读取当前目录首屏3个置顶、17个普通主题；完整获取下列7主题正文与68条评论对象（含删除占位），不是穷尽全部旧讨论。图像附件未独立核验。

- [743222：八项负面实验，9月25日新帖](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/743222)。COMMUNITY_REPORT：作者基线0.948；关闭motion relink和增加Z-flip TTA各0.946，检测0.960为0.946、0.970为0.945，secondary权重0.65为0.945，自训替换0.939。其局部指标提升与Public相反。该结果来自旧栈，不证明x138的XD960必输，更不证明0.965是普适最优；但削弱盲扫阈值、额外TTA、换弱模型的优先级。帖子还指出validator筛样随可见/隐藏test交集变化；XR0明确关闭validator，不能把这个风险说成XR0现存缺陷。
- [742266：重连阶段与局部分数失配](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/742266)。COMMUNITY_REPORT：多个参与者未找到稳定关联提升；一位越过平台的作者强调不能只看总分，应看收益是否被一两个样本驱动。没有提供可直接复现的高分改法。
- [742942：标注错误观察](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/742942)。COMMUNITY_REPORT，非主办方确认；不据此重写GT或将误差全部归因标注。
- [743006：Public/Private分布问题](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/743006)。最新回复只是共同疑问，没有主办方给出的分布结论；私榜是否新成像条件仍UNKNOWN。榜页明确29% Public/71% Private。
- [742131：模型融合](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/742131)。作者弱模型融合未获提升，评论无可复现成功方案。
- [738217：FOCUS3D长讨论](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/738217)。提及检测到标注域的坐标校准、多帧关联、轨迹假设选择；也报告高召回未转化成高Public、稠密伪标签关联失败与超时。不是四天内可直接替换XR0的已验证模型。
- [743146：预训练权重交付问题](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/743146)。暂无回复，记录为未决问题，不推断新规则。

## 新公开仓库方法：有思路，但不能直接叠加

固定来源：[kito 175ad9a5c41596f48b4d3224b4737211e9223998](https://github.com/kito2718/kaggle_Biohub-Cell_Tracking_During_Development/tree/175ad9a5c41596f48b4d3224b4737211e9223998)，最新commit上海9月26日13:21。取得summary2/3及052/054完整Notebook文件，针对新函数与调用链审查，未做全仓或全部函数语义审计。

AUTHOR_CLAIM：[summary3](https://github.com/kito2718/kaggle_Biohub-Cell_Tracking_During_Development/blob/175ad9a5c41596f48b4d3224b4737211e9223998/s7_summary/s7_summary3.md) 更新049边界Z校准Public0.948，低于其041b基线0.949；048形态成本与其他补丁组合出现负交互。052漂移补偿报告四个可见样本局部Jaccard0.89404→0.92426，053几何关联局部分数不变，054分裂修复0.92429。052/053/054正式记录仍PENDING；文中0.960+、0.972+是目标，不是Public。仅依据作者文档，未独立验证其账号正式结果。

SOURCE_CODE_VERIFIED：052用每点至多3近邻产生位移候选，逐候选统计2.5µm内一致集，估计全局位移并以0.35µm软收缩，重新定义匹配门限。该实现全候选一致性扫描最坏呈二次增长；其旧管线没有XR0的V1284/seed-flow/readmit/gapfill链。XR0已有局部邻域flow，flow存在时以source+flow预测，仅缺flow才使用velocity。把全局drift直接再加到当前预测或历史速度上可能重复计算运动，不能以旧基线局部+0.03推导XR0收益。

SOURCE_CODE_VERIFIED：054在有一个子节点的父节点上补第二条边，使用平均密度350、父历史及双子存活15帧、第二子位移6–11µm、姐妹8–13µm及角度145°等固定经验筛选，每视频上限12。它覆盖写safe_divisions_added统计，会混淆已有修复计数；强密度假设与几何门限没有跨域保证。“无退步/安全”是作者在小样本上的描述，不是本队可接受的普遍证明。

[Junhao仓库](https://github.com/JunhaoLiXD/Biohub_Cell_Tracking/tree/e8f233cddecde45e66d75ab5f39878541a54fce7)最新仍为昨日固定commit，没有新Public证据可据以升级方案。

## 重新优化：以可证伪的关联改动为主

以下均为INFERENCE / 待执行方案，**不是已证明提分**，也不是本轮新增平台额度授权。

1. **固定XR0为0.953比较基线。** 保存本次精确SV与源码；保留A、现有最终选择。先复核已有XD960运行/提交状态，有ID只回收，没ID不把它算作已测。XD960仍可完成原有单因素问题，但不将其预设为主攻方向，不扩展阈值网格。
2. **优先审查并验证“多帧关联歧义”候选。** 保持检测节点、坐标、head、flow、gapfill及所有原阈值。只在相邻轨迹竞争同一目标、两种连接代价接近时，比较连续3–5帧的运动一致性；只允许有明确双向/轨迹证据的成对边交换，保护既有分裂和一父至多二子。没有竞争证据则原样返回，不全局替换Hungarian、不全局增加drift。
3. **先用已完成XR0的缓存/轨迹定位，再决定是否值得占正式名额。** 当前普通统计证明模块在工作，但不足以定位错误。最小诊断应列出换边候选、前后局部轨迹、逐视频edge/division/节点数指标，以及低密度/高密度子组；稀疏GT下未标注不等于错误。训练集proxy只作淘汰与解释，不声称独立泛化CV。初步候选不得改节点数；若后续短轨过滤使节点集变化，必须另列实际差异，不能继续声称输出节点不变。
4. **备选仅为分裂候选的时间持续性判别。** 在原有DeepCenter和几何修复之间检查母/子时间历史与二女存活，不照搬“密度350意味着不分裂”或固定Z规则。只有实际病例表明当前拒绝/误接发生在这一步，才构建独立候选；不与关联交换第一轮叠加。

建议节奏：9月26日完成缓存病例与最小实现，第一轮最多两个独立候选；9月27日回收正式分再决定第二轮，只有可解释且超过0.953才晋级；9月28日集中验证胜者和鲁棒性；9月29日留足普通运行、正式队列和工程修复缓冲，停止新增大结构。截止上海9月30日07:59；实际队列时长与余额需在执行时重查，8小时不是保证。此处是计划，不创建后台监控或自动提交。

不建议本阶段启动新检测器训练、全局Z-flip TTA、弱模型平均融合、固定Z边界移动或validator大扫描。理由分别是四天内验证成本、已有负面反例、与XR0已有模块重叠及缺少高于0.953的正式证据。它们不是永久无效结论。

## 证据与限制

来源与字节哈希：`research/PUBLIC_UPDATE_20260926/source_manifest.json`；三排序原目录、7讨论全文、源码及diff、team_submissions、XR0_scored_readback、普通运行摘要及leaderboard均在同目录。截图/目录卡片仅用于发现，关键分数已核对版本页或正式API。本轮没有把Public解释成私榜保证，没有声称新候选能达到0.956。
