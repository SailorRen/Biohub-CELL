# 执行任务：Biohub V19C ScriptVersionId 346969653 源码、日志与优化空间审计及 GitHub 同步

## 用户请求

用户提供 Kaggle 精确链接：

`https://www.kaggle.com/code/sailorren/biohub-v19c-public0939-sis14-only?scriptVersionId=346969653`

并要求只读取得该方案的内容、运行日志及相关文件，分析能否以此方案为基础继续优化，最终将分析报告同步 GitHub。

## 精确目标

- 比赛：`biohub-cell-tracking-during-development`
- Notebook ref：`sailorren/biohub-v19c-public0939-sis14-only`
- 用户指定 ScriptVersionId：`346969653`
- 目标仓库：`SailorRen/Biohub-CELL`
- 目标分支：`main`
- 任务性质：只读源码/日志/小型输出审计与优化机会分析，不执行优化实验。

## 需要回答的问题

1. 用户给出的 ScriptVersionId 是否能由 Kaggle 只读接口绑定到目标 Notebook 和具体版本？
2. 该固定版本的实际源码结构、模型、参数、推理流程和后处理机制是什么？
3. 完整运行日志和小型输出暴露了哪些时间、资源、错误、告警、回退、拓扑与验证信号？
4. 当前 0.939 分数与该固定版本或 submission 的绑定强度如何，哪些字段仍未暴露？
5. 在不凭空承诺提升的前提下，是否存在可执行的优化空间？
6. 候选优化的证据、预期方向、主要风险、独立验证门和停止条件分别是什么？

## 允许范围

1. 使用 Kaggle 官方 CLI/API 对目标 ref、ScriptVersionId、version metadata、source、status、output inventory、runtime log 和本人 submission 历史做只读访问。
2. 将固定版本完整 Notebook source 下载到临时目录，仅用于逐 cell 静态审计、哈希、参数提取和结构比较。
3. 完整读取 runtime log；只下载明确命名且体积小的 JSON、CSV 或文本审计输出。
4. 对源码做 AST/静态分析，对日志和小型表格做可复现统计。
5. 复用仓库内 2026-09-04 V19C 前序审计作为对照，但必须重新绑定用户给出的 ScriptVersionId，不能把旧结论自动当作当前结论。
6. 生成原创优化分析、证据清单、候选优先级和验证计划。
7. 将任务合同、分析报告、小型安全证据、验证器与账本提交并推送到 `SailorRen/Biohub-CELL` 的 `main`。

## 禁止范围

- 不得启动、重跑或保存 Kaggle Notebook Version。
- 不得创建、重试或选择 Kaggle submission。
- 不得启动训练、长时间推理或超参数搜索。
- 不得创建 Kaggle Dataset、Model 或其他平台对象。
- 不得接受规则、报名、组队或更改比赛设置。
- 不得下载比赛原始数据、完整 Dataset、模型权重、GEFF、Zarr 或 `submission.csv`。
- 不得把优化候选、静态推断或本地 proxy 写成已实现、已验证或已提升 leaderboard 分数。
- 不得向 GitHub 提交完整 `.ipynb`、未经确认许可的大段源码、凭据、Cookie、Token、环境变量或签名 URL。
- 不得修改其他 GitHub 仓库。

## 证据分类

- `OFFICIAL_FACT`：官方比赛规则、指标或平台定义；仅在实际读取权威来源后使用。
- `HOST_CONFIRMED`：Kaggle 主机/API 对对象身份、版本、状态或输出的当前只读返回。
- `SOURCE_CODE_VERIFIED`：由固定版本实际源码及逐 cell 审计直接支持。
- `MEASURED`：由完整日志、小型输出或本轮可复现统计直接支持。
- `AUTHOR_CLAIM`：Notebook 说明、注释或回执自报，未被独立运行复现。
- `COMMUNITY_REPORT`：公开作者或社区描述；不能替代当前源码和日志。
- `INFERENCE`：基于多个证据推导的优化判断，必须附验证门。
- `UNKNOWN`：平台未暴露、读取失败或证据不足。

## 预期产物

- `research/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_V01/00_source_manifest.jsonl`
- `research/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_V01/01_version_identity_and_lineage.md`
- `research/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_V01/02_source_cell_audit.csv`
- `research/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_V01/03_runtime_log_inventory.csv`
- `research/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_V01/04_runtime_and_artifact_analysis.md`
- `research/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_V01/05_optimization_opportunities.csv`
- `research/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_V01/06_prioritized_optimization_plan.md`
- `research/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_V01/07_risks_and_unknowns.md`
- `research/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_V01/audit_summary.json`
- `research/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_V01/evidence/kernel_version_metadata.json`
- `research/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_V01/evidence/runtime_log_sanitized.log`
- `governance/CODEX_20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_LEDGER.json`
- `reports/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_REPORT_V01.md`
- `reports/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_VERIFY.json`
- `scripts/verify_v19c_sv346969653_optimization_audit.py`

## 分析质量要求

每项优化候选必须至少记录：

1. 候选 ID 和优先级；
2. 当前观察到的瓶颈或风险；
3. 建议改变的单一主变量；
4. 证据分类；
5. 预期影响方向，不虚构提升幅度；
6. 离线验证协议；
7. Kaggle 平台验证前置门；
8. 回归风险与停止条件；
9. 状态必须是 `CANDIDATE_NOT_EXECUTED`。

候选优先级不能只按直觉排列，应综合：证据强度、预期收益方向、实现复杂度、算力成本、过拟合风险、现有日志暴露的失败模式，以及能否用冻结 A/B 验证。

## 完成标准

只有同时满足以下条件，才允许把本轮报告同步任务写为 `COMPLETED_VERIFIED`：

1. `346969653` 已通过 Kaggle 只读接口与目标 Notebook/version 做身份核对；如果接口不能完全绑定，必须精确标记证据缺口。
2. 固定版本实际 source 已取得，所有 code cell 均检查、哈希并完成 AST/静态审计。
3. 可取得的完整 runtime log 已读取、解析、哈希并通过秘密扫描。
4. output inventory 已读取；仅允许下载明确命名的小型证据文件。
5. 优化结论明确区分可优化性判断、候选方案和未经执行的实验，不声称已经提分。
6. 至少三项优化候选拥有源码或日志证据、验证协议、风险和停止条件。
7. Kaggle submission、Notebook 写入、训练、Dataset/Model 创建和大型下载计数均为 0。
8. 新验证器通过，前序 V19C 审计与 INITIAL_RECON 验证器继续通过。
9. GitHub `main` 与本地 HEAD 一致，工作区干净，冻结交付物从固定远端 commit 逐文件回读且 SHA-256 一致。

任一关键证据无法取得时，使用 `PARTIAL`、`BLOCKED` 或 `UNKNOWN`，不得以用户提供的链接、页面标题、文件存在、命令退出 0 或旧报告替代当前版本的实际读取。
