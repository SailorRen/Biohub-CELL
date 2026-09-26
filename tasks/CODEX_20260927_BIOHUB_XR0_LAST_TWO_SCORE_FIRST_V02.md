# Codex：最后两候选，以正式提分为目标，同批运行与提交

任务ID：BIOHUB_XR0_LAST_TWO_20260926_V01  
指令版本：SCORE_FIRST_V02；编写日期：2026-09-27，上海时区。  
仓库：SailorRen/Biohub-CELL  
执行分支：codex/xr0-last-two-20260926  
代码基点：4033cdf778b70cf6957107efaaebeb729f122f7c  
任务文件：tasks/CODEX_20260927_BIOHUB_XR0_LAST_TWO_SCORE_FIRST_V02.md

## 1. 本批目标与授权边界

用户要求：剩余冲刺时间内，以提高正式分数为主，当前报告还有2次提交机会。延续已提出的XD960、XRL9两候选，不再把公开调研、G1退分调查或局部flow诊断放在正式评分之前。本指令覆盖此前聊天中的LAST_TWO V01调度要求；是同一批任务，不是另外增加2次预算。

目标交付是两个不同配置的有效正式submission及其终态，不是两个Quick Save母版，也不是诊断报告。无需再次申请本批既定构建、GPU推理和最多2次正式请求授权。所有收益仍为UNKNOWN，只有正式Public高于XR0的0.953才能记为本批可观察提分；不承诺具体分数。

基线XR0：dongdongjiaqi/biohub-x138-xr0-score-20260925，V1/SV352643547，submission56546951，已归档Public0.953。本批不复跑或重提XR0，不使用XG95或组合版作母版。

## 2. 必要读取与去重，不扩展研究

在代码基点读取以下现有文件，复用已有构建和检查方法：
- AGENTS.md。
- reports/20260926_BIOHUB_XR0_TRANSFER_TRIO_RESULTS.md。
- reports/20260925_BIOHUB_XR0_XD960_SCORE_PAIR_RESULTS.md。
- experiments/BIOHUB_XR0_XD960_SCORE_PAIR_20260925_V01/XR0/candidate.ipynb及kernel-metadata.json。
- 同一目录XD960/candidate.ipynb；只复用算法差异，不继承未验证的旧镜像设置。
- experiments/BIOHUB_TWO_WAVE_20260922_V01/A/consumption_precheck.json。

研究补充入口（非模型运行前置）：61280038d0460a85242df21929431cf7ba51a293下reports/20260926_BIOHUB_PUBLIC_LB_UPDATE.md。该报告未发现已验证高于0.953的公开完整方案，不是穷尽证明。本次网页补查未获得新的可用精确版本证据，不安排新一轮全网搜索。

已有依据：XD960已准备好主检测0.960的单因素源码，但旧报告不是实时提交状态。旧A普通运行选中combo(tight55+bonus125+relaxed9)，只支持XRL9的参数来源，不证明relaxed9单独提分。上一批XV25=0.953、XG95=0.929、XV25G95=0.952，均不晋级；不追加G1阈值试探。

接手先只读核对当前登录身份、GPU余额、可用并发、正式剩余次数、额度重置时间与比赛截止时间。只查询本队这两个准确算法配置及其副本，避免重复运行/提交。今日余额以实际页面/API为准，不按本地午夜推定重置；用户所说2次是上限，不是可绕过平台限制的保证。

如已有同配置运行或submission，续接该对象，保存准确ID；如已取得同配置有效Public，只回收该结果，不重提、不临时发明第三候选。GitHub没有分支不能证明Kaggle没运行。两份普通可见CSV相同，也不能单独判定不同算法在隐藏测试上相同；去重先看源码有效参数、输入和精确版本。

## 3. 固定两个候选

| 参数/模块 | XR0 | XD960 | XRL9 |
|---|---|---|---|
| BIOHUB_DET_THRESHOLD | 0.965 | 0.960 | 0.965 |
| BIOHUB_READMIT_MIN_SCORE | 0.965 | 0.965 | 0.965 |
| BIOHUB_MOTION_RELINK_RELAXED_UM | 10.0 | 10.0 | 9.0 |
| BIOHUB_MOTION_RELINK_FLOW_RELAXED_UM | 0 | 0 | 0 |
| BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT | 0.5 | 0.5 | 0.5 |
| BIOHUB_MOTION_RELINK_LEARNED_BONUS | 1.0 | 1.0 | 1.0 |
| DeepCenter安全分裂阈值 | 0.25 | 0.25 | 0.25 |
| G1 / validator | 关闭 | 关闭 | 关闭 |

### XD960：争取检测召回净收益

独立从XR0构建，只将Cell1主检测阈值及Cell2对应守卫改为0.960。不要全局替换所有0.965；READMIT_MIN_SCORE继续0.965。保留坐标精修和关联处理，让正式评分验证新增检测能否带来净收益。可能增加误检，因此不是已知更优版本。

### XRL9：争取减少宽松阶段错接

独立从XR0构建，只在配置常量读取前明确设置：

```python
os.environ["BIOHUB_MOTION_RELINK_RELAXED_UM"] = "9.0"
```

