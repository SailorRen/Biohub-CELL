# PUBLIC946 TTA 实测报告

当前为执行中记录，尚未取得本批正式成绩；不能判断提分。最终交付前以统一 `results.json` 和实际平台回读更新。

任务：PUBLIC946_TTA_20260908。任务提交 `a0e63708a60d72e2eab907c03a8cb9c47abe378a`，研究提交 `bf0cda3012f9885587c0ee0da0af348d0ab11c8b`。已安全快进 main，开始时工作树干净，既有实验未改。

## 正式结果

| 对象 | Notebook | Version / ScriptVersionId | 普通运行 | submission / 正式状态 | Public Score | 相对 B0 | 相对启动时自有最好 | 相对公开 0.946 | 实际 PP |
|---|---|---|---|---|---|---|---|---|---|
| B0 | sailorren/biohub-946-b0-repro-20260908 | 1 / 348114666 | RUNNING | 无 / NOT_REQUESTED | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| C1 | sailorren/biohub-946-c1-xy8-20260908 | NOT_RUN | NOT_RUN | 无 / NOT_REQUESTED | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| C2 | sailorren/biohub-946-c2-secondary-edge-tta-20260908 | NOT_RUN | NOT_RUN | 无 / NOT_REQUESTED | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

启动时可核实的自有最好正式分为 0.942（V21A，submission 56069192，Version 1 / SV 347862850）。用户已有 Harmonic submission 56087974 当时 PENDING，不属于本批。公开 0.946 仅是参考，不能预填为 B0 得分。普通 COMPLETE、合成 PASS、proxy 和 ACTIVE 日志均不作为正式成绩。

## 来源、改动与实际测试

开发母版为 [redoctopusk/biohub-942tta Version 1](https://www.kaggle.com/code/redoctopusk/biohub-942tta?scriptVersionId=347821442)，ScriptVersionId 347821442。实际取得完整 12 个代码单元并核验全部源码，实时下载与固定母版字节一致，SHA256 `521cb97f0f457643379a51b60c4f71e3f4cc7d1823fd98cbb97633ffaa515ec4`。母版 Input 页面确认 DeepCenter / 次模型 / 支持包版本分别为 5 / 2 / 10，三个候选 metadata 固定同一输入、Docker、GPU 和 offline 设置。

B0 展开算法与原版逐字相同。C1 仅 5 处输入/逆变换白名单修改，把重复 XY 视角替换为反对角线；两模型检测与主模型特征同步逆变换，次模型关联仍用原图单视角特征。C2 独立来自 B0，保留原八 pass/七唯一视角，只把次模型已有编码逆变换、逐视角累加并平均，均值交给现有关联路径。无额外 encoder、融合权重或参数变化，无 C1+C2 组合。

原 12 单元去除共同审计注入后逐字恢复，原八 FOV、七单候选和条件组合、自动选参与最后重写完整保留。没有把作者选中的 5.5 写死。新增相同的最终审计单元，在全部选参和重写后只读读取最后 CSV 与真实配置；前序 hash 和陈旧参数只作历史记录。

CPU 合成测试实际执行通过：30 组视角/布局测试覆盖非方形 3×5、方形 5×5、多维及不同分辨率特征；B0/C2 八 pass 七唯一，C1 八唯一；真实展开 predictor 和支持库 encode、采样、edge-head 调用链使用小型测试模型执行，C2 每模型八次编码，检测/主模型结果与 B0 一致，平均特征实际被次模型关联消费。开启和关闭共同审计时生产张量逐元素相同，RNG 不变。共同最终 CSV 检查的 16 个正反例及整个最终 hook 合成执行均 PASS。以上是 MEASURED CPU 合成结论，真实权重 GPU smoke 由云端运行回收。

公共审计每视频只在前三窗内首次有可用关联时增加一次只读 edge-head 诊断，新增 encoder 为零；不改变生产输出。局部数值差异不能说明预测质量，特殊输入零差异也不作为无效判定。原八样本是 FOV，不声称八个独立胚胎或无偏 CV；训练重叠 UNKNOWN。

## 执行与证据边界

冻结 manifest SHA256：`e126e7fff52941518b70a3dc3c8e9523a804f7fcffdd511079c63f6f098831e7`。已在长推理前冻结 22 个文件、源码身份、输入、三个差异、比较政策和预算。全部请求先落账；每个对象正式提交最多一次，写响应不明只读核对。当前保存 1/4、正式提交 0/3、共享修复 0/1，新 Notebook 1/3。实时初始 GPU 余额约 23.10 小时，今日正式提交已用 1/5，剩余 4 次；每次写前重新读取更低平台上限。

B0 已在 2026-09-08 11:41:41（上海）发起真实保存并运行，Version 1 / SV 348114666 / kernel 133498982；唯一 HTTP 写发送回执已保存。平台 13 个执行单元与本地源码一致，JSON 序列化字节哈希单独记录。普通运行最终重写审计、实际后处理选择、完整日志与 GPU 资源、正式提交和分数仍待回收。正式隐藏重跑产物与选参若不可见则始终为 UNKNOWN，不能以普通产物代替。

源文件、开发回执、实际测试、逐对象源码与配置位于 `experiments/PUBLIC946_TTA_20260908/`。统一状态为 `results.json`，请求账本为 `write_ledger.json`，独立机器验收器为 `verify.py`。大型原始回收保留 ignored `downloads/PUBLIC946_TTA_20260908/`，GitHub 仅收源码、小型证据与哈希；不提交比赛数据、权重、submission.csv 或凭据。

## GitHub 交付

当前本任务文件尚未提交 GitHub。任务文件已在 main 固定提交中；实验实际完成、是否提分、GitHub 同步及远端回读分别验收。最终固定内容提交、交付提交与权威远端字节/哈希回读将在交付时记录。没有自动追加实验、跨日重跑或后台完成承诺。
