# V19C 方法分析

## 方法总览

`SOURCE_CODE_VERIFIED`：V19C 是一个纯推理与图后处理 Notebook，主链路可概括为：双 seed 的 3D 时序检测器生成候选节点，Transformer 模型为跨帧候选边评分，双向关联分数融合后通过匹配、运动补链和 ILP 选择图，再用 gap closing、DeepCenter veto、安全分裂修复、短轨迹过滤/救援与直线拟合平滑形成最终轨迹，最后转换为竞赛提交格式。

`SOURCE_CODE_VERIFIED`：12 个单元包括 2 个 Markdown 和 10 个 code cell，总 cell source 为 193,824 bytes。10/10 个代码单元均可由 Python AST 解析。本次静态扫描没有发现 `.backward()`、`optimizer.step()`、`.fit()` 等训练调用，运行日志也没有训练阶段。依赖包中包含名为 `train_unet_transformer.py` 的支持源码并不等同于该 Notebook 启动训练；日志显示实际流程加载既有权重并执行 inference。

## 1. 检测与双 seed 融合

`SOURCE_CODE_VERIFIED`：检测器使用 `TemporalUNet3D` 对每帧中心热图进行推理。主 seed 和次 seed 的预训练权重分别从已挂载工件 materialize，源代码设置次 seed detection weight 为 `0.80`。代码包含类似 D4 的测试时增强路径，并在峰值提取后将候选节点交给关联阶段。

`MEASURED`：运行日志确认两套权重均找到，最终 resolved manifest 显示 `Dual-seed ensemble: requested=True weights_found=True`。次模型运行行显示 detection weight `0.800`、edge weight `0.150`、`low_margin_consensus`、low-margin max `0.350` 和 edge threshold `0.480`。

`SOURCE_CODE_VERIFIED`：帧保留 guard 比较融合候选数与主模型候选数。如果 retention 低于 `0.90`，该帧回退到主模型候选，避免双 seed 融合意外大量删除候选。

## 2. Transformer 边评分与双向融合

`SOURCE_CODE_VERIFIED`：`SimpleNodeTransformer` 对父子候选边打分。正向与反向关联在概率空间做 harmonic fusion；代码的冻结配置和最终运行 manifest 都给出权重 `0.15`、mode `harmonic_probability`。次模型边分数主要在低 margin 条件下参与 consensus。

`MEASURED`：日志最终 resolved state 明确记录 `weight=0.15 active=True mode=harmonic_probability`。早期普通打印行却写了 `Reverse-time association weight: 0.200`。最终 manifest、实际“fusion applied”行及源代码 guard 一致指向 `0.15`，因此 `0.200` 被标记为陈旧或不准确的显示文本，不能作为实际配置。

## 3. 匹配、运动补链与 ILP

`SOURCE_CODE_VERIFIED`：代码组合使用 `scipy.optimize.linear_sum_assignment`、`cKDTree`、距离/速度代价和学习边概率完成候选匹配及 motion relink。随后由 ILP 选择全局一致边集合，约束节点入度和出度，并容纳 appearance、disappearance、gap 与 division。

本次读取到的主配置包括：

| 参数 | 激活值 | 证据 |
|---|---:|---|
| detector threshold | 0.965 | source 配置与 guard |
| edge candidate threshold | 0.48 | source / runtime |
| ILP appearance weight | 0.0 | source 配置与 guard |
| ILP disappearance weight | 2.0 | source 配置与 guard |
| gap close distance | 5.8 µm | source 配置与 guard |
| output minimum track length | 6 | source 配置与 guard |
| secondary detection weight | 0.80 | source / runtime |
| secondary edge weight | 0.15 | source / runtime |
| bidirectional fusion weight | 0.15 | source / resolved runtime manifest |

这里的“激活值”只描述这次 source 和 resolved runtime state，不表示这些值是最优超参数。

## 4. Gap、分裂与 DeepCenter veto

`SOURCE_CODE_VERIFIED`：图后处理包含 gap closing 与 gap-2 synthetic node 路径、基于 Hungarian/KDTree 的候选选择、运动一致性、密度自适应距离，以及 DeepCenter 对 gap 和 safe division 的否决。safe division 的运行阈值为 parent 距离不超过 `7.0 µm`、sister 距离不超过 `14.0 µm`，全局比例上限 `0.00375`，逐帧比例上限 `0.0076`。

