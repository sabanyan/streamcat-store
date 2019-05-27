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
            'square': Square(),
            'mcut': McutCommand(),
            'mselstr': MselstrCommand(),
            "mjoin": MjoinCommand(),
            "store": SaverCommand(),
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
            "column_list": ColumnlistCommand(),
            "mdformat": MdformatCommand(),
            "mshare": MshareCommand(),
            "mchgnum": MchgnumCommand(),
            "groupby": GroupbyCommand(),
            "mfldname": MfldnameCommand(),
            "mcount": McountCommand(),
            "column_unique_name": ColumnUniqueNameCommand(),
            "column_name": ColumnNameCommand(),
            "sml_modeling": SmlModelingCommand()
        }

        if runnable_id not in table:
            raise Exception(f"存在しないcommandId'{runnable_id}'が指定されています")

        return table[runnable_id]
