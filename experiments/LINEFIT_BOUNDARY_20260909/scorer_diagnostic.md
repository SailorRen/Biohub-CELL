# LINEFIT_BOUNDARY P0：官方评分器与 B0 手写 proxy 实际诊断

状态：**PASS**；83 个断言，83 通过。读取时间：2026-09-09T10:30:01.584892+08:00。
证据类别为 `MEASURED`：本地合成图已实际执行；这不是 Kaggle 正式分，也没有证明候选提分。

结论：B0 正常分裂和延后一帧的分裂对照与固定官方源码一致，但弱连通替代有向双分支、一个预测 fork 被多个 GT 分裂复用、跨 GT 分量的未匹配 fork，以及合流非法拓扑均显示规则差异。未取得同一份 B0 原始预测与 GT，生产重评分状态为 `NO_SAME_PREDICTION_GRAPHS`。

官方源码固定为 `075fc5f5a52d11077f9dc2b074644618f26939e2`；入口为 `evaluate → per_sample_metrics → summarise`，并另外实测 `evaluate_datasets`。B0 只提取冻结 Notebook 的零起点 cell 8 中 9 个原始函数定义执行，未执行任何 Notebook 顶层代码。

| 合成场景 | 官方 edge TP/FP/FN | 官方 div TP/FP/FN | B0 div TP/FP/FN | B0 proxy − 官方完整 score |
|---|---|---|---|---:|
| perfect_division | [5, 0, 0] | [1, 0, 0] | [1, 0, 0] | +0.0000000000 |
| weak_component_same_branch | [2, 2, 3] | [0, 1, 1] | [1, 0, 0] | +0.1000000000 |
| one_pred_fork_two_gt_divisions | [6, 1, 5] | [1, 0, 1] | [2, 0, 0] | +0.0500000000 |
| unmatched_fork_cross_components | [0, 2, 2] | [0, 1, 0] | [0, 0, 0] | +0.0000000000 |
| delayed_local_division | [1, 3, 4] | [1, 0, 0] | [1, 0, 0] | +0.0000000000 |
| merged_child_reject | [5, 1, 0] | [0, 1, 1] | [1, 0, 0] | +0.1000000000 |

这些差值只适用于列出的微型合成输入。合流例是非法拓扑负例，不能据此声称 B0 正式输出含有合流。每个场景的完整输入、逐场景哈希、双方逐样本指标与所有断言都在 JSON 回执中。

完整聚合入口实测：含 6 个额外孤立预测节点的完美分裂图，加一个完美直线图。官方完整 score=`1.028571428571`，B0 proxy=`1.028571428571`；未做节点数校正的官方便捷入口 `evaluate_datasets` 为 `1.100000000000`，高 `0.071428571429`。因此不能将便捷入口当作完整聚合链替代品，也不能说 B0 缺少节点数校正。该合成分值可高于 1，直接来自公式，不代表赛事成绩。
缺失 n_total 的独立边界检查：官方 adjusted J 为 NaN，B0 返回未经校正的 J。真实任务是否出现此情况未知；本诊断未修改其行为。

实际执行命令：

```sh
downloads/LINEFIT_BOUNDARY_20260909/scorer/venv/bin/python experiments/LINEFIT_BOUNDARY_20260909/scorer_diagnostic.py
```

运行环境 Python 3.11.14；依赖：`{"tracksdata": "0.1.0rc6.dev3+g980c2d30a", "polars": "1.42.0", "numpy": "2.4.2", "scipy": "1.17.1", "rustworkx": "0.18.1", "geff": "1.3.1.1.3", "numba": "0.67.0", "zarr": "3.1.6"}`。固定 tracksdata 源码完整 SHA 为 `980c2d30aeca76b86eddef0aeadb4d10dee8530d`，源码压缩包用过程级版本元数据补全后安装到任务隔离 venv；没有改全局环境。tracksdata 和 polars 与 B0 记录相同，NumPy 2.4.2 / SciPy 1.17.1 与 B0 的 2.0.2 / 1.16.3 不同，因此不是 Kaggle 环境逐字节复现。首次 Git 依赖安装因 TLS 失败，第一次源码归档安装因版本元数据失败，日志及哈希如实保留。全部安装命令写入 JSON 回执；完整依赖清单保存在 ignored 目录。

`scripts/evaluate.py` 的 GEFF CLI 文件读写入口只读核对、未运行；执行的是该 CLI 所调用的实际评分与完整聚合函数，不是重写官方评分器。现有下载中只找到汇总 CSV，没有可配对的原始预测图和 GT 图，因此没有生产数据数值重评分。

限制：只证明固定官方源码与冻结 B0 proxy 在这些输入上不等价。不能证明 Kaggle 私有部署恰好使用同一源码，也不能推断实际 B0 错误比例、真实 PP 排序改变或修正 proxy 后必定提分。本诊断不改变候选自动选择器，不把 proxy 提高设为正式提交前置条件。

本文件为本地诊断交付，不自证 GitHub 推送、远端回读或最终任务完成。
