from streamz import Stream
from streamcat.core import Port
from streamcat.store import StreamzModule
from .script import SCommand, LoaderCommand

class StreamzLoaderCommand(LoaderCommand):
    """
    ローカルファイルからデータを取得する
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('folder', 'store')]
        self.o_ports = [Port('o', 'streamz')]
        self.name = 'streamz_loader'

    def run(self, args, inputs):
        import csv

        # CSVをジェネレータで順次読み込む
        def csv_stream(file_path, encoding):
            with open(file_path, newline='', encoding=encoding) as f:
                # CSVファイルを1行ずつリスト形式で読み込む
                reader = csv.reader(f)
                for row in reader:
                    yield row

        # ファイルパスと文字コードを取得する
        path, encoding = self._get_frame(args)

        # CSVファイルを読み込むStreamを作成する
        stream = Stream().from_iterable(csv_stream(path, encoding))

        # StreamzModuleを返す
        return {'o': StreamzModule(stream)}

class SteramzToListCommand(SCommand):
    """
    入力データをPython Listに出力する
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'streamz')]
        self.o_ports = [Port('o', 'streamz')]

    def run(self, args, inputs):
        def add(x):
            ret.append(x)
        # Streamzの出力結果を格納するList
        ret = []
        # 入力PortからStreamを取得する
        stream = inputs['i'].content
        # Streamの結果をListに格納する
        stream.sink(add)
        # StreamzModuleを返す
        streamz_module = StreamzModule(stream)
        streamz_module.context['list'] = ret
        return {'o': streamz_module}

class StreamzRunCommand(SCommand):
    """
    Pipelineを実行する
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('*', 'streamz')]
        self.o_ports = [Port('*', 'out')]

    def run(self, args, inputs):
        from streamcat.store import Matrix, ApparentOut, CommandException

        def do_run(module:StreamzModule):
            import asyncio
            
            # Streamの処理が完了するまで待つ
            async def wait():
                while not stream.stopped:
                    await asyncio.sleep(0.05)

            stream:Stream = module.content
            list = module.context['list']

            # start()を実行するとStreamが実行される
            stream.start()

            # Streamの処理が完了するまで待つ
            asyncio.run(wait())

            # 実行結果を返す
            return list

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
            elif isinstance(input, (StreamzModule, Matrix)):
                rets[i_port_name] = ApparentOut(None, input.context.get('frame'))
            else:
                raise Exception(f'StreamzRunCommandにStreamzModuleまたはCommandException以外のデータ型({input})が入力されました')

        if exception_exists:
            # ActivityCommandにSaverが生成したFrameと例外を渡す
            return rets

        # Streamzを実行する
        exs_list = []
        out_list = do_run(inputs['0'])

        # resultsの要素はnm_listへのappend順に対応している?ため
        # 入力ポートと出力ポートは同じキーで対応付ける
        i = 0
        rets = {}
        for i_port_name, nysol_module in inputs.items():
            # プレビューの場合はframe=Noneである
            frame = nysol_module.context.get('frame')
            if len(exs_list) == 0:
                matrix = Matrix(out_list)
                rets[i_port_name] = ApparentOut(None, frame or matrix)
            else:
                rets[i_port_name] = ApparentOut(None, frame, exs=exs_list)
            i += 1

        return rets
