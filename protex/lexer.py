import string
from .ast import (
    PlainText, CommandTok, CloseBra, OpenBra, TextPos, NewParagraph
)


class Lexer:

    ident_chars = set(string.ascii_letters) + set(string.digits) + {
        '-', '_', '+', '*'
    }
    special_chars = {'\\', '{', '}', '%'}

    def __init__(self, source_file, ident_chars=None, special_chars=set()):
        self.source_file = source_file
        self.file = open(self.source_file)
        self.buffer = []
        self.pos = TextPos(0, 1)
        if ident_chars is not None:
            self.ident_chars = ident_chars
        if special_chars is not None:
            self.special_chars = special_chars

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
                    self.buffer = c
                    c = self.read()
                    while c in self.ident_chars:
                        self.buffer.append(c)
                        c = self.read()
                    yield CommandTok(init_pos, ''.join(self.buffer))

                elif c == '}':
                    yield CloseBra(self.pos)
                    c = self.read()

                elif c == '{':
                    yield OpenBra(self.pos)
                    c = self.read()

            elif c == '\n':
                newlines = 0
                new_par_pos = self.pos()
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
