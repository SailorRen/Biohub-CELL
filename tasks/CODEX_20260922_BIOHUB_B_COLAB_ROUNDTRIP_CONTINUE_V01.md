# Codex续接：B的Colab计算与Kaggle无普通GPU运行提交路径测试

指令ID：BIOHUB_B_COLAB_ROUNDTRIP_20260922_V01  
仓库／执行及交付分支：SailorRen/Biohub-CELL ／ codex/two-wave-four-submit-20260922  
交接基点：096d3cba3ae9cda83a0f76df132bcf5d7b200a9a  
沿用实验：BIOHUB_TWO_WAVE_20260922_V01；沿用唯一B，不另建算法批次。

## 1. 目标和本次修正

用户已授权继续实际测试：将同一个B导出到Colab自有托管GPU运行，再尝试通过Kaggle正式支持的方式保存完整推理代码并提交评分。目标是确认这条路径，而不是再次调查全部GPU政策或设计新算法。

本指令细化并替代旧任务的后备启动条件：只读对账仍未发现B版本、排队或运行时，可以继续测试Colab和无运行保存；不要求先证明旧JSON错误一定由GPU额度引起。旧请求仍保留REQUEST_UNCERTAIN及已用次数，不改成未派发，也不重发。不要在这一步再次把任务直接交回Chat。

Kaggle普通GPU Save & Run新增0次，不因余额恢复自动启动。允许同一B的非运行版本保存、Colab同一候选生产和最多1次正式提交，详细上限见第8节。失败后记录具体停点交回Chat，不购买算力、不迁移TPU、不换账号绕限、不启动A/DF960/C/D、不改最终选择。

## 2. 从最新GitHub续接，不依赖旧临时文件

用户在Mac，可复用本机已授权Git/CLI/SDK/浏览器，但先核对实际能力及登录账号。安全fetch原分支；用户工作区有改动就用隔离worktree，不reset、stash、覆盖、强推或合并main。只读以下必要文件，旧初始情报任务的阅读数量合同不适用：

- AGENTS.md、本指令。
- reports/20260922_BIOHUB_TWO_WAVE_RESULTS.md的末尾B停点。
- experiments/BIOHUB_TWO_WAVE_20260922_V01/platform_ledger.json。
- 同目录B/draft_readback.json、B/resource_events.jsonl、B/candidate.ipynb、B/kernel-metadata.json。
- 同目录check_actual_csv.py、patch_support.py、known_output_hashes.json、A/formal_precheck.json。
- 仅有疑问时补读旧任务tasks/CODEX_20260922_BIOHUB_B_KAGGLE_FIRST_COLAB_FALLBACK_V01.md，冲突按本指令处理。

B：sailorren/biohub-d960-l030p-20260922，Kernel135375343。冻结源码commit4dca986a5bd61e3191ff790b74b505017678652e；B/candidate.ipynb SHA256为03e4abd5c80b5724b959bc453352524e276bebcf9aa0c2ffa38f22442d3e2ceb，14个代码单元。现有草稿不用重新复制、重命名或无故重新导入。

B仅为D960加保护版leaf0.30，velocity0.5；det0.960、harmonic0.15、DeepCenter分裂门0.20、自有G1门保留。保护分裂分支、真实最后帧、无真实模型概率的边，一次性剪枝、不级联。不得加入gshift/DivNet/relative-rank或改成A的0.25；不关闭选择器后默认base。此次不同时做性能重构，必要环境适配单列diff。

固定输入：primary pilkwang/biohub-tracking-support-pack-50ep-v1/10；secondary pilkwang/biohub-temporal-unet3d-seed314159-v1/2；DeepCenter pilkwang/biohub-deepcenter-unet3d-center-prior-v1/5；gate输出sailorren/biohub-division-train-20260914/1，历史SV349707105；比赛biohub-cell-tracking-during-development。权重哈希从既有断言及experiments/BIOHUB_SCORE_TRIO_20260921_V01/batch_manifest.json读取，不用同名最新版替换。

历史A为submission56456090/V1/SV351739212；DF960为56445846/SV351617874。只读，不重复提交。B此前无Version/SV/submission，不能预设无运行保存后必为V1，必须记录真实返回。

## 3. 一次只读对账，结束旧请求悬置但不伪造终态

