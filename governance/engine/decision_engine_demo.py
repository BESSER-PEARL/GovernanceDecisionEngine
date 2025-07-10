import argparse
import logging
import os

from besser.agent.core.agent import Agent
from besser.agent.exceptions.logger import logger
from besser.agent.library.transition.events.base_events import ReceiveFileEvent
from besser.agent.library.transition.events.github_webhooks_events import PullRequestAssigned, GitHubEvent, \
    PullRequestOpened

from governance.engine.events import DeadlineEvent, VoteEvent, CollaborationProposalEvent, UserRegistrationEvent, \
    UpdatePolicyEvent
from governance.engine.state_bodies import individual_body, vote_body, collab_bodybuilder, \
    decide_bodybuilder, gh_webhooks_bodybuilder, update_policy_body, init_body, read_policy_bodybuilder
from governance.engine.testing.hooks import add_testing_hooks
from governance.engine.testing.platform_mock import PlatformMock

logger.setLevel(logging.INFO)

def setup(testing: bool) -> Agent:
    logger.info(os.getcwd())
    agent = Agent('decision_engine')
    agent.load_properties('../../config.ini')

    if not testing:
        websocket_platform = agent.use_websocket_platform(use_ui=True)
    gh_platform = agent.use_github_platform()


    # STATES
    init = agent.new_state('init', initial=True)
    idle = agent.new_state('idle')
    read_policy = agent.new_state('read_policy')
    gh_webhooks = agent.new_state('gh_webhooks')
    update_policy = agent.new_state('update')
    individual_state = agent.new_state('individual')
    collab_state = agent.new_state('collab')
    vote_state = agent.new_state('vote')
    decide_state = agent.new_state('decide')


    # STATES BODIES' LINKING
    init.set_body(init_body)
    read_policy.set_body(read_policy_bodybuilder(agent))
    gh_webhooks.set_body(gh_webhooks_bodybuilder(agent))
    update_policy.set_body(update_policy_body)
    individual_state.set_body(individual_body)
    platform = PlatformMock(agent) if testing else gh_platform
    os.environ["ENGINE_TESTING"] = "True"
    collab_state.set_body(collab_bodybuilder(platform, agent))
    os.environ["ENGINE_TESTING"] = "False"
    vote_state.set_body(vote_body)
    decide_state.set_body(decide_bodybuilder(gh_platform,agent))


    # TRANSITIONS DEFINITION

    if testing:
        # testing setup
        init.go_to(idle)
        idle.when_event(GitHubEvent("policy", "update", None)).go_to(gh_webhooks)
    else:
        # production setup
        init.when_event(ReceiveFileEvent()).go_to(read_policy)
        idle.when_event(ReceiveFileEvent()).go_to(read_policy)

    # translate platform input to workflow events
    idle.when_event(PullRequestAssigned()).go_to(gh_webhooks)
    idle.when_event(PullRequestOpened()).go_to(gh_webhooks)
    idle.when_event(GitHubEvent("pull_request_review","submitted", None)).go_to(gh_webhooks)

    # map workflow events to dedicated states
    idle.when_event(UpdatePolicyEvent()).go_to(update_policy)
    idle.when_event(UserRegistrationEvent()).go_to(individual_state)
    idle.when_event(CollaborationProposalEvent()).go_to(collab_state)
    idle.when_event(VoteEvent()).go_to(vote_state)
    idle.when_event(DeadlineEvent()).go_to(decide_state)

    # when event managed go back to idle
    read_policy.go_to(idle)
    gh_webhooks.go_to(idle)
    update_policy.go_to(idle)
    individual_state.go_to(idle)
    collab_state.go_to(idle)
    vote_state.go_to(idle)
    decide_state.go_to(idle)

    # ADDITIONAL HOOKS AND FEATURES FOR TESTING
    if testing:
        add_testing_hooks(agent, idle, platform)

    return agent


# RUN APPLICATION

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Governance Decision Engine',
        description='Agent in charge of enforcing governance policies expressed using the Governance DSL.')
    parser.add_argument('-t','--test', action='store_true',
                        help='Start the engine in testing mode (add features and hooks for automatic testing)')
    args = parser.parse_args()
    os.environ["ENGINE_TESTING"] = str(args.test)
    agent = setup(args.test)
    agent.run()