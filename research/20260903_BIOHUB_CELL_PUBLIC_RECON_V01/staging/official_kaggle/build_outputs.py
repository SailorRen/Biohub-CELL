#!/usr/bin/env python3
"""从已落盘的只读证据生成 official_kaggle staging 01–07 草稿。"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / "evidence"
SG = ZoneInfo("Asia/Singapore")
REL_PREFIX = "research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/staging/official_kaggle/"


def repo_evidence(path: str) -> str:
    return REL_PREFIX + path.lstrip("/")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, default=str) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def num(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def pipe(value: Iterable[Any]) -> str:
    return " | ".join(str(x) for x in value if x not in (None, ""))


def notebook_source_id(ref: str) -> str:
    """Keep one stable source-id mapping across inventory, manifest and claims."""
    return "KAGGLE_CODE_" + ref.upper().replace("/", "_")


def bool_text(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return "UNKNOWN"


def now_pair() -> tuple[str, str]:
    value = datetime.now(timezone.utc)
    return value.isoformat(), value.astimezone(SG).isoformat()


sort_doc = read_json(EVIDENCE / "browser_code_sort_captures.json")
keyword_doc = read_json(EVIDENCE / "browser_code_keyword_captures.json")
official_doc = read_json(EVIDENCE / "browser_official_routes.json")
lb_doc = read_json(EVIDENCE / "browser_leaderboard_snapshot.json")
deep_rows = read_jsonl(EVIDENCE / "notebook_deep_read.jsonl")
cell_rows = read_jsonl(EVIDENCE / "notebook_cell_audit.jsonl")
deep_summary = read_json(ROOT / "notebook_deep_read_summary.json")
metadata_summary = read_json(ROOT / "metadata_collection_summary.json")
official_api_rows = list(csv.DictReader((EVIDENCE / "official_pages_metadata.csv").open(encoding="utf-8")))
partial_file_rows = list(csv.DictReader((EVIDENCE / "competition_files_metadata.csv").open(encoding="utf-8")))


# ---------- Notebook 证据正规化 ----------

code_categories: defaultdict[str, set[str]] = defaultdict(set)
markdown_categories: defaultdict[str, set[str]] = defaultdict(set)
code_cell_hashes: defaultdict[str, set[str]] = defaultdict(set)
for row in cell_rows:
    ref = row["notebook_ref"]
    if row.get("cell_type") == "code":
        code_categories[ref].update(row.get("semantic_categories", []))
        if int(row.get("cell_bytes") or 0) >= 500:
            code_cell_hashes[ref].add(row["cell_sha256"])
    elif row.get("cell_type") == "markdown":
        markdown_categories[ref].update(row.get("semantic_categories", []))

for row in deep_rows:
    # GetKernel 的 lastRunTime 本轮呈现“与请求秒级同步但固定早 3 日”的异常形态，
    # 不得把它误写成 Notebook 更新时间。
    observed_last_run = row.get("api_last_run_time_field_observed") or row.pop("updated_at", "")
    row["api_last_run_time_field_observed"] = observed_last_run
    row["updated_at"] = ""
    row["updated_at_status"] = "UNKNOWN_API_LAST_RUN_TIME_FIELD_ANOMALOUS_REQUEST_CADENCE_MINUS_3_DAYS"
    row["created_at_status"] = "UNKNOWN_NOT_EXPOSED"
    row["license"] = row.get("license") or "UNKNOWN_NOT_EXPOSED"
    row["script_version_id"] = row.get("script_version_id") or "UNKNOWN"
    row["implemented_code_categories"] = sorted(code_categories[row["notebook_ref"]])
    row["narrative_only_categories"] = sorted(markdown_categories[row["notebook_ref"]] - code_categories[row["notebook_ref"]])
    row["output_status"] = (
        "OUTPUTS_CLEARED_OR_ABSENT_IN_GETKERNEL_SOURCE"
        if int(row.get("output_item_count") or 0) == 0
        else "OUTPUTS_PRESENT_AND_HASHED"
    )
    row["read_status"] = "FULL_SOURCE_READ"

# 用正规化后的事实覆盖之前生成件；不产生任何网络访问。
write_jsonl(EVIDENCE / "notebook_deep_read.jsonl", deep_rows)
deep_by_ref = {row["notebook_ref"]: row for row in deep_rows}


# ---------- 浏览器 Code 发现清单 ----------

occurrences: list[dict[str, Any]] = []
cards_by_ref: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
for capture in sort_doc["sorts"]:
    for position, card in enumerate(capture.get("rows", []), start=1):
        row = {**card, "discovery_type": "competition_code_sort", "discovery_context": capture["sort"], "position": position}
        occurrences.append(row)
        cards_by_ref[card["ref"]].append(row)
for capture in keyword_doc["captures"]:
    for position, card in enumerate(capture.get("rows", []), start=1):
        row = {**card, "discovery_type": "keyword", "discovery_context": capture["query"], "position": position}
        occurrences.append(row)
        cards_by_ref[card["ref"]].append(row)


def pick_card(rows: list[dict[str, Any]]) -> dict[str, Any]:
    # 关键词抓取晚于排序抓取；以最后一次可见值为当前卡片观察，另保留所有值。
    return rows[-1]


inventory_rows: list[dict[str, Any]] = []
for ref in sorted(cards_by_ref):
    observations = cards_by_ref[ref]
    card = pick_card(observations)
    deep = deep_by_ref.get(ref)
    owner, slug = ref.split("/", 1)
    observed_scores = sorted({str(x.get("score")) for x in observations if x.get("score") not in (None, "")})
    max_score = max((num(x) for x in observed_scores if num(x) is not None), default=None)
    title_risk = bool(re.search(r"metric.?hack|exploit", f"{ref} {card.get('title', '')}", re.I))
    if title_risk or (max_score is not None and max_score > 0.963):
        stale_risk = "HIGH_EXPLICIT_HACK_OR_ABOVE_CURRENT_LB_TOP"
    elif observed_scores:
        stale_risk = "UNKNOWN_DYNAMIC_SCORE_UNBOUND_TO_SOURCE_VERSION"
    else:
        stale_risk = "UNKNOWN_NO_PAGE_SCORE_OBSERVED"
    read_status = "FULL_SOURCE_READ" if deep else "METADATA_ONLY"
    notes: list[str] = [
        f"discovered_in={len(observations)} visible query/sort occurrences",
        "Code card score is dynamic and not bound to current GetKernel source or a submission",
    ]
    if deep:
        notes.extend(
            [
                f"all {deep['code_cell_count']} code cells hashed and semantically scanned",
                deep["output_status"],
                deep["script_version_id_status"],
                deep["updated_at_status"],
            ]
        )
    inventory_rows.append(
        {
            "source_id": notebook_source_id(ref),
            "owner": owner,
            "notebook_title": card.get("title", ""),
            "notebook_slug": slug,
            "url": card.get("url") or f"https://www.kaggle.com/code/{ref}",
            "current_version": deep.get("current_version", "") if deep else "UNKNOWN",
            "script_version_id": deep.get("script_version_id", "UNKNOWN") if deep else "UNKNOWN",
            "created_at": deep.get("created_at", "") if deep else "",
            "updated_at": "",
            "updated_at_page_text": card.get("updated", ""),
            "votes": max((int(x.get("votes")) for x in observations if str(x.get("votes", "")).isdigit()), default=""),
            "comments": max((int(x.get("comments")) for x in observations if str(x.get("comments", "")).isdigit()), default=""),
            "page_displayed_score": observed_scores[-1] if len(observed_scores) == 1 else pipe(observed_scores),
            "score_source": "KAGGLE_CODE_LIST_CARD_DYNAMIC",
            "accelerator": deep.get("accelerator", "") if deep else "UNKNOWN",
            "runtime": "NOT_VERIFIED_OUTPUTS_EMPTY" if deep else "UNKNOWN",
            "internet_setting": bool_text(deep.get("internet_setting")) if deep else "UNKNOWN",
            "input_datasets": pipe(deep.get("input_dataset_slugs_from_source", [])) if deep else "UNKNOWN",
            "output_files": pipe(deep.get("output_paths_from_source", [])) if deep else "UNKNOWN",
            "license": deep.get("license", "UNKNOWN") if deep else "UNKNOWN",
            "read_status": "FULL_NOTEBOOK_SOURCE_READ" if deep else "METADATA_ONLY",
            "source_saved": "false",
            "source_sha256": deep.get("source_sha256", "") if deep else "",
            "source_bytes": deep.get("source_bytes", "") if deep else "",
            "markdown_cells": deep.get("markdown_cell_count", "") if deep else "",
            "code_cells": deep.get("code_cell_count", "") if deep else "",
            "output_cells": deep.get("output_bearing_code_cell_count", "") if deep else "",
            "all_code_cells_checked": "true" if deep else "false",
            "relevance": pipe(sorted({x["discovery_context"] for x in observations})),
            "current_score_verified": "false",
            "stale_score_risk": stale_risk,
            "notes": "; ".join(notes),
        }
    )

inventory_fields = [
    "source_id", "owner", "notebook_title", "notebook_slug", "url", "current_version", "script_version_id",
    "created_at", "updated_at", "updated_at_page_text", "votes", "comments", "page_displayed_score",
    "score_source", "accelerator", "runtime", "internet_setting", "input_datasets", "output_files",
    "license", "read_status", "source_saved", "source_sha256", "source_bytes", "markdown_cells",
    "code_cells", "output_cells", "all_code_cells_checked", "relevance", "current_score_verified",
    "stale_score_risk", "notes",
]
write_csv(ROOT / "05_kaggle_code_inventory.csv", inventory_rows, inventory_fields)


# ---------- 方法矩阵 ----------

def select_categories(categories: set[str], prefixes: tuple[str, ...]) -> str:
    return pipe(sorted(x for x in categories if x.startswith(prefixes))) or "NOT_FOUND_IN_CODE_SCAN"


method_rows: list[dict[str, Any]] = []
for deep in deep_rows:
    ref = deep["notebook_ref"]
    cats = set(deep["implemented_code_categories"])
    cv_signals = sorted(x for x in cats if x.startswith("metric_"))
    local_score = pipe(deep.get("reported_local_score_strings_unverified", [])) or "NONE_EXTRACTED"
    known_failures = [
        deep["output_status"],
        "ScriptVersionId=UNKNOWN",
        "PAGE_SCORE_NOT_BOUND_TO_CURRENT_SOURCE_OR_SUBMISSION",
        "TRAINING_EXECUTION_NOT_VERIFIED",
    ]
    if deep.get("narrative_only_categories"):
        known_failures.append("TITLE_OR_MARKDOWN_METHOD_NOT_IMPLEMENTED_IN_CODE=" + pipe(deep["narrative_only_categories"]))
    method_rows.append(
        {
            "source_id": deep["source_id"],
            "owner": deep["owner"],
            "notebook_slug": deep["notebook_slug"],
            "current_version": deep["current_version"],
            "script_version_id": "UNKNOWN",
            "detection": select_categories(cats, ("detection_", "model_3d_unet", "model_cellpose", "model_stardist")),
            "segmentation": select_categories(cats, ("segmentation_", "model_cellpose", "model_stardist")),
            "node_extraction": select_categories(cats, ("detection_local_maxima", "segmentation_connected_components", "model_cellpose", "model_stardist")),
            "temporal_linking": select_categories(cats, ("linking_", "model_trackastra", "model_ultrack", "motion_", "gap_")),
            "assignment_optimization": select_categories(cats, ("linking_hungarian", "optimization_", "model_trackastra", "model_ultrack")),
            "division_detection": "division_detection" if "division_detection" in cats else "NOT_FOUND_IN_CODE_SCAN",
            "track_filtering": "track_filtering" if "track_filtering" in cats else "NOT_FOUND_IN_CODE_SCAN",
            "node_count_calibration": "node_count_calibration" if "node_count_calibration" in cats else "NOT_FOUND_IN_CODE_SCAN",
            "external_model_data": "inputs=" + pipe(deep.get("input_dataset_slugs_from_source", [])) + "; weights=" + pipe(deep.get("weight_paths_from_source", [])),
            "cv_design": pipe(cv_signals) if cv_signals else "NO_METRIC_CV_CODE_SIGNAL_FOUND",
            "reported_local_score": local_score,
            "current_verified_public_score": "UNKNOWN_UNBOUND",
            "page_displayed_score": deep.get("page_displayed_score", ""),
            "runtime": "NOT_VERIFIED_OUTPUTS_EMPTY; accelerator=" + str(deep.get("accelerator", "")),
            "reproducibility": f"FULL_SOURCE_READ; current_version={deep['current_version']}; source_sha256={deep['source_sha256']}; outputs=0",
            "license": deep["license"],
            "known_failure": pipe(known_failures),
            "evidence_source_ids": deep["source_id"] + " | NOTEBOOK_CELL_AUDIT",
        }
    )

method_fields = [
    "source_id", "owner", "notebook_slug", "current_version", "script_version_id", "detection", "segmentation",
    "node_extraction", "temporal_linking", "assignment_optimization", "division_detection",
    "track_filtering", "node_count_calibration", "external_model_data", "cv_design",
    "reported_local_score", "current_verified_public_score", "page_displayed_score", "runtime",
    "reproducibility", "license", "known_failure", "evidence_source_ids",
]
write_csv(ROOT / "07_kaggle_method_comparison.csv", method_rows, method_fields)


# ---------- 数据清单 ----------

def file_group(name: str) -> str:
    if name == "sample_submission.csv":
        return "sample_submission.csv"
    if name.startswith("test/"):
        return "test_zarr_metadata" if name.endswith("zarr.json") else "test_zarr_chunks_or_metadata"
    if name.startswith("train/") and ".geff/" in name:
        if "/nodes/" in name:
            return "train_geff_nodes"
        if "/edges/" in name:
            return "train_geff_edges"
        return "train_geff_metadata"
    if name.startswith("train/") and ".zarr/" in name:
        return "train_zarr_metadata" if name.endswith("zarr.json") else "train_zarr_chunks_or_metadata"
    return "other"


data_rows: list[dict[str, Any]] = [
    {
        "source_id": "KAGGLE_DATA_PAGE_TOTAL",
        "path": "[competition dataset total reported by page]",
        "item_type": "competition_dataset_summary",
        "size_bytes": "UNKNOWN_PAGE_REPORTS_87.61_GB",
        "inventory_scope": "OFFICIAL_PAGE_TOTAL",
        "group": "competition_dataset",
        "observed_file_count": 24886,
        "observed_bytes": "",
        "reported_size": "87.61 GB",
        "format": "Zarr v3 images + GEFF Zarr v3 tracking graphs + sample_submission.csv",
        "split": "train/test embryo-disjoint; visible test copies from train; hidden test swapped on rerun",
        "license": "CC0: Public Domain",
        "read_status": "FULL_PAGE_BODY_READ",
        "evidence": repo_evidence("evidence/browser_official_routes.json"),
        "notes": "Page total; not independently reconstructed from all file metadata because API page 28 was rate-limited.",
    },
    {
        "source_id": "KAGGLE_DATA_FILE_METADATA_GAP_HTTP429",
        "path": "[unfetched file metadata after page 27]",
        "item_type": "competition_file_metadata_gap",
        "size_bytes": "UNKNOWN",
        "inventory_scope": "API_FILE_METADATA_GAP",
        "group": "unfetched",
        "observed_file_count": 24886 - len(partial_file_rows),
        "observed_bytes": "UNKNOWN",
        "reported_size": "",
        "format": "UNKNOWN_NOT_FETCHED",
        "split": "UNKNOWN",
        "license": "CC0: Public Domain (official page)",
        "read_status": "RATE_LIMITED",
        "evidence": repo_evidence("evidence/failure_ledger.json"),
        "notes": f"File API page 28 returned HTTP 429; fetched={len(partial_file_rows)}/page_total=24886; missing_vs_page_total={24886-len(partial_file_rows)}. Do not treat missing as NOT_FOUND.",
    },
]
for index, row in enumerate(partial_file_rows, start=1):
    group = file_group(row["name"])
    data_rows.append(
        {
            "source_id": f"KAGGLE_DATA_FILE_{index:05d}",
            "path": row["name"],
            "item_type": group,
            "size_bytes": int(row["total_bytes"] or 0),
            "inventory_scope": "PARTIAL_API_FILE_METADATA_PAGES_1_27_OF_UNKNOWN",
            "group": group,
            "observed_file_count": 1,
            "observed_bytes": int(row["total_bytes"] or 0),
            "reported_size": "",
            "format": "Zarr v3 member" if ".zarr/" in row["name"] else ("GEFF Zarr v3 member" if ".geff/" in row["name"] else "CSV"),
            "split": "test" if group.startswith("test") else ("train" if group.startswith("train") else "root"),
            "license": "CC0: Public Domain (official page)",
            "read_status": "METADATA_ONLY",
            "evidence": repo_evidence("evidence/competition_files_metadata.csv"),
            "notes": f"API metadata obtained on result_page={row['result_page']}; creation_date={row['creation_date']}; belongs to 5400/24886 partial listing; no file bytes downloaded.",
        }
    )

data_fields = ["source_id", "path", "item_type", "size_bytes", "format", "read_status", "notes", "inventory_scope", "group", "observed_file_count", "observed_bytes", "reported_size", "split", "license", "evidence"]
write_csv(ROOT / "02_official_data_inventory.csv", data_rows, data_fields)


# ---------- Leaderboard ----------

rank_names = {1: "Soheil Ayati", 5: "Tang", 10: "slime", 25: "Dylan Gallagher", 50: "xanderr", 100: "Takauchi Suguru"}
cluster_by_rank = {1: "ranks 1-2 tied at 0.963", 5: "", 10: "", 25: "ranks 25-31 tied at 0.944", 50: "ranks 50-55 tied at 0.940", 100: "ranks 64-99 tied at 0.938; rank100 begins 0.937"}
leader_rows = []
for row in lb_doc["selected_ranks"]:
    rank = int(row["rank"])
    leader_rows.append(
        {
            "source_id": f"KAGGLE_LEADERBOARD_RANK_{rank}",
            "snapshot_time_utc": lb_doc["captured_at_utc"],
            "team_count": lb_doc["dynamic_team_count_observed"],
            "public_score": row["score"],
            "snapshot_utc": lb_doc["captured_at_utc"],
            "snapshot_singapore": lb_doc["captured_at_asia_singapore"],
            "dynamic_team_count_observed": lb_doc["dynamic_team_count_observed"],
            "public_test_fraction": lb_doc["public_fraction_approx"],
            "private_test_fraction": lb_doc["private_fraction"],
            "rank": rank,
            "team_name_visible": rank_names[rank],
            "score": row["score"],
            "tie_cluster": cluster_by_rank[rank],
            "read_status": "FULL_PAGE_BODY_READ",
            "notes": "Dynamic snapshot only; not a frozen final result.",
        }
    )
leader_fields = ["snapshot_time_utc", "rank", "team_count", "public_score", "read_status", "source_id", "notes", "snapshot_utc", "snapshot_singapore", "dynamic_team_count_observed", "public_test_fraction", "private_test_fraction", "team_name_visible", "score", "tie_cluster"]
write_csv(ROOT / "04_leaderboard_snapshot.csv", leader_rows, leader_fields)


# ---------- Markdown 01 / 03 / 06 ----------

routes_by_name = {row["route"]: row for row in official_doc["routes"]}
route_table = "\n".join(
    f"| {r['route']} | {r['read_status']} | {r['main_chars']:,} | `{r['main_sha256']}` | {r['captured_at_utc']} | {r['captured_at_asia_singapore']} |"
    for r in official_doc["routes"]
)

official_md = f"""# 官方比赛事实（staging 草稿）

