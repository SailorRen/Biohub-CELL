"""One readback of the newly created ID, without accessing status/score fields."""
from datetime import datetime,timezone
import json
from pathlib import Path

P=Path(__file__).resolve().parent


def identity_fields(response):
    # Deliberately do not call to_dict() or read status/public_score/private_score.
    return {'submission_id':int(response.ref),'description':str(response.description),
            'file_name':str(response.file_name),'submitted_at_utc':str(response.date)}


def main():
    ledger=json.loads((P/'write_ledger.json').read_text())
    ops=[o for o in ledger['operations'] if o['action']=='submit']
    assert len(ops)==1 and ops[0]['status']=='RESPONSE_RECEIVED_READBACK_REQUIRED'
    op=ops[0];expected=op['response']
    from kaggle import api
    from kagglesdk.competitions.types.competition_api_service import ApiGetSubmissionRequest
    req=ApiGetSubmissionRequest();req.ref=int(expected['submission_id'])
    with api.build_kaggle_client() as c:response=c.competitions.competition_api_client.get_submission(req)
    result=identity_fields(response)
    assert result['submission_id']==expected['submission_id'] and result['description']==expected['description']
    binding=json.loads((P/'version_binding.json').read_text())
    result.update(task_id='DIVISION_TRAIN_20260914',identity_readback_verified=True,
                  ref=binding['ref'],version=binding['version'],script_version_id=binding['script_version_id'],
                  source_sha256=op['candidate_sha256'],observed_at_utc=datetime.now(timezone.utc).isoformat(),
                  score_read=False,scoring_status_read=False,
                  version_binding_basis='Exact CreateCodeSubmission kernel/version arguments, pre-submit Notebook readback, and matching returned submission description; GetSubmission does not expose ScriptVersionId.',
                  note='Only this newly created submission ID, description, file name and creation date were inspected.')
    (P/'submission_receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
