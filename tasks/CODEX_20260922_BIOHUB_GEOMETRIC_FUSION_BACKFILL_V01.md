# Codex跨电脑任务：Geometric Fusion最小证据补全

任务ID：BIOHUB_GEOMETRIC_FUSION_BACKFILL_20260922_V01  
仓库：SailorRen/Biohub-CELL  
唯一交付分支：codex/geometric-fusion-backfill-20260922  
交接基点：34df61552d4331c999148c2db684c3c9a217c43f  
任务性质：公开资料／已有提交只读核查＋GitHub小型报告交付；不是新实验。日期使用Asia/Shanghai（UTC+8），每次观测记录实际日期时间。

## 0. 先理解本次环境与授权

用户现在使用另一台电脑、全新Codex对话。旧Mac、本地项目目录、旧终端、旧浏览器登录态、旧临时目录以及Chat的sandbox附件均不可依赖。项目历史只以GitHub中真实存在的文件为入口；不要要求用户回Mac找日志，不把未下载到新电脑的文件写成“本地已有”。

本次只补影响下一步决策的三项：①公开Geometric Fusion的0.948精确版本绑定；②DF960既有提交的最新结果；③直接相关的最新公开反馈。不是再调研全部比赛，更不是执行旧任务的启动／提交步骤。

允许：读取GitHub、只读访问公开Kaggle页面；使用新电脑已授权的账号／浏览器只读查分；下载现有源码、小型输出；本地纯文本／JSON／AST比较；向本任务分支提交小型报告和证据。禁止：训练、模型推理、GPU诊断、Notebook创建／Fork／Save & Run、正式提交／重提、Dataset写入、取消作业、改最终选择、接受规则、报名、建立自动监控。本任务上述Kaggle写入预算全部为0；不继承旧任务的实验授权或剩余额度。

## 1. 从GitHub开始：新电脑可直接执行

先检查当前目录，选择新电脑的一个空目录；不假定操作系统或绝对路径。Git已可用且目标目录尚不存在时，使用以下命令（PowerShell／bash均可）：

```text
git clone --single-branch --branch codex/geometric-fusion-backfill-20260922 https://github.com/SailorRen/Biohub-CELL.git Biohub-CELL-geom-backfill-20260922
cd Biohub-CELL-geom-backfill-20260922
git remote get-url origin
git branch --show-current
git rev-parse HEAD
git status --short
```

若已有本仓库，先检查remote和工作区；有未提交改动就另建独立目录，不reset、stash、覆盖、强推，不切走用户正在工作的分支。不要只拉main：本轮材料在上述命名分支。记录实际读取HEAD；用户启动消息给出的固定任务commit必须存在于HEAD历史中，可用 `git merge-base --is-ancestor <任务commit> HEAD` 检查，不在历史中则fetch该任务分支后重新核实，不强行回退。

若只有GitHub连接器没有Git终端，可按相同分支／固定commit逐文件读取并通过连接器交付。此时本地工作区／ahead-behind写NOT_APPLICABLE，不编造git检查结果。没有GitHub写权限时先完成可做的读取，报告交付阻断；不要声称已同步。

新电脑的Kaggle授权单独核对：优先使用本会话实际可用的只读Kaggle工具或已授权浏览器，不假定旧Mac凭据自动迁移。不打印／索取明文Token，不从仓库寻找密钥，不安装大环境。没有登录态时继续公开页面与GitHub分析；私有查分写BLOCKED_AUTH，明确需要在新电脑建立授权，但不因此重跑DF960或停掉所有其他核查。

## 2. 必读顺序：所有项目输入都有GitHub入口

以下前五组文件均从本任务分支读取；相对路径均以仓库根目录为起点。