状态：`OFFICIAL_ROUTES_7_OF_7_FULL_VISIBLE_MAIN_READ`。本文件仅来自 Kaggle 官方页面/API；动态字段均附抓取时点。

## 已核实事实

- 目标：在 3D+time 显微影像中检测细胞、跨时间关联、识别分裂并重建谱系。
- Sponsor：Biohub SF。
- 时间线（官方 Timeline；除另有说明均为 23:59 UTC）：2026-06-29 开始；2026-09-22 报名截止；2026-09-22 组队合并截止；2026-09-29 最终提交截止。
- 奖金总额：$60,000（$18k/$12k/$8k/$6k/$6k/$5k/$5k）。
- Code competition 限制：CPU ≤12h、GPU ≤12h、internet disabled；允许免费且公开可得的外部数据和预训练模型；输出名须为 `submission.csv`。
- Overview 动态值：抓取时显示 3,300 Participants、3,029 Teams；Leaderboard 另一个稍晚快照的末名为 3,032。两者均为时点观察，不强行对齐。
- 本轮 Kaggle 写入：submission=0、Notebook Version save=0、training=0、rule acceptance=0、Dataset create=0。

## 7 个强制入口实读证据

| route | read_status | main chars | main SHA-256 | UTC | Asia/Singapore |
|---|---|---:|---|---|---|
{route_table}

