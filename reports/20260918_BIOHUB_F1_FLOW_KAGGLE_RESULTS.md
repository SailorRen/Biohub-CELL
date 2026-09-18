# F1 Kaggle 云端实验：写入结果不明，未取得实测结果

任务 `BIOHUB_F1_FLOW_KAGGLE_20260918`，分支 `codex/f1-flow-kaggle-20260918`。依据固定任务提交 `a88938c587a2444831a9b60bda292f1621ce6e7b`；冻结代码提交 [2590c8516c4a0fc729aa39940f8a2dba34c2e93a](https://github.com/SailorRen/Biohub-CELL/commit/2590c8516c4a0fc729aa39940f8a2dba34c2e93a)。时间均注明上海时区或 UTC。

## 结论与状态

实验状态 **BLOCKED_WRITE_OUTCOME_UNKNOWN**；正式评分 **NOT_RUN**。本轮已实际调用一次诊断 Save & Run，但不能证明 Kaggle 创建了版本或启动了计算。没有 8 视野结果，没有 F1 Public，不判定有利、混合、退化或 NO_EFFECT。GitHub 交付状态以独立 `github_readback.json` 为准，不能代替实验成功。

2026-09-18 **17:34:57.809820 至 17:35:09.683118**，调用 `api.kernels_push`，返回解析失败 `JSONDecodeError: Expecting value: line 1 column 1 (char 0)`。调用前已持久化账本并消费诊断请求额度。没有保存原始 HTTP 响应体及状态，因此无法定位为确定性接口/镜像/挂载错误，也不能声称请求明确失败。

之后只读对账：

| 证据 | 观测 | 意义 |
|---|---|---|
| API 17:37:19 | 目标 `GetKernel` 返回 403 | 未读到对象；不是创建失败的明确回执 |
| 已登录浏览器约 17:38 | 目标页显示 `We can't find that page.` | 该页面当时不可见 |
| 完整账户列表 17:38:32 | 85 个 Notebook，无 F1 名称/slug | 未发现同批对象或改名对象 |

上述证据保留在 `diagnostic/platform_20260918T093719Z.json`、`diagnostic/ui_readback.json`、`post_request_inventory.json`。没有 Version、ScriptVersionId、kernel ID 或正式 submission ID 可供绑定，均为 null。遵守任务第7、8节，不盲目重发，不把备用额度当成未知请求的自动重试权。

## 已验证起点与平台条件

`SOURCE_CODE_VERIFIED`：远端 G1 `sailorren/biohub-sprint01-g1-frozen-inference-20260916` V1／SV350197436，与归档母版全部代码单元相同。本地文件 SHA256 `de010e6ba142be0e01000093e061ef7d3388ddaa411185b40d26c63a3febe731`；本次远端整文件 SHA256 `2455dcd654dba55017e27547558b3e51cd95017d3519dafc2205b239709d5094`，两者分开记录，未把元数据差异冒称代码变更。

`OFFICIAL_FACT`：本次 API 及展开的 submission 页面核对 G1 submission **56270217** 为 COMPLETE，Public **0.948**；仅使用平台返回的三位精度。17:10:32 API 核实账户 sailorren，已参赛，允许提交，代码竞赛，每日最多5次、当日未见提交；GPU 剩余约13.409565小时。浏览器规则页显示已接受规则；未进行接受规则或报名操作。截止为上海时间2026-09-30 07:59。磁盘实际余量和实际 GPU 型号没有云端回执，仍为 UNKNOWN。

`SOURCE_CODE_VERIFIED`：官方评分仓库 main 只读核对仍为 `075fc5f5a52d11077f9dc2b074644618f26939e2`，冻结评分器未变。诊断沿用 `evaluate → per_sample_metrics → summarise`，原有 proxy 仅为历史诊断字段，不用其替代官方分。

## F1 改动及冻结设计

仅修改 G1 `motion_relink_edges` 的预测位置：先以独立、未修改的 G1 运动连接得到各帧对 tight 种子，再按物理距离和稳定节点 ID 排序，最多12邻居、半径40µm，排除自身及距离≤1.5µm的种子。全局种子少于4则退回原先验；局部无邻居亦回退。位移逐坐标中位数，只做一轮；非有限值报错。

原 G1 gate、`motion + 0.05*raw - learned_bonus*prob` 代价、学习概率、匹配顺序、个体速度系数、分裂规则、后续 gap/safe-div/过滤保持。种子来自 B0 原始 predecessor 链，不从 F1 已改变的图反推。此实现多执行一次原运动匹配用于取种子，真实开销尚未测得。

来源为公开 flow2 V1／SV350702651 的邻域位移机制；不是整本复现。没有移入 det=.96、flow tight=7、raw-admit、raw-cost=0、HOCT/H2 或标注名单。诊断受控 tight55 与生产原自动选择器明确分开；生产 Notebook 原有第0–4、6–12单元原样保留，仅第5单元安装 F1，并增加回执单元。

冻结 hash：

| 文件 | SHA256 |
|---|---|
| flow_patch.py | `d2511cb21d536d230a6607d3119bccb1d931e21f4ec49237790d6dc335266896` |
| diagnostic/candidate.ipynb | `5a94bc79a1ffe55c71d1b456b579792048c7c3adb2eac3ecb96b801acf382bab` |
| production/candidate.ipynb | `d82f8ba98aa9d4ac51b62105155b1aadbbbf9f202ddd700a9b6281162e2d9c31` |

本地9类小型人工样例通过：空输入、关闭等价、物理单位、整体平移、自身排除、全局种子不足、无局部邻居、端点/时间/运动阶段度约束、非有限值拒绝。未在本地加载模型、运行真实图重放或官方全量评分。这些测试不是比赛性能证据。

## 云端设计与实际缺口

诊断代码固定8视野（44b6_12dfb391、44b6_267148e4、44b6_2a2eff9f、44b6_341df25f、6bba_062c8d37、6bba_07e24132、6bba_085bf656、6bba_09961292），挂载已归档 division V1 的原始 GEFF，逐文件验证264个哈希，再验证各视野运动前图哈希。没有使用 H1/HOCT 图、最终 G1 图或 safe-div 后图冒充输入。父 Notebook 在写前已通过准确 ID、V1、归档代码单元一致检查。

代码独立深拷贝给 B0、B0_repeat、F1_off、F1，共享只读 DeepCenter 热图磁盘缓存及 refinement 缓存。诊断 G1 分类器使用真实胚胎 held_out 权重；原权重固定，训练为0。计划导出官方每视野/胚胎/总体分、图哈希、运动/最终改边、官方匹配支持下TP/FP/UNKNOWN及邻域覆盖统计。

**实际均未取得**：8视野/2胚胎分数、TP/FP/FN变化、flow覆盖/回退、耗时/内存、最终图变化、生产选择器交互。未制造 `results.json`、`per_view.csv`、`edge_changes.csv`、`flow_usage.csv` 实测文件。

这8视野属于重复使用的受控面板。归档 secondary manifest 的 train 列表包含全部8视野；primary、DeepCenter完整训练谱系UNKNOWN。分类器留组证明与全流程独立验证是不同事项。既有样本泄漏情况不能被本轮局部对照掩盖。

读取清单与未读范围见 `source_binding.json`。运行前读完修改函数与直接依赖、母版后处理调用链及准确身份回执；生产尚未启动，G1第4单元的大段内嵌推断字符串与第9单元仍需在生产前补全读取，不能宣称已全读生产源码。云端实际模块版本/哈希、schema、输入挂载、磁盘与真实运行状态也未得到回执。

## 预算与续跑

| 操作 | 已消费或确认 | 上限 |
|---|---:|---:|
| Save & Run 请求 | 1（结果不明） | 3 |
| 诊断首请求 | 1 | 1 |
| 工程修复备用 | 0 | 1 |
| 生产请求 | 0 | 1 |
| 新私有 Notebook | 确认0；原请求是否创建UNKNOWN | 2 |
| 正式 submission | 0 | 1 |
| 训练、Dataset写入、H1/H2、最终选择修改 | 0 | 0 |

前两次启动编排只在只读前置阶段中断，未到写入：显式 `version_label=1` 查询404，以及 OAuth 连接 EOF。单独存 `prewrite_interruption.json`，未冒称已消费两次 Save & Run。

续跑首先读取 ledger，然后只读运行 `read_run.py diagnostic` 并核对账户列表、目标页。若原对象出现，绑定准确源码、Version、SV并回收原作业，不重新运行。若仍缺对象，必须先拿到明确失败结论并定位符合第8节的确定性工程问题，或取得新的重试授权；不能直接再次执行 `save_once.py`，该脚本会拒绝重复请求。没有定时监控或会话外自动动作。

因没有真实实验结果，本轮没有基于效果的调参建议；仅建议先解决写入回执与对象身份对账。

## 工作区与交付验证

使用隔离 worktree `/private/tmp/biohub-f1-flow-20260918`。原工作区仍在 `codex/sprint02-hoct-20260917`、HEAD `9d3c0f57b07444999c4326528470fe501c13c3a8` 且干净；未切换、重置或清理。远端原实验分支为 `cc5f843820d8ca1e09288ca9e9561b876ec6a461`，main 为 `a123f0ad7f8808b44909d4c5fab48caf5147b50c`；本轮未推送它们、未合并main。

本地 `verification.json` 只验证冻结字节、预算、源码范围和没有虚构测量。GitHub 回读按固定提交下载归档，逐文件比较 SHA256；验证回执不自引自身哈希。交付完成不等于实验完成。
