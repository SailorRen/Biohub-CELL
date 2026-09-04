# Biohub V19C ScriptVersionId 346969653 源码、日志与优化可行性报告

## 结论

本轮已对用户指定的 Kaggle 精确版本 `sailorren/biohub-v19c-public0939-sis14-only?scriptVersionId=346969653` 做完只读源码、完整日志、输出清单和四个小型诊断文件审计。结论是：**可以在 V19C 的基础上继续优化，但目前只能把方向写为带门禁的候选，不能写成已验证的性能提升。** 决策状态为 `OPTIMIZATION_FEASIBLE_WITH_GATES`，全部七项候选均为 `CANDIDATE_NOT_EXECUTED`。

关键依据：

1. `HOST_CONFIRMED`：精确页面 URL、Edit run 路径和 0.939 的 Version 1 分数链接都包含 `346969653`；页面显示 `Version 1 of 1`、运行成功、GPU T4 x2、307 个输出文件。API 返回同一 ref 的 current version 1 和 `KernelWorkerStatus.COMPLETE`。
2. `SOURCE_CODE_VERIFIED`：完整 source 为 213,952 bytes，SHA-256 `92bf632410fedc9eb7e0984a20525590b5583d5abb002d8239ff65d9f51fbf57`；12/12 cells 全读，10/10 code cells AST PASS。源码与前序目标副本哈希一致，有序 cell source 也与此前固定的公开对照 12/12 相同。
3. `MEASURED`：完整运行日志为 111,209 bytes、622 events，SHA-256 `a3d3de4a9644f943f37a4804740cd4c44ed0d658d76a47df62a1793fb868634d`；无 Traceback、Exception、fatal 或 failed event，平台状态 COMPLETE。
4. `HOST_CONFIRMED`：submission `55978992` 的 description 精确绑定目标 Notebook Version 1，状态 COMPLETE，Public Score 0.939；页面的分数链接进一步绑定 `346969653`。0.939 只是读取时本人已完成记录中的最高值，不是全球、private 或 final 分数声明。
5. `MEASURED`：四样本 validator 的 division 为 1 TP / 0 FP / 4 FN；一个 production 视频有 64/100 帧触发双 seed retention 回退；validator 还有 56 fragmented 和 45 lost-to-detection edges。这些是最具体的优化信号。
6. `MEASURED`：当前验证只有四个经 division-enriched 选择的样本，node-count 真值使用估计值；配置说明、guard receipt 与实际运行值多处冲突。先建立冻结 CV 与 canonical receipt，是任何参数晋升的前置条件。

本轮没有运行 Notebook、训练、推理、超参数搜索，没有创建或重试 submission，没有保存新 Version，也没有下载比赛数据、权重、GEFF、Zarr 或 `submission.csv`。

## 证据等级

- `HOST_CONFIRMED`：来自当前 Kaggle 页面或 API 的对象、版本、状态、输入、运行展示和 submission 记录。
- `SOURCE_CODE_VERIFIED`：来自本轮实际取得的目标 source 和逐 cell 静态审计。
- `MEASURED`：来自完整日志、四个小型输出或本轮可复现统计。
- `INFERENCE`：把失败模式转成候选实验的判断；必须附验证门和停止条件。
- `UNKNOWN`：平台未暴露、接口失败、来源冲突或没有执行实验的部分。

页面或 Markdown 中的作者叙述不能覆盖 actual source、resolved runtime manifest 或具体 submission 记录。

## 版本身份

用户 URL 当前解析到目标私有 Notebook，查询参数为 `scriptVersionId=346969653`。页面同屏观察到：

- `Version 1 of 1`；
- Edit 链接尾部为 `/edit/run/346969653`；
- `Public Score 0.939 Best Score`，Version 1 分数链接回指同一 ScriptVersionId；
- Runtime `31m 45s · GPU T4 x2`；
- Logs `1904.8 second run - successful`；
- Output 307 files。