1. `AGENTS.md` 与本任务文件。保留项目安全和真实性要求，但9月3日初始情报任务的阅读数量合同不属于本次验收范围；本次不新增阅读配额、重复合同或审查框架。
2. `reports/20260922_GEOMETRIC_FUSION_COMPARISON.md`：Chat已完成的静态比较和建议。这是历史分析，不是当前查分，不需要重做整篇报告。
3. `research/GEOMETRIC_FUSION_BACKFILL_20260922/uploaded_notebook_fingerprints.json` 与同目录 `leaf_guard_unit_checks.json`：原上传附件的精确文件／逐单元源码指纹，以及既有4项CPU合成测试记录。全套原Notebook未在本交接包镜像；验证源码身份不需要Mac原件。不要声称GitHub已经保存了完整原附件或真实CSV。
4. `reports/20260921_BIOHUB_DF960_ONE_SHOT_V01.md`：DF960最新归档报告；以及 `experiments/BIOHUB_DF960_20260921_V01/platform_ledger.json`（先确认存在再读；缺失不否定已有提交）。只读，不执行该目录启动器／提交器。
5. `reports/20260921_BIOHUB_SCORE_TRIO_V01.md` 与 `experiments/BIOHUB_SCORE_TRIO_20260921_V01/public_score_order.json`：D960、F1、G1等历史成绩与排序。分数与排序时间分开，不将旧截图当实时结果。

只在需要解释差异时补读以下已存在的固定GitHub版本，不整仓扫描：

|对象|固定commit与路径|
|---|---|
|D960源码|`1cf89f1f9380f005d98e9cb15ca9f5d80c4ebaca` 下 `experiments/BIOHUB_SCORE_TRIO_20260921_V01/D960/candidate.ipynb`；原文件SHA256 `b12568e27ea5a8c66942a6301c2c80d037fdffe43f338a23a86266f80a02d192`|
|D960输入与权重|同commit下 `experiments/BIOHUB_SCORE_TRIO_20260921_V01/batch_manifest.json`|
|G1分裂门|`e9c7c63b896812660a78ec55fc3284c10f85e776` 下 `experiments/BIOHUB_SPRINT01_20260916/production_module.py`、`division_patch.py`|
|F1参考补丁|`8f18a8dd83146d6399b296ff54c4176c300724b5` 下 `experiments/BIOHUB_F1_FLOW_KAGGLE_20260918/flow_patch.py`；正式F1绑定以DF960报告的精确SV核对结果为准，不能引用该旧分支内过期NOT_RUN成绩文件|
|既有公开情报|`6ec61f54cd5fb5b93fe7cd1dbc37b01a8e41bc57` 下 `research/PUBLIC_INTEL_20260918/update_20260920/最新公开情报.md`，来源版本索引在 `research/PUBLIC_INTEL_20260918/sources.json`|

分支内没有其他分支文件时，不去Mac查找；直接用GitHub固定commit读取，或按需要fetch已知分支后 `git show <commit>:<path>`。不用merge/cherry-pick整条历史分支，不覆盖本任务文件。

## 3. 任务A：把公开0.948绑定到精确代码版本（最高优先级）

目标地址：
https://www.kaggle.com/code/amanatar/biohub-geometric-fusion

用户提供了0.948和一个Notebook附件；之前Chat已分析附件12个代码单元，但尚未独立确认该分数属于哪个Version／ScriptVersionId。不要把标题、卡片Best Score、附件局部proxy0.9530或普通运行COMPLETE当正式分数绑定。

按最短路径读取目标页及Version History，查清：作者／slug、Notebook Version、ScriptVersionId、版本时间、页面展示的Public原始字符串、分数展示位置、版本固定链接、观测时间。作者submission ID若不公开，写NOT_PUBLIC，不设为阻断条件。明确区分当前版本分数与历史Best；只能看到历史Best时，版本归属仍UNKNOWN。

下载对应精确SV的现有Notebook源码，或读取该版本完整source；不要Fork或Save & Run以获取源码。用交接包指纹确认它是否等于用户上传的附件：

