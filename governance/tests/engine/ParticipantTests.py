from governance.engine.testing.framework.engine_testing import EngineTesting

def test_participant_with_role():
    engine = EngineTesting(8901, "secret_test_webhook", '../policy_examples/engine_testing/participants.txt')
    (engine
     .propose_collaboration("Alice")
     .vote("Alice", True)
     .vote("Bob", True)
     .wait_decision(5)
     .assert_voters()
     .equals(["Alice", "Bob"])
     .for_policy("ParticipantPolicy"))

def test_participant_as_individual():
    engine = EngineTesting(8901, "secret_test_webhook", '../policy_examples/engine_testing/participants.txt')
    (engine
     .propose_collaboration("Zoe")
     .vote("Zoe", True)
     .wait_decision(5)
     .assert_voters()
     .equals(["Zoe"])
     .for_policy("ParticipantPolicy"))


def test_non_participant_with_role():
    engine = EngineTesting(8901, "secret_test_webhook", '../policy_examples/engine_testing/participants.txt')
    (engine
     .propose_collaboration("Charlie")
     .vote("Charlie", True)
     .vote("Daniel", True)
     .wait_decision(5)
     .assert_voters()
     .equals([])
     .for_policy("ParticipantPolicy"))


def test_non_participant_as_individual():
    engine = EngineTesting(8901, "secret_test_webhook", '../policy_examples/engine_testing/participants.txt')
    (engine
     .propose_collaboration("Agent")
     .vote("Agent", True)
     .wait_decision(5)
     .assert_voters()
     .equals([])
     .for_policy("ParticipantPolicy"))