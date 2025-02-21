"""
Dynamic info weaving :
Decisions have Rules
Decisions result from Collaborations and are created at the Deadline
at Collaboration creation, pull applicable rules and launch DeadlineEvents
Collaborations have one Decision except for Phased
Collaboration has Metadata
Collaboration has Votes created by Users
Users have Roles

"""
import time

from besser.governance.language.governance_metamodel import Role, Rule, CollabType


class Metadata:
    pass

class Priority(Metadata):
    def __init__(self, value: str):
        self._value: str = value

class TagBased(Metadata):
    def __init__(self, tags:set[str]):
        def toTag(t:str):
            return Tag(t)
        self._tags = set(map(toTag, tags))

class Tag:
    def __init__(self, value: str):
        self._value: str = value


class User:
    def __init__(self, id: str, roles: set[Role]):
        self._id: str = id
        self._roles: set[Role] = roles
        self._proposes: set[Collaboration] = set()
        self._leads: set[Collaboration] = set()
        self._votes: set[Vote] = set()

    @property
    def votes(self):
        return self._votes

    @property
    def proposes(self):
        return self._proposes

    @property
    def leads(self):
        return self._leads


class Collaboration:
    def __init__(self, id: str, collab_type: CollabType, rationale: str, creator: User, metadata: Metadata):
        self._id: str = id
        self._type: CollabType = collab_type
        self._rationale: str = rationale
        self._proposed_by: User = creator
        self._leader: User = creator
        self._votes: set[Vote] = set()
        self._metadata: Metadata = metadata
        self._is_decided: set[Decision] = set()
        creator.proposes.add(self)
        creator.leads.add(self)

    def vote(self, user: User, agreement: bool, rationale: str):
        vote = Vote(agreement, time.time(), rationale, user)
        self._votes.add(vote)
        user.votes.add(vote)

    def make_decision(self):
        pass

    @property
    def leader(self):
        return self._leader

    @leader.setter
    def leader(self, user: User):
        self._leader.leads.remove(self)
        self._leader = user
        user.leads.add(self)

    @property
    def type(self):
        return self._type


class Decision:
    def __init__(self):
        self._accepted: bool = None
        self._timestamp: float = None
        self._decides: Collaboration = None
        self._votes: set[Vote] = set()
        self._rule: Rule = None

class Vote:
    def __init__(self, agreement: bool, timestamp: float, rationale: str, voted_by: User):
        self._agreement: bool = agreement
        self._timestamp: float = timestamp
        self._rationale: str = rationale
        self._voted_by: User = voted_by
        self._part_of: Decision = None


class Interaction:
    def __init__(self):
        self._users: set[User] = set()
        self._collaborations: dict[str,Collaboration] = dict()
        self._decisions: set[Decision] = set()

    def propose(self, user: User, id: str, collab_type: CollabType, rationale: str, metadata: Metadata)-> Collaboration:
        collab = Collaboration(id, collab_type, rationale, user, metadata)
        self._collaborations[id.lower()] = collab
        return collab

    @property
    def users(self):
        return self._users

    @property
    def collaborations(self):
        return self._collaborations
