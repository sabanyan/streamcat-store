import io
import unittest
import pprint
from datetime import datetime
from jsonschema import ValidationError
from kskp.store import FlowData
from .test_case_base import TestCaseBase

class FlowJsonTest(TestCaseBase):
    """
    フローJSONの書式の検証機能をテストする
    """

    def test_validate_all_syntax(self):
        """
        全ての文法要素を含んだフローJSONを検証できること
        """
        # ルートデータストアを取得する
        root = self.factory.data.load_root()
        # 参照先フレームを作成する
        frame = root.create_frame('CSV', io.BytesIO(b''))
        frame.save()
        # 参照先サブフローを作成する
        sub_flow = root.create_flow('サブフロー', FlowData({}))
        sub_flow.save()
        # (おそらく)全ての文法要素を含んだフローJSON
        flow_json1 ={
            'label': 'share',
            'nodes': [
                {
                'id': 'd',
                'size': {
                    'width': 38,
                    'height': 38
                },
                'type': 'frame',
                'uuid': frame.uuid,
                'error': {},
                'label': 'testData',
                'invalid': {},
                'position': {
                    'x': 99,
                    'y': 119
                },
                'makeCache': False,
                'dataSource': 'csv',
                'cacheCreatedAt': None
                },
                {
                'id': 'd1',
                'size': {
                    'width': 38,
                    'height': 38
                },
                'type': 'frame',
                'uuid': None,
                'error': {},
                'label': 'd1',
                'invalid': {},
                'position': {
                    'x': 99,
                    'y': 283
                },
                'makeCache': False,
                'dataSource': 'csv',
                'cacheCreatedAt': None
                },
                {
                'id': 'c1',
                'args': {},
                'dsts': {
                    'o': 'd1'
                },
                'size': {
                    'width': 38,
                    'height': 38
                },
                'srcs': {
                    'i': 'd'
                },
                'type': 'command',
                'error': {},
                'label': 'c1',
                'invalid': {},
                'position': {
                    'x': 99,
                    'y': 201
                },
                'commandId': 'mcut',
                'srcsOrder': [
                    'i'
                ]
                },
                {
                'id': 'd2',
                'size': {
                    'width': 38,
                    'height': 38
                },
                'type': 'frame',
                'uuid': None,
                'error': {},
                'label': 'd2',
                'invalid': {},
                'position': {
                    'x': 233,
                    'y': 201
                },
                'makeCache': False,
                'dataSource': 'csv',
                'cacheCreatedAt': None
                },
                {
                'id': 'f1',
                'args': {},
                'dsts': {
                    'd1': 'd2'
                },
                'size': {
                    'width': 38,
                    'height': 38
                },
                'srcs': {},
                'type': 'flow',
                'uuid': sub_flow.uuid,
                'error': {},
                'label': 'f1',
                'invalid': {},
                'position': {
                    'x': 233,
                    'y': 119
                },
                'srcsOrder': []
                },
                {
                'id': 'n1',
                'size': {
                    'width': 88,
                    'height': 25
                },
                'type': 'note',
                'color': 'green',
                'error': {},
                'label': 'n1',
                'title': '新しいメモ',
                'content': '新しいメモ',
                'invalid': {},
                'fontSize': 10,
                'position': {
                    'x': 334,
                    'y': 122
                }
                },
                {
                'id': 'd3',
                'size': {
                    'width': 38,
                    'height': 38
                },
                'type': 'frame',
                'uuid': None,
                'error': {},
                'label': 'd3',
                'invalid': {},
                'position': {
                    'x': 166,
                    'y': 365
                },
                'makeCache': False,
                'dataSource': 'csv',
                'cacheCreatedAt': None
                },
                {
                'id': 'd4',
                'size': {
                    'width': 38,
                    'height': 38
                },
                'type': 'frame',
                'uuid': None,
                'error': {},
                'label': 'd4',
                'invalid': {},
                'position': {
                    'x': 300,
                    'y': 365
                },
                'makeCache': False,
                'dataSource': 'csv',
                'cacheCreatedAt': None
                },
                {
                'id': 'c2',
                'args': {
                    'from': '0',
                    'size': '1'
                },
                'dsts': {
                    'o': 'd3',
                    'u': 'd4'
                },
                'size': {
                    'width': 38,
                    'height': 38
                },
                'srcs': {
                    'i': 'd2'
                },
                'type': 'command',
                'error': {},
                'label': 'c2',
                'invalid': {},
                'position': {
                    'x': 233,
                    'y': 283
                },
                'commandId': 'mbest',
                'srcsOrder': [
                    'i'
                ]
                }
            ],
            'ports': [
                [
                {
                    'type': 'frame',
                    'label': 'd1',
                    'nodeId': 'd1'
                }
                ],
                [
                {
                    'type': 'frame',
                    'label': 'd2',
                    'nodeId': 'd2'
                }
                ]
            ],
            'params': [
                {
                'name': 'new_param1',
                'type': 'string',
                'uuid': '9a289268-2267-443e-8ef8-2aeb774a0be2',
                'label': 'new_param1'
                }
            ],
            'creator': 'ユーザー管理者',
            'createdAt': '2021-01-12 10:28:31',
            'projectId': None,
            'description': '説明です'
        }
        # ルートデータストアの直下にフローを作成する
        flow = root.create_flow('ALLフロー', FlowData(flow_json1))
        # フローJSONの検証エラーが送出されないこと
        flow.save()
        # フローを削除する
        flow.delete()

    def test_validate_sample(self):
        """
        サンプルフローJSONを検証する
        """
        # ルートデータストアを取得する
        root = self.factory.data.load_root()
        # 参照先フレームを作成する
        frame1 = root.create_frame('CSV1', io.BytesIO(b''))
        frame1.save()
        frame2 = root.create_frame('CSV2', io.BytesIO(b''))
        frame2.save()
        frame3 = root.create_frame('CSV3', io.BytesIO(b''))
        frame3.save()
        frame4 = root.create_frame('CSV4', io.BytesIO(b''))
        frame4.save()
        # 参照先サブフローを作成する
        sub_flow1 = root.create_flow('サブフロー1', FlowData({}))
        sub_flow1.save()
        sub_flow2 = root.create_flow('サブフロー2', FlowData({}))
        sub_flow2.save()
        sub_flow3 = root.create_flow('サブフロー3', FlowData({}))
        sub_flow3.save()
        sub_flow4 = root.create_flow('サブフロー4', FlowData({}))
        sub_flow4.save()
        sub_flow5 = root.create_flow('サブフロー5', FlowData({}))
        sub_flow5.save()

        # サンプルフローJSON
        flow_json ={
            "label": "データセットv0.2.1_10分割＆R2TAG21phase単位分割&R2TAG9変化点分割_集計v01",
            "nodes": [
                {
                    "id": "d",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": frame1.uuid,
                    "error": {},
                    "label": "RESULT",
                    "invalid": {},
                    "position": {
                        "x": 186,
                        "y": 564
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "d1",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": frame2.uuid,
                    "error": {},
                    "label": "R2_SER4-11 終了時刻13:48:59 全体処理時間1秒",
                    "invalid": {},
                    "position": {
                        "x": 1017,
                        "y": 316
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "d2",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": frame3.uuid,
                    "error": {},
                    "label": "R1_SER4-11 終了時刻13:48:59 全体処理時間1秒",
                    "invalid": {},
                    "position": {
                        "x": 660,
                        "y": 326
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "d4",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "d4",
                    "invalid": {},
                    "position": {
                        "x": 1120,
                        "y": 705
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "f1",
                    "args": {},
                    "dsts": {
                        "d1": "d4"
                    },
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "srcs": {
                        "d": "d14"
                    },
                    "type": "flow",
                    "uuid": sub_flow1.uuid,
                    "error": {},
                    "label": "__R2TAG9波形分割__",
                    "invalid": {},
                    "position": {
                        "x": 1124,
                        "y": 620
                    },
                    "srcsOrder": [
                        "d"
                    ]
                },
                {
                    "id": "d3",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "d3",
                    "invalid": {},
                    "position": {
                        "x": 661,
                        "y": 683
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "c1",
                    "args": {
                        "F": "0",
                        "f": "TIME:bucket",
                        "k": "LOT",
                        "n": "3",
                        "rng": True,
                        "bufcount": 10
                    },
                    "dsts": {
                        "o": "d3"
                    },
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "srcs": {
                        "i": "d15"
                    },
                    "type": "command",
                    "error": {},
                    "label": "一次元均等化バケット分割",
                    "invalid": {},
                    "position": {
                        "x": 659,
                        "y": 613
                    },
                    "commandId": "mbucket",
                    "srcsOrder": [
                        "i"
                    ]
                },
                {
                    "id": "d9",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "d9",
                    "invalid": {},
                    "position": {
                        "x": 664.5,
                        "y": 877.75
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "f2",
                    "args": {
                        "LOTの項目名": "LOT",
                        "区分化キー項目名": "bucket",
                        "集計対象の項目名": "R1*",
                        "区分化キー種類(列名作成時の接頭辞)": "B"
                    },
                    "dsts": {
                        "d2": "d9"
                    },
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "srcs": {
                        "d3": "d3"
                    },
                    "type": "flow",
                    "uuid": sub_flow2.uuid,
                    "error": {},
                    "label": "データセットv0.1_集計",
                    "invalid": {},
                    "position": {
                        "x": 663,
                        "y": 800
                    },
                    "srcsOrder": [
                        "d3"
                    ]
                },
                {
                    "id": "d5",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "d5",
                    "invalid": {},
                    "position": {
                        "x": 1121,
                        "y": 880
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "f3",
                    "args": {
                        "LOTの項目名": "LOT",
                        "区分化キー項目名": "phaseNo",
                        "集計対象の項目名": "R2*",
                        "区分化キー種類(列名作成時の接頭辞)": "ph"
                    },
                    "dsts": {
                        "d2": "d5"
                    },
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "srcs": {
                        "d3": "d4"
                    },
                    "type": "flow",
                    "uuid": sub_flow2.uuid,
                    "error": {},
                    "label": "データセットv0.1_集計",
                    "invalid": {},
                    "position": {
                        "x": 1122,
                        "y": 788
                    },
                    "srcsOrder": [
                        "d3"
                    ]
                },
                {
                    "id": "d6",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "d6",
                    "invalid": {},
                    "position": {
                        "x": 950,
                        "y": 698
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "c2",
                    "args": {
                        "F": "0",
                        "f": "TIME:bucket",
                        "k": "LOT",
                        "n": "3",
                        "rng": True,
                        "bufcount": 10
                    },
                    "dsts": {
                        "o": "d6"
                    },
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "srcs": {
                        "i": "d14"
                    },
                    "type": "command",
                    "error": {},
                    "label": "一次元均等化バケット分割",
                    "invalid": {},
                    "position": {
                        "x": 950,
                        "y": 616
                    },
                    "commandId": "mbucket",
                    "srcsOrder": [
                        "i"
                    ]
                },
                {
                    "id": "d7",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "d7",
                    "invalid": {},
                    "position": {
                        "x": 950,
                        "y": 874
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "f4",
                    "args": {
                        "LOTの項目名": "LOT",
                        "区分化キー項目名": "bucket",
                        "集計対象の項目名": "R2*",
                        "区分化キー種類(列名作成時の接頭辞)": "B"
                    },
                    "dsts": {
                        "d2": "d7"
                    },
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "srcs": {
                        "d3": "d6"
                    },
                    "type": "flow",
                    "uuid": sub_flow2.uuid,
                    "error": {},
                    "label": "データセットv0.1_集計",
                    "invalid": {},
                    "position": {
                        "x": 950,
                        "y": 792
                    },
                    "srcsOrder": [
                        "d3"
                    ]
                },
                {
                    "id": "d8",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "d8",
                    "invalid": {},
                    "position": {
                        "x": 423.5,
                        "y": 1060.75
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "c3",
                    "args": {
                        "K": "LOT",
                        "k": "LOT",
                        "bufcount": "10"
                    },
                    "dsts": {
                        "o": "d8"
                    },
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "srcs": {
                        "i": "d",
                        "m": "d9"
                    },
                    "type": "command",
                    "error": {},
                    "label": "自然結合",
                    "invalid": {},
                    "position": {
                        "x": 423.5,
                        "y": 978.75
                    },
                    "commandId": "mnjoin",
                    "srcsOrder": [
                        "i",
                        "m"
                    ]
                },
                {
                    "id": "d10",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "d10",
                    "invalid": {},
                    "position": {
                        "x": 563.5,
                        "y": 1153.25
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "c4",
                    "args": {
                        "K": "LOT",
                        "k": "LOT",
                        "bufcount": "10"
                    },
                    "dsts": {
                        "o": "d10"
                    },
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "srcs": {
                        "i": "d8",
                        "m": "d27"
                    },
                    "type": "command",
                    "error": {},
                    "label": "自然結合",
                    "invalid": {},
                    "position": {
                        "x": 561.5,
                        "y": 1069.25
                    },
                    "commandId": "mnjoin",
                    "srcsOrder": [
                        "i",
                        "m"
                    ]
                },
                {
                    "id": "d11",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "d11",
                    "invalid": {},
                    "position": {
                        "x": 665,
                        "y": 1231
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "c5",
                    "args": {
                        "K": "LOT",
                        "k": "LOT",
                        "bufcount": "10"
                    },
                    "dsts": {
                        "o": "d11"
                    },
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "srcs": {
                        "i": "d10",
                        "m": "d7"
                    },
                    "type": "command",
                    "error": {},
                    "label": "自然結合",
                    "invalid": {},
                    "position": {
                        "x": 665,
                        "y": 1161
                    },
                    "commandId": "mnjoin",
                    "srcsOrder": [
                        "i",
                        "m"
                    ]
                },
                {
                    "id": "d12",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "データセットv0.2",
                    "invalid": {},
                    "position": {
                        "x": 765,
                        "y": 1863.3333333333335
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "c6",
                    "args": {
                        "q": True
                    },
                    "dsts": {
                        "o": "d12"
                    },
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "srcs": {
                        "i": "d26"
                    },
                    "type": "command",
                    "error": {},
                    "label": "項目名の変更",
                    "invalid": {},
                    "position": {
                        "x": 762,
                        "y": 1785.3333333333335
                    },
                    "commandId": "mfldname",
                    "srcsOrder": [
                        "i"
                    ]
                },
                {
                    "id": "d14",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "d14",
                    "invalid": {},
                    "position": {
                        "x": 1017,
                        "y": 501
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "c7",
                    "args": {
                        "f": "R2TAG1,R2TAG2,R2TAG3,R2TAG4,R2TAG5,R2TAG6,R2TAG18,R2TAG33,R2TAG37,R2TAG52,R2TAG53,R2TAG54",
                        "r": True
                    },
                    "dsts": {
                        "o": "d14"
                    },
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "srcs": {
                        "i": "d1"
                    },
                    "type": "command",
                    "error": {},
                    "label": "項目の選択",
                    "invalid": {},
                    "position": {
                        "x": 1018,
                        "y": 424
                    },
                    "commandId": "mcut",
                    "srcsOrder": [
                        "i"
                    ]
                },
                {
                    "id": "d15",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "d15",
                    "invalid": {},
                    "position": {
                        "x": 660,
                        "y": 503
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "c8",
                    "args": {
                        "f": "R1TAG2,R1TAG6,R1TAG30,R1TAG32,R1TAG38",
                        "r": True
                    },
                    "dsts": {
                        "o": "d15"
                    },
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "srcs": {
                        "i": "d2"
                    },
                    "type": "command",
                    "error": {},
                    "label": "項目の選択",
                    "invalid": {},
                    "position": {
                        "x": 658,
                        "y": 422
                    },
                    "commandId": "mcut",
                    "srcsOrder": [
                        "i"
                    ]
                },
                {
                    "id": "d26",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "d26",
                    "invalid": {},
                    "position": {
                        "x": 762.3333333333334,
                        "y": 1720.666666666667
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "f6",
                    "args": {
                        "グループの項目名": "LOT"
                    },
                    "dsts": {
                        "d1": "d26"
                    },
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "srcs": {
                        "d": "d19"
                    },
                    "type": "flow",
                    "uuid": sub_flow3.uuid,
                    "error": {},
                    "label": "__NULL値あり列の削除__",
                    "invalid": {},
                    "position": {
                        "x": 762.6666666666666,
                        "y": 1630.9999999999998
                    },
                    "srcsOrder": [
                        "d"
                    ]
                },
                {
                    "id": "n4",
                    "size": {
                        "width": 165,
                        "height": 25
                    },
                    "type": "note",
                    "color": "green",
                    "error": {},
                    "label": "n4",
                    "title": "注意：キャッシュを作って下さい",
                    "content": "新しいメモ",
                    "invalid": {},
                    "fontSize": 10,
                    "position": {
                        "x": 619.5,
                        "y": 934
                    }
                },
                {
                    "id": "n5",
                    "size": {
                        "width": 175,
                        "height": 25
                    },
                    "type": "note",
                    "color": "green",
                    "error": {},
                    "label": "n5",
                    "title": "注意：キャッシュを作ってください",
                    "content": "新しいメモ",
                    "invalid": {},
                    "fontSize": 10,
                    "position": {
                        "x": 956.5,
                        "y": 938
                    }
                },
                {
                    "id": "n6",
                    "size": {
                        "width": 95,
                        "height": 25
                    },
                    "type": "note",
                    "color": "green",
                    "error": {},
                    "label": "n6",
                    "title": "変動ない列の削除",
                    "content": "新しいメモ",
                    "invalid": {},
                    "fontSize": 10,
                    "position": {
                        "x": 584.5,
                        "y": 390
                    }
                },
                {
                    "id": "n7",
                    "size": {
                        "width": 95,
                        "height": 25
                    },
                    "type": "note",
                    "color": "green",
                    "error": {},
                    "label": "n7",
                    "title": "変動ない列の削除",
                    "content": "新しいメモ",
                    "invalid": {},
                    "fontSize": 10,
                    "position": {
                        "x": 946.5,
                        "y": 384
                    }
                },
                {
                    "id": "d27",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "******",
                    "invalid": {},
                    "position": {
                        "x": 796,
                        "y": 876
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": "2021-03-10 11:01:52"
                },
                {
                    "id": "f7",
                    "args": {
                        "LOTの項目名": "LOT",
                        "集計対象の項目名": "R1*"
                    },
                    "dsts": {
                        "d2": "d27"
                    },
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "srcs": {
                        "d3": "d15"
                    },
                    "type": "flow",
                    "uuid": sub_flow4.uuid,
                    "error": {},
                    "label": "_集計_ロット単位v0.1",
                    "invalid": {},
                    "position": {
                        "x": 800,
                        "y": 805
                    },
                    "srcsOrder": [
                        "d3"
                    ]
                },
                {
                    "id": "d28",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "d28",
                    "invalid": {},
                    "position": {
                        "x": 1328,
                        "y": 876
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "f8",
                    "args": {
                        "LOTの項目名": "LOT",
                        "集計対象の項目名": "R2*"
                    },
                    "dsts": {
                        "d2": "d28"
                    },
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "srcs": {
                        "d3": "d14"
                    },
                    "type": "flow",
                    "uuid": sub_flow4.uuid,
                    "error": {},
                    "label": "_集計_ロット単位v0.1",
                    "invalid": {},
                    "position": {
                        "x": 1327.75,
                        "y": 780.75
                    },
                    "srcsOrder": [
                        "d3"
                    ]
                },
                {
                    "id": "d13",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "d13",
                    "invalid": {},
                    "position": {
                        "x": 789.5,
                        "y": 1319
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "c9",
                    "args": {
                        "K": "LOT",
                        "k": "LOT",
                        "bufcount": "10"
                    },
                    "dsts": {
                        "o": "d13"
                    },
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "srcs": {
                        "i": "d11",
                        "m": "d5"
                    },
                    "type": "command",
                    "error": {},
                    "label": "自然結合",
                    "invalid": {},
                    "position": {
                        "x": 786.5,
                        "y": 1230
                    },
                    "commandId": "mnjoin",
                    "srcsOrder": [
                        "i",
                        "m"
                    ]
                },
                {
                    "id": "d16",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "d16",
                    "invalid": {},
                    "position": {
                        "x": 920.25,
                        "y": 1445
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "c10",
                    "args": {
                        "K": "LOT",
                        "k": "LOT",
                        "bufcount": "10"
                    },
                    "dsts": {
                        "o": "d16"
                    },
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "srcs": {
                        "i": "d13",
                        "m": "d28"
                    },
                    "type": "command",
                    "error": {},
                    "label": "自然結合",
                    "invalid": {},
                    "position": {
                        "x": 913.25,
                        "y": 1328
                    },
                    "commandId": "mnjoin",
                    "srcsOrder": [
                        "i",
                        "m"
                    ]
                },
                {
                    "id": "d17",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "d17",
                    "invalid": {},
                    "position": {
                        "x": 1501.9999999999998,
                        "y": 702.0000000000002
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "f5",
                    "args": {},
                    "dsts": {
                        "d1": "d17"
                    },
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "srcs": {
                        "d": "d14"
                    },
                    "type": "flow",
                    "uuid": sub_flow5.uuid,
                    "error": {},
                    "label": "__要望1:特徴量_R2TAG39_変化点間の区間キー付与__",
                    "invalid": {},
                    "position": {
                        "x": 1505.3333333333328,
                        "y": 616.666666666667
                    },
                    "srcsOrder": [
                        "d"
                    ]
                },
                {
                    "id": "d19",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "d19",
                    "invalid": {},
                    "position": {
                        "x": 1041.1250000000002,
                        "y": 1539.166666666667
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "c11",
                    "args": {
                        "K": "LOT",
                        "k": "LOT",
                        "bufcount": "10"
                    },
                    "dsts": {
                        "o": "d19"
                    },
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "srcs": {
                        "i": "d16",
                        "m": "d20"
                    },
                    "type": "command",
                    "error": {},
                    "label": "自然結合",
                    "invalid": {},
                    "position": {
                        "x": 1041.1249999999998,
                        "y": 1453.8333333333333
                    },
                    "commandId": "mnjoin",
                    "srcsOrder": [
                        "i",
                        "m"
                    ]
                },
                {
                    "id": "d20",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "d20",
                    "invalid": {},
                    "position": {
                        "x": 1499.9999999999998,
                        "y": 867.0000000000002
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "f10",
                    "args": {
                        "LOTの項目名": "LOT",
                        "区分化キー項目名": "R2TAG39変化点間連番",
                        "集計対象の項目名": "R2*",
                        "区分化キー種類(列名作成時の接頭辞)": "CpR2TAG39"
                    },
                    "dsts": {
                        "d2": "d20"
                    },
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "srcs": {
                        "d3": "d17"
                    },
                    "type": "flow",
                    "uuid": sub_flow2.uuid,
                    "error": {},
                    "label": "データセットv0.1_集計",
                    "invalid": {},
                    "position": {
                        "x": 1501.9999999999998,
                        "y": 788.0000000000002
                    },
                    "srcsOrder": [
                        "d3"
                    ]
                },
                {
                    "id": "d18",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": frame4.uuid,
                    "error": {},
                    "label": "Expected Data",
                    "invalid": {},
                    "position": {
                        "x": 905,
                        "y": 1863.5
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "d21",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "d21",
                    "invalid": {},
                    "position": {
                        "x": 835,
                        "y": 2039.4166666666667
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "c12",
                    "args": {
                        "dlimit": 10,
                        "verbose": True
                    },
                    "dsts": {
                        "o": "d21"
                    },
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "srcs": {
                        "i": "d18",
                        "m": "d12"
                    },
                    "type": "command",
                    "error": {},
                    "label": "c12",
                    "invalid": {},
                    "position": {
                        "x": 835,
                        "y": 1957.4166666666667
                    },
                    "commandId": "assert",
                    "srcsOrder": [
                        "i",
                        "m"
                    ]
                }
            ],
            "ports": [
                [],
                [
                    {
                        "type": "frame",
                        "label": "d21",
                        "nodeId": "d21"
                    }
                ]
            ],
            "params": [],
            "creator": "開発用",
            "createdAt": "2020-05-28 11:44:38",
            "projectId": None,
            "description": ""
        }
        # ルートデータストアの直下にフローを作成する
        flow = root.create_flow('フロー', FlowData(flow_json))
        # フローJSONの検証エラーが送出されないこと
        flow.save()
        # フローを削除する
        flow.delete()

    def test_validate_note(self):
        """
        content属性のないNoteノードが検証できること
        """
        # ルートデータストアを取得する
        root = self.factory.data.load_root()
        # サンプルフローJSON
        flow_json = {
            "label": "モノの流れで紐付け",
            "nodes": [
                {
                    "id": "n16",
                    "size": {
                        "width": 323.3,
                        "height": 37
                    },
                    "type": "note",
                    "color": "red",
                    "error": {},
                    "label": "n16",
                    "title": "課題：機械学習用の特徴量生成",
                    "invalid": {},
                    "fontSize": 22,
                    "position": {
                        "x": 599,
                        "y": 1631.5
                    }
                }
            ],
            "ports": [
                [],
                []
            ],
            "params": [],
            "creator": "ユーザー管理者",
            "createdAt": "2020-06-16 15:34:08",
            "projectId": None,
            "description": "【課題】\n  時刻をキーとした観測データから、\n  モノの流れをキーとした\n  分析用データを作成する\n\n【入力データ】\n  時刻をキーとして、\n  異なる工程の観測値が記録されている\n\n【問題点】\n  工程間の移動時間があるため、\n  製造されたモノをキーとした分析ができない\n\n【アプローチ】\n  工程間の標準的な移動時間がある場合、\n  その時間分、各工程ごとに、\n  観測値の時刻をずらし、\n  モノをキーとしたデータに、変形する"
        }    
        # ルートデータストアの直下にフローを作成する
        flow = root.create_flow('フロー', FlowData(flow_json))
        # フローJSONの検証エラーが送出されないこと
        flow.save()
        # フローを削除する
        flow.delete()

    def test_validate_args(self):
        """
        引数の名称に日本語文字列の値が設定できること
        """
        # ルートデータストアを取得する
        root = self.factory.data.load_root()
        # 参照先サブフローを作成する
        sub_flow1 = root.create_flow('サブフロー1', FlowData({}))
        sub_flow1.save()
        # フローJSONを作成する
        flow_json = {
            'projectId': 1,
            'label': 'テストフロー',
            'ports': [[],[]],
            'params': [],
            'description': '',
            'nodes' : [
                {
                    "id": "f8",
                    "args": {
                        "LOTの項目名": "LOT",
                        "集計対象の項目名": "R2*"
                    },
                    "dsts": {
                        "d2": "d28"
                    },
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "srcs": {
                        "d3": "d14"
                    },
                    "type": "flow",
                    "uuid": sub_flow1.uuid,
                    "error": {},
                    "label": "_集計_ロット単位v0.1",
                    "invalid": {},
                    "position": {
                        "x": 1327.75,
                        "y": 780.75
                    },
                    "srcsOrder": [
                        "d3"
                    ]
                }
            ],
            'creator': '羽柴 秀吉',
            'createdAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        # ルートデータストアの直下にフローを作成する
        flow = root.create_flow('フロー', FlowData(flow_json))
        # フローJSONの検証エラーが送出されないこと
        flow.save()
        # フローを削除する
        flow.delete()

    def test_validate_size(self):
        """
        Size属性に小数点付きの数値が指定できること
        """
        # ルートデータストアを取得する
        root = self.factory.data.load_root()
        # フローJSONを作成する
        flow_json = {
            'projectId': 1,
            'label': 'テストフロー',
            'ports': [[],[]],
            'params': [],
            'description': '',
            'nodes' : [
                {
                    "id": "n1",
                    "size": {
                        "width": 115.595703125,
                        "height": 25
                    },
                    "type": "note",
                    "color": "green",
                    "error": {},
                    "label": "n1",
                    "title": "10x70x0.001=700MB",
                    "content": "新しいメモ",
                    "invalid": {},
                    "fontSize": 10,
                    "position": {
                        "x": 164,
                        "y": 380
                    }
                }
            ],
            'creator': '羽柴 秀吉',
            'createdAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        # ルートデータストアの直下にフローを作成する
        flow = root.create_flow('フロー', FlowData(flow_json))
        # フローJSONの検証エラーが送出されないこと
        flow.save()
        # フローを削除する
        flow.delete()

    def test_validate_inner_flow(self):
        """
        type=flowのノードにFlowリテラルが記述できること
        """
        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # プロジェクトを作成する
        project = root.create_project_folder('Mighty mouse')
        project.save()
        project = project.reload()

        # プロジェクトの下にフレームを作成する
        import io
        frame = project.create_frame('Magic mouse', io.BytesIO(b'date,amount\n20100101,2300'))
        frame.uuid = '28f41407-e457-414c-a62c-e9507adb4b97'
        frame.save()

        # フローJSONを作成する
        flow_json =  {
            "label": "Flowのリテラル表記のテスト",
            "ports": [[],[]],
            "params": [],  
            "nodes": [
                {
                    "id": "d", 
                    "label": "testData", 
                    "type": "frame", 
                    "uuid": "28f41407-e457-414c-a62c-e9507adb4b97", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "f1", 
                    "label": "f1", 
                    "type": "flow",
                    "flow": {
                        "label": "リテラル表記のフロー", 
                        "description": "",
                        "projectId": None, 
                        "ports": [
                            [
                                {
                                    "type": "frame", 
                                    "label": "testData", 
                                    "nodeId": "d"
                                }
                            ], 
                            [
                                {
                                    "type": "frame", 
                                    "label": "d1", 
                                    "nodeId": "d1"
                                }
                            ]
                        ], 
                        "params": [], 
                        "nodes": [
                            {
                                "id": "d", 
                                "label": "testData", 
                                "type": "frame", 
                                "uuid": "28f41407-e457-414c-a62c-e9507adb4b97", 
                                "dataSource": "csv"
                            }, 
                            {
                                "id": "c1", 
                                "label": "c1", 
                                "type": "command", 
                                "commandId": "mcombi",
                                "args": {
                                    "a": "date_combi", 
                                    "f": "date", 
                                    "n": "1", 
                                    "s": "date"
                                }, 
                                "srcs": {
                                    "i": "d"
                                }, 
                                "dsts": {
                                    "o": "d1"
                                }
                            },
                            {
                                "id": "d1", 
                                "label": "d1", 
                                "type": "frame", 
                                "dataSource": "csv"
                            }
                        ], 
                        "creator": "ユーザー管理者", 
                        "createdAt": "2021-04-23 14:14:22", 
                    },
                    "args": {}, 
                    "srcs": {
                        "d": "d"
                    },
                    "dsts": {
                        "d1": "d1"
                    }
                },
                {
                    "id": "d1", 
                    "label": "d1", 
                    "type": "frame", 
                    "dataSource": "csv"
                }
            ], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-23 14:16:55"
        }
        # プロジェクトの直下にフローを作成する
        flow = project.create_flow('フロー', FlowData(flow_json))
        # フローJSONの検証エラーが送出されないこと
        flow.save()

        # プロジェクトをほかす
        project.throw_away()
        # ゴミ箱を空にする
        self.factory.data.find_trashcan().trash_all()

    def test_validate_port_id(self):
        """
        ポートid属性に日本語文字列の値が設定できること
        """
        # ルートデータストアを取得する
        root = self.factory.data.load_root()
        # フローJSONを作成する
        flow_json = {
            'projectId': 1,
            'label': 'テストフロー',
            'ports': [
                [
                    {
                        # valid
                        'label': 'ラベルid*',
                        'nodeId': 'd1',
                        'type': 'frame'
                    }
                ],
                []
            ],
            'params': [],
            'description': '',
            'nodes' : [
                {
                    'id': 'invalid_id',
                    'type': 'frame',
                    'dataSource': 'csv',
                    'uuid': None,
                    'label': '入力データ'
                }
            ],
            'creator': '羽柴 秀吉',
            'createdAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        # ルートデータストアの直下にフローを作成する
        flow = root.create_flow('フロー', FlowData(flow_json))
        # フローJSONの検証エラーが送出されないこと
        flow.save()
        # フローを削除する
        flow.delete()

    def test_validate_error_ports(self):
        """
        Ports属性の配列要素は2要素固定である
        """
        # ルートデータストアを取得する
        root = self.factory.data.load_root()
        # フローJSONを作成する
        flow_json = {
            'projectId': 1,
            'label': 'テストフロー',
            # invalid
            'ports': [[]],
            'params': [],
            'description': '',
            'nodes' : [
                {
                    'id': 'i',
                    'type': 'frame',
                    'dataSource': 'csv',
                    'uuid': None,
                    'label': '入力データ'
                }
            ],
            'creator': '織田信長',
            'createdAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        # ルートデータストアの直下にフローを作成する
        flow = root.create_flow('フロー', FlowData(flow_json))
        # フローJSONの検証エラーにより例外が送出されること
        with self.assertRaises(ValidationError):
            flow.save()

    def test_validate_error_uuid(self):
        """
        uuid属性に不正な形式の値が設定されたらエラーになること
        """
        # ルートデータストアを取得する
        root = self.factory.data.load_root()
        # フローJSONを作成する
        flow_json = {
            'projectId': 1,
            'label': 'テストフロー',
            'ports': [[],[]],
            'params': [],
            'description': '',
            'nodes' : [
                {
                    'id': 'i',
                    'type': 'frame',
                    'dataSource': 'csv',
                    # invalid
                    'uuid': 'NULL',
                    'label': '入力データ'
                }
            ],
            'creator': '織田信長',
            'createdAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        # ルートデータストアの直下にフローを作成する
        flow = root.create_flow('フロー', FlowData(flow_json))
        # フローJSONの検証エラーにより例外が送出されること
        with self.assertRaises(ValidationError):
            flow.save()

    def test_validate_error_node_id(self):
        """
        ノードid属性に不正な形式の値が設定されたらエラーになること
        """
        # ルートデータストアを取得する
        root = self.factory.data.load_root()
        # フローJSONを作成する
        flow_json = {
            'projectId': 1,
            'label': 'テストフロー',
            'ports': [[],[]],
            'params': [],
            'description': '',
            'nodes' : [
                {
                    # invalid
                    'id': 'invalid id',
                    'type': 'frame',
                    'dataSource': 'csv',
                    'uuid': None,
                    'label': '入力データ'
                }
            ],
            'creator': '羽柴 秀吉',
            'createdAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        # ルートデータストアの直下にフローを作成する
        flow = root.create_flow('フロー', FlowData(flow_json))
        # フローJSONの検証エラーにより例外が送出されること
        with self.assertRaises(ValidationError):
            flow.save()

    def test_validate_error_position(self):
        """
        ノードのPosition属性に不正な値が設定されたらエラーになること
        """
        # ルートデータストアを取得する
        root = self.factory.data.load_root()
        # フローJSONを作成する
        flow_json = {
            'projectId': None,
            'label': 'テストフロー',
            'ports': [[],[]],
            'params': [],
            'description': '',
            'nodes' : [
                {
                    'id': 'invalid_id',
                    'type': 'frame',
                    'dataSource': 'csv',
                    'uuid': None,
                    'label': '入力データ',
                    'position': {
                        'x': 0,
                        # invalid
                        'y': -20
                    }
                }
            ],
            'creator': '羽柴 秀吉',
            'createdAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        # ルートデータストアの直下にフローを作成する
        flow = root.create_flow('フロー', FlowData(flow_json))
        # フローJSONの検証エラーにより例外が送出されること
        with self.assertRaises(ValidationError):
            flow.save()

    def test_validate_error_inner_flow(self):
        """
        Flowリテラルが参照するUUIDが参照できない場合はエラーになること
        """
        # ルートデータストアを取得する
        root = self.factory.data.load_root()
        # フローJSONを作成する
        flow_json =  {
            "label": "Flowのリテラル表記のテスト",
            "ports": [[],[]],
            "params": [],  
            "nodes": [
                {
                    "id": "d", 
                    "label": "testData", 
                    "type": "frame", 
                    "uuid": "30576973-0dc9-42e1-8fd6-aba699517043", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "f1", 
                    "label": "f1", 
                    "type": "flow",
                    "flow": {
                        "label": "リテラル表記のフロー", 
                        "description": "",
                        "projectId": None, 
                        "ports": [
                            [
                                {
                                    "type": "frame", 
                                    "label": "testData", 
                                    "nodeId": "d"
                                }
                            ], 
                            [
                                {
                                    "type": "frame", 
                                    "label": "d1", 
                                    "nodeId": "d1"
                                }
                            ]
                        ], 
                        "params": [], 
                        "nodes": [
                            {
                                "id": "d", 
                                "label": "testData", 
                                "type": "frame", 
                                "uuid": "30576973-0dc9-42e1-8fd6-aba699517043", 
                                "dataSource": "csv"
                            }, 
                            {
                                "id": "c1", 
                                "label": "c1", 
                                "type": "command", 
                                "commandId": "mcombi",
                                "args": {
                                    "a": "date_combi", 
                                    "f": "date", 
                                    "n": "1", 
                                    "s": "date"
                                }, 
                                "srcs": {
                                    "i": "d"
                                }, 
                                "dsts": {
                                    "o": "d1"
                                }
                            },
                            {
                                "id": "d1", 
                                "label": "d1", 
                                "type": "frame", 
                                "dataSource": "csv"
                            }
                        ], 
                        "creator": "ユーザー管理者", 
                        "createdAt": "2021-04-23 14:14:22", 
                    },
                    "args": {}, 
                    "srcs": {
                        "d": "d"
                    },
                    "dsts": {
                        "d1": "d1"
                    }
                },
                {
                    "id": "d1", 
                    "label": "d1", 
                    "type": "frame", 
                    "dataSource": "csv"
                }
            ], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-23 14:16:55"
        }
        # ルートデータストアの直下にフローを作成する
        flow = root.create_flow('フロー', FlowData(flow_json))
        # フローJSONの検証エラーにより例外が送出されること
        with self.assertRaises(Exception):
            flow.save()
