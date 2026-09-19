# Codex执行任务：从F1最终图恢复官方评分，通过门槛后生产并正式提交

任务ID：`BIOHUB_F1_CACHE_RESCORE_AND_SUBMIT_20260919`
仓库：`SailorRen/Biohub-CELL`
比赛：`biohub-cell-tracking-during-development`
执行分支：沿用 `codex/f1-flow-kaggle-20260918`
证据起点：`523462f2e667cacda23ea7b8063bc9173d619662`
任务路径：`tasks/CODEX_20260919_BIOHUB_F1_CACHE_RESCORE_AND_SUBMIT.md`
原实验目录（下称E）：`experiments/BIOHUB_F1_FLOW_KAGGLE_20260918/`
本次恢复目录（下称R）：`E/score_recovery_20260919/`（E展开为上一行的实际目录）
报告路径：`reports/20260919_BIOHUB_F1_CACHE_RESCORE_AND_SUBMIT_RESULTS.md`

## 1. 执行目标与本次授权

用户目标是提高正式分数。本任务实际推进：读取已存在的诊断最终图 → 有限的本地CPU重新评分 → 按原冻结条件判断 → 通过后运行原F1生产Notebook并正式提交一次。不得只交计划，也不得保证F1一定提分。

本次新增授权仅为：（1）有界下载现有最终图、对应标注图和必要评分元数据，在本地CPU恢复评分；（2）修复独立评分恢复脚本的字段汇总与检查点；（3）允许经过核验的缓存恢复回执，代替旧启动器要求的“诊断Notebook必须COMPLETE”的工程证据入口。后两项不得改变F1、官方公式、样本、科学筛查门槛或生产配置。

这不是重做诊断的授权。不重新运行F1运动重连、上游检测、DeepCenter、gap、safe-div或任何模型来重建预测；不下载原始视频、权重和热图。最终图已经包含这些处理的结果，本次仅重做官方图匹配、评分和结果分析。

| 操作 | 本次与累计边界 |
|---|---|
| 本地计算 | 仅人工接口测试、最终图合法性/等价检查、CPU评分和小型结果分析；禁止模型推断、训练和完整后处理重放 |
| 新诊断/修复Save & Run | 0；不得新增诊断版本或云端“只评分”运行来绕过预算 |
| 生产Save & Run | 本批尚未执行时最多1次；全F1批次累计仍最多3次，已有2次计入 |
| 正式submission | 全F1批次累计最多1次，现有记录为0；失败或结果未知也计数 |
| 共享工程备用 | 已用1/1，不恢复、不清零，不挪用生产额度 |
| Dataset写入、训练、额外候选/阈值扫描 | 全部0 |
| GitHub写入 | 本执行分支上的本任务、恢复脚本、小型证据、账本和报告；不合并main，不强推，不写其他项目 |
| 最终提交选择 | 0；原G1保留，不自动修改最终选择 |

安全同步后先检查分支的新进度和账本。上述数字是固定证据起点，不是允许覆盖更新状态的指令。已经恢复、已启动生产或已提交时，直接续接准确原对象，不重复计算或写入。保留第一次请求UNKNOWN、第二次请求及V1报错的历史事实。

## 2. 起点身份与只需读取的材料

恢复对象：`sailorren/biohub-f1-flow-diag-20260918`，kernel `134976549`，V1，ScriptVersionId `351058693`。归档worker状态ERROR，错误为末尾汇总读取不存在的 `edge_tp`；8个视野四个实验臂均已执行，32份最终图在输出清单中，但字节完整性和可下载性需要本任务核验。

母版G1：submission `56270217`，V1 / SV `350197436`，归档Public `0.948`。不得以诊断逐视野分或标题替代正式分。

先读AGENTS.md、原两份任务书、E/contract.json、E/ledger.json及E/recovery_20260919/contract_amendment.json，再定向读取：
- `reports/20260919_BIOHUB_F1_RECOVER_AND_SCORE_RESULTS.md` 的终态补充；
- E/recovery_20260919/failure_analysis.json；E/diagnostic/platform_20260919T130712Z.json；E/diagnostic/runtime_start.json；
- E/diagnostic_runtime.py、E/build.py中缓存序列化与评分适配部分，以及实际诊断Notebook内的评分包装函数；
- `experiments/TARGET950_20260914/vendor/official_075fc5/metrics.py`、division_metrics.py及直接评分依赖；
- E/save_once.py、E/read_run.py和E/recovery_20260919/budget.py中与生产入口有关的部分。

不重新遍历全部公开区、历史Notebook或上游训练谱系。本次问题是已有预测的评分恢复。

先将本任务原文及R/contract_amendment.json保存并同步执行分支。修订明确本地资源边界、可恢复证据入口、缺失统计处理和累计预算；原科学合同不覆盖。实现后、真实恢复开始前固定恢复脚本hash。保护原工作区，使用已有隔离工作区或安全worktree，不重置有新进度的分支。

