#!/usr/bin/env python3
"""Deterministic verifier for the fixed V19C ScriptVersion optimization audit."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote


TASK_ID = "CODEX_20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_SYNC_V01"
SCRIPT_VERSION_ID = 346969653
RESEARCH_REL = Path("research/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_V01")
SUMMARY_REL = RESEARCH_REL / "audit_summary.json"
VERIFY_REL = Path("reports/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_VERIFY.json")
REPORT_REL = Path("reports/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_REPORT_V01.md")
LEDGER_REL = Path("governance/CODEX_20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_LEDGER.json")

REQUIRED_FILES = [
    Path("tasks/CODEX_20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_SYNC_TASK.md"),
    Path("tasks/CODEX_20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_SYNC_CONTRACT.json"),
    RESEARCH_REL / "00_source_manifest.jsonl",
    RESEARCH_REL / "01_version_identity_and_lineage.md",
    RESEARCH_REL / "02_source_cell_audit.csv",
    RESEARCH_REL / "03_runtime_log_inventory.csv",
    RESEARCH_REL / "04_runtime_and_artifact_analysis.md",
    RESEARCH_REL / "05_optimization_opportunities.csv",
    RESEARCH_REL / "06_prioritized_optimization_plan.md",
    RESEARCH_REL / "07_risks_and_unknowns.md",
    RESEARCH_REL / "evidence/kernel_version_metadata.json",
    RESEARCH_REL / "evidence/runtime_log_sanitized.log",
    SUMMARY_REL,
    LEDGER_REL,
    REPORT_REL,
    Path("scripts/verify_v19c_sv346969653_optimization_audit.py"),
]

REMOTE_READBACK_FILES = [*REQUIRED_FILES, VERIFY_REL]

MANIFEST_FIELDS = {
    "source_id", "source_type", "platform", "title", "owner", "url_or_ref",
    "version_number", "script_version_id", "submission_id", "read_status",
    "access_time_utc", "access_time_asia_shanghai", "bytes_observed", "sha256",
    "evidence_path", "license", "factual_use_allowed", "notes",
}
REQUIRED_SOURCE_IDS = {
    "SV346969653_VERSION_METADATA",
    "SV346969653_NOTEBOOK_SOURCE",
    "SV346969653_RUNTIME_LOG",
    "SV346969653_OUTPUT_INVENTORY",
}
ALLOWED_MANIFEST_STATUSES = {
    "FULL_NOTEBOOK_SOURCE_READ", "FULL_LOG_READ", "FULL_OUTPUT_INVENTORY_READ",
    "METADATA_ONLY", "SUBMISSION_RECORD_READ", "PARTIAL", "BLOCKED", "UNKNOWN",
}
ALLOWED_EVIDENCE_CLASSES = {
    "SOURCE_CODE_VERIFIED", "MEASURED", "INFERENCE", "UNKNOWN",
}
ALLOWED_DECISIONS = {
    "OPTIMIZATION_FEASIBLE_WITH_GATES",
    "INSUFFICIENT_EVIDENCE_FOR_OPTIMIZATION",
    "OPTIMIZATION_NOT_RECOMMENDED",
}
SHA256_RE = re.compile(r"[0-9a-f]{64}")
SECRET_PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "kaggle_key_assignment": re.compile(r"KAGGLE_KEY\s*[=:]\s*['\"]?[A-Za-z0-9_-]{16,}"),
    "bearer_token": re.compile(r"Authorization\s*:\s*Bearer\s+[A-Za-z0-9._-]{16,}", re.I),
    "signed_url": re.compile(r"(?:X-Goog-Signature|X-Amz-Signature)=", re.I),
}
PROHIBITED_SUFFIXES = {".ipynb", ".zarr", ".geff", ".pt", ".pth", ".ckpt", ".onnx"}
PROHIBITED_NAMES = {"submission.csv", "kaggle.json"}


@dataclass
class Check:
    check_id: str
    status: str
    details: dict[str, Any]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def check_required_files(root: Path) -> Check:
    missing = [p.as_posix() for p in REQUIRED_FILES if not (root / p).is_file()]
    empty = [p.as_posix() for p in REQUIRED_FILES if (root / p).is_file() and (root / p).stat().st_size == 0]
    status = "PASS" if not missing and not empty else "FAIL"
    return Check("required_files_present_nonempty", status, {"missing": missing, "empty": empty})


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    if not path.is_file():
        return rows, ["file_missing"]
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line_{line_number}:{exc.msg}")
            continue
        if not isinstance(row, dict):
            errors.append(f"line_{line_number}:not_object")
            continue
        rows.append(row)
    return rows, errors


def check_manifest(root: Path) -> Check:
    rows, errors = load_jsonl(root / RESEARCH_REL / "00_source_manifest.jsonl")
    ids: list[str] = []
    for index, row in enumerate(rows, 1):
        missing = sorted(MANIFEST_FIELDS - set(row))
        if missing:
            errors.append(f"row_{index}:missing={','.join(missing)}")
        source_id = str(row.get("source_id", ""))
        ids.append(source_id)
        if row.get("read_status") not in ALLOWED_MANIFEST_STATUSES:
            errors.append(f"{source_id}:bad_read_status")
        evidence = str(row.get("evidence_path", ""))
        if evidence and not (root / evidence).is_file():
            errors.append(f"{source_id}:missing_evidence")
        if row.get("read_status") in {"FULL_NOTEBOOK_SOURCE_READ", "FULL_LOG_READ"}:
            if not isinstance(row.get("bytes_observed"), int) or row["bytes_observed"] <= 0:
                errors.append(f"{source_id}:missing_bytes")
            if not SHA256_RE.fullmatch(str(row.get("sha256", ""))):
                errors.append(f"{source_id}:missing_sha256")
    duplicates = sorted({source_id for source_id in ids if ids.count(source_id) > 1})
    missing_required = sorted(REQUIRED_SOURCE_IDS - set(ids))
    if duplicates:
        errors.append(f"duplicate_ids={duplicates}")
    if missing_required:
        errors.append(f"missing_required={missing_required}")
    return Check("source_manifest_complete", "PASS" if not errors else "FAIL", {"records": len(rows), "errors": errors})


def check_cells(root: Path) -> Check:
    path = root / RESEARCH_REL / "02_source_cell_audit.csv"
    required = {
        "script_version_id", "cell_index", "cell_type", "source_bytes", "source_sha256",
        "checked", "ast_parse", "method_tags", "optimization_signals", "notes",
    }
    errors: list[str] = []
    rows: list[dict[str, str]] = []
    if path.is_file():
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            if not required.issubset(set(reader.fieldnames or [])):
                errors.append("missing_columns")
            rows = list(reader)
    else:
        errors.append("file_missing")
    code_rows = [row for row in rows if row.get("cell_type") == "code"]
    for row in rows:
        if row.get("script_version_id") != str(SCRIPT_VERSION_ID):
            errors.append(f"wrong_script_version:{row.get('cell_index')}")
        if row.get("checked", "").lower() != "true":
            errors.append(f"unchecked:{row.get('cell_index')}")
        if not SHA256_RE.fullmatch(row.get("source_sha256", "")):
            errors.append(f"bad_sha:{row.get('cell_index')}")
    for row in code_rows:
        if row.get("ast_parse") != "PASS":
            errors.append(f"ast_not_pass:{row.get('cell_index')}")
    if not rows or not code_rows:
        errors.append("missing_rows_or_code")
    return Check("all_source_cells_audited", "PASS" if not errors else "FAIL", {"rows": len(rows), "code_cells": len(code_rows), "errors": errors})


def check_runtime_log(root: Path) -> Check:
    inventory = root / RESEARCH_REL / "03_runtime_log_inventory.csv"
    required = {
        "artifact_name", "artifact_type", "bytes", "sha256", "read_status",
        "record_count", "error_count", "warning_count", "evidence_path", "notes",
    }
    errors: list[str] = []
    rows: list[dict[str, str]] = []
    if inventory.is_file():
        with inventory.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            if not required.issubset(set(reader.fieldnames or [])):
                errors.append("missing_columns")
            rows = list(reader)
    else:
        errors.append("file_missing")
    full_logs = [row for row in rows if row.get("read_status") == "FULL_LOG_READ"]
    if len(full_logs) != 1:
        errors.append(f"full_log_count={len(full_logs)}")
    for row in full_logs:
        evidence = root / row.get("evidence_path", "")
        expected = root / RESEARCH_REL / "evidence/runtime_log_sanitized.log"
        if evidence != expected or not evidence.is_file():
            errors.append("unexpected_or_missing_log_evidence")
            continue
        if str(evidence.stat().st_size) != row.get("bytes") or sha256_file(evidence) != row.get("sha256"):
            errors.append("runtime_log_digest_mismatch")
        try:
            if int(row.get("record_count", "0")) <= 0:
                errors.append("empty_runtime_log")
        except ValueError:
            errors.append("bad_record_count")
    return Check("runtime_log_fully_read", "PASS" if not errors else "FAIL", {"records": len(rows), "full_logs": len(full_logs), "errors": errors})


def check_opportunities(root: Path) -> Check:
    path = root / RESEARCH_REL / "05_optimization_opportunities.csv"
    required = {
        "rank", "candidate_id", "stage", "observed_bottleneck", "proposed_change",
        "evidence_class", "expected_direction", "validation_gate", "risk",
        "stop_condition", "status",
    }
    errors: list[str] = []
    rows: list[dict[str, str]] = []
    if path.is_file():
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            if not required.issubset(set(reader.fieldnames or [])):
                errors.append("missing_columns")
            rows = list(reader)
    else:
        errors.append("file_missing")
    ids: list[str] = []
    ranks: list[int] = []
    for row in rows:
        candidate_id = row.get("candidate_id", "")
        ids.append(candidate_id)
        try:
            ranks.append(int(row.get("rank", "")))
        except ValueError:
            errors.append(f"bad_rank:{candidate_id}")
        if row.get("evidence_class") not in ALLOWED_EVIDENCE_CLASSES:
            errors.append(f"bad_evidence_class:{candidate_id}")
        if row.get("status") != "CANDIDATE_NOT_EXECUTED":
            errors.append(f"bad_status:{candidate_id}")
        for field in ["observed_bottleneck", "proposed_change", "validation_gate", "risk", "stop_condition"]:
            if not row.get(field, "").strip():
                errors.append(f"empty_{field}:{candidate_id}")
    if len(rows) < 3:
        errors.append("fewer_than_three_candidates")
    if len(set(ids)) != len(ids):
        errors.append("duplicate_candidate_id")
    if ranks and sorted(ranks) != list(range(1, len(ranks) + 1)):
        errors.append("ranks_not_contiguous")
    return Check("optimization_candidates_actionable", "PASS" if not errors else "FAIL", {"candidates": len(rows), "errors": errors})


def check_summary(root: Path) -> Check:
    try:
        data = read_json(root / SUMMARY_REL)
    except Exception as exc:
        return Check("audit_summary_semantics", "FAIL", {"errors": [f"read_error:{type(exc).__name__}"]})
    errors: list[str] = []
    expected = {
        ("status",): "PASS",
        ("target", "notebook_ref"): "sailorren/biohub-v19c-public0939-sis14-only",
        ("target", "script_version_id"): SCRIPT_VERSION_ID,
        ("source_audit", "all_cells_checked"): True,
        ("runtime_log", "read_status"): "FULL_LOG_READ",
        ("optimization", "experiment_executed"): False,
        ("redistribution", "full_notebook_source_committed"): False,
    }
    for pointer, expected_value in expected.items():
        current: Any = data
        for key in pointer:
            current = current.get(key) if isinstance(current, dict) else None
        if current != expected_value:
            errors.append(f"{'/'.join(pointer)}={current!r}")
    decision = data.get("optimization", {}).get("decision")
    if decision not in ALLOWED_DECISIONS:
        errors.append(f"bad_decision={decision!r}")
    if not str(data.get("optimization", {}).get("top_candidate_id", "")).strip():
        errors.append("top_candidate_id_empty")
    if int(data.get("source_audit", {}).get("code_cells", 0) or 0) <= 0:
        errors.append("code_cells_missing")
    if int(data.get("runtime_log", {}).get("bytes", 0) or 0) <= 0:
        errors.append("runtime_log_bytes_missing")
    return Check("audit_summary_semantics", "PASS" if not errors else "FAIL", {"errors": errors})


def check_zero_writes(root: Path) -> Check:
    try:
        data = read_json(root / LEDGER_REL)
    except Exception as exc:
        return Check("forbidden_external_actions_zero", "FAIL", {"errors": [f"read_error:{type(exc).__name__}"]})
    fields = [
        "kaggle_submission_create_count", "kaggle_notebook_write_count", "training_task_count",
        "kaggle_dataset_create_count", "kaggle_model_create_count",
        "competition_join_or_rule_accept_count", "large_dataset_download_count",
    ]
    errors = [f"{field}={data.get(field)!r}" for field in fields if data.get(field) != 0]
    return Check("forbidden_external_actions_zero", "PASS" if not errors else "FAIL", {"fields": fields, "errors": errors})


def check_safety(root: Path) -> Check:
    errors: list[str] = []
    for base in [root / RESEARCH_REL, root / "reports", root / "tasks", root / "governance"]:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or ".task-verification" in path.parts:
                continue
            rel = path.relative_to(root).as_posix()
            lower = path.name.lower()
            if path.stat().st_size > 20 * 1024 * 1024:
                errors.append(f"oversized:{rel}")
            if lower in PROHIBITED_NAMES or any(lower.endswith(suffix) for suffix in PROHIBITED_SUFFIXES):
                errors.append(f"prohibited:{rel}")
            if path.stat().st_size <= 5 * 1024 * 1024:
                text = path.read_text(encoding="utf-8", errors="ignore")
                for name, pattern in SECRET_PATTERNS.items():
                    if pattern.search(text):
                        errors.append(f"secret_pattern:{name}:{rel}")
    return Check("no_large_prohibited_or_secret_artifacts", "PASS" if not errors else "FAIL", {"errors": errors})


def check_reports(root: Path) -> Check:
    required_tokens = {
        RESEARCH_REL / "01_version_identity_and_lineage.md": ["346969653", "版本身份", "UNKNOWN"],
        RESEARCH_REL / "04_runtime_and_artifact_analysis.md": ["完整日志", "MEASURED", "错误"],
        RESEARCH_REL / "06_prioritized_optimization_plan.md": ["优先级", "验证计划", "CANDIDATE_NOT_EXECUTED"],
        RESEARCH_REL / "07_risks_and_unknowns.md": ["UNKNOWN", "未执行"],
        REPORT_REL: ["结论", "版本身份", "源码结构", "运行日志", "优化判断", "优先级", "验证计划", "局限", "SOURCE_CODE_VERIFIED", "MEASURED", "INFERENCE", "UNKNOWN"],
    }
    errors: list[str] = []
    for rel, tokens in required_tokens.items():
        path = root / rel
        if not path.is_file():
            errors.append(f"missing:{rel}")
            continue
        text = path.read_text(encoding="utf-8")
        for token in tokens:
            if token not in text:
                errors.append(f"missing_token:{rel}:{token}")
    return Check("reports_have_required_evidence_sections", "PASS" if not errors else "FAIL", {"errors": errors})


def run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)


def check_remote(root: Path) -> Check:
    errors: list[dict[str, str]] = []
    local_proc = run_git(root, ["rev-parse", "HEAD"])
    remote_proc = run_git(root, ["ls-remote", "origin", "refs/heads/main"])
    local_head = local_proc.stdout.decode().strip() if local_proc.returncode == 0 else ""
    remote_line = remote_proc.stdout.decode().strip() if remote_proc.returncode == 0 else ""
    remote_head = remote_line.split()[0] if remote_line else ""
    if not local_head or local_head != remote_head:
        errors.append({"path": "refs/heads/main", "reason": "head_mismatch_or_read_failed"})
    matches = 0
    if not errors:
        for rel in REMOTE_READBACK_FILES:
            local = root / rel
            if not local.is_file():
                errors.append({"path": rel.as_posix(), "reason": "local_missing"})
                continue
            api_path = quote(rel.as_posix(), safe="/")
            proc = subprocess.run(
                ["gh", "api", "-H", "Accept: application/vnd.github.raw+json", f"repos/SailorRen/Biohub-CELL/contents/{api_path}?ref={remote_head}"],
                cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120,
            )
            if proc.returncode:
                errors.append({"path": rel.as_posix(), "reason": "remote_fetch_failed"})
            elif sha256_bytes(proc.stdout) != sha256_file(local):
                errors.append({"path": rel.as_posix(), "reason": "sha256_mismatch"})
            else:
                matches += 1
    return Check("github_authoritative_remote_readback", "PASS" if not errors else "FAIL", {"local_head": local_head, "remote_head": remote_head, "matched": matches, "expected": len(REMOTE_READBACK_FILES), "errors": errors})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--remote-readback", action="store_true")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    checks = [
        check_required_files(root),
        check_manifest(root),
        check_cells(root),
        check_runtime_log(root),
        check_opportunities(root),
        check_summary(root),
        check_zero_writes(root),
        check_safety(root),
        check_reports(root),
    ]
    if args.remote_readback:
        checks.append(check_remote(root))
    passed = sum(check.status == "PASS" for check in checks)
    failed = len(checks) - passed
    report = {
        "schema_version": "1.0",
        "task_id": TASK_ID,
        "status": "PASS" if failed == 0 else "FAIL",
        "summary": {"passed": passed, "failed": failed, "total": len(checks)},
        "checks": [asdict(check) for check in checks],
    }
    if not args.verify_only:
        target = root / VERIFY_REL
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if failed:
        print("V19C_SV346969653_OPTIMIZATION_VERIFICATION_FAIL")
        return 1
    print("V19C_SV346969653_LOCAL_AUDIT_PASS")
    if args.remote_readback:
        print("V19C_SV346969653_REMOTE_READBACK_PASS")
    print("V19C_SV346969653_OPTIMIZATION_VERIFICATION_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
