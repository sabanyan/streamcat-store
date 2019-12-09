import unittest
import nysol.mcmd as nm
import uuid
import pprint
import pandas as pd

pp = pprint.PrettyPrinter(depth=6)

from pathlib import Path
from kskp.store import Library, CommandLink
from kskp.store import NysolModule
from bokeh.plotting import figure
from bokeh.palettes import Dark2_5 as palette
from bokeh.models import HoverTool, Select, Legend, ColumnDataSource
from bokeh.layouts import gridplot
from bokeh.plotting import figure, output_file, show
import itertools

@unittest.skip('test_vcmdに移行する')
class ExecuteViualizeTestCase(unittest.TestCase):
    """
    visualize用コマンドの実行テスト
    """
    RESULT_DIR = 'kskp/store/frames/csv/フロー実行結果/'
    CACHE_DIR = 'kskp/store/frames/csv/フロー実行キャッシュ/'
    TESTDATA_DIR = 'kskp/store/frames'

    def setUp(self):
        pass

    # @unittest.skip
    def test_execute_table(self):
        """
        表形式でデータを出力するテスト
        """
        table_command = CommandLink('csvtohtmltable').resolve()
        # テストデータ作成
        data = [
            ['顧客', '数量', '金額'],
            ['A', 1, 10],
            ['A', 2, 20],
            ['B', 1, 30],
            ['B', 3, 40],
            ['B', 1, 50]
        ]
        frame_path = Path(self.TESTDATA_DIR) / 'test_data.csv'
        frame_uuid = create_data(frame_path, data)

        args = {}

        inputs = {
            'i': frame_uuid
        }

        result = table_command.run(args, inputs)

        correct = {
            'header':['顧客', '数量', '金額\n'],
            'reader':[['A', '1', '10\n'], ['A', '2', '20\n'],
                      ['B', '1', '30\n'], ['B', '3', '40\n'], ['B', '1', '50\n']]
        }

        self.assertIsNotNone(result['o'])
        self.assertEqual(result['o']['header'], correct['header'])
        self.assertEqual(result['o']['reader'], correct['reader'])

        # 後片付け
        Library.delete_frame(frame_uuid)

    # @unittest.skip
    def test_execute_table_use_limit(self):
        """
        表形式でデータを出力するテスト
        limit使用
        """
        table_command = CommandLink('csvtohtmltable').resolve()
        # テストデータ作成
        data = [
            ['顧客', '数量', '金額'],
            ['A', 1, 10],
            ['A', 2, 20],
            ['B', 1, 30],
            ['B', 3, 40],
            ['B', 1, 50]
        ]
        frame_path = Path(self.TESTDATA_DIR) / 'test_data.csv'
        frame_uuid = create_data(frame_path, data)

        args = {
            'limit': 3
        }

        inputs = {
            'i': frame_uuid
        }

        result = table_command.run(args, inputs)

        correct = {
            'header':['顧客', '数量', '金額\n'],
            'reader':[['A', '1', '10\n'], ['A', '2', '20\n'], ['B', '1', '30\n']]
        }

        self.assertIsNotNone(result['o'])
        self.assertEqual(result['o']['header'], correct['header'])
        self.assertEqual(result['o']['reader'], correct['reader'])

        # 後片付け
        Library.delete_frame(frame_uuid)

    # @unittest.skip
    def test_execute_table_use_offset(self):
        """
        表形式でデータを出力するテスト
        offset使用
        """
        table_command = CommandLink('csvtohtmltable').resolve()
        # テストデータ作成
        data = [
            ['顧客', '数量', '金額'],
            ['A', 1, 10],
            ['A', 2, 20],
            ['B', 1, 30],
            ['B', 3, 40],
            ['B', 1, 50]
        ]
        frame_path = Path(self.TESTDATA_DIR) / 'test_data.csv'
        frame_uuid = create_data(frame_path, data)

        args = {
            'offset': 2
        }

        inputs = {
            'i': frame_uuid
        }

        result = table_command.run(args, inputs)

        correct = {
            'header':['顧客', '数量', '金額\n'],
            'reader':[['B', '1', '30\n'], ['B', '3', '40\n'], ['B', '1', '50\n']]
        }

        self.assertIsNotNone(result['o'])
        self.assertEqual(result['o']['header'], correct['header'])
        self.assertEqual(result['o']['reader'], correct['reader'])

        # 後片付け
        Library.delete_frame(frame_uuid)

    # @unittest.skip
    def test_execute_table_use_offset_and_limit(self):
        """
        表形式でデータを出力するテスト
        offsetとlimit使用
        """
        table_command = CommandLink('csvtohtmltable').resolve()
        # テストデータ作成
        data = [
            ['顧客', '数量', '金額'],
            ['A', 1, 10],
            ['A', 2, 20],
            ['B', 1, 30],
            ['B', 3, 40],
            ['B', 1, 50]
        ]
        frame_path = Path(self.TESTDATA_DIR) / 'test_data.csv'
        frame_uuid = create_data(frame_path, data)

        args = {
            'offset': 3,
            'limit': 1
        }

        inputs = {
            'i': frame_uuid
        }

        result = table_command.run(args, inputs)

        correct = {
            'header':['顧客', '数量', '金額\n'],
            'reader':[['B', '3', '40\n']]
        }

        self.assertIsNotNone(result['o'])
        self.assertEqual(result['o']['header'], correct['header'])
        self.assertEqual(result['o']['reader'], correct['reader'])

        # 後片付け
        Library.delete_frame(frame_uuid)

    # @unittest.skip
    def test_execute_table_no_data(self):
        """
        表形式でデータを出力するテスト
        dataが空の場合
        """
        table_command = CommandLink('csvtohtmltable').resolve()
        # テストデータ作成
        data = [['']]
        frame_path = Path(self.TESTDATA_DIR) / 'test_data.csv'
        frame_uuid = create_data(frame_path, data)

        args = {
            'offset': 2
        }

        inputs = {
            'i': frame_uuid
        }

        result = table_command.run(args, inputs)

        correct = {
            'header':['\n'],
            'reader':[]
        }

        self.assertIsNotNone(result['o'])
        self.assertEqual(result['o']['header'], correct['header'])
        self.assertEqual(result['o']['reader'], correct['reader'])

        # 後片付け
        Library.delete_frame(frame_uuid)

    # @unittest.skip
    def test_execute_linegraph(self):
        """
        折れ線グラフコマンドのテスト
        """
        table_command = CommandLink('csvtolinegraph').resolve()
        # テストデータ作成
        data = [
            ['TIME','S1','層別属性'],
            ['0','0.28','OK'],
            ['0.1','1.20','OK'],
            ['0.2','0.74','OK'],
            ['0.3','1.56','NG'],
            ['0.4','1.94','OK'],
            ['0.5','2.71','NG'],
            ['0.6','3.05','OK'],
            ['0.7','2.84','OK'],
            ['0.8','2.71','NG'],
            ['0.9','3.18','OK'],
        ]
        frame_path = Path(self.TESTDATA_DIR) / 'test_data.csv'
        frame_uuid = create_data(frame_path, data)

        args = {
            'data_column'   : ['層別属性'],
            'height'        : 600,
            'limit'         : 100,
            'width'         : 1000,
            'x_axis'        : [{'column': 'TIME', 'label': ''}],
            'y_axis'        : [{'column': 'S1', 'label': ''}],
        }

        inputs = {
            'i': frame_uuid
        }

        result = table_command.run(args, inputs)

        self.assertIsNotNone(result['o']['script'])
        self.assertIsNotNone(result['o']['div'])

        # 後片付け
        Library.delete_frame(frame_uuid)


    # @unittest.skip
    def test_execute_histogram(self):
        """
        ヒストグラムコマンドのテスト
        """
        table_command = CommandLink('csvtohistogram').resolve()
        # テストデータ作成
        data = [
            ['TIME','S1','層別属性'],
            ['0','0.28','OK'],
            ['0.1','1.20','OK'],
            ['0.2','0.74','OK'],
            ['0.3','1.56','NG'],
            ['0.4','1.94','OK'],
            ['0.5','2.71','NG'],
            ['0.6','3.05','OK'],
            ['0.7','2.84','OK'],
            ['0.8','2.71','NG'],
            ['0.9','3.18','OK'],
        ]
        frame_path = Path(self.TESTDATA_DIR) / 'test_data.csv'
        frame_uuid = create_data(frame_path, data)

        args = {
            'data_column'   : [],
            'bins'          : 20,
            'height'        : 600,
            'limit'         : 100,
            'width'         : 1000,
            'x_axis'        : [{'column': 'TIME', 'label': ''}],
        }

        inputs = {
            'i': frame_uuid
        }

        result = table_command.run(args, inputs)

        self.assertIsNotNone(result['o']['script'])
        self.assertIsNotNone(result['o']['div'])

        # 後片付け
        Library.delete_frame(frame_uuid)

    # @unittest.skip
    def test_execute_scatter(self):
        """
        散布図コマンドのテスト
        """
        table_command = CommandLink('csvtoscatter').resolve()
        # テストデータ作成
        data = [
            ['TIME','S1','層別属性'],
            ['0','0.28','OK'],
            ['0.1','1.20','OK'],
            ['0.2','0.74','OK'],
            ['0.3','1.56','NG'],
            ['0.4','1.94','OK'],
            ['0.5','2.71','NG'],
            ['0.6','3.05','OK'],
            ['0.7','2.84','OK'],
            ['0.8','2.71','NG'],
            ['0.9','3.18','OK'],
        ]
        frame_path = Path(self.TESTDATA_DIR) / 'test_data.csv'
        frame_uuid = create_data(frame_path, data)

        args = {
            'data_column'   : ['層別属性'],
            'height'        : 600,
            'limit'         : 100,
            'width'         : 1000,
            'x_axis'        : [{'column': 'TIME', 'label': ''}],
            'y_axis'        : [{'column': 'S1', 'label': ''}],
        }

        inputs = {
            'i': frame_uuid
        }

        result = table_command.run(args, inputs)

        self.assertIsNotNone(result['o']['script'])
        self.assertIsNotNone(result['o']['div'])

        # 後片付け
        Library.delete_frame(frame_uuid)

    # @unittest.skip
    def test_execute_boxplot(self):
        """
        箱ひげ図コマンドのテスト
        """
        table_command = CommandLink('csvtoboxplot').resolve()
        # テストデータ作成
        data = [
            ['TIME','S1','層別属性'],
            ['0','0.28','OK'],
            ['0.1','1.20','OK'],
            ['0.2','0.74','OK'],
            ['0.3','1.56','NG'],
            ['0.4','1.94','OK'],
            ['0.5','2.71','NG'],
            ['0.6','3.05','OK'],
            ['0.7','2.84','OK'],
            ['0.8','2.71','NG'],
            ['0.9','3.18','OK'],
        ]
        frame_path = Path(self.TESTDATA_DIR) / 'test_data.csv'
        frame_uuid = create_data(frame_path, data)

        args = {
            'data_column'   : [],
            'height'        : 600,
            'limit'         : 100,
            'width'         : 1000,
            'y_axis'        : [{'column': 'S1', 'label': ''}],
        }

        inputs = {
            'i': frame_uuid
        }

        result = table_command.run(args, inputs)

        self.assertIsNotNone(result['o']['script'])
        self.assertIsNotNone(result['o']['div'])

        # 後片付け
        Library.delete_frame(frame_uuid)

    def test_execute_timecompression(self):
        table_command = CommandLink('csvtotimecompressionform').resolve()
        mbucket_command = CommandLink('mbucket').resolve()

        # テストデータ作成
        data = [
            ['TIME','S1','層別属性'],
            ['0','0.28','OK'],
            ['0.1','1.20','OK'],
            ['0.2','0.74','OK'],
            ['0.3','1.56','NG'],
            ['0.4','1.94','OK'],
            ['0.5','2.71','NG'],
            ['0.6','3.05','OK'],
            ['0.7','2.84','OK'],
            ['0.8','2.71','NG'],
            ['0.9','3.18','OK'],
        ]

        frame_path = Path(self.TESTDATA_DIR) / 'test_data.csv'
        frame_uuid = create_data(frame_path, data)

        args = {
            'data'         : ['層別属性'],
            'division'      : '3',
            'statics'       : 'min,mean,max',
            'height'        : 600,
            'limit'         : 100,
            'offset'        : 0,
            'width'         : 1000,
            'y_axis'        : [{'column': 'S1', 'label': ''}],
            'x_axis'        : [{'column': 'TIME', 'label': ''}],
        }

        # 軸の設定
        x_axis         = args.get('x_axis')
        x_axis_column  = x_axis[0]['column']
        x_axis_label   = x_axis[0]['label']

        y_axis              = args.get('y_axis')
        y_axis_column  = y_axis[0]['column']
        y_axis_label   = y_axis[0]['label']

        # データ系列の設定
        data     = args.get('data')   if args.get('data') is not None else []

        # データ表示範囲の設定
        offset          = int(args.get('offset'))   if args.get('offset')   else 0
        limit           = int(args.get('limit'))    if args.get('limit')    else None

        # グラフ表示要素の設定
        division        = args.get('division')
        statics         = args.get('statics')
        display_pattern = args.get('display_pattern')
        
        # グラフサイズの設定
        graph_width     = int(args.get('width'))
        graph_height    = int(args.get('height'))

        # df
        frame = Library.load_frame(frame_uuid)
        df = frame.get_dataframe(limit, offset)
        
         # title
        df_x_minmax = self.doMsummary(df, None, x_axis_column, "min,max")
        df_y_minmax = self.doMsummary(df, None, y_axis_column, "min,max")

        x_min = df_x_minmax.iat[0, 1]
        x_max = df_x_minmax.iat[0, 2]

        y_min = df_y_minmax.iat[0, 1]
        y_max = df_y_minmax.iat[0, 2]

        if len(data) > 0:
            results = self.direct_product_by_keys(df, data)
            named_dfs = self.process_df(df, results)
        else:
            named_dfs = {}
            named_dfs['all'] = df

        def rangesToPoints(df, column):
            for index, row in df.iterrows():
                array = df.at[index, column].split("_")
                df.at[index, column] = '0' if array[0] == '' else array[0]

        staticsArray = statics.split(",")
        source = {}
        for label, _df in named_dfs.items():
            source[label] = {}

            # 分割
            result_column = x_axis_column + "_"
            f = "{}:{}".format(x_axis_column, result_column)
            df_bucket = self.doMbucket(_df, None, f, division)

            # min, max
            df_x_minmax = self.doMsummary(_df, None, x_axis_column, "min,max")
            df_y_minmax = self.doMsummary(_df, None, y_axis_column, "min,max")

            x_min = df_x_minmax.iat[0, 1]
            x_max = df_x_minmax.iat[0, 2]

            y_min = df_y_minmax.iat[0, 1]
            y_max = df_y_minmax.iat[0, 2]

            source[label]["x_range"] = [float(x_min),float(x_max)]
            source[label]["y_range"] = [float(y_min),float(y_max)]

            # 統計量
            df_summary = self.doMsummary(df_bucket, result_column, y_axis_column, statics)
            rangesToPoints(df_summary, result_column)
            df_summary = df_summary.sort_values(result_column)

            source[label][result_column] = df_summary[result_column].tolist()
            for s in staticsArray:
                source[label][s] = df_summary[s].tolist()
 
        # Graph Plot
        plots = []
        for g in source:
            title = "時間圧縮図:{}、 期間:{} ~ {}".format(g, source[g]["x_range"][0], source[g]["x_range"][1])
            tools = "pan,wheel_zoom,box_zoom,reset,save,box_select"
            plot = figure(
                title=title,
                tools=tools,
                x_range=source[g]["x_range"],
                y_range=source[g]["y_range"],
                x_axis_label=x_axis_label,
                y_axis_label=y_axis_label
            )
            colors = self.get_colors(len(staticsArray))
            index = 0
            for index in range(len(staticsArray)):
                color = colors[index]
                statics = staticsArray[index]
                plot.line(source[g][result_column], source[g][statics], legend=statics, color=color, alpha=0.75, muted_color=color, muted_alpha=0.2)
                if display_pattern == "hatch" and index + 1 < len(staticsArray):
                        x = source[g][result_column]
                        y1 = source[g][staticsArray[index]]
                        y2 = source[g][staticsArray[index + 1]]
                        plot.varea(x=x, y1=y1, y2=y2, fill_color='#cccccc', alpha=0.5)  

            plot.legend.location = "top_left"
            plot.legend.click_policy = "mute"
            plots.append(plot)

        result = gridplot(plots, ncols=1, plot_width=graph_width, plot_height=graph_height) 
        
        assertIsNotNone(result)

    def get_colors(self, size):
        i = 0
        colors = []
        for d in itertools.cycle(palette):
            if i >= size:
                break
            colors.append(d)
            i = i + 1

        return colors

    def doMsummary(self, df, k, f, c):

        i = df.values.tolist()
        i.insert(0,list(df.columns))

        result = None
        result <<= nm.msummary(i=i, k=k, f=f, c=c).writelist(header=True)
        result = result.run()

        name = result.pop(0)
        result_df = pd.DataFrame(result,columns=name)

        return result_df

    def doMbucket(self, df, k, f, n):
        
        i = df.values.tolist()
        i.insert(0,list(df.columns))

        result = None
        result <<= nm.mbucket(i=i, k=k, n=n, f=f, F="1").writelist(header=True)
        result = result.run()

        name = result.pop(0)
        result_df = pd.DataFrame(result,columns=name)

        return result_df

    def direct_product_by_keys(self, df, keys):
        """
        キー項目の直積を求める
        """
        args = {key: df[key].unique().tolist() for key in keys}
        direct_product = list(itertools.product(*list(args.values())))

        results = []
        for seki in direct_product:
            results.append(dict(zip(keys, seki)))

        return results

    def process_df(self, df, direct_product):
        """
        直積で絞り込んだdf群を返す
        """
        df_dict = {}
        for result in direct_product:
            _df = df
            for key, value in result.items():
                _df = _df[_df[key]==value]
            df_dict['-'.join(map(str, list(result.values())))] = _df
        return df_dict
def create_data(file_path_obj, data=None):
    """;

    テストデータ作成用
    frameのuuidが返る
    """
    
    root = Library.load_root()
    if data is not None:
        nm.mread(i=data, o=file_path_obj.as_posix()).run()
    frame = Library.save_frame(root.uuid, str(uuid.uuid4()), file_path_obj)
    return frame.uuid


