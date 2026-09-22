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

## A现有V1正式提交续接：Mac独立验收

2026-09-22从GitHub同步至任务commit5d6093a8d27e21c6900acba01f81cb81dc289b0c，隔离worktree续接，未使用Mac旧账本启动。当前A Kernel135318885 / V1 / SV351739212，普通COMPLETE，耗时9029.9秒；全部14代码单元类型/顺序/source与冻结SHA256 393dc558654af6abffd8c786a1b8fd4065a58e5c2a6a0ba61af4b9d3b4be40df一致。SDK metadata的lastRunTime为继承旧值，未用于本次完成时间；精确SV以版本页面和edit/run链接绑定。

选择性下载实际CSV和所需小回执到Git外。原check_actual_csv.py原样执行PASS：241889行、4样本、schema/坐标/哨兵/行ID/图结构/时间/度/哈希/归档去重通过；同次云端官方reader往返PASS。CSV SHA256 d46a19a6579538034f00701550e86b6a7087b1a58921eccf615767d60852aa55；ID无关摘要5e5210eb2c0460d2ff7a7171cbfde42c2820a1f03a37643736541b44f083aec0。4样本均有非纯重编号变化，不代表Public提分。

独立最终消费复核PASS：velocity0.25共127524次，leaf禁用且删除0；det0.960、harmonic0.15、secondary detection0.8、G1分裂门0.20、三推理权重及gate一致，模型实际加载与后处理使用正常。原选择器本次选combo(tight55+bonus125+relaxed9)。追加消费核验脚本初次将worker_harmonic_records列表按整数比较导致TypeError，修正为非空列表检查后通过；未修改生产源码或放松标准。

提交前SDK及UI均核对剩余4次，UI显示17小时刷新；精确Notebook V1及submission.csv正式Submit入口可用。先前误以默认JSON文件打开对话框只提示无法找到该输出，未点击提交；选择实际submission.csv后入口正常。本机SDK源码明确支持competition_submit_code(kernel_version=1)，将使用该接口，非本地CSV上传。唯一正式请求意图已追加原账本；本阶段尚未派发，新增Notebook/SaveRun为0，B/C/D未执行。

### A正式请求已受理

上海2026-09-22 14:40:43通过Kaggle SDK精确版本code submission发送一次，取得submission **56456090**，Kernel135318885 / Version1 / SV351739212，输出submission.csv。请求UUID d641440c-e68c-44a8-af6e-10b8cd4054d9；意图与必要验收摘要先同步commit cb92190da7347c58e0104f3cb0e5d7c9e3e6cfe6，发送前GitHub远端HEAD及原账本全文回读一致，没有并发新增A请求；API实时剩余4次。计数在派发前持久化，不盲重试。

14:41:20只回查一次：正式状态PENDING（SCORE_PENDING），原始Public=""，归一化Public=null，原始error=""。受理已核验，评分未完成，不声称提分。下一步仅按用户请求只读查56456090。

本次新增Notebook=0、Save & Run=0、正式请求=1/1。原批累计Notebook1/4、Save & Run1/5、正式1/4、共享工程备用0/1；训练、Dataset、独立GPU诊断、最终选择修改均0。B/C/D本次未执行，也未授权续启动；原历史记录保留。未提交原始CSV、完整图、权重、凭据或大日志。

本次新增/变更小型文件的固定报告commit和远端字节核验见A/github_readback.json；保留原github_readback.json既有记录并加引用。原Mac工作区未改动，交付采用隔离worktree非强制push原任务分支。

## B：Kaggle额度耗尽／Colab后备测试

### 2026-09-22 20:33 上海阶段记录

固定任务 a593633，唯一源码4dca986，SHA256 `03e4abd5c80b5724b959bc453352524e276bebcf9aa0c2ffa38f22442d3e2ceb`。隔离 worktree，原工作区无改动。已创建唯一私有B草稿 `sailorren/biohub-d960-l030p-20260922`，Kernel135375343；尚无Version/SV/submission。官方SDK回读后，14个cell源码在规范化source列表/字符串表示后全部相等，既有CPU14项检查复用；无真实CSV，生产/后处理验收NOT_RUN。导入覆盖数据源后已恢复三个固定版本及gate，详见B/draft_readback.json。

