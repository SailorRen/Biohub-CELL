# Kaggle Code 源码深读（staging 草稿）

## 覆盖结论

- 5 种 competition Code 排序实际加载：Most Votes、Hotness、Recently Created、Recently Run、Public Score。
- 20 个指定关键词全部实际检索；`temporal affinity fields` 返回 0 条可见结果，其余实际返回 10–20 条。
- 可见 occurrence：排序 104 + 关键词 356 = 460；按 `owner/slug` 去重后 194。
- 实际 GetKernel 当前源码：30/30 成功，来源 25 个不同作者；最大单一作者 3 本。
- 源码合计 3,022,497 bytes；340 cells = 122 markdown + 218 code。218 个 code cells 全部生成 SHA 并做语义扫描。
- 输出：30/30 的 GetKernel 源码均为 0 个 output-bearing cell、0 个 output item。因此训练执行、推理成功、运行时、本地得分与产物存在均 `NOT_VERIFIED`。
- Current version number 30/30 有值；ScriptVersionId 0/30 被当前 GetKernel 响应暴露，统一为 `UNKNOWN`。`metadata.id` 另存为 `kernel_metadata_id`，不冒充 ScriptVersionId。
- 页面 Best Score 30/30 未绑定当前源码版本或 submission；`current_score_verified=false`。

## 源码级方法观察

- pinned getting-started：uniform filter + percentile threshold + connected-label centroids；相邻帧 `linear_sum_assignment`；写 `submission.csv`。
- host/organizer baseline candidate：离线 repo/wheels + edge predictor weight；高 detection threshold；可选全局 ILP；写 GEFF/CSV。当前 Notebook 是 inference，未见训练输出。
- Trackastra：DoG、`peak_local_max`、可选 marker watershed，把 4D 结果交给 Trackastra graph transformer，并对孤立/短轨做处理。
- Classical/3D U-Net：Otsu/局部峰值或 3D U-Net heatmap；cKDTree/Hungarian、运动门限、保守分裂、短轨剪枝。
- 多个近期高分候选：TemporalUNet3D + node transformer edge score + ILP，再做 gap recovery、motion relink、safe division、node-count/short-track filtering。源码存在不等于作者声称分数已被本轮复现。
- Cellpose candidate：current code 调用 Cellpose slice/stitch 检测并用 Motile ILP；但 metadata `internet=false` 且 outputs=0，无法证明运行时依赖安装成功。
- 标题为 StarDist/btrack 的候选：StarDist 仅在 markdown 叙述命中，current code cells 未命中 StarDist symbol；代码实际可见 DoG/local maxima 与 fallback tracking，故不把标题当实现证明。
- 明确 exploit：`xiaoleilian/biohub-ct-mix-divaug` 当前源码注释写出 fake out-of-volume/negative-time hub + forks；其页面当前卡片 0.884，与旧高分卡片情形不可混为一谈。

## code-cell 类别计数（30 本中出现次数）

- `detection_dog_log`: 17/30
- `detection_local_maxima`: 9/30
- `detection_threshold`: 30/30
- `division_detection`: 25/30
- `gap_closing`: 22/30
- `linking_graph`: 26/30
- `linking_hungarian`: 25/30
- `linking_nearest_neighbor`: 19/30
- `metric_division_jaccard`: 13/30
- `metric_edge_jaccard`: 16/30
- `model_3d_unet`: 19/30
- `model_cellpose`: 1/30
- `model_trackastra`: 1/30
- `motion_kalman`: 17/30
- `node_count_calibration`: 24/30
- `optimization_ilp_motile`: 21/30
- `segmentation_connected_components`: 13/30
- `segmentation_watershed`: 1/30
- `submission_generation`: 30/30
- `track_filtering`: 23/30

## 30 本逐项

`M/C/O` 为 markdown cells / code cells / output-bearing code cells。