另有 Kaggle API `competition_list_pages` 返回的 8 个正文页全部读取并记录哈希：rules、Description、Evaluation、Timeline、data-description、Prizes、Code Requirements、abstract；见 `evidence/official_pages_metadata.csv`。

## 重要边界

- Rules 页面显示账号此前已接受规则；这是既有账号状态，本轮未执行接受或报名。
- Leaderboard 页面也显示账号既有 0.885 行及一个正在评分的既有 submission；均不是本轮动作，也未绑定为本项目结果。
- 官方文件元数据仅取得 5,400 条后在第 28 页 HTTP 429；因此文件级清单是 `PARTIAL_METADATA_LIST_RATE_LIMITED`，不能称全量。
"""
(ROOT / "01_official_competition.md").write_text(official_md, encoding="utf-8")

rules_metric_md = f"""# 官方规则、数据与评分（staging 草稿）

## 评分公式与聚合

- `score = adjusted_edge_jaccard + 0.1 * division_jaccard`。
- 每个时间点按物理尺度后的质心距离做最优二分匹配，最大距离 7.0 µm；尺度 `z=1.625, y=x=0.40625 µm/voxel`。
- 若预测边两端都匹配到由真值边连接的真值节点，则为 edge TP；基础 Edge Jaccard 为 `TP/(TP+FP+FN)`，并对过量预测总节点数施加调整。
- 每样本 adjusted edge Jaccard 以该样本 `(TP+FP+FN)` 加权平均。
- 真值分裂定义为出度≥2；预测连通分量需覆盖分裂前阶段并触达两条子代谱系。Division TP/FP/FN 跨全部样本 micro-average 后求 Jaccard。
- 稀疏真值由 metric 处理；官方明确说明最终 score 可能超过 1.0。

## 数据与提交

- 图像是 Zarr v3，数组路径 `0/`，形状 `(T,Z,Y,X)`，典型 `(100,64,256,256)`、`uint16`；chunk `(1,64,256,256)`、blosc/zstd。
- GEFF 同样基于 Zarr v3：`nodes/ids`，`nodes/props/{{t,z,y,x}}/values`，`edges/ids` 为 `(N,2)` 的 source/target。
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
- 评分补丁的正式时间线、重算范围和 host 解释需与 Discussion 深读结果合并；本 staging 不把普通参赛者文字升级为官方规则。

证据：`evidence/official_pages_metadata.csv`、`evidence/browser_official_routes.json`、`evidence/browser_leaderboard_snapshot.json`、`evidence/notebook_deep_read.jsonl`。
"""
(ROOT / "03_official_rules_and_metric.md").write_text(rules_metric_md, encoding="utf-8")

method_counts = Counter(cat for ref in code_categories for cat in code_categories[ref])
source_bytes_total = sum(int(r["source_bytes"]) for r in deep_rows)
markdown_total = sum(int(r["markdown_cell_count"]) for r in deep_rows)
code_total = sum(int(r["code_cell_count"]) for r in deep_rows)
outputs_total = sum(int(r["output_item_count"]) for r in deep_rows)
unique_authors = len({r["owner"] for r in deep_rows})

pair_overlaps: list[dict[str, Any]] = []
refs = sorted(code_cell_hashes)
for i, left in enumerate(refs):
    for right in refs[i + 1 :]:
        a, b = code_cell_hashes[left], code_cell_hashes[right]
        shared = len(a & b)
        union = len(a | b)
        if shared:
            pair_overlaps.append({"left": left, "right": right, "shared_large_code_cells": shared, "jaccard": shared / union if union else 0.0})
pair_overlaps.sort(key=lambda x: (-x["shared_large_code_cells"], -x["jaccard"]))

deep_table_rows = []
for row in deep_rows:
    cats = ", ".join(row["implemented_code_categories"])
    deep_table_rows.append(
        f"| `{row['notebook_ref']}` | V{row['current_version']} / UNKNOWN | {row['source_bytes']:,} | {row['markdown_cell_count']}/{row['code_cell_count']}/0 | {cats} | {row.get('page_displayed_score','')} |"
    )

overlap_lines = "\n".join(
    f"- `{x['left']}` ↔ `{x['right']}`：共享 {x['shared_large_code_cells']} 个 ≥500-byte code cell SHA（Jaccard {x['jaccard']:.3f}）。"
    for x in pair_overlaps[:10]
) or "- 未发现完全相同的 ≥500-byte code cell SHA。"

deep_md = f"""# Kaggle Code 源码深读（staging 草稿）

