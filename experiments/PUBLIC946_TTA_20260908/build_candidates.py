#!/usr/bin/env python3
"""Build B0/C1/C2 from the byte-frozen public V1, without running inference."""
from __future__ import annotations

import argparse
import ast
import copy
import difflib
import hashlib
import json
from pathlib import Path

from tta_patch import patch_expanded_predictor

ROOT = Path(__file__).resolve().parents[2]
BATCH = Path(__file__).resolve().parent
PUBLIC = ROOT / "downloads/20260908_public946/tta/biohub-942tta.ipynb"
SUPPORT = ROOT / "downloads/PUBLIC946_TTA_20260908/support_v10/repo/scripts/predict_unet_transformer.py"
PUBLIC_SHA = "521cb97f0f457643379a51b60c4f71e3f4cc7d1823fd98cbb97633ffaa515ec4"
SUPPORT_SHA = "c44e771ba5980b820f93091e03a303c25dfe8f3232e501f54dc9565731c234b9"
MARKER = "# ===== end edge-feature TTA ====="


def sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode()).hexdigest()


def source(cell):
    value = cell["source"]
    return value if isinstance(value, str) else "".join(value)


def load_public(path=PUBLIC):
    data = Path(path).read_bytes()
    if sha(data) != PUBLIC_SHA or len(data) != 213474:
        raise ValueError("The archived public source bytes differ from the task's frozen original")
    notebook = json.loads(data)
    if len(notebook["cells"]) != 12 or any(c["cell_type"] != "code" for c in notebook["cells"]):
        raise ValueError("Expected exactly the 12 public code cells")
    for index, cell in enumerate(notebook["cells"]):
        compile(source(cell), f"public_cell_{index:02}.py", "exec")
    return notebook


def expand_public_predictor(support_source, notebook=None):
    """Execute the literal string-patch transformations in their real order.

    This does not execute CUDA setup, model loading or any Notebook cell.
    Literal old/new values are read from the public cell AST rather than copied
    from a conversational reconstruction. All expanded source is compiled.
    """
    notebook = notebook or load_public()
    cell = source(notebook["cells"][4])
    literals = {}
    for node in ast.parse(cell).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                literals[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError, SyntaxError):
                pass
    pairs = [("eight_detection_views", literals["_old"], literals["_new"])]
    pairs.extend((f"ensemble_{i}", old, new) for i, (old, new) in enumerate(literals["_ensemble_replacements"], 1))
    pairs.extend((name, literals[old], literals[new]) for name, old, new in [
        ("frame_retention", "_guard_old", "_guard_new"),
        ("harmonic_bidirectional", "_bi_old", "_bi_new"),
        ("coordinate_manifest", "_coordinate_manifest_old", "_coordinate_manifest_new"),
        ("primary_edge_feature_tta", "_et_old", "_et_new"),
    ])
    out = support_source
    receipt = []
    for label, old, new in pairs:
        count = out.count(old)
        if count != 1:
            raise ValueError(f"Public patch {label}: expected one anchor, got {count}")
        out = out.replace(old, new, 1)
        compile(out, f"public_expanded_after_{label}.py", "exec")
        receipt.append({"label": label, "matches": count, "old_sha256": sha(old), "new_sha256": sha(new),
                        "result_sha256": sha(out)})
    return out, receipt


def injection(arm, public_expanded_sha, patch_text, runtime_text):
    return (
        "\n\n# PUBLIC946_TTA_20260908: task-authorized arm and identical read-only hooks.\n"
        f"os.environ['BIOHUB_PUBLIC946_ARM'] = {arm!r}\n"
        f"_p946_patch_text = {patch_text!r}\n"
        f"_p946_runtime_text = {runtime_text!r}\n"
        "import hashlib as _p946_hashlib\n"
        "_p946_original_expanded = _ps.read_text()\n"
        f"assert _p946_hashlib.sha256(_p946_original_expanded.encode()).hexdigest() == {public_expanded_sha!r}\n"
        "_p946_namespace = {}\n"
        "exec(compile(_p946_patch_text, 'public946_patch.py', 'exec'), _p946_namespace)\n"
        "_p946_patched, _p946_patch_receipt = _p946_namespace['patch_expanded_predictor'](\n"
        "    _p946_original_expanded, os.environ['BIOHUB_PUBLIC946_ARM'], audit=True)\n"
        "(REPO_DIR / 'scripts' / 'public946_runtime.py').write_text(_p946_runtime_text)\n"
        "_ps.write_text(_p946_patched)\n"
        "(WORKING_DIR / 'public946_expanded_patch_receipt.json').write_text(\n"
        "    json.dumps(_p946_patch_receipt, indent=2, sort_keys=True) + '\\n')\n"
        "print('PUBLIC946_PATCH_RECEIPT', json.dumps(_p946_patch_receipt, sort_keys=True))\n"
        "# END PUBLIC946_TTA_20260908 additions; original production runner follows.\n"
    )


