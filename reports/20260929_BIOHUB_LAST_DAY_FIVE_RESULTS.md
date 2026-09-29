# 最后一天五候选执行记录

任务 BIOHUB_LAST_DAY_FIVE_20260929_V01；固定任务提交 d97e29c72f223169af6fc62c3ab74d2a47b5e09e；分支 codex/last-day-five-20260929。
母版 DIV04_READMIT940 / V1 / SV353458552 / submission 56626891 / Public 0.958；SHA256 ac3651a886a11ecab5e89e8e2a80e10f8b4547b7b4775a6a75e437d8e2ea8035。

五份均独立从唯一母版生成；除单因素配置、对应守卫断言、候选与任务回执标识外，保留其余代码。0.94625 全精度保留；RL8 两种 flow 路径通过实际函数合成检查。构建检查 60 项，readmit 合成检查 5 份；全部 13 单元已读取/AST 检查，2—11 单元与母版字节相同，未重做科学效果验证。普通运行完成后仍须验证实际输出与挂载。

## 当前状态
观察：2026-09-29T03:57:53.335557+00:00（UTC）。stage=ROLLING_SCORE_PENDING。普通请求 5/5，正式请求 3/5，工程备用 0/1。

|候选|ILP/readmit/relaxed|Version|SV|submission|普通状态|正式状态|Public|Δ0.958|
|---|---|---|---|---|---|---|---|---|
|DIV06_READMIT940|0.6/0.94/9.0|1|353755204|56661592|COMPLETE|SubmissionStatus.PENDING|None|UNKNOWN|
|DIV03_READMIT940|0.3/0.94/9.0|1|353755286|56661753|COMPLETE|SubmissionStatus.PENDING|None|UNKNOWN|
|DIV04_READMIT930|0.4/0.93/9.0|1|353758519|56661944|COMPLETE|SCORE_PENDING|None|UNKNOWN|
|DIV04_READMIT94625|0.4/0.94625/9.0|1|353758544|None|RUNNING|NOT_SUBMITTED|None|UNKNOWN|
|DIV04_READMIT940_RL8|0.4/0.94/8.0|1|353761942|None|NOT_REQUESTED|NOT_SUBMITTED|None|UNKNOWN|

## 实时资源与排重

首次页面读取显示 sailorren、正式余额 5 次、约 21 小时后重置；截止上海 2026-09-30 07:59。活动事件为 0。GPU 页面 04:49 / 30 hrs，官方 SDK 原始 timedelta 总额 108000 秒、已用 17356.864 秒、预留 0 秒。SDK to_dict() 的 timedelta 序列化丢失 days，误显示 totalTimeAllowed=21600s；必须用 total_seconds()，保留原响应和规范化数值，不虚构资源。

API 已分页枚举本人 131 个 Notebook，其中 60 个 Biohub 源码逐项读取配置；团队完整提交 66 项，无下一页。五个固定新配置未发现已有本人对象，团队近期记录未见本批对象。精确配置/输入/源码列表见 preflight.json；每次发送另作即时排重与资源核对。最多两普通槽，正式请求不串行等 Public。

## 最终选择与边界

本轮初读平台显示手动选择 **0/2**，手动选中 submission ID 列表为空；页面说明不足两份时 Kaggle 自动选高分，不能据此预填具体自动选择 ID。56626891 和 56638061 的两个 0.958 对象继续保留。只读核对，不勾选或取消。

旧两批 5/5 账本保持原字节；旧 ILP 批前两次未逐次刷新 GPU 余额缺口保留，本轮每次正式请求重新读取 GPU 与正式余额。新模型训练、Dataset 写入、最终选择修改均为 0。无自动后台调度、无第六算法候选。UNKNOWN/null 不冒充已受理或低分；超过 0.958 才是新增 Public 提升，不保证 Private。