`MEASURED`：resolved manifest 显示 DeepCenter `requested=True loaded=True`，预期 epoch 为 2，gap veto 与 safe-div veto 均开启。运行完整性回执记录 DeepCenter 权重 SHA-256 为 `8040999a92f6b7bbd98fa8cf458141e045c0f9ad7c936bdb3b18e1f7edafe2a0`。

## 5. 短轨迹处理、平滑与输出

`SOURCE_CODE_VERIFIED`：输出图会执行短轨迹过滤，同时保留包含可信 division 的 component，并在需要时使用受预算约束的短轨迹 rescue。之后对可处理节点做 line-fit smoothing，生成 GEFF 轨迹并转换成 submission 表结构。

`MEASURED`：四个测试视频最终共有 119,358 个 node rows 和 115,124 个 edge rows，总计 234,482 rows。运行回执给出的 submission 内容 SHA-256 是 `b4d8319bcbcbb53d60ca723346fbe3a93cfe60f7a1d5c420a5cfe5ad31943feb`。本轮没有下载或提交该 `submission.csv`，只保留运行回执中的行数和哈希。

## 6. 权重与支持代码身份

`MEASURED`：运行完整性回执给出：

- 主权重 SHA-256：`12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771`
- 次 seed 权重 SHA-256：`9bac2fa0dadc4a6fc1899e0caf187f4b553e0a7cd90ba1261a68b35ffe9e305f`
- DeepCenter 权重 SHA-256：`8040999a92f6b7bbd98fa8cf458141e045c0f9ad7c936bdb3b18e1f7edafe2a0`
- 13 个支持 Python 文件的 manifest SHA-256：`978b626d1fd1e7397435a437dfe68691defe1572fc3c20e61012d7c9b52ed029`

回执还写明 production test inference 的 `ground_truth_accessed=false`，并且动态 source patch 前已做完整性检查。这支持“测试推理阶段没有读取 ground truth”的运行自报与工件证据；它不是对 Kaggle 平台沙箱的外部取证，也不证明训练阶段的数据合规性。

## 配置回执冲突

`MEASURED`：`dual_seed_frame_retention_guard_report.json` 中若干配置与 source 命令/最终 resolved manifest 不一致：

- detector threshold：回执 `0.96875`，实际 source 配置 `0.965`；
- secondary detection weight：回执 `0.475`，运行行 `0.800`；
- ILP disappearance weight：回执 `1.5`，source guard `2.0`；
- bidirectional primary weight：回执 `0.3`，最终激活 fusion weight `0.15`。

同一回执的 `quality_promotion.status` 是 `candidate_unverified`，所需 receipt 缺失，`validated_receipt_sha256` 为 null，且 `execute_push_submit` 写为禁止。因此该文件可用于 topology、帧回退和 submission 哈希审计，但不能作为激活配置或质量晋升的唯一权威来源。

## 关于 0.939 的可解释边界

`INFERENCE`：从源码与日志看，V19C 的差异重点集中在双 seed 候选融合、双向关联、保留 guard、gap/division 修复和多重安全阈值。这些机制都在最终 manifest 中处于激活状态，且这次 Version 1 对应 submission 的 Public Score 为 0.939。

但是没有同一提交工件、同一数据、仅改变一个组件的受控消融，也没有冻结的多折验证。因而不能从一次 0.939 反推出某个组件带来了多少提升，更不能把 `0.939 - 0.938` 写成已证实的单参数增益。该因果归因仍为 `UNKNOWN`。

## 未验证事项

- `UNKNOWN`：公开源码与其依赖的许可证未由当前接口闭合。
- `UNKNOWN`：三份权重的训练数据、训练配置和独立复现结果没有在本任务中验证。
- `UNKNOWN`：ScriptVersionId 未由已读接口暴露。
- `UNKNOWN`：Kaggle 没有在 `kernel_sources` 中声明 fork 血缘。
- `UNKNOWN`：0.939 对私有榜、最终榜或未来重评分的表现。
