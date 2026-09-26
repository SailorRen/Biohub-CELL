# XR0 最后两候选正式评分

任务：BIOHUB_XR0_LAST_TWO_20260926_V01，遵循 SCORE_FIRST_V02。当前 RUNNING_BATCH，尚未完成两份正式评分。实时观测时间以账本各对象为准。

| 候选 | Notebook（owner 均 sailorren） | Version / SV | 普通运行 | submission ID | 正式状态 | Public / 相对 XR0 0.953 |
| --- | --- | --- | --- | --- | --- | --- |
| XD960 | biohub-xr0-xd960-last-two-20260926 | V1 / 353050916 | COMPLETE，输出验收 PASS | 56585147 | PENDING | UNKNOWN / UNKNOWN |
| XRL9 | biohub-xr0-xrl9-last-two-20260926 | V1 / 353050971 | 已受理，页面 Queued，尚无输出 | 无 | 未提交 | UNKNOWN / UNKNOWN |

XD960 正式请求时间：2026-09-27 01:22:53（上海），平台回执时间 01:22:55。两份普通运行分别于 00:48:37、00:48:52 请求。暂未观察到直接错误。排队和等待评分不计为失败，也不能据此推断算法表现。

## 已核验事实

- 固定交付 commit b05a5e115111cfae66424f0b2e7eac09c1b914b8 的任务原文 9571 字节及 SHA256 核对通过。
- 沿用 XR0 十二个有效单元：XD960 仅主检测阈值及守卫改为 0.960；XRL9 仅在参数消费前设置 RELAXED_UM=9.0。保留其余算法；附加只读 head 哈希、参数消费计数和轻量输出验收。
- 本地必要检查 18/18 通过，包含 nbformat、逐单元 AST、允许的算法差异、参数顺序、实际 support 源码动态补丁与缓存先于 head。
- 代码冻结 commit 2a574a0127abdfc46fb8fd33f3d0cc5778a77b3a：关键文件远端逐字节回读 26/26 一致。
- 两个实际保存版本源码与冻结候选一致，Private、GPU 开启、Internet 关闭；实际镜像摘要均为 37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461。
- XD960 普通 GPU 运行 1479.6 秒，实际双 Tesla T4；三个主权重断言与 head 哈希通过。保存版本主输入 V10、secondary V2、DeepCenter V5；head 按 /1 固定，官方数据集当前版本为 1，实际挂载哈希一致。
- XD960 独立 CSV 验收通过：238585 行，完整测试覆盖、字段、时序、坐标及图结构通过。SHA256 为 f698481ed9273e367dae3efce20c5c96cece170cc0286c98d8bd94b36922072c。CSV 未入 Git。
- XD960 head、低阈缓存与实际检测参数消费已核验；repair_fallback=0、deadline_degraded=0 为实际报告值。告警限依赖弃用、转换器转义和 Torch JIT 缓存目录，未发现推理中断。
- 正式 ID 回执与账本在 commit 2a86a2b4f9abb2e321c535726efcf6995f623ef0 远端回读 2/2 一致。

## 额度与排重

启动前核实当前账号 sailorren；提交窗口剩余 2 次，无活动事件。GPU 界面 00:59/30 小时；API 总量 21600 秒、reserved=0，timeUsed 序列化异常，按较小总量保守规划。并发上限未明确公开；两个本批普通运行均已受理，第二份排队原因 UNKNOWN。

完整团队 54 条 submission 与本账号比赛 Notebook 列表未见本批配置已有正式请求。旧 XD960 V1/SV352620382 仅约 9 秒 Quick Save、无输出，保持不动。新 slug 的只读 403 未被当作不存在的证据。

已用：完整运行请求 2/2，工程备用 0/1，正式请求 1/2；训练、Dataset 写入、最终选择变更均为 0。不得重复请求 XD960 正式提交，也不得重启排队中的 XRL9。

## 尚待完成

继续查询已有 XRL9 V1/SV353050971；普通运行成功后核验真实输出与部署，再正式提交一次精确版本。随后仅查询两个准确 submission ID，待正式终态齐备再统一比较。当前不能声称两候选完成评分或提分。

证据及账本目录：experiments/BIOHUB_XR0_LAST_TWO_20260926_V01/。详细原始状态、观测时间、请求回执及预算以 platform_ledger.json 和候选验收文件为准。