查看同一B的版本历史、当前状态、活跃作业及最新账本；同时记录实际GPU用量/预留、正式剩余额度、刷新提示和时间。旧值是30:15:24.248/30h、预留0、剩3个正式名额，不当作实时事实。

- 发现延迟出现的B排队/运行：续接已有作业，不开Colab重复生产、不再保存新版本。
- 发现B已普通完成：复核现有输出，合格则按原授权最多正式提交一次；无需再做Colab完整运行。
- 仍无B版本及活跃作业、无对应预留：追加NO_ACTIVE_B_OBSERVED_AT_RECHECK，旧请求仍保留REQUEST_UNCERTAIN。本次用户授权下继续第4、5节，不再等待“证明后台绝未收到请求”。
- 账号未登录或页面不可读：访问失败不能充当无作业证据；停止需要排重的外部计算，交付具体权限缺口。

不为复现JSON错误重发Save & Run。已有网络记录可以只读提取脱敏HTTP状态、响应类型及错误正文；没有就写NOT_CAPTURED，不重建整套接口诊断。后续若发现迟到的B作业，停止新的重复启动并记录，不擅自取消旧作业。

## 4. 实测不运行保存与提交入口，不把草稿提示当成最终结论

先核对本机kaggle --version与kaggle kernels push --help。2026-09-22读取的官方仓库Kaggle/kaggle-cli固定commit47354f35239a62293e0d62ebf9a2458e82d715a3：docs/kernels.md明确列出--no-run，但CHANGELOG.md仍列于Next。因此不能假定Mac已安装版本支持，也不为此升级整个环境。CLI不支持时使用网页Quick Save；不要删掉--no-run继续普通push。

允许在唯一B上先做一次真实、不执行单元的版本保存，以便检查无运行版本的实际状态、输出要求及加速器。保存前持久化独立请求ID、源码/元数据哈希、目标Kernel及操作类型；保留is_private=true、enable_gpu=true、Internet=false和固定Inputs。仅当本机帮助支持且目录内容已核对时，命令形式是：

```bash
# 在安全同步的仓库根目录；先记请求意图，只执行下面这一条写命令一次。
kaggle kernels push -p experiments/BIOHUB_TWO_WAVE_20260922_V01/B --no-run
```

网页路径则明确选择Quick Save，不勾选执行单元，不打开普通GPU交互会话。CLI与网页只选一个，不把后者当不明响应的重试入口。保存失败/响应不明时只读对账，不新建替代Notebook。

保存后读取真实Kernel/Version/SV、14个代码单元、Inputs、GPU设置、版本状态、Output页和该版本Submit入口。分别记录：版本创建是否成功；代码是否未运行；是否要求实际输出/已完成版本；GPU设置是否保存；隐藏评分GPU是否仍未知。配置显示GPU不等于隐藏worker已经实测使用GPU。

旧B草稿提示“no completed versions”只证明当时没有版本；无运行保存后可能仍受限，也可能不同，必须检查新状态。反过来，保存成功也不证明能提交。

若无运行版本仍缺输出，查看当前官方导入/保存输出路径及本机已安装SDK的code submission接口：实际输出是否能合法附带、是否允许只指定未来输出文件名，还是明确必须先完成Kaggle运行。页面按钮禁用且没有其他官方支持证据时，不调用隐藏接口强行绕过。

没有正式请求前，不把UI无文件提示记为正式提交失败或消耗名额。不得touch空CSV、复制A的CSV、编造completed状态或篡改配额。

## 5. 实际进入Colab：独立GPU与最小可达性检查

通过同一B的File → Open in Colab打开；入口失效时从GitHub固定源码导入一次。只保存一个本任务私有Colab Notebook；不使用截图中的其他Geometric Fusion作为母版。导出后核对源代码，自动插入的输入初始化单独审查，不假定固定数据版本、gate或输出会自动同步。

确认连接的是Colab自己的托管运行时，不是Kaggle Jupyter Server、Mac本地运行时或其他付费云项目。申请一次免费GPU会话，记录实际型号/数量/显存、torch版本及torch.cuda.is_available()。未分配GPU就保存原始提示，不反复断开重连换卡，不以“没有付费计算单位”推断已经试过。

以下最小检查可以在第4节提交资格仍未知时执行，不因资格暂未知永远停在计划：GPU分配、现有输入清单/大小/权限检查、必要导入和源代码路径检查。若第4节已证明无法提交，也仍可只做这一次小检查，回答“Colab能否提供算力”；但不下载大数据或启动完整生产。

