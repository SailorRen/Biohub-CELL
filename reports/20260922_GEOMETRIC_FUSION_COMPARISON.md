> GitHub交接归档说明（2026-09-22）：以下为此前会话的分析报告，供新电脑Codex续接使用，不是本次重新研究或查分。原报告末行“尚未同步GitHub”是原分析时的历史说明；本次将报告纳入交接包。文中本地测试文件改从同提交 `research/GEOMETRIC_FUSION_BACKFILL_20260922/leaf_guard_unit_checks.json` 读取，不访问旧电脑或sandbox。
> 原报告字节SHA256：`fa3bf73f8ff9708467efd5c4ea9e902ca583b18bcc8a190df51b5c266866a841`。新分析应作为新报告追加，不篡改原有结论。

# Biohub Geometric Fusion：源码对比与可迁移改动

分析日期：2026-09-22（UTC+8）。范围：上传 Notebook 静态审查、已存运行输出读取、GitHub 固定源码/报告核对、公开网页检索、4项合成图 CPU 函数测试。没有执行整本 Notebook、训练、GPU 推理或 Kaggle 写请求；没有修改 GitHub 或最终选择。

## 1. 来源与精确边界

- 上传文件：biohub-geometric-fusion.ipynb；SHA256 `940ccce3466a8fdbbe4ead62c1bf33faef23054958ddf92d62858f81bdef774f`。
- 共12个代码单元，展开source为4437行（包含内嵌代码字符串）；全部AST解析通过。重点审查融合、motion、division、leaf prune、局部评分、选参、最终CSV写出及运行输出。没有审计全部外部依赖执行链。
- 附件已有运行时间：2026-09-21 09:18:44–13:15:25 UTC，约3小时56分41秒；这是已存运行记录，不是本次运行。
- 用户给出的0.948尚未由本次在线读取绑定到amanatar的精确Version/SV/submission。该页面本次未返回可读正文，不能把Notebook局部0.9530当作正式Public。
- D960固定代码：SailorRen/Biohub-CELL，commit `1cf89f1f9380f005d98e9cb15ca9f5d80c4ebaca`，`experiments/BIOHUB_SCORE_TRIO_20260921_V01/D960/candidate.ipynb`。D960 submission56416049 / V1 / SV351441983，历史Public0.948。
- G1 gate固定代码：commit `e9c7c63b896812660a78ec55fc3284c10f85e776` 下 `experiments/BIOHUB_SPRINT01_20260916/{build_production.py,production_module.py,division_patch.py}`。
- DF960报告固定：commit `34df61552d4331c999148c2db684c3c9a217c43f` 下 `reports/20260921_BIOHUB_DF960_ONE_SHOT_V01.md`。已提交56445846 / V1 / SV351617874；最后归档查分为2026-09-22 08:00:31上海，PENDING、Public=null。本次不是实时Kaggle查分。

## 2. 差异摘要

|维度|上传公开方案|D960 / DF960|
|---|---|---|
|主干|双seed UNet/关联模型、DeepCenter、TTA、ILP|同家族；不是新增独立模型路线|
|检测阈值|0.965|0.960|
|双向融合|harmonic_probability，反向0.15|同样harmonic_probability / 0.15|
|运动预测|单轨速度外推，最终权重0.25|D960原权重0.5；DF960在有覆盖节点使用F1邻域中位位移|
|新增分裂过滤|无本项目G1训练后冻结的分裂分类门|保留G1概率0.95过滤，缺上下文时原规则回退|
|DeepCenter分裂门|初始0.25，最终选0.15|0.20；不同于G1分类器的0.95|
|安全分裂几何|最终11 / 16 / 12 µm|9 / 14 / 10 µm|
|弱末端剪枝|新增，最终阈值0.30|没有该独立步骤|
|后处理选择|24个预设候选＋按条件形成组合；按胚胎前缀限制退化；从高到低找首个合格者|7个预设候选＋按条件组合；原逻辑只检查第一名|

公开方案的融合公式是加权调和平均：`h = 1/(0.85/p_forward + 0.15/p_reverse)`，随后归一化和logit校准，不是几何平均。

附件中三份推理权重预期SHA256：
- primary: `12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771`
- secondary: `9bac2fa0dadc4a6fc1899e0caf187f4b553e0a7cd90ba1261a68b35ffe9e305f`
- DeepCenter: `8040999a92f6b7bbd98fa8cf458141e045c0f9ad7c936bdb3b18e1f7edafe2a0`

## 3. 附件局部试验记录（不是官方重新评分）

|候选|旧proxy|adjusted edge|division TP/FP/FN|
|---|---:|---:|---|
|base|0.9490|0.9260|3/1/9|
|tight55|0.9511|0.9280|3/1/9|
|tight55 + leaf030|0.9514|0.9284|3/1/9|
|vel025|0.9505|0.9274|3/1/9|
|leaf030 / leaf040|0.9494|0.9263|3/1/9|
|组合|0.9530|0.9300|3/1/9|
|diverge150|0.9428|0.9261|3/6/9|

