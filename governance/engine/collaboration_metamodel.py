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

from metamodel import Role, LeaderDrivenRule, Rule, MajorityRule, Scope, Individual


class Interaction:
    def __init__(self):
        self._individuals: set[Individual] = set()
        self._collaborations: dict[str,Collaboration] = dict()
        self._decisions: set[Decision] = set()

    @property
    def individuals(self):
        return self._individuals

    @property
    def collaborations(self):
        return self._collaborations

    @property
    def decisions(self):
        return self._decisions

    def new_individual(self, id: str, roles: set[Role]) -> 'Individual':
        #TODO : update
        u = Individual(self, id, roles)
        self._individuals.add(u)
        return u

    def propose(self, individual: 'Individual', id: str, scope: Scope, rationale: str, metadata: 'Metadata')-> 'Collaboration':
        collab = Collaboration(self, id, scope, rationale, individual, metadata)
        self._collaborations[id.lower()] = collab
        return collab

    def make_decision(self, collab: 'Collaboration', rule: Rule) -> 'Decision':
        # TODO : Update with new conditions
        if isinstance(rule, MajorityRule):
            maj: MajorityRule = rule
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

        elif isinstance(rule, LeaderDrivenRule):
            pass


# Modification for the Individual class
Individual._interaction: Interaction = None
Individual._proposes: set['Collaboration'] = set()
Individual._leads: set['Collaboration'] = set()
Individual._votes: set['Vote'] = set()
def votes(self):
    return self._votes
def proposes(self):
    return self._proposes
def leads(self):
    return self._leads
Individual.proposes = proposes
Individual.leads = leads
Individual.votes = votes

class Collaboration:
    def __init__(self, interaction: Interaction, id: str, scope: Scope, rationale: str, creator: Individual, metadata: 'Metadata'):
        self._interaction: Interaction = interaction
        self._id: str = id
        self._scope: Scope = scope
        self._rationale: str = rationale
        self._proposed_by: Individual = creator
        self._leader: Individual = creator
        self._votes: set[Vote] = set()
        self._metadata: Metadata = metadata
        self._is_decided: set[Decision] = set()
        creator.proposes.add(self)
        creator.leads.add(self)

    def vote(self, individual: Individual, agreement: bool, rationale: str):
        vote = Vote(agreement, time.time(), rationale, individual)
        self._votes.add(vote)
        individual.votes.add(vote)

    @property
    def leader(self):
        return self._leader

    @leader.setter
    def leader(self, individual: Individual):
        self._leader.leads.remove(self)
        self._leader = individual
        individual.leads.add(self)

    @property
    def scope(self):
        return self._scope

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
    def __init__(self, agreement: bool, timestamp: float, rationale: str, voted_by: Individual):
        self._agreement: bool = agreement
        self._timestamp: float = timestamp
        self._rationale: str = rationale
        self._voted_by: Individual = voted_by
        self._part_of: Decision = None

class Decision:
    def __init__(self, interaction: Interaction, accepted: bool, timestamp: float, collab: Collaboration, votes: set[Vote], rule: Rule):
        self._interaction: Interaction = interaction
        self._accepted: bool = accepted
        self._timestamp: float = timestamp
        self._decides: Collaboration = collab
        self._votes: set[Vote] = votes
        self._rule: Rule = rule


