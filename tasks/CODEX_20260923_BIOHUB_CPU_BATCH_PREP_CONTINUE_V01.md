# Codex：改用 CPU 批量准备，续接离线短片段验证

任务ID：BIOHUB_CPU_BATCH_PREP_CONTINUE_20260923_V01
仓库：SailorRen/Biohub-CELL
执行／交付分支：codex/cpu-offline-chain-20260923
交接基点：eedc1c38befb87ba47bee86a019f27f8914258b5
沿用实验：BIOHUB_CPU_OFFLINE_CHAIN_20260923_V01

## 1. 目标与本次授权

用户已同意：让已准备代码实际执行一次。准备阶段由“交互CPU会话＋Quick Save”改为一次非交互CPU Save & Run；部署包验收通过后，继续原定的一次干净断网短片段验证。不是再做一轮连接调查，也不是重新设计模型。

本指令替代旧任务的准备启动方式及“交互会话额度耗尽后必须停止”的限制，其余样本、算法、隐私和验收边界保留。无需为本指令内的两阶段执行再次申请授权。

本次允许：
- 既有准备Notebook新增CPU Save & Run最多1次，准备代码执行硬超时30分钟。
- 新私有离线Notebook最多1个、CPU Save & Run最多1次，沿用旧任务尚未使用的额度；离线安装和两条短片段流程合计硬超时120分钟。
- 新增交互会话、Quick Save、GPU、Colab、完整视频／全测试集生产、训练、正式提交、Dataset写入、购买、共享变更、最终选择修改均0。

旧失败交互会话仍记1次，不退账、不清零；旧Quick Save步骤停用。原尚未使用的最小工程修复额度保留1次，但不产生额外平台运行／版本额度。先完成本地必要开发和检查再派发；失败后不重跑。

## 2. 同步与排重

安全fetch上述分支，确认包含基点；远端有更新先读并排重。沿用隔离worktree，不覆盖用户改动、不reset/stash、强推或合并main。不修改A/B生产源码、队友母版／副本／权限、two-wave原提交账本。

将本全文保存为：
tasks/CODEX_20260923_BIOHUB_CPU_BATCH_PREP_CONTINUE_V01.md
先提交、推送该研究分支并固定回读，再操作平台；正文就是任务原文，不依赖附件。

只读AGENTS.md、原离线链任务、最新报告和以下实验目录：
experiments/BIOHUB_CPU_OFFLINE_CHAIN_20260923_V01/
重点读取ledger.json、session_release_evidence.json、preparation.ipynb、preparation_cell.py、prepare_bundle.py、convert_bundle.py、install_offline.py、chain.py、diagnostic_validate.py及它们实际依赖的source／清单。

只读确认账号sailorren、旧准备会话已终止、当前没有本任务重复作业。已存在新批量作业就续接；已有合格部署Output就复用。查询失败不能当作“无作业”。

## 3. 只修启动封装，确保空目录能执行

复用已有脚本，构建自包含的preparation_batch.ipynb及匹配的kernel-metadata.json，放在本实验下的prepare_batch目录。目标仍是：
sailorren/biohub-cpu-small-probe-20260923
Kernel135480603
历史V1/SV352060904只作历史证据，不预设下一Version／SV。

Notebook从第一单元开始自行创建工作目录、写出执行脚本和所需清单，再启动准备程序。不得依赖Console预写文件、旧内核变量、本机路径或已释放会话中的IR。

派发前在本地临时空目录仅检查文件展开／哈希、Python语法、入口与相对路径；不安装完整模型环境、不跑模型。确认source_hashes.json、dependency_specs.json、source目录、安装与诊断脚本都能由提交源码生成，并且部署包包含后续离线所需内容。已有文件不要重复开发。

允许将当前已核验的小代码文件内嵌进Notebook；不内嵌原始数据、权重或凭据。清除复制来的旧执行输出与执行计数；不能把旧成功日志当成本轮结果。代码就绪后同步源码、差异和实际哈希。

固定B原件SHA256：
03e4abd5c80b5724b959bc453352524e276bebcf9aa0c2ffa38f22442d3e2ceb
不改其算法。实际环境、输入和权重仍需在本次worker重新核验，不能以本地编译代替。

## 4. 一次CPU批量准备

设置：Private、Accelerator=None、GPU/TPU关闭、Internet on、无持久化；沿用可用的原CPU镜像并记录实际版本。

挂载比赛biohub-cell-tracking-during-development，以及：
pilkwang/biohub-tracking-support-pack-50ep-v1/10
核对真实挂载路径，禁止递归遍历整棵比赛目录寻找依赖。

优先使用已安装且已授权的官方CLI普通kernels push发起批量运行；先看本机help、核对目标id和全部metadata。CLI与网页Save Version→Save & Run All只选一个入口，不先手动Run All，不加--no-run，不打开交互CPU会话测试连接。

唯一请求ID：CPU-BATCH-PREP-01。派发前写本实验ledger并同步意图；只发一次。若网页连接仍不好，但CLI实际可用，可在任何写请求派发前选择CLI；派发后响应不明，不换入口重发。

运行必须完成：原依赖准备、固定官方PyPI补充包获取、真实权重校验、主编码器FP32转换、IR落盘／重载推理、必要文件清单生成。保持compress_to_fp16=False及显式CPU FP32，不额外缩小输入，不量化或修改模型。

复用原依赖约束并记录实际安装版本；收齐离线所需wheels及传递依赖，不升级整套环境。准备与离线阶段尽量绑定同一实际CPU镜像，列明哪些基础包由镜像提供；不能把“联网会话里已安装”误当成部署包已具备。

