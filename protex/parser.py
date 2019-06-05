from .ast import CommandTok, CloseBra, OpenBra, PlainText, Command


class Parser:
    def __init__(self, tokens, commands):
        self.tokens = tokens
        self.commands = commands

    def parse(self):
        for tok in self.tokens:
            if isinstance(tok, PlainText):
                pass
