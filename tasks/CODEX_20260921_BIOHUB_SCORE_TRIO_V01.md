# Codex执行任务：D960 / H30 / R00 三臂正式评分

任务ID：BIOHUB_SCORE_TRIO_20260921_V01
日期：2026-09-21；记录UTC与Asia/Shanghai时间。
仓库：SailorRen/Biohub-CELL
独立分支：codex/score-trio-20260921
任务路径：tasks/CODEX_20260921_BIOHUB_SCORE_TRIO_V01.md
实验目录：experiments/BIOHUB_SCORE_TRIO_20260921_V01/
报告路径：reports/20260921_BIOHUB_SCORE_TRIO_V01.md
本文件是新增批次的执行任务，不是任何候选已运行或已提分的证明。

## 1. 新批次授权和预算

用户在S50/G58正式评分期间报告当日提交额度已更新为5次，要求继续上传几个方案验证。本批据此只新增D960、H30、R00三个独立候选，不等待S50/G58出分，不组合尚无分数的新改动。

硬上限：新私有Notebook 3个；Save & Run计划3次加全批共享工程修复备用1次，总计最多4次；正式submission请求最多3次，每臂最多1次。失败或不明响应计账，不盲重试。训练/fit、Dataset创建更新、最终选择修改、已有Notebook修改取消或重提均为0。

当平台实际剩余为5次时，本批用至多3次，保留2次给后续决策；若S50/G58或其他提交已计入当前窗口，按实际余额收缩，不把每日上限当余额。开始及每次写入前核查账号sailorren、比赛、当天已用/剩余、GPU剩余额度及普通/正式作业占用。额度不足时按D960、R00、H30优先级执行已就绪者；不能因此新增第四方案。

提交额度不等于GPU额度或并发槽位。依据既有运行耗时与平台实时资源安排；资源不足就只启动可承受的候选，记录未运行者。不取消S50/G58腾位置，不假定三个作业可同时运行，不保证6小时内或当天出分。配额刷新不增加本批总预算，不跨日自动追加。续接先读账本和平台，已创建的版本或submission不得重建。

## 2. 已有作业、固定母版与复用

工具/历史证据起点：d1fa52dd66f598bb85be8ca60d7891a3cf049017。新分支从该提交建立，复用现有构建、实际CSV复核、submit_once和请求防重实现；读取AGENTS.md。独立worktree，不reset/stash/覆盖用户工作区，不写main或任何旧实验分支。

在上述固定提交读取reports/20260920_BIOHUB_SCORE_PAIR2_V01.md，以及experiments/BIOHUB_SCORE_PAIR2_20260920_V01/内本批实际复用的manifest、账本、构建和检查代码。不要运行旧launch_once.py/submit_once.py。

S50：V1 / SV351350449 / submission56407778；G58：V1 / SV351350591 / submission56407804。归档观测为2026-09-21 07:28上海、SCORE_PENDING。只读核对最新状态；结果即使返回，也不在本批中临时换母版、参数或叠加改动。新代码与输出目录必须和这两个作业隔离。

三臂算法母版统一为G1，而非S50或G58：
- 固定代码提交e9c7c63b896812660a78ec55fc3284c10f85e776。
- experiments/BIOHUB_SPRINT01_20260916/own/candidate.ipynb。
- Notebook SHA-256：de010e6ba142be0e01000093e061ef7d3388ddaa411185b40d26c63a3febe731。
- 正式身份submission56270217 / V1 / SV350197436；既有Public观测0.948，不重新提交母版。
- 输入、权重、镜像继承850fafe77eaa6438cae06f9773d1b6a0b3d8c118下experiments/BIOHUB_DIVGATE_PAIR_20260920_V01/candidate_manifest.json，并与最近已跑通版本核对。不得换最新依赖。

快速查现有实验索引/账本，避免同母版同改动的精确重复；不要为此重读全仓库。旧V19C报告中的漏检测/断轨数量只是历史机制线索，不是当前G1误差统计。三臂数值均为本批预先指定假设，未证明提分。

## 3. 三个独立候选

### D960：提高检测候选召回

唯一主动改动：BIOHUB_DET_THRESHOLD从0.965降至0.960。精确更新真实赋值和对应配置断言，检查传入检测worker及retention计数所用阈值，不只改显示文本。不做全文数字替换。

保持SECONDARY_DETECTION_WEIGHT=0.80、secondary edge=0.15、bidirectional edge=0.15、retention门槛0.90、原TTA/权重、原分裂与gap规则。不是S50的0.50融合版。重新生成受影响的检测、候选边及解图，不加载0.965下已定型的图冒充新推理。

保留原G1选择算法及选项。上游变化可能使其selected_label改变；记录真实最终配置，将Public解释为单个上游干预的完整流水线效果，而非宣称下游实际选择必然一致。

假设：让略低于原门槛、但有图像支持的检测进入后续关联，可能恢复漏检轨迹；风险是过检、错误连接和节点数惩罚。不能把新增节点当成收益。
拟用私有slug：sailorren/biohub-g1-det0960-20260921。

### H30：增强正反向关联的一致性约束

唯一主动改动：BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT从0.15改为0.30；保留harmonic_probability融合公式、现有尺度校准与TTA。它是反向时间关联权重，不是第二模型融合权重。

母版含初始化_EXPECTED_NUMERIC和_bidirectional_weight_guard两处相关断言；只更新该变量的预期值，不能删除全部配置守卫。核对实际worker在harmonic_prob公式中读取0.30，保留forward/reverse的维度、转置、归一化和校准步骤。只改变权重，不把harmonic换成算术平均。

保持检测门槛0.965、secondary detection=0.80、secondary edge=0.15及其他G1逻辑。重新计算受影响的关联和解图，原选择算法保留；记录其选择是否变化。母版已经计算反向关联，本候选不新增模型、TTA轮数或训练。

