from governance.engine.testing.framework.engine_testing import EngineTesting

def test_majority_rule_accept():
    engine = EngineTesting(8901, "secret_test_webhook", '../policy_examples/majority_policy.txt')
    (engine
     .propose_collaboration("gwendal")
     .vote("gwendal", True)
     .vote("Mike", True)
     .vote("adem", True)
     .wait_decision(5)
     .assert_acceptance()
     .equals(True)
     .for_policy("TestPolicy"))