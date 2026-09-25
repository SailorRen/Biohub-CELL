# XR0 / XD960 正式评分任务阶段结果

状态：`READY_FOR_TEAMMATE_RUN`。母版2/2；完整GPU运行0/2；合法输出验收0/2；正式提交0/2；Public结果0/2。**最终评分目标尚未完成**。

## 已核验证据

- 干净隔离 worktree，指定分支 `codex/x138-score-pair-20260925` 从开发基点6205f21建立；未改原工作区、A/025、旧X0/X25或最终选择。
- 原ipynb SHA256与用户指定一致。XR0的12个有效代码单元逐字节保留；XD960只改Cell1主检测阈值与Cell2对应守卫到0.960，READMIT_MIN_SCORE=0.965、velocity=0.5。
- 本地41项检查PASS：nbformat、12单元AST、8个完整嵌入脚本、参数顺序、允许diff，以及在从旧实际普通输出回收且hash匹配support预期的源码上应用动态补丁。低阈缓存先head。此结果不是模型载入、真实推理或云端兼容性证明。
- 冻结源码commit `8bf74286f48e0aec40e08efbdda86e387f210425`，GitHub固定SHA回读23/23字节一致，之后才执行平台创建。首次回读因中文路径quotePath导致404，修正读取路径方式后成功，非一次无错误尝试。
- 两份实际保存源码与冻结candidate.ipynb全部单元内容一致；Private / enableGpu=true / NvidiaTeslaT4 / Internet=false。UI四数据集明确pin到10/2/5/1；kernel_sources未添加。

| 候选 | Kernel / owner | 母版 Version / SV | 模板 | 完整GPU / 输出 | submission / Public |
|---|---|---|---|---|---|
| [XR0](https://www.kaggle.com/code/sailorren/biohub-x138-xr0-score-20260925?scriptVersionId=352619216) | 135784801 / sailorren | V1 / 352619216 | 已保存、dongdongjiaqi Viewer | NOT_RUN / NOT_VERIFIED | 无 / 无 |
| [XD960](https://www.kaggle.com/code/sailorren/biohub-x138-xd960-score-20260925?scriptVersionId=352620382) | 135785956 / sailorren | V1 / 352620382 | 已保存、dongdongjiaqi Viewer | NOT_RUN / NOT_VERIFIED | 无 / 无 |

两次都是Quick Save。平台显示约10秒Successful仅是模板保存处理；没有submission.csv，提交入口也显示无所需输出，不能当普通GPU运行或可评分验收通过。

## 旧V2排查及部署差异

X0 V2 SV352574161 / submission56539500：实际普通日志80.2s、Accelerator=None、API GPU=false，Cell5直接报CUDA GPU required。此前离线依赖和三个主权重哈希通过。新母版实际GPU=true，具有可检验的部署差异，非仅改名重提。隐藏正式traceback仍UNKNOWN，不归因velocity。

X25 V2 SV352574469 / submission56539537正式ERROR；历史V2 API源码不可访问。最新V3 SV352576552 / submission56539761普通同CUDA错误，但不以V3代证V2。X0 V2、X25 V3完整源码与旧模板一致。详见排查记录及普通日志。

新母版仍实际使用镜像 `gcr.io/kaggle-images/python@sha256:dafd4ce5668bbf1ad422e4c109e0f18c9623c3a7c7f48b0235f13142755c40b9`。UI已选择Pin to original environment但未得到用户指定37c64f镜像；不能声称完全同环境。新镜像完整离线推理兼容性NOT_VERIFIED，需并入队友首个XR0完整运行。

head固定V1只读下载遇TLS EOF，没有降低TLS保护。本批实际挂载head哈希、3权重断言通过、head/缓存模型载入与运行、生效参数、真实CSV、repair_fallback及deadline_degraded均待运行核查，不能用静态PASS替代。

## 实时限制与下一步

2026-09-25上海约15:49：官方提交弹窗明确今日剩余1次、约16小时重置。四条今日旧失败已计账，不退账；新任务提交消耗为0。用户确认队友GPU充足，独立余额UNKNOWN。截止上海2026-09-30 07:59，GPU Notebook上限12小时，Internet关闭、submission.csv为必需。

已向用户交接两份真实链接，请当前同队dongdongjiaqi本人运行并回传副本Version/SV。先XR0验证共同部署，再立即XD960；用户要求同批提交、不等待首份正式分数。当前额度不足两份，需在正式动作时重新核对；若仍不足优先XR0，不自动跨周期提交。

当前没有可供验收的队友运行、输出或正式回执，因此不得声称评分完成或提分。历史D960显示0.948与G1持平；XD960在x138上的收益UNKNOWN。详见实验目录的队友交接、platform_ledger、execution_status、platform_template_readback及GitHub回读。
