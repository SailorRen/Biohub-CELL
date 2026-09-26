# 公开榜单与代码增量核查（9月26日夜间）

观测窗口：2026-09-26 23:57 至 2026-09-27 00:04，中国上海时区。
分支：codex/public-lb-update-20260926。只读研究；训练、推理、Notebook保存、正式提交、最终选择修改均为0。

## 结论

本次覆盖范围内，没有发现超过 XR0 0.953、且能绑定精确版本正式分数的新公开完整方案。排行榜已有0.975，但排行榜分数不能证明其实现公开。新增实质源码有漂移校正、连接竞争消歧、断轨及分裂后续链修复；目前均不足以声称在XR0上提分。

## 排行榜证据（MEASURED / OFFICIAL_FACT）

[公开榜单](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/leaderboard)：Sergio Alvarez、Gabriel均0.975；第三yu4u为0.973；第20为0.965；第49为0.961。本队Sailor Ren / Dongdongjiaqi为第498名、0.953，最新提交0.952，最佳仍0.953。共3931名次。此处是本次观测快照，不宣称这些榜首分数全部是今天新增。

页面显示Public约29%测试集、Private为其余71%；截止时间为2026-09-30 07:59上海时间。未据此调整最终选择。

## 公开代码（版本绑定）

| 对象 | 本次事实 | 含义 |
|---|---|---|
| [Raunak Harmonic Fusion V3 V5 / SV352639153](https://www.kaggle.com/code/raunakdey07/biohub-harmonic-fusion-v3?scriptVersionId=352639153) | MEASURED：Public 0.953，GPU T4×2，16m48s | SOURCE_CODE_VERIFIED：完整下载12个有效代码单元并逐单元AST及差异核查；相对XR0仅发现注释/docstring、日志及time导入位置变化，没有识别出算法改动。不能作为独立升级。 |
| [Aman optimized V4 / SV352554580](https://www.kaggle.com/code/amanatar/optimized-biohub-max-score?scriptVersionId=352554580) | MEASURED：精确页面目前Public为0.953，1h56m53s | 更新9月25日旧观察：旧报告当时未见该分数，现有新证据；仍没有超过XR0。 |
| [Aman 最新V5 / SV352997256](https://www.kaggle.com/code/amanatar/optimized-biohub-max-score?scriptVersionId=352997256) | MEASURED：页面明确标注最新运行error，2h24m12s；Best Score 0.953链接仍指V4，V5未显示Public | 不能用列表卡片0.953为最新源码背书。直接异常根因UNKNOWN，本次没有诊断运行。 |
| [Track Your Cells](https://www.kaggle.com/code/anhadmahajan06/biohub-track-your-cells) | 最新运行列表显示约13分钟前更新、卡片0.946 | 仅发现线索，未深读或绑定评分版本；不列为高分新方法。 |

Aman V5完整源码已下载，12/12有效单元AST可解析，针对新增函数、配置及自动选择器进行静态深读，未标记完整语义审计。源码存在子链延伸、常速度合成补点、端点重接、低竞争差值父节点重分配，以及读取预测GEFF节点数元数据的裁剪目标。上述新增开关初始为0，进入sweep候选；validator则开启。因此“源码中有功能”不能推导“实际产物采用了功能”。尤其节点数元数据可能缺失并回退，不能声称拥有隐藏测试真值数量。

一个具体工程风险：close_predicted_gaps在挑选终点时依赖原in_map，追加桥后没有更新目标的in_map，静态上存在多个桥选择同一终点的风险；未执行该分支，不能据此认定是页面报错原因。不建议整份移植。

## 新增公开研究与负面结果

固定研究仓库commit：[kito 33220916c88f707f097b46a68751b4f33c6c9f22](https://github.com/kito2718/kaggle_Biohub-Cell_Tracking_During_Development/tree/33220916c88f707f097b46a68751b4f33c6c9f22)，更新于2026-09-26 19:23:37上海时间。读取三部分实验记录的相关章节及052针对性源码，不是全仓审计。

- AUTHOR_CLAIM：[summary2](https://github.com/kito2718/kaggle_Biohub-Cell_Tracking_During_Development/blob/33220916c88f707f097b46a68751b4f33c6c9f22/s7_summary/s7_summary2.md) 现记录049边界校准Public **0.948**，低于其041b基线0.949；043c样条和048形态单项保持0.949。此前边界方向应下调优先级，不能继续用旧局部提升支持直接移植。
- AUTHOR_CLAIM：[summary3](https://github.com/kito2718/kaggle_Biohub-Cell_Tracking_During_Development/blob/33220916c88f707f097b46a68751b4f33c6c9f22/s7_summary/s7_summary3.md) 的052–056新增漂移、竞争感知匹配与后续组合。作者记录局部GT Micro Jaccard 0.89404→0.92426/0.92429；五项正式结果仍写PENDING（56567134、56568172、56569861、56572153、56573659）。这只代表固定文档的自报，非当前官方队列状态；0.960+～0.978+是目标，不是成绩。尝试读取056 Kaggle页返回“找不到页面”，实际Public为UNKNOWN。
- SOURCE_CODE_VERIFIED：[052实现](https://github.com/kito2718/kaggle_Biohub-Cell_Tracking_During_Development/blob/33220916c88f707f097b46a68751b4f33c6c9f22/working/s7_052_physics_drift_sota/s7_052_physics_drift_sota.ipynb) 在12μm内取至多3近邻位移，用2.5μm一致性投票得到整体平移，再以0.35μm软收缩，校正搜索中心并做Hungarian匹配。实现是对候选位移逐一全量比较，不是高效随机采样；候选数大时有平方级开销。只估计平移，不足以说明旋转也被纠正。XR0已具备seed邻域flow，不能把它视作XR0完全缺失的模块，也不能直接再加一次位移。

## 最新讨论（COMMUNITY_REPORT）

[743222：八次公开栈实验负收益](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/743222)：作者报告关闭motion relink本地+0.017但Public−0.002，额外Z翻转、检测阈值0.960/0.970、secondary权重0.65均未超过原版；还指出自动验证样本随隐藏测试集合变化，可能选出不同后处理。数字未绑定可独立读取的submission，不能视作本队实测，更不能据此证明0.965全局最优。对本队的意义是不要恢复动态自动选择器，也不要仅凭训练集局部提升追加阈值网格。

[742942：标注误差](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/742942)：正文及4条评论报告分裂位置、链接和漏标问题。没有官方确认或统计复核；不能将其当作本队掉分的已证实解释，也不应人为拟合猜测中的标注噪声。

## 对本队的优化方向（INFERENCE，未执行）

1. **优先审查flow失配下的整体漂移补偿。** 只对现有flow无足够样本或估计不可靠的情况研究补偿；先辨别整体运动和细胞自身运动，防止与seed flow重复相加。新公开实现的耗时和密集区错误共识需先解决。比重复扫DET/velocity阈值更有新的信息来源，但收益UNKNOWN。
2. **其次审查小范围竞争连接修复。** 固定XR0检测节点、head和基础flow，仅查看候选距离接近、前后轨迹不一致的连接；保持唯一父节点和时间方向，避免全图重新连接、无图像依据合成补点或粗暴剪分裂。Aman新源码仅提供思路，其V5报错，不能直接用作母版。
3. **暂缓边界固定Z、泛化分裂gate及训练集自动sweep。** 本队三候选正式回收XV25=0.953、XG95=0.929、XV25G95=0.952，均未超过XR0。证据见[固定三候选报告4033cdf](https://github.com/SailorRen/Biohub-CELL/blob/4033cdf778b70cf6957107efaaebeb729f122f7c/reports/20260926_BIOHUB_XR0_TRANSFER_TRIO_RESULTS.md)。一次Public不能证明稳定因果，但足以说明本批没有支持继续放大G1的正收益证据。

## 覆盖与限制

浏览当前排行榜、Code Public Score/Recently Run/Recently Created各首批20项（重叠不去重计独立方法）、Discussion近期评论首屏；深读2篇讨论正文及742942的4评论；下载2份完整Kaggle代码做24个有效单元AST与差异分析，针对性读取Kito052。列表沿用页面excludeNonAccessedDatasources=true，未宣称覆盖不可访问输入的所有Notebook。未搜索整个互联网或所有排名靠前队伍的私有实现。

只同步报告、哈希、出处和小型检查，不同步CSV、权重、原始数据或凭据。机器可检查来源字段及交付一致性；优化判断仍需后续实验或人工复核，不是提分保证。