## 覆盖结论

- 5 种 competition Code 排序实际加载：Most Votes、Hotness、Recently Created、Recently Run、Public Score。
- 20 个指定关键词全部实际检索；`temporal affinity fields` 返回 0 条可见结果，其余实际返回 10–20 条。
- 可见 occurrence：排序 104 + 关键词 356 = 460；按 `owner/slug` 去重后 194。
- 实际 GetKernel 当前源码：30/30 成功，来源 25 个不同作者；最大单一作者 3 本。
- 源码合计 {source_bytes_total:,} bytes；340 cells = {markdown_total} markdown + {code_total} code。218 个 code cells 全部生成 SHA 并做语义扫描。
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

""" + "\n".join(f"- `{key}`: {value}/30" for key, value in sorted(method_counts.items())) + f"""

## 30 本逐项

`M/C/O` 为 markdown cells / code cells / output-bearing code cells。

| Notebook | current version / ScriptVersionId | bytes | M/C/O | code-verified categories | page card score |
|---|---|---:|---:|---|---:|
""" + "\n".join(deep_table_rows) + f"""

## 完全相同大 code-cell 复用信号

下列仅证明至少一个大 cell SHA 完全相同，不自动断言整本复制关系：

{overlap_lines}

## 版本、分数和时间字段限制

- `currentVersionNumber` 是当前源码响应中的版本序号，不是 ScriptVersionId。
- API `lastRunTime` 本轮 30 个值均与请求秒级同步、但固定早约 3 天，和 Code 卡片相对更新时间冲突；已保留为 `api_last_run_time_field_observed`，不作为 updated_at。
- Historical version source/diff 未读取；同一 Notebook 的 score-linked historical ScriptVersionId 仍是 `UNKNOWN`。这项不能用不同 slug（例如 v18/v19）冒充同一 Notebook 版本史。
- 许可证字段未由 GetKernel 暴露，源码未落盘；仅保存 hash、短摘录和逐-cell evidence。

