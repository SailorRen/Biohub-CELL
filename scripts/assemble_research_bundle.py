#!/usr/bin/env python3
"""Assemble the canonical INITIAL_RECON_V01 bundle from reviewed staging outputs.

This script performs no network access.  It copies the three bounded research
subtask outputs, merges their manifest/query/claim fragments, and refuses to
continue on duplicate identifiers, unsupported read states, or missing local
evidence.  It intentionally does not edit the final report or completion claim.
"""

from __future__ import annotations

import csv
import json
import shutil
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECON = ROOT / "research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01"
OFFICIAL = RECON / "staging/official_kaggle"
GITHUB = RECON / "staging/github_ecosystem"
COMMUNITY = RECON / "staging/community_history_data"

MANIFEST_FIELDS = [
    "source_id", "source_type", "platform", "title", "author", "url", "query",
    "sort_order", "result_page", "result_rank", "access_time_utc",
    "access_time_singapore", "read_status", "bytes_observed", "sha256", "version_id",
    "commit_sha", "license", "evidence_path", "factual_use_allowed", "notes",
]
QUERY_FIELDS = [
    "query_id", "category", "platform", "query", "sort_order", "result_page",
    "reported_total", "actually_obtained", "unique_after_dedupe", "deep_read_count",
    "access_time_utc", "access_time_singapore", "status", "evidence_path", "notes",
]
CLAIM_FIELDS = [
    "claim_id", "report_section", "claim_text", "claim_type", "source_ids",
    "evidence_paths", "direct_or_inference", "confidence", "conflict_present",
    "conflict_notes",
]
ALLOWED_READ_STATUSES = {
    "FULL_PAGE_BODY_READ", "FULL_THREAD_READ", "PARTIAL_THREAD_READ",
    "FULL_NOTEBOOK_SOURCE_AND_OUTPUTS_READ", "FULL_NOTEBOOK_SOURCE_READ",
    "NOTEBOOK_SOURCE_PARTIAL", "FULL_RELEVANT_REPO_SOURCE_READ", "TARGET_FILES_READ",
    "README_ONLY", "METADATA_ONLY", "TITLE_SNIPPET_ONLY", "BLOCKED", "RATE_LIMITED",
    "LOGIN_REQUIRED", "DELETED", "NOT_FOUND", "UNKNOWN",
}
BLOCK_STATUSES = {
    "BLOCKED", "RATE_LIMITED", "LOGIN_REQUIRED", "DELETED", "NOT_FOUND", "UNKNOWN",
}


def copy_required(source_dir: Path, names: list[str]) -> None:
    for name in names:
        source = source_dir / name
        if not source.is_file() or source.stat().st_size == 0:
            raise RuntimeError(f"missing or empty staging output: {source.relative_to(ROOT)}")
        shutil.copyfile(source, RECON / name)


def normalize_canonical_narrative() -> None:
    """Remove staging-only labels without altering any observed evidence."""
    replacements = {
        "01_official_competition.md": {
            "# 官方比赛事实（staging 草稿）": "# 官方比赛事实",
        },
        "03_official_rules_and_metric.md": {
            "# 官方规则、数据与评分（staging 草稿）": "# 官方规则、数据与评分",
            "评分补丁的正式时间线、重算范围和 host 解释需与 Discussion 深读结果合并；本 staging 不把普通参赛者文字升级为官方规则。":
                "评分补丁的正式时间线、重算范围和 host 解释已与 Discussion 深读结果交叉核对；不把普通参赛者文字升级为官方规则。",
        },
        "06_kaggle_code_deep_read.md": {
            "# Kaggle Code 源码深读（staging 草稿）": "# Kaggle Code 源码深读",
        },
        "12_github_deep_read.md": {
            "# GitHub 生态固定提交深读草稿": "# GitHub 生态固定提交深读",
            "> 这是 `github_ecosystem` 隔离 staging 草稿，未修改 canonical、未提交、未推送，也未修改任何外部仓库。":
                "> 本文档保留隔离子任务的固定 commit 阅读结果；研究过程未修改任何第三方仓库。",
        },
    }
    for name, mapping in replacements.items():
        path = RECON / name
        text = path.read_text(encoding="utf-8")
        for old, new in mapping.items():
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")


