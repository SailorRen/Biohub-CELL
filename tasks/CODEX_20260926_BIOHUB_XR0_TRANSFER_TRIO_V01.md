# Biohub-CELL：XR0 0.953 × 旧版有效改动，三候选同批执行任务

任务 ID：BIOHUB_XR0_TRANSFER_TRIO_20260926_V01  
编写日期：2026-09-26，UTC+8  
交付状态：DESIGNED_NOT_RUN_NOT_SYNCED。本文件是执行任务，不是平台运行、评分或 GitHub 同步回执。

## 1. 用户目标与本轮授权

比较本队旧 A/025 Public 0.950 与 x138/XR0 Public 0.953，保留新基线的新增能力，迁移旧版有实测支持的改动；在剩余约三天、用户报告 GPU 额度恢复、正式评分需八小时以上的条件下，同批构建并提交三个候选，不等第一个正式分数才运行第二个。

本轮候选数最多 3、正式 submission 最多 3（每候选一次）。计划完整 Save & Run 3 次；共享工程修复备用最多 1 次，仅用于明确的同一候选工程故障，不增加第四算法。失败和响应不明请求均计入账本，先查准确对象再决定是否使用备用。无新训练、无 Dataset 创建或更新、无购买资源、无新报名/组队、无最终选择修改。不得自动继承其他历史任务额度。

使用当前已授权账号及既有比赛团队；不操作队友账号，不改队友母版、A、XR0、旧 X25/XD960 或历史账本。任务和本批产物同步独立分支 `codex/xr0-transfer-trio-20260926`，不合并或修改 main。

## 2. 固定证据与身份

研究基点：`e67ea3fd5c1d8b45723559e0cf60baea37369caa`，仓库 `SailorRen/Biohub-CELL`。

| 对象 | 准确身份 | 已有证据 |
|---|---|---|
| A / 025 | Kernel 135318885；V1 / SV351739212；submission 56456090 | Public 0.950；旧 D960 上 velocity 0.5→0.25；保留 G1 |
| D960 | V1 / SV351441983；submission 56416049 | Public 0.948 |
| G1 | V1 / SV350197436；submission 56270217 | Public 0.948，相对原 Forge 0.947 显示增加 0.001 |
| 已评分 XR0 | dongdongjiaqi/biohub-x138-xr0-score-20260925；Kernel 135797557；V1 / SV352643547；submission 56546951 | Public 0.953；2026-09-26 固定报告核验 COMPLETE |
| 原公开 x138 | V1 / SV351539814 | 原 ipynb SHA256：6b655e39bbfd2d3d6c762badea69847d3f00f5b548f385cb01b07ee2600fde6d |

XR0 的 12 个有效代码单元与本队冻结原版一致；构建必须以已成功运行 XR0 的准确代码/设置为准。可用固定归档原 x138 的有效代码核对，但不可直接继承其陈旧 Notebook 内嵌 GPU/papermill 元数据。

以下资料位于同一固定研究 commit：

- `reports/20260926_BIOHUB_PUBLIC_UPDATE.md`
- `research/PUBLIC_UPDATE_20260926/XR0_scored_readback.json`
- `research/PUBLIC_UPDATE_20260926/team_submissions.json`
- `reports/20260925_BIOHUB_XR0_XD960_SCORE_PAIR_RESULTS.md`
- `research/PUBLIC_0950_20260924/sources/x138/biohub-x138.ipynb`
- `research/PUBLIC_0950_20260924/sources/x138/source.py`
- `experiments/BIOHUB_TWO_WAVE_20260922_V01/A/candidate.ipynb`
- `experiments/BIOHUB_TWO_WAVE_20260922_V01/A/kernel-metadata.json`
- `reports/20260922_BIOHUB_TWO_WAVE_RESULTS.md`
- `reports/20260916_BIOHUB_SPRINT01_RESULTS.md`
- `experiments/BIOHUB_SPRINT01_20260916/saved_inference.py`
- `experiments/BIOHUB_SPRINT01_20260916/division_patch.py`
- `experiments/BIOHUB_SPRINT01_20260916/production_module.py`
- `experiments/BIOHUB_SPRINT01_20260916/build_production.py`

