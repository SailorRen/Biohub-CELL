# Codex执行任务：两批共四次正式验证，先A/B、出分后再C/D

任务ID：BIOHUB_TWO_WAVE_20260922_V01  
仓库：SailorRen/Biohub-CELL  
执行／交付分支：codex/two-wave-four-submit-20260922  
交接基点：b2c3526fd48b0c64446b41bf78efa17a5697dfad  
日期口径：Asia/Shanghai（UTC+8）；状态以执行时真实观测为准。

## 1. 目标、授权和环境

用户已授权本轮必要开发、生产推理及最多4次正式提交：首批两个独立候选A/B；取得正式分数后，用剩余两个名额按第6节生成C/D。目标是提高正式Public，并尽量在启动时所在的同一平台额度周期刷新前提交第二批；不是只交方案或普通运行报告。上一轮只读补查任务的零写入限制不再限制本轮，但本轮授权不修改任何旧作业或最终选择。

用户在另一台电脑，新对话没有Mac缓存、权重、CSV、日志、旧终端或旧CLI凭据。历史输入只从GitHub读取；比赛数据和推理权重通过Kaggle已有输入挂载留在云端。新电脑只保存必要源码、元数据和本次下载输出；不得要求用户回Mac取资料。不存在的本地文件不能写为已验证。

本轮不训练、不新建Dataset、不增加独立8视野诊断或GPU对照、不做大范围参数扫描／全量公开调研、不建立新评估框架、不改最终选择。不向main或其他旧分支写入。以下“可能改善”均是待测假设，不承诺0.95或Private成绩。

## 2. 新电脑启动：GitHub是唯一历史入口，CLI不是门槛

在安全空目录开始。Git可用时：
```text
git clone --single-branch --branch codex/two-wave-four-submit-20260922 https://github.com/SailorRen/Biohub-CELL.git Biohub-CELL-two-wave-20260922
cd Biohub-CELL-two-wave-20260922
git remote get-url origin
git branch --show-current
git rev-parse HEAD
git status --short
```
核对HEAD包含用户启动消息给出的任务commit。已有未提交改动时另建目录，不reset、stash、强推或覆盖。此前新电脑出现过缺git remote-https helper：再次出现就改用GitHub连接器逐文件读取／写入，不花时间重装Git；本地git状态写NOT_APPLICABLE。不要只读main。Python不可用而Node可用时，用Node构建Notebook JSON和检查文本，不安装完整训练环境。

先发现实际可用的Kaggle工具和浏览器，再用一个只读操作确认授权及账号sailorren。优先已授权连接器或浏览器；上一报告曾用Edge，但本次必须重新核实，不能假定登录态仍在。CLI已安装且能认证时才复用；没有CLI不构成任务阻断，不索取／打印明文Token，不从浏览器提取Cookie绕过工具权限。新电脑需要登录时只指出需要用户完成正常授权，继续可完成的开发和GitHub交付，不能伪造平台动作。

浏览器可用时可直接上传构建好的ipynb或复制本账户精确D960版本到新的私有Notebook，接入下列固定Inputs，核对参数后Save Version / Save & Run；普通完成后从精确版本输出下载实际CSV，再用比赛的Notebook提交入口选择该版本和submission.csv正式提交。页面按钮以当前实际UI为准，不假装CLI已经执行。复制／导入只创建每候选一个对象，计入Notebook预算；旧对象不编辑。若连接器／浏览器没有实际上传或运行权限，交付已构建文件与明确缺失动作，不声称已运行。

### 必读的最小GitHub输入

以下均在交接基点的历史中；先读本分支的AGENTS.md、本任务与两份报告，不重读全部旧任务：
- `reports/20260922_GEOMETRIC_FUSION_BACKFILL_RESULTS.md`：公开V3的0.948及源码身份已核实，不重复整轮补查。
- `reports/20260922_GEOMETRIC_FUSION_COMPARISON.md`；`research/GEOMETRIC_FUSION_BACKFILL_20260922/leaf_guard_unit_checks.json`：候选依据与剪枝边界。
- `reports/20260921_BIOHUB_DF960_ONE_SHOT_V01.md`、`reports/20260921_BIOHUB_SCORE_TRIO_V01.md`：历史版本、结果、运行时间，均不是实时平台状态。
- D960精确母版：commit `1cf89f1f9380f005d98e9cb15ca9f5d80c4ebaca` 下 `experiments/BIOHUB_SCORE_TRIO_20260921_V01/D960/candidate.ipynb`，SHA256 `b12568e27ea5a8c66942a6301c2c80d037fdffe43f338a23a86266f80a02d192`；同目录`kernel-metadata.json`；上级`batch_manifest.json`。
- 可复用检查代码：本分支 `experiments/BIOHUB_SCORE_TRIO_20260921_V01/check_outputs.py`、`runtime.py`；官方reader在 `experiments/BIOHUB_DIVGATE_PAIR_20260920_V01/official/csv_to_geffs.py`。

