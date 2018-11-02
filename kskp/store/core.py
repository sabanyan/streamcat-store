class Store:
    pass

class Source:
    pass

class PathFileSource(Source):
    def __init__(self, path):
        self.path = path

    def data(self):
        from pathlib import Path
        return [PathLink(p) for p in Path(self.path).iterdir()]

class Datum:
    pass

class Command(Datum):
    def __init__(self):
        self.i_ports = []
        self.o_ports = []
        self.params = []

    def run(self, args=None, inputs=None):
        return {}

# class Future(Command):
#     pass

class PathLink(Command):
    def __init__(self, source: PathFileSource):
        super().__init__()
        self.source = source

    def __repr__(self):
        return f'PathLink({repr(self.source.path.as_posix())})'