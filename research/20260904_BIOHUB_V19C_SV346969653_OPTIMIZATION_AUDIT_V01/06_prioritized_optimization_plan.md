# V19C 优先级与冻结验证计划

## 优化判断

决定为 `OPTIMIZATION_FEASIBLE_WITH_GATES`。当前方案已经是完整的“检测—关联—全局选图—gap/division 修复—输出校验”管线，0.939 也已绑定目标 Version 1/submission；继续优化不需要推倒重来。最有价值的工作是把现有失败模式转成可归因的单变量实验。

所有项目目前均为 `CANDIDATE_NOT_EXECUTED`。本文件是实验顺序与验收合同草案，不是启动训练、推理、Notebook Version 或 submission 的授权。

## 两类优先级

执行优先级与潜在得分优先级不同：

1. 执行第一位：`OPT001_FROZEN_EMBRYO_DISJOINT_CV`。没有冻结验证，其他任何候选都不允许晋升。
2. 执行第二位：`OPT002_CANONICAL_RESOLVED_CONFIG_RECEIPT`。它确保运行的确是声明的单变量配置。
3. 首个直接得分候选：`OPT003_SAFE_DIV_PARENT_RADIUS`。四样本 division 为 1 TP / 0 FP / 4 FN，active parent radius 为 7.0 µm，证据方向最清楚。
4. 第二个直接得分候选：`OPT004_SECONDARY_DETECTION_WEIGHT`。单个生产视频 64/100 帧回退，说明固定 0.80 融合有强异质性。
5. 后续候选：gap distance、bidirectional weight、global detector threshold。它们分别针对 fragmentation/lost、association fusion 因果缺口和 node-count 校准，但风险或证据弱于前两项。

## Phase 0：冻结可比较的验证合同

未来获得实验授权后，先固定：

- source SHA-256 `92bf632410fedc9eb7e0984a20525590b5583d5abb002d8239ff65d9f51fbf57` 作为基线；
- primary、secondary、DeepCenter 三份 checkpoint SHA；
- 13 个支持 Python 文件的 manifest SHA `978b626d1fd1e7397435a437dfe68691defe1572fc3c20e61012d7c9b52ed029`；
- 官方 scorer 的具体来源/commit/hash；
- embryo-disjoint split 的 stem 清单和哈希，禁止把公开 test stem 混入选择；
- 运行环境、CUDA 数、随机种子、输入 Dataset version、时间预算；
- 每个 candidate 只能改变一个主变量；
- 每样本 node count、edge TP/FP/FN、adjusted edge、division TP/FP/FN、总分、fragmented/lost/wrong association、fallback、运行时与输出 hash。

当前 validator 的四个样本可以保留为 smoke，但不能单独承担晋升。正式比较至少要覆盖全部可用 embryo prefix，并以 pairwise per-sample delta 展示均值、中位数和最差 prefix；若样本数仍不足，应报告置信区间/重采样稳定性，而不是给一个小数点后三位的确定提升。

## Phase 1：配置回执，不改模型行为

建立 canonical resolved receipt。回执在所有动态 source patch 和环境变量解析后生成，至少包括 detector、secondary detection/edge、retention、bidirectional mode/weight、ILP、motion、gap、safe-div、DeepCenter、track filter、validator、输入/权重/source/output 哈希。

必须删除或明确标为 narrative 的陈旧文本；运行一旦出现 parent 9 对 source 7、reverse 0.20 对 active 0.15 一类冲突，验证器直接 FAIL。该阶段预期得分方向为“无直接变化”，目的只是让后续实验可审计。

## Phase 2A：safe-div parent radius 单变量实验

固定 sister radius 14.0、symmetry tau 0.6、divergence 2.25、DeepCenter checkpoint/threshold、global/frame caps、detector candidates 和所有关联参数，只改变 `BIOHUB_SAFE_DIV_MAX_UM`。建议先测试 7.0（control）、8.0、9.0；数字是待验证网格，不是推荐最终值。

