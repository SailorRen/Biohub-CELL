# PUBLIC946 TTA 实测报告

截至 2026-09-08 14:52:10（上海，UTC+08:00），**B0、C1 已完成真实普通推理及独立产物审计，各自唯一正式 submission 均为 PENDING；C2 已创建 Version 1 并在普通推理中。本批尚无正式分数，不能判断是否提分。** 这是执行中记录，整体验收尚未完成。统一事实来源为 `experiments/PUBLIC946_TTA_20260908/results.json`、请求账本和逐对象平台回执；下文区分普通运行、正式评分和 GitHub 交付。

任务为 PUBLIC946_TTA_20260908，任务提交 `a0e63708a60d72e2eab907c03a8cb9c47abe378a`，研究提交 `bf0cda3012f9885587c0ee0da0af348d0ab11c8b`。开始前已安全快进 main、确认工作树干净，未覆盖或夹带用户已有改动。

## 正式身份与评分状态

| 对象 | Notebook | Version / ScriptVersionId / kernel | 普通运行 | submission / 正式状态 | Public Score | 相对 B0 | 相对当前自有最好 | 普通运行实际 PP |
|---|---|---|---|---|---|---|---|---|
| B0 | sailorren/biohub-946-b0-repro-20260908 | 1 / 348114666 / 133498982 | COMPLETE；独立审计通过 | 56091397 / PENDING | UNKNOWN | UNKNOWN | UNKNOWN | tight55 |
| C1 | sailorren/biohub-946-c1-xy8-20260908 | 1 / 348131494 / 133505731 | COMPLETE；独立审计 25/25 PASS | 56092872 / PENDING | UNKNOWN | UNKNOWN | UNKNOWN | relaxed9 |
| C2 | sailorren/biohub-946-c2-secondary-edge-tta-20260908 | 1 / 348150127 / 133513708 | RUNNING；未验收 | 无 / NOT_REQUESTED | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

B0 正式状态的精确回读时间为 14:41:30，C1 为 14:49:49；C2 普通状态回读时间为 14:52:08，均为 2026-09-08 上海时间。B0 于 13:21:47 发起正式请求，C1 于 14:49:00 发起正式请求，两个请求均绑定精确 Version、ScriptVersionId 及 SDK 源码 SHA256，已取得各自 submission ID；均未重复提交。

启动时及 14:52:10 完整自有 submission 列表回读时，可核实的自有最好正式分均为 **0.942**（明确对照身份：V21A，submission 56069192，Version 1 / SV 347862850；另有同分 submission 56066312、56066361）。用户已有 Harmonic submission 56087974 不属于本批。公开 0.946 只作参考，不能预填为 B0 得分。相对 B0、启动时/当前自有最好和公开参考的全部正式分差，以及 Private Score，均为 UNKNOWN。

**正式隐藏重跑的最终文件、实际后处理选择和不可见日志均为 UNKNOWN。** 下文的 tight55、relaxed9、CSV 哈希、数量和 proxy 全部属于普通运行，不能冒充隐藏结果。普通 COMPLETE、合成 PASS、proxy 和 ACTIVE 日志不作为正式成绩；目前没有可成立的提分结论。

## 来源、改动与实际测试