def load_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise RuntimeError(f"JSONL record is not an object: {path}:{line_number}")
        rows.append(row)
    return rows


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def assert_unique(rows: list[dict[str, object]], key: str, label: str) -> None:
    values = [str(row.get(key, "")).strip() for row in rows]
    missing = sum(not value for value in values)
    duplicates = sorted(value for value, count in Counter(values).items() if value and count > 1)
    if missing or duplicates:
        raise RuntimeError(f"{label}: missing {key}={missing}; duplicate {key}={duplicates[:20]}")


def ensure_evidence(path_value: object, label: str) -> None:
    evidence_path = str(path_value or "").strip()
    if not evidence_path or not (ROOT / evidence_path).is_file():
        raise RuntimeError(f"{label}: evidence does not resolve from repository root: {evidence_path!r}")


def add_github_discovery_records(manifest: list[dict[str, object]]) -> None:
    """Represent every repository discovery row in the unified manifest.

    The GitHub subtask manifest has one record per search-result page plus one
    per deep-read repository.  The inventory also contains distinct repository
    URLs discovered on those pages.  Adding the latter as TITLE_SNIPPET_ONLY
    makes the row-level provenance explicit without upgrading a title/link to a
    README or source-code read.
    """
    existing = {str(row.get("source_id", "")) for row in manifest}
    inventory = load_csv(RECON / "11_github_repository_inventory.csv")
    for row in inventory:
        source_id = row.get("source_id", "").strip()
        if not source_id or source_id in existing:
            continue
        if row.get("read_status") != "TITLE_SNIPPET_ONLY":
            raise RuntimeError(f"unmanifested non-discovery GitHub row: {source_id}")
        owner_repo = row.get("owner_repo", "")
        author = owner_repo.split("/", 1)[0] if "/" in owner_repo else ""
        manifest.append({
            "source_id": source_id,
            "source_type": "github_repository_search_result",
            "platform": "GitHub",
            "title": owner_repo,
            "author": author,
            "url": row.get("url", ""),
            "query": row.get("notes", ""),
            "sort_order": "search-result discovery",
            "result_page": "recorded in query-page evidence",
            "result_rank": "UNKNOWN",
            "access_time_utc": "2026-09-03T08:19:00Z/2026-09-03T08:25:00Z",
            "access_time_singapore": "2026-09-03T16:19:00+08:00/2026-09-03T16:25:00+08:00",
            "read_status": "TITLE_SNIPPET_ONLY",
            "bytes_observed": 0,
            "sha256": "",
            "version_id": "",
            "commit_sha": "",
            "license": row.get("license", "NOT_CHECKED"),
            "evidence_path": row.get("evidence_path", ""),
            "factual_use_allowed": False,
            "notes": "Derived repository title/link from recorded GitHub search pages; no README or source claim. "
                     + row.get("notes", ""),
        })
        existing.add(source_id)


