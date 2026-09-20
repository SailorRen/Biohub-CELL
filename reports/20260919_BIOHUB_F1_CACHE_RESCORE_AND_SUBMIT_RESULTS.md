# F1 缓存评分恢复与正式提交

## 2026-09-20 续接：生产验收通过，准备一次正式提交

准确生产 V1 / SV351084196 已由 API 核验 COMPLETE，页面耗时 12171.7 秒。回收 8 个必要文件；submission.csv 留 ignored，完整 F1 回执用无损 gzip 同步（133285 bytes，解压后 SHA256 与原始字节一致）。其余小型回执、完整输出清单和脱敏日志同步。

独立 CSV 检查共 241020 行（122719 节点、118301 边），四个测试数据集均覆盖 t=0..99，端点/连续时间/入度≤1/出度≤2/重复边检查通过；逐集计数与 run_stats 一致。submission SHA256：da80c6aa879f1531a35088e029cf3f9658108265ee9c74d959d86e64182f6726。冻结权重、源码及 F1 配置一致，80 次 flow 调用全部有预测，训练仍为 0。

原选择器选中 combo(tight55+relaxed9)，内部 proxy=0.9548168641878856，仅是反复使用验证面板的内部结果，不能作 Public 或独立泛化证据。实际 F1 回执尾缀是正常换行；此前从转义展示推测的字面量反斜杠 n 未出现在回收字节中。未修改或重跑 Notebook。

预检：账户 sailorren、参赛有效、提交开放、今日 0/5，完整提交列表没有 F1；准确 G1 submission56270217 仍 COMPLETE / Public 0.948。正式预算尚未消费，提交前先同步本验收证据。

以下保留 9 月 19 日历史记录，历史 RUNNING / NOT_RUN 不是本轮最新状态。

更新时间：2026-09-19T22:11:58.658476+08:00

评分恢复：`CACHE_RESCORE_VERIFIED`。32 份最终图已绑定诊断 V1 / SV351058693 / kernel134976549，16 个 B0/F1 日志分数全部精确一致（差值 0，门槛 1e-10）。原云端状态仍为 ERROR；第一次请求仍为 UNKNOWN。

冻结门槛结论：`DIAGNOSTIC_MIXED_EXPLORATORY`，允许一次探索性生产及随后满足输出验收的一次正式提交。这不是独立泛化验证。

|范围|B0 官方分|F1 官方分|F1−B0|
|---|---:|---:|---:|
|all|0.9434057263411257|0.9452963026993741|+0.0018905763582484|
|44b6|0.9351292868208174|0.9333259364129790|-0.0018033504078384|
|6bba|0.9450315056946966|0.9482427618461325|+0.0032112561514359|

总体 adjusted edge 提升 +0.001890576358248408；division Jaccard 不变。B0/F1 分别使用自身边计数权重 5988/5978，未平均逐视野总分。总体 n/n_adj=8，各胚胎=4。

|范围/臂|edge TP/FP/FN|division TP/FP/FN|权重|
|---|---|---|---:|
|all/B0|5539/237/212|2/1/10|5988|
|all/F1|5541/227/210|2/1/10|5978|
|44b6/B0|1404/83/65|1/1/3|1552|
|44b6/F1|1404/86/65|1/1/3|1555|
|6bba/B0|4135/154/147|1/0/7|4436|
|6bba/F1|4137/141/145|1/0/7|4423|

计数为从最终图重新评分取得，非找回旧进程内存。8/8 B0_repeat、F1_off 与 B0 有序图等价，各自引用 B0 评分；B0/F1 共实际评分 16 次，首视野试评分只计算一次。

最终加边 3281、删边 3158；归属详见 final_edge_changes.csv。UNKNOWN 不算负例，官方 FP 不等于生物学错误。重新匹配可能改变未增删边的归属，因此增删 TP 差不等同总 TP 差。

## 资源及复现

仅下载预测图 204784683 bytes（约 195.30 MiB）；GT 91958 bytes 全部复用原有下载并核对哈希，新 GT 下载 0。32 图与完整 GT 留在 ignored downloads，GitHub 仅小型证据。
CPU 单进程最多 2 线程。首视野耗时 3.077s，峰值 521404416 bytes；后续恢复耗时 12.283s，峰值 564428800 bytes，启动预算 1827782656 bytes（当时可用内存的一半以内）。这些不是原 GPU 运行耗时。

tracksdata 固定 0.1.0rc6.dev3+g980c2d30a，全部 Python 文件与本地固定 wheel 比较一致；官方 metrics/division_metrics 保持 075fc5 原字节。CPU numpy/scipy/geff/zarr 与云端版本差异见 resource_start.json；关键 tracksdata 与 polars 一致，16/16 实际评分一致。GT 通过原 IndexedRXGraph 顺序读取，并与既有 8 份有序 GT hash 比较。无 Torch/CUDA 安装、模型调用、训练或完整后处理重放。

flow 覆盖率、邻居分布、运动中间图和旧 GPU 耗时标记 NOT_RECOVERABLE_FROM_FINAL_GRAPHS。替代证据为 FROZEN_SOURCE_PLUS_FINAL_GRAPH_CHANGE：冻结源码、264 输入哈希、权重/配置、8/8 完成日志、关闭等价、最终图变化。没有伪称旧 SILENT_ALL_FALLBACK 断言执行。