| Notebook | current version / ScriptVersionId | bytes | M/C/O | code-verified categories | page card score |
|---|---|---:|---:|---|---:|
| `nusrati/0-938` | V3 / UNKNOWN | 196,950 | 0/10/0 | detection_dog_log, detection_threshold, division_detection, gap_closing, linking_graph, linking_hungarian, linking_nearest_neighbor, metric_division_jaccard, metric_edge_jaccard, model_3d_unet, motion_kalman, node_count_calibration, optimization_ilp_motile, segmentation_connected_components, submission_generation, track_filtering | 0.938 |
| `inversion/cell-tracking-getting-started-w-nearest-neighbor` | V3 / UNKNOWN | 5,273 | 0/4/0 | detection_threshold, linking_hungarian, submission_generation | 0.143 |
| `thibautgoldsborough/unet-baseline-inference-submission` | V1 / UNKNOWN | 8,574 | 6/5/0 | detection_threshold, division_detection, linking_graph, optimization_ilp_motile, submission_generation |  |
| `jirkaborovec/biohub-celltrack-dog-trackastra-graph-trans` | V8 / UNKNOWN | 50,463 | 16/16/0 | detection_dog_log, detection_local_maxima, detection_threshold, linking_graph, linking_hungarian, linking_nearest_neighbor, metric_edge_jaccard, model_trackastra, optimization_ilp_motile, segmentation_watershed, submission_generation, track_filtering | 0.616 |
| `xiaoleilian/biohub-cell-tracking-classical-baseline` | V10 / UNKNOWN | 28,077 | 10/10/0 | detection_local_maxima, detection_threshold, division_detection, linking_graph, linking_hungarian, linking_nearest_neighbor, node_count_calibration, submission_generation, track_filtering | 0.763 |
| `xiaoleilian/biohub-cell-tracking-3d-u-net` | V15 / UNKNOWN | 17,133 | 5/4/0 | detection_local_maxima, detection_threshold, linking_hungarian, linking_nearest_neighbor, model_3d_unet, motion_kalman, submission_generation, track_filtering | 0.843 |
| `xiaoleilian/biohub-ct-mix-divaug` | V1 / UNKNOWN | 20,142 | 1/4/0 | detection_dog_log, detection_local_maxima, detection_threshold, division_detection, gap_closing, linking_hungarian, linking_nearest_neighbor, metric_division_jaccard, model_3d_unet, node_count_calibration, submission_generation | 0.884 |
| `pilkwang/biohub-cell-tracking-learned-graph-w-gap-recovery` | V32 / UNKNOWN | 83,640 | 6/5/0 | detection_threshold, division_detection, gap_closing, linking_graph, linking_hungarian, motion_kalman, node_count_calibration, optimization_ilp_motile, submission_generation, track_filtering | 0.894 |
| `pilkwang/biohub-cell-tracking-two-seeds-logit-blend` | V40 / UNKNOWN | 140,768 | 7/6/0 | detection_threshold, division_detection, gap_closing, linking_graph, linking_hungarian, linking_nearest_neighbor, model_3d_unet, motion_kalman, node_count_calibration, optimization_ilp_motile, submission_generation, track_filtering | 0.912 |
| `pilkwang/biohub-cell-tracking-data-model-eda-baseline` | V26 / UNKNOWN | 38,297 | 3/2/0 | detection_dog_log, detection_local_maxima, detection_threshold, division_detection, gap_closing, linking_graph, linking_hungarian, model_3d_unet, motion_kalman, node_count_calibration, submission_generation, track_filtering | 0.827 |
| `yusuketogashi/clean-approach-lightweight-local-cv-no-hack` | V106 / UNKNOWN | 165,239 | 11/9/0 | detection_threshold, division_detection, gap_closing, linking_graph, linking_hungarian, linking_nearest_neighbor, metric_division_jaccard, metric_edge_jaccard, model_3d_unet, motion_kalman, node_count_calibration, optimization_ilp_motile, submission_generation, track_filtering | 0.908 |
| `yusuketogashi/lb897-baseline` | V49 / UNKNOWN | 106,920 | 8/10/0 | detection_dog_log, detection_threshold, division_detection, gap_closing, linking_graph, linking_hungarian, motion_kalman, node_count_calibration, optimization_ilp_motile, submission_generation, track_filtering | 0.896 |
| `yaroslavkholmirzayev/biohub-cell-tracking-v4-unet-ilp-reproduction` | V13 / UNKNOWN | 97,908 | 6/5/0 | detection_threshold, division_detection, gap_closing, linking_graph, linking_hungarian, linking_nearest_neighbor, motion_kalman, node_count_calibration, optimization_ilp_motile, submission_generation, track_filtering | 0.896 |
| `seshurajup/lb-0-857-best-rule-base-v14` | V14 / UNKNOWN | 41,867 | 1/1/0 | detection_dog_log, detection_local_maxima, detection_threshold, division_detection, gap_closing, linking_graph, linking_hungarian, metric_division_jaccard, metric_edge_jaccard, node_count_calibration, segmentation_connected_components, submission_generation, track_filtering | 0.857 |
| `isakatsuyoshi/biohub-rule-based-baseline` | V7 / UNKNOWN | 36,093 | 0/1/0 | detection_dog_log, detection_local_maxima, detection_threshold, division_detection, gap_closing, linking_graph, linking_hungarian, metric_division_jaccard, metric_edge_jaccard, model_3d_unet, motion_kalman, node_count_calibration, segmentation_connected_components, submission_generation, track_filtering | 0.826 |
| `kirneo/metric-hack-last-call-update` | V13 / UNKNOWN | 70,863 | 0/9/0 | detection_threshold, division_detection, gap_closing, linking_graph, linking_hungarian, metric_edge_jaccard, model_3d_unet, node_count_calibration, optimization_ilp_motile, segmentation_connected_components, submission_generation, track_filtering | 0.885 |
| `amanatar/improved-metric-hack-last-call` | V1 / UNKNOWN | 64,106 | 0/9/0 | detection_threshold, division_detection, gap_closing, linking_graph, linking_hungarian, metric_edge_jaccard, model_3d_unet, node_count_calibration, optimization_ilp_motile, segmentation_connected_components, submission_generation, track_filtering | 0.966 |
| `outwrest/metric-hack-minimal-baseline-tta-2gpu` | V1 / UNKNOWN | 33,365 | 0/8/0 | detection_threshold, division_detection, linking_graph, metric_edge_jaccard, model_3d_unet, node_count_calibration, optimization_ilp_motile, segmentation_connected_components, submission_generation | 0.95 |
| `yunusgmsoy/kimi-notebook-v19` | V19 / UNKNOWN | 214,729 | 1/10/0 | detection_dog_log, detection_threshold, division_detection, gap_closing, linking_graph, linking_hungarian, linking_nearest_neighbor, metric_division_jaccard, metric_edge_jaccard, model_3d_unet, motion_kalman, node_count_calibration, optimization_ilp_motile, segmentation_connected_components, submission_generation, track_filtering | 0.938 |
| `anhadmahajan06/biohub-track-your-cells-development` | V37 / UNKNOWN | 219,493 | 10/10/0 | detection_dog_log, detection_threshold, division_detection, gap_closing, linking_graph, linking_hungarian, linking_nearest_neighbor, metric_division_jaccard, metric_edge_jaccard, model_3d_unet, motion_kalman, node_count_calibration, optimization_ilp_motile, segmentation_connected_components, submission_generation, track_filtering | 0.933 |
| `flexonafft/biohub-harmonic-fusion` | V25 / UNKNOWN | 201,600 | 0/10/0 | detection_dog_log, detection_threshold, division_detection, gap_closing, linking_graph, linking_hungarian, linking_nearest_neighbor, metric_division_jaccard, metric_edge_jaccard, model_3d_unet, motion_kalman, node_count_calibration, optimization_ilp_motile, segmentation_connected_components, submission_generation, track_filtering | 0.933 |
| `kunaldesale2408/biohub-cell-tracking` | V6 / UNKNOWN | 150,828 | 0/8/0 | detection_threshold, division_detection, gap_closing, linking_graph, linking_hungarian, linking_nearest_neighbor, model_3d_unet, motion_kalman, node_count_calibration, optimization_ilp_motile, submission_generation, track_filtering | 0.926 |
| `alioman/biohub-v19c-public0939-sis14-only` | V1 / UNKNOWN | 213,952 | 2/10/0 | detection_dog_log, detection_threshold, division_detection, gap_closing, linking_graph, linking_hungarian, linking_nearest_neighbor, metric_division_jaccard, metric_edge_jaccard, model_3d_unet, motion_kalman, node_count_calibration, optimization_ilp_motile, segmentation_connected_components, submission_generation, track_filtering | 0.939 |
| `rishabhr0y/biohub-div45-stack` | V1 / UNKNOWN | 213,602 | 1/10/0 | detection_dog_log, detection_threshold, division_detection, gap_closing, linking_graph, linking_hungarian, linking_nearest_neighbor, metric_division_jaccard, metric_edge_jaccard, model_3d_unet, motion_kalman, node_count_calibration, optimization_ilp_motile, segmentation_connected_components, submission_generation, track_filtering | 0.938 |
| `cloudssdut/biohub-0-948-reproduction-20260901` | V1 / UNKNOWN | 211,483 | 4/10/0 | detection_dog_log, detection_threshold, division_detection, gap_closing, linking_graph, linking_hungarian, linking_nearest_neighbor, metric_division_jaccard, metric_edge_jaccard, model_3d_unet, motion_kalman, node_count_calibration, optimization_ilp_motile, segmentation_connected_components, submission_generation, track_filtering | 0.935 |
| `aagneye/biohub-v23-division-rebuild-reclaim` | V1 / UNKNOWN | 209,461 | 14/11/0 | detection_dog_log, detection_threshold, division_detection, gap_closing, linking_graph, linking_hungarian, linking_nearest_neighbor, model_3d_unet, motion_kalman, node_count_calibration, optimization_ilp_motile, submission_generation, track_filtering |  |
| `pawanmali/biohub-cli-learned-div-v1` | V2 / UNKNOWN | 34,600 | 1/7/0 | detection_dog_log, detection_threshold, division_detection, gap_closing, linking_graph, metric_division_jaccard, metric_edge_jaccard, optimization_ilp_motile, submission_generation | 0.889 |
| `mdmahfujulkarim/biohub-cell-tracking-graph-pipeline` | V28 / UNKNOWN | 20,484 | 0/4/0 | detection_dog_log, detection_local_maxima, detection_threshold, gap_closing, linking_hungarian, linking_nearest_neighbor, model_3d_unet, node_count_calibration, submission_generation | 0.003 |
| `dfhgfdghfdhg/biohub-final-cyto2` | V1 / UNKNOWN | 4,881 | 0/1/0 | detection_threshold, linking_graph, linking_nearest_neighbor, model_cellpose, optimization_ilp_motile, submission_generation |  |
| `aaaa1597/s1-06-stardist-btrack-pipeline` | V36 / UNKNOWN | 121,706 | 9/9/0 | detection_dog_log, detection_local_maxima, detection_threshold, division_detection, linking_graph, linking_nearest_neighbor, metric_division_jaccard, metric_edge_jaccard, node_count_calibration, segmentation_connected_components, submission_generation, track_filtering | 0.648 |

