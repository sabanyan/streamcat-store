import unittest
import nysol.mcmd as nm
import uuid

from pathlib import Path
from kskp.store import Library, CommandLink

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
            ['datetime', 'stockprice', 'price'],
            ['2018/1/4', 'openingprice', 7300],
            ['2018/1/4', 'closingprice', 7419],
            ['2018/1/5', 'openingprice', 7450],
            ['2018/1/5', 'closingprice', 7552]
        ]
        frame_path = Path(self.TESTDATA_DIR) / 'test_data.csv'
        frame_uuid = create_data(frame_path, data)

        args = {
            'alpha': 1,
            'data_column': 'stockprice',
            'graph_title': "",
            'limit': 100,
            'offset': None,
            'time_series_column': [
                'datetime'
            ],
            'x_axis_column': 'datetime',
            'y_axis_column': 'price',
            'x_label': '',
            'x_size': 1000,
            'y_label': '',
            'y_size': 1000
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
            'alpha': 1,
            'bins': 20,
            'data_column': '顧客',
            'graph_title': "",
            'limit': 100,
            'offset': None,
            'x_axis': '金額',
            'x_label': '',
            'x_size': 1000,
            'y_label': '',
            'y_size': 1000
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
            'alpha': 1,
            'graph_title': "",
            'limit': 100,
            'offset': None,
            'x_axis': "数量",
            'x_label': "",
            'x_size': 1000,
            'y_axis': "金額",
            'y_label': "",
            'y_size': 600
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
            'graph_title': "",
            'limit': 100,
            'offset': None,
            'x_axis': ["顧客"],
            'x_label': "",
            'x_size': 1000,
            'y_axis': "金額",
            'y_label': "",
            'y_size': 600
        }

        inputs = {
            'i': frame_uuid
        }

        result = table_command.run(args, inputs)

        self.assertIsNotNone(result['o']['script'])
        self.assertIsNotNone(result['o']['div'])

        # 後片付け
        Library.delete_frame(frame_uuid)

def create_data(file_path_obj, data=None):
    """
    テストデータ作成用
    frameのuuidが返る
    """
    root = Library.load_root()
    if data is not None:
        nm.mread(i=data, o=file_path_obj.as_posix()).run()
    frame = Library.save_frame(root.uuid, str(uuid.uuid4()), file_path_obj)
    return frame.uuid
