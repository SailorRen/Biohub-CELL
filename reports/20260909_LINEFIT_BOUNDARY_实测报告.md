# LINEFIT_BOUNDARY 单候选实测报告

**尚未取得正式终态成绩；本任务未完成。尚不能判断是否提分。** 本报告的实验状态、成绩比较与 GitHub 交付分别举证。当前记录时间来自下方平台回执，不把普通 COMPLETE、局部测试或 proxy 当正式成绩。

## 冻结对象与授权范围

任务 `LINEFIT_BOUNDARY_20260909`。用户接受上一轮“分裂边界内 linefit”单候选建议，授权实际运行。合同 SHA256：`38ef065b940817d544c3d75de505f955473583a1f9dbf6a7a01019af5fb97bfd`；manifest SHA256：`eb45073c9ab58005c603353d59782b4d6c879b03027c15e27bd91573279cbdda`。

只在 B0 的 linefit 回溯进入前驱前，要求前驱恰有一个后继，阻止跨越分裂父→女儿边。前向逻辑、weight=.8、window=2、模型/权重/输入版本/检测/融合/TTA/ILP/motion/gap/safe-div/短轨和原自动选参器均不变。增加的五项统计不改变预测。13个cell仅cell5的指定函数改变；metadata仅id/title改变。原B0未修改。没有训练、Dataset/Model写入、组合候选、参数搜索或最终选择改动。

| 对象 | Notebook / Version / ScriptVersionId | submission / 状态 / Public |
|---|---|---|
| B0 | sailorren/biohub-946-b0-repro-20260908 / 1 / 348114666 | 56091397 / COMPLETE / 0.946 |
| 候选 | sailorren/biohub-946-linefit-boundary-20260909 / 1 / UNKNOWN | 尚未正式提交 / NOT_RUN / null |

候选 kernel ID：`133664101`。本地 Notebook SHA256：`2476eae2ff6f95d79a18c8a1294e14e10e5309c61ec86872cbc4962687b852a5`；实际SDK序列化写入源码 SHA256：`4271519ed44e28da93e89128fc6e39515f954e96b8c2d0a9b102c23f3e08f11b`。Kaggle返回JSON排版可能不同，平台字节hash与13cell源hash另存 read 快照及 remote_binding；不混淆文件hash与wire hash。

正式相对B0变化：`UNKNOWN`；相对提交前自有最好成绩 `0.946` 的变化：`UNKNOWN`。基线当前读取状态来自本轮官方 submissions API 的 submission56091397，并与浏览器 Version1/SV348114666描述核对，不使用历史标题分数。

## 实际执行与测试

- linefit 合成测试：20/20 PASS，实际执行提取的原函数与候选函数；直/弯无分叉轨道逐字节等同B0、父女儿两侧隔离、旧B0跨边界敏感性正对照、起终点/孤立/非连续边/禁用、拓扑与非坐标字段保持、观测纯度和物理单位。
- 独立候选/写入审阅：24/24 PASS，包含实际无网络mock验证。不明写结果退出3，账本落盘后禁止第二次写；只读TLS每层最多3次、嵌套最坏9次，写传输重试0且send上限1。
- 官方评分诊断：6合成场景、2图完整聚合、83/83断言 PASS。官方075fc5与B0旧proxy在弱连通单分支、一fork服务多个GT等场景实际出现差异；正常分裂对照一致。它不替换候选的原自动选参器，也不构成真实提分证据。
- 没有取得同一份生产预测图与GT：`NO_SAME_PREDICTION_GRAPHS`。真实PP排名是否改变仍UNKNOWN。诊断隔离环境NumPy/SciPy与Kaggle不同，GEFF CLI I/O未运行；完整实际评分/聚合函数已执行。详见 scorer_diagnostic.json/.md。

唯一保存请求时间为上海 2026-09-09 10:32:38。响应返回 Version1/kernel133664101、空error与空invalid_sources，但相对`/code/`地址触发本地严格ref保护。随后只读 GetKernel核实目标ref、kernelID、Version及13cell源码完全相同，浏览器显示 GPU T4×2运行。没有重复保存或创建修复版本；原不明状态与回读回执均保留。

实际保存请求 `1/1`，正式 submission请求 `0/1`。任何写入不确定均先只读核验，不自动重发。

## 普通运行与正式结果分离

普通最近状态：`RUNNING`，读取时间UTC `2026-09-09T02:38:12.036345+00:00`；输出验收：`False`。

普通自动后处理选择：`UNKNOWN`，完整实际配置保存在 ordinary_summary.json（取得后）。正式隐藏运行的后处理选择、分项及Private Score仍为UNKNOWN，不能从普通输出推断。

普通边界命中节点数：`UNKNOWN`；其中实际平滑：`UNKNOWN`；候选相对输入坐标位移总和/最大值：`UNKNOWN` / `UNKNOWN` µm。边界命中不等于最终坐标改变，此位移也不是与B0预测的差值。

正式状态：`NOT_RUN`；读取时间UTC：`UNKNOWN`；正式错误说明：``。只有准确绑定的submission为COMPLETE且有数值Public才判断收益；持平/下降也如实交付，不追加实验。

## GitHub交付

所有本轮代码、配置、哈希、合成测试、评分诊断、平台小型回执和本报告同步 SailorRen/Biohub-CELL。原始源码下载、依赖环境与完整日志留ignored downloads，未提交比赛数据、模型权重或submission.csv。

内容提交与最终回执提交的固定SHA、逐文件远端回读以 delivery_receipt.json及最终交付输出为准。当前文件本身不自证远端完成。冻结合同要求实际正式终态成绩、验收通过、干净Git与GitHub权威远端回读；评分未结束时只记录实际状态，不承诺后台完成。
