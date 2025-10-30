from governance.engine.testing.framework.engine_testing import EngineTesting

policy_filepath = '../policy_examples/kubernetes.txt'

def test_replication_kubernetes_pr_134154():
    engine = EngineTesting(8901, "secret_test_webhook", policy_filepath)
    (engine
     .propose_collaboration("macsko", "kubernetes/kubernetes", 134154)
     .vote("itzPranshul", False, id=134154)
     .vote("dom4ha", True, id=134154)
     .wait_decision(1)
     .wait_decision(1)
     .vote("k8s-ci-robot", True, id=134154)
     .wait_decision(1)
     .assert_acceptance()
     .equals(True)
     .for_policy("pr_merge"))


def test_replication_kubernetes_pr_134140():
    engine = EngineTesting(8901, "secret_test_webhook", policy_filepath)
    (engine
     .propose_collaboration("omerap12", "kubernetes/kubernetes", 134140)
     .vote("adrianmoisey", False, id=134140)
     .vote("adrianmoisey", True, id=134140)
     .wait_decision(0.5)
     .vote("soltysh", True, id=134140)
     .wait_decision(1)
     .vote("k8s-ci-robot", True, id=134140)
     .wait_decision(1)
     .assert_acceptance()
     .equals(True)
     .for_policy("pr_merge"))


def test_replication_kubernetes_pr_134514():
 engine = EngineTesting(8901, "secret_test_webhook", policy_filepath)
 (engine
  .propose_collaboration("richabanker", "kubernetes/kubernetes", 134514)
  .vote("Jefftree", False, id=134514)
  .vote("liggitt", False, id=134514)
  .vote("liggitt", True, id=134514)
  .wait_decision(0.5)
  .wait_decision(1)
  .vote("k8s-ci-robot", True, id=134514)
  .wait_decision(1)
  .assert_acceptance()
  .equals(True)
  .for_policy("pr_merge"))

def test_replication_kubernetes_pr_134387():
 engine = EngineTesting(8901, "secret_test_webhook", policy_filepath)
 (engine
  .propose_collaboration("adrianmoisey", "kubernetes/kubernetes", 134387)
  .vote("omerap12", True, id=134387)
  .wait_decision(0.5)
  .vote("soltysh", True, id=134387)
  .wait_decision(1)
  .vote("k8s-ci-robot", True, id=134387)
  .wait_decision(1)
  .assert_acceptance()
  .equals(True)
  .for_policy("pr_merge"))

def test_replication_kubernetes_pr_134293():
  engine = EngineTesting(8901, "secret_test_webhook", policy_filepath)
  (engine
   .propose_collaboration("bart0sh", "kubernetes/kubernetes", 134293)
   .vote("ffromani", False, id=134293)
   .vote("ffromani", False, id=134293)
   .vote("ffromani", True, id=134293)
   .wait_decision(0.5)
   .wait_decision(1)
   .vote("k8s-ci-robot", True, id=134293)
   .wait_decision(1)
   .assert_acceptance()
   .equals(True)
   .for_policy("pr_merge"))

def test_replication_kubernetes_pr_134271():
 engine = EngineTesting(8901, "secret_test_webhook", policy_filepath)
 (engine
  .propose_collaboration("Jefftree", "kubernetes/kubernetes", 134271)
  .vote("jpbetz", True, id=134271)
  .wait_decision(0.5)
  .wait_decision(1)
  .vote("k8s-ci-robot", True, id=134271)
  .wait_decision(1)
  .assert_acceptance()
  .equals(True)
  .for_policy("pr_merge"))

def test_replication_kubernetes_pr_134275():
 engine = EngineTesting(8901, "secret_test_webhook", policy_filepath)
 (engine
  .propose_collaboration("humblec", "kubernetes/kubernetes", 134275)
  .vote("xing-yang", True, id=134275)
  .wait_decision(0.5)
  .wait_decision(1)
  .vote("k8s-ci-robot", True, id=134275)
  .wait_decision(1)
  .assert_acceptance()
  .equals(True)
  .for_policy("pr_merge"))

def test_replication_kubernetes_pr_134267():
 engine = EngineTesting(8901, "secret_test_webhook", policy_filepath)
 (engine
  .propose_collaboration("zk-123", "kubernetes/kubernetes", 134267)
  .vote("liggitt", False, id=134267)
  .vote("liggitt", False, id=134267)
  .vote("liggitt", False, id=134267)
  .vote("liggitt", True, id=134267)
  .wait_decision(0.5)
  .wait_decision(1)
  .vote("k8s-ci-robot", True, id=134267)
  .wait_decision(1)
  .assert_acceptance()
  .equals(True)
  .for_policy("pr_merge"))

def test_replication_kubernetes_pr_134259():
 engine = EngineTesting(8901, "secret_test_webhook", policy_filepath)
 (engine
  .propose_collaboration("mayank-agrwl", "kubernetes/kubernetes", 134259)
  .vote("sttts", True, id=134259)
  .wait_decision(0.5)
  .wait_decision(1)
  .vote("k8s-ci-robot", True, id=134259)
  .wait_decision(1)
  .assert_acceptance()
  .equals(True)
  .for_policy("pr_merge"))

