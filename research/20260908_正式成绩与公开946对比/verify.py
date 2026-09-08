"""只读核验正式成绩、来源审读与固定 GitHub 文件字节；不执行 Notebook。"""
import ast
import hashlib
import json
import subprocess
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = P.parents[1]
START = "545613e4f53986e353b1a03c1126d01b8253d9d3"
CONTRACT = "tasks/CODEX_20260908_BIOHUB_SCORE_PUBLIC946_CONTRACT.json"
REPORT = "reports/20260908_正式成绩与公开946方案对比.md"
V21REPORT = "reports/20260907_V21A_双参数实测报告.md"

def sha(b):
    return hashlib.sha256(b).hexdigest()

def read(p):
    return json.loads(p.read_text())

def local():
    assert sha((ROOT / CONTRACT).read_bytes()) == "fd238a491532c024730f8ce1fb5abf151651ddd0a59bcf20f4d91ba1b74b2800"
    obs = read(P / "平台观察.json")
    e = read(ROOT / "experiments/V21A/evidence.json")
    c, b = e["candidate"]["submission"], e["baseline"]["current_submission"]
    assert c["id"] == 56069192 and b["id"] == 55978992
    assert c["status"] == b["status"] == "COMPLETE"
    assert c["public_score"] == "0.942" and b["public_score"] == "0.939"
    assert Decimal(c["public_score"]) - Decimal(b["public_score"]) == Decimal(e["delta_public"]) == Decimal("0.003")
    assert obs["api_receipt"]["candidate"] == c and obs["api_receipt"]["baseline"] == b
    assert obs["kaggle_writes_this_turn"] == 0
    assert obs["research_reproduction"] == "NOT_RUN"
    assert e["write_ledger"]["save_requests"] == e["write_ledger"]["submission_requests"] == 1
    assert e["write_ledger"]["repair_requests"] == 0
    # Both frozen algorithm source and write budget are rechecked by the existing verifier.
    subprocess.run([sys.executable, str(ROOT / "experiments/V21A/verify.py")], cwd=ROOT, check=True)
    for rel in ["experiments/V21A/candidate.ipynb", "experiments/V21A/kernel-metadata.json", "experiments/V21A/contract.json", "experiments/V21A/execute_once.py"]:
        assert (ROOT / rel).read_bytes() == subprocess.check_output(["git", "show", f"{START}:{rel}"], cwd=ROOT)
    matrix = read(P / "源码机械对照.json")
    assert len(matrix["cells"]) == 12 and all(x["ast_equal_excluding_module_docstring"] for x in matrix["cells"])
    for key, ref, version, sv, digest in [
        ("tta", "redoctopusk/biohub-942tta", 1, 347821442, "521cb97f0f457643379a51b60c4f71e3f4cc7d1823fd98cbb97633ffaa515ec4"),
        ("harmonic", "flexonafft/biohub-harmonic-fusion", 29, 347965685, "6e1f25c4db92ca05084a3cab39ff083d10c3f43a730581c141363301c0e985bb"),
    ]:
        audit = read(P / (key + "_源码审读.json"))
        pub = next(x for x in obs["public_notebooks"] if x["key"] == key)
        assert (pub["ref"], pub["version"], pub["script_version_id"], pub["public_score"]) == (ref, version, sv, "0.946")
        assert digest == matrix[key + "_source_sha256"]
        # Original public sources remain ignored; rehash them when locally available.
        source = ROOT / "downloads/20260908_public946" / key / (ref.split("/")[-1] + ".ipynb")
        if source.exists():
            assert sha(source.read_bytes()) == digest
            cells = read(source)["cells"]
            assert len(cells) == 12
            for i, cell in enumerate(cells):
                s = "".join(cell["source"])
                ast.parse(s)
                assert sha(s.encode()) == matrix["cells"][i][key + "_source_sha256"]
        serialized = json.dumps(audit, ensure_ascii=False)
        assert digest in serialized and str(sv) in serialized and ref in serialized
        assert len(audit["cells"]) == 12
    report = (ROOT / REPORT).read_text()
    for term in ["0.942", "0.939", "0.946", "0.003", "0.004", "NOT_RUN", "UNKNOWN", "11/12", "12/12"]:
        assert term in report
    print("SCORE_RESEARCH_PASS")

def remote():
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    scope = [str(P.relative_to(ROOT)), CONTRACT, REPORT, "experiments/V21A", V21REPORT, "tasks/CODEX_20260907_BIOHUB_V21A_TWO_PARAMETER_SCORE_TEST.md"]
    paths = [p for p in subprocess.check_output(["git", "ls-tree", "-r", "--name-only", "-z", commit, "--", *scope], cwd=ROOT, text=True).split("\0") if p]
    assert len(paths) >= 26
    def one(path):
        expected = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)
        url = "https://raw.githubusercontent.com/SailorRen/Biohub-CELL/" + commit + "/" + urllib.parse.quote(path)
        with urllib.request.urlopen(url, timeout=45) as response:
            actual = response.read()
        assert actual == expected, path
        return {"path": path, "sha256": sha(actual), "bytes": len(actual)}
    with ThreadPoolExecutor(max_workers=4) as pool:
        files = list(pool.map(one, paths))
    head = subprocess.check_output(["git", "ls-remote", "origin", "refs/heads/main"], cwd=ROOT, text=True).split()[0]
    assert head == commit
    print(json.dumps({"commit": commit, "remote_main": head, "files": files}, ensure_ascii=False))
    print("REMOTE_READBACK_PASS")

if __name__ == "__main__":
    local()
    if "--remote" in sys.argv:
        remote()
