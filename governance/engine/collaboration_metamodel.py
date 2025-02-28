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

from governance.language.governance_metamodel import Role, Rule, CollabType, Majority, LeaderDriven, Phased, \
    RatioMajority

class Interaction:
    def __init__(self):
        self._users: set[User] = set()
        self._collaborations: dict[str,Collaboration] = dict()
        self._decisions: set[Decision] = set()

    @property
    def users(self):
        return self._users

    @property
    def collaborations(self):
        return self._collaborations

    @property
    def decisions(self):
        return self._decisions

    def new_user(self, id: str, roles: set[Role]) -> 'User':
        u = User(self, id, roles)
        self._users.add(u)
        return u

    def propose(self, user: 'User', id: str, collab_type: CollabType, rationale: str, metadata: 'Metadata')-> 'Collaboration':
        collab = Collaboration(self, id, collab_type, rationale, user, metadata)
        self._collaborations[id.lower()] = collab
        return collab

    def make_decision(self, collab: 'Collaboration', rule: Rule) -> 'Decision':
        if isinstance(rule, Majority):
            maj: Majority = rule
            decision = Decision(self, False, time.time(), collab, collab.votes, rule)
            if maj.min_vote <= len(collab.votes):
                vote_count: int = 0
                for vote in collab.votes:
                    vote_count += 1 if vote._agreement else 0
                    vote._part_of = decision
                #avoid float comparison
                decision._accepted = 2*vote_count > len(collab.votes)

            self._decisions.add(decision)
            collab._is_decided.add(decision)
            return decision

        elif isinstance(rule, RatioMajority):
            pass
        elif isinstance(rule, LeaderDriven):
            pass
        elif isinstance(rule, Phased):
            pass

class User:
    def __init__(self, interaction: Interaction, id: str, roles: set[Role]):
        self._interaction: Interaction = interaction
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
    def __init__(self, interaction: Interaction, id: str, collab_type: CollabType, rationale: str, creator: User, metadata: 'Metadata'):
        self._interaction: Interaction = interaction
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

    @property
    def votes(self):
        return self._votes


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

class Vote:
    def __init__(self, agreement: bool, timestamp: float, rationale: str, voted_by: User):
        self._agreement: bool = agreement
        self._timestamp: float = timestamp
        self._rationale: str = rationale
        self._voted_by: User = voted_by
        self._part_of: Decision = None

class Decision:
    def __init__(self, interaction: Interaction, accepted: bool, timestamp: float, collab: Collaboration, votes: set[Vote], rule: Rule):
        self._interaction: Interaction = interaction
        self._accepted: bool = accepted
        self._timestamp: float = timestamp
        self._decides: Collaboration = collab
        self._votes: set[Vote] = votes
        self._rule: Rule = rule