## 3. 只取必要数据，保留原错误版本

固定8个视野，顺序不变：
```
44b6_12dfb391
44b6_267148e4
44b6_2a2eff9f
44b6_341df25f
6bba_062c8d37
6bba_07e24132
6bba_085bf656
6bba_09961292
```

只读列出并精确取得上述版本的 `f1_cache/{stem}_{arm}_graph.json`，arm为B0、B0_repeat、F1_off、F1，共32份；再取得对应8个视野的GT标注GEFF及评分需要的estimated true node count等元数据。优先复用本地已有且来源/hash一致的GT。GEFF可能为目录，只获取评分需要的节点/边数组和元数据，不凭扩展名假定其体积小。

输出列表归档为5页498项；这不代表允许整包下载498项。现有小文件白名单读取器可新增一个“32份指定最终图”的独立下载入口，不可直接移除其所有大小/类型保护。不得下载 `*_deepcenter.npy`、原始图像Zarr、模型权重或无关目录。

使用当前实际支持的只读API/界面获取已有文件，不猜测未支持的版本接口。若接口只能读当前版本，下载前后均确认当前仍为V1、SV关联和源码一致，期间不保存任何新诊断版本；无法锁定准确输出就停止，不取“同名最新版本”。保留来源、精确文件名、长度、下载时间和SHA256。平台无原始hash时明确记录“下载字节hash”，不冒称它是崩溃前已保存的hash。临时签名URL、Cookie、Token与认证响应不得同步GitHub。

### 本地资源上限（任务设置，不是已有性能测量）

使用隔离评分环境、单进程、CPU最多2线程、按视野流式；新增预测/标注缓存总量最多2GiB，评分进程峰值内存最多4GiB，且启动预算不得占用当时可用内存的一半以上。先检查空间和文件体积，再下载；未知大小采用有上限的流式接收。只安装必要CPU评分依赖，不安装CUDA镜像或重新配置全局环境。

先完成固定清单第一个视野B0/F1的评分作为资源与等价试运行。它计入最终结果，不重复跑。若资源不可接受、需要大量原始图像、必须运行模型、依赖无法适配或准确缓存无法取得，保存已有检查点及具体阻断；不悄悄扩容，不新增云端动作。本任务没有“本地失败自动多开一个云端任务”的授权。

## 4. 独立评分恢复：不执行原Notebook主流程

编写R/restore_scores.py，只复用原诊断的纯数据图构造、GT读取及官方评分包装。禁止通过执行整个Notebook/diagnostic_runtime.py来调用评分，也不通过删除CLOUD_ONLY或GPU_REQUIRED断言来运行原主流程。

官方评分源码固定 `075fc5f5a52d11077f9dc2b074644618f26939e2`，用runtime_start.json记录核验：
- metrics.py SHA256：`cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444`
- division_metrics.py SHA256：`0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9`

核对评分直接依赖，尤其tracksdata `0.1.0rc6.dev3+g980c2d30a`及节点/边schema；记录CPU环境与云端版本差异。不要为了图评分安装云端CUDA版Torch或照搬全部GPU环境。关键匹配实现和源码不得换成近似版本；非评分依赖不作为阻断条件。

缓存结构为 `nodes=list(n.items())` 与 `edges=e`。恢复整型节点ID、坐标精度、时间、原节点/边顺序和构造规则；不得先排序、去重、四舍五入或重编号来“规范化”输入。匹配器可受顺序和边ID影响，必须沿用原评分包装的图构造和ID映射。坐标单位、scale、7微米匹配半径、GT元数据、节点惩罚均以原代码为准，不自行再次缩放坐标。

逐视野完成：
1. 核验4份图完整、有限坐标、端点/时间/重复边/度约束，并保存原始字节hash及与旧gh定义一致的有序图hash。
2. 验证B0、B0_repeat、F1_off的有序图完全相同。相同则仅对B0评分一次，其余两臂引用同一结果，明确标为“图等价后复用”，不能声称重新执行了三次评分。若不等价则停止，不根据最终分数挑一份作为B0。
3. B0与F1分别通过原 `evaluate → per_sample_metrics → summarise` 调用链评分。匹配会修改图属性，因此使用独立新构造/副本，不共享可变匹配状态。F1最终图等同B0时可以复用已核验的评分，记录复用关系。
4. 与failure_analysis.json的16个完整精度B0/F1日志值核对，`abs(delta) <= 1e-10, rtol=0`。不得用报告九位小数表代替原日志值。差异超过容差时先查图顺序、单位、GT和匹配实现，不放宽容差或改分数。
5. 在评分产生官方匹配结果时保存最终加边/删边和可确定的TP/FP/UNKNOWN归属；沿用原ID映射并验证双射。UNKNOWN不当负例；官方FP不直接称为生物学错误。原边列表副本在评分前保存，以免匹配器的内部处理污染最终图差异。

