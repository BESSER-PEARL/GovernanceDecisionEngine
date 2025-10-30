from typing import TYPE_CHECKING

from besser.agent.core.agent import Agent
from besser.agent.platforms.github.github_platform import GitHubPlatform

from governance.engine.semantics.helpers import start_policies
from utils.chp_extension import CheckCiCd, LabelCondition, Repository

if TYPE_CHECKING:
    from governance.engine.semantics.collaboration_metamodel import Collaboration

from metamodel import Policy, ConsensusPolicy, LazyConsensusPolicy, VotingPolicy, MajorityPolicy, \
    AbsoluteMajorityPolicy, LeaderDrivenPolicy, ComposedPolicy, Condition, ParticipantExclusion, \
    MinimumParticipant, VetoRight, Role, Individual, EvaluationMode, Activity, Task, Deadline


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

    vote_count: float = 0
    total_count: float = 0
    for vote in collab.ballot_boxes[rule]:
        vote_count += vote._vote_value if vote._agreement else 0
        total_count += vote._vote_value
    ratio = rule.ratio if rule.ratio is not None else 0.5
    percentage = vote_count / total_count
    return percentage > ratio or percentage == 1.0

def visitLazyConsensusPolicy(collab: 'Collaboration', rule:LazyConsensusPolicy) -> bool:
    if not check_conditions(collab, rule, rule.conditions):
        return False

    potential_participant = set()
    for p in rule.participants:
        if isinstance(p, Role):
            potential_participant = potential_participant.union(p.individuals)
        else:  # is individual
            potential_participant.add(p)

    vote_count: float = 0
    total_count: float = 0
    for vote in collab.ballot_boxes[rule]:
        vote_count += vote._vote_value if vote._agreement else 0
        total_count += vote._vote_value

    positive_abstention = len(potential_participant) - len(collab.ballot_boxes[rule])
    ratio = rule.ratio if rule.ratio is not None else 0.5
    percentage = (vote_count + positive_abstention) / (total_count + positive_abstention)
    return percentage > ratio or percentage == 1.0

def visitVotingPolicy(collab: 'Collaboration', rule:VotingPolicy) -> bool:
    if not check_conditions(collab, rule, rule.conditions):
        return False

    vote_count: float = 0
    total_count: float = 0
    for vote in collab.ballot_boxes[rule]:
        vote_count += vote._vote_value if vote._agreement else 0
        total_count += vote._vote_value
    ratio = rule.ratio if rule.ratio is not None else 0.5
    percentage = vote_count / total_count
    return percentage > ratio or percentage == 1.0

def visitMajorityPolicy(collab: 'Collaboration', rule:MajorityPolicy) -> bool:
    if not check_conditions(collab, rule, rule.conditions):
        return False

    vote_count: float = 0
    total_count: float = 0
    for vote in collab.ballot_boxes[rule]:
        vote_count += vote._vote_value if vote._agreement else 0
        total_count += vote._vote_value
    ratio = rule.ratio if rule.ratio is not None else 0.5
    percentage = vote_count / total_count
    return percentage > ratio or percentage == 1.0

def visitAbsoluteMajorityPolicy(collab: 'Collaboration', rule:AbsoluteMajorityPolicy) -> bool:
    if not check_conditions(collab, rule, rule.conditions):
        return False

    potential_participant = set()
    for p in rule.participants:
        if isinstance(p, Role):
            potential_participant = potential_participant.union(p.individuals)
        else:  # is individual
            potential_participant.add(p)

    vote_count: float = 0
    total_count: float = 0
    for vote in collab.ballot_boxes[rule]:
        vote_count += vote._vote_value if vote._agreement else 0
        total_count += vote._vote_value

    abstention = len(potential_participant) - len(collab.ballot_boxes[rule])
    ratio = rule.ratio if rule.ratio is not None else 0.5
    percentage = vote_count / (total_count + abstention)
    return percentage > ratio or percentage == 1.0

