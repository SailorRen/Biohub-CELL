# Codex 执行任务：恢复 F1 云端实验并取得一次正式评分

任务 ID：`BIOHUB_F1_RECOVER_AND_SCORE_20260919`
仓库：`SailorRen/Biohub-CELL`
比赛：`biohub-cell-tracking-during-development`
执行分支：沿用 `codex/f1-flow-kaggle-20260918`，不新开模型实验分支。
已核验起点：`8f4334d56b37b3447d3dfdff23e98d9ccd48a744`
本任务保存到：`tasks/CODEX_20260919_BIOHUB_F1_RECOVER_AND_SCORE.md`
原实验目录：`experiments/BIOHUB_F1_FLOW_KAGGLE_20260918/`
恢复记录目录：原实验目录下 `recovery_20260919/`
结果报告：`reports/20260919_BIOHUB_F1_RECOVER_AND_SCORE_RESULTS.md`

## 1. 目标、范围与新增恢复权限

用户目标是提升正式分数。本任务应实际推进“已有 F1 诊断 → 生产运行 → 一次正式评分”，不以再次输出计划或研究报告替代执行。候选有工程错误、无有效改动或满足冻结的全面退化条件时依法停止，不为了拿一个分数提交已被门槛拒绝的版本；也不承诺 F1 必然提分。

母版仍为 G1：submission `56270217`，V1 / SV `350197436`，归档 Public `0.948`。唯一候选仍为已经冻结的 F1 邻域运动先验，不换母版，不移植整本公开 flow2，不加入 H1/H2、其他模型或参数搜索。

本任务的执行范围**新增一次受控恢复许可**：一轮完整核对后仍找不到原 F1 作业，且账户和读取通道正常时，允许保留原请求 UNKNOWN，对同一冻结诊断最多补发一次。该许可接受有限的重复计算风险，不要求先取得可能已无法补齐的原 HTTP 拒绝回执。不把第一次未知请求改写为失败、不删除记录、不反复要求用户确认本条已经覆盖的补发。

这一次补发占用原合同唯一共享工程修复备用，不增加总预算。首次请求已消费的额度、源码和错误证据均保留。除本任务明确修改的恢复与编排条款外，原科学设计、数据范围、筛查门槛和最终选择限制继续有效。

### 全 F1 批次累计预算：从 9 月 18 日首次请求起算，不因新任务清零

| 操作 | 累计上限与分配 |
|---|---|
| 保存版本 / Save & Run / 启动运行的写入请求 | 总计最多 3 次：原诊断已计 1 次；共享恢复备用最多 1 次；生产至少保留 1 次额度 |
| 共享恢复备用 | 全批最多 1 次；可用于本次未知结果恢复，或在原作业可续接时用于已定位的工程修复，不能两者都用 |
| 正式 submission 请求 | 全批最多 1 次；沿用原任务授权，失败或结果不明也计数 |
| 自有私有 Notebook 对象 | 诊断、生产共最多 2 个；未知对象也纳入潜在占用；不增加第三个恢复用 slug |
| 训练 / fit / 优化器更新；Dataset 创建或更新 | 全部 0 |
| H1/H2、F2、阈值扫描、额外 seed、新训练路线 | 全部 0 |
| 最终提交选择修改、合并 main、强推、其他项目写入 | 全部 0 |

API、CLI、浏览器中的同类写入合并计数；换工具不产生新额度。禁止以 Quick Save、额外测试 Notebook 或 SDK 隐式重发绕过预算。不使用付费算力或开启新计费服务。

## 2. 起点与最小读取范围

安全 fetch 当前执行分支，保护原工作区；不要 reset、强推、覆盖未提交改动或自动合并 main。现有 HEAD 若已推进，先核对新增账本和作业，不退回旧状态，不重复执行已完成阶段。

先读以下已存在文件，不重做整个公开区调研：

- `AGENTS.md`
- `tasks/CODEX_20260918_BIOHUB_F1_FLOW_KAGGLE.md`
- 原实验目录内 `contract.json`、`ledger.json`、`save_once.py`、`read_run.py`、`source_binding.json`
- `reports/20260918_BIOHUB_F1_FLOW_KAGGLE_RESULTS.md`
- 按实际修改需要读取 `diagnostic_runtime.py`、`flow_patch.py`、诊断和生产 Notebook、metadata；生产前补读与实际加载、运行和导出直接相关的未核实部分。

先将本任务原文和小型 `recovery_20260919/contract_amendment.json` 保存并同步本执行分支。修订文件引用原合同 hash，明确：`unknown_outcome_recovery_max=1`、`counts_as_shared_reserve=true`、`save_and_run_total_max=3`、`formal_submission_total_max=1`、`algorithm_change_allowed=false`。原合同不覆盖改写。记录固定 checkpoint commit 后再发送新的 Kaggle 写入。

