# 正式评分回读：2026-09-20 22:35 上海

**A18、B22 均已正式 COMPLETE，Public 为 0.948；F1、G1 同样为 COMPLETE / 0.948。** API 原始 public_score 字符串也都只提供 "0.948"，没有取得更多小数位。

|对象|Submission ID|ScriptVersionId|Public|自动选择候选|
|---|---:|---:|---:|---|
|A18 V1|56383942|351207161|0.948|否|
|B22 V1|56384003|351207989|0.948|否|
|F1 V1|56375774|351084196|0.948|是|
|G1 V1|56270217|350197436|0.948|是|

页面人工选择为 0/2，F1 与 G1 有自动候选蓝色标记。比赛规则允许最多两个最终提交，未选足时由系统按最佳成绩自动补选；最终名次依据 Private Leaderboard。规则的胜者同分条款优先较早提交，但本次未验证账户内自动候选同分排序的具体实现。

因此可以确认：**两次新方案在公开精度上没有提分，也没有替换 F1/G1 自动候选。** 不能仅凭未入选断言 A18/B22 的真实分数严格低于 F1；隐藏小数较低与完全同分仍无法区分，严格大小关系为 UNKNOWN。此结论不表示两份预测相同，也不推断 Private 分数。

只读证据见 score_raw_readback.json、formal_status_snapshot.json、score_selection_observation.json。累计预算保持 Notebook 2/2、Save & Run 2/3、正式提交 2/2；本次平台写入为 0。main、V1/F1、最终选择均未修改。下文为已完成的正式提交阶段历史快照，其 PENDING 描述已由本节评分结果更新。

---

# BIOHUB_DIVGATE_PAIR_20260920_V01 正式提交结果

两臂已完成实际最终 CSV 独立复核，各正式提交一次，并取得平台 ID。正式评分仍为 **SCORE_PENDING**，Public 均为 null；普通运行 COMPLETE 不代表评分完成。

平台 API 观测时间：**2026-09-20 14:52:21.765921 上海 / 06:52:21.765921 UTC**。

|候选|Kernel / Version|ScriptVersionId|正式 submission ID|平台状态|Public|相对 G1 Public|
|---|---|---:|---:|---|---|---|
|A18|135051720 / V1|351207161|56383942|PENDING|null|null|
|B22|135052315 / V1|351207989|56384003|PENDING|null|null|

A18 请求时间为上海 14:50:28，B22 为 14:52:07。平台成功响应中的 ID 与随后完整提交列表一致。正式详情页实际 Notebook 链接分别绑定 SV351207161、SV351207989。请求前账本以唯一 UUID 持久化且计入预算；没有重复提交或不明响应后的重试。提交前未发现这两个精确版本的既有正式 submission。

G1 submission 56270217 / SV350197436 的实时回读为 COMPLETE、Public 0.948；F1 submission 56375774 / SV351084196 仍为 PENDING、Public null，均仅只读。现有 V1/F1、main、模型、阈值和最终选择未修改。

## 实际 CSV 独立复核

从各精确 V1 下载真实最终文件及 G1 原始/0.20 重放输出，下载前后核对版本、全部代码单元、私有属性与输入。下载清单为各臂 formal_input_collection.json；正式复核为 formal_precheck.json。

|候选|CSV 数据行|原始字节 SHA-256|相对同源 G1 的真实完整图差异|
|---|---:|---|---|
|A18|241313|2e22cd6024d04d0b0fc29ff964fa38caa138ec4b9bd076258f966c638e32ee72|节点 +12，边 +16/-0，分裂 +7|
|B22|241238|18ea6f091ae5d5de2cc0ae938ceb061b16ba897445fe52a87eeb4ba6b167834f|节点 -22，边 +0/-25，分裂 -8|

两臂均 PASS：原始字节哈希与生产回执相符；官方 10 列 schema、4 个预期测试样本完整覆盖；行 ID 连续、节点/边唯一、端点合法、时间前进、入度/出度合法；官方 reader 回读内容与独立解析一致，规范化图哈希与回执一致；原 0.20 重放等价；候选均有真实内容变化且两臂不同，未触发无效应/去重停止条件。

