# 社区、历史比赛与 Kaggle Datasets 访问失败片段

## 状态

本片段是只读失败账本。失败不解释为“来源不存在”或“没有相关内容”；只有页面明确返回 not found 时才写页面不可用。未执行大型下载，也未在限流后自动重试 Kaggle API/CLI。

## Manifest 中的受阻来源

- `biohub_royer_initial`：`https://www.czbiohub.org/royer/` 导航超时，`BLOCKED`，0 bytes；随后替代官方域名 `https://biohub.org/royer/` 成功读取，记录为独立来源 `biohub_royer`。
- `biorxiv_zebrahub_full`：bioRxiv `.full` 路由只显示安全验证页，235 bytes，`BLOCKED`；未把验证页当成论文正文。
- `biorxiv_zebrahub_abs`：bioRxiv 摘要路由再次只显示安全验证页，235 bytes，`BLOCKED`。已发表版本的 PubMed 摘要成功读取，但不能冒充 bioRxiv 全文覆盖。
- `dataset_page_eariosb_trackastra_offline`：页面标题可见，但可访问性 `main` 未加载，0 bytes，`BLOCKED`；CLI 元数据与文件列表曾成功，因此 Dataset inventory 保留为 `METADATA_ONLY`。
- `dataset_page_pilkwang_deepcenter_snapshot`：Kaggle 页面明确返回找不到页面，76 bytes，`BLOCKED`；CLI 同一对象返回 403。

## Kaggle Dataset API/CLI 限流

35 个高相关对象的详情尝试中，23 个同时取得 metadata 与文件列表，2 个仅取得 metadata，10 个详情调用受阻。之后通过浏览器把部分受阻对象升级为全文页面证据。仍无详情元数据的五个 inventory 行标为 `RATE_LIMITED`：

- `justinkim1216/biohub-nnunet-flow-support-v1`
- `eliork/biohub-geff-label-bundle-v1`
- `engadamalmohammedi/biohub-full-eda`
- `t2better/biohub-audit-code-v1`
- `rudispresence/biohub-stabledet-hoct-runtime`

原始 429/403 stderr 位于 `evidence/kaggle_cli/dataset_details/`，并由 `dataset_detail_records.json` 绑定 UTC/新加坡时间、响应字节和 SHA-256。收到并发限流协调指令后，Kaggle API/CLI 保持停止，没有自动重试。

## Reddit 初始访问失败

- Reddit native search 首次出现 CAPTCHA，随后通过已登录浏览器正常读取 8 个搜索结果页。初始失败的独立精确时间未保存，时间字段保持 `UNKNOWN`，不伪造时间。
- Reddit `/search.json` 的命令行访问返回网络安全阻断提示；未绕过限制，改用可见浏览器页面。该失败没有被解释为搜索结果为零。

## 搜索结果计数边界

`site:reddit.com` 搜索引擎没有稳定暴露全局总数；query log 中的数值是实际返回的相关命中或下界，`reported_total` 保持 “not exposed”。Reddit native search 的 7 是可见结果卡片数，不代表全站总量。

## 对完成状态的影响

- Dataset 页面深读下限已达到：28 个 `FULL_PAGE_BODY_READ`，超过合同要求的 25；另有 1 个 `METADATA_ONLY`、5 个 `RATE_LIMITED`、1 个页面 `BLOCKED`，共 35 行 inventory。
- 科学来源中 15 个全文/目标范围成功，bioRxiv 两个路由受阻；因此 bioRxiv 本身仍是证据缺口。
- Reddit 有 5 个 `FULL_THREAD_READ` 和 1 个 `PARTIAL_THREAD_READ`；后者虽载入 12/12 个已报告评论，但页面仍显示更多回复。
- 本线总体可交付，但外部数据使用资格一律保持 `DO_NOT_USE_PENDING_RULE_REVIEW`。
