from streamcat.core import Command, Port
from streamcat.store import Matrix

class Square(Command):
    """
    与えられた数値を2乗する
    テストコード内でのみ使用のため、ここに置いておく
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'matrix')]
        self.o_ports = [Port('o_sq', 'matrix')]

    def run(self, args, inputs):
        m = inputs['i'].content if isinstance(inputs['i'], Matrix) else inputs['i']
        return {self.o_ports[0].label : Matrix([[m[0][0] ** 2]])}
