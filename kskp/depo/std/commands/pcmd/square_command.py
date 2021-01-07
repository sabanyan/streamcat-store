from kskp.core import Datum, Command, Port

class Square(Command):
    """
    与えられた数値を2乗する
    テストコード内でのみ使用のため、ここに置いておく
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'integer')]
        self.o_ports = [Port('o_sq', 'integer')]

    def run(self, args, inputs):
        # 厳密にはframeじゃないが、まぁテスト用のコマンドなので
        # ラップするのはなんでもいいかなと思いframeにした。
        i = inputs['i'].content if isinstance(inputs['i'], Integer) else inputs['i']
        frame = Integer()
        frame.set_content([[i[0][0] ** 2]])
        return {self.o_ports[0].name: frame}

class Integer(Datum):
    """
    テスト用のクラス
    下記のSquareCommandで使うdatumをラップするためのもの
    """
    def __init__(self):
        super().__init__(None, None, 'test', None)
        self._content = None

    def set_content(self, module):
        self._content = module

    @property
    def content(self):
        return self._content