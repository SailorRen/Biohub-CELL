# 交给 Chat：Biohub 最新公开情报

截至 **2026-09-18 14:37:51（UTC+8，平台观察结束上界）**。本轮状态 **PARTIAL_RESEARCH_BLOCKED**：两份入围Notebook全部单元已读并合法保存，support V10必要脚本已补齐；仍缺N01依赖许可/版本绑定、部分独立配置及官方更正源码的实时核查。没有新正式评分，没有证明任何新Public提升。

主体固定提交：**267dcb04bdab7a730fa2cceef7d3fb86bef1351a**，研究分支 `codex/public-intel-20260918`。先读以下固定文件，不依赖Codex本地路径或旧对话：

- [完整调研报告](https://github.com/SailorRen/Biohub-CELL/blob/267dcb04bdab7a730fa2cceef7d3fb86bef1351a/reports/20260918_BIOHUB最新公开情报.md)
- [来源索引、逐单元分析与G01–G07缺口](https://github.com/SailorRen/Biohub-CELL/blob/267dcb04bdab7a730fa2cceef7d3fb86bef1351a/research/PUBLIC_INTEL_20260918/sources.json)
- [逐评论语义摘要、时间与图片覆盖](https://github.com/SailorRen/Biohub-CELL/blob/267dcb04bdab7a730fa2cceef7d3fb86bef1351a/research/PUBLIC_INTEL_20260918/讨论逐条阅读.json)
- [准确版本与分数冲突](https://github.com/SailorRen/Biohub-CELL/blob/267dcb04bdab7a730fa2cceef7d3fb86bef1351a/research/PUBLIC_INTEL_20260918/准确分数核对.json)
- [列表筛查和排除理由](https://github.com/SailorRen/Biohub-CELL/blob/267dcb04bdab7a730fa2cceef7d3fb86bef1351a/research/PUBLIC_INTEL_20260918/列表筛查.json)
- [当前官方页面与排行榜前20/本队附近](https://github.com/SailorRen/Biohub-CELL/blob/267dcb04bdab7a730fa2cceef7d3fb86bef1351a/research/PUBLIC_INTEL_20260918/官方页面与排行榜.json)

## 三条最重要信息

1. **新代码不等于新成绩。** 9/18的flow2 det096 V1/SV350702651新增邻域中位运动补偿，已读12/12单元；无可见Public。同时改变det=.96等参数，并存在旧审计字段与实际配置不一致。可以拆成单改动候选，不能宣称强于G1。
2. **两个“高分”线索被准确详情纠正。** `anvithpothula/biohub-0-95`的V1/SV337000331实际Public **.877**，列表曾.950；`haideptry/...density-adaptive...`的V1/SV350463514实际 **.945**，标题却是“0.948+”。本次范围内未找到准确绑定且源码/依赖齐全、高于G1 .948的公开生产版本；不是全站不存在声明。
3. **新讨论主要增加反证和未解问题。** D02作者自述更大模型/更长训练/长窗没有稳定转成LB收益，条件融合与合成预训较有希望，但无版本回执；D03外部胚胎独立性仍待主办方确认；D04新公私榜统计没有tracking任务。都不能替代本项目独立验证。

## 完整阅读清单：不同层次分别标明

|来源|Notebook本体|自定义依赖|准确分数|Chat可回读源码/缺口|
|---|---|---|---|---|
|N01 hengck23 end2end V3/SV350162298，9/16 05:47|5/5，零基0–4；原文件本轮重新取得并匹配旧hash|model_v12页面全文已读；support V10 io/metrics等已读，但未与N01实际挂载版本独立绑定|无Public；作者11样本raw edge宏平均约.895998，非官方综合分|[5个完整原单元](https://github.com/SailorRen/Biohub-CELL/blob/267dcb04bdab7a730fa2cceef7d3fb86bef1351a/research/PUBLIC_INTEL_20260918/sources/N01/source_cells.json)。model_v12 DatasetV2许可Unknown，不镜像，Chat完整依赖仍未交齐|
|N02 thtennant flow2 det096 V1/SV350702651，9/18 09:24|12/12，零基0–11|support V10的13脚本、4,090行全部已读并hash匹配；secondaryV2、DeepCenterV5输入已绑定|无Public；15m21s为可见4样例ordinary运行|[12个完整原单元](https://github.com/SailorRen/Biohub-CELL/blob/267dcb04bdab7a730fa2cceef7d3fb86bef1351a/research/PUBLIC_INTEL_20260918/sources/N02/source_cells.json)；[13个依赖脚本](https://github.com/SailorRen/Biohub-CELL/tree/267dcb04bdab7a730fa2cceef7d3fb86bef1351a/research/PUBLIC_INTEL_20260918/dependencies/support_v10)。独立config/权重内配置与训练谱系未全部取齐|

source_cells保留原始source字段、Markdown及零基索引；去除输出和metadata，原件/副本hash分开记录。两份Notebook许可Apache-2.0；support Data Card CC0，原脚本字节与注释保留。未下载权重，不把作者日志中的哈希称为本轮实测权重哈希。

13个已读依赖：scripts/{augmentations.py,dataspec.py,evaluate.py,predict_unet_transformer.py,train_unet_transformer.py}；src/biohub_tracking/{__init__.py,division_metrics.py,img_proc.py,io.py,metrics.py}；models/{__init__.py,simple_node_transformer.py,temporal_unet.py}。逐文件行数与hash见 [依赖来源清单](https://github.com/SailorRen/Biohub-CELL/blob/267dcb04bdab7a730fa2cceef7d3fb86bef1351a/research/PUBLIC_INTEL_20260918/dependencies/support_v10/来源与许可.json)。全部是静态阅读，未执行训练模块。

|讨论|主帖|页面计数→实际唯一回复块|关键图片/更正|
|---|---|---|---|
|D01 741868 / Dashboards|已读|0→0|3D可视化图已看；无效果量|
|D02 741749 / 模型平台期|已读|1→1|无关键图；追问基线未答|
|D03 741386 / 外部zebrafish|已读|3→3|无关键图；参赛者判断不是主办方授权|
|D04 735352 / shakeup|已读|11（列表12）→12|新13场表与旧.940原图已看；缺版本绑定|
|D05 740145 / magic or overfitting|已读|9+1感谢（列表12）→12|关键定位/FP/域偏移/轨迹/候选图已看，小字未全转录；保留过拟合质疑|
|D06 736937 / 排名刷新|已读|1→1|社区反馈，不是官方公告|
|D07 741242 / 节省75min|已读|0→0|计时表、配置片段已读；validator未评价HOCT|
|D08 740573 / 分裂步长|已读|4（列表8）→8|外观及回溯建议图已看；保留稀疏标注、定位误差、单位更正|

合计8篇、37条；未见遗留折叠加载控件。计数混合顶层/嵌套或缓存，因此不机械称100%。评论按顺序、作者和准确时间定位；Unknown许可的全文和原图不公开镜像。浏览器全文导出不支持，完整本地讨论快照未全部形成；工具中读过不等于Chat有原文副本。

## 对现有方案的约束与下一步

G1 submission56270217/V1/SV350197436/Public.948是既有归档；本轮动态队伍榜148/.948不重新证明同一submission。H1固定诊断虽然平均proxy改善，但删除3条TP，保持DIAGNOSTIC_REJECT；三边恢复oracle用标注，不能部署；H2仅草案。不要混淆G1原选择器与诊断tight55。

N01的top1消解冲突最多一源一子，不能产生分裂；20帧chunk并非长窗联合链接。其“无Kaggle标签训练”仍缺完整权重谱系，现成Notebook又require_tracks读取训练真值做评价，不能直接作为隐藏测试生产包装。

最多三个候选建议，均未执行：零训练的单独邻域运动模块；零训练的推理可计算TP保护门；需训练且先补许可/谱系的定位精修+稠密伪标注路线。具体失败模式、成本UNKNOWN与最小改动见主报告。没有承诺提分区间。

列表仅有限筛查：讨论两排序第一页；Code Hotness20、PublicScore20、Created60，部分过滤未闭合，Created不等于最近更新。未入围FOCUS49回复/合成数据等不能称读完。当前Overview限制12h/互联网关闭与9/30 07:59截止已读，官方评价源码最新commit/公告变更尚未闭合。

## 交付核验与停止

主体本地检查已通过单元原文一致性、13脚本哈希、索引计数、定向敏感模式与本地引用检查。[检查记录](https://github.com/SailorRen/Biohub-CELL/blob/267dcb04bdab7a730fa2cceef7d3fb86bef1351a/research/PUBLIC_INTEL_20260918/本地交付检查.json)。原依赖img_proc.py含尾部空白行；为保持上游哈希未格式化，不把该whitespace提示写成算法失败或无警告PASS。

最终推送后的权威远端逐文件字节比较另存回执；回执不自引自己的hash。无新Public，无运行复现。训练、模型推断、图修改实验、H2、Save & Run、Notebook创建/复制、Dataset写入、formal submission、最终选择修改、评论/点赞、自动监控全部0。交付后停止，由Chat依据证据再讨论实验建议。


后续更新：[2026-09-20公开情报增量](../research/PUBLIC_INTEL_20260918/update_20260920/最新公开情报.md)，保留本报告历史结论。
