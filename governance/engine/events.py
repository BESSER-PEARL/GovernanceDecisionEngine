from datetime import datetime

from besser.agent.core.transition.event import Event
from besser.agent.library.transition.events.github_webhooks_events import PullRequestOpened, GitHubEvent, \
    PullRequestAssigned
from besser.agent.library.transition.events.gitlab_webhooks_events import GitLabEvent

from metamodel import SinglePolicy, Scope, Task, StatusEnum, Activity
from utils.chp_extension import Patch, PullRequest, PatchAction, Repository
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

class DecideEvent(Event):
    def __init__(self, decide_collab=None, decide_policy: SinglePolicy = None):
        if decide_collab is None:
            super().__init__("decide")
        else:
            super().__init__(str(decide_collab._id) + "_decide")
        self._collab = decide_collab
        self._policy: SinglePolicy = decide_policy

    def is_matching(self, event: 'Event') -> bool:
        return isinstance(event, DecideEvent)

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
        self._login = None
        self._roles = None

    @classmethod
    def from_github_event(cls, event: GitHubEvent):
        the_event = cls(payload=event.payload)
        the_event._login = event.payload["assignee"]["login"]
        the_event._roles = ["REVIEWER"]
        return the_event

    @classmethod
    def from_gitlab_event(cls, event: GitLabEvent):
        the_event = cls(payload=event.payload)
        the_event._login = event.payload["assignee"]["login"]
        the_event._roles = ["REVIEWER"]
        return the_event

    @property
    def login(self):
        return self._login

    @property
    def roles(self):
        return self._roles


class CollaborationProposalEvent(EngineEvent):
    def __init__(self, payload=None):
        super().__init__('CollaborationProposalEvent',  payload)
        self._id = None
        self._creator = None
        self._rationale = None
        self._repoID = None
        self._PR_payload = None
        self._labels = set()
        self._platform = None

    @classmethod
    def from_github_event(cls, event: GitHubEvent, platform):
        the_event = cls(payload=event.payload)
        the_event._id = event.payload["pull_request"]["id"]
        the_event._creator = event.payload["pull_request"]["user"]["login"]
        the_event._rationale = event.payload["pull_request"]["title"]
        the_event._repoID = event.payload["repository"]["full_name"]
        the_event._PR_payload = event.payload["pull_request"]
        the_event._platform = platform
        labels_payload = event.payload["pull_request"]["labels"]
        for label in labels_payload:
            the_event._labels.add(label["name"])
        return the_event

    @classmethod
    def from_gitlab_event(cls, event: GitLabEvent, platform):
        the_event = cls(payload=event.payload)
        the_event._id = event.payload["pull_request"]["id"]
        the_event._creator = event.payload["pull_request"]["user"]["login"]
        the_event._rationale = event.payload["pull_request"]["title"]
        the_event._repoID = event.payload["repository"]["full_name"]
        the_event._PR_payload = event.payload["pull_request"]
        the_event._platform = platform
        labels_payload = event.payload["pull_request"]["labels"]
        for label in labels_payload:
            the_event._labels.add(label["name"])
        return the_event

    @property
    def id(self):
        logger.info("ID : " + str(self._id))
        return self._id

    @property
    def creator(self):
        return self._creator

    @property
    def rationale(self):
        return self._rationale

    @property
    def scope(self):
        title = f"Pull Request #{self.id} of {self._repoID}"
        pr = PullRequest(title, self._labels)
        pr.payload = self._PR_payload
        scope = Patch(title, StatusEnum.ACCEPTED, PatchAction.ALL, pr)


        scope.activity = Activity("", StatusEnum.ACCEPTED)
        scope.activity.tasks = {scope}
        scope.activity.project = Repository("Repository "+self._repoID, StatusEnum.ACCEPTED, self._repoID)
        scope.activity.project.activities = {scope.activity}
        return scope


class VoteEvent(EngineEvent):
    def __init__(self, payload=None):
        super().__init__('VoteEvent',  payload)
        self._user_login = None
        self._pull_request_id = None
        self._role = None
        self._agreement = None
        self._rationale = None

    @classmethod
    def from_github_event(cls, event: GitHubEvent):
        the_event = cls(payload=event.payload)
        the_event._user_login = event.payload["review"]["user"]["login"]
        the_event._pull_request_id = event.payload["pull_request"]["id"]
        the_event._role = event.payload["review"]["author_association"]
        the_event._agreement = event.payload["review"]["state"] == "APPROVED"
        the_event._rationale = event.payload["review"]["body"]
        return the_event

    @classmethod
    def from_gitlab_event(cls, event: GitLabEvent):
        the_event = cls(payload=event.payload)
        the_event._user_login = event.payload["review"]["user"]["login"]
        the_event._pull_request_id = event.payload["pull_request"]["id"]
        the_event._role = event.payload["review"]["author_association"]
        the_event._agreement = event.payload["review"]["state"] == "APPROVED"
        the_event._rationale = event.payload["review"]["body"]
        return the_event

    @property
    def user_login(self):
        return self._user_login

    @property
    def pull_request_id(self):
        return self._pull_request_id

    @property
    def role(self):
        # Is one of the following : COLLABORATOR, CONTRIBUTOR, FIRST_TIMER, FIRST_TIME_CONTRIBUTOR, MANNEQUIN, MEMBER, NONE, OWNER
        return self._role

    @property
    def agreement(self):
        return self._agreement

    @property
    def rationale(self):
        return self._rationale
