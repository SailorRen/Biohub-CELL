# Codex续接：实测B的Colab运行与返回Kaggle提交路径

指令ID：BIOHUB_B_COLAB_RETURN_PATH_CONTINUE_20260922_V01  
原批次：BIOHUB_TWO_WAVE_20260922_V01（沿用B和原账本，不重开算法实验）  
仓库／执行分支：SailorRen/Biohub-CELL ／ codex/two-wave-four-submit-20260922  
交接基点：096d3cba3ae9cda83a0f76df132bcf5d7b200a9a。

## 1. 本次要实际回答的问题

用户授权继续测试：Kaggle普通GPU额度用尽后，能否用Open in Colab完成同一个B的验证，再通过官方支持的方式回到Kaggle正式评分。不要再只写建议、重复解释额度或查找上次JSON报错的确定根因；需要取得实际入口、资源或执行结果，不能推进时保存直接证据并交回Chat。

本指令明确替代旧任务中“必须证明错误由GPU额度造成才进入Colab”的条件。旧请求仍为REQUEST_UNCERTAIN；一次新的只读对账仍未发现B版本／排队／运行／预留后，即可按本指令继续有限后备测试。不得将其改写为请求从未发出、扣回预算或盲重试Kaggle Save & Run。

本次只测试B，不运行A/C/D、不复现0.951、不购买Pro或算力、不改最终选择。最多使用一个正式名额，其他名额保留。新训练、新Dataset、额外Kaggle普通GPU/整本CPU运行、TPU迁移、换账号绕额度、取消旧作业、自动监控均为0。

## 2. Mac同步与精确起点

使用Mac已配置工具，但先核对实际仓库remote和工作区；安全fetch执行分支，不只读main。有用户改动或分叉时用隔离worktree，不reset、stash、覆盖、强推或合并main。以GitHub最新账本为准，Mac缓存只有核对来源／哈希后才可复用。Git不可用可用GitHub连接器，不为环境问题重建实验。

必读文件（仓库根目录相对路径）：
- `AGENTS.md`、本指令。
- `reports/20260922_BIOHUB_TWO_WAVE_RESULTS.md`末尾B资源测试节。
- `experiments/BIOHUB_TWO_WAVE_20260922_V01/platform_ledger.json`。
- 同目录 `B/resource_events.jsonl`、`B/draft_readback.json`。
- 同目录 `B/candidate.ipynb`、`B/kernel-metadata.json`、`check_actual_csv.py`、`patch_support.py`、`known_output_hashes.json`、`A/formal_precheck.json`。
- 只在需要时读旧任务 `tasks/CODEX_20260922_BIOHUB_B_KAGGLE_FIRST_COLAB_FALLBACK_V01.md` 的固定输入、Colab适配与验收部分；不要执行它的正常SaveRun步骤。

无需重读全仓、重复14项小图测试或执行9月3日初始调研数量合同。材料被工具截断时取完整文件，不凭摘要拼代码。

|对象|精确身份／历史状态|
|---|---|
|账号／团队／比赛|sailorren ／ Sailor Ren ／ biohub-cell-tracking-during-development|
|唯一B草稿|sailorren/biohub-d960-l030p-20260922；Kernel135375343|
|B编辑地址|https://www.kaggle.com/code/sailorren/biohub-d960-l030p-20260922/edit|
|B源码冻结|4dca986a5bd61e3191ff790b74b505017678652e；原B/candidate.ipynb SHA256=03e4abd5c80b5724b959bc453352524e276bebcf9aa0c2ffa38f22442d3e2ceb|
|旧请求|TW20260922-B-SAVERUN-01；一次SaveRun返回Unexpected end of JSON input；不得重发|
|20:42旧对账|Version/SV/submission均null；版本历史为空，状态404，未见B活跃运行，GPU预留0|
|旧额度|GPU已用30:15:24.248／30h；正式名额剩3；这些都是9月22日历史观测|
|A，仅查已有状态|submission56456090；V1/SV351739212，已正式提交，不重提|
|DF960，仅查已有状态|submission56445846；SV351617874；旧UI已显示0.948，不重提|

