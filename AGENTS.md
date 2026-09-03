# Biohub-CELL 项目执行规则

## 项目边界

- 本仓库只服务 Kaggle 比赛 `biohub-cell-tracking-during-development`。
- 所有研究结论、任务、实验、日志和证据必须同步到本 GitHub 仓库；未同步内容不得作为项目正式结论。
- 未来原始数据和训练原则上留在 Kaggle 云端。GitHub 只保存代码、配置、小型证据和报告。
- 不得提交原始比赛数据、大型外部数据、模型权重、`submission.csv`、凭据、Cookie、Token 或环境变量。

## 外部操作禁令

- 未经用户明确授权，不得提交 Kaggle submission。
- 未经用户明确授权，不得启动训练、长时间推理或创建、保存 Kaggle Notebook Version。
- 未经用户明确授权，不得创建 Kaggle Dataset、接受比赛规则、报名或组队。
- 只读研究不得修改其他 GitHub 仓库或任何外部来源。

## 证据与表述

- 搜索标题、搜索摘要、Kaggle 卡片和 GitHub 搜索摘要只能用于发现来源，不能证明正文方法或结论。
- 不得以推测代替数据；未知写为 `UNKNOWN`，阻断写明原因。
- Notebook 只有取得实际源码并检查全部代码单元，才可标记相应 `FULL_NOTEBOOK_SOURCE_*` 状态。
- GitHub 仓库必须记录固定 branch、commit、实际读取文件；只读 README 只能标记 `README_ONLY`。
- 所有 Kaggle 分数必须绑定具体 Notebook Version、ScriptVersionId 或 submission，并记录读取位置和时间。
- 评分补丁前后的分数必须区分；页面残留的 Best Score 不等于当前有效分数。
- 事实分类仅使用项目约定的 `OFFICIAL_FACT`、`HOST_CONFIRMED`、`SOURCE_CODE_VERIFIED`、`MEASURED`、`AUTHOR_CLAIM`、`COMMUNITY_REPORT`、`INFERENCE`、`UNKNOWN`。

## 完成门禁

- 所有“完成”声明必须通过机器验收、Git 状态核验和 GitHub 权威远端回读。
- `git push` 成功、本地文件存在或脚本退出 0，都不是单独的完成证据。
- 未达到冻结合同的最低检索或深读数量时，必须标记 `PARTIAL_RESEARCH_BLOCKED`，不得写成 `COMPLETED_VERIFIED`。
- 最终状态只服从 `tasks/CODEX_20260903_BIOHUB_CELL_INITIAL_RECON_CONTRACT.json` 及验证报告。

