# BIOHUB_XR0_XD960_SCORE_PAIR_20260925_V01

用户于2026-09-25直接授权的两候选正式评分任务。仓库 SailorRen/Biohub-CELL；唯一执行/交付分支 codex/x138-score-pair-20260925；开发基点6205f21d9366abcc7d39d34f41dc609eb10fc77b；公开研究基点8ce433abbbbab610e5f985aac67c41479c1b3cb3；原源码基点d01c627a3006455d7ac3f4351c76ddf1fd9f4eb2。

## 目标、权限、范围

最终目标是取得XR0、XD960两份实际正式Public。sailorren准备Private母版，向已核实同队成员Can view；队友本人Copy & Edit、完整GPU运行、合格后各提交一次。不登录队友账号、不索要凭据、不切换账号绕过配额。保留A/025、旧X0/X25全部历史、其他运行及最终选择。新任务单独计账，旧失败不退账，不继承旧额度。本任务替代旧任务仅交模板的停点。

先读AGENTS.md及开发基点X138报告、source.diff、candidate_manifest、platform_ledger；公开研究基点PUBLIC_UPDATE；源码基点完整ipynb/source.py/kernel-metadata；20260921 SCORE_TRIO的D960结果。干净隔离worktree、安全fetch与排重；不覆盖用户改动，不reset/stash、强推或合并main。任务及冻结代码先同步本分支、远端回读，再写平台。

## 失败调查

只读核对失败V2实际SV、submission、保存/运行方式、GPU、镜像、Inputs、完整源码与普通日志。主动排查建议30分钟，隐藏traceback不可得记UNKNOWN，不猜velocity。V1的GPU=false不能当作V2根因。明确问题只作有证据的最小工程修复；若旧V2同源码/输入/镜像已完整GPU通过且无可检验部署差异，禁止仅改名盲重提。

## 冻结候选

原ipynb SHA256：6b655e39bbfd2d3d6c762badea69847d3f00f5b548f385cb01b07ee2600fde6d。
XR0保留全部原算法及12个有效代码单元顺序：DET_THRESHOLD=.965、MOTION_RELINK_VELOCITY_WEIGHT=.5、DEEPCENTER_SAFE_DIV_THRESHOLD=.25、VALIDATOR_ENABLE=0、FLOW_MODE=seed，其余原版。
XD960从XR0仅原Cell1主检测阈值及Cell2对应_EXPECTED_NUMERIC守卫改.960；READMIT_MIN_SCORE=.965、velocity=.5不变。禁止全局替换、X25叠加、A私有gate、固定Z边界补丁、形态模型、训练或第三候选。head/flow/低阈缓存/gapfill/DeepCenter/ILP/TTA/旧补点/分裂修复/短轨过滤/linefit/CSV均保持。
历史D960=.948与G1显示持平，不证明阈值提分；XD960在x138上的收益UNKNOWN。

## 固定输入与部署

- pilkwang/biohub-tracking-support-pack-50ep-v1 V10
- pilkwang/biohub-temporal-unet3d-seed314159-v1 V2
- pilkwang/biohub-deepcenter-unet3d-center-prior-v1 V5
- anvithpothula/biohub-v1284-head-s075 V1
- 比赛biohub-cell-tracking-during-development

head v1284_head.pt，33913字节，SHA256 625a0d9340f48193f2ec294fc2d81c5bb3c03087eab78ef0ae998a9c4c7da00c。保留且实际通过原三个主权重哈希断言。不得静默Latest、kernel_sources或改旧资产。
目标T4×2、Internet off；优先请求 gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461。镜像不可用需记录实际镜像、在完整运行验证离线兼容，不伪称完全一致，不转CPU/Colab。实际保存的运行/评分版本须由GPU与日志核对，不能只看metadata或截图；禁止None、空CSV、旧CSV、跳过推理取得提交资格。

## 检查与执行顺序

一批本地nbformat、逐单元AST、嵌入脚本、算法diff、参数读取和补丁顺序；实际support源码验证动态补丁，低阈缓存先于head。优先原日志，不添加复杂包装。不写死可见视频数量/名字/输出哈希，不要求每视频新增节点。辅助报告失败不能人为使已完成预测报错；输入、权重、真实推理、图结构检查保留。
先队友XR0一次GPU Save & Run All，整合依赖、模型加载、模块和真实CSV检查；完整通过立即推进XD960，不等XR0分数。共同错误明确则不复制错误到第二次请求。检查实际CSV字段、完整动态test覆盖、时序/坐标/父子关系、head/缓存/实际参数消费、repair_fallback/deadline_degraded/异常告警；缺字段不默认0，正常零新增不是失效。

2026-09-25用户追加指令：**需要同时提交，GPU剩余时间充足**。GPU充足属于用户确认，非本工具对队友余额独立核验。两份完成输出验收后，同批尽快相继正式提交；不得因“同时”绕过XR0共同部署检查或平台额度。

## 预算与停止条件

计划完整GPU运行2次（各1）；共用备用完整运行最多1次，仅具体工程错误证据及不改算法的局部修复。正式最多2次、各1次、正式重提0。新训练、Dataset写入、独立GPU诊断、CPU转换、Colab、最终选择修改均0。实时核对截止/Code Requirements/团队提交余额/GPU余额/已存在请求。资源不足优先XR0，不取消他任务。8小时仅经验，不是超时或重提门槛。任何已有submission ID仅只读，不换入口重发；Editor Submit产生条目也计账。不建后台监控或跨额度周期自动提交。

## 交付与验收

建议slug sailorren/biohub-x138-xr0-score-20260925 与 sailorren/biohub-x138-xd960-score-20260925；先排重，仅提供真实创建链接。两份完整代码/参数/输入，队友无需拼代码、Git或命令行。
交接：本人Copy & Edit → Private/T4×2/Internet off/固定Inputs → Save & Run All → 输出验收 → 对应精确版本Submit to Competition。
任务/源码/diff/小检查/部署/运行和正式回执/交接/报告同步指定分支，固定commit小文件一次回读记录真实数；CSV、图、权重、原数据、凭据不进Git。
各候选记录kernel、owner、Version、SV、submission、时间、原始状态及Public；模板、完整GPU、正式受理和分数分别报告。未执行为READY_FOR_TEAMMATE_RUN（须母版真实就绪）；受理无分SCORE_PENDING；ERROR不是低分。没有完整GPU及合法输出不得称可评分验收通过，没有Public不得称提分。总验收不得以历史初始研究合同取代本次用户明确合同；仍保留项目旧规则原文。
