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
    pass

# class Future(Command):
#     pass

class PathLink(Command):
    def __init__(self, path):
        self.path = path

    def __repr__(self):
        return f'PathLink({repr(self.path.as_posix())})'