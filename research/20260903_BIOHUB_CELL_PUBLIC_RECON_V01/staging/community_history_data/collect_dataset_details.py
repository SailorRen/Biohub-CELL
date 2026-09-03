#!/usr/bin/env python3
"""Collect metadata and bounded file listings for selected Kaggle Datasets.

Only the read-only ``datasets metadata`` and ``datasets files`` subcommands are
used. Dataset payloads are never downloaded.
"""

from __future__ import annotations

import concurrent.futures
import datetime as dt
import hashlib
import json
import re
import subprocess
import tempfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / "evidence" / "kaggle_cli" / "dataset_details"
CANDIDATES = [
    ("kms111201/biohub-cell-tracking-data", "large competition-named data mirror; leakage review"),
    ("jobayerhossain/biohub-cell-tracking-during-development", "competition-named data copy"),
    ("isacinformagenie5/biohub-cell-tracking-during-development", "competition-named output/model bundle"),
    ("soufianehajou/biohub-officiel-v6", "competition-named small artifact"),
    ("pilkwang/biohub-tracking-support-pack-50ep-v1", "high-use competition support pack"),
    ("pilkwang/biohub-temporal-unet3d-seed314159-v1", "competition temporal 3D weights"),
    ("pilkwang/biohub-deepcenter-epoch400-snapshot", "competition center model snapshot"),
    ("pilkwang/biohub-local-association-ranker-unet300-v1", "competition association ranker"),
    ("dalloliogm/biohub-official-scorer-patched", "patched metric code"),
    ("busyaprime/biohub-local-scoring-support-pack", "local scoring support"),
    ("dariushafshar/biohub-local-cv-pack", "competition CV and GT statistics"),
    ("ideaplatsteven/biohub-celltrack-pipeline", "competition pipeline and tracksdata"),
    ("aaaa1597/cell-tracking-src", "cell-tracking source bundle"),
    ("ayeshasummaiyya/royerlabkaggle-cell-tracking-competition", "mirror of required starter repository"),
    ("omararaby1/kaggle-cell-tracking-competition", "second starter repository mirror"),
    ("rommelsharma/biohub-tracking-src", "competition tracking source"),
    ("shorooghahmadi/biohub-embryo-celltrack-v2-ipynb", "competition notebook artifact"),
    ("shubzk17/biohub-cellmot-baseline", "competition CellMOT baseline"),
    ("aradhitadatey/biohub-cell-tracking-classical-baseline-ipynb", "competition classical baseline"),
    ("abdulhamidodejimi/biohub-cell-tracking-baseline-script", "competition baseline script"),
    ("eariosb/trackastra-offline", "Trackastra offline package and CTC model"),
    ("subinium/biohub-trackastra-public-weights-mirror", "competition Trackastra weight mirror"),
    ("varonvictormiranda/ultrack-offline-min", "Ultrack offline package"),
    ("remylivecellimaging/e-coli-cells-tracking-dataset-for-gnn", "true cell-tracking data for GNN"),
    ("vyshnavveeravalli/zebrafish-embryonic-development", "zebrafish embryo data"),
    ("kkunizaw/biohub-zh001r", "Biohub/Zebrahub-named artifact"),
    ("haashaatif/fuse-my-cells-part-01", "3D light-sheet cell data part 1"),
    ("kmader/electron-microscopy-3d-segmentation", "historical 3D microscopy segmentation data"),
    ("rudispresence/biohub-embryo-stardist-bayesian-assets", "competition StarDist lineage assets"),
    ("felipeporcher/trackastra", "Trackastra package/model artifact"),
    ("justinkim1216/biohub-nnunet-flow-support-v1", "competition flow support pack"),
    ("eliork/biohub-geff-label-bundle-v1", "competition GEFF label bundle"),
    ("engadamalmohammedi/biohub-full-eda", "competition EDA artifact"),
    ("t2better/biohub-audit-code-v1", "competition evaluation audit code"),
    ("rudispresence/biohub-stabledet-hoct-runtime", "competition runtime with GEFF/tracksdata"),
]


def now_pair() -> tuple[str, str]:
    utc = dt.datetime.now(dt.timezone.utc)
    sg = utc.astimezone(dt.timezone(dt.timedelta(hours=8)))
    return utc.isoformat(), sg.isoformat()


def safe_ref(ref: str) -> str:
    return ref.replace("/", "__")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_files(raw: bytes) -> tuple[list[dict], str | None, str | None]:
    text = raw.decode("utf-8", errors="replace")
    token_match = re.search(r"^Next Page Token = (.+)$", text, re.MULTILINE)
    start = text.find("[")
    if start < 0:
        if "No files found" in text:
            return [], token_match.group(1).strip() if token_match else None, None
        return [], token_match.group(1).strip() if token_match else None, "JSON array not found"
    try:
        return json.loads(text[start:]), token_match.group(1).strip() if token_match else None, None
    except Exception as exc:  # noqa: BLE001 - preserved as an evidence gap
        return [], token_match.group(1).strip() if token_match else None, f"{type(exc).__name__}: {exc}"


def extension(name: str) -> str:
    lower = name.casefold()
    for suffix in (".ome.zarr", ".tar.gz", ".nii.gz"):
        if lower.endswith(suffix):
            return suffix
    p = Path(lower)
    return p.suffix or "[no_extension]"