B仍为D960-L030P：velocity0.5、det0.960、harmonic0.15、DeepCenter分裂门0.20，保留G1分类门；leaf阈值0.30，保护分裂父节点两支、真实最后帧和缺少真实模型概率的边，一次快照不级联。不叠加A的0.25、F1、gshift、DivNet或新选参。算法源码不改，允许独立Colab启动包装及必要路径／依赖／设备数量适配。

## 3. 先做一次只读对账，随后继续，不困在旧错误

按Kernel135375343和精确slug查看版本历史、活跃事件、状态、GPU已用/预留、B正式列表；一次成组查询即可，不轮询等确定性。

- 若发现B已有版本且排队/运行：记录真实Version/SV，续接该作业，不启动Colab重复生产。若已普通完成则按原验收流程处理并最多正式提交一次。
- 若仍无B版本/活动/预留：追加NO_ACCEPTED_RUN_OBSERVED_AFTER_RECHECK，保留原REQUEST_UNCERTAIN和全部计数，进入下一步。这个观测支持继续后备测试，不是证明后台从未收到请求。
- 若身份/状态读取也失败到无法排除当前B作业：先做不启动GPU的入口检查并报告可见性缺口，不用新运行来试探。

已有浏览器网络记录可顺手保存脱敏后的HTTP状态/响应摘要；没有就写NOT_CAPTURED。禁止为了抓原始错误再点Save & Run。后备生产开始前再核对一次是否出现延迟B作业；若发现，停止新的生产动作并报告，不擅自取消任何旧作业。

## 4. 非运行保存与提交条件：允许实际试，不要求先保证成功

本轮优先核对这条官方路径，最多约15分钟主动操作；无需遍历全部竞赛论坛：

- 官方导出／导入说明：https://www.kaggle.com/product-announcements/470030
- 官方CLI说明：https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels.md
- CLI变更记录：https://github.com/Kaggle/kaggle-cli/blob/main/CHANGELOG.md
- Quick Save/GPU历史提醒：https://www.kaggle.com/discussions/product-feedback/440750
- 当前比赛要求：https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/overview/code-requirements

Chat本次读到官方main的kernels文档支持`--no-run`，但CHANGELOG将其列在Next；因此不能假定Mac已安装CLI支持或已正式发布到本机。先读本机`kaggle --version`和`kaggle kernels push --help`。本机明确支持才可用下面模式；没有该参数就用页面Quick Save，不默默删除参数或用旧SDK猜字段，也不为此安装未发布开发版：

```bash
# B_SAVE_DIR必须由本轮确认：完整固定B源码+真实存在的同一B元数据目录。
# 执行前核对metadata.id精确为sailorren/biohub-d960-l030p-20260922。
# 仅在本机help明确支持--no-run、意图已记账后执行：
kaggle kernels push -p "$B_SAVE_DIR" --no-run
```

最多先做一次同一B对象的非运行试存，用完整Kaggle版B源码及固定Inputs，不改成空Notebook。若当前UI明确不允许，则记录而不反复点击。保存前持久化唯一意图；返回后记录真实Version/SV、源代码回读、Inputs、保存类型、加速器配置、是否出现新普通运行及GPU快照。响应不明仍只读对账，不从CLI切浏览器再发一次。

然后查看该精确版本的提交入口，记录：
1. 是否被“必须completed version”限制；
2. 是否仅缺输出文件，以及官方是否提供绑定真实外部输出的方式；
3. 正式评分GPU/Internet/Inputs如何绑定。

只观察资格，不点击正式Submit来探路，不消耗正式名额测试无效版本。源文件/元数据的enable_gpu=true仅为配置证据，不能声称已验证隐藏评分GPU。历史工作人员说Quick Save可能导致评分无GPU，只是风险依据，以当前界面/接口事实为准；明确CPU-only则不提交本GPU代码。

如果只创建了代码版本且没有输出，记录NO_RUN_VERSION_SAVED_OUTPUT_MISSING，这不是算法失败，也不自动证明所有外部返回方式都不支持。非运行保存不会凭空生成CSV，Notebook单元outputs里的文字/表格也不等于平台持久化的submission.csv。

若需要真实Colab结果才能完成资格验证，可以先继续最小Colab检查；不要在这里要求“保证正式评分成功”才前进。若平台已明确仍强制要求一次无法进行的Kaggle普通GPU运行，保留该阻断，不进行完整Colab长跑；但仍可按第5节实测一次独立GPU可用性，分别回答两个问题。