- 原附件字节：637942；SHA256 `940ccce3466a8fdbbe4ead62c1bf33faef23054958ddf92d62858f81bdef774f`。
- 代码单元：12，编号0–11。source为list时直接join，为str时原样保留。逐单元只对source的UTF-8字节取SHA256，同时比较单元类型和顺序；不strip，不混入outputs、execution_count或metadata。全部预期指纹在JSON中。
- 原ipynb字节不同但12个source／顺序／类型一致，可以写SOURCE_CELLS_MATCH、FILE_BYTES_DIFFER；不能因输出或运行时间不同就说算法变了。
- 若严格source不同，只检查变动单元与真正影响预测的函数／配置。只有进一步证实只是换行或格式变化才能单独记录语义等价；不要把“哈希不同”直接当新方法。原附件全文未镜像，无法定位的旧文本差异应写明，不能虚构逐行diff。
- 下载不到完整source，就记录SOURCE_COMPARISON_BLOCKED，不把页面0.948强行绑定到附件。

纯文本指纹对照可用下面的Python标准库片段；n是已读取的公开版本Notebook JSON，f是GitHub指纹JSON。严禁执行Notebook单元：

```python
import hashlib
cells = n.get('cells', [])
expected = f['cells']
rows = []
for i in range(max(len(cells), len(expected))):
    if i >= len(cells) or i >= len(expected):
        rows.append({'index': i, 'match': False, 'reason': 'cell_count_mismatch'})
        continue
    source = cells[i].get('source', '')
    source = ''.join(source) if isinstance(source, list) else source
    digest = hashlib.sha256(source.encode('utf-8')).hexdigest()
    rows.append({'index': i, 'sha256': digest,
                 'match': digest == expected[i]['source_sha256']
                 and cells[i].get('cell_type') == expected[i]['cell_type']})
```

有现成小输出时顺手读取 `ppsweep_selected.json`、`ppsweep_results.csv`、manifest／日志必要段，确认最终实际消费参数；没有就沿用已归档日志，不为获取这些文件跑Notebook。不将大CSV、权重、完整日志入库。读取许可并保留署名；未确认再分发许可时不镜像整本第三方源码或讨论全文，只保存自写摘要、版本链接、指纹和必要小型事实记录。

既有静态结论供核对而非新实验：该附件仍是harmonic_probability、反向权重0.15；det0.965；最终velocity0.25、leaf0.30、DeepCenter分裂阈值0.15、几何11/16/12；没有我们的G1分裂门。公开整体0.948不能归因为velocity单项，也不代表优于D960。

## 4. 任务B：只读查询DF960已有提交

已有提交身份如下，不能新建或重提：

|方案|Version|ScriptVersionId|submission ID|最近已归档状态|
|---|---:|---:|---:|---|
|DF960|1|351617874|56445846|2026-09-22 08:00:31上海：PENDING，原始Public为空字符串|
|D960|1|351441983|56416049|历史COMPLETE／0.948|
|F1|1|351084196|56375774|历史COMPLETE／0.948|
|G1|1|350197436|56270217|历史COMPLETE／0.948|

DF960 Kernel135257948；slug为 `sailorren/biohub-df960-flow-20260921`。先核对新电脑实际授权账号，不能读到别的账号就冒充本队记录。用已有只读入口按ID查询一次；若需要提交列表，读取足以匹配这4个ID的内容，不重新审计全队所有历史提交。

记录实际正式状态、原始Public字符串、错误描述与观测时间。空字符串归一化null；PENDING不等于失败。已COMPLETE时同窗核对D960／F1／G1。UI能读取Public Score排序则额外记录，不为排序另装工具或修改最终选择。显示同分写PUBLIC_TIED，排序领先单列，未知同分规则不能证明隐藏小数严格提分，Private未知。

没有Kaggle授权或读不到该ID时，写当前查分BLOCKED_AUTH／BLOCKED_ACCESS，引用08:00:31历史状态并明确不是最新平台状态。GitHub报告未更新不代表Kaggle仍PENDING。不要等分、定时轮询、取消或重跑。本批旧正式请求已用1/1，未用工程备用不是本次可用提交名额。

## 5. 任务C：只补直接相关的公开增量

公开增量搜索最多10分钟，不以阅读数量验收；先目标Notebook评论与近24小时Code／Discussion更新，然后仅补读直接有关的内容：

- https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/code
- https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion
- https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/742266 （relink与单参数反馈）
- https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/742064 （训练覆盖与验证独立性）
- https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/741749 （模型平台期及作者分数更正）

