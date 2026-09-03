# 访问失败与未暴露字段

本清单由总装脚本从统一来源清单确定性生成。它记录实际访问中的阻断、限流、登录要求、删除、未找到和未暴露状态；不使用搜索摘要补写缺失正文。

受影响来源记录：11。

## KAGGLE_COMPETITION_FILE_METADATA_PARTIAL

- 状态：`RATE_LIMITED`
- 标题：Competition files metadata pages 1-27
- URL：https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/data
- 证据：`research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/staging/official_kaggle/evidence/competition_files_metadata.csv`
- 说明：5400 metadata records; 21748854443 listed data bytes; no competition data bytes downloaded; not complete.

## biohub_royer_initial

- 状态：`BLOCKED`
- 标题：Royer Group initial URL
- URL：https://www.czbiohub.org/royer/
- 证据：`research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/staging/community_history_data/evidence/browser_reddit_science_history_reads.jsonl`
- 说明：初始域名导航超时，后以 biohub.org 版本成功读取。

## biorxiv_zebrahub_abs

- 状态：`BLOCKED`
- 标题：Zebrahub preprint abstract route
- URL：https://www.biorxiv.org/content/10.1101/2023.03.06.531398v1
- 证据：`research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/staging/community_history_data/evidence/browser_reddit_science_history_reads.jsonl`
- 说明：再次只读到安全验证页，未读取论文正文。

## biorxiv_zebrahub_full

- 状态：`BLOCKED`
- 标题：Zebrahub preprint full route
- URL：https://www.biorxiv.org/content/10.1101/2023.03.06.531398v1.full
- 证据：`research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/staging/community_history_data/evidence/browser_reddit_science_history_reads.jsonl`
- 说明：只读到安全验证页，未读取论文正文。

## dataset_candidate_eliork_biohub_geff_label_bundle_v1

- 状态：`RATE_LIMITED`
- 标题：eliork/biohub-geff-label-bundle-v1
- URL：https://www.kaggle.com/datasets/eliork/biohub-geff-label-bundle-v1
- 证据：`research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/staging/community_history_data/dataset_detail_records.json`
- 说明：Metadata/file detail call rate-limited; no automatic retry; DO_NOT_USE_PENDING_RULE_REVIEW.

## dataset_candidate_engadamalmohammedi_biohub_full_eda

- 状态：`RATE_LIMITED`
- 标题：engadamalmohammedi/biohub-full-eda
- URL：https://www.kaggle.com/datasets/engadamalmohammedi/biohub-full-eda
- 证据：`research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/staging/community_history_data/dataset_detail_records.json`
- 说明：Metadata/file detail call rate-limited; no automatic retry; DO_NOT_USE_PENDING_RULE_REVIEW.

## dataset_candidate_justinkim1216_biohub_nnunet_flow_support_v1

- 状态：`RATE_LIMITED`
- 标题：justinkim1216/biohub-nnunet-flow-support-v1
- URL：https://www.kaggle.com/datasets/justinkim1216/biohub-nnunet-flow-support-v1
- 证据：`research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/staging/community_history_data/dataset_detail_records.json`
- 说明：Metadata/file detail call rate-limited; no automatic retry; DO_NOT_USE_PENDING_RULE_REVIEW.

## dataset_candidate_rudispresence_biohub_stabledet_hoct_runtime

- 状态：`RATE_LIMITED`
- 标题：rudispresence/biohub-stabledet-hoct-runtime
- URL：https://www.kaggle.com/datasets/rudispresence/biohub-stabledet-hoct-runtime
- 证据：`research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/staging/community_history_data/dataset_detail_records.json`
- 说明：Metadata/file detail call rate-limited; no automatic retry; DO_NOT_USE_PENDING_RULE_REVIEW.

## dataset_candidate_t2better_biohub_audit_code_v1

- 状态：`RATE_LIMITED`
- 标题：t2better/biohub-audit-code-v1
- URL：https://www.kaggle.com/datasets/t2better/biohub-audit-code-v1
- 证据：`research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/staging/community_history_data/dataset_detail_records.json`
- 说明：Metadata/file detail call rate-limited; no automatic retry; DO_NOT_USE_PENDING_RULE_REVIEW.

## dataset_page_eariosb_trackastra_offline

- 状态：`BLOCKED`
- 标题：Trackastra Offline (wheels + ctc model) | Kaggle
- URL：https://www.kaggle.com/datasets/eariosb/trackastra-offline
- 证据：`research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/staging/community_history_data/evidence/browser_dataset_page_reads.jsonl`
- 说明：页面标题可见，但可访问性主区域未加载，未计入深读。 DO_NOT_USE_PENDING_RULE_REVIEW

## dataset_page_pilkwang_deepcenter_snapshot

- 状态：`BLOCKED`
- 标题：Kaggle: Your Home for Data Science
- URL：https://www.kaggle.com/datasets/pilkwang/biohub-deepcenter-epoch400-snapshot
- 证据：`research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/staging/community_history_data/evidence/browser_dataset_page_reads.jsonl`
- 说明：Kaggle 返回找不到页面；未计入深读。 DO_NOT_USE_PENDING_RULE_REVIEW

## 子任务详细失败账本

统一 manifest 用一条 source 记录表示同一访问面的阻断状态；下列详细账本保留逐次请求失败、隔离上下文和停止重试决定：

- `research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/staging/official_kaggle/access_failures_fragment.md`：官方文件元数据 API 的 33 次 HTTP 429 失败及统一 `RATE_LIMITED` 结论。
- `research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/staging/github_ecosystem/20_access_failures.github_fragment.md`：GitHub 隔离子任务的登录/匿名限流与源文件读取失败。
- `research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/staging/community_history_data/20_access_failures.community_history_data.md`：Reddit、科学页面、历史比赛和 Dataset 的阻断/限流明细。

GitHub 子任务中的登录错误仅描述其早期隔离默认上下文；主任务写入前已独立验证 `gh api user` 为 `SailorRen`，不把隔离失败外推为当前主环境凭据失效。
