# Store用コマンド
import os
import nysol.mcmd as nm

from kskp.library import NysolModule, Cache, Frame
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
        datum_module = inputs['store'].save(self, args, inputs['i'])
        # 2. lasts用なのでコマンド実行のrunをする（繋げる必要はない）
        # result = datum_module.run(msg='on')

        return {'o': self.wrap_datum(datum_module, args)}

    def module(self, args, input):
        command_args = {}
        command_args['i'] = input
        command_args['o'] = args['frame_path'].as_posix()
        return nm.m2tee(command_args)

    def get_datum_obj(self):
        from kskp.store import FRAME_FOLDER_UUID
        return Frame(FRAME_FOLDER_UUID, 'frame', None)

    def wrap_datum(self, datum_module, args):
        datum = self.get_datum_obj()
        datum.set_centext(args)
        datum.set_content(datum_module)
        return datum

class CacheSaverCommand(SaverCommand):
    """
    指定されているstoreに出力するコマンド（テスト用）
    キャッシュ作成用で、Cache型で返すので別クラスで作った
    """
    def __init__(self):
        super().__init__()

    def get_datum_obj(self):
        from kskp.store import CACHE_FOLDER_UUID
        return Cache(CACHE_FOLDER_UUID, 'cache', None)

class RunsSaver(Command):
    """
    nm.runsを行うSaverコマンド
    ※未完成
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('*', 'nm')]
        self.o_ports = [Port('?', '?')]

    def run(self, args, inputs):
        result = {}
        import nysol.mcmd as nm
        nm_list = []
        for nysol_module in inputs.values():
            nm_list.append(nysol_module)

        nm.runs(nm_list, msg='on')
        return {'o': result}

class Frame2DBSaver(Command):
    """
    frameをdbへの保存を行うsaver
    ※未完成
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'result')]
        self.o_ports = [Port('o', 'result')]

    def run(self, args, inputs):
        result = {}
        from kskp.store import Library

        for value in inputs['i'].values():
            save_datum_args = args.get(value)
            frame = Library.save_frame(save_datum_args.get('folder_uuid'),
                                       save_datum_args.get('label'),
                                       save_datum_args.get('frame_path'))

            if save_datum_args.get('type') == 'cache':
                # キャッシュ保存処理
                pass

        return {'o': result}

# 1つ保存のsaverはどうなる？
# 普通なら、inputsできたものをargs情報を使って保存か
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
