import io
import unittest
from streamcat.engine import execute, FlowCommand
from .test_case_base import TestCaseBase

class VCmdTestCase(TestCaseBase):
    """
    visualize用コマンドの実行テスト
    """

    # テストデータのUUID
    frame_uuid = None

    @classmethod
    def setUpClass(cls):
        # 親クラスのsetUpClass()を実行する
        TestCaseBase.setUpClass()

        # ルートフォルダを取得する
        root = cls.factory.data.load_root()
        # テスト用データを作成する
        test_data  = b'customer,date,amount,add1,add2,add3' + b'\n'
        test_data += b'A,20180101,5200,0,0,0' + b'\n'
        test_data += b'B,20180101,800,0,0,0'  + b'\n'
        test_data += b'B,20180112,3500,1,2,3' + b'\n'
        test_data += b'A,20180105,2000,4,5,6' + b'\n'
        test_data += b'B,20180107,4000,0,0,0' + b'\n'
        with io.BytesIO(test_data) as b:
            frame = root.create_frame("customer data", b)
            VCmdTestCase.frame_uuid = frame.uuid
            frame.save()
    
    @classmethod
    def tearDownClass(cls):
        # 親クラスのtearDownClass()を実行する
        TestCaseBase.tearDownClass()

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
    
    @unittest.skip('パラメタ列の推測の実装を更新してから再テスト')
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

    @unittest.skip('パラメタ列の推測の実装を更新してから再テスト')
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

    def convert_from_activity_vis(self, outs):
        """
        execute()の戻り値であるActivityから
        pointのidとvisのDictに置き換える
        """
        from streamcat.store import Activity
        # Activityを取得して返り値とする
        for point_id, datum in outs.items():
            if isinstance(datum, Activity):
                return {point.id : vis.result for point, vis in datum.outs}

    def exec_flow(self, vis_args):
        from streamcat.store import FlowData
        root = self.factory.data.load_root()
        flow_data = FlowData(self.flow_csvtohtmltable)
        flow = root.create_flow('CSV to graph', flow_data)
        flow_link = FlowCommand(flow)
        outs = execute(flow_link, {'vis':vis_args}, {})
        result = self.convert_from_activity_vis(outs)['d1']
        return result