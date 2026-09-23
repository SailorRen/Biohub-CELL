# CPU 离线调用链：批量准备依赖冲突

最新续接结果见文末：V2/SV352083775 的 CPU 批量 worker 已实际执行，依赖解析失败，未进入离线链。以下旧连接失败证据保留。

任务 `BIOHUB_CPU_OFFLINE_CHAIN_20260923_V01`。本轮未取得离线部署或短片段推理结果，状态为 **BLOCKED_PREPARATION_SESSION_CONNECTION**。上轮 `NEEDS_HUMAN_REVIEW` 保留。

## 实际停点与直接证据

2026-09-23 16:09（上海时间）向既有 `sailorren/biohub-cpu-small-probe-20260923`（Kernel135480603）派发一次准备单元执行。派发前确认会话 off、加速器 None、Internet on、比赛输入及 Primary 固定 V10。旧 V1/SV352060904 未修改；未创建新保存版本。

编辑器持续显示 `Draft Session Starting`，活动事件却显示该 Notebook 的 `Interactive Session / Running: 10 minutes`。准备单元最初显示 `Cell execution is queued`，未取得任何本轮 Python 回执。浏览器实际日志多次出现：

- `Connection lost, reconnecting in 0 seconds.`
- `Connection lost, reconnecting in 24 seconds.`
- `Could not get context`

仅刷新一次已保存编辑器，续接同一个会话，仍未恢复连接；未重复执行代码、未重新启动会话。目录读取最终只显示 `.virtual_documents`，没有可确认的 `cpu_bundle`。不能以界面 Running 声称模型或安装代码运行成功，也没有证据把本次问题归因为 CPU 配额不足。

停止时，编辑器 Run 菜单的 Stop session 禁用；通过活动事件中**该 Notebook 唯一事件**的 Stop Session 释放。随后回读显示 `Cancelled`、`Draft Session off (run a cell to start)`、`0 Active Events`。没有取消其他旧作业。具体时间和脱敏证据见实验目录的 `ledger.json`、`browser_connection_errors.json`、`session_release_evidence.json`、`resource_events.jsonl`。

## 已准备的代码及其证据边界

独立 worktree 来源为 `cdccdefeb6b1e7fb1fcaf3a73ee205d3ef6ba3e3`，任务正文先以 `9af0c705e79e9f45ac1de36ed9cfdc528582a7f7` 发布到 `codex/cpu-offline-chain-20260923`，任务与冻结合同已从该 commit 逐字节回读（2/2）。原 A/B、队友母版、共享权限和原批账本未修改。

冻结 B SHA256 为 `03e4abd5c80b5724b959bc453352524e276bebcf9aa0c2ffa38f22442d3e2ceb`。本轮本地整理了准备、转换、离线安装、双路径诊断、数值记录和 CSV 结构校验代码；未执行原整本 Notebook。`source/postprocess.py` 的 42 个算法函数/类定义与冻结源码 AST 一致，仅把 DeepCenter 路径发现函数改为已核验路径入口；移除生产自动入口，避免伪造生产回执。源码 diff 和 hash 已保留。静态编译通过不代表云端运行通过，所有新增适配仍待实际运行验证。

样本计划固定为 `44b6_0113de3b` 的 0–15 帧。源码窗口2、短轨门槛6、救援门槛4；计划保留原帧号、原空间尺寸与下采样。原 T100/末帧99来自上轮已核验记录，本轮未重新加载。第15帧不当作真实末帧。不同原生空间尺寸的附加窗口本轮未选择，不能标为尺寸泛化通过。

准备入口使用30分钟父进程硬超时，计划从固定 support wheels 解析版本约束；官方 PyPI 补充固定 OpenVINO2026.4.0 与 telemetry2025.2.0。它们未在本轮实际安装。IR转换、FP32类型回读和重载推理均无本轮执行证据。`cpu_bundle` 未形成可交付的精确 Output，因此没有继续创建离线 Notebook 或派发 Save & Run。

代码中的离线安装只允许 `--no-index --find-links`，诊断设计采用 `selector_mode=FIXED_DIAGNOSTIC_CONFIG`，原选择器未验证。参考和候选均安排独立计算，主编码器后端不同，其余使用原 CPU 调用；这只是待执行代码，不是已完成模块覆盖。代码审阅后仍需真实环境检查，不能直接视为可部署版本。

## 本轮实际测量

| 项目 | 实际状态 |
|---|---|
| 离线安装／首次加载 | NOT_RUN |
| IR转换、落盘、精确Output哈希 | NOT_OBSERVED / NOT_VERIFIED |
| 参考 PyTorch 短片段链 | NOT_RUN |
| 候选 OpenVINO＋PyTorch 短片段链 | NOT_RUN |
| primary、secondary、TTA、关联、融合、DeepCenter、gate、ILP、救援、L030P | 本轮无真实调用证据 |
| 条件模块 | NOT_RUN，不能写成 NOT_TRIGGERED |
| 数值误差、节点／边决策、规范化图差异 | NOT_MEASURED |
| 完整片段墙钟、阶段耗时、峰值RSS | NOT_MEASURED |
| diagnostic_reference.csv / diagnostic_cpu.csv | 未生成、未验收 |
| CPU型号／核数／线程／内存 | 本轮未读取，不能借用上轮作为当前测量 |