def build(public_path=PUBLIC, support_path=SUPPORT, require_final=True):
    public = load_public(public_path)
    support_bytes = Path(support_path).read_bytes()
    if sha(support_bytes) != SUPPORT_SHA:
        raise ValueError("The support predictor hash differs from the public guard")
    expanded, public_patches = expand_public_predictor(support_bytes.decode(), public)
    patch_text = (BATCH / "tta_patch.py").read_text()
    runtime_text = (BATCH / "runtime_audit.py").read_text()
    final_path = BATCH / "final_audit.py"
    if require_final and not final_path.is_file():
        raise FileNotFoundError("Awaiting the independently authored common final_audit.py")
    final_source = (final_path.read_text() + "\npublic946_final_audit(globals())\n") if final_path.is_file() else None
    output = {"public_ref": "redoctopusk/biohub-942tta", "public_version": 1,
        "public_script_version_id": 347821442, "public_sha256": PUBLIC_SHA,
        "support_predictor_sha256": SUPPORT_SHA, "public_expanded_sha256": sha(expanded),
        "public_patch_anchors": public_patches, "public_cell_source_sha256": [sha(source(c)) for c in public["cells"]],
        "common_audit": {"runtime_source_sha256": sha(runtime_text),
                         "final_source_sha256": sha(final_source) if final_source else None},
        "arms": {}}
    ignored = ROOT / "downloads/PUBLIC946_TTA_20260908/expanded"
    ignored.mkdir(parents=True, exist_ok=True)
    (ignored / "public.py").write_text(expanded)
    for arm in ("B0", "C1", "C2"):
        destination = BATCH / arm
        destination.mkdir(parents=True, exist_ok=True)
        algorithm, algorithm_receipt = patch_expanded_predictor(expanded, arm, audit=False)
        audited, audit_receipt = patch_expanded_predictor(expanded, arm, audit=True)
        (ignored / f"{arm}_algorithm.py").write_text(algorithm)
        (ignored / f"{arm}_audited.py").write_text(audited)
        diff = "".join(difflib.unified_diff(expanded.splitlines(True), algorithm.splitlines(True),
            fromfile="public_expanded_predictor.py", tofile=f"{arm}_expanded_predictor.py", n=3))
        (destination / "algorithm.diff").write_text(diff)
        notebook = copy.deepcopy(public)
        add = injection(arm, sha(expanded), patch_text, runtime_text)
        old_cell = source(public["cells"][4])
        if old_cell.count(MARKER) != 1:
            raise ValueError("Public cell 4 injection anchor is not unique")
        notebook["cells"][4]["source"] = old_cell.replace(MARKER, MARKER + add, 1)
        for index, cell in enumerate(notebook["cells"]):
            original = source(public["cells"][index])
            reconstructed = source(cell).replace(add, "", 1) if index == 4 else source(cell)
            if reconstructed != original:
                raise ValueError(f"Unexpected mutation to original public code cell {index}")
            cell["outputs"] = []
            cell["execution_count"] = None
        if final_source is not None:
            notebook["cells"].append({"cell_type": "code", "execution_count": None,
                "metadata": {}, "outputs": [], "source": final_source})
        for index, cell in enumerate(notebook["cells"]):
            compile(source(cell), f"{arm}_cell_{index:02}.py", "exec")
        data = (json.dumps(notebook, ensure_ascii=False, indent=1) + "\n").encode()
        (destination / "candidate.ipynb").write_bytes(data)
        output["arms"][arm] = {"candidate_sha256": sha(data), "bytes": len(data),
            "cell_source_sha256": [sha(source(c)) for c in notebook["cells"]],
            "original_twelve_cells_recover_byte_identically_by_removing_common_injection": True,
            "algorithm_changes": algorithm_receipt, "audited_expansion": audit_receipt,
            "algorithm_diff_sha256": sha(diff), "final_audit_present": final_source is not None}
        (destination / "source_review.json").write_text(json.dumps(output["arms"][arm], indent=2, sort_keys=True) + "\n")
    (BATCH / "build_receipt.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-missing-final-audit", action="store_true", help="Local development only; cannot be a frozen candidate")
    args = parser.parse_args()
    result = build(require_final=not args.allow_missing_final_audit)
    print(json.dumps({"public_expanded_sha256": result["public_expanded_sha256"],
        "arms": {arm: {k: v for k, v in value.items() if k in {"candidate_sha256", "bytes", "final_audit_present"}}
                 for arm, value in result["arms"].items()}}, indent=2))
