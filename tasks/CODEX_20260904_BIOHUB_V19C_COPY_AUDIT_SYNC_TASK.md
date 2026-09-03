# 执行任务：Biohub V19C 复制版本源码、日志与分数血缘审计及 GitHub 同步

## 用户请求

用户于 2026-09-04（中国上海时区）提供 Kaggle Submissions 页面截图，并要求：

> 这是我从公开代码区复制的方案，目前最高分数是 v19c 的 0.939，读取这个方案和相关的 log 日志，然后同步 GitHub。

## 精确目标

- 比赛：`biohub-cell-tracking-during-development`
- 用户复制版本：`sailorren/biohub-v19c-public0939-sis14-only`
- 截图显示：`Version 1`、`Succeeded`、Public Score `0.939`
- 公开上游候选：`alioman/biohub-v19c-public0939-sis14-only`
- 目标仓库：`SailorRen/Biohub-CELL`
- 目标分支：`main`

截图只属于用户提供的观察证据，不能单独证明 Notebook 源码、ScriptVersionId、submission ID、运行日志内容或分数血缘。必须使用 Kaggle 只读接口重新读取并绑定。

## 允许范围

1. 只读查询 Kaggle Notebook、Kernel status、Kernel source、Kernel output/log 和本人 submission 历史。
2. 下载小型 Notebook 源码和运行日志到临时目录，仅用于审计。
3. 检查 Notebook 全部 Markdown/code cells，记录逐单元字节数和 SHA-256。
4. 比较用户复制版本与公开上游版本的源码哈希、cell 哈希和参数差异。
5. 阅读完整可取得日志，记录阶段、耗时、输出、告警、错误、资源与最终状态。
6. 将原创分析、小型脱敏日志证据、哈希、来源清单、验证报告同步至目标 GitHub 仓库。

## 禁止范围

- 不得创建或保存新的 Kaggle Notebook Version。
- 不得启动或重跑 Notebook、训练或长时间推理。
- 不得创建 Kaggle submission、Dataset、Model 或其他平台对象。
- 不得接受规则、报名、组队或选择最终 submission。
- 不得下载完整比赛数据、大型 Dataset、模型权重、`.zarr`、`.geff` 或 `submission.csv`。
- 不得在公开 GitHub 中提交 Kaggle 凭据、Cookie、Token、环境变量、签名 URL 或其他秘密。
- 公开 Notebook 的许可证未闭合时，不得再分发完整 `.ipynb` 或源码正文；只保存哈希、结构、短摘录和原创分析。

## 证据分类

- `SOURCE_CODE_VERIFIED`：由实际 Notebook 源码和逐 cell 审计支持。
- `MEASURED`：由 Kaggle 当前只读 API、完整日志或本轮计算直接支持。
- `AUTHOR_CLAIM`：源码注释或上游作者文字声明，未由本轮复现。
- `INFERENCE`：根据源码与日志推导，必须明确写出推理边界。
- `UNKNOWN`：平台未暴露、无法绑定或证据不足。

## 预期产物

- `research/20260904_BIOHUB_V19C_COPY_AUDIT_V01/00_source_manifest.jsonl`
- `research/20260904_BIOHUB_V19C_COPY_AUDIT_V01/01_notebook_identity_and_lineage.md`
- `research/20260904_BIOHUB_V19C_COPY_AUDIT_V01/02_notebook_cell_audit.csv`
- `research/20260904_BIOHUB_V19C_COPY_AUDIT_V01/03_method_analysis.md`
- `research/20260904_BIOHUB_V19C_COPY_AUDIT_V01/04_runtime_log_inventory.csv`
- `research/20260904_BIOHUB_V19C_COPY_AUDIT_V01/05_runtime_log_analysis.md`
- `research/20260904_BIOHUB_V19C_COPY_AUDIT_V01/06_submission_score_binding.md`
- `research/20260904_BIOHUB_V19C_COPY_AUDIT_V01/07_failures_and_unknowns.md`
- `research/20260904_BIOHUB_V19C_COPY_AUDIT_V01/audit_summary.json`
- `governance/CODEX_20260904_BIOHUB_V19C_COPY_AUDIT_LEDGER.json`
- `reports/20260904_BIOHUB_V19C_COPY_AUDIT_REPORT_V01.md`
- `reports/20260904_BIOHUB_V19C_COPY_AUDIT_VERIFY.json`
- `scripts/verify_v19c_copy_audit.py`

## 完成标准

只有同时满足以下条件，才允许把本轮同步任务写为 `COMPLETED_VERIFIED`：

1. 用户复制版本身份和 Version 1 已由 Kaggle 只读接口确认。
2. 实际 Notebook 源码已取得，全部 code cells 已检查并哈希。
3. 最新运行日志已完整取得、逐行检查并固化安全的小型证据。
4. `0.939` 已绑定具体 submission 记录；若仅有截图或卡片分数，则不得通过。
5. 公开上游与复制版本的相同/不同点基于源码哈希，不凭标题推断。
6. 许可证未确认时不提交完整上游或复制 Notebook 源码。
7. Kaggle submission、Notebook 写入、训练、Dataset 创建和大型下载计数均为 0。
8. 新验证器全部通过，原 INITIAL_RECON 验证器继续通过。
9. GitHub `main` 与本地 HEAD 一致，工作区干净，新交付物从远端逐文件回读且 SHA-256 一致。

任一关键条件无法取得证据时，必须写为 `PARTIAL` 或 `BLOCKED`，并保留精确失败记录；不得用截图、文件存在或命令退出 0 替代内容验证。
