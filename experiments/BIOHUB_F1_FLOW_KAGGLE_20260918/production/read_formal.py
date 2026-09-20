"""One read only snapshot of exact submission and G1. No polling or writes to Kaggle."""
import json
from decimal import Decimal
from formal_api import P,E,COMP,REF,DESC,listed,row,now

def main():
 l=json.loads((E/'ledger.json').read_text());assert l['formal_submission_requests']==1
 e=l['formal_requests'][0];subs=listed();rid=e.get('response',{}).get('ref')
 matches=[s for s in subs if (str(s.ref)==str(rid) if rid else s.description==DESC)]
 assert len(matches)==1,'EXACT_FORMAL_NOT_IDENTIFIED_NO_RETRY'
 s=matches[0];assert s.description==DESC
 observed=row(s);state=str(s.status).split('.')[-1];score=str(s.public_score) if state=='COMPLETE' and s.public_score is not None else None
 g1=[row(x) for x in subs if int(x.ref)==56270217];assert len(g1)==1
 comparison='SCORE_PENDING' if state in ['PENDING','RUNNING'] else 'FORMAL_'+state
 if score is not None and g1[0]['public_score'] is not None:
  a,b=Decimal(score),Decimal(g1[0]['public_score']);comparison='PUBLIC_IMPROVEMENT_OBSERVED' if a>b else 'PUBLIC_TIE' if a==b else 'PUBLIC_REGRESSION'
 r={'observed_at_utc':now(),'competition':COMP,'principal':'sailorren','ref':REF,'version':1,'script_version_id':351084196,'kernel_id':134988494,'source_sha256':e['source_sha256'],'submission_id':int(s.ref),'status':state,'public_score':score,'observation':observed,'g1':g1[0],'comparison':comparison,'final_selection_changes':0}
 (P/'formal_status.json').write_text(json.dumps(r,indent=2)+'\n')
 l.update(status=comparison,formal_stage=state,public_score=score,formal_submission_id=int(s.ref));l['formal_requests'][0]['reconciled_submission_id']=int(s.ref)
 (E/'ledger.json').write_text(json.dumps(l,indent=2)+'\n');print(json.dumps(r))
if __name__=='__main__':main()
