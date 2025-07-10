from governance.engine.testing.framework.engine_testing import EngineTesting

def test_task_not_matching_task():
    engine = EngineTesting(8901, "secret_test_webhook", '../policy_examples/engine_testing/scope_task.txt')
    (engine
     .propose_collaboration("Alice", repo="other/repo")
     .vote("Alice", True)
     .vote("Bob", True)
     .vote("Zoe", True)
     .wait_decision(5)
     .assert_acceptance()
     .equals(None)
     .for_policy("ScopePolicy"))

def test_task_matching_task():
    engine = EngineTesting(8901, "secret_test_webhook", '../policy_examples/engine_testing/scope_task.txt')
    (engine
     .propose_collaboration("Alice")
     .vote("Alice", True)
     .vote("Bob", True)
     .vote("Zoe", True)
     .wait_decision(5)
     .assert_acceptance()
     .equals(True)
     .for_policy("ScopePolicy"))

def test_task_matching_activity():
    engine = EngineTesting(8901, "secret_test_webhook", '../policy_examples/engine_testing/scope_activity.txt')
    (engine
     .propose_collaboration("Alice")
     .vote("Alice", True)
     .vote("Bob", True)
     .vote("Zoe", True)
     .wait_decision(5)
     .assert_acceptance()
     .equals(True)
     .for_policy("ScopePolicy"))

def test_task_matching_project():
    engine = EngineTesting(8901, "secret_test_webhook", '../policy_examples/engine_testing/scope_project.txt')
    (engine
     .propose_collaboration("Alice")
     .vote("Alice", True)
     .vote("Bob", True)
     .vote("Zoe", True)
     .wait_decision(5)
     .assert_acceptance()
     .equals(True)
     .for_policy("ScopePolicy"))

def test_task_not_matching_project():
    engine = EngineTesting(8901, "secret_test_webhook", '../policy_examples/engine_testing/scope_project.txt')
    (engine
     .propose_collaboration("Alice",repo="other/repo")
     .vote("Alice", True)
     .vote("Bob", True)
     .vote("Zoe", True)
     .wait_decision(5)
     .assert_acceptance()
     .equals(None)
     .for_policy("ScopePolicy"))