def visitLeaderDrivenPolicy(collab: 'Collaboration', rule:LeaderDrivenPolicy, agent: Agent) -> bool:
    if not check_conditions(collab, rule, rule.conditions):
        return False

    if rule.default in collab.ballot_boxes:
        return visitPolicy(collab, rule.default, agent)

    for vote in collab.ballot_boxes[rule]:
        # if vote.voted_by == collab.leader:
            return vote._agreement

    start_policies(agent, [rule.default], collab)
    return None

def visitComposedPolicy(collab: 'Collaboration', rule:ComposedPolicy) -> bool | None:
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
        if cond.evaluation_mode == EvaluationMode.CONCURRENT:
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
    if isinstance(cond, CheckCiCd):
        return visitCheckCiCd(collab, rule, cond)
    if isinstance(cond, LabelCondition):
        return visitLabelCondition(collab, rule, cond)
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

def visitCheckCiCd(collab: 'Collaboration', rule: Policy, cond: CheckCiCd) -> bool:
    gh_platform: GitHubPlatform = collab._platform
    pr_payload = collab.scope.element.payload
    commits = gh_platform.getitem(pr_payload["commits_url"].removeprefix('https://api.github.com'))
    status_url = commits[0]["url"].removeprefix('https://api.github.com') + '/status'
    status_payload = gh_platform.getitem(status_url)
    return status_payload["state"] == "success"

def visitLabelCondition(collab: 'Collaboration', rule: Policy, cond: LabelCondition) -> bool:
    gh_platform: GitHubPlatform = collab._platform
    pr_id = collab.scope.element.payload["id"]
    project: Repository = collab.scope
    if isinstance(collab.scope, Activity):
        project = collab.scope.project
    elif isinstance(collab.scope, Task):
        project = collab.scope.activity.project
    user_repo = project.repo_id.split('/')
    pr = gh_platform.get_issue(user_repo[0], user_repo[1], pr_id)
    if cond.evaluation_mode == EvaluationMode.POST:
        for label in cond.labels:
            gh_platform.set_label(pr, label.name)
    else:
        labels_name = {label["name"] for label in pr.labels}
        for label in cond.labels:
            if (label.name not in labels_name) == cond.inclusion:
                return False
        return True



def isDecidablePolicy(collab: 'Collaboration', rule: Policy) -> bool:
    if isinstance(rule, ConsensusPolicy):
        return isDecidableConsensusPolicy(collab, rule)
    if isinstance(rule, LazyConsensusPolicy):
        return isDecidableLazyConsensusPolicy(collab, rule)
    if isinstance(rule, MajorityPolicy):
        return isDecidableMajorityPolicy(collab, rule)
    if isinstance(rule, AbsoluteMajorityPolicy):
        return isDecidableAbsoluteMajorityPolicy(collab, rule)
    if isinstance(rule, VotingPolicy):
        return isDecidableVotingPolicy(collab, rule)
    if isinstance(rule, LeaderDrivenPolicy):
        return isDecidableLeaderDrivenPolicy(collab, rule)
    if isinstance(rule, ComposedPolicy):
        return isDecidableComposedPolicy(collab, rule)


