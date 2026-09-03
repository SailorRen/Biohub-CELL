执行任务：为 Kaggle 比赛 “Biohub - Cell Tracking During Development”
创建独立 GitHub 项目仓库，并完成第一轮公开资料全量检索、深度阅读、
证据固化和 GitHub 同步。

本任务不是只写计划。必须实际创建仓库、实际搜索、实际打开正文或源码、
实际生成研究文件、实际提交并从 GitHub 远端回读验证。

比赛入口：
https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/overview

目标 GitHub 仓库：
SailorRen/Biohub-CELL

建议本地目录：
/Users/sailor/kaggle/项目/Biohub-CELL

任务日期与文件版本：
20260903
INITIAL_RECON_V01

==================================================
一、最高优先级真实性原则
==================================================

1. 严禁编造任何比赛信息、Notebook 方法、讨论结论、GitHub 项目内容、
   Reddit 内容、数据集大小、分数、排名、版本、作者、许可证或实验结果。

2. 搜索结果标题、搜索引擎摘要、Kaggle 卡片摘要、GitHub 搜索摘要，
   均只能用于发现来源，不能用于证明来源正文中的方法或结论。

3. 只读取了标题或摘要时，必须标记为：
   TITLE_SNIPPET_ONLY
   或 METADATA_ONLY

   不得标记为：
   FULL_CONTENT_READ
   FULL_SOURCE_READ
   COMPLETED

4. 不得因为打开了 Notebook 页面，就声称已经读取完整 Notebook。
   只有下载或取得实际 Notebook 源码，并检查全部代码单元后，
   才能标记 FULL_SOURCE_READ。

5. 不得因为读取了 GitHub README，就声称读取了整个 GitHub 仓库。
   必须分别记录：
   - README_ONLY
   - TARGET_FILES_READ
   - FULL_REPO_TREE_AUDITED
   - FULL_RELEVANT_SOURCE_READ

6. 不得声称“搜索了全部公开方案”或“读取了全部讨论”，除非同时证明：
   - 检索入口；
   - 查询词；
   - 排序方式；
   - 分页范围；
   - 页面或 API 返回总数；
   - 实际获取数量；
   - 去重后数量；
   - 深度阅读数量；
   - 未读取数量及原因。

7. 无法访问、需要登录、HTTP 403、API 限流、内容已删除或正文未加载时，
   必须记录为 BLOCKED、RATE_LIMITED、DELETED、LOGIN_REQUIRED 或 UNKNOWN。
   不得根据摘要补写正文。

8. 所有结论必须区分以下证据类别：
   - OFFICIAL_FACT
   - HOST_CONFIRMED
   - SOURCE_CODE_VERIFIED
   - MEASURED
   - AUTHOR_CLAIM
   - COMMUNITY_REPORT
   - INFERENCE
   - UNKNOWN

9. 对任何 Kaggle 分数，至少保存：
   - Notebook/Submission 所有者；
   - Notebook slug；
   - Notebook Version 或 ScriptVersionId；
   - 页面显示分数；
   - 分数读取时间；
   - 分数来自 Notebook 页面、提交历史还是 Leaderboard；
   - 是否可能属于评分补丁之前的旧分数；
   - 是否能够与具体 submission 绑定。

10. 不得把过期的 Notebook “Best Score”直接当成当前有效分数。
    必须调查评分补丁、Leaderboard 重算和旧页面分数残留问题。

==================================================
二、安全边界与禁止操作
==================================================

本任务仅限建仓库和只读研究。

明确禁止：

- 不得进行任何 Kaggle 正式提交；
- 不得创建或保存 Kaggle Notebook Version；
- 不得启动训练；
- 不得启动长时间推理；
- 不得接受比赛规则或代表用户执行报名操作；
- 不得创建 Kaggle Dataset；
- 不得下载约 88GB 的完整比赛数据；
- 不得下载大型外部数据集；
- 不得修改用户其他 GitHub 仓库；
- 不得删除或覆盖任何已有目录；
- 不得提交 kaggle.json、GitHub Token、Cookie、密码、API Key 或环境变量；
- 不得把原始比赛数据、模型权重或 submission.csv 提交到 GitHub。

