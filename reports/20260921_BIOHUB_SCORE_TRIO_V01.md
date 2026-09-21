# BIOHUB_SCORE_TRIO_20260921_V01

同批续执行，流程以固定 7ef58d77f7654648684616d653252f4aa688ccb1 的精简指令为准；算法及输入按固定 2f1ac2572a7849a7ac7685d0d0f820dff9e079ad 原任务。task_delivery=SOURCE_BYTES_VERIFIED（最新回执同步范围见 github_readback.json）；execution=ORDINARY_PAIR_COMPLETE_H30_NOT_STARTED；score=NOT_SUBMITTED。任务尚未整体完成。

G1 固定母版 e9c7c63b896812660a78ec55fc3284c10f85e776，Notebook SHA-256 de010e6ba142be0e01000093e061ef7d3388ddaa411185b40d26c63a3febe731。工具复用 d1fa52dd66f598bb85be8ca60d7891a3cf049017，输入、三份推理权重及 G1 gate 权重未变。三臂源码已构建；5 项改动路径 CPU 短测试通过，所有代码单元解析通过。未启动独立诊断、训练或重复母版推理。

|候选|唯一主动干预|版本 / SV|submission|原始 Public|状态|
|---|---|---|---|---|---|
|G1|既有母版|V1 / 350197436|56270217|0.948|COMPLETE|
|S50|仅只读|V1 / 351350449|56407778|null|SCORE_PENDING|
|G58|仅只读|V1 / 351350591|56407804|null|SCORE_PENDING|
|D960|检测阈值 0.965→0.960|V1 / 351441983|null|null|普通 COMPLETE；NOT_SUBMITTED|
|R00|最终短轨救援启动比例 0.10→0.00|V1 / 351442164|null|null|普通 COMPLETE；NOT_SUBMITTED|
|H30|反向关联 harmonic 权重 0.15→0.30|null|null|null|NOT_STARTED；NOT_SUBMITTED|

首次平台对账时间 UTC 2026-09-21 01:41:49（上海09:41:49），已枚举93个自有 Notebook，无三个指定slug，也无其正式提交。当前UTC日已用0/5，不将上海午夜当重置依据；GPU UI可用16h19m/30h，SDK totalTimeAllowed=6h 与UI不一致，保留原始小型记录。两项活跃事件均为 S50/G58 正式评分，普通运行0。ListSubmissions 首次传返回的 competition.ref 得到403，纠正为固定比赛slug后成功；未产生写请求。

唯一冻结记录 batch_manifest.json，唯一请求账本 platform_ledger.json。累计 Notebook 2/3、Save & Run 2/4（共享修复未用）、正式 submission 0/3且每臂最多1。训练、Dataset、最终选择、已有Notebook修改或取消为0。保留的两个额外提交名额未动用。

必要实现：D960 精确更新初始化赋值及对应守卫，worker记录其实际检测阈值；H30 更新两处守卫并在实际 harmonic 使用点记录消费权重，公式、校准和TTA保持；R00 在原选择后直接设置消费全局值，原始预测图重新后处理，保留质量筛选和逐调用预算，记录实际救援决策。每个候选只继承原选择算法，不新增选项。附加回执不冒充正式分数。

## 本次实际请求与续接

冻结源码提交 1cf89f1f9380f005d98e9cb15ca9f5d80c4ebaca，启动前29文件远端逐字节回读一致（source_github_readback.json）。三臂候选源码、runtime、build、manifest 此后未变；只修复本地续接脚本对后续账本提交的识别，继续复用已回读的冻结源码，不重复启动或冻结。

- D960：Kernel 135169669；上海09:49:20发送唯一 Save & Run，V1 / SV351441983，平台完整代码单元与冻结源码一致、私有、GPU T4×2、Internet关闭。上海12:03:48只读回读为 COMPLETE。
- R00：Kernel 135169776；上海09:50:28发送唯一 Save & Run，V1 / SV351442164，同样完成身份及源码回读，上海12:03:50只读回读为 COMPLETE。
- H30：构建和短测试已完成，尚无平台对象和请求。首次执行结束时两个普通 GPU 作业均在运行，沿用既有启动器两作业门禁等待槽位；未用额外请求探测超限。此等待状态不是平台拒绝回执，也不表示 GPU 时数耗尽。对公开并发说明的网页读取未返回正文，不以搜索摘要作为当前账号硬上限的独立证明。

普通状态的精确观测时间见各臂 platform_latest.json；S50/G58 的只读查分时间为上海2026-09-21 12:03:52，API原始Public均为空字符串，归一化为null，正式状态PENDING。G1仍为COMPLETE / 原始字符串0.948。未修改已有作业或最终选择。

后续先读取本账本和平台状态，D960/R00禁止重复launch_once。任何一臂普通 COMPLETE 后立即执行 collect_outputs.py、check_outputs.py（已有scorer Python环境），复核实际CSV和官方reader往返；真实差异且非重复者依原授权执行 submit_once.py 一次，不等其他Public。新复核证据按需同步，源码不变时复用原回读commit。H30槽位允许时使用既有冻结源码启动。一个候选故障不阻塞其他。

实际CSV尚未下载及独立复核，正式请求尚未发送，均不得写成SCORE_PENDING。没有建立后台定时器或声称会话结束后继续自动执行。下次续接直接执行未完成步骤，不重复要求授权。

## 2026-09-21 12:03:52 上海时间只读结果更新

D960、R00 的精确 V1 普通运行均为 COMPLETE，完整代码单元仍与冻结源码一致。正式列表中没有三臂 submission；两臂仍为 NOT_SUBMITTED / Public=null，实际 CSV 复核为 NOT_RUN。H30 账本无启动请求；此前两项普通运行已结束，本次未探测剩余额度或启动 H30。

S50（56407778 / SV351350449）、G58（56407804 / SV351350591）API均为PENDING，原始Public为空字符串，归一化null；登录态比赛页面同时显示Notebook Running。本次未发送任何平台写请求，累计预算不变。更新仅记录已观测结果，不代表整个续执行任务完成。
