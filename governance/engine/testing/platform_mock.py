from besser.agent.platforms.github.github_platform import GitHubPlatform


class PlatformMock(GitHubPlatform):
    def __init__(self, agent: 'Agent', payload=""):
        super().__init__(agent)
        self._payload = payload

    def getitem(self,url):
        return self._payload[url]

    @property
    def payload(self):
        return self._payload

    @payload.setter
    def payload(self, payload):
        self._payload = payload