# MYSOLコマンド

from typing import Callable
from asteval import Interpreter
from mysol import core, csv
from streamcat.core import Command, Port
from streamcat.store import MysolModule, CommandException
from ..scmd.script import LoaderCommand

class NCommand(Command):
    """
    MYSOLコマンド
    (0入力1出力)
    """
    def __init__(self):
        super().__init__()
        self.i_ports = []
        self.o_ports = [Port('o', 'mysol')]

    def run(self, args:dict, inputs:dict) -> dict:
        cmd = self.mysol_cmd(**self.eval_args(args))
        return {'o': MysolModule(cmd)}

    def eval_args(self, args:dict) -> dict:
        """
        iifとcolsに指定された式を安全に評価する
        """
        # minimal=True：不必要なPython文法を無効化する
        # with_lambda=True：lambda式を有効化する
        # user_symbols={'v': core.v}：mysolのクラスvを使用可能にする
        aeval = Interpreter(minimal=True, with_lambda=True, user_symbols={'v': csv.v})

        evaled_args = args.copy()
        for key, arg in evaled_args.items():
            # 'if'や'cols'の引数は、文字列として渡されるため、評価して関数オブジェクトに変換する
            if key in ['iif', 'cols']:
                evaled_args[key] = aeval('lambda i: ' + arg)

        # エラーが発生した場合は表示する
        if len(aeval.error) > 0:
            for err in aeval.error:
                raise CommandException(f'引数の評価中にエラーが発生しました: {err.get_error()}')

        return evaled_args

    @property
    def mysol_cmd(self) -> Callable:
        pass

class NCommandI(NCommand):
    """
    MYSOLコマンド
    (1入力1出力)
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', ['mysol','matrix'])]
        self.o_ports = [Port('o', 'mysol')]

    def run(self, args:dict, inputs:dict) -> dict:
        input_cmd = inputs['i'].content
        cmd = input_cmd >> self.mysol_cmd(**self.eval_args(args))
        return {'o': MysolModule(cmd)}

class NewCommand(NCommand):
    @property
    def mysol_cmd(self) -> Callable:
        return csv.new

class LoadCommand(LoaderCommand):
    """
    ローカルファイルからCSVを取得する
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('folder', 'store')]
        self.o_ports = [Port('o', 'mysol')]
        self.name = 'load'

    def run(self, args:dict, inputs:dict) -> dict:
        # ファイルパスと文字コードを取得する
        path, encoding = self._get_frame(args)
        # CSVファイルを読み込むStreamを作成する
        cmd = csv.load(path)
        # StreamzModuleを返す
        return {'o': MysolModule(cmd)}

class TeeCommand(NCommand):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', ['mysol','matrix'])]
        self.o_ports = [Port('o', 'mysol'), Port('u', 'mysol')]

    def run(self, args:dict, inputs:dict) -> dict:
        input_cmd = inputs['i'].content
        cmd = input_cmd >> core.tee()
        return {'o': MysolModule(cmd), 'u': MysolModule(cmd.u)}

class SelectCommand(NCommandI):
    @property
    def mysol_cmd(self) -> Callable:
        return csv.select

class FilterCommand(NCommandI):
    @property
    def mysol_cmd(self) -> Callable:
        return csv.filter
    def run(self, args:dict, inputs:dict) -> dict:
        # ifで渡された引数をiifに変換する
        if 'if' in args:
            args['iif'] = args.pop('if')
        return super().run(args, inputs)

class ColumnsCommand(NCommandI):
    @property
    def mysol_cmd(self) -> Callable:
        return csv.columns

class TransposeCommand(NCommandI):
    @property
    def mysol_cmd(self) -> Callable:
        return csv.transpose

class OutlCommand(NCommandI):
    def run(self, args:dict, inputs:dict) -> dict:
        input_cmd = inputs['i'].content
        outl_cmd = self.mysol_cmd()
        cmd = input_cmd >> outl_cmd
        # Outlの結果をStreamzModuleに格納する
        mysol_module = MysolModule(cmd)
        mysol_module.context['list'] = outl_cmd.to_list
        return {'o': mysol_module}

    @property
    def mysol_cmd(self) -> Callable:
        return core.outl

class MysolRunsCommand(NCommandI):
    """
    MYSOLを実行する
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('*', 'mysol')]
        self.o_ports = [Port('*', 'out')]

    def run(self, args, inputs):
        from streamcat.store import Matrix, ApparentOut, CommandException

        def do_run(module:MysolModule):
            # run()を実行するとMYSOLが実行される
            cmd:core.Cmd = module.content
            cmd.run()
            # 実行結果を返す
            return module.context['list']

        # 
        # CommandExceptionが1つでも入力された場合は処理を中断する
        # (例外が入力されたら対応する出力ポートに渡す)
        # 
        rets = {}
        exception_exists = False
        for i_port_name, input in inputs.items():
            if isinstance(input, CommandException):
                rets[i_port_name] = ApparentOut(None, None, [input])
                exception_exists = True
            elif isinstance(input, (MysolModule, Matrix)):
                rets[i_port_name] = ApparentOut(None, input.context.get('frame'))
            else:
                raise Exception(f'MysolRunsCommandにMysolModuleまたはCommandException以外のデータ型({input})が入力されました')

        if exception_exists:
            # ActivityCommandにSaverが生成したFrameと例外を渡す
            return rets

        # MYSOLを実行する
        exs_list = []
        out_list = do_run(inputs['0'])

        # resultsの要素はnm_listへのappend順に対応している?ため
        # 入力ポートと出力ポートは同じキーで対応付ける
        i = 0
        rets = {}
        for i_port_name, mysol_module in inputs.items():
            # プレビューの場合はframe=Noneである
            frame = mysol_module.context.get('frame')
            if len(exs_list) == 0:
                matrix = Matrix(out_list)
                rets[i_port_name] = ApparentOut(None, frame or matrix)
            else:
                rets[i_port_name] = ApparentOut(None, frame, exs=exs_list)
            i += 1

        return rets
