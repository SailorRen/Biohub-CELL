"""Only the two authorized TTA changes, applied after the public dynamic patch.

No prediction runs or external writes occur when this module is imported.
Each replacement is exact and required to match once. Tests consume the same
expanded source emitted here and subsequently written into Kaggle's predictor.
"""
from __future__ import annotations

import ast
import hashlib
import re


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def patch_expanded_predictor(source, arm, audit=False):
    if arm not in {"B0", "C1", "C2"}:
        raise ValueError(arm)
    original = source
    replacements = []

    def change(label, old, new):
        nonlocal source
        count = source.count(old)
        if count != 1:
            raise ValueError(f"{arm}: {label}: expected one anchor, got {count}")
        replacements.append({"label": label, "matches": count,
                             "old_sha256": _sha(old), "new_sha256": _sha(new)})
        source = source.replace(old, new, 1)

    if arm == "C1":
        change("primary_input_antidiagonal",
               "imgs_at = torch.rot90(imgs, 1, dims=(-2, -1)).transpose(-1, -2)",
               "imgs_at = imgs.flip((-2, -1)).transpose(-1, -2)")
        change("primary_detection_inverse_antidiagonal",
               "torch.rot90(det_at[f].transpose(-1, -2), -1, dims=(-2, -1))",
               "det_at[f].transpose(-1, -2).flip((-2, -1))")
        change("primary_feature_inverse_antidiagonal",
               "torch.rot90(_u_at.transpose(-1, -2), -1, dims=(-2, -1))",
               "_u_at.transpose(-1, -2).flip((-2, -1))")
        change("secondary_input_antidiagonal",
               "secondary_imgs_at = torch.rot90(\n                        imgs, 1, dims=(-2, -1)\n                    ).transpose(-1, -2)",
               "secondary_imgs_at = imgs.flip((-2, -1)).transpose(-1, -2)")
        change("secondary_detection_inverse_antidiagonal",
               "torch.rot90(\n                            secondary_det_at[f].transpose(-1, -2),\n                            -1,\n                            dims=(-2, -1),\n                        )",
               "secondary_det_at[f].transpose(-1, -2).flip((-2, -1))")
    if arm == "C2":
        change("secondary_accumulator_clone_preserves_original",
               "                    _secondary_nv = 1\n",
               "                    _secondary_nv = 1\n                    _secondary_feature_acc = secondary_unet_out.clone()\n")
        for suffix in ("flip", "rot", "t", "at"):
            change(f"secondary_reuse_existing_encode_{suffix}",
                   f"_, secondary_det_{suffix} = secondary_model.encode(secondary_imgs_{suffix})",
                   f"_secondary_u_{suffix}, secondary_det_{suffix} = secondary_model.encode(secondary_imgs_{suffix})")
            indent = "                        " if suffix in {"flip", "rot"} else "                    "
            inverses = {"flip": "_secondary_u_flip.flip(dims)",
                        "rot": "torch.rot90(_secondary_u_rot, -_k, dims=(-2, -1))",
                        "t": "_secondary_u_t.transpose(-1, -2)",
                        "at": "torch.rot90(_secondary_u_at.transpose(-1, -2), -1, dims=(-2, -1))"}
            change(f"secondary_accumulate_release_{suffix}",
                   f"{indent}del secondary_imgs_{suffix}, secondary_det_{suffix}",
                   f"{indent}_secondary_feature_acc.add_({inverses[suffix]})\n"
                   f"{indent}del secondary_imgs_{suffix}, secondary_det_{suffix}, _secondary_u_{suffix}")
        change("secondary_average_consumed_by_existing_association",
               "                    for f in range(W):\n                        secondary_det_logits[f] = secondary_det_logits[f] / _secondary_nv\n",
               "                    for f in range(W):\n                        secondary_det_logits[f] = secondary_det_logits[f] / _secondary_nv\n"
               "                    if _secondary_feature_acc.shape != secondary_unet_out.shape:\n"
               "                        raise RuntimeError('SECONDARY EDGE TTA shape mismatch')\n"
               "                    secondary_unet_out = _secondary_feature_acc.div_(_secondary_nv)\n"
               "                    del _secondary_feature_acc\n")
    algorithm_source = source
    if audit:
        # Identical instrumentation is added to all arms. Encode calls return
        # their untouched original tensors; diagnostics never enter prediction.
        change("audit_window_begin",
               "        unet_out, det_logits = model.encode(imgs)",
               "        from public946_runtime import (begin_window as _p946_begin, encode as _p946_encode,\n"
               "            after_encodes as _p946_after, association as _p946_association,\n"
               "            end_window as _p946_end)\n"
               "        _p946_context = _p946_begin(ds_path, frame_indices, imgs)\n"
               "        unet_out, det_logits = model.encode(imgs)")
        for role, modelname in (("secondary", "secondary_model"), ("primary", "model")):
            pattern = rf"(?<![A-Za-z_]){modelname}\.encode\("
            source, count = re.subn(pattern, f'_p946_encode(_p946_context, "{role}", {modelname}, ', source)
            if count != 5:
                raise ValueError(f"{arm}: expected 5 static {role} encode sites, got {count}")
            replacements.append({"label": f"audit_{role}_encode_sites", "matches": count})
        change("audit_encoding_output",
               "        del imgs\n",
               "        _p946_after(_p946_context, unet_out, secondary_unet_out,\n"
               "            secondary_link_mode, secondary_edge_weight, secondary_detection_weight, det_logits)\n"
               "        del imgs\n")
        edge_anchor = "                if secondary_link_mode == \"raw\":\n"
        change("audit_actual_secondary_association",
               edge_anchor,
               "                _p946_association(_p946_context, secondary_model, f_idx,\n"
               "                    secondary_unet_out, secondary_feat_src, secondary_feat_tgt,\n"
               "                    secondary_logits_pair, p_coords_src, p_coords_tgt,\n"
               "                    p_mask_src, p_mask_tgt, ds_arr_t, p_pos_src, p_pos_tgt,\n"
               "                    unet_feat_src, unet_feat_tgt, edge_logits_pair)\n\n" + edge_anchor)
        change("audit_window_end",
               "        del unet_out\n",
               "        _p946_end(_p946_context)\n        del unet_out\n")
    ast.parse(source)
    compile(source, f"{arm}_expanded_predictor.py", "exec")
    return source, {"arm": arm, "parent_sha256": _sha(original),
                    "algorithm_sha256": _sha(algorithm_source),
                    "expanded_sha256": _sha(source), "audit_enabled": audit,
                    "replacements": replacements}