只记录实际读过的范围，不宣称重新完整审查了全部历史 Notebook 或依赖；也不把与本次加载、改动和评分无关的历史材料补读设为无限扩展的前置任务。

冻结科学身份（来自原 contract.json）：

| 对象 | SHA-256 |
|---|---|
| `flow_patch.py` | `d2511cb21d536d230a6607d3119bccb1d931e21f4ec49237790d6dc335266896` |
| `diagnostic/candidate.ipynb` | `5a94bc79a1ffe55c71d1b456b579792048c7c3adb2eac3ecb96b801acf382bab` |
| `production/candidate.ipynb` | `d82f8ba98aa9d4ac51b62105155b1aadbbbf9f202ddd700a9b6281162e2d9c31` |

F1 参数保持：`k=12`、`radius_um=40`、`exclude_um=1.5`、`min_global_seeds=4`、`iterations=1`。诊断样本、原 G1 gate/cost、权重和生产自动选择器不变。修复上传或读取脚本不应改变这些 Notebook 字节；确有已定位的路径、依赖或运行包装错误时，保存旧版、最小 diff 和新 hash，在再次运行前冻结，并证明没有改变算法、样本、权重与评分口径。无法保持科学设计时停止，不伪装为工程修复。

## 3. 只做一轮原请求核对，随后按状态行动

原目标：`sailorren/biohub-f1-flow-diag-20260918`。
原请求时间：`2026-09-18T09:34:57.809820+00:00`。
原响应状态：JSONDecodeError，服务端写入结果 UNKNOWN。

核对顺序：先用已知存在的 G1 确认账户 `sailorren` 与读取权限正常；再查原 F1 目标、完整分页自有 Notebook 列表和可用的版本/运行记录。已有授权浏览器可用时读取已登录目标页；不用公共搜索结果证明私有对象不存在。列表记录分页是否完整，不将 403 或鉴权失败解释为“未创建”。

一轮核对同时刷新参赛/提交权限、GPU 可用额度、可用兼容加速器、日提交余量与当前运行限制。不沿用 9 月 18 日的额度快照，不接受规则、不报名、不擅自取消其他作业。没有明确可用资源时记录实际阻断，不用猜测填补。

按下列规则行动：

| 状态 | 动作 |
|---|---|
| 同源码、同输入的原运行已完成 | 绑定准确版本和输出，直接回收结果，不重新运行 |
| 原运行排队或运行中 | 续接该运行，做有界读取；不得同时启动恢复副本 |
| 原运行已报错 | 回收原错误，定位可保持科学设计的工程修复；仅在共享备用未使用时修复运行一次 |
| 找到同源对象，但明确只有未执行的草稿/版本、无可续接运行 | 核实其身份后，以一次恢复额度保存并运行同一冻结诊断；不得误称旧版已经运行 |
| 账户/读取通道正常，完整核对仍无对象 | 本任务允许一次受控补发，无须证明第一次明确失败；保留原 UNKNOWN |
| 账户、权限、列表完整性或候选身份仍不可信 | 停止写入并给出具体缺口；不得靠盲目新建对象试探权限 |

一轮核对不是每次换工具重复一整轮。满足受控恢复条件就继续实施，不再返回同一份“建议核对”报告。准备实际写入时在锁内作最后一次去重读取；若原运行此时出现则续接。

恢复使用原诊断 slug，不覆盖无关对象，不添加 r2/r3 后缀创建多个候选。同一 slug 的 push 可能新增版本，不视为具有幂等性，不保证不会重复计算。

写入后立刻回读，记录对象、版本、ScriptVersionId、worker 状态和源码/输入绑定。若原请求与恢复请求后来都出现，记录两个实际版本及成本风险，不再加写入。读取指标前固定使用最早的身份核验通过、可完整取得结果的成功运行；已经绑定了正在运行的版本则继续用它。其余结果不用于挑高分，不产生第二个正式候选。

## 4. 只修阻塞执行的编排代码

已读源码存在下列具体限制，需按修订合同修正，而不是简单删除保护：