重点找velocity0.25、motion/relink、leaf pruning、分裂误删保护、验证分与Public不一致的实现／测算／负面结果。新帖直接链接到代码时只补看相关实现及精确版本。搜索标题和摘要只发现来源，不算正文证据；记录绝对发布时间、更新时间、观测时间，别把旧缓存“几天前”写成今天新消息。

真实官方／平台分数、作者声称、代码事实、局部proxy分开写。没有找到新结果就写NO_NEW_DIRECT_EVIDENCE；页面不可读写具体缺口，不虚构全文阅读，不无限重试，不开展新模型／HOCT／训练路线综述。版本绑定和DF960查分各自独立，一项受阻不妨碍其余任务交付。

## 6. 最终只回答决策问题，不执行候选

用补查证据回答：
1. 公开0.948是否绑定到精确Version／SV，并且source是否与上传附件一致？
2. DF960现在有无正式结果？与D960／F1／G1的显示分差及排序证据是什么？
3. 是否继续把D960-V025作为下一轮单参数候选，或有直接新证据要求换方向？这里是建议，不自动批准开发／运行。

已有候选建议是D960-V025：只改原运动速度外推权重0.5→0.25，尚未实现／未正式评分；不能把它写成已验证改进。DF960有F1位置替换，不应直接把V025无差别叠加到DF960。leaf030需要分裂分支保护和缺失概率区分；既有4项CPU测试只证明边界行为，不证明71个实际删除节点中有多少误删。不要重做这些测试或为了剪枝回收全量图，本次仅确认有没有新相关证据。

附件及自有旧选参器的proxy存在官方分裂匹配口径差异；本次只在报告中保留此限制，不改评分器、选择器、候选源码或现有生产配置。无直接反证可保留V025为实验假设，但不能把“没找到反证”写成“会提分”。

## 7. 最小交付、GitHub同步和真实性

新增／更新仅限本任务研究文件和结果报告：

- `reports/20260922_GEOMETRIC_FUSION_BACKFILL_RESULTS.md`：一份简短报告，包含任务A/B/C结果、事实／假设区别、下一步建议、未闭合项和本次所有Kaggle写入0。
- `research/GEOMETRIC_FUSION_BACKFILL_20260922/backfill_evidence.json`：对应页面／固定链接、准确Version／SV、观测时间、逐单元比较、4个自有submission的只读结果、少量公开来源和访问限制；未知字段用null及原因，不填猜测值。
- 本目录 `github_readback.json`：对本次明确新增／修改payload做一次远端回读的回执，说明固定commit、文件、核验方式与结果。回执验证前一个payload commit即可，不验证自己、不递归产生回执链。

历史报告／指纹／旧CPU测试保持原样；新证据若推翻旧结论，在新结果报告明确更正，不篡改原测试结果。原始CSV、比赛数据、模型权重、凭据、浏览器Cookie、环境变量快照均不入库。不要修改main、其他实验分支、旧账本或最终选择，不创建第二套合同和多格式报告。

git工作区时只暂存明确列出的本任务文件，不使用可能夹带其他文件的 `git add .`。提交到本任务分支，普通非强制push；远端有并发更新就先核对，只整合本任务文件，不覆盖别人结果。最终确认remote HEAD与本次commit关系，按实际方式做源码／证据回读。若只有GitHub连接器，核对远端diff与文件blob即可，说明未访问本地git。

任务交付完整不等于所有问题都有答案。分别给出TASK_A/TASK_B/TASK_C状态，以及DELIVERY状态；无法绑定分数或查分受阻时用PARTIAL_BACKFILL_BLOCKED，但仍保存已有结果。不得为了写COMPLETED而补猜ID、分数或阅读范围，不套用初始调研的数量门槛。

最后给用户返回：公开0.948精确绑定表、DF960结果、是否保留V025建议、实际阻断、固定报告commit／路径、远端回读结果、Kaggle写请求0。整个任务不需要旧Mac资料，也不要求重新运行任何现有方案。
