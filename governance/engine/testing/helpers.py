from datetime import datetime

from besser.agent.core.agent import Agent

from governance.engine.events import DeadlineEvent
from metamodel import Policy, ComposedPolicy


def start_testing_policies(agent: Agent, policies: list[Policy], collab: 'Collaboration') -> None:
    for starting_policy in policies:
        collab.ballot_boxes[starting_policy] = set()
        if isinstance(starting_policy, ComposedPolicy):
            continue

        timestamp = datetime.now().timestamp()
        timestamp += 1
        agent.receive_event(DeadlineEvent(collab, starting_policy, timestamp))