账号登录、验证码、OAuth同意及敏感授权由用户处理；不读取明文密钥、不给聊天/GitHub保存Cookie、Token或完整环境变量。导回若要求广泛Drive授权，先请用户处理，或使用单一文件的本地导入，不能私自授予整个Drive访问。

数据/权重允许按合法权限直接获取到Colab临时磁盘，优先官方API/Kagglehub。先核对固定版本、下载清单、空间和必要大小，不全量搬比赛到Mac，不重训私有gate，不公开数据、不创建新Dataset。保留原验证/选参时必须保证原样本发现一致，不能少下载目录就静默换选参样本。未实际下载的文件不能记为存在。

B/colab_adapter.py或B/colab_candidate.ipynb只允许设备数量、文件路径、依赖安装兼容等变化，列出diff；不改权重、精度、阈值、batch、选择器、坐标/概率语义，不增加研究步骤。只有一张GPU时使用原单进程回退，不模拟第二张卡。依赖主动排查最多约30分钟、一轮最小修复，下载时间另记；需要算法重写、额外平台或付费时停止交回Chat。

## 6. 完整Colab运行与返回：只在存在可检验提交路径时推进

完整运行的启动条件不是“已证明一定提交成功”，而是：第4节已经形成精确无运行版本或明确的最终导入保存办法；有官方支持的代码提交入口，输出/加速器要求可满足或仅余一次正规请求确认；没有已确认的“必须再完整Kaggle GPU预跑”限制。仅凭猜测Quick Save万能，不满足条件。

具备上述条件：同一Colab会话做固定权重载入及一个真实小批次检查，成功后继续一次完整B生产。分阶段记依赖、下载、主推理、后处理及总耗时；不把调用DeepCenter的阶段笼统称CPU-only。不运行新训练、额外8视野诊断或性能扫描。使用现有B的必要流程，不新增回放。

对真实submission.csv和two_wave/production_receipt.json执行现有check_actual_csv.py，--arm B，--other-check指向A/formal_precheck.json。输出保存为B/colab_output_check.json；检查文案注明Colab产物，不冒称Kaggle完成版本。复核leaf0.30实际删除、velocity0.5、固定模型、真实样本覆盖、合法图及非重复。无有效变化就不提交，不放宽保护激活剪枝。

返回Kaggle时，最终保存的必须是能在Internet关闭时对当次比赛输入独立完整推理的B代码；Colab联网下载/授权初始化不能混入Kaggle必经路径。必要环境适配可以按运行环境选择路径，但不得按已知可见/隐藏样本特判跳过推理。保留原B，最终代码另存B/return_candidate.ipynb并同步差异。

若预先保存的版本代码与最终提交代码完全相同，直接复用，不再保存。确实需要导回适配后代码或通过官方流程关联真实输出时，最多再允许一次同一B的无运行保存；必须说明第一次与第二次的差异与必要性，不能反复试版本。输出只有在正规接口支持时才能附带，保持Colab来源；导入ipynb的文本outputs不等于上传了磁盘submission.csv。

仅在正规真实输出导入流程确实需要时，允许一个不超过10分钟的Kaggle CPU文件处理会话，用于检查/接收真实Colab文件；不运行神经网络、不执行整本、不保存“只复制CSV”的冒牌生产代码。没有该需求就不创建CPU会话。此操作不保证平台接受或隐藏GPU有效，必须回读最终代码/Inputs/加速器与输出绑定；若因此只能保存CPU评分版本，停止正式请求。

明确要求额外Kaggle完整GPU运行、无法绑定真实输出、无法保留所需GPU、Colab没有GPU/权限或输出失败时，停止对应后续动作，写清哪一关失败。不要用公开方案0.951或其他候选替代B凑测试。

## 7. 唯一正式请求与结果

实际Colab验证通过、完整Kaggle版本身份和所需配置可核对、正规code submission接口允许该版本时，最多正式提交一次B。若官方接口设计不要求预先产物，允许在已验证代码/输出后使用其明确支持的文件名参数测试；不能自行忽略接口明确要求的completed/output条件。隐藏GPU是否真正可用，若仅能由正式运行确认，就记录待确认，不声称提交前已实测。

