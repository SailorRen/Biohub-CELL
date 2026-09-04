# Biohub V20B 两胚胎配对 safe-div parent radius 实验报告 V01

> 结论边界：本报告汇总冻结证据，但不自行授予 `COMPLETED_VERIFIED`。只有独立领域验证器在读取本报告、重算 promotion、检查秘密与写入预算后，才可在冻结合同范围内给出交付核验状态。交付核验不等于性能提升。

## 结论先行

| 字段 | 观察值 |
| --- | --- |
| task_id | CODEX_20260904_BIOHUB_V20B_TWO_EMBRYO_PAIRED_RADIUS |
| screen | TWO_EMBRYO_PAIRED_SENSITIVITY_SCREEN |
| 报告构建状态 | EVIDENCE_ASSEMBLED_PENDING_INDEPENDENT_VERIFIER |
| 最终领域状态 | BLOCKED_VALIDATION_PAYLOAD_OR_RUNTIME |
| offline promotion decision | BLOCKED_VALIDATION_PAYLOAD_OR_RUNTIME |
| terminal promotion decision | BLOCKED_VALIDATION_PAYLOAD_OR_RUNTIME |
| selected arm | null |
| selected radius um | null |
| submitted | false |
| submission ID | null |
| Public Score | null |
| validation worker status | KernelWorkerStatus.ERROR |
| checkpoint overlap | CHECKPOINT_TRAINING_OVERLAP_UNKNOWN |

最终领域状态为 `BLOCKED_VALIDATION_PAYLOAD_OR_RUNTIME`，离线 decision 为 `BLOCKED_VALIDATION_PAYLOAD_OR_RUNTIME`。selected radius=null。V20B 的离线结果只属于 `TWO_EMBRYO_PAIRED_SENSITIVITY_SCREEN`；如果产生候选，也只能称为 **Kaggle test candidate**。新的 Kaggle Public Score 才可能提供 hidden-test 性能证据，当前值为 `null`。

## 证据边界与历史不变量

V20A 为什么停止：其冻结状态仍为 `BLOCKED_INSUFFICIENT_EMBRYO_GROUPS`，R70/R80/R90 均为 `NOT_RUN_HARD_GATE`。V20B 是新合同，不是对 V20A 的历史回填。V20B 允许两个 embryo 层的配对敏感性筛选，是因为比较发生在同一批样本与同一 upstream cache 上，但这不会增加独立 embryo 数量。

199 个 structurally eligible labeled train samples 分属 44b6（71）与 6bba（128）。199 个 field of view 不等于 199 个独立 embryo；两个 embryo 内部样本也不能被当作相互独立的生物重复。本实验不是 CV、不是 3-fold/5-fold，不使用 sample-level 显著性宣称跨胚胎泛化。checkpoint 训练数据与 split 未闭合，故证据状态持续为 `CHECKPOINT_TRAINING_OVERLAP_UNKNOWN`。

离线 official score 是固定 scorer 在训练侧带标签数据上的度量，不是 Kaggle Public Score。历史 0.939 只绑定 V19C Version 1 / ScriptVersionId 346969653 / submission 55978992；页面历史分数不得代填为 V20B 分数。

## 平台对象与版本链

| object | Notebook Version | ScriptVersionId | submission ID | Public Score | evidence status |
| --- | --- | --- | --- | --- | --- |
| historical V19C baseline | 1 | 346969653 | 55978992 | 0.939 | OBSERVED_HISTORICAL_ONLY |
| V20B validation | 1 | 347223762 | null | null | VALIDATION_EVIDENCE_ONLY |
| V20B production | null | null | null | null | NOT_APPLICABLE_VALIDATION_BLOCKED |

## Validation 终态与失败诊断

