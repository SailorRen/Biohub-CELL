# Codex：DF960 单候选、一次正式提交

仓库：SailorRen/Biohub-CELL；执行分支：codex/df960-one-shot-20260921；起点：33921079143d162fb09bef1813dca8241fae86b1。
任务／实验 ID：BIOHUB_DF960_20260921_V01。用户本轮已授权必要开发、候选运行及一次正式提交；目标是今晚送入正式评分，2026-09-22 再读结果，不是再做一批诊断。任务文件存在不代表已执行。

## 1. 今晚的唯一方案

候选 **DF960 = 已正式出分的 D960 生产链 + 已正式出分的 F1 邻域运动补偿**。相对 D960 只增加 F1 的位移预测，检测阈值保持0.960，不进一步降阈值，不组合其他改动。D960／F1在团队 Public Score 排序中分别第一／第二，显示均0.948；这是选择本次实验的依据，不是组合必然提分或精确分差已知的证明。

固定来源，按需读取，不重读全仓库：
- D960：submission56416049，V1／SV351441983。源码固定1cf89f1f9380f005d98e9cb15ca9f5d80c4ebaca下 `experiments/BIOHUB_SCORE_TRIO_20260921_V01/D960/candidate.ipynb`，SHA256 `b12568e27ea5a8c66942a6301c2c80d037fdffe43f338a23a86266f80a02d192`；输入与权重沿用该批 `batch_manifest.json`。
- F1：submission56375774，V1／SV351084196。参考8f18a8dd83146d6399b296ff54c4176c300724b5下 `experiments/BIOHUB_F1_FLOW_KAGGLE_20260918/flow_patch.py` 和 `build.py`。注意该commit的 `formal_score.json` 仍是旧NOT_RUN，不能用它证明正式版本绑定；从已有本地回执或平台精确SV读取正式生产源码，核对实际flow函数及配置，忽略无关metadata／日志差异，不重新诊断整本。
- 已出分证据：起点commit下 `reports/20260921_BIOHUB_SCORE_TRIO_V01.md` 及同批 `public_score_order.json`。保留G1／D960／F1原版，不重跑、不重提、不改最终选择。

## 2. 公开思路与一次短补查

Chat本次在线访问Kaggle Code／Discussion未取得正文，不能称为完成9月21日全量增量调查；已读取以下归档，并实时核对Junhao公开main仍为e6fb6739b290b938717076b32d01a86eb462380d，所读STATE尚无exp060新评分。现有证据已足以选择DF960；不要另起研究任务。

