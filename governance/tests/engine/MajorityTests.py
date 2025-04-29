from governance.tests.framework.engine_testing import EngineTesting


def test_majority_rule_accept():
    engine = EngineTesting(8901, "secret_test_webhook", '../policies/majority_policy.txt')
    (engine.register_user("gwendal")
     .register_user("Mike")
     .register_user("adem")
     .propose_collaboration("gwendal")
     .vote("gwendal", True)
     .vote("Mike", True)
     .vote("adem", True))