# DF960 单次正式提交

任务固定ed143c02ddf97f9dd6e75ab256bf41383e4e4256。唯一候选：固定D960检测0.960生产链，原后处理调用点安装正式F1（V1/SV351084196/submission56375774）的邻域位移补偿；其实际源码与参考补丁逐字相同，SHA256 d2511cb21d536d230a6607d3119bccb1d931e21f4ec49237790d6dc335266896。k12、半径40um、排除1.5um、至少4种子、一轮；保留其他配置、原选择器和输入/权重。仅改变D960代码单元5和13（补丁安装及小型回执）；CPU六项短检查PASS，包括关闭补丁恢复缓存D960图子集的原运动结果。

## 限时公开补查

2026-09-21晚，登录态检查Code Recently Run列表、Discussion Recent Comments列表与直接相关正文，约8分钟，无全量调查声明。
- [flow2 V1/SV350702651](https://www.kaggle.com/code/thtennant/biohub-frontier947-flow2-det096-v1?scriptVersionId=350702651)：当前页面Public和V1链接均显示0.946，纠正任务内旧UNKNOWN。该版本还有更宽关联门槛、关闭validator等不同配置；不是本账户D960+正式F1唯一补丁组合，不能直接判定DF960失败，也不能借它声称提分。保留Teddy Tennant来源署名。
- [新relink讨论742266](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/742266)：正文作者称十项单参数试验均跌，训练离线分与榜分不一致，并询问relink增益；属于AUTHOR_CLAIM，未提供精确DF960失败证据。
- [近期Code](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/code)按Recently Run查看24小时内条目，仅用卡片发现来源；未发现明确标明本组合的新失败结果，未引入新模型或方案。

## 启动前历史状态

账号sailorren；初始团队当日4/5已用、剩1，目标slug全量owned inventory不存在。GPU UI9h46m，Active Events0。不假定上海午夜刷新。候选已构建，实际生产、CSV检查及正式提交尚未执行；NOT_SUBMITTED，Public=null。预算上限Notebook1、SaveRun2（计划1+明确工程备用1）、正式1；训练/Dataset/其他候选/最终选择0。唯一请求账本platform_ledger.json。

## 2026-09-21 已启动的唯一生产运行

上海2026-09-21 23:06:43持久化并发送一次Save & Run，Kernel135257948 / V1 / SV351617874，source commit eb231c474e435f5255ece0c4745250b1d38c5904，Notebook SHA256 17ab1c1ff18d6b692d1f30a8e40e3a866b59e966760efa3fbd648b24bebfb813。平台全14代码单元回读一致，私有、GPU T4x2、Internet关闭；普通RUNNING。正式NOT_SUBMITTED / submission=null / Public=null，CSV尚待普通完成。已用Notebook1/1、SaveRun1/2、正式0/1。已有F1 V1实际CSV已回收至Git外，用于候选完成后的规范化去重，不产生GPU对照运行。

## 2026-09-22 续接：提交前独立复核

上海07:53，精确V1/SV351617874普通COMPLETE，平台源码全单元一致，运行12989秒。实际CSV共241944行、4样本；原始SHA256为4798073c56ce777b217898afda628120aa493452053e1f6866321548b06f0405，规范化内容SHA256为82366701907d91135dfd94bc3c352546c5122b79b9e645772de9a044378f4c96。check_outputs.py独立复核PASS：官方schema、样本覆盖、坐标、图端点/时间/度、官方reader回读、输出和回执一致；模型权重、det0.960、flow配置与实际调用、其余配置通过。原选择器选择combo(tight55+relaxed9)。

4个样本相对归档D960实际CSV均变化，合计节点净减118，边增加2565、移除2784；与F1及已有候选规范化内容不重复。跨运行输入字节同一性未重新独立建立，差异不代表精度提升。历史D960/F1输出从平台恢复并与原归档字节哈希一致，完整CSV/图不入Git。

最初只读下载遇到连接中断，随后完整下载及哈希核验成功；没有新增Save & Run。平台提交列表未见DF960，UI无活动作业，GPU剩6h10m，提交入口可用；正式请求发送前再次API核对配额。此阶段正式NOT_SUBMITTED，Public=null。

## 最终交付状态（2026-09-22）

**已正式提交，SCORE_PENDING；普通运行与独立CSV复核完成，正式评分尚未完成。** 上海07:55:03发送唯一正式请求，平台返回submission **56445846**，绑定Kernel135257948 / Version1 / ScriptVersionId351617874；07:55:22一次正式列表回读确认PENDING，原始Public为空字符串，归一化Public=null，无错误描述。没有等待Public，没有重试正式请求。

提交前复核证据commit f06d4adb56f18e507a467209982da4a1cb216774，GitHub固定commit回读9文件逐字一致；唯一请求UUID df9cd6fc-3281-4e88-acba-82c36ca4e420在发送前持久化。实时API提交前团队日额度4/5，剩1；跨上海午夜没有假定刷新。

同次正式列表中D960 submission56416049、F1 submission56375774、G1 submission56270217均COMPLETE，原始Public均“0.948”；本次未重新读取Public排序，不声称排序或隐藏精度变化，DF960无分数不能比较。Private未知；最终选择未修改。

累计预算：新私有Notebook **1/1**，Save & Run **1/2**（工程备用未用），正式submission **1/1**，训练、Dataset写入、额外GPU诊断、其他候选、最终选择修改均0。候选源码、模型、参数、main及旧作业均未修改。临时目录清理后用原分支最新commit的独立detached worktree续接，原用户工作区保持不动；通过非强制push更新原任务分支。

小型证据和本报告同步至原分支，最终新增文件的固定commit及字节回读见github_readback.json；该回读文件单独收口提交，避免递归生成验证链。下一步仅按用户通知只读查询56445846，不重提或重跑，不建立后台定时器。
