# 独自コマンド

import nysol.mcmd as nm
from pathlib import Path

from kskp.library import NysolModule
from kskp.core import Command, Port

PCMD_DIR = Path(__file__).resolve().parent

class PCommand(Command):
    """
    独自コマンドのスーパークラス
    TODO: そういえばいつから独自コマンドはpcmdに。。。？
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]

    def command_args(self, args):
        """
        nm.cmdで実行可能なargsに変換（文字列にして並べる）
        """
        args_string = ''
        for key, value in args.items():
            if isinstance(value, bool):
                if value == True:
                    args_string +=  ' -' + key
            else:
                args_string += ' %s=%s' % (key, value)

        return args_string

    def module(self, flow_obj, args):
        """
        moduleでラップする
        """
        import nysol.mcmd as nm
        flow_obj <<= nm.cmd(args)

        nysol_module = NysolModule()
        nysol_module.set_content(flow_obj)

        return nysol_module

    def run(self, args, inputs):
        """
        実際実行(for override)
        """
        pass


class SmlModelingCommand(PCommand):
    """
    独自コマンドのsml_modelingコマンド
    """
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/sml_modeling.sh').as_posix()
        args_string += ' kcmd_path=' + (PCMD_DIR.parent / 'kcmd/src').as_posix()
        args_string += ' temp_path=' + (PCMD_DIR / 'tmp').as_posix()
        args_string += ' model_data_path=' + (PCMD_DIR / 'model').as_posix()
        args_string += self.command_args(args)

        return {'o': self.module(f, args_string)}

class ColumnlistCommand(PCommand):
    """
    独自コマンドのColumnlistコマンド
    """
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/column_list.sh').as_posix()
        args_string += self.command_args(args)

        return {'o': self.module(f, args_string)}

class GroupbyCommand(PCommand):
    """
    独自コマンドのGroupbyコマンド
    """
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/groupby.sh').as_posix()
        args_string += self.command_args(args)

        return {'o': self.module(f, args_string)}

class ColumnUniqueNameCommand(PCommand):
    """
    独自コマンドのcolumn_unique_nameコマンド
    """
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/column_unique_name.sh').as_posix()
        args_string += self.command_args(args)

        return {'o': self.module(f, args_string)}

class ColumnNameCommand(PCommand):
    """
    独自コマンドのcolumn_nameコマンド
    """
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/column_name.sh').as_posix()
        args_string += self.command_args(args)

        return {'o': self.module(f, args_string)}