1. `save_once.py` 的“同 phase 只能一次”、`len(requests)<2` 与本次受控恢复/累计3次上限不一致。改为带 `attempt_id`、`phase`、`reason` 和一次性恢复凭据的账本控制；共享备用与总数分别扣减，发送前持久化，保留互斥锁。禁止清空 requests 或隐藏前一次记录。
2. `read_run.py` 写死 `version==1`，且主要查询当前版本。改为绑定实际返回的准确 Version、SV、源码和输入；之后所有日志、输出与提交都必须来自该版本。不得把最新版本当作已绑定版本；无法准确关联时只补查关联，不重跑。
3. `read_run.py` 当前仅记录第一页输出清单和日志，不能把这些当已下载结果。补齐分页和必要小型文件回收，真实读取 `f1_small/results.json`、`per_view.csv`、`edge_changes.csv`、`flow_usage.csv`、`stages.json`、运行和输入回执；验证文件确属同一版本及 hash 后才生成诊断完成回执。
4. 保留完整脱敏 traceback，区分发送前异常、发送后异常、HTTP 异常和解析异常。能获取时记录 HTTP 状态、Content-Type、响应长度、body hash 和平台请求标识；不可获取的项明确写 UNAVAILABLE，不虚构。不要为重建第一次已丢失的响应无限阻塞本次执行。
5. 核实本地实际 Kaggle 客户端版本和已有成功调用方式。优先使用已确认可用的官方 CLI/SDK；已授权浏览器可作为替代路径。写入前选定路径；API 结果不明后改用浏览器也算一次新的写入，不能两边连续点。禁止业务写入自动重试；每个实际发送的保存/启动请求计数。

本地只做静态检查、小型人工样例、账本和模拟网络响应测试，不加载模型或运行真实视频。受控补发默认保持诊断源码和输入不变；当前异常原因未定位到具体字段时不要猜测修改 metadata。

仅将脱敏证据提交 GitHub。Token、Cookie、Authorization、签名下载链接、完整环境变量和带凭据响应不得进入报告或仓库。原始敏感日志如需保留仅放 ignored 路径。

## 5. 完成一次云端配对诊断，不重复重计算

本批真实数据诊断、模型计算、官方评分和生产推理仍放 Kaggle；不因上传阻断临时迁回本地重算，不新训练、不新增 Dataset。

优先复用准确挂载的运动重连前缓存；不得拿最终 G1 图、safe-div 后图或 HOCT 图代替。旧合同允许缓存真正缺失时在本次云端诊断内补算固定8视野所需上游一次。原始数据、完整图和权重留云端，按视野处理，缓存共享但可变图必须独立深拷贝。

沿用原 contract.json 中的8个视野、配置与官方评分聚合，执行 B0、B0_repeat、F1_off、F1。重复只重复必要后处理，不重复整套上游推断。B0_repeat 和 F1_off 图必须与 B0 相同，评分浮点容差继续 `epsilon=1e-10`，不能按 F1 结果放宽。

必须实际取得：每视野/每胚胎/整体 B0与F1分数和差值、连接与分裂 TP/FP/FN、运动阶段和最终输出改边、flow覆盖/回退、异常和必要运行耗时。UNKNOWN边不当负例；不能测得的资源值如实写 UNKNOWN。当前8视野有反复使用与已知上游训练覆盖，仍称受控诊断，不称独立泛化证明。

已有可靠小型测试不用全部重做一轮大型验收；只对编排改动做定向测试。也不要等公开区增量调研完成才运行本诊断。

## 6. 用原冻结门槛决定是否正式评分

工程身份正确、真实计算完整、无 GT 流入新推理模块、图合法、关闭等价、无第二方向修改、无未解释异常或静默全回退，是必要条件。8个视野最终图全部不变时记 `NO_EFFECT`，本批不正式提交。

保持原“全面退化”停止条件：

```text
overall_delta < -epsilon
AND 两个 embryo_delta 都 < -epsilon
AND adjusted_edge_delta <= epsilon
AND division_delta <= epsilon
```

满足时标 `DIAGNOSTIC_DOMINATED`，结束 F1，不扫描参数挽救。其余工程正常且有实际最终改动的结果：有利为 `DIAGNOSTIC_FAVORABLE`，有取舍或持平为 `DIAGNOSTIC_MIXED_EXPLORATORY`，均允许进入生产和一次探索性正式评分。公开列出退化视野、TP损失和分裂变化，不增加“每个胚胎必须提升”或“任何TP不能损失”的新门槛。

达到这些既定条件后，生产与一次正式提交已包含在本任务范围中，直接继续，不再向用户重复请求确认。不会因为希望拿分而绕过硬错误或全面退化停止条件。

## 7. 生产、正式提交与真实成绩

生产目标沿用 `sailorren/biohub-f1-flow-prod-20260918`，先查是否已有本批准确运行，存在则续接。只用冻结 F1 和准确 G1 正式权重、原自动选择器；生产不能锁死为诊断 tight55，不能追加 F1 专属 sweep。必要读取完成后立即执行，不开新的研究阶段。

生产以平台 COMPLETE、准确源码/输入绑定、输出文件存在且结构与覆盖合法为准；记录 F1 启用/调用、回退、原选择器选项和输出 hash。普通可见测试没有改边不自动否定已有8视野改动证据，但必须证明 F1 未被全局禁用。无需为了对照再运行一遍完整 G1 生产。

