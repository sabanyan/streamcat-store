import os
import unittest
import json
import uuid
import pprint
from pathlib import Path
from datetime import datetime

from kskp.store import Library, Flow, FlowData
from kskp.engine import execute, FlowJsonLink, FlowLinkContext
from .test_case_base import TestCaseBase

class CommandTest(TestCaseBase):
    
    @classmethod
    def setUpClass(cls):
        # 親クラスのsetUpClass()を実行する
        TestCaseBase.setUpClass()

        # テスト用テーブルを作成する
        from kskp.store import engine
        from sqlalchemy import DDL
        create_table = """
        CREATE TABLE IF NOT EXISTS {schema}.test (
            id    integer,
            char1 char(4),
            char2 varchar(64),
            date  date,
            stamp timestamp,
            len   interval hour to minute
        )
        """.format(schema=os.environ['KSKP_POSTGRESQL_SCHEMA_NAME'])
        engine.execute(DDL(create_table))

        # テスト用データを作成する
        insert_test = """
        INSERT INTO {schema}.test VALUES(1, 'a', 'b', '1900-12-31', '1900-12-31 01:01:01.123456', '1:10:00')
        """.format(schema=os.environ['KSKP_POSTGRESQL_SCHEMA_NAME'])
        engine.execute(insert_test)

    @classmethod
    def tearDownClass(cls):
        # 親クラスのtearDownClass()を実行する
        TestCaseBase.tearDownClass()


    flow_json = {
        "projectId": None, 
        "label": "abc", 
        "ports": [
        [], 
        []
        ], 
        "params": [], 
        "description": "", 
        "creator": "開発用", 
        "createdAt": "2019-09-18 15:04:24", 
        "nodes": [
            {
                "invalid": {}, 
                "error": {}, 
                "id": "d", 
                "type": "frame", 
                "label": "d", 
                "uuid": None, 
                "makeCache": False, 
                "cacheCreatedAt": None, 
                "dataSource": "csv"
            }, 
            {
                "invalid": {}, 
                "error": {}, 
                "id": "c", 
                "type": "command", 
                "label": "RDBからの読み込み", 
                "srcs": {}, 
                "srcsOrder": [], 
                "dsts": {
                "o": "d"
                }, 
                "args": {
                "dbms": "postgresql", 
                "hostname": "kskp.cr4gfi5zl5xm.ap-northeast-1.rds.amazonaws.com", 
                "port": "5432", 
                "database": "kskp",
                "user_id": "kskp", 
                "password": "J2-pH|%B",
                "schema_name" : os.environ['KSKP_POSTGRESQL_SCHEMA_NAME'],
                "table_name": "test"
                }, 
                "commandId": "db_loader"
            }
        ]
    }

    @unittest.skip('最新のDbLoader/Saverの実装に合わせる予定')
    def test_db_loader_command(self):
        """
        DBローダーコマンドが正しくデータを取得できること
        """
        flow_data = FlowData(self.flow_json)
        flow = Flow(None, self.flow_json['label'], flow_data)
        flow_link = FlowJsonLink(flow, FlowLinkContext())
        lasts = execute(flow_link, {}, {})

        correct = {'d': [['1', 'a   ', 'b', '1900-12-31', '1900-12-31 01:01:01.123456', '1:10:00']]}
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = get_frame_by_uuid(lasts['d'].uuid)
        self.assertEqual(result, correct['d'])

        # 後片付け
        Library.delete_frame(lasts['d'].uuid)

    flow_json2 = {
        "projectId": None, 
        "label": "abc", 
        "ports": [
        [], 
        []
        ], 
        "params": [], 
        "description": "", 
        "creator": "開発用", 
        "createdAt": "2019-09-18 15:04:24", 
        "nodes": [
            {
                "invalid": {}, 
                "error": {}, 
                "id": "d", 
                "type": "frame", 
                "label": "d", 
                "uuid": None, 
                "makeCache": False, 
                "cacheCreatedAt": None, 
                "dataSource": "csv"
            }, 
            {
                "invalid": {}, 
                "error": {}, 
                "id": "c", 
                "type": "command", 
                "label": "DBからの読み込み", 
                "srcs": {}, 
                "srcsOrder": [], 
                "dsts": {
                "o": "d"
                }, 
                "args": {
                "dbms": "postgresql", 
                "hostname": "aaa.bbb.ccc.ddd", 
                "port": "5432", 
                "database": "kskp",
                "user_id": "kskp", 
                "password": "J2-pH|%B",
                "schema_name" : os.environ['KSKP_POSTGRESQL_SCHEMA_NAME'],
                "table_name": "test"
                }, 
                "commandId": "db_loader"
            }
        ]
    }

    @unittest.skip('最新のDbLoader/Saverの実装に合わせる予定')
    def test_not_connected_to_db(self):
        """
        DBに接続できない場合は例外を送出すること
        """
        flow_data2 = FlowData(self.flow_json2)
        flow = Flow(None, self.flow_json2['label'], flow_data2)
        flow_link = FlowJsonLink(flow, FlowLinkContext())

        from sqlalchemy import exc
        with self.assertRaises(exc.OperationalError):
            lasts = execute(flow_link, {}, {})

# Helpler
def get_frame_by_uuid(uuid, header=True):
    """
    指定したuuidのframeを取得する
    """
    import csv
    result = []
    frame = Library.load_frame(uuid)
    with open(frame.path, 'r') as f:
        rows = csv.reader(f)
        if header:
            header = next(rows)
        for row in rows:
            result.append(row)

    return result