### 修复汇总schema，不改官方分数

官方 `summarise(rows)` 的返回值不包含edge_tp/edge_fp/edge_fn。整体和胚胎官方分继续原样调用该函数；另从同一有效逐视野行显式求和补齐edge计数，用独立counts字段或经过测试的适配器输出。禁止 `.get(key, 0)` 掩盖缺字段，禁止修改vendor评分器来迎合错误调用。

每个实验臂分别使用自己的逐视野计数和权重。不得用B0权重替F1加权，不平均8个总分，不用evaluate_datasets的未调整分替代原summarise。保留原NaN/无分裂项处理；不得把未恢复字段填0，不裁剪大于1的合法分数。

要求总体8个有效视野、每胚胎4个；检查summarise的n/n_adj和每行必要指标，不允许静默跳过缺失行后声称完整。恢复计数标记为“从最终图重新评分取得”，不是已找回原进程内存中的计数。

### 检查点与最小测试

每个独立评分臂一完成，先原子保存R/checkpoints/{stem}_{arm}.json，再继续；包含输入/GT/scorer/适配器hash、完整逐视野指标、日志对照、等价引用和必要事件统计。后续汇总随时能由检查点重建，不依赖内存；重启只复用hash和完整性验证通过的检查点。

真实评分前做小型人工测试：缺edge摘要字段能正确适配且不改变官方score；缺必需逐视野字段会明确拒绝；不同权重和无分裂情况遵从原函数；中断后能从检查点恢复。复用现有测试体系，不新增大框架。

## 5. 最小可恢复证据与生产门槛

必须恢复：8视野B0/F1完整官方指标、两个胚胎及总体官方分、连接/分裂计数、权重、最终图变化和合法性、B0重复/F1关闭等价、全部日志分的容差一致性。

不强行恢复：旧运行的flow邻居分布/覆盖率、运动阶段中间图、各臂原始GPU耗时。它们不能从最终图完整反推，标记NOT_RECOVERABLE_FROM_FINAL_GRAPHS；本次CPU评分耗时不得冒充原运行耗时。不要只为补齐这些字段而重跑模型或整个后处理。

本次允许以下替代工程证据入口：固定源码、输入/配置回执、8/8完成日志、B0_repeat/F1_off等价、F1最终图实际变化，且定向核对没有超时降级/随机性/异常等其他解释时，记录 `flow_effect_evidence=FROZEN_SOURCE_PLUS_FINAL_GRAPH_CHANGE`。它仅说明F1产生了输出影响，不证明具体flow覆盖率或每帧均运行。不能因为丢失覆盖计数就直接伪造旧SILENT_ALL_FALLBACK断言已执行；替代证据不充分时保留阻断。

恢复证据充分时写R/receipt.json：
- `status=CACHE_RESCORE_VERIFIED`；准确ref/kernel/Version/SV和原源码绑定；
- `source_worker_status=ERROR`、`recovery_execution=LOCAL_CPU_SCORING_ONLY`；
- 本次下载manifest、评分脚本/评分器和结果hash，16个日志对照结果与复用说明；
- 已恢复项目、未恢复项目、等价性/图变化及替代证据；
- `cloud_diagnostic_reruns=0, model_inference_calls=0, training_calls=0`。

同时用原contract.json规则判定R/results.json。只做工程证据入口修订，不改epsilon或科学门槛：
- 硬错误、评分不完整、标签进入新推理、图非法、关闭不等价、第二算法改动或未解释异常：停止。
- 8视野最终图全部不变：NO_EFFECT，停止。
- 总体差值<-epsilon，两个胚胎差值均<-epsilon，整体adjusted edge差值<=epsilon且division差值<=epsilon：DIAGNOSTIC_DOMINATED，停止。
- 总体提升且两个胚胎均不下降：DIAGNOSTIC_FAVORABLE；其余满足工程条件且不被上述规则拒绝：DIAGNOSTIC_MIXED_EXPLORATORY。

后两种状态允许生产和一次探索性正式评分，不要求每个视野都提升，不因3升3降就直接通过。恢复样本仍是反复使用且存在上游训练覆盖的8视野，不能称独立泛化验证。

## 6. 修复生产入口，保留唯一生产额度

允许修改启动器/预算读取器，让它读取新恢复结果及 `CACHE_RESCORE_VERIFIED` 回执，并校验来源、hash、通过状态和实际剩余额度。不得造一个假的 `diagnostic/receipt.json: COMPLETE_SOURCE_VERIFIED`，不得把V1平台状态或历史报告改成COMPLETE。

