from besser.agent.core.event import Event, ReceiveJSONEvent
from governance.engine.collaboration_metamodel import Collaboration
from metamodel import Rule


class DeadlineEvent(Event):
    def __init__(self, deadline_collab: Collaboration = None, deadline_rule: Rule = None,
                 deadline_timestamp: float = None, session_id: str = None):
        if deadline_collab is None:
            super().__init__("deadline")
        else:
            super().__init__(deadline_collab._id+"_deadline", session_id)
        self._collab: Collaboration = deadline_collab
        self._rule: Rule = deadline_rule
        self._timestamp: float = deadline_timestamp

    def is_matching(self, event: 'Event') -> bool:
        return isinstance(event, DeadlineEvent)

    @property
    def type(self):
        return self._type

    @property
    def collab(self):
        return self._collab

    @property
    def rule(self):
        return self._rule

    @property
    def timestamp(self):
        return self._timestamp

class UserRegistrationEvent(ReceiveJSONEvent):

    def is_matching(self, event: 'Event') -> bool:
        if isinstance(event, ReceiveJSONEvent):
            return event.payload["req_type"] == 'user'
        return False

    @property
    def name(self):
        return self.payload["name"]

    @property
    def roles(self):
        return self.payload["roles"]

class CollaborationProposalEvent(ReceiveJSONEvent):

    def is_matching(self, event: 'Event') -> bool:
        if isinstance(event, ReceiveJSONEvent):
            return event.payload["req_type"] == 'collab'
        return False

    @property
    def name(self):
        return self.payload["name"]

    @property
    def rationale(self):
        return self.payload["rationale"]

    @property
    def scope(self):
        return self.payload["scope"]

class VoteEvent(ReceiveJSONEvent):

    def is_matching(self, event: 'Event') -> bool:
        if isinstance(event, ReceiveJSONEvent):
            return event.payload["req_type"] == 'vote'
        return False

    @property
    def name(self):
        return self.payload["name"]

    @property
    def agreement(self):
        return self.payload["agreement"]

    @property
    def rationale(self):
        return self.payload["rationale"]
