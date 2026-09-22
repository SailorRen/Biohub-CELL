# Codex执行：B单候选，先Kaggle，资源受阻再Colab

指令ID：BIOHUB_B_RESOURCE_TRIAL_20260922_V01  
原实验：BIOHUB_TWO_WAVE_20260922_V01，沿用B及原累计账本，不另开算法批次。  
仓库／交付分支：SailorRen/Biohub-CELL ／ codex/two-wave-four-submit-20260922。  
交接基点：3540a5acab8709a7cc42eef1f4fa18f66d44aa02。  
优先目标：把一个有明确改动的候选送入Kaggle正式评分；其次，用真实证据查清GPU耗尽时哪里能继续、哪里不能。

## 1. 当前授权与起点

用户现报Kaggle GPU余额为0、今天正式名额剩3。按执行时真实页面重新核对，不将其视为永久状态。当前已回到Mac，可用本机已有Git/CLI/SDK/浏览器，但不能假定登录态、缓存、解释器或目录一定存在；GitHub是历史交接依据。

本轮已授权：B的必要开发／环境适配、一次候选生产、最多一次正式提交；先用Kaggle正常流程，遇到明确GPU/运行资源阻断后，改用Colab自有托管GPU验证同一个候选，并尝试通过平台明确支持的方式返回Kaggle提交。数据与固定权重允许按权限直接下载到本人的Colab临时运行时，这是本轮对“计算只留Kaggle”旧安排的限定调整；不是允许公开数据、上传权重到GitHub或调用隐藏测试数据。

不重新申请上述范围的授权，但登录、验证码、OAuth同意等由用户处理，不读取明文密钥。不得购买/升级Pro、购买计算单位、绑定付费云项目、使用其他账号绕限额、部署SSH/保活绕过Colab限制、TPU迁移、训练新模型、改变最终选择、创建Dataset或取消旧作业。本轮不执行C/D，不复现两份0.951，不扩大公开调研。

已知历史：A=D960-V025，V1/SV351739212，submission56456090，上海2026-09-22 14:41:20最后归档PENDING；DF960为56445846/SV351617874。两者不得重跑或重提，GitHub未更新也不能推断平台仍待分。D960为56416049/SV351441983，历史Public0.948。原批累计Notebook1/4、SaveRun1/5、正式1/4，B此前仅源码就绪；先核对后续真实请求，避免并发重复。

## 2. 只读取够用的GitHub材料

在当前安全仓库先核对remote和工作区，再fetch上述分支。不要只拉main；用户改动存在时用隔离worktree/独立clone，不reset、stash、覆盖、强推或合并main。Git不可用则用GitHub连接器；本地状态写NOT_APPLICABLE，不能编造git成功。

必读：
- `AGENTS.md`、本指令、`reports/20260922_BIOHUB_TWO_WAVE_RESULTS.md`末尾A正式提交节。
- `experiments/BIOHUB_TWO_WAVE_20260922_V01/platform_ledger.json`、`batch_plan.json`。
- 同目录 `B/candidate.ipynb`、`B/kernel-metadata.json`、`patch_support.py`、`unit_checks.json`、`check_actual_csv.py`、`known_output_hashes.json`。
- `reports/20260922_GEOMETRIC_FUSION_BACKFILL_RESULTS.md`：公开0.948版本已闭合，不能把V025/leaf单项称为正式提分。
- `research/GPU_COLAB_A951_REVIEW_20260922/20260922_GPU_COLAB_A951_REVIEW.md`：只重点读资源路径和重复计算结论；同目录`code_path_tests.json`仅为历史小图证据，不重新测试0.951代码。

最后两份文件是前次Chat分析的原文归档；“未写GitHub”为其生成时状态。报告提到的source_review_manifest.json及第三方完整Notebook未随本任务镜像，不是本轮必要输入，不得伪称已读。

B冻结来源commit：4dca986a5bd61e3191ff790b74b505017678652e。路径`experiments/BIOHUB_TWO_WAVE_20260922_V01/B/candidate.ipynb`；SHA256：03e4abd5c80b5724b959bc453352524e276bebcf9aa0c2ffa38f22442d3e2ceb。文件可直接从GitHub固定版本恢复，不依赖Mac旧缓存。工具返回截断就分段或下载完整Raw再核对，禁止把摘要拼成Notebook。

## 3. 唯一候选：沿用已经构建的D960-L030P

B以D960为母版，velocity保持0.5，只增加阈值0.30的带保护弱末端节点剪枝：末端出度0、入度1、非真实视频最后帧、父节点出度1、入边有真实模型评分且p<0.30才删除。缺失评分不当0，保护分裂两支，一次快照、不级联。保持det0.960、harmonic0.15、DeepCenter分裂门0.20及自有G1分类门；不用A的0.25，不叠加F1、DivNet、gshift、relative-rank或宽分裂。

