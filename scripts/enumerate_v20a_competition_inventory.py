#!/usr/bin/env python3
"""Freeze a metadata-only inventory of Biohub train/test samples.

The script performs read-only Kaggle API calls.  It never downloads image,
GEFF, checkpoint, or submission payloads and never stores pagination tokens.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


COMPETITION = "biohub-cell-tracking-during-development"
SAMPLE_RE = re.compile(r"^(train|test)/([^/]+)\.(zarr|geff)(?:/|$)")
REQUIRED_IMAGE_SUFFIXES = ("zarr.json", "0/zarr.json")
REQUIRED_GT_SUFFIXES = (
    "zarr.json",
    "nodes/ids/zarr.json",
    "nodes/props/t/values/zarr.json",
    "nodes/props/z/values/zarr.json",
    "nodes/props/y/values/zarr.json",
    "nodes/props/x/values/zarr.json",
    "edges/ids/zarr.json",
)


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_bytes(data)
    os.replace(temp, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--page-size", type=int, default=200)
    args = parser.parse_args()
    if not 1 <= args.page_size <= 200:
        parser.error("--page-size must be in [1, 200]")

    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()

    page_token: str | None = None
    pages = 0
    raw_rows: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    while True:
        response = api.competition_list_files(
            COMPETITION, page_token=page_token, page_size=args.page_size
        )
        pages += 1
        files = list(response.files or [])
        for item in files:
            name = str(item.name)
            if name in seen_names:
                raise RuntimeError(f"duplicate competition file metadata name: {name}")
            seen_names.add(name)
            raw_rows.append(
                {
                    "name": name,
                    "total_bytes": int(item.total_bytes or 0),
                    "creation_date": str(item.creation_date or ""),
                }
            )
        if pages == 1 or pages % 10 == 0 or not getattr(response, "next_page_token", None):
            print(f"page={pages} files={len(raw_rows)}", file=sys.stderr, flush=True)
        page_token = getattr(response, "next_page_token", None)
        if not page_token:
            break

    raw_rows.sort(key=lambda row: row["name"])
    raw_blob = b"".join(canonical_json(row) for row in raw_rows)
    raw_sha = hashlib.sha256(raw_blob).hexdigest()

    members: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    byte_counts: dict[tuple[str, str, str], int] = defaultdict(int)
    file_counts: dict[tuple[str, str, str], int] = defaultdict(int)
    for row in raw_rows:
        match = SAMPLE_RE.match(row["name"])
        if not match:
            continue
        split, stem, kind = match.groups()
        prefix = f"{split}/{stem}.{kind}/"
        suffix = row["name"][len(prefix) :] if row["name"].startswith(prefix) else ""
        key = (split, stem, kind)
        members[key].add(suffix)
        byte_counts[key] += row["total_bytes"]
        file_counts[key] += 1

    train_stems = sorted({stem for split, stem, _ in members if split == "train"})
    test_stems = sorted({stem for split, stem, _ in members if split == "test"})
    inventory_rows: list[dict[str, Any]] = []
    for stem in train_stems:
        prefix = stem.split("_", 1)[0]
        image_key = ("train", stem, "zarr")
        gt_key = ("train", stem, "geff")
        image_members = members.get(image_key, set())
        gt_members = members.get(gt_key, set())
        missing_image = [suffix for suffix in REQUIRED_IMAGE_SUFFIXES if suffix not in image_members]
        missing_gt = [suffix for suffix in REQUIRED_GT_SUFFIXES if suffix not in gt_members]
        paired = bool(image_members) and bool(gt_members)
        schema_complete = paired and not missing_image and not missing_gt
        inventory_rows.append(
            {
                "stem": stem,
                "embryo_prefix": prefix,
                "embryo_group": prefix,
                "visible_test_copy": str(stem in test_stems).lower(),
                "train_zarr_present": str(bool(image_members)).lower(),
                "train_geff_present": str(bool(gt_members)).lower(),
                "required_metadata_paths_present": str(schema_complete).lower(),
                "estimated_number_of_nodes_content": "UNKNOWN_NOT_DOWNLOADED",
                "official_scorer_eligibility": (
                    "ELIGIBLE_METADATA_SCHEMA_PRESENT" if schema_complete else "INELIGIBLE_METADATA_GAP"
                ),
                "included_in_frozen_inventory": str(schema_complete).lower(),
                "exclusion_reason": "" if schema_complete else "MISSING_REQUIRED_METADATA_PATH",
                "train_zarr_file_count": file_counts.get(image_key, 0),
                "train_zarr_total_bytes": byte_counts.get(image_key, 0),
                "train_geff_file_count": file_counts.get(gt_key, 0),
                "train_geff_total_bytes": byte_counts.get(gt_key, 0),
                "missing_required_image_paths": "|".join(missing_image),
                "missing_required_gt_paths": "|".join(missing_gt),
                "evidence_class": "HOST_CONFIRMED_METADATA_ONLY",
            }
        )

    columns = list(inventory_rows[0]) if inventory_rows else ["stem"]
    from io import StringIO

    buffer = StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(inventory_rows)
    inventory_blob = buffer.getvalue().encode("utf-8")

    eligible = [row for row in inventory_rows if row["included_in_frozen_inventory"] == "true"]
    embryo_groups = sorted({row["embryo_group"] for row in eligible})
    now_utc = datetime.now(timezone.utc)
    now_shanghai = now_utc.astimezone(timezone(timedelta(hours=8)))
    receipt = {
        "schema_version": "1.0",
        "competition": COMPETITION,
        "access_mode": "KAGGLE_COMPETITION_LIST_FILES_METADATA_ONLY",
        "access_time_utc": now_utc.isoformat(),
        "access_time_asia_shanghai": now_shanghai.isoformat(),
        "page_size": args.page_size,
        "pages_read": pages,
        "unique_file_metadata_rows": len(raw_rows),
        "unique_file_metadata_total_bytes": sum(row["total_bytes"] for row in raw_rows),
        "canonical_file_metadata_sha256": raw_sha,
        "train_stem_count": len(train_stems),
        "eligible_train_stem_count": len(eligible),
        "test_stem_count": len(test_stems),
        "embryo_groups": embryo_groups,
        "embryo_group_count": len(embryo_groups),
        "inventory_sha256": hashlib.sha256(inventory_blob).hexdigest(),
        "raw_payload_persisted": False,
        "pagination_tokens_persisted": False,
        "image_or_geff_payload_download_count": 0,
        "eligibility_boundary": (
            "Paired train image/GT directories and all required schema metadata paths are present in "
            "the authoritative file listing; GEFF metadata contents were not downloaded."
        ),
    }

    atomic_write(args.output_dir / "frozen_embryo_inventory.csv", inventory_blob)
    atomic_write(
        args.output_dir / "competition_file_inventory_receipt.json",
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n",
    )
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
