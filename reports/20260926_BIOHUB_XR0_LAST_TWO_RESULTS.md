# XR0 最后两候选正式评分结果

任务 BIOHUB_XR0_LAST_TWO_20260926_V01；遵循 SCORE_FIRST_V02。平台状态 SCORED_ALL：两份完整 GPU 普通运行、输出验收、正式受理及正式评分均已实际完成。没有修改最终选择，没有启动下一批实验。

## 正式结果

以下为 OFFICIAL_FACT，由准确 submission ID 的官方 API 结果及团队 Submissions 页交叉核验。时间均为上海时区，日期为 2026-09-27；最后 API 观测为 10:05:08。

| 候选 | owner / Notebook | Version / SV | submission ID | 正式终态 | Public | 相对 XR0 0.953 | 正式请求时间 | 直接错误 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| XD960 | sailorren/biohub-xr0-xd960-last-two-20260926 | V1 / 353050916 | 56585147 | COMPLETE | 0.954 | +0.001 | 01:22:53 | 无 |
| XRL9 | sailorren/biohub-xr0-xrl9-last-two-20260926 | V1 / 353050971 | 56587392 | COMPLETE | 0.955 | +0.002 | 03:33:35 | 无 |

精确版本：[XD960](https://www.kaggle.com/code/sailorren/biohub-xr0-xd960-last-two-20260926?scriptVersionId=353050916)、[XRL9](https://www.kaggle.com/code/sailorren/biohub-xr0-xrl9-last-two-20260926?scriptVersionId=353050971)。正式状态源：[团队提交页](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/submissions)。Kernel ID 分别为 135997845、135997875。

比较基线是既有 XR0：dongdongjiaqi/biohub-x138-xr0-score-20260925，V1/SV352643547，submission 56546951，归档 Public 0.953；本批未复跑或重提基线。

MEASURED：XD960、XRL9 分别取得本次可观察 Public 提升 0.001、0.002；XRL9 比 XD960 高 0.001。按任务定义，两份均列为待用户选择的提分候选。该比较不是私榜保证，不证明稳定的跨数据集收益，也不证明两项修改组合有益。本轮不合成第三方案，不自动更改最终选择。

## 构建和运行验收

SOURCE_CODE_VERIFIED：固定任务交付 commit b05a5e115111cfae66424f0b2e7eac09c1b914b8 的原任务 9571 字节及 SHA256 核对通过。沿用 XR0 十二个有效代码单元：XD960 仅 Cell1 主检测阈值及 Cell2 守卫改为 0.960；XRL9 仅在参数消费前设置 RELAXED_UM=9.0。READMIT=0.965、velocity=0.5、DeepCenter 安全分裂=0.25、G1/validator 关闭，其他算法保留。附加只读 head 哈希、参数消费计数及轻量输出验收。

本地必要检查 18/18 通过，覆盖 nbformat、逐单元和嵌入代码 AST、允许算法差异、参数读取顺序、真实 support 源码上的动态补丁以及低阈缓存先于 head。实际保存的两份完整源码与冻结候选一致。

| 检查 | XD960 | XRL9 |
| --- | --- | --- |
| 普通运行 | COMPLETE，1479.6 秒 | COMPLETE，1151.7 秒 |
| 实际 CUDA | 双 Tesla T4 | 双 Tesla T4 |
| CSV 独立验收 | PASS，238585 行 | PASS，238154 行 |
| 主检测阈值实际消费 | 0.960 | 0.965 |
| relaxed / flow 配置 | 10.0 / 0，继承 10.0 | 9.0 / 0，继承 9.0 |
| flow / no_flow 门限消费次数 | 792 / 0 | 792 / 0 |
| repair_fallback / deadline_degraded | 0 / 0 | 0 / 0 |

两份均覆盖实际发现的全部测试对象；CSV 字段、坐标、时序、唯一性、父子关系及图结构验收通过。当前可见数据没有 no_flow 分支调用，不以零调用推断模块失效；对应代码路径及消费位置在构建检查中核验。普通输出不是正式隐藏测试分数。

XD960 CSV SHA256：f698481ed9273e367dae3efce20c5c96cece170cc0286c98d8bd94b36922072c。
XRL9 CSV SHA256：3d852be302e2de612edbc782265909efe4ded6afb952bad6fb869682739d4a03。
CSV、模型和图未进入 GitHub。

## 实际部署

两份均 Private、GPU T4×2、Internet off，另挂比赛，kernel_sources 为空。四项固定 Dataset 为：

- pilkwang/biohub-tracking-support-pack-50ep-v1，V10。
- pilkwang/biohub-temporal-unet3d-seed314159-v1，V2。
- pilkwang/biohub-deepcenter-unet3d-center-prior-v1，V5。
- anvithpothula/biohub-v1284-head-s075，V1。

实际运行镜像摘要均为 37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461。页面虽标 Latest Container Image，实际链接摘要与冻结请求相同；未用标签文字代替摘要核对。

XRL9 四项版本均从实际保存 V1 的 Input 页逐项回读。XD960 主/副/DeepCenter 从实际 Input 页读回，head 以固定 /1 请求、官方数据集当前版本 1 及实际挂载哈希共同核对。两份三个主权重原哈希断言和 head 33913 字节、SHA256 625a0d9340f48193f2ec294fc2d81c5bb3c03087eab78ef0ae998a9c4c7da00c 均实际通过。head、低阈缓存、真实推理及参数消费均有运行日志和小型回执。

告警为依赖弃用、Notebook 转换器转义和 Torch JIT 缓存目录告警；没有推理 Traceback，没有把缺失统计当作 0。只读查分曾发生一次已记录 SSL 连接中断，随后恢复；它不是候选正式错误，不消耗正式请求。

## 调度、预算及证据

启动前核实 sailorren、当时正式剩余 2 次及额度窗口，无活动事件；完整团队 54 条 submission 与本账号 Notebook 列表完成排重。GPU 页面 00:59/30 小时，API 总量 21600 秒、reserved=0，timeUsed 序列化异常，按较小额度规划。并发上限未明确公开，两份普通运行于 00:48:37、00:48:52 同批请求；XRL9 在平台排队后执行，没有重启或取消其他任务。

每份普通输出验收通过后立即正式提交其精确 V1，不等待第一份 Public 才推进第二份。XRL9 提交前页面实时剩余 1 次。已用完整运行 2/2、工程备用 0/1、正式请求 2/2，每候选一次；训练、Dataset 写入、最终选择变更均为 0。没有后台监控、跨额度周期自动提交或下一轮实验。

代码冻结 commit 2a574a0127abdfc46fb8fd33f3d0cc5778a77b3a：关键文件远端逐字节回读 26/26 一致。两份正式回执与验收同步 commit 2c82c57dd5c31140c3422dad6be54ed9be7a70ca：回读 8/8 一致。第一份正式结果同步 commit 3dabd9965575885d259791fb3e132b2b5998e4c8：回读 4/4 一致。最终终态内容 commit 及回读收口回执见本实验目录的 final_remote_readback.json。

完整候选、source.diff、部署配置、必要检查、普通验收、正式请求及终态回执位于 experiments/BIOHUB_XR0_LAST_TWO_20260926_V01/。账本为 platform_ledger.json。冻结验收合同 tasks/CODEX_20260927_LAST_TWO_ACCEPTANCE.json 的 SHA256 为 59b160185e2c36acb882f94354acad88f3c57bad94927007e9c09b8ea66b358c；其 formal-review 为必需人工项，不能仅凭本报告把机器状态写成 COMPLETED_VERIFIED。
