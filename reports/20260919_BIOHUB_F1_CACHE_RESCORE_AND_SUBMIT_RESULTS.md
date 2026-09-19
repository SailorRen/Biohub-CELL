# F1 缓存评分恢复与正式提交

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

Kaggle 生产：NOT_RUN_PREWRITE_CHECKPOINT。正式 submission：NOT_RUN；Public=null。实时刷新 G1 submission56270217 状态 COMPLETE、Public=0.948（显示精度）。生产完成并验收后才可提交准确生产版本；禁止再次诊断。
当前账本 Save & Run=2/3，工程备用=1/1，生产=0/1，正式提交=0/1；失败或未知也计入。Dataset/训练/最终选择修改=0。

## 证据与读取覆盖

完整读取任务与原合同/账本/修订；定向读取 diagnostic_runtime、build 的缓存与评分路径、实际评分包装、官方 metrics.py/division_metrics.py、tracksdata 直接匹配实现、GT 原读取器、save_once/read_run/budget。生产直接路径沿用此前 G1 审读，补核对 selector、CSV schema/端点/覆盖和最终 F1 回执单元。没有执行 Notebook 主流程做本地恢复。

机器复核：tests.json、verify_evidence.py、verification.json；生产入口人工回执测试接受有效恢复并拒绝错误 hash、未完成评分、预算耗尽、错误版本、失败门槛。原工作区分支/HEAD/干净状态保持，main 未修改。

本次合同先于恢复同步：546a7888ba34bb47385b9fa381f6bc60189a4c0d；评分脚本先于真实评分冻结并同步：96504be（完整 SHA 可由分支历史解析）。生产写入前再次同步全部恢复证据并固定提交回读。文件交付与生产/正式评分分别核验。

关键文件位于 experiments/BIOHUB_F1_FLOW_KAGGLE_20260918/score_recovery_20260919/：contract_amendment.json、input_manifest.json、script_freeze.json、checkpoints/（32）、per_view.csv、final_edge_changes.csv、results.json、receipt.json。
