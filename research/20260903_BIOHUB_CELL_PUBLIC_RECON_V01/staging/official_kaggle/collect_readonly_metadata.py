#!/usr/bin/env python3
"""只读采集 Biohub CELL 官方 Kaggle 元数据；不调用任何写 API。"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from kaggle.api.kaggle_api_extended import KaggleApi
from kagglesdk.competitions.types.competition_api_service import ApiGetLeaderboardRequest


SLUG = "biohub-cell-tracking-during-development"
ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / "evidence"
EVIDENCE.mkdir(parents=True, exist_ok=True)

KERNEL_SORTS = ["scoreDescending", "voteCount", "hotness", "dateRun", "dateCreated"]
KERNEL_KEYWORDS = [
    "biohub cell tracking",
    "biohub-cell-tracking-during-development",
    "zebrafish cell tracking",
    "3D cell tracking",
    "3D+time microscopy",
    "cell lineage reconstruction",
    "cell division tracking",
    "GEFF",
    "tracksdata",
    "OME-Zarr",
    "adjusted edge jaccard",
    "division jaccard",
    "temporal affinity fields",
    "Ultrack",
    "Trackastra",
    "Cellpose",
    "StarDist",
    "3D U-Net tracking",
    "graph optimization cell tracking",
    "transformer cell tracking",
]
TOPIC_SORTS = ["hot", "top", "new", "recent", "active", "relevance"]


def now_pair() -> tuple[str, str]:
    value = datetime.now(timezone.utc)
    return value.isoformat(), value.astimezone(ZoneInfo("Asia/Singapore")).isoformat()


def sha_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", value).strip()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, default=str) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def object_dict(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return {name: value for name, value in vars(obj).items() if not name.startswith("_")}


api = KaggleApi()
queries: list[dict[str, Any]] = []
failures: list[dict[str, Any]] = []
manifest: list[dict[str, Any]] = []


def log_query(
    source_type: str,
    endpoint: str,
    query: str,
    sort_order: str,
    page: str,
    returned: int | None,
    total_reported: int | None,
    status: str,
    started_utc: str,
    started_sg: str,
    payload: Any = None,
    error: str = "",
) -> None:
    ended_utc, ended_sg = now_pair()
    raw = json_bytes(payload) if payload is not None else b""
    queries.append(
        {
            "source_type": source_type,
            "platform": "Kaggle official API",
            "endpoint": endpoint,
            "query": query,
            "sort_order": sort_order,
            "result_page": page,
            "returned_count": returned if returned is not None else "",
            "total_reported": total_reported if total_reported is not None else "",
            "access_started_utc": started_utc,
            "access_started_singapore": started_sg,
            "access_ended_utc": ended_utc,
            "access_ended_singapore": ended_sg,
            "status": status,
            "response_bytes": len(raw),
            "response_sha256": sha_bytes(raw) if raw else "",
            "error": error,
        }
    )


def capture_failure(source_type: str, endpoint: str, query: str, sort_order: str, page: str, exc: Exception, started: tuple[str, str]) -> None:
    error = f"{type(exc).__name__}: {exc}"
    failures.append(
        {
            "source_type": source_type,
            "endpoint": endpoint,
            "query": query,
            "sort_order": sort_order,
            "page": page,
            "error": error,
            "access_time_utc": started[0],
            "access_time_singapore": started[1],
        }
    )
    log_query(source_type, endpoint, query, sort_order, page, None, None, "BLOCKED", started[0], started[1], error=error)


# 1. Official content pages (full content is held in memory only; evidence stores hashes and short excerpts).
page_rows: list[dict[str, Any]] = []
started = now_pair()
try:
    pages = api.competition_list_pages(SLUG)
    payload = []
    for page in pages or []:
        content = page.content or ""
        raw = content.encode("utf-8")
        headings = re.findall(r"(?m)^#{1,6}\s*(.+)$|<h[1-6][^>]*>(.*?)</h[1-6]>", content)
        flat_headings = [clean_text(a or b) for a, b in headings if clean_text(a or b)]
        row = {
            "page_name": page.name,
            "url": f"https://www.kaggle.com/competitions/{SLUG}",
            "access_time_utc": started[0],
            "access_time_singapore": started[1],
            "read_status": "FULL_PAGE_BODY_READ" if content else "BLOCKED",
            "characters": len(content),
            "bytes_observed": len(raw),
            "sha256": sha_bytes(raw) if raw else "",
            "headings": " | ".join(flat_headings),
            "short_excerpt": clean_text(content)[:480],
        }
        page_rows.append(row)
        payload.append({"name": page.name, "bytes": len(raw), "sha256": row["sha256"]})
        manifest.append(
            {
                "source_id": f"KAGGLE_OFFICIAL_PAGE_{page.name.upper().replace(' ', '_').replace('-', '_')}",
                "source_type": "official_competition_page",
                "platform": "Kaggle",
                "title": page.name,
                "author": "Kaggle / Biohub SF",
                "url": f"https://www.kaggle.com/competitions/{SLUG}",
                "query": "competition pages",
                "sort_order": "",
                "result_page": "",
                "access_time_utc": started[0],
                "access_time_singapore": started[1],
                "read_status": row["read_status"],
                "bytes_observed": len(raw),
                "sha256": row["sha256"],
                "version_id": "",
                "commit_sha": "",
                "license": "page-specific; competition data license is CC0",
                "evidence_path": "evidence/official_pages_metadata.csv",
                "factual_use_allowed": True,
                "notes": "正文经 API 完整加载；仅保存哈希、标题和短摘录，不再分发完整页面。",
            }
        )
    log_query("official_competition_page", "competitions/pages", SLUG, "", "all", len(page_rows), len(page_rows), "OK", started[0], started[1], payload)
except Exception as exc:
    capture_failure("official_competition_page", "competitions/pages", SLUG, "", "all", exc, started)

write_csv(
    EVIDENCE / "official_pages_metadata.csv",
    page_rows,
    ["page_name", "url", "access_time_utc", "access_time_singapore", "read_status", "characters", "bytes_observed", "sha256", "headings", "short_excerpt"],
)


# 2. Complete competition file metadata listing. No file bytes are downloaded.
file_rows: list[dict[str, Any]] = []
file_token: str | None = None
file_page = 0
while True:
    file_page += 1
    started = now_pair()
    try:
        response = api.competition_list_files(SLUG, page_token=file_token, page_size=1000)
        current = []
        for item in response.files or []:
            row = {
                "name": item.name,
                "total_bytes": item.total_bytes,
                "creation_date": item.creation_date,
                "result_page": file_page,
            }
            current.append(row)
            file_rows.append(row)
        log_query("competition_file_metadata", "competitions/files", SLUG, "name", str(file_page), len(current), None, "OK", started[0], started[1], current)
        next_token = response.next_page_token or ""
        if not next_token or not current:
            break
        file_token = next_token
        if file_page >= 200:
            failures.append({"source_type": "competition_file_metadata", "endpoint": "competitions/files", "query": SLUG, "sort_order": "name", "page": file_page, "error": "STOP_CAP_200_PAGES", "access_time_utc": started[0], "access_time_singapore": started[1]})
            break
    except Exception as exc:
        capture_failure("competition_file_metadata", "competitions/files", SLUG, "name", str(file_page), exc, started)
        break

write_csv(EVIDENCE / "competition_files_metadata.csv", file_rows, ["name", "total_bytes", "creation_date", "result_page"])


# 3. Complete public leaderboard pagination.
leaderboard_rows: list[dict[str, Any]] = []
leader_token: str | None = None
leader_page = 0
try:
    with api.build_kaggle_client() as client:
        while True:
            leader_page += 1
            started = now_pair()
            request = ApiGetLeaderboardRequest()
            request.competition_name = SLUG
            request.page_size = 1000
            if leader_token:
                request.page_token = leader_token
            response = client.competitions.competition_api_client.get_leaderboard(request)
            current = []
            for item in response.submissions or []:
                row = {
                    "rank": len(leaderboard_rows) + 1,
                    "team_id": item.team_id,
                    "team_name": item.team_name,
                    "submission_date": item.submission_date,
                    "score": item.score,
                    "snapshot_utc": started[0],
                    "snapshot_singapore": started[1],
                    "result_page": leader_page,
                }
                current.append(row)
                leaderboard_rows.append(row)
            log_query("leaderboard", "competitions/leaderboard", SLUG, "public_score_desc", str(leader_page), len(current), None, "OK", started[0], started[1], current)
            leader_token = response.next_page_token or ""
            if not leader_token or not current:
                break
            if leader_page >= 20:
                failures.append({"source_type": "leaderboard", "endpoint": "competitions/leaderboard", "query": SLUG, "sort_order": "public_score_desc", "page": leader_page, "error": "STOP_CAP_20_PAGES", "access_time_utc": started[0], "access_time_singapore": started[1]})
                break
except Exception as exc:
    capture_failure("leaderboard", "competitions/leaderboard", SLUG, "public_score_desc", str(leader_page or 1), exc, started)

write_csv(EVIDENCE / "leaderboard_full_snapshot.csv", leaderboard_rows, ["rank", "team_id", "team_name", "submission_date", "score", "snapshot_utc", "snapshot_singapore", "result_page"])


# 4. Kaggle Code discovery: competition-linked multi-sort pages plus all required keyword queries.
kernel_occurrences: list[dict[str, Any]] = []
kernel_union: dict[str, dict[str, Any]] = {}
kernel_seen_context: defaultdict[str, list[str]] = defaultdict(list)


def ingest_kernels(items: list[Any], query: str, sort_order: str, page: int, discovery_type: str) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for rank, item in enumerate(items, 1):
        record = {
            "ref": item.ref,
            "title": item.title,
            "author": item.author,
            "last_run_time": item.last_run_time,
            "total_votes": item.total_votes,
            "query": query,
            "sort_order": sort_order,
            "result_page": page,
            "result_rank": rank,
            "discovery_type": discovery_type,
        }
        payload.append(record)
        kernel_occurrences.append(record)
        kernel_seen_context[item.ref].append(f"{discovery_type}:{query}:{sort_order}:p{page}:r{rank}")
        existing = kernel_union.setdefault(
            item.ref,
            {
                "ref": item.ref,
                "title": item.title,
                "author": item.author,
                "last_run_time": item.last_run_time,
                "total_votes": item.total_votes,
                "url": f"https://www.kaggle.com/code/{item.ref}",
                "read_status": "METADATA_ONLY",
            },
        )
        if int(item.total_votes or 0) > int(existing.get("total_votes") or 0):
            existing["total_votes"] = item.total_votes
    return payload


for sort_order in KERNEL_SORTS:
    for page in range(1, 6):
        started = now_pair()
        try:
            items = api.kernels_list(page=page, page_size=100, competition=SLUG, sort_by=sort_order) or []
            payload = ingest_kernels(items, SLUG, sort_order, page, "competition_linked")
            log_query("kaggle_code", "kernels/list", SLUG, sort_order, str(page), len(items), None, "OK", started[0], started[1], payload)
            if len(items) < 100:
                break
        except Exception as exc:
            capture_failure("kaggle_code", "kernels/list", SLUG, sort_order, str(page), exc, started)
            break

for keyword in KERNEL_KEYWORDS:
    started = now_pair()
    try:
        items = api.kernels_list(page=1, page_size=100, search=keyword, sort_by="relevance") or []
        payload = ingest_kernels(items, keyword, "relevance", 1, "keyword_search")
        log_query("kaggle_code", "kernels/list", keyword, "relevance", "1", len(items), None, "OK", started[0], started[1], payload)
    except Exception as exc:
        capture_failure("kaggle_code", "kernels/list", keyword, "relevance", "1", exc, started)

kernel_union_rows = []
for ref, row in kernel_union.items():
    out = dict(row)
    out["discovery_occurrence_count"] = len(kernel_seen_context[ref])
    out["discovery_contexts"] = " | ".join(kernel_seen_context[ref])
    kernel_union_rows.append(out)
kernel_union_rows.sort(key=lambda row: (-int(row.get("total_votes") or 0), str(row.get("ref"))))

write_csv(EVIDENCE / "kaggle_code_discovery_occurrences.csv", kernel_occurrences, ["ref", "title", "author", "last_run_time", "total_votes", "query", "sort_order", "result_page", "result_rank", "discovery_type"])
write_csv(EVIDENCE / "kaggle_code_discovered.csv", kernel_union_rows, ["ref", "title", "author", "last_run_time", "total_votes", "url", "read_status", "discovery_occurrence_count", "discovery_contexts"])


# 5. Discussion discovery across every supported competition-topic sort and every page.
topic_occurrences: list[dict[str, Any]] = []
topic_union: dict[int, dict[str, Any]] = {}
topic_seen_context: defaultdict[int, list[str]] = defaultdict(list)
for sort_order in TOPIC_SORTS:
    total = None
    page = 1
    while True:
        started = now_pair()
        try:
            response = api.competition_list_topics(SLUG, sort_by=sort_order, page=page)
            items = response.topics or []
            total = int(response.total_count or 0)
            payload = []
            for rank, item in enumerate(items, 1):
                record = {
                    "discussion_id": item.id,
                    "title": item.title,
                    "author": item.author_name,
                    "created_at": item.post_date,
                    "votes": item.votes,
                    "comment_count": item.comment_count,
                    "url": f"https://www.kaggle.com/competitions/{SLUG}/discussion/{item.id}",
                    "sort_order": sort_order,
                    "result_page": page,
                    "result_rank": rank,
                }
                payload.append(record)
                topic_occurrences.append(record)
                topic_seen_context[item.id].append(f"{sort_order}:p{page}:r{rank}")
                topic_union.setdefault(item.id, {**record, "read_status": "METADATA_ONLY"})
            log_query("kaggle_discussion", "competitions/topics", SLUG, sort_order, str(page), len(items), total, "OK", started[0], started[1], payload)
            if not items or page >= math.ceil(total / max(1, len(items))):
                break
            page += 1
            if page > 100:
                failures.append({"source_type": "kaggle_discussion", "endpoint": "competitions/topics", "query": SLUG, "sort_order": sort_order, "page": page, "error": "STOP_CAP_100_PAGES", "access_time_utc": started[0], "access_time_singapore": started[1]})
                break
        except Exception as exc:
            capture_failure("kaggle_discussion", "competitions/topics", SLUG, sort_order, str(page), exc, started)
            break

topic_union_rows = []
for topic_id, row in topic_union.items():
    out = dict(row)
    out["discovery_occurrence_count"] = len(topic_seen_context[topic_id])
    out["discovery_contexts"] = " | ".join(topic_seen_context[topic_id])
    topic_union_rows.append(out)
topic_union_rows.sort(key=lambda row: (-int(row.get("votes") or 0), -int(row.get("comment_count") or 0), int(row["discussion_id"])))

write_csv(EVIDENCE / "kaggle_discussion_discovery_occurrences.csv", topic_occurrences, ["discussion_id", "title", "author", "created_at", "votes", "comment_count", "url", "sort_order", "result_page", "result_rank"])
write_csv(EVIDENCE / "kaggle_discussion_discovered.csv", topic_union_rows, ["discussion_id", "title", "author", "created_at", "votes", "comment_count", "url", "read_status", "discovery_occurrence_count", "discovery_contexts"])


write_csv(
    ROOT / "search_query_log.csv",
    queries,
    ["source_type", "platform", "endpoint", "query", "sort_order", "result_page", "returned_count", "total_reported", "access_started_utc", "access_started_singapore", "access_ended_utc", "access_ended_singapore", "status", "response_bytes", "response_sha256", "error"],
)
write_jsonl(ROOT / "source_manifest.jsonl", manifest)
write_json(ROOT / "metadata_collection_summary.json", {
    "competition_slug": SLUG,
    "official_content_pages": len(page_rows),
    "competition_file_records": len(file_rows),
    "competition_file_pages": file_page,
    "competition_total_bytes": sum(int(row.get("total_bytes") or 0) for row in file_rows),
    "leaderboard_rows": len(leaderboard_rows),
    "leaderboard_pages": leader_page,
    "kaggle_code_occurrences": len(kernel_occurrences),
    "kaggle_code_unique": len(kernel_union_rows),
    "discussion_occurrences": len(topic_occurrences),
    "discussion_unique": len(topic_union_rows),
    "query_calls": len(queries),
    "failures": failures,
    "generated_at_utc": now_pair()[0],
    "generated_at_singapore": now_pair()[1],
})
write_json(EVIDENCE / "access_failures.json", failures)

print(json.dumps({
    "status": "OK_WITH_FAILURES" if failures else "OK",
    "official_content_pages": len(page_rows),
    "competition_file_records": len(file_rows),
    "competition_total_bytes": sum(int(row.get("total_bytes") or 0) for row in file_rows),
    "leaderboard_rows": len(leaderboard_rows),
    "kaggle_code_unique": len(kernel_union_rows),
    "discussion_unique": len(topic_union_rows),
    "query_calls": len(queries),
    "failure_count": len(failures),
}, ensure_ascii=False, indent=2))
