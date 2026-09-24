# Codex：制作两个 x138 队友可复制候选，先交付、不运行

任务ID：BIOHUB_X138_TEAM_PAIR_20260924_V01  
仓库：SailorRen/Biohub-CELL  
执行／交付分支：codex/x138-team-pair-20260924  
固定研究基点：d01c627a3006455d7ac3f4351c76ddf1fd9f4eb2  
任务文件：tasks/CODEX_20260924_BIOHUB_X138_TEAM_PAIR_V01.md  
实验目录：experiments/BIOHUB_X138_TEAM_PAIR_20260924_V01/  
结果报告：reports/20260924_BIOHUB_X138_TEAM_PAIR_RESULTS.md

## 1. 目标、交付模式与本批边界

用户强调剩余约6天，以提高正式Public分数为第一优先级；现在要求先设计两个方案，并由Codex做成此前提供给队伍的模式。本批交付两个完整、独立、可复制的Kaggle私有母版，不只交付一段补丁或报告。

沿用“sailorren准备私有母版 → 只向当前已核实的现有队友授予Can view → 队友本人Copy & Edit到自己账号”的方式。历史协作者为dongdongjiaqi，分享前只读核对当前同队身份；不得凭历史身份向其他人扩权，不登录或代管队友账号，不索取凭据，不创建账号绕过配额。现有A、B、CPU研究、历史母版／副本及最终选择不动。

用户转交本任务后，Codex仅进行本任务代码构建、本地无模型小检查、GitHub任务分支同步、至多两个私有母版的非运行保存与必要共享。不继承历史跑分授权：本批Save & Run、Kaggle模型推理、GPU／Colab／独立CPU会话、新训练、正式submission、Dataset写入、最终选择修改均为0。队友后续运行和提交另行协调，不由本任务自动启动。

## 2. 最少必读材料和证据

安全fetch并读取固定基点；若本任务分支已有后续交付，先排重，不回退重做。使用干净隔离worktree，不覆盖用户未提交改动，不reset/stash、强推或合并main。将本任务原文存入上述tasks路径，连同本批产物同步任务分支；不要求重新审计全仓库。

在固定基点读取：

- AGENTS.md。
- reports/20260924_BIOHUB_0953_CHAT_HANDOFF.md。
- reports/20260924_BIOHUB_PUBLIC_0950_RESEARCH.md。
- research/PUBLIC_0950_20260924/source_archive_manifest.json。
- research/PUBLIC_0950_20260924/sources/x138/biohub-x138.ipynb、source.py、kernel-metadata.json。
- reports/20260923_BIOHUB_A950_THREE_CANDIDATES_RESEARCH.md。
- experiments/BIOHUB_TWO_WAVE_20260922_V01/A/consumption_precheck.json。
- experiments/BIOHUB_TWO_WAVE_20260922_V01/B/team_copy_handoff.json（只参考交付方式，不复制B算法、gate或旧额度）。

归档事实，不冒充本轮实时查询：

|对象|精确身份|已有证据|
|---|---|---|
|x138|anvithpothula/biohub-x138，V1／SV351539814|9月24日归档页面Public0.953；本队尚未复现|
|Kunal同代码|kunaldesale2408/biohub-cell-tracking，V10／SV352321925|归档Public0.953；12个有效代码单元与x138 AST相同，不另做第三个复制候选|
|A／025|submission56456090，V1／SV351739212|归档Public0.950；实际velocity0.25；selector为combo(tight55+bonus125+relaxed9)|
|D960|submission56416049，V1／SV351441983|归档Public0.948|

x138原始ipynb SHA256必须为：
6b655e39bbfd2d3d6c762badea69847d3f00f5b548f385cb01b07ee2600fde6d

0.25在A路线有成绩与实际消费依据；其在x138中的效果仍未知，不能声称可直接叠加+0.002，也不能预测必达0.955。Notebook中历史标题、硬编码报告参数和旧papermill时间不等于本次有效配置或执行证据。

## 3. 两个方案，不扩展第三个

|候选|母版及算法差异|目的|顺序|
|---|---|---|---|
|X0：X138-Exact|完整保留x138原版，velocity有效值0.5|争取在本队复现归档0.953，并建立新实测基线|优先交付|
|X25：X138-V025|完整x138，只把BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT的有效值0.5改为0.25|保留head、邻域flow和真实检测恢复，测试A的较弱自身速度外推是否能进一步改善关联|与X0一起准备，不等X0出分才写代码|

两份都是候选推理Notebook，不是原版与删模块消融。不要将Kunal同源码复制当第二方案；不加入H0/F0/G0，不扩参、不扫描，不重训head，不拼接A的整套后处理或私有gate。

### X25唯一算法改动

在配置初始化之前的确定位置设置：

```python
os.environ["BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT"] = "0.25"
```

X0在对应公共配置位置可显式设为"0.5"以避免外部环境污染；它与原版默认语义相同，仍须在diff中披露。两版除该值、候选身份／说明／slug和不影响推理的回执外，其余算法源码相同。