def collect_one(candidate: tuple[str, str]) -> dict:
    ref, selection_reason = candidate
    started_utc, started_sg = now_pair()
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    stem = safe_ref(ref)

    with tempfile.TemporaryDirectory(prefix="biohub-kaggle-meta-") as temp:
        meta_proc = subprocess.run(
            ["kaggle", "datasets", "metadata", ref, "-p", temp],
            capture_output=True,
            text=False,
            timeout=120,
        )
        temp_meta = Path(temp) / "dataset-metadata.json"
        meta_raw = temp_meta.read_bytes() if temp_meta.exists() else b""
    meta_path = EVIDENCE / f"{stem}.metadata.json"
    if meta_raw:
        meta_path.write_bytes(meta_raw)
    meta_stdout_path = EVIDENCE / f"{stem}.metadata.stdout.txt"
    if meta_proc.stdout:
        meta_stdout_path.write_bytes(meta_proc.stdout)
    meta_stderr_path = EVIDENCE / f"{stem}.metadata.stderr.txt"
    if meta_proc.stderr:
        meta_stderr_path.write_bytes(meta_proc.stderr)
    metadata = None
    meta_error = None
    if meta_proc.returncode == 0 and meta_raw:
        try:
            metadata = json.loads(meta_raw)
        except Exception as exc:  # noqa: BLE001
            meta_error = f"{type(exc).__name__}: {exc}"
    elif meta_proc.returncode != 0:
        meta_error = f"metadata exit {meta_proc.returncode}"
    else:
        meta_error = "metadata file missing"

    files_proc = subprocess.run(
        ["kaggle", "datasets", "files", ref, "--format", "json", "--page-size", "200"],
        capture_output=True,
        text=False,
        timeout=120,
    )
    files_path = EVIDENCE / f"{stem}.files_page1.txt"
    files_path.write_bytes(files_proc.stdout)
    files_stderr_path = EVIDENCE / f"{stem}.files.stderr.txt"
    if files_proc.stderr:
        files_stderr_path.write_bytes(files_proc.stderr)
    files, next_token, files_parse_error = parse_files(files_proc.stdout) if files_proc.returncode == 0 else ([], None, f"files exit {files_proc.returncode}")
    ext_counts = Counter(extension(str(x.get("name", ""))) for x in files)
    names = [str(x.get("name", "")) for x in files]
    suspicious = sorted(
        {
            marker
            for marker in ("submission", "test", "train", "label", "gt", "geff", "onnx", "weight", "checkpoint")
            if any(marker in name.casefold() for name in names)
        }
    )
    finished_utc, finished_sg = now_pair()
    return {
        "ref": ref,
        "url": f"https://www.kaggle.com/datasets/{ref}",
        "selection_reason": selection_reason,
        "started_utc": started_utc,
        "started_singapore": started_sg,
        "finished_utc": finished_utc,
        "finished_singapore": finished_sg,
        "metadata_exit_code": meta_proc.returncode,
        "metadata_bytes": len(meta_raw),
        "metadata_sha256": sha(meta_raw) if meta_raw else None,
        "metadata_path": str(meta_path.relative_to(ROOT)) if meta_raw else None,
        "metadata_stdout_bytes": len(meta_proc.stdout),
        "metadata_stderr_bytes": len(meta_proc.stderr),
        "metadata_error": meta_error,
        "metadata": metadata,
        "files_exit_code": files_proc.returncode,
        "files_response_bytes": len(files_proc.stdout),
        "files_response_sha256": sha(files_proc.stdout),
        "files_path": str(files_path.relative_to(ROOT)),
        "files_parse_error": files_parse_error,
        "files_observed_count": len(files),
        "files_observed_bytes_sum": sum(int(x.get("size", 0) or 0) for x in files),
        "file_extensions": dict(sorted(ext_counts.items())),
        "file_names": names,
        "next_page_token_present": bool(next_token),
        "file_list_complete": not bool(next_token) and files_parse_error is None and files_proc.returncode == 0,
        "suspicious_file_markers": suspicious,
        "read_status": "METADATA_ONLY" if metadata is not None and files_parse_error is None else "BLOCKED",
    }


def main() -> int:
    records = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        future_map = {pool.submit(collect_one, item): item[0] for item in CANDIDATES}
        for future in concurrent.futures.as_completed(future_map):
            ref = future_map[future]
            try:
                records.append(future.result())
            except Exception as exc:  # noqa: BLE001
                utc, sg = now_pair()
                records.append(
                    {
                        "ref": ref,
                        "url": f"https://www.kaggle.com/datasets/{ref}",
                        "finished_utc": utc,
                        "finished_singapore": sg,
                        "read_status": "BLOCKED",
                        "collector_error": f"{type(exc).__name__}: {exc}",
                    }
                )
    order = {ref: i for i, (ref, _) in enumerate(CANDIDATES)}
    records.sort(key=lambda r: order[r["ref"]])
    (ROOT / "dataset_detail_records.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    blocked = sum(1 for r in records if r.get("read_status") == "BLOCKED")
    partial_files = sum(1 for r in records if not r.get("file_list_complete", False))
    print(f"selected={len(records)} metadata_ok={len(records)-blocked} blocked={blocked} partial_file_lists={partial_files}")
    return 0 if blocked == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
