# V19C 运行日志、小型输出与失败模式分析

## 完整日志状态

`MEASURED`：目标 Version 1 可取得的完整 runtime log 已读取。日志为 111,209 bytes，SHA-256 `a3d3de4a9644f943f37a4804740cd4c44ed0d658d76a47df62a1793fb868634d`，JSON 数组内有 622 个 event：547 stdout、75 stderr。首末 event 时间为 6.04564465 与 1904.137987524 秒，覆盖 1,898.092342874 秒，约 31 分 38.09 秒。页面显示 31 分 45 秒，两者量级一致但语义不同，前者是首末日志 event 差，后者是平台 runtime 展示。

秘密扫描覆盖私钥头、GitHub token、Kaggle key assignment、Bearer token 和常见签名 URL 参数，命中 0；仓库中的 `runtime_log_sanitized.log` 未改写任何字节。扫描不是对所有秘密格式的形式化证明，但冻结规则内没有命中。

## 状态、错误与告警

`HOST_CONFIRMED`：status API 为 `KernelWorkerStatus.COMPLETE`，页面日志状态为 successful。

`MEASURED`：日志没有 Traceback、Exception、fatal 或明确 failed event。四行包含单词 `errors:` 的文本属于 validator 的 `missed_gt_nodes`、`spurious_pred_nodes` 等算法诊断，不是运行异常，所以 runtime error count 为 0。

32 个 warning header 包括 28 个 scikit-image plugin `FutureWarning`、2 个 nbconvert/Mistune `SyntaxWarning`，以及两组 debugger warning header。它们没有阻止本次运行完成。`COMPLETE` 和无异常只能证明执行终止并生成输出，不能证明参数最优、指标实现无误或重跑逐位一致。

## 源码结构与实际运行主线

`SOURCE_CODE_VERIFIED`：Notebook 共 12 个 cell，2 个 Markdown、10 个 code；cell source 合计 193,824 bytes。10/10 个 code cell 均通过 Python AST 解析，没有发现 `.backward()`、`optimizer.step()`、`.fit()` 或训练调用。实际流程是加载预训练 checkpoint 后推理：

1. 主、次两个 `TemporalUNet3D` 生成中心热图；次 seed detection weight 为 0.80；
2. 以每帧 candidate retention 0.90 为回退门，融合候选不足时使用主检测器候选；
3. `SimpleNodeTransformer` 为相邻帧候选边评分，次模型以 low-margin consensus、edge weight 0.15 参与；
4. 正反向边概率以 harmonic probability 融合，激活 weight 0.15；
5. Hungarian/KDTree 与 motion relink 产生主要连续边，随后 ILP 与图后处理保证入度、出度、gap 和 division 结构；
6. single-gap、gap-2、safe division、DeepCenter veto、短轨迹过滤/救援和 line-fit smoothing 生成最终图；
7. GEFF 转为竞赛 CSV schema，并运行本地 held-out validator。

激活配置中关键值包括 detector threshold 0.965、edge candidate threshold 0.48、ILP appearance 0.0、disappearance 2.0、gap distance 5.8 µm、minimum track length 6、safe-div parent 7.0 µm、sister 14.0 µm、divergence 2.25 µm、bidirectional weight 0.15。描述文字声称 parent 9 与 divergence 4.5，但 source 赋值和最终 runtime manifest 分别是 7.0 与 2.25；前者不能覆盖实际执行状态。

## 运行资源与输出规模

`MEASURED`：日志识别两张 Tesla T4，将四个测试视频划分到两条独立 CUDA shard。生产 test inference 日志耗时 8.85 分钟，held-out validator inference 为 7.68 分钟。当前 31 分 45 秒总运行时间在 12 小时限制内留有空间，但官方资料说明 hidden test 与公开占位数据存在规模/分布差异，因此不能从这一轮断言未来运行仍有同样余量。

四个测试视频最终 topology：

| dataset | nodes | edges | division parents |
|---|---:|---:|---:|
| `44b6_0113de3b` | 25,475 | 24,757 | 50 |
| `44b6_0b24845f` | 18,548 | 17,342 | 26 |
| `6bba_05b6850b` | 6,044 | 5,844 | 4 |
| `6bba_05db0fb1` | 69,291 | 67,181 | 45 |