API 返回 kernel ID `132979728`、current version `1`、private、Python、GPU enabled、internet disabled、NvidiaTeslaT4，并列出比赛输入和三份 Dataset。status 为 `KernelWorkerStatus.COMPLETE`。

Kaggle SDK 的固定 `version_label="1"` GetKernel/output 请求返回 HTTP 404，成功响应里也没有独立 `script_version_id` 字段。因此本轮没有伪造“API 字段完全绑定”。实际采用 fail-closed 组合：页面三个 `346969653` 指针 + 页面 Version 1 of 1 + API current version 1；只有 current version 仍为 1 才读取当前 source/output。若出现 Version 2，此回退即失效。

GetKernel 的 last-run 时间与 kernels list、页面时间存在冲突，所以版本身份不依赖单一时间字段。详细安全回执见 `research/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_V01/evidence/kernel_version_metadata.json`。

## 来源与血缘

用户说明方案从公开代码区复制。当前 source 的有序 cell 内容与此前固定的公开 `alioman/biohub-v19c-public0939-sis14-only` 捕获 12/12 相同，支持“内容相同”。但平台 parent identity 仍为 `UNKNOWN`：当前页面显示 `Copied from private notebook`，API `kernel_sources=[]`，源码 Markdown 又同时声称 public fork 与 standalone。它们不能拼成一个平台已确认的父版本。

当前目标和依赖的许可证没有全部暴露，故 GitHub 不保存完整 `.ipynb` 或源码摘录；只保存 source/file/cell hashes、结构、运行证据和原创分析。

## 源码结构

`SOURCE_CODE_VERIFIED`：Notebook 有 2 个 Markdown cell 和 10 个 Python code cell，cell source 总计 193,824 bytes。全部 code cell 通过 AST 解析，没有发现训练调用。支持包里出现训练脚本文件名只证明该包包含相关源码，不证明这次 Notebook 启动训练。

主流程如下：

1. 两个 `TemporalUNet3D` checkpoint 对每帧做 3D 中心热图推理；secondary detection weight 为 0.80。
2. 融合候选相对主模型的 retention 低于 0.90 时逐帧回退主模型。
3. `SimpleNodeTransformer` 对相邻帧候选边评分；secondary edge 以 low-margin consensus、weight 0.15 参与。
4. 正向与反向概率采用 harmonic probability fusion，active weight 0.15。
5. Hungarian、KDTree、motion relink 与 ILP 形成拓扑一致的连续边。
6. single-gap、gap-2 synthetic node、safe division、DeepCenter veto、短轨迹过滤/救援和 line-fit smoothing 修复图。
7. 输出 GEFF/CSV schema，并对四个 held-out train sample 运行本地 validator。

关键 active 参数包括 detector 0.965、edge threshold 0.48、ILP appearance 0.0、disappearance 2.0、gap 5.8 µm、minimum track length 6、safe-div parent 7.0 µm、sister 14.0 µm、divergence 2.25 µm、global/frame caps 0.00375/0.0076。

值得注意的是，Markdown 描述过 parent 9.0 与 divergence 4.5 的其他实验故事，但当前 source 分别赋值 7.0 和 2.25；运行 final manifest 也显示 parent 7.0。报告以实际赋值、调用与 resolved state 为准。

## 运行日志

`MEASURED`：622 个 event 包含 547 stdout、75 stderr；首末 event 差约 1,898.09 秒。日志显示两张 Tesla T4、四个测试视频分到两条 CUDA shard。生产预测耗时 8.85 分钟，held-out validator 预测耗时 7.68 分钟。

秘密扫描对私钥头、GitHub token、Kaggle key assignment、Bearer token 和常见签名 URL 参数命中 0；入库日志与下载字节一致。32 个 warning header 主要是 scikit-image 的 FutureWarning，另有 debugger 与 nbconvert/Mistune warning。它们未使本次运行失败，但不代表未来环境没有兼容风险。