直接复用现成B和已通过的14项CPU检查，不重设计算法。该候选的真实Public收益未知。此次先验证既定候选与执行路径，不同时改写原7项选择器、batch或并行策略；尤其不能关闭验证器后默认base并称为同一B。已知旧回放可能触发DeepCenter GPU计算，应从现有日志记录时间，不再额外添加一轮验证/回放/性能基准。不为复用旧预检而改实际参数。

环境路径或设备数量适配另存`B/colab_adapter.py`或`B/colab_candidate.ipynb`并列出diff，B原候选保留。只允许载入路径、依赖安装/兼容和实际GPU数量等必要变化；模型权重、坐标单位、概率含义、真实输入覆盖、候选参数及选择规则必须保持。若需要更改算法或把自动选择改固定参数才能跑通，则停止提出建议，不在本任务中另造B-Lite。

## 4. 第一阶段：Kaggle正常流程，查清究竟卡在哪一步

1. 使用实际可用的已授权CLI/SDK或浏览器，核实sailorren账号、比赛、现有B、A/DF960状态、剩余提交名额和GPU已用/可用/预留/恢复提示。截图和小时提示记实际时间；不猜刷新时刻，不靠换工具扩大额度。已有B或不明请求先对账续接。
2. 优先已有官方Notebook流程。B尚未创建时，可创建一个私有草稿并挂固定Inputs，保留精确源码与元数据。计划slug：`sailorren/biohub-d960-l030p-20260922`。源码同步和一次回读后才启动实际运行。
3. 在正常GPU选择/Save & Run入口检查平台是否允许。UI明确额度不足、按钮禁用即可作为真实阻断证据，不必为证明再点击拒绝按钮。没有明确UI限制时，允许一次正常计划Save & Run请求；不允许用空Notebook额外探测。记录“没有发出请求”“明确拒绝”“已受理排队/运行”“响应不明”，四者不能混淆。
4. 正常GPU运行被受理后，沿用该精确版本，禁止同时到Colab重复跑；运行完成就做第7节验收和一次正式提交。排队不等于失败；响应不明先只读对账，不把它当不存在。
5. 只有确认Kaggle普通GPU运行受阻/明确失败且没有同候选仍在运行时，才进入Colab后备。认证、缺输入或非法CSV不是GPU耗尽，不得以迁移平台掩盖。CPU默认保存导致的整本CPU推理不属于替代成功，不能盲跑数小时。

固定云端Inputs（由B元数据再次核对）：
- `pilkwang/biohub-deepcenter-unet3d-center-prior-v1/5`
- `pilkwang/biohub-temporal-unet3d-seed314159-v1/2`
- `pilkwang/biohub-tracking-support-pack-50ep-v1/10`
- Notebook输出 `sailorren/biohub-division-train-20260914/1`（已记录SV349707105），以及比赛 `biohub-cell-tracking-during-development`。
固定权重哈希以`experiments/BIOHUB_SCORE_TRIO_20260921_V01/batch_manifest.json`及已有B断言为准；同名最新版不能替换。Kaggle最终代码保留Internet关闭和可支持的原GPU配置。

## 5. 第二阶段：真正的Colab托管GPU，不是Kaggle远程后台

先在Kaggle记录直接阻断，再使用用户截图中的`File → Open in Colab`；该入口不可用时，可由Colab从GitHub固定B源码导入，记录实际入口。优先本账号已有Colab文件，不无必要复制多份。允许保存一个默认私有的候选Notebook；不要共享公开或挂载整个Drive。

核实账号及运行时连接类型：应为Colab自己的托管运行时，不是`Kaggle Jupyter Server`或Mac本地连接。免费Colab能否分配GPU必须实际验证，不能根据没有付费计算单位直接推断不能用。申请一次GPU运行时，记录界面结果、实际型号/数量/显存、torch.cuda.is_available()和torch版本；没有GPU即停，不反复断开重连换卡。

参考官方入口（只补查有阻塞的问题，不做全量调研）：
- https://www.kaggle.com/product-announcements/470030
- https://www.kaggle.com/product-announcements/567740
- https://www.kaggle.com/product-announcements/540971
- https://research.google.com/colaboratory/faq.html
- https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/overview/code-requirements

在长跑前，同步核对第6节“回到Kaggle提交”的入口。若已明确仍强制要求一次无法启动的Kaggle普通GPU运行，Colab不能消除这道限制，应停止长跑并报告；不为收集一份不能提交的完整CSV耗费数小时。无法确定则记录未知，只进行最小资源/依赖/数据可达性检查，不先承诺零Kaggle额度上传。

