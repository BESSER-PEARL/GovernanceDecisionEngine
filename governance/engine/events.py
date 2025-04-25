from datetime import datetime

from besser.agent.core.transition.event import Event
from besser.agent.library.transition.events.github_webhooks_events import PullRequestOpened, GitHubEvent, \
    PullRequestAssigned

from metamodel import SinglePolicy, Scope, Task, StatusEnum
from utils.gh_extension import Patch, PullRequest, ActionEnum


class DeadlineEvent(Event):
    def __init__(self, deadline_collab = None, deadline_policy: SinglePolicy = None,
                 deadline_timestamp: float = None, session_id: str = None):
        if deadline_collab is None:
            super().__init__("deadline")
        else:
            super().__init__(str(deadline_collab._id)+"_deadline")
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

class UserRegistrationEvent(PullRequestAssigned):

    @classmethod
    def from_github_event(cls, event: GitHubEvent):
        return cls(payload=event.payload)

    @property
    def login(self):
        return self.payload["assignee"]["login"]

    @property
    def roles(self):
        return ["REVIEWER"]

class CollaborationProposalEvent(PullRequestOpened):

    @classmethod
    def from_github_event(cls, event: GitHubEvent):
        return cls(payload=event.payload)

    @property
    def id(self):
        return self.payload["pull_request"]["id"]

    @property
    def title(self):
        return self.payload["pull_request"]["title"]

    @property
    def reviewers(self):
        requested_reviewers = self.payload["pull_request"]["requested_reviewers"]
        reviewers = []
        for reviewer in requested_reviewers:
            reviewers.append(reviewer["login"])
        return reviewers

    @property
    def creator(self):
        return self.payload["pull_request"]["user"]["login"]

    @property
    def rationale(self):
        return self.payload["pull_request"]["body"]

    @property
    def scope(self):
        labels_payload = self.payload["pull_request"]["labels"]
        labels = set()
        for label in labels_payload:
            labels.add(label["name"])
        pr = PullRequest(self.title, labels)
        pr.payload = self.payload["pull_request"]
        return Patch(self.title,StatusEnum.ACCEPTED, ActionEnum.MERGE, pr)

class VoteEvent(GitHubEvent):
    def __init__(self, payload=None):
        super().__init__('pull_request_review', 'submitted', payload)

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
