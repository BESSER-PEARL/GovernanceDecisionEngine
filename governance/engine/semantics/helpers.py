import re
from datetime import datetime
from typing import TYPE_CHECKING

from scope_comparator import compare_scopes, MatchingType

if TYPE_CHECKING:
    from runtime_metamodel import Collaboration, Vote
from ..events import DeadlineEvent, DecideEvent, VoteEvent
from metamodel import Policy, ComposedPolicy, Role, Deadline, Project, Activity, Task, SinglePolicy, EvaluationMode, \
    hasRole, Individual, Human, Agent


def get_reaction_for(agent, collab: 'Collaboration'):
    reactions = collab._platform.getitem(
        f"/repos/{collab.scope.activity.project.repo_id}/issues/{collab.scope.element.payload["number"]}/reactions"
    )
    for reaction in reactions:
        if reaction["content"] != "+1" and reaction["content"] != "-1":
            continue
        evt = VoteEvent()
        evt._agreement = reaction["content"] == "+1"
        evt._pull_request_id = collab._id
        evt._user_login = reaction["user"]["login"]
        evt._rationale = ""
        agent.receive_event(evt)

def serialize_individual(indiv: Individual, roles: set[Role]):
    indiv_roles = []
    real_indiv = None
    for role in roles:
        for i in role.individuals:
            if i.name == indiv.name:
                indiv_roles.append(role)
                real_indiv = i
    roles = ", ".join({role.name for role in indiv_roles})
    role_section = "" if len(indiv_roles) == 0 else f", role : {roles}"
    if real_indiv is not None and isinstance(real_indiv, Agent):
        return f"(Agent) {real_indiv.name} {{ voteValue : {real_indiv.vote_value}, confidence : {real_indiv.confidence}, autonomy level : {real_indiv.autonomy_level}, explainability : {real_indiv.explainability}{role_section} }}"

    if real_indiv is not None and isinstance(real_indiv, Human):
        profile = "" if real_indiv.profile is None else f", profile : {real_indiv.profile.name}"
        return f"{real_indiv.name} {{ voteValue : {real_indiv.vote_value}{profile}{role_section} }}"
    return f"{indiv.name} {{ voteValue : {indiv.vote_value}{role_section} }}"

def update_individual(text: str, indiv: Individual, roles: set[Role]):
    regex = re.compile(rf"(\(Agent\)\s*)?{indiv.name}\s*({{[^}}]*}})?")
    return re.sub(regex, serialize_individual(indiv, roles), text, count=1)

def get_all_roles(policy):
    roles: set[Role]= set()
    if isinstance(policy, ComposedPolicy):
        for phase in policy.phases:
            phase_roles = get_all_roles(phase)
            roles = roles | phase_roles
    else:
        for participant in policy.participants:
            if isinstance(participant, Role):
                roles.add(participant)

    return roles

def get_all_individuals(policy):
    individuals: set[Individual] = set()
    if isinstance(policy, ComposedPolicy):
        for phase in policy.phases:
            phase_individuals = get_all_individuals(phase)
            individuals = individuals.union(phase_individuals)
    else:
        for participant in policy.participants:
            if isinstance(participant, Individual):
                individuals.add(participant)

    return individuals

def find_policy_for(policies: set[Policy], collab: 'Collaboration'):
    matching_policies: list[Policy] = []
    include_policies: list[Policy] = []
    for policy in policies:
        expected_scope = policy.scope
        received_scope = collab.scope
        matching = compare_scopes(expected_scope, received_scope)
        if matching == MatchingType.MISMATCH:
            continue
        if matching == MatchingType.MATCH:
                matching_policies.append(policy)
        elif matching == MatchingType.INCLUDE:
            if isinstance(expected_scope, Activity):
                include_policies.insert(0, policy)
            else:
                include_policies.append(policy)
    for match in matching_policies:
        starting = find_starting_policies_in(match, collab)
        if len(starting) > 0:
            return match, starting
    for included in include_policies:
        starting = find_starting_policies_in(included, collab)
        if len(starting) > 0:
            return included, starting
    return None


def find_starting_policies_in(policy: Policy, collab: 'Collaboration') -> list[Policy]:
    from governance.engine.semantics.policy_visitor import visitCondition

    out = []
    if isinstance(policy, ComposedPolicy):
        out.append(policy)
        if policy.sequential:
            first_phase = policy.phases[0]
            out.extend(find_starting_policies_in(first_phase, collab))
        else:
            for phase in policy.phases:
                out.extend(find_starting_policies_in(phase, collab))
    else:
        single_policy: SinglePolicy = policy
        pass_cond = True
        for cond in single_policy.conditions:
            if cond.evaluation_mode == EvaluationMode.PRE:
                pass_cond = pass_cond and visitCondition(collab, policy, cond) # TODO
        if pass_cond:
            out.append(policy)
    return out

# Called for composed policies from which one phase (direct child) was decided but not the composition
def find_policies_in(policy: ComposedPolicy, collab: 'Collaboration') -> list[Policy]:
    if policy.sequential:
        for phase in policy.phases:
            if phase not in collab.ballot_boxes:
                return find_starting_policies_in(phase, collab)
    # else:  Parallel does not need anything as all the direct child are already started
    return []

def start_policies(agent: Agent, policies: list[Policy], collab: 'Collaboration') -> None:
    from governance.engine.semantics.policy_visitor import check_conditions
    for starting_policy in policies:
        collab.ballot_boxes[starting_policy] = set()
        if isinstance(starting_policy, ComposedPolicy):
            continue

        # Nested SinglePolicy carry over
        if starting_policy.parent is not None and starting_policy.parent.carry_over:
            prev_policy_index = starting_policy.parent.phases.index(starting_policy) - 1
            if prev_policy_index >= 0:
                prev_policy = starting_policy.parent.phases[prev_policy_index]
                for vote in collab.ballot_boxes[prev_policy]:
                    individual = vote.voted_by
                    valid_vote = False
                    for participant in starting_policy.participants:
                        if isinstance(participant, Role):
                            for registered in participant.individuals:
                                if individual.name == registered.name:
                                    valid_vote = True
                                    individual.enacted_roles.add(
                                        hasRole(individual.name, participant, individual, collab.scope))
                        elif individual == participant:
                            valid_vote = True
                            part_indiv: Individual = participant  # if not a role it is an individual
                            role = part_indiv.role_assignement.role
                            individual.enacted_roles.add(hasRole(individual.name, role, individual, collab.scope))
                    if valid_vote:
                        box: set[Vote] = collab._ballot_boxes[starting_policy]
                        vote_copy = Vote(vote._agreement, vote._timestamp, vote._rationale, vote._voted_by)
                        vote_copy._vote_value = vote._vote_value
                        box.add(vote_copy)
                        individual.votes.add(vote_copy)

                # Can we decide
                if check_conditions(collab, starting_policy, starting_policy.conditions):
                    agent.receive_event(DecideEvent(collab, starting_policy))

        # Find deadlines and send the associated events
        deadlines = [d for d in starting_policy.conditions if isinstance(d, Deadline)]
        for deadline in deadlines:
            if deadline.date is not None:
                timestamp = deadline.date.timestamp()
                agent.receive_event(DeadlineEvent(collab, starting_policy, timestamp))
            else:
                timestamp = (datetime.now() + deadline.offset).timestamp()
                agent.receive_event(DeadlineEvent(collab, starting_policy, timestamp))