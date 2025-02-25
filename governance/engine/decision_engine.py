# You may need to add your working directory to the Python path. To do so, uncomment the following lines of code
# import sys
# sys.path.append("/Path/to/directory/agentic-framework") # Replace with your directory path

import logging
import time

from textx import metamodel_from_file

from besser.agent.core.agent import Agent
from besser.agent.core.session import Session
from besser.agent.exceptions.logger import logger
from besser.agent.library.entity.base_entities import any_entity
from besser.agent.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction
from collaboration_metamodel import Interaction, User, TagBased, Collaboration
from governance.language.governance_metamodel import governance_classes, Role, Project, CollabType, Rule, Timer, Condition, WaitForVote

# Configure the logging module (optional)
logger.setLevel(logging.INFO)

agent = Agent('decision_engine')
# Load agent properties stored in a dedicated file
agent.load_properties('config.ini')
# Define the platform your agent will use
websocket_platform = agent.use_websocket_platform(use_ui=True)


# STATES

init = agent.new_state('init', initial=True)
idle = agent.new_state('idle')
user_state = agent.new_state('user')
collab_state = agent.new_state('collab')
vote_for_state = agent.new_state('vote_for')
vote_against_state = agent.new_state('vote_against')
decode_state = agent.new_state('decide')

# GLOBAL VARIABLES

monologue_session = None
metamodel = None
gov_rules: Project = None
interactions: Interaction = None

# CUSTOM EVENTS

def deadline_event_matched(session: 'Session', event_params: dict) -> bool:
    """This event checks if the first event of the session is the expected event

    Args:
        session (Session): the current user session
        event_params (dict): the event parameters

    Returns:
        bool: True if the 2 event are the same, false otherwise
    """
    if session.flags['event']:
        received_event: DeadlineEvent = session.events.pop()
        session.events.append(received_event)
        match received_event.type:
            case "Timer":
                return time.time() > received_event.timestamp
            case "Condition":
                return False # eval received_event._condition
            case "WaitForVote":
                for role in received_event.roles:
                    # Filter Users by roles
                    # Depending on the semantics :
                    #   - at least one user of each role voted
                    #   - all users of this role voted
                    return False

class DeadlineEvent:
    def __init__(self, deadline_type: str, deadline_collab: Collaboration, deadline_rule: Rule,
                 deadline_timestamp: float = None, deadline_condition: str = None, deadline_roles: set[Role] = None):
        self._type: str = deadline_type
        self._collab: Collaboration = deadline_collab
        self._rule: Rule = deadline_rule
        self._timestamp: float = deadline_timestamp
        self._condition: str = deadline_condition
        self._roles: set[Role] = deadline_roles

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
# Intents

user_intent = agent.new_intent('user_intent', [
    'add user NAME with roles ROLES',
    'new user NAME with roles ROLES',
    'create user NAME with roles ROLES',
    'connect user NAME with roles ROLES',
])
user_intent.parameter('name', 'NAME', any_entity)
user_intent.parameter('roles', 'ROLES', any_entity)

collab_intent = agent.new_intent('collab_intent', [
    'add collab NAME about RATIONALE',
    'new collab NAME about RATIONALE',
    'create collab NAME about RATIONALE',
])
collab_intent.parameter('name', 'NAME', any_entity)
collab_intent.parameter('rationale', 'RATIONALE', any_entity)

vote_for_intent = agent.new_intent('vote_for_intent', [
    'vote for NAME because RATIONALE',
    'agree with NAME because RATIONALE',
    'in favor of NAME because RATIONALE',
])
vote_for_intent.parameter('name', 'NAME', any_entity)
vote_for_intent.parameter('rationale', 'RATIONALE', any_entity)

vote_against_intent = agent.new_intent('vote_against_intent', [
    'vote against NAME because RATIONALE',
    'disagree with NAME because RATIONALE',
    'not in favor of NAME because RATIONALE',
])
vote_against_intent.parameter('name', 'NAME', any_entity)
vote_against_intent.parameter('rationale', 'RATIONALE', any_entity)

# STATES BODIES' DEFINITION + TRANSITIONS


def global_fallback_body(session: Session):
    print('Greetings from global fallback')

