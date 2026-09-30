        secondary_unet_out, secondary_det_logits = secondary_model.encode(imgs)

            if secondary_detection_weight > 0.0:
                if cfg.det_tta:
                    _secondary_nv = 1
                    for dims in [(-1,), (-2,), (-2, -1)]:
                        secondary_imgs_flip = imgs.flip(dims)
                        _, secondary_det_flip = secondary_model.encode(secondary_imgs_flip)
                        for f in range(W):
                            secondary_det_logits[f] = (
                                secondary_det_logits[f] + secondary_det_flip[f].flip(dims)
                            )
                        del secondary_imgs_flip, secondary_det_flip
                        _secondary_nv += 1
                    for _k in (1, 3):
                        secondary_imgs_rot = torch.rot90(imgs, _k, dims=(-2, -1))
                        _, secondary_det_rot = secondary_model.encode(secondary_imgs_rot)
                        for f in range(W):
                            secondary_det_logits[f] = secondary_det_logits[f] + torch.rot90(
                                secondary_det_rot[f], -_k, dims=(-2, -1)
                            )
                        del secondary_imgs_rot, secondary_det_rot
                        _secondary_nv += 1
                    secondary_imgs_t = imgs.transpose(-1, -2)
                    _, secondary_det_t = secondary_model.encode(secondary_imgs_t)
                    for f in range(W):
                        secondary_det_logits[f] = (
                            secondary_det_logits[f] + secondary_det_t[f].transpose(-1, -2)
                        )
                    del secondary_imgs_t, secondary_det_t
                    _secondary_nv += 1
                    secondary_imgs_at = torch.rot90(
                        imgs, 1, dims=(-2, -1)
                    ).transpose(-1, -2)
                    _, secondary_det_at = secondary_model.encode(secondary_imgs_at)
                    for f in range(W):
                        secondary_det_logits[f] = secondary_det_logits[f] + torch.rot90(
                            secondary_det_at[f].transpose(-1, -2),
                            -1,
                            dims=(-2, -1),
                        )
                    del secondary_imgs_at, secondary_det_at
                    _secondary_nv += 1
                    for f in range(W):
                        secondary_det_logits[f] = secondary_det_logits[f] / _secondary_nv

                for f in range(W):