GPU官方接口：已用30:15:24.248，总30h，预留0；原始刷新字符串2026-09-26 00:00:00不带时区。UI普通Save & Run GPU选项和Save未禁用，因此先持久化唯一正常运行意图，尚未发送。Colab尚未进入，正式请求本轮0、原批1；Notebook本轮1、原批2；SaveRun本轮0、原批1。编辑器超时/导入/序列化比较误判及最小修复已归并记录，未重训、未新建Dataset、未执行C/D。

### 本轮停点：REQUEST_UNCERTAIN（上海2026-09-22 20:42）

唯一正常 Save & Run 请求 `TW20260922-B-SAVERUN-01` 已发出；运行前意图 commit `ffc710b8956bc7eafd388f99ba0b9aa10487a488` 已推送并按固定SHA回读账本一致。选择 GPU for this session，计划版本名 `B L030P source 4dca986`。页面原文：

> An error occurred while committing kernel: Failed to execute 'json' on 'Response': Unexpected end of JSON input

只读对账：官方 GetKernelSessionStatus 返回404；B版本历史显示 `Starting Fresh` / `Start writing your notebook then save and view your versions here.`；B提交对话框直接选中本候选，显示 `The selected Notebook has no completed versions to submit. Please run the Notebook or select a different one.`，Submit禁用。现有两个Active Events为旧正式评分，未见B普通作业。上述证据支持“未观察到受理版本”，不把异常响应当作从未收到请求，不重发。

GPU前后官方快照分别20:31:20与20:41:33上海：已用均30:15:24.248，总额30h，预留均0；不归因本轮扣时。刷新原值2026-09-26 00:00:00无时区，未猜上海精确恢复时刻。正式额度最新3次、UI resets in11hours。A仍Notebook Running，SV351739212、submission56456090仅只读查询；DF960的SV351617874当前Succeeded/Public0.948。原批历史A接受不等于出分。

**Colab未启动。** 虽然Kaggle额度已耗尽，实际SaveRun错误是响应解析失败，没有GPU拒绝原文，不能把未知原因归为资源拒绝；依任务要求停在对账边界，未迁移平台掩盖错误。没有Colab连接、GPU分配、环境检查、数据下载或生产，也没有验证外部产物替代保存的完整通路。当前B正常提交入口要求完成版本，这是本次UI事实，不推断所有正式替代路径均不可能。

保留唯一私有草稿 Kernel135375343，固定B的14个cell源码逐一规范化回读相等；Version=null、SV=null、submission=null。下载Notebook通过SDK返回的source字符串与原列表表示不同，曾引起直接对象比较误报，已以逐cell文本一致纠正；没有算法改动。固定Dataset选择为5/2/10，gate重挂现有输出，SDK只返回slug，不能将该字段夸大为当前gate SV独立回读。无需再导入代码。没有真实CSV、生产回执、真实删除数或非重复验收结果，均NOT_RUN，不以CPU检查代替实际输出。

|请求类别|本轮|原批累计|上限|
|---|---:|---:|---:|
|新Kaggle候选Notebook|1|2|4|
|普通SaveRun尝试（含异常响应）|1|2|5|
|正式提交|0|1|4|
|工程备用|0|0|1|
|Colab GPU会话/生产|0/0|本轮0/0|1/1|

今天3个正式名额均未由B消耗，要求保留的2个仍保留。同一草稿导入修复2次为编辑请求，不伪计为2个Notebook或运行。没有替代版本保存、训练、Dataset、TPU、购买、C/D、旧作业取消或自动监控。状态查询的首次自动审批超时发生在进程启动前，按工具允许只重试一次只读查询；不是运行重试，也不是安全拒绝。

下一步交回Chat决定：先分析SaveRun响应解析失败及平台后台状态，是否需要向平台核实；本轮正常运行尝试已用完，不自行再次提交运行。只有资源阻断原因得到直接确认且无B在运行时，才考虑继续既定Colab路径。此次交付是资源路径与失败证据归档，不是候选跑通或评分成功。最终固定交付commit及四个小文件远端字节回读结果在本任务最终回复给出。


## B Colab 往返续接实测（2026-09-22 21:29—21:48 上海时间）

状态：`BLOCKED_RETURN_OUTPUT_BINDING`。已建立非运行 V1，且实测 Colab 自有 GPU 可用；没有完整生产、真实 CSV 或正式提交。此结论替代上一节“未进入 Colab”的当前状态，旧 REQUEST_UNCERTAIN 和已用次数保留。

