        secondary_unet_out, secondary_det_logits = secondary_model.encode(imgs)
            _secondary_edge_tta = os.environ.get(
                "BIOHUB_SECONDARY_EDGE_FEATURE_TTA", "0"
            ) != "0"
            _secondary_unet_acc = (
                secondary_unet_out.clone() if _secondary_edge_tta else None
            )

            if secondary_detection_weight > 0.0:
                if cfg.det_tta:
                    _secondary_nv = 1
                    for dims in [(-1,), (-2,), (-2, -1)]:
                        secondary_imgs_flip = imgs.flip(dims)
                        _secondary_u_flip, secondary_det_flip = secondary_model.encode(
                            secondary_imgs_flip
                        )
                        for f in range(W):
                            secondary_det_logits[f] = (
                                secondary_det_logits[f] + secondary_det_flip[f].flip(dims)
                            )
                        if _secondary_edge_tta:
                            _secondary_unet_acc = _secondary_unet_acc + _secondary_u_flip.flip(dims)
                        del secondary_imgs_flip, secondary_det_flip, _secondary_u_flip
                        _secondary_nv += 1
                    for _k in (1, 3):
                        secondary_imgs_rot = torch.rot90(imgs, _k, dims=(-2, -1))
                        _secondary_u_rot, secondary_det_rot = secondary_model.encode(
                            secondary_imgs_rot
                        )
                        for f in range(W):
                            secondary_det_logits[f] = secondary_det_logits[f] + torch.rot90(
                                secondary_det_rot[f], -_k, dims=(-2, -1)
                            )
                        if _secondary_edge_tta:
                            _secondary_unet_acc = _secondary_unet_acc + torch.rot90(
                                _secondary_u_rot, -_k, dims=(-2, -1)
                            )
                        del secondary_imgs_rot, secondary_det_rot, _secondary_u_rot
                        _secondary_nv += 1
                    secondary_imgs_t = imgs.transpose(-1, -2)
                    _secondary_u_t, secondary_det_t = secondary_model.encode(secondary_imgs_t)
                    for f in range(W):
                        secondary_det_logits[f] = (
                            secondary_det_logits[f] + secondary_det_t[f].transpose(-1, -2)
                        )
                    if _secondary_edge_tta:
                        _secondary_unet_acc = _secondary_unet_acc + _secondary_u_t.transpose(-1, -2)
                    del secondary_imgs_t, secondary_det_t, _secondary_u_t
                    _secondary_nv += 1
                    secondary_imgs_at = torch.rot90(
                        imgs, 1, dims=(-2, -1)
                    ).transpose(-1, -2)
                    _secondary_u_at, secondary_det_at = secondary_model.encode(
                        secondary_imgs_at
                    )
                    for f in range(W):
                        secondary_det_logits[f] = secondary_det_logits[f] + torch.rot90(
                            secondary_det_at[f].transpose(-1, -2),
                            -1,
                            dims=(-2, -1),
                        )
                    if _secondary_edge_tta:
                        _secondary_unet_acc = _secondary_unet_acc + torch.rot90(
                            _secondary_u_at.transpose(-1, -2), -1, dims=(-2, -1)
                        )
                    del secondary_imgs_at, secondary_det_at, _secondary_u_at
                    _secondary_nv += 1
                    for f in range(W):
                        secondary_det_logits[f] = secondary_det_logits[f] / _secondary_nv
                    if _secondary_edge_tta:
                        if _secondary_unet_acc.shape != secondary_unet_out.shape:
                            raise RuntimeError("SECONDARY_EDGE_TTA_SHAPE_MISMATCH")
                        _secondary_delta = float(
                            (_secondary_unet_acc / _secondary_nv - secondary_unet_out).abs().mean()
                        )
                        if _secondary_delta == 0.0:
                            raise RuntimeError("SECONDARY_EDGE_TTA_NO_OP")
                        _secondary_edge_tta_weight = float(os.environ.get(
                            "BIOHUB_SECONDARY_EDGE_FEATURE_TTA_WEIGHT", "1.0"
                        ))
                        if not 0.0 < _secondary_edge_tta_weight <= 1.0:
                            raise RuntimeError("SECONDARY_EDGE_TTA_BAD_WEIGHT")
                        _secondary_tta_mean = _secondary_unet_acc / _secondary_nv
                        secondary_unet_out = (
                            (1.0 - _secondary_edge_tta_weight) * secondary_unet_out
                            + _secondary_edge_tta_weight * _secondary_tta_mean
                        )
                        print(
                            "SECONDARY_EDGE_TTA_ACTIVE views=",
                            _secondary_nv,
                            "weight=",
                            _secondary_edge_tta_weight,
                            "mean_abs_feat_delta=",
                            round(_secondary_delta, 6),
                            flush=True,
                        )
                        del _secondary_unet_acc

                for f in range(W):