## 预算与下一步

新增 CPU 准备会话1/1，执行请求1次（排队后实际执行未确认）；同会话页面刷新1次、释放1次。工程代码修复0/1。带输出 Quick Save0/1，新离线 Notebook0/1，离线 Save & Run0/1。GPU、Colab、训练、完整视频、正式提交、Dataset、购买、共享变更全部0。旧计数不清零。

下一步最小问题是恢复编辑器与 Kaggle CPU 会话的连接。本轮唯一会话请求已经消耗，不能在现授权下再开一轮。应在用户明确授权新的准备会话后续接部署准备；未达到提出“完整单视频验证”的前提，不应直接进入更大规模推理。

本轮只交付阻断证据和待执行适配代码，不宣称短片段CPU调用链通过、完整CPU B、GPU等价、隐藏集时限或正式分数已验证。没有 IR/wheels 的新 Kaggle 部署位置；唯一仍可引用的历史保存版本是 V1/SV352060904，其 Output 不包含本轮部署包。

最终交付按独立分支固定 commit 回读小文件，实际 commit、remote HEAD、字节一致数及 worktree 状态由交付回读结果报告。原视频、权重、张量、IR、wheels、CSV和凭据均未加入Git。


## 2026-09-23 批量准备续接：实际执行后停止

任务 `BIOHUB_CPU_BATCH_PREP_CONTINUE_20260923_V01`。原文先以 `628d861422f1336f81f8e794f2ce6ca8b50643dc` 发布并逐字节回读；启动源码和唯一意图随后同步。空目录展开15个代码／清单文件，哈希与语法检查通过，未在Mac执行模型。

16:52（上海时间）通过官方CLI仅派发一次 `CPU-BATCH-PREP-01`，实际准备版本为 [V2 / SV352083775](https://www.kaggle.com/code/sailorren/biohub-cpu-small-probe-20260923?scriptVersionId=352083775)，Kernel135480603。CLI终态 `KernelWorkerStatus.ERROR`，页面运行时间23秒；准备子程序实际记录6.144秒，不能当作模型算时。第一单元已输出任务ID和源码摘要的STARTED，脚本成功从空目录展开；本轮已补齐批量worker真实启动证据，旧交互连接错误不是本次停点。

直接错误来自离线support wheels依赖解析：

```text
imagecodecs 2026.6.26 depends on numpy>=2.1
The user requested (constraint) numpy==2.0.2
ERROR: ResolutionImpossible
```

这里“user requested”是pip对代码约束文件的称呼，不是用户要求固定NumPy2.0.2。脚本为保留镜像NumPy而施加该约束，与固定support wheel要求冲突。没有证据归因为CPU配额、模型不兼容或浏览器断连。父进程正确非零退出，未打印成功。失败后未修复重跑、未创建离线Notebook。

精确V2 Output已有cpu_bundle启动／错误回执及代码；已下载小JSON和错误摘录、记录字节数与SHA256。未形成IR、wheels部署包、requirements.lock或bundle_manifest，**部署Output验收不通过**，不能把错误回执保存成功当作部署成功。官方CLI精确版本pull返回403；当前源码pull成功且两个代码单元逐一等于提交源码，UI同时核验V2/SV身份。当前回读元数据Private、GPU/TPU false、Internet true、machine_shape None，镜像digest为 `dafd4ce5668bbf1ad422e4c109e0f18c9623c3a7c7f48b0235f13142755c40b9`。请求固定Primary V10；CLI回读省略版本后缀，UI精确版本字段未观察到，不能夸称已独立回读该字段。

模型权重校验、转换、IR落盘重载、PyPI补充阶段均NOT_RUN。参考和候选短片段链、primary/secondary/TTA/关联融合/DeepCenter/gate/ILP/救援/L030P全部NOT_RUN；条件模块不是NOT_TRIGGERED。未生成诊断CSV，数值／决策／图差异、片段耗时与峰值RSS均NOT_MEASURED。离线Notebook Version/SV均无，未进行断网安装。

本批准备SaveRun 1/1、离线SaveRun 0/1、新Notebook0/1、交互会话0、QuickSave0、工程修复0/1。累计保留旧失败交互会话1次，加本次CPU准备批作业1次；其他旧消耗不清零。GPU、Colab、正式提交、Dataset、共享修改均0。作业已ERROR自然结束，没有执行取消其他作业，也没有后台监控。

可复用产物为自包含启动Notebook、15文件源码清单、同版本错误回执和基础镜像包清单；不能复用不存在的IR。后续最小工作是协调NumPy与imagecodecs的固定依赖组合，再由用户决定是否授权新的准备运行；本轮不追加运行。`NEEDS_HUMAN_REVIEW`保留，不宣称短片段链通过。

本次小文件交付沿用研究分支，最终固定commit和逐字节远端回读数量在交付回复中列明。
