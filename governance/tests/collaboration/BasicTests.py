import pytest

from governance.engine.collaboration_metamodel import Interaction, Collaboration
from governance.language.governance_metamodel import Role, CollabType
from metamodel import Individual


def utils_create_dev(interaction) -> Individual:
    roles = set()
    role = Role("Dev")
    roles.add(role)
    return interaction.add_individual("test", roles)

def utils_create_collab(interaction) -> Collaboration:
    individual = utils_create_dev(interaction)
    return interaction.propose(individual, "Collab_Test", CollabType.TASK, "Just a simple test", None)

def test_individual_creation():
    interaction = Interaction()
    roles = set()
    role = Role("Dev")
    roles.add(role)
    individual = interaction.add_individual("test", roles)
    assert individual._id == "test"
    assert role in individual._roles
    assert individual in interaction.individuals
    assert individual._interaction == interaction

def test_collaboration_creation():
    interaction = Interaction()
    individual = utils_create_dev(interaction)
    collab = interaction.propose(individual, "Collab_Test", CollabType.TASK, "Just a simple test", None)
    assert collab._id == "Collab_Test"
    assert collab._rationale == "Just a simple test"
    assert collab._type == CollabType.TASK
    assert collab._proposed_by == individual
    assert collab._leader == individual
    assert collab in individual.leads
    assert collab._id.lower() in interaction.collaborations.keys()
    assert collab in interaction.collaborations.values()
    assert collab == interaction.collaborations[collab._id.lower()]
    assert collab._interaction == interaction

def test_collaboration_leader_change():
    interaction = Interaction()
    individual = interaction.add_individual('individual2', set())
    collab = utils_create_collab(interaction)
    old_leader = collab.leader

    collab.leader = individual
    assert collab in individual.leads
    assert collab.leader == individual
    assert collab not in old_leader.leads

def test_vote_creation():
    interaction = Interaction()
    collab = utils_create_collab(interaction)
    individual = collab.leader

    collab.vote(individual, True, "Fair enough")
    assert len(collab.votes) == 1
    vote = None
    for voted in collab.votes:
        vote = voted
    assert vote is not None
    assert vote._voted_by == individual
    assert vote._agreement
    assert vote in individual.votes