| 字段 | 权威观察或冻结诊断 |
| --- | --- |
| worker status | KernelWorkerStatus.ERROR |
| failed stage | PREDICTOR_PATCHES |
| error type | RuntimeError |
| observed error | Calibrated dual-seed patch 2 expected one match, found 0 |
| internal wall-clock seconds | 223.33422 |
| platform log runtime seconds | 242.6 |
| authenticated UI runtime | 4m 3s GPU T4 x2 |
| predictor runs started | 0 |
| payload preflight completed | false |
| R70 metrics | NOT_RUN |
| R80 metrics | NOT_RUN |
| R90 metrics | NOT_RUN |
| root-cause code | GUARD_WRAPPER_INDENTED_MULTILINE_PATCH_SENTINEL |
| root-cause summary | The validation builder wrapped inherited V19C code in a try block by adding four leading spaces to every physical source line. That mechanical indentation also changed the content of the triple-quoted `_old` TTA patch sentinel. The pinned support source therefore did not match the altered sentinel; the optional TTA patch emitted a warning, and mandatory dual-seed patch 2 then found zero `_nv` blocks and failed closed. |

失败诊断用于解释为什么 validation fail-closed，不把未运行的 payload、cache、R70/R80/R90 指标补写为 PASS。静态 `--validate-only` 通过只证明构建侧检查，不证明动态 patch chain 能在 Kaggle 固定 support source 上成功应用。冻结 `retry=0` 控制后续行为：根因已定位也不授权第二次 SaveKernel。

## 平台写入与轮询精确计数

| 操作 | 物理调用计数 |
| --- | --- |
| validation SaveKernel | 1 |
| production SaveKernel | 0 |
| SaveKernel total | 1 |
| Kaggle Notebook platform run | 1 |
| formal competition submission | 0 |
| submission status poll | 0 |
| retry | 0 |
| duplicate submission | 0 |
| Dataset write | 0 |
| Model write | 0 |
| unauthorized Kaggle write | 0 |

`notebook_run` 指 Kaggle Notebook 平台 run，与 validation 内部的 predictor logical runs、full/cache 比较不是同一个计数。ledger 采用 `PHYSICAL_API_CALL_COUNTED_AT_STARTED_BEFORE_INVOCATION`，错误也消耗对应物理调用预算；任何错误均不得 retry。

## 两个 embryo 的独立结果

| arm | embryo | status | samples | offline official score | division Jaccard | division TP | division FP | division FN | node-count penalty | frame cap rate | global cap rate | topology valid | runtime seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R70 | 44b6 | NOT_AVAILABLE | null | null | null | null | null | null | null | null | null | null | null |
| R70 | 6bba | NOT_AVAILABLE | null | null | null | null | null | null | null | null | null | null | null |
| R80 | 44b6 | NOT_AVAILABLE | null | null | null | null | null | null | null | null | null | null | null |
| R80 | 6bba | NOT_AVAILABLE | null | null | null | null | null | null | null | null | null | null | null |
| R90 | 44b6 | NOT_AVAILABLE | null | null | null | null | null | null | null | null | null | null | null |
| R90 | 6bba | NOT_AVAILABLE | null | null | null | null | null | null | null | null | null | null | null |

表内 official score 是离线 scorer 结果。44b6 与 6bba 始终分开陈述，不能只以 199 样本 pooled 总和替代，因为 6bba 的 128 个样本会压过 44b6 的 71 个样本。

## embryo-equal macro 与 pooled micro

| arm | scope | samples | offline official score | adjusted edge Jaccard | division Jaccard | node-count penalty | topology valid | schema valid | runtime seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R70 | EMBRYO_EQUAL_MACRO | null | null | null | null | null | null | null | null |
| R70 | POOLED_MICRO | null | null | null | null | null | null | null | null |
| R80 | EMBRYO_EQUAL_MACRO | null | null | null | null | null | null | null | null |
| R80 | POOLED_MICRO | null | null | null | null | null | null | null | null |
| R90 | EMBRYO_EQUAL_MACRO | null | null | null | null | null | null | null | null |
| R90 | POOLED_MICRO | null | null | null | null | null | null | null | null |

embryo-equal macro 对 44b6 与 6bba 等权；pooled micro 汇总全部 sample。两者并列是为了揭示样本数不平衡，不代表两次独立复现，也不构成 CV。

## 冻结晋升 gate 的实际结果

| candidate | gate | result |
| --- | --- | --- |
| R80 | NOT_AVAILABLE_VALIDATION_BLOCKED | null |
| R90 | NOT_AVAILABLE_VALIDATION_BLOCKED | null |

### 预注册 gate 定义

