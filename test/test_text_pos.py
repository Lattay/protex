from protex.lexer import Lexer
from protex.text_pos import TextDeltaPos, TextPos

# test data
t1 = '''\
Un texte

Avec des lignes vides
et des \\commandes{avec}{des argument}.
Et qui finit pas par un newline.
Pouet.'''

t2 = '''Un bout de texte sans newline.'''


def test_text_delta_pos():
    tp = TextDeltaPos.from_source(t1)
    assert tp.offset == len(t1)
    assert tp.line == 6
    assert tp.col == 6

    tp = TextDeltaPos.from_source(t2)
    assert tp.offset == len(t2)
    assert tp.line == 1
    assert tp.col == len(t2)


def test_text_pos_from_source():
    tp = TextPos.from_source(t1)
    assert tp.offset == len(t1)
    assert tp.line == 6
    assert tp.col == 6

    tp = TextPos.from_source(t2)
    assert tp.offset == len(t2)
    assert tp.line == 1
    assert tp.col == len(t2)


def test_text_pos_from_lexer():
    lx = Lexer.from_source(t1)
    list(lx.tokens())
    assert lx.pos.offset == len(t1)
    assert lx.pos.line == 6
    assert lx.pos.col == 6


def test_text_pos_additive():
    tp1 = TextPos.from_source(t1 + ' ' + t2)

    tp2 = TextPos.from_source(t1 + ' ') + TextDeltaPos.from_source(t2)
    assert tp1 == tp2

    tp2 = TextPos.from_source(t1) + TextDeltaPos.from_source(' ' + t2)
    assert tp1 == tp2

    tp1 = TextPos.from_source(t1 + '\n' + t2)
    tp2 = TextPos.from_source(t1 + '\n') + TextDeltaPos.from_source(t2)
    assert tp1 == tp2

    tp2 = TextPos.from_source(t1) + TextDeltaPos.from_source('\n' + t2)
    assert tp1 == tp2
