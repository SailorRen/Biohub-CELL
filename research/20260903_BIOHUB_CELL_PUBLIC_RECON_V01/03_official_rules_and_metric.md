# 官方规则、数据与评分

## 评分公式与聚合

- `score = adjusted_edge_jaccard + 0.1 * division_jaccard`。
- 每个时间点按物理尺度后的质心距离做最优二分匹配，最大距离 7.0 µm；尺度 `z=1.625, y=x=0.40625 µm/voxel`。
- 若预测边两端都匹配到由真值边连接的真值节点，则为 edge TP；基础 Edge Jaccard 为 `TP/(TP+FP+FN)`，并对过量预测总节点数施加调整。
- 每样本 adjusted edge Jaccard 以该样本 `(TP+FP+FN)` 加权平均。
- 真值分裂定义为出度≥2；预测连通分量需覆盖分裂前阶段并触达两条子代谱系。Division TP/FP/FN 跨全部样本 micro-average 后求 Jaccard。
- 稀疏真值由 metric 处理；官方明确说明最终 score 可能超过 1.0。

## 数据与提交

- 图像是 Zarr v3，数组路径 `0/`，形状 `(T,Z,Y,X)`，典型 `(100,64,256,256)`、`uint16`；chunk `(1,64,256,256)`、blosc/zstd。
- GEFF 同样基于 Zarr v3：`nodes/ids`，`nodes/props/{t,z,y,x}/values`，`edges/ids` 为 `(N,2)` 的 source/target。
- `estimated_number_of_nodes` 是样本真实总细胞数的估计，不是稀疏标注节点数。
- train/test embryo-disjoint。可见 test 是 train copies；Notebook rerun 时换入 hidden test，hidden test 大小约同 train。
- 页面报告 24,886 files、87.61 GB、CC0: Public Domain。本轮未下载比赛数据。
- submission 字段：`id,dataset,row_type,node_id,t,z,y,x,source_id,target_id`。每个 test dataset 必须出现；node 行无效 edge 字段填 -1，edge 行无效 node/坐标字段填 -1。

## 竞赛规则

- 最大团队 5 人；每日最多 5 次提交；最多选择 2 个 Final Submissions。
- Winner source code 采用 MIT；数据访问/使用页为 CC0。
- 外部数据需公开、同等可得且免费，或满足主办方 Reasonableness 标准；外部模型/工具也受可获得性、成本和获奖者复现义务约束。

## 评分补丁与旧分边界

- 官方 Overview 当前只给出当前 metric 说明，不提供历史版本号或变更时间线。
- Code 当前列表存在 0.966/0.965/0.964 的 Best Score 卡片值，而本轮当前 Leaderboard rank 1 是 0.963；这些卡片分数没有与 GetKernel 当前源码版本或具体 submission 绑定，标为 `HIGH_EXPLICIT_HACK_OR_ABOVE_CURRENT_LB_TOP`，不能作为当前有效成绩。
- `xiaoleilian/biohub-ct-mix-divaug` 当前源码有明确注释称可选末 cell 是以 negative-time/out-of-volume hub 与 forks 操作 division term 的 “METRIC EXPLOIT”，且自称 patchable；这是 `SOURCE_CODE_VERIFIED` 的实现存在性，不证明卡片分数或当前榜有效性。
- 评分补丁的正式时间线、重算范围和 host 解释已与 Discussion 深读结果交叉核对；不把普通参赛者文字升级为官方规则。

证据：`evidence/official_pages_metadata.csv`、`evidence/browser_official_routes.json`、`evidence/browser_leaderboard_snapshot.json`、`evidence/notebook_deep_read.jsonl`。