需要保留的文件放/kaggle/working/cpu_bundle，包括IR、wheels、requirements.lock、bundle_manifest.json、source_hashes.json、sample_manifest.json和离线诊断所需代码。manifest记录部署文件大小及SHA256。原始视频、临时切片放/tmp，不作为部署Output保存。

第一单元立即输出并落盘带本次任务ID／源码摘要的STARTED回执；每阶段flush日志并保存小回执。父进程为整段准备设置统一30分钟硬超时，子进程共享剩余预算；错误／超时尽可能落盘后非零退出，不捕获失败再打印成功。

批量任务受理后只读查精确作业状态、版本日志和Output。编辑器Starting或断连不作为重新启动理由；若批量worker本身失败，保存该作业直接错误，不把它猜成CPU配额或模型不兼容。

## 5. 部署Output通过后，直接接离线运行

准备阶段放行条件：本次批量版本已完成；实际日志证明准备程序执行；所需部署文件位于同一精确Version／SV的Output；manifest与真实文件哈希一致。仅版本创建、Running或源码中有成功字符串均不够。

从精确版本读取／下载核验小清单，必要时在后续挂载端复算IR／wheel哈希，避免为校验把大文件搬到Mac。准备未通过就停止，不创建离线作业。

通过后在原剩余额度内创建或复用唯一私有Notebook：
sailorren/biohub-cpu-offline-chain-20260923
挂载刚完成的精确准备Output，不用Latest，并核对五项原固定输入：
- 比赛：biohub-cell-tracking-during-development。
- primary／离线依赖：pilkwang/biohub-tracking-support-pack-50ep-v1/10。
- secondary：pilkwang/biohub-temporal-unet3d-seed314159-v1/2。
- DeepCenter：pilkwang/biohub-deepcenter-unet3d-center-prior-v1/5。
- gate：sailorren/biohub-division-train-20260914/1，历史SV349707105。

Settings及实际保存版本必须为CPU、Internet off、Private、无持久化。离线入口自行加载挂载包，从本地wheels执行--no-index --find-links安装；缺依赖即报错，不开启网络补包。新增进程实际import和加载模型，不复用联网准备进程。

唯一请求ID：CPU-OFFLINE-CHAIN-01。意图同步后，仅Save & Run All一次；不先交互试跑，也不再Quick Save。通过准备检查后继续本阶段，不只交“准备完成”后再次等待授权。

## 6. 沿用短片段测试，不扩大生产范围

保持sample_plan和原诊断代码范围：44b6_0113de3b的0–15帧，原帧号、空间分辨率、下采样、归一化和时间门槛不变；重新核对实际T轴，片段末端不冒充真实视频末帧。最多一个额外原生不同尺寸窗口，找不到就标记未覆盖，不造假尺寸。

参考PyTorch CPU FP32与候选OpenVINO主编码器＋其余PyTorch CPU各独立运行一次。保留原启用的secondary、TTA、正反向关联／融合、DeepCenter、gate、图优化、救援和L030P；不关闭耗时模块求通过。

只使用已冻结诊断配置，明确selector_mode=FIXED_DIAGNOSTIC_CONFIG；完整选择器不在本轮验证范围。条件模块无触发写NOT_TRIGGERED，模块根本未运行写NOT_RUN，不伪造候选触发。

统一可比线程及计时边界；仍不一致就不声称严格加速比，不另开性能扫描。逐阶段记录真实调用、耗时、内存，以及数值／检测／关联／最终图差异。误差阈值沿用atol=1e-4、rtol=1e-3、equal_nan=False，不放宽。

生成diagnostic_reference.csv和diagnostic_cpu.csv，用现有诊断校验器检查真实片段覆盖、schema、坐标、端点、时间方向、入出度、重复边、规范化图及官方reader往返。L030P删除0条可如实记录，不制造差异；数值接近不覆盖实际图差异。不得命名或声称为正式submission.csv。

离线安装与双路径运行统一120分钟硬超时，逐阶段落盘。不得用片段耗时简单外推隐藏全量时限。准备通过不等于离线通过，短片段通过不等于完整CPU B通过。

## 7. 停止与交付

本轮最多两个新CPU批作业：准备1、离线1。响应不明只读对账；确认失败／超时保留日志，不再次派发。只允许终止已唯一识别的本次超时作业及子进程，不取消其他作业。排队／Running时保留精确ID和停点，不把页面等待当成算子耗时，不建立定时器或会话结束后的自动续跑。

沿用本实验ledger.json、resource_events.jsonl、result.json及报告：
reports/20260923_BIOHUB_CPU_OFFLINE_CHAIN.md
保留旧连接失败证据，追加本次实际状态与预算。只增加必要启动Notebook、代码差异和小回执，不新建治理框架。

IR／wheels留私有Kaggle精确Output；原始视频、权重、张量、诊断CSV和凭据不入GitHub。源码、清单、哈希、证据和报告推送同一研究分支，固定commit回读一次，报告remote HEAD、实际匹配数、worktree状态。

NEEDS_HUMAN_REVIEW不因机械检查通过而自动清除；逐项说明实际补齐和未覆盖内容。无论停在哪一阶段，返回准备与离线两项各自的Version／SV、真实状态、Output绑定、执行到的模块、差异、片段耗时／内存、直接错误和预算。

本轮不正式提交，不自动进入单视频验证。最终最多声称“已测短片段离线CPU调用链通过”，不能宣称GPU等价、完整CPU B、隐藏集时限或Public提分。