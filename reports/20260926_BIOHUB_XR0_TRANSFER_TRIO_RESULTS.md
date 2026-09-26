# XR0 迁移三候选正式评分结果

任务：BIOHUB_XR0_TRANSFER_TRIO_20260926_V01。业务状态：**SCORED_ALL**。三份完整GPU运行、真实输出验收、各一次正式提交和正式终态回收均已执行，3/3取得有效Public。本批未取得高于XR0 0.953的分数；保留A及当前最终选择，没有执行下一批实验。

## 正式结果（MEASURED）

所有时间为中国上海时区，提交时间采用Kaggle官方回执date；最后观测为精确ID API回读时间，非平台实际完成时间。

| 候选 / 精确Notebook链接 | Version / SV | submission ID | 正式终态 | Public | 相对XR0 0.953 | 官方提交时间 | 最后观测时间 | 直接错误 |
|---|---|---|---|---|---|---|---|---|
| [XV25](https://www.kaggle.com/code/sailorren/biohub-xr0-xv25-20260926?scriptVersionId=352908214) | V1 / 352908214 | 56573059 | COMPLETE | 0.953 | +0.000 | 2026-09-26 15:31:40 | 2026-09-26 23:21:09 | 无 |
| [XG95](https://www.kaggle.com/code/sailorren/biohub-xr0-xg95-20260926?scriptVersionId=352908258) | V1 / 352908258 | 56573089 | COMPLETE | 0.929 | -0.024 | 2026-09-26 15:32:41 | 2026-09-26 23:21:09 | 无 |
| [XV25G95](https://www.kaggle.com/code/sailorren/biohub-xr0-xv25g95-20260926?scriptVersionId=352913254) | V1 / 352913254 | 56573515 | COMPLETE | 0.952 | -0.001 | 2026-09-26 15:51:48 | 2026-09-26 23:21:09 | 无 |

三份owner均为sailorren，Kernel ID依次为135935605、135935626、135937770。官方页面也逐条显示Succeeded及相同Public。准确请求/终态原始回执在各候选目录的formal_request_receipt.json、formal_terminal_receipt.json、formal_last_observed.json。未以普通运行、Quick Save、空CSV或旧CSV替代正式评分。

## 本批比较及限制

XV25本次显示分数与XR0持平（0.000）；XG95低0.024；XV25G95低0.001。本次观察没有支持提分的候选。由于每候选只有一次正式Public，且没有隐藏测试逐项诊断，不能将分数差异解释为稳定收益或确定的因果机制。组合与G1单项在普通可见测试中CSV相同，但正式Public不同；可见测试不能替代隐藏测试结果，也不据此猜测平台故障。本轮未变更最终选择、晋级或追加实验。

## 冻结任务、代码与检查（SOURCE_CODE_VERIFIED）

原任务V01/V02与交付manifest核对2/2字节数、SHA256一致，原文未重写。交付commit为5d08e68b642c584d651b2220c1d74e46edbb097e。V02执行授权覆盖三份构建、运行、正式提交和前台等待；V01算法保持不变。

母版为已正式取得0.953的XR0：dongdongjiaqi/biohub-x138-xr0-score-20260925，V1/SV352643547、submission56546951，其完整源码已重新读回并与冻结母版比对。原始12个有效代码单元保持顺序，附加轻量输出回执单元。

XV25只将原无flow自身速度权重改0.25；XG95仅增加冻结G1分裂候选过滤（0.95）；XV25G95组合两项。检测0.965、DeepCenter0.25、head、连续坐标采样、flow、readmit、gapfill、几何、排序及cap等保持XR0设置。未训练、未引入第三项算法修改、未恢复自动选择器。

G1实现参考固定研究commit e67ea3fd5c1d8b45723559e0cf60baea37369caa中的saved_inference.py与ProposalPolicy.admit；使用已有sailorren/biohub-division-train-20260914/1（SV349707105）输出的final模型。实际下载及GPU挂载文件SHA256均核对为0a1f9b93bb529e70f4f7c2ba0907eea8b4cecd2befccc8ba1fb75e569edf77a0。

本地30项小型检查通过：nbformat、逐单元AST、嵌入脚本、参数读取时序、算法diff、原几何/排序/cap还原、动态补丁顺序、G1边界/回退/坐标单位等。低阈缓存及head动态补丁在实际support源码上验证，缓存先于head；不是仅凭AST判定动态生效。另用实际final模型核验有限分数路径。没有额外GPU诊断或第二遍推理。

## 实际部署与普通输出验收（MEASURED）

三份均Private、T4×2、Internet off。实际保存版本API源码回读与冻结候选相同，并均使用原版镜像：
`gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461`。

保存版本Input页逐项核对四项Dataset为：primary pilkwang/biohub-tracking-support-pack-50ep-v1 V10；secondary pilkwang/biohub-temporal-unet3d-seed314159-v1 V2；DeepCenter pilkwang/biohub-deepcenter-unet3d-center-prior-v1 V5；head anvithpothula/biohub-v1284-head-s075 V1；另挂本比赛，G1两份再挂既有Division Train精确V1。未静默使用Latest、未改旧资产。

实际普通日志确认离线依赖载入、双T4分片推理、原三主权重哈希断言、head大小33913及SHA256 625a0d9340f48193f2ec294fc2d81c5bb3c03087eab78ef0ae998a9c4c7da00c、head在低阈缓存补丁之后生效、真实CSV写出。G1两份实际加载final模型和正确哈希。

| 候选 | 普通终态 / 输出检查 | CSV行数 | 速度实际消费计数 | G1候选 / 有限分数 / 过滤 | repair_fallback | deadline_degraded |
|---|---|---:|---:|---|---:|---:|
| XV25 | COMPLETE / PASS | 238260 | 26 | 关闭 | 0 | 0 |
| XG95 | COMPLETE / PASS | 238236 | 26 | 67 / 67 / 17 | 0 | 0 |
| XV25G95 | COMPLETE / PASS | 238236 | 26 | 67 / 67 / 17 | 0 | 0 |

独立逐行核查字段、连续ID、实际测试集合覆盖、坐标、边端点、相邻时序、唯一父节点及最多两个子节点；未写死可见视频数、名称或输出哈希，也未强制每视频新增节点。上述诊断数值均来自普通GPU运行的实际字段，不将缺失字段默认为0。隐藏正式重跑的详细repair/deadline等诊断未取得，记为UNKNOWN；正式终态/分数及输出字节数已从官方精确ID回收，不能把普通运行诊断冒充隐藏重跑诊断。

普通日志警告为依赖弃用、nbconvert转义和Torch JIT内核缓存目录不可写；预测仍完成，未触发repair fallback或deadline降级。JIT内核缓存提示不等于算法的低阈检测缓存失效。中途只读查询出现SSL EOF，已记录；不计作运行失败或新增请求。

## 调度、额度与预算

前两份同批启动，普通运行释放槽位后立即启动组合，不等待Public；各普通输出验收后立即提交精确V1，官方提交时间见上表。平台最大并发上限未明确展示，记为UNKNOWN；实测两份同时运行获准，采取两槽调度，未取消其他任务。GPU界面30小时与API totalTimeAllowed21600秒口径不同，按较小6小时规划。首次提交前实时剩余额度5次，第三份前剩3次。

完整Save & Run **3/3**；共用工程备用 **0/1**；正式请求 **3/3**，每候选1次；正式重提0。训练、Dataset写入、CPU转换、Colab、最终选择修改均0。前台按约10分钟间隔查询准确ID，直到三份正式终态齐全；未创建后台监控或跨周期自动提交。

## Git交付与验收

任务分支：codex/xr0-transfer-trio-20260926，隔离工作区执行，canonical仓库未覆盖用户改动，未reset/stash/强推/合并main。CSV、图、原始数据、权重及凭据未入GitHub。

冻结代码commit 5787a38c114f17f179de6181758c2ef0222c3e28关键文件远端逐字节回读26/26通过；全受理commit ac61c5ce9212c247c1eab8f52c81b4b7c9984ce8关键回执回读11/11通过。最终结果commit与关键文件回读记录将写入本批github_final_readback.json。final_receipt_check.json核对三份身份、SV、非空正式分数、实际输出及请求预算，3/3通过。

冻结验收合同SHA256：be06357a4ea31e6c21aca4456659c12f68f3d793c3a90516b3015f7ae341f9d6。验收器的formal-readback属于预先冻结的manual语义项，不因本次已取得官方回执而改写合同；验收器结论与业务SCORED_ALL分开记录。
