import json
import os
import time

import requests
import hmac

from governance.engine.testing.framework.assert_builder import AssertType, DecisionAssertBuilder


class EngineTesting(object):
    def __init__(self, port, secret, path):
        self._port = port
        self._secret = secret

        with open(path, "r") as file:
            filename = file.name.split('/')[-1].rsplit('.', 1)[0]
            self._result_path = os.getcwd() + "/result_" + filename

            if os.path.exists(self._result_path):
                os.remove(self._result_path)

            data = file.read()
            self._send('clear',
                       'clear',
                       {})
            self._send('link',
                       'link',
                       {"path": self._result_path})
            self._send('policy',
                       'update',
                       {"file_content":data, "file_type":"txt", "file_name":file.name})




    def _send(self, event, action, data):
        url = 'http://127.0.0.1:{}'.format(self._port)
        data["action"] = action

        msg = json.dumps(data).encode(encoding="utf-8")
        hmac_sig = hmac.new(
            self._secret.encode("UTF-8"), msg=msg, digestmod="sha256"
        ).hexdigest()
        calculated_sig = "sha256=" + hmac_sig

        headers = {'X-GitHub-Event': event,
                   "X-Hub-Signature-256": calculated_sig,
                   "X-GitHub-Delivery": "",
                   "content-type": "application/json"}

        requests.post(url, headers=headers, json=data)
        # time.sleep(1)

    def state(self, passing_tests: bool = True):
        data = {
            "commits": [{"url":"commit"}],
            "commit/status" : {"state": passing_tests}
        }
        self._send('mock','mock', data)
        return self

    def register_user(self, username):
        self._send('pull_request',
                   'assigned',
                   {"assignee":{
                       "login":username
                   }})
        return self

    def propose_collaboration(self,creator,repo = "owner/repo", id = 1, title = "Collaboration", description = "Collaboration", labels = []):
        full_title = title+' '+str(id)
        full_description = description+' '+str(id)

        key = "#" + str(id)
        mock = {key: {
            'id': id,
            'number': id,
            'title': title,
            'user': {
                'id': '',
                'login': creator,
                'html_url': '',
                'organizations_url': '',
                'repos_url': ''
            },
            'labels': labels,
            'state': '',
            'locked': '',
            'assignees': '',
            'milestone': '',
            'url': '',
            'repository_url': '',
            'labels_url': '',
            'comments_url': '',
            'url': '',
            'events_url': ''
        }}
        self._send('mock', 'mock', mock)

        self._send('pull_request',
                   'opened',
                   {
                       "pull_request": {
                           "id": id,
                           "number": id,
                           "title": full_title,
                           "requested_reviewers": [],
                           "user": {'login': creator},
                           "body": full_description ,
                           "labels": labels,
                           "commits_url": "commits"
                       },
                       "repository": {
                           "full_name":repo
                       }
                   })
        return self

    def vote(self, username, agreement: bool, id = 1):
        self._send('pull_request_review',
                   'submitted',
                   {
                       "review": {
                           "user": {"login": username},
                           "body": "Rationale of {} for Collaboration {}".format(username, id),
                           "author_association": "CONTRIBUTOR",
                           "state": ("APPROVED" if agreement else "REJECTED"),
                       },
                       "pull_request": {"id": id}
                   })
        return self

    def wait_decision(self, seconds = 2):
        time.sleep(seconds)
        return self

    def assert_acceptance(self) -> DecisionAssertBuilder:
        return DecisionAssertBuilder(self, AssertType.ACCEPTANCE)

    def assert_voters(self) -> DecisionAssertBuilder:
        return DecisionAssertBuilder(self, AssertType.VOTERS)

    def assert_number_of_votes(self) -> DecisionAssertBuilder:
        return DecisionAssertBuilder(self, AssertType.VOTE_NUMBER)