|来源|实际证据与今晚的取舍|
|---|---|
|[公开flow2 V1／SV350702651](https://www.kaggle.com/code/thtennant/biohub-frontier947-flow2-det096-v1?scriptVersionId=350702651)|9月18日原始源码归档记录det0.96＋邻域中位位移，但还改了关联门槛、关闭validator；正式Public未知。不照搬整本，只取已经本账户F1跑分的运动补偿。|
|[训练覆盖讨论742064](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/742064)|9月20日归档核对secondary manifest train199／test40交集40；不把该探索集上涨作为今晚提交门槛。|
|[Junhao STATE](https://github.com/JunhaoLiXD/Biohub_Cell_Tracking/blob/e6fb6739b290b938717076b32d01a86eb462380d/STATE.json)|分裂门槛0.18／0.22仍是待结果计划；本账户A18／B22已有0.948记录，今晚不重复扫它。|
|新MLP／XGBoost及“0.95”标题|9月20日归档未核验正式提分，部分私人依赖不全、评价对象不一致；今晚不引入新训练／新权重。|

归档固定6ec61f54cd5fb5b93fe7cd1dbc37b01a8e41bc57：`research/PUBLIC_INTEL_20260918/sources.json` 的N02，以及 `research/PUBLIC_INTEL_20260918/update_20260920/最新公开情报.md`。保留公开来源署名，不把作者主张写成独立实测。

本地Codex先用已有登录态工具短查最近24小时Code／Discussion更新及flow2页面，最多10分钟，只找与本候选直接相关的新实现或明确负面结果；在最终报告记少量来源、时间、结论即可，不设阅读数量门槛。无新证据或页面不可读就沿用上述已读来源继续；若出现直接否定DF960的新正式结果，先核实，不盲交同一失败方案，也不私自展开第二候选。

## 3. 实现：只移植运动补偿，不扩大参数搜索

以D960为母版，在原有motion后处理调用点安装正式F1中的一轮邻域位移预测。参考实现配置为k=12、半径40µm、排除距离1.5µm、全局种子至少4条、iterations=1；以精确SV核对后的正式F1实现为准，若不同只记录实际差异，不凭旧报告混装函数与配置。

种子来自D960未修改的motion函数在**当次0.960检测图**上的tight边；排除自身，取近邻位移中位数修正预测位置。种子不足／无有效近邻时走原回退。不得拿旧0.965节点／边缓存替代当前图；保持µm坐标、时间方向、原代价、Hungarian分配、距离门槛和冲突处理。原分裂／gap／短轨救援／TTA／模型／权重／输入不变；不加入H30、S50、A18/B22或更宽松的flow关联门槛，不直接编辑CSV。

原生产选择器逻辑与候选集合保留，不新增扫描；新图引发原选择器选项变化则如实记下。隐藏运行必须对当次输入重新生成正确结果，不能硬编码普通输出。复用现有构建、平台调用和输出检查工具，路径／参数按真实接口适配，不复制整套框架。

## 4. 最小检查后直接生产与提交

仅做代码解析、补丁启用／禁用、无邻居回退、坐标／端点等短CPU测试。复用已有同输入合法图缓存核对关闭flow时恢复原D960运动逻辑；没有缓存也不额外跑G1／D960整套GPU对照。不要增加8视野诊断、训练集评分、交叉验证、仪表盘或错误归因项目。

安全同步后先核对账号sailorren、比赛 `biohub-cell-tracking-during-development`、团队实时剩余名额及算力，并查是否已经存在本候选或请求。计划私有slug：`sailorren/biohub-df960-flow-20260921`。已运行者续接、已提交者只查分，不重复创建。上海午夜不作为配额重置的假定；本轮无论跨日与否始终最多一次正式请求。

源码／简短配置在启动前同步并回读一次。启动一个生产Notebook；继续复用现有前台等待／续接工具，普通COMPLETE后立即回收**该精确Version／SV的实际最终CSV**，核对模型正常加载、det0.960和flow实际消费、schema／样本覆盖／有限坐标／图端点与时间／官方reader往返、内容与已提交版本非重复。只需小型摘要，不以完整报告或辅助分数为前置条件。

合格即走现有Notebook正式提交入口，绑定精确Version／SV／输出文件。先记唯一请求，发送一次，保存并回读submission ID。响应不明先只读对账，不盲重试。纯无效补丁、非法输出或完全重复则不浪费唯一名额，报告直接证据；输出差异不冒充精度收益。不要停在“方案已写好”或“普通COMPLETE但没提交”。

## 5. 本轮预算与收口

预算：一个新私有Notebook；一次计划Save & Run，另最多一次明确工程故障修复备用（仅同一候选，非算法调参）；**正式提交请求累计最多1次**，失败／响应不明也计数。先扣已发生请求。不得挪用旧三臂修复额度或把每日刷新当新授权。训练、Dataset写入、额外GPU诊断、其他候选、最终选择修改均0。

取得正式ID后只确认一次接收状态，今晚不等Public、不以缺分数重跑。2026-09-22续接时仅查该ID的正式结果，与D960／F1／G1同窗记录原始Public和排序；显示持平仍记PUBLIC_TIED，未知同分规则不能证明精确提分，Private未知。本文件不建立后台定时器，不承诺明天一定完成评分。

只用 `experiments/BIOHUB_DF960_20260921_V01/` 保存候选、必要diff／短检查和唯一请求账本，结果写 `reports/20260921_BIOHUB_DF960_ONE_SHOT_V01.md`，来源与结论并入同报告。不另建合同／验收框架；仅回读新增小文件一次。数据、权重、完整图、submission.csv、凭据不入库。不覆盖用户工作区、不reset／stash／强推，不改main或已完成三臂记录。

最终直接报：是否已正式提交、Version／SV／submission ID、实际CSV检查、原始Public／观测时间、实际预算、固定报告commit。未取得ID绝不写SCORE_PENDING；仅任务或代码同步绝不写Kaggle执行完成。发生真实资源／平台阻断则保留精确身份和下一步，不编造今晚已经提交。
