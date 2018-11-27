from enum import Enum, auto

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
    def __init__(self):
        self.context = {}

class Port:
    def __init__(self, name, port_type):
        self.name = name
        self.type = port_type

    def __repr__(self):
        return f'<Port({self.name})>'

class Parameter:
    """
    パラメータ定義1つを表す

    :param name: パラメータ名。必須
    :param caption: このパラメータを表す短いタイトル。GUI上でのラベルとして使われる。
                    オプショナルで、未指定だとnameと同じになる。
    """

    class WidgetType(Enum):
        """
        パラメータ値の分類を表す。
        type属性に使われ、
        この値によってGUI上で使われる部品が変化することを想定している
        """
        TEXTBOX = auto()


    def __init__(self, name, caption=None):
        assert name is not None and name != '', 'nameは必須です'

        self.name = name
        if caption is None:
            self.caption = name
        else:
            self.caption = caption

        self.widget_type = self.WidgetType.TEXTBOX

        # self.default = None
        # self.validation = None

class Command(Datum):
    def __init__(self):
        super().__init__()
        self.i_ports = []
        self.o_ports = []
        self.params = []

        self.lasts = {}

    def run(self, args=None, inputs=None):
        result = {}
        self.lasts = result
        return result

# class Future(Command):
#     pass

class PathLink(Command):
    def __init__(self, source: PathFileSource):
        super().__init__()
        self.context.update({'source': source})

    def __repr__(self):
        return f"PathLink({repr(self.context['source'].path.as_posix())})"