from os.path import dirname, join, exists, normpath, expanduser


class CommandPrototype:
    def __init__(self, expected_narg, template):
        self.expected_narg = expected_narg
        self.template = template


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
