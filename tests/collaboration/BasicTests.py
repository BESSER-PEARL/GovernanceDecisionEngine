import pytest

from governance.engine.collaboration_metamodel import Interaction, User, Collaboration
from governance.language.governance_metamodel import Role, CollabType


def utils_create_dev(interaction) -> User:
    roles = set()
    role = Role("Dev")
    roles.add(role)
    return interaction.new_user("test", roles)

def utils_create_collab(interaction) -> Collaboration:
    user = utils_create_dev(interaction)
    return interaction.propose(user, "Collab_Test", CollabType.TASK, "Just a simple test", None)

def test_user_creation():
    interaction = Interaction()
    roles = set()
    role = Role("Dev")
    roles.add(role)
    user = interaction.new_user("test", roles)
    assert user._id == "test"
    assert role in user._roles
    assert user in interaction.users
    assert user._interaction == interaction

def test_collaboration_creation():
    interaction = Interaction()
    user = utils_create_dev(interaction)
    collab = interaction.propose(user, "Collab_Test", CollabType.TASK, "Just a simple test", None)
    assert collab._id == "Collab_Test"
    assert collab._rationale == "Just a simple test"
    assert collab._type == CollabType.TASK
    assert collab._proposed_by == user
    assert collab._leader == user
    assert collab in user.leads
    assert collab._id.lower() in interaction.collaborations.keys()
    assert collab in interaction.collaborations.values()
    assert collab == interaction.collaborations[collab._id.lower()]
    assert collab._interaction == interaction

def test_collaboration_leader_change():
    interaction = Interaction()
    user = interaction.new_user('user2', set())
    collab = utils_create_collab(interaction)
    old_leader = collab.leader

    collab.leader = user
    assert collab in user.leads
    assert collab.leader == user
    assert collab not in old_leader.leads

def test_vote_creation():
    interaction = Interaction()
    collab = utils_create_collab(interaction)
    user = collab.leader

    collab.vote(user, True, "Fair enough")
    assert len(collab.votes) == 1
    vote = None
    for voted in collab.votes:
        vote = voted
    assert vote is not None
    assert vote._voted_by == user
    assert vote._agreement
    assert vote in user.votes