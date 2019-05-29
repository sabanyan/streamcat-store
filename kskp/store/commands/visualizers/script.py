# ビジュアライズコマンド

from kskp.core import Command, Port

class VisualizersCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'table')]

    def run(self, args, inputs):
        # HTML作成
        visualize_html = self.template_data(args, inputs)
        return { 'o': visualize_html }

    def template_data(self, args, inputs):
        """ for override """
        raise Exception()

class VisualizersHtml(VisualizersCommand):
    """
    Bokehを使うコマンドと分けたかったのでとりあえず作成
    とりあえず感が半端ない。。。
    """
    def __init__(self):
        super().__init__()

class CsvToTableCommand(VisualizersHtml):
    def __init__(self):
        super().__init__()

    def template_data(self, args, inputs):
        """
        csvのファイルパスから、
        HTMLのテーブル形式にして返す
        """

        # inputsにはパスが来て欲しい
        file_path = inputs.get('i')
        offset = int(args.get('offset')) if args.get('offset') else 0
        limit = int(args.get('limit')) if args.get('limit') else None

        import os
        # ブロック句
        if not os.path.exists(file_path):
            return ''

        result = {}

        # テーブル構造
        with open(file_path, 'r') as f:
            n = 0

            result['reader'] = []
            for line in f:
                # 指定されたlimitの数だけ要素が達していたら終了
                if limit is not None and len(result['reader']) == limit:
                    break

                if n == 0:
                    # 一行目はヘッダとみなす
                    result['header'] = line.split(',')
                else:
                    if offset < n:
                        result['reader'].append(line.split(','))

                n += 1

        return result
