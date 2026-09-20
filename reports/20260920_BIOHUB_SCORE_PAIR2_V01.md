# BIOHUB_SCORE_PAIR2_20260920_V01

状态：task_delivery=PENDING；execution=BUILT_NOT_RUN；score=NOT_SUBMITTED。

S50 仅主动修改 G1 第二模型检测融合 0.80→0.50，保留原选择器；下游选择可能随检测变化。G58 仅在原选择后覆盖最终 GAP_CLOSE_UM 为5.8，原始图重新后处理，DeepCenter 分裂门槛仍0.20。附加代码仅记录实际 worker 参数和最终生产输出，没有独立诊断。

固定任务93d12fa；母版e9c7c63；复用850fafe。完整原文、输入/权重哈希、预算与停止条件在唯一冻结 batch_manifest.json。全部代码单元解析通过，4项改动路径短测试通过。一次 py_compile 因 macOS 外部缓存目录权限失败，随后使用不落缓存的 AST 解析成功；不是生产失败，不消耗平台预算。

开始时账号 sailorren、比赛136605，每日已用3/5，API按UTC日期计数，当前读取接口未暴露确切每日重置时刻。GPU已登录UI20h38m/30h，活跃作业0。SDK GPU总量6h与UI不一致，保留两侧观测。跨上海午夜不扩张本批2次正式请求预算。

未改原用户工作区、main、G1/F1、A18/B22、最终选择。现有四个正式Public均0.948，不推断严格同分关系或Private。下一步：源码远端回读后各一次Save & Run，完成者独立进入实际CSV检查和正式提交。
