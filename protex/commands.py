from os.path import dirname, join, exists, normpath, expanduser


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
                            raise ValueError('Template {} is broken.'.format(self.name))
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


class PrintName(CommandPrototype):
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


class CommandFileLoader:
    def __init__(self, command_dict, default_proto=None):
        pass

    @classmethod
    def from_file(self, filename, default_proto=None):
        pass

    def update(self, other):
        pass

    def get(self, name):
        pass


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

    return files


def load_all_files(name='commands.json'):
    files = reversed(command_file_seek('.', file_name=name))

    default_proto = CommandPrototype(100, "")

    commands = CommandFileLoader({}, default_proto)
    for f in files:
        new = CommandFileLoader.from_file(f)
        commands.update(new)

    return commands
