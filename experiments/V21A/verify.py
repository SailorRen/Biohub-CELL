"""只读验收：反向核对冻结源码、预算及固定 GitHub commit 文件字节。"""
import ast
import csv
import hashlib
import json
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = P.parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def source(cell):
    return "".join(cell["source"])


def check_source():
    n = json.loads((P / "candidate.ipynb").read_text())
    audit = json.loads((ROOT / "research/20260907_公共方案对比/v19c_逐单元审读.json").read_text())
    assert audit["notebook_sha256"] == "92bf632410fedc9eb7e0984a20525590b5583d5abb002d8239ff65d9f51fbf57"
    assert len(n["cells"]) == 12
    for i, (cell, original) in enumerate(zip(n["cells"], audit["cells"])):
        s = source(cell)
        if cell["cell_type"] == "code":
            ast.parse(s)
            assert cell.get("outputs") == [] and cell.get("execution_count") is None
        if i == 0:
            s = s[s.index("# Biohub V19C - Public 0939 Sister14 Only"):]
        if i == 2:
            a = 'os.environ["BIOHUB_SAFE_DIV_MAX_UM"] = "9.0"'
            b = 'os.environ["BIOHUB_DEEPCENTER_SAFE_DIV_THRESHOLD"] = "0.26"\n'
            assert s.count(a) == s.count(b) == 1
            s = s.replace(a, a.replace('"9.0"', '"7.0"')).replace(b, "")
        if i == 3:
            for added in ['    "BIOHUB_SAFE_DIV_MAX_UM": 9.0,\n', '    "BIOHUB_DEEPCENTER_SAFE_DIV_THRESHOLD": 0.26,\n']:
                assert s.count(added) == 1
                s = s.replace(added, "")
        assert sha(s.encode()) == original["sha256"], f"Unexpected source change: cell {i}"
    m = json.loads((P / "kernel-metadata.json").read_text())
    assert m["id"] == "sailorren/biohub-v21a-parent9-dc026"
    assert m["is_private"] is True and m["enable_gpu"] is True and m["enable_internet"] is False
    assert m["machine_shape"] == "NvidiaTeslaT4"
    assert m["dataset_sources"] == ["pilkwang/biohub-deepcenter-unet3d-center-prior-v1/5", "pilkwang/biohub-temporal-unet3d-seed314159-v1/2", "pilkwang/biohub-tracking-support-pack-50ep-v1/10"]
    assert m["competition_sources"] == ["biohub-cell-tracking-during-development"]
    assert m["kernel_sources"] == m["model_sources"] == []
    e = json.loads((P / "evidence.json").read_text())
    assert m["docker_image"] == e["read_observations"][0]["baseline_source_current_guard"]["docker_image"]
    c = e["candidate"]
    if "file_sha256" in c:
        assert sha((P / "candidate.ipynb").read_bytes()) == c["file_sha256"]
        assert sha((P / "kernel-metadata.json").read_bytes()) == c["metadata_sha256"]
        for cell in n["cells"]:
            cell["source"] = source(cell)
        assert sha(json.dumps(n).encode()) == c["submitted_source_sha256"]
    ledger = e["write_ledger"]
    assert 0 <= ledger["save_requests"] <= 2
    assert len(ledger["actual_versions"]) <= ledger["save_requests"]
    assert len(set(ledger["actual_versions"])) == len(ledger["actual_versions"])
    assert 0 <= ledger["repair_requests"] <= 1 and 0 <= ledger["submission_requests"] <= 1
    assert ledger["training"] == ledger["dataset_model_writes"] == 0
    assert sum(x["action"] == "SaveKernel" for x in ledger["operations"]) == ledger["save_requests"]
    assert sum(x["action"] == "CreateCodeSubmission" for x in ledger["operations"]) == ledger["submission_requests"]
    if c.get("remote_binding", {}).get("verified"):
        assert c["remote_binding"]["all_12_source_cells_match"]
        assert c["remote_binding"]["normalized_notebook_objects_equal"]
        assert len(c["remote_binding"]["source_sha256"]) == 64
        for cell, bound in zip(n["cells"], c["remote_binding"]["cell_hashes"]):
            assert sha(source(cell).encode()) == bound["sha256"]
        assert c["version"] == c["remote_binding"]["version"]
        assert c["script_version_id"] and c["remote_binding"]["inputs_match"]
    if c["submission"].get("public_score") is not None:
        assert c["submission"]["status"] == "COMPLETE" and c["submission"]["id"]
        assert c["ordinary"]["verified"] and c["remote_binding"]["verified"]
    print("V21A_EVIDENCE_PASS")


