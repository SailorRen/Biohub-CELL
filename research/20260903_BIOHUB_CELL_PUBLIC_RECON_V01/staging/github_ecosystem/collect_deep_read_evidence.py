#!/usr/bin/env python3
"""Collect read-only, commit-pinned GitHub repository evidence from /tmp clones.

The script never writes to a remote. It checks out only explicitly selected public
files into disposable /tmp clones, reads their complete bytes, and persists only
tree metadata, hashes, structural statistics, and symbol/keyword summaries.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CLONES = Path("/tmp/biohub_github_ecosystem")
EVIDENCE = ROOT / "evidence"

KEYWORDS = (
    "detect", "segment", "track", "link", "division", "lineage", "assign",
    "hungarian", "linear_sum_assignment", "min_cost", "flow", "transformer",
    "attention", "unet", "stardist", "cellpose", "geff", "zarr", "ctc",
    "jaccard", "submission", "csv", "sparse", "train", "infer", "predict",
    "evaluate", "postprocess", "prune", "kalman", "bayes", "ilp", "gurobi",
)


REPOS = [
    {
        "repo": "royerlab/kaggle-cell-tracking-competition",
        "relation": "competition_host_baseline",
        "full_relevant": True,
        "targets": {},
    },
    {
        "repo": "royerlab/tracksdata",
        "relation": "competition_graph_library",
        "full_relevant": True,
        "targets": {
            "README.md": "readme", "LICENSE": "license", "pyproject.toml": "dependency",
            "src/tracksdata/io/_geff.py": "data_io", "src/tracksdata/metrics/_matching.py": "evaluation",
            "src/tracksdata/metrics/_ctc_metrics.py": "evaluation", "src/tracksdata/metrics/_traccuracy.py": "evaluation",
            "src/tracksdata/functional/_division.py": "division", "src/tracksdata/edges/_distance_edges.py": "temporal_linking",
            "src/tracksdata/solvers/_ilp_solver.py": "optimization", "src/tracksdata/solvers/_nearest_neighbors_solver.py": "optimization",
            "src/tracksdata/graph/_sql_graph.py": "graph_model",
        },
    },
    {
        "repo": "live-image-tracking-tools/geff",
        "relation": "geff_reference_implementation",
        "full_relevant": True,
        "targets": {
            "README.md": "readme", "LICENSE": "license", "pyproject.toml": "dependency", "geff-schema.json": "format_schema",
            "packages/geff/README.md": "readme", "packages/geff/pyproject.toml": "dependency",
            "packages/geff/src/geff/core_io/_base_read.py": "data_io", "packages/geff/src/geff/core_io/_base_write.py": "data_io",
            "packages/geff/src/geff/convert/_ctc.py": "conversion", "packages/geff/src/geff/validate/graph.py": "validation",
            "packages/geff/src/geff/validate/tracks.py": "validation", "packages/geff/src/geff/_graph_libs/_graph_adapter.py": "graph_model",
            "packages/geff-spec/src/geff_spec/_schema.py": "format_schema",
        },
    },
    {
        "repo": "royerlab/ultrack",
        "relation": "general_2d_3d_tracking_and_zebrafish",
        "full_relevant": True,
        "targets": {
            "README.md": "readme", "LICENSE": "license", "pyproject.toml": "dependency", "docs/source/theory.rst": "method",
            "ultrack/core/tracker.py": "pipeline", "ultrack/core/segmentation/processing.py": "segmentation",
            "ultrack/core/segmentation/hierarchy.py": "segmentation", "ultrack/core/linking/processing.py": "temporal_linking",
            "ultrack/core/linking/features.py": "temporal_linking", "ultrack/core/solve/processing.py": "optimization",
            "ultrack/core/solve/solver/mip_solver.py": "optimization", "ultrack/core/export/geff.py": "submission_conversion",
            "ultrack/core/export/ctc.py": "submission_conversion", "examples/zebrahub/config.toml": "zebrafish_example",
            "examples/zebrahub/zebrahub.ipynb": "zebrafish_example",
        },
    },
    {
        "repo": "weigertlab/trackastra",
        "relation": "transformer_cell_tracking",
        "full_relevant": True,
        "targets": {
            "README.md": "readme", "LICENSE": "license", "pyproject.toml": "dependency", "scripts/train.py": "training",
            "trackastra/data/data.py": "data_loader", "trackastra/data/features.py": "features",
            "trackastra/data/matching.py": "assignment", "trackastra/model/model.py": "model",
            "trackastra/model/model_api.py": "inference", "trackastra/model/predict.py": "inference",
            "trackastra/tracking/tracking.py": "temporal_linking", "trackastra/tracking/ilp.py": "optimization",
            "trackastra/tracking/track_graph.py": "graph_model", "trackastra/model/pretrained.json": "weights_metadata",
        },
    },
    {
        "repo": "CellTrackingChallenge/py-ctcmetrics",
        "relation": "cell_tracking_challenge_metrics",
        "full_relevant": True,
        "targets": {
            "README.md": "readme", "LICENSE.txt": "license", "requirements.txt": "dependency", "setup.py": "dependency",
            "ctc_metrics/scripts/evaluate.py": "evaluation", "ctc_metrics/metrics/technical/det.py": "evaluation",
            "ctc_metrics/metrics/technical/seg.py": "evaluation", "ctc_metrics/metrics/technical/tra.py": "evaluation",
            "ctc_metrics/metrics/technical/lnk.py": "evaluation", "ctc_metrics/metrics/hota/hota.py": "evaluation",
            "ctc_metrics/metrics/hota/chota.py": "evaluation", "ctc_metrics/metrics/validation/valid.py": "validation",
        },
    },
    {
        "repo": "CellTrackingChallenge/2021-edition-available-colabs",
        "relation": "cell_tracking_challenge_reusable_training_inference",
        "full_relevant": True,
        "targets": {},
    },
    {
        "repo": "WenChentao/3DeeCellTracker",
        "relation": "3d_time_lapse_tracking",
        "full_relevant": True,
        "targets": {
            "README.md": "readme", "LICENSE": "license", "pyproject.toml": "dependency", "requirements.txt": "dependency",
            "CellTracker/preprocess.py": "data_loader", "CellTracker/stardistwrapper.py": "segmentation",
            "CellTracker/unet3d.py": "model", "CellTracker/ffn.py": "model",
            "CellTracker/track.py": "temporal_linking", "CellTracker/tracker.py": "pipeline",
            "CellTracker/trackerlite.py": "pipeline", "CellTracker/watershed.py": "postprocessing",
        },
    },
    {
        "repo": "quantumjot/btrack",
        "relation": "bayesian_cell_tracking",
        "full_relevant": True,
        "targets": {
            "README.md": "readme", "LICENSE.md": "license", "pyproject.toml": "dependency", "btrack/core.py": "pipeline",
            "btrack/models.py": "model", "btrack/dataio.py": "data_io", "btrack/io/importers.py": "data_loader",
            "btrack/io/exporters.py": "export", "btrack/optimise/hypothesis.py": "optimization",
            "btrack/optimise/optimiser.py": "optimization", "btrack/src/tracker.cc": "temporal_linking",
            "btrack/src/hypothesis.cc": "division",
        },
    },
    {
        "repo": "raphaelreme/byotrack",
        "relation": "modular_biological_tracking_framework",
        "full_relevant": True,
        "targets": {
            "README.md": "readme", "LICENSE": "license", "pyproject.toml": "dependency", "examples/ctc/link.py": "inference",
            "src/byotrack/api/tracker.py": "pipeline", "src/byotrack/api/tracking_graph.py": "graph_model",
            "src/byotrack/dataset/ctc.py": "data_loader", "src/byotrack/geff/io.py": "data_io",
            "src/byotrack/implementation/linker/frame_by_frame/greedy_lap.py": "assignment",
            "src/byotrack/implementation/linker/frame_by_frame/kalman_linker.py": "temporal_linking",
            "src/byotrack/implementation/linker/trackastra/trackastra.py": "temporal_linking",
            "src/byotrack/implementation/refiner/stitching/dist_stitcher.py": "postprocessing",
            "src/byotrack/metrics/ctc.py": "evaluation",
        },
    },
    {
        "repo": "matt-ceran/biohub-cell-tracking",
        "relation": "competition_participant_pipeline",
        "full_relevant": True,
        "targets": {
            "README.md": "readme", "pyproject.toml": "dependency", "src/biohub/io.py": "data_io",
            "src/biohub/detect.py": "detection", "src/biohub/appearance_model.py": "model", "src/biohub/link.py": "temporal_linking",
            "src/biohub/division.py": "division", "src/biohub/division_model.py": "model", "src/biohub/metric.py": "evaluation",
            "src/biohub/submission.py": "submission_conversion", "scripts/train_appearance.py": "training",
            "scripts/train_division.py": "training", "scripts/run_baseline.py": "inference",
            "experiments/2026-08-13-phase11-v2-atlasforge.md": "experiment_report",
        },
    },
    {
        "repo": "tarunn613/biohub-cell-tracking",
        "relation": "competition_participant_pipeline",
        "full_relevant": True,
        "targets": {
            "README.md": "readme", "requirements.txt": "dependency", "docs/metric.md": "evaluation", "docs/results.md": "experiment_report",
            "src/baseline.py": "pipeline", "src/detect_cellpose.py": "detection", "src/track_lap.py": "temporal_linking",
            "src/track_motile.py": "temporal_linking", "src/score.py": "evaluation", "src/assemble_submission.py": "submission_conversion",
        },
    },
    {
        "repo": "phucthaiv02/biohub-cell-tracking",
        "relation": "competition_participant_baseline_derivative",
        "full_relevant": True,
        "targets": {"src/biohub_cell_tracking/metrics": "evaluation"},
    },
    {
        "repo": "sota1111/biohub-claude",
        "relation": "competition_participant_experiment_system",
        "targets": {
            "README.md": "readme", "NOTICE.md": "license_notice", "pyproject.toml": "dependency", "requirements.txt": "dependency",
            "src/biohub_tracking/io.py": "data_io", "src/biohub_tracking/detect.py": "detection",
            "src/biohub_tracking/learned_detect.py": "model", "src/biohub_tracking/link.py": "temporal_linking",
            "src/biohub_tracking/xattn_edge.py": "model", "src/biohub_tracking/division_overlay.py": "division",
            "src/biohub_tracking/eval/official.py": "evaluation", "src/biohub_tracking/eval/score.py": "evaluation",
            "src/biohub_tracking/build_submission.py": "submission_conversion", "submit/make_submission.py": "submission_conversion",
            "docs/ai/sot-2830-global-mincostflow-linking.md": "experiment_report",
        },
    },
    {
        "repo": "tossowski/BioHub",
        "relation": "competition_participant_pipeline",
        "full_relevant": True,
        "targets": {
            "README.md": "readme", "LICENSE": "license", "pyproject.toml": "dependency", "scripts/train_detection.py": "training",
            "scripts/predict.py": "inference", "scripts/evaluate.py": "evaluation", "src/biohub_tracking/dataspec.py": "data_loader",
            "src/biohub_tracking/io.py": "data_io", "src/biohub_tracking/detection/heatmap.py": "detection",
            "src/biohub_tracking/linking/lap.py": "assignment", "src/biohub_tracking/linking/ultrack_linker.py": "optimization",
            "src/biohub_tracking/linking/postprocess.py": "postprocessing", "src/biohub_tracking/metrics.py": "evaluation",
            "src/biohub_tracking/submission.py": "submission_conversion", "src/biohub_tracking/pipeline.py": "pipeline",
        },
    },
    {
        "repo": "m9h/biohub-starter",
        "relation": "competition_participant_validation_starter",
        "full_relevant": True,
        "targets": {
            "README.md": "readme", "FINDINGS.md": "experiment_report", "CV_LB_LOG.md": "experiment_report",
            "notebook/embryo_holdout_validation.py": "evaluation", "scripts/analyze_dataset.py": "data_loader",
            "scripts/eval_per_sample.py": "evaluation", "scripts/make_embryo_splits.py": "cv_design",
            "scripts/analyze_candidate_divisions.py": "division", "scripts/build_division_classifier.py": "division",
            "scripts/postprocess.py": "postprocessing",
        },
    },
    {
        "repo": "elephant-track/elephant-server",
        "relation": "incremental_deep_learning_3d_tracking",
        "targets": {
            "README.md": "readme", "LICENSE": "license", "requirements.txt": "dependency", "elephant-core/setup.py": "dependency",
            "elephant-core/elephant/datasets.py": "data_loader", "elephant-core/elephant/models.py": "model",
            "elephant-core/elephant/losses.py": "training", "script/train.py": "training", "script/eval.py": "evaluation",
            "script/run_elephant.py": "inference", "script/dataset_generator.py": "data_loader",
        },
    },
    {
        "repo": "MouseLand/cellpose",
        "relation": "candidate_3d_segmentation_component",
        "targets": {
            "README.md": "readme", "LICENSE": "license", "setup.py": "dependency", "environment.yml": "dependency",
            "cellpose/io.py": "data_io", "cellpose/models.py": "model", "cellpose/vit.py": "model",
            "cellpose/train.py": "training", "cellpose/dynamics.py": "postprocessing", "cellpose/metrics.py": "evaluation",
            "docs/do3d.rst": "three_dimensional_inference", "docs/train.rst": "training",
        },
    },
    {
        "repo": "live-image-tracking-tools/geff-java",
        "relation": "geff_cross_language_implementation",
        "full_relevant": True,
        "targets": {},
    },
]


def run_git(repo_dir: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(repo_dir), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def infer_category(path: str) -> str:
    low = path.lower()
    for token, category in (
        ("license", "license"), ("readme", "readme"), ("require", "dependency"),
        ("pyproject", "dependency"), ("setup", "dependency"), ("train", "training"),
        ("predict", "inference"), ("infer", "inference"), ("eval", "evaluation"),
        ("metric", "evaluation"), ("data", "data_loader"), ("io", "data_io"),
        ("geff", "data_io"), ("submit", "submission_conversion"), ("csv", "submission_conversion"),
        ("division", "division"), ("model", "model"), ("network", "model"),
        ("post", "postprocessing"), ("link", "temporal_linking"), ("track", "temporal_linking"),
    ):
        if token in low:
            return category
    return "relevant_source"


def full_relevant_paths(paths: list[str]) -> tuple[list[str], list[dict[str, str]]]:
    """Freeze the auditable definition of *relevant repository source*.

    We include all human-readable code, notebooks, documentation, dependency/
    runtime configuration, schemas, tests, and license/notices.  We exclude only
    repository-hosting automation plus binary/generated/runtime artefacts.  The
    complete Git tree is separately retained, so every exclusion remains visible.
    """
    code_ext = {
        ".py", ".pyi", ".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp",
        ".java", ".kt", ".kts", ".rs", ".js", ".jsx", ".ts", ".tsx",
        ".r", ".m", ".scala",
    }
    text_ext = {
        ".md", ".rst", ".txt", ".toml", ".json", ".jsonl", ".yml", ".yaml",
        ".xml", ".ipynb", ".sh", ".bash", ".zsh", ".cfg", ".ini",
        ".properties", ".gradle", ".cmake", ".csv", ".tsv",
    }
    infrastructure_prefixes = (
        ".github/", ".binder/", ".gitlab/", ".circleci/", ".vscode/",
    )
    generated_or_cache_parts = {
        "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
        "node_modules", "dist", "site", "_build", "target",
    }
    selected: list[str] = []
    excluded: list[dict[str, str]] = []
    for path in paths:
        path_obj = Path(path)
        name = path_obj.name.lower()
        ext = path_obj.suffix.lower()
        parts = set(path_obj.parts)
        if path.startswith(infrastructure_prefixes):
            excluded.append({"path": path, "reason": "repository_hosting_infrastructure"})
            continue
        if parts & generated_or_cache_parts:
            excluded.append({"path": path, "reason": "generated_or_cache_path"})
            continue
        is_legal = name.startswith(("license", "copying", "notice"))
        if is_legal or ext in code_ext or ext in text_ext:
            selected.append(path)
        else:
            excluded.append({"path": path, "reason": "non_text_or_non_source_extension"})
    return selected, excluded


def detect_license(text: str) -> str:
    low = text.lower()
    if "apache license" in low and "version 2.0" in low:
        return "Apache-2.0"
    if "mit license" in low or "permission is hereby granted, free of charge" in low:
        return "MIT"
    if "redistribution and use in source and binary forms" in low:
        if "neither the name" in low or "three clauses" in low:
            return "BSD-3-Clause"
        return "BSD-family"
    if "gnu general public license" in low:
        return "GPL-family"
    return "LICENSE_FILE_READ_UNCLASSIFIED"


def analyze_bytes(path: str, data: bytes) -> dict:
    text = data.decode("utf-8", errors="replace")
    lower = text.lower()
    result = {
        "path": path,
        "bytes": len(data),
        "sha256": sha256(data),
        "line_count": text.count("\n") + (1 if text else 0),
        "keyword_counts": {word: lower.count(word) for word in KEYWORDS if lower.count(word)},
    }
    suffix = Path(path).suffix.lower()
    if suffix == ".ipynb":
        try:
            notebook = json.loads(text)
            cells = notebook.get("cells", [])
            code_cells = [c for c in cells if c.get("cell_type") == "code"]
            markdown_cells = [c for c in cells if c.get("cell_type") == "markdown"]
            result["notebook"] = {
                "cell_count": len(cells),
                "code_cell_count": len(code_cells),
                "markdown_cell_count": len(markdown_cells),
                "output_cell_count": sum(bool(c.get("outputs")) for c in code_cells),
                "all_code_cells_traversed": True,
                "code_cell_source_sha256": [
                    sha256("".join(c.get("source", [])).encode("utf-8")) for c in code_cells
                ],
            }
        except json.JSONDecodeError as exc:
            result["notebook_parse_error"] = str(exc)
    else:
        result["symbols"] = re.findall(
            r"(?m)^\s*(?:async\s+def|def|class|public\s+(?:static\s+)?(?:class|interface|[\w<>\[\]]+))\s+([A-Za-z_][A-Za-z0-9_]*)",
            text,
        )[:80]
        if suffix in {".md", ".rst"}:
            result["headings"] = [
                line.strip()[:180] for line in text.splitlines()
                if line.lstrip().startswith("#")
            ][:60]
    return result


def collect_repo(spec: dict) -> dict:
    repo = spec["repo"]
    slug = repo.replace("/", "__")
    repo_dir = CLONES / slug
    out_dir = EVIDENCE / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    collected_at = datetime.now(timezone.utc).isoformat()
    if not repo_dir.exists():
        return {"repo": repo, "status": "BLOCKED", "error": "temporary clone missing"}

    commit = run_git(repo_dir, "rev-parse", "HEAD").stdout.decode().strip()
    branch = run_git(repo_dir, "rev-parse", "--abbrev-ref", "HEAD").stdout.decode().strip()
    commit_date = run_git(repo_dir, "show", "-s", "--format=%cI", "HEAD").stdout.decode().strip()
    # Do not request blob sizes here: these are partial clones and `ls-tree -l`
    # would lazily download every blob, including unrelated binary assets.
    tree_bytes = run_git(repo_dir, "ls-tree", "-r", "HEAD").stdout
    tree_path = out_dir / "tree.txt"
    tree_path.write_bytes(tree_bytes)
    paths = []
    for line in tree_bytes.decode("utf-8", errors="replace").splitlines():
        if "\t" in line:
            paths.append(line.split("\t", 1)[1])

    targets = dict(spec.get("targets", {}))
    policy_excluded: list[dict[str, str]] = []
    if spec.get("full_relevant"):
        relevant_paths, policy_excluded = full_relevant_paths(paths)
        for path in relevant_paths:
            targets.setdefault(path, infer_category(path))
    existing = [path for path in targets if path in paths]
    missing = [path for path in targets if path not in paths]

    checkout = run_git(repo_dir, "checkout", "HEAD", "--", *existing, check=False)
    read_files = []
    read_errors = []
    license_type = "NO_LICENSE_FILE_OBSERVED"
    for path in existing:
        disk_path = repo_dir / path
        if not disk_path.is_file():
            read_errors.append({"path": path, "error": "checkout did not materialize file"})
            continue
        data = disk_path.read_bytes()
        entry = analyze_bytes(path, data)
        entry["category"] = targets[path]
        read_files.append(entry)
        if targets[path] in {"license", "license_notice"}:
            license_type = detect_license(data.decode("utf-8", errors="replace"))

    required_categories = {
        "readme", "dependency", "training", "inference", "evaluation", "data_loader",
        "data_io", "submission_conversion", "model", "postprocessing", "division",
        "temporal_linking", "optimization", "license",
    }
    observed_categories = {entry["category"] for entry in read_files}
    absent_categories = sorted(required_categories - observed_categories)
    category_coverage = {
        category: {
            "status": "READ" if category in observed_categories else "N/A_NO_DEDICATED_FILE_OBSERVED_IN_FIXED_TREE",
            "paths": [entry["path"] for entry in read_files if entry["category"] == category],
        }
        for category in sorted(required_categories)
    }
    full_coverage = bool(spec.get("full_relevant")) and not missing and not read_errors and len(read_files) == len(targets)
    read_status = "FULL_RELEVANT_REPO_SOURCE_READ" if full_coverage else "TARGET_FILES_READ"
    evidence = {
        "schema_version": "1.0",
        "source_id": f"GH-DEEP-{slug}",
        "repo": repo,
        "url": f"https://github.com/{repo}",
        "relation_to_competition": spec["relation"],
        "access_time_utc": collected_at,
        "fixed_branch": branch,
        "fixed_commit_sha": commit,
        "latest_commit_date": commit_date,
        "tree_file_count": len(paths),
        "tree_bytes": len(tree_bytes),
        "tree_sha256": sha256(tree_bytes),
        "tree_evidence_path": str(tree_path.relative_to(ROOT.parent.parent)),
        "read_status": read_status,
        "files_requested": len(targets),
        "relevant_source_paths_selected": len(targets) if spec.get("full_relevant") else None,
        "relevant_source_selection_coverage": 1.0 if full_coverage else None,
        "files_actually_read_count": len(read_files),
        "files_actually_read": read_files,
        "target_paths_missing": missing,
        "read_errors": read_errors,
        "checkout_exit": checkout.returncode,
        "checkout_stderr_excerpt": checkout.stderr.decode("utf-8", errors="replace")[:2000],
        "checkout_stderr_sha256": sha256(checkout.stderr),
        "license": license_type,
        "categories_observed": sorted(observed_categories),
        "categories_not_present_in_selected_files": absent_categories,
        "category_coverage": category_coverage,
        "selection_policy": {
            "included": "all human-readable code, notebooks, documentation, dependency/runtime configuration, schemas, tests, and license/notices at the fixed commit",
            "excluded": "repository-hosting automation, generated/cache directories, and binary/non-source artefacts",
            "excluded_path_count": len(policy_excluded),
            "excluded_paths": policy_excluded,
        } if spec.get("full_relevant") else None,
        "scope_note": "Full bytes were read for every listed relevant-source path; only hashes, structure, notebook-cell hashes, and symbol/keyword summaries are persisted. The complete tree and per-path exclusions preserve the coverage boundary.",
    }
    evidence_path = out_dir / "repo_evidence.json"
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "repo": repo,
        "status": read_status,
        "commit": commit,
        "branch": branch,
        "file_count": len(paths),
        "read_count": len(read_files),
        "missing_count": len(missing),
        "error_count": len(read_errors),
        "license": license_type,
        "evidence": str(evidence_path.relative_to(ROOT)),
    }


def main() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=5) as executor:
        summary = list(executor.map(collect_repo, REPOS))
    (ROOT / "deep_read_collection_summary.json").write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "repository_count": len(summary),
                "summaries": summary,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
