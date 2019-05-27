# 独自コマンド

import nysol.mcmd as nm
from pathlib import Path

from kskp.library import NysolModule
from kskp.core import Command, Port

PCMD_DIR = Path(__file__).resolve().parent

# ※ sml_modelingコマンドはKコマンドを使う関係上、importで場所を指定している
#   今はテストで動かしている部分があるため、ローカルで動く様なパス設定をしてある
class SmlModelingCommand(Command):
    """
    独自コマンドのsml_modelingコマンド
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        import nysol.mcmd as nm
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/sml_modeling.sh').as_posix()
        args_string += ' kcmd_path=' + (PCMD_DIR.parent / 'kcmd/src').as_posix()
        args_string += ' temp_path=' + (PCMD_DIR / 'tmp').as_posix()
        args_string += ' model_data_path=' + (PCMD_DIR / 'model').as_posix()

        for key,value in args.items():
            if isinstance(value, bool):
                if value == True:
                    args_string +=  ' -' + key
            else:
                args_string += ' %s=%s' % (key, value)

        f <<= nm.cmd(args_string)
        nysol_module = NysolModule()
        nysol_module.set_content(f)
        return {'o': nysol_module}

class ColumnlistCommand(Command):
    """
    独自コマンドのColumnlistコマンド
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        import nysol.mcmd as nm
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/column_list.sh').as_posix()

        for key,value in args.items():
            if isinstance(value, bool):
                if value == True:
                    args_string +=  ' -' + key
            else:
                args_string += ' %s=%s' % (key, value)

        f <<= nm.cmd(args_string)
        nysol_module = NysolModule()
        nysol_module.set_content(f)
        return {'o': nysol_module}

class GroupbyCommand(Command):
    """
    独自コマンドのGroupbyコマンド
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        import nysol.mcmd as nm
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/groupby.sh').as_posix()

        for key,value in args.items():
            if isinstance(value, bool):
                if value == True:
                    args_string +=  ' -' + key
            else:
                args_string += ' %s=%s' % (key, value)

        f <<= nm.cmd(args_string)
        nysol_module = NysolModule()
        nysol_module.set_content(f)
        return {'o': nysol_module}

class ColumnUniqueNameCommand(Command):
    """
    独自コマンドのcolumn_unique_nameコマンド
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        import nysol.mcmd as nm
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/column_unique_name.sh').as_posix()

        for key,value in args.items():
            if isinstance(value, bool):
                if value == True:
                    args_string +=  ' -' + key
            else:
                args_string += ' %s=%s' % (key, value)

        f <<= nm.cmd(args_string)
        nysol_module = NysolModule()
        nysol_module.set_content(f)
        return {'o': nysol_module}

class ColumnNameCommand(Command):
    """
    独自コマンドのcolumn_nameコマンド
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        import nysol.mcmd as nm
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/column_name.sh').as_posix()

        for key,value in args.items():
            if isinstance(value, bool):
                if value == True:
                    args_string +=  ' -' + key
            else:
                args_string += ' %s=%s' % (key, value)

        f <<= nm.cmd(args_string)
        nysol_module = NysolModule()
        nysol_module.set_content(f)
        return {'o': nysol_module}
