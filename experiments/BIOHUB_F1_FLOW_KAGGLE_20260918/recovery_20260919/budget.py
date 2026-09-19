"""Pure, task-specific cumulative budget checks; no platform imports."""
def authorize(ledger, phase, reason):
    requests=ledger['requests']
    assert len(requests)<3, 'TOTAL_BUDGET_EXHAUSTED'
    assert ledger.get('formal_submission_requests',0)<=1
    assert ledger.get('training_calls',0)==ledger.get('dataset_writes',0)==ledger.get('final_selection_changes',0)==0
    if phase=='diagnostic':
        assert reason=='unknown_outcome_recovery'
        assert len(requests)==1 and requests[0]['phase']=='diagnostic'
        assert requests[0]['status']=='OUTCOME_UNKNOWN_NO_RETRY'
        assert ledger.get('engineering_reserve_used',0)==0
        assert not any(e.get('reason')==reason for e in requests)
    else:
        assert phase=='production' and reason=='frozen_gate_passed'
        assert not any(e['phase']=='production' for e in requests)