## 5. 实际Open in Colab：先验证独立GPU和最小链路

从现有B编辑器使用`File → Open in Colab`；入口失败可把GitHub固定B源码导入Colab，不新建Kaggle候选。只保存一份默认私有Colab文件；只访问本任务文件，不公开共享，不挂载整个Drive。登录/验证码/OAuth新授权交给用户在页面处理，优先用无需广泛Drive授权的文件导入；不索取明文Token或代点付费授权。

确认连接Colab自己的托管运行时，不是Kaggle Jupyter Server/自定义远程服务器/Mac本地连接。可先在未连接状态检查数据初始化代码，准备好再申请一次GPU。记录账号（最小必要标识）、连接类型、GPU型号/数量/显存、torch版本和cuda可用性；没有GPU就保存原文并停止GPU步骤，不反复重连换卡。不要因免费账号没有计算单位就直接判定GPU不可用。

只读比较运行前后Kaggle用量；受其他并发作业影响时不能声称精确扣时为零。真正的Colab后台证据来自连接类型和运行环境，而不是网址或一次余额差。

固定输入直接下载到本人Colab临时磁盘，不全量拉到Mac：
- pilkwang/biohub-deepcenter-unet3d-center-prior-v1/5
- pilkwang/biohub-temporal-unet3d-seed314159-v1/2
- pilkwang/biohub-tracking-support-pack-50ep-v1/10
- sailorren/biohub-division-train-20260914/1（gate历史SV349707105）
- biohub-cell-tracking-during-development比赛数据。

原权重哈希以同批B断言和`experiments/BIOHUB_SCORE_TRIO_20260921_V01/batch_manifest.json`为准。先确认访问权限、下载清单/磁盘空间；优先官方Kaggle API/Kagglehub，固定版本不可偷换最新版。私有gate授权缺失就停在该输入，不重训或公开它。自动导出的初始化若会整库下载，先改为所需文件；全量生产仍需完整的既定测试和验证样本，不能因少下载目录而静默改变选参样本。

路径/依赖/单GPU适配写在`B/colab_adapter.py`或`B/colab_candidate.ipynb`，另记最小diff；原B不覆盖。不要仅因只有一张GPU改变batch、TTA、精度、权重或算法规则。必要包使用兼容版本；已知当前回放可能触发DeepCenter推理，记录实际阶段耗时，不称全部CPU-only。

执行必要导入、固定权重加载及一个最小真实批次；这是有限GPU冒烟，不是训练或完整诊断。若正式返回路径已明确阻断，只完成GPU可用性/轻量CUDA检查，不下载大模型和全量比赛数据。路径尚未闭合时，最多进行最小数据/依赖/真实批次检查，不把全量长跑当作证明路径的必要步骤。

主动环境排错最多约30分钟，不含正常下载等待；同一会话最多一轮明确的环境修复，不反复重装。失败保留异常和最小修复结果。需要购买、修改算法、丢输入或绕过权限才能继续则停止并同步。

## 6. 具备合理返回路径后，才做完整生产与正式提交

若当前官方机制允许真实输出和正确GPU配置绑定，且没有强制新增Kaggle普通GPU运行的阻断，允许在同一Colab会话完成一次B生产。无需预先保证未来分数或隐藏执行成功；完整CSV/参数/权重检查通过才使用正式名额。

沿用既有检查器和A预检去重，检查真实CSV、velocity0.5、leaf0.30、保护条件、实际删除及非纯编号变化。Colab检查另存`B/colab_output_check.json`并显式写backend=COLAB_HOSTED；不要让旧检查器的Kaggle产物说明冒充身份。原云端reader往返与Mac标准库解析可以复用，不新增对照推理/参数扫描。没有有效输出变化就不提交。

返回Kaggle时区分两份文件：Colab环境包装只负责外部验证；正式代码必须仍是完整Kaggle推理版B，Internet关闭，对当次真实输入重新预测，不包含外部下载凭据或Colab联网依赖。导入时核对源码与固定Inputs未被改成latest或丢掉gate。无实质代码变化时不为“回传”再重复导入原代码。