四个测试图最终合计 119,358 nodes、115,124 edges、125 个 division parent，submission 共 234,482 rows。生产小型回执记录内容 SHA-256 `b4d8319bcbcbb53d60ca723346fbe3a93cfe60f7a1d5c420a5cfe5ad31943feb`；本轮没有下载实际 submission。

后处理并非轻量装饰：总计新增 644 个 single-gap nodes、270 个 gap-2 nodes，short-track 阶段移除 3,333 nodes；DeepCenter 对 356 个 safe-div geometric candidates 接受 245、拒绝 111，最终添加 125 个 division。它说明 gap/division/track filtering 是潜在收益与风险都较高的阶段。

## 可观测失败模式

### 1. 分裂召回不足

四样本 validator 聚合为 division TP 1、FP 0、FN 4，division Jaccard 0.2。active sister radius 已为 14.0 µm，而 parent radius 仍为 7.0 µm。`INFERENCE`：在保持 DeepCenter、symmetry、divergence 与 caps 不变时，parent radius 是可做单变量小网格的直接候选；0 FP 提供一些放宽空间，但样本过少，不能据此直接选择 8 或 9。

### 2. 双 seed 融合跨视频不稳定

production guard report 的 400 帧中有 65 帧回退，其中 `44b6_0b24845f` 独占 64 帧；其 minimum retention 约 0.453、median 约 0.862，而另外两个视频 median 略高于 1。`INFERENCE`：固定 secondary detection weight 0.80 在不同密度/胚胎类型上的行为差异很大，值得先做更低 scalar weight 的冻结 A/B。retention 只是候选数量比例，不是真实 recall，所以不能以“回退更少”单独晋升。

### 3. Fragmentation 与 lost detection

validator 汇总 edge TP 2,192、FP 104、FN 101；错误分解有 56 fragmented、45 lost-to-detection、0 wrong-association。`INFERENCE`：现有 matched-node association 没暴露明显 wrong-link 问题，优先修复 detection/gap 比盲目增加关联复杂度更合理。gap radius 5.8 µm 可作为后续单变量候选。

### 4. Node-count 方向不一致

四样本 predicted/estimated node ratio 约为 0.727、1.102、0.968、1.126。一部分欠检、一部分过检，反对“统一向上或向下改 detector threshold 就会普遍更好”的简单结论。global threshold 只保留为低优先级诊断；若不同 prefix 的方向冲突，应停止该路线，而不是给 test ID 写特例。

### 5. 配置证据漂移

辅助 guard report 的 detector 0.96875、secondary detection 0.475、ILP disappearance 1.5、bidirectional 0.3，与 active 0.965、0.80、2.0、0.15 不一致；普通日志还打印 reverse 0.200。回执自身状态为 `candidate_unverified`，validated receipt SHA 为 null，并记录 leaderboard feedback used。它是后续任何实验前必须修复的治理缺口。

## 优化判断

`INFERENCE`：在 V19C 上继续做受控优化是合理的，原因不是 0.939 与 0.938 的 0.001 差异，而是 source/log 暴露了四个能测量的失败面：division FN、dataset-specific fallback、fragment/lost edge 和 node-count heterogeneity。同时现有运行时间为后续小规模离线消融提供了工程可能性。

但可优化不等于确定能超过 0.939。没有固定多折、没有单变量对照、没有新运行、没有 private score，就无法把任一机制写成已证实收益。Notebook Markdown 中关于旧 arm 的分数和预期只作为 `AUTHOR_CLAIM`，不进入本报告的性能结论。

## 优先级