旧check_outputs.py写死`/private/tmp/score-trio-private`及旧A18/G1缓存路径，并只接受旧三臂名称。只提取其schema／端点／度／canonical哈希／官方reader检查函数，适配本次目录与身份；禁止直接运行整个旧脚本、旧launch_once.py或submit_once.py。本轮可调整上一批专属回执、硬编码arm名称及参数断言，但不得删掉实际模型加载、输入、参数生效和图合法性检查。

需要其他分支文件时用固定commit读取或按需fetch，不merge整个分支，不从Mac找文件。连接器返回内容被截断时继续分页，或用新电脑Node/Python从固定GitHub Raw URL只读下载完整文件；不得拿搜索摘要拼成生产源码。D960直接下载入口为 `https://raw.githubusercontent.com/SailorRen/Biohub-CELL/1cf89f1f9380f005d98e9cb15ca9f5d80c4ebaca/experiments/BIOHUB_SCORE_TRIO_20260921_V01/D960/candidate.ipynb`，下载后校验上述SHA256。G1分类门代码在commit `e9c7c63b896812660a78ec55fc3284c10f85e776`的`experiments/BIOHUB_SPRINT01_20260916/production_module.py`和`division_patch.py`。新首批不用移植F1。

### 首批两臂固定云端输入

|类型|精确来源|
|---|---|
|比赛|biohub-cell-tracking-during-development|
|DeepCenter|pilkwang/biohub-deepcenter-unet3d-center-prior-v1，Dataset V5|
|secondary|pilkwang/biohub-temporal-unet3d-seed314159-v1，Dataset V2|
|primary及离线依赖|pilkwang/biohub-tracking-support-pack-50ep-v1，Dataset V10|
|G1 gate权重来源|sailorren/biohub-division-train-20260914，Notebook V1输出|

权重哈希和环境使用上述batch_manifest，不以同名最新版替换。沿用私有Notebook、T4×2、Internet关闭及原依赖；旧Docker不可选时记录真实可选镜像，优先原版本，只对必要导入和固定权重兼容做短检查，不换模型或训练。不要把原始比赛数据／模型权重下载到新电脑，更不能上传GitHub。缺已有私有输入权限时只阻断对应运行，不新建替代Dataset或重训。

## 3. 先核对时间、额度与已有状态，然后立即推进首批

读取实际比赛提交页／运行页，记录当前时间、团队剩余正式名额、GPU时数／活跃作业、下一额度刷新时刻及比赛截止时刻。用户说有4次、约8小时出分，这是规划输入，不替代当前账号观测；上海午夜不自动等于平台刷新。UI能确认关键数值即可，不为API原始字段缺失新建接口工程。刷新时间若只能按官方规则推算须注明，完全未知则写UNKNOWN，不伪造倒计时。

必须区别：候选普通推理耗时、从正式提交到出分的等待、第二批普通推理耗时。为约8小时留等待窗口，还要给第二批生产留时间；“8小时”不是硬保证。用已有运行日志估计，不开GPU基准。首批两臂资源允许则并行，各自普通完成／验收后立即提交，不等另一臂。提交名额不等于GPU可用；余额不足就优先A，不取消DF960或其他旧作业腾资源。无法完成2+2就如实报告，不能把加速希望写成已实现。

先对账已有Notebook和提交：A计划slug `sailorren/biohub-d960-v025-20260922`，B为 `sailorren/biohub-d960-l030p-20260922`。存在则续接，不重复创建。旧DF960为submission56445846 / V1 / SV351617874；D960为56416049 / SV351441983；F1为56375774 / SV351084196；G1为56270217 / SV350197436。一次只读查最新状态；DF960待分不阻塞首批，不重提。

