import time

from besser.agent.core.agent import Agent
from nltk.sem.relextract import roles_demo

import metamodel
from governance.engine.semantics.policy_visitor import visitPolicy, visitComposedPolicy, visitCondition, \
    check_conditions, isDecidablePolicy
from metamodel import Role, Policy, Scope, Individual, StatusEnum, ComposedPolicy, hasRole, SinglePolicy, EvaluationMode


# Modification for the Individual class
class DynamicIndividual(Individual):
    def __init__(self, individual: Individual, interaction):
        super().__init__(individual.name, individual.vote_value)
        self._interaction: Interaction = interaction
        self._proposes: set['Collaboration'] = set()
        self._leads: set['Collaboration'] = set()
        self._votes: set['Vote'] = set()
        self._enacted_roles: set[hasRole] = set()
        self._base_individual = individual

    def __eq__(self, other):
        if not isinstance(other, Individual):
            return False
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    @property
    def votes(self):
        return self._votes

    @property
    def proposes(self):
        return self._proposes

    @property
    def leads(self):
        return self._leads

    @property
    def enacted_roles(self):
        return self._enacted_roles

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

    def register_individuals(self, individuals: set[Individual]):
        for individual in individuals:
            self._individuals[individual.name] = DynamicIndividual(individual, self)

    def get_or_create_dynamic_individual(self, id: str) -> DynamicIndividual:
        if id not in self._individuals:
            u = Individual(id)
            self._individuals[id] = DynamicIndividual(u, self)
        return self._individuals[id]

    def propose(self, individual: DynamicIndividual, id: int, scope: Scope, rationale: str, platform)-> 'Collaboration':
        collab = Collaboration(self, id, scope, rationale, individual, platform)
        self._collaborations[id] = collab
        return collab

    def make_decision(self, collab: 'Collaboration', rule: SinglePolicy, agent: Agent) -> 'Decision':
        result = visitPolicy(collab, rule, agent)
        decision = Decision(self, result, time.time(), collab, collab.ballot_boxes[rule], rule)

        if result is not None:
            for cond in rule.conditions:
                if cond.evaluation_mode == EvaluationMode.POST:
                    visitCondition(collab, rule, cond)

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
        if known_result is not None:
            result = known_result
        else:
            result = visitComposedPolicy(collab, rule)

        if result is not None:
            for phase in rule.phases:
                if phase in collab.ballot_boxes:
                    collab.ballot_boxes[rule] = collab.ballot_boxes[rule].union(collab.ballot_boxes[phase])
            decision = Decision(self, result, time.time(), collab, collab.ballot_boxes[rule], rule)
        else:
            return None

        if decision._accepted:
            collab.scope.status = StatusEnum.PARTIAL

        for vote in collab.ballot_boxes[rule]:
            vote._part_of = decision
        self._decisions.add(decision)
        if rule.parent is None:
            collab._is_decided = decision
            collab.scope.status = StatusEnum.COMPLETED
        return decision


class Collaboration:
    def __init__(self, interaction: Interaction, id: int, scope: Scope, rationale: str, creator: DynamicIndividual, platform):
        self._interaction: Interaction = interaction
        self._id: int = id
        self._scope: Scope = scope
        self._rationale: str = rationale
        self._proposed_by: DynamicIndividual = creator
        self._leader: DynamicIndividual = creator
        self._is_decided: Decision = None
        self._ballot_boxes: dict[Policy, set[Vote]] = dict()
        self._platform = platform
        creator.proposes.add(self)
        creator.leads.add(self)

    def vote(self, individual: DynamicIndividual, agreement: bool, rationale: str):
        vote = Vote(agreement, time.time(), rationale, individual)
        decidable: set[Policy] = set()
        for policy in self._ballot_boxes:
            if isinstance(policy, SinglePolicy):
                valid_vote = False
                roles = {part for part in policy.participants if isinstance(part, Role)}
                individuals = {part for part in policy.participants if not isinstance(part, Role)}
                for role in roles:
                    for registered in role.individuals:
                        if individual.name == registered.name:
                            valid_vote = True
                            if role.vote_value > vote._vote_value:
                                vote._vote_value = role.vote_value
                            individual.enacted_roles.add(hasRole(individual.name, role, individual, self.scope))
                for part_indiv in individuals:
                    if individual.name == part_indiv.name:
                        valid_vote = True
                        if part_indiv.vote_value > vote._vote_value:
                            vote._vote_value = part_indiv.vote_value
                        role_assignement = part_indiv.role_assignement
                        if role_assignement is not None:
                            individual.enacted_roles.add(hasRole(individual.name, role_assignement.role, individual, self.scope))
                if isinstance(individual._base_individual, metamodel.Agent):
                    vote._vote_value = vote._vote_value * individual._base_individual.confidence

                if valid_vote:
                    box: set[Vote] = self._ballot_boxes[policy]
                    add_vote = False
                    if len(box) > 0:
                        prev_vote = next(iter(box))
                        add_vote = prev_vote._part_of is None
                    else:
                        add_vote = True

                    if add_vote:
                        has_voted = False
                        for existing_vote in box:
                            if existing_vote.voted_by is individual:
                                has_voted = True
                                existing_vote._vote_value = vote._vote_value
                                existing_vote._agreement = vote._agreement
                                existing_vote._rationale = vote._rationale
                                existing_vote._timestamp = vote._timestamp
                        if not has_voted:
                            box.add(vote)
                            individual.votes.add(vote)

                        # Can we decide
                        isDecidable = isDecidablePolicy(self, policy)
                        if isDecidable:
                            decidable.add(policy)
        return decidable


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
        self._vote_value: float = 0.0

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


