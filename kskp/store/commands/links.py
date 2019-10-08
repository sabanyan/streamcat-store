import json
import os
from . import *
from pathlib import Path
from kskp.core import Command

class CommandLink:
    """
    コマンド名を解決するリンク
    """

    def __init__(self, command_id):
        self.command_id = command_id

    def resolve(self):
        return self.select_runnable(self.command_id)

    def select_runnable(self, runnable_id):
        """
        idとなる文字列を受け取ってrunnableのインスタンスを返却する
        """
        from kskp.engine.tests.test_main import Square

        # runfunc用の関数のimport
        from kskp.store.commands.pcmd.src import (
            hex2bin
        )

        table = {
            # テスト用コマンド
            'square': Square(),
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
            "merge_FS": Merge_FSCommand(),
            "merge_ibutsu": Merge_ibutsuCommand(),
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
            "mtee": MteeCommand(),
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
            'utf8_to_cp932': Utf8ToCp932Command(),
            'sml_modeling': SmlModelingCommand(),
            'selrow': SelRowCommand(),
            'tmc_phase2_loader': TmcPhase2Loader(),
            # ビジュアライズ
            'csvtohtmltable': CsvToTableCommand(),
            'csvtolinegraph': CsvToLineGraphCommand(),
            'csvtohistogram': CsvToHistogramCommand(),
            'csvtoscatter': CsvToScatterCommand(),
            'csvtoboxplot': CsvToBoxplotCommand(),
            # Storeコマンド
            'saver': SaverCommand(),
            'cachesaver': CacheSaverCommand(),
            'loader': LoaderCommand()
        }

        if runnable_id not in table:
            raise Exception(f"存在しないcommandId'{runnable_id}'が指定されています")

        return table[runnable_id]

class Source:
    pass

class PathFileSource(Source):
    def __init__(self, path):
        self.path = path

    def data(self):
        from pathlib import Path
        return [PathLink(p) for p in Path(self.path).iterdir()]

class PathLink(Command):
    def __init__(self, source: PathFileSource):
        super().__init__()
        self.context.update({'source': source})

    def __repr__(self):
        return f"PathLink({repr(self.context['source'].path.as_posix())})"

class CommandsPathLink(PathLink):
    def __init__(self, source):
        super().__init__(source)

    def run(self, args=None, inputs=None):
        """
        コマンド定義のJSONを読んで一覧を返す
        """
        if self.context['source'].path is None:
            return

        commands = []
        for command_path in self.context['source'].path.iterdir():
            if not command_path.suffix == '.json':
                continue
            command_json = command_path.read_text(encoding='utf-8')
            command_data = json.loads(command_json)
            commands.append(command_data)

        return commands

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

    def __init__(self, visible_command):
        path = Path(__file__).resolve()
        commands_path = path.parent / visible_command / 'json'
        if commands_path.exists():
            super().__init__(commands_path)
