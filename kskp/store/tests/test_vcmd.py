import os
import io
import json
import unittest
from kskp.store import Library, Flow
from kskp.engine import execute, FlowJsonLink, FlowLinkContext


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
        root = Library.load_root()
        # テスト用データを作成する
        test_data  = b'customer,date,amount,add1,add2,add3' + b'\n'
        test_data += b'A,20180101,5200,0,0,0' + b'\n'
        test_data += b'B,20180101,800,0,0,0'  + b'\n'
        test_data += b'B,20180112,3500,1,2,3' + b'\n'
        test_data += b'A,20180105,2000,4,5,6' + b'\n'
        test_data += b'B,20180107,4000,0,0,0' + b'\n'
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
            "label": "vis",
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
                        "f": "*"
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
        vis_args = 	{
			"d1" : {
                "args" : {
                    "visualizer" : "csvtohtmltable",
                    "offset" : 2,
                    "limit"  : 2
                }
			}
		}
        
        result = self.exec_flow(vis_args)

        expected_result = {'header': ['customer', 'date', 'amount', 'add1', 'add2', 'add3'], 
                           'reader': [['B', '20180112', '3500', '1', '2', '3'], 
                                      ['A', '20180105', '2000', '4', '5', '6']]
                          }

        self.assertDictEqual(result, expected_result)
        
    def test_csvtolinegraph(self):
        vis_args = 	{
			"d1" : {
                "args" : {
                    "visualizer" : "csvtolinegraph",
                    "offset" : 2,
                    "limit"  : 2
                }
			}
		}
        result = self.exec_flow(vis_args)
        self.assertIsInstance(result['div'], str)
        self.assertIsInstance(result['script'], str)

    @unittest.skip('パラメタ列の推測の実装を更新してから再テスト')
    def test_csvtohistogram(self):
        vis_args = 	{
			"d1" : {
                "args" : {
                    "visualizer" : "csvtohistogram",
                    "offset" : 2,
                    "limit"  : 2
                }
			}
		}
        result = self.exec_flow(vis_args)
        self.assertIsInstance(result['div'], str)
        self.assertIsInstance(result['script'], str)

    @unittest.skip('パラメタ列の推測の実装を更新してから再テスト')
    def test_csvtoscatter(self):
        vis_args = 	{
			"d1" : {
                "args" : {
                    "visualizer" : "csvtoscatter",
                    "offset" : 2,
                    "limit"  : 2
                }
			}
		}
        result = self.exec_flow(vis_args)
        self.assertIsInstance(result['div'], str)
        self.assertIsInstance(result['script'], str)

    def test_csvtoboxplot(self):
        vis_args = 	{
			"d1" : {
                "args" : {
                    "visualizer" : "csvtoboxplot",
                    "offset" : 2,
                    "limit"  : 2
                }
			}
		}
        result = self.exec_flow(vis_args)
        self.assertIsInstance(result['div'], str)
        self.assertIsInstance(result['script'], str)

    @unittest.skip('パラメタ列の推測の実装を更新してから再テスト')
    def test_csvtorepetitiviewaveform(self):
        vis_args = 	{
			"d1" : {
                "args" : {
                    "visualizer" : "csvtorepetitiviewaveform",
                    "offset" : 2,
                    "limit"  : 2
                }
			}
		}
        result = self.exec_flow(vis_args)
        self.assertIsInstance(result['div'], str)
        self.assertIsInstance(result['script'], str)

    def convert_from_activity_vis(self, activity):
        """
        execute()の戻り値であるActivityから
        pointのidとvisのDictに置き換える
        """
        return {point.id : vis.result for point, vis in activity.result}

    def exec_flow(self, vis_args):
        flow = Flow(None, 'CSV to graph', self.flow_csvtohtmltable)
        flow_link = FlowJsonLink(flow, vis_args=vis_args)
        activity = execute(flow_link, {}, {})
        result = self.convert_from_activity_vis(activity)['d1']
        return result