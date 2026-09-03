# community_history_data 合并交接

## 结果状态

`COMPLETED_VERIFIED` 仅适用于本 staging 子任务的文件生成与 schema/证据自检；不表示任何 Dataset 已获规则准入，也不表示模型、训练、推理、submission 或分数完成。

## 精确计数

- Reddit native search：8 个合同查询，8/8 结果页为 `FULL_PAGE_BODY_READ`，每页观察到 7 张可见结果卡。
- `site:reddit.com`：8 个合同查询 + 1 个补充未加引号查询；搜索引擎未稳定暴露全局总数，query log 只写观察命中/下界。
- Reddit 主题深读：6 个；5 `FULL_THREAD_READ`、1 `PARTIAL_THREAD_READ`。评论实际载入 28/28 个报告评论，但 partial 主题仍显示更多回复。
- 科学/软件来源路由：18 次；13 `FULL_PAGE_BODY_READ`、2 `README_ONLY`、3 `BLOCKED`。成功目标范围 15。
- 历史 Kaggle 候选：10；深研 6。深研证据为 6 个官方比赛页 + 6 个官方 writeup/作者 discussion，共 12 `FULL_PAGE_BODY_READ`。
- Kaggle Dataset 搜索：20 个合同关键词 × 页 1–2 = 40 个查询；搜索失败 0；去重候选 185。15 个 page-2 响应为官方 CLI 的空结果，不是错误。
- Dataset 详情：35 个高相关对象尝试；23 个 metadata+文件列表成功，2 个 metadata-only，10 个初始详情调用受阻。未下载内容。
- Dataset 浏览器：30 个唯一页；28 `FULL_PAGE_BODY_READ`、2 `BLOCKED`。最终 inventory 35 行：28 full、1 metadata-only、5 rate-limited、1 blocked。
- Dataset 风险：35/35 `rule_eligibility_checked=false`；35/35 `DO_NOT_USE_PENDING_RULE_REVIEW`。

## 可合并产物

- `14_reddit_and_web_inventory.csv`：44 行。
- `15_external_scientific_sources.md`。
- `16_similar_kaggle_competitions.csv`：10 行，6 行 `deep_read=true`。
- `17_historical_solution_research.md`。
- `18_kaggle_datasets_inventory.csv`：35 行，28 个 `FULL_PAGE_BODY_READ`。
- `00_source_manifest.community_history_data.jsonl`：123 个唯一 source IDs。
- `19_claims_evidence_matrix.community_history_data.csv`：10 行。
- `20_access_failures.community_history_data.md`。
- `21_search_query_log.community_history_data.csv`：82 行，覆盖 `reddit_native`、`reddit_site_search`、`scientific_web`、`similar_kaggle`、`kaggle_datasets`。
- 页面证据：`evidence/browser_dataset_page_reads.jsonl` 与 `evidence/browser_reddit_science_history_reads.jsonl`。

## 自检

- 14/16/18/19/21 均包含 `scripts/verify_research_bundle.py` 要求的完整表头；数据行非空。
- manifest 123 条、source ID 唯一、read status 全在根 allowlist、evidence paths 全部可从 repository root 解析。
- 14/16/18 的每个 `source_id` 均能回连到本 manifest 片段中的唯一记录。
- manifest 中所有 `FULL_*` 项均有正 bytes 与合法 64 位 SHA-256。
- claims 的所有 source IDs 均存在于本 manifest 片段，evidence paths 全部存在。
- 16 表满足候选不少于 8、deep read 不少于 5；18 表满足 full Dataset 页面不少于 25。

## 边界与阻断

- Kaggle API/CLI 在 429 协调指令后保持停止，没有自动重试。
- bioRxiv 两个路由仅显示安全验证页；没有宣称全文已读。
- 一条 Reddit 主题仍有隐藏回复，保持 `PARTIAL_THREAD_READ`。
- 所有外部 Dataset 的来源、时间、current-test 重合、许可与规则兼容性尚未形成完整准入闭环，因此全部禁用等待规则审查。
- 仅写本 staging；未修改 canonical 文件，未 commit、未 push。
