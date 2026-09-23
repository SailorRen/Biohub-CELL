# 025提分后：三候选设计与公开信息核查

日期：2026-09-23。状态：DESIGN_READY_EXECUTION_PENDING。本文件不是Kaggle新提交或实时分数回执。

## 已确认的项目依据

来源分支codex/two-wave-four-submit-20260922，本轮回读HEAD为4fc1703fea6e4dbef254ce99b8113f9115409f88。

1. b00be3c7377876a8116ffc6b04eba6cb29c370f0的reports/20260922_BIOHUB_TWO_WAVE_RESULTS.md末节归档A 56456090/V1/SV351739212 COMPLETE Public0.950、D960 56416049/V1/SV351441983 0.948。本轮没有重新读取登录态正式列表；不能冒充实时查询。
2. 用户当前截图新增证据：dongdongjiaqi名下biohub-d960-l030p-20260922 Version1出现在比赛Submissions，Notebook Running；submission ID和分数未显示。这是已提交在跑的B，不再“补交原B”。
3. 4fc1703下A/consumption_precheck.json显示实际velocity0.25，所选标签combo(tight55+bonus125+relaxed9)。因此单独宣称“加入tight55”为新改进有重复风险。
4. 原两批任务第6节已有V025+L030P、V025+L020P、V0375计划，但旧计划需A/B同时出分及原额度周期。本次用户新增几方案跑分要求下，采用新批预算，优先不依赖B结果的V0375和L020P，第三份L030P保留正向先验结果门槛。
5. Geometric Fusion比较和回读报告已绑定公开V3/SV351532492的整体Public0.948；其单项velocity、leaf、tight的局部proxy并非正式单项成绩。不能把局部0.9530当可复制Public。保护剪枝与作者原始叶子删除不同，必须独立验证。

## 本轮公开检索及限制

本轮实际搜索Kaggle讨论／代码、读取可返回正文的讨论及日志、检索GitHub仓库并读取指定文件。网页Discussion最新排序、Code最近更新、amanatar主Notebook页及742064/741749/742266直接打开失败；默认Discussion没有正文。部分结果为上周／前几日缓存。没有覆盖9月23日全部新增内容，不能声称发现新的完整0.95以上公开方案，也不能宣布公开区无新方案。执行任务安排最多15分钟登录态增量补查。

可读的公开方向：
- FOCUS3D讨论738217涉及密集伪标注、将分割质心校准到Kaggle标注坐标、长时窗关联；原帖也有超时和无明显结果反馈。本轮不投入新分割／训练路线。来源为作者和评论者经验，未独立复现。
- motion讨论739685报告离线变动与LB变化不一致，支持实际Public验证，不支持据局部proxy预测提分。
- 736937及官方728324提示历史指标修补后旧Notebook显示分可能残留，不能按Highest Score卡片直接采用。
- 可读flexonafft Lineage Forge日志出现tight55；与我们的025实际选择回执相结合，排除将已启用选项重新包装。
- GitHub检索返回若干外部仓库；本轮读取pomagrenate/biohub-cell-tracking的5423530b62195756635badb8f195a27620788d0d README，仅READ_ME级检查，不据此认定其训练／推理已复现或成绩更强。
- 官方royerlab/kaggle-cell-tracking-competition检索最新提交为075fc5f5a52d11077f9dc2b074644618f26939e2（2026-07-18）。完整读取metrics.md：真实分裂须局部有向拓扑、两条不同子分支且不能合并；这支持保留B分裂保护，不能靠节点删除保证提高分数。

本轮未新增任何性能／精度测算。所有新参数结论均为INFERENCE，必须以正式提交验证。

## 本批设计

|候选|设置|测量问题|
|---|---|---|
|V0375|A的velocity0.25改0.375，leaf=None|在0.25／0.5间作一个插值点，不假设单调关系|
|V025-L020P|velocity0.25＋保护leaf0.20|更保守末端剪枝能否改善A|
|V025-L030P|velocity0.25＋保护leaf0.30|较强剪枝与已提分运动参数的互作；B>=D960或L020P>=A时才推进正式运行|

每份保留原7项选择器和固定模型，不强制沿用A普通选出的配置；候选改变后选择结果可变，须记录。不复跑A原版或队友已在跑的B，不为填满额度提交相同实际输出。三份都不保证提高0.950。

## 执行现实

sailorren零GPU时数的编辑器直接提交已被明确拒绝；用户截图显示现有队友副本已受理。当前可用路线是Codex准备私有母版并共享，队友本人复制、运行、提交。不能假定其历史18小时仍是当前余额，不能代登录或绕过账号配额。

本会话已发现的工具能读写GitHub，但没有Kaggle登录态写入／浏览器操作工具；插件管理本轮仅提供权限管理接口，没有可用的安装搜索动作。容器下载GitHub原始文件也因DNS失败。这些限制意味着本轮实际交付是研究与执行任务，不是已经生成Kaggle母版或提交得分。Codex需读取完整A/B源码并完成构建和平台上传。平台真实状态须另记，不把任务发布算作模型执行。

## 来源入口

- https://github.com/SailorRen/Biohub-CELL/blob/b00be3c7377876a8116ffc6b04eba6cb29c370f0/reports/20260922_BIOHUB_TWO_WAVE_RESULTS.md
- https://github.com/SailorRen/Biohub-CELL/blob/4fc1703fea6e4dbef254ce99b8113f9115409f88/experiments/BIOHUB_TWO_WAVE_20260922_V01/A/consumption_precheck.json
- https://github.com/SailorRen/Biohub-CELL/blob/4fc1703fea6e4dbef254ce99b8113f9115409f88/tasks/CODEX_20260922_BIOHUB_TWO_WAVE_FOUR_SUBMISSIONS_V01.md
- https://github.com/SailorRen/Biohub-CELL/blob/4fc1703fea6e4dbef254ce99b8113f9115409f88/reports/20260922_GEOMETRIC_FUSION_COMPARISON.md
- https://github.com/SailorRen/Biohub-CELL/blob/4fc1703fea6e4dbef254ce99b8113f9115409f88/reports/20260922_GEOMETRIC_FUSION_BACKFILL_RESULTS.md
- https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/738217
- https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/739685
- https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/736937
- https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/728324
- https://www.kaggle.com/code/flexonafft/biohub-lineage-forge-precision-tracking/log
- https://github.com/royerlab/kaggle-cell-tracking-competition/blob/075fc5f5a52d11077f9dc2b074644618f26939e2/metrics.md
- https://github.com/pomagrenate/biohub-cell-tracking/blob/5423530b62195756635badb8f195a27620788d0d/README.md
