#!/usr/bin/env python3
"""Collect bounded, read-only Kaggle Dataset search evidence.

This script invokes only ``kaggle datasets list``. It never downloads dataset
payloads and never calls a Kaggle write endpoint.
"""

from __future__ import annotations

import concurrent.futures
import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / "evidence" / "kaggle_cli" / "dataset_search"
QUERIES = [
    "biohub",
    "cell tracking",
    "zebrafish cell tracking",
    "zebrafish embryo",
    "Zebrahub",
    "3D microscopy",
    "4D microscopy",
    "time lapse microscopy",
    "fluorescent nuclei",
    "cell lineage",
    "Cell Tracking Challenge",
    "OME-Zarr",
    "GEFF",
    "tracksdata",
    "Ultrack",
    "Trackastra",
    "Cellpose",
    "StarDist",
    "nuclei tracking",
    "light sheet microscopy",
]
PAGES = (1, 2)


def now_pair() -> tuple[str, str]:
    utc = dt.datetime.now(dt.timezone.utc)
    sg = utc.astimezone(dt.timezone(dt.timedelta(hours=8)))
    return utc.isoformat(), sg.isoformat()


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")


def run_one(query: str, page: int) -> dict:
    started_utc, started_sg = now_pair()
    argv = [
        "kaggle",
        "datasets",
        "list",
        "-s",
        query,
        "--format",
        "json",
        "-p",
        str(page),
    ]
    proc = subprocess.run(argv, capture_output=True, text=False, timeout=120)
    finished_utc, finished_sg = now_pair()
    stem = f"{slugify(query)}_p{page}"
    stdout_path = EVIDENCE / f"{stem}.json"
    stderr_path = EVIDENCE / f"{stem}.stderr.txt"
    stdout_path.write_bytes(proc.stdout)
    if proc.stderr:
        stderr_path.write_bytes(proc.stderr)
    rows = []
    parse_error = None
    no_results = proc.stdout.strip() in {b"", b"No datasets found"}
    if proc.returncode == 0 and no_results:
        rows = []
    elif proc.returncode == 0:
        try:
            rows = json.loads(proc.stdout.decode("utf-8"))
        except Exception as exc:  # noqa: BLE001 - preserved in evidence log
            parse_error = f"{type(exc).__name__}: {exc}"
    return {
        "query": query,
        "sort_order": "hottest_default",
        "result_page": page,
        "argv": argv,
        "started_utc": started_utc,
        "started_singapore": started_sg,
        "finished_utc": finished_utc,
        "finished_singapore": finished_sg,
        "exit_code": proc.returncode,
        "result_count": len(rows) if isinstance(rows, list) else 0,
        "stdout_bytes": len(proc.stdout),
        "stdout_sha256": hashlib.sha256(proc.stdout).hexdigest(),
        "stdout_path": str(stdout_path.relative_to(ROOT)),
        "stderr_bytes": len(proc.stderr),
        "stderr_sha256": hashlib.sha256(proc.stderr).hexdigest() if proc.stderr else None,
        "stderr_path": str(stderr_path.relative_to(ROOT)) if proc.stderr else None,
        "parse_error": parse_error,
        "empty_result_response": proc.returncode == 0 and no_results,
        "rows": rows if isinstance(rows, list) else [],
    }


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    jobs = [(query, page) for query in QUERIES for page in PAGES]
    records = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        future_map = {pool.submit(run_one, q, p): (q, p) for q, p in jobs}
        for future in concurrent.futures.as_completed(future_map):
            q, p = future_map[future]
            try:
                records.append(future.result())
            except Exception as exc:  # noqa: BLE001 - failure is evidence
                utc, sg = now_pair()
                records.append(
                    {
                        "query": q,
                        "sort_order": "hottest_default",
                        "result_page": p,
                        "started_utc": None,
                        "started_singapore": None,
                        "finished_utc": utc,
                        "finished_singapore": sg,
                        "exit_code": None,
                        "result_count": 0,
                        "stdout_bytes": 0,
                        "stdout_sha256": None,
                        "stdout_path": None,
                        "stderr_bytes": 0,
                        "stderr_sha256": None,
                        "stderr_path": None,
                        "parse_error": f"{type(exc).__name__}: {exc}",
                        "empty_result_response": False,
                        "rows": [],
                    }
                )
    records.sort(key=lambda r: (QUERIES.index(r["query"]), r["result_page"]))
    search_log = [{k: v for k, v in r.items() if k != "rows"} for r in records]
    (ROOT / "dataset_search_log.json").write_text(
        json.dumps(search_log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    combined: dict[str, dict] = {}
    for record in records:
        for rank, row in enumerate(record["rows"], start=1):
            ref = row.get("ref")
            if not ref:
                continue
            item = combined.setdefault(ref, {**row, "discoveries": []})
            item["discoveries"].append(
                {
                    "query": record["query"],
                    "sort_order": record["sort_order"],
                    "result_page": record["result_page"],
                    "result_rank": rank,
                    "evidence_path": record["stdout_path"],
                    "access_time_utc": record["finished_utc"],
                    "access_time_singapore": record["finished_singapore"],
                }
            )
    combined_rows = sorted(combined.values(), key=lambda x: x["ref"])
    (ROOT / "dataset_search_candidates.json").write_text(
        json.dumps(combined_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    failures = sum(1 for r in records if r["exit_code"] != 0 or r["parse_error"])
    print(f"queries={len(QUERIES)} pages={len(records)} unique={len(combined_rows)} failures={failures}")
    return 0 if failures == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
