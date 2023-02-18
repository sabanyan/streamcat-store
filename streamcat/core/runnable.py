"""
コマンドと、それに関係するクラスを定義したモジュール
"""
from enum import Enum, auto
from . import Datum, SavableDatum

class Command(Datum):
    """
    実行(run)可能な最小単位
    """
    def __init__(self, label=None):
        super().__init__(SavableDatum.COMMAND_TYPE, label or self.__class__.__name__)
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

class Types:
    """
    データ型
    複数指定されたデータ型のうち、いずれかの型の値を持つことを意味する
    """
    def __init__(self, types:list) -> None:
        self._types = types

    def __repr__(self):
        return str([t for t in self._types])

    def __contains__(self, type):
        """
        in演算子のオーバーロード
        """
        if isinstance(type, str):
            return self.__contains_sub(type)
        elif isinstance(type, Types):
            # いずれかの型同士が一致すればTrueとする
            for t in type._types:
                if self.__contains_sub(t):
                    return True
            return False

    def __contains_sub(self, type):
        # TODO: サブフローのフローJSONにはPortの型に'frame'が記述されているため、
        # 後方互換として'frame'は'mcmd'と読み替えて比較する
        type1 = 'mcmd' if type == 'frame' else type
        types = ['mcmd' if t == 'frame' else t for t in self._types]

        return type1 in types

class Port:
    """
    データ(Datum)の入力・出力の口。
    runnableなクラス(CommandやFlow)にそれぞれ、
    入力はi_ports属性・出力はo_ports属性として使われる
    """
    def __init__(self, label:str, port_types):
        self.label = label
        if isinstance(port_types, str):
            self.types = Types([port_types])
        elif isinstance(port_types, list):
            self.types = Types(port_types)
        elif isinstance(port_types, Types):
            self.types = port_types
        else:
            raise Exception('port_typesに不正な型の値が指定されました')

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
