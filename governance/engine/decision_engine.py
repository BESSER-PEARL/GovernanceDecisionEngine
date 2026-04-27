import argparse
import logging
import os
import subprocess

from besser.agent.core.agent import Agent
from besser.agent.core.session import Session
from besser.agent.exceptions.logger import logger
from besser.agent.library.transition.events.base_events import ReceiveFileEvent
from besser.agent.library.transition.events.github_webhooks_events import PullRequestAssigned, GitHubEvent, \
    PullRequestOpened, IssuesOpened, Push
from besser.agent.library.transition.events.gitlab_webhooks_events import MergeRequestApproved, GitLabEvent, \
    MergeRequestOpened, MergeRequestUnapproved, MergeRequestApproval, MergeRequestUpdated

from governance.engine.events import DeadlineEvent, VoteEvent, CollaborationProposalEvent, UserRegistrationEvent, \
    UpdatePolicyEvent, DecideEvent
from governance.engine.parsing import parse_text
from governance.engine.semantics.helpers import get_all_individuals, get_all_roles
from governance.engine.semantics.runtime_metamodel import Interaction
from governance.engine.state_bodies import individual_body, vote_body, collab_bodybuilder, \
    decide_bodybuilder, gh_webhooks_bodybuilder, update_policy_body, init_body, read_policy_bodybuilder, \
    gl_webhooks_bodybuilder, deadline_body
from governance.engine.testing.hooks import add_testing_hooks
from governance.engine.testing.platform_mock import PlatformMock

logger.setLevel(logging.INFO)

def setup(testing: bool, playground: bool, init_policy_path: str) -> Agent:
    agent = Agent('decision_engine')
    agent.load_properties('config.yaml')

    if not testing and not playground:
        websocket_platform = agent.use_websocket_platform(use_ui=(not playground))
    gh_platform = agent.use_github_platform()
    # gl_platform = agent.use_gitlab_platform()


    # STATES
    init = agent.new_state('init', initial=True)
    idle = agent.new_state('idle')
    read_policy = agent.new_state('read_policy')
    gh_webhooks = agent.new_state('gh_webhooks')
    # gl_webhooks = agent.new_state('gl_webhooks')
    update_policy = agent.new_state('update')
    individual_state = agent.new_state('individual')
    collab_state = agent.new_state('collab')
    vote_state = agent.new_state('vote')
    deadline_state = agent.new_state('deadline')
    decide_state = agent.new_state('decide')


    # STATES BODIES' LINKING
    init.set_body(init_body)
    read_policy.set_body(read_policy_bodybuilder(agent))

    test_platform = PlatformMock(agent)
    gh_webhooks.set_body(gh_webhooks_bodybuilder(agent, test_platform if testing else gh_platform))
    # gl_webhooks.set_body(gl_webhooks_bodybuilder(agent, test_platform if testing else gl_platform))

    update_policy.set_body(update_policy_body)
    individual_state.set_body(individual_body)
    collab_state.set_body(collab_bodybuilder(agent))
    vote_state.set_body(vote_body)
    deadline_state.set_body(deadline_body)
    decide_state.set_body(decide_bodybuilder(agent))

    # ADDITIONAL HOOKS AND FEATURES FOR TESTING
    if testing:
        add_testing_hooks(agent, idle, test_platform)

    # MANAGING INITIAL POLICY AS PARAM

    if init_policy_path is not None:
        with open(init_policy_path, "r") as file:
            data = file.read()
            def init_playground(session: Session):
                session.set("interactions", Interaction())
                model = parse_text(data)
                session.set("policies", model)
                interact = session.get("interactions")

                individuals = set()
                for policy in model:
                    individuals = individuals.union(get_all_individuals(policy))
                roles = set()
                for policy in model:
                    roles = roles.union(get_all_roles(policy))
                interact.register_individuals(individuals)
                interact.register_roles(roles)
            init.set_body(init_playground)

    # TRANSITIONS DEFINITION

    if testing:
        # testing setup
        init.go_to(idle)
        idle.when_event(GitHubEvent("policy", "update", None)).go_to(gh_webhooks)
    elif playground:
        init.go_to(idle)
    else:
        # production setup
        init.when_event(ReceiveFileEvent()).go_to(read_policy)
        idle.when_event(ReceiveFileEvent()).go_to(read_policy)

    # translate platform input to workflow events
    idle.when_event(PullRequestAssigned()).go_to(gh_webhooks)
    idle.when_event(PullRequestOpened()).go_to(gh_webhooks)
    idle.when_event(IssuesOpened()).go_to(gh_webhooks)
    idle.when_event(GitHubEvent("pull_request_review","submitted", None)).go_to(gh_webhooks)
    # idle.when_event(MergeRequestUpdated()).go_to(gl_webhooks)
    # idle.when_event(MergeRequestOpened()).go_to(gl_webhooks)
    # idle.when_event(MergeRequestApproval()).go_to(gl_webhooks)
    # idle.when_event(MergeRequestUnapproved()).go_to(gl_webhooks)

    # map workflow events to dedicated states
    idle.when_event(VoteEvent()).go_to(vote_state)
    idle.when_event(DecideEvent()).go_to(decide_state)
    idle.when_event(DeadlineEvent()).go_to(deadline_state)
    idle.when_event(UpdatePolicyEvent()).go_to(update_policy)
    idle.when_event(UserRegistrationEvent()).go_to(individual_state)
    idle.when_event(CollaborationProposalEvent()).go_to(collab_state)


    # when event managed go back to idle
    read_policy.go_to(idle)
    gh_webhooks.go_to(idle)
    # gl_webhooks.go_to(idle)
    update_policy.go_to(idle)
    individual_state.go_to(idle)
    collab_state.go_to(idle)
    vote_state.go_to(idle)
    deadline_state.go_to(idle)
    decide_state.go_to(idle)

    return agent


# RUN APPLICATION

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Governance Decision Engine',
        description='Agent in charge of enforcing governance policies expressed using the Governance DSL.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-t','--test', action='store_true',
                        help='Start the engine in testing mode (add features and hooks for automatic testing)')
    group.add_argument('-p', '--playground', action='store_true',
                        help='Start the engine in Playground mode')
    parser.add_argument('-P', '--Policy',
                        help='Start the engine with base policy')
    args = parser.parse_args()
    os.environ["ENGINE_TESTING"] = str(args.test)
    os.environ["ENGINE_PLAYGROUND"] = str(args.playground)
    policy_file = str(args.Policy) if args.Policy is not None else None
    if args.playground:
        os.environ["PLAYGROUND_POLICY"] = policy_file
    agent = setup(args.test, args.playground, policy_file)
    agent.run()