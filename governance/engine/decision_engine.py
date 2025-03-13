# You may need to add your working directory to the Python path. To do so, uncomment the following lines of code
# import sys
# sys.path.append("/Path/to/directory/agentic-framework") # Replace with your directory path
from datetime import datetime
import io
import json
import logging
import time

from antlr4 import (
    InputStream, CommonTokenStream, ParseTreeWalker
)

from besser.agent.core.agent import Agent
from besser.agent.core.session import Session
from besser.agent.exceptions.logger import logger
from collaboration_metamodel import Interaction, TagBased, Collaboration
from governance.engine.events import DeadlineEvent, VoteEvent, CollaborationProposalEvent, UserRegistrationEvent
from grammar import govdslLexer, govdslParser, PolicyCreationListener
from grammar.govErrorListener import govErrorListener
from metamodel import PhasedPolicy, Role, Deadline, Scope, Policy, Individual

# Configure the logging module (optional)
logger.setLevel(logging.INFO)

agent = Agent('decision_engine')
# Load agent properties stored in a dedicated file
agent.load_properties('config.ini')
# Define the platform your agent will use
websocket_platform = agent.use_websocket_platform(use_ui=False)


def setup_parser(text):
    lexer = govdslLexer(InputStream(text))
    stream = CommonTokenStream(lexer)
    parser = govdslParser(stream)

    error = io.StringIO()

    parser.removeErrorListeners()
    error_listener = govErrorListener(error)
    parser.addErrorListener(error_listener)

    return parser

def parse(path):
    with open(path, "r") as file:
        text = file.read()

        # Setup parser and create model
        parser = setup_parser(text)
        tree = parser.policy()

        listener = PolicyCreationListener()
        walker = ParseTreeWalker()
        walker.walk(listener, tree)
        return listener.get_policy()

def get_all_roles(policy):
    roles: dict[str,Role]= dict()
    if isinstance(policy, PhasedPolicy):
        for phase in policy.phases:
            phase_roles = get_all_roles(phase)
            roles = roles | phase_roles
    else:
        for rule in policy.rules:
            for participant in rule.participants:
                if isinstance(participant, Role):
                    roles[participant.name.lower()] = participant

    return roles

def find_rule_for(collab: Collaboration):
    pass
    # # Pseudo-code for the function
    # # create scope/policy mapping
    # # this require scopes to be hashable (see https://docs.python.org/3/glossary.html#term-hashable)
    # # This should work as scopes can be associated to only one policy
    # # WARNING : Verify that you can not create two Scope object representing the same scope (hence having the same hash)
    # mapping = dict()
    # for policy in policies:
    #     mapping[policy.scope] = policy
    #
    #     # Recursive function to search the scope tree
    #     def find_scoped_rule_for(collab: Collaboration, scope: Scope):
    #         pass
    #         # Pseudo-code for the function
    #         policy = mapping[scope]
    #         if policy:
    #             rule = find_rule_in(policy, collab)
    #             if rule:
    #                 return rule
    #         return find_scoped_rule_for(collab, scope.parent)
    #
    # return find_scoped_rule_for(collab, collab.scope)

def find_rule_in(policy: Policy, collab: Collaboration):
    pass
#     if isinstance(policy, PhasedPolicy):
#         for phase in policy.phases:
#             find_rule_in(phase, collab)
#     else: # Then SimplePolicy
#         for rule in policy.rules:
#             # In the current state all defined rules apply to the scope
#             # Two possibilities:
#             #   1. return the first one
#             #   2. use all the rules and apply the first to conclude (Deadline met and valid voting conditions)
#             # TODO : Discuss with Jordi and Adem
#             # For now the first option is implemented
#             return rule
#     return None


# STATES

init = agent.new_state('init', initial=True)
idle = agent.new_state('idle')
individual_state = agent.new_state('individual')
collab_state = agent.new_state('collab')
vote_state = agent.new_state('vote')
decide_state = agent.new_state('decide')

# GLOBAL VARIABLES

monologue_session = None
policy = parse('tests/majority_policy.txt')
policy_roles = get_all_roles(policy)
interactions= Interaction()

# STATES BODIES' DEFINITION + TRANSITIONS

def global_fallback_body(session: Session):
    print('Greetings from global fallback')

# Assigned to all agent states (overriding all currently assigned fallback bodies).
agent.set_global_fallback_body(global_fallback_body)


# Parse the governance rules to enforce and store them
def init_body(session: Session):
    pass


init.set_body(init_body)
init.go_to(idle)


# Wait for Collab to be created, Users to vote, or Deadline to finish
def idle_body(session: Session):
    pass

idle.set_body(idle_body)
idle.when_event(UserRegistrationEvent()).go_to(individual_state)
idle.when_event(CollaborationProposalEvent()).go_to(collab_state)
idle.when_event(VoteEvent()).go_to(vote_state)
idle.when_event(DeadlineEvent())\
    .with_condition(lambda session : time.time() > session.event.timestamp)\
    .go_to(decide_state)

def individual_body(session: Session):
    individual_event: UserRegistrationEvent = session.event
        
    effective_roles = set()
    for role in individual_event.roles:
        if policy_roles[role.lower()]:
            effective_roles.add(policy_roles[role.lower()])
    individual = interactions.new_individual(individual_event.name, effective_roles)
    session.set('individual', individual)


individual_state.set_body(individual_body)
individual_state.go_to(idle)


def collab_body(session: Session):
    collab_event: CollaborationProposalEvent = session.event
    individual = session.get('individual')
    collab = interactions.propose(individual,
                                  collab_event.name,
                                  collab_event.scope,
                                  collab_event.rationale,
                                  TagBased(set('code')))
    # TODO : add the search for the appropriate policy (when we will have multiple policies)
    # Since we only have one policy we assume it does match all the scopes

    # Pseudocode for the policy search
    for rule in policy.rules:
        # Find deadlines and send the associated events
        deadlines = [d for d in rule.conditions if isinstance(d, Deadline)]
        for deadline in deadlines:
            if deadline.date is not None:
                timestamp = deadline.date.timestamp()
                agent.receive_event(DeadlineEvent(collab, rule, timestamp, monologue_session.id))
            else:
                timestamp = (datetime.now() + deadline.offset).timestamp()
                agent.receive_event(DeadlineEvent(collab, rule, timestamp, monologue_session.id))

collab_state.set_body(collab_body)
collab_state.go_to(idle)

def vote_body(session: Session):
    vote: VoteEvent = session.event
    individual = session.get('individual')
    collaboration = interactions.collaborations[vote.name.lower()] or None
    collaboration.vote(individual, vote.agreement, vote.rationale)

vote_state.set_body(vote_body)
vote_state.go_to(idle)

def decide_body(session: Session):
    deadline_event: DeadlineEvent = session.event
    
    interactions.make_decision(deadline_event.collab, deadline_event.rule)

decide_state.set_body(decide_body)
decide_state.go_to(idle)


# RUN APPLICATION

if __name__ == '__main__':
    monologue_session = agent.get_or_create_session("Decision Engine Monologue", None)
    agent.run()