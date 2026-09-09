#!/usr/bin/env python3
"""Execute frozen official scorer and unchanged B0 proxy on tiny local graphs.

No notebook top-level code, model, competition data, or external write is run.
Requires the task-local tracksdata environment described in the output receipt.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/LINEFIT_BOUNDARY_20260909"
RAW = ROOT / "downloads/LINEFIT_BOUNDARY_20260909/scorer"
OFFICIAL = ROOT / "downloads/20260909_public_research/github/royerlab__kaggle-cell-tracking-competition/source"
NOTEBOOK = ROOT / "experiments/PUBLIC946_TTA_20260908/B0/candidate.ipynb"
OFFICIAL_COMMIT = "075fc5f5a52d11077f9dc2b074644618f26939e2"
SCALE = (1.625, 0.40625, 0.40625)
EXPECTED_HASHES = {
    "src/tracking_cellmot/metrics.py": "cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444",
    "src/tracking_cellmot/division_metrics.py": "0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9",
    "scripts/evaluate.py": "03ad4049530d3682c77435194e5d921981f331df3462abcde4a7156d1a57b7d3",
}
PROXY_FUNCTIONS = [
    "match_nodes_bipartite", "compute_edge_confusion", "edge_jaccard",
    "adjusted_jaccard", "weakly_connected_components", "compute_division_confusion",
    "decompose_errors", "score_sample", "aggregate_official",
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def clean(obj):
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    if isinstance(obj, dict):
        return {str(k): clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    return obj


def graph(nodes, edges):
    # All supplied coordinates are physical y micrometres; z and x are zero.
    return {"nodes_t_y_um": nodes, "edges": edges}


def fixtures():
    perfect = graph(
        {"P": [0, 0], "D": [1, 0], "C1": [2, 10], "C2": [2, -10],
         "G1": [3, 10], "G2": [3, -10]},
        [["P", "D"], ["D", "C1"], ["D", "C2"], ["C1", "G1"], ["C2", "G2"]],
    )
    two_gt = graph(
        {"P0": [0, 0], "D1": [1, 0], "A2": [2, -20], "B2": [2, 20],
         "A3": [3, -20], "E3": [3, 20], "A4": [4, -20], "C4": [4, 10],
         "D4": [4, 30], "A5": [5, -20], "C5": [5, 10], "D5": [5, 30]},
        [["P0", "D1"], ["D1", "A2"], ["D1", "B2"], ["A2", "A3"],
         ["A3", "A4"], ["A4", "A5"], ["B2", "E3"], ["E3", "C4"],
         ["E3", "D4"], ["C4", "C5"], ["D4", "D5"]],
    )
    one_fork = graph(
        {k: two_gt["nodes_t_y_um"][k] for k in ["P0", "D1", "A2", "E3", "C4", "D4", "C5", "D5"]},
        [["P0", "D1"], ["D1", "A2"], ["A2", "E3"], ["E3", "C4"],
         ["E3", "D4"], ["C4", "C5"], ["D4", "D5"]],
    )
    cases = [
        ("perfect_division", "正常分裂阳性对照", perfect, perfect,
         [5, 0, 0, 1, 0, 0], [5, 0, 0, 1, 0, 0]),
        ("weak_component_same_branch", "同一弱连通块包含两条GT女儿，但命中同一有向预测分支",
         perfect, graph({"P": [0, 0], "D": [1, 0], "C1": [2, 10], "X": [2, 50], "G2": [3, -10]},
                        [["P", "D"], ["D", "C1"], ["D", "X"], ["C1", "G2"]]),
         [2, 2, 3, 0, 1, 1], [2, 2, 3, 1, 0, 0]),
        ("one_pred_fork_two_gt_divisions", "仅一个预测fork，被B0弱连通规则重复计为两个GT分裂",
         two_gt, one_fork, [6, 1, 5, 1, 0, 1], [6, 1, 5, 2, 0, 0]),
        ("unmatched_fork_cross_components", "未匹配预测fork的女儿分别命中不同GT连通分量",
         graph({"A0": [0, 0], "A1": [1, 0], "B0": [0, 20], "B1": [1, 20]}, [["A0", "A1"], ["B0", "B1"]]),
         graph({"F": [0, 10], "A1": [1, 0], "B1": [1, 20]}, [["F", "A1"], ["F", "B1"]]),
         [0, 2, 2, 0, 1, 0], [0, 2, 2, 0, 0, 0]),
        ("delayed_local_division", "分裂延后一帧且保持两条有向分支的阳性对照",
         perfect, graph({"P": [0, 0], "D": [1, 0], "M": [2, 0], "G1": [3, 10], "G2": [3, -10]},
                        [["P", "D"], ["D", "M"], ["M", "G1"], ["M", "G2"]]),
         [1, 3, 4, 1, 0, 0], [1, 3, 4, 1, 0, 0]),
        ("merged_child_reject", "女儿有两个入边的非法拓扑反例；不声称B0正式图有此问题",
         perfect, graph({**perfect["nodes_t_y_um"], "X": [1, 50]}, perfect["edges"] + [["X", "C1"]]),
         [5, 1, 0, 0, 1, 1], [5, 1, 0, 1, 0, 0]),
    ]
    fixture_list = [{"id": key, "purpose": purpose, "gt": gt, "pred": pred,
                     "n_total": len(gt["nodes_t_y_um"]),
                     "expected_official_counts": official, "expected_proxy_counts": proxy}
                    for key, purpose, gt, pred, official, proxy in cases]
    inflated = graph({**perfect["nodes_t_y_um"], **{f"extra{i}": [0, 100 + 20*i] for i in range(6)}}, perfect["edges"])
    straight = graph({"A": [0, 0], "B": [1, 0], "C": [2, 0]}, [["A", "B"], ["B", "C"]])
    aggregation = [{"id": "division_extra_isolated_nodes", "gt": perfect, "pred": inflated, "n_total": 6},
                   {"id": "straight_perfect", "gt": straight, "pred": straight, "n_total": 3}]
    return {"scale_zyx_um": SCALE, "match_radius_um": 7.0, "cases": fixture_list, "aggregation": aggregation}


def load_proxy():
    raw = NOTEBOOK.read_bytes()
    assert digest(raw) == "c4bfcd8d765c67d35435876b3f3eb7bb810e20556479a918143451e2c61f849c"
    source = "".join(json.loads(raw)["cells"][8]["source"])
    assert digest(source.encode()) == "3988c72818365e0cf42169df1d42d3d64e64a6f2815a42255a04222523936349"
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    scope = {"np": np, "linear_sum_assignment": linear_sum_assignment,
             "VOXEL_SCALE_UM": SCALE, "VALIDATOR_MATCH_RADIUS_UM": 7.0,
             "VALIDATOR_NODE_COUNT_PENALTY_A": 0.1, "VALIDATOR_DIVISION_WEIGHT": 0.1}
    tree = ast.parse(source)
    selected = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in PROXY_FUNCTIONS]
    assert {n.name for n in selected} == set(PROXY_FUNCTIONS)
    exec(compile(ast.Module(body=selected, type_ignores=[]), "frozen_B0_cell8_function_defs", "exec"), scope)
    return scope, {"path": str(NOTEBOOK.relative_to(ROOT)), "sha256": digest(raw), "zero_based_cell": 8,
                   "cell_sha256": digest(source.encode()), "executed_functions": PROXY_FUNCTIONS,
                   "execution": "Original AST function definitions only; no notebook top-level cell executed."}


def build_graph(spec, td, pl):
    g = td.graph.InMemoryGraph()
    for key in ("z", "y", "x"):
        g.add_node_attr_key(key, pl.Float64, 0.0)
    ids = {name: g.add_node({"t": int(t), "z": 0.0, "y": y/SCALE[1], "x": 0.0})
           for name, (t, y) in spec["nodes_t_y_um"].items()}
    for a, b in spec["edges"]:
        g.add_edge(ids[a], ids[b], {})
    plain = {ids[k]: (int(t), 0.0, y/SCALE[1], 0.0) for k, (t, y) in spec["nodes_t_y_um"].items()}
    return g, plain, [(ids[a], ids[b]) for a, b in spec["edges"]]


def same_prediction_scan():
    roots = [ROOT / "downloads", ROOT / "data", ROOT / "artifacts"]
    candidates = []
    for root in roots:
        if not root.exists():
            continue
        # Bounded repository-local inventory; excludes the isolated dependency tree.
        for p in root.rglob("*"):
            if "venv" in p.parts:
                continue
            if (p.is_dir() and p.suffix in (".geff", ".zarr")) or (p.is_file() and p.suffix in (".csv", ".geff")):
                candidates.append({"path": str(p.relative_to(ROOT)), "bytes": p.stat().st_size if p.is_file() else None})
    return {"status": "NO_SAME_PREDICTION_GRAPHS", "scanned_roots": [str(p.relative_to(ROOT)) for p in roots],
            "existing_roots": [str(p.relative_to(ROOT)) for p in roots if p.exists()], "candidate_files": candidates,
            "reason": "Only aggregate run_stats/validator_results/ppsweep CSVs found; no paired original B0 prediction graph and exact GT graph. No competition graph downloaded.",
            "production_rescore": "NOT_RUN"}


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    source_manifest = []
    for rel, expected in EXPECTED_HASHES.items():
        p = OFFICIAL / rel
        actual = digest(p.read_bytes())
        assert actual == expected, (rel, actual)
        source_manifest.append({"path": str(p.relative_to(ROOT)), "sha256": actual,
                                "url": f"https://github.com/royerlab/kaggle-cell-tracking-competition/blob/{OFFICIAL_COMMIT}/{rel}"})
    sys.path.insert(0, str(OFFICIAL / "src"))
    import polars as pl
    import tracksdata as td
    from tracking_cellmot import metrics
    proxy, proxy_manifest = load_proxy()
    inputs = fixtures()
    (RAW / "synthetic_inputs.json").write_bytes(canonical(inputs))
    checks, outputs = [], []

    def check(name, actual, expected):
        ok = math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12) if isinstance(actual, float) else actual == expected
        checks.append({"id": name, "actual": clean(actual), "expected": clean(expected), "status": "PASS" if ok else "FAIL"})

    def evaluate_one(item):
        pred, pn, pe = build_graph(item["pred"], td, pl)
        gt, gn, ge = build_graph(item["gt"], td, pl)
        er = metrics.evaluate(pred, gt, scale=SCALE, max_distance=7.0)
        row = metrics.per_sample_metrics(er, n_total=item["n_total"], node_recall=metrics.node_recall(pred, gt))
        pr = proxy["score_sample"](pn, pe, gn, ge, item["n_total"])
        return er, row, pr

    for item in inputs["cases"]:
        er, row, pr = evaluate_one(item)
        oc = [er.edge_tp, er.edge_fp, er.edge_fn, er.division_tp, er.division_fp, er.division_fn]
        pc = [pr[k] for k in ("edge_tp", "edge_fp", "edge_fn", "div_tp", "div_fp", "div_fn")]
        for idx, label in enumerate(("edge_tp", "edge_fp", "edge_fn", "division_tp", "division_fp", "division_fn")):
            check(f"{item['id']}.official.{label}", oc[idx], item["expected_official_counts"][idx])
            check(f"{item['id']}.proxy.{label}", pc[idx], item["expected_proxy_counts"][idx])
        os = metrics.summarise([row])
        ps = proxy["aggregate_official"]([pr])
        outputs.append({"id": item["id"], "purpose": item["purpose"], "input_sha256": digest(canonical(item)),
                        "official_counts": oc, "proxy_counts": pc, "official_per_sample": row,
                        "proxy_per_sample": pr, "official_summary": os, "proxy_summary": ps,
                        "proxy_minus_official_score": ps["proxy_score"] - os["score"]})

    rows, prs = [], []
    for item in inputs["aggregation"]:
        _, row, pr = evaluate_one(item)
        rows.append(row)
        prs.append(pr)
    full = metrics.summarise(rows)
    pa = proxy["aggregate_official"](prs)
    pairs = [(build_graph(i["pred"], td, pl)[0], build_graph(i["gt"], td, pl)[0]) for i in inputs["aggregation"]]
    convenience = metrics.evaluate_datasets(pairs, scale=SCALE, max_distance=7.0)._asdict()
    check("aggregation.full.adjusted_edge", full["adj_edge_jaccard"], 6.5/7)
    check("aggregation.full.score", full["score"], 6.5/7 + 0.1)
    check("aggregation.proxy_matches_full", pa["proxy_score"], full["score"])
    check("aggregation.convenience.score", convenience["score"], 1.1)
    check("aggregation.convenience_omits_adjustment", convenience["score"] - full["score"], 0.5/7)
    # Missing metadata is a separate real entry-point discrepancy, not a change to the candidate selector.
    metadata_missing = metrics.per_sample_metrics(metrics.EvaluationResult(5, 0, 0, 1, 0, 0, 12), float("nan"), 1.0)
    check("metadata_missing.official_is_nan", math.isnan(metadata_missing["adj_edge_jaccard"]), True)
    check("metadata_missing.proxy_uses_unadjusted", proxy["adjusted_jaccard"](1.0, 12, None), 1.0)
    check("normal_division_equal", outputs[0]["proxy_minus_official_score"], 0.0)
    check("same_branch_proxy_inflation", outputs[1]["proxy_minus_official_score"], 0.1)
    check("one_fork_two_gt_proxy_inflation", outputs[2]["proxy_minus_official_score"], 0.05)
    check("delayed_division_equal", outputs[4]["proxy_minus_official_score"], 0.0)

    freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True, check=True)
    (RAW / "pip_freeze.txt").write_text(freeze.stdout)
    dependencies = {}
    for name in ("tracksdata", "polars", "numpy", "scipy", "rustworkx", "geff", "numba", "zarr"):
        try:
            dependencies[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            dependencies[name] = "NOT_INSTALLED"
    install_logs = []
    for p in sorted(RAW.glob("install*.log")):
        install_logs.append({"path": str(p.relative_to(ROOT)), "sha256": digest(p.read_bytes()), "bytes": p.stat().st_size})
    commands = [
        {"command": "python3 -m venv --system-site-packages downloads/LINEFIT_BOUNDARY_20260909/scorer/venv", "exit_code": 0},
        {"command": "downloads/LINEFIT_BOUNDARY_20260909/scorer/venv/bin/python -m pip install --no-cache-dir 'tracksdata @ git+https://github.com/royerlab/tracksdata.git@980c2d30a' 'polars==1.42.0'", "exit_code": 1, "result": "Git clone TLS failure; no installation completed."},
        {"command": "curl -fsSL --retry 1 --max-time 45 https://codeload.github.com/royerlab/tracksdata/tar.gz/980c2d30a -o downloads/LINEFIT_BOUNDARY_20260909/scorer/tracksdata_980c2d30a.tar.gz", "exit_code": 0},
        {"command": "SETUPTOOLS_SCM_PRETEND_VERSION_FOR_TRACKSDATA=0.1.0rc6.dev3+g980c2d30a downloads/LINEFIT_BOUNDARY_20260909/scorer/venv/bin/python -m pip install --no-cache-dir downloads/LINEFIT_BOUNDARY_20260909/scorer/tracksdata_980c2d30a.tar.gz 'polars==1.42.0'", "exit_code": 1, "result": "Archive lacked VCS version metadata; per-distribution override did not apply."},
        {"command": "SETUPTOOLS_SCM_PRETEND_VERSION=0.1.0rc6.dev3+g980c2d30a downloads/LINEFIT_BOUNDARY_20260909/scorer/venv/bin/python -m pip install --no-cache-dir downloads/LINEFIT_BOUNDARY_20260909/scorer/tracksdata_980c2d30a.tar.gz 'polars==1.42.0'", "exit_code": 0, "result": "Installed only in task-local venv; subprocess-scoped version metadata supplied."},
        {"command": "gh api repos/royerlab/tracksdata/commits/980c2d30a --jq .sha", "exit_code": 0, "result": "980c2d30aeca76b86eddef0aeadb4d10dee8530d"},
    ]
    (RAW / "environment_commands.json").write_bytes(canonical(commands))
    result = {
        "schema_version": "1.0", "task_id": "LINEFIT_BOUNDARY_20260909", "phase": "P0_SCORER_DIAGNOSTIC",
        "status": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL",
        "evidence_class": "MEASURED", "executed": True,
        "observed_at_shanghai": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
        "script_sha256": digest(Path(__file__).read_bytes()),
        "official": {"repository": "royerlab/kaggle-cell-tracking-competition", "branch": "main", "commit": OFFICIAL_COMMIT,
                     "files": source_manifest, "entrypoints_executed": ["evaluate", "node_recall", "per_sample_metrics", "summarise", "evaluate_datasets"],
                     "cli_io_entrypoint": "scripts/evaluate.py read and hashed; not executed because no GEFF fixtures required. Same evaluate→per_sample_metrics→summarise computation called directly."},
        "proxy": proxy_manifest, "runtime": {"executable": sys.executable, "python": platform.python_version(),
            "platform": platform.platform(), "dependencies": dependencies,
            "environment": "Task-local venv --system-site-packages; added/updated packages confined to venv.",
            "pip_freeze_sha256": digest(freeze.stdout.encode()), "install_logs": install_logs,
            "tracksdata_source_archive_sha256": digest((RAW / "tracksdata_980c2d30a.tar.gz").read_bytes()),
            "tracksdata_source_commit_ref": "980c2d30a",
            "tracksdata_source_commit": "980c2d30aeca76b86eddef0aeadb4d10dee8530d",
            "archive_version_metadata_override": "SETUPTOOLS_SCM_PRETEND_VERSION=0.1.0rc6.dev3+g980c2d30a; only builds missing archive metadata; source not changed.",
            "compatibility_limit": "tracksdata source and polars match recorded B0; NumPy 2.4.2/SciPy 1.17.1 differ from B0 NumPy 2.0.2/SciPy 1.16.3. This is not a bitwise Kaggle environment reproduction."},
        "environment_commands": commands,
        "command": "downloads/LINEFIT_BOUNDARY_20260909/scorer/venv/bin/python experiments/LINEFIT_BOUNDARY_20260909/scorer_diagnostic.py",
        "input": {"kind": "Original hand-constructed tiny synthetic graphs", "fixture_count": len(inputs["cases"]),
                  "aggregation_sample_count": len(inputs["aggregation"]), "path": str((RAW / "synthetic_inputs.json").relative_to(ROOT)),
                  "sha256": digest(canonical(inputs)), "scale_zyx_um": SCALE, "max_distance_um": 7.0,
                  "node_count_metadata": "Known exact synthetic n_total supplied; no real estimated_number_of_nodes inferred."},
        "cases": outputs,
        "aggregation": {"official_per_sample": rows, "official_full": full, "proxy": pa, "official_convenience": convenience,
                        "convenience_minus_full": convenience["score"] - full["score"],
                        "missing_metadata_official_adjusted": metadata_missing["adj_edge_jaccard"],
                        "missing_metadata_proxy_adjusted": proxy["adjusted_jaccard"](1.0, 12, None)},
        "checks": checks, "check_summary": {"total": len(checks), "passed": sum(c["status"] == "PASS" for c in checks),
                                               "failed": sum(c["status"] == "FAIL" for c in checks)},
        "same_prediction_rescore": same_prediction_scan(),
        "scope_limits": ["This is a local synthetic scorer execution, not a Kaggle submission or formal score.",
                         "Source commit identity does not independently prove Kaggle private deployed evaluator version.",
                         "Fixtures prove non-equivalence and specific count differences, not the prevalence of these patterns in B0.",
                         "No real original B0 prediction+GT rescore; no improvement or actual PP ranking change established.",
                         "Candidate and original PP selection are unchanged by this diagnostic.",
                         "No training, model inference, Kaggle write, or Git operation performed by this script."],
    }
    (OUT / "scorer_diagnostic.json").write_bytes(canonical(clean(result)))
    lines = ["# LINEFIT_BOUNDARY P0：官方评分器与 B0 手写 proxy 实际诊断", "",
             f"状态：**{result['status']}**；{len(checks)} 个断言，{result['check_summary']['passed']} 通过。读取时间：{result['observed_at_shanghai']}。",
             "证据类别为 `MEASURED`：本地合成图已实际执行；这不是 Kaggle 正式分，也没有证明候选提分。", "",
             "结论：B0 正常分裂和延后一帧的分裂对照与固定官方源码一致，但弱连通替代有向双分支、一个预测 fork 被多个 GT 分裂复用、跨 GT 分量的未匹配 fork，以及合流非法拓扑均显示规则差异。未取得同一份 B0 原始预测与 GT，生产重评分状态为 `NO_SAME_PREDICTION_GRAPHS`。", "",
             f"官方源码固定为 `{OFFICIAL_COMMIT}`；入口为 `evaluate → per_sample_metrics → summarise`，并另外实测 `evaluate_datasets`。B0 只提取冻结 Notebook 的零起点 cell 8 中 9 个原始函数定义执行，未执行任何 Notebook 顶层代码。", "",
             "| 合成场景 | 官方 edge TP/FP/FN | 官方 div TP/FP/FN | B0 div TP/FP/FN | B0 proxy − 官方完整 score |", "|---|---|---|---|---:|"]
    for r in outputs:
        lines.append(f"| {r['id']} | {r['official_counts'][:3]} | {r['official_counts'][3:]} | {r['proxy_counts'][3:]} | {r['proxy_minus_official_score']:+.10f} |")
    lines += ["", "这些差值只适用于列出的微型合成输入。合流例是非法拓扑负例，不能据此声称 B0 正式输出含有合流。每个场景的完整输入、逐场景哈希、双方逐样本指标与所有断言都在 JSON 回执中。", "",
              f"完整聚合入口实测：含 6 个额外孤立预测节点的完美分裂图，加一个完美直线图。官方完整 score=`{full['score']:.12f}`，B0 proxy=`{pa['proxy_score']:.12f}`；未做节点数校正的官方便捷入口 `evaluate_datasets` 为 `{convenience['score']:.12f}`，高 `{convenience['score'] - full['score']:.12f}`。因此不能将便捷入口当作完整聚合链替代品，也不能说 B0 缺少节点数校正。该合成分值可高于 1，直接来自公式，不代表赛事成绩。",
              "缺失 n_total 的独立边界检查：官方 adjusted J 为 NaN，B0 返回未经校正的 J。真实任务是否出现此情况未知；本诊断未修改其行为。", "",
              "实际执行命令：", "", "```sh", result["command"], "```", "",
              f"运行环境 Python {platform.python_version()}；依赖：`{json.dumps(dependencies, ensure_ascii=False)}`。固定 tracksdata 源码完整 SHA 为 `980c2d30aeca76b86eddef0aeadb4d10dee8530d`，源码压缩包用过程级版本元数据补全后安装到任务隔离 venv；没有改全局环境。tracksdata 和 polars 与 B0 记录相同，NumPy 2.4.2 / SciPy 1.17.1 与 B0 的 2.0.2 / 1.16.3 不同，因此不是 Kaggle 环境逐字节复现。首次 Git 依赖安装因 TLS 失败，第一次源码归档安装因版本元数据失败，日志及哈希如实保留。全部安装命令写入 JSON 回执；完整依赖清单保存在 ignored 目录。", "",
              "`scripts/evaluate.py` 的 GEFF CLI 文件读写入口只读核对、未运行；执行的是该 CLI 所调用的实际评分与完整聚合函数，不是重写官方评分器。现有下载中只找到汇总 CSV，没有可配对的原始预测图和 GT 图，因此没有生产数据数值重评分。", "",
              "限制：只证明固定官方源码与冻结 B0 proxy 在这些输入上不等价。不能证明 Kaggle 私有部署恰好使用同一源码，也不能推断实际 B0 错误比例、真实 PP 排序改变或修正 proxy 后必定提分。本诊断不改变候选自动选择器，不把 proxy 提高设为正式提交前置条件。", "",
              "本文件为本地诊断交付，不自证 GitHub 推送、远端回读或最终任务完成。", ""]
    (OUT / "scorer_diagnostic.md").write_text("\n".join(lines))
    print(json.dumps({"status": result["status"], "checks": result["check_summary"],
                      "cases": [{"id": x["id"], "official": x["official_counts"], "proxy": x["proxy_counts"],
                                 "delta": x["proxy_minus_official_score"]} for x in outputs],
                      "aggregation": clean(result["aggregation"]), "dependencies": dependencies}, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
