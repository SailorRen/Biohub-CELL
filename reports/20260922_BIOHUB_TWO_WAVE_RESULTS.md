# Biohub 两批四次正式验证：阶段结果

任务：BIOHUB_TWO_WAVE_20260922_V01。分支：codex/two-wave-four-submit-20260922。状态：PARTIAL；A 普通生产已启动，正式提交尚未开始。以下平台观测为上海 2026-09-22 11:09—11:39；不是四臂完成报告。

## 实际推进状态

|臂|母版与唯一算法改动|普通 Version / SV|正式 submission / 状态 / 原始 Public|参数和实际 CSV|相对 D960 / 排序|
|---|---|---|---|---|---|
|A|精确 D960；velocity 0.5→0.25|V1 / 351739212；RUNNING；11:33:55 保存|null / NOT_SUBMITTED / NOT_SUBMITTED|初始化配置日志0.25；最终消费回执、实际CSV、有效变化仍待普通完成|尚不可比较；未取得候选排序|
|B|同 D960；velocity0.5，增加L030P单次保护剪枝|未创建、未运行|null / NOT_SUBMITTED / NOT_SUBMITTED|源码与14项CPU小图检查完成；无真实CSV|尚不可比较|
|C|WAITING_FOR_WAVE1，未按表选择配置|无|无正式请求|A/B均未取得正式结果，不提前运行|尚不可比较|
|D|WAITING_FOR_WAVE1，未按表选择配置|无|无正式请求|同上|尚不可比较|

