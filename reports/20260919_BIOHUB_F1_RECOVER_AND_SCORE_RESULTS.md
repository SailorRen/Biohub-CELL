# F1 恢复与评分：诊断已启动，结果待回收

B0 诊断分 **null**，F1 诊断分 **null**，差值 **null**。F1 正式 submission / 生产 Version / Public 均为 **null / NOT_RUN**。准确 G1 submission **56270217** 本轮 API 读取为 COMPLETE、Public **0.948**。本轮结论为 **DIAG_RUNNING**，不是算法成功、失败或正式评分完成。

截至上海时间 **2026-09-19 20:17:25** 发起的最后一轮读取，诊断 `sailorren/biohub-f1-flow-diag-20260918` **V1 / SV351058693 / kernel134976549** 为 RUNNING；输出列表完整但为空，尚无结果文件。每个阶段本会话有界读取后停止，不建立自动监控；已有 Kaggle 作业继续在平台运行。本报告是续跑交付，不是整个评分任务完成声明。

## 实际执行与准确身份

- 安全隔离克隆 `/private/tmp/biohub-f1-recovery-20260919`，执行分支 `codex/f1-flow-kaggle-20260918` 包含任务固定提交 `80857e0d6c35e239d7bcd32c474170f787c7682a`。
- 合同修订先保存并推送至 [4ab0ee0f371a2023d50a7bbb8ad194310f47b5df](https://github.com/SailorRen/Biohub-CELL/commit/4ab0ee0f371a2023d50a7bbb8ad194310f47b5df)，任务书及修订文件经 fixed-commit raw 字节回读一致，见 `recovery_20260919/checkpoint_readback.json`。原合同未改。
- 先核实 sailorren 身份和准确 G1 V1 全部代码单元，再查目标、完整分页自有列表及已登录页面。列表87个、无 F1 对象，目标 API403、页面不存在；403没有单独被解释为未创建。活动作业0，GPU剩余30小时，已参赛、允许提交、当日提交0/5。证据见 `preflight_api.json`、`inventory.json`、`reconciliation.json`。
- 按新增恢复许可，在互斥锁中再查完整列表及目标，保存账本后，于 **20:09:01.948294** 发送一次官方 SDK SaveKernel 请求，**20:09:07.558871** 收到 HTTP200/application-json，168字节，响应 hash `2a9e9533df59ae10fdc9f6a1d278f8e9ecbf2c62a725081ce6f73dc0f97a1d68`。平台请求ID不可得，写 UNAVAILABLE。没有自动重发。见 `F1-02_request.json`。
- 响应返回 V1/kernel134976549；已登录页面 Edit 链接 `/edit/run/351058693` 绑定准确SV，未点击编辑。GPU T4×2。诊断远端整文件 hash `e6e63a2c5f49d8372011037f8beb6812bb58cf06a293c9f3487a7cce1026ef37`，全部源码单元与冻结本地候选相同。整文件metadata差异没有冒称源码变化。
- 原 **2026-09-18** 请求及其 UNKNOWN 记录逐字段保留。不能把今天创建成功倒推成昨天明确失败，也无法彻底排除迟到重复计算；本次未见第二个实际版本。

## 未改变的科学设计与已修编排

`flow_patch.py`、诊断和生产 Notebook、两个 metadata 均保持原固定提交字节。F1仍为 k12/radius40µm/exclude1.5µm/min_global_seeds4/iterations1；8视野、G1权重、gate/cost、诊断tight55、生产原选择器及冻结门槛均不变。没有训练、参数搜索或第二算法方向。

`save_once.py` 新增 attempt_id/reason/恢复许可绑定、累计3次和共享备用独立门禁、写前持久化以及一次HTTP发送保护；记录HTTP元信息与脱敏完整异常。读取使用已安装 Kaggle2.2.3 / kagglesdk0.1.33；官方 [kernels 命令文档](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels.md)核对了 push 与 T4 标识。未升级客户端或猜测修改 metadata。

`read_run.py` 去掉固定V1假设，保存不可静默替换的实际版本绑定；分页输出、仅下载白名单小文件、大小限制和文件hash已实现。当前SDK显式 version_label 返回404，因此使用前后完全一致的已绑定 Version/源码/输入包围状态与输出读取；若当前版本变化则拒绝，不能取最新版本替代。该方法仍需保留UI SV关联。

两处读取问题已如实保存：API metadata省略输入的数字版本后缀，最初严格字符串比较触发断言；随后显式版本查询404。另一次 ListKernelSessionOutput 出现TLS EOF，保存完整脱敏traceback。它们不是Notebook运行失败，也未触发写入重试。定向人工测试覆盖预算耗尽/重复恢复拒绝、生产额度保留、模拟HTTP200非JSON元信息捕获与第二次发送拒绝；2项测试通过，语法与diff检查通过。没有本地真实推理或官方全量评分。

## 已有证据、缺口及门槛

云端日志已显示 support源码清单 hash `978b626d…`、主权重 `12f6881e…`、DeepCenter `8040999a…`、secondary `9bac2fa0…`，均与归档对应。实际GPU与容器hash已绑定。API输入名称一致，但不会把省略版本的名称当成完整版本证明；待回收 runtime_start/input_hashes，对division权重和264个运动前缓存文件作内容核验。

尚未取得8视野/2胚胎/总体 B0、B0_repeat、F1_off、F1分数、连接与分裂TP/FP/FN、最终图变化、flow覆盖/回退、实际资源峰值及耗时。因此工程等价、NO_EFFECT、全面退化、有利或混合均未判定，不能启动生产。历史日志中的旧分数/配置打印不是本轮实测结论。该8视野是重复使用且存在上游训练覆盖的受控面板，不是独立泛化验证。

没有生产运行、正式提交、Public比较或最终选择修改；G1保持。此时不提出算法优化建议。

## 累计账本与续跑

| 操作 | 全批已用 | 上限/剩余 |
|---|---:|---|
| Save & Run请求 | 2 | 上限3，剩余1仅留生产 |
| 共享恢复备用 | 1 | 已耗尽，禁止再次诊断重跑 |
| 正式submission | 0 | 最多1，须诊断和生产门禁通过 |
| 私有Notebook | 已确认诊断1个 | 最多诊断、生产2个；首请求未知风险保留 |
| 训练、Dataset写入、H1/H2、最终选择修改 | 0 | 0 |

下一会话先读取本报告、账本和 `diagnostic/version_binding.json`，仅续接准确V1/SV351058693：

```sh
/opt/anaconda3/envs/ml/bin/python3 experiments/BIOHUB_F1_FLOW_KAGGLE_20260918/read_run.py diagnostic
```

COMPLETE后回收全部小型结果，复核官方聚合、每视野改边与冻结工程门槛；完整且非NO_EFFECT/非全面退化才继续原生产和一次正式提交，无需重复索要已授权动作的确认。若该诊断报错，共享备用已耗尽，不得挪用生产额度修诊断。若仍运行则只续接。读取器当前完成诊断小型文件路径；生产专用输出回收和正式提交编排仍须在进入相应阶段时落实并核验，不能声称已通过生产/评分验收。

## 读取覆盖与交付核验

本轮完整读取清单见 `recovery_20260919/read_scope.json`：任务书、原合同/账本/编排/来源绑定/报告、F1补丁与诊断runtime、构建代码和诊断metadata；补读G1第4单元全部推断代码（包括4段长字符串）及第9单元。其他历史读取仅引用原 `source_binding.json`，未宣称本轮重读所有历史依赖。

本地核验只证明冻结科学字节、预算、准确绑定、真实缺口和原工作区保护；`recovery_20260919/verification.json` 不代表云端实验完成。GitHub固定提交文件字节回读见同目录 `github_readback.json`，最后交付提交再作一次外部回读。

原工作区仍为 `codex/sprint02-hoct-20260917` / `9d3c0f57b07444999c4326528470fe501c13c3a8`，干净。远端main `a123f0ad7f8808b44909d4c5fab48caf5147b50c`、原实验分支 `cc5f843820d8ca1e09288ca9e9561b876ec6a461` 未被本任务改动。仅向指定F1分支推送；没有上传原始数据、权重、完整图或submission.csv。

文件交付、云端实验、正式评分三个状态分别报告：交付以远端字节回执为准；云端 **DIAG_RUNNING**；评分 **NOT_RUN**。
