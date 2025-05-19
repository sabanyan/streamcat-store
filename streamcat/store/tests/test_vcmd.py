import io
import unittest
from streamcat.engine import FlowCommand, aexecute
from .test_case_base import TestCaseBase

class VCmdTest(TestCaseBase, unittest.IsolatedAsyncioTestCase):
    """
    Vコマンドの実行テスト
    """

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()

        # テスト用データを作成する
        test_data  = b'customer,date,amount,add1,add2,add3' + b'\n'
        test_data += b'A,20180101,5200,0,0,0' + b'\n'
        test_data += b'B,20180101,800,0,0,0'  + b'\n'
        test_data += b'B,20180112,3500,1,2,3' + b'\n'
        test_data += b'A,20180105,2000,4,5,6' + b'\n'
        test_data += b'B,20180107,4000,0,0,0' + b'\n'

        root = self.finder.data.load_root()
        frame = root.create_frame("customer data", io.BytesIO(test_data))
        frame.save()
        self.finder.end()

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
                    "uuid": frame.uuid, 
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

    async def exec_flow(self, vis_args):
        from streamcat.store import FlowData
        root = self.finder.data.load_root()
        flow_data = FlowData(self.flow_csvtohtmltable)
        flow = root.create_flow('CSV to graph', flow_data)
        flow_link = FlowCommand(flow)
        outs = await aexecute(flow_link, {'vis':vis_args}, {})
        result = self.convert_from_job_vis(outs)['d1']
        return result


    def convert_from_job_vis(self, job):
        """
        execute()の戻り値から
        pointのidとvisのDictに置き換える
        """
        from streamcat.store import ApparentOuts
        for point_id, datum in job.join().items():
            if isinstance(datum, ApparentOuts):
                return {out.out_point.id : out.datum.result for out in datum.outs}

    async def test_csvtohtmltable(self):
        vis_args = 	{
			"d1" : {
                "args" : {
                    "visualizer" : "csvtohtmltable",
                    "offset" : 2,
                    "limit"  : 2
                }
			}
		}
        
        result = await self.exec_flow(vis_args)

        expected_result = {'header': ['customer', 'date', 'amount', 'add1', 'add2', 'add3'], 
                           'reader': [['B', '20180112', '3500', '1', '2', '3'], 
                                      ['A', '20180105', '2000', '4', '5', '6']]
                          }

        self.assertDictEqual(result, expected_result)
    
    @unittest.skip('パラメタ列の推測の実装を更新してから再テスト')
    async def test_csvtolinegraph(self):
        vis_args = 	{
			"d1" : {
                "args" : {
                    "visualizer" : "csvtolinegraph",
                    "offset" : 2,
                    "limit"  : 2
                }
			}
		}
        result = await self.exec_flow(vis_args)
        self.assertIsInstance(result['div'], str)
        self.assertIsInstance(result['script'], str)

    @unittest.skip('パラメタ列の推測の実装を更新してから再テスト')
    async def test_csvtohistogram(self):
        vis_args = 	{
			"d1" : {
                "args" : {
                    "visualizer" : "csvtohistogram",
                    "offset" : 2,
                    "limit"  : 2
                }
			}
		}
        result = await self.exec_flow(vis_args)
        self.assertIsInstance(result['div'], str)
        self.assertIsInstance(result['script'], str)

    @unittest.skip('パラメタ列の推測の実装を更新してから再テスト')
    async def test_csvtoscatter(self):
        vis_args = 	{
			"d1" : {
                "args" : {
                    "visualizer" : "csvtoscatter",
                    "offset" : 2,
                    "limit"  : 2
                }
			}
		}
        result = await self.exec_flow(vis_args)
        self.assertIsInstance(result['div'], str)
        self.assertIsInstance(result['script'], str)

    @unittest.skip('パラメタ列の推測の実装を更新してから再テスト')
    async def test_csvtoboxplot(self):
        vis_args = 	{
			"d1" : {
                "args" : {
                    "visualizer" : "csvtoboxplot",
                    "offset" : 2,
                    "limit"  : 2
                }
			}
		}
        result = await self.exec_flow(vis_args)
        self.assertIsInstance(result['div'], str)
        self.assertIsInstance(result['script'], str)

    @unittest.skip('パラメタ列の推測の実装を更新してから再テスト')
    async def test_csvtorepetitiviewaveform(self):
        vis_args = 	{
			"d1" : {
                "args" : {
                    "visualizer" : "csvtorepetitiviewaveform",
                    "offset" : 2,
                    "limit"  : 2
                }
			}
		}
        result = await self.exec_flow(vis_args)
        self.assertIsInstance(result['div'], str)
        self.assertIsInstance(result['script'], str)
