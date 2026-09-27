# XRL9 两波正式评分执行记录

状态：WAVE2_ORDINARY_QUEUED；报告生成时间 2026-09-27T17:04:27.863419+00:00（UTC）。

任务交付 commit：`ffd6a3b6036037c76372787b487f6d800454e8e4`；原文 SHA256：`aa66741012266c7e0c30d186f2ac2819206cfa567e4b0ae0591bad15c4908d6d`。

MEASURED 基线 XRL9：Public 0.955，submission 56587392，V1 / SV353050971。新候选只有正式 Public 才用于比较。

| 候选 | DET / relaxed µm | Version / SV | submission ID | 状态 | Public | Δ XRL9 | 请求时间 UTC | 最后观测 UTC | 直接错误 |
|---|---|---|---|---|---|---|---|---|---|
| [R9D960](https://www.kaggle.com/code/sailorren/biohub-xrl9-r9d960-20260927) | 0.96 / 9.0 | 1 / 353188100 | 56599443 | SCORED | 0.955 | +0.0000 | 2026-09-27T05:55:57.582371+00:00 | 2026-09-27T13:17:49.203600+00:00 | 未返回错误 |
| [R8D965](https://www.kaggle.com/code/sailorren/biohub-xrl9-r8d965-20260927) | 0.965 / 8.0 | 1 / 353188155 | 56599380 | SCORED | 0.955 | +0.0000 | 2026-09-27T05:53:06.171876+00:00 | 2026-09-27T13:17:49.203600+00:00 | 未返回错误 |
| [R9D955](https://www.kaggle.com/code/sailorren/biohub-xrl9-r9d955-20260927) | 0.955 / 9.0 | 1 / 353192186 | 56599964 | SCORED | 0.956 | +0.0010 | 2026-09-27T06:08:32.999420+00:00 | 2026-09-27T13:17:49.203600+00:00 | 未返回错误 |
| [R9D950](https://www.kaggle.com/code/sailorren/biohub-xrl9-r9d950-20260927) | 0.95 / 9.0 | 1 / 353314948 | UNKNOWN | ORDINARY_QUEUED | UNKNOWN | UNKNOWN | UNKNOWN | 2026-09-27T17:04:25.318008+00:00 | UNKNOWN |
| [R8D955](https://www.kaggle.com/code/sailorren/biohub-xrl9-r8d955-20260927) | 0.955 / 8.0 | 1 / 353315066 | UNKNOWN | ORDINARY_QUEUED | UNKNOWN | UNKNOWN | UNKNOWN | 2026-09-27T17:04:27.863419+00:00 | UNKNOWN |

预算：已发送 Save & Run 请求 6（含明确失败）；实际受理完整运行 5；工程备用 1/1；正式请求 3/5。第二波最多 2，首批正式结果齐备之前不启动。

三份候选已通过 27 项小型检查：完整 Notebook/13 代码单元、AST、允许差异、参数消费、实际 support 动态补丁、缓存先于 head。冻结源码 commit `00a930ffe17bbda213397a438bc3fd45a0ea4cc0`，32/32 文件远端逐字节回读通过。静态检查不等于运行通过或正式得分。

输入冻结 primary V10、secondary V2、DeepCenter V5、head V1，Private、T4×2、Internet off。三份已受理运行 API 回读源码一致、GPU enabled、原镜像摘要一致；界面通用镜像标题为 Latest，实际摘要另存 ordinary_readback.json。实际挂载版本与完整输出在每份 deployment_check.json / output_check.json 中验收后才提交。

平台已明确返回批处理 GPU 并发上限 2。第三份初次请求被拒绝，无 Version/SV；失败不退账。单对象读取返回 HTTP 500，不作为不存在的证明；随后本人完整 Notebook 列表未发现第三份。空槽后允许使用一次工程备用恢复同一冻结配置。

额度启动前：正式剩余 5 / 19h 重置；GPU UI 已用 01:43 / 30h，API 总额 21600s 且 used 字符串格式异常。按较小总额估计约剩 4h17，不把估计说成精确余额。每次正式请求前另刷新实际额度。

第二批决策（WAVE2_SCORE_FIRST_V02）：按用户固定任务 74ffade，以 R9D955 V1/SV353192186、submission 56599964、Public 0.956 为母版，独立构建 R9D950（DET .950 / relaxed 9）和 R8D955（DET .955 / relaxed 8）。不叠加其他算法；比较基准 .956，仍保留 .955 对照。实时正式余额2；GPU页面已用02:36/30h，接口总额6h存在口径差异，保守估计余3h23。冻结源码和回执先远端回读，再启动两份GPU普通运行；各自验收后立即正式提交，不等首份Public。

不改最终选择、不修改旧账本、不新增训练或 Dataset。CSV、图、原始数据、权重和凭据不入 GitHub。

持续等待方式：ACTIVE_HEARTBEAT。此前后台调度被拒是历史状态；用户随后明确授权值守，现已通过应用工具创建并回读 biohub 值守任务，每15分钟续接本聊天。首波分数已齐。

## 第二波当前执行状态

两份 Save & Run All 均已受理，实际源码与冻结文件一致、GPU启用、Private、Internet off、原镜像摘要一致。平台当前 QUEUED，尚无普通运行完整输出；实际 CUDA/挂载版本/CSV与运行告警验收均待运行完成。第二波正式请求 0/2，submission ID 尚不存在，Public UNKNOWN。

已建立本地应用定时值守（须电脑开机、应用运行）。恢复只查询 R9D950 V1/SV353314948、R8D955 V1/SV353315066；不重复运行，普通请求已达6/6。每份完成后分别核对实际输入和日志、验收CSV，刷新额度并正式提交一次，不等另一份Public。第二波冻结代码 commit 61103113bf333fb7586488103d710c938e92a3d5 已9/9远端逐字节回读。完整任务尚未完成。


## 值守启用回执

观测时间 2026-09-27T16:05:19.268519+00:00（UTC）。自动任务 `biohub` 已创建，配置回读确认 ACTIVE、每15分钟、当前聊天。即时平台只读连通性检查通过：两份准确普通版本仍为 QUEUED；本次未新增正式请求。普通完成并通过验收后分别正式提交一次，随后查询精确ID至终态；响应不明不重发。遇到明确错误通知用户。终态或无合法后续动作时暂停值守。证据：`wave2_automation_receipt.json`。这不代表普通运行或正式评分已经完成。
