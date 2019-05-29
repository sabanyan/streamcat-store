from kskp.store.commands import *

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
        TODO: 下記の対応表をなくす様に実装する
        """
        from kskp.engine.tests.test_main import Square

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
            # ビジュアライズ
            'csvtohtmltable': CsvToTableCommand(),
            # Storeコマンド
            'saver': SaverCommand(),
            'cachesaver': CacheSaverCommand(),
            'loader': LoaderCommand()
        }

        if runnable_id not in table:
            raise Exception(f"存在しないcommandId'{runnable_id}'が指定されています")

        return table[runnable_id]