只允许：

- Kaggle、GitHub、Reddit、论文网站和其他公开网站的只读访问；
- Kaggle CLI/API 的 list、metadata、files、kernels、competitions 等只读命令；
- 下载公开 Notebook 源码，但仅在平台允许且许可证允许保存时提交 GitHub；
- 获取数据文件列表、大小、更新时间、许可证和元数据；
- 创建目标 GitHub 仓库并推送研究材料。

==================================================
三、GitHub 身份和仓库创建安全门
==================================================

写入前执行并保存输出：

gh auth status
gh api user --jq '.login'

principal 必须精确验证为 SailorRen。

如果不是 SailorRen：
- 禁止创建仓库；
- 禁止向任何仓库写入；
- 最终状态设为 BLOCKED_GITHUB_PRINCIPAL_MISMATCH。

检查目标仓库是否存在：

gh repo view SailorRen/Biohub-CELL

如果仓库已经存在：
- 不得覆盖；
- 不得删除；
- 不得自动改用 Biohub-CELL-2 等其他名称；
- 最终状态设为 BLOCKED_REPO_ALREADY_EXISTS；
- 报告已有仓库 URL、可见性和默认分支后停止。

若仓库不存在，则创建公开仓库：

gh repo create SailorRen/Biohub-CELL \
  --public \
  --description "Research and experiments for Kaggle Biohub - Cell Tracking During Development" \
  --clone

默认分支必须为 main。

在任何外部资料采集前，先把本任务完整原文保存为：

tasks/CODEX_20260903_BIOHUB_CELL_INITIAL_RECON_TASK.md

==================================================
四、建立仓库治理文件
==================================================

创建：

1. AGENTS.md

必须写明：

- 所有研究结论、任务、实验、日志和证据必须同步 GitHub；
- 未经用户明确授权，不得提交 Kaggle；
- 未经用户明确授权，不得启动训练或创建 Notebook Version；
- 不得把搜索摘要当成完整正文；
- 不得以推测代替数据；
- 所有“完成”声明必须经过远端回读；
- 所有 Kaggle 分数必须绑定具体版本或 submission；
- 评分补丁前后的分数必须区分；
- 未来原始数据和训练原则上留在 Kaggle 云端，GitHub 只保存代码、配置、
  小型证据和报告。

2. governance/CURRENT_PROJECT_CONTEXT.json

初始状态至少包含：

{
  "project": "Biohub-CELL",
  "competition_slug": "biohub-cell-tracking-during-development",
  "phase": "INITIAL_PUBLIC_RESEARCH",
  "kaggle_submission_authorized": false,
  "training_authorized": false,
  "notebook_write_authorized": false,
  "github_repository": "SailorRen/Biohub-CELL",
  "completion_status": "IN_PROGRESS"
}

3. README.md

必须写明：

- 比赛名称及官方入口；
- 当前项目阶段为 RESEARCH_ONLY；
- 当前没有自有 Kaggle submission；
- 当前没有经过验证的 baseline 分数；
- 本仓库不保存原始比赛数据；
- 研究报告和证据目录位置。

4. .gitignore

至少排除：

data/
raw_data/
downloads/
*.zarr
*.geff
*.tif
*.tiff
*.ome.zarr
*.zip
*.tar
*.tar.gz
*.7z
*.pt
*.pth
*.ckpt
*.onnx
submission.csv
kaggle.json
.env
.env.*
cookies*
__pycache__/
.ipynb_checkpoints/

==================================================
五、必须读取的官方比赛页面
==================================================

逐页实际读取，不得只读导航标题：

https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/overview
https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/data
https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/code
https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion
https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/leaderboard
https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/rules
https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/models

官方资料必须核实：

