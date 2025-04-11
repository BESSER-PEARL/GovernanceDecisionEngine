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

from governance.engine.policy_visitor import visitPolicy
from metamodel import Role, LeaderDrivenPolicy, Policy, MajorityPolicy, Scope, Individual, StatusEnum, ComposedPolicy


class Interaction:
    def __init__(self):
        self._individuals: dict[str, Individual] = dict()
        self._collaborations: dict[int,Collaboration] = dict()
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

    def add_individual(self, id: str, roles: set[Role]) -> 'Individual':
        if id not in self._individuals:
            u = Individual(id)
            self._individuals[id] = u
            return u
        return self._individuals[id]

    def propose(self, individual: 'Individual', id: int, scope: Scope, rationale: str)-> 'Collaboration':
        collab = Collaboration(self, id, scope, rationale, individual)
        self._collaborations[id] = collab
        return collab

    def make_decision(self, collab: 'Collaboration', rule: Policy) -> 'Decision':
        result = visitPolicy(collab, rule)
        decision = Decision(self, result, time.time(), collab, collab.ballot_boxes[rule], rule)

        if result:
            collab.scope.status = StatusEnum.PARTIAL

        for vote in collab.ballot_boxes[rule]:
            vote._part_of = decision
        self._decisions.add(decision)
        if rule.parent is None:
            collab._is_decided.add(decision)
            collab.scope.status = StatusEnum.COMPLETED
        return decision

    def compose_decision(self, collab: 'Collaboration', rule: ComposedPolicy, known_result: bool | None = None) -> 'Decision':
        decision = None
        if known_result is not None:
            decision = Decision(self, known_result, time.time(), collab, collab.ballot_boxes[rule], rule)
        else:
            result = visitPolicy(collab, rule)
            decision = Decision(self, result, time.time(), collab, collab.ballot_boxes[rule], rule)

        if decision._accepted:
            collab.scope.status = StatusEnum.PARTIAL

        for vote in collab.ballot_boxes[rule]:
            vote._part_of = decision
        self._decisions.add(decision)
        if rule.parent is None:
            collab._is_decided.add(decision)
            collab.scope.status = StatusEnum.COMPLETED
        return decision


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
    def __init__(self, interaction: Interaction, id: int, scope: Scope, rationale: str, creator: Individual):
        self._interaction: Interaction = interaction
        self._id: int = id
        self._scope: Scope = scope
        self._rationale: str = rationale
        self._proposed_by: Individual = creator
        self._leader: Individual = creator
        # self._votes: set[Vote] = set()
        self._is_decided: Decision = None
        self._ballot_boxes: dict[Policy, set[Vote]] = dict()
        creator.proposes.add(self)
        creator.leads.add(self)

    def vote(self, individual: Individual, agreement: bool, rationale: str):
        vote = Vote(agreement, time.time(), rationale, individual)
        box: set[Vote] = self._ballot_boxes[list(self._ballot_boxes)[0]]
        box.add(vote)
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
    def ballot_boxes(self):
        return self._ballot_boxes

class Vote:
    def __init__(self, agreement: bool, timestamp: float, rationale: str, voted_by: Individual):
        self._agreement: bool = agreement
        self._timestamp: float = timestamp
        self._rationale: str = rationale
        self._voted_by: Individual = voted_by
        self._part_of: Decision = None

    @property
    def voted_by(self):
        return self._voted_by

class Decision:
    def __init__(self, interaction: Interaction, accepted: bool, timestamp: float, collab: Collaboration, votes: set[Vote], rule: Policy):
        self._interaction: Interaction = interaction
        self._accepted: bool = accepted
        self._timestamp: float = timestamp
        self._decides: Collaboration = collab
        self._votes: set[Vote] = votes
        self._rule: Policy = rule


