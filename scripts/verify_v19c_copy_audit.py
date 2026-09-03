#!/usr/bin/env python3
"""Deterministic verifier for the 2026-09-04 V19C copy/source/log audit."""

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


TASK_ID = "CODEX_20260904_BIOHUB_V19C_COPY_AUDIT_SYNC_V01"
RESEARCH_REL = Path("research/20260904_BIOHUB_V19C_COPY_AUDIT_V01")
VERIFY_REL = Path("reports/20260904_BIOHUB_V19C_COPY_AUDIT_VERIFY.json")
SUMMARY_REL = RESEARCH_REL / "audit_summary.json"
LEDGER_REL = Path("governance/CODEX_20260904_BIOHUB_V19C_COPY_AUDIT_LEDGER.json")

REQUIRED_FILES = [
    Path("tasks/CODEX_20260904_BIOHUB_V19C_COPY_AUDIT_SYNC_TASK.md"),
    Path("tasks/CODEX_20260904_BIOHUB_V19C_COPY_AUDIT_SYNC_CONTRACT.json"),
    RESEARCH_REL / "00_source_manifest.jsonl",
    RESEARCH_REL / "01_notebook_identity_and_lineage.md",
    RESEARCH_REL / "02_notebook_cell_audit.csv",
    RESEARCH_REL / "03_method_analysis.md",
    RESEARCH_REL / "04_runtime_log_inventory.csv",
    RESEARCH_REL / "05_runtime_log_analysis.md",
    RESEARCH_REL / "06_submission_score_binding.md",
    RESEARCH_REL / "07_failures_and_unknowns.md",
    RESEARCH_REL / "evidence/user_screenshot_observation.json",
    RESEARCH_REL / "evidence/kaggle_kernel_metadata.json",
    RESEARCH_REL / "evidence/runtime_log_sanitized.log",
    SUMMARY_REL,
    LEDGER_REL,
    Path("reports/20260904_BIOHUB_V19C_COPY_AUDIT_REPORT_V01.md"),
    Path("scripts/verify_v19c_copy_audit.py"),
]

REMOTE_READBACK_FILES = [
    Path("tasks/CODEX_20260904_BIOHUB_V19C_COPY_AUDIT_SYNC_TASK.md"),
    Path("tasks/CODEX_20260904_BIOHUB_V19C_COPY_AUDIT_SYNC_CONTRACT.json"),
    RESEARCH_REL / "00_source_manifest.jsonl",
    RESEARCH_REL / "01_notebook_identity_and_lineage.md",
    RESEARCH_REL / "02_notebook_cell_audit.csv",
    RESEARCH_REL / "03_method_analysis.md",
    RESEARCH_REL / "04_runtime_log_inventory.csv",
    RESEARCH_REL / "05_runtime_log_analysis.md",
    RESEARCH_REL / "06_submission_score_binding.md",
    RESEARCH_REL / "07_failures_and_unknowns.md",
    RESEARCH_REL / "evidence/user_screenshot_observation.json",
    RESEARCH_REL / "evidence/kaggle_kernel_metadata.json",
    RESEARCH_REL / "evidence/runtime_log_sanitized.log",
    SUMMARY_REL,
    LEDGER_REL,
    Path("reports/20260904_BIOHUB_V19C_COPY_AUDIT_REPORT_V01.md"),
    VERIFY_REL,
    Path("scripts/verify_v19c_copy_audit.py"),
]

MANIFEST_FIELDS = {
    "source_id", "source_type", "platform", "title", "owner", "url_or_ref",
    "version_number", "script_version_id", "submission_id", "read_status",
    "access_time_utc", "access_time_asia_shanghai", "bytes_observed", "sha256",
    "evidence_path", "license", "factual_use_allowed", "notes",
}
REQUIRED_SOURCE_IDS = {
    "V19C_USER_SCREENSHOT",
    "V19C_PUBLIC_ORIGINAL_SOURCE",
    "V19C_USER_COPY_SOURCE",
    "V19C_USER_COPY_RUNTIME_LOG",
    "V19C_SUBMISSION_SCORE_RECORD",
}
ALLOWED_READ_STATUSES = {
    "USER_PROVIDED_SCREENSHOT_READ", "FULL_NOTEBOOK_SOURCE_READ", "FULL_LOG_READ",
    "SUBMISSION_RECORD_READ", "METADATA_ONLY", "PARTIAL", "BLOCKED", "UNKNOWN",
}
SHA256_RE = re.compile(r"[0-9a-f]{64}")
SECRET_PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "kaggle_key_assignment": re.compile(r"KAGGLE_KEY\s*[=:]\s*['\"]?[A-Za-z0-9_-]{16,}"),
    "bearer_token": re.compile(r"Authorization\s*:\s*Bearer\s+[A-Za-z0-9._-]{16,}", re.I),
    "signed_url": re.compile(r"(?:X-Goog-Signature|X-Amz-Signature)=", re.I),
}
PROHIBITED_SUFFIXES = {".zarr", ".geff", ".pt", ".pth", ".ckpt", ".onnx"}
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
    return Check("required_files_present_nonempty", "PASS" if not missing and not empty else "FAIL", {"missing": missing, "empty": empty})


