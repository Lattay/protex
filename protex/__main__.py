import argparse

from .lexer import Lexer
from .ast import CommandTok


class ArgParser(object):

    cmds = {
        'list_commands': {
            'help': 'list all command names found in a set of files',
            'aliases': ['list'],
        },
    }

    def __init__(self):
        parser = argparse.ArgumentParser(
            description='tool box for Abinit test'
        )
        sub = parser.add_subparsers(dest='cmd')
        parser.set_defaults(cmd='not a command')

        for cmd in self.cmds:
            cmd_parser = sub.add_parser(cmd, **self.cmds[cmd])
            getattr(self, 'parse_' + cmd)(cmd_parser)

        # Run
        args = parser.parse_args()

        self.unalias(args)

        if args.cmd == 'not a command':
            parser.parse_args(['--help'])
        else:
            getattr(self, args.cmd)(args)

    def alias(self, cmd):
        return self.aliases.get(cmd, {'aliases': []})['aliases']

    def unalias(self, args):
        if args.cmd in self.cmds:
            return
        for cmd, opts in self.cmds.items():
            if args.cmd in opts['aliases']:
                args.cmd = cmd
                return

    def parse_list_commands(self, parser):
        '''
            Create command line argument parser for the diff subcommand
        '''
        parser.add_argument('files', metavar='SOURCE', nargs='+',
                            help='source files')

    def list_commands(self, args):
        lexers = (Lexer(filename) for filename in args.files)
        res = sorted(set(
            tok.name for lx in lexers for tok in lx.token()
            if isinstance(tok, CommandTok)
        ))
        for cmd in res:
            print(cmd)


ArgParser()
