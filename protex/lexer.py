import string
from io import StringIO
from os.path import normpath, join, dirname
from .text_pos import text_origin, TextPos
from .ast import (
    PlainText, CommandTok, CloseBra, OpenBra, NewParagraph,
    CloseSqBra, OpenSqBra
)


class Lexer:

    ident_chars = set(string.ascii_letters).union(set(string.digits)).union({
        '-', '+', '*'
    })
    special_chars = {'\\', '{', '}', '%', '[', ']'}
    special_command_chars = {'_', '\\', '%', '{', '}'}

    def __init__(self, source_name, stream, ident_chars=None, special_chars=set()):
        self.source_file = source_name
        self.file = stream
        self.buffer = []
        self.pos = text_origin
        if ident_chars is not None:
            self.ident_chars = ident_chars
        self.special_chars = self.special_chars.union(special_chars)

    @classmethod
    def from_file(cls, filename):
        file = open(filename)
        return cls(filename, file)

    def from_source(cls, source, filename=None):
        if filename is None:
            _filename = 'anonym'
        else:
            _filename = filename
        return cls(StringIO(source), _filename)

    def open_newfile(self, source_file):
        path = normpath(join(dirname(self.source_file), source_file))
        return Lexer(path, ident_chars=self.ident_chars,
                     special_chars=self.special_chars)

    def read(self):
        c = self.file.read(1)
        if c == '\n':
            self.pos = TextPos(0, self.pos.line + 1)
        else:
            self.pos += 1
        return c

    def token(self):
        c = self.read()
        buff_init_pos = self.pos
        while c != '':
            if c in self.special_chars:

                if self.buffer:
                    yield PlainText(buff_init_pos, ''.join(self.buffer))
                    self.buffer = []

                if c == '%':
                    while c != '\n':
                        c = self.read()
                    c = self.read()

                elif c == '\\':
                    init_pos = self.pos
                    self.buffer = [c]
                    c = self.read()
                    while c in self.ident_chars:
                        self.buffer.append(c)
                        c = self.read()
                    if len(self.buffer) == 1 and c in self.special_command_chars:
                        self.buffer.append(c)
                        c = self.read()
                    yield CommandTok(init_pos, ''.join(self.buffer))
                    self.buffer = []

                elif c == '}':
                    yield CloseBra(self.pos)
                    c = self.read()

                elif c == '{':
                    yield OpenBra(self.pos)
                    c = self.read()

                elif c == ']':
                    yield CloseSqBra(self.pos)
                    c = self.read()

                elif c == '[':
                    yield OpenSqBra(self.pos)
                    c = self.read()

            elif c == '\n':
                newlines = 0
                new_par_pos = self.pos
                while c == '\n':
                    newlines += 1
                    c = self.read()

                if newlines > 1:
                    if self.buffer:
                        yield PlainText(buff_init_pos, ''.join(self.buffer))
                        self.buffer = []
                    yield NewParagraph(new_par_pos, self.pos)
                else:
                    self.buffer.append('\n')
            else:
                if not self.buffer:
                    buff_init_pos = self.pos
                self.buffer.append(c)
                c = self.read()

        if self.buffer:
            yield PlainText(buff_init_pos, ''.join(self.buffer))