def isDecidableConsensusPolicy(collab: 'Collaboration', rule:ConsensusPolicy) -> bool:
    if not check_conditions(collab, rule, rule.conditions):
        return False

    potential_participant = set()
    for p in rule.participants:
        if isinstance(p, Role):
            potential_participant = potential_participant.union(p.individuals)
        else:  # is individual
            potential_participant.add(p)

    vote_count: float = 0
    vote_against: float = 0
    total_count: float = 0
    for vote in collab.ballot_boxes[rule]:
        vote_count += vote._vote_value if vote._agreement else 0
        vote_against += vote._vote_value if not vote._agreement else 0
        total_count += vote._vote_value

    if total_count == 0.0:
        return False

    abstention = len(potential_participant) - len(collab.ballot_boxes[rule])
    ratio = rule.ratio if rule.ratio is not None else 0.5
    inv_ratio = 1 - ratio

    deadlines = {cond for cond in rule.conditions if isinstance(cond, Deadline)}

    if len(deadlines) > 0:
        return (vote_count / (total_count + abstention) > ratio or  # still true if all abstentionists vote false
                vote_against / (total_count + abstention) > inv_ratio or  # still false if all abstentionists vote true
                vote_count / (total_count + abstention) == 1.0)  ## edge-case : if everyone vote true when ratio is 1
    else:
        return (vote_count / (total_count) > ratio or  # still true if all abstentionists vote false
                vote_against / (total_count + abstention) > inv_ratio or  # still false if all abstentionists vote true
                vote_count / (total_count) == 1.0)  ## edge-case : if everyone vote true when ratio is 1

def isDecidableLazyConsensusPolicy(collab: 'Collaboration', rule:LazyConsensusPolicy) -> bool:
    if not check_conditions(collab, rule, rule.conditions):
        return False

    potential_participant = set()
    for p in rule.participants:
        if isinstance(p, Role):
            potential_participant = potential_participant.union(p.individuals)
        else:  # is individual
            potential_participant.add(p)

    vote_count: float = 0
    vote_against: float = 0
    total_count: float = 0
    for vote in collab.ballot_boxes[rule]:
        vote_count += vote._vote_value if vote._agreement else 0
        vote_against += vote._vote_value if not vote._agreement else 0
        total_count += vote._vote_value

    if total_count == 0.0:
        return False

    abstention = len(potential_participant) - len(collab.ballot_boxes[rule])
    ratio = rule.ratio if rule.ratio is not None else 0.5
    inv_ratio = 1 - ratio

    deadlines = {cond for cond in rule.conditions if isinstance(cond, Deadline)}

    if len(deadlines) > 0:
        return (vote_count / (total_count + abstention) > ratio or  # still true if all abstentionists vote false
                vote_against / (total_count + abstention) > inv_ratio or  # still false if all abstentionists vote true
                vote_count / (total_count + abstention) == 1.0)  ## edge-case : if everyone vote true when ratio is 1
    else:
        return (vote_count / (total_count) > ratio or  # still true if all abstentionists vote false
                vote_against / (total_count + abstention) > inv_ratio or  # still false if all abstentionists vote true
                vote_count / (total_count) == 1.0)  ## edge-case : if everyone vote true when ratio is 1

def isDecidableVotingPolicy(collab: 'Collaboration', rule:VotingPolicy) -> bool:
    if not check_conditions(collab, rule, rule.conditions):
        return False

    potential_participant = set()
    for p in rule.participants:
        if isinstance(p, Role):
            potential_participant = potential_participant.union(p.individuals)
        else:  # is individual
            potential_participant.add(p)

    vote_count: float = 0
    vote_against: float = 0
    total_count: float = 0
    for vote in collab.ballot_boxes[rule]:
        vote_count += vote._vote_value if vote._agreement else 0
        vote_against += vote._vote_value if not vote._agreement else 0
        total_count += vote._vote_value

    if total_count == 0.0:
        return False

    abstention = len(potential_participant) - len(collab.ballot_boxes[rule])
    ratio = rule.ratio if rule.ratio is not None else 0.5
    inv_ratio = 1 - ratio

    deadlines = {cond for cond in rule.conditions if isinstance(cond, Deadline)}

    if len(deadlines) > 0:
        return (vote_count / (total_count + abstention) > ratio or  # still true if all abstentionists vote false
                vote_against / (total_count + abstention) > inv_ratio or  # still false if all abstentionists vote true
                vote_count / (total_count + abstention) == 1.0)  ## edge-case : if everyone vote true when ratio is 1
    else:
        return (vote_count / (total_count) > ratio or  # still true if all abstentionists vote false
                vote_against / (total_count + abstention) > inv_ratio or  # still false if all abstentionists vote true
                vote_count / (total_count) == 1.0)  ## edge-case : if everyone vote true when ratio is 1

