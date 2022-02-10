import copy
from kskp.engine import execute, FlowCommand
from kskp.store import FlowData
from .test_case_base import TestCaseBase

class AssertCmdTest(TestCaseBase):
    """
    2つの入力に対して、出力が一致しているかどうかを確認する。入力にはcsv、StreamCatのエラーに対応する
    入力されたデータが行ごとに一致しているかを確認し、結果を出力する

    出力値の各列情報は、
    ["フロー名","フローUUID", "フローのパス","実行日時","テストポイントID","テスト成功","エラー発生","行番号","入力iのデータ","入力mのデータ"]

    本テストでは、入力データを変化させ、その出力が想定通りであるかを確認する
    """
    flow_json = {
        "label": "テストフロ",
        "params": [],
        "description": "",
        "ports": [[],[]],
        "nodes": [
            {
                "id": "i",
                "label": "テストデータ",
                "type": "frame",
                "value": [['顧客','数量','金額'],
                    ['A',1,10],
                    ['A',2,20],
                    ['B',1,30],
                    ['B',3,40],
                    ['B',1,50]],
                "dataSource": "csv"
            },
            {
                "id": "d1",
                "type": "frame",
                "label": "d1",
                "uuid": None,
                "dataSource": "csv"
            },
            {
                "id": "c1",
                "label": "c1",
                "type": "command",
                "srcs": {
                    "i": "i"
                },
                "dsts": {
                    "o": "d1"
                },
                "args": {
                    "f": "0,1",
                    "x": True
                },
                "commandId": "mcut"
            }
        ]
    }

    simple_assert_json = {
        "label": "テストフロ",
        "params": [],
        "description": "",
        "ports": [[],[]],
        "nodes": [
            {
                "id": "i",
                "label": "テストデータ",
                "type": "frame",
                "value": [['顧客','数量','金額'],
                    ['A',1,10],
                    ['A',2,20],
                    ['B',1,30],
                    ['B',3,40],
                    ['B',1,50]],
                "dataSource": "csv"
            },
            {
                "id": "d1",
                "label": "d1",
                "type": "frame",
                "uuid": None,
                "dataSource": "csv"
            },
            {
                "id": "i2",
                "label": "テストデータ2",
                "type": "frame",
                "value": [['顧客','数量','金額'],
                    ['A',1,10],
                    ['B',1,30]],
                "dataSource": "csv"
            },
            {
                "id": "c1",
                "label": "c1",
                "type": "command",
                "commandId": "assert",
                "args": {
                    "dlimit": "10"
                },
                "dsts": {
                    "o": "d1"
                },
                "srcs": {
                    "i": "i",
                    "m": "i2"
                }
            }
        ]
    }

    flow_json_same = {
        "label": "テストフロ",
        "params": [],
        "description": "",
        "ports": [[],[]],
        "nodes": [
            {
                "id": "i",
                "label": "テストデータ",
                "type": "frame",
                "value": [['顧客','数量','金額'],
                    ['A',1,10],
                    ['A',2,20],
                    ['B',1,30],
                    ['B',3,40],
                    ['B',1,50]],
                "dataSource": "csv"
            },
            {
                "id": "d1",
                "label": "d1",
                "type": "frame",
                "uuid": None,
                "dataSource": "csv"
            },
            {
                "id": "i2",
                "label": "テストデータ2",
                "type": "frame",
                "value": [['顧客','数量','金額'],
                    ['A',1,10],
                    ['A',2,20],
                    ['B',1,30],
                    ['B',3,40],
                    ['B',1,50]],
                "dataSource": "csv"
            },
            {
                "id": "c1",
                "label": "c1",
                "type": "command",
                "commandId": "assert",
                "args": {
                    "verbose": True,
                    "dlimit": "10"
                },
                "dsts": {
                    "o": "d1"
                },
                "srcs": {
                    "i": "i",
                    "m": "i2"
                }
            }
        ]
    }

    sequential_assert_json = {
        "label": "テストフロ",
        "params": [],
        "description": "",
        "ports": [[],[]],
        "nodes": [
            {
                "id": "i",
                "label": "テストデータ",
                "type": "frame",
                "value": [['顧客','数量','金額'],
                    ['A',1,10],
                    ['A',2,20],
                    ['B',1,30],
                    ['B',3,40],
                    ['B',1,50]],
                "dataSource": "csv"
            },
            {
                "id": "d1",
                "label": "d1",
                "type": "frame",
                "uuid": None,
                "dataSource": "csv"
            },
            {
                "id": "d2",
                "label": "d2",
                "type": "frame",
                "uuid": None,
                "dataSource": "csv"
            },
            {
                "id": "i2",
                "label": "テストデータ2",
                "type": "frame",
                "value": [['顧客','数量','金額'],
                    ['A',1,10],
                    ['B',1,30]],
                "dataSource": "csv"
            },
            {
                "id": "c1",
                "label": "c1",
                "type": "command",
                "commandId": "assert",
                "args": {
                    "verbose": True,
                    "dlimit": "10"
                },
                "dsts": {
                    "o": "d1"
                },
                "srcs": {
                    "i": "i",
                    "m": "i2"
                }
            },
            {
                "id": "c2",
                "label": "c2",
                "type": "command",
                "commandId": "assert",
                "args": {
                    "verbose": True,
                    "dlimit": "10"
                },
                "dsts": {
                    "o": "d2"
                },
                "srcs": {
                    "i": "i",
                    "m": "d1"
                }
            }
        ]
    }

    double_assert_json = {
        "label": "テストフロ",
        "params": [],
        "description": "",
        "ports": [[],[]],
        "nodes": [
            {
                "id": "i",
                "label": "テストデータ",
                "type": "frame",
                "value": [['顧客','数量','金額'],
                    ['A',1,10],
                    ['A',2,20],
                    ['B',1,30],
                    ['B',3,40],
                    ['B',1,50]],
                "dataSource": "csv"
            },
            {
                "id": "d1",
                "label": "d1",
                "type": "frame",
                "uuid": None,
                "dataSource": "csv"
            },
            {
                "id": "d2",
                "label": "d2",
                "type": "frame",
                "uuid": None,
                "dataSource": "csv"
            },
            {
                "id": "i2",
                "label": "テストデータ2",
                "type": "frame",
                "value": [['顧客','数量','金額'],
                    ['A',1,10],
                    ['B',1,30]],
                "dataSource": "csv"
            },
            {
                "id": "c1",
                "label": "c1",
                "type": "command",
                "commandId": "assert",
                "args": {
                    "verbose": True,
                    "dlimit": "10"
                },
                "dsts": {
                    "o": "d1"
                },
                "srcs": {
                    "i": "i",
                    "m": "i2"
                }
            },
            {
                "id": "c2",
                "label": "c2",
                "type": "command",
                "commandId": "assert",
                "args": {
                    "verbose": True,
                    "dlimit": "10"
                },
                "dsts": {
                    "o": "d2"
                },
                "srcs": {
                    "i": "i",
                    "m": "i2"
                }
            }
        ]
    }

    one_side_error_json = {
        "label": "テストフロ",
        "params": [],
        "description": "",
        "ports": [[],[]],
        "nodes": [
            {
                "id": "i",
                "label": "テストデータ",
                "type": "frame",
                "value": [['顧客','数量','金額'],
                    ['A',1,10],
                    ['A',2,20],
                    ['B',1,30],
                    ['B',3,40],
                    ['B',1,50]],
                "dataSource": "csv"
            },
            {
                "id": "d1",
                "label": "d1",
                "type": "frame",
                "uuid": None,
                "dataSource": "csv"
            },
            {
                "id": "c2",
                "label": "c2",
                "type": "command",
                "commandId": "mnewnumber",
                "args": {},
                "srcs": {},
                "dsts": {
                    "o": "d1"
                },
                "error": {}
            },
            {
                "id": "d2",
                "label": "d2",
                "type": "frame",
                "uuid": None,
                "dataSource": "csv"
            },
            {
                "id": "c1",
                "label": "c1",
                "type": "command",
                "commandId": "assert",
                "args": {
                    "verbose": True,
                    "dlimit": "10"
                },
                "dsts": {
                    "o": "d2"
                },
                "srcs": {
                    "i": "i",
                    "m": "d1"
                }
            }
        ]
    }

    both_same_error_json = {
        "label": "テストフロ",
        "params": [],
        "description": "",
        "ports": [[],[]],
        "nodes": [
            {
                "id": "c3",
                "label": "c3",
                "type": "command",
                "commandId": "mnewnumber",
                "args": {},
                "srcs": {},
                "dsts": {
                    "o": "d3"
                }
            },
            {
                "id": "d3",
                "label": "d3",
                "type": "frame",
                "uuid": None,
                "dataSource": "csv"
            },
            {
                "id": "c2",
                "label": "c2",
                "type": "command",
                "commandId": "mnewnumber",
                "args": {},
                "srcs": {},
                "dsts": {
                    "o": "d1"
                }
            },
            {
                "id": "d1",
                "label": "d1",
                "type": "frame",
                "uuid": None,
                "dataSource": "csv"
            },
            {
                "id": "c1",
                "label": "c1",
                "type": "command",
                "commandId": "assert",
                "args": {
                    "verbose": True,
                    "dlimit": "10"
                },
                "srcs": {
                    "i": "d3",
                    "m": "d1"
                },
                "dsts": {
                    "o": "d2"
                }
            },
            {
                "id": "d2",
                "label": "d2",
                "type": "frame",
                "uuid": None,
                "dataSource": "csv"
            }
        ]
    }

    both_error_json = {
        "label": "テストフロ",
        "params": [],
        "description": "",
        "ports": [[],[]],
        "nodes": [
            {
                "id": "c3",
                "label": "c3",
                "type": "command",
                "commandId": "mnewnumber",
                "args": {},
                "srcs": {},
                "dsts": {
                    "o": "d3"
                }
            },
            {
                "id": "d3",
                "label": "d3",
                "type": "frame",
                "uuid": None,
                "dataSource": "csv"
            },
            {
                "id": "d4",
                "label": "d4",
                "type": "frame",
                "uuid": None,
                "dataSource": "csv"
            },
            {
                "id": "c1",
                "label": "c1",
                "type": "command",
                "commandId": "assert",
                "args": {
                    "verbose": True,
                    "dlimit": "10"
                },
                "srcs": {
                    "i": "d3",
                    "m": "d4"
                },
                "dsts": {
                    "o": "d2"
                }
            },
            {
                "id": "d2",
                "label": "d2",
                "type": "frame",
                "uuid": None,
                "dataSource": "csv"
            },
            {
                "id": "c2",
                "label": "c2",
                "type": "command",
                "commandId": "mnewrand",
                "args": {},
                "srcs": {},
                "dsts": {
                    "o": "d4"
                }
            },
            {
                "id": "d1",
                "label": "d1",
                "type": "frame",
                "uuid": None,
                "dataSource": "csv"
            }
        ]
    }

    error_groupby2_json = {
        "label": "テストフロ",
        "params": [],
        "description": "",
        "ports": [[],[]],
        "nodes": [
            {
                "id": "i",
                "label": "テストデータ",
                "type": "frame",
                "value": [['顧客','数量','金額'],
                    ['A',1,10],
                    ['A',2,20],
                    ['B',1,30],
                    ['B',3,40],
                    ['B',1,50]],
                "dataSource": "csv"
            },
            {
                "id": "d1",
                "label": "d1",
                "type": "frame",
                "uuid": None,
                "dataSource": "csv"
            },
            {
                "id": "i2",
                "label": "テストデータ2",
                "type": "frame",
                "value": [['顧客','数量','金額'],
                    ['A',1,10],
                    ['B',1,30]],
                "dataSource": "csv"
            },
            {
                "id": "c2",
                "label": "c2",
                "type": "command",
                "commandId": "groupby2",
                "args": {
                    "clist":[
                        {
                            "c": "",
                            "fld": ""
                        }
                    ],
                    "fclist": [
                        {
                            "c": "sum",
                            "f": "random1"
                        },
                        {
                            "c": "max",
                            "f": "random2"
                        },
                        {
                            "c": "min",
                            "f": "random3"
                        }
                    ],
                    "format": "&_%",
                    "nfclist": [
                        {
                            "c": "",
                            "f": "",
                            "n": ""
                        }
                    ],
                    "xfclist": [
                        {
                            "c": "",
                            "f": "",
                            "x": ""
                        }
                    ],
                    "xfcnlist": [
                        {
                            "c": "",
                            "f": "",
                            "n": "",
                            "x": ""
                        }
                    ],
                    "precision": "10",
                    "dataformat": "date"
                },
                "srcs": {
                    "i": "i2"
                },
                "dsts": {
                    "o": "d3"
                }
            },
            {
                "id": "d3",
                "label": "d3",
                "type": "frame",
                "uuid": None,
                "dataSource": "csv"
            },
            {
                "id": "c1",
                "label": "c1",
                "type": "command",
                "commandId": "assert",
                "args": {
                    "verbose": True,
                    "dlimit": "10"
                },
                "dsts": {
                    "o": "d1"
                },
                "srcs": {
                    "i": "i",
                    "m": "d3"
                }
            }
        ]
    }

    dlimit_overred_json = {
        "label": "テストフロ",
        "ports": [[],[]],
        "params": [],
        "description": "",
        "nodes": [
            {
                "id": "d",
                "label": "テストデータ1",
                "type": "frame",
                "dataSource": "csv"
            },
            {
                "id": "c",
                "label": "c",
                "type": "command",
                "commandId": "mnewnumber",
                "args": {
                    "I": "1",
                    "S": "100",
                    "a": "column2",
                    "l": "10"
                },
                "dsts": {
                    "o": "d"
                },
                "srcs": {},
                "srcsOrder": []
            },
            {
                "id": "d1",
                "type": "frame",
                "label": "テストデータ2",
                "dataSource": "csv"
            },
            {
                "id": "c1",
                "label": "c1",
                "type": "command",
                "commandId": "mnewnumber",
                "args": {
                    "I": "1",
                    "S": "1",
                    "a": "column1",
                    "l": "10"
                },
                "dsts": {
                    "o": "d1"
                },
                "srcs": {},
                "srcsOrder": []
            },
            {
                "id": "d2",
                "label": "d2",
                "type": "frame",
                "dataSource": "csv"
            },
            {
                "id": "c2",
                "label": "c2",
                "type": "command",
                "commandId": "assert",
                "args": {
                    "verbose": True,
                    "dlimit": "10"
                },
                "dsts": {
                    "o": "d2"
                },
                "srcs": {
                    "i": "d1",
                    "m": "d"
                },
                "srcsOrder": [
                    "i",
                    "m"
                ]
            }
        ]
    }




    @classmethod
    def setUpClass(cls):
        # 親クラスのsetUpClass()を実行する
        TestCaseBase.setUpClass()
        cls.root = cls.factory.data.load_root()
        cls.TESTDATA_DIR = cls.root.path
        maxDiff = None

    @classmethod
    def tearDownClass(cls):
        # 親クラスのtearDownClass()を実行する
        TestCaseBase.tearDownClass()

    # Helpler
    def get_frame_by_uuid(self, uuid, header=True):
        """
        指定したuuidのframeを取得する
        """
        import csv
        result = []
        frame = self.factory.data.find_by_uuid(uuid)
        try:
          with open(frame.path, 'r') as f:
              rows = csv.reader(f)
              if header:
                  header = next(rows)
              for row in rows:
                  result.append(row)
        except Exception as e:
          raise e

        return result

    # @unittest.skip
    def test_simple_assert_command(self):
        """
        内容が3行目以降違う２つの入力に対して、assert_commandを一つ配置したフローを実行、
        出力で、入力データの3行目以降不一致判定が出ることを期待する。
        エラー判定はfalse        
        """
        flow_json = copy.deepcopy(self.simple_assert_json)
        flow_json['nodes'].append(self.create_data_dst_node('d1'))

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # 正解データ内のuuid, タイムスタンプはダミー、テスト実行時には、毎回変動するので、出力がされているかどうかのみ確認する
        corrects = {'d1': [
            ['00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','d1','False','False','3','A,2,20','B,1,30','False','0000-00-00 00:00:00.000000+00:00'],
            ['00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','d1','False','False','4','B,1,30','','False','0000-00-00 00:00:00.000000+00:00'],
            ['00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','d1','False','False','5','B,3,40','','False','0000-00-00 00:00:00.000000+00:00'],
            ['00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','d1','False','False','6','B,1,50','','False','0000-00-00 00:00:00.000000+00:00']
        ]}
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.exists(lasts['d1'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        results = self.get_frame_by_uuid(lasts['d1'].uuid)

        # 出力の一致を確認
        self.assertEqual(len(results), len(corrects['d1']))
        for result,correct in zip(results, corrects['d1']):
            self.assertEqual(len(result), len(correct))
            
            self.assertIsNotNone(result[0])
            self.assertEqual(result[1], correct[1])
            self.assertEqual(result[2], correct[2])
            self.assertEqual(result[3], correct[3])
            self.assertEqual(result[4], correct[4])
            self.assertEqual(result[5], correct[5])
            self.assertEqual(result[6], correct[6])
            self.assertEqual(result[7], correct[7])
            self.assertEqual(result[8], correct[8])
            self.assertIsNotNone(result[9])

        # 後片付け
        lasts['d1'].delete()

    # @unittest.skip
    def test_same_execute(self):
        """
        内容が同じ２つの入力に対して、assert_commandを一つ配置したフローを実行、
        出力で、入力データが一致という判定が出ることを期待する。
        エラー判定はfalse     
        """
        flow_json = copy.deepcopy(self.flow_json_same)
        flow_json['nodes'].append(self.create_data_dst_node('d1'))

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
        # 正解データ内のuuid, タイムスタンプはダミー、テスト実行時には、毎回変動するので、出力がされているかどうかのみ確認する
        corrects = {'d1': [
            ['00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','d1','True','False','','','','False','0000-00-00 00:00:00.000000+00:00']
        ]}
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.exists(lasts['d1'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        results = self.get_frame_by_uuid(lasts['d1'].uuid)

        # 出力の一致を確認
        self.assertEqual(len(results), len(corrects['d1']))
        for result,correct in zip(results, corrects['d1']):
            self.assertEqual(len(result), len(correct))
            
            self.assertIsNotNone(result[0])
            self.assertEqual(result[1], correct[1])
            self.assertEqual(result[2], correct[2])
            self.assertEqual(result[3], correct[3])
            self.assertEqual(result[4], correct[4])
            self.assertEqual(result[5], correct[5])
            self.assertEqual(result[6], correct[6])
            self.assertEqual(result[7], correct[7])
            self.assertEqual(result[8], correct[8])
            self.assertIsNotNone(result[9])

        # 後片付け
        lasts['d1'].delete()


    # @unittest.skip
    def test_case_sequential_assert(self):
        """
        assert_commandが２連続で実行されるフローを実行、出力結果をテストする
        assert_commandを２連続配置したフローを実行、
        出力で入力データ全行が不一致判定が出ることを期待する。
        エラー判定はfalse     
        """
        flow_json = copy.deepcopy(self.sequential_assert_json)
        flow_json['nodes'].append(self.create_data_dst_node('d2'))

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # # 正解データ内のuuid, タイムスタンプはダミー、テスト実行時には、毎回変動するので、出力がされているかどうかのみ確認する
        corrects = {'d2': [
            ['00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','d2','False','False','1','顧客,数量,金額','フローUUID,フローのパス,出力ノードID,差分なし,例外送出,行番号,入力iのデータ,入力mのデータ,差分取得限界数超過,実行日時','False','0000-00-00 00:00:00.000000+00:00'],
            ['00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','d2','False','False','2','A,1,10','00000000-0000-0000-0000-000000000000,/ライブラリ/テストフロ,d1,False,False,3,"A,2,20","",False,0000-00-00 00:00:00.000000+00:00','False','0000-00-00 00:00:00.000000+00:00'],
            ['00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','d2','False','False','3','A,2,20','00000000-0000-0000-0000-000000000000,/ライブラリ/テストフロ,d1,False,False,4,"B,1,30","",False,0000-00-00 00:00:00.000000+00:00','False','0000-00-00 00:00:00.000000+00:00'],
            ['00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','d2','False','False','4','B,1,30','00000000-0000-0000-0000-000000000000,/ライブラリ/テストフロ,d1,False,False,5,"B,3,40","",False,0000-00-00 00:00:00.000000+00:00','False','0000-00-00 00:00:00.000000+00:00'],
            ['00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','d2','False','False','5','B,3,40','00000000-0000-0000-0000-000000000000,/ライブラリ/テストフロ,d1,False,False,6,"B,1,50","",False,0000-00-00 00:00:00.000000+00:00','False','0000-00-00 00:00:00.000000+00:00'],
            ['00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','d2','False','False','6','B,1,50','','False','0000-00-00 00:00:00.000000+00:00']
        ]}
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.exists(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        results = self.get_frame_by_uuid(lasts['d2'].uuid)

        # 比較するデータ内にタイムスタンプがあるので、文字列を置き換え。
        # コマンドの動作自体は別のコマンドがしてくれているので、ここではerrorが発生しないことを確認
        for s in results:
            s[9]= "Replacement of output information"
        for s in corrects['d2']:
            s[9]= "Replacement of output information"

        results, corrects['d2'] = self.check_equal(results, corrects['d2'])

        # 出力の一致を確認
        self.assertEqual(len(results), len(corrects['d2']))
        for result,correct in zip(results, corrects['d2']):
            self.assertEqual(len(result), len(correct))
            
            self.assertIsNotNone(result[0])
            self.assertEqual(result[1], correct[1])
            self.assertEqual(result[2], correct[2])
            self.assertEqual(result[3], correct[3])
            self.assertEqual(result[4], correct[4])
            self.assertEqual(result[5], correct[5])
            self.assertEqual(result[6], correct[6])
            # self.assertEqual(result[7], correct[7])
            self.assertEqual(result[8], correct[8])
            self.assertIsNotNone(result[9])

        # 後片付け
        lasts['d2'].delete()

    # @unittest.skip
    def test_case_two_assert(self):
        """
        内容が3行目以降違う２つの入力に対して、assert_commandを一つ配置したフローの島を2つ用意し、同時実行、
        出力で、入力データが3行目以降不一致という判定が出ることを期待する。
        エラー判定はfalse
        """
        flow_json = copy.deepcopy(self.double_assert_json)
        flow_json['nodes'].append(self.create_data_dst_node('d1'))
        flow_json['nodes'].append(self.create_data_dst_node('d2'))

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # 正解データ内のuuid, タイムスタンプはダミー、テスト実行時には、毎回変動するので、出力がされているかどうかのみ確認する
        corrects = {
        'd1':[
            ['00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','d1','False','False','3','A,2,20','B,1,30','False','0000-00-00 00:00:00.000000+00:00'],
            ['00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','d1','False','False','4','B,1,30','','False','0000-00-00 00:00:00.000000+00:00'],
            ['00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','d1','False','False','5','B,3,40','','False','0000-00-00 00:00:00.000000+00:00'],
            ['00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','d1','False','False','6','B,1,50','','False','0000-00-00 00:00:00.000000+00:00']
        ],
        'd2': [
            ['00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','d2','False','False','3','A,2,20','B,1,30','False','0000-00-00 00:00:00.000000+00:00'],
            ['00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','d2','False','False','4','B,1,30','','False','0000-00-00 00:00:00.000000+00:00'],
            ['00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','d2','False','False','5','B,3,40','','False','0000-00-00 00:00:00.000000+00:00'],
            ['00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','d2','False','False','6','B,1,50','','False','0000-00-00 00:00:00.000000+00:00']
        ]}
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.exists(lasts['d1'].uuid))
        self.assertIsNotNone(self.factory.data.exists(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        results = self.get_frame_by_uuid(lasts['d1'].uuid)
        results2 = self.get_frame_by_uuid(lasts['d2'].uuid)

        # 出力の一致を確認
        self.assertEqual(len(results), len(corrects['d1']))
        for result,correct in zip(results, corrects['d1']):
            self.assertEqual(len(result), len(correct))
            
            self.assertIsNotNone(result[0])
            self.assertEqual(result[1], correct[1])
            self.assertEqual(result[2], correct[2])
            self.assertEqual(result[3], correct[3])
            self.assertEqual(result[4], correct[4])
            self.assertEqual(result[5], correct[5])
            self.assertEqual(result[6], correct[6])
            self.assertEqual(result[7], correct[7])
            self.assertEqual(result[8], correct[8])
            self.assertIsNotNone(result[9])

        self.assertEqual(len(results), len(corrects['d2']))
        for result,correct in zip(results2, corrects['d2']):
            self.assertEqual(len(result), len(correct))
            
            self.assertIsNotNone(result[0])
            self.assertEqual(result[1], correct[1])
            self.assertEqual(result[2], correct[2])
            self.assertEqual(result[3], correct[3])
            self.assertEqual(result[4], correct[4])
            self.assertEqual(result[5], correct[5])
            self.assertEqual(result[6], correct[6])
            self.assertEqual(result[7], correct[7])
            self.assertEqual(result[8], correct[8])
            self.assertIsNotNone(result[9])

        # 後片付け
        lasts['d1'].delete()
        lasts['d2'].delete()


    # @unittest.skip
    def test_one_side_error_assert(self):
        """
        ２つの入力のうち、片方がassert_command以前のノードでエラーが発生するフローを実行、
        出力で、入力データが全行不一致という判定が出ることを期待する。
        エラー判定はtrue
        """
        flow_json = copy.deepcopy(self.one_side_error_json)
        flow_json['nodes'].append(self.create_data_dst_node('d2'))

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # 正解データ内のuuid, タイムスタンプはダミー、テスト実行時には、毎回変動するので、出力がされているかどうかのみ確認する
        corrects = {'d2': [
            ['00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','d2','False','True','1','顧客,数量,金額','MCMDError:#ERROR# parameter a= is mandatory (kgNewnumber); kgNewnumber;  OUT=0; 2020/09/13 16:54:32; 2020/09/13 16:54:32','False','0000-00-00 00:00:00.000000+00:00'],
            ['00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','d2','False','True','2','A,1,10','','False','0000-00-00 00:00:00.000000+00:00'],
            ['00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','d2','False','True','3','A,2,20','','False','0000-00-00 00:00:00.000000+00:00'],
            ['00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','d2','False','True','4','B,1,30','','False','0000-00-00 00:00:00.000000+00:00'],
            ['00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','d2','False','True','5','B,3,40','','False','0000-00-00 00:00:00.000000+00:00'],
            ['00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','d2','False','True','6','B,1,50','','False','0000-00-00 00:00:00.000000+00:00']
        ]}
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.exists(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        results = self.get_frame_by_uuid(lasts['d2'].uuid)

        results, corrects['d2'] = self.check_equal(results, corrects['d2'])

        # 出力の一致を確認
        self.assertEqual(len(results), len(corrects['d2']))
        for result,correct in zip(results, corrects['d2']):
            self.assertEqual(len(result), len(correct))
            
            self.assertIsNotNone(result[0])
            self.assertEqual(result[1], correct[1])
            self.assertEqual(result[2], correct[2])
            self.assertEqual(result[3], correct[3])
            self.assertEqual(result[4], correct[4])
            self.assertEqual(result[5], correct[5])
            self.assertEqual(result[6], correct[6])
            self.assertEqual(result[7], correct[7])
            self.assertEqual(result[8], correct[8])
            self.assertIsNotNone(result[9])

        # 後片付け
        lasts['d2'].delete()


    # @unittest.skip
    def test_same_both_error_assert(self):
        """
        内容がどちらも同じエラーを出す２つの入力に対して、assert_commandを一つ配置し実行、
        出力で、入力データが一致という判定が出ることを期待する。
        エラー判定はtrue
        """
        flow_json = copy.deepcopy(self.both_same_error_json)
        flow_json['nodes'].append(self.create_data_dst_node('d2'))

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # 正解データ内のuuid, タイムスタンプはダミー、テスト実行時には、毎回変動するので、出力がされているかどうかのみ確認する
        corrects = {
            'd2': [
                ['fa95ec62-5141-44fb-b4b0-f680139b4adc','/ライブラリ/テストフロ','d2','True','True','','','','False','0000-00-00 00:00:00.000000+00:00']
        ]}
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.exists(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        results = self.get_frame_by_uuid(lasts['d2'].uuid)

        # 出力の一致を確認
        self.assertEqual(len(results), len(corrects['d2']))
        for result,correct in zip(results, corrects['d2']):
            self.assertEqual(len(result), len(correct))
            
            self.assertIsNotNone(result[0])
            self.assertEqual(result[1], correct[1])
            self.assertEqual(result[2], correct[2])
            self.assertEqual(result[3], correct[3])
            self.assertEqual(result[4], correct[4])
            self.assertEqual(result[5], correct[5])
            self.assertEqual(result[6], correct[6])
            self.assertEqual(result[7], correct[7])
            self.assertEqual(result[8], correct[8])
            self.assertIsNotNone(result[9])

        # 後片付け
        lasts['d2'].delete()
    
    # @unittest.skip
    def test_both_error_assert(self):
        """
        内容が違うエラーを出す２つの入力に対して、assert_commandを一つ配置し実行、
        出力で、入力データが不一致という判定が出ることを期待する。
        エラー判定はtrue
        """
        flow_json = copy.deepcopy(self.both_error_json)
        flow_json['nodes'].append(self.create_data_dst_node('d2'))

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # 正解データ内のuuid, タイムスタンプはダミー、テスト実行時には、毎回変動するので、出力がされているかどうかのみ確認する
        corrects = {'d2': [
            ['cb4cf7ad-44de-4df9-a7b7-a4d5a4201d81','/ライブラリ/テストフロ','d2','False','True','None','MCMDError:#ERROR# parameter a= is mandatory (kgNewnumber); kgNewnumber;  OUT=0; 2020/09/12 11:24:50; 2020/09/12 11:24:50','MCMDError:#ERROR# parameter a= is mandatory (kgnewrand); kgnewrand;  OUT=0; 2020/09/12 11:24:50; 2020/09/12 11:24:50','False','0000-00-00 00:00:00.000000+00:00']
        ]}
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.exists(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        results = self.get_frame_by_uuid(lasts['d2'].uuid)

        results, corrects['d2'] = self.check_equal(results, corrects['d2'])

        # 出力の一致を確認
        self.assertEqual(len(results), len(corrects['d2']))
        for result,correct in zip(results, corrects['d2']):
            self.assertEqual(len(result), len(correct))

            self.assertIsNotNone(result[0])
            self.assertEqual(result[1], correct[1])
            self.assertEqual(result[2], correct[2])
            self.assertEqual(result[3], correct[3])
            self.assertEqual(result[4], correct[4])
            self.assertEqual(result[5], correct[5])
            self.assertEqual(result[6], correct[6])
            self.assertEqual(result[7], correct[7])
            self.assertEqual(result[8], correct[8])
            self.assertIsNotNone(result[9])

        # 後片付け
        lasts['d2'].delete()

    # @unittest.skip
    def test_dlimit_overred_assert(self):
        """
        assert_commandの処理の途中で出力不一致行の検出上限を超えた時、検出処理を途中で辞め、
        出力でその旨を通知することと、テスト失敗の判定が出ることを期待する。
        エラー判定はfalse     
        """
        flow_json = copy.deepcopy(self.dlimit_overred_json)
        flow_json['nodes'].append(self.create_data_dst_node('d2'))

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # # 正解データ内のuuid, タイムスタンプはダミー、テスト実行時には、毎回変動するので、出力がされているかどうかのみ確認する
        corrects = {'d2': [
            ['564fb0a7-00bb-416f-9ccc-4e7a056d7564', '/ライブラリ/テストフロ', 'd2', 'False', 'False', '1', 'column1', 'column2', 'True', '2021-01-12 17:38:01'],
            ['564fb0a7-00bb-416f-9ccc-4e7a056d7564', '/ライブラリ/テストフロ', 'd2', 'False', 'False', '2', '1', '100', 'True', '2021-01-12 17:38:01'],
            ['564fb0a7-00bb-416f-9ccc-4e7a056d7564', '/ライブラリ/テストフロ', 'd2', 'False', 'False', '3', '2', '101', 'True', '2021-01-12 17:38:01'],
            ['564fb0a7-00bb-416f-9ccc-4e7a056d7564', '/ライブラリ/テストフロ', 'd2', 'False', 'False', '4', '3', '102', 'True', '2021-01-12 17:38:01'],
            ['564fb0a7-00bb-416f-9ccc-4e7a056d7564', '/ライブラリ/テストフロ', 'd2', 'False', 'False', '5', '4', '103', 'True', '2021-01-12 17:38:01'],
            ['564fb0a7-00bb-416f-9ccc-4e7a056d7564', '/ライブラリ/テストフロ', 'd2', 'False', 'False', '6', '5', '104', 'True', '2021-01-12 17:38:01'],
            ['564fb0a7-00bb-416f-9ccc-4e7a056d7564', '/ライブラリ/テストフロ', 'd2', 'False', 'False', '7', '6', '105', 'True', '2021-01-12 17:38:01'],
            ['564fb0a7-00bb-416f-9ccc-4e7a056d7564', '/ライブラリ/テストフロ', 'd2', 'False', 'False', '8', '7', '106', 'True', '2021-01-12 17:38:01'],
            ['564fb0a7-00bb-416f-9ccc-4e7a056d7564', '/ライブラリ/テストフロ', 'd2', 'False', 'False', '9', '8', '107', 'True', '2021-01-12 17:38:01'],
            ['564fb0a7-00bb-416f-9ccc-4e7a056d7564', '/ライブラリ/テストフロ', 'd2', 'False', 'False', '10', '9', '108', 'True', '2021-01-12 17:38:01'],
            ['564fb0a7-00bb-416f-9ccc-4e7a056d7564', '/ライブラリ/テストフロ', 'd2', 'False', 'False', '11', '10', '109', 'True', '2021-01-12 17:38:01']
        ]}
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.exists(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        results = self.get_frame_by_uuid(lasts['d2'].uuid)

        results, corrects['d2'] = self.check_equal(results, corrects['d2'])

        # 出力の一致を確認
        self.assertEqual(len(results), len(corrects['d2']))
        for result,correct in zip(results, corrects['d2']):
            self.assertEqual(len(result), len(correct))

            self.assertIsNotNone(result[0])
            self.assertEqual(result[1], correct[1])
            self.assertEqual(result[2], correct[2])
            self.assertEqual(result[3], correct[3])
            self.assertEqual(result[4], correct[4])
            self.assertEqual(result[5], correct[5])
            self.assertEqual(result[6], correct[6])
            self.assertEqual(result[7], correct[7])
            self.assertEqual(result[8], correct[8])
            self.assertIsNotNone(result[9])

        # 後片付け
        lasts['d2'].delete()



    def check_equal(self, result, correct):
        """
        MCommandが出すエラーにあるタイムスタンプ部位を取り除く
        """
        # TODO:
        # mcmd_error_infoのMCMDErrorにタイムスタンプを取り除く処理を描こうとしたが、
        # mコマンドにもエラーメッセージでタイムスタンプが出ないものがあり対応に時間が取られるため、後回し

        for row in result:
            if row[6].find('MCMDError') != -1:
                row[6] = row[6][:-42]

            if row[7].find('MCMDError') != -1:
                row[7] = row[7][:-42]

        for row in correct:
            if row[6].find('MCMDError') != -1:
                row[6] = row[6][:-42]

            if row[7].find('MCMDError') != -1:
                row[7] = row[7][:-42]

        return result, correct


def convert_from_activity(lasts):
    """
    execute()の戻り値から
    pointのidとframeのDictに置き換える
    """
    from kskp.store import Activity
    # Activityを取得して返り値とする
    for point_id, datum in lasts.items():
        if isinstance(datum, Activity):
            return {point.id : frame for point, frame in datum.outs}

            