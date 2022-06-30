import os
import pickle
from typing import Iterable, List, Tuple

import apache_beam as beam
from apache_beam.io.filesystems import FileSystems
from apache_beam.transforms import PTransform
from apache_beam.transforms.core import _ReiterableChain

from streamcat.core import Command, Port
from streamcat.store import BeamModule
from streamcat.store import NysolModule
from .script import SCommand, LoaderCommand

class BeamNoop(Command):
    """
    何もしない
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'beam')]
        self.o_ports = [Port('o', 'beam')]

    def run(self, args, inputs):

        def noop(row:List[str]) -> Iterable[List[str]]:
            yield row

        # 入力PortからPTransformを取得する
        ptransform:PTransform = inputs['i'].content

        # PTransformを繋げる
        ptransform |= (
            'No Operation' >> beam.ParDo(noop)
        )

        # BeamModuleを返す
        return {'o': BeamModule(ptransform)}


class BeamNumber(Command):
    """
    連番を付与する
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'beam')]
        self.o_ports = [Port('o', 'beam')]

    def run(self, args, inputs):

        count = 0
        def noop(row:List[str]) -> Iterable[List[str]]:
            # nonlocal : 関数の外で定義した変数を参照する
            nonlocal count
            count += 1
            row.insert(0, str(count))
            yield row

        # 入力PortからPTransformを取得する
        ptransform:PTransform = inputs['i'].content

        # PTransformを繋げる
        ptransform |= (
            'Number' >> beam.ParDo(noop)
        )

        # BeamModuleを返す
        return {'o': BeamModule(ptransform)}


class BeamTee(Command):
    """
    入力を二分岐して出力する
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'beam')]
        self.o_ports = [Port('o', 'beam'), Port('u', 'beam')]

    def run(self, args, inputs):

        def noop(row:List[str]) -> Iterable[List[str]]:
            yield row

        # 入力PortからPTransformを取得する
        ptransform:PTransform = inputs['i'].content

        # PTransformを繋げる
        ptransform_o = ptransform | (
            'Tee(o)' >> beam.ParDo(noop)
        )
        ptransform_u = ptransform | (
            'Tee{u)' >> beam.ParDo(noop)
        )

        # BeamModuleを返す
        return {'o': BeamModule(ptransform_o), 'u': BeamModule(ptransform_u)}


class BeamLoaderCommand(LoaderCommand):
    """
    ローカルファイルからデータを取得する
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('folder', 'store')]
        self.o_ports = [Port('o', 'beam')]
        self.name = 'beam_loader'

    def run(self, args, inputs):
        import csv
        import codecs

        def read_csv_lines(file_path:str, encoding:str) -> Iterable[List[str]]:
            with FileSystems.open(file_path) as f:
                # Beam reads files as bytes, but csv expects strings,
                # so we need to decode the bytes into utf-8 strings.
                for row in csv.reader(codecs.iterdecode(f, encoding)):
                    yield row

        # ファイルパスと文字コードを取得する
        path, encoding = self._get_frame(args)
        # CSVファイルを読み込むPTransformを作成する
        ptransform = (
            f'Create file path' >> beam.Create([path.as_posix()])
          | f'Load {path.name}' >> beam.FlatMap(read_csv_lines, encoding=encoding)
        )

        # BeamModuleを返す
        return {'o': BeamModule(ptransform)}


