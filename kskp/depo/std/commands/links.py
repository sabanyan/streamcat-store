import json
from typing import List
from pathlib import Path
from kskp.core import Command

from .mcmd.script import *
from .kcmd.script import *
from .pcmd.script import *
from .scmd.script import *
from .vcmd.script import *

class CommandLink:
    """
    コマンド名を解決するリンク
    """
    from .pcmd.square_command import Square
    from .pcmd.groupby2_command import GroupBy2Command
    from .pcmd.iot_command import (
        MissingValueInterpolateCommand,
        MeasurementPeriodIdentifyCommand,
        TimeSeriesDataJoinCommand,
        TimeAxisDataGenerateIn1Command,
        TimeAxisDataGenerateIn0Command
    )

    COMMAND_TABLE = {
        # テスト用コマンド
        'square': Square(),
        'raise' : RaiseCommand(),
        # mコマンド
        'mcut': McutCommand(),
        'mselstr': MselstrCommand(),
        "mjoin": MjoinCommand(),
        "mtee": MteeCommand(),
        "mcat": McatCommand(),
        "msetstr": MsetstrCommand(),
        "msummary": MsummaryCommand(),
        "msortf": MsortfCommand(),
        "msel": MselCommand(),
        "mnumber": MnumberCommand(),
        "mcross": McrossCommand(),
        "m2cross": M2crossCommand(),
        "mcal": McalCommand(),
        "mchkcsv": MchkcsvCommand(),
        "mdformat": MdformatCommand(),
        "mshare": MshareCommand(),
        "mchgnum": MchgnumCommand(),
        "mfldname": MfldnameCommand(),
        "mcount": McountCommand(),
        "maccum": MaccumCommand(),
        "marff2csv": Marff2csvCommand(),
        "mavg": MavgCommand(),
        "mbest": MbestCommand(),
        "mbucket": MbucketCommand(),
        "mchgstr": MchgstrCommand(),
        "mcombi": McombiCommand(),
        "mcommon": McommonCommand(),
        "mcsv2arff": Mcsv2arffCommand(),
        "mdelnull": MdelnullCommand(),
        "mduprec": MduprecCommand(),
        "mfsort": MfsortCommand(),
        "mhashavg": MhashavgCommand(),
        "mhashsum": MhashsumCommand(),
        "mkeybreak": MkeybreakCommand(),
        "mmbucket": MmbucketCommand(),
        "mmvavg": MmvavgCommand(),
        "mmvsim": MmvsimCommand(),
        "mmvstats": MmvstatsCommand(),
        "mnewnumber": MnewnumberCommand(),
        "mnewrand": MnewrandCommand(),
        "mnewstr": MnewstrCommand(),
        "mnjoin": MnjoinCommand(),
        "mnormalize": MnormalizeCommand(),
        "mnrcommon": MnrcommonCommand(),
        "mnrjoin": MnrjoinCommand(),
        "mnullto": MnulltoCommand(),
        "mpadding": MpaddingCommand(),
        "mpaste": MpasteCommand(),
        "mproduct": MproductCommand(),
        "mrand": MrandCommand(),
        "mrjoin": MrjoinCommand(),
        "msed": MsedCommand(),
        "mselnum": MselnumCommand(),
        "mselrand": MselrandCommand(),
        "msep": MsepCommand(),
        "msep2": Msep2Command(),
        "mshuffle": MshuffleCommand(),
        "msim": MsimCommand(),
        "mslide": MslideCommand(),
        "msplit": MsplitCommand(),
        "mstats": MstatsCommand(),
        "msum": MsumCommand(),
        "mtab2csv": Mtab2csvCommand(),
        "mtonull": MtonullCommand(),
        "mtra": MtraCommand(),
        "mtrafld": MtrafldCommand(),
        "mtraflg": MtraflgCommand(),
        "muniq": MuniqCommand(),
        "mvcat": MvcatCommand(),
        "mvcommon": MvcommonCommand(),
        "mvcount": MvcountCommand(),
        "mvdelim": MvdelimCommand(),
        "mvdelnull": MvdelnullCommand(),
        "mvjoin": MvjoinCommand(),
        "mvnullto": MvnulltoCommand(),
        "mvreplace": MvreplaceCommand(),
        "mvsort": MvsortCommand(),
        "mvuniq": MvuniqCommand(),
        "mwindow": MwindowCommand(),
        "mxml2csv": Mxml2csvCommand(),
        # 独自コマンド
        'check_duplicate_rows': CheckDuplicateRowsCommand(),
        'merge_FS': MergeFSCommand(),
        'merge_ibutsu': MergeIbutsuCommand(),
        'column_grouping_name': ColumnGroupingNameCommand(),
        'column_unique_name': ColumnUniqueNameCommand(),
        'column_name': ColumnNameCommand(),
        'column_blank_name': ColumnBlankNameCommand(),
        'column_list': ColumnListCommand(),
        'windows_cp932_csv_read': WinCp932ReadCommand(),
        'columns_to_rows': ColumnsToRowsCommand(),
        'groupby_columns': GroupbyColumnsCommand(),
        'groupby': GroupbyCommand(),
        'groupby2': GroupBy2Command(),
        'utf8_to_cp932': Utf8ToCp932Command(),
        'sml_modeling': SmlModelingCommand(),
        'multi_mcal_manyformula': MultiMcalCommand(),
        'multi_mcal_oneformula': MultiMcalWCCommand(),
        'multi_mvavg': MvAvgCommand(),
        'multi_mvstats': MvStatsCommand(),
        'multi_mvsim': MvSimCommand(),
        'plaintext2csv': PlainText2Csv(),
        'rowrange': RowRangeCommand(),
        'rowrandom': RowRandomCommand(),
        'convtoutf8' : ConvEncoding(),
        'convtocp932' : ConvEncoding(),
        'align' : AlignColumns(),
        'to_list' : ToListCommand(),
        'to_tlist' : ToTListCommand(),
        'to_pipe' : ToNamedPipeCommand(),
        # IoT コマンド
        'ts_polation' : MissingValueInterpolateCommand(),
        'ts_mpid' : MeasurementPeriodIdentifyCommand(),
        'ts_join' : TimeSeriesDataJoinCommand(),
        'ts_axis_1in_generator' : TimeAxisDataGenerateIn1Command(),
        'ts_axis_0in_generator' : TimeAxisDataGenerateIn0Command(),
        # ビジュアライズ
        'csvtohtmltable': CsvToTableCommand(),
        'csvtolinegraph': CsvToLineGraphCommand(),
        'csvtohistogram': CsvToHistogramCommand(),
        'csvtoscatter': CsvToScatterCommand(),
        'csvtoboxplot': CsvToBoxplotCommand(),
        'csvtorepetitiviewaveform': CsvToRepetitivieWaveCommand(),
        'csvtotimecompressionform': CsvToTimeCompressionCommand(),
        # Storeコマンド
        'saver': SaverCommand(),
        'cachesaver': CacheSaverCommand(),
        'loader': LoaderCommand(),
        'db_loader' : DbLoaderCommand(),
        'db_saver'  : DbSaverCommand(),
        'remotefolder_loader' : RemoteFolderLoaderCommand(),
        'remotefolder_saver'  : RemoteFolderSaverCommand(),
        'activity' : ActivityCommand(),
        'assert' : AssertCommand(),
        'runs' : RunsCommand()
    }

    def __init__(self, command_id:str):
        self.command_id = command_id

    def resolve(self):
        return self.select_runnable(self.command_id)

    def select_runnable(self, runnable_id) -> Command:
        """
        idとなる文字列を受け取ってrunnableのインスタンスを返却する
        """
        if runnable_id not in self.COMMAND_TABLE:
            raise Exception(f"存在しないcommandId'{runnable_id}'が指定されています")
        return self.COMMAND_TABLE[runnable_id]

