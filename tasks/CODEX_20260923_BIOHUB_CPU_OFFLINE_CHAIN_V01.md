执行 BIOHUB_CPU_OFFLINE_CHAIN_20260923_V01。

本消息正文可直接作为执行指令保存，不需要等待附件。
目标：补齐离线部署和真实短片段的CPU调用流程。
不修改队友母版，不正式提交，不重复仅测试主编码器。

一、同步与隔离

仓库：SailorRen/Biohub-CELL
来源分支：codex/cpu-small-probe-20260923
交接基点：cdccdefeb6b1e7fb1fcaf3a73ee205d3ef6ba3e3
独立执行／交付分支：codex/cpu-offline-chain-20260923

安全同步并检查后续更新，使用独立worktree。
不覆盖用户改动，不reset、stash、强推或合并main。

先把本指令保存为：
tasks/CODEX_20260923_BIOHUB_CPU_OFFLINE_CHAIN_V01.md
推送独立分支并回读，再操作平台。

读取上轮报告、probe.py、prepare.py、result.json、
runtime_receipts.json、source_hashes.json、saved_version_readback.json，
以及冻结B源码、输入配置和实际调用模块。

冻结B：
experiments/BIOHUB_TWO_WAVE_20260922_V01/B/candidate.ipynb
SHA256：
03e4abd5c80b5724b959bc453352524e276bebcf9aa0c2ffa38f22442d3e2ceb

A/B原源码、正式提交、队友母版／副本／共享权限、
原批账本和最终选择全部不动。

二、本轮预算

1. 复用旧CPU诊断Notebook准备部署文件：
   sailorren/biohub-cpu-small-probe-20260923
   Kernel135480603

历史V1/SV352060904保留不动。
新增CPU交互会话最多1次，联网准备与转换合计最多30分钟；
带Output的Quick Save最多1次，完成后释放会话。

2. 新私有离线Notebook最多1个：
   biohub-cpu-offline-chain-20260923

CPU/None、Internet off、无持久化。
Save & Run All最多1次，在干净会话中执行安装、加载和测试。
整次离线作业预算120分钟，设置硬超时并逐阶段保存结果。

全批最多一次明确的最小工程修复，不增加上述会话和运行次数。
GPU、Colab、完整视频／全测试集生产、训练、
正式提交、Dataset写入、购买、共享变更全部0。

新增操作单独记本实验账本，旧消耗不清零。
保存或运行响应不明，只读对账，不换入口盲重发。

三、固定输入与算法

固定挂载以下输入并核对实际版本和权重哈希：

比赛：
biohub-cell-tracking-during-development

Primary及离线依赖：
pilkwang/biohub-tracking-support-pack-50ep-v1/10

Secondary：
pilkwang/biohub-temporal-unet3d-seed314159-v1/2

DeepCenter：
pilkwang/biohub-deepcenter-unet3d-center-prior-v1/5

Gate：
sailorren/biohub-division-train-20260914/1
历史SV349707105

保持B的velocity0.5、L030P0.30及原模型、阈值、归一化、
空间下采样、实际batch、增强集合、融合和保护规则。

只允许CPU设备、推理后端、路径及短片段诊断入口适配，
保存diff，不伪造CUDA可用。

默认主编码器使用已验证的OpenVINO FP32；
secondary、DeepCenter、gate和关联可保留PyTorch CPU。
不要求所有模型都转OpenVINO，不量化，不增加多后端研究。

四、先固定真实样本，再准备离线文件

主片段沿用44b6_0113de3b，从开头取连续16帧。
先从源码确认时间窗口、最短轨迹和上下文要求；
不足时，在首次模型运行前扩到满足条件的最小长度，最多32帧。
不降低原时间门槛，不额外缩小空间尺寸。

记录原视频T轴长度、原帧号、片段范围和坐标映射。
截取末端不是真实视频末帧，保留原last-frame信息，
明确标识截断边界影响，不把片段结果冒充全视频结果。
必要临时切片放/tmp，不放将被保存的/kaggle/working。

另从已挂载公开数据中，最多选择一个原生空间尺寸不同的真实窗口。
找不到就记SHAPE_GENERALIZATION_NOT_COVERED；
不通过裁切、缩放或随机张量制造“不同尺寸真实样本”。

上轮IR没有保存进版本Output，不能假定仍可下载。
复用转换代码重建主编码器IR：
compress_to_fp16=False，显式CPU FP32，
回读权重／输出类型和实际执行精度，不使用BF16、FP16或INT8。

保留上轮TracerWarning，检查输入shape。
必要时按实际shape转换／编译或明确回退PyTorch CPU，
记录回退次数；不能按样本ID或公开／隐藏身份特判。
简单reshape不能当作尺寸条件分支已验证。

优先原镜像已有包和support离线wheels；
仅从官方PyPI补齐必要wheel及依赖，固定版本、文件大小和哈希。
不要升级整套环境，不重新使用不固定版本的pip install。

将IR、必要wheels、安装脚本和manifest保存到cpu_bundle目录。
只保存部署文件，不打包原始视频，不重复公开原始权重。

