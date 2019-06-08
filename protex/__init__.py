from .commands import load_all_files
from .lexer import Lexer
from .parser import Parser


def parse_with_default(filename, expand_input=False):
    commands = load_all_files()
    lexer = Lexer.from_file(filename)
    parser = Parser(lexer, commands, filename=filename,
                    expand_input=expand_input)
    return parser.parse()