现有save_once.py将旧诊断reconciliation与preflight条件用于整个main：生产时应使用新的生产账户/参赛/额度/准确父输入核对，以及本次评分恢复证据；不继续要求“诊断对象不存在”或沿用已过期的controlled_recovery_eligible。这只是阶段编排修复，写前锁、账本、单次发送、结果不明不重发、禁止付费计算等保护保留。用人工回执测试新入口接受有效恢复证据、拒绝错误hash/未完成复算/预算耗尽，不能全局删除检查。

生产候选和F1补丁保持冻结：
- E/flow_patch.py SHA256 `d2511cb21d536d230a6607d3119bccb1d931e21f4ec49237790d6dc335266896`
- E/production/candidate.ipynb SHA256 `d82f8ba98aa9d4ac51b62105155b1aadbbbf9f202ddd700a9b6281162e2d9c31`

不要运行build.py覆盖上述文件，不把修复评分的本地脚本注入生产；无需再保存一个修复版诊断Notebook。原生产权重、输入、自动选择器及其配置集均保持，不改成诊断tight55，不把恢复GT或诊断输出作为生产输入。

生产前保存必要修订/恢复证据到GitHub并回读，完成此前未读的直接生产执行路径检查；不重新做与本次无关的全项目审计。确认没有已有生产作业或已提交对象可续接，实时检查账户、比赛、配额和输入后，预记账本，使用剩余1次额度运行准确生产Notebook。

## 7. 正式提交与结果收口

生产必须平台COMPLETE、实际输出存在、schema/端点/覆盖等检查通过、F1启用和冻结源码绑定成立，再按原代码竞赛流程提交准确生产Version/SV一次。不得提交报错的诊断版本、恢复结果表或本地训练集预测，也不先提交后补验证。

满足本任务和原门槛后的生产、正式submission已包含在执行范围，不再询问是否提交。发生网络不明响应先只读核对原对象，不发第二次请求；生产失败时没有剩余备用，真实记录错误。

正式回执绑定比赛、账户、Notebook、Version、SV、submission ID、源代码hash、请求/观测时间、状态和Public。PENDING/RUNNING时Public=null。评分后只读刷新准确G1 submission 56270217，使用相同实际显示精度比较；无法刷新时注明相对归档0.948，不猜测更多小数。

F1高于G1：PUBLIC_IMPROVEMENT_OBSERVED；同精度持平：PUBLIC_TIE；更低：PUBLIC_REGRESSION。均不自动修改最终选择，不宣称Private提升，不自行进入F2或参数扫描。

不创建会话外监控。当前会话未到终态就保存精确作业身份、已消费预算及可续跑命令，下次继续原作业而非重启。已明确停止的候选照实收口，不能为得到一个分数突破门槛。

## 8. 交付保持精简、可续跑、可回读

GitHub仅保存任务书、R/contract_amendment.json、恢复/入口修复代码和小型测试、R/input_manifest.json、R/checkpoints/、R/results.json、R/receipt.json、per_view.csv、final_edge_changes.csv、更新账本及最终报告。可将重复环境/校验字段合并进回执，不另造几十份重复报告。

32份完整预测图、GT图、临时下载链接和凭据放在ignored目录，绝不提交公共GitHub。报告至少给出总体/两胚胎B0与F1分差、计数和门槛结论、正式身份/分数或真实未评分原因、资源实际用量、缺失统计及其影响。

GitHub同步后，固定commit回读本批关键小型文件并比较字节/hash；分别报告“评分恢复”“Kaggle生产”“正式评分”“文件交付”状态。旧云端ERROR、第一次UNKNOWN和本次恢复成功可以同时成立。恢复无效或生产未运行时，不用文件验收掩盖实验状态。

验收重点：优先回收已经付出计算成本的预测结果，给出能决定是否正式评分的数据；不重跑同一套模型，不用简单平均代替官方分，不让丢失的辅助统计无条件拖住有效候选。

## 固定证据入口

- 失败报告： https://github.com/SailorRen/Biohub-CELL/blob/523462f2e667cacda23ea7b8063bc9173d619662/reports/20260919_BIOHUB_F1_RECOVER_AND_SCORE_RESULTS.md
- 账本： https://github.com/SailorRen/Biohub-CELL/blob/523462f2e667cacda23ea7b8063bc9173d619662/experiments/BIOHUB_F1_FLOW_KAGGLE_20260918/ledger.json
- 云端环境回执： https://github.com/SailorRen/Biohub-CELL/blob/523462f2e667cacda23ea7b8063bc9173d619662/experiments/BIOHUB_F1_FLOW_KAGGLE_20260918/diagnostic/runtime_start.json
- 官方冻结评分器： https://github.com/royerlab/kaggle-cell-tracking-competition/blob/075fc5f5a52d11077f9dc2b074644618f26939e2/src/tracking_cellmot/metrics.py
