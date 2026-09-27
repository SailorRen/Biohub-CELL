# XRL9 两波正式评分执行记录

状态：WAVE1_SCORE_PENDING；报告生成时间 2026-09-27T05:58:35.967724+00:00（UTC）。

任务交付 commit：`ffd6a3b6036037c76372787b487f6d800454e8e4`；原文 SHA256：`aa66741012266c7e0c30d186f2ac2819206cfa567e4b0ae0591bad15c4908d6d`。

MEASURED 基线 XRL9：Public 0.955，submission 56587392，V1 / SV353050971。新候选只有正式 Public 才用于比较。

| 候选 | DET / relaxed µm | Version / SV | submission ID | 状态 | Public | Δ XRL9 | 请求时间 UTC | 最后观测 UTC | 直接错误 |
|---|---|---|---|---|---|---|---|---|---|
| [R9D960](https://www.kaggle.com/code/sailorren/biohub-xrl9-r9d960-20260927) | 0.96 / 9.0 | 1 / 353188100 | 56599443 | SCORE_PENDING | UNKNOWN | UNKNOWN | 2026-09-27T05:55:57.582371+00:00 | 2026-09-27T05:58:17.732395+00:00 | UNKNOWN |
| [R8D965](https://www.kaggle.com/code/sailorren/biohub-xrl9-r8d965-20260927) | 0.965 / 8.0 | 1 / 353188155 | 56599380 | SCORE_PENDING | UNKNOWN | UNKNOWN | 2026-09-27T05:53:06.171876+00:00 | 2026-09-27T05:58:19.867221+00:00 | UNKNOWN |
| [R9D955](https://www.kaggle.com/code/sailorren/biohub-xrl9-r9d955-20260927) | 0.955 / 9.0 | 1 / 353192186 | UNKNOWN | ORDINARY_RUNNING | UNKNOWN | UNKNOWN | UNKNOWN | 2026-09-27T05:58:21.190935+00:00 | UNKNOWN |

预算：已发送 Save & Run 请求 4（含明确失败）；实际受理完整运行 3；工程备用 1/1；正式请求 2/5。第二波最多 2，首批正式结果齐备之前不启动。

三份候选已通过 27 项小型检查：完整 Notebook/13 代码单元、AST、允许差异、参数消费、实际 support 动态补丁、缓存先于 head。冻结源码 commit `00a930ffe17bbda213397a438bc3fd45a0ea4cc0`，32/32 文件远端逐字节回读通过。静态检查不等于运行通过或正式得分。

输入冻结 primary V10、secondary V2、DeepCenter V5、head V1，Private、T4×2、Internet off。两份已受理运行 API 回读源码一致、GPU enabled、原镜像摘要一致；界面通用镜像标题为 Latest，实际摘要另存 ordinary_readback.json。实际挂载版本与完整输出在每份 deployment_check.json / output_check.json 中验收后才提交。

平台已明确返回批处理 GPU 并发上限 2。第三份初次请求被拒绝，无 Version/SV；失败不退账。单对象读取返回 HTTP 500，不作为不存在的证明；随后本人完整 Notebook 列表未发现第三份。空槽后允许使用一次工程备用恢复同一冻结配置。

额度启动前：正式剩余 5 / 19h 重置；GPU UI 已用 01:43 / 30h，API 总额 21600s 且 used 字符串格式异常。按较小总额估计约剩 4h17，不把估计说成精确余额。每次正式请求前另刷新实际额度。

第二批决策：尚未作出；只在首批所有已受理正式请求终态齐备后，根据任务指定范围冻结方案。没有有效分数的错误不当作低分。

不改最终选择、不修改旧账本、不新增训练或 Dataset。CSV、图、原始数据、权重和凭据不入 GitHub。