def check_remote():
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    paths = [p for p in subprocess.check_output(["git", "ls-tree", "-r", "--name-only", "-z", commit, "experiments/V21A", "tasks/CODEX_20260907_BIOHUB_V21A_TWO_PARAMETER_SCORE_TEST.md", "reports/20260907_V21A_双参数实测报告.md"], cwd=ROOT, text=True).split("\0") if p]
    assert len(paths) >= 8
    results = []
    for path in paths:
        expected = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)
        url = f"https://raw.githubusercontent.com/SailorRen/Biohub-CELL/{commit}/" + urllib.parse.quote(path)
        with urllib.request.urlopen(url, timeout=30) as response:
            actual = response.read()
        assert sha(expected) == sha(actual), path
        results.append({"path": path, "sha256": sha(actual), "bytes": len(actual)})
    remote = subprocess.check_output(["git", "ls-remote", "origin", "refs/heads/main"], cwd=ROOT, text=True).split()[0]
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    if branch == "main":
        assert remote == commit
    else:
        branch_remote = subprocess.check_output(["git", "ls-remote", "origin", f"refs/heads/{branch}"], cwd=ROOT, text=True).split()[0]
        assert branch_remote == commit
    print(json.dumps({"commit": commit, "branch": branch, "remote_main": remote, "files": results}, ensure_ascii=False))
    print("V21A_REMOTE_READBACK_PASS")


def check_ordinary():
    e = json.loads((P / "evidence.json").read_text())
    c = e["candidate"]
    assert c["ordinary"]["status"] == "COMPLETE"
    assert c["version"] in e["write_ledger"]["actual_versions"]
    assert c["script_version_id"] == c["remote_binding"]["script_version_id"]
    assert c["remote_binding"]["verified"]
    integrity = json.loads((P / "bidirectional_production_runtime_integrity.json").read_text())
    assert integrity["checkpoint_sha256"] == {
        "primary": "12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771",
        "secondary": "9bac2fa0dadc4a6fc1899e0caf187f4b553e0a7cd90ba1261a68b35ffe9e305f",
        "deepcenter": "8040999a92f6b7bbd98fa8cf458141e045c0f9ad7c936bdb3b18e1f7edafe2a0",
    }
    assert integrity["support_repo_python_file_count"] == 13
    assert integrity["support_repo_python_manifest_sha256"] == "978b626d1fd1e7397435a437dfe68691defe1572fc3c20e61012d7c9b52ed029"
    assert integrity["verified_before_dynamic_source_patch"] is True
    guard = json.loads((P / "dual_seed_frame_retention_guard_report.json").read_text())
    assert guard["status"] == "clean_graph_audit_pass_candidate_unverified_quality"
    assert guard["hardware"]["visible_gpu_count"] == 2
    splits = json.loads((P / "kaggle_test_splits_50ep.json").read_text())
    assert isinstance(splits, list) and len(splits) == 1
    splits = splits[0]
    assert splits["train"] == [] and splits["test"]
    with (P / "run_stats.csv").open(newline="") as handle:
        stats = list(csv.DictReader(handle))
    names = [x["dataset"] for x in stats]
    assert len(names) == len(set(names))
    assert sorted(names) == sorted(splits["test"]) == sorted(guard["submission"]["datasets"]) == sorted(guard["topology"])
    total = 0
    for row in stats:
        topology = guard["topology"][row["dataset"]]
        for field in ["nodes", "edges"]:
            assert int(row[field]) == topology[field]
            total += int(row[field])
        assert int(row["division_like_sources"]) == topology["division_parents"]
        assert topology["max_indegree"] <= 1 and topology["max_outdegree"] <= 2
    assert total == guard["submission"]["rows"] > 0
    assert len(guard["submission"]["sha256"]) == 64
    log = (P / "ordinary.log").read_text()
    # Kaggle returns an event-array JSON, not rendered console text.
    events = json.loads(log)
    assert isinstance(events, list) and events
    log = "".join(event["data"] for event in events)
    for text in ['"safe_div_max_um": 9.0', '"deepcenter_safe_div_threshold": 0.26', '"gap_close_um": 5.8', '"unet_batch_size": 4', '"det_threshold": 0.965', '"slice": ""', 'Configuration guard: PASS', 'weights_found=True', 'weight=0.15', 'mode=harmonic_probability', 'loaded=True']:
        assert text in log, text
    print(json.dumps({"ordinary_status": "COMPLETE", "datasets": names, "rows": total, "submission_sha256": guard["submission"]["sha256"], "asset_hashes_match": True}, ensure_ascii=False))
    print("V21A_ORDINARY_PASS")


if __name__ == "__main__":
    check_source()
    evidence = json.loads((P / "evidence.json").read_text())
    if "--ordinary" in sys.argv or evidence["candidate"].get("ordinary", {}).get("verified"):
        check_ordinary()
    if "--remote" in sys.argv:
        check_remote()
