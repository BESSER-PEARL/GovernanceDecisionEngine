from datetime import datetime
from typing import TYPE_CHECKING

from besser.agent.core.agent import Agent

if TYPE_CHECKING:
    from governance.engine.semantics.collaboration_metamodel import Collaboration
from governance.engine.events import DeadlineEvent
from metamodel import Policy, ComposedPolicy, Role, Deadline
from utils.gh_extension import Patch


def get_all_roles(policy):
    roles: dict[str,Role]= dict()
    if isinstance(policy, ComposedPolicy):
        for phase in policy.phases:
            phase_roles = get_all_roles(phase)
            roles = roles | phase_roles
    else:
        for participant in policy.participants:
            if isinstance(participant, Role):
                roles[participant.name.lower()] = participant

    return roles

def find_policy_for(policies: set[Policy], collab: 'Collaboration'):
    for policy in policies:
        expected_scope = policy.scope
        received_scope = collab.scope
        if type(expected_scope) == type(received_scope):
            if isinstance(expected_scope, Patch):
                if expected_scope.action is not None and expected_scope.action != received_scope.action:
                    continue
                expected_elem = expected_scope.element
                received_elem = received_scope.element
                if type(expected_elem) != type(received_elem):
                    continue
                if expected_elem.labels is None:
                    return policy
                match = True
                for label in expected_elem.labels:
                    if label not in received_elem.labels:
                        match = False
                        break
                if match:
                    return policy
    return None

def find_starting_policies_in(policy: Policy) -> list[Policy]:
    out = [policy]
    if isinstance(policy, ComposedPolicy):
        if policy.sequential:
            # get the first phase in traverse order (should be a list)
            first_phase = policy.phases[0]
            out.extend(find_starting_policies_in(first_phase))
        else:
            for phase in policy.phases:
                out.extend(find_starting_policies_in(phase))
    return out

# Called for composed policies from which one phase (direct child) was decided but not the composition
def find_policies_in(policy: ComposedPolicy, collab: 'Collaboration') -> list[Policy]:
    if policy.sequential:
        for phase in policy.phases:
            if phase not in collab.ballot_boxes:
                return find_starting_policies_in(policy)
    # else:  Parallel does not need anything as all the direct child are already started
    return []

def start_policies(agent: Agent, policies: list[Policy], collab: 'Collaboration') -> None:
    for starting_policy in policies:
        collab.ballot_boxes[starting_policy] = set()
        if isinstance(starting_policy, ComposedPolicy):
            continue

        # Find deadlines and send the associated events
        deadlines = [d for d in starting_policy.conditions if isinstance(d, Deadline)]
        for deadline in deadlines:
            if deadline.date is not None:
                timestamp = deadline.date.timestamp()
                agent.receive_event(DeadlineEvent(collab, starting_policy, timestamp))
            else:
                timestamp = (datetime.now() + deadline.offset).timestamp()
                agent.receive_event(DeadlineEvent(collab, starting_policy, timestamp))