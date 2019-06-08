import argparse
import sys
import json

from .lexer import Lexer
from .ast import CommandTok
from . import parse_with_default


class ArgParser(object):

    cmds = {
        'list_commands': {
            'help': 'list all command names found in a set of files',
            'aliases': ['list'],
        },
        'clean': {
            'help': ('clean a file from its latex and create a mapping'
                     ' of position before and after.'),
            'aliases': ['detex']
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

    def parse_clean(self, parser):
        '''
        '''
        parser.add_argument('file', metavar='SOURCE', help='source file')
        parser.add_argument('-o', '--output', nargs=1, default=None,
                            help='output file. stdout is used if omited.')
        parser.add_argument('-i', '--expand-input', action='store_true',
                            help='enable expanding input commands')
        parser.add_argument('-j', '--json', action='store_true',
                            help='output the result as a JSON')
        parser.add_argument('-c', '--clean', action='store_true',
                            help='output the cleaned text')
        parser.add_argument('-m', '--map', action='store_true',
                            help='output the position mapping (text format)')
        parser.add_argument('-u', '--ugly-json', action='store_true',
                            help=('disable pretty printing options for JSON dump'
                                  ' producing ugly (but compact) JSON'))
        parser.add_argument('-d', '--debug', action='store_true',
                            help='debugging tools')

    def list_commands(self, args):
        lexers = (Lexer.from_file(filename) for filename in args.files)
        res = sorted(set(
            tok.name for lx in lexers for tok in lx.token()
            if isinstance(tok, CommandTok)
        ))
        for cmd in res:
            print(cmd)

    def clean(self, args):
        if args.output:
            try:
                f = open(args.output, 'w')
            except FileNotFoundError:
                print('{} does not exists.'.format(args.output), file=sys.stderr)
                exit(1)
        else:
            f = sys.stdout

        expand_input = args.expand_input

        if args.json:
            output_type = 'json'
        elif args.clean:
            output_type = 'clean'
        elif args.map:
            output_type = 'map'
        else:
            output_type = 'clean'

        if args.debug:
            print(list(Lexer.from_file(args.file).token()))
            root = parse_with_default(args.file, expand_input)
            print(root.elems)
            exit(0)

        root = parse_with_default(args.file, expand_input)

        if output_type == 'json':
            d = {
                'text': root.render(),
                'map': root.dump_pos_map().as_dict()
            }
            if args.ugly_json:
                indent = None
                sep = (',', ':')
            else:
                indent = 2
                sep = (', ', ': ')
            json.dump(d, f, indent=indent, separators=sep)

        elif output_type == 'clean':
            f.write(root.render())

        else:
            root.render()
            f.write(root.dump_pos_map().as_text())


ArgParser()