数值原样抄录附件四位日志，非重新计算；例如leaf行显示差+0.0003与四位值相减不完全一致，属于四舍五入信息限制。宽分裂/降低DeepCenter门的单项没有显示额外分裂TP，不能把组合增益归因于分裂召回改善。

最终实际覆盖参数为：tight=5.5，leaf=0.30，几何11/16/12，DeepCenter=0.15，velocity=0.25。组合名称虽同时包含dcsd015和dcsd010，`setdefault`只保留实际0.15。

最终普通输出日志记录4样本剪枝10、9、0、52个节点，总计71节点/71边。最终CSV241311行、122764节点、118547边；本次没有独立下载该实际CSV，所以这些是日志证据。

## 4. 两个剪枝迁移风险

原函数仅检查末端节点出度0、入度1、非图内最后一帧、入边概率低于阈值。它没有检查父节点是否分裂。

本次提取原函数做合成图CPU测试，结果见 `leaf_guard_unit_checks.json`：
1. 父节点分成两支，其中一支是非最后帧的0.2概率叶子：原函数删除该子节点，将父节点出度2变1。
2. 同一子节点概率None：不删。
3. 同一子节点概率0.0：删除。
4. 最后一帧子节点低概率：不删。

另提取原motion函数内的learned_prob验证：不存在的概率返回0.0。因而“缺少模型评分”和“真实低评分”在后续剪枝处可能混淆。合成测试证明边界行为，不证明附件71次删除中发生了多少次此风险，也不是准确率实验。

拟迁移时应保护分裂父节点的两个分支、保留缺乏实际模型概率的运动/修复边、不递归级联删除、保留最后帧和原图不变量。先用已有图/概率记录确认存在可剪候选，不为此另起完整GPU诊断。

## 5. 共同的局部评分问题

附件cell8的compute_division_confusion使用全图弱连通分量与全部后代。D960固定源码cell8同样保留这一旧逻辑。官方metrics.md要求局部有向分叉和独立子分支，全图连通不等价。

因此，上述proxy只可作为探索性证据，不能替代当前官方分数；已完成的真实Public也不会因该源码发现而失效。后续需要离线比较时应复用现有官方评分器、评价最终CSV往返后的图，不新建一套评分框架，也不修改已提交版本。

## 6. 迁移顺序建议（未执行、无提分承诺）

优先单候选：D960-V025，只把实际motion速度外推权重0.5改为0.25，其他模型、G1门、几何和选择器规则不变，不增加参数扫描。依据是作者单项局部边指标改善和改动范围小；在本项目Public上尚未验证。

第二候选：带上述保护的leaf030。它与公开原版不同，不能继承作者0.948结论；可能因为保护后没有合法变化而不值得提交。不要同时组合V025、宽分裂和leaf。

DF960当前有邻域位移覆盖，覆盖节点原predicted被F1替换，所以不能假定velocity0.25在DF960上产生相同效果。先读取既有DF960正式结果，不取消/重跑它。

选择器“第一名不合格就检查下一名”是小型逻辑修正，值得保留为单独后续改动；两胚胎前缀保护不等于未见模型独立验证。不要整体复制24候选扫描。

## 7. 公开区检索与证据限制

本次检索可读取一些Kaggle正文/索引缓存，但未获得amanatar目标页及742064、741749、742266的新完整正文，也未完整遍历9月21日晚至22日全部新帖。不把缓存的“几天前”当成今天发帖，不宣称找到全网最高分。

- 同家族实现：flexonafft/biohub-harmonic-fusion，可读取页面V30显示Public0.947；原Lineage Forge日志也显示同类融合、后处理选择。新名字不等于新模型。
- 运动关联：讨论739685作者报告局部波动与榜单变化不一致，是作者经验，不是可保证的改善幅度。DF960报告另归档了9月21日742266的类似反馈；本次没有该帖实时正文。
- FOCUS-3D/长时窗：讨论738217提出密集伪标注、坐标域校准、更长时序匹配，也有超时和无明显成绩的反馈。属于需要训练和泛化验证的路线，不建议在本轮直接替换现有主干。
- HOCT：讨论726521主办方作者给出推理代码和权重，但该帖明说未在比赛数据上试验，依赖分割质量；不能认定接入即可涨分。
- 评价一致性：官方metrics.md是检查局部分裂评分的重要依据；排名刷新讨论736937提示旧Notebook展示分可能混淆，需精确版本绑定。

### 公开来源入口

- https://www.kaggle.com/code/amanatar/biohub-geometric-fusion （用户提供；本次页面不可读，源码来自附件）
- https://www.kaggle.com/code/flexonafft/biohub-harmonic-fusion
- https://www.kaggle.com/code/flexonafft/biohub-lineage-forge-precision-tracking/log
- https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/739685
- https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/738217
- https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/726521
- https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/736937
- https://github.com/royerlab/kaggle-cell-tracking-competition/blob/main/metrics.md

本文件是当前会话分析附件，尚未同步GitHub；不是新实验任务或平台运行回执。