## 4. 首批A/B：相同D960母版，两个独立改动

### A：D960-V025，只降低速度外推权重

相对D960只将`MOTION_RELINK_VELOCITY_WEIGHT`从0.5改成0.25，保持det0.960、harmonic0.15、DeepCenter分裂门0.20、G1 gate、其他几何门槛及选择器规则不变。不要加F1、剪枝或公开版本的宽分裂组合。

在配置实际初始化前设置BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT，并在真正计算predicted位置的调用点记录消费值；核对最终选参后仍为0.25，不能只改显示配置或等写完CSV后才赋值。所有受影响的原生产／原有选择器调用使用同一候选参数，保持原7项候选及选择规则，不新增velocity扫描。原选择器结果因候选图改变而变化时如实记录，不声称下游配置必然完全相同。

依据：公开Geometric Fusion V3 / SV351532492整套Public0.948已绑定；其已有局部日志velocity0.25单项proxy0.9505、base0.9490。旧proxy并非当前官方独立验证，不能把差0.0015预测成Public增益。这是小范围、单维度的正式实验。

### B：D960-L030P，单次、带保护的弱末端节点剪枝

相对D960仅新增保守叶子清理，velocity保持0.5。沿用原后处理顺序，在短轨过滤及原救援完成后、坐标平滑／最终CSV写出前调用；作用于每次实际输出图，包括原选择器使用的后处理入口，不改选择器候选集合。禁止直接按CSV行号删数据。下面是完整实现语义，不依赖旧Mac或完整公开源码：

节点同时满足以下条件才可删除：出度0；入度恰好1；不是当次真实输入视频的最后一帧；其父节点出度恰好1（保护分裂的两支）；唯一入边有可追溯、有效的真实模型概率，按既有概率转换口径得到p且p<0.30。全部条件基于剪枝前同一图快照判断，一次性删除符合节点及关联入边，不递归级联，不放宽其他门槛。

必须区分缺失评分和真实0概率：原motion的learned_prob对缺失返回0.0，所以仅看edge_prob数值不够。保留原模型概率字典的key存在性／有效性，给选中的边附加只读来源标记，或把该信息传入剪枝函数；不改变原匹配代价和概率数值。由几何重连新造且无真实模型评分的边、gap/safe-div等无评分修复边、非有限或无效概率，一律豁免。真实有模型记录的0.0不是缺失。不得将缺失一律填0后删除。

原视频最后帧从运行实际读取的时间轴获得，不能固定100帧，也不能用过滤后已缺节点的max(t)冒充真实最后帧。读不到该信息时保守跳过对应样本剪枝并记录，不猜测。日志仅记录候选／因分裂豁免／缺概率豁免／最终删除数及少量ID。B的规则与公开原版不同，不能继承其0.948结论。

参考依据：V3日志leaf030有小幅局部信号；既有合成测试确认原剪枝可能删分裂子节点、混淆缺失评分。P版针对这两个问题，不以这类合成测试宣称真实精度提升。若保护后真实输出无任何变化，不凑数提交，也不为激活它放宽保护或偷偷加大阈值。

### 最小检查与生产

仅测试本次修改路径：A实际消费0.25；B正常弱叶删除、强边不删、分裂分支不删、缺概率0不删而真实低概率可删、最后帧不删、一次性不级联；补丁关闭保持原逻辑。纯CPU小图即可，不要求旧数据或全GPU对照。

构建Notebook时去除旧outputs／旧execution_count（可保留来源信息），替换旧专属回执为本批回执，不把历史执行输出冒充新运行。必要构建／参数配置在对应Save & Run前同步GitHub并回读一次，然后立即启动生产。

实际CSV落盘后，先用独立解析代码检查schema、样本覆盖、整数坐标及哨兵、端点、时间方向、入度<=1、出度<=2、行ID和重复边；同时核对模型加载和参数实际生效。官方reader往返可放在同一次Kaggle生产运行末尾对实际落盘文件做，复用云端已有依赖；再由新电脑Python标准库或Node独立读实际CSV及摘要核验，不为安装本地tracksdata/scorer延误，不新增诊断作业。

