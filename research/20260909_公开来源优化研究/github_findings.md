# GitHub 公开来源优化研究

本次静态阅读的首要发现是：B0 的内置分裂 proxy 与当前官方公开指标实现不等价。因此建议先校正判断依据并定位损失，再投入新检测或长时序关联。B0 正式 0.946、C1 正式 0.940、C2 正式 0.946 的平台事实不受此静态发现否定；proxy 差异是否改变本批自动选参、是否解释 C1 下降仍为 UNKNOWN。

本子任务仅研究，第三方实现未执行、未下载模型或原始数据，所有优化收益均为 NOT_RUN。完整下载源码留在 ignored downloads/20260909_public_research/github，Git 仅保存摘要、固定身份、逐文件 SHA-256 与实际阅读范围，详见 github_findings.json。

## 固定来源与阅读覆盖

| 仓库 | branch / commit | 已读核心 | 许可与范围 |
|---|---|---|---|
| [royerlab/kaggle-cell-tracking-competition](https://github.com/royerlab/kaggle-cell-tracking-competition/tree/075fc5f5a52d11077f9dc2b074644618f26939e2) | main / `075fc5f5a52d11077f9dc2b074644618f26939e2` | `src/tracking_cellmot/metrics.py`, `src/tracking_cellmot/division_metrics.py`, `scripts/evaluate.py`, `tests/test_division_sandbox_examples.py` | BSD-3-Clause；CORE_SOURCE_READ |
| [matt-ceran/biohub-cell-tracking](https://github.com/matt-ceran/biohub-cell-tracking/tree/446589b772f4d98adecc3f6ba15434f0e0d57069) | main / `446589b772f4d98adecc3f6ba15434f0e0d57069` | `src/biohub/division_truth_rank.py`, `src/biohub/division_v2.py`, `src/biohub/metric.py`, `src/biohub/split.py` | UNKNOWN_NO_LICENSE_FILE；CORE_SOURCE_READ |
| [weigertlab/trackastra](https://github.com/weigertlab/trackastra/tree/aa57a95160002e0fc70b915ab74178b39c99fd6a) | main / `aa57a95160002e0fc70b915ab74178b39c99fd6a` | `trackastra/model/predict.py`, `trackastra/tracking/tracking.py`, `trackastra/tracking/ilp.py`, `trackastra/model/pretrained.py` | BSD-3-Clause；CORE_SOURCE_READ |
| [royerlab/hoct](https://github.com/royerlab/hoct/tree/2ccc5040823bc944ab67790abd1f56eea7cd4f05) | main / `2ccc5040823bc944ab67790abd1f56eea7cd4f05` | `examples/basic_tracking.py`, `src/hoct/_api.py`, `src/hoct/_models.py`, `src/hoct/tracking/_solver.py`, `src/hoct/features/features.py`, `src/hoct/features/constants.py`, `src/hoct/inference/_predict.py` | MIT；CORE_SOURCE_READ |
| [royerlab/ultrack-td](https://github.com/royerlab/ultrack-td/tree/fc8f988856ecd129d36b2c93a46d617c75ccad99) | main / `fc8f988856ecd129d36b2c93a46d617c75ccad99` | `examples/zebrahub.py`, `src/ultrack_td/__init__.py` | BSD-3-Clause；PYTHON_INTERFACE_CORE_READ_CPP_NOT_READ |
| [yu-lab-vt/FOCUS-3D](https://github.com/yu-lab-vt/FOCUS-3D/tree/5c4b53f743a0fbbae056e2c1a139895ae819f069) | main / `5c4b53f743a0fbbae056e2c1a139895ae819f069` | `src/focus3d/segmentation/segmentation.py`, `src/focus3d/segmentation/mask2former_adapter.py` | BSD-3-Clause plus nested MIT; weights AUTHOR_CLAIM Apache-2.0；INTERFACE_SOURCE_READ_MODEL_CORE_NOT_READ |

共冻结 6 个仓库，完整阅读 39 个选定文件。官方指标、Trackastra、matt-ceran 与 HOCT 共 4 个仓库计入核心源码覆盖；ultrack-td 只读完整 Python 接口，未深读 C++；FOCUS-3D 只读 worker/adapter 接口，未深读 backbone 和 inference_win.py，后二者不计最低核心源码数量。没有宣称任何仓库“全仓读完”。

## P0：先校正 proxy，再解释增益

SOURCE_CODE_VERIFIED：B0 的 `candidate.ipynb` 第 9 个 code cell（零基索引 8）源码 SHA-256 为 `3988c72818365e0cf42169df1d42d3d64e64a6f2815a42255a04222523936349`。其 `compute_division_confusion` 使用全图一次节点匹配、全图弱连通分量，以及任意深度 GT daughter descendants：只要父侧和两条后代线索进入含分叉的同一分量，就可能计 TP。它没有官方局部有向双分支、每个分裂独立重匹配、预测 fork 一对一分配和跨组件/合流 FP 规则。

官方 `division_metrics.py` 的 [match_divisions](https://github.com/royerlab/kaggle-cell-tracking-competition/blob/075fc5f5a52d11077f9dc2b074644618f26939e2/src/tracking_cellmot/division_metrics.py#L90)、[局部有向分支与一对一匹配](https://github.com/royerlab/kaggle-cell-tracking-competition/blob/075fc5f5a52d11077f9dc2b074644618f26939e2/src/tracking_cellmot/division_metrics.py#L227)、[跨组件和合流检测](https://github.com/royerlab/kaggle-cell-tracking-competition/blob/075fc5f5a52d11077f9dc2b074644618f26939e2/src/tracking_cellmot/division_metrics.py#L410) 是精确对照来源。

INFERENCE：下一步应冻结官方 scorer 的源码与依赖，先用合成图检查当前手写 proxy 的差异，再对相同已有图重评分，分别报告节点惩罚、edge TP/FP/FN、division TP/FP/FN、自动 PP 排名与最终选择是否变化。若变化，之后单独提出“只改选参评价器”的候选；本轮没有改 B0 或新增提交。不要预先承诺这个修复会超过 0.946。

SOURCE_CODE_VERIFIED：官方完整聚合路径是 `per_sample_metrics → summarise`，不是直接使用同仓 `evaluate_datasets`：后者只聚合未校正 edge Jaccard，前者读取 `estimated_number_of_nodes` 后才包含节点数项。官方 `metrics.py` 和 `scripts/evaluate.py` 未发现 min-component-size 删除规则，不能把 B0 生产短轨过滤 min6 写成官方指标规则。官方 edge 清理包含重复边、非相邻帧边、映射合并重复和超过两子边裁剪。

参考：[官方分项/聚合源码](https://github.com/royerlab/kaggle-cell-tracking-competition/blob/075fc5f5a52d11077f9dc2b074644618f26939e2/src/tracking_cellmot/metrics.py#L412)、[实际评价入口](https://github.com/royerlab/kaggle-cell-tracking-competition/blob/075fc5f5a52d11077f9dc2b074644618f26939e2/scripts/evaluate.py#L67)。官方 PR [#2](https://github.com/royerlab/kaggle-cell-tracking-competition/pull/2) 已合并到所冻结 HEAD；近期训练可视化 PR [#5](https://github.com/royerlab/kaggle-cell-tracking-competition/pull/5) 和 smoke 参数说明 PR [#6](https://github.com/royerlab/kaggle-cell-tracking-competition/pull/6) 为 closed 但 `merged=false`，不应写成 main 已有功能。

## P1：诊断候选可达性和错误排序

INFERENCE：把 B0 的分裂损失拆成“真实母/女细胞是否存在 → 是否进入候选 → 同母排序 → DeepCenter/几何门限 → 冲突和配额 → 最终保留”。B0 已有孤儿第二女儿、最近候选、后继发散、DC、对称性等约束；如果正确女儿根本不在候选中，继续改 TTA 或调整接受阈值无法恢复它。如果候选在但排序错误，应改关联表示或局部排序，而不是盲目扩半径。

matt-ceran 的源码把真实候选排序与阈值/同母竞争/女儿冲突/全视频配额阻断分别记录。这种分析结构可借鉴，但其 DoG+CNN+MCF 是另一条系统。其作者记录 v2 候选召回提高、学习排序跨 development 崩溃并拒绝晋升，是对“更多候选/低训练损失自动等于效果更好”的反例，不是本系统的因果证据。

来源：[truth-rank 核心](https://github.com/matt-ceran/biohub-cell-tracking/blob/446589b772f4d98adecc3f6ba15434f0e0d57069/src/biohub/division_truth_rank.py#L129)、[v2 拒绝报告](https://github.com/matt-ceran/biohub-cell-tracking/blob/446589b772f4d98adecc3f6ba15434f0e0d57069/experiments/2026-08-13-phase11-v2-atlasforge.md#L5)。该仓 `metric.py` 明示 local approximation，实际含 macro mean 和不同 score 公式，不能作为本赛当前正式 scorer；完整文件树未见 LICENSE 且 API license 为 null，仅借鉴方法，不建议直接移植代码。

## P2：长时序关联与真正独立检测信息

SOURCE_CODE_VERIFIED：HOCT 已有 5 帧窗口接口、窗口内预测聚合、显式 orphan 概率和二阶段 tracklet ILP；`general_v1` 在模型注册中绑定 release URL 与 SHA-256，默认不是裸无版本下载。它接收实例 labels 或完备 regionprops graph。尤其 `create_graph_from_points` 当前只有 TODO 与 `pass`，不能宣称 B0 质心直接调用就可运行。其 CUDA autocast 当前强制 bfloat16；本项目 T4 的兼容、耗时、显存没有实测。

INFERENCE：如果错误主要是邻帧信息不足，真正 5 帧上下文/有监督训练应优先于更多高度相关视角平均。但当前 B0 checkpoint 实际 window_size=2，不能只改配置为 5/8 就称长时序训练模型。HOCT 现公开包的训练实现、训练数据许可与本赛重叠范围仍未闭合；候选 max_delta_t 默认 3，也必须处理赛事相邻帧边输出要求。保留 B0 固定对照，先做接口/特征合同核验和最小试验，再决定是否值得正式实验。

来源：[HOCT 未实现的点接口](https://github.com/royerlab/hoct/blob/2ccc5040823bc944ab67790abd1f56eea7cd4f05/src/hoct/_api.py#L63)、[5 帧与特征输入](https://github.com/royerlab/hoct/blob/2ccc5040823bc944ab67790abd1f56eea7cd4f05/src/hoct/_api.py#L137)、[窗口聚合和 orphan 归一化](https://github.com/royerlab/hoct/blob/2ccc5040823bc944ab67790abd1f56eea7cd4f05/src/hoct/inference/_predict.py#L387)、[固定模型注册](https://github.com/royerlab/hoct/blob/2ccc5040823bc944ab67790abd1f56eea7cd4f05/src/hoct/_models.py#L22)。

SOURCE_CODE_VERIFIED / AUTHOR_CLAIM：FOCUS-3D 有核/通用/膜分割 checkpoint 描述，但 Hugging Face 页面当前有共享联系信息的访问条件，本次未接受或下载。代码顶层 BSD-3-Clause、嵌套组件 MIT；权重页面宣称 Apache-2.0，不能混用代码许可代替模型准入。当前 adapter 明确选择 no-Detectron2 的跨平台 PyTorch inference_win.py，所以不能沿用早期“Linux 必须 Detectron2 才能推理”的假设。

INFERENCE：只有先证明 B0 漏检或粘连细胞定位主导损失，才值得试 FOCUS-3D 的独立检测信息。必须核原始强度归一化、ZYX 尺度（比赛 Z:XY=4:1）、胞核/膜 checkpoint、分割到质心、临近细胞分离和节点总量惩罚，先看局部分项再做整个 pipeline。FOCUS 的公开 segmentation AP、讨论区作者推荐均不是 Biohub 正式分。

来源：[FOCUS adapter 路由](https://github.com/yu-lab-vt/FOCUS-3D/blob/5c4b53f743a0fbbae056e2c1a139895ae819f069/src/focus3d/segmentation/mask2former_adapter.py#L194)、[参数传递](https://github.com/yu-lab-vt/FOCUS-3D/blob/5c4b53f743a0fbbae056e2c1a139895ae819f069/src/focus3d/segmentation/segmentation.py#L77)、[官方权重页面](https://huggingface.co/Qinghua-thu/FOCUS-3D)。

## P3：已有图方法作为对照，避免重复堆叠

Trackastra 的窗口关联汇总、greedy/ILP、生物拓扑约束已有实现；ultrack-td 的层次多假设分割与 Zebrahub 示例也可供独立验证或伪标签支线参考。但 B0 已含 ILP、motion relink、双向 harmonic 融合、safe-div 和短轨处理，引入同名技术本身不构成新信息或预期提分。ultrack-td 的 v1 兼容入口还缺少 motion vector、temporal window 等完整功能，不能把示例成功外推为本项目端到端可用。

来源：[Trackastra 窗口汇总](https://github.com/weigertlab/trackastra/blob/aa57a95160002e0fc70b915ab74178b39c99fd6a/trackastra/model/predict.py#L91)、[ILP 约束](https://github.com/weigertlab/trackastra/blob/aa57a95160002e0fc70b915ab74178b39c99fd6a/trackastra/tracking/ilp.py#L79)、[ultrack-td 核心 Python 接口](https://github.com/royerlab/ultrack-td/blob/fc8f988856ecd129d36b2c93a46d617c75ccad99/src/ultrack_td/__init__.py#L146)、[Zebrahub 示例](https://github.com/royerlab/ultrack-td/blob/fc8f988856ecd129d36b2c93a46d617c75ccad99/examples/zebrahub.py#L41)。

本轮没有从所读 GitHub 实现取得绑定本赛当前 submission 的更高正式分。优先顺序为 **官方 scorer 对照 → B0 错误阶段诊断 → 由主导损失选择长时序关联或独立检测 → 单个可归因正式候选**；其中每项候选的实测收益均为 **NOT_RUN**。
