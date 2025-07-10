from datetime import datetime

from besser.agent.core.transition.event import Event
from besser.agent.library.transition.events.github_webhooks_events import PullRequestOpened, GitHubEvent, \
    PullRequestAssigned

from metamodel import SinglePolicy, Scope, Task, StatusEnum, Activity
from utils.gh_extension import Patch, PullRequest, ActionEnum, Repository
from besser.agent.exceptions.logger import logger


class DeadlineEvent(Event):
    def __init__(self, deadline_collab=None, deadline_policy: SinglePolicy = None,
                 deadline_timestamp: float = None, session_id: str = None):
        if deadline_collab is None:
            super().__init__("deadline")
        else:
            super().__init__(str(deadline_collab._id) + "_deadline")
        self._collab = deadline_collab
        self._policy: SinglePolicy = deadline_policy
        self._timestamp: float = deadline_timestamp

    def is_matching(self, event: 'Event') -> bool:
        return isinstance(event, DeadlineEvent) and datetime.now().timestamp() > event._timestamp

    @property
    def collab(self):
        return self._collab

    @property
    def policy(self):
        return self._policy

    @property
    def timestamp(self):
        return self._timestamp


class EngineEvent(Event):
    def __init__(self, name, payload=None):
        super().__init__(name)
        self.payload = payload


class UpdatePolicyEvent(EngineEvent):
    def __init__(self, text=''):
        super().__init__('UpdatePolicyEvent', text)
        self.text = text


class UserRegistrationEvent(EngineEvent):
    def __init__(self, payload=None):
        super().__init__('UserRegistrationEvent',  payload)

    @classmethod
    def from_github_event(cls, event: GitHubEvent):
        return cls(payload=event.payload)

    @property
    def login(self):
        return self.payload["assignee"]["login"]

    @property
    def roles(self):
        return ["REVIEWER"]


class CollaborationProposalEvent(EngineEvent):
    def __init__(self, payload=None):
        super().__init__('CollaborationProposalEvent',  payload)

    @classmethod
    def from_github_event(cls, event: GitHubEvent):
        return cls(payload=event.payload)

    @property
    def id(self):
        logger.info("ID : " + str(self.payload["pull_request"]["id"]))
        return self.payload["pull_request"]["id"]

    @property
    def creator(self):
        return self.payload["pull_request"]["user"]["login"]

    @property
    def rationale(self):
        return self.payload["pull_request"]["title"]

    @property
    def scope(self):
        repoID = self.payload["repository"]["full_name"]
        title = f"Pull Request #{self.payload['pull_request']['id']} of {repoID}"
        labels_payload = self.payload["pull_request"]["labels"]
        labels = set()
        for label in labels_payload:
            labels.add(label["name"])
        pr = PullRequest(title, labels)
        pr.payload = self.payload["pull_request"]
        scope = Patch(title, StatusEnum.ACCEPTED, ActionEnum.ALL, pr)


        scope.activity = Activity("", StatusEnum.ACCEPTED)
        scope.activity.tasks = {scope}
        scope.activity.project = Repository("Repository "+repoID, StatusEnum.ACCEPTED, repoID)
        scope.activity.project.activities = {scope.activity}
        return scope


class VoteEvent(EngineEvent):
    def __init__(self, payload=None):
        super().__init__('VoteEvent',  payload)

    @classmethod
    def from_github_event(cls, event: GitHubEvent):
        return cls(payload=event.payload)

    @property
    def user_login(self):
        return self.payload["review"]["user"]["login"]

    @property
    def pull_request_id(self):
        return self.payload["pull_request"]["id"]

    @property
    def role(self):
        # Is one of the following : COLLABORATOR, CONTRIBUTOR, FIRST_TIMER, FIRST_TIME_CONTRIBUTOR, MANNEQUIN, MEMBER, NONE, OWNER
        return self.payload["review"]["author_association"]

    @property
    def agreement(self):
        return self.payload["review"]["state"] == "APPROVED"

    @property
    def rationale(self):
        return self.payload["review"]["body"]
