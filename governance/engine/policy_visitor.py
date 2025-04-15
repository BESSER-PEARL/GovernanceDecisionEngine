from typing import TYPE_CHECKING

from besser.agent.core.agent import Agent

from governance.engine.events import DeadlineEvent
from governance.engine.helpers import start_policies
from utils.gh_extension import PassedTests

if TYPE_CHECKING:
    from governance.engine.collaboration_metamodel import Collaboration

from metamodel import Policy, ConsensusPolicy, LazyConsensusPolicy, VotingPolicy, MajorityPolicy, \
    AbsoluteMajorityPolicy, LeaderDrivenPolicy, ComposedPolicy, Condition, ParticipantExclusion, \
    MinimumParticipant, VetoRight, Role, Deadline


def visitPolicy(collab: 'Collaboration', rule: Policy, agent: Agent) -> bool:
    if isinstance(rule, ConsensusPolicy):
        return visitConsensusPolicy(collab, rule)
    if isinstance(rule, LazyConsensusPolicy):
        return visitLazyConsensusPolicy(collab, rule)
    if isinstance(rule, VotingPolicy):
        return visitVotingPolicy(collab, rule)
    if isinstance(rule, MajorityPolicy):
        return visitMajorityPolicy(collab, rule)
    if isinstance(rule, AbsoluteMajorityPolicy):
        return visitAbsoluteMajorityPolicy(collab, rule)
    if isinstance(rule, LeaderDrivenPolicy, agent):
        return visitLeaderDrivenPolicy(collab, rule)
    if isinstance(rule, ComposedPolicy):
        return visitComposedPolicy(collab, rule)

def visitConsensusPolicy(collab: 'Collaboration', rule:ConsensusPolicy) -> bool:
    pass

def visitLazyConsensusPolicy(collab: 'Collaboration', rule:LazyConsensusPolicy) -> bool:
    pass

def visitVotingPolicy(collab: 'Collaboration', rule:VotingPolicy) -> bool:
    for cond in rule.conditions:
        if not visitCondition(collab, cond):
            return False

    vote_count: int = 0
    for vote in collab.ballot_boxes[rule]:
        vote_count += 1 if vote._agreement else 0
    # avoid float comparison
    return vote_count / rule.ratio > len(collab.ballot_boxes[rule])

def visitMajorityPolicy(collab: 'Collaboration', rule:MajorityPolicy) -> bool:
    for cond in rule.conditions:
         if not visitCondition(collab, cond):
             return False

    vote_count: int = 0
    for vote in collab.ballot_boxes[rule]:
        vote_count += 1 if vote._agreement else 0
    # avoid float comparison
    return vote_count / rule.ratio > len(collab.ballot_boxes[rule])

def visitAbsoluteMajorityPolicy(collab: 'Collaboration', rule:AbsoluteMajorityPolicy) -> bool:
    for cond in rule.conditions:
        if not visitCondition(collab, cond):
            return False

    vote_count: int = 0
    for vote in collab.ballot_boxes[rule]:
        vote_count += 1 if vote._agreement else 0
    # avoid float comparison
    return vote_count / rule.ratio > len(collab.ballot_boxes[rule])

def visitLeaderDrivenPolicy(collab: 'Collaboration', rule:LeaderDrivenPolicy, agent: Agent) -> bool:
    for cond in rule.conditions:
        if not visitCondition(collab, cond):
            return False

    if rule.default in collab.ballot_boxes:
        return visitPolicy(collab, rule.default, agent)

    for vote in collab.ballot_boxes[rule]:
        if vote.voted_by == collab.leader:
            return vote._agreement

    start_policies(agent, [rule.default], collab)
    return None

def visitComposedPolicy(collab: 'Collaboration', rule:ComposedPolicy) -> bool | None:
    result = rule.require_all
    finished = True
    for phase in rule.phases:
        if phase in collab.ballot_boxes:
            box = collab.ballot_boxes[phase]
            vote = box.pop()
            box.add(vote)
            if vote._part_of is not None:
                decision = vote._part_of._accepted
                if rule.require_all != decision:
                    return decision
            else:
                finished = False
        else:
            finished = False
    return None if not finished else rule.require_all




def visitCondition(collab: 'Collaboration', cond: Condition) -> bool:
    if isinstance(cond, ParticipantExclusion):
        return visitParticipantExclusion(collab, cond)
    if isinstance(cond, MinimumParticipant):
        return visitMinimumParticipant(collab, cond)
    if isinstance(cond, VetoRight):
        return visitVetoRight(collab, cond)
    if isinstance(cond, PassedTests):
        return visitPassedTests(collab, cond)
    # We do not check deadlines here
    return True

def visitParticipantExclusion(collab: 'Collaboration', cond: ParticipantExclusion) -> bool:
    names = []
    for excl in cond.excluded:
        names.append(excl.name)
    to_remove = set()
    for vote in collab.votes:
        if vote.voted_by.name in names:
            vote.voted_by.votes.remove(vote)
            to_remove.add(vote)
    collab.votes = collab.votes - to_remove
    return True


def visitMinimumParticipant(collab: 'Collaboration', cond: MinimumParticipant) -> bool:
    return len(collab.votes) >= cond.min_participants

def visitVetoRight(collab: 'Collaboration', cond: VetoRight) -> bool:
    veto_roles = []
    veto_names = []
    for vetoer in cond.vetoers:
        if isinstance(vetoer, Role):
            veto_roles.append(vetoer.name)
        else:
            veto_names.append(vetoer.name)
    for vote in collab.votes:
        if vote.voted_by.name in veto_names or  vote.voted_by.role in veto_roles:
            if not vote._agreement:
                return False

    return True

def visitPassedTests(collab: 'Collaboration', cond: PassedTests) -> bool:
    return True