固定任务 commit `96e55736423a92717860e593b4b070c3b88b55f1` 已包含于执行分支。Mac canonical remote 正确且无未提交改动，复用隔离 worktree 并安全 fetch/ff-only；未改 canonical 分支、reset、stash、强推或合并 main。已读完整当前任务及所列必要材料；B 源码 SHA256 仍为 `03e4abd5c80b5724b959bc453352524e276bebcf9aa0c2ffa38f22442d3e2ceb`，算法未变。

|检查|结果及证据|
|---|---|
|一次旧请求对账|21:29 未发现 B 版本/活动普通作业，SDK404、Starting Fresh；GPU used30:15:24.248/30h、reserved0。记录 NO_ACTIVE_B_OBSERVED_AT_RECHECK，不推定旧请求未收到。|
|非运行保存|CLI2.2.3 help 不支持 --no-run；只做一次网页 Quick Save。Kernel135375343 / **V1 / SV351871500**，私有、Internet关闭，SDK enable_gpu true/NvidiaTeslaT4。|
|运行与代码|12.7秒 nbconvert HTML 打包，日志 Accelerator None，Output0B；14单元 execution_count=null、outputs空，normalized source与冻结B逐单元一致。不是模型运行。精确/1 pull403后，以UI唯一V1绑定current pull读取。|
|配置边界|五个输入身份存在，总88.45GB；本次SDK没有独立返回固定版本号。Docker digest变为`dafd4ce5668bbf1ad422e4c109e0f18c9623c3a7c7f48b0235f13142755c40b9`，与冻结原环境不同。隐藏评分GPU和环境未验证。|
|V1提交入口|明确 requires submission.csv / selected Notebook Version does not output this file；Submit禁用，File Upload禁用；剩3次、提示10小时刷新。未发送正式请求。|
|Open in Colab|同一B导出成功；延迟打开导致两个临时导出页，重复页未保存/运行并关闭。保存到Drive的Notebook0个；没有第二GPU。Kaggle显示账号已关联，未购买/授权新OAuth。|
|Colab托管GPU|21:44设备探针：Python3 Google Compute Engine GPU，1×Tesla T4，15360MiB（torch可见15637086208bytes），driver580.82.07；Python3.13.15、torch2.11.0+cu128、CUDA12.8、available=true、cwd=/content。已释放本次会话。|
|输入、依赖、真实批次|NOT_RUN。自动插入的kagglehub登录及下载单元未执行；下载语句不含固定版本，不能直接作为冻结输入。没有依赖安装、权重下载或真实模型批次。|
|完整生产/CSV验收|NOT_RUN，未生成CSV、production_receipt或output_check，不将设备探针当生产验收。|
|回传/正式受理|BLOCKED / NOT_RUN。V1缺真实磁盘输出；尚未建立官方输出绑定方法，未做第二次保存或CPU文件会话。B submission=null，无分数。|

