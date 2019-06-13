# Store用コマンド
import os
import nysol.mcmd as nm

from kskps.library import NysolModule, Cache, Frame
from kskps.core import Command, Port



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
        result = datum_module.run(msg='on')

        return {'o': self.wrap_datum(result, args)}

    def module(self, args, input):
        if os.environ['FRAME_CHARACTER_CODE'] == 'shift-jis':
            from kskps.store import CommandLink
            sjis_command = CommandLink('utf8_to_cp932').resolve()
            # sオプションをつけると標準出力にも流す、このsaverは最後のFrameを出力するものなので、オプションはつけない
            return sjis_command.run({'o': args['frame_path']}, {'i': input})['o'].content
        else:
            command_args = {}
            command_args['i'] = input
            command_args['o'] = args['frame_path'].as_posix()
            return nm.m2tee(command_args)

    def get_datum_obj(self):
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

    def run(self, args, inputs):
        # 1. storeにsaveする(runはしない)
        datum_module = inputs['store'].save(self, args, inputs['i'])
        return {'o': self.wrap_datum(datum_module, args)}

    def module(self, args, input):
        if os.environ['FRAME_CHARACTER_CODE'] == 'shift-jis':
            from kskps.store import CommandLink
            sjis_command = CommandLink('utf8_to_cp932').resolve()
            # sオプションをつけると標準出力にも流す
            # FIXIT: sオプションをつけるためにcommand_argsをオーバーライドしているのダサい。。。
            return sjis_command.run({'o': args['frame_path'], 's': True}, {'i': input})['o'].content
        else:
            command_args = {}
            command_args['i'] = input
            command_args['o'] = args['frame_path'].as_posix()
            return nm.m2tee(command_args)

    def get_datum_obj(self):
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