def isDecidableMajorityPolicy(collab: 'Collaboration', rule:MajorityPolicy) -> bool:
    if not check_conditions(collab, rule, rule.conditions):
        return False

    potential_participant = set()
    for p in rule.participants:
        if isinstance(p, Role):
            potential_participant = potential_participant.union(p.individuals)
        else:  # is individual
            potential_participant.add(p)

    vote_count: float = 0
    vote_against: float = 0
    total_count: float = 0
    for vote in collab.ballot_boxes[rule]:
        vote_count += vote._vote_value if vote._agreement else 0
        vote_against += vote._vote_value if not vote._agreement else 0
        total_count += vote._vote_value

    if total_count == 0.0:
        return False

    abstention = len(potential_participant) - len(collab.ballot_boxes[rule])
    ratio = rule.ratio if rule.ratio is not None else 0.5
    inv_ratio = 1 - ratio

    deadlines = {cond for cond in rule.conditions if isinstance(cond, Deadline)}

    if len(deadlines)>0:
        return (vote_count / (total_count + abstention) > ratio or  # still true if all abstentionists vote false
                vote_against / (total_count + abstention) > inv_ratio or  # still false if all abstentionists vote true
                vote_count / (total_count + abstention) == 1.0)  ## edge-case : if everyone vote true when ratio is 1
    else:
        return (vote_count / (total_count) > ratio or  # still true if all abstentionists vote false
            vote_against / (total_count + abstention) > inv_ratio or  # still false if all abstentionists vote true
            vote_count / (total_count) == 1.0)  ## edge-case : if everyone vote true when ratio is 1

def isDecidableAbsoluteMajorityPolicy(collab: 'Collaboration', rule:AbsoluteMajorityPolicy) -> bool:
    if not check_conditions(collab, rule, rule.conditions):
        return False

    potential_participant = set()
    for p in rule.participants:
        if isinstance(p, Role):
            potential_participant = potential_participant.union(p.individuals)
        else:  # is individual
            potential_participant.add(p)

    vote_count: float = 0
    vote_against: float = 0
    total_count: float = 0
    for vote in collab.ballot_boxes[rule]:
        vote_count += vote._vote_value if vote._agreement else 0
        vote_against += vote._vote_value if not vote._agreement else 0
        total_count += vote._vote_value

    if total_count == 0.0:
        return False

    abstention = len(potential_participant) - len(collab.ballot_boxes[rule])
    ratio = rule.ratio if rule.ratio is not None else 0.5
    inv_ratio = 1 - ratio
    return (vote_count / (total_count + abstention) > ratio or    # still true if all abstentionists vote false
            vote_against / (total_count + abstention) > inv_ratio or # still false if all abstentionists vote true
            vote_count / (total_count + abstention) == 1.0) ## edge-case : if everyone vote true when ratio is 1

def isDecidableLeaderDrivenPolicy(collab: 'Collaboration', rule:LeaderDrivenPolicy) -> bool:
    if not check_conditions(collab, rule, rule.conditions):
        return False

    if rule.default in collab.ballot_boxes:
        return isDecidablePolicy(collab, rule.default)

    if len(collab.ballot_boxes[rule]) > 0:
        return True
    # for vote in collab.ballot_boxes[rule]:
    #     return vote.voted_by == collab.leader

    return False

def isDecidableComposedPolicy(collab: 'Collaboration', rule:ComposedPolicy) -> bool | None:
    finished = True
    for phase in rule.phases:
        if phase in collab.ballot_boxes:
            box = collab.ballot_boxes[phase]
            vote = box.pop()
            box.add(vote)
            if vote._part_of is not None:
                decision = vote._part_of._accepted
                if rule.require_all != decision:
                    return True
            else:
                finished = False
        else:
            finished = False
    return finished