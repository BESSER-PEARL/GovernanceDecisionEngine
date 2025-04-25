import time

from besser.agent.core.agent import Agent

from governance.engine.policy_visitor import visitPolicy, visitComposedPolicy
from metamodel import Role, Policy, Scope, Individual, StatusEnum, ComposedPolicy

# Modification for the Individual class
class DynamicIndividual(Individual):
    def __init__(self, individual: Individual):
        super().__init__(individual.name, individual.confidence)
        self._interaction: Interaction = None
        self._proposes: set['Collaboration'] = set()
        self._leads: set['Collaboration'] = set()
        self._votes: set['Vote'] = set()

    @property
    def votes(self):
        return self._votes

    @property
    def proposes(self):
        return self._proposes

    @property
    def leads(self):
        return self._leads

class Interaction:
    def __init__(self):
        self._individuals: dict[str, DynamicIndividual] = dict()
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

    def add_individual(self, id: str, roles: set[Role]) -> DynamicIndividual:
        if id not in self._individuals:
            u = Individual(id)
            self._individuals[id] = DynamicIndividual(u)
            return u
        return self._individuals[id]

    def propose(self, individual: DynamicIndividual, id: int, scope: Scope, rationale: str)-> 'Collaboration':
        collab = Collaboration(self, id, scope, rationale, individual)
        self._collaborations[id] = collab
        return collab

    def make_decision(self, collab: 'Collaboration', rule: Policy, agent: Agent) -> 'Decision':
        result = visitPolicy(collab, rule, agent)
        decision = Decision(self, result, time.time(), collab, collab.ballot_boxes[rule], rule)

        if result is not None:
            if collab.scope.status == StatusEnum.ACCEPTED:
                collab.scope.status = StatusEnum.PARTIAL

            for vote in collab.ballot_boxes[rule]:
                vote._part_of = decision
            self._decisions.add(decision)
            if rule.parent is None:
                collab._is_decided = decision
                collab.scope.status = StatusEnum.COMPLETED
            return decision
        return None

    def compose_decision(self, collab: 'Collaboration', rule: ComposedPolicy, known_result: bool | None = None) -> 'Decision':
        decision = None
        if known_result is not None:
            decision = Decision(self, known_result, time.time(), collab, collab.ballot_boxes[rule], rule)
        else:
            result = visitComposedPolicy(collab, rule)
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


class Collaboration:
    def __init__(self, interaction: Interaction, id: int, scope: Scope, rationale: str, creator: DynamicIndividual):
        self._interaction: Interaction = interaction
        self._id: int = id
        self._scope: Scope = scope
        self._rationale: str = rationale
        self._proposed_by: DynamicIndividual = creator
        self._leader: DynamicIndividual = creator
        # self._votes: set[Vote] = set()
        self._is_decided: Decision = None
        self._ballot_boxes: dict[Policy, set[Vote]] = dict()
        creator.proposes.add(self)
        creator.leads.add(self)

    def vote(self, individual: DynamicIndividual, agreement: bool, rationale: str):
        vote = Vote(agreement, time.time(), rationale, individual)
        for policy in self._ballot_boxes:
            box: set[Vote] = self._ballot_boxes[policy]
            box.add(vote)
        individual.votes.add(vote)

    @property
    def leader(self):
        return self._leader

    @leader.setter
    def leader(self, individual: DynamicIndividual):
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
    def __init__(self, agreement: bool, timestamp: float, rationale: str, voted_by: DynamicIndividual):
        self._agreement: bool = agreement
        self._timestamp: float = timestamp
        self._rationale: str = rationale
        self._voted_by: DynamicIndividual = voted_by
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


