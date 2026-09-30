# Final run evidence: trained weights and the actual chosen postprocess.
_division_stats = pd.read_csv(RUN_STATS_PATH)
_division_totals = {k: int(_division_stats[k].fillna(0).sum()) for k in _division_stats.columns
                    if k.startswith("learned_division_") or k == "safe_divisions_added"}
if _division_totals.get("learned_division_scored", 0) <= 0:
    raise RuntimeError("TRAINED_GATE_NOT_INVOKED_ON_TEST_PREDICTIONS")
_division_audit = {
    "task_id": "DIVISION_TRAIN_20260914", "training_completed": True,
    "weights_sha256": DIVISION_MODULE.digest(WORKING_DIR / "division_gate_weights.json"),
    "training_receipt_sha256": DIVISION_MODULE.digest(WORKING_DIR / "division_training_receipt.json"),
    "module_sha256": __import__("hashlib").sha256(DIVISION_SOURCE.encode()).hexdigest(),
    "selected_label": selected_label, "selected_config": selected_config,
    "counts": _division_totals, "source_models_retrained": False,
    "formal_score": None, "score_read": False,
    "submission_sha256": DIVISION_MODULE.digest(SUBMISSION_PATH),
}
(WORKING_DIR / "division_runtime_audit.json").write_text(json.dumps(_division_audit, indent=2)+"\n")
print("DIVISION_RUNTIME_AUDIT", json.dumps(_division_audit), flush=True)
