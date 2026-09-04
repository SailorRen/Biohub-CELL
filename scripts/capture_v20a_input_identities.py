#!/usr/bin/env python3
"""Capture metadata-only identities for the three V19C Kaggle input datasets."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


DATASETS = {
    "deepcenter": {
        "ref": "pilkwang/biohub-deepcenter-unet3d-center-prior-v1",
        "selected_artifact": "weights/full_frame_center/best.pt",
        "selected_artifact_sha256": "8040999a92f6b7bbd98fa8cf458141e045c0f9ad7c936bdb3b18e1f7edafe2a0",
    },
    "secondary": {
        "ref": "pilkwang/biohub-temporal-unet3d-seed314159-v1",
        "selected_artifact": "weights/unet_transformer/split_0/edge_predictor_best.pth",
        "selected_artifact_sha256": "9bac2fa0dadc4a6fc1899e0caf187f4b553e0a7cd90ba1261a68b35ffe9e305f",
    },
    "primary_and_support": {
        "ref": "pilkwang/biohub-tracking-support-pack-50ep-v1",
        "selected_artifact": "weights/unet_transformer/split_0/edge_predictor_best.pth",
        "selected_artifact_sha256": "12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771",
        "support_python_manifest_sha256": "978b626d1fd1e7397435a437dfe68691defe1572fc3c20e61012d7c9b52ed029",
    },
}


def canonical_bytes(value: Any) -> bytes:
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
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()
    records: list[dict[str, Any]] = []
    for role, frozen in DATASETS.items():
        ref = frozen["ref"]
        owner, slug = ref.split("/", 1)
        matches = [
            row
            for row in (api.dataset_list(search=slug, user=owner, page=1, sort_by="updated") or [])
            if row.ref == ref
        ]
        if len(matches) != 1:
            raise RuntimeError(f"expected one exact Dataset identity for {ref}, found {len(matches)}")
        metadata = matches[0].to_dict()
        files_response = api.dataset_list_files(ref, page_size=200)
        files = sorted(
            (
                {
                    "name": str(item.name),
                    "total_bytes": int(item.total_bytes or 0),
                    "creation_date": str(item.creation_date or ""),
                }
                for item in (files_response.files or [])
            ),
            key=lambda row: row["name"],
        )
        if getattr(files_response, "next_page_token", None):
            raise RuntimeError(f"Dataset {ref} unexpectedly exceeds one 200-row page")
        names = {row["name"] for row in files}
        if frozen["selected_artifact"] not in names:
            raise RuntimeError(f"selected artifact missing from {ref}: {frozen['selected_artifact']}")
        file_blob = b"".join(canonical_bytes(row) for row in files)
        record = {
            "role": role,
            "ref": ref,
            "dataset_id": int(metadata["id"]),
            "current_version_number": int(metadata["currentVersionNumber"]),
            "dataset_version_id": "UNKNOWN_NOT_EXPOSED_BY_LIST_API",
            "last_updated": metadata.get("lastUpdated"),
            "total_bytes_reported": int(metadata.get("totalBytes") or 0),
            "license_name": metadata.get("licenseName"),
            "file_count": len(files),
            "canonical_file_metadata_sha256": hashlib.sha256(file_blob).hexdigest(),
            "selected_artifact": frozen["selected_artifact"],
            "selected_artifact_sha256": frozen["selected_artifact_sha256"],
            "selected_artifact_hash_evidence": (
                "V19C ScriptVersionId 346969653 runtime integrity receipt"
            ),
        }
        if "support_python_manifest_sha256" in frozen:
            record["support_python_manifest_sha256"] = frozen["support_python_manifest_sha256"]
        records.append(record)

    now_utc = datetime.now(timezone.utc)
    payload = {
        "schema_version": "1.0",
        "access_mode": "KAGGLE_DATASET_LIST_AND_FILE_METADATA_ONLY",
        "access_time_utc": now_utc.isoformat(),
        "access_time_asia_shanghai": now_utc.astimezone(timezone(timedelta(hours=8))).isoformat(),
        "records": records,
        "payload_download_count": 0,
        "write_count": 0,
    }
    atomic_write(
        args.output,
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n",
    )
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