正式提交前：刷新实时提交权限与配额；锁内检查全批 ledger 和已有 submission；固定已完成生产 Version/SV 与 `submission.csv` 对应关系，预记 attempt。按当前官方代码竞赛提交流程提交准确生产版本，而不是上传本地缓存 CSV 或提交诊断 Notebook。实际命令以执行环境的官方文档/`--help` 为准，不盲套旧 SDK 参数。

正式请求全批最多一次。请求结果不明或隐藏重跑失败时只回读和回收错误，不第二次 submit，不换标题再提交。

结果回执至少包含：比赛、账户、Notebook、Version、SV、submission ID、请求/观测时间、状态、真实 Public、可用错误、源码绑定。只有平台实际返回的数字才填 Public；pending/error 不填0，不用诊断分替代。

终态时同步读取 G1 submission `56270217` 的同口径分数。只能按真实返回精度比较；无同步读取则明确相对归档 0.948。高于为 `PUBLIC_IMPROVEMENT_OBSERVED`、持平为 `PUBLIC_TIE`、下降为 `PUBLIC_REGRESSION`；Public改善不等于Private提升。最终选择仍不修改，G1保留。

## 8. 收口与续跑：交付数据，不以文档数替代实验

每个已启动阶段当前会话最多做6次有界只读状态检查，不高频刷新、不建立自动监控、不承诺会话外继续工作。存在尚未完成的真实作业时保存准确状态 `DIAG_RUNNING` / `PRODUCTION_RUNNING` / `SCORE_PENDING` 及绑定版本、预算和下一命令；后续会话先续接原作业，不因换会话重新启动。已达终态则本会话内继续到下一合法阶段。

共享备用已消费后生产再失败，或受控恢复再次结果不明，停止新增写入；前者保存实际错误，后者保留两个 UNKNOWN 并回读已可能存在的作业。不能凭预算紧张伪造完成，也不能仅为了“继续推进”借用正式提交额度创建诊断版本。

最小交付：本任务、一个合同修订文件、原 ledger 的可追溯追加、每次请求/回读/结果的必要小型证据、一个结果报告。优先复用现有代码和验证脚本，不再搭建新的通用管理框架。

报告开头直接给出 B0、F1 诊断分与差值，F1 submission/准确版本/Public、G1正式基准、预算及结论。没有获得的值写 null 或 NOT_RUN，并说明所在阶段。F1提交前被门槛拒绝时给出真实拒绝数据，不能宣称已取得正式分。

结果出来后只提出至多一个与实测问题对应的下一改动建议；不自动执行下一候选。持平不称成功；下降不替换G1；工程失败不冒充算法失败。

将任务、最小代码diff、脱敏日志、小型结果和报告同步 `codex/f1-flow-kaggle-20260918`。GitHub不保存原始比赛数据、模型权重、完整预测图或submission.csv。保存固定commit及远端回读hash；检查main和原工作区未被本任务修改，区分“文件交付通过”“云端实验完成”“正式评分完成”三种状态。

## 证据入口（按已读取材料记录，不代表重新查询 Kaggle）

截至本任务撰写时，GitHub执行分支回读HEAD仍为 `8f4334d56b37b3447d3dfdff23e98d9ccd48a744`，账本仍只有一次结果未知的诊断请求。

- 固定报告：<https://github.com/SailorRen/Biohub-CELL/blob/8f4334d56b37b3447d3dfdff23e98d9ccd48a744/reports/20260918_BIOHUB_F1_FLOW_KAGGLE_RESULTS.md>
- 固定合同：<https://github.com/SailorRen/Biohub-CELL/blob/8f4334d56b37b3447d3dfdff23e98d9ccd48a744/experiments/BIOHUB_F1_FLOW_KAGGLE_20260918/contract.json>
- 固定账本：<https://github.com/SailorRen/Biohub-CELL/blob/8f4334d56b37b3447d3dfdff23e98d9ccd48a744/experiments/BIOHUB_F1_FLOW_KAGGLE_20260918/ledger.json>
- 已读取上传脚本：<https://github.com/SailorRen/Biohub-CELL/blob/8f4334d56b37b3447d3dfdff23e98d9ccd48a744/experiments/BIOHUB_F1_FLOW_KAGGLE_20260918/save_once.py>
- 已读取回读脚本：<https://github.com/SailorRen/Biohub-CELL/blob/8f4334d56b37b3447d3dfdff23e98d9ccd48a744/experiments/BIOHUB_F1_FLOW_KAGGLE_20260918/read_run.py>
- Kaggle官方运行命令文档（执行时核对当前版本）：<https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels.md>
- Kaggle官方提交命令文档（执行时核对当前版本）：<https://github.com/Kaggle/kaggle-cli/blob/main/docs/competitions.md>
