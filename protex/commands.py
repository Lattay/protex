class CommandPrototype:
    def __init__(self, expected_narg, template):
        self.expected_narg = expected_narg
        self.template = template


class CommandFileLoader:
    def __init__(self, command_dict, default_proto=None):
        pass

    @classmethod
    def from_file(self, filename):
        pass

    def update(self, other):
        pass

    def get(self, name):
        pass


class CommandFileSeeker:
    pass
