#!/usr/bin/env python3
"""Build the deterministic V20A split artifacts after the embryo-count gate.

This script never reads image/GEFF payloads and never calls Kaggle.  It consumes
the already captured competition metadata inventory and creates a fail-closed
split receipt.  A blocked split deliberately contains no fold assignments.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


TASK_ID = "CODEX_20260904_BIOHUB_V20A_SAFE_DIV_RADIUS"
BLOCK_STATUS = "BLOCKED_INSUFFICIENT_EMBRYO_GROUPS"
OFFICIAL_RULE_EVIDENCE = (
    "research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/staging/official_kaggle/"
    "evidence/browser_official_routes.json"
)
OFFICIAL_RULE_EVIDENCE_SHA256 = (
    "86dce5c34f8e17df231ae6f67486aa950ad61972f06418b5030c0f4c5eb1ebaf"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build(project_root: Path) -> None:
    exp = project_root / "experiments/V20A"
    inventory_path = exp / "frozen_embryo_inventory.csv"
    receipt_path = exp / "competition_file_inventory_receipt.json"
    split_csv_path = exp / "frozen_split.csv"
    split_json_path = exp / "frozen_split.json"
    split_sha_path = exp / "frozen_split_sha256.txt"

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    with inventory_path.open(newline="", encoding="utf-8") as handle:
        inventory = list(csv.DictReader(handle))

    included = [
        row
        for row in inventory
        if row["included_in_frozen_inventory"].lower() == "true"
        and row["official_scorer_eligibility"] == "ELIGIBLE_METADATA_SCHEMA_PRESENT"
    ]
    included.sort(key=lambda row: row["stem"])
    groups = Counter(row["embryo_group"] for row in included)

    if len(included) != receipt["eligible_train_stem_count"]:
        raise RuntimeError("eligible sample count differs from inventory receipt")
    if sorted(groups) != receipt["embryo_groups"]:
        raise RuntimeError("embryo groups differ from inventory receipt")
    if sha256_file(inventory_path) != receipt["inventory_sha256"]:
        raise RuntimeError("inventory hash differs from inventory receipt")
    if len(groups) >= 3:
        raise RuntimeError("this builder is only valid for the hard-stop branch")

    with split_csv_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "stem",
            "embryo_group",
            "fold",
            "assignment_status",
            "included",
            "exclusion_reason",
            "evidence_class",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in included:
            writer.writerow(
                {
                    "stem": row["stem"],
                    "embryo_group": row["embryo_group"],
                    "fold": "NOT_ASSIGNED",
                    "assignment_status": BLOCK_STATUS,
                    "included": "true",
                    "exclusion_reason": "",
                    "evidence_class": "HOST_CONFIRMED_METADATA_ONLY",
                }
            )

    split = {
        "schema_version": "1.0",
        "task_id": TASK_ID,
        "status": BLOCK_STATUS,
        "decision_rule": {
            "minimum_effective_embryo_groups": 3,
            "if_sufficient": "K=min(5, embryo_group_count)",
            "if_insufficient": (
                "stop all candidate arms and forbid Kaggle Notebook/version/submission writes"
            ),
        },
        "grouping": {
            "field": "first underscore-delimited segment of the sample folder name",
            "meaning": "embryo_id",
            "official_rule_evidence_path": OFFICIAL_RULE_EVIDENCE,
            "official_rule_evidence_sha256": OFFICIAL_RULE_EVIDENCE_SHA256,
            "official_rule_excerpt_paraphrase": (
                "The first folder-name segment identifies the embryo; multiple samples may "
                "share an embryo and train/test embryos are disjoint."
            ),
        },
        "inventory": {
            "path": "experiments/V20A/frozen_embryo_inventory.csv",
            "sha256": receipt["inventory_sha256"],
            "competition_file_metadata_sha256": receipt[
                "canonical_file_metadata_sha256"
            ],
            "eligible_sample_count": len(included),
            "eligibility_boundary": receipt["eligibility_boundary"],
            "image_or_geff_payload_download_count": receipt[
                "image_or_geff_payload_download_count"
            ],
        },
        "effective_embryo_group_count": len(groups),
        "embryo_groups": [
            {"embryo_group": name, "sample_count": groups[name]}
            for name in sorted(groups)
        ],
        "effective_group_count_is_upper_bound": (
            "All labeled train stems in the authoritative listing use only these two "
            "prefixes; payload-level ineligibility could reduce but cannot increase the count."
        ),
        "selected_sample_count": len(included),
        "excluded_sample_count": 0,
        "fold_count": None,
        "folds": [],
        "fold_assignment_status": "NOT_CREATED_HARD_GATE",
        "embryo_leakage_status": "NOT_EVALUABLE_NO_FOLDS_CREATED",
        "test_identity_used_for_split": False,
        "test_isolation_check": "PASS_TEST_IDENTITIES_NOT_USED_FOR_ASSIGNMENT",
        "split_csv_path": "experiments/V20A/frozen_split.csv",
        "split_csv_sha256": sha256_file(split_csv_path),
        "candidate_runs_allowed": False,
        "kaggle_submission_allowed": False,
    }
    write_json(split_json_path, split)
    split_sha_path.write_text(
        f"{sha256_file(split_json_path)}  experiments/V20A/frozen_split.json\n"
        f"{sha256_file(split_csv_path)}  experiments/V20A/frozen_split.csv\n"
        f"{sha256_file(inventory_path)}  experiments/V20A/frozen_embryo_inventory.csv\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()
    build(Path(args.project_root).resolve())
    print("V20A_BLOCKED_FREEZE_BUILT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
