from datetime import datetime

from besser.agent.core.agent import Agent

from governance.engine.events import DeadlineEvent, DecideEvent
from governance.engine.semantics.runtime_metamodel import Vote
from governance.engine.semantics.policy_visitor import check_conditions, isDecidablePolicy
from metamodel import Policy, ComposedPolicy, Deadline, Individual, hasRole, Role


def start_testing_policies(agent: Agent, policies: list[Policy], collab: 'Collaboration') -> None:
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
                isDecidable = isDecidablePolicy(collab, starting_policy)
                if isDecidable:
                    agent.receive_event(DecideEvent(collab, starting_policy))

        deadlines = [d for d in starting_policy.conditions if isinstance(d, Deadline)]
        for d in deadlines:
            timestamp = datetime.now().timestamp()
            timestamp += 1
            agent.receive_event(DeadlineEvent(collab, starting_policy, timestamp))