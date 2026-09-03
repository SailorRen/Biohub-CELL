# 官方比赛事实（staging 草稿）

状态：`OFFICIAL_ROUTES_7_OF_7_FULL_VISIBLE_MAIN_READ`。本文件仅来自 Kaggle 官方页面/API；动态字段均附抓取时点。

## 已核实事实

- 目标：在 3D+time 显微影像中检测细胞、跨时间关联、识别分裂并重建谱系。
- Sponsor：Biohub SF。
- 时间线（官方 Timeline；除另有说明均为 23:59 UTC）：2026-06-29 开始；2026-09-22 报名截止；2026-09-22 组队合并截止；2026-09-29 最终提交截止。
- 奖金总额：$60,000（$18k/$12k/$8k/$6k/$6k/$5k/$5k）。
- Code competition 限制：CPU ≤12h、GPU ≤12h、internet disabled；允许免费且公开可得的外部数据和预训练模型；输出名须为 `submission.csv`。
- Overview 动态值：抓取时显示 3,300 Participants、3,029 Teams；Leaderboard 另一个稍晚快照的末名为 3,032。两者均为时点观察，不强行对齐。
- 本轮 Kaggle 写入：submission=0、Notebook Version save=0、training=0、rule acceptance=0、Dataset create=0。

## 7 个强制入口实读证据

| route | read_status | main chars | main SHA-256 | UTC | Asia/Singapore |
|---|---|---:|---|---|---|
| overview | FULL_VISIBLE_MAIN_READ | 6,070 | `7d8713bf67adf1500571e28544ca3f8abf858d5d1e15dfa5d76b22efbf404654` | 2026-09-03T08:30:17.003Z | 2026-09-03, 16:30:17 GMT+8 |
| data | FULL_VISIBLE_MAIN_READ | 4,572 | `201c69d8344caaa0a2d9be1f7df225d3c3982466c7e2918b2f6b3808773de081` | 2026-09-03T08:29:56.128Z | 2026-09-03, 16:29:56 GMT+8 |
| code | FULL_VISIBLE_MAIN_READ | 3,443 | `1f358d73375aefbe705e9b6c1cfdaf42dc35f53fe6b4692274bf24c8285dfb2d` | 2026-09-03T08:18:29.409Z | 2026-09-03, 16:18:29 GMT+8 |
| discussion | FULL_VISIBLE_MAIN_READ | 3,504 | `ec1558909dfa3dc564be8207716bcc38c51d53f39ed6f4831296b9dba5857998` | 2026-09-03T08:18:34.197Z | 2026-09-03, 16:18:34 GMT+8 |
| leaderboard | FULL_VISIBLE_MAIN_READ_WITH_VIRTUAL_SCROLL_THROUGH_RANK_149 | 3,392 | `659c23ea56abcc0998c60a150784e87bc8ecefcea9765bcdc446bdbcf6f3468b` | 2026-09-03T08:32:44.130Z | 2026-09-03, 16:32:44 GMT+8 |
| rules | FULL_VISIBLE_MAIN_READ | 36,794 | `6ba45819135a1bd942cc6b0842cb4e0468bdaf12a998bae1f561a699b410bcef` | 2026-09-03T08:30:21.783Z | 2026-09-03, 16:30:21 GMT+8 |
| models | FULL_VISIBLE_MAIN_READ | 624 | `94567a218ad25674e1d876d4d5854ddcf9fa4806559c73b41ea38d068bb39088` | 2026-09-03T08:18:53.965Z | 2026-09-03, 16:18:53 GMT+8 |

另有 Kaggle API `competition_list_pages` 返回的 8 个正文页全部读取并记录哈希：rules、Description、Evaluation、Timeline、data-description、Prizes、Code Requirements、abstract；见 `evidence/official_pages_metadata.csv`。

## 重要边界

- Rules 页面显示账号此前已接受规则；这是既有账号状态，本轮未执行接受或报名。
- Leaderboard 页面也显示账号既有 0.885 行及一个正在评分的既有 submission；均不是本轮动作，也未绑定为本项目结果。
- 官方文件元数据仅取得 5,400 条后在第 28 页 HTTP 429；因此文件级清单是 `PARTIAL_METADATA_LIST_RATE_LIMITED`，不能称全量。