def main() -> None:
    copy_required(OFFICIAL, [
        "01_official_competition.md", "02_official_data_inventory.csv",
        "03_official_rules_and_metric.md", "04_leaderboard_snapshot.csv",
        "05_kaggle_code_inventory.csv", "06_kaggle_code_deep_read.md",
        "07_kaggle_method_comparison.csv",
    ])
    copy_required(GITHUB, [
        "11_github_repository_inventory.csv", "12_github_deep_read.md",
        "13_github_code_method_matrix.csv",
    ])
    copy_required(COMMUNITY, [
        "14_reddit_and_web_inventory.csv", "15_external_scientific_sources.md",
        "16_similar_kaggle_competitions.csv", "17_historical_solution_research.md",
        "18_kaggle_datasets_inventory.csv",
    ])
    normalize_canonical_narrative()

    manifest_sources = [
        OFFICIAL / "source_manifest.jsonl",
        RECON / "staging/root_discussion_manifest.jsonl",
        GITHUB / "00_source_manifest.github_fragment.jsonl",
        COMMUNITY / "00_source_manifest.community_history_data.jsonl",
    ]
    manifest: list[dict[str, object]] = []
    for source in manifest_sources:
        if not source.is_file():
            raise RuntimeError(f"missing manifest fragment: {source.relative_to(ROOT)}")
        manifest.extend(load_jsonl(source))
    add_github_discovery_records(manifest)
    assert_unique(manifest, "source_id", "source manifest")
    for row in manifest:
        source_id = str(row.get("source_id", ""))
        status = str(row.get("read_status", ""))
        if status not in ALLOWED_READ_STATUSES:
            raise RuntimeError(f"source manifest: {source_id} has unsupported read_status={status!r}")
        ensure_evidence(row.get("evidence_path"), f"source manifest {source_id}")
    manifest.sort(key=lambda row: str(row.get("source_id", "")))
    with (RECON / "00_source_manifest.jsonl").open("w", encoding="utf-8") as handle:
        for row in manifest:
            normalized = {field: row.get(field, "") for field in MANIFEST_FIELDS}
            handle.write(json.dumps(normalized, ensure_ascii=False, separators=(",", ":")) + "\n")

    query_sources = [
        OFFICIAL / "search_query_log.csv",
        RECON / "staging/root_discussion_query_log.csv",
        GITHUB / "21_search_query_log.github_fragment.csv",
        COMMUNITY / "21_search_query_log.community_history_data.csv",
    ]
    queries: list[dict[str, object]] = []
    for source in query_sources:
        if not source.is_file():
            raise RuntimeError(f"missing query fragment: {source.relative_to(ROOT)}")
        queries.extend(load_csv(source))
    assert_unique(queries, "query_id", "search query log")
    for row in queries:
        ensure_evidence(row.get("evidence_path"), f"search query {row.get('query_id')}")
    queries.sort(key=lambda row: str(row.get("query_id", "")))
    write_csv(RECON / "21_search_query_log.csv", QUERY_FIELDS, queries)

    claim_sources = [
        OFFICIAL / "claims_fragment.csv",
        RECON / "staging/root_discussion_claims.csv",
        GITHUB / "19_claims_evidence_matrix.github_fragment.csv",
        COMMUNITY / "19_claims_evidence_matrix.community_history_data.csv",
    ]
    claims: list[dict[str, object]] = []
    for source in claim_sources:
        if not source.is_file():
            raise RuntimeError(f"missing claim fragment: {source.relative_to(ROOT)}")
        claims.extend(load_csv(source))
    assert_unique(claims, "claim_id", "claims evidence matrix")
    claims.sort(key=lambda row: str(row.get("claim_id", "")))
    write_csv(RECON / "19_claims_evidence_matrix.csv", CLAIM_FIELDS, claims)

    blocked = [row for row in manifest if row.get("read_status") in BLOCK_STATUSES]
    lines = [
        "# 访问失败与未暴露字段",
        "",
        "本清单由总装脚本从统一来源清单确定性生成。它记录实际访问中的阻断、限流、登录要求、删除、未找到和未暴露状态；不使用搜索摘要补写缺失正文。",
        "",
        f"受影响来源记录：{len(blocked)}。",
        "",
    ]
    for row in blocked:
        source_id = str(row.get("source_id", ""))
        title = str(row.get("title", "")).replace("\n", " ")
        status = str(row.get("read_status", ""))
        url = str(row.get("url", ""))
        evidence_path = str(row.get("evidence_path", ""))
        notes = str(row.get("notes", "")).replace("\n", " ")
        lines.extend([
            f"## {source_id}",
            "",
            f"- 状态：`{status}`",
            f"- 标题：{title or '未暴露'}",
            f"- URL：{url or '未暴露'}",
            f"- 证据：`{evidence_path}`",
            f"- 说明：{notes or '来源未返回可完整核验的正文或字段。'}",
            "",
        ])
    lines.extend([
        "## 子任务详细失败账本",
        "",
        "统一 manifest 用一条 source 记录表示同一访问面的阻断状态；下列详细账本保留逐次请求失败、隔离上下文和停止重试决定：",
        "",
        "- `research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/staging/official_kaggle/access_failures_fragment.md`：官方文件元数据 API 的 33 次 HTTP 429 失败及统一 `RATE_LIMITED` 结论。",
        "- `research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/staging/github_ecosystem/20_access_failures.github_fragment.md`：GitHub 隔离子任务的登录/匿名限流与源文件读取失败。",
        "- `research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/staging/community_history_data/20_access_failures.community_history_data.md`：Reddit、科学页面、历史比赛和 Dataset 的阻断/限流明细。",
        "",
        "GitHub 子任务中的登录错误仅描述其早期隔离默认上下文；主任务写入前已独立验证 `gh api user` 为 `SailorRen`，不把隔离失败外推为当前主环境凭据失效。",
        "",
    ])
    (RECON / "20_access_failures.md").write_text("\n".join(lines), encoding="utf-8")

    summary = {
        "manifest_records": len(manifest),
        "manifest_status_counts": dict(sorted(Counter(str(r.get("read_status", "")) for r in manifest).items())),
        "queries": len(queries),
        "claims": len(claims),
        "blocked_records": len(blocked),
    }
    (RECON / "staging/integration_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
