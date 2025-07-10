import base64
import os

from aiohttp import ClientSession
from besser.agent.core.session import Session
from besser.agent.library.transition.events.base_events import ReceiveFileEvent
from besser.agent.library.transition.events.github_webhooks_events import GitHubEvent
from besser.agent.exceptions.logger import logger
from besser.agent.platforms.github.github_objects import Issue
from gidgethub.aiohttp import GitHubAPI

from governance.engine.parsing import parse_text
from governance.engine.semantics.collaboration_metamodel import Interaction
from governance.engine.events import DeadlineEvent, VoteEvent, CollaborationProposalEvent, UserRegistrationEvent, \
    UpdatePolicyEvent
from governance.engine.semantics.helpers import find_policies_in, find_starting_policies_in, start_policies, \
    find_policy_for
from governance.engine.testing.helpers import start_testing_policies
from metamodel import ComposedPolicy
from utils.gh_extension import Patch, PullRequest, ActionEnum


def init_body(session: Session):
    session.set("policies", None)
    session.set("interactions", Interaction())

def read_policy_bodybuilder(agent):
    def read_policy_body(session: Session):
        event: ReceiveFileEvent = session.event
        text = base64.b64decode(event.file.base64).decode('utf-8')
        agent.receive_event(UpdatePolicyEvent(text))
    return read_policy_body

def update_policy_body(session: Session):
    update_event: UpdatePolicyEvent = session.event
    session.set("policies", parse_text(update_event.text))

def gh_webhooks_bodybuilder(agent):
    def gh_webhooks_body(session: Session):
        event: GitHubEvent = session.event
        if event.action == "assigned":
            agent.receive_event(UserRegistrationEvent.from_github_event(event))
        elif event.action == "opened":
            agent.receive_event(CollaborationProposalEvent.from_github_event(event))
        elif event.action == "submitted":
            agent.receive_event(VoteEvent.from_github_event(event))
        elif event.action == "update":
            agent.receive_event(UpdatePolicyEvent(event.payload["file_content"]))
    return gh_webhooks_body

def individual_body(session: Session):
    individual_event: UserRegistrationEvent = session.event

    effective_roles = set()
    # for role in individual_event.roles:
    #     if policy_roles[role.lower()]:
    #         effective_roles.add(policy_roles[role.lower()])
    session.get("interactions").get_or_create_dynamic_individual(individual_event.login, effective_roles)

def collab_bodybuilder(platform, agent):
    start_function = start_testing_policies if os.environ.get("ENGINE_TESTING") == "True" else start_policies
    def collab_body(session: Session):
        collab_event: CollaborationProposalEvent = session.event
        creator = session.get("interactions").get_or_create_dynamic_individual(collab_event.creator)
        collab_event.scope.platform = platform
        collab = session.get("interactions").propose(creator,
                                      collab_event.id,
                                      collab_event.scope,
                                      collab_event.rationale)

        # TODO : add the search for the appropriate policy (when we will have multiple policies)
        # Since we only have one policy we assume it does match all the scopes
        applicable_policy = find_policy_for(session.get("policies"), collab)

        if applicable_policy is not None:
            starting_policies = find_starting_policies_in(applicable_policy)
            start_function(agent, starting_policies, collab)
    return collab_body


def vote_body(session: Session):
    vote: VoteEvent = session.event
    individual = session.get("interactions").get_or_create_dynamic_individual(vote.user_login)
    collaboration = session.get("interactions").collaborations[vote.pull_request_id] or None
    if collaboration is not None:
        collaboration.vote(individual, vote.agreement, vote.rationale)

def decide_bodybuilder(platform, agent):
    start_function = start_testing_policies if os.environ.get("ENGINE_TESTING") == "True" else start_policies
    def decide_body(session: Session):
        deadline_event: DeadlineEvent = session.event
        result = session.get("interactions").make_decision(deadline_event.collab, deadline_event.policy, agent)

        parent: ComposedPolicy = deadline_event.policy.parent
        while parent is not None:
            known_result = result._accepted if parent.require_all != result._accepted else None
            result = session.get("interactions").compose_decision(deadline_event.collab, parent, known_result)
            if result is None:
                break
            parent = parent.parent

        if result is None:
            to_start = find_policies_in(parent, deadline_event.collab)
            start_function(agent, to_start, deadline_event.collab)
        elif result._accepted:
            scope = deadline_event.policy.scope
            if isinstance(scope, Patch):
                if scope.action == ActionEnum.MERGE:
                    pr = deadline_event.collab.scope.element
                    if isinstance(pr, PullRequest):
                        platform.put(f"/repos/{scope.activity.project.repo_id}/pulls/{pr.payload["number"]}/merge",
                            data={
                                "commit_title":"Validated Merge",
                                "commit_message":"Merge of a pull request validated by the decision engine"
                            })
    return decide_body