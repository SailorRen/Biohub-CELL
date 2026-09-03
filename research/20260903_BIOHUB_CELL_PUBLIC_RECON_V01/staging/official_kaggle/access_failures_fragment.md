# Kaggle 只读访问失败片段（供父任务合并）

## 结论

- 阻断 source_id：`KAGGLE_COMPETITION_FILE_METADATA_PARTIAL`，manifest 状态 `RATE_LIMITED`。
- 文件元数据取得 27 页 × 200 = 5,400 条；第 28 页 HTTP 429。官方 data 页时点总量为 24,886，故缺口是相对页面时点总量的 19,486 条，不能写成 `NOT_FOUND`，也不能宣称全量。
- 初始 collector 共记录 33 次 HTTP 429：competition files 1、leaderboard 1、Kaggle Code list 25、Discussion list 6。
- 收到限流后停止高频自动重试。冷却后仅运行一次受控的 GetKernel 源码读取队列（4 秒间隔、首个 429 即停），30/30 成功且无 429；这不补齐 competition files 的缺页。
- Leaderboard、Code discovery 与 official routes 后续通过登录态浏览器只读路径取得；Discussion 由父任务另行负责。本轮物理 Kaggle 写入均为 0。

完整机器可读证据：`research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/staging/official_kaggle/evidence/failure_ledger.json`、`research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/staging/official_kaggle/search_query_log.csv`。

## 原始失败逐项

