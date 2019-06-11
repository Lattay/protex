from protex.lexer import Lexer
from protex.parser import Parser

from protex.commands import CommandDict, CommandPrototype, PrintOnePrototype

# test data
t1 = '''\
\\title{Un titre}

Des histoires de \\phi.
Pouet.'''

r1 = '''\
Un titre

Des histoires de phi. Pouet.'''

commands = CommandDict({
    'title': PrintOnePrototype('title'),
    'phi': CommandPrototype('phi', 0, 'phi'),
}, default_proto=lambda name: None)


def test_clean_1():
    lx = Lexer.from_source(t1)
    psr = Parser(lx, commands)
    root = psr.parse()
    assert root.render() == r1
