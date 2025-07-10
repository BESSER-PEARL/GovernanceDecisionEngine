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


def test_majority_rule_reject():
 engine = EngineTesting(8901, "secret_test_webhook", '../policy_examples/majority_policy.txt')
 (engine
  .propose_collaboration("gwendal")
  .vote("gwendal", True)
  .vote("Mike", True)
  .vote("adem", False)
  .wait_decision(5)
  .assert_acceptance()
  .equals(False)
  .for_policy("TestPolicy"))


def test_veto_rule_accept():
 engine = EngineTesting(8901, "secret_test_webhook", '../policy_examples/maj_with_veto_right.txt')
 (engine
  .propose_collaboration("adem")
  .vote("gwendal", True)
  .vote("Mike", True)
  .vote("adem", True)
  .wait_decision(5)
  .assert_acceptance()
  .equals(True)
  .for_policy("TestPolicy"))

# Fails due to vetoers only parsed as Role and not as Individual
def test_veto_rule_reject():
 engine = EngineTesting(8901, "secret_test_webhook", '../policy_examples/maj_with_veto_right.txt')
 (engine
  .propose_collaboration("adem")
  .vote("gwendal", True)
  .vote("Mike", True)
  .vote("adem", False)
  .wait_decision(5)
  .assert_acceptance()
  .equals(False)
  .for_policy("TestPolicy"))