| 顺序 | 候选 | 作用 | 当前状态 |
|---:|---|---|---|
| 1 | `OPT001_FROZEN_EMBRYO_DISJOINT_CV` | 冻结 split、scorer 和 paired promotion 门 | `CANDIDATE_NOT_EXECUTED` |
| 2 | `OPT002_CANONICAL_RESOLVED_CONFIG_RECEIPT` | 消除 active config 与叙述/回执冲突 | `CANDIDATE_NOT_EXECUTED` |
| 3 | `OPT003_SAFE_DIV_PARENT_RADIUS` | 首个直接得分候选，针对 4 个 division FN | `CANDIDATE_NOT_EXECUTED` |
| 4 | `OPT004_SECONDARY_DETECTION_WEIGHT` | 针对 64/100 帧的单视频回退集中 | `CANDIDATE_NOT_EXECUTED` |
| 5 | `OPT005_GAP_CLOSE_DISTANCE` | 针对 fragmentation 与 lost detection | `CANDIDATE_NOT_EXECUTED` |
| 6 | `OPT006_BIDIRECTIONAL_FUSION_WEIGHT` | 验证 harmonic 0.15 的独立作用 | `CANDIDATE_NOT_EXECUTED` |
| 7 | `OPT007_GLOBAL_DETECTOR_THRESHOLD` | 诊断全局阈值是否能改善 node-count | `CANDIDATE_NOT_EXECUTED` |

执行第一位是验证合同；首个模型/图规则实验是 safe-div parent radius。详细证据、风险和停止条件见 `05_optimization_opportunities.csv`。

## 验证计划

### Phase 0：冻结比较单位

固定 source、三份 checkpoint、支持代码、Dataset version、official scorer、embryo-disjoint split、随机种子、硬件与运行预算。四样本现有 validator 只当 smoke，正式晋升必须报告每个样本和 embryo prefix 的 paired delta、均值、中位数与 worst-prefix。

主指标为冻结 official scorer 的总分；同时报告 adjusted edge、division、node-count adjustment、fragmented/lost/wrong association、fallback、拓扑与运行时。缺失任何 fold 都不能忽略。

### Phase 1：只修回执

在所有动态 patch 后输出 canonical resolved config，绑定 source/checkpoint/support/input/output hashes。验证器必须对缺失字段和陈旧显示失败。该阶段不改变算法行为，也不宣称得分方向。

### Phase 2：两个优先实验

第一项只改变 `BIOHUB_SAFE_DIV_MAX_UM`，建议控制组 7.0，并预注册 8.0、9.0；sister 14、divergence 2.25、DeepCenter 与 caps 全部不动。要求 micro division Jaccard 和总分稳定改善，且任何 prefix 不显著退化、FP/cap 不失控。

第二项只改变 `BIOHUB_SECONDARY_DETECTION_WEIGHT`，控制组 0.80，再测试少量更低值；detector threshold、retention threshold、edge blend 和后处理不动。要求 fallback、candidate/node count 和 official total score共同支持，而非只看一个公开 test 视频。

### Phase 3：低优先级实验

gap radius 只围绕 5.8 做窄网格，目标减少 fragment/lost，不增加 wrong link；bidirectional weight 必含 forward-only 0 和 active 0.15，尽可能复用相同 detector nodes；global detector threshold 若各 prefix 最优方向不一致则停止。

### 平台前置门

离线候选通过也不自动允许 Kaggle 写入。未来若要保存 Version 或提交，必须另起任务，由用户明确授权，并先冻结账号/比赛 identity、配额、目标 source SHA、Dataset versions、duplicate gate、单次写入预算和失败回收。不得自动 retry。

## 不建议的动作

- 不建议立即在 0.939 上继续叠加多个 division 参数；无法区分收益来源，且 FP 风险高。
- 不建议按 `44b6_0b24845f` 或当前公开 test ID 写特例；hidden test 不同，属于明显过拟合风险。
- 不建议把 local proxy 0.9414 当成预测 Public Score；它来自四个富集样本和估计 node count。
- 不建议仅凭页面/Markdown 的旧 arm 分数选择 9.0 或 4.5；当前 active source 不是这些值。
- 不建议优先更换大模型；现有日志先暴露的是验证、配置、division 和融合稳定性问题。

## 分数边界

submission `55978992` 与目标 Version 1 的 0.939 已闭合。读取快照中还有不同 Notebook 的 submission `56002593` 为 PENDING；本任务没有轮询它，报告也不预测其结果。后续动态成绩不自动改变本报告。

