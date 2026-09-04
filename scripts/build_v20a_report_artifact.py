#!/usr/bin/env python3
"""Build the canonical report artifact consumed by the portable HTML packager."""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path


REPORT_STEM = "20260904_BIOHUB_V20A_SAFE_DIV_RADIUS_OPTIMIZATION_REPORT_V01"
GENERATED_AT = "2026-09-04T12:45:00+08:00"


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    report_path = root / f"reports/{REPORT_STEM}.md"
    artifact_path = root / f"reports/{REPORT_STEM}.artifact.json"
    report_markdown = report_path.read_text(encoding="utf-8")

    inventory_path = root / "experiments/V20A/frozen_embryo_inventory.csv"
    decision_path = root / "experiments/V20A/promotion_decision.json"
    ledger_path = root / "experiments/V20A/platform_write_ledger.json"
    with inventory_path.open(newline="", encoding="utf-8") as handle:
        inventory_rows = [
            row
            for row in csv.DictReader(handle)
            if row["included_in_frozen_inventory"] == "true"
        ]
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))

    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("CREATE TABLE inventory (stem TEXT PRIMARY KEY, embryo_group TEXT NOT NULL)")
    connection.executemany(
        "INSERT INTO inventory (stem, embryo_group) VALUES (?, ?)",
        [(row["stem"], row["embryo_group"]) for row in inventory_rows],
    )
    connection.execute("CREATE TABLE platform_write_counts (action TEXT PRIMARY KEY, value INTEGER NOT NULL)")
    connection.executemany(
        "INSERT INTO platform_write_counts (action, value) VALUES (?, ?)",
        [(key, int(value)) for key, value in sorted(ledger["counts"].items())],
    )
    connection.execute(
        "CREATE TABLE arms (arm_order INTEGER, arm TEXT, radius_um REAL, role TEXT, status TEXT)"
    )
    roles = {"R70": "control", "R80": "candidate", "R90": "candidate"}
    radii = {"R70": 7.0, "R80": 8.0, "R90": 9.0}
    connection.executemany(
        "INSERT INTO arms (arm_order, arm, radius_um, role, status) VALUES (?, ?, ?, ?, ?)",
        [
            (index, arm, radii[arm], roles[arm], decision["candidate_results"][arm])
            for index, arm in enumerate(("R70", "R80", "R90"), start=1)
        ],
    )
    connection.execute(
        "CREATE TABLE promotion_gates (gate_order INTEGER, gate TEXT, status TEXT, evidence TEXT)"
    )
    gate_rows = []
    for index, gate in enumerate(decision["promotion_gates"], start=1):
        evidence = "No downstream result"
        if gate["id"] == "minimum_three_embryo_groups":
            evidence = f"{gate['observed']} observed / {gate['required']} required"
        gate_rows.append((index, gate["id"], gate["status"], evidence))
    connection.executemany(
        "INSERT INTO promotion_gates (gate_order, gate, status, evidence) VALUES (?, ?, ?, ?)",
        gate_rows,
    )

    summary_sql = """SELECT
  'BLOCKED_INSUFFICIENT_EMBRYO_GROUPS' AS status,
  COUNT(*) AS eligible_samples,
  COUNT(DISTINCT embryo_group) AS embryo_groups,
  (SELECT SUM(value) FROM platform_write_counts) AS kaggle_writes
FROM inventory"""
    groups_sql = """SELECT embryo_group, COUNT(*) AS sample_count
FROM inventory
GROUP BY embryo_group
ORDER BY embryo_group"""
    arms_sql = """SELECT arm, radius_um, role, status
FROM arms
ORDER BY arm_order"""
    gates_sql = """SELECT gate, status, evidence
FROM promotion_gates
ORDER BY gate_order"""

    def query_rows(sql: str) -> list[dict[str, object]]:
        return [dict(row) for row in connection.execute(sql).fetchall()]

    summary_rows = query_rows(summary_sql)
    embryo_group_rows = query_rows(groups_sql)
    arm_rows = query_rows(arms_sql)
    promotion_gate_rows = query_rows(gates_sql)

    sources = [
        {
            "id": "summary_sql",
            "label": "V20A summary snapshot query",
            "query": {
                "engine": "sqlite3-in-memory",
                "sql": summary_sql,
                "description": "Executed after loading the frozen inventory and platform write ledger.",
                "executed_at": GENERATED_AT,
                "tables_used": ["inventory", "platform_write_counts"],
            },
        },
        {
            "id": "groups_sql",
            "label": "Embryo group count query",
            "query": {
                "engine": "sqlite3-in-memory",
                "sql": groups_sql,
                "description": "Counts all eligible train stems by the frozen embryo prefix.",
                "executed_at": GENERATED_AT,
                "tables_used": ["inventory"],
            },
        },
        {
            "id": "arms_sql",
            "label": "Preregistered arm status query",
            "query": {
                "engine": "sqlite3-in-memory",
                "sql": arms_sql,
                "description": "Reads arm radius, role, and hard-stop status from the promotion decision.",
                "executed_at": GENERATED_AT,
                "tables_used": ["arms"],
            },
        },
        {
            "id": "gates_sql",
            "label": "Promotion gate status query",
            "query": {
                "engine": "sqlite3-in-memory",
                "sql": gates_sql,
                "description": "Reads the preregistered gate statuses in frozen order.",
                "executed_at": GENERATED_AT,
                "tables_used": ["promotion_gates"],
            },
        },
        {
            "id": "inventory",
            "label": "V20A frozen embryo inventory",
            "path": "experiments/V20A/frozen_embryo_inventory.csv",
        },
        {
            "id": "split",
            "label": "V20A frozen split hard-stop receipt",
            "path": "experiments/V20A/frozen_split.json",
        },
        {
            "id": "decision",
            "label": "V20A promotion decision",
            "path": "experiments/V20A/promotion_decision.json",
        },
        {
            "id": "contract",
            "label": "V20A frozen execution contract",
            "path": "experiments/V20A/contract.json",
        },
        {
            "id": "v19c_audit",
            "label": "Fixed V19C source and runtime audit",
            "path": "research/20260904_BIOHUB_V19C_SV346969653_OPTIMIZATION_AUDIT_V01/audit_summary.json",
        },
        {
            "id": "official_data_facts",
            "label": "Captured official Kaggle data-description facts",
            "path": "research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/staging/official_kaggle/evidence/browser_official_routes.json",
        },
        {
            "id": "official_scorer",
            "label": "Official scorer pinned commit",
            "href": "https://github.com/royerlab/kaggle-cell-tracking-competition/tree/075fc5f5a52d11077f9dc2b074644618f26939e2",
        },
        {
            "id": "write_ledger",
            "label": "V20A platform write ledger",
            "path": "experiments/V20A/platform_write_ledger.json",
        },
    ]

    manifest_sources = [dict(source) for source in sources]
    artifact = {
        "surface": "report",
        "manifest": {
            "version": 1,
            "surface": "report",
            "title": "Biohub V20A safe-div radius optimization gate",
            "description": "Evidence-backed hard-stop report for the preregistered embryo-disjoint validation gate.",
            "generatedAt": GENERATED_AT,
            "cards": [
                {
                    "id": "status",
                    "description": "The domain outcome after applying the frozen pre-run gate.",
                    "dataset": "summary",
                    "sourceId": "summary_sql",
                    "metrics": [{"label": "Final status", "field": "status"}],
                },
                {
                    "id": "samples",
                    "description": "Train stems with paired image/GT schema paths in the full metadata inventory.",
                    "dataset": "summary",
                    "sourceId": "summary_sql",
                    "metrics": [{"label": "Eligible samples", "field": "eligible_samples", "format": "number"}],
                },
                {
                    "id": "groups",
                    "description": "Independent embryo prefixes; the frozen minimum is three.",
                    "dataset": "summary",
                    "sourceId": "summary_sql",
                    "metrics": [{"label": "Embryo groups", "field": "embryo_groups", "format": "number"}],
                },
                {
                    "id": "writes",
                    "description": "Kaggle Notebook, SaveKernel, run, submission, poll, and retry writes combined.",
                    "dataset": "summary",
                    "sourceId": "summary_sql",
                    "metrics": [{"label": "Kaggle writes", "field": "kaggle_writes", "format": "number"}],
                },
            ],
            "charts": [
                {
                    "id": "embryo_group_counts",
                    "title": "Only two embryo groups are present",
                    "subtitle": "All 199 structurally eligible train stems group into 44b6 or 6bba; exact values are repeated in the table below.",
                    "type": "bar",
                    "dataset": "embryo_groups",
                    "sourceId": "groups_sql",
                    "encodings": {
                        "x": {"field": "embryo_group", "type": "nominal", "label": "Embryo group"},
                        "y": {"field": "sample_count", "type": "quantitative", "label": "Eligible samples", "format": "number"},
                    },
                    "yAxisTitle": "Eligible samples",
                    "valueFormat": "number",
                    "layout": "full",
                }
            ],
            "tables": [
                {
                    "id": "embryo_groups",
                    "title": "All eligible samples collapse to two embryo groups",
                    "subtitle": "Exact group counts from the complete competition file metadata inventory.",
                    "dataset": "embryo_groups",
                    "sourceId": "groups_sql",
                    "columns": [
                        {"field": "embryo_group", "label": "Embryo group", "type": "text"},
                        {"field": "sample_count", "label": "Samples", "format": "number"},
                    ],
                },
                {
                    "id": "arms",
                    "title": "Preregistered arms were not run",
                    "subtitle": "The hard gate occurred before control reproduction or candidate execution.",
                    "dataset": "arms",
                    "sourceId": "arms_sql",
                    "columns": [
                        {"field": "arm", "label": "Arm", "type": "text"},
                        {"field": "radius_um", "label": "Parent radius (um)", "format": "number"},
                        {"field": "role", "label": "Role", "type": "text"},
                        {"field": "status", "label": "Status", "type": "text"},
                    ],
                },
                {
                    "id": "promotion_gates",
                    "title": "Promotion gates",
                    "subtitle": "Only the prerequisite group-count gate was evaluated; downstream gates remain NOT_EVALUATED.",
                    "dataset": "gates",
                    "sourceId": "gates_sql",
                    "density": "dense",
                    "columns": [
                        {"field": "gate", "label": "Gate", "type": "text"},
                        {"field": "status", "label": "Status", "type": "text"},
                        {"field": "evidence", "label": "Evidence boundary", "type": "text"},
                    ],
                },
            ],
            "sources": manifest_sources,
            "blocks": [
                {
                    "id": "title",
                    "type": "markdown",
                    "body": "# Biohub V20A safe-div parent radius\n\nThe frozen embryo-disjoint prerequisite failed before any arm or Kaggle write. This report documents the hard stop without inventing missing metrics.",
                },
                {"id": "metrics", "type": "metric-strip", "cardIds": ["status", "samples", "groups", "writes"]},
                {"id": "group_chart", "type": "chart", "chartId": "embryo_group_counts", "layout": "full"},
                {"id": "group_table", "type": "table", "tableId": "embryo_groups", "layout": "full"},
                {"id": "arm_table", "type": "table", "tableId": "arms", "layout": "full"},
                {"id": "gate_table", "type": "table", "tableId": "promotion_gates", "layout": "full"},
                {
                    "id": "reading_note",
                    "type": "markdown",
                    "sourceId": "split",
                    "body": "## Reading boundary\n\n`NOT_RUN` is neither a zero score nor a failed candidate. No folds exist, so leakage is `NOT_EVALUABLE_NO_FOLDS_CREATED`. The historical V19C Public Score 0.939 remains a version-bound historical observation only.",
                },
                {
                    "id": "full_report",
                    "type": "markdown",
                    "sourceId": "contract",
                    "body": report_markdown,
                    "layout": "full",
                },
            ],
        },
        "snapshot": {
            "version": 1,
            "generatedAt": GENERATED_AT,
            "status": "ready",
            "datasets": {
                "summary": summary_rows,
                "embryo_groups": embryo_group_rows,
                "arms": arm_rows,
                "gates": promotion_gate_rows,
            },
        },
        "sources": sources,
    }
    artifact_path.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(artifact_path.relative_to(root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