| # | UTC | Asia/Singapore | source_type | endpoint | page | sort_order | error |
|---:|---|---|---|---|---:|---|---|
| 1 | 2026-09-03T08:06:31.436576+00:00 | 2026-09-03T16:06:31.436576+08:00 | competition_file_metadata | competitions/files | 28 | name | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/competitions.CompetitionApiService/ListDataFiles` |
| 2 | 2026-09-03T08:06:32.339166+00:00 | 2026-09-03T16:06:32.339166+08:00 | leaderboard | competitions/leaderboard | 1 | public_score_desc | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/competitions.CompetitionApiService/GetLeaderboard` |
| 3 | 2026-09-03T08:06:33.135685+00:00 | 2026-09-03T16:06:33.135685+08:00 | kaggle_code | kernels/list | 1 | scoreDescending | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/kernels.KernelsApiService/ListKernels` |
| 4 | 2026-09-03T08:06:34.788756+00:00 | 2026-09-03T16:06:34.788756+08:00 | kaggle_code | kernels/list | 1 | voteCount | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/kernels.KernelsApiService/ListKernels` |
| 5 | 2026-09-03T08:06:36.255803+00:00 | 2026-09-03T16:06:36.255803+08:00 | kaggle_code | kernels/list | 1 | hotness | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/kernels.KernelsApiService/ListKernels` |
| 6 | 2026-09-03T08:06:37.089939+00:00 | 2026-09-03T16:06:37.089939+08:00 | kaggle_code | kernels/list | 1 | dateRun | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/kernels.KernelsApiService/ListKernels` |
| 7 | 2026-09-03T08:06:39.111224+00:00 | 2026-09-03T16:06:39.111224+08:00 | kaggle_code | kernels/list | 1 | dateCreated | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/kernels.KernelsApiService/ListKernels` |
| 8 | 2026-09-03T08:06:41.376897+00:00 | 2026-09-03T16:06:41.376897+08:00 | kaggle_code | kernels/list | 1 | relevance | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/kernels.KernelsApiService/ListKernels` |
| 9 | 2026-09-03T08:06:42.700298+00:00 | 2026-09-03T16:06:42.700298+08:00 | kaggle_code | kernels/list | 1 | relevance | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/kernels.KernelsApiService/ListKernels` |
| 10 | 2026-09-03T08:06:43.570048+00:00 | 2026-09-03T16:06:43.570048+08:00 | kaggle_code | kernels/list | 1 | relevance | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/kernels.KernelsApiService/ListKernels` |
| 11 | 2026-09-03T08:06:44.385771+00:00 | 2026-09-03T16:06:44.385771+08:00 | kaggle_code | kernels/list | 1 | relevance | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/kernels.KernelsApiService/ListKernels` |
| 12 | 2026-09-03T08:06:45.859126+00:00 | 2026-09-03T16:06:45.859126+08:00 | kaggle_code | kernels/list | 1 | relevance | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/kernels.KernelsApiService/ListKernels` |
| 13 | 2026-09-03T08:06:46.709769+00:00 | 2026-09-03T16:06:46.709769+08:00 | kaggle_code | kernels/list | 1 | relevance | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/kernels.KernelsApiService/ListKernels` |
| 14 | 2026-09-03T08:06:48.249986+00:00 | 2026-09-03T16:06:48.249986+08:00 | kaggle_code | kernels/list | 1 | relevance | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/kernels.KernelsApiService/ListKernels` |
| 15 | 2026-09-03T08:06:49.835983+00:00 | 2026-09-03T16:06:49.835983+08:00 | kaggle_code | kernels/list | 1 | relevance | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/kernels.KernelsApiService/ListKernels` |
| 16 | 2026-09-03T08:06:51.468146+00:00 | 2026-09-03T16:06:51.468146+08:00 | kaggle_code | kernels/list | 1 | relevance | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/kernels.KernelsApiService/ListKernels` |
| 17 | 2026-09-03T08:06:56.249918+00:00 | 2026-09-03T16:06:56.249918+08:00 | kaggle_code | kernels/list | 1 | relevance | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/kernels.KernelsApiService/ListKernels` |
| 18 | 2026-09-03T08:06:57.069131+00:00 | 2026-09-03T16:06:57.069131+08:00 | kaggle_code | kernels/list | 1 | relevance | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/kernels.KernelsApiService/ListKernels` |
| 19 | 2026-09-03T08:06:57.899857+00:00 | 2026-09-03T16:06:57.899857+08:00 | kaggle_code | kernels/list | 1 | relevance | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/kernels.KernelsApiService/ListKernels` |
| 20 | 2026-09-03T08:06:58.671785+00:00 | 2026-09-03T16:06:58.671785+08:00 | kaggle_code | kernels/list | 1 | relevance | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/kernels.KernelsApiService/ListKernels` |
| 21 | 2026-09-03T08:07:00.007827+00:00 | 2026-09-03T16:07:00.007827+08:00 | kaggle_code | kernels/list | 1 | relevance | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/kernels.KernelsApiService/ListKernels` |
| 22 | 2026-09-03T08:07:00.822628+00:00 | 2026-09-03T16:07:00.822628+08:00 | kaggle_code | kernels/list | 1 | relevance | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/kernels.KernelsApiService/ListKernels` |
| 23 | 2026-09-03T08:07:02.291417+00:00 | 2026-09-03T16:07:02.291417+08:00 | kaggle_code | kernels/list | 1 | relevance | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/kernels.KernelsApiService/ListKernels` |
| 24 | 2026-09-03T08:07:03.170064+00:00 | 2026-09-03T16:07:03.170064+08:00 | kaggle_code | kernels/list | 1 | relevance | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/kernels.KernelsApiService/ListKernels` |
| 25 | 2026-09-03T08:07:03.976858+00:00 | 2026-09-03T16:07:03.976858+08:00 | kaggle_code | kernels/list | 1 | relevance | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/kernels.KernelsApiService/ListKernels` |
| 26 | 2026-09-03T08:07:05.458539+00:00 | 2026-09-03T16:07:05.458539+08:00 | kaggle_code | kernels/list | 1 | relevance | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/kernels.KernelsApiService/ListKernels` |
| 27 | 2026-09-03T08:07:06.290955+00:00 | 2026-09-03T16:07:06.290955+08:00 | kaggle_code | kernels/list | 1 | relevance | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/kernels.KernelsApiService/ListKernels` |
| 28 | 2026-09-03T08:07:07.132462+00:00 | 2026-09-03T16:07:07.132462+08:00 | kaggle_discussion | competitions/topics | 1 | hot | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/competitions.CompetitionApiService/ListCompetitionTopics` |
| 29 | 2026-09-03T08:07:07.976497+00:00 | 2026-09-03T16:07:07.976497+08:00 | kaggle_discussion | competitions/topics | 1 | top | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/competitions.CompetitionApiService/ListCompetitionTopics` |
| 30 | 2026-09-03T08:07:08.808102+00:00 | 2026-09-03T16:07:08.808102+08:00 | kaggle_discussion | competitions/topics | 1 | new | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/competitions.CompetitionApiService/ListCompetitionTopics` |
| 31 | 2026-09-03T08:07:09.638452+00:00 | 2026-09-03T16:07:09.638452+08:00 | kaggle_discussion | competitions/topics | 1 | recent | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/competitions.CompetitionApiService/ListCompetitionTopics` |
| 32 | 2026-09-03T08:07:11.230461+00:00 | 2026-09-03T16:07:11.230461+08:00 | kaggle_discussion | competitions/topics | 1 | active | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/competitions.CompetitionApiService/ListCompetitionTopics` |
| 33 | 2026-09-03T08:07:13.071201+00:00 | 2026-09-03T16:07:13.071201+08:00 | kaggle_discussion | competitions/topics | 1 | relevance | `HTTPError: 429 Client Error: Too Many Requests for url: https://api.kaggle.com/v1/competitions.CompetitionApiService/ListCompetitionTopics` |