| gate | 冻结解释 |
| --- | --- |
| 两个 embryo official score 均不劣于 R70 | 容差 0.0001；不得只看 pooled |
| 至少一个 embryo 严格改善 | strict positive epsilon=1e-12 |
| embryo-equal macro 严格改善 | 两个 embryo 等权，防止 128 样本组压过 71 样本组 |
| pooled micro 不劣 | 容差 0.0001；仅为并行聚合口径 |
| pooled division Jaccard 严格改善 | 不能只用 division recall |
| 任一 embryo division Jaccard 无实质下降 | 最大允许下降 0.0001 |
| division FP 增长被补偿 | 需要新增 TP 且 official total gain 为正 |
| topology 与 schema 全部通过 | 597 个 arm/sample 检查 |
| cap saturation 无实质恶化 | frame/global cap 均纳入 |
| node-count penalty 无无法解释恶化 | 不能被总体分数掩盖 |
| 收益不完全由单 sample 驱动 | 至少两个正向 sample |
| source/cache/checkpoint/input/support/scorer identity 一致 | 共享 upstream cache |
| 唯一变化为 parent radius | R70=7.0、R80=8.0、R90=9.0 |
| runtime 在冻结预算内 | validation 39600 秒；production 2700 秒 |

promotion decision 必须可由指标机器重算。若只有一个 candidate 通过则选择；若两个都通过，依次按 maximin embryo delta、macro、micro、division Jaccard、较少新增 FP、较低 cap saturation、较短 runtime 判定；仍相同则 `NO_UNIQUE_WINNER_NO_SUBMISSION`。

## 用户要求的 20 个问题逐项回答

### Q1. V20A 为什么停止

V20A 的冻结领域状态保持为 BLOCKED_INSUFFICIENT_EMBRYO_GROUPS，因为当时合同要求至少 3 个 embryo groups；实际只有 44b6 与 6bba 两组。因此 V20A 的 R70/R80/R90 都保持 NOT_RUN_HARD_GATE，V20B 没有回填或改写这段历史。

### Q2. V20B 为什么允许两个 embryo 的配对敏感性实验

V20B 是新冻结合同，把目标限定为 TWO_EMBRYO_PAIRED_SENSITIVITY_SCREEN：同一批 199 个样本在共享 pre-division cache 下只改变 safe-div parent radius，并分别保留 44b6 与 6bba 两个报告层。它允许做方向一致性和敏感性筛选，但不把两组扩写成多折验证。

### Q3. 为什么本实验不是 CV

没有训练/验证折轮换、没有 held-out fold，也没有 3-fold 或 5-fold；两个 embryo 都是训练侧带标签数据上的配对评估。每个 embryo 内的 field of view 也不是独立生物重复，因此不得称为 CV 或以 sample-level 显著性推断跨胚胎泛化。

### Q4. checkpoint overlap 为什么仍是 UNKNOWN

当前证据只固定了 checkpoint SHA，没有闭合 checkpoint 的训练样本和 split；因此必须持续写 CHECKPOINT_TRAINING_OVERLAP_UNKNOWN，不能从文件 hash 推断训练重叠不存在。

### Q5. 是否实际读取全部 199 个 payload

否或未能证明。完整 199 个 payload 的 PASS 证据不存在，报告不把文件名枚举当作 payload 读取。

### Q6. cache 是否通过完整运行等价性验证

否或未到达；cache equivalence 没有 PASS，所以不得晋升或提交。

### Q7. R70 是否复现

否。R70 metrics=NOT_RUN；运行在 PREDICTOR_PATCHES、predictor subprocess 启动前 fail-closed，因此没有 R70 复现证据。

### Q8. R80/R90 相对 R70 的每 sample 和每 embryo delta

逐 sample 配对表共有 0 行，逐 embryo 配对表共有 0 行；完整数值列于附录 A/B。没有用 pooled 结果替代两个 embryo 的独立 delta。arm 状态为 R70=NOT_RUN、R80=NOT_RUN、R90=NOT_RUN。

### Q9. embryo-equal macro 与 pooled micro 是否一致

验证在聚合阶段前已阻断，embryo-equal macro 与 pooled micro 均无可用结果，不能判断方向是否一致。

### Q10. division TP/FP/FN 如何变化