若平台确有保存真实外部输出的官方入口，允许把本轮Colab生成且验收过的真实CSV作为可见运行产物导入同一B；必要时只启一个Kaggle CPU交互会话用于文件传输/哈希，不执行B的模型或全流程。不得创建Dataset承载这些输出，不假定上传到input会自动变成output，不把这项CPU文件操作记录成GPU推理完成。

只有最终代码/真实输出绑定确有必要时，才允许第二次非运行保存（同一B最终版本）。这不是算法新候选或SaveRun重试；第一次已足够就不再保存。不存在正规输出绑定、保存强制改CPU、保存后仍不满足提交条件，或第二次保存也响应不明时，停止，不造更多版本。

禁止假CSV、空文件占位、冒用A/D960输出、硬编码可见样本、按隐藏运行标识跳过真实预测、篡改任务状态、绕过禁用按钮或私有后端字段。代码竞赛最终是代码在隐藏输入上运行，不是上传一份Colab CSV就已完成评测。

正式请求前核对实时剩余额度和同一B既有请求，原账本持久化唯一意图并同步一次。只用支持精确Notebook版本的code submission接口或当前官方UI，最多一次正式请求；返回不明只对账，不换入口补交。记录真实submission ID/Version/SV；UI受理但ID不可见则明确ID_UNAVAILABLE。观察到受理即可交付，不等8小时，不重提A/DF960。

## 7. 本次上限、记录与收口

|动作|本次允许的上限|
|---|---:|
|新增Kaggle候选／普通GPU SaveRun／完整CPU模型运行|0|
|同一B非运行保存|最多2次：入口试存1＋确需真实产物/最终代码绑定时1；不是必须用完|
|Colab私有Notebook／托管GPU会话／完整生产|各1，复用已存在者并扣除后续已发生动作|
|Kaggle CPU文件传输会话|仅有正式支持的实际需要时1；不运行完整Notebook|
|B正式提交|累计最多1次，计入原批4次总上限，其他2个当日名额不自动使用|
|训练／Dataset／购买／TPU／C/D／最终选择／旧作业取消／自动监控|0|

原批最近已用Notebook2、SaveRun尝试2、正式1；旧不明SaveRun保持已计账。非运行保存独立记operation=SAVE_NO_RUN及created_version/no_compute，不假称一次GPU运行；若原汇总包含版本保存则按既有口径同时记清，始终不能超过旧相关总上限。本指令只将旧替代保存上限明确为最多2次，不恢复普通SaveRun预算。跨日最多仍只提交B一次，额度以实际可用为准，未用额度不自动开启后续实验。

继续追加`B/resource_events.jsonl`和原`platform_ledger.json`。每个推进/阻断节点记录实际时间、后台、对象、请求是否发出、原文提示、最小修复、资源变化、保留产物及下一步。同类错误合并次数，响应/截图去除Cookie、Token、签名参数、无关个人信息；不提交完整网络HAR。入口检查和最小Colab检查结果分别写，不能一个失败就把另一个写成“不可行”。

结果只追加到`reports/20260922_BIOHUB_TWO_WAVE_RESULTS.md`的B章节。必要时保存`B/return_path_check.json`、Colab适配源码和真实预检。原数据、CSV、完整图、权重、大日志不入GitHub。阶段或阻断后同步原分支，固定commit回读新增小文件一次；不建立新合同/仪表盘，不循环验证回执。保留用户Mac工作区，不改main。

最终明确回答：
1. 新对账是否发现旧B延迟作业？
2. 非运行保存是否成功？实际Version/SV、计算状态及GPU绑定是什么？
3. Open in Colab是否导入成功、是否真实分配独立GPU、执行到导入/模型最小批次/完整生产哪一步？
4. 真实外部输出能否形成可提交版本？若不能，原文限制在哪一层？
5. 是否真正正式提交、精确身份/状态/原始Public、预算及GitHub报告commit？

可分别为NO_RUN_SAVE_BLOCKED、COLAB_GPU_CHECKED、INPUT_OR_ENV_BLOCKED、COLAB_VALIDATED_KAGGLE_SUBMISSION_BLOCKED、REQUEST_UNCERTAIN或SCORE_PENDING；文件交付完成、运行完成、正式评分完成分开写。会话结束不声称后台持续操作；保存必要结果后可断开本任务新建且已闲置的Colab会话，不关闭他人/旧任务会话。出现无法推进的情况，报告事实交回Chat，不自行购买或转第三个平台。
