import os
import re
import subprocess

from governance.engine.semantics.helpers import update_individual
from governance.engine.semantics.runtime_metamodel import Collaboration
from metamodel import SinglePolicy, StringList, Individual, Role
from utils.chp_extension import Patch, PatchAction, PullRequest, MemberLifecycle, MemberAction


def resolve_action(collab: Collaboration, policy: SinglePolicy):
    scope = policy.scope
    if isinstance(scope, Patch):
        if isinstance(scope.element, PullRequest):
            if scope.action == PatchAction.MERGE:
                merge_PR(collab)
    elif isinstance(scope, MemberLifecycle):
        if scope.action == MemberAction.ONBOARD:
            promote(collab, policy)
        if scope.action == MemberAction.REMOVE:
            demote(collab, policy)

def merge_PR(collab: Collaboration):
    pr = collab.scope.element
    if isinstance(pr, PullRequest):
        collab._platform.put(
            f"/repos/{collab.scope.activity.project.repo_id}/pulls/{pr.payload["number"]}/merge",
            data={
                "commit_title": "Validated Merge",
                "commit_message": "Merge of a pull request validated by the decision engine"
            })

def close_PR(collab: Collaboration):
    pr = collab.scope.element
    if isinstance(pr, PullRequest):
        collab._platform.patch(
            f"/repos/{collab.scope.activity.project.repo_id}/pulls/{pr.payload["number"]}",
            data={
                "state": "closed"
            })

def close_issue(collab: Collaboration):
    pr = collab.scope.element
    if isinstance(pr, PullRequest):
        collab._platform.patch(
            f"/repos/{collab.scope.activity.project.repo_id}/issues/{pr.payload["number"]}",
            data={
                "state": "closed"
            })

def promote(collab: Collaboration, policy: SinglePolicy):
    regex = re.compile("@([A-Za-z0-9_][A-Za-z0-9_-]*)")
    issue_body = collab.scope.element.payload["body"]
    matchname = regex.search(issue_body)
    username = matchname.group(1)
    dyn_indiv = collab._interaction.get_or_create_dynamic_individual(username)
    the_role = None
    if isinstance(policy.decision_type, StringList):
        the_role = next(iter(policy.decision_type.options))

    if the_role is None:
        return

    role = collab._interaction._roles.get (the_role)
    if role is None:
        return

    for indiv in role.individuals:
        if indiv.name == dyn_indiv.name:
            return

    role.individuals.add(dyn_indiv._base_individual)
    update_indiv_in_gov_file(dyn_indiv._base_individual, collab._interaction._roles.values())


def demote(collab: Collaboration, policy: SinglePolicy):
    regex = re.compile("@([A-Za-z0-9_][A-Za-z0-9_-]*)")
    issue_body = collab.scope.element.payload["body"]
    matchname = regex.search(issue_body)
    username = matchname.group(1)
    dyn_indiv = collab._interaction.get_or_create_dynamic_individual(username)
    the_role = None
    if isinstance(policy.decision_type, StringList):
        the_role = next(iter(policy.decision_type.options))

    if the_role is None:
        return

    role = collab._interaction._roles.get(the_role)
    if role is None:
        return

    real_indiv = None
    for indiv in role.individuals:
        if indiv.name == dyn_indiv.name:
            real_indiv = indiv
    role.individuals.remove(real_indiv)
    update_indiv_in_gov_file(real_indiv, collab._interaction._roles.values())

def update_indiv_in_gov_file(indiv: Individual, roles: set[Role]):
    dir, file_name = os.path.split(os.environ["PLAYGROUND_POLICY"])
    subprocess.run(["git", "pull"], cwd=dir)
    with open(os.environ["PLAYGROUND_POLICY"], "r") as file:
        data = file.read()

    new_version = update_individual(data, indiv, roles)

    with open(os.environ["PLAYGROUND_POLICY"], "w") as file:
        file.write(new_version)

    subprocess.run(["git", "add", file_name], cwd=dir)
    subprocess.run(["git", "commit", "-m", "Update roles in governance"], cwd=dir)
    subprocess.run(["git", "push"], cwd=dir)



