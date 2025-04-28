import json
import time

import requests
import hmac

class EngineTesting(object):
    def __init__(self, port, secret):
        self._port = port
        self._secret = secret

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

    def register_user(self, username):
        self._send('pull_request',
                   'assigned',
                   {"assignee":{
                       "login":username
                   }})
        return self

    def propose_collaboration(self,creator, id = 1, title = "Collaboration", description = "Collaboration", labels = []):
        full_title = title+' '+str(id)
        full_description = description+' '+str(id)
        self._send('pull_request',
                   'opened',
                   {"pull_request": {
                       "id": id,
                       "title": full_title,
                       "requested_reviewers": [],
                       "user": {'login': creator},
                       "body": full_description ,
                       "labels": labels
                   }})
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