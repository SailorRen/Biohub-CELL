# V19C 运行日志分析

## 完整日志读取状态

`MEASURED`：已完整读取目标 Notebook Version 1 当前可取得的 Kaggle runtime log。保留文件为 111,209 bytes，SHA-256 `a3d3de4a9644f943f37a4804740cd4c44ed0d658d76a47df62a1793fb868634d`，解析为 622 个 JSON event：547 个 stdout、75 个 stderr。首末 event time 为 6.0456 与 1904.138 秒，日志覆盖时长约 1,898.092 秒，即 31 分 38.09 秒。

本地保留的 `runtime_log_sanitized.log` 在写入仓库前扫描了私钥标记、GitHub token、Kaggle key assignment、Bearer token 和签名 URL，命中数为 0，因此无需修改内容；证据文件与下载日志字节一致。这里的“脱敏”表示通过冻结规则做了扫描，不表示可以检测所有可能的秘密格式。

## 状态、错误与警告

`MEASURED`：Kaggle status API 返回 `KernelWorkerStatus.COMPLETE`。完整日志中未发现 Traceback、Exception、fatal 或明确 failed event，因此错误计数为 0。

stderr 中共有 32 个 warning header event：

- 28 个来自 scikit-image plugin 基础设施的 `FutureWarning`；
- 2 个 debugger warning；
- 2 个 nbconvert/Mistune 相关 `SyntaxWarning`。

日志最后由 nbconvert 写出 307,322-byte 的执行后 Notebook 和 1,159,280-byte 的 HTML。上述 warning 没有导致运行失败，但 `COMPLETE` 仅证明平台任务结束，不能单独证明方法正确或分数提升。

## 运行阶段与耗时

`MEASURED`：运行先进行离线依赖 materialize、权重和支持代码完整性检查，再进入生产 test inference。可见两张 Tesla T4，四个测试视频被分成两个独立 CUDA shard。测试预测耗时日志值为 8.85 分钟。

随后 Notebook 选择四个 held-out train sample 运行本地 validator。为防止与 test stem 混用，日志明确排除四个与测试目录同名的 train stem；选择结果覆盖两个 embryo-type prefix，每个 prefix 两个样本，四个样本都含至少一个 GT division。验证预测耗时为 7.68 分钟。

这些阶段耗时是单次 Kaggle 日志观察值，不能外推到其他硬件、数据版本或重新运行。

## 测试输出规模

四个测试视频的最终 topology 为：

| dataset | nodes | edges | division parents | max indegree | max outdegree |
|---|---:|---:|---:|---:|---:|
| `44b6_0113de3b` | 25,475 | 24,757 | 50 | 1 | 2 |
| `44b6_0b24845f` | 18,548 | 17,342 | 26 | 1 | 2 |
| `6bba_05b6850b` | 6,044 | 5,844 | 4 | 1 | 2 |
| `6bba_05db0fb1` | 69,291 | 67,181 | 45 | 1 | 2 |

`MEASURED`：合计 119,358 nodes、115,124 edges，对应 submission 的 234,482 rows。回执给出其内容哈希，但本任务没有下载 `submission.csv`。

`run_stats.csv` 还记录每个视频的 raw/final nodes、raw/final edges、gap、motion relink、safe division、DeepCenter 检查、短轨迹处理和 line-fit 计数。它们是运行诊断，不是评分指标。

## 帧保留 guard

`MEASURED`：生产四个 test video 共 400 帧，guard report 记录 65 个 fallback frame：

- `44b6_0b24845f`：64/100；
- `6bba_05b6850b`：1/100；
- 其余两个：0/100。

完整日志出现 194 个 `BIOHUB_RETENTION_GUARD` event，但去重后有 97 条；重复来自 shard 日志的双重呈现，并且后半还含 validator 样本事件。去重记录的 retention 最小约 0.45307、中位数约 0.85385、最大约 0.89905，所有 guard 记录均显示 `use_primary=true`。生产 test 的权威逐视频回退计数使用 guard report 的 65/400，而不是把 validator 和重复日志混入。

## 本地 validator 结果

`MEASURED`：日志汇总四个选择样本的 adjusted edge Jaccard 为 `0.9214`、division Jaccard 为 `0.2000`，按 Notebook 中的代理公式得到 `PROXY_SCORE=0.9414`。逐样本 adjusted edge Jaccard 分别约为 0.9364、0.8084、0.9832 和 0.8313；只有一个样本匹配到 division true positive。

这不是 public leaderboard score，原因包括：

1. 只使用按规则选择的四个 train sample，不是冻结的全量或多折评估；
2. `t_true` 来源是 `estimated_number_of_nodes`；
3. 样本选择主动要求含 GT division，分布不代表 hidden test；
4. public `0.939` 来自 Kaggle submission 评分系统，不来自本地 validator。

因此不能把 `0.9414` 与 `0.939` 做误差分析或宣称“本地验证预测了榜分”。它只能用于检查管线能运行、指标代码产生有限值以及观察所选样本的失败模式。

## 配置状态的日志判读

早期日志打印 `Reverse-time association weight: 0.200`，guard report 又记录 `bidirectional_primary_weight: 0.3`。但实际 fusion-applied 行和最后的 resolved pipeline manifest 都显示 `0.15` 且模式为 `harmonic_probability`。同理，guard report 的 detector、secondary detection 与 ILP disappearance 参数也与 source/运行行冲突。

本报告按以下优先级判读本次激活状态：最终 resolved manifest与实际运行调用行 > source 的冻结 guard > 辅助 guard report > 普通说明性打印。冲突本身保留在失败与未知清单中，不通过静默选择一个值掩盖。

## 日志能够与不能够证明的内容

日志和小型输出共同支持：

- `MEASURED`：双 seed 权重存在、双向融合激活、DeepCenter 成功加载；
- `MEASURED`：四个 test video 均生成图，submission schema/拓扑检查完成；
- `MEASURED`：完整日志无运行错误，存在非致命 warning；
- `MEASURED`：本地 validator 在四个选择样本上完成；
- `MEASURED`：production integrity 回执声明 test inference 未读取 ground truth。

它们不能证明：

- `UNKNOWN`：模型是如何训练、训练数据是否完全合规；
- `UNKNOWN`：0.939 相对其他版本的因果提升来源；
- `UNKNOWN`：未来重跑是否逐位复现；
- `UNKNOWN`：私有榜或最终榜得分；
- `UNKNOWN`：辅助 guard report 中陈旧配置产生的具体原因。
