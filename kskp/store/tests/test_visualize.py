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
    TESTDATA_DIR = 'store/frames'

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

def create_data(file_path_obj, data=None):
    """
    テストデータ作成用
    frameのuuidが返る
    """
    root = Library.load_root()
    if data is not None:
        print('file_path_obj.as_posix(): ' + file_path_obj.as_posix())
        print('file_path_obj.resolve(): ' + file_path_obj.resolve().as_posix())
        nm.mread(i=data, o=file_path_obj.resolve().as_posix()).run()
    frame = Library.save_frame(root.uuid, str(uuid.uuid4()), file_path_obj)
    return frame.uuid
