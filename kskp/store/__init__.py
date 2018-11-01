class Store:
    pass

class Source:
    pass

class PathFileSource(Source):
    def __init__(self, path):
        self.path = path
        
    def data(self):
        return []