入口：[固定研究报告](https://github.com/SailorRen/Biohub-CELL/blob/e67ea3fd5c1d8b45723559e0cf60baea37369caa/reports/20260926_BIOHUB_PUBLIC_UPDATE.md)。

## 3. 两版差异：代码事实，不是单模块因果归因

| 维度 | A / 025：0.950 | x138 / XR0：0.953 | 本批处理 |
|---|---|---|---|
| 基本模型 | 双 temporal 模型、关联、TTA、ILP、DeepCenter；harmonic 反向权重 0.15 | 同一技术家族，不是整体重训的新检测器 | 保留 XR0 全部原模型与输入 |
| 坐标与关联特征 | 没有 x138 的 V1284 坐标头/配套连续采样改动 | 224→32→3 坐标回归头；位移限幅小于 2 µm；三线性采样关联特征 | 全部保留，不拆配套修改 |
| 运动 | 自身轨迹速度权重 0.25；A 实际消费回执已验证 | seed 邻域位移中位数，K=12、半径40 µm、最少4种子；无 flow 时使用速度，权重0.5 | 只试无 flow 分支的0.25，不再叠加旧 F1/global drift |
| 检测恢复 | 不含 XR0 的整套 readmit/真实低阈值 gapfill 新增链 | readmit 最低0.965；真实低阈值检测补最多3帧间隙，禁止合成补点，新增比例上限3% | 全部保留 |
| 主检测阈值 | 0.960 | 0.965 | 固定0.965；不扩展检测阈值网格 |
| DeepCenter 安全分裂门 | 0.20 | 0.25 | 固定XR0的0.25，不与G1混改 |
| 本队 G1 学习分裂门 | 有；过滤门得分阈值0.95 | 无本队G1 | 作为独立迁移因素 |
| 后处理选择 | 保留旧自动选择器；普通运行选 combo(tight55+bonus125+relaxed9) | validator关闭；普通选择base，tight=5.5；既定运行时限/缓存保护 | 保留XR0，不恢复旧扫描 |

0.953−0.950=0.003 是完整管线显示分差。没有实验证据把这0.003分拆为坐标头、flow、补点各自收益。

G1、DeepCenter、Public 是三种不同数字：G1 分类门阈值0.95；本批 DeepCenter 阈值0.25；已有 Public0.953。不得把旧报告中概括性的“G1分裂门0.20”误读为分类器阈值。

## 4. 三个候选：一个二因素交叉设计，不是三套大框架

现有 XR0 为 X00（velocity0.5，G1关闭），不新增基线运行。

| 候选 | 建议私有 Notebook slug | velocity | G1 | 相对XR0的算法改动 |
|---|---|---:|---|---|
| XV25 | biohub-xr0-xv25-20260926 | 0.25 | 关闭 | 仅无flow时的速度收缩 |
| XG95 | biohub-xr0-xg95-20260926 | 0.5 | 开启、阈值0.95 | 仅新增冻结G1候选过滤 |
| XV25G95 | biohub-xr0-xv25g95-20260926 | 0.25 | 开启、阈值0.95 | 上述两项组合；不得有第三项修改 |

有3个槽位时同批启动；仅2个并发槽位时先 XV25、XG95，任一普通运行释放槽位后启动 XV25G95，不等正式 Public。各自普通完成、必要验收通过即正式提交，不等三份全部普通完成，也不等首份正式成绩。

### XV25：速度收缩

在配置初始化前显式设置 `BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT=0.25`。从XR0实际调用链确认变量被消费，不以初始化打印证明生效。

必须保留 `FLOW_MODE=seed` 和全部 flow 参数。有 flow 时仍使用 XR0 原预测；只在原本使用速度的分支生效，不把0.25乘到全部flow向量，不新增drift。

证据：旧 D960→A 的单参数实验显示0.948→0.950。边界：XR0有flow覆盖，实际受影响范围可能缩小；旧X25因GPU/部署错误无有效分数，不能当作算法已失败，也不能复用错误运行壳。

### XG95：迁移 G1 的三帧分裂候选过滤

只复用现有冻结分类器及 G1 接入位置，不运行训练 Notebook，不照搬历史0.945整本训练版，不启用R1重新排序，不改原几何资格、DeepCenter、排序、cap及已存在分裂。

既有模型输入：`sailorren/biohub-division-train-20260914/1`，历史精确 SV349707105。只添加其既有输出作为输入；不创建Dataset、不把权重上传GitHub。模型文件 `division_gate_weights.json` 的 SHA256 必须为：

`0a1f9b93bb529e70f4f7c2ba0907eea8b4cecd2befccc8ba1fb75e569edf77a0`

生产使用其中 `final` 模型。保持10维特征、标准化mean/scale、clip[-8,8]、线性与平方项、coefficients、sigmoid均与 `saved_inference.py` 一致；不重新拟合或调整0.95。

特征上下文是母细胞t、两个子细胞t+1、两子各自唯一后继t+2。源文件坐标为(z,y,x)体素，按(1.625,0.40625,0.40625)转物理单位；迁移前核对XR0节点存储仍是该约定，保留浮点坐标，不能二次乘尺度或取整。

在XR0 `add_safe_divisions_postlink` 内，原几何和DeepCenter判断通过、加入 proposals 之前加入过滤。参考 `division_patch.py::ProposalPolicy.admit`：三帧上下文存在且有限得分<0.95时不接纳；上下文不足返回abstain并保持原规则；恰好0.95保留。不得先最终挑选再删边替代候选过滤，否则竞争与cap语义不同。

仅改受控函数与必要推理/日志接线；使用独立命名空间，避免覆盖XR0的同名辅助函数。用AST定位和唯一锚点计数，不全局盲替换。保留XR0低阈值缓存补丁→head补丁顺序。

不要直接运行旧 `build_production.py`，它从旧Forge母版构建，会丢失XR0新增模块。也不要原样复制旧 `production_module.py` 每视频全量deepcopy和原规则双重回放；保留冻结推理语义，用少量计数/样例记录实际使用，避免重复影像/后处理工作。

注意：G1限制的是新增safe-div候选，不是删除所有低分既存分裂。下游短轨过滤、竞争等可能改变最终节点和边；不能宣称最终节点数量不变。XR0精修后的特征分布也可能影响旧分类器，是否迁移成功只靠本批实测。

### XV25G95：组合

从同一XR0母版组合已构建的两项补丁。相对XV25只能新增G1；相对XG95只能改变velocity。以diff/AST核验这两个关系。

这使本批在一个评分周期获得两个单项与一个组合，不需要先等单项8小时以上后再启动组合。组合可能负交互，不假设收益相加。

## 5. 最小执行流程，不新增长诊断工程

1. 一次集中预检：读取本任务、AGENTS、固定源码、已有X25/XD960及团队准确提交记录，排除这三个配置已被提交的重复。核对当前登录身份、团队日剩余额度、GPU可用量和并发槽位。API失败而官方已登录页面能提供必要事实时可用页面，不把两通道必须同时成功设为额外门槛。无可靠身份或无法确认写入结果时才停止对应操作。
2. 三份在本地同批构建。复用既有CPU测试器做语法、配置、G1上下文不足回退、0.95边界、原排序/cap保持、坐标单位和禁用一致性检查。只做小型检查，不重训、不另开完整GPU诊断、不做新交叉验证/大网格。
3. 保存源码、参数和简短构建回执，推送本批分支并按固定commit回读。不得把新任务覆盖旧账本。
4. 实际Save & Run前核对Private、GPU实际启用、Internet关闭、输入版本及镜像。普通运行启动后在真实日志确认CUDA/T4；旧Notebook内嵌isGpuEnabled、Quick Save成功或复制成功均不能替代GPU运行证明。
5. 按槽位连续启动本批候选。采用同一已成功XR0部署设置，不为了新候选重新复现XR0。每份普通完成后直接做最小输出验收并提交一次，不等其它候选正式分数。
6. 当本次交互结束时，只记录实际精确Version/SV/submission和最后查询状态。已受理但尚未出分写SCORE_PENDING；没有ID不能写已提交；不承诺会话外后台监控或自动操作。

### 冻结运行设置

以XR0已评分版本实际读取设置为准。固定报告记录的成功镜像为：

`gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461`

原输入：support-pack V10、secondary V2、DeepCenter V5、head V1及比赛数据；仅XG95/XV25G95增加上述既有gate输出。原三个主权重断言保留；head按固定V1实际挂载核对并记录哈希，不猜测未取得的哈希。模型和原始数据留Kaggle/本地Git忽略目录。

若成功XR0精确源码读取暂不可用，但固定原件12代码单元已能与归档成功XR0核对一致，可按已验证的原件和明确部署设置继续，不把标题/旧时间戳不一致当作算法阻断。若模型输入确实缺失，仅阻断受影响的G1候选，XV25不随之停止；不为凑满三份自行替换成未授权第四方案。

## 6. 必要验收及轻量日志

所有候选：保存源码SHA、实际参数、输入/权重身份、CUDA日志、普通版本、样本覆盖、CSV schema/有限坐标/端点/时间方向/一子最多一父/一父最多二子/重复边检查、运行耗时、repair_fallback和deadline_degraded。复用既有验收器，修接口不重建框架。

XV25及组合：记录实际flow与no-flow/velocity分支计数或等价消费证据。

G1及组合：记录独立前缀下的候选数、有限得分次数、拒绝数、上下文不足数及少量候选样例；不得覆盖XR0已有safe_divisions_added等统计。异常不得伪装成“安全无变化”；缺权重或结构不兼容在正式提交前明确处理。

不要要求隐藏图可下载，也不要用可见4视频“输出没变”推断隐藏集一定没变。明显补丁未接入、参数被覆盖或候选精确重复才是不应提交的工程问题。局部总分不作为必须先提高的硬门，稀疏未标注不当负例。

三份Public均与既有0.953比较；同时比较组合与两单项。高于0.953才可称可观察的Public改善；同分不臆测更多小数。若只有组合提高，也只能记录组合提高，不能虚构各模块贡献。Private泛化仍未知；本任务不修改最终选择。

## 7. 时间和结果收口

按固定报告，截止为2026-09-30 07:59（上海/新加坡，UTC+8）；执行时在官方页面核对。用户提供的“8小时以上”是排程依据，不是完成时间保证。

优先本批同日开始普通运行并尽快把三份分别送入正式队列。9月29日优先处理已启动方案的结果、工程错误及交付，不再增大架构。三份运行占用与GPU并发以平台当时显示为准，不因同批设计而保证同刻启动或同时出分。

固定交付路径：

- `tasks/CODEX_20260926_BIOHUB_XR0_TRANSFER_TRIO_V01.md`
- `experiments/BIOHUB_XR0_TRANSFER_TRIO_20260926_V01/{XV25,XG95,XV25G95}/candidate.ipynb`
- 同候选目录 `kernel-metadata.json`、`source.diff`、必要构建/输出小回执
- 本批目录 `platform_ledger.json`
- `reports/20260926_BIOHUB_XR0_TRANSFER_TRIO_RESULTS.md`

报告必须分列：母版、唯一改动、普通运行Version/SV、submission、最后观测状态、Public、相对0.953差值、实际GPU/输入、失败直接原因、使用次数、固定Git commit及远端回读。不得用一串COMPLETED标签替代真实对象。

当前任务生成会话：新GPU运行0、正式提交0、GitHub写入0；无可用Kaggle执行连接、GitHub连接仅提供读取。以上是后续执行要求，不是已经完成的动作。
