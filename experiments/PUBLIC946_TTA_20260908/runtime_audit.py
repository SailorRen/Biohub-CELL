"""Common read-only GPU smoke and actual-call evidence for PUBLIC946 arms.

The first available nonempty association within the first three windows of each video is diagnosed using feature
maps already computed by its existing eight encodes. A diagnostic edge-head
call is read-only and never replaces returned production logits. No extra
encoder calls, gradients, precision changes, seeds, thresholds or weights.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

import torch

_VIDEOS = {}


def _sync(device):
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def _tensor_info(value, full_finite=False):
    result = {"shape": list(value.shape), "dtype": str(value.dtype),
              "device": str(value.device), "stride": list(value.stride()),
              "numel": value.numel()}
    if full_finite:
        result["all_finite"] = bool(torch.isfinite(value).all().item())
        if not result["all_finite"]:
            raise RuntimeError("PUBLIC946 runtime audit found nonfinite consumed features")
    return result


def _delta(a, b):
    if a.shape != b.shape or a.dtype != b.dtype or a.device != b.device:
        raise RuntimeError("PUBLIC946 feature comparison grid/precision/device mismatch")
    step = max(1, a.numel() // 65536)
    x = a.detach().reshape(-1)[::step][:65536].float()
    y = b.detach().reshape(-1)[::step][:65536].float()
    d = (x - y).abs()
    return {"sample_elements": d.numel(), "sample_stride": step,
            "sample_mean_abs_delta": float(d.mean().item()) if d.numel() else None,
            "sample_max_abs_delta": float(d.max().item()) if d.numel() else None,
            "sample_equal": bool(torch.equal(x, y))}


def _sample_signature(value):
    step = max(1, value.numel() // 65536)
    sample = value.detach().reshape(-1)[::step][:65536].float().cpu().numpy()
    return hashlib.sha256(sample.tobytes()).hexdigest()


def begin_window(ds_path, frame_indices, imgs):
    key = str(ds_path)
    video = _VIDEOS.setdefault(key, {"windows": 0, "association_recorded": False})
    video["windows"] += 1
    detailed = not video["association_recorded"] and video["windows"] <= 3
    if detailed:
        _sync(imgs.device)
    return {"dataset": ds_path.stem, "input_parent": str(ds_path.parent),
            "window_index": video["windows"],
            "frames": [int(x) for x in frame_indices],
            "counts": {"primary": 0, "secondary": 0},
            "details": detailed, "video": video, "device": imgs.device,
            "started": time.perf_counter(), "encode_seconds": {},
            "input": _tensor_info(imgs, detailed), "encode_views": [],
            "base_features": {}, "base_signatures": {}, "association_count": 0}


def encode(context, role, model, imgs):
    context["counts"][role] += 1
    if context["details"]:
        _sync(imgs.device)
    started = time.perf_counter()
    features, heatmaps = model.encode(imgs)
    if context["details"]:
        _sync(imgs.device)
        context["encode_seconds"][role] = context["encode_seconds"].get(role, 0.0) + time.perf_counter() - started
        context["encode_views"].append({"role": role,
            "pass": context["counts"][role], "input": _tensor_info(imgs),
            "feature": _tensor_info(features),
            "heatmap0": _tensor_info(heatmaps[0])})
        if context["counts"][role] == 1:
            # Reference only. C2's accumulator is an independent clone and
            # cannot mutate this original feature tensor.
            context["base_features"][role] = features
            context["base_signatures"][role] = _sample_signature(features)
    return features, heatmaps


def after_encodes(context, primary, secondary, link_mode, edge_weight, detection_weight, heatmaps):
    if context["counts"] != {"primary": 8, "secondary": 8}:
        raise RuntimeError({"PUBLIC946_encode_call_drift": context["counts"]})
    if link_mode != "low_margin_consensus" or edge_weight != 0.15 or detection_weight != 0.80:
        raise RuntimeError("PUBLIC946 association/detection mixture configuration drift")
    context["config"] = {"secondary_link_mode": link_mode,
        "secondary_edge_weight": edge_weight, "secondary_detection_weight": detection_weight}
    if context["details"]:
        context["consumed_features"] = {}
        for role, value in (("primary", primary), ("secondary", secondary)):
            base = context["base_features"][role]
            unchanged = _sample_signature(base) == context["base_signatures"][role]
            if not unchanged:
                raise RuntimeError("PUBLIC946 TTA accumulator mutated original encoded features")
            context["consumed_features"][role] = {
                "original_encoded_feature_sample_unchanged": unchanged,
                **_tensor_info(value, True), "single_pass": _tensor_info(base),
                "delta_vs_single_pass": _delta(value, base),
                "same_storage_as_original": value.data_ptr() == base.data_ptr()}
        context["base_features"].pop("primary", None)
        context["consumed_heatmaps"] = [_tensor_info(x, True) for x in heatmaps]
        context["secondary_consumed_ptr"] = secondary.data_ptr()


def association(context, model, f_idx, consumed, feat_src, feat_tgt, logits,
                coords_src, coords_tgt, mask_src, mask_tgt, ds_arr,
                pos_src, pos_tgt, primary_src, primary_tgt, primary_logits):
    context["association_count"] += 1
    if not context["details"] or context.get("association") is not None:
        return
    if consumed.data_ptr() != context["secondary_consumed_ptr"]:
        raise RuntimeError("PUBLIC946 TTA feature was not passed to actual association")
    if model.training:
        raise RuntimeError("PUBLIC946 diagnostic requires the unchanged eval model")
    base = context["base_features"]["secondary"]
    devices = [consumed.device.index or 0] if consumed.is_cuda else []
    _sync(consumed.device)
    start = time.perf_counter()
    with torch.no_grad(), torch.random.fork_rng(devices=devices):
        base_src = model._index_features(base[:, f_idx], coords_src, mask_src)
        base_tgt = model._index_features(base[:, f_idx + 1], coords_tgt, mask_tgt)
        baseline_logits = model.predict_edges(base_src, base_tgt,
            coords_src * ds_arr, coords_tgt * ds_arr,
            pos_src, pos_tgt, mask_src, mask_tgt)
        actual_probs = torch.softmax(logits.float(), dim=1)
        base_probs = torch.softmax(baseline_logits.float(), dim=1)
        result = {
            "frame_pair_index": int(f_idx), "production_calls": context["association_count"],
            "actual_secondary_feature_consumed": True,
            "source_sampled_features": _tensor_info(feat_src, True),
            "target_sampled_features": _tensor_info(feat_tgt, True),
            "source_delta_vs_single_pass": _delta(feat_src, base_src),
            "target_delta_vs_single_pass": _delta(feat_tgt, base_tgt),
            "actual_secondary_logits": _tensor_info(logits, True),
            "probability_delta_vs_single_pass_same_coordinates": _delta(actual_probs, base_probs),
            "probability_comparison_stage": "secondary edge-head softmax over parents, before original calibration and low-margin mixing",
            "primary_source_sampled_features": _tensor_info(primary_src, True),
            "primary_target_sampled_features": _tensor_info(primary_tgt, True),
            "actual_primary_logits_after_original_harmonic_fusion": _tensor_info(primary_logits, True),
            "coordinate_grid": {"source": _tensor_info(coords_src),
                                "target": _tensor_info(coords_tgt),
                                "downsample": ds_arr.detach().cpu().tolist()},
            "diagnostic_encoder_calls": 0,
            "diagnostic_edge_head_calls": 1,
            "diagnostic_probabilities_used_in_production": False,
            "same_low_margin_config": dict(context["config"]),
        }
    _sync(consumed.device)
    result["diagnostic_seconds"] = time.perf_counter() - start
    context["association"] = result
    context["video"]["association_recorded"] = True
    # Release the retained base features immediately after the only paired
    # diagnostic; no eight-feature cache and no cross-window feature retention.
    context["base_features"].clear()


def end_window(context):
    _sync(context["device"])
    record = {"arm": os.environ["BIOHUB_PUBLIC946_ARM"],
        "event": "actual_predictor_window", "dataset": context["dataset"],
        "input_parent": context["input_parent"], "frames": context["frames"],
        "window_index": context["window_index"], "encode_calls": context["counts"],
        "association_calls": context["association_count"],
        "seconds_including_common_audit": time.perf_counter() - context["started"],
        "input": context["input"], "config": context["config"],
        "cuda_peak_allocated_bytes_process": torch.cuda.max_memory_allocated(context["device"]) if context["device"].type == "cuda" else None,
        "cuda_peak_reserved_bytes_process": torch.cuda.max_memory_reserved(context["device"]) if context["device"].type == "cuda" else None}
    if context["details"]:
        record.update({"worker_execution_settings": {
                "torch_version": str(torch.__version__),
                "cuda_runtime": torch.version.cuda,
                "torch_initial_seed": torch.initial_seed(),
                "default_dtype": str(torch.get_default_dtype()),
                "grad_enabled": torch.is_grad_enabled(),
                "autocast_enabled": torch.is_autocast_enabled(),
                "cudnn_benchmark": torch.backends.cudnn.benchmark,
                "cudnn_deterministic": torch.backends.cudnn.deterministic,
                "cudnn_allow_tf32": torch.backends.cudnn.allow_tf32,
                "matmul_allow_tf32": torch.backends.cuda.matmul.allow_tf32,
                "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
                "float32_matmul_precision": torch.get_float32_matmul_precision(),
                "gpu_name": torch.cuda.get_device_name(context["device"]) if context["device"].type == "cuda" else None,
            }, "encode_views": context["encode_views"],
            "encode_seconds": context["encode_seconds"],
            "consumed_features": context.get("consumed_features"),
            "consumed_heatmaps": context.get("consumed_heatmaps"),
            "association": context.get("association")})
    destination = Path("/kaggle/working") / f"public946_runtime_{os.getpid()}.jsonl"
    with destination.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
    if context["details"]:
        print("PUBLIC946_GPU_SMOKE " + json.dumps(record, sort_keys=True, allow_nan=False), flush=True)
    context["base_features"].clear()
