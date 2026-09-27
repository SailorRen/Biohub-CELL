# XRL9 两波正式评分执行记录

状态：PREPARED；尚无本批运行或正式请求。

任务交付 commit：`ffd6a3b6036037c76372787b487f6d800454e8e4`，任务原文 SHA256：`aa66741012266c7e0c30d186f2ac2819206cfa567e4b0ae0591bad15c4908d6d`。

母版 XRL9：Public 0.955，submission 56587392，V1 / SV353050971。仅作为本轮比较基线。

| 首批候选 | DET | relaxed µm | 状态 |
|---|---:|---:|---|
| R9D960 | 0.960 | 9.0 | LOCAL_PREPARED |
| R8D965 | 0.965 | 8.0 | LOCAL_PREPARED |
| R9D955 | 0.955 | 9.0 | LOCAL_PREPARED |

三份已完成 27 项检查：Notebook 格式、13 代码单元 AST、完整原算法继承及允许差异、参数先后消费、实际 support 源码动态补丁和低阈缓存先于 head。静态检查不等于 GPU 推理或正式得分。

排重读取团队 56 条正式提交以及本人 49 份 Biohub Notebook 的源码配置，未发现三份准确配置。当前 owner sailorren，界面显示正式剩余 5 次、19 小时重置、0 Active Events。GPU 界面显示已用 01:43 / 30 hrs；API 配额总数为 21600s 且 used 字符串格式异常，两者不宣称完全一致，按较小总量估计约剩 4h17。固定输入与原镜像、T4×2、Internet off 保持。

预算：计划完整运行最多 5，工程备用最多 1；正式请求累计最多 5。失败或响应未知均记账不盲重发。首批正式终态齐备后才冻结并执行第二波最多 2 份。

准确版本、SV、submission ID 与时刻随后记入 platform_ledger.json；每份完成普通推理并通过真实 CSV、图结构、CUDA、权重和模块检查后才正式提交。本次不更改最终选择。CSV、权重和原始数据不入 GitHub。