class BeamToListCommand(SCommand):
    """
    入力データを名前付きPIPEに出力する
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'beam')]
        self.o_ports = [Port('o', 'beam')]

    def run(self, args, inputs):
        """
        PTransformの結果を名前付きPIPEに出力する
        """
        from streamcat.core import Tmp

        # CombineGloballyへは任意の数の入力要素をitrに纏めて渡される
        # そのため、このreduce関数は複数回呼び出される
        def reduce(itr:_ReiterableChain) -> Tuple[List]:
            rets  = ()
            is_first = True

            # 以下のように初回呼出時とそれ以降の呼出時で、itrの最初の要素は変わる
            # (rets)には前回呼出時の戻値が格納される
            # itr (初回呼出) : [intpu1, input2, ...]
            # itr (次回以降) : [(rets), input1, input2, ...]
            for list in itr:
                if is_first:
                    is_first = False
                    if isinstance(list, tuple):
                        # 次回以降の呼出の場合
                        rets = list
                    else:
                        # 初回呼出の場合
                        rets = tuple([list])
                else:
                    # *ret : tupleの要素を展開する
                    rets = (*rets, list)
            # 纏めた結果を返す
            return rets

        def write(tuple:Tuple[List]) -> None:
            # Tuple型をList型に変換する
            lists = [*tuple]
            # 入力データをシリアライズする
            pickled_lists = pickle.dumps(lists)
            # ファイル記述子からPIPEのStreamを作成する
            in_pipe = open(in_fd, mode='wb', buffering=0, closefd=False)
            # PIPEのStreamにデータを書き込む
            in_pipe.write(pickled_lists)

        # 入力PortからPTransformを取得する
        ptransform:PTransform = inputs['i'].content

        # 名前付きPIPEを/tmpディレクトリに作成する
        pipe_path = Tmp.create_file()
        os.mkfifo(pipe_path)

        # 名前付きPIPEを開き、ファイル記述子を取得する
        in_fd = os.open(pipe_path, flags=os.O_NONBLOCK|os.O_RDWR)
        out_fd= os.open(pipe_path, flags=os.O_NONBLOCK|os.O_RDONLY)

        # PIPEに書き込むデータはシリアライズする必要があるが、Pickleは対象データを一括でシリアライズする必要がある
        # そのため、CombineGloballyで全ての入力データを纏めてから、それをPickleでシリアライズする
        ptransform |= (
              'Combine all' >> beam.CombineGlobally(reduce)
            | 'Write to named pipe' >> beam.ParDo(write)
        )

        # BeamModuleを返す
        beam_module = BeamModule(ptransform)
        beam_module.context['fifo'] = (in_fd, out_fd)
        return {'o': beam_module}

    def run_with_error(self, args, inputs):
        """
        PTransformの結果をPIPEに出力する
        """
        import fcntl
        from multiprocessing import Pipe

        def write(lists:list) -> None:
            # 入力データをシリアライズする
            pickled_lists = pickle.dumps(lists)
            # ファイル記述子からPIPEのStreamを作成する
            in_pipe = open(send_conn.fileno(), mode='wb', buffering=0, closefd=False)
            # 
            # write_line()内でPIPEのファイル記述子を操作すると以下の例外が送出される
            # RuntimeError: OSError: [Errno 9] Bad file descriptor
            # 
            # PIPEのStreamにデータを書き込む
            in_pipe.write(pickled_lists)

        # 入力PortからPTransformを取得する
        ptransform:PTransform = inputs['i'].content

        # 名前なしPIPEを作成すし、ファイル記述子を取得する
        recv_conn, send_conn = Pipe(duplex=False)
        in_fd = send_conn.fileno()
        out_fd = recv_conn.fileno()

        # PIPEをNon-Blockingにして受信処理が待ち状態になるのを防ぐ
        # in_fd
        fl = fcntl.fcntl(in_fd, fcntl.F_GETFL)
        fl = fl | os.O_NONBLOCK 
        fcntl.fcntl(in_fd, fcntl.F_SETFL, fl)
        # out_fd
        fl = fcntl.fcntl(out_fd, fcntl.F_GETFL)
        fl = fl | os.O_NONBLOCK 
        fcntl.fcntl(out_fd, fcntl.F_SETFL, fl)

        # PIPEに出力するPTransformを繋げる
        # (pipelineの実行前に、beam.ParDo()に渡した関数がシリアライズ可能かチェックされる)
        ptransform = ptransform | 'Write to pipe' >> beam.ParDo(write)

        # BeamModuleを返す
        beam_module = BeamModule(ptransform)
        beam_module.context['fifo'] = (in_fd, out_fd)
        return {'o': beam_module}


class BeamRunCommand(SCommand):
    """
    Pipelineを実行する
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('*', 'beam')]
        self.o_ports = [Port('*', 'out')]

    def run(self, args, inputs):
        from streamcat.store import Matrix, ApparentOut, CommandException

        def do_run(module:BeamModule):
            if 'fifo' not in module.context:
                raise Exception(f'名前付きPIPEのファイル記述子がありません({module})')

            ptransform:PTransform = module.content
            (in_fd, out_fd) = module.context['fifo']

            # Pipelineを実行する
            pipeline = beam.Pipeline()
            pipeline | ptransform
            result = pipeline.run()

            # 実行が終了するまで待つ
            result.wait_until_finish()
            
            # PIPEから全てのデータを読み込む
            with open(out_fd, mode='rb', buffering=0, closefd=False) as f:
                byte_array = f.read()

            # PIPEを閉じる
            os.close(out_fd)
            os.close(in_fd)

            # Deserializeする
            return pickle.loads(byte_array)

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
            elif isinstance(input, (BeamModule, Matrix)):
                rets[i_port_name] = ApparentOut(None, input.context.get('frame'))
            else:
                raise Exception(f'BeamRunCommandにBeamModuleまたはCommandException以外のデータ型({input})が入力されました')

        if exception_exists:
            # ActivityCommandにSaverが生成したFrameと例外を渡す
            return rets

        # Apache Beamを実行する
        exs_list = []
        results = {}
        for i_port_name, input in inputs.items():
            try:
                results[i_port_name] = do_run(input)
            except Exception as e:
                exs_list.append(e)

        rets = {}
        for i_port_name, beam_module in inputs.items():
            # プレビューの場合はframe=Noneである
            frame = beam_module.context.get('frame')
            if len(exs_list) == 0:
                matrix = Matrix(results[i_port_name])
                rets[i_port_name] = ApparentOut(None, frame or matrix)
            else:
                rets[i_port_name] = ApparentOut(None, frame, exs=exs_list)

        return rets


class OutToNysol(SCommand):
    """
    ApparentOutからNysolModuleへ変換する
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('*', 'out')]
        self.o_ports = [Port('*', 'mcmd')]

    def run(self, args, inputs):
        import nysol.mcmd as nm
        from streamcat.store import ApparentOut, CommandException

        rets = {}

        for i_port_name, input in inputs.items():
            if not isinstance(input, ApparentOut):
                raise CommandException(f'OutToNysolCommandにApparentOut以外のデータ型({input})が入力されました')
                
            out:ApparentOut = input

            if out.has_exs:
                rets[i_port_name] = out.exs[0]
            elif out.has_list: 
                cmd = nm.m2tee(i=out.datum.content)
                rets[i_port_name] = NysolModule(cmd)
            elif out.has_frame:
                cmd = nm.m2tee(i=out.datum.path.as_posix())
                rets[i_port_name] = NysolModule(cmd)
            else:
                raise CommandException(f'OutToNysolに入力されたApparentOutにデータが格納されていません')

        return rets
