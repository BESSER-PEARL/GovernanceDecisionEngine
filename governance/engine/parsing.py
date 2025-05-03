import io

from antlr4.CommonTokenStream import CommonTokenStream
from antlr4.InputStream import InputStream
from antlr4.tree.Tree import ParseTreeWalker

from grammar import PolicyCreationListener, govdslParser, govdslLexer
from grammar.govErrorListener import govErrorListener


def setup_parser(text):
    lexer = govdslLexer(InputStream(text))
    stream = CommonTokenStream(lexer)
    parser = govdslParser(stream)

    error = io.StringIO()

    parser.removeErrorListeners()
    error_listener = govErrorListener(error)
    parser.addErrorListener(error_listener)

    return parser

def parse_text(text):
        parser = setup_parser(text)
        tree = parser.policy()

        listener = PolicyCreationListener()
        walker = ParseTreeWalker()
        walker.walk(listener, tree)
        return listener.get_policy()

def parse(path):
    with open(path, "r") as file:
        return parse_text(file.read())