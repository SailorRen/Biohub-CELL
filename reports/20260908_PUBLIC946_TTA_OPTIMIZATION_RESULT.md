# PUBLIC946 TTA 实测报告

截至 2026-09-08 13:23:52（上海，UTC+08:00），**B0 已完成真实普通推理、最终产物审计及唯一正式提交，正式状态 PENDING；C1 已启动普通推理，C2 尚未运行。本批尚无正式分数，不能判断是否提分。** 这是执行中记录，整体验收尚未完成；统一事实来源为 `experiments/PUBLIC946_TTA_20260908/results.json`、请求账本和各对象实际平台回执。

任务：PUBLIC946_TTA_20260908。任务提交 `a0e63708a60d72e2eab907c03a8cb9c47abe378a`，研究提交 `bf0cda3012f9885587c0ee0da0af348d0ab11c8b`。已安全快进 main，开始时工作树干净，既有实验未改。

## 正式结果

| 对象 | Notebook | Version / ScriptVersionId | 普通运行 | submission / 正式状态 | Public Score | 相对 B0 | 相对启动时自有最好 | 相对公开 0.946 | 实际 PP |
|---|---|---|---|---|---|---|---|---|---|
| B0 | sailorren/biohub-946-b0-repro-20260908 | 1 / 348114666 | COMPLETE；独立审计通过 | 56091397 / PENDING | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | 普通运行：tight55 |
| C1 | sailorren/biohub-946-c1-xy8-20260908 | 1 / 348131494 | RUNNING | 无 / NOT_REQUESTED | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| C2 | sailorren/biohub-946-c2-secondary-edge-tta-20260908 | NOT_RUN | NOT_RUN | 无 / NOT_REQUESTED | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

启动时及 13:23:52 完整自有 submission 列表回读时，可核实的自有最好正式分均为 **0.942**（明确对照身份：V21A，submission 56069192，Version 1 / SV 347862850；另有同分 submission 56066312、56066361）。B0 精确正式回读时间为 13:22:17，C1 普通状态回读时间为 13:23:50，均为 2026-09-08 上海时间。用户已有 Harmonic submission 56087974 不属于本批。公开 0.946 仍只是参考，不能预填为 B0 得分。相对 B0、启动时/当前自有最好和公开参考的全部正式分差均为 UNKNOWN，Private Score 也为 UNKNOWN。普通 COMPLETE、合成 PASS、proxy 和 ACTIVE 日志均不作为正式成绩。

## 来源、改动与实际测试

