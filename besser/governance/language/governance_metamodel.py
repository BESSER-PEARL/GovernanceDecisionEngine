from enum import Enum, auto
from typing import Any


class Project:
    def __init__(self, name, roles, deadlines, rules):
        self._name: str = name
        self._roles: set[Role] = roles
        self._deadlines: set[Deadline] = deadlines
        self._rules: set[Rule] = rules

    @property
    def roles(self):
        return self._roles

    @property
    def rules(self):
        return self._rules


class Role:
    def __init__(self, name, parent):
        self._name: str = name
        self._parent: Any = parent

    @property
    def name(self):
        return self._name



class Deadline:
    def __init__(self, name, parent):
        self._name: str = name
        self._parent: Any = parent

class Timer(Deadline): 
    def __init__(self, name, parent, timestamp):
        super().__init__(name, parent)
        self._timestamp: int = timestamp

    @property
    def timestamp(self):
        return self._timestamp


class Condition(Deadline): 
    def __init__(self, name, parent, expression):
        super().__init__(name, parent)
        self._expression: str = expression

    @property
    def expression(self):
        return self._expression


class WaitForVote(Deadline): 
    def __init__(self, name, parent, roles):
        super().__init__(name, parent)
        self._roles: set[Role] = set(roles)

    @property
    def roles(self):
        return self._roles


class Rule:
    def __init__(self, name, parent, applied_to, stage, query_filter, deadline, people):
        self._name: str = name
        self._parent: Any = parent
        self._applied_to: CollabType = CollabType[applied_to]
        self._stage: Stage = Stage[stage]
        self._query_filter: str = query_filter
        self._deadline: Deadline = deadline
        self._people: set[Role] = people

    @property
    def deadline(self):
        return self._deadline


class LeaderDriven(Rule):
    def __init__(self, name, parent, applied_to, stage, query_filter, deadline, people, default):
        super().__init__(name, parent, applied_to, stage, query_filter, deadline, people)
        self._default: Rule = default


class Majority(Rule):
    def __init__(self, name, parent, applied_to, stage, query_filter, deadline, people, range_type, min_vote):
        super().__init__(name, parent, applied_to, stage, query_filter, deadline, people)
        self._range_type: RangeType = RangeType[range_type]
        self._min_vote: int = min_vote


class RatioMajority(Majority):
    def __init__(self, name, parent, applied_to, stage, query_filter, deadline, people, range_type, min_vote , ratio):
        super().__init__(name, parent, applied_to, stage, query_filter, deadline, people, range_type, min_vote)
        self._ratio: float = ratio

class Phased(Rule):
    def __init__(self, name, parent, applied_to, stage, query_filter, deadline, people, phases):
        super().__init__(name, parent, applied_to, stage, query_filter, deadline, people)
        self._phases: list[Rule] = phases


class RangeType(Enum):
    PRESENT = auto()
    QUALIFIED = auto()

class CollabType(Enum):
    TASK = auto()
    PATCH = auto()
    COMMENT = auto()
    ALL = auto()

class Stage(Enum):
    TASK_REVIEW = auto()
    PATCH_REVIEW = auto()
    RELEASE = auto()
    ALL = auto()


governance_classes = [Project, Role, Deadline, Timer, Condition, WaitForVote, Rule, LeaderDriven, Majority, RatioMajority, Phased]