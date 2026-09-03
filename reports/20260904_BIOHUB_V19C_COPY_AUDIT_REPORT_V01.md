# Biohub V19C 复制版本源码、运行日志与 0.939 分数审计报告

## 结论

本轮已对用户从 Kaggle 公开代码区复制的 `sailorren/biohub-v19c-public0939-sis14-only` Version 1 做完只读源码与运行证据审计。

核心结论如下：

1. `SOURCE_CODE_VERIFIED`：目标私有 Notebook 的实际源码已取得，12/12 个 cell 全部检查，10/10 个代码单元均通过 AST 解析。其 12 个 cell source 与前一日固定读取的公开 `alioman/biohub-v19c-public0939-sis14-only` Version 1 逐项哈希一致。
2. `MEASURED`：Kaggle status 为 `COMPLETE`；完整运行日志为 111,209 bytes、622 个事件，日志覆盖约 31 分 38 秒，没有 Traceback、Exception 或 fatal event，记录了 32 个非致命 warning header。
3. `MEASURED`：submission ID `55978992` 的 description 明确是 `Notebook biohub-v19c-public0939-sis14-only | Version 1`，状态 `COMPLETE`，Public Score `0.939`。这闭合了截图、Notebook ref、Version 1 与具体 submission 记录的绑定。
4. `MEASURED`：0.939 是本轮返回的四条本人 submission 中当前可见最高 Public Score；它不是“全球比赛最高分”，也没有可见 private score。
5. `UNKNOWN`：Kaggle 元数据 `kernel_sources=[]`，没有平台声明的 fork parent；当前可见接口也未暴露 ScriptVersionId 和明确的公开源码许可证。报告只陈述“用户说明复制 + cell 内容完全一致”，不把它升级为平台 provenance 或许可结论。
6. 本轮 Kaggle submission、Notebook Version 写入、训练、Dataset/Model 创建、规则接受和大型下载均为 0。完整 `.ipynb`、权重、GEFF/Zarr 以及 `submission.csv` 都没有进入 GitHub。

## Notebook 身份与血缘

目标 ref 为 `sailorren/biohub-v19c-public0939-sis14-only`，Kaggle 元数据返回 current version `1`、private notebook、Python、Nvidia Tesla T4、GPU enabled、internet disabled。`kernels status` 返回 `KernelWorkerStatus.COMPLETE`。临时拉取的 `.ipynb` 为 213,952 bytes，SHA-256：

`92bf632410fedc9eb7e0984a20525590b5583d5abb002d8239ff65d9f51fbf57`

公开对照是 `alioman/biohub-v19c-public0939-sis14-only` Version 1。它已在 2026-09-03 初始研究中完整读取，source response 同为 213,952 bytes，SHA-256：

`363139b1f15ebd4b822b286019c0ce46533d0e045cdb31a99a9ffe0d7c208fd9`

两个整文件 SHA 不同，因为一个是私有副本拉取的 `.ipynb` 文件，另一个是 GetKernel source response，外层元数据和 JSON 序列化载体可以不同。为避免错误比较，审计把每个 cell 的原始 source 文本作为规范单位，同时比较 index、type、UTF-8 bytes 和 SHA-256。结果为 12/12 全等，其中代码单元为 10/10 全等，没有发现 source 增删、重排或文本差异。

本轮重读公开上游返回 HTTP 403；没有绕过权限。对照数据来自已经固定在本仓库并通过初始研究验收的逐单元证据。该限制不会改变内容相等结果，但意味着“本轮再次成功下载公开 source”并未发生。

Kaggle 目标元数据的 `kernel_sources` 为空，所以 `UNKNOWN`：平台是否把副本登记为该公开 ref 的正式 fork。用户明确说明来源于公开代码区，内容证据也完全相符，足以记录内容来源说明，却不足以伪造一个平台未返回的 parent ID。

## 源码结构

Notebook 共 12 个 cell：2 个 Markdown、10 个 Python code cell，合计 cell source 193,824 bytes。逐单元清单在 `research/20260904_BIOHUB_V19C_COPY_AUDIT_V01/02_notebook_cell_audit.csv`。

`SOURCE_CODE_VERIFIED` 的计算主线是：

- 双 seed `TemporalUNet3D` 检测每帧细胞中心；
- 以次 seed detection weight `0.80` 融合候选，并用 0.90 retention guard 做逐帧回退；
- `SimpleNodeTransformer` 对候选父子边评分；
- 正反向关联在概率空间做 harmonic fusion，实际激活权重 `0.15`；
- Hungarian、KDTree 与运动代价做匹配和补链；
- ILP 选取全局一致图，允许 appearance、disappearance、gap 和 division；
- gap closing、gap-2 synthetic node、DeepCenter veto 和 safe division 修复图结构；
- 短轨迹过滤/救援与 line-fit smoothing 处理最终图；
- 输出 GEFF 并转换为竞赛 submission schema。

