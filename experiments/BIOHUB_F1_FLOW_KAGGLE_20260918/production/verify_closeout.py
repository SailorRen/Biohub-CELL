"""Independent final audit of actual local bytes, exact platform readback and budget."""
import json,gzip,hashlib
from pathlib import Path
from validate_output import validate
P=Path(__file__).resolve().parent;E=P.parent
v=validate();saved=json.loads((P/'ordinary_verified.json').read_text())
for key in ['binding','submission_sha256','row_counts','coverage','selected_config','flow_calls']:assert v[key]==saved[key]
assert hashlib.sha256(gzip.decompress((P/'output_v1/f1_production_receipt.json.gz').read_bytes())).hexdigest()==saved['raw_f1_receipt_sha256']
l=json.loads((E/'ledger.json').read_text());r=json.loads((P/'formal_request.json').read_text());s=json.loads((P/'formal_status.json').read_text())
assert l['formal_submission_requests']==len(l['formal_requests'])==1 and r['wire_sends']==1
assert l['save_and_run_requests']==len(l['requests'])==3 and l['engineering_reserve_used']==1
assert s['submission_id']==int(r['response']['ref'])==l['formal_submission_id']
assert s['version']==1 and s['script_version_id']==351084196 and s['source_sha256']==saved['binding']['source_sha256']
assert s['observation']['description']==r['description'] and str(s['submission_id'])==s['observation']['ref']
assert all(l[k]==0 for k in ['training_calls','dataset_writes','final_selection_changes'])
if s['status']!='COMPLETE':assert s['public_score'] is None
assert s['status']==l['formal_stage'] and s['public_score']==l['public_score']
print(json.dumps({'status':'DELIVERY_CHECKS_PASS','production':'ORDINARY_OUTPUT_VERIFIED','formal_status':s['status'],'public_score':s['public_score'],'scope':'A pending score is not a completed scoring task; verifies truthful resumable delivery only.'}))
