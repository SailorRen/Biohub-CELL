# Geometric Fusion 证据补全结果

观测日期：2026-09-22，Asia/Shanghai（UTC+8）。任务状态：**PARTIAL_BACKFILL_BLOCKED**。A 已闭合；B 已完成当前 UI 只读查分，但 DF960 尚无正式分数，API 原始字段仍有缺口；C 已完成限时核查。交付核验见同目录 `github_readback.json`，不以本报告文字替代远端回读。

## A．公开 0.948 已绑定，附件指纹全部一致

|字段|本次核实结果|
|---|---|
|作者 / slug|Aman Atar / amanatar/biohub-geometric-fusion|
|Notebook Version / ScriptVersionId|**V3 / 351532492**|
|版本历史时间|2026-09-21 17:18:35 上海；页面头部为17:18:34，分别保留|
|当前 Public / 历史 Best|**0.948 / 0.948（V3）**|
|分数展示位置|固定版本页 Competition Notebook 面板；Best链接同样指向SV351532492|
|观测窗口|2026-09-22 10:16:27–10:21:24 上海|
|作者 submission ID|NOT_PUBLIC；不阻断版本绑定|
|固定链接|[Geometric Fusion V3](https://www.kaggle.com/code/amanatar/biohub-geometric-fusion?scriptVersionId=351532492)|

以上为 **OFFICIAL_FACT**（平台当前展示），不是仅凭卡片Best或普通运行状态推断。只读下载精确SV现有源码，2026-09-22 10:20:38取得637,942字节，SHA256：
`940ccce3466a8fdbbe4ead62c1bf33faef23054958ddf92d62858f81bdef774f`。

**SOURCE_CODE_VERIFIED：12/12代码单元的类型、顺序、原样source SHA256全部匹配；整文件字节哈希也匹配。** 有序source总哈希为 `4e54b0202bc8d6f4428664a1e7f4feec5592020c01540d8450bd4e628efafe6a`。比对不strip、不改换行，单元哈希排除outputs/execution_count/metadata。逐单元证据见JSON。旧Chat附件本次未访问；比较基准是GitHub固定提交中的附件指纹，本次取得的是公开V3。未镜像第三方整本源码到GitHub，页面许可显示Apache 2.0。

读取V3已有outputs确认最终组合实际采用velocity0.25、leaf0.30、tight5.5、几何11/16/12、DeepCenter0.15，融合仍harmonic_probability / 0.15。cell11的leaf0.0是写出后恢复全局值的读数：cell10在pp_apply后写CSV，再finally pp_restore；已有输出记录剪枝10/9/0/52。未下载实际CSV或单独ppsweep文件，未执行Notebook。局部proxy0.9530及vel025单项0.9505均是**已有局部测量**，不是正式单项Public，更不能把整个0.948归因于velocity。

## B．DF960当前仍待评分；查分已恢复访问

本次先遇到内置浏览器未登录，随后发现**Edge已有sailorren登录态**（账号菜单Profile链接核实），只读查看[正式提交列表](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/submissions)，没有登录、提取凭据或新建任务。

|方案|归档submission ID / 当前V1精确SV|本次UI状态|原样UI Public|
|---|---|---|---|
|DF960|56445846 / 351617874|Pending（图标title）/ Notebook Running|空字符串，归一化null|
|D960|56416049 / 351441983|Succeeded|0.948|
|F1|56375774 / 351084196|Succeeded|0.948|
|G1|56270217 / 350197436|Succeeded|0.948|

DF960详情观测自10:24:25起；[详情精确SV链接](https://www.kaggle.com/code/sailorren/biohub-df960-flow-20260921?scriptVersionId=351617874)、完整描述、作者及Version一致。页面未显示错误，但**未取得API原始error字段，不能声称API确认无错误**。数值submission ID未在当前UI暴露，表中ID来自固定归档绑定，不是本次API重新读取；当前版本身份由精确SV链接和描述建立。API原始Public=null（未读取），UI原始Public为空，两者不能混淆。

10:25:48同窗Public Score排序前三为**D960、F1、G1**；三者显示PUBLIC_TIED、差0.000，排序领先单独成立；隐藏精度、同分规则和Private未知。手动选择仍0/2，本次未改。DF960没有分数，不能计算分差；正式列表里的Notebook Running不推翻旧报告普通运行COMPLETE，二者语境不同。08:00:31旧PENDING快照仅为历史，本节是新UI观测。没有等分、刷新轮询、取消或重提。

## C．直接相关公开增量

实际核查10:21:24–10:23:50，146秒，低于10分钟。先读目标V3评论（0条），再看Code Recently Run及Discussion默认/Today列表并核对绝对时间。近24小时窗口从9月21日10:21:24起；Today筛选不保证精确覆盖24小时，未宣称全量检索。

- [742266](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/742266)：正文仍是十项单参数均跌的AUTHOR_CLAIM。新增OpPrime评论（9月22日02:52:06）称分裂关联可能在ILP前、选择及relink阶段损失，关联改动未形成可靠增益；为COMMUNITY_REPORT，无V025/DF960精确版本回执。04:24:20另一评论是泛化建议，没有直接实测。
- [新增评分说明 V3 / SV351615701](https://www.kaggle.com/code/busyaprime/biohub-what-one-link-node-and-division-are-worth?scriptVersionId=351615701)：Akmal Xodarev（Busya PRIME），9月21日22:58:03头部时间，Code列表22:58:04。读摘要、相关scorer调用、限制和署名，未完整审计或复算。作者称在4个示例图做单项扰动：节点删除伴随真边丢失或近邻重匹配时会抵消收益；明确没有正式提交、示例可能训练内、榜单尺度只是估计。作为AUTHOR_CLAIM，强化谨慎剪枝的理由，不是保护版leaf030正式验证。
- [742064](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/742064)（9月19日旧帖）读到作者的训练覆盖与离线/Public反例；未本次独立核对模型manifest。[741749](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/741749)读到作者更正：自己的管线0.939，0.947属于公开Notebook；不是新候选成绩。
- Today列表其余两帖已读：[741651](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/741651)的02:27:00评论报告CV变动但Public未动；[742325](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/742325)为过拟合/耗时观点。均无本候选精确实测，不据此定量判断。

结论：有新的相关定性反馈，但针对D960-V025、分裂保护版leaf030的直接正式增量仍为 **NO_NEW_DIRECT_EVIDENCE**。卡片标题里的分数未当作验证结果；未扩大调查到训练或新模型路线。

## 决策与未闭合项

**继续保留D960-V025作为下一轮单参数候选建议（INFERENCE），未实现、未运行、未提交。** 依据是附件身份已确认、既有velocity单项局部边指标改善，以及只改0.5→0.25的清晰范围。整体公开0.948包含多项变化，也未证明优于D960；未发现直接反证不等于会提分。不能把它无差别叠加到已有F1位移替换的DF960。

仍未闭合：
1. DF960正式分数：平台当前UI Pending，故无分数可比较；不等待或轮询。
2. 本次API原始Public/error和数值submission ID重新读取：没有Kaggle API连接器，UI不暴露这些字段。Edge授权可用，因此不能再笼统标记BLOCKED_AUTH。
3. V025独立正式收益、leaf误删真实数量、Private及隐藏小数：本任务没有新实验授权或相应公开证据。保留既有局部分裂评分口径与训练内验证限制；CPU合成测试不重做，也不据它推断71次实际删除的误删数。

## 输入与交付边界

执行/交付分支 `codex/geometric-fusion-backfill-20260922`；初始远端HEAD `b70f453bc345bde06128fe7a2719d96e46120172`，GitHub分支响应确认其直接父提交为任务固定提交 `3840c240957275ecd6b255dda087212942e43f55`。按要求顺序读取AGENTS、任务、比较报告、指纹、leaf测试、DF960报告、SCORE_TRIO报告、public_score_order，最后从同步回执提交读取handoff_readback；确认存在后补读DF960 platform_ledger。历史报告中的旧执行授权未继承。

当前本地初始空仓库无remote、无用户改动；克隆因缺git remote-https helper失败，改用GitHub连接器。目标项目本地git工作区/ahead-behind为NOT_APPLICABLE，不能编造clone或push成功。交付仅新增本报告、backfill_evidence.json及github_readback.json，远端固定提交全文及blob核验由回执记录；不修改main、历史报告、指纹、测试、账本或候选代码。

**本次Kaggle写请求为0**：训练、GPU诊断、推理、Notebook创建、Fork、Save & Run、正式提交、Dataset写入、最终选择修改、自动监控均0。浏览器只读导航/排序不属于候选写入；Node仅下载和解析现有源码，没有执行代码单元。
