from kskps.core import Command

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

# class Future(Command):
#     pass

class PathLink(Command):
    def __init__(self, source: PathFileSource):
        super().__init__()
        self.context.update({'source': source})

    def __repr__(self):
        return f"PathLink({repr(self.context['source'].path.as_posix())})"