每折至少报告：geometric candidates、DeepCenter accepted/rejected、mutual-NN/divergence/symmetry rejected、added divisions、cap saturation、division TP/FP/FN、total score。晋升要求不是“division recall 上升”，而是 micro division Jaccard 与总分在均值、中位数、最差 prefix 均不退化，并且没有 topology violation。

如果 8/9 只增加 FP、触发 cap、或增益依赖一个样本，立即停止。Notebook Markdown 关于旧 arm 的 +0.001 或 lower-base sweep 属于作者叙述，不替代该冻结 A/B。

## Phase 2B：secondary detection weight 单变量实验

固定 detector threshold 0.965、retention threshold 0.90、secondary edge weight 0.15、association mode及全部后处理，只调整 `BIOHUB_SECONDARY_DETECTION_WEIGHT`。建议控制组 0.80，并选两个更低的预注册值；不根据公开 test 的 `44b6_0b24845f` 单独定规则。

对每个样本保存 primary/blended candidate count、retention 分布、fallback fraction、node-count adjustment、missed node proxy、edge/division/total score。改善 fallback fraction 不是充分条件：只有冻结 official scorer 也稳定改善才可晋升。若不同 embryo prefix 的最优方向冲突，则不继续全局权重；只能在训练数据特征上设计可泛化的 density/disagreement adaptive rule，并重新立项。

## Phase 3：fragmentation 与关联

先测试 `OPT005_GAP_CLOSE_DISTANCE`：只改变 5.8 µm 半径，保持 gap length=2、density adaptation 和 node caps 不变。目标是减少 56 个 fragmented 与 45 个 lost-to-detection edge，而不引入 wrong association。

随后测试 `OPT006_BIDIRECTIONAL_FUSION_WEIGHT`：只改变 harmonic weight，必须包含 forward-only 0.0 和 current 0.15。若能冻结相同 detector candidate，则 association 比较应复用候选，避免 detection 漂移。额外 reverse inference 的耗时必须计入 hidden-test 安全余量。

`OPT007_GLOBAL_DETECTOR_THRESHOLD` 仅是低优先级诊断。四样本 node ratio 方向相反，如果全局阈值曲线没有跨 prefix 一致方向，应保留 0.965 并停止；不得按 test ID 写特例。

## 统一晋升门

任何候选要从 `CANDIDATE_NOT_EXECUTED` 进入“可考虑平台验证”，必须同时满足：

1. candidate/control 的 source、输入、权重、scorer、split、随机种子和唯一差异有机器回执；
2. 所有折/样本均执行成功，缺失折不能被忽略；
3. 官方总分是主指标，adjusted edge、division、node-count 与 failure decomposition 是诊断指标；
4. paired mean、中位数与 worst-prefix 通过事先冻结阈值；
5. topology、schema、ID、坐标、dataset coverage、悬空 edge 检查全部通过；
6. 运行时间、内存和输出体积留有 hidden-test 余量；
7. 没有读取 hidden/public-output feedback 来动态配置规则；
8. canonical receipt 与实际运行参数完全一致；
9. 仍需用户对新的 Kaggle Notebook Version、训练或 submission 做另一次明确授权。

## Kaggle 平台验证边界

离线晋升也不自动授权 Kaggle 写入。若未来确需平台验证，应新建冻结任务，先确认 competition identity、账号 principal、剩余提交配额、目标 Notebook/source SHA、Dataset versions、是否存在等价 submission、单次写入预算和回收方式。最多使用预先批准的一次 Version/一次 submission，不自动 retry；失败后先回收错误证据，再请求新授权。

当前 pending submission `56002593` 不属于本审计操作，本计划不轮询、不取消、不选择，也不把其未来分数当作本轮优化验证。

## 预期产出形式

每个未来实验应输出一张 paired results 表、一个 canonical receipt、一个 failure decomposition、一个 runtime receipt 和一个明确结论：`PROMOTE_CANDIDATE`、`REJECT_CANDIDATE` 或 `INSUFFICIENT_EVIDENCE`。没有冻结证据时保持 `CANDIDATE_NOT_EXECUTED`，不能以 Notebook 名称、单次 Public Score 或作者注释代替。