必须沿真实消费链核查：当存在邻域流时，仍使用source_pos + flow_step；没有邻域流但有自身前驱位置时，才使用source_pos + velocity * (source_pos - prev_pos)。没有前驱时仍用source_pos。0.25不是缩放邻域位移，也不是把整个flow结果减半。seed阶段和正式匹配阶段所有实际调用保持原逻辑。

参数必须在Cell 3读取常量之前设置，不能只改最终说明、失效的环境变量或打印值；不能全局替换所有0.5。保留FLOW_MODE=seed及全部原版流门限。没有flow的场景也会发生于seed构造或局部样本不足，不要删除这些路径。

### 两版共同保留

完整保留原head权重及其mean/scale、连续坐标、三线性特征读取、主／副模型TTA、harmonic融合、ILP、flow、readmit、新gapfill、旧single-frame和gap2、分裂修复、短轨过滤、linefit以及最终CSV舍入。

有效检测阈值0.965、DeepCenter安全分裂阈值0.25、validator关闭、原版固定后处理全部不改；不导入A的检测0.960、DeepCenter0.20、bonus1.25或relaxed9。新gapfill禁止合成点不等于整条流水线禁止合成点，不删除原版旧补点。

低阈值缓存补丁必须在head补丁之前；保留head在Cell 5中的candidate模式。源码完整展开检查嵌入模块及补丁锚点，不因共享锚点被破坏而让缓存／gapfill静默关闭。

## 4. 完整母版、输入和必要检查

用同一构建脚本生成两份完整ipynb。保留原12个有效代码单元的相对执行顺序，清除继承的输出／执行计数及容易误导的历史执行状态，不改模型逻辑。增加简短中文Markdown首页：真实候选名、差异、原版历史分数与本候选未跑分状态、输入表和队友操作步骤。

每份在运行环境内能直接Save & Run All，不依赖Mac路径、另一个候选的Output、联网git clone、现场下载代码、手工拼单元或运行时选X0/X25的交互开关。候选在构建时固定身份，防止队友选错。

按x138精确版本绑定四个Dataset及比赛输入：

- pilkwang/biohub-tracking-support-pack-50ep-v1。
- pilkwang/biohub-temporal-unet3d-seed314159-v1。
- pilkwang/biohub-deepcenter-unet3d-center-prior-v1。
- anvithpothula/biohub-v1284-head-s075，文件v1284_head.pt。
- 比赛biohub-cell-tracking-during-development。

先核对精确x138版本的Inputs。A曾用的primary V10、secondary V2、DeepCenter V5只作为查找线索，不能直接当成x138已经核实的版本；head V1也是归档观察，须核实实际输入。两版使用同一冻结输入集。原版前三套checkpoint已有代码哈希断言，保留并记录；head下载／读取如可进行则计算哈希，权重只放本地忽略目录或平台输入，不入GitHub。无法确认的版本或文件标UNKNOWN，不能按Latest静默替代并声称Exact。

核对原Notebook及权重的实际许可与作者归属；权重Dataset许可不能推定整份Notebook许可。无权访问或许可存在实质冲突时不擅自复制／分享，记录具体缺口。已明确的合法输入不重复发明额外研究门槛。不复用A/B的私有gate，不修改任何既有Dataset或旧共享权限。

本地只做一次小范围检查：

1. nbformat结构、逐单元AST和嵌入模块语法；两版算法diff只有一个有效参数，参数读取顺序正确，补丁锚点和CSV写出链完整。
2. 复用／抽取真实重连函数的无模型小图测试，分别覆盖无流有前驱、有流和无前驱：证明0.5／0.25在自身速度路径被消费，有流路径不直接缩放；这不是精度测量。
3. 不加全量CV、真实视频推理、旧A重跑或新评估框架。优先给两版增加相同的轻量运行后回执，记录实际参数、head路径／哈希、既有run_stats、模块告警、CSV哈希和候选身份；不重写旧硬编码报告冒充实测。

回执或辅助检查只读，不改变预测；不要在隐藏运行强制要求某个视频必须新增节点、必须和公开输出不同或必须包含已知视频名。浮点坐标影响不能只用旧int16坐标哈希判断。必要运行检查嵌入后续队友的一次完整运行，不另开GPU诊断。

## 5. 发布成此前队友复制模式，停在交付

计划母版slug（必须实际创建／读取后才给真实链接）：

- sailorren/biohub-x138-exact-team-20260924。
- sailorren/biohub-x138-v025-team-20260924。

先查是否存在；本批同名母版已存在则排重续接，不覆盖未知来源Notebook。每候选只创建一个Private母版，只做一次Quick Save或官方明确不执行的等价保存，不使用会触发运行的push/save方法。

可以在session off、Accelerator=None状态准备母版；这不代表CPU推理候选。队友运行时需要T4×2、Internet off；不要为了保存模板启动GPU或重新做GPU＋Output探针。官方Quick Save是代码／当前状态快照，不能写成端到端执行通过。

仅对当前团队页核实的现有协作者dongdongjiaqi授予Can view，Private保持不变。不得新增Can edit、公开母版或扩张旧资产权限。若队伍身份变化或无法核实，就先交付两个ipynb和权限待办，不猜收件人。