# Assigned to all agent states (overriding all currently assigned fallback bodies).
agent.set_global_fallback_body(global_fallback_body)


# Parse the governance rules to enforce and store them
def init_body(session: Session):
    global metamodel, gov_rules
    metamodel = metamodel_from_file('governance_language.tx', classes=governance_classes)
    gov_rules = metamodel.model_from_file('tests/test.gov')


init.set_body(init_body)
init.go_to(idle)


# Wait for Collab to be created, Users to vote, or Deadline to finish
def idle_body(session: Session):
    pass

idle.set_body(idle_body)
idle.when_intent_matched_go_to(user_intent, user_state)
idle.when_intent_matched_go_to(collab_intent, collab_state)
idle.when_intent_matched_go_to(vote_for_intent, vote_for_state)
idle.when_intent_matched_go_to(vote_against_intent, vote_against_state)
idle.when_event_go_to(deadline_event_matched, decode_state, {})

def user_body(session: Session):
    predicted_intent: IntentClassifierPrediction = session.predicted_intent
    name = predicted_intent.get_parameter('name').value
    roles_txt = predicted_intent.get_parameter('roles').value
    roles = roles_txt.split(',')
    role_map = {}
    for role in gov_rules.roles:
        role_map[role.name.lower()] = role
    effective_roles = set()
    for role in roles:
        if role_map[role.lower()]:
            effective_roles.add(role_map[role.lower()])
            user = User(name, effective_roles)
    interactions.users.add(user)
    session.set('user', user)


user_state.set_body(user_body)
user_state.go_to(idle)

def collab_body(session: Session):
    predicted_intent: IntentClassifierPrediction = session.predicted_intent
    name = predicted_intent.get_parameter('name').value
    rationale = predicted_intent.get_parameter('rationale').value
    user = session.get('user')
    collab = interactions.propose(user, name, CollabType.TASK, rationale, TagBased(set('code')))
    # Find the applying rules
    applied_rule = None
    for rule in gov_rules.rules:
        same_collab_type = rule.applied_to == collab.type
        included_in_filter = True  # Parse the filter ?
        if same_collab_type and included_in_filter:
            applied_rule = rule
            break
    # Create the Deadline event
    deadline = applied_rule.deadline
    event = None
    if isinstance(deadline, Timer):
        event = DeadlineEvent('Timer', collab, applied_rule, deadline_timestamp=deadline.timestamp)
    elif isinstance(deadline, Condition):
        event = DeadlineEvent('Condition', collab, applied_rule, deadline_condition=deadline.expression)
    elif isinstance(deadline, WaitForVote):
        event = DeadlineEvent('WaitForVote', collab, applied_rule, deadline_roles=deadline.roles)

    monologue_session.events.appendleft(event)

collab_state.set_body(collab_body)
collab_state.go_to(idle)

def vote_for_body(session: Session):
    predicted_intent: IntentClassifierPrediction = session.predicted_intent
    name = predicted_intent.get_parameter('name').value
    rationale = predicted_intent.get_parameter('rationale').value
    user = session.get('user')
    collaboration = interactions.collaborations[name.lower()] or None
    collaboration.vote(user, True, rationale)

vote_for_state.set_body(vote_for_body)
vote_for_state.go_to(idle)

def vote_against_body(session: Session):
    predicted_intent: IntentClassifierPrediction = session.predicted_intent
    name = predicted_intent.get_parameter('name').value
    rationale = predicted_intent.get_parameter('rationale').value
    user = session.get('user')
    collaboration = interactions.collaborations[name.lower()] or None
    collaboration.vote(user, False, rationale)

vote_against_state.set_body(vote_against_body)
vote_against_state.go_to(idle)

def decide_body(session: Session):
    pass

decode_state.set_body(decide_body)
decode_state.go_to(idle)


# RUN APPLICATION

if __name__ == '__main__':
    monologue_session = agent.get_or_create_session("Decision Engine Monologue", None)
    agent.run()

"""
Dynamic info weaving :
Decisions have Rules
Decisions result from Collaborations and are created at the Deadline
at Collaboration creation, pull applicable rules and launch DeadlineEvents
Collaborations have one Decision except for Phased
Collaboration has Metadata
Collaboration has Votes created by Users
Users have Roles

"""