假设：对正向支持但反向不支持的连接施加更大抑制，可能减少误连接；风险是抑制真实但时间上不对称的连接。0.30不是已验证最佳值。
拟用私有slug：sailorren/biohub-g1-harmonic030-20260921。

### R00：解除短轨救援的全视频启动门槛

唯一主动改动：最终生产后处理SHORT_TRACK_RESCUE_TRIGGER_REMOVED_FRAC从0.10改为0.00。源码现有条件为removed_frac >= SHORT_TRACK_RESCUE_TRIGGER_REMOVED_FRAC，且removed_before_rescue <= 0时提前返回。只解除“删点达到10%才启动”的条件，不取消逐短轨质量筛选。

保持原ADAPTIVE_SHORT_TRACK_RESCUE开启；SHORT_TRACK_RESCUE_MIN_LEN=4、MIN_MEAN_EDGE_PROB=0.88、MAX_MEAN_EDGE_DIST_UM=3.0、MAX_NODES_FRAC=0.012、MAX_NODES_ABS=120和原候选排序不变；总体OUTPUT_MIN_TRACK_LEN=6、分裂分量保护和其他后处理不变。上限沿用原函数的逐次调用作用域，不能改成每轨120。不得无条件保留所有短轨，不增加新检测或凭空补边。

先按完整G1原选择器得到最终配置，再从未做最终后处理的同源图执行原后处理，仅在此次最终调用把实际全局/配置值设为0.00。该键可能不在PP_SWEEP_KEYS中，必须显式核对实际消费值；不能只加一个不会被读取的selected_config键。最终文件不能被后续G1写出覆盖。

记录每样本removed_before_rescue、removed_frac、triggered、救援节点数及实际budget。已有同次G1结果可作对照，但不额外重跑一整套G1。该门槛原已触发或无合格短轨时可能无效果；无效不得临时放宽置信度或数量限制。

假设：删点不到10%的视频中也可能有高置信短轨值得保留；风险是恢复误检及节点数惩罚。当前尚无证据证明被这个门槛挡住的短轨都是真实细胞。
拟用私有slug：sailorren/biohub-g1-rescue-trigger000-20260921。

## 4. 一次构建、同批执行、就绪即正式提交

只做改动路径短测试：D960阈值传播；H30双守卫/真实融合权重；R00低于10%时允许进入原筛选、高于原门槛时保持原行为、零删除早退、低置信拒绝及数量上限。关闭改动恢复母版值应通过既有人工图/配置回归。不新建验证框架，不运行新的8视野GPU诊断，不完整普查漏分裂，不做参数网格或新增训练。

用一份batch_manifest.json合并母版、三臂参数、输入/源码哈希、预算和停止条件。任务、manifest、源码/diff、复用必要脚本在一次payload同步并回读后启动。只审本批变化，不复制旧证据包。

开发/普通运行可以复用已绑定输入、权重、生成阶段和配置的缓存；D960不能复用旧检测图，H30不能复用旧关联评分/解图，R00不能在已过滤的最终图上重复修复。没有现成合格缓存就走原生产入口，不另建Dataset或大缓存工程。正式隐藏运行必须对当次实际输入正确计算，禁止固定可见样本、固定CSV复用或按Public/Private识别切换算法。

启动每个已就绪候选，不等待另一臂Public，不因独立故障阻塞其余。原G1确实参与选择的计算保留；新增效果诊断一律不挡提交。普通COMPLETE后直接收集实际最终CSV，复用CPU独立复核：版本/SV及输入权重绑定、模型加载、实际参数、schema/样本覆盖/有限坐标/ID端点/时间方向/图结构、最终字节及规范化内容哈希、官方reader往返。参数被覆盖、错版、无效输出或静默模型降级必须停；原retention保护回退仍允许。

有实际内容差异且工程合格者按精确Version各正式提交一次，不要求训练重叠诊断集上涨。普通输出完全等同母版且无其他实际决策变化证据时不浪费名额；候选彼此完全等同则去重。无法构成新有效候选时报告阻断，不为凑3个临时换方案。

每次提交前持久化唯一请求记录、核对全账号实时余额及已有submission；响应不明先只读对账，禁止盲重发。通过者立即提交，不能以“Notebook已上传”收尾。会话结束仍在运行则如实保存SV、下一步骤与预算；续接不重复授权同一批，不启动后台定时器或跨日自动扩展。

## 5. 最小交付和结果边界

只维护一份platform_ledger.json和指定报告。表内并列G1、S50/G58只读状态、D960/H30/R00，列版本/SV/submission ID、原始Public字符串、时间、实际预算及阻断。尚未创建正式submission不得写SCORE_PENDING；分数未返回为null。三位显示精度同分写PUBLIC_TIED，不能推断严格大小或Private。

GitHub仅保存任务、manifest、源码/diff、短测试/输出复核小型证据、ledger和报告；不存比赛数据、完整图、权重、CSV、凭据、环境变量快照或签名URL。只回读新增/修改文件并引用未变资产固定哈希；一次明确payload核验加一次回执即可，不做无限自证。task_delivery、execution、score分开表述。

本批三臂结果返回后集中分析；留出的两个名额不自动使用，不自动组合赢家或改最终选择。本批可继续既有S50/G58的只读查分，但不可重提或改动。

设计依据及阅读边界：实际读取了G1检测/短轨初始化、短轨10%触发分支、反向关联guard和harmonic公式片段；固定旧报告的历史错误线索、最新S50/G58回执和AGENTS.md。未逐行重新审计全部大单元，未运行模型。官方metrics.md说明额外节点和误连接存在评分风险。所有三个改进方向是待测假设，不是实测提分承诺。