激活参数中可稳定绑定的关键值包括 detector threshold `0.965`、edge candidate threshold `0.48`、ILP appearance `0.0`、ILP disappearance `2.0`、gap distance `5.8 µm`、最短轨迹长度 `6`、次 seed edge weight `0.15`、双向 harmonic fusion weight `0.15`。safe division 的 parent/sister 距离阈值分别为 `7.0 µm` 与 `14.0 µm`，全局/逐帧上限为 `0.00375` 与 `0.0076`。

10 个 code cell 均通过 AST 解析。没有发现 `.backward()`、`optimizer.step()` 或 `.fit()` 等训练调用，运行日志也没有训练阶段。支持包中存在 `train_unet_transformer.py` 文件只能说明依赖包包含训练源码，不能据此说本 Notebook 执行了训练。

## 模型与支持代码身份

运行完整性回执记录三份实际加载工件的哈希：

- primary：`12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771`
- secondary：`9bac2fa0dadc4a6fc1899e0caf187f4b553e0a7cd90ba1261a68b35ffe9e305f`
- DeepCenter：`8040999a92f6b7bbd98fa8cf458141e045c0f9ad7c936bdb3b18e1f7edafe2a0`

支持代码仓库共 13 个 Python 文件，其汇总 manifest SHA-256 为 `978b626d1fd1e7397435a437dfe68691defe1572fc3c20e61012d7c9b52ed029`。回执还记录 production inference 的 `ground_truth_accessed=false`，并称动态 source patch 前完成完整性检查。

这些信息可用于将运行绑定到具体权重/支持代码字节，但不能替代训练数据血缘、许可证、训练脚本执行与可复现性审计。因此训练过程和数据合规仍为 `UNKNOWN`。

## 运行日志

完整日志 SHA-256 为 `a3d3de4a9644f943f37a4804740cd4c44ed0d658d76a47df62a1793fb868634d`，包含 547 个 stdout 和 75 个 stderr event。首末 event time 差约 1,898.092 秒。

运行显示两张 Tesla T4 可见，四个 test video 被划分到两个 CUDA shard。测试预测阶段耗时 8.85 分钟。最后四个测试图的规模为：

| dataset | nodes | edges | division parents |
|---|---:|---:|---:|
| `44b6_0113de3b` | 25,475 | 24,757 | 50 |
| `44b6_0b24845f` | 18,548 | 17,342 | 26 |
| `6bba_05b6850b` | 6,044 | 5,844 | 4 |
| `6bba_05db0fb1` | 69,291 | 67,181 | 45 |

总计 119,358 个 node row、115,124 个 edge row，共 234,482 rows。运行回执记录生成内容 SHA-256 为 `b4d8319bcbcbb53d60ca723346fbe3a93cfe60f7a1d5c420a5cfe5ad31943feb`；为遵守仓库边界，本轮没有下载或提交实际 `submission.csv`。

生产 guard report 记录 400 帧中 65 帧回退主检测器，其中 `44b6_0b24845f` 占 64 帧、`6bba_05b6850b` 占 1 帧。原始日志有 194 条 guard event，但事件成对重复且还混入 validator 阶段；去重后为 97 条。因此报告使用独立 production guard report 的 65/400，不把日志行数直接误写成不同生产帧数。

错误扫描没有发现 Traceback、Exception、failed 或 fatal event。32 个 warning header 主要来自 scikit-image plugin 的 `FutureWarning`，另有 debugger 与 nbconvert/Mistune `SyntaxWarning`。它们未阻止这次运行完成，但“无显式错误”不等于“算法没有语义错误”。

## 本地验证结果

Notebook 从 train 区域选择四个 held-out sample，并明确排除与四个 test stem 同名的 train stem。选择覆盖两个 embryo prefix，每个 prefix 两个样本，且四个样本均包含至少一个 GT division。验证推理耗时 7.68 分钟。

`MEASURED`：四个样本汇总 adjusted edge Jaccard `0.9214`、division Jaccard `0.2000`，Notebook 代理公式输出 `PROXY_SCORE=0.9414`。

该 0.9414 不能与 Kaggle Public Score 0.939 混为同一指标：它只来自四个选择样本，`t_true` 使用 `estimated_number_of_nodes`，没有冻结多折验证，也没有独立的同协议 baseline。它最多证明本地指标路径在所选样本上运行并产生有限值，不能证明或预测 leaderboard 表现。

## 配置冲突

辅助 `dual_seed_frame_retention_guard_report.json` 包含若干与源代码或最终 resolved manifest 不一致的值：detector `0.96875` 对 active `0.965`，secondary detection `0.475` 对 runtime `0.800`，ILP disappearance `1.5` 对 source guard `2.0`，bidirectional primary `0.3` 对最终 active fusion `0.15`。

