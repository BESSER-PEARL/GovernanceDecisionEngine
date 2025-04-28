from datetime import datetime
import logging
import time

from besser.agent.core.agent import Agent
from besser.agent.core.session import Session
from besser.agent.exceptions.logger import logger
from collaboration_metamodel import Interaction
from governance.engine.events import DeadlineEvent, VoteEvent, CollaborationProposalEvent, UserRegistrationEvent
from governance.engine.helpers import find_policies_in, get_all_roles, parse, find_starting_policies_in, start_policies, \
    find_policy_for
from metamodel import Deadline, ComposedPolicy

# Configure the logging module (optional)
logger.setLevel(logging.INFO)

agent = Agent('decision_engine')
# Load agent properties stored in a dedicated file
agent.load_properties('config.ini')
# Define the platform your agent will use
# websocket_platform = agent.use_websocket_platform(use_ui=False)
gh_platform = agent.use_github_platform()


# STATES

idle = agent.new_state('idle', initial=True)
individual_state = agent.new_state('individual')
collab_state = agent.new_state('collab')
vote_state = agent.new_state('vote')
decide_state = agent.new_state('decide')

# GLOBAL VARIABLES

policy = parse('governance/tests/majority_policy.txt')
policy_roles = get_all_roles(policy)
interactions= Interaction()

# STATES BODIES' DEFINITION + TRANSITIONS


# Wait for Collab to be created, Users to vote, or Deadline to finish
idle.when_event(UserRegistrationEvent()).go_to(individual_state)
idle.when_event(CollaborationProposalEvent()).go_to(collab_state)
idle.when_event(VoteEvent()).go_to(vote_state)
idle.when_event(DeadlineEvent()).go_to(decide_state)




def individual_body(session: Session):
    individual_event: UserRegistrationEvent = UserRegistrationEvent.from_github_event(session.event)

    effective_roles = set()
    # for role in individual_event.roles:
    #     if policy_roles[role.lower()]:
    #         effective_roles.add(policy_roles[role.lower()])
    interactions.add_individual(individual_event.login, effective_roles)


individual_state.set_body(individual_body)
individual_state.go_to(idle)


def collab_body(session: Session):
    collab_event: CollaborationProposalEvent = CollaborationProposalEvent.from_github_event(session.event)
    creator = interactions.add_individual(collab_event.creator, ["CREATOR"])
    collab_event.scope.platform = gh_platform
    collab = interactions.propose(creator,
                                  collab_event.id,
                                  collab_event.scope,
                                  collab_event.title + "\n\nComment:\n" + collab_event.rationale)
    for reviewer in collab_event.reviewers:
        interactions.add_individual(reviewer, ["REVIEWER"])

    # TODO : add the search for the appropriate policy (when we will have multiple policies)
    # Since we only have one policy we assume it does match all the scopes
    applicable_policy = find_policy_for({policy}, collab)

    if applicable_policy is not None:
        starting_policies = find_starting_policies_in(applicable_policy)
        start_policies(agent, starting_policies, collab)

collab_state.set_body(collab_body)
collab_state.go_to(idle)

def vote_body(session: Session):
    vote: VoteEvent = VoteEvent.from_github_event(session.event)
    individual = interactions.add_individual(vote.user_login, set())
    collaboration = interactions.collaborations[vote.pull_request_id] or None
    collaboration.vote(individual, vote.agreement, vote.rationale)

vote_state.set_body(vote_body)
vote_state.go_to(idle)

def decide_body(session: Session):
    deadline_event: DeadlineEvent = session.event
    result = interactions.make_decision(deadline_event.collab, deadline_event.policy, agent)

    parent: ComposedPolicy = deadline_event.policy.parent
    while parent is not None:
        known_result = result._accepted if parent.require_all != result._accepted else None
        result = interactions.compose_decision(deadline_event.collab, parent, known_result)
        if result is None:
            break
        parent = parent.parent

    if result is None:
        to_start = find_policies_in(parent, deadline_event.collab)
        start_policies(agent, to_start, deadline_event.collab)

decide_state.set_body(decide_body)
decide_state.go_to(idle)


# RUN APPLICATION

if __name__ == '__main__':
    agent.run()