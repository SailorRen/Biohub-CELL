"""Build exactly one boundary-aware linefit notebook from the frozen B0."""
from __future__ import annotations

import ast
import copy
import difflib
import hashlib
import json
from pathlib import Path

from linefit_patch import patch_cell


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / "experiments/PUBLIC946_TTA_20260908/B0"
BASE_NOTEBOOK_SHA256 = "c4bfcd8d765c67d35435876b3f3eb7bb810e20556479a918143451e2c61f849c"
CANDIDATE_REF = "sailorren/biohub-946-linefit-boundary-20260909"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source(cell: dict) -> str:
    value = cell["source"]
    return value if isinstance(value, str) else "".join(value)


def build() -> dict:
    raw = (BASE / "candidate.ipynb").read_bytes()
    if sha(raw) != BASE_NOTEBOOK_SHA256:
        raise ValueError("B0 notebook byte identity changed")
    baseline = json.loads(raw)
    if len(baseline["cells"]) != 13:
        raise ValueError("Expected frozen thirteen-cell B0 including original audit")
    candidate = copy.deepcopy(baseline)
    old = source(baseline["cells"][5])
    new, patch_receipt = patch_cell(old)
    candidate["cells"][5]["source"] = new if isinstance(baseline["cells"][5]["source"], str) else new.splitlines(keepends=True)
    changed = [i for i, (a, b) in enumerate(zip(baseline["cells"], candidate["cells"])) if a != b]
    if changed != [5] or not patch_receipt["only_function_changed"]:
        raise ValueError({"unexpected_changed_cells": changed})
    for cell in candidate["cells"]:
        if cell["cell_type"] == "code":
            ast.parse(source(cell))
    stripped = copy.deepcopy(candidate)
    stripped["cells"][5] = copy.deepcopy(baseline["cells"][5])
    if stripped != baseline:
        raise ValueError("Change outside authorized cell")
    metadata = json.loads((BASE / "kernel-metadata.json").read_text())
    updated_metadata = copy.deepcopy(metadata)
    updated_metadata.update(id=CANDIDATE_REF, title=CANDIDATE_REF.split("/")[1])
    changed_metadata = [k for k in sorted(set(metadata) | set(updated_metadata)) if metadata.get(k) != updated_metadata.get(k)]
    if changed_metadata != ["id", "title"]:
        raise ValueError(changed_metadata)
    notebook_bytes = (json.dumps(candidate, ensure_ascii=False, indent=2) + "\n").encode()
    metadata_bytes = (json.dumps(updated_metadata, ensure_ascii=False, indent=2) + "\n").encode()
    (HERE / "candidate.ipynb").write_bytes(notebook_bytes)
    (HERE / "kernel-metadata.json").write_bytes(metadata_bytes)
    diff = "".join(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True), fromfile="B0/cell5", tofile="LINEFIT_BOUNDARY_20260909/cell5", n=3))
    (HERE / "algorithm.diff").write_text(diff)
    receipt = {
        "task_id": "LINEFIT_BOUNDARY_20260909", "status": "BUILT_NOT_RUN",
        "baseline_ref": "sailorren/biohub-946-b0-repro-20260908",
        "baseline_version": 1, "baseline_script_version_id": 348114666,
        "baseline_submission_id": 56091397,
        "baseline_notebook_sha256": sha(raw),
        "candidate_ref": CANDIDATE_REF,
        "candidate_notebook_sha256": sha(notebook_bytes),
        "metadata_sha256": sha(metadata_bytes), "algorithm_diff_sha256": sha(diff.encode()),
        "changed_cell_indices": changed, "metadata_changed_keys": changed_metadata,
        "all_other_cells_and_notebook_metadata_equal": stripped == baseline,
        "cell_source_sha256": [sha(source(c).encode()) for c in candidate["cells"]],
        "patch": patch_receipt,
        "preserved_audit_scope": "B0/PUBLIC946 original observational audit retained unchanged; candidate identity comes from new kernel metadata and external exact-version receipts",
        "algorithm_change": "backward linefit traversal requires predecessor successor count exactly one; forward traversal unchanged",
        "postprocess_policy": "weight=.8/window=2 and original automatic PP candidate list/selection unchanged",
        "kaggle_writes": 0,
    }
    (HERE / "build_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
