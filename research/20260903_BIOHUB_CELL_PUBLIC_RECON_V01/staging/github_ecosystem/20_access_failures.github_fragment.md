# GitHub 访问失败与覆盖限制

## 已观察失败

- `LOGIN_REQUIRED` — 仅本子任务早期默认隔离上下文中的 `gh auth status` / `gh api` 调用返回凭据不可用。它不是主环境当前认证状态：根任务后来在获批环境独立验证 `gh api user` 为 `SailorRen` 且 PASS。没有改 token、没有重新登录。
- `RATE_LIMITED` — 匿名 GitHub REST API 返回 HTTP 403，响应明确为该出口 IP 的 API rate limit exceeded，remaining=0。未把它误写成仓库不存在。
- `BLOCKED` — 默认本地沙箱中的 partial-clone blob 补取首次因 `Could not resolve host: github.com` 失败；随后仅对公开固定提交做获批的只读 blob 读取。没有任何 GitHub 写调用。

## 结果边界

- 深读仓库数：19；最终逐文件读取错误数：66。
- GitHub Code Search 九个大查询仅首屏，状态为 `PARTIAL_FIRST_PAGE_ONLY`；不是完整代码索引。
- `tracksdata in:name` 报告 144 项但只读首屏 10 项，其中 9 项为同名账号的明显主题碰撞；状态为 `PARTIAL_PAGE_1_ONLY_NAME_COLLISION_DOMINATED`。
- 普通网页搜索只保留主要 GitHub 结果，未声称全网穷尽。
- 仓库运行、模型下载、训练、推理、Kaggle 提交及动态分数均 `NOT_RUN`。

## 外部副作用核对

- GitHub commit/push/fork/issue/PR/release：0。
- 外部仓库文件修改：0。
- 持久化的第三方完整源码：0；临时 shallow/partial clones 位于 `/tmp`，持久证据仅为 URL、commit、tree、hash、结构统计与自写摘要。