本机SDK `competition_submit_code` 文档把file_name定义为kernel产生的输出文件，请求只指向kernel/version/filename，不附带外部CSV。[官方导入公告](https://www.kaggle.com/product-announcements/572642)支持Colab/GitHub/文件Notebook导入及Quick Save；[官方Notebook文档](https://www.kaggle.com/docs/notebooks)说明Quick Save快照。两者均未为本次建立外部磁盘CSV随V1绑定的证据。**未证明所有正规返回路径都不可能，也未证明必须再普通GPU运行**；已验证的是当前V1不具备提交资格，完整生产启动门禁未满足。

预算：本轮新增Kaggle候选0、普通GPU运行0、非运行保存1/2、Colab保存Notebook0/1（另有两个临时导出页）、GPU申请及分配1/1、完整生产0/1、CPU文件会话0/1、正式请求0。原批累计候选2、普通SaveRun尝试2（旧B不明请求不退账）、非运行保存1、正式请求1（A）；B累计正式0/1，另外两个名额保留。未操作A/DF960/C/D。

保留：Kaggle私有B V1及冻结源代码、原账本、resource_events.jsonl、colab_roundtrip_result.json。没有原始数据、CSV、模型、签名导出URL、邮箱或凭据入库。Colab仅设备探针，原模型单元未执行，导出后原14单元未再次逐字节导出验收，不能声称Colab生产源码验收完成。

交回Chat的最小问题：是否能给出可核验的、同一B保留GPU与完整离线推理代码的正规输出绑定流程；若不能，应修改后续授权，而不是继续猜测或耗费完整生产。无后台监控、不等评分。交付验证由固定commit的远端字节回读另附于本轮回复。


## CPU输出快照探针（2026-09-22 上海时间）

结论：**真实工作目录文件快照及精确版本下载哈希验证通过；GPU生产配置未保留**。同一B Kernel135375343的新版本为 **V2 / SV351886222**，名称`B output snapshot probe - NOT FOR SUBMISSION`。这只验证Kaggle工作目录→版本Output，不证明Colab CSV回传、B生产或正式评分。

安全fetch并快进隔离worktree至固定任务`301563f7902e9a54483f349a30c32893eab15e2d`；canonical分支干净、remote正确且未切换。完整读取任务/AGENTS/账本/上轮结果和事件；源码哈希未变。对账时B只有V1、草稿off、没有后续B活动或重复探针。

22:32启动唯一CPU文件会话，先将Accelerator由GPU T4×2设为None，Internet保持关闭。只用Console列目录和执行任务原标准库探针，无临时单元、模型导入、权重加载、RunAll或SaveRun。原目录仅`.virtual_documents/__notebook_source__.ipynb`245600bytes；没有未知用户文件，未删除文件。

探针`/kaggle/working/output_binding_probe.txt`：**103bytes**，SHA256 **`86298e704f9c847ebe421b0ccdabf5635ff63a9f058be0db8d5fe42dd73f084a`**。CPU打印回执、Mac独立构造payload、官方CLI精确`/2`下载文件三者一致。首次只读下载TLS `UNEXPECTED_EOF_WHILE_READING`，仅一次同版本只读重试成功，不重发保存。

Quick Save明确选择 **Save output for this version when creating a Quick Save**，不是Never。唯一意图`TW20260922-B-OUTPUTSNAP-01`先写原账本，再派发一次；保持CPU直至上传、快照和文件验收完成。版本Output实见文本内容及103B，另含平台自动`.virtual_documents`源码文件；总245.7kB。打包日志6行：语法警告及nbconvert HTML转换，Successfully ran in11.9s，Accelerator None，无模型运行。

保存前后下载源码逐单元比对：原14代码单元类型、顺序、source完全一致，execution_count全部null、outputs全部空；版本Diff+0/-0。编辑器旧“Cell executed at4:32am”提示源于继承的2026-09-09元数据，不代表本轮执行。

新版本元数据：private=true、Internet=false、enable_gpu=false、enable_tpu=false、machine_shape=None。五个Inputs身份保留，SDK未独立返回各版本号，本次未修改Inputs。Docker为`gcr.io/kaggle-images/python@sha256:dafd4ce5668bbf1ad422e4c109e0f18c9623c3a7c7f48b0235f13142755c40b9`，与上轮一致；编辑器Pin to original标签不能替代实际digest。CPU交互/打包为None不证明隐藏评分，**hidden_gpu=UNTESTED**。没有submission.csv；未点击Output页的通用Submit to Competition按钮，未打开或测试正式资格，正式请求0。

22:34:36实读GPU used30:15:24.248/30h、reserved0，恢复原字段2026-09-26 00:00:00（时区未指明）。本次CPU约7分钟后正常Stop session，确认off；快照和下载均已完成，不影响旧任务。

预算：本轮CPU文件会话1/1、带输出Quick Save1/1；新增Notebook/GPU/Colab/TPU/模型/数据下载/正式提交/Dataset均0。原批累计候选2、普通SaveRun尝试2、非运行保存**2/2**、正式1（A），B正式0；旧不明请求未退账。

没有文件快照机制阻断。下一步最小问题：若要继续真实Colab产物返回，需另行授权新Colab会话及最终保存，并明确如何保留GPU生产配置。本轮不恢复GPU、不继续生产。结构化证据在`B/output_snapshot_probe.json`；固定报告commit和4文件远端字节回读结果由最终回复给出。


## B真实输出回传续接（2026-09-22 23:12起，上海时间）

停点：**BLOCKED_GPU_OUTPUT_COEXISTENCE**，发生于GPU＋输出组合路径闭合之前。没有启动本批Colab生产，没有真实CSV、最终版本或正式B请求。最新仍为 **Kernel135375343 / V2 / SV351886222**，CPU文本探针，禁止提交；B Public为NOT_RUN，不写SCORE_PENDING。

本任务原文先以`7999df89645512c588d7ac986408ad3aa8e8fe3d`提交原分支并远端字节回读通过（10345bytes，SHA256 `7711b7646bf44387a9e82c92cfe86a0f4486fe285bbdf0605f31f247a503f1a7`），随后才操作平台。安全复用隔离worktree，包含交接基点1735cafe；canonical未改动。冻结B源码哈希仍为`03e4abd5c80b5724b959bc453352524e276bebcf9aa0c2ffa38f22442d3e2ceb`，原14单元未编辑或模型执行。

实际动作及边界：

1. 只读核对账号sailorren、B版本历史/活动作业和正式列表，未发现后续B生产或提交。剩余正式3次，UI提示9小时刷新；没有跨刷新使用额度。A56456090仍PENDING，D96056416049实际Public原值0.948，均未执行。
2. 草稿off时成功恢复GPU T4×2元数据，仍off，说明单独改GPU标签无需启动计算。查看Quick Save高级设置，仅有Save Output选项，没有独立GPU绑定项；取消，未派发保存。
3. 为组合检查将草稿设None，按原账本意图启动本批唯一CPU文件会话。Console初始目录为空，仅重建已归档103byte探针并打印同一SHA256 `86298e704f9c847ebe421b0ccdabf5635ff63a9f058be0db8d5fe42dd73f084a`。没有重复CPU-only快照、临时Notebook单元、模型加载或Run All。
4. 活动CPU会话选择GPU T4×2后出现确认框：**“Availability is limited to 30 hours per week. You have 0 hours remaining.”**，按钮Turn on GPU T4 x2。[Kaggle官方文档](https://www.kaggle.com/docs/notebooks)说明活动会话添加GPU会重启至GPU环境。该路径涉及本批禁止的Kaggle交互GPU申请，因此未确认，取消并停止本次CPU。最后UI为off，草稿None，版本数仍2。

阻断不是“hidden_gpu尚未验证”，也不是旧JSON错误或缺submission.csv。本轮核实的当前活动会话切换路径需要GPU重启；没有获得官方支持的独立GPU＋磁盘输出保存路径。**未证明所有官方路径绝对不可能；停止CPU后恢复GPU并保留磁盘输出的组合仍NOT_VERIFIED，未冒充已支持或已失败。** 无新保存故无新打包日志、版本GPU或输出下载验收。V1 GPU与V2输出不能拼接。

23:22:41 SDK实读GPU used30:15:24.248/30h、reserved0，refresh原文2026-09-26 00:00:00（未标时区）；首次TLS EOF后一次只读重试成功。未发GPU请求；释放后未重复查询配额。原Inputs未改，5个身份可见，本批未独立回读各版本号。

自动审批两次在派发前拦截：off状态GPU确认最初被识别为GPU启动，经核对本任务明确元数据授权和off状态后同一动作获准；GPU配置下“取消＋打开Run菜单”批操作被拦截，改为单独取消并设None后查看CPU菜单。没有借此发GPU、SaveRun或模型执行；最终平台阻断依据为上述实际界面和官方文档。

|预算项|本批新增|原批累计|累计授权上限|
|---|---:|---:|---:|
|CPU文件会话|1（已释放）|2|3|
|非运行Quick Save|0|2|4|
|Colab托管GPU会话|0|1（历史探针）|2|
|完整B生产|0|0|本批1|
|正式请求|0|1（仅A）|4；B累计最多1|
|普通SaveRun尝试|0|2（含旧不明请求）|本批新增0|

另外两个正式名额保留。新增Notebook、数据下载、训练、TPU、Dataset、购买、C/D、最终选择修改均0。旧REQUEST_UNCERTAIN不退账。保留冻结源码、V2探针及Mac归档；没有源码适配或CSV可复用。

下一步最小问题：在不启动Kaggle GPU的条件下，是否有可核验的官方GPU元数据与CPU磁盘输出同版本保存流程。此处按任务停止，不自行新开研究轮次或先启动Colab。结构化本批结果在`B/colab_roundtrip_result.json`的`return_gpu_submit`，事件追加原JSONL，预算沿用原账本。关闭时间记录为2026-09-22T23:30:52.459485+08:00（收尾转录时间）。固定交付commit、远端小文件回读及worktree状态在最终回复给出。


## B编辑器直接正式提交一次（2026-09-23 上海时间）

**实际点击一次最终Submit，平台明确拒绝：`Accelerator Quota Exceeded`。未受理B，未生成V3或自动普通作业。** 状态`EDITOR_SUBMIT_REJECTED_ACCELERATOR_QUOTA`。任务原文已先提交`32eac4c90e47a75201e09d2db11338929b674b29`并固定字节回读通过；原分支包含交接基点c5f91b9，无后续并行交付，canonical及用户文件未改。

本任务替代旧CSV、GPU＋Output及9月22日额度周期前置条件。故没有重复Colab/CPU探针，也没有以旧停点拒绝执行。当前账号sailorren；初查No Active Events，正式列表无B。Daily Submissions为2/5 used，确认框剩3次、7小时刷新，未等待刷新。

准备：从同一B编辑器File→Download Notebook下载当前草稿，原14个代码单元source逐一与冻结B相等，execution_count全部null；冻结SHA256仍`03e4abd5c80b5724b959bc453352524e276bebcf9aa0c2ffa38f22442d3e2ceb`。未导入或改源码。当前UI分别核实primary固定V10、secondaryV2、DeepCenterV5；仅查看后取消，无版本切换。gate身份保持，V1/SV349707105沿用原回执，不声称本次重新独立核实gate SV。Share为Private，Internet off；会话off时将None设为GPU T4×2，确认仍off。下载ipynb的继承metadata含isGpuEnabled=false，不能代替当前UI设置或最终精确版本元数据。

官方编辑器右栏Submit to competition→Submit打开新版本确认框，默认Version3，原文：

> Your submission file must be named submission.csv. Submitting will save a new version and based on your settings will run on a GPU T4 x2.

该入口使用当前草稿创建新版本，不是选旧V2；无需预先制造CSV。填版本名`B D960-L030P editor direct submission`，描述`TW20260923-B-EDITOR-SUBMIT-01 D960-L030P velocity0.5 leaf0.30`。唯一意图先以71e67c1同步，确认信息补充同步至`4b2a38ec642df5a96b35d851fd7d7734458f5ad4`，随后只点击一次最终Submit。

平台返回完整错误：

> You've exceeded the number of hours allowed to use GPU. Your quota will reset to 30 hours in 3 days. You can continue working in this session until you've reached your 9 hour limit. You will not be able to commit unless you turn off GPU.

这是平台提示，不是本批自动审批拦截。只点Continue working关闭提示，没有选Turn off GPU、SaveRun、QuickSave或换入口重发。提示中的“continue working in this session”是平台通用文案，不能据此声称已启动会话；实际UI仍off。

点击后只读对账：版本历史仍只有V1及V2，最新 **V2/SV351886222** 仍为NOT FOR SUBMISSION文本探针；没有新V3、B正式条目或活动作业。submission、实际新Version及SV均null；Public=NOT_RUN。GPU证据只到当前草稿GPU T4×2设置，**提交版本GPU绑定未产生，正式worker GPU=NOT_OBSERVED，完整推理NOT_RUN**。不把计划V3当真实版本，不称SCORE_PENDING。

计账区分：最终提交按钮操作确实发出1次，按一次上限保守计账；没有网络层CreateCodeSubmission回执，不能声称正式评分服务已收到/受理。本次正式尝试1、受理0；原批累计正式尝试2/4（A受理1＋B拒绝1），B一次上限已用，不退账。平台Daily仍2/5 used，另外两个正式名额保留。本次自动版本0/1、配套普通作业0/1；手动SaveRun、QuickSave、CPU、Colab、交互GPU、训练、Dataset全部0。历史普通SaveRun尝试2、QuickSave2、CPU文件会话2、Colab设备会话1保持，旧REQUEST_UNCERTAIN不退账。自动作业无可识别对象，没有取消任何作业；无本次会话需要释放，无新增GPU运行可据以归因扣时。

同窗只读发现：A **56456090/V1/SV351739212** 已COMPLETE，Public原值 **0.950**；D960 **56416049/V1/SV351441983** 原值 **0.948**。B无分数，不能报告B差值；A显示值差0.002不等于精确隐藏差值或稳定因果提升。未改最终选择。

停止时间（收尾转录）：2026-09-23T01:13:08.313866+08:00。保留GPU草稿、冻结源码、旧V2、原账本与直接拒绝回执；本批不继续研究、重试、购买、等待额度或建立监控。固定报告commit及本批小文件远端回读在最终回复给出。
