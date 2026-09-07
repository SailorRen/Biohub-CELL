"""V21A 只读状态回收；不创建版本、不提交、不下载预测文件。"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from kaggle import api

P = Path(__file__).resolve().parent
E = P / "evidence.json"
parser = argparse.ArgumentParser()
parser.add_argument("--logs", action="store_true")
parser.add_argument("--formal", action="store_true")
args = parser.parse_args()
e = json.loads(E.read_text())
c = e["candidate"]
now = datetime.now(timezone.utc).isoformat()
out = {"operation": "READ_STATUS", "observed_at_utc": now, "ref": c["ref"], "version": c["version"], "script_version_id": c["script_version_id"]}
try:
    if args.formal:
        rows = api.competition_submissions("biohub-cell-tracking-during-development", page_size=100) or []
        ids = {55978992, int(c["submission"]["id"])} if c["submission"]["id"] else {55978992}
        matches = []
        for s in rows:
            if int(s.ref) in ids or "v21a" in (s.description or "").lower():
                matches.append({"id": int(s.ref), "status": str(s.status).split(".")[-1], "public_score": s.public_score or None, "description": s.description, "date_utc": str(s.date), "error_description": getattr(s, "error_description", None), "observed_at_utc": now})
        out["submissions"] = matches
        for s in matches:
            if s["id"] == 55978992:
                e["baseline"]["current_submission"] = s
            elif s["id"] == c["submission"].get("id"):
                c["submission"].update(s)
                e["experiment_status"] = "FORMAL_" + s["status"]
    else:
        out["ordinary"] = api.kernels_status(c["ref"]).to_dict()
        c.setdefault("ordinary", {}).update(out["ordinary"], observed_at_utc=now)
        if e["write_ledger"]["submission_requests"] == 0:
            e["experiment_status"] = "ORDINARY_" + out["ordinary"]["status"]
        if args.logs:
            log = api.kernels_logs(c["ref"])
            out["log_bytes"] = len(log.encode())
            out["log_sha256"] = hashlib.sha256(log.encode()).hexdigest()
            # Persist the platform's ordinary log only. No credentials/headers are requested.
            (P / "ordinary.log").write_text(log)
            out["log_tail"] = log[-3500:]
except Exception as exc:
    out["read_error"] = {"type": type(exc).__name__, "http_status": getattr(getattr(exc, "response", None), "status_code", None)}
e["read_observations"].append({k: v for k, v in out.items() if k != "log_tail"})
temp = E.with_suffix(".tmp")
temp.write_text(json.dumps(e, ensure_ascii=False, indent=2, default=str) + "\n")
temp.replace(E)
print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