- 比赛目标；
- 主办方；
- 开始时间；
- 报名截止；
- 组队截止；
- 最终提交截止；
- 奖金；
- 每日提交次数；
- 最终提交选择数量；
- Public/Private 测试比例；
- Notebook CPU/GPU 时间限制；
- 网络限制；
- 外部数据和预训练模型规则；
- 团队人数上限；
- 数据许可证；
- 数据总大小；
- train/test 文件组织；
- Zarr 版本；
- GEFF 格式；
- 节点、边和分裂表示；
- estimated_number_of_nodes 的含义；
- submission.csv 字段；
- 每个 test dataset 是否必须出现在 submission 中；
- 评分公式；
- 节点匹配距离；
- 物理像素比例；
- Edge Jaccard；
- 节点数量调整项；
- Division Jaccard；
- 跨样本聚合方式；
- 是否存在评分实现更新或漏洞补丁。

对每个页面保存：

- URL；
- 页面标题；
- 访问时间 UTC；
- 访问时间 Asia/Singapore；
- 正文读取状态；
- 正文主要标题列表；
- 正文字符数；
- 页面或响应内容 SHA-256；
- 可验证的短摘录；
- 对应本地证据文件路径。

输出：

research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/
01_official_competition.md
02_official_data_inventory.csv
03_official_rules_and_metric.md
04_leaderboard_snapshot.csv

Leaderboard 快照至少包含：

- 抓取时间；
- 当前队伍数；
- Public 测试比例；
- 前 1、5、10、25、50、100 名分数；
- 相同分数聚集情况；
- 当前是否存在明显旧分数或异常分数；
- 页面无法读取时的精确失败证据。

不得根据搜索引擎摘要伪造 Leaderboard 数值。

==================================================
六、Kaggle 公开代码区/公开方案候选检索
==================================================

注意：比赛仍在进行中，Kaggle Code 区中的 Notebook 只能称为
“公开代码”或“公开方案候选”。

不能仅凭标题称其为成熟方案、金牌方案或有效高分方案。

必须使用多种排序方式检索：

- Highest Score / Best Score；
- Most Votes；
- Hotness；
- Recently Updated；
- Newest；
- 与比赛直接关联的 Code 页面。

必须使用以下关键词及合理变体：

- biohub cell tracking
- biohub-cell-tracking-during-development
- zebrafish cell tracking
- 3D cell tracking
- 3D+time microscopy
- cell lineage reconstruction
- cell division tracking
- GEFF
- tracksdata
- OME-Zarr
- adjusted edge jaccard
- division jaccard
- temporal affinity fields
- Ultrack
- Trackastra
- Cellpose
- StarDist
- 3D U-Net tracking
- graph optimization cell tracking
- transformer cell tracking

先建立完整可发现结果清单。

输出：

05_kaggle_code_inventory.csv

至少包含：

- owner；
- notebook_title；
- notebook_slug；
- URL；
- current_version；
- ScriptVersionId；
- created_at；
- updated_at；
- votes；
- comments；
- page_displayed_score；
- score_source；
- accelerator；
- runtime；
- internet_setting；
- input_datasets；
- output_files；
- license；
- read_status；
- source_saved；
- source_sha256；
- relevance；
- current_score_verified；
- stale_score_risk；
- notes。

在可访问结果中：

- 深度读取所有 Competition Host 或组织方发布的 Notebook；
- 深度读取所有官方 baseline/template；
- 深度读取至少 30 个不同 Notebook；
- 如果相关 Notebook 少于 30 个，则读取全部；
- 30 个必须覆盖高分、近期更新、高投票和不同方法类别，不能只读取同一作者的版本复制。

Notebook 深度读取标准：

1. 必须取得实际 .ipynb 或脚本源码；
2. 记录文件字节数和 SHA-256；
3. 记录 Markdown cell、code cell、output cell 数量；
4. 检查全部代码单元；
5. 记录真正的检测方法、连接方法、分裂方法和后处理；
6. 记录训练是否真实发生；
7. 记录权重来源；
8. 记录外部数据来源；
9. 记录推理耗时和资源；
10. 记录输出文件生成路径；
11. 记录 Notebook 页面分数是否能绑定具体 Version；
12. 对无源码、源码不完整、输出被清空或仅复制其他 Notebook 的情况明确标记。

输出：

06_kaggle_code_deep_read.md
07_kaggle_method_comparison.csv