此外，日志早期普通打印写 `Reverse-time association weight: 0.200`，但实际 fusion-applied 行和最后 resolved manifest 均为 `0.15`、`harmonic_probability`。本报告把最终 resolved state、实际调用行和 source guard置于辅助回执/说明性打印之前，同时显式保存冲突。

guard report 本身还写明 `quality_promotion.status=candidate_unverified`，所需 receipt 缺失、validated SHA 为 null，并禁止 promotion push/submit。故它不能证明候选配置经过晋升门禁，更不能单独证明 0.939 的原因。

## 分数绑定

用户截图显示 `biohub-v19c-public0939-sis14-only - Version 1`、Succeeded 和 0.939。截图文件 SHA-256 为 `2d6e2b21bfc6d01ac45bab4d1ec2251e7d2e884cd26f6ae1fdbac79e5a4c069e`，它保存了界面观察，但不含 submission ID。

Kaggle 本人 submissions 只读记录补齐了机器绑定：submission `55978992`，description `Notebook biohub-v19c-public0939-sis14-only | Version 1`，status `COMPLETE`，Public Score `0.939`，file name `submission.csv`。这条记录与目标 Notebook current Version 1 身份一致。

本轮返回的四条本人记录分数为 0.939、0.938、0.938 和 0.885，所以 V19C 是这四条中的当前可见最高分。这里不声称它是全体参赛者 global best，也不声称 private/final score 已知。

## 局限

1. `UNKNOWN`：当前 Kaggle 接口未暴露 ScriptVersionId；绑定依赖 submission ID、description 和 Version 1 source，而不是 ScriptVersionId。
2. `UNKNOWN`：目标 `kernel_sources` 为空，平台 fork parent 未闭合。
3. `UNKNOWN`：公开 Notebook 和依赖工件许可证未明确暴露，因此不再分发完整源码。
4. `UNKNOWN`：`kernels list` 与 GetKernel 的 `lastRunTime` 不一致；没有用它们替代 submission ID。
5. `UNKNOWN`：辅助 guard report 的旧配置值来自哪条生成路径；本轮没有重跑定位。
6. `UNKNOWN`：0.939 相对 0.938 的 +0.001 因果来源。没有单变量消融或冻结同协议 A/B。
7. `UNKNOWN`：private/final leaderboard 和未来重评分表现。
8. `UNKNOWN`：相同环境重跑能否逐位复现；本轮没有得到启动重跑的授权。

## 安全与外部动作

本轮严格只读访问 Kaggle。计数如下：submission 创建 0、submission retry 0、Notebook 写入/保存/重跑 0、训练 0、Dataset/Model 创建 0、规则接受/报名/组队 0、大型下载 0。

Kaggle output 共列出 307 个唯一路径。只下载四个明确命名的小型审计文件：runtime integrity、frame retention guard report、`run_stats.csv` 和 `validator_results.csv`。没有下载权重、GEFF/Zarr、比赛数据或 `submission.csv`。

日志入库前扫描私钥标记、GitHub token、Kaggle key assignment、Bearer token 和签名 URL，命中 0。仓库内保留的日志与下载原文哈希一致，无需做文本改写。

## 证据索引与完成边界

- 来源清单：`research/20260904_BIOHUB_V19C_COPY_AUDIT_V01/00_source_manifest.jsonl`
- 身份与血缘：`research/20260904_BIOHUB_V19C_COPY_AUDIT_V01/01_notebook_identity_and_lineage.md`
- 逐单元哈希：`research/20260904_BIOHUB_V19C_COPY_AUDIT_V01/02_notebook_cell_audit.csv`
- 方法分析：`research/20260904_BIOHUB_V19C_COPY_AUDIT_V01/03_method_analysis.md`
- 日志清单与分析：`research/20260904_BIOHUB_V19C_COPY_AUDIT_V01/04_runtime_log_inventory.csv`、`05_runtime_log_analysis.md`
- 分数绑定：`research/20260904_BIOHUB_V19C_COPY_AUDIT_V01/06_submission_score_binding.md`
- 冲突与未知：`research/20260904_BIOHUB_V19C_COPY_AUDIT_V01/07_failures_and_unknowns.md`
- 机器摘要：`research/20260904_BIOHUB_V19C_COPY_AUDIT_V01/audit_summary.json`
- 零写入账本：`governance/CODEX_20260904_BIOHUB_V19C_COPY_AUDIT_LEDGER.json`

本报告的内容状态由冻结验证器检查；GitHub 同步是否真正完成，还必须以本地 8 项机器验收、旧 INITIAL_RECON 回归、`main` 远端 HEAD 一致以及固定 commit 的逐文件远端回读为准。单独看到此报告、本地文件存在或 `git push` 返回成功，都不是充分完成证据。