一次带Output的Quick Save后，
从精确Version/SV核实文件存在并校验哈希。
新离线Notebook通过Add Input挂载这个精确准备版本，
不新建Dataset，不依赖临时会话或“最新版”。

五、在干净断网会话中运行两条短片段流程

离线Notebook从头Save & Run All，不执行联网准备单元。
安装仅用已挂载wheels，使用--no-index和--find-links。
记录精确版本Internet=false、CPU设置、包版本及首次加载结果。
缺依赖就记录失败，不开启网络继续运行并称为离线成功。

同一真实片段、同一固定诊断配置，顺序运行各一次：

参考：原模型的PyTorch CPU FP32。
候选：主编码器OpenVINO FP32，其余明确使用PyTorch CPU。

两边使用相同预处理和CPU attention适配，输出目录分开；
各自计算，不用参考最终图或CSV替代候选推理。
这不是与历史GPU生产版本的等价性测试。

必须接入实际启用的：
primary、secondary、TTA、正反向关联与融合、
DeepCenter、gate、图优化、短轨救援、L030P和CSV写出。

不关闭模块、减少增强次数或修改阈值来缩短运行。
逐模块记录加载、真实调用次数、输入shape、耗时和作用对象。
仅import或load不算完成推理。

条件模块没有触发就写NOT_TRIGGERED。
存在合法真实候选时，可追加一次独立模块调用并单列证据；
不伪造节点、概率或分裂来强行触发。

本轮不运行需要完整多视野数据的全量选择器。
固定B已有配置作为诊断夹具：
selector_mode=FIXED_DIAGNOSTIC_CONFIG。
选择器代码不改，完整选择器及生产配置选择仍NOT_VALIDATED。
不得把固定夹具说成选择器已经验证，也不能暗中挑更快配置。

必要模块无法执行时保留具体错误和已完成部分，
不以静默跳过、空输出或默认常数代替。

六、验收实际输出，而不是只看程序是否退出成功

数值沿用：
atol=1e-4、rtol=1e-3、equal_nan=False。

报告输出shape、有限值、最大／平均绝对误差、相对误差，
以及检测节点／坐标、关联阈值、DeepCenter/gate判断和最终图变化。
不隐藏近零相对误差，不因失败放宽阈值。
最终图比较去除节点ID和行顺序影响。

生成：
diagnostic_reference.csv
diagnostic_cpu.csv

不得命名或宣称为可正式提交的submission.csv。

复用原check_actual_csv.py和patch_support.py中的结构检查：
列定义、坐标与哨兵、端点、时间方向、入出度、
重复边、规范化图摘要和官方reader往返。

原验收器不改；把结构检查提取到本轮诊断校验器。
样本范围明确使用本轮sample_manifest。
不伪造原生产任务身份、完整覆盖或production_receipt字段。

短片段不需要满足正式候选的has_effect和归档去重门槛：
L030P真实删除0条可以如实记录，
不能为通过检查修改规则制造差异。

数值allclose不能覆盖图或决策差异。
必要分支没触发、尺寸没覆盖、选择器未测试，均保留缺口。

七、测量完整片段成本，不单独追求编码器加速比

分别记录加载、转换、编译、预处理、双模型、
增强／融合、条件模块、图处理和CSV写出时间。

顺手统一两后端实际有效线程及计时边界，
包含或排除相同的输出复制操作。
仍无法一致就保留观测值，不报告严格加速比，
但不因此停止兼容性验证。

记录实际CPU配额、线程、可用内存，
以及明确测量范围的峰值RSS。

只报告这个片段的实际墙钟时间和阶段占比。
不由单个编码器速度或简单帧数比例，
宣称整个隐藏测试集满足比赛时限。

每个阶段立即落盘。超时保存最后成功阶段和已覆盖范围，
不继续追加会话或运行。

八、交付

独立目录：
experiments/BIOHUB_CPU_OFFLINE_CHAIN_20260923_V01/

报告：
reports/20260923_BIOHUB_CPU_OFFLINE_CHAIN.md

保存必要适配代码／diff、样本清单、部署文件manifest、
运行回执和结果，不新增庞大治理框架。

IR及wheels保留于私有Kaggle精确Output。
GitHub仅保存代码、manifest、哈希与小型证据；
原始视频、权重、完整张量、诊断CSV和凭据不入GitHub。

推送独立分支，从固定commit回读变更小文件一次。
报告remote HEAD、实际一致数和worktree状态。
不自动清除上轮NEEDS_HUMAN_REVIEW，
逐项说明本轮真正补齐了哪些证据。

最终回复：
离线安装／加载是否成功；
两条短片段流程是否实际执行；
模块覆盖与未触发项；
数值和图差异；
完整片段耗时、内存与CSV结构检查；
实际Version/SV、部署文件位置、预算和GitHub固定commit。

本轮最多得出“已测短片段CPU调用链通过”；
不能宣称完整CPU B、GPU等价、隐藏集时限或正式分数已验证。
通过后只提出下一轮单视频验证建议，不自动运行或提交。