## 完全相同大 code-cell 复用信号

下列仅证明至少一个大 cell SHA 完全相同，不自动断言整本复制关系：

- `alioman/biohub-v19c-public0939-sis14-only` ↔ `rishabhr0y/biohub-div45-stack`：共享 9 个 ≥500-byte code cell SHA（Jaccard 0.818）。
- `alioman/biohub-v19c-public0939-sis14-only` ↔ `cloudssdut/biohub-0-948-reproduction-20260901`：共享 6 个 ≥500-byte code cell SHA（Jaccard 0.429）。
- `cloudssdut/biohub-0-948-reproduction-20260901` ↔ `rishabhr0y/biohub-div45-stack`：共享 6 个 ≥500-byte code cell SHA（Jaccard 0.429）。
- `amanatar/improved-metric-hack-last-call` ↔ `kirneo/metric-hack-last-call-update`：共享 5 个 ≥500-byte code cell SHA（Jaccard 0.455）。
- `alioman/biohub-v19c-public0939-sis14-only` ↔ `nusrati/0-938`：共享 5 个 ≥500-byte code cell SHA（Jaccard 0.333）。
- `nusrati/0-938` ↔ `rishabhr0y/biohub-div45-stack`：共享 5 个 ≥500-byte code cell SHA（Jaccard 0.333）。
- `cloudssdut/biohub-0-948-reproduction-20260901` ↔ `yunusgmsoy/kimi-notebook-v19`：共享 4 个 ≥500-byte code cell SHA（Jaccard 0.250）。
- `mdmahfujulkarim/biohub-cell-tracking-graph-pipeline` ↔ `xiaoleilian/biohub-ct-mix-divaug`：共享 3 个 ≥500-byte code cell SHA（Jaccard 0.600）。
- `alioman/biohub-v19c-public0939-sis14-only` ↔ `anhadmahajan06/biohub-track-your-cells-development`：共享 3 个 ≥500-byte code cell SHA（Jaccard 0.176）。
- `alioman/biohub-v19c-public0939-sis14-only` ↔ `yunusgmsoy/kimi-notebook-v19`：共享 3 个 ≥500-byte code cell SHA（Jaccard 0.176）。

## 版本、分数和时间字段限制

- `currentVersionNumber` 是当前源码响应中的版本序号，不是 ScriptVersionId。
- API `lastRunTime` 本轮 30 个值均与请求秒级同步、但固定早约 3 天，和 Code 卡片相对更新时间冲突；已保留为 `api_last_run_time_field_observed`，不作为 updated_at。
- Historical version source/diff 未读取；同一 Notebook 的 score-linked historical ScriptVersionId 仍是 `UNKNOWN`。这项不能用不同 slug（例如 v18/v19）冒充同一 Notebook 版本史。
- 许可证字段未由 GetKernel 暴露，源码未落盘；仅保存 hash、短摘录和逐-cell evidence。

证据：`evidence/notebook_deep_read.jsonl`、`evidence/notebook_cell_audit.jsonl`、`evidence/notebook_source_request_log.csv`。