class Source:
    pass

class PathFileSource(Source):
    def __init__(self, path:Path):
        self.path = path

    def data(self):
        return [PathLink(p) for p in Path(self.path).iterdir()]

class PathLink(Command):
    def __init__(self, source:PathFileSource):
        super().__init__()
        self.context.update({'source': source})

    def __repr__(self):
        return f"PathLink({repr(self.context['source'].path.as_posix())})"

class CommandsPathLink(PathLink):

    # {path_str : command_data}
    COMMAND_JSONS = {}

    @staticmethod
    def _read_command_jsons(path:Path):
        # COMMAND_JSONSのハッシュキー
        path_str = path.as_posix()
        CommandsPathLink.COMMAND_JSONS[path_str] = []

        for command_path in path.iterdir():
            command_data = CommandsPathLink._read_command_json(command_path)
            if command_data:
                # 読み込んだコマンドJSONはメモリ(dict)に保持する
                CommandsPathLink.COMMAND_JSONS[path_str].append(command_data)

        return CommandsPathLink.COMMAND_JSONS[path_str]

    @staticmethod
    def _read_command_json(command_path:Path):
        if not command_path.suffix == '.json':
            return None
        try:
            command_json = command_path.read_text(encoding='utf-8')
            return json.loads(command_json)
        except Exception as e:
            raise Exception(f'コマンドJSON({command_path})の読み込みに失敗しました ({e})')

    def __init__(self, source:PathFileSource):
        super().__init__(source)

    def run(self, args=None, inputs=None) -> List[dict]:
        """
        コマンド定義のJSONを読んで一覧を返す
        """
        if self.context['source'].path is None:
            return

        path = self.context['source'].path
        path_str = path.as_posix()
        if path_str in CommandsPathLink.COMMAND_JSONS:
            # メモリ(dict)にコマンドJSONがある場合はメモリから読み込む
            return CommandsPathLink.COMMAND_JSONS[path_str]
        else:
            return CommandsPathLink._read_command_jsons(path)

    def resolve(self, args=None, inputs=None):
        """
        runメソッドのエイリアス
        意味的にlink.resolveの方がわかりやすいかと
        """
        return self.run(args, inputs)

class CommandsPathFileSource(PathFileSource):
    """
    コマンドJSONの一覧が入ったパスを持つsource
    """

    def __init__(self, visible_command:str):
        path = Path(__file__).resolve()
        commands_path = path.parent / visible_command / 'json'
        if commands_path.exists():
            super().__init__(commands_path)
