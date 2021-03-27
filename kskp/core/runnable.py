"""
コマンドと、それに関係するクラスを定義したモジュール
"""
from enum import Enum, auto
from . import Datum

class Command(Datum):
    """
    実行(run)可能な最小単位。
    """
    def __init__(self):
        super().__init__(None, None, 'command', self.__class__.__name__)
        self.i_ports = []
        self.o_ports = []
        self.params = []

        self.lasts = {}

    def run(self, args={}, inputs={}):
        result = {}
        self.lasts = result
        return result

    def dtor(self, args={}):
        pass

class Port:
    """
    データ(Datum)の入力・出力の口。
    runnableなクラス(CommandやFlow)にそれぞれ、
    入力はi_ports属性・出力はo_ports属性として使われる
    """
    def __init__(self, label, port_type):
        self.label = label
        self.type = port_type

    def __repr__(self):
        return f'<Port({self.label})>'

    def __eq__(self, other):
        return self.label == other.label

    def __ne__(self, other):
        return self.label != other.label

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
