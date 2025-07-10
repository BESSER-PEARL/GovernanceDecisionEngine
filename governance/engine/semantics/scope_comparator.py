from enum import Enum

from metamodel import Scope, Task, Project, Activity
from utils.gh_extension import Patch, Repository, ActionEnum


class MatchingType(Enum):
    MISMATCH = 1
    MATCH = 2
    INCLUDE = 3

def compare_scopes(expected_scope: Scope, received_scope: Scope):
    if type(expected_scope) == type(received_scope):
        mapping = {
            Project: compare_project,
            Activity: compare_activity,
            Task: compare_task,
            Patch: compare_patch,
            Repository: compare_repository,
            Scope: compare_project
        }
        compare_function = mapping[type(expected_scope)]
        return compare_function(expected_scope, received_scope)

    elif isinstance(expected_scope, Task) or isinstance(received_scope, Project):
        return MatchingType.MISMATCH
    elif isinstance(received_scope, Task):
        match_act = compare_scopes(expected_scope, received_scope.activity)
        return MatchingType.INCLUDE if match_act != MatchingType.MISMATCH else MatchingType.MISMATCH
    elif isinstance(received_scope, Activity):
        match_proj = compare_scopes(expected_scope, received_scope.project)
        return MatchingType.INCLUDE if match_proj != MatchingType.MISMATCH else MatchingType.MISMATCH


def compare_project(expected_scope: Project, received_scope: Project):
    return MatchingType.MATCH

def compare_activity(expected_scope: Activity, received_scope: Activity):
    return compare_scopes(expected_scope.project, received_scope.project)

def compare_task(expected_scope: Task, received_scope: Task):
    return compare_scopes(expected_scope.activity, received_scope.activity)

def compare_repository(expected_scope: Repository, received_scope: Repository):
    return MatchingType.MISMATCH if expected_scope.repo_id != received_scope.repo_id else MatchingType.MATCH

def compare_patch(expected_scope: Patch, received_scope: Patch):
    expected_action = expected_scope.action
    received_action = received_scope.action
    expected_elem = expected_scope.element
    received_elem = received_scope.element

    if (expected_action is not None and
        expected_action is not ActionEnum.ALL and
        received_action is not ActionEnum.ALL and
        expected_action != received_action):
        return MatchingType.MISMATCH

    if type(expected_elem) != type(received_elem):
        return MatchingType.MISMATCH

    if expected_elem.labels is None:
        return compare_scopes(expected_scope.activity, received_scope.activity)

    for label in expected_elem.labels:
        if label not in received_elem.labels:
            return MatchingType.MISMATCH

    return compare_scopes(expected_scope.activity, received_scope.activity)