0.939 没有 private score，不能说明最终排名；也不能从相邻 0.938 submission 推导某个参数贡献了 0.001，因为 notebook、source 和多个机制可能同时不同。

## 进一步需要回答的问题

1. 扩大到冻结 embryo-disjoint 多折后，division 仍是否呈现“低 FP、高 FN”，还是四样本选择造成的偶然现象？
2. `44b6_0b24845f` 的双 seed retention 异常主要由 embryo 类型、密度、强度标定还是 secondary checkpoint 域偏移驱动？只有训练样本特征分析可以回答，不能用 test ID 规则回答。
3. global detector threshold 的最优方向是否跨 prefix 一致？如果不一致，应测试训练数据派生的密度/置信度特征，而不是继续扩大全局网格。
4. motion relink 几乎重建连续边时，Transformer 的 learned bonus 与 harmonic fusion 各自贡献多少？需要固定 detector nodes 的 association-only 消融。
5. dynamic patch 后的完整 active config 是否能由一个 canonical receipt 无冲突复现？这是所有模型结论成立前的工程问题。
6. 三份 checkpoint 的训练 split、数据资格、许可证和可复现训练配置能否闭合？本任务只有运行哈希，不能回答训练血缘。

本报告没有绘制趋势图：validator 只有四个非随机、division-enriched 样本，趋势视觉会放大不存在的总体稳定性。精确 audit table、逐样本数值和文字限制更适合当前证据；未来多折样本充足时再增加 paired-delta 分布图。

## 安全与外部动作

Kaggle submission 创建/retry/选择、Notebook 写入/保存/重跑、训练、推理重跑、超参数搜索、Dataset/Model 创建、规则接受、比赛数据下载、权重下载、大型输出下载均为 0。完整 output inventory 仅列名；只读取四个明确命名且小于 4 KB 的 JSON/CSV 诊断文件。

完整 source 留在临时目录且不入库；日志通过秘密扫描后入库。未保存 Cookie、Token、环境变量或签名 URL。GitHub 修改仅限用户要求的 Biohub-CELL 报告同步。

## 局限

1. `UNKNOWN`：成功 API 响应没有独立 ScriptVersionId 字段，固定版本参数请求 404；当前唯一 Version 1 guard 是合理但较弱的回退。
2. `UNKNOWN`：平台 fork parent、目标 source 许可证及三份 checkpoint 的完整训练血缘。
3. `UNKNOWN`：0.939 在 private/final leaderboard 或未来重评分中的结果。
4. `UNKNOWN`：任一候选在冻结多折、hidden test 与新平台运行中的真实效果。
5. 当前 validator 只有四个 division-enriched 样本；样本量和选择机制限制外推。
6. source 使用动态字符串 patch，虽有 guard 和 integrity hash，仍增加版本漂移与审计难度。
7. GetKernel、kernels list 和页面时间存在冲突；报告不把时间字段当 version identity。
8. 运行时间来自公开占位数据与当前 T4 x2；不能直接外推 hidden test。

## 证据索引与完成边界

- 来源清单：`research/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_V01/00_source_manifest.jsonl`
- 版本身份：`01_version_identity_and_lineage.md`
- 逐 cell 审计：`02_source_cell_audit.csv`
- 日志清单：`03_runtime_log_inventory.csv`
- 运行分析：`04_runtime_and_artifact_analysis.md`
- 候选表：`05_optimization_opportunities.csv`
- 优先计划：`06_prioritized_optimization_plan.md`
- 风险：`07_risks_and_unknowns.md`
- 机器摘要：`audit_summary.json`
- 零写入账本：`governance/CODEX_20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_LEDGER.json`

本地报告内容通过机器验收后仍不等于 GitHub 同步完成。最终 `COMPLETED_VERIFIED` 只在新验证器、前序 V19C 验证器、INITIAL_RECON 回归全部通过，本地 clean，`origin/main` 与 HEAD 一致，并从固定远端 commit 对全部冻结文件逐项回读 SHA-256 一致后成立。