同输入的已有产物有合法来源才对照；没有旧缓存时可只在这次生产中的同一原始图上做CPU回放／关闭新增补丁的输出对照，不额外推理模型。不得用旧检测图替换新输入。输出去重先用Github已有规范化哈希和本批实际输出；仅ID重新编号／行顺序变化不算有效改动。无改动、重复、非法图、模型静默缺失、参数失效只阻断该臂；合法且有效者立即走Notebook正式提交入口，不等完整报告、proxy上涨或DF960结果。

## 5. 本轮总预算、请求记录与等待期间

|项目|本任务累计上限|
|---|---:|
|新私有Notebook|4，每个候选最多1个|
|Save & Run|4次计划＋1次全批共享明确工程修复备用，总计5次|
|正式提交请求|4次总计，首批至多2、第二批至多2，每候选最多1次|
|新训练／Dataset／独立GPU诊断／最终选择修改|0|

失败或不明响应也计入相应请求预算；一次点击同时创建Notebook和Save & Run时分别计相应资源，不重复计算同一次网络动作。正式请求不明时先只读对账，不能盲重试。共享备用只修路径、接口、配置传播或写出错误，不作第五候选或算法试分；旧三臂／DF960未用预算不继承。

本任务总计4次不因跨会话或额度刷新增加。授权目标是本次启动额度周期；刷新后不得自动继续花新周期名额。若首批工程失败或无效，不能把它当Public下跌，也不强行补满四次；写清直接阻断和已用名额。团队其他人使用名额后实时剩余不足时只执行还合法可用的请求。

唯一账本 `experiments/BIOHUB_TWO_WAVE_20260922_V01/platform_ledger.json`。每个写请求前保存candidate、唯一request_id、操作、母版、源码hash、拟定版本／文件、时间；返回后补实际Kernel/Version/SV/submission、状态。浏览器写入也必须记，不要求CLI。若UI已证明提交被接受并绑定精确SV但不展示数值submission ID，记SUBMITTED_UI_CONFIRMED_ID_UNAVAILABLE及完整绑定，ID=null、不冒用旧ID，不为补ID重提。API未读字段写NOT_OBSERVED，不能用null假装API返回了空值。

正式提交后不占用空闲GPU等分，也不在没有结果时先跑C/D。同步A/B的精确身份、预算、已知刷新时刻和续接动作到GitHub。当前Codex前台会话可用时做合理低频只读查分；会话结束就停止工具操作，不承诺仍在后台监控，不新建无人值守定时器。约8小时后同一任务续接：读Github最新账本→查已有A/B/DF960→根据第6节做第二批，无需在已授权范围内重新申请。

## 6. 第二批C/D：以首批实际正式结果做决策，禁止未出分硬上

开始条件：A/B都已取得正式终态和可比较Public，仍在目标额度周期、剩余两个名额和运行资源足够。在普通推理加输出复核所需时间内能够赶上刷新前正式提交；第二批本身不要求刷新前完成8小时评分。此条件是计划检查，不承诺队列耗时。缺分数就保持WAITING_FOR_WAVE1；不能为抢额度把普通完成、局部proxy或排序当新Public。若只能赶上一臂优先C并如实说明；不能取消旧作业、降低检查或制造重复版本。

比较均用同窗D960的显示Public，D960历史是0.948但必须读当次值；记录当次全队最佳和DF960结果作参考。数值相同写PUBLIC_TIED，平台排序单列，不认定隐藏小数严格上涨。下面“未下降”仅指显示分未下降，不是证明等效。“下跌”只指成功评分后的显示分下跌。

|首批正式结果|C：优先验证互作或减弱干预|D：另一独立的小范围验证|
|---|---|---|
|A、B均未下降|D960 + A的V025 + B的L030P，检验两项互作|若B有显示上涨而A没有，测D960-L020P；否则测D960-V0375|
|A未下降、B下跌|D960 + V025 + L020P，减弱失败的剪枝干预|D960-V0375，不加剪枝|
|A下跌、B未下降|D960 + V0375 + L030P，减弱失败的外推干预|D960-L020P，velocity仍0.5|
|A、B均下跌|D960-V0375，回到原母版做较小改动|D960-L020P，回到原母版做更保守剪枝|