证据：`evidence/notebook_deep_read.jsonl`、`evidence/notebook_cell_audit.jsonl`、`evidence/notebook_source_request_log.csv`。
"""
(ROOT / "06_kaggle_code_deep_read.md").write_text(deep_md, encoding="utf-8")


# ---------- Query log ----------

with (EVIDENCE / "api_query_log_original.csv").open(encoding="utf-8") as handle:
    base_api_query_rows = [row for row in csv.DictReader(handle) if row.get("platform") == "Kaggle official API"]
query_rows: list[dict[str, Any]] = []
query_fields = [
    "query_id", "category", "platform", "query", "sort_order", "result_page", "reported_total",
    "actually_obtained", "unique_after_dedupe", "deep_read_count", "access_time_utc",
    "access_time_singapore", "status", "evidence_path", "notes",
]

for base in base_api_query_rows:
    source_type = base.get("source_type", "")
    category = "kaggle_code" if source_type == "kaggle_code" else ("kaggle_discussion" if source_type == "kaggle_discussion" else "official")
    is_rate = "429" in base.get("error", "")
    evidence_rel = "evidence/failure_ledger.json" if is_rate else (
        "evidence/official_pages_metadata.csv" if source_type == "official_competition_page" else "evidence/competition_files_metadata.csv"
    )
    query_rows.append({
        "category": category, "platform": base["platform"], "query": base["query"],
        "sort_order": base.get("sort_order", ""), "result_page": base.get("result_page", ""),
        "reported_total": base.get("total_reported", ""), "actually_obtained": base.get("returned_count", ""),
        "unique_after_dedupe": base.get("returned_count", ""), "deep_read_count": 0,
        "access_time_utc": base.get("access_started_utc", ""), "access_time_singapore": base.get("access_started_singapore", ""),
        "status": "RATE_LIMITED" if is_rate else base.get("status", "UNKNOWN"), "evidence_path": repo_evidence(evidence_rel),
        "notes": f"endpoint={base.get('endpoint','')}; response_bytes={base.get('response_bytes','')}; response_sha256={base.get('response_sha256','')}; error={base.get('error','')}",
    })

sort_time = sort_doc["captured_at_utc"]
sort_sg = datetime.fromisoformat(sort_time.replace("Z", "+00:00")).astimezone(SG).isoformat()
for capture in sort_doc["sorts"]:
    query_rows.append({
        "category": "kaggle_code", "platform": "Kaggle logged-in browser",
        "query": "biohub-cell-tracking-during-development", "sort_order": capture["sort"], "result_page": "visible_loaded_panel",
        "reported_total": "", "actually_obtained": len(capture["rows"]),
        "unique_after_dedupe": len({row["ref"] for row in capture["rows"]}), "deep_read_count": 0,
        "access_time_utc": sort_time, "access_time_singapore": sort_sg, "status": "OK_BROWSER_VISIBLE",
        "evidence_path": repo_evidence("evidence/browser_code_sort_captures.json"),
        "notes": f"response_bytes={capture['bytes']}; response_sha256={capture['sha256']}; only visible loaded panel, total not reported",
    })
for capture in keyword_doc["captures"]:
    time_utc = capture["captured_at"]
    time_sg = datetime.fromisoformat(time_utc.replace("Z", "+00:00")).astimezone(SG).isoformat()
    query_rows.append({
        "category": "kaggle_code", "platform": "Kaggle logged-in browser",
        "query": capture["query"], "sort_order": "Public Score / scoreDescending", "result_page": "visible_loaded_panel",
        "reported_total": "", "actually_obtained": len(capture["rows"]),
        "unique_after_dedupe": len({row["ref"] for row in capture["rows"]}), "deep_read_count": 0,
        "access_time_utc": time_utc, "access_time_singapore": time_sg,
        "status": "OK_ZERO_VISIBLE_RESULTS" if len(capture["rows"]) == 0 else "OK_BROWSER_VISIBLE",
        "evidence_path": repo_evidence("evidence/browser_code_keyword_captures.json"),
        "notes": f"response_bytes={capture['bytes']}; response_sha256={capture['sha256']}; only visible loaded panel, total not reported",
    })
for route in official_doc["routes"]:
    query_rows.append({
        "category": "official", "platform": "Kaggle logged-in browser", "query": route["url"],
        "sort_order": "", "result_page": "visible_main", "reported_total": 1, "actually_obtained": 1,
        "unique_after_dedupe": 1, "deep_read_count": 1, "access_time_utc": route["captured_at_utc"],
        "access_time_singapore": route["captured_at_asia_singapore"], "status": "FULL_PAGE_BODY_READ",
        "evidence_path": repo_evidence("evidence/browser_official_routes.json"),
        "notes": f"route={route['route']}; main_bytes={route['main_utf8_bytes']}; main_sha256={route['main_sha256']}; browser_status={route['read_status']}",
    })
with (EVIDENCE / "notebook_source_request_log.csv").open(encoding="utf-8") as handle:
    for request in csv.DictReader(handle):
        query_rows.append({
            "category": "kaggle_code", "platform": "Kaggle official GetKernel API",
            "query": request["notebook_ref"], "sort_order": request["selection_reason"],
            "result_page": request["attempt_index"], "reported_total": 1,
            "actually_obtained": 1 if request["status"] == "FULL_SOURCE_READ" else 0,
            "unique_after_dedupe": 1 if request["status"] == "FULL_SOURCE_READ" else 0,
            "deep_read_count": 1 if request["status"] == "FULL_SOURCE_READ" else 0,
            "access_time_utc": request["access_started_utc"], "access_time_singapore": request["access_started_singapore"],
            "status": "FULL_NOTEBOOK_SOURCE_READ" if request["status"] == "FULL_SOURCE_READ" else request["status"],
            "evidence_path": repo_evidence("evidence/notebook_deep_read.jsonl"),
            "notes": f"endpoint=KernelsApiService/GetKernel; response_source_bytes={request['response_source_bytes']}; response_sha256={request['response_source_sha256']}; error={request['error']}",
        })
for index, row in enumerate(query_rows, start=1):
    row["query_id"] = f"OFFICIAL_KAGGLE_Q{index:04d}"
write_csv(ROOT / "search_query_log.csv", query_rows, query_fields)


# ---------- Source manifest ----------

manifest: list[dict[str, Any]] = []
for row in official_api_rows:
    manifest.append({
        "source_id": "KAGGLE_OFFICIAL_API_" + row["page_name"].upper().replace(" ", "_").replace("-", "_"),
        "source_type": "official_competition_page", "platform": "Kaggle", "title": row["page_name"],
        "author": "Kaggle / Biohub SF", "url": "https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/overview",
        "query": "competition_list_pages", "sort_order": "official page order", "result_page": "all", "result_rank": "",
        "access_time_utc": row["access_time_utc"], "access_time_singapore": row["access_time_singapore"],
        "read_status": "FULL_PAGE_BODY_READ", "bytes_observed": row["bytes_observed"], "sha256": row["sha256"],
        "version_id": "", "commit_sha": "", "license": "page-specific; competition data CC0",
        "evidence_path": repo_evidence("evidence/official_pages_metadata.csv"), "factual_use_allowed": True,
        "notes": "Full API body read in memory; persisted hash/headings/short excerpt only.",
    })
for route in official_doc["routes"]:
    manifest.append({
        "source_id": "KAGGLE_OFFICIAL_BROWSER_" + route["route"].upper(), "source_type": "official_competition_page",
        "platform": "Kaggle", "title": route["title"], "author": "Kaggle / Biohub SF", "url": route["url"],
        "query": route["route"], "sort_order": "official route", "result_page": "visible_main", "result_rank": "",
        "access_time_utc": route["captured_at_utc"],
        "access_time_singapore": route["captured_at_asia_singapore"], "read_status": "FULL_PAGE_BODY_READ",
        "bytes_observed": route["main_utf8_bytes"], "sha256": route["main_sha256"], "version_id": "", "commit_sha": "",
        "license": "page-specific", "evidence_path": repo_evidence("evidence/browser_official_routes.json"), "factual_use_allowed": True,
        "notes": route["read_status"],
    })
manifest.extend([
    {
        "source_id": "KAGGLE_COMPETITION_FILE_METADATA_PARTIAL", "source_type": "competition_file_metadata", "platform": "Kaggle",
        "title": "Competition files metadata pages 1-27", "author": "Kaggle", "url": "https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/data",
        "query": "competition_list_files page_size=200", "sort_order": "API order", "result_page": "1-27 then page28 HTTP429", "result_rank": "1-5400",
        "access_time_utc": "2026-09-03T08:05:58.440376+00:00", "access_time_singapore": "2026-09-03T16:05:58.440376+08:00",
        "read_status": "RATE_LIMITED", "bytes_observed": (EVIDENCE / "competition_files_metadata.csv").stat().st_size,
        "sha256": sha_file(EVIDENCE / "competition_files_metadata.csv"), "version_id": "", "commit_sha": "", "license": "CC0 (official page)",
        "evidence_path": repo_evidence("evidence/competition_files_metadata.csv"), "factual_use_allowed": True,
        "notes": "5400 metadata records; 21748854443 listed data bytes; no competition data bytes downloaded; not complete.",
    },
    {
        "source_id": "KAGGLE_LEADERBOARD_BROWSER_20260903", "source_type": "leaderboard_browser_snapshot", "platform": "Kaggle",
        "title": "Biohub public leaderboard snapshot", "author": "Kaggle", "url": lb_doc["url"], "query": "leaderboard virtual scroll",
        "sort_order": "public score descending", "result_page": "rank1-149 plus total range", "result_rank": "1|5|10|25|50|100",
        "access_time_utc": lb_doc["captured_at_utc"],
        "access_time_singapore": lb_doc["captured_at_asia_singapore"], "read_status": "FULL_PAGE_BODY_READ",
        "bytes_observed": (EVIDENCE / "browser_leaderboard_snapshot.json").stat().st_size,
        "sha256": sha_file(EVIDENCE / "browser_leaderboard_snapshot.json"), "version_id": "", "commit_sha": "", "license": "page-specific",
        "evidence_path": repo_evidence("evidence/browser_leaderboard_snapshot.json"), "factual_use_allowed": True,
        "notes": "Dynamic snapshot; selected ranks 1/5/10/25/50/100 and tie clusters.",
    },
])
for inv in inventory_rows:
    ref = inv["owner"] + "/" + inv["notebook_slug"]
    deep = deep_by_ref.get(ref)
    manifest.append({
        "source_id": notebook_source_id(ref), "source_type": "kaggle_public_code",
        "platform": "Kaggle", "title": inv["notebook_title"], "author": inv["owner"], "url": inv["url"],
        "query": inv["relevance"], "sort_order": "multi-sort + keyword", "result_page": "visible code cards",
        "result_rank": pipe(f"{x['discovery_context']}:{x['position']}" for x in cards_by_ref[ref]),
        "access_time_utc": deep.get("access_time_utc", sort_time) if deep else sort_time,
        "access_time_singapore": deep.get("access_time_singapore", sort_sg) if deep else sort_sg,
        "read_status": inv["read_status"], "bytes_observed": deep.get("source_bytes", "") if deep else "",
        "sha256": inv["source_sha256"], "version_id": "UNKNOWN" if not deep else f"currentVersionNumber={deep['current_version']}; ScriptVersionId=UNKNOWN",
        "commit_sha": "", "license": inv["license"],
        "evidence_path": repo_evidence("evidence/notebook_deep_read.jsonl" if deep else "evidence/browser_code_keyword_captures.json"),
        "factual_use_allowed": bool(deep),
        "notes": "Method claims allowed only for FULL_NOTEBOOK_SOURCE_READ rows; card score is unbound and dynamic.",
    })
write_jsonl(ROOT / "source_manifest.jsonl", manifest)


# ---------- Claims fragment for parent merge ----------

claims_fields = [
    "claim_id", "report_section", "claim_text", "claim_type", "source_ids", "evidence_paths",
    "direct_or_inference", "confidence", "conflict_present", "conflict_notes",
]
official_evidence = repo_evidence("evidence/official_pages_metadata.csv")
browser_evidence = repo_evidence("evidence/browser_official_routes.json")
leaderboard_evidence = repo_evidence("evidence/browser_leaderboard_snapshot.json")
notebook_evidence = repo_evidence("evidence/notebook_deep_read.jsonl")
cell_evidence = repo_evidence("evidence/notebook_cell_audit.jsonl")
file_evidence = repo_evidence("evidence/competition_files_metadata.csv")
failure_evidence = repo_evidence("evidence/failure_ledger.json")
claims_rows: list[dict[str, Any]] = [
    {
        "claim_id": "OFFICIAL_KAGGLE_CLAIM_001", "report_section": "official_competition",
        "claim_text": "任务要求在 3D+time 显微影像中检测并跨时间关联细胞、识别分裂并重建谱系。",
        "claim_type": "OFFICIAL_FACT", "source_ids": "KAGGLE_OFFICIAL_API_DESCRIPTION | KAGGLE_OFFICIAL_BROWSER_OVERVIEW",
        "evidence_paths": f"{official_evidence} | {browser_evidence}", "direct_or_inference": "DIRECT",
        "confidence": "HIGH", "conflict_present": "false", "conflict_notes": "",
    },
    {
        "claim_id": "OFFICIAL_KAGGLE_CLAIM_002", "report_section": "metric",
        "claim_text": "官方 score 为 adjusted_edge_jaccard + 0.1 * division_jaccard。",
        "claim_type": "OFFICIAL_FACT", "source_ids": "KAGGLE_OFFICIAL_API_EVALUATION | KAGGLE_OFFICIAL_BROWSER_OVERVIEW",
        "evidence_paths": f"{official_evidence} | {browser_evidence}", "direct_or_inference": "DIRECT",
        "confidence": "HIGH", "conflict_present": "false", "conflict_notes": "",
    },
    {
        "claim_id": "OFFICIAL_KAGGLE_CLAIM_003", "report_section": "metric",
        "claim_text": "节点匹配最大物理距离为 7.0 µm，体素尺度为 z=1.625、y=x=0.40625 µm/voxel。",
        "claim_type": "OFFICIAL_FACT", "source_ids": "KAGGLE_OFFICIAL_API_EVALUATION",
        "evidence_paths": official_evidence, "direct_or_inference": "DIRECT", "confidence": "HIGH",
        "conflict_present": "false", "conflict_notes": "",
    },
    {
        "claim_id": "OFFICIAL_KAGGLE_CLAIM_004", "report_section": "metric",
        "claim_text": "adjusted edge Jaccard 按各样本 TP+FP+FN 加权；division Jaccard 跨样本 micro-average，最终 score 可超过 1。",
        "claim_type": "OFFICIAL_FACT", "source_ids": "KAGGLE_OFFICIAL_API_EVALUATION",
        "evidence_paths": official_evidence, "direct_or_inference": "DIRECT", "confidence": "HIGH",
        "conflict_present": "false", "conflict_notes": "",
    },
    {
        "claim_id": "OFFICIAL_KAGGLE_CLAIM_005", "report_section": "official_data",
        "claim_text": "图像使用 Zarr v3，数组通常为 (T,Z,Y,X)=(100,64,256,256) uint16，chunk=(1,64,256,256)，并采用 blosc/zstd。",
        "claim_type": "OFFICIAL_FACT", "source_ids": "KAGGLE_OFFICIAL_API_DATA_DESCRIPTION | KAGGLE_OFFICIAL_BROWSER_DATA",
        "evidence_paths": f"{official_evidence} | {browser_evidence}", "direct_or_inference": "DIRECT",
        "confidence": "HIGH", "conflict_present": "false", "conflict_notes": "",
    },
    {
        "claim_id": "OFFICIAL_KAGGLE_CLAIM_006", "report_section": "official_data",
        "claim_text": "跟踪图采用 GEFF Zarr v3，包含 node ids/props 与 edge ids；estimated_number_of_nodes 是真实总细胞数估计。",
        "claim_type": "OFFICIAL_FACT", "source_ids": "KAGGLE_OFFICIAL_API_DATA_DESCRIPTION | KAGGLE_OFFICIAL_BROWSER_DATA",
        "evidence_paths": f"{official_evidence} | {browser_evidence}", "direct_or_inference": "DIRECT",
        "confidence": "HIGH", "conflict_present": "false", "conflict_notes": "",
    },
    {
        "claim_id": "OFFICIAL_KAGGLE_CLAIM_007", "report_section": "official_data",
        "claim_text": "train/test embryo-disjoint；可见 test 是 train copies，hidden test 会在 rerun 时替换。",
        "claim_type": "OFFICIAL_FACT", "source_ids": "KAGGLE_OFFICIAL_API_DATA_DESCRIPTION | KAGGLE_OFFICIAL_BROWSER_DATA",
        "evidence_paths": f"{official_evidence} | {browser_evidence}", "direct_or_inference": "DIRECT",
        "confidence": "HIGH", "conflict_present": "false", "conflict_notes": "",
    },
    {
        "claim_id": "OFFICIAL_KAGGLE_CLAIM_008", "report_section": "official_data",
        "claim_text": "数据页在抓取时报告 24,886 files、87.61 GB、CC0: Public Domain。",
        "claim_type": "OFFICIAL_FACT", "source_ids": "KAGGLE_OFFICIAL_BROWSER_DATA",
        "evidence_paths": browser_evidence, "direct_or_inference": "DIRECT", "confidence": "HIGH",
        "conflict_present": "false", "conflict_notes": "动态页面时点值。",
    },
    {
        "claim_id": "OFFICIAL_KAGGLE_CLAIM_009", "report_section": "official_data",
        "claim_text": "只读文件 API 取得 5,400 条元数据后第 28 页遇到 HTTP 429，因此清单是 5,400/24,886 的部分覆盖，而非全量。",
        "claim_type": "MEASURED", "source_ids": "KAGGLE_COMPETITION_FILE_METADATA_PARTIAL",
        "evidence_paths": f"{file_evidence} | {failure_evidence}", "direct_or_inference": "DIRECT",
        "confidence": "HIGH", "conflict_present": "false", "conflict_notes": "缺失项为 RATE_LIMITED，不是 NOT_FOUND。",
    },
    {
        "claim_id": "OFFICIAL_KAGGLE_CLAIM_010", "report_section": "submission_format",
        "claim_text": "submission 字段为 id,dataset,row_type,node_id,t,z,y,x,source_id,target_id，且每个 test dataset 都必须出现。",
        "claim_type": "OFFICIAL_FACT", "source_ids": "KAGGLE_OFFICIAL_API_EVALUATION | KAGGLE_OFFICIAL_API_DATA_DESCRIPTION",
        "evidence_paths": official_evidence, "direct_or_inference": "DIRECT", "confidence": "HIGH",
        "conflict_present": "false", "conflict_notes": "",
    },
    {
        "claim_id": "OFFICIAL_KAGGLE_CLAIM_011", "report_section": "timeline_and_prizes",
        "claim_text": "比赛时间线为 2026-06-29 开始、2026-09-22 报名及组队合并截止、2026-09-29 最终提交截止；总奖金为 60,000 美元。",
        "claim_type": "OFFICIAL_FACT", "source_ids": "KAGGLE_OFFICIAL_API_TIMELINE | KAGGLE_OFFICIAL_API_PRIZES",
        "evidence_paths": official_evidence, "direct_or_inference": "DIRECT", "confidence": "HIGH",
        "conflict_present": "false", "conflict_notes": "截止时间按官方页为 23:59 UTC。",
    },
    {
        "claim_id": "OFFICIAL_KAGGLE_CLAIM_012", "report_section": "rules",
        "claim_text": "团队最多 5 人、每日最多 5 次提交、最多选择 2 个 final submissions；winner code license 为 MIT。",
        "claim_type": "OFFICIAL_FACT", "source_ids": "KAGGLE_OFFICIAL_API_RULES | KAGGLE_OFFICIAL_BROWSER_RULES",
        "evidence_paths": f"{official_evidence} | {browser_evidence}", "direct_or_inference": "DIRECT",
        "confidence": "HIGH", "conflict_present": "false", "conflict_notes": "",
    },
    {
        "claim_id": "OFFICIAL_KAGGLE_CLAIM_013", "report_section": "code_requirements",
        "claim_text": "Code competition 允许 CPU/GPU 各最多 12 小时，internet 必须关闭；允许公开且免费可得的外部数据和预训练模型。",
        "claim_type": "OFFICIAL_FACT", "source_ids": "KAGGLE_OFFICIAL_API_CODE_REQUIREMENTS | KAGGLE_OFFICIAL_API_RULES",
        "evidence_paths": official_evidence, "direct_or_inference": "DIRECT", "confidence": "HIGH",
        "conflict_present": "false", "conflict_notes": "外部资源另受 Reasonableness 和获奖者复现义务约束。",
    },
    {
        "claim_id": "OFFICIAL_KAGGLE_CLAIM_014", "report_section": "leaderboard",
        "claim_text": "2026-09-03T08:32:44.130Z 动态公开榜快照：rank 1/5/10/25/50/100 分别为 0.963/0.955/0.949/0.944/0.940/0.937，页面公开/私有比例约 29%/71%。",
        "claim_type": "MEASURED", "source_ids": "KAGGLE_LEADERBOARD_BROWSER_20260903 | KAGGLE_OFFICIAL_BROWSER_LEADERBOARD",
        "evidence_paths": leaderboard_evidence, "direct_or_inference": "DIRECT", "confidence": "HIGH",
        "conflict_present": "false", "conflict_notes": "动态时点快照，不是最终结果。",
    },
    {
        "claim_id": "OFFICIAL_KAGGLE_CLAIM_015", "report_section": "kaggle_code_coverage",
        "claim_text": "5 个排序和 20 个关键词页面合计观察 460 个卡片出现，去重后为 194 个 owner/slug。",
        "claim_type": "MEASURED", "source_ids": "KAGGLE_OFFICIAL_BROWSER_CODE",
        "evidence_paths": f"{repo_evidence('evidence/browser_code_sort_captures.json')} | {repo_evidence('evidence/browser_code_keyword_captures.json')}",
        "direct_or_inference": "DIRECT", "confidence": "HIGH", "conflict_present": "false",
        "conflict_notes": "仅是已加载可见结果，不是 Kaggle 全部 Code 的平台总数。",
    },
    {
        "claim_id": "OFFICIAL_KAGGLE_CLAIM_016", "report_section": "kaggle_code_deep_read",
        "claim_text": "30 本不同 Notebook 当前源码已逐 cell 审计，共 3,022,497 bytes、122 个 markdown cells、218 个 code cells；GetKernel 中 output-bearing cells 为 0。",
        "claim_type": "MEASURED", "source_ids": pipe(row["source_id"] for row in deep_rows),
        "evidence_paths": f"{notebook_evidence} | {cell_evidence}", "direct_or_inference": "DIRECT",
        "confidence": "HIGH", "conflict_present": "false",
        "conflict_notes": "输出为空，因此不验证训练、推理、runtime、本地分数或产物成功。",
    },
    {
        "claim_id": "OFFICIAL_KAGGLE_CLAIM_017", "report_section": "kaggle_code_method",
        "claim_text": "getting-started Notebook 当前源码使用阈值型节点提取、相邻帧 Hungarian 匹配并生成 submission。",
        "claim_type": "SOURCE_CODE_VERIFIED",
        "source_ids": "KAGGLE_CODE_INVERSION_CELL-TRACKING-GETTING-STARTED-W-NEAREST-NEIGHBOR",
        "evidence_paths": f"{notebook_evidence} | {cell_evidence}", "direct_or_inference": "DIRECT",
        "confidence": "HIGH", "conflict_present": "false", "conflict_notes": "源码存在不证明已在平台成功运行。",
    },
    {
        "claim_id": "OFFICIAL_KAGGLE_CLAIM_018", "report_section": "kaggle_code_method",
        "claim_text": "Trackastra 候选当前源码包含 DoG/local maxima、watershed、Trackastra graph transformer 与轨迹过滤信号。",
        "claim_type": "SOURCE_CODE_VERIFIED",
        "source_ids": "KAGGLE_CODE_JIRKABOROVEC_BIOHUB-CELLTRACK-DOG-TRACKASTRA-GRAPH-TRANS",
        "evidence_paths": f"{notebook_evidence} | {cell_evidence}", "direct_or_inference": "DIRECT",
        "confidence": "HIGH", "conflict_present": "false", "conflict_notes": "源码存在不证明已在平台成功运行。",
    },
    {
        "claim_id": "OFFICIAL_KAGGLE_CLAIM_019", "report_section": "metric_exploit_risk",
        "claim_text": "biohub-ct-mix-divaug 当前源码明确注释可选 negative-time/out-of-volume hub 与 forks 为 metric exploit，并注明可能被 patch。",
        "claim_type": "SOURCE_CODE_VERIFIED", "source_ids": "KAGGLE_CODE_XIAOLEILIAN_BIOHUB-CT-MIX-DIVAUG",
        "evidence_paths": f"{notebook_evidence} | {cell_evidence}", "direct_or_inference": "DIRECT",
        "confidence": "HIGH", "conflict_present": "false",
        "conflict_notes": "仅证明当前源码中存在该逻辑与注释，不验证卡片分数或补丁状态。",
    },
]
write_csv(ROOT / "claims_fragment.csv", claims_rows, claims_fields)


# ---------- Failure ledger / coverage ----------

failures = metadata_summary.get("failures", [])
failure_ledger = {
    "schema_version": "1.0",
    "api_failure_count": len(failures),
    "rate_limited_failure_count": sum("429" in x.get("error", "") for x in failures),
    "failures": failures,
    "recovery": {
        "high_frequency_retry_storm": False,
        "getkernel_low_frequency_run": "30/30 success at 4-second interval; no 429",
        "competition_file_metadata": "not retried; remains 5400/24886 page-total, PARTIAL",
        "browser_zero_result_query": "temporal affinity fields = 0 visible rows; OK_ZERO_VISIBLE_RESULTS, not NOT_FOUND",
    },
}
write_json(EVIDENCE / "failure_ledger.json", failure_ledger)

failure_table = "\n".join(
    "| {index} | {utc} | {sg} | {source_type} | {endpoint} | {page} | {sort_order} | `{error}` |".format(
        index=index,
        utc=row.get("access_time_utc", ""),
        sg=row.get("access_time_singapore", ""),
        source_type=row.get("source_type", ""),
        endpoint=row.get("endpoint", ""),
        page=row.get("page", ""),
        sort_order=row.get("sort_order", ""),
        error=str(row.get("error", "")).replace("|", "\\|"),
    )
    for index, row in enumerate(failures, start=1)
)
failure_md = f"""# Kaggle 只读访问失败片段（供父任务合并）