R80/R90 相对 R70 的 division TP、FP、FN 变化分别按 44b6、6bba 列于附录 B，逐 sample 变化列于附录 A；主表同时给出每个 arm 的绝对 confusion counts。晋升 gate 还要求 FP 增长必须由新增 TP 与 official total gain 补偿。

### Q11. 是否出现 cap、topology 或 node-count 风险

未评估：三个 arm 的 metrics 均为 NOT_RUN，所以 cap、topology 与 node-count 风险都是 NOT_AVAILABLE，而不是 PASS。运行失败本身发生在指标生成之前。

### Q12. 是否有唯一 Kaggle test candidate

没有唯一 Kaggle test candidate；decision=BLOCKED_VALIDATION_PAYLOAD_OR_RUNTIME，selected radius=null。 离线候选措辞仅为 Kaggle test candidate，不表示已证明提分、预计高于 0.939 或新最佳。

### Q13. 是否创建 Notebook Version

validation：Notebook Version=1，ScriptVersionId=347223762；production：NOT_APPLICABLE_VALIDATION_BLOCKED。

### Q14. 是否创建 submission

否；没有带 submission ID 的 V20B 正式 submission。

### Q15. submission ID

submission ID=null。未创建时严格写 null。

### Q16. 30 分钟状态

NOT_APPLICABLE_NO_SUBMISSION；poll count=0。监控不适用、未来读分仍须用户明确通知。

### Q17. Public Score 当前值或 null

V20B 当前 Public Score=null。历史 V19C Public Score=0.939 仅绑定 baseline submission 55978992，不得代填到 V20B。

### Q18. retry 是否为 0

是；ledger retry=0，validation/production/submission 任一路径均禁止自动重试。duplicate_submit=0。

### Q19. 未解决的证据缺口

CHECKPOINT_TRAINING_OVERLAP_UNKNOWN：checkpoint 训练集合与 split 未闭合；仅有两个训练胚胎，199 个 field of view 不是 199 个独立生物重复；离线 official scorer 结果不是 hidden-test Public Score，也不证明 Kaggle 提分；新的 V20B Public Score 当前为 null；没有观察到的分数就没有性能提升证据；本路径没有创建带 submission ID 的 V20B 正式提交；验证或平台路径在阶段 PREDICTOR_PATCHES fail-closed；已定位运行根因 GUARD_WRAPPER_INDENTED_MULTILINE_PATCH_SENTINEL；冻结 retry=0 不授权修复后重跑。

### Q20. 后续必须由用户显式通知读取分数

是。未来任何 Public Score 回读都需要用户新的明确通知；本任务不后台 sleep、不建 cron、不等待约 10 小时，也不因 pending 或无分数创建新 Version/重复提交。

## 必报 22 类指标覆盖说明

| 序号 | 指标 | 报告层级 |
| --- | --- | --- |
| 1 | official total score | sample / embryo / global |
| 2 | adjusted edge score/Jaccard | sample / embryo / global |
| 3 | division Jaccard | sample / embryo / global |
| 4 | division TP、FP、FN | sample / embryo / global |
| 5 | node-count adjustment/penalty | sample / embryo / global |
| 6 | predicted node count | sample / embryo / global |
| 7 | GT/estimated node count 与证据等级 | sample / embryo / global |
| 8 | edge TP、FP、FN | sample / embryo / global |
| 9 | fragmented edges | sample / embryo / global |
| 10 | lost-to-detection edges | sample / embryo / global |
| 11 | wrong-association edges | sample / embryo / global |
| 12 | safe-division candidate count | sample / embryo / global |
| 13 | accepted division count | sample / embryo / global |
| 14 | DeepCenter accepted/rejected count | sample / embryo / global |
| 15 | frame cap saturation | sample / embryo / global |
| 16 | global cap saturation | sample / embryo / global |
| 17 | topology validity | sample / embryo / global |
| 18 | schema validity | sample / embryo / global |
| 19 | runtime | sample / embryo / global |
| 20 | peak memory | sample / embryo / global |
| 21 | pre-division cache SHA | sample / embryo / global |
| 22 | final output SHA | sample / embryo / global |

