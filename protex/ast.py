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
            return TextPos(self.col if num.line == 0 else num.col,
                           self.line + num.line)
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


class PosMap:
    pass


class ContiguousPosMap(PosMap):
    def __init__(self, src_start, src_end, final_start, final_end):
        self.src_start = src_start
        self.src_end = src_end
        self.final_start = final_start
        self.final_end = final_end


class RootPosMap(PosMap):
    def __init__(self, filename, maps):
        self.filename = filename
        self.src_start = 0
        self.maps = self.sort(maps)

    def sort(self, maps):
        return sorted(maps, key=lambda it: it.src_start)


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
        return [ContiguousPosMap(self.src_start, self.src_end, self.res_start, self.res_end)]


class PlainText(Token):
    def __init__(self, start, content):
        self.content = content
        super().__init__(start, start + len(content))

    def render(self, at_pos):
        self._render(at_pos, at_pos + TextDeltaPos.from_src(self.content))
        return self.content


class NewParagraph(Token):
    def render(self, at_pos):
        self._render(at_pos, at_pos + TextDeltaPos(0, 2))
        return '\n\n'


class BlankToken(Token):
    def render(self, at_pos):
        self._render(at_pos, at_pos)
        return ''


class OpenBra(BlankToken):
    def __init__(self, pos):
        super().__init__(pos, pos + 1)


class CloseBra(BlankToken):
    def __init__(self, pos):
        super().__init__(pos, pos + 1)


class CommandTok(BlankToken):
    def __init__(self, start, content):
        self.name = content[1:]
        super().__init__(start, start + len(content))


class Group(AstNode):
    def __init__(self, start, end, elems):
        self.elems = elems
        super().__init__(start, end)

    def render(self, at_pos):
        res = []
        new_pos = at_pos
        for elem in self.elems:
            eres = elem.render()
            new_pos += TextDeltaPos.from_src(eres)
            res.append(eres)
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
        return self._final_pos + (init_pos - self.start)

    def res_to_src_pos(self, final_pos):
        assert self._rendered
        if not (final_pos >= self.res_start and final_pos < self.res_end):
            raise TextPosOutOfRangeError()
        for tok in self.toks:
            try:
                return tok.res_to_src_pos(final_pos)
            except TextPosOutOfRangeError:
                pass
        return self.start_pos + (final_pos - self.res_start)

    def dump_pos_map(self):
        return (m for t in self.toks for m in t.dump_pos_map())


class Root(Group):
    def __init__(self, filename, group):
        self.filename = filename
        if group:
            start = group[0].src_start
            stop = group[-1].src_stop
        else:
            start = TextPos(0, 1)
            stop = TextPos(0, 1)
        super().__init__(start, stop, group)

    def dump_pos_map(self):
        return RootPosMap(self.filename, super().dump_pos_map)


sep_re = re.compile('{|}')


class CommandTemplate:
    def __init__(self, start, end, proto):
        self.start = start
        self.end = end
        self.prototype = proto

    def apply(self, args):
        res = []
        for tok in self.prototype.tokens():
            if isinstance(tok, int):
                res.append(args[tok])
            else:
                res.append(PlainText(tok))
        return res


class Command(AstNode):
    def __init__(self, start, end, command_args, proto):
        self.name = proto.name
        self.args = command_args
        self.template = CommandTemplate(start, end, proto)
        self.toks = []
        super().__init__(start, end)

    def render(self, at_pos):
        self.toks = self.template.apply(self.args)
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
