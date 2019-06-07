import re
from .text_pos import text_origin, ContiguousPosMap, TextDeltaPos, RootPosMap


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

    def __repr__(self):
        return '<{}>'.format(self.__class__.__name__)


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

    def __repr__(self):
        return '<PlainText:{}>'.format(self.content[:5])


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

    def __repr__(self):
        return '<CommandTok: {}>'.format(self.name)


class Group(AstNode):
    def __init__(self, start, end, elems):
        self.elems = elems
        super().__init__(start, end)

    def render(self, at_pos):
        res = []
        new_pos = at_pos
        for elem in self.elems:
            eres = elem.render(new_pos)
            new_pos += TextDeltaPos.from_src(eres)
            res.append(eres)
        self._render(at_pos, new_pos)
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
        for e in self.elems:
            pmap = e.dump_pos_map()
            if isinstance(pmap, RootPosMap):
                yield pmap
            else:
                yield from pmap

    def __repr__(self):
        return '<Group:{}>'.format(self.elems)


class Root(Group):
    def __init__(self, filename, group):
        self.filename = filename
        if group:
            start = group[0].src_start
            stop = group[-1].src_end
        else:
            start = text_origin
            stop = text_origin
        super().__init__(start, stop, group)

    def dump_pos_map(self):
        return RootPosMap(self.filename, super().dump_pos_map())

    def render(self, at_pos=text_origin):
        return super().render(at_pos)

    def __repr__(self):
        return '<Root:{}>'.format(self.elems)


sep_re = re.compile('{|}')


class CommandTemplate:
    def __init__(self, start, end, proto):
        self.start = start
        self.end = end
        self.prototype = proto

    def apply(self, src_start, args):
        res = []
        for tok in self.prototype.tokens():
            if isinstance(tok, int):
                res.append(args[tok])
            else:
                res.append(PlainText(src_start, tok))
        return res


class Command(AstNode):
    def __init__(self, start, end, command_args, proto):
        self.name = proto.name
        self.args = command_args
        self.template = CommandTemplate(start, end, proto)
        self.toks = []
        super().__init__(start, end)

    def render(self, at_pos):
        self.toks = self.template.apply(self.src_start, self.args)
        res = []
        new_pos = at_pos
        for tok in self.toks:
            tres = tok.render(new_pos)
            new_pos += TextDeltaPos.from_src(tres)
            res.append(tres)
        self._render(at_pos, new_pos)
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

    def __repr__(self):
        return '<Command:{}-{}>'.format(self.name, self.args)
