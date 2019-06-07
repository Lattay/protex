class TextPos:
    def __init__(self, col, line):
        self.col = col
        self.line = line

    def as_dict(self):
        return {
            'col': self.col,
            'line': self.line
        }

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
        if other == 0:
            return True
        assert isinstance(other, TextPos)
        return self.line > other.line or (self.line == other.line
                                          and self.col > other.col)

    def __ge__(self, other):
        if other == 0:
            return True
        assert isinstance(other, TextPos)
        return self.line > other.line or (self.line == other.line
                                          and self.col >= other.col)

    def __lt__(self, other):
        if other == 0:
            return False
        assert isinstance(other, TextPos)
        return not (self >= other)

    def __le__(self, other):
        if other == 0:
            return False
        assert isinstance(other, TextPos)
        return not (self > other)

    def __eq__(self, other):
        if other == 0:
            return False
        assert isinstance(other, TextPos)
        return self.line == other.line and self.col == other.col


text_origin = TextPos(0, 1)


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
        if not hasattr(maps, '__iter__'):
            print(maps)
            exit()
        self.maps = self.sort(maps)

    def sort(self, maps):
        return sorted(maps, key=lambda it: it.src_start)

    def _for_all(self):
        root_stack = [self]
        while root_stack:
            root = root_stack.pop()
            yield ('file', root.filename)
            for map in root.maps:
                if isinstance(map, RootPosMap):
                    root_stack.append(map)
                else:
                    yield ('map', map)

    def as_text(self):
        lines = []
        for t, obj in self._for_all():
            if t == 'file':
                lines.append('[{}]'.format(obj))
            else:
                lines.append('{}-{}={}-{}'.format(*obj))
        return '\n'.join(lines)

    def as_dict(self):
        d = {}
        fname = None
        for t, obj in self._for_all():
            if t == 'file':
                fname = obj
                d[fname] = []
            else:
                d[fname].append({
                    'src': (obj.src_start.as_dict(), obj.src_end.as_dict()),
                    'dest': (obj.final_start.as_dict(), obj.final_end.as_dict())
                })
        return d
