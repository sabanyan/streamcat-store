# Store用コマンド

import nysol.mcmd as nm

from kskp.library import NysolModule
from kskp.core import Command, Port

class SaverCommand(Command):
    """
    指定されているstoreに出力するコマンド（テスト用）
    基本的にはlastsを保存するためにある
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame'), Port('store', 'store')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        # 1. storeにsaveする
        datum_module = inputs['store'].save(args, inputs['i'])
        # 2. lasts用なのでコマンド実行のrunをする（繋げる必要はない）
        result = datum_module.run(msg='on')

        return {'o': self.wrap_datum(result, args)}

    def get_datum_obj(self):
        from kskp.engine import Frame
        return Frame()

    def wrap_datum(self, datum_module, args):
        datum = self.get_datum_obj()
        datum.set_cache_info(args)
        datum.set_content(datum_module)
        return datum

class CacheSaverCommand(SaverCommand):
    """
    指定されているstoreに出力するコマンド（テスト用）
    キャッシュ作成用で、Cache型で返すので別クラスで作った
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame'), Port('store', 'store')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        # 1. storeにsaveする(runはしない)
        datum_module = inputs['store'].save(args, inputs['i'])
        return {'o': self.wrap_datum(datum_module, args)}

    def get_datum_obj(self):
        # 書いて気づいたけどコンストラクタで決め打ちで設定でいいのかな。。。？
        from kskp.engine import Cache
        return Cache()

class LoaderCommand(Command):
    """
    指定したstoreからデータを取ってくる（テスト用）
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('store', 'store')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        nysol_module = NysolModule()
        nysol_module.set_content(inputs['store'].load(args['uuid']))
        return {'o': nysol_module}
