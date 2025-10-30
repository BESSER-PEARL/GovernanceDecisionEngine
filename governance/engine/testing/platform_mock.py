from besser.agent.platforms.github.github_objects import Issue
from besser.agent.platforms.github.github_platform import GitHubPlatform


class PlatformMock(GitHubPlatform):
    def __init__(self, agent: 'Agent', payload={}):
        super().__init__(agent)
        self._payload = payload

    def getitem(self,url):
        return self._payload[url]

    def put(self,url, data):
        pass

    @property
    def payload(self):
        return self._payload

    @payload.setter
    def payload(self, payload):
        self._payload = payload

    def get_issue(self, user: str, repository: str, issue_number: int) -> Issue:
        return Issue(self._payload["#"+str(issue_number)])

    def set_label(self, issue: Issue, label: str):
        pr = self._payload["#"+str(issue.number)]
        pr['labels'].append({'name': label})