每个保存版本回读真实Kernel、Version、SV、完整代码、Inputs与可读取设置和共享结果。只读到了渲染源码时按相应证据层级报告，不能声称原始ipynb字节一致。队友端能否打开／挂载是单独状态，未由队友确认就是NOT_VERIFIED。

交付一段可直接转发给队友的中文说明，使用真实精确版本链接，不使用占位符冒充链接。内容只需包含：

“本次两个新候选X0／X25，优先X0；均未取得本队新分数。请用本人账号打开分享链接，Copy & Edit，确认Private、T4×2、Internet off和四个Dataset＋比赛输入未丢失、版本正确；不挂载旧gate。先把自己的副本链接与Inputs/Settings截图回传。本批仅准备，尚不启动运行／提交。后续统一协调后，每候选在本人副本运行一次Save & Run All，检查真实submission.csv及回执后再从对应版本提交；不要直接提交母版。”

队友不应需要GitHub、Codex或命令行才能运行。两个可复制母版和这一段说明是主要交付，不让长报告挡住链接交接。

## 6. 本批额度和最少产物

新增私有母版≤2、非运行保存请求≤2；仅为两个新母版向已核实队友各保存一次Can view权限（已具备则不重复）。所有不明写响应先只读对账，不换入口盲重发。新训练／fit、Save & Run、真实模型推理、正式submission、Dataset写入、GPU／Colab／独立CPU会话、最终选择修改均0。不能继承旧任务的后续跑分额度。

最少产物：

```text
tasks/CODEX_20260924_BIOHUB_X138_TEAM_PAIR_V01.md
experiments/BIOHUB_X138_TEAM_PAIR_20260924_V01/
  build.py
  X0/candidate.ipynb
  X0/kernel-metadata.json
  X25/candidate.ipynb
  X25/kernel-metadata.json
  candidate_manifest.json
  source.diff
  checks.json
  team_handoff.md
  platform_ledger.json
  github_readback.json
reports/20260924_BIOHUB_X138_TEAM_PAIR_RESULTS.md
```

不新增重复合同或治理框架。manifest区分历史参考分数与本候选Public=null，记录实际input版本／哈希和缺口；ledger区分模板创建、权限、队友复制、模型运行、正式受理和正式分数，不能混为“完成”。只同步本任务文件、源码、小型证据、短报告；模型、原始数据、完整图、submission.csv、凭据和签名URL不入GitHub。

在任务分支commit并push，从固定commit回读本批新增／变更文件核对SHA256一次，报告实际通过数、remote HEAD和工作树状态；不合并main。回读记录可绑定已验证的主体commit，避免为写回自身回执无限提交。Kaggle发布受阻也先同步可用代码和具体错误，不能谎称已共享。

## 7. 完成口径及以后如何评判

本批终点为TEMPLATES_PREPARED_TEAM_ACTION_PENDING，或具体的PARTIAL/BLOCKED状态。delivery、template、teammate_access、execution、submission、score分开写；本批execution=NOT_RUN，submission=NOT_SUBMITTED，public=null。只有真实远端回读通过才能说交付核验通过，不能说已提分。

后续正式跑分不在本批授权内：资源和团队额度足够时可并行评测X0／X25，资源不足先X0；不为制作第二份等待X0出分。最终按同窗正式Public比较X0、X25和保留的A；相同可见输出不证明隐藏预测相同，但重复候选先由用户决定是否值得占用提交；不自动补跑／扩参。ERROR没有质量分数，PENDING不是完成。

最终回复重点：两个真实精确模板链接、各自唯一差异、输入／共享已验证范围、队友最短操作说明、GitHub固定commit，以及本轮运行／提交均0。未拿到新Public不能填预期分数。

## 来源入口（固定档案与官方操作说明）

- 固定交接：https://github.com/SailorRen/Biohub-CELL/blob/d01c627a3006455d7ac3f4351c76ddf1fd9f4eb2/reports/20260924_BIOHUB_0953_CHAT_HANDOFF.md
- 公开源码：https://github.com/SailorRen/Biohub-CELL/blob/d01c627a3006455d7ac3f4351c76ddf1fd9f4eb2/research/PUBLIC_0950_20260924/sources/x138/source.py
- 旧团队模式：https://github.com/SailorRen/Biohub-CELL/blob/d01c627a3006455d7ac3f4351c76ddf1fd9f4eb2/experiments/BIOHUB_TWO_WAVE_20260922_V01/B/team_copy_handoff.json
- A成绩依据：https://github.com/SailorRen/Biohub-CELL/blob/d01c627a3006455d7ac3f4351c76ddf1fd9f4eb2/reports/20260923_BIOHUB_A950_THREE_CANDIDATES_RESEARCH.md
- x138原版：https://www.kaggle.com/code/anvithpothula/biohub-x138?scriptVersionId=351539814
- Kaggle官方Quick Save与Save & Run All说明：https://www.kaggle.com/docs/notebooks

本任务由Chat拟定，尚不代表已同步GitHub、已发布Kaggle母版或已启动Codex。