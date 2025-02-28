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
from besser.agent.core.event import ReceiveMessageEvent, Event
from besser.agent.core.session import Session
from besser.agent.exceptions.logger import logger
from collaboration_metamodel import Interaction, User, TagBased, Collaboration
from grammar import govdslLexer, govdslParser, PolicyCreationListener
from grammar.govErrorListener import govErrorListener
from metamodel import PhasedPolicy, Role, Rule, Deadline

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
# STATES

init = agent.new_state('init', initial=True)
idle = agent.new_state('idle')
user_state = agent.new_state('user')
collab_state = agent.new_state('collab')
vote_state = agent.new_state('vote')
decide_state = agent.new_state('decide')

# GLOBAL VARIABLES

monologue_session = None
policy = parse('tests/majority_policy.txt')
policy_roles = get_all_roles(policy)
interactions= Interaction()

# CUSTOM EVENTS AND COND

class DeadlineEvent(Event):
    def __init__(self, deadline_collab: Collaboration = None, deadline_rule: Rule = None,
                 deadline_timestamp: float = None):
        if deadline_collab is None:
            super().__init__("deadline")
        else:
            super().__init__(deadline_collab._id+"_deadline", monologue_session.id)
        self._collab: Collaboration = deadline_collab
        self._rule: Rule = deadline_rule
        self._timestamp: float = deadline_timestamp

    def is_matching(self, event: 'Event') -> bool:
        return isinstance(event, DeadlineEvent)

    @property
    def type(self):
        return self._type

    @property
    def collab(self):
        return self._collab

    @property
    def rule(self):
        return self._rule

    @property
    def timestamp(self):
        return self._timestamp


# STATES BODIES' DEFINITION + TRANSITIONS

def cond_req_type(req_type: str):
    def cond(session):
        struct = json.loads(session.event.message)
        return struct["req_type"] == req_type
    return cond


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
idle.when_event(ReceiveMessageEvent())\
    .with_condition(cond_req_type('user'))\
    .go_to(user_state)
idle.when_event(ReceiveMessageEvent())\
    .with_condition(cond_req_type('collab'))\
    .go_to(collab_state)
idle.when_event(ReceiveMessageEvent())\
    .with_condition(cond_req_type('vote'))\
    .go_to(vote_state)
idle.when_event(DeadlineEvent())\
    .with_condition(lambda session : time.time() > session.event.timestamp)\
    .go_to(decide_state)

def user_body(session: Session):
    message = json.loads(session.event.message)
    name = message["name"]
    roles = message["roles"]
        
    effective_roles = set()
    for role in roles:
        if policy_roles[role.lower()]:
            effective_roles.add(policy_roles[role.lower()])
    user = User(interactions, name, effective_roles)
    interactions.users.add(user)
    session.set('user', user)


user_state.set_body(user_body)
user_state.go_to(idle)

def collab_body(session: Session):
    message = json.loads(session.event.message)
    name = message["name"]
    rationale = message["rationale"]
    scope = message["scope"]
    user = session.get('user')
    collab = interactions.propose(user, name, scope, rationale, TagBased(set('code')))

    for rule in policy.rules:
        # Find deadlines and send the associated events
        deadlines = [d for d in rule.conditions if isinstance(d, Deadline)]
        for deadline in deadlines:
            if deadline.date is not None:
                timestamp = deadline.date.timestamp()
                agent.receive_event(DeadlineEvent(collab, rule, timestamp))
            else:
                timestamp = (datetime.now() + deadline.offset).timestamp()
                agent.receive_event(DeadlineEvent(collab, rule, timestamp))

collab_state.set_body(collab_body)
collab_state.go_to(idle)

def vote_body(session: Session):
    message = json.loads(session.event.message)
    name = message["name"]
    agreement = message["agreement"]
    rationale = message["rationale"]
    user = session.get('user')
    collaboration = interactions.collaborations[name.lower()] or None
    collaboration.vote(user, agreement, rationale)

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