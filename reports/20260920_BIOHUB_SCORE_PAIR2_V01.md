# BIOHUB_SCORE_PAIR2_20260920_V01

两臂实际输出复核通过，各一次正式提交已受理并从平台回读。execution=FORMAL_PAIR_ACCEPTED；score=SCORE_PENDING。Public 尚未返回，不能宣称提分或正式评分完成。最终文件交付验证见本批 github_readback.json，其状态只覆盖指定 payload 字节。

## 精确身份和结果

正式状态观测时间：2026-09-21 07:28:31 +08:00（UTC 2026-09-20 23:28:31）。API 为 PENDING；登录页面显示 Notebook Running，链接绑定精确 SV。

|候选|Kernel|版本|ScriptVersionId|submission ID|正式状态|Public|
|---|---:|---|---:|---:|---|---|
|G1|既有母版|V1|350197436|56270217|COMPLETE|0.948|
|S50|135123707|V1|351350449|56407778|SCORE_PENDING|null|
|G58|135123769|V1|351350591|56407804|SCORE_PENDING|null|

S50 正式请求为上海 07:26:30；G58 为 07:28:10。UUID、请求前记录、响应 ID、UTC/上海时间见 platform_ledger.json。两次请求前均 fsync 记账，无不明响应、无重试。已存在的 F1/A18/B22 平台显示均 0.948；三位小数同分不能推断严格排名、隐藏精度或 Private。

## 冻结范围与真实配置

任务固定 93d12faea46c514e4cccdf969c6d56d1545a2aa0；G1 母版 e9c7c63b896812660a78ec55fc3284c10f85e776；复用工具和旧证据 850fafe77eaa6438cae06f9773d1b6a0b3d8c118。唯一 batch_manifest.json 的 SHA-256 为 a1cbf0c88508203932a74ef36e9684e4ca231b64f9b57f9fcfdd92e74d19d918，未修改。

|项|S50|G58|
|---|---|---|
|唯一主动干预|第二模型检测融合 0.80→0.50|最终 GAP_CLOSE_UM 5.0→5.8|
|worker 实际检测权重|0.50|0.80|
|原选择器 selected_label|base|tight55|
|最终 GAP_CLOSE_UM|5.0|5.8|
|DeepCenter safe-div 门槛|0.20|0.20|
|最终 CSV 行数|244199|241314|
|节点 / 边 / 分裂|124276 / 119923 / 78|122810 / 118504 / 73|

保持 DET_THRESHOLD=0.965、secondary edge=0.15、bidirectional edge=0.15、retention=0.90。原选择器未改；S50 的上游变化伴随原选择器实际选择变化，其正式结果应解释为该干预的完整流水线效果。G58 从同次原始预测图重新后处理，最后仅覆盖 gap 距离，输入图哈希不变。

## 最低必要输出复核

两臂当前私有 V1 的全部代码单元与冻结源码一致，输出下载前后再次核对身份与版本。实际下载 CSV 到 Git 外，独立 csv.DictReader 解析并调用固定官方 reader 进行 CPU 往返：schema、当次运行发现的样本覆盖、整数有限坐标、连续行 ID、节点唯一、端点存在、边唯一、相邻时间方向、单父/最多双子全部通过。实际 CSV 原始字节哈希、规范化图哈希、节点/边/分裂计数与回执及最终后处理调用记录一致。检查模型加载日志、三份推理权重和 G1 gate 权重哈希、实际 worker 配置，无静默模型回退。原 retention 保护回退仍保留。

|候选|实际 CSV SHA-256|规范化内容 SHA-256|
|---|---|---|
|S50|39e2fbdd030173921dba9c865326c4adc28e5c53c53c38115d92751e834d69ea|a8caa3098c6fa35b085c3190f4e7f8f12f0ed9c6f1be25488674a022667659bd|
|G58|f2c6bee2000fe495251c0aacff106866e615122619317907f7146414121b72c8|b35ccc37c0377271d8733cf7bf845399ebec8e133c6e7b548e580ceda8b2df03|

两臂规范化内容不同，各自相对所用 G1 对照均有实际变化。G58 使用同次运行保存的原 G1 输出；S50 使用上一批 A18 所存原 G1 输出，重新下载后与归档 SHA-256 01d070e371bb38147d603f5d26e38df782b1c95491d87a0b9210d20cc98bbca9 完全一致。S50 对照的比赛输入字节同源性未重新建立，保留因果比较限制。内容变化、边数变化和普通运行完成均不代表 Public 改善。

证据：各臂 formal_input_collection.json、formal_precheck.json、production_receipt.json；baseline_restoration.json；formal_ui_readback.json；formal_status_snapshot.json。完整 CSV、图、权重、日志未写入 GitHub。

## 预算、额度与保护状态

累计新私有 Notebook 2/2；Save & Run 2/3，共享修复备用未使用；正式 submission 2/2。训练、Dataset 写入、最终选择修改、旧 Notebook 修改或取消均为 0。本次续接未新增普通运行。

两个请求前 API 当日已用分别 3/5、4/5，按接口提交日期的 UTC 窗口核对；确切每日重置时刻未暴露，未假定上海午夜重置。登录 UI GPU 为 16h19m/30h。SDK quota 的 totalTimeAllowed=21600s 与 UI 不一致，保留原始小型记录；其可见 quotaRefreshTime=2026-09-26T00:00:00Z 不冒充每日提交重置时间。S50 前无活跃事件；G58 前仅 S50 一项 Competition submission / Scoring，无普通 Notebook 活跃。提交入口可用，无并发阻断通知。

main、F1 分支、旧 DIVGATE 分支及原用户工作区按 protected_state_final.json 核对。未调整最终选择（页面 0/2 人工选择），未重提既有 G1/F1/A18/B22。

## 同步与后续边界

e8f7d0396cd7aa2af647594bad5367935cc76cec 的冻结代码经 21 文件远端回读后才启动。暂停期间记录保存在 e9594ec8dcbcfbc0c9d6bdb21f18532278ebf932。用户通知完成后恢复工作区；原临时目录消失不改变平台预算，未重新执行 launch_once.py。提交前源码/复核提交 1868c3126dc0f8960e20971bfa4217a5db40005b 经 52 文件 GitHub 固定提交逐字节回读，两条正式请求均绑定此提交。

最终仅同步本批新增/变更的小型证据和本报告，再对固定 payload 回读并提交一次核验回执。未变资产引用旧固定提交，不重新复制旧证据包。

后续只读查分，禁止再次调用 submit_once.py 或 launch_once.py。本批正式请求已达上限。待两臂分数均返回后再集中比较；当前不自动开展下一轮、第三臂、参数扫描或修改最终选择。没有创建轮询或定时任务。
