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
                'uuid': 'd8b65fa1-9960-4955-b6b2-74ab490ec3c4',
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
                'uuid': '02f77dc2-e319-4fda-bbc5-0bb0f14501b4',
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

    def test_validate_error_port_id(self):
        """
        ポートid属性に不正な形式の値が設定されたらエラーになること
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
                        # invalid
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

