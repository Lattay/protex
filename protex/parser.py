from .text_pos import text_origin
from .ast import (
    CommandTok, CloseBra, OpenBra, PlainText, Command, Group, NewParagraph,
    Root, BlankToken
)


class ParserError(Exception):
    pass


class UnpairedBracketError(ParserError):
    def __init__(self, pos):
        super().__init__('Found unpaired closing bracket at {}.'.format(pos))


class Parser:
    def __init__(self, lexer, commands, filename='anonym', **opts):
        self._tok_back_stack = []
        self.lexer = lexer
        self._tokens = lexer.token()
        self.commands = commands
        self.options = opts
        self.filename = filename

    def next_tok(self):
        if self._tok_back_stack:
            return self._tok_back_stack.pop()
        else:
            try:
                return next(self._tokens)
            except StopIteration:
                pass

    def tok_push_back(self, tok):
        self._tok_back_stack.append(tok)

    def parse(self):
        root, _ = self._parse(0)
        return Root(self.filename, root)

    def _parse(self, deep):
        nodes = []
        node = self._parse_node(deep)
        while node is not None and not isinstance(node, CloseBra):
            nodes.append(node)
            node = self._parse_node(deep)

        if deep == 0 and node is not None:
            raise UnpairedBracketError(node.src_end)

        if deep > 0 and node is None:
            print(nodes)
            raise UnpairedBracketError(text_origin)
        return nodes, node

    def _parse_command(self, prototype, deep):
        if prototype.expected_narg == 0:
            return []
        args = []
        next_arg = self._parse_node(deep)
        c = 0
        while (c < prototype.expected_narg
               and next_arg is not None
               and not isinstance(next_arg, (PlainText, NewParagraph))):
            args.append(next_arg)
            c += 1
            next_arg = self._parse_node(deep)

        if c == prototype.expected_narg:
            self.tok_push_back(next_arg)

        elif isinstance(next_arg, PlainText):
            if not next_arg.content[0].isspace():
                args.append(PlainText(next_arg.src_start, next_arg.content[0]))
            if len(next_arg.content) > 1:
                self.tok_push_back(
                    PlainText(next_arg.src_start + 1, next_arg.content[1:])
                )
        return args

    def _parse_input(self, input_tok, deep):
        next_node = self._parse_node(deep)
        if not (isinstance(next_node, Group)
                and next_node.elems
                and isinstance(next_node.elems[0], PlainText)):
            raise SyntaxError(
                'Illformed input command at {}'.format(next_node.src_start)
            )
        blank = BlankToken(input_tok.src_start, next_node.src_end)
        if self.options.get('expand_input', False):
            filename = next_node.elems[0].content
            content, _ = Parser(self.lexer.open_newfile(filename),
                                self.commands)._parse(0)
            self.tok_push_back(Root(filename, content))
        return blank

    def _parse_node(self, deep):
        tok = self.next_tok()
        if isinstance(tok, OpenBra):
            group, close_bra = self._parse(deep + 1)
            return Group(tok.src_start, close_bra.src_end, group)
        elif isinstance(tok, CommandTok):
            if tok.name == 'input':
                return self._parse_input(tok, deep)
            else:
                start_pos = tok.src_start
                prototype = self.commands.get(tok.name)
                args = self._parse_command(prototype, deep)
                if args:
                    end_pos = args[-1].src_end
                else:
                    end_pos = tok.src_end
                return Command(start_pos, end_pos, args, prototype)
        else:
            return tok
