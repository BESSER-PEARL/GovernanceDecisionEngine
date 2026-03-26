import re

from governance.engine.semantics.runtime_metamodel import Collaboration
from metamodel import SinglePolicy, StringList
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

    dyn_indiv._base_individual.roles.add(role)
    role.individuals.add(dyn_indiv._base_individual)


def demote(collab: Collaboration, policy: SinglePolicy):
    regex = re.compile("@([A-Za-z0-9_][A-Za-z0-9_\-]*)")
    dyn_indiv = collab._interaction.get_or_create_dynamic_individual(
        regex.match(collab.scope.element.payload["body"]).group(1))
    the_role = None
    if isinstance(policy.decision_type, StringList):
        the_role = next(policy.decision_type.options())

    if the_role is None:
        return

    role = collab._interaction._roles.get(the_role)
    if role is None:
        return

    for indiv in role.individuals:
        if indiv.name == dyn_indiv.name:
            dyn_indiv._base_individual.roles.remove(role)
            role.individuals.remove(dyn_indiv._base_individual)

