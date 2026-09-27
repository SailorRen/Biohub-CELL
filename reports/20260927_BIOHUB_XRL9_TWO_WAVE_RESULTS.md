# XRL9 两波正式评分执行记录

状态：首批运行中；正式请求 0。R9D960 V1/SV353188100，R8D965 V1/SV353188155 已实际 RUNNING。R9D955 被明确拒绝：Maximum batch GPU session count of 2 reached；未取得版本或运行 ID。请求失败保留计账，待空槽且核实无对象后以工程备用处理。

任务交付 commit：`ffd6a3b6036037c76372787b487f6d800454e8e4`，任务原文 SHA256：`aa66741012266c7e0c30d186f2ac2819206cfa567e4b0ae0591bad15c4908d6d`。

母版 XRL9：Public 0.955，submission 56587392，V1 / SV353050971。仅作为本轮比较基线。

| 首批候选 | DET | relaxed µm | 状态 |
|---|---:|---:|---|
| R9D960 | 0.960 | 9.0 | 参见实时账本 |
| R8D965 | 0.965 | 8.0 | 参见实时账本 |
| R9D955 | 0.955 | 9.0 | 参见实时账本 |

三份已完成 27 项检查：Notebook 格式、13 代码单元 AST、完整原算法继承及允许差异、参数先后消费、实际 support 源码动态补丁和低阈缓存先于 head。静态检查不等于 GPU 推理或正式得分。

排重读取团队 56 条正式提交以及本人 49 份 Biohub Notebook 的源码配置，未发现三份准确配置。当前 owner sailorren，界面显示正式剩余 5 次、19 小时重置、0 Active Events。GPU 界面显示已用 01:43 / 30 hrs；API 配额总数为 21600s 且 used 字符串格式异常，两者不宣称完全一致，按较小总量估计约剩 4h17。固定输入与原镜像、T4×2、Internet off 保持。

预算：计划完整运行最多 5，工程备用最多 1；正式请求累计最多 5。失败或响应未知均记账不盲重发。首批正式终态齐备后才冻结并执行第二波最多 2 份。

准确版本、SV、submission ID 与时刻随后记入 platform_ledger.json；每份完成普通推理并通过真实 CSV、图结构、CUDA、权重和模块检查后才正式提交。本次不更改最终选择。CSV、权重和原始数据不入 GitHub。

冻结代码 commit `00a930ffe17bbda213397a438bc3fd45a0ea4cc0`，远端 32/32 文件逐字节回读通过。两份运行源码逐单元相等、GPU enabled、Private、Internet off、API 实际镜像摘要与冻结值一致；日志界面显示 GPU T4×2。界面通用容器标题显示 Latest，实际摘要以 API 读回记录为证，不静默替换镜像。
