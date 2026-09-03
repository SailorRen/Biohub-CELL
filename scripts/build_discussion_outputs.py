#!/usr/bin/env python3
"""Build the discussion inventory and narrative from browser-read evidence."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01"
EVIDENCE_REL = "research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/staging/root_discussion_deep_reads.json"
EVIDENCE = ROOT / EVIDENCE_REL
LISTING_REL = "research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/evidence/discussion_listing_pages_1_3.json"
LISTING = ROOT / LISTING_REL
QUERY_REL = "research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/evidence/discussion_keyword_searches.json"
QUERY = ROOT / QUERY_REL
BASE = "https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/"

# These were transcribed from the first three pages of the logged-in Discussion
# listing on 2026-09-03. The listing is discovery evidence, not body evidence.
DISCOVERED = [
    ("738833", "Cell Tracking In-Person Workshop", 1, 1),
    ("714101", "How to get started + Competition's Official Discord", 1, 2),
    ("716062", "Welcome to the Biohub - Cell Tracking During Development Challenge", 1, 3),
    ("738217", "focus3d : one of the best 3d cell segmentation", 1, 4),
    ("739018", "Question about the node-count adjustment in the metric (adj_edge_jaccard can exceed 1)", 1, 5),
    ("738276", "Quick question for anyone above the 0.94 line — is the detector still a 3D UNet heatmap for you, or did you move to something else ?", 1, 6),
    ("738773", "Detector overfits past ~epoch 10 on fixed sparse-GT frames -- anyone else see this?", 1, 7),
    ("739221", "TemporalUNet loss", 1, 8),
    ("739220", "How to reach 0.9", 1, 9),
    ("737103", "Hand labeling - is it external data?", 1, 10),
    ("738778", "GNN", 1, 11),
    ("738970", "Starters", 1, 12),
    ("737101", "Stuck at 0.928", 1, 13),
    ("737543", "what layer did ur gains actually come from", 1, 14),
    ("737896", "Very dim nodes?", 1, 15),
    ("738210", "Training notebooks", 1, 16),
    ("736937", "Public Notebook Rankings Need a Metric Refresh", 1, 17),
    ("737659", "Scoring after notebook ran", 1, 18),
    ("737438", "Division designs", 1, 19),
    ("737577", "division jaccard", 1, 20),
    ("735352", "Leaderboard shakeup", 2, 1),
    ("734604", "Model", 2, 2),
    ("735307", "First submit", 2, 3),
    ("734237", "Scoring time", 2, 4),
    ("734330", "Is public Zebrahub data allowed as external training data?", 2, 5),
    ("735531", "Baseline training", 2, 6),
    ("732474", "Errors on GT cell traces", 2, 7),
    ("724130", "Visualizer", 2, 8),
    ("732103", "Synthetic dataset", 2, 9),
    ("734192", "Points", 2, 10),
    ("734093", "Case study", 2, 11),
    ("733877", "A one-to-one linker scores 0.000 on divisions - four measurements on the metric itself", 2, 12),
    ("734053", "The voxels are 4:1 anisotropic in Z, and two other things sitting in zarr.json", 2, 13),
    ("734015", "Patch vs whole volume", 2, 14),
    ("733973", "The linking radius is 8.4 µm, and divisions are one link in 853", 2, 15),
    ("733389", "GEFF node coordinates alignment with Zarr image volume", 2, 16),
    ("732674", "Every submission except the unmodified sample_submission.csv gets Submission Scoring Error", 2, 17),
    ("732345", "Training time", 2, 18),
    ("730160", "Does CV match LB in this competition?", 2, 19),
    ("724283", "beware of jumps in ground truth track", 2, 20),
    ("730924", "Diversity", 3, 1),
    ("729930", "Training time", 3, 2),
    ("726924", "CoTracker", 3, 3),
    ("730486", "Engine", 3, 4),
    ("729082", "Exact duplicate volumes, but GT edge moves 8.9 µm", 3, 5),
    ("728613", "Score 0", 3, 6),
    ("729053", "not all sparse GT edge are correct", 3, 7),
    ("728551", "Post-patch: is the 0.91+ frontier separated by the edge term or by divisions?", 3, 8),
    ("730054", "Save and run", 3, 9),
    ("729057", "Cell Tracking Challenge dataset", 3, 10),
    ("730149", "Submission time", 3, 11),
    ("728324", "COMPLETED: Rescore Underway", 3, 12),
    ("727154", "Division Metric exploit and patch.", 3, 13),
    ("729420", "Data update", 3, 14),
    ("729878", "Test samples", 3, 15),
    ("727957", "Any update on the re-scoring timeline?", 3, 16),
    ("728300", "You can score on train locally, and why a clean prediction can go above 1.0", 3, 17),
    ("728620", "What if we want the raw data, and/or want to use a language other than Python?", 3, 18),
    ("727881", "Zarr import", 3, 19),
    ("727051", "Video", 3, 20),
]


def topic(title: str) -> str:
    low = title.lower()
    for needle, label in [
        ("exploit", "metric_patch"), ("rescore", "leaderboard_recalculation"),
        ("jaccard", "metric"), ("score", "scoring"), ("zarr", "data_format"),
        ("geff", "data_format"), ("division", "division"), ("label", "labels_external_data"),
        ("zebrahub", "external_data"), ("train", "training"), ("notebook", "public_code"),
        ("cv", "validation"), ("ground truth", "ground_truth"), ("gt", "ground_truth"),
        ("workshop", "announcement"), ("welcome", "announcement"),
    ]:
        if needle in low:
            return label
    return "method_or_operations"


def main() -> None:
    deep = {str(r["discussion_id"]): r for r in json.loads(EVIDENCE.read_text(encoding="utf-8"))}
    listing_pages = json.loads(LISTING.read_text(encoding="utf-8"))
    query_pages = json.loads(QUERY.read_text(encoding="utf-8"))
    discovered = []
    seen_listing = set()
    for page in listing_pages:
        for rank, item in enumerate(page["items"], 1):
            if item["id"] in seen_listing:
                continue
            seen_listing.add(item["id"])
            title_lines = [line.strip() for line in item["text"].splitlines() if line.strip() and line.strip() != "emoji_people"]
            discovered.append((item["id"], title_lines[0], page["page"], rank, LISTING_REL))
    for query in query_pages:
        for rank, item in enumerate(query["items"], 1):
            if item["id"] in seen_listing:
                continue
            seen_listing.add(item["id"])
            discovered.append((item["id"], item["text"], "keyword_search", rank, QUERY_REL))
    fields = [
        "source_id", "discussion_id", "title", "author", "author_role", "created_at", "updated_at",
        "votes", "comment_count", "url", "topic", "read_status", "first_post_read",
        "comments_loaded", "comments_total", "host_reply_present", "evidence_path", "notes",
    ]
    seen = set()
    rows = []
    for did, listing_title, page, rank, discovery_evidence in discovered:
        if did in seen:
            continue
        seen.add(did)
        rec = deep.get(did)
        if rec:
            row = {
                "source_id": f"KDISC_{did}", "discussion_id": did, "title": rec["title"],
                "author": rec["author"], "author_role": rec["author_role"],
                "created_at": rec["posted_display"], "updated_at": "UNKNOWN", "votes": rec["votes"],
                "comment_count": rec["comments_total"], "url": rec["url"], "topic": topic(rec["title"]),
                "read_status": rec["read_status"], "first_post_read": "true",
                "comments_loaded": rec["comments_loaded"], "comments_total": rec["comments_total"],
                "host_reply_present": str(rec.get("host_reply_present", rec["author_role"] == "Competition Host")).lower(),
                "evidence_path": EVIDENCE_REL,
                "notes": rec["summary"],
            }
        else:
            row = {
                "source_id": f"KDISC_{did}", "discussion_id": did, "title": listing_title,
                "author": "UNKNOWN", "author_role": "UNKNOWN", "created_at": "UNKNOWN", "updated_at": "UNKNOWN",
                "votes": "UNKNOWN", "comment_count": "UNKNOWN", "url": BASE + did, "topic": topic(listing_title),
                "read_status": "TITLE_SNIPPET_ONLY", "first_post_read": "false", "comments_loaded": "0",
                "comments_total": "UNKNOWN", "host_reply_present": "UNKNOWN", "evidence_path": discovery_evidence,
                "notes": f"Logged-in Discussion listing discovery only; page={page}; rank={rank}; no body inference.",
            }
        rows.append(row)

    output = RESEARCH / "08_kaggle_discussion_inventory.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    ordered = [deep[did] for did, *_ in discovered if did in deep]
    # Include any deep-read record not present in the three listing pages.
    ordered.extend(rec for did, rec in deep.items() if did not in {x[0] for x in discovered})
    lines = [
        "# Kaggle Discussion 深度阅读",
        "",
        "> 范围：2026-09-03 登录态浏览器只读。正文不再分发；仓库仅保存 URL、动态元数据、页面哈希和原创摘要。",
        "> 证据解释：Host/Kaggle Staff 与普通参赛者严格分开；参赛者数值若无版本或独立复算，不作为官方事实。",
        "",
        f"- 三页清单发现：{len(rows)} 个唯一主题。",
        f"- 实际正文深读：{len(deep)} 个唯一主题。",
        f"- 完整线程：{sum(r['read_status'] == 'FULL_THREAD_READ' for r in deep.values())} 个。",
        "- 浏览器操作：只导航、等待、展开回复和读取 DOM；没有点赞、回复、发帖或提交。",
        "",
    ]
    for idx, rec in enumerate(ordered, 1):
        sg = datetime.fromisoformat(rec["access_time_utc"].replace("Z", "+00:00")).astimezone(ZoneInfo("Asia/Singapore"))
        lines += [
            f"## {idx}. {rec['title']}", "",
            f"- source_id: `KDISC_{rec['discussion_id']}`",
            f"- URL: {rec['url']}",
            f"- 作者/角色: {rec['author']} / {rec['author_role']}",
            f"- 访问时间: {rec['access_time_utc']} UTC；{sg.isoformat()} Asia/Singapore",
            f"- 读取: {rec['read_status']}；评论 {rec['comments_loaded']}/{rec['comments_total']}；Host 回复: {str(rec.get('host_reply_present', rec['author_role'] == 'Competition Host')).lower()}",
            f"- 页面字节/SHA-256: {rec['bytes']} / `{rec['sha256']}`",
            f"- 摘要: {rec['summary']}", "",
        ]
    (RESEARCH / "09_kaggle_discussion_deep_read.md").write_text("\n".join(lines), encoding="utf-8")

    host_records = [r for r in ordered if r["author_role"] in {"Competition Host", "Kaggle Staff"} or r.get("host_reply_present", False)]
    hlines = [
        "# Host 与 Kaggle Staff 澄清",
        "",
        "> 仅收录已实际读取线程中由 Competition Host 或 Kaggle Staff 发布/回复的内容。普通参赛者回复不据此升级为规则。",
        "",
    ]
    for rec in host_records:
        hlines += [
            f"## {rec['title']}", "",
            f"- source_id: `KDISC_{rec['discussion_id']}`；角色: {rec['author_role']}；Host reply: {str(rec.get('host_reply_present', rec['author_role'] == 'Competition Host')).lower()}",
            f"- {rec['summary']}",
            f"- 证据: {rec['url']}；页面 SHA-256 `{rec['sha256']}`。", "",
        ]
    (RESEARCH / "10_host_clarifications.md").write_text("\n".join(hlines), encoding="utf-8")

    listing_by_page = {str(page["page"]): page for page in listing_pages}
    query_by_id = {}
    for query in query_pages:
        for item in query["items"]:
            query_by_id.setdefault(item["id"], query)
    manifest_rows = []
    for row in rows:
        did = row["discussion_id"]
        if did in deep:
            rec = deep[did]
            utc = rec["access_time_utc"]
            size = rec["bytes"]
            sha = rec["sha256"]
            query_value = "selected_from_listing_and_keyword_searches"
            sort_order = "relevance_and_required_topic"
            result_page = "thread"
            allowed = True
        else:
            discovery_note = row["notes"]
            page_marker = discovery_note.split("page=", 1)[1].split(";", 1)[0]
            if page_marker.isdigit():
                ev = listing_by_page[page_marker]
                query_value = "discussion listing"
                sort_order = "Hotness"
                result_page = page_marker
            else:
                ev = query_by_id[did]
                query_value = ev["query"]
                sort_order = "Kaggle discussion relevance"
                result_page = "1"
            utc = ev["access_time_utc"]
            size = ev["bytes"]
            sha = ev["sha256"]
            allowed = False
        sg = datetime.fromisoformat(utc.replace("Z", "+00:00")).astimezone(ZoneInfo("Asia/Singapore"))
        manifest_rows.append({
            "source_id": row["source_id"], "source_type": "kaggle_discussion", "platform": "Kaggle",
            "title": row["title"], "author": row["author"], "url": row["url"], "query": query_value,
            "sort_order": sort_order, "result_page": result_page, "result_rank": "UNKNOWN",
            "access_time_utc": utc, "access_time_singapore": sg.isoformat(), "read_status": row["read_status"],
            "bytes_observed": size, "sha256": sha, "version_id": "", "commit_sha": "", "license": "UNKNOWN",
            "evidence_path": row["evidence_path"], "factual_use_allowed": allowed,
            "notes": row["notes"],
        })
    with (RESEARCH / "staging/root_discussion_manifest.jsonl").open("w", encoding="utf-8") as handle:
        for row in manifest_rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    qfields = [
        "query_id", "category", "platform", "query", "sort_order", "result_page", "reported_total",
        "actually_obtained", "unique_after_dedupe", "deep_read_count", "access_time_utc",
        "access_time_singapore", "status", "evidence_path", "notes",
    ]
    qrows = []
    for page in listing_pages:
        utc = page["access_time_utc"]
        sg = datetime.fromisoformat(utc.replace("Z", "+00:00")).astimezone(ZoneInfo("Asia/Singapore"))
        ids_on_page = {item["id"] for item in page["items"]}
        qrows.append({
            "query_id": f"Q_KDISC_LIST_P{page['page']}", "category": "kaggle_discussion", "platform": "Kaggle",
            "query": "competition discussion listing", "sort_order": "Hotness", "result_page": page["page"],
            "reported_total": "UNKNOWN", "actually_obtained": len(page["items"]),
            "unique_after_dedupe": len(ids_on_page), "deep_read_count": len(ids_on_page & set(deep)),
            "access_time_utc": utc, "access_time_singapore": sg.isoformat(), "status": "FULL_PAGE_BODY_READ",
            "evidence_path": LISTING_REL, "notes": f"Rendered listing bytes={page['bytes']} sha256={page['sha256']}",
        })
    for idx, query in enumerate(query_pages, 1):
        utc = query["access_time_utc"]
        sg = datetime.fromisoformat(utc.replace("Z", "+00:00")).astimezone(ZoneInfo("Asia/Singapore"))
        ids = {item["id"] for item in query["items"]}
        qrows.append({
            "query_id": f"Q_KDISC_KEY_{idx:02d}", "category": "kaggle_discussion", "platform": "Kaggle",
            "query": query["query"], "sort_order": "Kaggle discussion relevance", "result_page": 1,
            "reported_total": "UNKNOWN", "actually_obtained": query["obtained"],
            "unique_after_dedupe": len(ids), "deep_read_count": len(ids & set(deep)),
            "access_time_utc": utc, "access_time_singapore": sg.isoformat(), "status": "FULL_PAGE_BODY_READ",
            "evidence_path": QUERY_REL, "notes": f"Rendered search bytes={query['bytes']} sha256={query['sha256']}",
        })
    with (RESEARCH / "staging/root_discussion_query_log.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=qfields)
        writer.writeheader()
        writer.writerows(qrows)

    cfields = [
        "claim_id", "report_section", "claim_text", "claim_type", "source_ids", "evidence_paths",
        "direct_or_inference", "confidence", "conflict_present", "conflict_notes",
    ]
    claim_specs = [
        ("CLM_DISC_METRIC_PATCH", "评分补丁和旧分数风险", "Competition Host 确认 Division Jaccard 存在漏洞、已发布补丁并启动重算。", "HOST_CONFIRMED", "KDISC_727154", "direct", "high", "false", ""),
        ("CLM_DISC_RESCORE_COMPLETE", "评分补丁和旧分数风险", "Kaggle Staff 在同一公告线程后续回复中确认重算完成。", "OFFICIAL_FACT", "KDISC_728324", "direct", "high", "false", ""),
        ("CLM_DISC_NOTEBOOK_STALE_RISK", "评分补丁和旧分数风险", "参赛者报告部分公开 Notebook 页面可能仍显示补丁前分数；该点没有 Host 确认。", "COMMUNITY_REPORT", "KDISC_736937", "direct", "medium", "false", "需与当前页面和具体版本绑定后才能确认单本分数是否过期"),
        ("CLM_DISC_ZEBRAHUB_ALLOWED", "外部数据合法性和泄漏风险", "Competition Host 明确允许使用公开 Zebrahub 数据和资源，并称其与隐藏 test set 无重叠。", "HOST_CONFIRMED", "KDISC_734330", "direct", "high", "false", "具体资产仍须逐项核对许可证和公开可得性"),
        ("CLM_DISC_DUMMY_PUBLIC_TEST", "数据结构和规模", "Competition Host 说明公开 test 文件只是运行占位样本，实际排行榜使用更大的私有 test set，且与公开 train 无重叠。", "HOST_CONFIRMED", "KDISC_716062", "direct", "high", "false", ""),
        ("CLM_DISC_CV_RISK", "当前未知事项", "参赛者报告公开权重可能见过全部训练视频，因此在训练视频上做 CV 有泄漏风险；尚未在本轮独立验证全部权重谱系。", "COMMUNITY_REPORT", "KDISC_730160", "direct", "medium", "false", "模型和 split manifest 需逐版本独立核验"),
        ("CLM_DISC_HAND_LABEL_UNKNOWN", "外部数据合法性和泄漏风险", "关于自行手工标注外部数据的规则解释在讨论中没有 Host 回复，当前结论为 UNKNOWN。", "UNKNOWN", "KDISC_737103", "direct", "high", "true", "参赛者回复互相冲突"),
    ]
    with (RESEARCH / "staging/root_discussion_claims.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=cfields)
        writer.writeheader()
        for cid, section, text, ctype, sid, direct, confidence, conflict, notes in claim_specs:
            writer.writerow({
                "claim_id": cid, "report_section": section, "claim_text": text, "claim_type": ctype,
                "source_ids": sid, "evidence_paths": EVIDENCE_REL, "direct_or_inference": direct,
                "confidence": confidence, "conflict_present": conflict, "conflict_notes": notes,
            })


if __name__ == "__main__":
    main()