## 云端与正式评分状态

Kaggle 生产：RUNNING，V1 / SV351084196 / kernel134988494，ref=sailorren/biohub-f1-flow-prod-20260918。正式 submission：NOT_RUN_WAITING_FOR_PRODUCTION；Public=null。实时刷新 G1 submission56270217 状态 COMPLETE、Public=0.948（显示精度）。生产完成并验收后才可提交准确生产版本；禁止再次诊断。
当前账本 Save & Run=3/3，工程备用=1/1，生产=1/1，正式提交=0/1；失败或未知也计入。Dataset/训练/最终选择修改=0。

## 证据与读取覆盖

完整读取任务与原合同/账本/修订；定向读取 diagnostic_runtime、build 的缓存与评分路径、实际评分包装、官方 metrics.py/division_metrics.py、tracksdata 直接匹配实现、GT 原读取器、save_once/read_run/budget。生产直接路径沿用此前 G1 审读，补核对 selector、CSV schema/端点/覆盖和最终 F1 回执单元。没有执行 Notebook 主流程做本地恢复。

机器复核：tests.json、verify_evidence.py、verification.json；生产入口人工回执测试接受有效恢复并拒绝错误 hash、未完成评分、预算耗尽、错误版本、失败门槛。原工作区分支/HEAD/干净状态保持，main 未修改。

本次合同先于恢复同步：546a7888ba34bb47385b9fa381f6bc60189a4c0d；评分脚本先于真实评分冻结并同步：96504be（完整 SHA 可由分支历史解析）。生产写入前再次同步全部恢复证据并固定提交回读。文件交付与生产/正式评分分别核验。

关键文件位于 experiments/BIOHUB_F1_FLOW_KAGGLE_20260918/score_recovery_20260919/：contract_amendment.json、input_manifest.json、script_freeze.json、checkpoints/（32）、per_view.csv、final_edge_changes.csv、results.json、receipt.json。

## 本轮实际生产请求与续接

2026-09-19 22:13:03（上海）预记并发送 F1-03，HTTP200，wire_sends=1，创建生产 V1，准确 SV351084196 从页面 Edit 链接绑定。SDK 回读 RUNNING；源码字节哈希 a7cb7f8a0da5b5055594779019ebb3ab688e3ce5916079d23b59574b628720b1，全部代码单元与冻结候选一致。平台序列化后字节与本地 Notebook 不同，未将两个哈希混用。

生产前证据固定提交 bf1139342160e8efd86b82f3414470fb05a5e71d，GitHub 98/98 文件字节一致后才发送请求。第一次 UNKNOWN、第二次诊断 ERROR 均未覆盖，共享备用仍用满 1/1。

生产尚在运行，本轮没有正式分数，完整实验目标尚未完成。G1 历史普通运行 8168.5 秒仅作等待背景，不是 F1 耗时预测。当前没有生产输出，不能把启动成功当验收完成。

下一次在同一隔离分支执行以下只读命令续接原对象（不是启动器）：

```bash
cd /private/tmp/biohub-f1-recovery-20260919
/opt/anaconda3/envs/ml/bin/python3 experiments/BIOHUB_F1_FLOW_KAGGLE_20260918/read_run.py production
```

若仍 RUNNING/PENDING，保留 Public=null；不要运行 save_once.py（3/3 已耗尽）。若 ERROR，则真实终止，无备用。若 COMPLETE，需要补齐生产输出回收/验收后，按原代码竞赛流程对准确生产 V1/SV351084196 正式提交一次。旧 read_run.py 当前只记录生产清单，不回收生产回执/CSV；不能仅凭其状态输出直接提交。

必要输出：f1_production_receipt.json、sprint_production_receipt.json、bidirectional_production_runtime_integrity.json、ppsweep_selected.json、run_stats.csv 与 ignored submission.csv（以真实清单文件名为准）。验证输入/权重哈希、源代码绑定、F1 启用、schema、端点、逐数据集覆盖与 submission SHA256。冻结的 F1 回执写出语句追加的是字面量反斜杠 n；读取时可仅对该已知尾缀用 JSONDecoder.raw_decode 严格解析，保留原始字节哈希，不修改/重跑生产 Notebook。

正式提交已有授权，无需再征求；提交前重新核对账户/比赛/日限额/已有 submission，永久预记 ledger.formal_submission_requests=1，再单次 competition_submit_code(kernel=准确ref,kernel_version=1,file_name='submission.csv')。绑定正式 submission ID 后只读刷新 Public，与准确 G1 submission56270217 同精度比较；结果未知不可重发，不修改最终选择。没有创建会话外监控。

文件交付阶段：固定提交 9690f7f1b2f65defe44ce4120d74a9c559bea12d 已完成 GitHub 104/104 文件字节回读；见 score_recovery_20260919/github_readback.json。后续提交仅保存该回读回执，本地最终回读另留 ignored .task-verification。

最终页面观测：2026-09-19T22:17:02.276925+08:00，准确生产页面仍显示 Running for 208.9s，Edit 链接保持 /edit/run/351084196。此时正式评分未执行。