方法比较至少包含：

- detection；
- segmentation；
- node extraction；
- temporal linking；
- assignment/optimization；
- division detection；
- track filtering；
- node-count calibration；
- external model/data；
- CV design；
- reported local score；
- current verified Public score；
- runtime；
- reproducibility；
- license；
- known failure；
- evidence source IDs。

必须单独调查：

- 评分漏洞修补前后的 Notebook 分数；
- 页面 Best Score 是否仍是旧分数；
- 同一 Notebook 不同版本之间的方法和分数变化；
- 高分是否来自真正的图像追踪，还是指标利用；
- 当前 Leaderboard 分数与 Notebook 页面展示是否一致。

==================================================
七、Kaggle 公开讨论区检索
==================================================

必须检索：

- Competition Host 公告；
- pinned discussion；
- metric；
- evaluation；
- division metric；
- edge jaccard；
- metric exploit；
- leaderboard recalculation；
- data format；
- sparse ground truth；
- estimated_number_of_nodes；
- external data；
- Zebrahub；
- runtime；
- memory；
- Zarr；
- GEFF；
- validation；
- CV/LB correlation；
- train/test distribution；
- submission error；
- package installation；
- internet-offline；
- baseline；
- public notebook；
- leakage；
- team merger；
- final submission。

输出：

08_kaggle_discussion_inventory.csv

至少包含：

- discussion_id；
- title；
- author；
- author_role；
- created_at；
- updated_at；
- votes；
- comment_count；
- URL；
- topic；
- read_status；
- first_post_read；
- comments_loaded；
- comments_total；
- host_reply_present；
- evidence_path；
- notes。

深度读取要求：

- 所有 Competition Host 发帖；
- 所有评分和规则变更帖；
- 所有 pinned 帖；
- 至少 30 个不同的高相关讨论；
- 若高相关讨论少于 30 个，则读取全部；
- 对重要帖子读取正文及所有可加载评论；
- 未加载全部评论时标记 PARTIAL_THREAD_READ，并记录 n/m。

输出：

09_kaggle_discussion_deep_read.md
10_host_clarifications.md

必须区分：

- 主办方正式确认；
- Kaggle 员工说明；
- 参赛者实测；
- 参赛者猜测；
- 未经验证的高分宣传。

不得把普通参赛者回复写成官方规则。

==================================================
八、GitHub 检索
==================================================

使用 GitHub Repository Search、Code Search 和普通网页搜索。

至少执行并记录这些查询及变体：

- "biohub-cell-tracking-during-development"
- "Biohub Cell Tracking"
- "Biohub" "cell tracking" Kaggle
- zebrafish 3D cell tracking kaggle
- GEFF tracksdata Biohub
- adjusted_edge_jaccard
- division_jaccard Biohub
- temporal affinity fields cell lineage
- OME-Zarr zebrafish tracking
- Ultrack zebrafish embryo
- Trackastra cell tracking
- graph optimization cell lineage

强制读取的起点：

https://github.com/royerlab/kaggle-cell-tracking-competition

同时调查：

- royerlab；
- Biohub/CZI 相关公开组织；
- GEFF；
- tracksdata；
- Ultrack；
- Trackastra；
- Cell Tracking Challenge 相关实现；
- 当前比赛参赛者公开仓库。

输出：

11_github_repository_inventory.csv

至少包含：

- owner/repo；
- URL；
- description；
- relation_to_competition；
- stars；
- forks；
- default_branch；
- latest_commit_sha；
- latest_commit_date；
- license；
- archived；
- file_count；
- read_status；
- files_actually_read；
- evidence_path；
- notes。

深度读取至少 15 个高度相关仓库；如果不足 15 个，则读取全部相关仓库。

对每个深度读取仓库：

- 固定 branch；
- 固定 commit SHA；
- 保存 tree 清单；
- 读取 README；
- 读取依赖文件；
- 读取训练入口；
- 读取推理入口；
- 读取评价代码；
- 读取数据加载代码；
- 读取 submission 转换代码；
- 读取主要模型与后处理代码；
- 检查许可证；
- 记录哪些文件实际读取。