实际生产调用仅分别将 DEEPCENTER_SAFE_DIV_THRESHOLD 从 0.20 改为 0.18 / 0.22。保留原 tight55 选择与其他配置，原始推理图哈希配对一致。权重、官方源码、运行依赖版本及 tracksdata 源码清单均绑定；日志确认模型实际加载、无静默回退。复核重用已有结果，没有重新运行大模型。

8 视野、2 胚胎的辅助官方诊断三组均为 0.9440708304724714，差值 0；全部与 secondary 训练归档重叠，为 TRAIN_SEEN_DIAGNOSTIC。该值不是 Public，不支持泛化或提分结论；不以诊断持平阻断已授权的探索性正式提交。

## 预算、冻结与异常记录

累计新私有 Notebook **2/2**、Save & Run **2/3**、正式 submission **2/2**；训练、Dataset 写入、最终选择修改、现有 V1/F1 写入均 **0**。本次正式阶段新增 Save & Run 为 0，未再次执行 launch_once.py，无第三臂、无后续轮次、无自动监控。

原任务固定提交 cd18d89d54f9dee9079d307bad8ae7021dfa0004，17826 字节，SHA-256 8e84b1c618adbb95d0b47a12e59740d1e8872b27e71a22f1349cccc6a3e2d520。冻结合同 SHA-256 **f236c8e2f73d8b3e9ed4ef6e04346caaeddc954e05cf7b6992104b1b2018c07e** 未变。固定研究 6ec61f54cd5fb5b93fe7cd1dbc37b01a8e41bc57、G1 代码 e9c7c63b896812660a78ec55fc3284c10f85e776 未变。

提交前必要代码、配置、独立复核已推送到 **ea96c3a24762c98bfe313235b2bb87c165da97e9**，formal_code_readback.json 记录 79 个文件的 GitHub 固定提交逐字节回读，先于两次正式请求。

写入前确认账号 sailorren、比赛 136605、已参赛/可提交、动态每日上限 5；A18 前已用 1、B22 前已用 2。已登录 UI GPU 余量 20h38m/30h，普通运行并发为 0，正式提交按钮可用。SDK quota 的 6h 总量与 UI 不一致，两侧原始观测保留，不声称一致；实际平台接受请求。各臂 formal_prewrite 与 formal_ui_prewrite 保存当时观测。

只读收集曾遇到版本标签接口 404，及每次读取都会变化的 lastRunTime；改为版本前后精确身份/完整源码/其他元数据核对，实际差异保留在 collection_interface_note.json 和各臂清单。均未发生平台写入，不消耗工程备用或正式重试预算。

## 交付与验收范围

实际 CSV、完整图、权重和原始大日志只留本地私有临时目录，不写 GitHub。仓库仅代码、小型清单、哈希、汇总、平台回执和报告。历史运行中及只读结果报告保留在 report_before_formal.md，历史状态不代表当前状态。

6 项人工图工程测试通过；冻结 verify.py --execution 返回 EXECUTION_VERIFIED。原冻结合同 5/5 必要检查通过（原文字节、工程测试、执行证据、交付证据、干净 Git 与远端 HEAD），在合同范围内为 COMPLETED_VERIFIED，见 acceptance_verification.json。验收 Git HEAD 为 566339e4a886b9be109feffa88928b1d22aa64b4；正式交付正文提交 428fc578a7136ec1a8d93c54a13067ee82f547ef 的 92 文件已通过 GitHub 固定提交逐字节核验，见 github_readback.json。上述核验范围是授权运行、输出复核、正式提交及交付，**不包含尚未返回的正式评分或效果结论**。保护前后证据见 formal_protected_refs_before.json / formal_protected_refs_after.json。

后续仅可按精确 submission ID 只读查分；本批正式预算已耗尽，不得重提、改版或自动开启下一轮。