合计 119,358 nodes、115,124 edges，submission 234,482 rows；运行回执给出的内容 SHA-256 为 `b4d8319bcbcbb53d60ca723346fbe3a93cfe60f7a1d5c420a5cfe5ad31943feb`。本任务没有下载 `submission.csv`，这些数字来自小型回执和 `run_stats.csv`。

图后处理总计新增 644 个 single-gap node、1,288 条相应 edge，gap-2 新增 270 node 与 405 edge；safe division 产生 356 个 geometric candidate，DeepCenter 接受 245、拒绝 111，最终添加 125 个 division。短轨迹阶段移除 770 个 component、3,333 nodes 和 2,563 edges；只有 `44b6_0b24845f` 触发救援，恢复 28 个 component、120 nodes。line-fit smoothing 处理 119,338 个节点。

这些统计说明后处理对最终图有实质影响，特别是 motion relink、gap、division 与短轨迹阶段；它们不告诉我们每一步对 0.939 的独立增益，因为没有只改变一个变量的同协议对照。

## 双 seed retention 的异质性

`MEASURED`：production guard report 覆盖 400 帧，65 帧回退主检测器：

- `44b6_0b24845f`：64/100；median retention 约 0.862，minimum 约 0.453；
- `6bba_05b6850b`：1/100；
- 另两个测试视频：0/100，median retention 均略高于 1。

完整日志有 194 条 guard event；事件因 shard 呈现重复，且还包含 validator 样本。按 dataset、frame、candidate 数与 retention 去重后为 97 条，其中 production 的权威计数仍取独立 guard report 的 65/400。明显的 dataset-specific 差异说明固定 0.80 融合权重不是对所有视频同样稳定；但 retention 低只说明候选数量相对主模型减少，不直接等于真实 recall 降低。

## held-out validator 信号

`MEASURED`：validator 只选择四个 train sample，每个 embryo prefix 两个，并优先选择含 GT division 的样本。四样本聚合输出 adjusted edge Jaccard 0.9214、division Jaccard 0.2000、proxy 0.9414。逐样本 adjusted edge Jaccard 为约 0.9364、0.8084、0.9832、0.8313，离散度明显。

错误分解合计：edge TP 2,192、FP 104、FN 101；division TP 1、FP 0、FN 4；fragmented edge 56、lost-to-detection 45、wrong-association 0；missed GT node 36。`spurious_pred_nodes` 合计 91,469，但这个数受 7 µm 节点匹配、稀疏真值与总节点估计语义影响，不能直接当普通 detection false positive 使用。

预测/估计总节点比在四个样本分别约为 0.727、1.102、0.968、1.126，方向不一致。它反对仅凭一个全局 detector threshold 就能稳定修复所有样本的简单假设，也提示需要按 embryo/density 分层看结果。

local proxy 与 public 0.939 不能直接比较：样本仅四个且是 division-enriched 选择，`t_true` 来自 `estimated_number_of_nodes`，没有冻结多折统计或同协议 baseline。0.9414 只能证明 validator 路径可运行并暴露失败模式。

## 配置与证据完整性问题

`MEASURED`：`dual_seed_frame_retention_guard_report.json` 把 detector 写为 0.96875、secondary detection 写为 0.475、ILP disappearance 写为 1.5、bidirectional primary weight 写为 0.3；source/运行实际对应 0.965、0.80、2.0、0.15。日志早期普通文本又打印 reverse weight 0.200，而实际 fusion applied 和最终 manifest 是 0.15。

该 guard report 自身标记 `quality_promotion.status=candidate_unverified`，缺失 required receipt，validated SHA 为 null，并写明禁止 promotion push/submit。它还记录 `leaderboard_feedback_used_for_configuration=true`。因此它能用于 topology、fallback 和文件哈希审计，却不能独自证明 active config、候选已晋升或 0.939 的因果来源。

## 优化可行性判断

`INFERENCE`：存在可执行的优化空间，决定为 `OPTIMIZATION_FEASIBLE_WITH_GATES`。证据最集中的方向是：先冻结可信的 embryo-disjoint 验证与 canonical config receipt；随后做 safe-div parent radius 的单变量召回实验，以及 secondary detection weight 的单变量稳定性实验。fragment/lost edge、gap 与 bidirectional weight 也可测试，但优先级更低。

这不是“当前方案有明确 bug，改后必然更高分”的结论。当前没有执行任何候选、训练、推理、Notebook Version 或 submission；预期影响只写方向，不写虚构幅度。
