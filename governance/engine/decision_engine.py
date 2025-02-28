# You may need to add your working directory to the Python path. To do so, uncomment the following lines of code
# import sys
# sys.path.append("/Path/to/directory/agentic-framework") # Replace with your directory path
import json
import logging
import time

from textx import metamodel_from_file

from besser.agent.core.agent import Agent
from besser.agent.core.event import ReceiveMessageEvent, Event
from besser.agent.core.session import Session
from besser.agent.exceptions.logger import logger
from collaboration_metamodel import Interaction, User, TagBased, Collaboration
from governance.language.governance_metamodel import governance_classes, Role, Project, CollabType, Rule, Timer, Condition, WaitForVote

# Configure the logging module (optional)
logger.setLevel(logging.INFO)

agent = Agent('decision_engine')
# Load agent properties stored in a dedicated file
agent.load_properties('config.ini')
# Define the platform your agent will use
websocket_platform = agent.use_websocket_platform(use_ui=False)


# STATES

init = agent.new_state('init', initial=True)
idle = agent.new_state('idle')
user_state = agent.new_state('user')
collab_state = agent.new_state('collab')
vote_state = agent.new_state('vote')
decide_state = agent.new_state('decide')

# GLOBAL VARIABLES

monologue_session = None
metamodel = metamodel_from_file('governance/language/governance_language.tx', classes=governance_classes)
gov_rules = metamodel.model_from_file('tests/test.gov')
interactions= Interaction()

# CUSTOM EVENTS AND COND

def deadline_valid(session: 'Session') -> bool:
    """This condition checks if the deadline event is valid

    Args:
        session (Session): the current user session

    Returns:
        bool: True if the deadline is valid
    """
    match session.event.type:
        case "Timer":
            return time.time() > session.event.timestamp
        case "Condition":
            return False # eval session.event._condition
        case "WaitForVote":
            for role in session.event.roles:
                # Filter Users by roles
                # Depending on the semantics :
                #   - at least one user of each role voted
                #   - all users of this role voted
                return False

class DeadlineEvent(Event):
    def __init__(self, deadline_type: str, deadline_collab: Collaboration, deadline_rule: Rule,
                 deadline_timestamp: float = None, deadline_condition: str = None, deadline_roles: set[Role] = None):
        if deadline_collab is None:
            super().__init__("deadline")
        else:
            super().__init__(deadline_collab._id+"_deadline", monologue_session.id)
        self._type: str = deadline_type
        self._collab: Collaboration = deadline_collab
        self._rule: Rule = deadline_rule
        self._timestamp: float = deadline_timestamp
        self._condition: str = deadline_condition
        self._roles: set[Role] = deadline_roles

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

    @property
    def condition(self):
        return self._condition

    @property
    def roles(self):
        return self._roles


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
idle.when_event(DeadlineEvent(None,None,None))\
    .with_condition(deadline_valid)\
    .go_to(decide_state)

def user_body(session: Session):
    message = json.loads(session.event.message)
    name = message["name"]
    roles = message["roles"]

    # TODO: avoid recomputing
    role_map = {}
    for role in gov_rules.roles:
        role_map[role.name.lower()] = role
        
    effective_roles = set()
    for role in roles:
        if role_map[role.lower()]:
            effective_roles.add(role_map[role.lower()])
    user = User(interactions, name, effective_roles)
    interactions.users.add(user)
    session.set('user', user)


user_state.set_body(user_body)
user_state.go_to(idle)

def collab_body(session: Session):
    message = json.loads(session.event.message)
    name = message["name"]
    rationale = message["rationale"]
    user = session.get('user')
    collab = interactions.propose(user, name, CollabType.TASK, rationale, TagBased(set('code')))
    # Find the applying rules
    applied_rule: Rule = None
    for rule in gov_rules.rules:
        same_collab_type = rule._applied_to == collab.type
        included_in_filter = True  # Parse the filter ?
        if same_collab_type and included_in_filter:
            applied_rule = rule
            break
    # Create the Deadline event
    deadline = applied_rule.deadline
    event = None
    if isinstance(deadline, Timer):
        event = DeadlineEvent('Timer', collab, applied_rule, deadline_timestamp=time.time()+deadline.timestamp)
    elif isinstance(deadline, Condition):
        event = DeadlineEvent('Condition', collab, applied_rule, deadline_condition=deadline.expression)
    elif isinstance(deadline, WaitForVote):
        event = DeadlineEvent('WaitForVote', collab, applied_rule, deadline_roles=deadline.roles)
    # send the event to the agent
    agent.receive_event(event)

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