开发母版为 [redoctopusk/biohub-942tta Version 1](https://www.kaggle.com/code/redoctopusk/biohub-942tta?scriptVersionId=347821442)，ScriptVersionId 347821442。实际取得完整 12 个代码单元并核验全部源码，实时下载与固定母版字节一致，SHA256 `521cb97f0f457643379a51b60c4f71e3f4cc7d1823fd98cbb97633ffaa515ec4`。母版 Input 页面确认 DeepCenter / 次模型 / 支持包版本分别为 5 / 2 / 10，三个候选 metadata 固定同一输入、Docker、GPU 和 offline 设置。

B0 展开算法与原版逐字相同。C1 仅 5 处输入/逆变换白名单修改，把重复 XY 视角替换为反对角线；两模型检测与主模型特征同步逆变换，次模型关联仍用原图单视角特征。C2 独立来自 B0，保留原八 pass/七唯一视角，只把次模型已有编码逆变换、逐视角累加并平均，均值交给现有关联路径。无额外 encoder、融合权重或参数变化，无 C1+C2 组合。

原 12 单元去除共同审计注入后逐字恢复，原八 FOV、七单候选和条件组合、自动选参与最后重写完整保留。没有把作者选中的 5.5 写死。新增相同的最终审计单元，在全部选参和重写后只读读取最后 CSV 与真实配置；前序 hash 和陈旧参数只作历史记录。

CPU 合成测试实际执行通过：30 组视角/布局测试覆盖非方形 3×5、方形 5×5、多维及不同分辨率特征；B0/C2 八 pass 七唯一，C1 八唯一；真实展开 predictor 和支持库 encode、采样、edge-head 调用链使用小型测试模型执行，C2 每模型八次编码，检测/主模型结果与 B0 一致，平均特征实际被次模型关联消费。开启和关闭共同审计时生产张量逐元素相同，RNG 不变。共同最终 CSV 检查的 16 个正反例及整个最终 hook 合成执行均 PASS。以上是 MEASURED CPU 合成结论。B0 真实权重 GPU smoke 已回收并通过独立核对；C1、C2 的 GPU 及最终产物结论仍分别等待实际运行证据。

公共审计每视频只在前三窗内首次有可用关联时增加一次只读 edge-head 诊断，新增 encoder 为零；不改变生产输出。局部数值差异不能说明预测质量，特殊输入零差异也不作为无效判定。原八样本是 FOV，不声称八个独立胚胎或无偏 CV；训练重叠 UNKNOWN。

## B0 已验证的普通运行

B0 在 2026-09-08 11:41:41（上海）发起保存，Version 1 / ScriptVersionId 348114666 / kernel 133498982。普通运行已为 COMPLETE，页面记录全 Notebook 耗时 **5,560.4 秒，即 92 分 40.4 秒**；其中生产预测 575.10 秒、原八个 train 验证 FOV 预测 988.15 秒，其余为环境准备、后处理、验证评分与原参数选择等阶段。不能把两个预测阶段相加当成整个 Notebook 耗时。

原七个单项后处理候选全部执行；只有 `tight55` 通过原单项正收益规则，原条件组合没有触发。实际选择 `tight55`，完整 overrides 为 `{"MOTION_RELINK_TIGHT_UM": 5.5}`；起始值仍为 6.0，其他最终后处理参数与 B0 基础配置一致。5.5 来自本次原自动选择流程，没有写死。原验证 proxy 从 0.9491896335339407 到 0.951247367385682，仅记录选择依据，不代表 Kaggle 正式成绩。

| B0 普通产物 | 选参前 | 全部选参及重写后 |
|---|---:|---:|
| 行数 | 241,282 | 241,400 |
| 最终节点 / 边 / 分裂父节点 | — | 122,841 / 118,559 / 102 |
| CSV SHA256 | `0319ba6d8e864335d3573f6b1a6227c546f17e9247a0c2858fa09b6c2422db3f` | `a852d1d07ff8c9307d9b10db7f9b4b12e8b1882f14c5dbeb1316d099f0795b3e` |

最终输出覆盖本次普通运行实际枚举的 4 个 test 视频，节点、边引用、重复项、有限坐标、整数标识和时间、下一帧边及分裂拓扑均通过源代码绑定的云端最终审计。没有意外 train 输出混入。4 个视频和 241,400 行是本次观测结果，不是隐藏测试数量或未来成功条件；未将完整 submission.csv 下载或提交 GitHub，本地独立审查核对云端审计、哈希及小型统计，未假称本地重新运行全 CSV 校验。

实际 GPU worker 回执共 **1,188 个不同窗口：396 个 test 生产窗口、792 个原 train 验证窗口**。每窗口主/次模型各 8 次编码，没有新增 encoder；12 个实际视频各有 1 次共同只读 edge-head 诊断，其中生产视频 4 次。普通日志中 smoke 重复打印不重复计入调用数。明细验证原特征未被污染，特征、热图和实际关联张量位于 CUDA、为 float32 且有限；B0 次模型实际消费仍是原图单视角特征，已观测配对诊断差异为零。

本次使用两张 Tesla T4；worker 最大进程 allocated 显存为 728,221,696 bytes，最大进程 reserved 为 981,467,136 bytes，均包含共同审计，不是双卡合计或整个平台显存。真实 checkpoint、支持源码及输入版本 5 / 2 / 10 已闭合。B0 本地文件 SHA256 为 `c4bfcd8d765c67d35435876b3f3eb7bb810e20556479a918143451e2c61f849c`，SDK 实际提交源码 SHA256 为 `1ae0ac1beb9599308119c380056c05ebc69c230395b37bc3d0966c3107153f19`，API 导出源码 SHA256 为 `703278ee6dfb3792f8a0049f7a295d68b7e6bb1df6de49115355fe415dc91a54`；文件字节因 JSON 序列化不同，13 个有序执行单元源码全部一致。

独立审查回执为 `experiments/PUBLIC946_TTA_20260908/B0/independent_audit.json`，最终审计为 `B0/public946_final_audit.json`，GPU 汇总为 `B0/runtime_summary.json`，完整普通日志为 `B0/ordinary.log`，选参依据为 `B0/ppsweep_selected.json`、`B0/ppsweep_results.csv` 和 `B0/validator_results.csv`。独立普通审查结论为 `ORDINARY_SOURCE_INPUT_OUTPUT_RUNTIME_VERIFIED`，只覆盖已回收的普通运行。

## 执行与证据边界

冻结 manifest SHA256：`e126e7fff52941518b70a3dc3c8e9523a804f7fcffdd511079c63f6f098831e7`。已在长推理前冻结 22 个文件、源码身份、输入、三个差异、比较政策和预算。全部请求先落账；每个对象正式提交最多一次，写响应不明只读核对。当前保存 **2/4**、正式提交 **1/3**、共享修复 **0/1**，新 Notebook **2/3**；已发送的 3 次写操作均有单次 HTTP 发送回执，没有自动重试。

B0 于 2026-09-08 13:21:47（上海）提交精确 Version 1，正式 submission **56091397** 已受理，状态 **PENDING**，Public/Private 均无分数。正式描述绑定 B0、Version、ScriptVersionId 和 SDK 源码哈希。**正式隐藏重跑的最终文件、后处理选择和不可见日志均为 UNKNOWN**，不得拿普通运行的 tight55、CSV 哈希、节点数或 proxy 冒充隐藏结果。

C1 于 2026-09-08 13:22:41（上海）保存并运行，Version 1 / ScriptVersionId **348131494** / kernel **133505731**，当前 RUNNING，未正式提交。API 回读 13 个执行单元与冻结 C1 一致；截至此报告快照，输入具体版本的当前 C1 页面补证仍待完成，因此其 `remote_binding.verified` 尚为 false。C1 最终产物、实际后处理选择、完整耗时和正式成绩均 UNKNOWN。C2 已完成本地构建和测试，仍为 NOT_RUN，未创建 Notebook、未保存 Version、未提交。

截至 13:23:52 的只读平台观察，GPU 余额约 21.54 小时；当日 UTC 正式提交共 2 次，平台日上限 5 次，按完整列表计算剩余 3 次。该数值是特定读取时点的额度，不是后续写入保证；每次请求前继续以实时剩余额度为更低上限。

源文件、开发回执、实际测试、逐对象源码与配置位于 `experiments/PUBLIC946_TTA_20260908/`。统一状态为 `results.json`，请求账本为 `write_ledger.json`，独立机器验收器为 `verify.py`。大型原始回收保留 ignored `downloads/PUBLIC946_TTA_20260908/`，GitHub 仅收源码、小型证据与哈希；不提交比赛数据、权重、submission.csv 或凭据。

## GitHub 交付

执行检查点已经同步：固定提交 **`e974d53179625e3a3ea43dc6ea915f410d93a39d`** 于 2026-09-08 11:51:09（上海）完成 **32/32 文件的 GitHub 固定提交字节回读**，全部哈希一致，回读时远端 main 指向同一提交、当时工作区干净。证据为 `downloads/PUBLIC946_TTA_20260908/checkpoint_remote_readback.json`，统一状态中的 `git_delivery` 记录相同 checkpoint。

该检查点证明此前开发与执行中记录已交付；不证明本批实验完成。B0 普通终态及正式提交、C1 启动与本次报告更新属于检查点之后的增量，后续内容提交和最终远端回读仍须单独记录。当前本批没有正式终态成绩、没有可成立的提分结论；C1 运行、C2 运行与正式结果等仍未完成。没有自动追加实验、跨日重跑或后台完成承诺。
