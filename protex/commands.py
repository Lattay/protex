from os.path import dirname, join, exists, normpath, expanduser
import json


class CommandPrototype:
    def __init__(self, name, expected_narg, template):
        self.name = name
        self.expected_narg = expected_narg
        self.template = template

    def tokens(self):
        i = 0
        mi = len(self.template)
        buff = []
        while i < mi:
            if self.template[i] == '%':
                if buff:
                    yield ''.join(buff)
                    buff = []
                if i == mi - 1 or self.template[i + 1] == '%':
                    yield '%'
                    i += 1
                else:
                    i += 1
                    while i < mi and self.template[i].isdigit():
                        buff.append(self.template[i])
                        i += 1
                    if buff:
                        i = int(''.join(buff))
                        if i == 0:
                            yield self.name
                        elif i <= self.expected_narg:
                            yield i - 1
                        else:
                            raise ValueError('Template {} is broken.'
                                             .format(self.name))
                    else:
                        yield '%'
                    buff = []
            else:
                buff.append(i)
                i += 1
        if buff:
            yield ''.join(buff)


class PrintLastPrototype(CommandPrototype):
    def __init__(self, name):
        self.name = name
        self.expected_narg = 100

    def tokens(self):
        yield -1


class PrintNamePrototype(CommandPrototype):
    def __init__(self, name):
        self.name = name
        self.expected_narg = 0

    def tokens(self):
        yield self.name


class DiscardPrototype(CommandPrototype):
    def __init__(self, name):
        self.name = name

    def tokens(self):
        yield from ()  # empty generator


class IllformedCommandJSON(ValueError):
    pass


class CommandLoader:
    def __init__(self, command_dict, default_proto=None):
        self.dict = command_dict
        self.default = default_proto

    @classmethod
    def from_file(cls, filename, default_proto=None):
        commands = {}
        with open(filename) as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise IllformedCommandJSON()

            if 'print_last' in data and isinstance(data['print_last'], (tuple, list)):
                for cmd in data['print_last']:
                    if not isinstance(cmd, str):
                        raise IllformedCommandJSON()
                    commands[cmd] = PrintLastPrototype(cmd)

            if 'print_name' in data and isinstance(data['print_name'], (tuple, list)):
                for cmd in data['print_name']:
                    if not isinstance(cmd, str):
                        raise IllformedCommandJSON()
                    commands[cmd] = PrintNamePrototype(cmd)

            if 'discard' in data and isinstance(data['discard'], (tuple, list)):
                for cmd in data['discard']:
                    if not isinstance(cmd, str):
                        raise IllformedCommandJSON()
                    commands[cmd] = DiscardPrototype(cmd)

            if 'other' in data and isinstance(data['other'], dict):
                for cmd in data['other']:
                    if not (isinstance(cmd, str)
                            and isinstance(data[cmd], (list, tuple))
                            and len(data[cmd]) == 2
                            and isinstance(data[cmd][0], int)
                            and isinstance(data[cmd][1], str)):
                        raise IllformedCommandJSON()
                    commands[cmd] = CommandPrototype(cmd, *data[cmd])
        return cls(cmd, default_proto)

    def update(self, other):
        self.dict.update(other.dict)

    def get(self, name):
        return self.dict.get(name, self.default)


class NoCommandFileFoundError(FileNotFoundError):
    pass


def command_file_seek(start_dir, file_name='commands.json', hidden_name=None):
    if hidden_name is None:
        hidden_name = '.' + file_name

    files = []

    current_dir = normpath(start_dir)
    while current_dir != '/':
        hf = join(start_dir, hidden_name)
        if exists():
            files.append(hf)
        current_dir = dirname(current_dir)

    user = join(expanduser('~'), hidden_name)
    if exists(user):
        files.append(user)

    default = join(dirname(dirname(__file__)), file_name)
    if exists(default):
        files.append(default)

    if not files:
        raise NoCommandFileFoundError("No command file have been found.")

    return reversed(files)


def load_all_files(name='commands.json'):
    files = command_file_seek('.', file_name=name)

    default_proto = DiscardPrototype()

    commands = CommandLoader({}, default_proto)
    for f in files:
        new = CommandLoader.from_file(f)
        commands.update(new)

    return commands