禁止只读 README 后声称读取完整代码。

输出：

12_github_deep_read.md
13_github_code_method_matrix.csv

未经许可证允许，不得把其他仓库完整复制进新仓库。
应保存 URL、commit、文件清单、SHA、短摘录和研究笔记。
有明确开放许可证且确有必要时，才可保存源文件，并保留 LICENSE 和 attribution。

==================================================
九、Reddit 和其他公开网站
==================================================

在 Reddit 及搜索引擎执行：

- exact competition title；
- competition slug；
- Biohub cell tracking Kaggle；
- zebrafish tracking Kaggle；
- 3D microscopy Kaggle；
- GEFF cell tracking；
- Ultrack Kaggle；
- cell lineage competition。

重点检查：

- r/kaggle
- r/MachineLearning
- r/computervision
- r/bioinformatics
- r/learnmachinelearning
- 其他实际检索出的相关 subreddit

不得声称“Reddit 没有相关信息”，除非：

- 保存了全部使用的查询；
- 保存查询日期；
- 保存返回结果数量；
- 保存零结果或无关结果证据；
- 同时使用 Reddit 搜索和 site:reddit.com 网页搜索。

对命中的帖子：

- 读取完整正文；
- 尽可能读取全部评论；
- 记录帖子日期、作者、subreddit、score、评论数；
- 删除或无法加载内容必须标记；
- 不得将 Reddit 观点视为官方事实。

其他必须调查的网站包括：

- Chan Zuckerberg Biohub/Biohub 官方网站；
- image.sc Forum；
- Cell Tracking Challenge；
- Zebrahub；
- PubMed；
- Nature Methods；
- arXiv；
- bioRxiv；
- 官方软件文档；
- 相关实验室或作者的公开页面。

优先调查：

- Ultrack；
- Zebrahub；
- Cell Tracking Challenge；
- GEFF；
- tracksdata；
- Trackastra；
- Temporal Affinity Fields；
- 3D/4D microscopy tracking；
- sparse-label cell tracking；
- lineage reconstruction。

输出：

14_reddit_and_web_inventory.csv
15_external_scientific_sources.md

==================================================
十、搜索历史上类似的 Kaggle 比赛和公开方案
==================================================

在 Kaggle Competitions、Code、Writeups、Discussion 中使用：

- cell tracking
- cell detection
- cell segmentation
- nuclei segmentation
- microscopy
- biomedical image segmentation
- 3D microscopy
- time-lapse microscopy
- object tracking
- multi-object tracking
- lineage
- instance segmentation
- zebrafish
- organoid
- embryo
- fluorescent nuclei

先发现候选比赛，再进行相似度筛选。

至少列出 8 个候选历史比赛。
从中深度研究至少 5 个最接近的比赛。

不能仅因为比赛含有“cell”或“microscopy”就认定相似。
必须建立比较维度：

- 是否为显微图像；
- 2D 或 3D；
- 是否包含时间维度；
- 目标是检测、分割、跟踪还是谱系；
- 是否有细胞分裂；
- 标签是否稀疏；
- 输出是 mask、坐标、轨迹还是图；
- 评分指标；
- 数据规模；
- 计算资源；
- 是否允许外部数据；
- 是否存在完整赛后方案；
- 方法能否迁移；
- 迁移时必须修改的部分；
- 与当前比赛不兼容的部分。

输出：

16_similar_kaggle_competitions.csv
17_historical_solution_research.md

对历史方案的分数、排名、奖牌和方法，必须来自：

- 官方 writeup；
- 可绑定的 Notebook；
- 公开代码；
- 作者仓库；
- 真实 Leaderboard 记录。

不得根据博客转载或标题编造名次和分数。

不得把历史比赛的方法原样照搬到当前比赛。
报告必须说明每种历史方法如何适配当前：

- 3D+time 数据；
- 稀疏标签；
- GEFF 图；
- 当前评分；
- 12 小时 Notebook 限制；
- 无互联网推理；
- 节点总量处罚；
- 分裂拓扑。

