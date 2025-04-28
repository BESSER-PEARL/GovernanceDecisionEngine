import unittest
import os

from governance.engine.collaboration_metamodel import Interaction
from governance.engine.helpers import parse
from governance.language.governance_metamodel import Role, CollabType, governance_classes

from metamodel.governance import Individual, Policy


# Verify the import worked
print(f"Successfully imported Individual: {Individual}")
print(f"Individual module path: {Individual.__module__}")

# Try creating a test instance
test_individual = Individual("TestName")
print(f"Created individual with name: {test_individual.name}")

class TestPolicyEngineCreation(unittest.TestCase):
    def parse_policy(self) -> Policy:
        policy_file_path = os.path.join(os.path.dirname(__file__), '../majority_policy.txt')
        policy = parse(policy_file_path)
        return policy
     
    def create_individual(self, interaction, name, roles) -> Individual:
        affected_roles = set()
        for role in roles:
            role_obj = Role(role)
            affected_roles.add(role_obj)
        return interaction.add_individual(name, roles)

    def test_majority_rule_accept(self):
        policy = self.parse_policy()
        interaction = Interaction()
        u1 = self.create_individual(interaction, "Individual 1", ["Developer"])
        u2 = self.create_individual(interaction, "Individual 2", ["Developer"])
        #TODO : change for a scope
        collab = interaction.propose(u1,"task", CollabType.TASK, "rationale", None)
        collab.vote(u1, True, "rationale")
        collab.vote(u2, True, "rationale")
        decision = interaction.make_decision(collab, policy.rules.pop())
        assert decision._accepted

    def test_majority_rule_reject(self):
        policy = parse_policy()
        interaction = Interaction()
        u1 = create_individual(interaction, "Individual 1", ["Developer"])
        u2 = create_individual(interaction, "Individual 2", ["Developer"])
        # TODO : change for a scope
        collab = interaction.propose(u1, "task", CollabType.TASK, "rationale", None)
        collab.vote(u1, False, "rationale")
        collab.vote(u2, False, "rationale")
        decision = interaction.make_decision(collab, policy.rules.pop())
        assert not decision._accepted

    def test_majority_rule_half(self):
        policy = parse_policy()
        interaction = Interaction()
        u1 = create_individual(interaction, "Individual 1", ["Developer"])
        u2 = create_individual(interaction, "Individual 2", ["Developer"])
        # TODO : change for a scope
        collab = interaction.propose(u1, "task", CollabType.TASK, "rationale", None)
        collab.vote(u1, True, "rationale")
        collab.vote(u2, False, "rationale")
        decision = interaction.make_decision(collab, policy.rules.pop())
        assert not decision._accepted