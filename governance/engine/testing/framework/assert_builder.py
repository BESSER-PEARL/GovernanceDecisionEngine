import json
import os
import time
from enum import Enum


class AssertType(Enum):
    ACCEPTANCE = 1
    VOTERS = 2
    VOTE_NUMBER = 3

class DecisionAssertBuilder:
    def __init__(self, test_engine, assert_type: AssertType):
        self._test_engine = test_engine
        self._type = assert_type

    def equals(self, value):
        return DecisionEqualsAssertBuilder(self, value)

    def is_less_than(self, value):
        return DecisionLessAssertBuilder(self, value)

    def is_more_than(self, value):
        return DecisionMoreAssertBuilder(self, value)


class DecisionEqualsAssertBuilder(DecisionAssertBuilder):
    def __init__(self, builder: DecisionAssertBuilder, value):
        super().__init__(builder._test_engine, builder._type)
        self._value = value

    def for_policy(self, name: str):
        self._test_engine._send("result", "result", {"name":name})
        time.sleep(1)
        path = self._test_engine._result_path

        while not os.path.isfile(path):
            pass

        with open(path, "r") as file:
            result = json.loads(file.read())
            if self._type == AssertType.ACCEPTANCE:
                assert self._value == result["acceptance"], f"acceptance is '{result["acceptance"]}' not '{self._value}'"
            elif self._type == AssertType.VOTERS:
                assert self._value == result["voters"]
            elif self._type == AssertType.VOTE_NUMBER:
                assert self._value == len(result["voters"])
        return self._test_engine

    def for_collaboration(self):
        pass

class DecisionLessAssertBuilder(DecisionAssertBuilder):
    def __init__(self, builder: DecisionAssertBuilder, value):
        super().__init__(builder._test_engine, builder._type)
        self._value = value

    def for_policy(self, name: str):
        self._test_engine._send("result", "result", {"name": name})
        path = self._test_engine._result_path

        while not os.path.isfile(path):
            pass

        with open(path, "r") as file:
            result = json.loads(file.read())
            if self._type == AssertType.ACCEPTANCE:
                assert self._value == result["acceptance"], f"acceptance is '{result["acceptance"]}' not '{self._value}'"
            elif self._type == AssertType.VOTERS:
                assert result["voters"].issubset(self._value)
            elif self._type == AssertType.VOTE_NUMBER:
                assert self._value < len(result["voters"])
        return self._test_engine

class DecisionMoreAssertBuilder(DecisionAssertBuilder):
    def __init__(self, builder: DecisionAssertBuilder, value):
        super().__init__(builder._test_engine, builder._type)
        self._value = value

    def for_policy(self, name: str):
        self._test_engine._send("result", "result", {"name": name})
        path = self._test_engine._result_path

        while not os.path.isfile(path):
            pass

        with open(path, "r") as file:
            result = json.loads(file.read())
            if self._type == AssertType.ACCEPTANCE:
                assert self._value == result["acceptance"], f"acceptance is '{result["acceptance"]}' not '{self._value}'"
            elif self._type == AssertType.VOTERS:
                assert result["voters"].issuperset(self._value)
            elif self._type == AssertType.VOTE_NUMBER:
                assert self._value > len(result["voters"])
        return self._test_engine


class PolicyAssertBuilder:
    def was_used(self, test_engine, policy_name: str):
        pass