==================================================
十一、Kaggle Datasets 区搜索
==================================================

第一部分：当前比赛数据元信息。

使用 Kaggle API/CLI 或页面获取：

- competition data 总大小；
- train/test 顶层目录；
- 文件和目录数量；
- 每个样本的名称；
- Zarr 和 GEFF 文件结构；
- 文件大小分布；
- embryo_id 和 field_of_view 命名；
- metadata 字段；
- estimated_number_of_nodes；
- 数据许可证；
- 更新时间。

只获取文件列表和元数据，不下载完整比赛数据。

第二部分：Kaggle Datasets 搜索。

至少使用：

- biohub
- cell tracking
- zebrafish cell tracking
- zebrafish embryo
- Zebrahub
- 3D microscopy
- 4D microscopy
- time lapse microscopy
- fluorescent nuclei
- cell lineage
- Cell Tracking Challenge
- OME-Zarr
- GEFF
- tracksdata
- Ultrack
- Trackastra
- Cellpose
- StarDist
- nuclei tracking
- light sheet microscopy

输出：

18_kaggle_datasets_inventory.csv

至少包含：

- owner/dataset；
- URL/ref；
- title；
- created_at；
- updated_at；
- size；
- license；
- usability；
- votes；
- download_count；
- files；
- file_formats；
- microscopy_type；
- species；
- dimensions；
- time_dimension；
- labels；
- relevance；
- possible_use；
- rule_eligibility_checked；
- leakage_risk；
- compatibility；
- read_status；
- notes。

深度检查至少 25 个高相关 Dataset 页面；若不足 25 个，则检查全部。

不得因为数据集标题包含 Biohub 就认定它是合法外部训练数据。
必须检查：

- 数据来源；
- 数据时间；
- 是否从当前比赛 test 或提交反推而来；
- 许可证；
- 是否公开且所有参赛者可合理获得；
- 是否包含当前比赛标签泄漏；
- 是否与规则兼容；
- 是否只是 Notebook 输出或 submission 文件。

任何存在泄漏风险的数据必须标记：
DO_NOT_USE_PENDING_RULE_REVIEW

不得下载大型数据集。
本轮只保存元数据、文件列表和小型说明文件。

==================================================
十二、统一来源清单和证据矩阵
==================================================

创建：

research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/
00_source_manifest.jsonl
19_claims_evidence_matrix.csv
20_access_failures.md
21_search_query_log.csv

source_manifest 每条至少包含：

- source_id
- source_type
- platform
- title
- author
- url
- query
- sort_order
- result_page
- result_rank
- access_time_utc
- access_time_singapore
- read_status
- bytes_observed
- sha256
- version_id
- commit_sha
- license
- evidence_path
- factual_use_allowed
- notes

read_status 仅允许使用：

- FULL_PAGE_BODY_READ
- FULL_THREAD_READ
- PARTIAL_THREAD_READ
- FULL_NOTEBOOK_SOURCE_AND_OUTPUTS_READ
- FULL_NOTEBOOK_SOURCE_READ
- NOTEBOOK_SOURCE_PARTIAL
- FULL_RELEVANT_REPO_SOURCE_READ
- TARGET_FILES_READ
- README_ONLY
- METADATA_ONLY
- TITLE_SNIPPET_ONLY
- BLOCKED
- RATE_LIMITED
- LOGIN_REQUIRED
- DELETED
- NOT_FOUND
- UNKNOWN

claims_evidence_matrix 至少包含：

- claim_id；
- report_section；
- claim_text；
- claim_type；
- source_ids；
- evidence_paths；
- direct_or_inference；
- confidence；
- conflict_present；
- conflict_notes。

任何报告中的重要结论都必须在 claims_evidence_matrix 找到对应来源。

==================================================
十三、研究材料目录结构
==================================================

最终仓库至少应为：

