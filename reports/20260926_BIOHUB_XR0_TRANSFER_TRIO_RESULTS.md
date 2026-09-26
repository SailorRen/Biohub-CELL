# XR0 迁移三候选执行结果

当前状态：WAITING_FOR_SCORES。三份普通 GPU 运行和输出验收全部通过，均已逐份正式受理。正式评分尚未齐，本报告不作方案优劣判断。

## 对象与回执

| 候选 | owner / Kernel slug | Version / SV | 普通运行 | submission ID | 正式状态 | Public | 提交时间（上海） |
|---|---|---|---|---|---|---|---|
| XV25 | sailorren/biohub-xr0-xv25-20260926 | V1 / 352908214 | COMPLETE，输出 PASS | 56573059 | PENDING | UNKNOWN | 2026-09-26 15:31:39 |
| XG95 | sailorren/biohub-xr0-xg95-20260926 | V1 / 352908258 | COMPLETE，输出 PASS | 56573089 | PENDING | UNKNOWN | 2026-09-26 15:32:40 |
| XV25G95 | sailorren/biohub-xr0-xv25g95-20260926 | V1 / 352913254 | COMPLETE，输出 PASS | 56573515 | PENDING | UNKNOWN | 2026-09-26 15:51:48 |

正式最后观测时间：2026-09-26 15:51:59 上海。准确原始状态和时间在 platform_ledger.json 与每候选 formal_last_observed.json。已有 ID 只读查询，不重发。相对 XR0 0.953 的差值尚不可计算。三份正式终态回收后才统一分析；不修改最终选择。

## 冻结定义及检查

原任务 V01/V02 按交付 manifest 验证 2/2 字节数和 SHA256 一致。成功 XR0 V1/SV352643547、submission56546951 的源码已实际读取并确认与冻结母版相同，其正式 Public 为0.953。G1 使用既有 V1/SV349707105 输出中的 final 模型，实际文件 SHA256 与任务要求一致，无重新训练。

三份同时构建，仅包含自身无 flow 分支速度0.25、冻结 G1 0.95 两项因素。原几何、排序和 cap 经 AST 还原一致。保留检测0.965、DeepCenter0.25、head、flow、readmit及原版其余算法。小型检查30项通过；另验证冻结G1真实final模型的有限分数路径。低阈缓存先于head的动态补丁在实际support源码上检查通过。代码冻结 commit：5787a38c114f17f179de6181758c2ef0222c3e28；固定远端关键文件回读26/26通过，详见 github_code_readback.json。

## 已完成实际运行验收

XV25 CSV共238260行，XG95共238236行；根据运行时真实测试集合核对覆盖，逐行复核字段、连续ID、坐标、边端点、相邻时序、唯一父节点、最多两个子节点。两份实际速度消费计数均26，repair_fallback=0、deadline_degraded=0，字段均实际存在。XG95 G1候选67、有限分数67、过滤17；零新增不作为失败条件。CSV仅留临时目录，不上传GitHub。

两份保存Input页逐项确认四个Dataset版本为V10/V2/V5/V1，XG95另挂既有Division Train输出。实际日志确认三主权重哈希、head哈希、离线依赖、双T4推理、head在低阈缓存之后生效及真实CSV写出。XG95实际加载冻结gate SHA和final模型。API回读三份均Private、GPU启用、Internet off、原版docker digest一致。普通输出警告包括依赖弃用、nbconvert转义及Torch JIT内核缓存目录不可写；没有真实推理失败、repair fallback或deadline降级。Torch JIT缓存提示不等同于低阈检测缓存失效。

## 调度与预算

本批完整Save & Run已用3/3，工程备用0/1，正式请求3/3；训练0、Dataset写入0、最终选择修改0。前两份同批启动，普通运行释放槽位后即启动组合，不等待Public。账号sailorren，提交前实时额度5次。GPU API可用总额21600秒与UI30小时口径不同，按较小6小时规划。平台未明确展示最大并发上限，记为UNKNOWN；实测两份同时运行获准，采取两槽调度，未占用其他已有任务。

后续只继续三个准确ID的终态回收，不追加方案或重提。仍有工作未完成，不声明COMPLETED_VERIFIED。

组合候选实际GPU普通运行19分28秒，238236行CSV通过检查，速度消费26，G1候选67/有限67/过滤17，repair_fallback与deadline_degraded均为0。实际输入页版本逐项确认V10/V2/V5/V1及既有Division Train。与XG95的可见CSV相同不作为跳过正式评分的依据，三方案的实际隐藏测试结果仍未知。第三份提交前实时剩余额度3次，正式受理56573515。

阶段Git回执：84c9eefbb4828c0fa5bfba1ba628f00e23c28202 的报告、账本及三个运行/提交回执远端逐字节回读5/5通过；不等于最终评分完成。中途一次GetKernelSessionStatus发生SSL EOF，只读失败已记录，没有新增运行或请求。

最新页面观测（UTC 2026-09-26T08:12:34.891809+00:00）：三个精确描述/Version/SV均为 `Notebook Running`，尚无Public。API查询连接偶发SSL EOF，仅影响只读观察，不产生新运行或提交。固定受理commit `ac61c5ce9212c247c1eab8f52c81b4b7c9984ce8` 关键文件远端逐字节回读11/11通过，见 `github_accepted_readback.json`。

定时只读回收：2026-09-26 17:13:18 上海，三个准确submission均为PENDING，Public均UNKNOWN，direct_error均为空。保持WAITING_FOR_SCORES，不进行方案比较。
