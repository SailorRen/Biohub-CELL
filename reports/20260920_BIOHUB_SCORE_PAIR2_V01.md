# BIOHUB_SCORE_PAIR2_20260920_V01

状态：task_delivery=SOURCE_BYTES_VERIFIED；execution=KERNEL_RUNNING；score=NOT_SUBMITTED。正式 submission ID 和 Public 均为 null。

S50 仅主动修改 G1 第二模型检测融合 0.80→0.50，保留原选择器；下游选择可能随检测变化。G58 仅在原选择后覆盖最终 GAP_CLOSE_UM 为5.8，原始图重新后处理，DeepCenter 分裂门槛仍0.20。附加代码仅记录实际 worker 参数和最终生产输出，没有独立诊断。

固定任务93d12fa；母版e9c7c63；复用850fafe。完整原文、输入/权重哈希、预算与停止条件在唯一冻结 batch_manifest.json。全部代码单元解析通过，4项改动路径短测试通过。一次 py_compile 因 macOS 外部缓存目录权限失败，随后使用不落缓存的 AST 解析成功；不是生产失败，不消耗平台预算。

开始时账号 sailorren、比赛136605，每日已用3/5，API按UTC日期计数，当前读取接口未暴露确切每日重置时刻。GPU已登录UI20h38m/30h，活跃作业0。SDK GPU总量6h与UI不一致，保留两侧观测。跨上海午夜不扩张本批2次正式请求预算。

未改原用户工作区、main、G1/F1、A18/B22、最终选择。现有四个正式Public均0.948，不推断严格同分关系或Private。两臂已经启动，不再重复 Save & Run。

## 已启动的精确身份

|候选|Kernel|Version|ScriptVersionId|启动上海时间|正式ID|Public|
|---|---:|---:|---:|---|---|---|
|S50|135123707|1|351350449|2026-09-20 23:45:56|null|null|
|G58|135123769|1|351350591|2026-09-20 23:46:38|null|null|

两份源码与唯一冻结记录在 e8f7d0396cd7aa2af647594bad5367935cc76cec 推送并完成21文件逐字节回读后启动。随后平台回读确认私有、V1、GPU T4×2、完整代码单元一致；SV 来自页面实际 Edit run 链接，未打开编辑器。累计 Notebook 2/2、Save & Run 2/3、正式 submission 0/2；其他预算为0。

## 直接续接边界

用户已要求暂停观察，待其通知流程结束后再续接。暂停自动查状态和正式提交，不取消平台运行。最后已取得的观测：S50 为上海时间 2026-09-21 00:14:52，G58 为 00:14:54，两者均 RUNNING；此后状态未知。正式提交均 NOT_SUBMITTED，ID 与 Public 均 null。以下续接步骤仅在用户通知后执行。

不得重新运行 launch_once.py。先 read_pair.py 与平台提交列表对账；任一臂 COMPLETE 即执行 collect_outputs.py <arm>，再用已有 scorer 环境执行 check_outputs.py <arm> 独立 CPU 解析和官方 CSV 往返。S50 可引用上一批已验证 G1 输出，但输入字节同源未经重新证明时保留因果比较限制；G58 使用同次原选参 G1 输出比较。不等待另一臂 Public。

通过后同步必要代码和输出复核，回读为 formal_code_readback.json；实时核查账号、额度、并发、既有提交后，submit_once.py <arm> 仅发一次正式请求。请求先 fsync 记账；响应不明只能只读对账。read_formal_status.py 保存原始分数字符串。本批累计正式请求上限2，跨本地午夜不重置。

普通运行尚未结束，实际最终输出复核与正式提交尚未执行。冻结 execution 验收仍须通过；源代码交付和运行受理均不表示整体完成。