Biohub-CELL/
├── AGENTS.md
├── README.md
├── .gitignore
├── governance/
│   └── CURRENT_PROJECT_CONTEXT.json
├── tasks/
│   └── CODEX_20260903_BIOHUB_CELL_INITIAL_RECON_TASK.md
├── research/
│   └── 20260903_BIOHUB_CELL_PUBLIC_RECON_V01/
│       ├── 00_source_manifest.jsonl
│       ├── 01_official_competition.md
│       ├── 02_official_data_inventory.csv
│       ├── 03_official_rules_and_metric.md
│       ├── 04_leaderboard_snapshot.csv
│       ├── 05_kaggle_code_inventory.csv
│       ├── 06_kaggle_code_deep_read.md
│       ├── 07_kaggle_method_comparison.csv
│       ├── 08_kaggle_discussion_inventory.csv
│       ├── 09_kaggle_discussion_deep_read.md
│       ├── 10_host_clarifications.md
│       ├── 11_github_repository_inventory.csv
│       ├── 12_github_deep_read.md
│       ├── 13_github_code_method_matrix.csv
│       ├── 14_reddit_and_web_inventory.csv
│       ├── 15_external_scientific_sources.md
│       ├── 16_similar_kaggle_competitions.csv
│       ├── 17_historical_solution_research.md
│       ├── 18_kaggle_datasets_inventory.csv
│       ├── 19_claims_evidence_matrix.csv
│       ├── 20_access_failures.md
│       ├── 21_search_query_log.csv
│       ├── evidence/
│       ├── licensed_notebooks/
│       └── licensed_source_extracts/
├── reports/
│   ├── 20260903_BIOHUB_CELL_INITIAL_RESEARCH_REPORT_V01.md
│   ├── 20260903_BIOHUB_CELL_INITIAL_RESEARCH_VERIFY.json
│   └── completion_claim.json
└── scripts/
    └── verify_research_bundle.py

不得把无明确再分发许可的完整网页、Reddit 帖子或 Notebook
直接复制进公开 GitHub 仓库。

对无明确许可证的来源，应保存：

- URL；
- 作者；
-日期；
- 页面版本；
- 内容哈希；
-短摘录；
- 自己撰写的摘要；
- 实际读取范围。

==================================================
十四、最终研究报告内容
==================================================

生成：

reports/20260903_BIOHUB_CELL_INITIAL_RESEARCH_REPORT_V01.md

报告至少包含：

1. Executive Summary
2. 本轮实际读取范围
3. 搜索覆盖统计
4. 官方比赛规则和时间线
5. 数据结构和规模
6. submission.csv 与 GEFF 图结构
7. 官方评分实现
8. 评分补丁和旧分数风险
9. 当前 Leaderboard 快照
10. 官方 baseline
11. Kaggle 公开代码方法分类
12. 高相关公开 Notebook 深度比较
13. 公开讨论中的官方确认
14. GitHub 代码生态
15. Reddit 和其他社区情况
16. Cell Tracking Challenge、Ultrack、Zebrahub 等相关研究
17. 类似 Kaggle 历史比赛
18. Kaggle Datasets 候选
19. 外部数据合法性和泄漏风险
20. 当前可复现资源
21. 当前未知事项
22. 被阻断的来源
23. 下一阶段建议调查事项

报告中的“下一阶段建议”只能基于已取得证据。

本轮不得设计并宣称某个新模型会提升分数。
可以列出候选方向，但必须写成：

- 已有来源证明了什么；
- 当前比赛中还没有证明什么；
- 后续需要怎样的本地 CV 或 Kaggle 提交来验证；
- 在取得真实测量前不得评价其优劣。

==================================================
十五、机器验收
==================================================

创建 scripts/verify_research_bundle.py，至少检查：

- 必需文件是否存在；
- 必需文件是否非空；
- CSV 是否有表头和数据行；
- source_manifest 是否为有效 JSONL；
- 每条关键 claim 是否有 source_id；
- evidence_path 是否存在；
- FULL_* 状态是否具有字节数和 SHA-256；
- Notebook FULL_SOURCE 状态是否有源码哈希和 cell 统计；
- GitHub 深读记录是否有固定 commit；
- 是否存在 TODO、TBD、PLACEHOLDER、待补充；
- 是否意外提交 kaggle.json、Token、Cookie 或 .env；
- 是否存在超过 20MB 的文件；
- 是否存在 .zarr、.geff、模型权重或 submission.csv；
- 是否满足最低深度阅读数量；
- 是否记录所有失败访问；
- 是否记录所有搜索查询；
- 是否存在没有证据支持的完成声明。