def load_manifest(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    if not path.is_file():
        return rows, ["manifest_missing"]
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line_{number}:{exc.msg}")
            continue
        if not isinstance(row, dict):
            errors.append(f"line_{number}:not_object")
            continue
        rows.append(row)
    return rows, errors


def check_manifest(root: Path) -> Check:
    rows, errors = load_manifest(root / RESEARCH_REL / "00_source_manifest.jsonl")
    ids: list[str] = []
    for i, row in enumerate(rows, 1):
        missing = sorted(MANIFEST_FIELDS - set(row))
        if missing:
            errors.append(f"row_{i}:missing_fields={','.join(missing)}")
        sid = str(row.get("source_id", ""))
        ids.append(sid)
        if row.get("read_status") not in ALLOWED_READ_STATUSES:
            errors.append(f"{sid}:bad_read_status")
        evidence = str(row.get("evidence_path", ""))
        if evidence and not (root / evidence).is_file():
            errors.append(f"{sid}:missing_evidence")
        if row.get("read_status") in {"FULL_NOTEBOOK_SOURCE_READ", "FULL_LOG_READ"}:
            if not isinstance(row.get("bytes_observed"), int) or row["bytes_observed"] <= 0:
                errors.append(f"{sid}:missing_bytes")
            if not SHA256_RE.fullmatch(str(row.get("sha256", ""))):
                errors.append(f"{sid}:missing_sha256")
    duplicate_ids = sorted({sid for sid in ids if ids.count(sid) > 1})
    missing_required = sorted(REQUIRED_SOURCE_IDS - set(ids))
    if duplicate_ids:
        errors.append(f"duplicate_ids={duplicate_ids}")
    if missing_required:
        errors.append(f"missing_required_ids={missing_required}")
    return Check("source_manifest_complete", "PASS" if not errors else "FAIL", {"records": len(rows), "errors": errors})


def check_cell_audit(root: Path) -> Check:
    path = root / RESEARCH_REL / "02_notebook_cell_audit.csv"
    errors: list[str] = []
    rows: list[dict[str, str]] = []
    required = {"notebook_role", "cell_index", "cell_type", "source_bytes", "source_sha256", "checked", "matches_public_cell", "method_tags", "notes"}
    if path.is_file():
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            if not required.issubset(set(reader.fieldnames or [])):
                errors.append("missing_columns")
            rows = list(reader)
    else:
        errors.append("missing_file")
    copy_rows = [r for r in rows if r.get("notebook_role") == "USER_COPY"]
    code_rows = [r for r in copy_rows if r.get("cell_type") == "code"]
    if not copy_rows or not code_rows:
        errors.append("missing_copy_or_code_rows")
    for r in copy_rows:
        if r.get("checked", "").lower() != "true":
            errors.append(f"unchecked_cell:{r.get('cell_index')}")
        if not SHA256_RE.fullmatch(r.get("source_sha256", "")):
            errors.append(f"bad_sha:{r.get('cell_index')}")
    return Check("all_copy_cells_audited", "PASS" if not errors else "FAIL", {"rows": len(rows), "copy_cells": len(copy_rows), "copy_code_cells": len(code_rows), "errors": errors})


def check_logs(root: Path) -> Check:
    inventory = root / RESEARCH_REL / "04_runtime_log_inventory.csv"
    errors: list[str] = []
    rows: list[dict[str, str]] = []
    required = {"artifact_name", "artifact_type", "bytes", "sha256", "read_status", "line_count", "error_count", "warning_count", "evidence_path", "notes"}
    if inventory.is_file():
        with inventory.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            if not required.issubset(set(reader.fieldnames or [])):
                errors.append("missing_columns")
            rows = list(reader)
    else:
        errors.append("missing_file")
    full = [r for r in rows if r.get("read_status") == "FULL_LOG_READ"]
    if not full:
        errors.append("no_full_log")
    for r in full:
        evidence = root / r.get("evidence_path", "")
        if not evidence.is_file():
            errors.append(f"missing_evidence:{r.get('artifact_name')}")
            continue
        if str(evidence.relative_to(root)) != str(RESEARCH_REL / "evidence/runtime_log_sanitized.log"):
            errors.append(f"unexpected_log_evidence:{r.get('artifact_name')}")
        if str(evidence.stat().st_size) != r.get("bytes") or sha256_file(evidence) != r.get("sha256"):
            errors.append(f"log_digest_mismatch:{r.get('artifact_name')}")
        try:
            if int(r.get("line_count", "0")) <= 0:
                errors.append(f"empty_log:{r.get('artifact_name')}")
        except ValueError:
            errors.append(f"bad_line_count:{r.get('artifact_name')}")
    return Check("runtime_log_fully_read", "PASS" if not errors else "FAIL", {"records": len(rows), "full_logs": len(full), "errors": errors})


def check_summary(root: Path) -> Check:
    errors: list[str] = []
    try:
        data = read_json(root / SUMMARY_REL)
    except Exception as exc:
        return Check("audit_summary_semantics", "FAIL", {"errors": [f"read_error:{type(exc).__name__}"]})
    expected = {
        ("status",): "PASS",
        ("target", "notebook_ref"): "sailorren/biohub-v19c-public0939-sis14-only",
        ("target", "version_number"): 1,
        ("public_original", "notebook_ref"): "alioman/biohub-v19c-public0939-sis14-only",
        ("source_audit", "all_copy_cells_checked"): True,
        ("runtime_log", "read_status"): "FULL_LOG_READ",
        ("score_binding", "public_score"): "0.939",
        ("score_binding", "notebook_ref"): "sailorren/biohub-v19c-public0939-sis14-only",
        ("score_binding", "version_number"): 1,
        ("redistribution", "full_notebook_source_committed"): False,
    }
    for path, value in expected.items():
        cur: Any = data
        for key in path:
            cur = cur.get(key) if isinstance(cur, dict) else None
        if cur != value:
            errors.append(f"{'/'.join(path)}={cur!r}")
    if not SHA256_RE.fullmatch(str(data.get("source_audit", {}).get("copy_source_sha256", ""))):
        errors.append("copy_source_sha256_missing")
    if int(data.get("source_audit", {}).get("copy_code_cells", 0) or 0) <= 0:
        errors.append("copy_code_cells_missing")
    if int(data.get("runtime_log", {}).get("bytes", 0) or 0) <= 0:
        errors.append("runtime_log_bytes_missing")
    binding = data.get("score_binding", {})
    if not str(binding.get("submission_id", "")).strip() or str(binding.get("submission_id")) == "UNKNOWN":
        errors.append("submission_id_unbound")
    return Check("audit_summary_semantics", "PASS" if not errors else "FAIL", {"errors": errors})


def check_zero_writes(root: Path) -> Check:
    errors: list[str] = []
    try:
        data = read_json(root / LEDGER_REL)
    except Exception as exc:
        return Check("forbidden_external_actions_zero", "FAIL", {"errors": [f"read_error:{type(exc).__name__}"]})
    fields = [
        "kaggle_submission_create_count", "kaggle_notebook_write_count", "training_task_count",
        "kaggle_dataset_create_count", "competition_join_or_rule_accept_count",
        "large_dataset_download_count",
    ]
    for field in fields:
        if data.get(field) != 0:
            errors.append(f"{field}={data.get(field)!r}")
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
            if lower in PROHIBITED_NAMES or any(lower.endswith(s) for s in PROHIBITED_SUFFIXES):
                errors.append(f"prohibited:{rel}")
            if path.suffix.lower() == ".ipynb" and RESEARCH_REL.as_posix() in rel:
                errors.append(f"notebook_source_redistributed:{rel}")
            if path.stat().st_size <= 5 * 1024 * 1024:
                text = path.read_text(encoding="utf-8", errors="ignore")
                for name, pattern in SECRET_PATTERNS.items():
                    if pattern.search(text):
                        errors.append(f"secret_pattern:{name}:{rel}")
    return Check("no_large_prohibited_or_secret_artifacts", "PASS" if not errors else "FAIL", {"errors": errors})


def check_reports(root: Path) -> Check:
    required_tokens = {
        RESEARCH_REL / "01_notebook_identity_and_lineage.md": ["sailorren/biohub-v19c-public0939-sis14-only", "alioman/biohub-v19c-public0939-sis14-only"],
        RESEARCH_REL / "03_method_analysis.md": ["SOURCE_CODE_VERIFIED", "INFERENCE", "UNKNOWN"],
        RESEARCH_REL / "05_runtime_log_analysis.md": ["MEASURED", "完整日志", "错误"],
        RESEARCH_REL / "06_submission_score_binding.md": ["0.939", "submission", "Version 1"],
        RESEARCH_REL / "07_failures_and_unknowns.md": ["UNKNOWN"],
        Path("reports/20260904_BIOHUB_V19C_COPY_AUDIT_REPORT_V01.md"): ["结论", "Notebook 身份与血缘", "源码结构", "运行日志", "分数绑定", "局限"],
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
        check_cell_audit(root),
        check_logs(root),
        check_summary(root),
        check_zero_writes(root),
        check_safety(root),
        check_reports(root),
    ]
    if args.remote_readback:
        checks.append(check_remote(root))
    passed = sum(c.status == "PASS" for c in checks)
    failed = len(checks) - passed
    report = {
        "schema_version": "1.0",
        "task_id": TASK_ID,
        "status": "PASS" if failed == 0 else "FAIL",
        "summary": {"passed": passed, "failed": failed, "total": len(checks)},
        "checks": [asdict(c) for c in checks],
    }
    if not args.verify_only:
        target = root / VERIFY_REL
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if failed:
        print("V19C_VERIFICATION_FAIL")
        return 1
    print("V19C_LOCAL_AUDIT_PASS")
    if args.remote_readback:
        print("V19C_REMOTE_READBACK_PASS")
    print("V19C_VERIFICATION_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