Colab获取固定输入时使用用户已有合法授权及官方API/Kagglehub，先确认版本与下载清单，数据直接到Colab临时磁盘。只取生产及保留选择流程实际需要的文件/权重，检查空间和预计大小，不全量下载数据到Mac。原验证样本选择不能因只下载了部分目录而静默变化。私有gate输出、比赛下载权限缺失时停止需要该输入的步骤；不重新训练gate、不公开Dataset，不让用户发送Token到聊天/GitHub。不擅自点击接受比赛规则。

适配只解决依赖和路径；先做必要导入、固定模型载入和一个最小真实批次测试，成功则在同一会话继续一次完整B生产，避免另开完整诊断。已完成上游结果且配置/输入/依赖身份可证实时可以续用；没有证据不要伪造缓存命中，不能拿A最终CSV冒充B输入。普通CPU图处理或DeepCenter回放是否触发GPU如实记阶段耗时，不把它笼统标CPU-only。

环境排查限约30分钟主动修复时间（正常下载/生产耗时另记），只做一轮明确的路径/依赖修复；遇算子、存储、输入权限、资源中断或需修改算法而不能继续时停止并同步证据，不反复重装/更换平台。没有GPU或明确权限问题不必耗满30分钟。

## 6. Colab之后能否正式提交：必须实际核实，不能用假产物绕过

用本比赛当前官方页面及本机SDK/CLI帮助，确认新版本的保存、输入/加速器、输出绑定及代码提交要求，区分普通保存和正式隐藏运行。旧竞赛的Quick Save经验只是线索，不能直接当本比赛支持。

若平台明确支持将外部已验证的完整Notebook导入、保存一个正式可提交版本且不新增普通GPU运行，可在同一B草稿最多尝试一次官方支持的替代保存路径，记录版本/输出/加速器如何绑定。提交代码必须在Kaggle读取当次真实输入并完整推理；Colab专用下载凭据和联网初始化不能带进隐藏运行。不可把加速器保存成CPU后假设隐藏运行会给GPU。

不创建假的submission.csv，不把Colab可见样本CSV当成隐藏测试答案，不通过硬编码样本、读取已知可见数据或判断是否隐藏运行来跳过正式推理。运行时路径适配与隐藏样本特判不同，只允许前者。不能通过上传本地CSV的普通竞赛接口冒充代码竞赛提交。

若平台仍要求已完成Kaggle普通运行的产物、拒绝外部输出绑定，或替代保存无法保留正确GPU/Inputs，则停止。准确结论为“Colab可运行/已验证，但Kaggle正式提交仍被X限制”，不是SCORE_PENDING，也不是“Colab方案失效”。不得再补一次未授权的Kaggle全量运行或购买额度。

## 7. 实际输出验收与正式请求

正常Kaggle路线取得精确版本CSV后，沿用标准库检查器（在实际文件下载后，设置OUT_DIR为本次真实目录）：

```bash
python3 experiments/BIOHUB_TWO_WAVE_20260922_V01/check_actual_csv.py \
  "$OUT_DIR/submission.csv" "$OUT_DIR/two_wave/production_receipt.json" \
  --arm B \
  --other-check experiments/BIOHUB_TWO_WAVE_20260922_V01/A/formal_precheck.json \
  --output experiments/BIOHUB_TWO_WAVE_20260922_V01/B/formal_precheck.json
```

检查器接口已在GitHub核对。A正式检查文件从最新分支确认后读取，不因Mac缓存缺失伪造。保留CSV schema/完整样本/坐标/端点/时间/度/哈希、权重加载、实际velocity0.5和leaf0.30消费、缺失评分/分裂/最后帧保护、真实删除数及与A/归档输出去重。无实际变化就不提交，不能放宽剪枝只为凑名额。

Colab产物可使用同一解析器做真实工程检查，但结果单独保存为`B/colab_output_check.json`，注明计算后台、源哈希和输入范围；不要让脚本原有“from exact ordinary version”文案冒充Kaggle产物身份。必要本地文案/绑定适配另记diff，不放松内容检查。Colab检查通过不代表Kaggle提交已通过。只有第6节确认的正规版本/输出路径成立，才可进入正式请求。

正式发送前再次核对当日可用名额及B是否已提交，先在原`platform_ledger.json`持久化唯一request_id、候选/版本/SV、源码与实际输出哈希、账号和时间，并做一次必要远端同步。已接受/不明请求的B禁止二次发送。优先支持精确版本的code submission SDK/CLI，否则浏览器；不要同时用两个入口。

