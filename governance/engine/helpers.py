import io
from datetime import datetime

from antlr4.CommonTokenStream import CommonTokenStream
from antlr4.InputStream import InputStream
from antlr4.tree.Tree import ParseTreeWalker
from besser.agent.core.agent import Agent

from governance.engine.collaboration_metamodel import Collaboration
from governance.engine.events import DeadlineEvent
from grammar import PolicyCreationListener, govdslParser, govdslLexer
from grammar.govErrorListener import govErrorListener
from metamodel import Policy, ComposedPolicy, Role, Deadline


def setup_parser(text):
    lexer = govdslLexer(InputStream(text))
    stream = CommonTokenStream(lexer)
    parser = govdslParser(stream)

    error = io.StringIO()

    parser.removeErrorListeners()
    error_listener = govErrorListener(error)
    parser.addErrorListener(error_listener)

    return parser

def parse(path):
    with open(path, "r") as file:
        text = file.read()

        # Setup parser and create model
        parser = setup_parser(text)
        tree = parser.policy()

        listener = PolicyCreationListener()
        walker = ParseTreeWalker()
        walker.walk(listener, tree)
        return listener.get_policy()

def get_all_roles(policy):
    roles: dict[str,Role]= dict()
    if isinstance(policy, ComposedPolicy):
        for phase in policy.phases:
            phase_roles = get_all_roles(phase)
            roles = roles | phase_roles
    else:
        for participant in policy.participants:
            if isinstance(participant, Role):
                roles[participant.name.lower()] = participant

    return roles

def find_policy_for(policies: set[Policy], collab: Collaboration):
    pass
    # # Pseudo-code for the function
    # # create scope/policy mapping
    # # this require scopes to be hashable (see https://docs.python.org/3/glossary.html#term-hashable)
    # # This should work as scopes can be associated to only one policy
    # # WARNING : Verify that you can not create two Scope object representing the same scope (hence having the same hash)
    # mapping = dict()
    # for policy in policies:
    #     mapping[policy.scope] = policy
    #
    #     # Recursive function to search the scope tree
    #     def find_scoped_rule_for(collab: Collaboration, scope: Scope):
    #         pass
    #         # Pseudo-code for the function
    #         policy = mapping[scope]
    #         if policy:
    #             rule = find_rule_in(policy, collab)
    #             if rule:
    #                 return rule
    #         return find_scoped_rule_for(collab, scope.parent)
    #
    # return find_scoped_rule_for(collab, collab.scope)

def find_starting_policies_in(policy: Policy) -> list[Policy]:
    out = [policy]
    if isinstance(policy, ComposedPolicy):
        if policy.sequential:
            # get the first phase in traverse order (should be a list)
            first_phase = policy.phases[0]
            out.extend(find_starting_policies_in(first_phase))
        else:
            for phase in policy.phases:
                out.extend(find_starting_policies_in(phase))
    return out

# Called for composed policies from which one phase (direct child) was decided but not the composition
def find_policies_in(policy: ComposedPolicy, collab: Collaboration) -> list[Policy]:
    if policy.sequential:
        for phase in policy.phases:
            if phase not in collab.ballot_boxes:
                return find_starting_policies_in(policy)
    # else:  Parallel does not need anything as all the direct child are already started
    return []

def start_policies(agent: Agent, policies: list[Policy], collab: Collaboration) -> None:
    for starting_policy in policies:
        collab.ballot_boxes[starting_policy] = set()
        if isinstance(starting_policy, ComposedPolicy):
            continue

        # Find deadlines and send the associated events
        deadlines = [d for d in starting_policy.conditions if isinstance(d, Deadline)]
        for deadline in deadlines:
            if deadline.date is not None:
                timestamp = deadline.date.timestamp()
                agent.receive_event(DeadlineEvent(collab, starting_policy, timestamp))
            else:
                timestamp = (datetime.now() + deadline.offset).timestamp()
                agent.receive_event(DeadlineEvent(collab, starting_policy, timestamp))