先查最新团队额度及B是否已有提交，再把唯一request_id、候选源码、Kernel/Version/SV、文件名、真实Colab输出哈希、入口和时间持久化到原账本。SDK/CLI支持code submission才用，否则浏览器；只选一个入口，不用普通本地CSV提交代替。剩3次是旧观测，本轮最多用1次，另外两次不自动使用；跨日不增加授权。

响应不明同样计为一次正式请求并只读对账，不能用第二入口重试。取得真实submission ID后只读回查一次；无分数记SCORE_PENDING。UI已证实受理但数值ID不可见则专门标记，不借A/DF960 ID。即使受理，也不等于验证了隐藏GPU、8小时出分或提分；这些阶段分开写。无需等正式分数再交付，不新建后台监控。

## 8. 预算、逐步事件记录与收口

沿用platform_ledger.json。旧已用Notebook2、SaveRun尝试2、正式1保持历史；先扣本轮启动前的任何新进展。旧B模糊请求不能退回预算。本指令的新增上限：

|动作|新增上限|
|---|---:|
|Kaggle候选Notebook创建/Fork|0，仅Kernel135375343|
|Kaggle普通GPU运行、整本CPU推理|0|
|同一B不运行版本保存|最多2次，首次路径验证＋确有必要的最终返回；无差异则1次|
|Colab私有Notebook/GPU会话/完整候选生产|各最多1，旧任务已发生者扣除|
|Kaggle可选CPU文件处理会话|最多1次、10分钟，仅正规真实文件导入需要时|
|正式提交请求|最多1，B累计最多1；旧原批总上限4不变|
|训练、Dataset写入、购买、TPU、C/D、最终选择修改|0|

不运行保存独立记no_run_version_save_requests，不伪记成SaveRun完成，也不以不扣GPU为由漏记；本次最多2次是对旧替代保存上限的限定细化。任何已派发保存请求含错误/不明都计数；第二次不是第一次不明响应的重试额度。只可恢复已确认失败的本次环境小操作，不自动多次保存或多会话长跑。

继续追加B/resource_events.jsonl，记录每个关键状态变化、写请求、直接错误和最小修复：真实时间/时区、后台、Kernel/Version/SV或Colab文件标识、动作、是否派发、原始脱敏提示、必要HTTP信息、资源前后值、文件哈希、结果和下一步。同一重复只读错误合并次数，不对每次滚动/鼠标动作建报告，不伪造精确旧时间。

结果写原reports/20260922_BIOHUB_TWO_WAVE_RESULTS.md的新节；B/colab_roundtrip_result.json用一张检查表给出：无运行保存、Colab GPU、输入与依赖、完整生产、实际CSV、回传、正式受理，各自PASS/BLOCKED/NOT_RUN及直接证据。代码适配和小型检查摘要留B目录。原始CSV/图/权重/大日志/凭据不入GitHub。

阻断时必须说明：具体错误及时间、哪个阶段、尝试过什么、未尝试什么、哪个草稿/版本/产物仍可续用、已用预算、希望Chat决定的最小问题。不要只重复“GPU为0所以不能运行”，也不要为了完成声明继续新建任务或平台。

结束前保存必要产物，正常释放仅本次创建且已不需要的Colab/CPU会话；不取消已有A/DF960或他人作业。推送原分支，新增/变更小文件远端回读一次，保留历史回执，不循环证明。返回固定commit和报告路径。平台执行结果、交付完成、正式受理、最终得分四者分开。

## 9. 已核对的官方线索（不是提交成功证明）

- https://www.kaggle.com/product-announcements/470030 ：Open in Colab导出、Import Notebook的Colab/Link导回。
- https://www.kaggle.com/product-announcements/567740 ：Kaggle Jupyter Server仍是Kaggle后台，不是Colab独立算力。
- https://github.com/Kaggle/kaggle-cli/blob/47354f35239a62293e0d62ebf9a2458e82d715a3/docs/kernels.md ：--no-run含义。
- 同固定commit的CHANGELOG.md：--no-run列于Next，本机支持情况必须检查。
- https://www.kaggle.com/discussions/product-feedback/440750 ：旧工作人员回复提示Quick Save的输出/GPU问题；这是历史风险线索，不代替2026年本次实测。
- https://research.google.com/colaboratory/faq.html ：免费GPU动态分配，不保证型号/时长。

本任务交付不代表已创建Kaggle版本、启动Colab或发出正式提交。执行者必须从首个未完成步骤实际推进。
