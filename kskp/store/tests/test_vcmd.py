import os
import io
import json
import unittest
from kskp.engine import execute, FlowJsonLink


class VCmdTestCase(unittest.TestCase):
    """
    visualize用コマンドの実行テスト
    """

    # テストデータのUUID
    frame_uuid = None

    @classmethod
    def setUpClass(cls):
        # テスト用スキーマを作成する
        from kskp.core import Datum
        from kskp.store import Frame
        # ルートフォルダを取得する
        root = Datum.find_root()
        # テスト用データを作成する
        test_data  = b'customer,date,amount' + b'\n'
        test_data += b'A,20180101,5200' + b'\n'
        test_data += b'B,20180101,800'  + b'\n'
        test_data += b'B,20180112,3500' + b'\n'
        test_data += b'A,20180105,2000' + b'\n'
        test_data += b'B,20180107,4000' + b'\n'
        with io.BytesIO(test_data) as b:
            frame = Frame(root.uuid, "customer data", b)
            VCmdTestCase.frame_uuid = frame.uuid
            frame.save()
    
    @classmethod
    def tearDownClass(cls):
        # ライブラリフォルダを削除する
        from kskp.core import Datum
        from kskp.store import STORE_DIR
        library_path = STORE_DIR.parent / Datum.find_root().path
        import shutil
        shutil.rmtree(library_path.as_posix())
        # Sessionを閉じる
        from kskp.store import ss as session
        session.close()
        # スキーマを破棄する
        from kskp.store import engine
        from sqlalchemy import DDL
        engine.execute(DDL('DROP SCHEMA IF EXISTS %s CASCADE' % os.environ['KSKP_POSTGRESQL_SCHEMA_NAME']))

    def setUp(self):
        # テスト用フローの定義
        self.flow_csvtohtmltable = {
            "label": "preview",
            "ports": [[],[]], 
            "params": [], 
            "creator": "開発用", 
            "createdAt": "2019-11-04 10:58:55", 
            "description": "",
            "nodes": [
                {
                    "id": "d2",
                    "type": "frame", 
                    "uuid": VCmdTestCase.frame_uuid, 
                    "error": {}, 
                    "label": "testData.csv", 
                    "invalid": {}, 
                    "makeCache": False, 
                    "dataSource": "csv", 
                    "cacheCreatedAt": None
                },
                {
                    "id": "c1", 
                    "args": {
                        "f": "customer,amount,date"
                    }, 
                    "dsts": {
                        "o": "d1"
                    },
                    "srcs": {
                        "i": "d2"
                    }, 
                    "type": "command", 
                    "error": {}, 
                    "label": "列選択", 
                    "invalid": {}, 
                    "commandId": "mcut", 
                    "srcsOrder": [
                        "i"
                    ]
                }, 
                {
                    "id": "d1", 
                    "type": "frame", 
                    "uuid": None, 
                    "error": {}, 
                    "label": "d1", 
                    "invalid": {}, 
                    "makeCache": False, 
                    "dataSource": "csv", 
                    "cacheCreatedAt": None
                }
            ]
        }

    def test_csvtohtmltable(self):
        json_str = json.dumps(self.flow_csvtohtmltable)
        preview_args = 	{
			"d1" : {
                "args" : {
                    "visualizer" : "csvtohtmltable",
                    "offset" : 2,
                    "limit"  : 2
                }
			}
		}
        flow_link = FlowJsonLink('CSV to HTML table', json_str, FlowLinkContext(), preview_args=preview_args)
        activity = execute(flow_link, {}, {})
        result = self.convert_from_activity_preview(activity)['d1']

        expected_result = {'header': ['customer', 'amount', 'date'], 
                           'reader': [['B', '3500', '20180112'], 
                                      ['A', '2000', '20180105']]
                          }

        self.assertDictEqual(result, expected_result)
        
    def test_csvtolinegraph(self):
        pass

    def test_csvtohistogram(self):
        pass

    def test_csvtoscatter(self):
        pass

    def test_csvtoboxplot(self):
        pass

    def test_csvtorepetitiviewaveform(self):
        pass

    def convert_from_activity_preview(self, activity):
        """
        execute()の戻り値であるActivityから
        pointのidとpreviewのDictに置き換える
        """
        return {point.id : preview.result for point, preview in activity.result}