## 结论

- 阻断 source_id：`KAGGLE_COMPETITION_FILE_METADATA_PARTIAL`，manifest 状态 `RATE_LIMITED`。
- 文件元数据取得 27 页 × 200 = 5,400 条；第 28 页 HTTP 429。官方 data 页时点总量为 24,886，故缺口是相对页面时点总量的 19,486 条，不能写成 `NOT_FOUND`，也不能宣称全量。
- 初始 collector 共记录 {len(failures)} 次 HTTP 429：competition files 1、leaderboard 1、Kaggle Code list 25、Discussion list 6。
- 收到限流后停止高频自动重试。冷却后仅运行一次受控的 GetKernel 源码读取队列（4 秒间隔、首个 429 即停），30/30 成功且无 429；这不补齐 competition files 的缺页。
- Leaderboard、Code discovery 与 official routes 后续通过登录态浏览器只读路径取得；Discussion 由父任务另行负责。本轮物理 Kaggle 写入均为 0。

完整机器可读证据：`{repo_evidence('evidence/failure_ledger.json')}`、`{repo_evidence('search_query_log.csv')}`。

## 原始失败逐项

| # | UTC | Asia/Singapore | source_type | endpoint | page | sort_order | error |
|---:|---|---|---|---|---:|---|---|
{failure_table}
"""
(ROOT / "access_failures_fragment.md").write_text(failure_md, encoding="utf-8")

coverage = {
    "schema_version": "1.0",
    "generated_at_utc": now_pair()[0],
    "generated_at_singapore": now_pair()[1],
    "bounded_scope_status": "PARTIAL_RATE_LIMITED_COMPETITION_FILE_METADATA; CODE_SOURCE_TARGET_MET",
    "official": {
        "required_routes": 7, "routes_full_visible_main_read": 7, "api_content_pages_full_read": 8,
        "competition_file_page_total_reported": 24886, "competition_file_metadata_obtained": 5400,
        "competition_file_metadata_missing_vs_page_total": 24886 - 5400, "file_metadata_status": "PARTIAL_RATE_LIMITED",
    },
    "leaderboard": {
        "required_rank_values_read": 6, "dynamic_team_count_observed": lb_doc["dynamic_team_count_observed"],
        "public_fraction": "29%", "private_fraction": "71%", "highest_score": 0.963,
    },
    "kaggle_code": {
        "sort_queries": len(sort_doc["sorts"]), "keyword_queries": len(keyword_doc["captures"]),
        "sort_visible_occurrences": sum(len(x["rows"]) for x in sort_doc["sorts"]),
        "keyword_visible_occurrences": sum(len(x["rows"]) for x in keyword_doc["captures"]),
        "visible_occurrences_total": len(occurrences), "unique_notebook_refs": len(inventory_rows),
        "full_source_read": len(deep_rows), "metadata_only": len(inventory_rows) - len(deep_rows),
        "source_bytes_read": source_bytes_total, "total_cells": len(cell_rows), "code_cells_all_hashed_scanned": code_total,
        "output_bearing_code_cells": sum(int(r["output_bearing_code_cell_count"]) for r in deep_rows),
        "ScriptVersionId_verified": sum(r["script_version_id"] != "UNKNOWN" for r in deep_rows),
        "ScriptVersionId_unknown": sum(r["script_version_id"] == "UNKNOWN" for r in deep_rows),
        "current_score_verified": 0, "source_saved": 0, "unique_authors_full_source": unique_authors,
    },
    "failures": {"api_failures_logged": len(failures), "http_429_failures": sum("429" in x.get("error", "") for x in failures)},
    "physical_actions": {"kaggle_submission": 0, "notebook_version_save": 0, "training": 0, "rule_acceptance": 0, "dataset_create": 0, "competition_data_download": 0},
    "handoff": "Discussion 08-10 intentionally not generated in this staging subtask; parent agent owns that scope.",
}
write_json(ROOT / "coverage_summary.json", coverage)


# ---------- Final lightweight self-check receipt ----------

project_root = ROOT.parents[3]
manifest_schema = {
    "source_id", "source_type", "platform", "title", "author", "url", "query", "sort_order",
    "result_page", "result_rank", "access_time_utc", "access_time_singapore", "read_status",
    "bytes_observed", "sha256", "version_id", "commit_sha", "license", "evidence_path",
    "factual_use_allowed", "notes",
}
allowed_manifest_statuses = {
    "FULL_PAGE_BODY_READ", "FULL_THREAD_READ", "PARTIAL_THREAD_READ",
    "FULL_NOTEBOOK_SOURCE_AND_OUTPUTS_READ", "FULL_NOTEBOOK_SOURCE_READ",
    "NOTEBOOK_SOURCE_PARTIAL", "FULL_RELEVANT_REPO_SOURCE_READ", "TARGET_FILES_READ",
    "README_ONLY", "METADATA_ONLY", "TITLE_SNIPPET_ONLY", "BLOCKED", "RATE_LIMITED",
    "LOGIN_REQUIRED", "DELETED", "NOT_FOUND", "UNKNOWN",
}
manifest_ids = {row["source_id"] for row in manifest}
claim_source_ids = {
    source_id.strip()
    for row in claims_rows
    for source_id in str(row["source_ids"]).split("|")
    if source_id.strip()
}
claim_evidence_paths = {
    path.strip()
    for row in claims_rows
    for path in str(row["evidence_paths"]).split("|")
    if path.strip()
}
all_manifest_evidence_exists = all((project_root / row["evidence_path"]).is_file() for row in manifest)
all_query_evidence_exists = all((project_root / row["evidence_path"]).is_file() for row in query_rows)
all_claim_evidence_exists = all((project_root / path).is_file() for path in claim_evidence_paths)

checks = {
    "official_routes_exactly_7": len(official_doc["routes"]) == 7,
    "official_browser_routes_verifier_compatible": sum(
        row["source_id"].startswith("KAGGLE_OFFICIAL_BROWSER_")
        and row["source_type"] == "official_competition_page"
        and row["platform"] == "Kaggle"
        and row["read_status"] == "FULL_PAGE_BODY_READ"
        for row in manifest
    ) == 7,
    "data_inventory_exactly_5402_rows": len(data_rows) == 5402,
    "data_inventory_metadata_exactly_5400": sum(row["read_status"] == "METADATA_ONLY" for row in data_rows) == 5400,
    "inventory_unique_exactly_194": len(inventory_rows) == 194 and len({(r["owner"], r["notebook_slug"]) for r in inventory_rows}) == 194,
    "inventory_status_mapping_exact": sum(r["read_status"] == "FULL_NOTEBOOK_SOURCE_READ" for r in inventory_rows) == 30
    and sum(r["read_status"] == "METADATA_ONLY" for r in inventory_rows) == 164,
    "deep_source_exactly_30": len(deep_rows) == 30,
    "deep_code_cells_exactly_218": code_total == 218,
    "deep_outputs_zero": outputs_total == 0,
    "script_version_unknown_exactly_30": sum(r["script_version_id"] == "UNKNOWN" for r in deep_rows) == 30,
    "query_sort_count_5": len(sort_doc["sorts"]) == 5,
    "query_keyword_count_20": len(keyword_doc["captures"]) == 20,
    "query_log_exactly_123": len(query_rows) == 123,
    "query_required_categories_present": {"official", "kaggle_code"}.issubset({r["category"] for r in query_rows}),
    "query_evidence_paths_repo_resolvable": all_query_evidence_exists,
    "leaderboard_required_ranks_6": len(leader_rows) == 6,
    "manifest_exactly_211_unique": len(manifest) == 211 and len(manifest_ids) == 211,
    "manifest_full_schema_every_row": all(manifest_schema.issubset(row) for row in manifest),
    "manifest_statuses_allowlisted": all(row["read_status"] in allowed_manifest_statuses for row in manifest),
    "manifest_evidence_paths_repo_resolvable": all_manifest_evidence_exists,
    "claims_fragment_exactly_19": len(claims_rows) == 19,
    "claims_source_ids_resolve_to_manifest": claim_source_ids.issubset(manifest_ids),
    "claims_evidence_paths_repo_resolvable": all_claim_evidence_exists,
    "method_source_ids_resolve_to_inventory": {row["source_id"] for row in method_rows}.issubset({row["source_id"] for row in inventory_rows}),
    "kaggle_writes_zero": all(v == 0 for v in coverage["physical_actions"].values()),
    "required_files_exist": all((ROOT / name).is_file() for name in [
        "01_official_competition.md", "02_official_data_inventory.csv", "03_official_rules_and_metric.md",
        "04_leaderboard_snapshot.csv", "05_kaggle_code_inventory.csv", "06_kaggle_code_deep_read.md",
        "07_kaggle_method_comparison.csv", "coverage_summary.json", "source_manifest.jsonl", "search_query_log.csv",
        "claims_fragment.csv", "access_failures_fragment.md",
    ]),
}
receipt = {
    "generated_at_utc": now_pair()[0], "checks": checks, "all_checks_pass": all(checks.values()),
    "counts": {
        "official_browser_routes": len(official_doc["routes"]),
        "official_api_content_pages": len(official_api_rows),
        "competition_file_metadata_obtained": len(partial_file_rows),
        "competition_file_page_total_reported": 24886,
        "competition_file_metadata_missing_vs_page_total": 24886 - len(partial_file_rows),
        "competition_file_metadata_bytes_sum": sum(int(row["total_bytes"] or 0) for row in partial_file_rows),
        "data_inventory_rows": len(data_rows),
        "leaderboard_selected_ranks": len(leader_rows),
        "code_sort_queries": len(sort_doc["sorts"]),
        "code_keyword_queries": len(keyword_doc["captures"]),
        "code_visible_occurrences": len(occurrences),
        "code_unique_notebooks": len(inventory_rows),
        "code_full_source_reads": len(deep_rows),
        "code_unique_authors_full_source": unique_authors,
        "code_source_bytes": source_bytes_total,
        "code_markdown_cells": markdown_total,
        "code_code_cells": code_total,
        "code_output_bearing_cells": outputs_total,
        "manifest_records": len(manifest),
        "query_records": len(query_rows),
        "claim_fragment_records": len(claims_rows),
        "http_429_failures": sum("429" in row.get("error", "") for row in failures),
    },
    "file_sha256": {name: sha_file(ROOT / name) for name in [
        "01_official_competition.md", "02_official_data_inventory.csv", "03_official_rules_and_metric.md",
        "04_leaderboard_snapshot.csv", "05_kaggle_code_inventory.csv", "06_kaggle_code_deep_read.md",
        "07_kaggle_method_comparison.csv", "coverage_summary.json", "source_manifest.jsonl", "search_query_log.csv",
        "claims_fragment.csv", "access_failures_fragment.md",
    ]},
}
write_json(ROOT / "build_verification_receipt.json", receipt)
if not receipt["all_checks_pass"]:
    raise SystemExit("build checks failed: " + json.dumps(checks, ensure_ascii=False))
print(json.dumps({"status": "PASS", "inventory": len(inventory_rows), "deep": len(deep_rows), "manifest": len(manifest), "queries": len(query_rows), "files_partial": len(partial_file_rows)}, ensure_ascii=False))
