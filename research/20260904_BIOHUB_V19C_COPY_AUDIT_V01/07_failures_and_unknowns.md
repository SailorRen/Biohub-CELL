# V19C 失败、冲突与未知项

## 已发生的读取失败

1. `UNKNOWN`：本轮再次读取公开上游 `alioman/biohub-v19c-public0939-sis14-only` 时，GetKernel 返回 HTTP 403。没有绕过权限，也没有把失败写成“来源不存在”。内容比较改用 2026-09-03 已固定并通过仓库验收的完整 source/cell 哈希证据。
2. `UNKNOWN`：当前可见 Kaggle API 没有返回 ScriptVersionId。报告保留 `UNKNOWN_NOT_EXPOSED`，不从 kernel ID 或 submission ID 推算。

## 身份与血缘未知

- `UNKNOWN`：目标元数据 `kernel_sources=[]`，Kaggle 没有声明其 platform fork parent。
- 用户说明该方案从公开代码区复制，12/12 cell source 又与公开候选固定捕获完全一致；这支持内容来源说明，但不等于平台 provenance 已闭合。
- 公开 source response 与私有拉取 `.ipynb` 的整文件 SHA 不相同。由于载体与 Notebook 外层元数据不同，本报告使用逐 cell source equality，不声称两个文件字节相同。

## 时间字段冲突

`MEASURED`：`kernels list` 与 GetKernel 返回不同的 `lastRunTime`：前者是 `2026-09-03 09:54:55.453000`，后者是 `2026-08-31T17:09:53.551Z`。GetKernel 值也与 submission 日期不自然地分离。平台没有解释字段语义，故两者都不作为 submission 的唯一绑定键；绑定改用具体 submission 记录及 description。

## 配置证据冲突

`dual_seed_frame_retention_guard_report.json` 与 source/最终 resolved manifest 至少有四处不一致：detector threshold、secondary detection weight、ILP disappearance weight、bidirectional weight。该回执还明确标记 `candidate_unverified`，缺少 required receipt，并禁止 quality promotion 的 push/submit。因此：

- topology、fallback frame、submission rows/hash 可作为该回执中的运行观察；
- 激活配置以 source guard、实际运行行和最终 resolved manifest 为主；
- `UNKNOWN`：guard report 为什么保留旧值，以及生成它的具体中间代码路径，本任务未动态重跑定位。

## 许可证与再分发

`UNKNOWN`：公开 Notebook 的许可证没有由当前已读 Kaggle 元数据/源码接口明确暴露。即使 source 可以读取，也不推断允许公开再分发。完整公开和私有 `.ipynb` 都没有提交，GitHub 仅保存哈希、结构、原创分析和用户运行的小型证据。

依赖 Dataset、权重和支持代码的各自许可证、训练数据来源也未在本任务中完整核验。报告中的模型哈希只支持身份，不支持版权或训练数据合规结论。

## 指标与因果未知

- `UNKNOWN`：0.939 的 private/final leaderboard 表现；private score 未暴露。
- `UNKNOWN`：相对 0.938 的 +0.001 是否来自 V19C 的任一特定机制。没有同工件单变量消融。
- `UNKNOWN`：本地 proxy `0.9414` 与 public `0.939` 的可比性。验证集只有四个选择样本且 `t_true` 使用估计节点数。
- `UNKNOWN`：未来 Kaggle 评分补丁、数据更新或重评分后的数值。
- `UNKNOWN`：重新运行在相同 Kaggle 镜像中是否 bitwise reproducible；本轮遵守禁令，没有启动重跑。

## 日志局限

完整日志有 622 个 event、无 traceback 或 fatal event，但这只证明当前取得的运行记录没有显式运行错误。`COMPLETE` 和无错误都不证明算法语义无 bug。32 个 warning header 被保留；它们看起来不致命，但未通过重跑逐个消除。

日志中的 retention guard event 有重复，并混合 production test 与 validator 阶段。生产回退统计采用独立 guard report 的 65/400，不把 194 条原始日志 event 直接当作 194 个不同帧。

## 本任务没有执行的动作

- Kaggle submission 创建或 retry：0；
- Notebook Version 创建、保存或重跑：0；
- 训练任务：0；
- Kaggle Dataset/Model 创建：0；
- 规则接受、报名或组队：0；
- 大型数据、GEFF/Zarr、权重或 `submission.csv` 下载：0。

这些未执行项属于本任务冻结边界，不是缺失工作。