最多发送一次正式请求。回查一次实际受理/状态和分数，获取真实submission ID；UI只显示精确SV受理但无数值ID时记`SUBMITTED_UI_CONFIRMED_ID_UNAVAILABLE`，ID=null，不借用A/DF960 ID。没有受理证据只能是NOT_SUBMITTED或REQUEST_UNCERTAIN，不能写SCORE_PENDING。API没读取的字段写NOT_OBSERVED，UI空字符串保留其来源。取得受理后不用等待约8小时出分，不额外启动其他候选。

## 8. 本轮上限与真实资源记账

本轮最多消耗今天3个剩余正式名额中的1个，另2个保留；原批正式总计上限4仍不变，先扣已发生请求。用户当前授权覆盖本次实际执行时可用的1个名额，不自动跨周期反复尝试或追加其他候选。

- Kaggle新候选Notebook最多1个（已有B则0），所有操作续用同一B对象。
- Kaggle正常Save & Run请求最多1次；明确UI禁用则0。若第6节合法替代路径确有需要，再允许同一B最多1次不启动普通GPU的版本保存。二者分别记操作及是否实际创建版本/启动运行；计入原批相关上限，不把被拒绝的请求冒称完成运行。
- Colab托管GPU会话最多1个，完整生产最多1次，最小检查和一次有限环境修复在同一会话进行；不并行重复Kaggle生产。Colab生产一旦开始，不另跑第二个全量版本。
- 正式提交最多1次，失败/响应不明也占本轮尝试；不明写响应先对账。
- 训练/新增Dataset/TPU/购买与付费关联/最终选择修改/旧作业取消/新自动监控各0。

Kaggle GPU已用、可用、预留、普通会话耗时、正式评分状态分别记录；Colab实际运行时间单独记录，不将Colab时间填成Kaggle扣费。没有GPU扣时账单时只写快照差和并发限制，不能宣称精确归因。

## 9. 遇到的每种情况都记录，但不造新框架

沿用原平台账本；另在`experiments/BIOHUB_TWO_WAVE_20260922_V01/B/resource_events.jsonl`按顺序记录本次所有影响推进的动作：查询/资源拒绝/创建或保存/下载/授权阻断/依赖报错/修复/运行/验收/正式受理。每条至少含：

`event_id, observed_at（带UTC偏移）, backend, phase, action, candidate_source_hash, target_version_or_url, request_id_or_null, dispatched, outcome, raw_message_redacted, artifact_reference, quota_before_after, duration_if_known, next_action`。

原话/截图/必要traceback先去除Token、Cookie、邮箱/付款信息及签名下载参数；网址使用稳定页面地址。没有某字段写NOT_OBSERVED，不编造精确Kernel/SV/扣时。相同错误合并记次数，不需每次滚动或鼠标点击单独建报告。写请求前本地持久化意图；在转Colab、明确阻断及正式提交等节点同步一次小型进度，避免会话结束丢记录，不每个只读动作都commit。

报告只追加到`reports/20260922_BIOHUB_TWO_WAVE_RESULTS.md`“B：Kaggle额度耗尽／Colab后备测试”一节，写清：已做什么、发生什么、尝试何种最小解决、为何仍不能继续、保留的版本/产物、下一步需要用户/Chat决定什么。现有A/旧实验记录不能改写。必要截图和小型检查放B目录，原数据/CSV/完整图/权重/大日志不入公共GitHub。

明确阻断后停止新外部写入，立即同步能保存的结果到指定分支，固定commit回读新增/变更小文件一次。若GitHub本身不可写，保留本地交付和错误，明确未同步，不伪称Chat可读取。按原AGENTS保留安全与真实性规则，但9月3日全量调研阅读配额不是本轮门槛；不新增合同/验收仪表盘。

收尾状态分开：交付是否远端核验、候选是否跑通、是否正式提交、是否已出分。允许分别为KAGGLE_RESOURCE_BLOCKED、COLAB_RESOURCE_BLOCKED、INPUT_OR_ENV_BLOCKED、COLAB_VALIDATED_KAGGLE_SUBMISSION_BLOCKED、REQUEST_UNCERTAIN、SCORE_PENDING。会话结束不承诺后台自动操作；本任务启动的闲置Colab运行时在保存必要结果后可正常断开，不能关闭不属于本任务的会话。

最终直接向用户返回：最终停在哪一阶段、B准确版本/SV/submission、实际CSV/后处理变化证据、Kaggle与Colab各自资源结果和请求次数、直接阻断原文摘要、固定报告commit及回读范围。取得正式ID不代表提分；遇到无法继续时，把问题交回Chat分析，不自行扩大到第三个平台、0.951复制或购买套餐。
