"""Minimal additions to the original Forge proposal acceptance and ordering.
No fit, model update, or new eligibility rule. Explicit model selection.
"""
import math

class ProposalPolicy:
    def __init__(self, arm, score_pair):
        if arm not in ('A0','G1','R1'): raise ValueError(arm)
        self.arm=arm; self.score_pair=score_pair; self.rows=[]; self.frame_fallbacks=[]
        self.scores={}
    def admit(self, snapshot, proposal, dataset, t, existing_child):
        distance,parent,child,*_=proposal
        score=None if self.arm=='A0' else self.score_pair(snapshot,parent,existing_child,child,dataset)
        if score is not None and not math.isfinite(score): raise RuntimeError('NONFINITE_LEARNED_SCORE')
        accept=not(self.arm=='G1' and score is not None and score<0.95)
        row={'dataset':dataset,'frame':t,'parent':parent,'child1':existing_child,'child2':child,
             'arm':self.arm,'original_eligible':True,'learned_score':score,'abstain':score is None and self.arm!='A0',
             'accepted_before_sort':accept,'distance_priority':distance,'selected':False}
        self.rows.append(row);self.scores[(dataset,t,parent,child)]=score
        return accept
    def order(self, proposals, dataset, t):
        before=[(x[1],x[2]) for x in proposals]
        if self.arm=='R1':
            scores=[self.scores[(dataset,t,p[1],p[2])] for p in proposals]
            if any(v is None for v in scores):
                self.frame_fallbacks.append((dataset,t)); proposals.sort(key=lambda p:p[0])
            else:
                proposals.sort(key=lambda p:(-self.scores[(dataset,t,p[1],p[2])],p[0]))
        else:proposals.sort(key=lambda p:p[0])
        assert set(before)=={(x[1],x[2]) for x in proposals}
        for rank,p in enumerate(proposals):
            row=next(r for r in reversed(self.rows) if (r['dataset'],r['frame'],r['parent'],r['child2'])==(dataset,t,p[1],p[2]))
            row['original_order']=before.index((p[1],p[2]));row['rank']=rank
    def selected(self,dataset,t,parent,child):
        row=next(r for r in reversed(self.rows) if (r['dataset'],r['frame'],r['parent'],r['child2'])==(dataset,t,parent,child));row['selected']=True

def patch_safe_div(source):
    """Patch one audited pure function; caller never passes a training cell."""
    append='                proposals.append((score, source_id, candidate_id, parent_dist, sister_dist))'
    assert source.count(append)==1
    source=source.replace(append,'''                proposal = (score, source_id, candidate_id, parent_dist, sister_dist)
                if SPRINT_POLICY.admit((nodes_by_id, out_by_source), proposal, dataset, t, existing_child_id):
                    proposals.append(proposal)''')
    old='        proposals.sort(key=lambda item: item[0])';assert source.count(old)==1
    source=source.replace(old,'        SPRINT_POLICY.order(proposals, dataset, t)')
    old='            used_targets.add(candidate_id)';assert source.count(old)==1
    return source.replace(old,'            SPRINT_POLICY.selected(dataset, t, source_id, candidate_id)\n'+old)