开发母版为 [redoctopusk/biohub-942tta Version 1](https://www.kaggle.com/code/redoctopusk/biohub-942tta?scriptVersionId=347821442)，ScriptVersionId 347821442。实际取得并检查完整 12 个代码单元，实时下载与固定母版字节一致，SHA256 `521cb97f0f457643379a51b60c4f71e3f4cc7d1823fd98cbb97633ffaa515ec4`。母版 Input 页面确认 DeepCenter / 次模型 / 支持包版本分别为 5 / 2 / 10。三个候选 metadata 固定相同输入、Docker、T4×2 和 offline 设置；B0、C1 的实际版本已通过页面补证，C2 的具体输入版本仍待普通运行后的页面回读。

B0 展开算法与原版逐字相同。C1 仅 5 处输入/逆变换白名单修改，把重复 XY 视角替换为反对角线；两模型检测与主模型特征同步逆变换，次模型关联仍用原图单视角特征。C2 独立来自 B0，保留原八 pass/七唯一视角，只把次模型已有编码逆变换、逐视角累加并平均，均值交给现有关联路径。没有增加 encoder、改变关联融合权重或组合 C1+C2。

三个对象保留原 12 单元结构，按各自白名单展开差异；去除 B0 共同审计注入可逐字恢复原 12 单元。原八个 FOV、七个单项后处理候选、条件组合、自动选参与最后重写均完整保留，没有把作者选中的 5.5 写死。新增相同的最终审计单元，在全部选参和重写后只读读取最终 CSV 与真实配置；前序哈希和陈旧参数只作历史记录。

CPU 合成测试已实际执行并保存证据：30 组视角/布局测试覆盖非方形 3×5、方形 5×5、多维及不同分辨率特征；B0/C2 八 pass 七唯一，C1 八唯一。实际展开 predictor 的 encode、采样和 edge-head 调用链以小型测试模型执行，C2 每模型八次编码，检测/主模型结果与 B0 一致，平均特征实际被次模型关联消费。开启和关闭共同审计时生产张量逐元素相同、RNG 不变。最终 CSV 检查 16 个正反例及整个最终 hook 合成执行均 PASS。这些是 MEASURED CPU 合成结论；B0、C1 的真实权重 GPU 证据也已回收并独立审查，C2 的 GPU 结论仍待实际回执。

共同运行审计在每视频前三窗内首次有可用关联时增加一次只读 edge-head 诊断，不增加编码、不改变生产输出。局部数值差异不能说明预测质量，特殊输入零差异也不作为无效判定。原八个验证样本是 FOV，不能称为八个独立胚胎或无偏 CV；训练重叠仍为 UNKNOWN。

## 已取得的普通运行结果

| 普通运行观测 | B0 | C1 | C2 |
|---|---:|---:|---|
| 全 Notebook 耗时 | 5,560.4 秒（92 分 40.4 秒） | 4,857.4 秒（80 分 57.4 秒） | UNKNOWN |
| 生产预测 / 原 train 验证预测 | 575.10 / 988.15 秒 | 547.08 / 913.12 秒 | UNKNOWN |
| 实际自动选择 | tight55 | relaxed9 | UNKNOWN |
| 选参前 / 最终行数 | 241,282 / 241,400 | 240,020 / 239,612 | UNKNOWN |
| 最终节点 / 边 / 分裂父节点 | 122,841 / 118,559 / 102 | 122,003 / 117,609 / 93 | UNKNOWN |
| 实际窗口数 | 1,188 = 396 test + 792 原 train 验证 | 1,188 = 396 test + 792 原 train 验证 | UNKNOWN |
| 独立普通审计 | ORDINARY_SOURCE_INPUT_OUTPUT_RUNTIME_VERIFIED | ORDINARY_SOURCE_INPUT_OUTPUT_RUNTIME_VERIFIED；25/25 PASS | 未执行 |

B0、C1 都实际执行了原七个单项后处理候选。B0 只有 `tight55` 通过原单项正收益规则，完整 overrides 为 `{"MOTION_RELINK_TIGHT_UM": 5.5}`；C1 只有 `relaxed9` 通过该规则，完整 overrides 为 `{"MOTION_RELINK_RELAXED_UM": 9.0}`。两者均未触发原条件组合。实际原验证 proxy 分别为 B0 0.9491896335339407 → 0.951247367385682、C1 0.9471522569212762 → 0.9493918792748964，仅记录自动选择依据。

**C1 与 B0 的最终后处理实际有两项差异。** 两者的基础后处理、权重、输入和依赖相同，但同一自动选择流程得到了不同配置：

| 最终有效参数（µm） | B0 | C1 |
|---|---:|---:|
| MOTION_RELINK_TIGHT_UM | 5.5 | 6.0 |
| MOTION_RELINK_RELAXED_UM | 10.0 | 9.0 |

因此，后续即使取得正式分差，也只能先表述为“该 TTA 修改经过保留的自动后处理流程后的整体结果”，不能当成固定 PP 下的纯 TTA 因果效果。C1 普通输出相对 B0 少 1,788 行、838 节点、950 条边和 9 个分裂父节点，这些数量或 proxy 变化本身不能证明质量提高。

| 普通 CSV 身份 | B0 SHA256 | C1 SHA256 |
|---|---|---|
| 选参前 | `0319ba6d8e864335d3573f6b1a6227c546f17e9247a0c2858fa09b6c2422db3f` | `d93f74e8ea1fd805b3b89df5c585c28224262bfdfb001d8457458e6f457e68eb` |
| 全部选参及重写后 | `a852d1d07ff8c9307d9b10db7f9b4b12e8b1882f14c5dbeb1316d099f0795b3e` | `e0f76698c0de55be2d5e7eefcd6f87f3805621716b45c6b6e047fe1268851873` |

两个普通运行都覆盖实际枚举的 4 个 test 视频：`44b6_0113de3b`、`44b6_0b24845f`、`6bba_05b6850b`、`6bba_05db0fb1`。节点、边引用、重复项、有限坐标、整数标识和时间、下一帧边及分裂拓扑通过源代码绑定的云端最终审计，未混入 train 输出。视频数、行数和哈希只是本次普通观测，不是隐藏测试数量或未来成功条件。完整 submission.csv 未下载或提交 GitHub；本地独立审查核对云端审计、哈希与小型统计，未重新运行全 CSV 校验。

B0、C1 每窗口主/次模型各 8 次编码，额外 encoder 为零；各有 12 个实际视频、每视频 1 次共同只读 edge-head 诊断，其中生产视频 4 次。计数来自实际 JSONL，普通日志中重复打印的 smoke 不重复计数。真实特征、热图及关联张量位于 CUDA、为 float32 且有限，原特征未被审计污染；B0、C1 次模型实际消费均保持原图单视角特征，已观测配对诊断一致。

两次运行使用 T4×2；每次 worker 最大进程 allocated 显存为 728,221,696 bytes、reserved 为 981,467,136 bytes，包含共同审计，不能当成双卡合计或整个平台显存。整个 Notebook 耗时还包含环境准备、后处理、验证评分和自动选参，不能仅累加两个预测阶段。每个对象只有一次普通运行，worker 自动初始化种子可不同，任务未修改种子或原 eval/no-grad 设置；当前耗时差异不能证明稳定提速。

B0、C1 的逐项证据位于 `experiments/PUBLIC946_TTA_20260908/{B0,C1}/`：`independent_audit.json`、`public946_final_audit.json`、`runtime_summary.json`、`ordinary.log`、`ppsweep_selected.json`、`ppsweep_results.csv` 和 `validator_results.csv`。独立审查只覆盖已回收的普通运行，不覆盖正式隐藏评分。

## 源码绑定、预算与未完成项

冻结 manifest SHA256 为 `e126e7fff52941518b70a3dc3c8e9523a804f7fcffdd511079c63f6f098831e7`，在长推理前冻结 22 个文件、源码身份、输入、白名单差异、比较政策和预算。下表分别记录本地文件与 SDK 实际发送的源码身份；API 导出有 JSON 序列化字节差异，三个对象的 13 个有序执行单元均已与冻结候选逐单元匹配。

| 对象 | 本地候选文件 SHA256 | SDK 实际发送源码 SHA256 |
|---|---|---|
| B0 | `c4bfcd8d765c67d35435876b3f3eb7bb810e20556479a918143451e2c61f849c` | `1ae0ac1beb9599308119c380056c05ebc69c230395b37bc3d0966c3107153f19` |
| C1 | `d3264807b20259b86a297a96f258640e7f752830c21f990f52be4c883a628341` | `accb328eeae3732101711c8d9b7e7a2c267ccd787c7228e72244b55f5488331f` |
| C2 | `a7177ccf303152180357ac6f7d23efefec1aa8ab8206bd3bdc99d1efa19b1de6` | `2f714f4159667aed98d4fa9b49256da2e44c29b8697c703f253a4ab765d04759` |

B0、C1 的 checkpoint、支持源码、实际输入版本 5 / 2 / 10 与最终产物绑定已闭合。C2 于 14:51:06 保存并运行 Version 1；已核对远端源码、Version、ScriptVersionId、kernel、设置和输入 slug，但 API 未提供输入具体版本，当前 `remote_binding.verified=false`，尚待运行后页面核验。C2 普通终态、实际后处理、产物、完整耗时、显存及正式结果均 UNKNOWN。

全部写请求先落账，写响应不确定时只读核实。本批已用保存 **3/4**、正式提交 **2/3**、共享工程修复 **0/1**、新 Notebook **3/3**；已发送的 5 次写操作均有单次 HTTP 发送回执，没有自动重试。剩余预算不授权新对象、组合或搜索。C2 仍需普通运行完成、身份和最终审计通过后才能使用本对象唯一正式请求；不得自动重复提交。

C2 写前 14:51:03 的只读额度回执为 GPU 余额约 20.21 小时，当日 UTC 正式提交 3 次、平台日上限 5 次，按完整列表计算剩余 2 次。该数值只代表当时观察，后续写前仍须实时核对，并服从本批剩余正式请求 1 次这一更低上限。

源码、配置、开发和合成测试证据保存在 `experiments/PUBLIC946_TTA_20260908/`，统一状态为 `results.json`，请求账本为 `write_ledger.json`，独立机器验收器为 `verify.py`。大型原始回收保留 ignored `downloads/PUBLIC946_TTA_20260908/`；GitHub 只收源码、小型证据与哈希，不提交比赛数据、权重、submission.csv 或凭据。

## GitHub 交付

| 已验证的执行检查点 | 上海回读时间 | 固定提交字节回读 | 交付范围 |
|---|---|---|---|
| `e974d53179625e3a3ea43dc6ea915f410d93a39d` | 2026-09-08 11:51:09 | 32/32 文件一致 | 开发、测试与 B0 启动时记录 |
| `5380edd95453cd187ccc13272bc769ae2cf53095` | 2026-09-08 13:30:26 | 13/13 文件一致 | B0 普通完成及正式请求、C1 启动时记录 |

两次回读时远端 main 均指向所列固定提交，当时工作区均干净。回执分别为 `downloads/PUBLIC946_TTA_20260908/checkpoint_remote_readback.json` 和 `downloads/PUBLIC946_TTA_20260908/b0_c1_checkpoint_remote_readback.json`，统一 `git_delivery.checkpoints` 已记录。因此不能把整个项目记录写成“尚未同步”；这些检查点也不证明实验已完成。

C1 普通终态与正式请求、C2 启动及本次报告更新属于第二个检查点之后的增量，尚待本轮后续同步和独立远端回读。最终实验交付 commit、C2 验收及正式提交、B0/C1/C2 正式终态成绩均未完成；当前没有提分结论，没有追加实验或后台完成承诺。
