import json

from besser.agent.core.session import Session
from besser.agent.library.transition.events.github_webhooks_events import GitHubEvent

from governance.engine.semantics.collaboration_metamodel import Interaction, Decision, Vote
from governance.engine.testing.platform_mock import PlatformMock


def clear_body(session: Session):
    session.events.clear()
    session.set("interactions", Interaction())
    session.delete("test_result_path")

def result_body(session: Session):
    event: GitHubEvent = session.event
    policy_name = event.payload["name"]

    interactions: Interaction = session.get("interactions")
    result: Decision = None
    for decision in interactions.decisions:
        if decision._rule.name == policy_name:
            result = decision
            break

    def get_login(vote: Vote):
        return vote.voted_by.name
    struct = {"acceptance": None,
           "voters": None}
    if result is not None:
        struct = {"acceptance": result._accepted,
              "voters": list(map(get_login, result._votes))}

    path = session.get("test_result_path")
    with open(path, "w") as file:
        file.write(json.dumps(struct))

def link_body(session: Session):
    event: GitHubEvent = session.event
    session.set("test_result_path", event.payload["path"])

def mock_bodybuilder(platform: PlatformMock):
    def mock_body(session: Session):
        event: GitHubEvent = session.event
        platform.payload = event.payload
    return mock_body

def add_testing_hooks(agent, idle, platform: PlatformMock):
    # STATES
    clear = agent.new_state('clear')
    result = agent.new_state('result')
    link = agent.new_state('link')
    mock = agent.new_state('mock')
    # EVENTS
    clear_event = GitHubEvent("clear", "clear", None)
    result_event = GitHubEvent("result", "result", None)
    link_event = GitHubEvent("link", "link", None)
    mock_event = GitHubEvent("mock", "mock", None)
    # BODIES
    clear.set_body(clear_body)
    result.set_body(result_body)
    link.set_body(link_body)
    mock.set_body(mock_bodybuilder(platform))
    # TRANSITIONS
    idle.when_event(clear_event).go_to(clear)
    clear.go_to(idle)
    idle.when_event(result_event).go_to(result)
    result.go_to(idle)
    idle.when_event(link_event).go_to(link)
    link.go_to(idle)
    idle.when_event(mock_event).go_to(mock)
    mock.go_to(idle)