V0375=速度0.375，位于已测试0.5和0.25之间；L020P=保留全部P保护，概率阈值0.20，删除范围不大于L030P。这些新取值是根据首批测量进行的区间探索，不是公开已证实高分参数，不许写预期加多少分。第二批每臂用一个最终配置、不内部扫描候选后再挑。不能为两个名额重复同配置／同实际输出；保护后0.20无变化就跳过，不继续降保护。

可选的唯一母版升级：若同窗DF960已正式出分且显示严格高于D960、A、B，并且B未下降且确实改图，C改为“精确已提交DF960 + 同一L030P”，保留其F1其余配置；不要再重复D960+A+B。DF960精确源码从本分支`experiments/BIOHUB_DF960_20260921_V01/`构建记录／manifest定位并绑定V1/SV351617874，不能去Mac取。D仍按表做独立小范围验证。未严格显示领先、仅排序领先或尚待分时，不启用这个例外；不对DF960盲加V025，因为F1会覆盖部分预测位置。

C/D计划私有slug固定为`sailorren/biohub-wave2-c-20260922`和`sailorren/biohub-wave2-d-20260922`；先查对象与账本，再绑定本次所选配置，已存在则续接。

在第二批启动前，把实际A/B/DF960分数、选择的C/D准确配置及理由（几句话）写入同一账本／结果报告并同步。无需新合同或新一轮长调研，不调用重新训练，不增加H30/S50/宽分裂等未授权维度。沿用第4节生产、实际CSV复核、唯一提交和回读流程。按表仍无有根据或有效的候选时宁可少提交，不虚构改进。

## 7. 最小交付与跨电脑续接

唯一实验目录：`experiments/BIOHUB_TWO_WAVE_20260922_V01/`，A/B/C/D各存实际需要的candidate.ipynb、元数据、少量diff和检查摘要；计划配置写唯一`batch_plan.json`，请求写唯一platform_ledger。唯一报告：`reports/20260922_BIOHUB_TWO_WAVE_RESULTS.md`。不另建评估框架、重复验收合同或多格式报告。

只把代码、配置、小型哈希／日志摘录／回执同步本任务分支；原始CSV、完整图、模型、比赛数据和凭据不入GitHub。为新会话续接记录下载来源、精确版本和hash，不只留新电脑临时绝对路径。新会话从GitHub开始重建少量必要文件，而非依赖任何一台机器。

每批源码冻结一次、阶段交付时对新增／修改小文件远端回读一次并保存`github_readback.json`；不循环验证回执。Git失败走已授权GitHub连接器；不得把创建本地文件／工具退出0单独叫完成。不改旧报告、旧任务、旧实验账本和main。AGENTS的真实性要求保留，但不重跑9月3日初始研究的阅读数量合同。

返回表必须含每臂：母版、唯一改动、普通Version/SV、正式submission（若UI不公开须写限制）、参数生效／实际CSV复核、正式状态、原始分数和来源／时间、相对D960显示差、当次排序（若可读）、累计预算、下一额度刷新与剩余动作。源码交付、普通完成、正式已接收、已出分、显示提分五种状态分开；任务文件同步不等于Kaggle已执行。已有错误给出真实错误及可用工程备用，不用重跑来查分。

首批交付应是A/B真实正式接收记录或具体运行／资源阻断；第二批交付应是基于真实首批结果选择的C/D及真实接收记录。若评分或资源导致不能在当前周期完成，写实际PARTIAL状态和下一步，不假称四次都已用完，也不把配额刷新后提交算作刷新前完成。

## 固定证据与工具参考（仅按需读）

- 公开V3绑定／新反馈：commit `ab759473304a2c7d9403de90134f3bc5283922a5`，`reports/20260922_GEOMETRIC_FUSION_BACKFILL_RESULTS.md`及`research/GEOMETRIC_FUSION_BACKFILL_20260922/backfill_evidence.json`。
- 公开精确版本：https://www.kaggle.com/code/amanatar/biohub-geometric-fusion?scriptVersionId=351532492 。本任务实现可完全依据GitHub D960及本任务语义，不要求再下载公开整本。
- 官方CLI参考：https://github.com/Kaggle/kaggle-cli 。已有可用CLI时用其当前--help核对接口；无CLI优先浏览器，不把安装它作为前置条件。Chat本次公开Overview/文档未返回比赛正文，未独立确认当前账号剩余额度、刷新或截止；执行时以授权页面／工具为准。
