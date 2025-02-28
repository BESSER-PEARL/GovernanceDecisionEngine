from textx import metamodel_from_file

from governance.engine.collaboration_metamodel import User, Collaboration, Interaction
from governance.language.governance_metamodel import Role, CollabType, Project, governance_classes

def parse_rules() -> Project:
    metamodel = metamodel_from_file('../../governance/language/governance_language.tx', classes=governance_classes)
    gov_rules = metamodel.model_from_file('../test.gov')
    return gov_rules

def create_user(interaction, name, roles) -> User:
    affected_roles = set()
    for role in roles:
        role_obj = Role(role)
        affected_roles.add(role_obj)
    return interaction.new_user(name, roles)

def test_majority_rule_accept():
    policy = parse_rules()
    interaction = Interaction()
    u1 = create_user(interaction, "User 1", ["Developer"])
    u2 = create_user(interaction, "User 2", ["Developer"])
    collab = interaction.propose(u1,"task", CollabType.TASK, "rationale", None)
    collab.vote(u1, True, "rationale")
    collab.vote(u2, True, "rationale")
    decision = interaction.make_decision(collab, policy.rules.pop())
    assert decision._accepted

def test_majority_rule_reject():
    policy = parse_rules()
    interaction = Interaction()
    u1 = create_user(interaction, "User 1", ["Developer"])
    u2 = create_user(interaction, "User 2", ["Developer"])
    collab = interaction.propose(u1, "task", CollabType.TASK, "rationale", None)
    collab.vote(u1, False, "rationale")
    collab.vote(u2, False, "rationale")
    decision = interaction.make_decision(collab, policy.rules.pop())
    assert not decision._accepted

def test_majority_rule_half():
    policy = parse_rules()
    interaction = Interaction()
    u1 = create_user(interaction, "User 1", ["Developer"])
    u2 = create_user(interaction, "User 2", ["Developer"])
    collab = interaction.propose(u1, "task", CollabType.TASK, "rationale", None)
    collab.vote(u1, True, "rationale")
    collab.vote(u2, False, "rationale")
    decision = interaction.make_decision(collab, policy.rules.pop())
    assert not decision._accepted