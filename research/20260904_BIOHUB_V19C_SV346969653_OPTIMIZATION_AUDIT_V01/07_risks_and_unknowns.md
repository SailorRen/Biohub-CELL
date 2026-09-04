# 风险、证据缺口与停止边界

## 版本与血缘

- `UNKNOWN`：Kaggle SDK 没有在成功响应中返回独立 `script_version_id` 字段；版本参数读取 HTTP 404。本轮用精确页面的三个 `346969653` 指针与 current Version 1 fail-closed guard 绑定。
- `UNKNOWN`：API `kernel_sources=[]`；页面只显示来自未命名 private notebook；Notebook Markdown 又同时自述 public fork 和 standalone，平台 parent identity 未闭合。
- `UNKNOWN`：目标 Notebook 与外部权重/支持代码的可再分发许可证未全部暴露，所以不提交完整 source 或权重。
- GetKernel、kernels list 与页面的运行时间字段不一致，不能用单一时间戳替代 version/source/submission identity。

## 指标与验证

- 四样本 validator 是 division-enriched 选择，不是冻结的全量 embryo-disjoint CV；其 0.9414 未执行独立复核，不能等价为 public score。
- `estimated_number_of_nodes` 是真实节点总数估计；spurious node 分解还受稀疏标注和匹配半径影响，不能直接按普通检测 FP 解读。
- division 只有 1 TP、0 FP、4 FN，样本量过小；放宽阈值可能快速增加 FP，必须看多折 micro-average 与总分。
- 公开测试占位样本、隐藏 test 和训练样本的域不同；在四个当前 test 视频上做自适应规则有过拟合风险。
- 比赛此前有 division metric 补丁与重算历史；任何旧页面 Best Score 或作者文字都不能替代当前 submission/version 绑定。

## 配置与实现

- Markdown 描述 parent 9、divergence 4.5，而 source 和 resolved runtime 为 parent 7、divergence 2.25；普通打印还有 reverse 0.200 对 active 0.15。
- guard report 多个参数陈旧，并明确 `candidate_unverified`；若不先建立 canonical resolved receipt，后续 A/B 可能比较了错误配置。
- Notebook 通过字符串替换动态 patch 支持代码。它可运行但提高了审计复杂度，字符串锚点漂移可能产生静默版本风险。
- motion relink、gap、DeepCenter、division 和短轨迹处理高度耦合；一次改变多个参数将失去因果归因。
- 三份 checkpoint 只有运行字节哈希；训练数据、训练配置、授权和可复现性仍为 `UNKNOWN`。

## 运行与平台

- 本轮生产 inference 8.85 分钟、总 runtime 约 31 分 45 秒，不证明 hidden test 或新实验仍在同一预算内。
- 读取快照时另一个不同 Notebook 的 submission `56002593` 为 PENDING；本任务没有继续轮询。后续成绩变化不会自动更新本报告。
- Public 0.939 是时间点观察值和具体 submission 记录，不是 private/final 分数，也不是保证未来重评分不变。

## 本轮未执行

所有候选状态均为 `CANDIDATE_NOT_EXECUTED`。本轮未执行训练、推理重跑、参数搜索、Kaggle Notebook Version 写入、submission 创建/retry/选择、Dataset/Model 创建、规则接受、比赛数据下载、权重下载或大型输出下载。

## 全局停止条件

未来实验若获单独授权，出现下列任一情况即停止晋升：身份/权重/source hash 不一致；split 泄漏或 scorer hash 漂移；不是单变量差异；任一 embryo prefix 明显退化；division FP、wrong association、node-count penalty 或 topology violation 上升而总分没有稳定补偿；运行超预算；缺少 canonical receipt；仅有单次 Public LB 波动而无离线证据；或 Kaggle 写入预算、submission identity、重复提交门未冻结。