def test_replication_kubernetes_pr_134229():
 engine = EngineTesting(8901, "secret_test_webhook", policy_filepath)
 (engine
  .propose_collaboration("yongruilin", "kubernetes/kubernetes", 134229)
  .vote("JoelSpeed", False, id=134229)
  .vote("JoelSpeed", False, id=134229)
  .vote("JoelSpeed", False, id=134229)
  .vote("thockin", False, id=134229)
  .vote("thockin", False, id=134229)
  .vote("thockin", True, id=134229)
  .wait_decision(0.5)
  .wait_decision(1)
  .vote("k8s-ci-robot", True, id=134229)
  .wait_decision(1)
  .assert_acceptance()
  .equals(True)
  .for_policy("pr_merge"))

def test_replication_kubernetes_pr_134176():
 engine = EngineTesting(8901, "secret_test_webhook", policy_filepath)
 (engine
  .propose_collaboration("adrianmoisey", "kubernetes/kubernetes", 134176)
  .vote("omerap12", True, id=134176)
  .vote("danwinship", False, id=134176)
  .vote("danwinship", True, id=134176)
  .wait_decision(0.5)
  .vote("aojea", True, id=134176)
  .wait_decision(1)
  .vote("k8s-ci-robot", True, id=134176)
  .wait_decision(1)
  .assert_acceptance()
  .equals(True)
  .for_policy("pr_merge"))

def test_replication_kubernetes_pr_134161():
 engine = EngineTesting(8901, "secret_test_webhook", policy_filepath)
 (engine
  .propose_collaboration("skitt", "kubernetes/kubernetes", 134161)
  .vote("pohly", False, id=134161)
  .vote("pohly", True, id=134161)
  .wait_decision(0.5)
  .wait_decision(1)
  .vote("k8s-ci-robot", True, id=134161)
  .wait_decision(1)
  .assert_acceptance()
  .equals(True)
  .for_policy("pr_merge"))

def test_replication_kubernetes_pr_134260():
 engine = EngineTesting(8901, "secret_test_webhook", policy_filepath)
 (engine
  .propose_collaboration("cpanato", "kubernetes/kubernetes", 134260)
  .vote("dims", True, id=134260)
  .wait_decision(0.5)
  .wait_decision(1)
  .vote("k8s-ci-robot", True, id=134260)
  .wait_decision(1)
  .assert_acceptance()
  .equals(True)
  .for_policy("pr_merge"))

def test_replication_kubernetes_pr_134304():
 engine = EngineTesting(8901, "secret_test_webhook", policy_filepath)
 (engine
  .propose_collaboration("humblec", "kubernetes/kubernetes", 134304)
  .vote("xing-yang", False, id=134304)
  .vote("xing-yang", False, id=134304)
  .vote("xing-yang", True, id=134304)
  .wait_decision(0.5)
  .wait_decision(1)
  .vote("k8s-ci-robot", True, id=134304)
  .wait_decision(1)
  .assert_acceptance()
  .equals(True)
  .for_policy("pr_merge"))

def test_replication_kubernetes_pr_134277():
 engine = EngineTesting(8901, "secret_test_webhook", policy_filepath)
 (engine
  .propose_collaboration("lalitc375", "kubernetes/kubernetes", 134277)
  .vote("liggitt", True, id=134277)
  .wait_decision(0.5)
  .wait_decision(1)
  .vote("k8s-ci-robot", True, id=134277)
  .wait_decision(1)
  .assert_acceptance()
  .equals(True)
  .for_policy("pr_merge"))

def test_replication_kubernetes_pr_134136():
 engine = EngineTesting(8901, "secret_test_webhook", policy_filepath)
 (engine
  .propose_collaboration("mariafromano-25", "kubernetes/kubernetes", 134136)
  .wait_decision(0.5)
  .wait_decision(1)
  .wait_decision(1)
  .assert_acceptance()
  .equals(False)
  .for_policy("pr_merge"))

def test_replication_kubernetes_pr_134220():
 engine = EngineTesting(8901, "secret_test_webhook", policy_filepath)
 (engine
  .propose_collaboration("oscarzhou", "kubernetes/kubernetes", 134220)
  .vote("Jefftree", False, id=134220)
  .vote("aojea", False, id=134220)
  .wait_decision(0.5)
  .wait_decision(1)
  .vote("k8s-ci-robot", False, id=134220)
  .wait_decision(1)
  .assert_acceptance()
  .equals(False)
  .for_policy("pr_merge"))

def test_replication_kubernetes_pr_134202():
 engine = EngineTesting(8901, "secret_test_webhook", policy_filepath)
 (engine
  .propose_collaboration("AwesomePatrol", "kubernetes/kubernetes", 134202)
  .vote("serathius", False, id=134202)
  .vote("serathius", False, id=134202)
  .vote("serathius", False, id=134202)
  .wait_decision(0.5)
  .wait_decision(1)
  .wait_decision(1)
  .assert_acceptance()
  .equals(False)
  .for_policy("pr_merge"))

def test_replication_kubernetes_pr_134181():
 engine = EngineTesting(8901, "secret_test_webhook", policy_filepath)
 (engine
  .propose_collaboration("mayank-agrwl", "kubernetes/kubernetes", 134181)
  .vote("pohly", False, id=134181)
  .wait_decision(0.5)
  .wait_decision(1)
  .wait_decision(1)
  .assert_acceptance()
  .equals(False)
  .for_policy("pr_merge"))

def test_replication_kubernetes_pr_134306():
 engine = EngineTesting(8901, "secret_test_webhook", policy_filepath)
 (engine
  .propose_collaboration("novahe", "kubernetes/kubernetes", 134306)
  .wait_decision(0.5)
  .wait_decision(1)
  .wait_decision(1)
  .assert_acceptance()
  .equals(False)
  .for_policy("pr_merge"))