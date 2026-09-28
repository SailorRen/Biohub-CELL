"""Freeze task-defined unique-best-combination branch; no platform writes."""
import json,hashlib,difflib
from datetime import datetime,timezone
from build import make,P,base,raw
lp=P/'platform_ledger.json';l=json.loads(lp.read_text());assert not l['wave2']
assert {a['candidate_id']:a['public_score'] for a in l['wave1']}=={'DIV04_READMIT940':'0.958','DIV04':'0.956','READMIT940':'0.957'}
assert all(a['status']=='SCORED' for a in l['wave1'])
rows=[]
for arm,ilp,rd in [('DIV02_READMIT940',.2,.94),('DIV04_READMIT9525',.4,.9525)]:
 d=P/arm;d.mkdir();nb,m=make(arm,ilp,rd);code=json.dumps(nb,ensure_ascii=False,indent=1)+'\n';(d/'candidate.ipynb').write_text(code);(d/'kernel-metadata.json').write_text(json.dumps(m,indent=2)+'\n');h=hashlib.sha256(code.encode()).hexdigest()
 (d/'build_receipt.json').write_text(json.dumps({'source_sha256':h,'baseline_sha256':hashlib.sha256(raw).hexdigest(),'ilp':ilp,'readmit':rd},indent=2)+'\n')
 (d/'source.diff').write_text(''.join(difflib.unified_diff(''.join(''.join(c['source']) for c in base['cells']).splitlines(True),''.join(c['source'] for c in nb['cells']).splitlines(True),fromfile='R9D955',tofile=arm)))
 rows.append(dict(candidate_id=arm,effective_config=dict(ilp=ilp,readmit=rd,det=.955,relaxed_um=9.,flow_relaxed=0.,velocity=.5,g1=False),planned_kernel_ref=m['id'],kernel_ref=None,kernel_id=None,version=None,script_version_id=None,submission_id=None,source_sha256=h,status='LOCAL_PREPARED',public_score=None,direct_error=None,events=[]))
l.update(wave2=rows,second_wave=[a['candidate_id'] for a in rows],wave2_decision_complete=True,stage='WAVE2_PREPARED',second_wave_decision={'at':datetime.now(timezone.utc).isoformat(),'rule':'组合唯一最高且 > 0.956','evidence':{a['candidate_id']:{'submission_id':a['submission_id'],'public_score':a['public_score']} for a in l['wave1']},'reason':'组合0.958唯一最高；ILP0.2继续降低分裂成本，readmit0.9525缓和补回阈值。两份在运行前同时冻结，不采用新情报中的其他方法。','remaining_formal_budget':2,'final_selection_changed':False})
lp.write_text(json.dumps(l,ensure_ascii=False,indent=2)+'\n')
s=(P/'check_build.py').read_text().replace("[('DIV04_READMIT940',.4,.94),('DIV04',.4,.965),('READMIT940',1.2,.94)]","[('DIV02_READMIT940',.2,.94),('DIV04_READMIT9525',.4,.9525)]").replace("P/'build_checks.json'","P/'wave2_build_checks.json'")
(P/'check_wave2_build.py').write_text(s)
