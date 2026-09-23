# BIOHUB CPU 真实小样本试验（2026-09-23）

结论：**核心编码器两份真实输入数值初筛通过，FP32转换、磁盘保存、重载及实际推理成功；一次真实关联调用通过。性能对照存在实际线程差异，因此不是严格同线程速度比较。完整CPU B、离线部署和正式提交均未验证。**

事实类型：运行值为 `MEASURED`；源码核查为 `SOURCE_CODE_VERIFIED`；下一轮建议为 `INFERENCE`。本轮未修改A/B、队友母版、权限、原提交账本或最终选择。

## 身份、来源与预算

- 独立分支：`codex/cpu-small-probe-20260923`；来源基点 `4fc1703fea6e4dbef254ce99b8113f9115409f88`。干净隔离worktree执行，canonical分支保留不动。
- 指令原文及冻结合同先发布于 `0c55ebdd78ae6ed53936408ec35a8a5b3b584172`，2个文件固定SHA远端字节回读通过后才写平台。
- [诊断Notebook固定V1](https://www.kaggle.com/code/sailorren/biohub-cpu-small-probe-20260923?scriptVersionId=352060904)：Kernel **135480603**，V1，SV **352060904**，Private、CPU/None、Internet On。
- 冻结B源码 SHA256：`03e4abd5c80b5724b959bc453352524e276bebcf9aa0c2ffa38f22442d3e2ceb`，原14代码单元没有执行或修改。
- 输入仅比赛 `biohub-cell-tracking-during-development` 与 `pilkwang/biohub-tracking-support-pack-50ep-v1/10`；UI明确Pin to version10，DatasetVersionId17804310。五个实际Python源文件哈希与B断言完全相符，见source_hashes.json。
- 云端实际权重 SHA256：`12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771`，匹配冻结断言。Mac仅下载必要小源码与165字节配置，没有下载模型或视频。
- 消耗：新私有Notebook **1/1**，CPU交互会话 **1/1**，末尾Quick Save **1/1**，最小修复 **1/1**；GPU、Colab、Save & Run、完整视频、训练、正式提交、Dataset写入、购买、共享变更、取消其他作业均 **0**。

## 实际执行与故障

时间均为上海时间（回执原文为UTC）。14:58:44派发CPU会话；14:58:58开始准备。初版用rglob定位support，递归扫到比赛目录，15:02:39中断，保留原始 `KeyboardInterrupt`、221.072秒与traceback。没有加载模型，未另开会话。

唯一最小修复是直接使用已核实的support挂载路径；控制台首次粘贴因换行转义报 `SyntaxError: unterminated string literal (detected at line 12)`，未执行任何修复或模型代码，修正传输转义后同一修复于15:07:30执行。剩余准备超时373.56秒，没有重置15分钟总预算。一次离线wheels安装补足zarr，官方PyPI安装OpenVINO一次。15:07:46准备完成，从CPU派发算542秒（9分02秒），其中修复后的准备16.041秒。

15:08:05唯一测试派发，父进程硬超时2700秒。15:08:51完成全部测试，测试进程耗时45.976秒。转换期间有原始TracerWarning：`Converting a tensor to a Python boolean might cause the trace to be incorrect`，对应 `if x.shape[2:] != skip.shape[2:]`。第二份同尺寸真实窗口已检验；其他尺寸泛化未验证。

末尾一次Quick Save，Save Output=Never，仅保存执行记录，不保存磁盘IR模型，不触发整本重跑。界面Quick Version/Ran in0seconds，查看页9秒为快照打包，不是推理耗时。15:12前仅停止本次会话，菜单从Stop session变为Start session，重启控件禁用。

CLI以owner/slug/1只读回收时403；按下载菜单显示的owner/slug命令成功回收唯一V1源码与元数据。CLI源码无单元输出，不能把源码中的成功字符串当测量证据；另从已保存V1渲染正文独立解析13个RECEIPT阶段，与运行时小回执13/13逐字段完全一致。

## 真实样本与保持不变的配置

按ID排序的4个公开test视频中取首个 `44b6_0113de3b`，原shape `[100,64,256,256]`；预先冻结窗口0–1、49–50帧。保持原window2、downsample `[1,4,4]`，实际输入均为 `[1,2,64,64,64]`，没有额外缩小空间。

使用原加载/预处理函数，q001=26.222222222222225、q999=2145.000000039654，归一化 `(x-q001)/(q999-q001+1e-6)` 后仅clamp最小值0。实际encode batch1；原CLI的unet_batch_size4在原predict_video中未用于该encode调用。保持D960检测阈值0.96、原pool3μm和edge阈值0.48；后者来自冻结B的环境覆盖，并非PredictConfig默认0.5。仅设备改CPU，原函数/类由哈希已验证源码AST提取，未导入训练或全视频入口。

编码器全部输出都保留：关联特征 `[1,2,32,64,64,64]`，两份检测logits各 `[1,1,64,64,64]`，两后端全部FP32、有限值。使用eager attention便于追踪，PyTorch参考和转换采用同一路径；没有伪造CUDA。

## 数值与决策

固定工程阈值 `atol=1e-4, rtol=1e-3, equal_nan=False`，未放宽。相对误差分母 `max(abs(PyTorch),1e-12)`。以下6项全部PASS，不是比赛评分容忍度，也不证明GPU等价。

| 窗口 | 输出 | 最大绝对误差 | 平均绝对误差 | 最大相对误差 | 平均相对误差 | allclose |
|---|---|---:|---:|---:|---:|---|
| 0–1 | 关联特征 | 1.07288361e-05 | 9.22552315e-07 | 1.15137 | 1.10243172e-06 | PASS |
| 0–1 | 检测logits帧1 | 9.15527344e-05 | 8.52625924e-06 | 0.00798871334 | 9.48621635e-07 | PASS |
| 0–1 | 检测logits帧2 | 7.82012939e-05 | 8.61474506e-06 | 0.0094246405 | 8.87148835e-07 | PASS |
| 49–50 | 关联特征 | 1.16825104e-05 | 9.36070662e-07 | 4.26117013 | 1.25542508e-06 | PASS |
| 49–50 | 检测logits帧1 | 8.58306885e-05 | 8.66342858e-06 | 0.0197410828 | 9.40522383e-07 | PASS |
| 49–50 | 检测logits帧2 | 9.15527344e-05 | 8.71867685e-06 | 0.00809603377 | 8.58290642e-07 | PASS |

最大相对误差在近零特征上可达4.261，不能隐去；绝对与联合allclose条件仍通过。原检测后处理得到帧0/1/49/50分别230/228/282/281个节点，两后端计数和坐标集合完全一致，坐标增减均0。

关联调用使用真实49–50帧282与281个节点、原特征索引、真实mask和原predict_edges，两份编码器特征都交由同一个PyTorch CPU关联模块处理。边概率shape `[282,281]`，最大绝对误差1.668930054e-6、平均8.317858954e-10，最大相对1.498373856e-5、平均1.801328465e-6，allclose通过；0.48阈值判断变化0。两次关联耗时0.642682/0.113122秒，顺序运行、首次初始化不同，不当作关联加速比。未做正反向融合。

## 转换、性能及内存

运行环境：Intel Xeon @2.20GHz，4个逻辑CPU、affinity4、cgroup CPU配额4核，内存上限32212254720字节=30GiB。Python3.12.13、PyTorch2.10.0+cpu、NumPy2.0.2、zarr3.2.1、OpenVINO2026.4.0-22959。实际CUDA=False。

| 阶段 | 实测秒 |
|---|---:|
| 权重哈希、构建与加载 | 0.397652 |
| 两份真实输入预处理与加载 | 0.410987 |
| OpenVINO转换 | 18.608920 |
| IR落盘 | 0.029085 |
| 磁盘IR重新读取 | 0.012521 |
| CPU编译 | 0.180005 |
| PyTorch首次/唯一预热 | 3.310046 |
| OpenVINO首次/唯一预热 | 2.576945 |
| PyTorch暖后3次 | 2.984639 / 3.090676 / 3.058227 |
| OpenVINO暖后3次 | 2.341619 / 2.303237 / 2.353857 |
| 暖后均值，PyTorch/OpenVINO | 3.044514 / 2.332904 |

转换追踪额外调用forward3次，计入转换时间，单列且不混作暖机/计时次数。两个后端各一次显式预热、三次计时，没有再次重复整个测试。

**性能门禁缺口**：请求均4线程、batch1，PyTorch实际4线程/interop1；OpenVINO编译属性实际返回INFERENCE_NUM_THREADS=2、NUM_STREAMS=1，不能报告同线程加速。另外PyTorch首两窗口测量含numpy复制，后两次计时只返回tensor，OpenVINO均复制输出，计时边界不完全一致。保留观测值，不补跑、不据此下完整性能结论。runtime09中的threads4是请求值，以07编译属性2为准。

峰值RSS=2068888KiB=1.973GiB，为同一测试进程持有两后端模型、参考输出及转换中间物的累计峰值；不是单后端峰值或整台VM总内存。

IR以 `compress_to_fp16=False` 保存，XML115562字节、BIN5983712字节；重载常量类型仅float32/int32/int64，3个输出float32；编译回读INFERENCE_PRECISION_HINT=float32，CPU执行已完成。没有BF16/FP16/INT8。大模型仅留本次临时运行环境，没有进入GitHub。网络仍On，因此**磁盘重载成功，但隔离网络的离线部署NOT_VERIFIED**。

## 结论边界与下一轮

未覆盖secondary、DeepCenter、gate、完整选择器、D4 TTA、正反向融合、全视频图优化、GPU等价、完整CPU B或正式评分；无CSV，无正式提交。

值得在另行授权后做完整CPU兼容验证（INFERENCE）：本次证明主编码器数值、检测决策以及一个关联对有可行基础。下一轮首先统一真实线程数及计时边界、验证断网依赖重载，再处理未覆盖模块。不能由3秒编码器外推完整B满足比赛时限；本轮不估计隐藏全量时间，也不自动启动下一轮。

## 产物与验收

独立实验目录包含prepare.py、probe.py、candidate.ipynb（修正路径后的诊断入口，未另行平台执行）、minimal_repair.py、saved_source_v1.ipynb（平台原始源码导出，无输出）、kernel-metadata.json、runtime_receipts.json、saved_version_readback.json、execution_receipt.json、result.json及source_hashes.json。初版路径错误和修复均保留，不把修正版源码声称为原保存版全文。

未上传原始视频、权重、完整张量、IR模型、CSV或凭据。交付固定commit及GitHub字节回读结果在最终回复给出。原生产目录与原账本相对来源基点必须无差异。

冻结合同SHA256 `af2588c7334d09ffb7a333adad7130e672a72bc88d21078deffcb2622ddc289d`；验收工具可机械检查源码哈希、结果/报告与Git，真实平台语义保留manual门禁，不能用本地PASS冒称无限制COMPLETED_VERIFIED。平台13阶段独立读回已经单独存证。
