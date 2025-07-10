from typing import TYPE_CHECKING

from besser.agent.core.agent import Agent
from besser.agent.platforms.github.github_platform import GitHubPlatform

from governance.engine.semantics.helpers import start_policies
from utils.gh_extension import PassedTests

if TYPE_CHECKING:
    from governance.engine.semantics.collaboration_metamodel import Collaboration

from metamodel import Policy, ConsensusPolicy, LazyConsensusPolicy, VotingPolicy, MajorityPolicy, \
    AbsoluteMajorityPolicy, LeaderDrivenPolicy, ComposedPolicy, Condition, ParticipantExclusion, \
    MinimumParticipant, VetoRight, Role, Individual


def visitPolicy(collab: 'Collaboration', rule: Policy, agent: Agent) -> bool:
    if isinstance(rule, ConsensusPolicy):
        return visitConsensusPolicy(collab, rule)
    if isinstance(rule, LazyConsensusPolicy):
        return visitLazyConsensusPolicy(collab, rule)
    if isinstance(rule, MajorityPolicy):
        return visitMajorityPolicy(collab, rule)
    if isinstance(rule, AbsoluteMajorityPolicy):
        return visitAbsoluteMajorityPolicy(collab, rule)
    if isinstance(rule, VotingPolicy):
        return visitVotingPolicy(collab, rule)
    if isinstance(rule, LeaderDrivenPolicy):
        return visitLeaderDrivenPolicy(collab, rule, agent)
    if isinstance(rule, ComposedPolicy):
        return visitComposedPolicy(collab, rule)

def visitConsensusPolicy(collab: 'Collaboration', rule:ConsensusPolicy) -> bool:
    if not check_conditions(collab, rule, rule.conditions):
        return False

    vote_count: int = 0
    for vote in collab.ballot_boxes[rule]:
        vote_count += 1 if vote._agreement else 0
    # avoid float comparison
    ratio = rule.ratio if rule.ratio is not None else 0.5
    return vote_count / ratio > len(collab.ballot_boxes[rule])

def visitLazyConsensusPolicy(collab: 'Collaboration', rule:LazyConsensusPolicy) -> bool:
    if not check_conditions(collab, rule, rule.conditions):
        return False

    potential_participant = set()
    for p in rule.participants:
        if isinstance(p, Role):
            potential_participant.union(p.individuals)
        else:  # is individual
            potential_participant.add(p)

    vote_count: int = 0
    for vote in collab.ballot_boxes[rule]:
        vote_count += 1 if vote._agreement else 0

    positive_abstention = len(potential_participant) - len(collab.ballot_boxes[rule])
    ratio = rule.ratio if rule.ratio is not None else 0.5
    return (vote_count + positive_abstention) / ratio > len(potential_participant)

def visitVotingPolicy(collab: 'Collaboration', rule:VotingPolicy) -> bool:
    if not check_conditions(collab, rule, rule.conditions):
        return False

    vote_count: int = 0
    for vote in collab.ballot_boxes[rule]:
        vote_count += 1 if vote._agreement else 0
    # avoid float comparison
    ratio = rule.ratio if rule.ratio is not None else 0.5
    return vote_count / ratio > len(collab.ballot_boxes[rule])

def visitMajorityPolicy(collab: 'Collaboration', rule:MajorityPolicy) -> bool:
    if not check_conditions(collab, rule, rule.conditions):
        return False

    vote_count: int = 0
    for vote in collab.ballot_boxes[rule]:
        vote_count += 1 if vote._agreement else 0
    # avoid float comparison
    ratio = rule.ratio if rule.ratio is not None else 0.5
    return vote_count / ratio > len(collab.ballot_boxes[rule])

def visitAbsoluteMajorityPolicy(collab: 'Collaboration', rule:AbsoluteMajorityPolicy) -> bool:
    if not check_conditions(collab, rule, rule.conditions):
        return False

    vote_count: int = 0
    for vote in collab.ballot_boxes[rule]:
        vote_count += 1 if vote._agreement else 0
    # avoid float comparison
    ratio = rule.ratio if rule.ratio is not None else 0.5
    potential_participant = set()
    for p in rule.participants:
        if isinstance(p, Role):
            potential_participant.union(p.individuals)
        else: # is individual
            potential_participant.add(p)

    return vote_count / ratio > len(potential_participant)

def visitLeaderDrivenPolicy(collab: 'Collaboration', rule:LeaderDrivenPolicy, agent: Agent) -> bool:
    if not check_conditions(collab, rule, rule.conditions):
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


def check_conditions(collab: 'Collaboration', rule: Policy, conds: set[Condition]) -> bool:
    exclusion = None
    other = set()
    for cond in conds:
        if isinstance(cond, ParticipantExclusion):
            exclusion = cond
        else:
            other.add(cond)

    if not visitCondition(collab, rule, exclusion):
        return False
    for cond in other:
        if not visitCondition(collab, rule, cond):
            return False
    return True


def visitCondition(collab: 'Collaboration', rule: Policy, cond: Condition) -> bool:
    if isinstance(cond, ParticipantExclusion):
        return visitParticipantExclusion(collab, rule, cond)
    if isinstance(cond, MinimumParticipant):
        return visitMinimumParticipant(collab, rule, cond)
    if isinstance(cond, VetoRight):
        return visitVetoRight(collab, rule, cond)
    if isinstance(cond, PassedTests):
        return visitPassedTests(collab, rule, cond)
    # We do not check deadlines here
    return True

def visitParticipantExclusion(collab: 'Collaboration', rule: Policy, cond: ParticipantExclusion) -> bool:
    to_remove = set()
    for vote in collab.ballot_boxes[rule]:
        if vote.voted_by in cond.excluded:
            vote.voted_by.votes.remove(vote)
            to_remove.add(vote)
    collab.ballot_boxes[rule] = collab.ballot_boxes[rule] - to_remove
    return True


def visitMinimumParticipant(collab: 'Collaboration', rule: Policy, cond: MinimumParticipant) -> bool:
    return len(collab.ballot_boxes[rule]) >= cond.min_participants

def visitVetoRight(collab: 'Collaboration', rule: Policy, cond: VetoRight) -> bool:
    vetoers = set()
    for vetoer in cond.vetoers:
        if isinstance(vetoer, Role):
            vetoers = vetoers.union(vetoer.individuals)
        else:
            vetoers.add(vetoer)
    for vote in collab.ballot_boxes[rule]:
        if vote.voted_by in vetoers:
            if not vote._agreement:
                return False

    return True

def visitPassedTests(collab: 'Collaboration', rule: Policy, cond: PassedTests) -> bool:
    gh_platform: GitHubPlatform = collab.scope.platform
    pr_payload = collab.scope.element.payload
    commits = gh_platform.getitem(pr_payload["commits_url"].removeprefix('https://api.github.com'))
    status_url = commits[0]["url"].removeprefix('https://api.github.com') + '/status'
    status_payload = gh_platform.getitem(status_url)
    return status_payload["state"] == "success"