输出：

reports/20260903_BIOHUB_CELL_INITIAL_RESEARCH_VERIFY.json

验证结果必须包含逐项 PASS/FAIL，不得只输出总计。

==================================================
十六、GitHub 提交和远端回读
==================================================

完成后执行：

git status
git add -A
git commit -m "Initialize Biohub CELL project and public research evidence"
git push -u origin main

然后验证：

LOCAL_HEAD=$(git rev-parse HEAD)
REMOTE_HEAD=$(git ls-remote origin refs/heads/main | awk '{print $1}')

要求：

- LOCAL_HEAD == REMOTE_HEAD；
- git status --porcelain 为空；
- git rev-list --left-right --count origin/main...HEAD 为 0 0。

必须从 GitHub 远端重新下载至少以下文件并计算 SHA-256，
与本地逐个比较：

- AGENTS.md
- README.md
- governance/CURRENT_PROJECT_CONTEXT.json
- 00_source_manifest.jsonl
- 03_official_rules_and_metric.md
- 05_kaggle_code_inventory.csv
- 08_kaggle_discussion_inventory.csv
- 11_github_repository_inventory.csv
- 16_similar_kaggle_competitions.csv
- 18_kaggle_datasets_inventory.csv
- 19_claims_evidence_matrix.csv
- 最终研究报告
- VERIFY.json

不得仅依据 git push 返回 0 就声称 GitHub 同步完成。

==================================================
十七、完成状态规则
==================================================

只有同时满足以下条件，才允许标记：

COMPLETED_VERIFIED

条件：

- GitHub principal 已验证；
- 新仓库真实创建；
- 官方页面真实读取；
- Kaggle Code 已检索并达到深读要求；
- Discussion 已检索并达到深读要求；
- GitHub 已检索并达到深读要求；
- Reddit 和其他网站已实际搜索；
- 类似 Kaggle 比赛已研究；
- Kaggle Datasets 已研究；
- 所有搜索和失败均有证据；
- 没有标题推断方法；
- 没有编造分数；
- 没有大型数据进入 GitHub；
- 验证脚本全部通过；
- local/remote HEAD 一致；
- GitHub 远端文件 SHA-256 回读一致；
- 工作区干净。

如果仓库已创建，但任一强制研究来源完全没有搜索，
或最低深度阅读要求未达到，状态必须是：

PARTIAL_RESEARCH_BLOCKED

如果实际搜索后确实没有 Reddit 或某类资料，但查询和零结果证据完整，
可以标记：

COMPLETED_VERIFIED_WITH_NOT_FOUND_SOURCES

不得把 NOT_FOUND 改写成“已读取全部但没有有用信息”。

==================================================
十八、最终向用户报告
==================================================

最终回复必须列出：

- 最终状态；
- GitHub 仓库 URL；
- 最终 commit SHA；
- local HEAD；
- remote HEAD；
- ahead/behind；
- 工作区状态；
- 官方页面读取数量；
- Kaggle Notebook 发现数量；
- Notebook 深度读取数量；
- Discussion 发现数量；
- Discussion 深度读取数量；
- GitHub 仓库发现数量；
- GitHub 仓库深度读取数量；
- Reddit 命中数量；
- 类似比赛数量；
- Kaggle Dataset 数量；
- FULL_READ 数量；
- METADATA_ONLY 数量；
- TITLE_ONLY 数量；
- BLOCKED 数量；
- NOT_FOUND 数量；
- 验证脚本 PASS/FAIL 数量；
- 远端 SHA-256 一致数量；
- 未解决问题；
- 本轮 Kaggle submission 数量，必须为 0；
- 本轮 Kaggle Notebook 写入数量，必须为 0；
- 本轮训练任务数量，必须为 0。

不得只回复“任务完成”或只提供一个报告链接。