保持FLOW_RELAXED_UM=0，沿原函数继承宽松门限9.0。无flow和有flow的两条调用路径都检查有效值；紧匹配门限5.5及有flow紧匹配7.0保持原值。保留原raw/flow候选准入、成本、Hungarian、排序与cap；不是对最终边长度做硬删除。可能损失正确长连接，因此只以正式结果判优。

不把bonus1.25、速度0.25、G1、逐点最少4个flow样本、全局漂移或竞争换边混入任何一份。两个候选不合成第三份。

### 共同保持与输入

完整保留原head、连续坐标及特征采样、主副模型、TTA、ILP、flow、readmit、gapfill、几何分裂、短轨过滤、linefit、最终导出及原运行时限保护。低阈检测缓存补丁必须先于head。新增统计只读，不改变原预测。XRL9虽然只改关联参数，后续过滤/平滑仍可能改变最终节点或坐标，不得预先承诺节点不变。

使用上一批成功运行环境：Private、T4×2、Internet off；四项Dataset固定为：
- pilkwang/biohub-tracking-support-pack-50ep-v1，V10。
- pilkwang/biohub-temporal-unet3d-seed314159-v1，V2。
- pilkwang/biohub-deepcenter-unet3d-center-prior-v1，V5。
- anvithpothula/biohub-v1284-head-s075，V1。
另挂本比赛。kernel_sources为空，不挂Division Train或其他候选Output。不得静默使用Latest。

原成功镜像：gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461。
保留三个主权重原哈希断言；head为33913字节、SHA256 625a0d9340f48193f2ec294fc2d81c5bb3c03087eab78ef0ae998a9c4c7da00c。实际GPU和挂载验证并入每份普通运行，不另开GPU探针。

## 4. 以尽早进入评分队列为调度目标

在干净隔离工作区安全续接，不覆盖用户修改、不reset/stash/强推、不合并main。把任务及候选源码提交本分支，回读关键文件后启动；复用旧检查器，不新建复杂验收框架。

仅做必要检查：Notebook/嵌入代码语法、允许diff、参数读取顺序、补丁锚点和实际消费路径。普通运行检查实际CUDA、冻结输入、覆盖全部实际测试对象、字段/坐标/拓扑合法、真实submission.csv、直接错误及repair_fallback/deadline_degraded。未知字段保留UNKNOWN，不把缺失当0。发现明确工程错误仅作最小修复，不能以候选身份提交静默退回原版的输出。

不要求独立CV、局部GT提分、人工病例报告、逐点flow覆盖诊断或G1原因定位作为提交门槛。不新增完整GPU诊断，不为了比较再跑XR0一遍。无需证明每个可见视频都有改动；只确认代码确实消费了指定参数，记录实际输出，不以可见无变化武断认定隐藏无效。

两槽可用就并行启动XD960和XRL9。一份普通运行验收通过，立即正式提交该精确Version/SV；不等另一份结束，不等第一份Public。只有一槽则先XD960、释放普通槽位后立即XRL9，仍不串行等正式评分。不得取消其他人的任务来抢槽。

用户报告正式评分往往需8小时以上，这只用作避免串行等待的规划依据，不是保证。归档截止为上海2026-09-30 07:59，接手时顺手重查官方时间；不拖到截止前才开始长运行。已在运行的同配置继续，不为本指令改名重启。

## 5. 本批总预算与等待

完整Save & Run计划最多2次；共用工程备用最多1次，只修明确工程错误，不换算法或调参。正式submission请求最多2次、每候选最多1次；失败及响应不明均记账。响应不明先查准确对象，禁止盲重发。旧LAST_TWO同批已消耗次数计入，不叠加授权；不自动增加第三份、重跑基线、重训、Dataset写入、共享变更或最终选择修改。

每次真实动作立即保存Notebook、Kernel、Version、SV、submission ID、时间和状态，受理后及时同步GitHub；不得把任务写入或Quick Save记成正式提交。

提交后在执行环境确实允许的持续前台任务中合理间隔查询两个准确ID，不超平台限流。两份终态回收后统一分析；待分写WAITING_FOR_SCORES，不提前淘汰或晋级。出现ERROR单列直接错误及无分，不当作低分。执行环境中断时先保存所有ID和最后状态；恢复只查询已有提交，不重复提交、不声称后台仍在监控。

## 6. 最少交付与判定

结果：reports/20260926_BIOHUB_XR0_LAST_TWO_RESULTS.md。  
账本：experiments/BIOHUB_XR0_LAST_TWO_20260926_V01/platform_ledger.json。

每候选保留完整ipynb、source.diff、有效参数/输入及输出检查、真实正式请求与终态回执。只归档代码和小型证据，不把原数据、图、模型、CSV或凭据提交GitHub。

报告只需要：精确Version/SV/submission、正式Public、相对XR0差值、是否出现直接错误/降级、实际预算、固定commit及关键文件远端回读。若正式Public高于0.953，列为待用户选择的提分候选；同分或更低不替换XR0。Public不是私榜保证；不把局部指标、可见输出或文件大小当正式分数。

本文件交付状态仅为TASK_DEFINITION；候选构建、GPU运行、上传、正式评分状态由Codex实际回执填报。本批结束不自动启动下一轮，也不修改最终选择。