数值主表只展示决策所需摘要；逐 sample 的 paired delta 在附录 A，逐 embryo delta 在附录 B。原始完整 metric CSV、runtime receipts、cache SHA 与 final output SHA 保留为机器证据。本报告不复制 raw image、GT、模型权重或 submission.csv。

## 附录 A：R80/R90 相对 R70 的逐 sample paired delta

`NOT_AVAILABLE_VALIDATION_BLOCKED`：验证在逐 sample paired delta 产物形成前 fail-closed，不能从部分日志推算或填补数值。

## 附录 B：R80/R90 相对 R70 的逐 embryo paired delta

| candidate | embryo | samples | official score delta | division Jaccard delta | division TP delta | division FP delta | division FN delta | node-count penalty delta | frame cap rate delta | global cap rate delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R80 | 44b6 | null | null | null | null | null | null | null | null | null |
| R80 | 6bba | null | null | null | null | null | null | null | null | null |
| R90 | 44b6 | null | null | null | null | null | null | null | null | null |
| R90 | 6bba | null | null | null | null | null | null | null | null | null |

## 附录 C：报告输入的 SHA-256

| repository-relative artifact | SHA-256 |
| --- | --- |
| experiments/V20B/artifact_manifest.json | 39eaf37a9210df99a03a69b0f2328e8563af9f19626cfe1c8d92d3a1871e84d0 |
| experiments/V20B/contract.json | ea46844436142e61c3bc570b4e616531b69eca2cbc609935cf84ce768d41a40b |
| experiments/V20B/evidence_boundary.json | 48fc1b23c0930e05c0371d9d6d0a85dd595bb440c85b11aff5910d589c7d548f |
| experiments/V20B/failure_diagnosis.json | 705c4fdd24ab7923386baafcb11b3c3a1a43ac42474eb9d1025de70f57d79c15 |
| experiments/V20B/kaggle_validation_terminal_receipt.json | 3f8e73a0137508a3323b94e5c83714aa1051acda5afca1ba6478c3265c5f7f50 |
| experiments/V20B/kaggle_validation_v1_log.txt | 0fb7fc3b61d556f60dc477030a7cc9fb17c9d1f950b78fc5543a14a08f0f707e |
| experiments/V20B/platform_write_ledger.json | 062a9553aeee82334b28ec4225e687751d34380b34ce23a8f5d8e9a5ead9bc85 |
| experiments/V20B/promotion_decision.json | 285bd63a443a097f4ab902d03bb61d7ef8d41a9379dad2914e8024c05551b08a |
| experiments/V20B/runtime_receipts.json | 8d8aa49c1c391fa4bdc7642175d04a1039333729ea762492aaf5afe90c4bdf7b |
| experiments/V20B/sample_manifest.json | 7b028996131fc189f8a480b8e1c01f26f72131877758680af9ed1b7c9edce842 |
| experiments/V20B/write_budget.json | 2ee55ca9d1a39b077d116800f0af7240780cdc56e68d22ffb973e632f9ec8186 |

这些 hash 证明本报告读取的本地证据字节；它们不单独证明 Kaggle 远端对象、Public Score 或 GitHub 交付。远端对象与 GitHub fixed-commit blob 必须由各自权威回读另行验证。

## 终态解释与明确未声明事项

- `EVIDENCE_ASSEMBLED_PENDING_INDEPENDENT_VERIFIER` 只表示报告构建器完成了严格输入检查与渲染，不是领域验证器结论。

- 即使最终 VERIFY JSON 为 `COMPLETED_VERIFIED`，其含义也仅是冻结合同内的交付与证据链通过；不能改写为模型性能提升。

- `CHECKPOINT_TRAINING_OVERLAP_UNKNOWN` 仍是未解决证据缺口；两个训练 embryo 的结果不证明 hidden test 提分。

- Public Score 为 `null` 时必须原样保留，不能用 0、历史 0.939、离线 proxy 或预测值替代。

- 若没有 submission，30 分钟监控为 `NOT_APPLICABLE_NO_SUBMISSION`；不得虚构已经监控。未来读分仍须用户明确通知。

- 若有 submission，本报告只记录冻结 30 分钟窗口内的观察值；不会后台 sleep、创建 cron、等待约 10 小时、重提或另存 Version。

监控不适用、未来读分仍须用户明确通知。
