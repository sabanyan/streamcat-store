"""
コマンドと、それに関係するクラスを定義したモジュール
"""
from enum import Enum, auto
from . import Datum

class Command(Datum):
    """
    実行(run)可能な最小単位
    """
    def __init__(self):
        super().__init__(None, None, Datum.COMMAND_TYPE, self.__class__.__name__)
        self.i_ports = []
        self.o_ports = []
        self.params = []
        self.lasts = {}

    def run(self, args={}, inputs={}):
        """
        実行する
        - `args`: 実行処理に渡す引数
        - `inputs`: 実行処理の入力値
        """
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

    def __lt__(self, other):
        """
        label名で大小比較する (数字 < 文字 とする)
        """
        # お互いのlabel名が'*'で始まる場合は、それに続く文字列が数字か否か判定する
        if self.label[0] == '*' and other.label[0] == '*':
            self_label = self.label[1:]
            other_label = other.label[1:]
        else:
            self_label = self.label
            other_label = other.label

        # 数字文字列か否かを判定する
        self_label_is_str = not self_label.isdigit()
        other_label_is_str = not other_label.isdigit()

        # 大小比較する
        if self_label_is_str and other_label_is_str:
            return self_label < other_label
        elif self_label_is_str:
            return False
        elif other_label_is_str:
            return True
        else:
            return int(self_label) < int(other_label)

    def __gt__(self, other):
        return not self < other

class Parameter:
    """
    パラメータ定義1つを表す
    - `param name`: パラメータ名。必須
    - `param caption`: このパラメータを表す短いタイトル。GUI上でのラベルとして使われる。
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
