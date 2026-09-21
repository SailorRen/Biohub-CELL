# BIOHUB_SCORE_TRIO_20260921_V01

同批续执行，流程以固定 7ef58d77f7654648684616d653252f4aa688ccb1 的精简指令为准；算法及输入按固定 2f1ac2572a7849a7ac7685d0d0f820dff9e079ad 原任务。task_delivery=SOURCE_FREEZE_PENDING；execution=NOT_STARTED；score=NOT_SUBMITTED。

G1 固定母版 e9c7c63b896812660a78ec55fc3284c10f85e776，Notebook SHA-256 de010e6ba142be0e01000093e061ef7d3388ddaa411185b40d26c63a3febe731。工具复用 d1fa52dd66f598bb85be8ca60d7891a3cf049017，输入、三份推理权重及 G1 gate 权重未变。三臂源码已构建；5 项改动路径 CPU 短测试通过，所有代码单元解析通过。未启动独立诊断、训练或重复母版推理。

|候选|唯一主动干预|版本 / SV|submission|原始 Public|状态|
|---|---|---|---|---|---|
|G1|既有母版|V1 / 350197436|56270217|0.948|COMPLETE|
|S50|仅只读|V1 / 351350449|56407778|null|SCORE_PENDING|
|G58|仅只读|V1 / 351350591|56407804|null|SCORE_PENDING|
|D960|检测阈值 0.965→0.960|null|null|null|NOT_SUBMITTED|
|R00|最终短轨救援启动比例 0.10→0.00|null|null|null|NOT_SUBMITTED|
|H30|反向关联 harmonic 权重 0.15→0.30|null|null|null|NOT_SUBMITTED|

首次平台对账时间 UTC 2026-09-21 01:41:49（上海09:41:49），已枚举93个自有 Notebook，无三个指定slug，也无其正式提交。当前UTC日已用0/5，不将上海午夜当重置依据；GPU UI可用16h19m/30h，SDK totalTimeAllowed=6h 与UI不一致，保留原始小型记录。两项活跃事件均为 S50/G58 正式评分，普通运行0。ListSubmissions 首次传返回的 competition.ref 得到403，纠正为固定比赛slug后成功；未产生写请求。

唯一冻结记录 batch_manifest.json，唯一请求账本 platform_ledger.json。累计上限 Notebook3、Save & Run4（含1次共享修复）、正式3且每臂1；当前实耗均0。训练、Dataset、最终选择、已有Notebook修改或取消为0。

必要实现：D960 精确更新初始化赋值及对应守卫，worker记录其实际检测阈值；H30 更新两处守卫并在实际 harmonic 使用点记录消费权重，公式、校准和TTA保持；R00 在原选择后直接设置消费全局值，原始预测图重新后处理，保留质量筛选和逐调用预算，记录实际救援决策。每个候选只继承原选择算法，不新增选项。附加回执不冒充正式分数。

下一步按 D960、R00、H30 优先级使用可用槽位。普通 COMPLETE 后立即收集实际CSV、官方reader往返和图合法性检查，真实差异且非重复者正式提交；一个候选故障不阻塞其他。无实时输出前不宣称复核通过。不建立后台定时器。
