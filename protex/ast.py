import re


class TextPos:
    def __init__(self, col, line):
        self.col = col
        self.line = line

    def __repr__(self):
        return self.__class__.__name__ + '({}, {})'.format(self.col, self.line)

    def __str__(self):
        return 'L{}C{}'.format(self.line, self.col)

    def __add__(self, num):
        if isinstance(num, int):
            return TextPos(self.col + num, self.line)
        elif isinstance(num, TextDeltaPos):
            return TextPos(self.col if num.line == 0 else num.col, self.line + num.line)
        else:
            raise ValueError('Cannot add TextPos with {}'.format(num))

    def __radd__(self, num):
        return self + num

    def __sub__(self, other):
        assert self >= other
        if self == other:
            return TextDeltaPos(0, 0)
        else:
            return TextDeltaPos(
                self.col - other.col if self.line == other.line else other.col,
                self.line - other.line
            )

    def __rsub__(self, other):
        return self - other

    def __gt__(self, other):
        return self.line > other.line or (self.line == other.line
                                          and self.col > other.col)

    def __ge__(self, other):
        return self.line > other.line or (self.line == other.line
                                          and self.col >= other.col)

    def __lt__(self, other):
        return not (self >= other)

    def __le__(self, other):
        return not (self > other)

    def __eq__(self, other):
        return self.line == other.line and self.col == other.col


class TextDeltaPos(TextPos):
    @classmethod
    def from_src(self, src):
        lines = src.split('\n')
        if lines:
            return TextDeltaPos(len(lines[-1]), len(lines))
        else:
            return TextDeltaPos(0, 0)

    def __str__(self):
        if self.line == 0:
            return 'c+{}'.format(self.col)
        else:
            return 'l+{}C{}'.format(self.line, self.col)


class TextPosOutOfRangeError(ValueError):
    pass


class AstNode:
    def __init__(self, start, end):
        self.src_start = start
        self.src_end = end
        self.res_start = start
        self.res_end = end
        self._rendered = False

    def _render(self, from_pos, to_pos):
        self._rendered = True
        self.res_start = from_pos
        self.res_end = to_pos

    def src_to_res_pos(self, p):
        raise NotImplementedError()

    def res_to_src_pos(self, p):
        raise NotImplementedError()

    def dump_pos_map(self):
        raise NotImplementedError()


class Token(AstNode):
    def src_to_res_pos(self, init_pos):
        assert self._rendered
        if not (init_pos >= self.src_start and init_pos < self.src_end):
            raise TextPosOutOfRangeError()
        return self._final_pos + (init_pos - self.start)

    def res_to_src_pos(self, final_pos):
        assert self._rendered
        if not (final_pos >= self.res_start and final_pos < self.res_end):
            raise TextPosOutOfRangeError()
        return self.start_pos + (final_pos - self.res_start)

    def dump_pos_map(self):
        assert self._rendered
        return [(self.src_start, self.src_end, self.res_start, self.res_end)]


class PlainText(Token):
    def __init__(self, start, content):
        self.content = content
        Token.__init__(self, start, len(content))

    def render(self, at_pos):
        self._render(at_pos, at_pos + TextDeltaPos.from_src(self.content))
        return self.content


class BlankToken(Token):
    def render(self, at_pos):
        self._render(at_pos, at_pos)
        return ''


class OpenBra(BlankToken):
    def __init__(self, pos):
        Token.__init__(self, pos, pos + 1)


class CloseBra(BlankToken):
    def __init__(self, pos):
        Token.__init__(self, pos, pos + 1)


class CommandTok(BlankToken):
    def __init__(self, start, content):
        self.name = content[1:]
        Token.__init__(self, start, start + len(content))


sep_re = re.compile('{|}')


class CommandTemplate:
    def __init__(self, definition):
        self.source = definition

    def parse(self):
        c = 0
        mc = len(self.source)
        buff = []
        while c < mc:
            if self.source[c] == '%':
                if buff:
                    yield ''.join(buff)
                    buff = []
                if c == mc - 1 or self.source[c + 1] == '%':
                    yield '%'
                    c += 1
                else:
                    c += 1
                    while c < mc and self.source[mc].isdigit():
                        buff.append(c)
                    yield int(''.join(buff))
                    buff = []
            else:
                buff.append(c)
                c += 1
        if buff:
            yield ''.join(buff)

    def render(self, args):
        res = []
        for tok in self.parse():
            if isinstance(tok, int):
                res.append(args[tok])
            else:
                res.append(PlainText(tok))
        return res


class Command(AstNode):
    def __init__(self, start, end, name, command_args, template):
        self.name = name
        self.args = command_args
        self.template = CommandTemplate(start, end, template)
        self.toks = []
        AstNode.__init__(self, start, end)

    def render(self, at_pos):
        self.toks = self.template.render(self.args)
        res = []
        new_pos = at_pos
        for tok in self.toks:
            tres = tok.render()
            new_pos += TextDeltaPos.from_src(tres)
            res.append(tres)
        self._rendered(at_pos, new_pos)
        return ''.join(res)

    def src_to_res_pos(self, init_pos):
        assert self._rendered
        if not (init_pos >= self.src_start and init_pos < self.src_end):
            raise TextPosOutOfRangeError()
        for tok in self.toks:
            try:
                return tok.src_to_res_pos(init_pos)
            except TextPosOutOfRangeError:
                pass

    def res_to_src_pos(self, final_pos):
        assert self._rendered
        if not (final_pos >= self.res_start and final_pos < self.res_end):
            raise TextPosOutOfRangeError()
        for tok in self.toks:
            try:
                return tok.res_to_src_pos(final_pos)
            except TextPosOutOfRangeError:
                pass

    def dump_pos_map(self):
        return (m for t in self.toks for m in t.dump_pos_map())
