#!/usr/bin/env python3
"""低频、只读审计 Biohub 公开 Kaggle Notebook 当前源码。

安全属性：
- 仅调用 KernelsApiService.GetKernel；不包含 SaveKernel、submission、Dataset 或训练调用。
- 每次请求至少间隔 4 秒；任一 HTTP 429 后立即停止全部网络读取，不重试。
- 源码仅在内存中读取；落盘只保存 SHA、计数、逐 cell 哈希、短摘录和语义标签。
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / "evidence"
SORT_CAPTURE = EVIDENCE / "browser_code_sort_captures.json"
KEYWORD_CAPTURE = EVIDENCE / "browser_code_keyword_captures.json"
DEEP_JSONL = EVIDENCE / "notebook_deep_read.jsonl"
CELL_JSONL = EVIDENCE / "notebook_cell_audit.jsonl"
REQUEST_CSV = EVIDENCE / "notebook_source_request_log.csv"
SUMMARY_JSON = ROOT / "notebook_deep_read_summary.json"
REQUEST_INTERVAL_SECONDS = 4.0
SUCCESS_TARGET = 30


# 顺序按：官方/pinned、方法多样性、高票、评分补丁风险、近期高分、外部模型。
# 后备项仅在前项不可读且 API 未限流时使用；每个 ref 都必须来自本轮浏览器发现清单。
CANDIDATES: list[tuple[str, str]] = [
    ("nusrati/0-938", "recent_high_score_recovery_probe"),
    ("inversion/cell-tracking-getting-started-w-nearest-neighbor", "pinned_official_getting_started"),
    ("thibautgoldsborough/unet-baseline-inference-submission", "host_or_organizer_baseline_candidate"),
    ("jirkaborovec/biohub-celltrack-dog-trackastra-graph-trans", "trackastra_model_linked"),
    ("xiaoleilian/biohub-cell-tracking-classical-baseline", "classical_detection_baseline"),
    ("xiaoleilian/biohub-cell-tracking-3d-u-net", "3d_unet_inference"),
    ("xiaoleilian/biohub-ct-mix-divaug", "high_vote_division_augmentation"),
    ("pilkwang/biohub-cell-tracking-learned-graph-w-gap-recovery", "learned_graph_gap_recovery"),
    ("pilkwang/biohub-cell-tracking-two-seeds-logit-blend", "two_seed_logit_blend"),
    ("pilkwang/biohub-cell-tracking-data-model-eda-baseline", "data_model_eda_baseline"),
    ("yusuketogashi/clean-approach-lightweight-local-cv-no-hack", "local_cv_no_hack"),
    ("yusuketogashi/lb897-baseline", "high_vote_baseline"),
    ("yaroslavkholmirzayev/biohub-cell-tracking-v4-unet-ilp-reproduction", "unet_ilp_reproduction"),
    ("seshurajup/lb-0-857-best-rule-base-v14", "rule_based"),
    ("isakatsuyoshi/biohub-rule-based-baseline", "rule_based_baseline"),
    ("kirneo/metric-hack-last-call-update", "metric_exploit_patch_risk"),
    ("amanatar/improved-metric-hack-last-call", "metric_exploit_stale_score_risk"),
    ("outwrest/metric-hack-minimal-baseline-tta-2gpu", "metric_exploit_minimal"),
    ("yunusgmsoy/kimi-notebook-v19", "recent_high_score"),
    ("anhadmahajan06/biohub-track-your-cells-development", "recent_high_vote"),
    ("flexonafft/biohub-harmonic-fusion", "harmonic_fusion"),
    ("kunaldesale2408/biohub-cell-tracking", "recent_high_vote_general"),
    ("alioman/biohub-v19c-public0939-sis14-only", "recent_high_score_sister_parameter"),
    ("rishabhr0y/biohub-div45-stack", "division_stack"),
    ("cloudssdut/biohub-0-948-reproduction-20260901", "score_reproduction_candidate"),
    ("aagneye/biohub-v23-division-rebuild-reclaim", "recent_division_rebuild"),
    ("pawanmali/biohub-cli-learned-div-v1", "learned_division"),
    ("mdmahfujulkarim/biohub-cell-tracking-graph-pipeline", "graph_pipeline"),
    ("dfhgfdghfdhg/biohub-final-cyto2", "cellpose_candidate"),
    ("aaaa1597/s1-06-stardist-btrack-pipeline", "stardist_btrack_candidate"),
    # 后备：覆盖运动、Kalman、ILP、Trackastra/Ultrack 关键词和近期运行。
    ("prvsiyan/biohub-motion-gap-persistence-lineage", "motion_gap_persistence"),
    ("biohack44/biohub-starter-package-public-max-lb", "multi_package_starter_candidate"),
    ("yuki16/biohub-ctdd-log-detection-hungarian-tracker", "log_hungarian"),
    ("maulikgajera/biohub-cell-tracking-unet-node-transformer-ilp", "unet_transformer_ilp"),
    ("pavloivanin/biohubtrackingv3-velocity-kalman-prior-gap-closing", "kalman_gap_closing"),
    ("wanderwaal/biohub-submission-classical-improved", "classical_cellpose_stardist_candidate"),
    ("rockerritesh/0-926-biohub-divsub", "division_submission_candidate"),
    ("evgendvorkin/biohub-0-934-lb-proxy-score-0-9384", "lb_proxy_score_candidate"),
    ("tangai1/biohub-c35-fallback-detection-cleanroom-20260831", "fallback_detection_recent"),
    ("yunusgmsoy/kimi-notebook-v18", "recent_high_score_prior_version_slug"),
]


METHOD_PATTERNS: dict[str, list[str]] = {
    "detection_dog_log": [r"difference_of_gaussian", r"gaussian_laplace", r"\bDoG\b", r"\bLoG\b"],
    "detection_local_maxima": [r"peak_local_max", r"maximum_filter", r"local_max"],
    "detection_threshold": [r"threshold_otsu", r"percentile\s*\(", r"binary_threshold", r"threshold"],
    "segmentation_connected_components": [r"connected_components", r"connected component", r"ndimage\.label", r"measure\.label"],
    "segmentation_watershed": [r"watershed"],
    "model_3d_unet": [r"UNet3D", r"3D.?U.?Net", r"Conv3d", r"monai.*UNet"],
    "model_cellpose": [r"cellpose", r"CellposeModel"],
    "model_stardist": [r"stardist", r"StarDist"],
    "model_trackastra": [r"trackastra", r"Trackastra"],
    "model_ultrack": [r"ultrack", r"Ultrack"],
    "linking_nearest_neighbor": [r"nearest.?neighbor", r"NearestNeighbors", r"cKDTree", r"KDTree", r"query_ball_point"],
    "linking_hungarian": [r"linear_sum_assignment", r"Hungarian", r"bipartite"],
    "linking_graph": [r"networkx", r"nx\.", r"graph", r"edge_index"],
    "optimization_ilp_motile": [r"\bILP\b", r"milp", r"motile", r"gurobi", r"pulp\.", r"ortools"],
    "motion_kalman": [r"Kalman", r"velocity", r"optical.?flow"],
    "gap_closing": [r"gap.?clos", r"gap.?recover", r"gap.?fill", r"max_gap"],
    "division_detection": [r"division", r"mitosis", r"daughter", r"sister", r"out_degree"],
    "track_filtering": [r"min_track", r"track_length", r"filter.*track", r"prun", r"remove.*short"],
    "node_count_calibration": [r"estimated_number_of_nodes", r"node.?count", r"target.?count", r"count.?calibr", r"quota"],
    "metric_edge_jaccard": [r"adjusted_edge_jaccard", r"edge.?jaccard"],
    "metric_division_jaccard": [r"division_jaccard", r"division.?jaccard"],
    "submission_generation": [r"submission\.csv", r"sample_submission", r"row_type", r"source_id", r"target_id"],
}


def now_pair() -> tuple[str, str]:
    value = datetime.now(timezone.utc)
    return value.isoformat(), value.astimezone(ZoneInfo("Asia/Singapore")).isoformat()


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "".join(str(x) for x in value)
    return str(value)


def short_excerpt(value: str, limit: int = 260) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    return value[:limit]


def object_dict(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): object_dict(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [object_dict(v) for v in value]
    if hasattr(value, "to_dict"):
        return object_dict(value.to_dict())
    if hasattr(value, "__dict__"):
        return {k: object_dict(v) for k, v in vars(value).items() if not k.startswith("_")}
    return str(value)


def iter_key_values(value: Any, prefix: str = "") -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            yield path, child
            yield from iter_key_values(child, path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_key_values(child, f"{prefix}[{index}]")


def first_key(raw: Any, names: set[str]) -> Any:
    normalized = {re.sub(r"[^a-z0-9]", "", x.casefold()) for x in names}
    for path, value in iter_key_values(raw):
        leaf = re.sub(r"[^a-z0-9]", "", path.rsplit(".", 1)[-1].split("[", 1)[0].casefold())
        if leaf in normalized and isinstance(value, (str, int, float, bool)):
            return value
    return ""


def discovered_cards() -> tuple[dict[str, dict[str, Any]], set[str], dict[str, set[str]]]:
    cards: dict[str, dict[str, Any]] = {}
    refs: set[str] = set()
    contexts: defaultdict[str, set[str]] = defaultdict(set)
    for path, array_key in [(SORT_CAPTURE, "sorts"), (KEYWORD_CAPTURE, "captures")]:
        data = json.loads(path.read_text(encoding="utf-8"))
        for capture in data[array_key]:
            label = capture.get("query") or capture.get("sort") or ""
            for row in capture.get("rows", []):
                ref = row.get("ref", "")
                if not ref:
                    continue
                refs.add(ref)
                contexts[ref].add(str(label))
                prior = cards.get(ref, {})
                # 优先保留字段更完整的卡片；分数/票数是动态页面展示值。
                cards[ref] = {**prior, **{k: v for k, v in row.items() if v not in (None, "")}}
    return cards, refs, contexts


def method_hits(text: str) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for category, patterns in METHOD_PATTERNS.items():
        snippets: list[str] = []
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                start = max(0, match.start() - 80)
                end = min(len(text), match.end() + 140)
                excerpt = short_excerpt(text[start:end], 240)
                if excerpt and excerpt not in snippets:
                    snippets.append(excerpt)
                if len(snippets) >= 3:
                    break
            if len(snippets) >= 3:
                break
        if snippets:
            found[category] = snippets
    return found


def output_to_text(outputs: list[Any]) -> str:
    chunks: list[str] = []
    for output in outputs:
        if not isinstance(output, dict):
            chunks.append(str(output))
            continue
        for key in ("text", "ename", "evalue", "traceback"):
            if key in output:
                chunks.append(safe_text(output.get(key)))
        data = output.get("data")
        if isinstance(data, dict):
            for mime, value in data.items():
                if mime.startswith("text/") or mime in {"application/json"}:
                    chunks.append(safe_text(value))
                else:
                    chunks.append(f"<{mime} payload omitted>")
    return "\n".join(chunks)


def analyze_source(ref: str, source: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    raw = source.encode("utf-8")
    source_sha = sha_bytes(raw)
    cells: list[dict[str, Any]] = []
    notebook_format = "SCRIPT"
    parse_error = ""
    try:
        parsed = json.loads(source)
        if isinstance(parsed, dict) and isinstance(parsed.get("cells"), list):
            raw_cells = parsed["cells"]
            notebook_format = "IPYNB"
        else:
            raw_cells = [{"cell_type": "code", "source": source, "outputs": []}]
            notebook_format = "JSON_NON_IPYNB_AS_SCRIPT"
    except Exception as exc:
        raw_cells = [{"cell_type": "code", "source": source, "outputs": []}]
        parse_error = f"{type(exc).__name__}: {exc}"

    code_texts: list[str] = []
    markdown_texts: list[str] = []
    output_texts: list[str] = []
    output_count = 0
    output_cells = 0
    for index, cell in enumerate(raw_cells):
        cell_type = str(cell.get("cell_type", "unknown")) if isinstance(cell, dict) else "unknown"
        cell_source = safe_text(cell.get("source", "")) if isinstance(cell, dict) else safe_text(cell)
        outputs = cell.get("outputs", []) if isinstance(cell, dict) and isinstance(cell.get("outputs", []), list) else []
        out_text = output_to_text(outputs)
        output_count += len(outputs)
        if outputs:
            output_cells += 1
        if cell_type == "code":
            code_texts.append(cell_source)
        elif cell_type == "markdown":
            markdown_texts.append(cell_source)
        output_texts.append(out_text)
        cell_payload = cell_source.encode("utf-8")
        output_payload = json.dumps(outputs, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
        cells.append(
            {
                "notebook_ref": ref,
                "source_sha256": source_sha,
                "cell_index": index,
                "cell_type": cell_type,
                "cell_bytes": len(cell_payload),
                "cell_sha256": sha_bytes(cell_payload),
                "execution_count": cell.get("execution_count", "") if isinstance(cell, dict) else "",
                "output_item_count": len(outputs),
                "output_bytes": len(output_payload),
                "output_sha256": sha_bytes(output_payload),
                "source_excerpt": short_excerpt(cell_source),
                "output_excerpt": short_excerpt(out_text),
                "semantic_categories": sorted(method_hits(cell_source).keys()),
            }
        )

    code_all = "\n\n".join(code_texts)
    markdown_all = "\n\n".join(markdown_texts)
    outputs_all = "\n\n".join(output_texts)
    complete_text = "\n\n".join([markdown_all, code_all, outputs_all])
    hits = method_hits(complete_text)

    training_code = bool(re.search(r"\.backward\s*\(|optimizer\.step\s*\(|model\.fit\s*\(|for\s+epoch\s+in|trainer\.fit", code_all, re.I))
    training_output = bool(re.search(r"(?:epoch\s*\d+|train(?:ing)?\s+loss|val(?:idation)?\s+loss|loss\s*[:=]\s*\d)", outputs_all, re.I))
    if training_code and training_output:
        training_status = "TRAINING_CODE_AND_OUTPUT_EVIDENCE_PRESENT_AUTHOR_NOTEBOOK"
    elif training_code:
        training_status = "TRAINING_CODE_PRESENT_NO_OUTPUT_PROOF"
    else:
        training_status = "NO_TRAINING_CODE_FOUND_EXECUTION_NOT_VERIFIED"

    input_slugs = sorted(set(re.findall(r"/kaggle/input/([A-Za-z0-9._-]+)", complete_text)))
    output_paths = sorted(set(re.findall(r"/kaggle/working/[A-Za-z0-9_./-]+|[A-Za-z0-9_.-]*submission[A-Za-z0-9_.-]*\.csv", complete_text, re.I)))
    weight_paths = sorted(set(re.findall(r"(?:/kaggle/input/[A-Za-z0-9_./-]+|[A-Za-z0-9_./-]+)\.(?:pt|pth|ckpt|onnx|h5|keras)", complete_text, re.I)))
    imported = sorted(set(re.findall(r"(?m)^\s*(?:from\s+([A-Za-z0-9_.]+)\s+import|import\s+([A-Za-z0-9_.]+))", code_all)))
    imports = sorted(set((a or b).split(".", 1)[0] for a, b in imported if a or b))
    local_scores = sorted(set(re.findall(r"(?i)(?:local|cv|validation)[^\n]{0,40}(?:score|jaccard)[^\n]{0,20}([01](?:\.\d+)?)", complete_text)))
    runtime_hints = [short_excerpt(x, 180) for x in re.findall(r"(?im)^.*(?:elapsed|runtime|minutes?|hours?|sec(?:ond)?s?).*$", outputs_all)[:8]]

    analysis = {
        "notebook_format": notebook_format,
        "parse_error": parse_error,
        "source_bytes": len(raw),
        "source_sha256": source_sha,
        "cell_count": len(raw_cells),
        "markdown_cell_count": sum(c.get("cell_type") == "markdown" for c in cells),
        "code_cell_count": sum(c.get("cell_type") == "code" for c in cells),
        "output_bearing_code_cell_count": sum(c.get("cell_type") == "code" and c.get("output_item_count", 0) > 0 for c in cells),
        "output_item_count": output_count,
        "output_bearing_any_cell_count": output_cells,
        "all_code_cells_hashed_and_scanned": sum(c.get("cell_type") == "code" for c in cells) == len(code_texts),
        "method_categories": sorted(hits.keys()),
        "method_evidence": hits,
        "training_status": training_status,
        "training_code_present": training_code,
        "training_output_evidence_present": training_output,
        "input_dataset_slugs_from_source": input_slugs,
        "output_paths_from_source": output_paths,
        "weight_paths_from_source": weight_paths,
        "imports": imports,
        "reported_local_score_strings_unverified": local_scores,
        "runtime_output_hints_author_not_benchmarked": runtime_hints,
        "source_saved": False,
    }
    return analysis, cells


def dump_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, default=str) + "\n")


def dump_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "notebook_ref", "selection_reason", "attempt_index", "access_started_utc",
        "access_started_singapore", "access_ended_utc", "access_ended_singapore",
        "status", "response_source_bytes", "response_source_sha256", "error",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def persist(records: list[dict[str, Any]], cells: list[dict[str, Any]], requests: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    dump_jsonl(DEEP_JSONL, records)
    dump_jsonl(CELL_JSONL, cells)
    dump_csv(REQUEST_CSV, requests)
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def metadata_projection(metadata: Any, blob: Any, response: Any) -> dict[str, Any]:
    meta = object_dict(metadata)
    blob_raw = object_dict(blob)
    response_raw = object_dict(response)
    if isinstance(blob_raw, dict):
        blob_raw.pop("source", None)
    # response_raw 可能嵌套 blob.source，显式删除避免第三方源码落盘。
    if isinstance(response_raw, dict) and isinstance(response_raw.get("blob"), dict):
        response_raw["blob"].pop("source", None)
    script_version_id = first_key(meta, {"scriptVersionId", "script_version_id"}) or first_key(response_raw, {"scriptVersionId", "script_version_id"})
    return {
        "kernel_metadata_id": getattr(metadata, "id", None),
        "script_version_id": script_version_id or "",
        "script_version_id_status": "VERIFIED_RESPONSE_FIELD" if script_version_id else "UNKNOWN_NOT_EXPOSED_BY_CURRENT_GETKERNEL_RESPONSE",
        "current_version": int(getattr(metadata, "current_version_number", 0) or first_key(meta, {"currentVersionNumber"}) or 0),
        "title": getattr(metadata, "title", "") or first_key(meta, {"title"}),
        "created_at": first_key(meta, {"creationDate", "createdAt", "dateCreated"}),
        "updated_at": first_key(meta, {"lastRunTime", "updatedAt", "dateUpdated"}),
        "accelerator": first_key(meta, {"accelerator", "machineShape", "gpuType"}),
        "gpu_enabled": first_key(meta, {"gpuEnabled", "enableGpu", "isGpuEnabled"}),
        "internet_setting": first_key(meta, {"internetEnabled", "enableInternet", "isInternetEnabled"}),
        "license": first_key(meta, {"license", "licenseName"}),
        "kernel_type": getattr(blob, "kernel_type", None) or first_key(blob_raw, {"kernelType"}),
        "language": getattr(blob, "language", None) or first_key(blob_raw, {"language"}),
        "metadata_keys": sorted(meta.keys()) if isinstance(meta, dict) else [],
        "blob_metadata_without_source": blob_raw,
    }


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    cards, discovered, contexts = discovered_cards()
    candidate_rows = [(ref, reason) for ref, reason in CANDIDATES if ref in discovered]
    missing_candidates = [ref for ref, _ in CANDIDATES if ref not in discovered]
    if len(candidate_rows) < SUCCESS_TARGET:
        raise RuntimeError(f"浏览器发现清单中的候选不足：{len(candidate_rows)} < {SUCCESS_TARGET}")

    records: list[dict[str, Any]] = []
    cell_rows: list[dict[str, Any]] = []
    request_rows: list[dict[str, Any]] = []
    summary: dict[str, Any] = {
        "schema_version": "1.0",
        "safety_mode": "READ_ONLY_GETKERNEL_ONLY_STOP_ON_FIRST_429_NO_RETRY",
        "request_interval_seconds": REQUEST_INTERVAL_SECONDS,
        "success_target": SUCCESS_TARGET,
        "browser_discovered_unique_refs": len(discovered),
        "candidate_count_in_discovered_set": len(candidate_rows),
        "candidate_refs_not_in_discovered_set": missing_candidates,
        "started_at_utc": now_pair()[0],
        "started_at_singapore": now_pair()[1],
        "attempted": 0,
        "full_source_read": 0,
        "blocked": 0,
        "rate_limited": False,
        "remaining_not_attempted_after_stop": [],
        "kaggle_write_calls": 0,
    }
    persist(records, cell_rows, request_rows, summary)

    # 导入 kaggle 会进行当前只读凭证认证；无凭证内容写入输出。
    from kaggle.api.kaggle_api_extended import KaggleApi
    from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest

    api = KaggleApi()
    with api.build_kaggle_client() as client:
        for attempt_index, (ref, reason) in enumerate(candidate_rows, start=1):
            if summary["full_source_read"] >= SUCCESS_TARGET:
                break
            started_utc, started_sg = now_pair()
            request_row = {
                "notebook_ref": ref,
                "selection_reason": reason,
                "attempt_index": attempt_index,
                "access_started_utc": started_utc,
                "access_started_singapore": started_sg,
                "status": "REQUESTED",
                "response_source_bytes": "",
                "response_source_sha256": "",
                "error": "",
            }
            try:
                owner, slug = ref.split("/", 1)
                request = ApiGetKernelRequest()
                request.user_name = owner
                request.kernel_slug = slug
                response = client.kernels.kernels_api_client.get_kernel(request)
                metadata = response.metadata
                blob = response.blob
                source = safe_text(getattr(blob, "source", ""))
                if not source:
                    raise RuntimeError("GetKernel response blob.source is empty")
                analysis, current_cells = analyze_source(ref, source)
                projection = metadata_projection(metadata, blob, response)
                card = cards.get(ref, {})
                score = card.get("score", "")
                stale_risk = "HIGH" if re.search(r"metric.?hack|exploit", f"{ref} {card.get('title','')}", re.I) or (score and float(score) > 0.963) else "UNKNOWN_DYNAMIC_UNBOUND"
                record = {
                    "source_id": f"KAGGLE_CODE_{ref.replace('/', '_').upper()}",
                    "notebook_ref": ref,
                    "owner": owner,
                    "notebook_slug": slug,
                    "url": f"https://www.kaggle.com/code/{ref}",
                    "selection_reason": reason,
                    "discovery_contexts": sorted(contexts.get(ref, set())),
                    "read_status": "FULL_SOURCE_READ_ALL_CODE_CELLS_HASHED_AND_SEMANTICALLY_SCANNED",
                    "access_time_utc": started_utc,
                    "access_time_singapore": started_sg,
                    "page_displayed_score": score,
                    "score_source": "KAGGLE_CODE_LIST_CARD_DYNAMIC",
                    "current_score_verified": False,
                    "score_bound_to_current_source_version": False,
                    "stale_score_risk": stale_risk,
                    "votes_dynamic": card.get("votes", ""),
                    "comments_dynamic": card.get("comments", ""),
                    "updated_card_text": card.get("updated", ""),
                    "source_license_status": "METADATA_OR_SOURCE_REVIEW_REQUIRED_NO_SOURCE_REDISTRIBUTION",
                    **projection,
                    **analysis,
                }
                records.append(record)
                cell_rows.extend(current_cells)
                request_row.update(
                    {
                        "status": "FULL_SOURCE_READ",
                        "response_source_bytes": analysis["source_bytes"],
                        "response_source_sha256": analysis["source_sha256"],
                    }
                )
                summary["full_source_read"] += 1
                print(f"FULL {summary['full_source_read']:02d}/{SUCCESS_TARGET} {ref} bytes={analysis['source_bytes']} cells={analysis['cell_count']}", flush=True)
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                status = "RATE_LIMITED" if re.search(r"(?:HTTP\s*)?429|Too Many Requests", error, re.I) else "BLOCKED_ACCESS_OR_SOURCE"
                request_row.update({"status": status, "error": error[:1200]})
                records.append(
                    {
                        "source_id": f"KAGGLE_CODE_{ref.replace('/', '_').upper()}",
                        "notebook_ref": ref,
                        "owner": ref.split("/", 1)[0],
                        "notebook_slug": ref.split("/", 1)[1],
                        "url": f"https://www.kaggle.com/code/{ref}",
                        "selection_reason": reason,
                        "discovery_contexts": sorted(contexts.get(ref, set())),
                        "read_status": status,
                        "access_time_utc": started_utc,
                        "access_time_singapore": started_sg,
                        "error": error[:1200],
                        "page_displayed_score": cards.get(ref, {}).get("score", ""),
                        "score_source": "KAGGLE_CODE_LIST_CARD_DYNAMIC",
                        "current_score_verified": False,
                        "score_bound_to_current_source_version": False,
                        "source_saved": False,
                    }
                )
                summary["blocked"] += 1
                print(f"{status} {ref}: {error[:240]}", flush=True)
                if status == "RATE_LIMITED":
                    summary["rate_limited"] = True
                    summary["rate_limit_stop_ref"] = ref
            ended_utc, ended_sg = now_pair()
            request_row["access_ended_utc"] = ended_utc
            request_row["access_ended_singapore"] = ended_sg
            request_rows.append(request_row)
            summary["attempted"] = len(request_rows)
            summary["ended_at_utc"] = ended_utc
            summary["ended_at_singapore"] = ended_sg
            persist(records, cell_rows, request_rows, summary)
            if summary["rate_limited"]:
                summary["remaining_not_attempted_after_stop"] = [r for r, _ in candidate_rows[attempt_index:]]
                persist(records, cell_rows, request_rows, summary)
                break
            if summary["full_source_read"] < SUCCESS_TARGET:
                time.sleep(REQUEST_INTERVAL_SECONDS)

    summary["selection_author_counts_full"] = dict(Counter(row["owner"] for row in records if row.get("read_status", "").startswith("FULL_SOURCE_READ")))
    summary["cell_audit_rows"] = len(cell_rows)
    summary["code_cell_audit_rows"] = sum(row.get("cell_type") == "code" for row in cell_rows)
    summary["success_target_met"] = summary["full_source_read"] >= SUCCESS_TARGET
    summary["final_status"] = "TARGET_MET" if summary["success_target_met"] else ("RATE_LIMITED_PARTIAL" if summary["rate_limited"] else "PARTIAL_BLOCKED")
    persist(records, cell_rows, request_rows, summary)
    print(json.dumps({k: summary[k] for k in ["final_status", "attempted", "full_source_read", "blocked", "rate_limited", "cell_audit_rows", "code_cell_audit_rows"]}, ensure_ascii=False), flush=True)
    return 0 if summary["success_target_met"] else 2


if __name__ == "__main__":
    sys.exit(main())