[A 精确运行版本](https://www.kaggle.com/code/sailorren/biohub-d960-v025-20260922?scriptVersionId=351739212)。Version Name：A V025 source 4dca986。未读取数值 Kernel ID，记 NOT_OBSERVED，不能用 SV 冒充。历史运行时间只用于资源估计，不表示本次已经完成。

## 平台身份、额度和直接限制

当前浏览器授权账号 sailorren / Sailor Ren；比赛团队 Sailor Ren，Sailor Ren 为 Team Leader，Dongdongjiaqi 为 Member。11:13左右提交对话框明确显示“4 submissions remaining today. This resets in 21 hours”。这是团队实时剩余额度；只提供小时级提示。精确刷新时刻 UNKNOWN，大致在9月23日上海08时附近，属于按UI相对时间估计，后续每次正式提交前必须重查，不能自动花下一周期名额。比赛截止页面提示2026-09-30 07:59（UTC+8）。最终选择保持0/2，无修改。

开始时GPU剩4h10m/30h；A启动前编辑器显示已用26:03/30h，即约剩3h57m。历史D960精确页面普通运行7492.7秒（2h04m53s）。两臂仅历史推理时间之和已超过3h57m，且账号另有 Biohub Geometric Fusion V1 / SV351717889 普通T4×2作业已运行约2小时，仍消耗余额；另有两个正式Scoring事件。本任务未修改或取消它们。故按授权优先A，B为 GPU_RESOURCE_BLOCKED，不能将“4个提交名额”当作“4次GPU生产资源”。运行耗时还可能受CPU回放、队列和输入影响；没有做GPU诊断。

A开始后活跃事件4项：本次A普通运行、既有Geometric Fusion普通运行、两个旧正式评分。A仍运行，尚无可以下载验收的最终产物，是正式提交的直接前置阻断。B不能启动导致A/B正式结果对尚未形成，C/D不满足任务第6节开始条件。没有新分数、显示提分或Private结论。

## 源码与检查

所有历史来自GitHub；未读旧Mac、旧缓存、凭据或比赛数据。新本机使用独立目录。Git HTTPS helper不可用，按任务改用已授权GitHub连接器；本地git状态NOT_APPLICABLE；未安装Kaggle CLI或训练环境。Python使用本机已有捆绑运行时，仅CPU小图检查。

D960来自固定1cf89f1f9380f005d98e9cb15ca9f5d80c4ebaca，文件SHA256 b12568e27ea5a8c66942a6301c2c80d037fdffe43f338a23a86266f80a02d192，完整下载且校验一致。其实际平台名称是biohub-g1-det0960-20260921，V1/SV351441983；名称含g1不代表误取另一母版。

首批源码冻结commit：4dca986a5bd61e3191ff790b74b505017678652e。10个新增文件已按固定commit全文回读一致。

- A candidate SHA256：393dc558654af6abffd8c786a1b8fd4065a58e5c2a6a0ba61af4b9d3b4be40df。
- B candidate SHA256：03e4abd5c80b5724b959bc453352524e276bebcf9aa0c2ffa38f22442d3e2ceb。
- 仅原cell0和cell5代码变化。原7项选择器、组合生成和选择规则逐字不变；清空outputs和execution_count。保留的旧execution/papermill元数据是母版来源信息，绝非本次执行证据。
- A在配置初始化前赋值0.25，实际predicted表达式保留并加入消费统计；原选择器调用共享同一参数。最终回执核对参数和实际消费次数，不以初始化显示代替验收。
- B从真实模型字典的存在性及有限值建立概率来源；缺评分、几何新边及无评分修复边豁免。短轨救援后、平滑前，一次快照评估并同时删除弱叶；保护父节点分裂、实际输入Zarr T轴最后帧，不级联；末帧不可读取则跳过并记录。
- 14项CPU检查PASS，包含实际改后motion函数、真实0与缺评分、强边、分裂、末帧、无级联、禁用无删除、ID重编号不影响规范化。测试不代表真实精度或Public增益。
- 同一次生产在同一原始推理图上CPU回放禁用候选的D960后处理，仅用于有效性证据；不额外推理、不重跑GPU。输出保留原canonical哈希，另加无节点ID/行顺序影响的有向森林摘要。回放使用候选所选下游配置，因此不是独立D960正式对照，也不能当Public分数。
- check_actual_csv.py为适配后的独立标准库验收器，覆盖schema、覆盖率、坐标/哨兵、端点、时间方向、入出度、行ID、重复边、哈希和运行回执；附已归档D960/H30/R00规范化哈希去重。后续B还须带入本批A的实际检查摘要去重。当前尚无实际CSV可供运行，不能把AST或小图测试写作CSV PASS。

## A 云端设置及已观测启动日志

A是唯一新私有Notebook。浏览器Copy & edit精确D960后重命名，再用Kaggle Link导入固定GitHub Raw源码。原Notebook内Kaggle元数据与独立kernel-metadata不完全一致；Link导入覆盖Inputs后，已在界面逐项固定DeepCenter Dataset V5、secondary V2、primary V10，补挂gate Notebook V1（当次来源页为Version1 of1 / SV349707105）。权重断言保留。原比赛输入留云端。

页面确认Private、GPU T4×2、Internet off、No persistence、Pin to original environment (2026-07-01)。运行Viewer的通用标签显示Latest Container Image，精确运行Docker摘要未通过API观测，不能声称已核对到历史digest。原依赖导入与固定权重短检查在同次生产中执行，没有另开诊断。

已观测：Configuration guard PASS；离线依赖安装成功；Required graph/Zarr/ILP packages import successfully；primary materialized SHA256为12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771；DeepCenter为8040999a92f6b7bbd98fa8cf458141e045c0f9ad7c936bdb3b18e1f7edafe2a0。secondary/gate实际加载及最终motion/CSV回执仍以后续生产日志为准。母版继承的旧文字打印（如Reverse-time association weight0.200）不是配置证据，以实际守卫、worker和新回执为准。

文件选择器上传被扩展以Not allowed拒绝，未传入文件；页面自带Link导入成功，因此它不再阻断本次启动。自动审批曾因D960名称含g1拒绝创建副本；补查固定D960元数据与SV证明身份一致后，单次平台创建成功。被审批阻止的动作未向Kaggle派发，未额外创建对象。Kaggle复制操作自动点赞母版，UI显示Copied notebook upvoted；记录这一附带效果，没有主动执行额外点赞。

## 已有正式结果：仅只读

上海11:09—11:13同窗提交页：DF960 submission56445846 / V1 / SV351617874仍Notebook Running，Public显示空；错误描述未显示，记NOT_OBSERVED。不是当前COMPLETE，也没有重跑或重提。D96056416049/SV351441983、F156375774/SV351084196、G156270217/SV350197436均Succeeded，Public原始显示字符串0.948。当前Recent视图不是Public排序，本轮排序NOT_OBSERVED；不推测隐藏小数。全队最佳显示至少0.948；第二批决策时必须重新读取同窗实际最佳和正式成绩。

## 累计预算与续接

Notebook 1/4；Save & Run 1/5（计划1/4，共享工程备用0/1）；正式提交0/4；训练、Dataset写入、独立GPU诊断、最终选择修改均0。所有本批预算跨会话累计，不因平台刷新增加。创建、草稿编辑组和Save & Run意图在操作前写入唯一platform_ledger；精确意图持久化时间采用GitHub commit时间，普通版本时间采用Kaggle UI。失败或不明确的实际平台写请求不能盲重试。

续接先读最新platform_ledger.json，再只读查A V1/SV351739212，严禁重复创建或重跑。普通完成后从精确版本下载submission.csv、two_wave/production_receipt.json及必要小回执；核对source/Inputs/模型、运行独立CSV检查与有效变化/去重，实时复核团队额度及刷新周期后，先记唯一正式请求意图，再立即提交A一次，不等待B或DF960。只有明确工程错误才考虑全批共享备用。B需资源真实足够才生产；C/D只有A/B正式可比结果都具备且仍在目标周期时按原任务第6节决策，先同步依据，不能提前推测配置。

本阶段尚未发出正式请求、没有任何新Public分数。会话结束后不声称代理仍在后台操作或自动提交；未创建定时器。Kaggle已接收的A是独立云端作业，其状态可用精确SV继续只读查询。阶段回读记录见同目录github_readback.json，仅保存本次小文件，不上传原始CSV、完整图、模型或凭据。

### 后续启动观测

同一SV351739212运行到508.9秒时仍RUNNING，日志已显示secondary SHA256与固定9bac2fa0dadc4a6fc1899e0caf187f4b553e0a7cd90ba1261a68b35ffe9e305f一致、CUDA Tesla T4、发现4个实际test视频，并启动CUDA0/1两个独立视频分片。worker实际日志det_threshold0.96、secondary_detection_weight0.8。此为真实生产进行中，不是最终图完成或正式评分。gate实际后处理调用和最终CSV仍未验收。
