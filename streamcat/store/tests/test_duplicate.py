import io
import unittest
from streamcat.store import FlowData, DatabaseConn, RemoteFolderConn
from .test_case_base import TestCaseBase

class DuplicateTest(TestCaseBase, unittest.IsolatedAsyncioTestCase):
    """
    複製処理を検証する
    """

    def create_test_flow_json(self, label:str, store_uuid:str):
        return {
            "label": label,
            "nodes": [
                {
                    "id": "d",
                    "type": "frame",
                    "label": "d",
                    "dataSource": "csv"
                },
                {
                    "id": "c",
                    "args": {
                        "I": "1",
                        "S": "1",
                        "a": "A",
                        "l": "10"
                    },
                    "dsts": {
                        "o": "d"
                    },
                    "srcs": {},
                    "type": "command",
                    "label": "c",
                    "commandId": "mnewnumber"
                },
                {
                    "id": "d1",
                    "type": "frame",
                    "label": "d1",
                    "dataSource": "csv"
                },
                {
                    "id": "c1",
                    "args": {
                        "a": "A",
                        "l": "10",
                        "v": "文字列です"
                    },
                    "dsts": {
                        "o": "d1"
                    },
                    "srcs": {},
                    "type": "command",
                    "label": "c1",
                    "commandId": "mnewstr"
                },
                {
                    "id": "d2",
                    "type": "frame",
                    "label": "d2",
                    "dataSource": "csv"
                },
                {
                    "id": "c2",
                    "args": {},
                    "dsts": {
                        "o": "d2"
                    },
                    "srcs": {
                        "*0": "d1",
                        "*1": "d"
                    },
                    "type": "command",
                    "label": "c2",
                    "commandId": "mcat"
                },
                {
                    "id": "o",
                    "args": {},
                    "dsts": {},
                    "flow": {
                        "label": "ライブラリ",
                        "nodes": [
                            {
                                "id": "d",
                                "type": "frame",
                                "label": "d",
                                "dataSource": "csv"
                            },
                            {
                                "id": "s",
                                "type": "store",
                                "uuid": store_uuid,
                                "label": "ライブラリ"
                            },
                            {
                                "id": "c1",
                                "args": {},
                                "dsts": {
                                    "o": "d1"
                                },
                                "srcs": {
                                    "i": "d",
                                    "folder": "s"
                                },
                                "type": "command",
                                "label": "c1",
                                "commandId": "saver"
                            },
                            {
                                "id": "d1",
                                "type": "frame",
                                "label": "d1",
                                "dataSource": "csv"
                            }
                        ],
                        "ports": [
                            [
                                {
                                    "label": "i",
                                    "types": [
                                        "mcmd"
                                    ],
                                    "nodeId": "d"
                                }
                            ],
                            []
                        ],
                        "params": [],
                        "creator": "ユーザー管理者",
                        "createdAt": "2023-06-14 11:18:47",
                        "projectId": None,
                        "description": ""
                    },
                    "srcs": {
                        "i": "d2"
                    },
                    "type": "flow",
                    "label": "ライブラリ",
                    "classification": "data_dest"
                }
            ],
            "ports": [
                [],
                [
                    {
                        "type": "frame",
                        "label": "d2",
                        "nodeId": "d2"
                    }
                ]
            ],
            "params": []
        }

    def assert_auths_equal(self, duplicated_datum_id, datum_id, auths_len=3):
        """
        権限設定の一致を検証する
        """
        auths = self.factory.auth.find_all_by_datum_id(datum_id)
        duplicated_auths = self.factory.auth.find_all_by_datum_id(duplicated_datum_id)
        # 権限設定の数は等しいこと
        self.assertEqual(len(auths), len(duplicated_auths))
        # everyone read,write,exec,own ...
        for i in range(0, auths_len):
            self.assertEqual(duplicated_auths[i].role_id, auths[i].role_id)
            self.assertEqual(duplicated_auths[i].operation, auths[i].operation)
            self.assertEqual(duplicated_auths[i].permission, auths[i].permission)

    async def test_duplicate_flow(self):
        """
        フローが複製できること
        """
        # ルートフォルダを取得する
        root = self.factory3.data.load_root()

        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('河原町')
        project.save()

        # プロジェクトの下にフローを作成する
        flow_json =self.create_test_flow_json('大宮', root.uuid)
        flow = project.create_flow('大宮', FlowData(flow_json))
        flow.save()
        flow.reload()

        # フローを複製する
        duplicated_flow = flow.duplicate('桂')

        # 作成を確定する
        self.factory3.end()

        # 複製したフローを検証する
        self.assertIsNotNone(duplicated_flow.id)
        self.assertNotEqual(duplicated_flow.id, flow.id)
        self.assertEqual(duplicated_flow.parent_id, project.id)
        self.assertIsNotNone(duplicated_flow.uuid)
        self.assertNotEqual(duplicated_flow.uuid, flow.uuid)
        self.assertIsNone(duplicated_flow.path)
        self.assertEqual(duplicated_flow.type, 'flow')
        self.assertEqual(duplicated_flow.label, '桂')
        self.assertEqual(duplicated_flow.creator, self.USER3)
        self.assertEqual(duplicated_flow.modifier, self.USER3)
        self.assertIsNotNone(duplicated_flow.created_at)
        self.assertIsNotNone(duplicated_flow.modified_at)
        # 複製時にキャッシュの紐付けを更新するので作成時刻と更新時刻は一致しない
        self.assertNotEqual(duplicated_flow.created_at, duplicated_flow.modified_at)

        # フローJSONが複製元と一致すること
        self.assertEqual(duplicated_flow.flow_data.description, flow.flow_data.description)
        # creatorには複製を実行したユーザ名が設定される
        self.assertEqual(duplicated_flow.flow_data.creator, self.USER3.name)
        self.assertEqual(duplicated_flow.flow_data.created_at, flow.flow_data.created_at)
        self.assertEqual(duplicated_flow.flow_data.params, flow.flow_data.params)
        self.assertEqual(duplicated_flow.flow_data.i_ports, flow.flow_data.i_ports)
        self.assertEqual(duplicated_flow.flow_data.o_ports, flow.flow_data.o_ports)
        self.assertEqual(duplicated_flow.flow_data.o_ports, flow.flow_data.o_ports)
        self.assertEqual(duplicated_flow.flow_data.get_nodes(), flow.flow_data.get_nodes())

        # 権限設定が複製元と一致すること
        self.assert_auths_equal(duplicated_flow.id, flow.id, auths_len=4)

        # フローを削除する
        flow.delete()
        duplicated_flow.delete()

        # プロジェクトを削除する
        project.delete()

    async def test_duplicate_database(self):
        """
        データベースが複製できること
        """
        # ルートフォルダを取得する
        root = self.factory3.data.load_root()

        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('長岡天神')
        project.save()

        # プロジェクトの下にデータベースを作成する
        conn_json = {
            'dbms'     : "postgresql",
            'hostname' : "db", 
            'port'     : 5432, 
            'database' : "streamcat", 
            'userId'  : "streamcat", 
            'password' : 'my pass word'
        }
        db = project.create_database('西向日', DatabaseConn(conn_json))
        db.save()
        db.reload()

        # データベースを複製する
        duplicated_db = db.duplicate('東向日')
        duplicated_db.reload()

        # 作成を確定する
        self.factory3.end()

        # 複製したデータベースを検証する
        self.assertIsNotNone(duplicated_db.id)
        self.assertNotEqual(duplicated_db.id, db.id)
        self.assertEqual(duplicated_db.parent_id, project.id)
        self.assertIsNotNone(duplicated_db.uuid)
        self.assertNotEqual(duplicated_db.uuid, db.uuid)
        self.assertIsNone(duplicated_db.path)
        self.assertEqual(duplicated_db.type, 'database')
        self.assertEqual(duplicated_db.label, '東向日')
        self.assertEqual(duplicated_db.creator, self.USER3)
        self.assertEqual(duplicated_db.modifier, self.USER3)
        self.assertIsNotNone(duplicated_db.created_at)
        self.assertIsNotNone(duplicated_db.modified_at)
        self.assertEqual(duplicated_db.created_at, duplicated_db.modified_at)

        # 接続情報が複製元と一致すること
        self.assertTrue(duplicated_db.conn, db.conn)

        # 権限設定が複製元と一致すること
        self.assert_auths_equal(duplicated_db.id, db.id)

        # データベースを削除する
        db.delete()
        duplicated_db.delete()

        # プロジェクトを削除する
        project.delete()

    async def test_duplicate_remote_folder(self):
        """
        リモートフォルダが複製できること
        """
        # ルートフォルダを取得する
        root = self.factory3.data.load_root()

        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('高槻市')
        project.save()

        # プロジェクトの下にリモートフォルダを作成する
        conn_json = {
            'protocol' : 'smb',
            'hostname' : "18.178.64.116",
            'domain'   : "WORKGROUP",
            'directory': "share",
            'userId'  : "samba",
            'password' : "kskanalytics"
        }
        folder = project.create_remote_folder('上牧', RemoteFolderConn(conn_json))
        folder.save()
        folder.reload()

        # リモートフォルダを複製する
        duplicated_folder = folder.duplicate('水瀬')
        duplicated_folder.reload()

        # 作成を確定する
        self.factory3.end()

        # 複製したリモートフォルダを検証する
        self.assertIsNotNone(duplicated_folder.id)
        self.assertNotEqual(duplicated_folder.id, folder.id)
        self.assertEqual(duplicated_folder.parent_id, project.id)
        self.assertIsNotNone(duplicated_folder.uuid)
        self.assertNotEqual(duplicated_folder.uuid, folder.uuid)
        self.assertIsNotNone(duplicated_folder.path)
        self.assertNotEqual(duplicated_folder.path, folder.path)
        self.assertEqual(duplicated_folder.type, 'rfolder')
        self.assertEqual(duplicated_folder.label, '水瀬')
        self.assertEqual(duplicated_folder.creator, self.USER3)
        self.assertEqual(duplicated_folder.modifier, self.USER3)
        self.assertIsNotNone(duplicated_folder.created_at)
        self.assertIsNotNone(duplicated_folder.modified_at)
        self.assertEqual(duplicated_folder.created_at, duplicated_folder.modified_at)

        # 接続情報が複製元と一致すること
        self.assertTrue(duplicated_folder.conn, folder.conn)

        # 権限設定が複製元と一致すること
        self.assert_auths_equal(duplicated_folder.id, folder.id)

        # リモートフォルダを削除する
        folder.delete()
        duplicated_folder.delete()

        # プロジェクトを削除する
        project.delete()

    async def test_duplicate_schedule(self):
        """
        スケジュールが複製できること
        """
        # ルートフォルダを取得する
        root = self.factory3.data.load_root()

        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('茨木市')
        project.save()

        # プロジェクトの下にフローを作成する
        flow_json =self.create_test_flow_json('南茨木', root.uuid)
        flow = project.create_flow('南茨木', FlowData(flow_json))
        flow.save()

        # プロジェクトの下にスケジュールを作成する
        args = {'params': {'my-param': 123}}
        trigger1 = {
            'type' : 'cron',
            'start_date' : '3021-06-29 12:01:02',
            'end_date'   : '4021-06-29 12:03:04',
            'year'  : 2021,
            'month' : 12,
            'week'  : 1,
            'day_of_week': 1,
            'day'   : 1,
            'hour'  : 1,
            'minute': 1,
            'second': 1
        }
        schedule = project.create_schedule('摂津市', flow.uuid, args=args, trigger=trigger1)
        schedule.save()
        schedule.reload()

        # スケジュールを複製する
        duplicated_schedule = schedule.duplicate('富田')
        duplicated_schedule.reload()

        # 作成を確定する
        self.factory3.end()

        # 複製したスケジュールを検証する
        self.assertIsNotNone(duplicated_schedule.id)
        self.assertNotEqual(duplicated_schedule.id, schedule.id)
        self.assertEqual(duplicated_schedule.parent_id, project.id)
        self.assertIsNotNone(duplicated_schedule.uuid)
        self.assertNotEqual(duplicated_schedule.uuid, schedule.uuid)
        self.assertIsNone(duplicated_schedule.path)
        self.assertEqual(duplicated_schedule.type, 'schedule')
        self.assertEqual(duplicated_schedule.label, '富田')
        self.assertEqual(duplicated_schedule.creator, self.USER3)
        self.assertEqual(duplicated_schedule.modifier, self.USER3)
        self.assertIsNotNone(duplicated_schedule.created_at)
        self.assertIsNotNone(duplicated_schedule.modified_at)
        self.assertEqual(duplicated_schedule.created_at, duplicated_schedule.modified_at)

        # スケジュールの情報が複製元と一致すること
        self.assertEqual(duplicated_schedule.runnable_uuid, schedule.runnable_uuid)
        self.assertEqual(duplicated_schedule.args, schedule.args)
        self.assertEqual(duplicated_schedule.inputs, schedule.inputs)
        self.assertEqual(duplicated_schedule.trigger, schedule.trigger)

        # 権限設定が複製元と一致すること
        self.assert_auths_equal(duplicated_schedule.id, schedule.id)

        # スケジュールとフローを削除する
        schedule.delete()
        duplicated_schedule.delete()
        flow.delete()

        # プロジェクトを削除する
        project.delete()

    async def test_duplicate_frame(self):
        """
        フレームが複製できること
        """
        # ルートフォルダを取得する
        root = self.factory3.data.load_root()

        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('淡路')
        project.save()

        # プロジェクトの下にフレームを作成する
        frame = project.create_frame('崇禅寺', io.BytesIO(b'starbacks'))
        frame.save()
        frame.reload()

        # フレームを複製する
        duplicated_frame1 = frame.duplicate('上新庄')
        duplicated_frame1.reload()

        # 作成を確定する
        self.factory3.end()

        # 複製したフレームを検証する
        self.assertIsNotNone(duplicated_frame1.id)
        self.assertNotEqual(duplicated_frame1.id, frame.id)
        self.assertEqual(duplicated_frame1.parent_id, project.id)
        self.assertIsNotNone(duplicated_frame1.uuid)
        self.assertNotEqual(duplicated_frame1.uuid, frame.uuid)
        self.assertEqual(duplicated_frame1.path, frame.path)
        self.assertEqual(duplicated_frame1.type, 'frame')
        self.assertEqual(duplicated_frame1.label, '上新庄')
        self.assertEqual(duplicated_frame1.creator, self.USER3)
        self.assertEqual(duplicated_frame1.modifier, self.USER3)
        self.assertIsNotNone(duplicated_frame1.created_at)
        self.assertIsNotNone(duplicated_frame1.modified_at)
        self.assertEqual(duplicated_frame1.created_at, duplicated_frame1.modified_at)

        # フレームの情報が複製元と一致すること
        self.assertEqual(duplicated_frame1.content_type, frame.content_type)
        self.assertEqual(duplicated_frame1.file_size, frame.file_size)
        self.assertEqual(duplicated_frame1.modified_at_str, frame.modified_at_str)
        self.assertEqual(duplicated_frame1.encoding, frame.encoding)
        self.assertEqual(duplicated_frame1.newline, frame.newline)

        # 権限設定が複製元と一致すること
        self.assert_auths_equal(duplicated_frame1.id, frame.id)

        # 
        # 改行コードと文字コードの変更後に複製しても複製元と一致すること
        # 
        frame.update_encoding_newline('CP932', 'CR', self.USER3)
        
        # フレームを複製する
        duplicated_frame2 = frame.duplicate('下新庄')
        duplicated_frame2.reload()

        # フレームの情報が複製元と一致すること
        self.assertEqual(duplicated_frame2.content_type, frame.content_type)
        self.assertEqual(duplicated_frame2.file_size, frame.file_size)
        self.assertEqual(duplicated_frame2.modified_at_str, frame.modified_at_str)
        self.assertEqual(duplicated_frame2.encoding, frame.encoding)
        self.assertEqual(duplicated_frame2.newline, frame.newline)

        # フレームを削除する
        frame.delete()
        # 複製元の削除によって実ファイルが削除されないこと
        self.assertTrue(duplicated_frame1.file_exists)
        self.assertTrue(duplicated_frame2.file_exists)
        duplicated_frame1.delete()
        duplicated_frame2.delete()

        # プロジェクトを削除する
        project.delete()

    async def test_duplicate_document(self):
        """
        ドキュメントが複製できること
        """
        # ルートフォルダを取得する
        root = self.factory3.data.load_root()

        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('梅田')
        project.save()

        # プロジェクトの下にドキュメントを作成する
        document = project.create_document('十三', io.BytesIO(b'I am document data'))
        document.save()
        document.reload()

        # ドキュメントを複製する
        duplicated_document = document.duplicate('南方')
        duplicated_document.reload()

        # 作成を確定する
        self.factory3.end()

        # 複製したドキュメントを検証する
        self.assertIsNotNone(duplicated_document.id)
        self.assertNotEqual(duplicated_document.id, document.id)
        self.assertEqual(duplicated_document.parent_id, project.id)
        self.assertIsNotNone(duplicated_document.uuid)
        self.assertNotEqual(duplicated_document.uuid, document.uuid)
        self.assertEqual(duplicated_document.path, document.path)
        self.assertEqual(duplicated_document.type, 'document')
        self.assertEqual(duplicated_document.label, '南方')
        self.assertEqual(duplicated_document.creator, self.USER3)
        self.assertEqual(duplicated_document.modifier, self.USER3)
        self.assertIsNotNone(duplicated_document.created_at)
        self.assertIsNotNone(duplicated_document.modified_at)
        self.assertEqual(duplicated_document.created_at, duplicated_document.modified_at)

        # ドキュメントの情報が複製元と一致すること
        self.assertEqual(duplicated_document.content_type, document.content_type)
        self.assertEqual(duplicated_document.file_size, document.file_size)
        self.assertEqual(duplicated_document.modified_at_str, document.modified_at_str)

        # 権限設定が複製元と一致すること
        self.assert_auths_equal(duplicated_document.id, document.id)

        # ドキュメントを削除する
        document.delete()
        # 複製元の削除によって実ファイルが削除されないこと
        self.assertTrue(duplicated_document.file_exists)
        duplicated_document.delete()

        # プロジェクトを削除する
        project.delete()

    async def test_duplicate_folder(self):
        """
        フォルダが複製できること
        """
        # ルートフォルダを取得する
        root = self.factory3.data.load_root()

        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('出町柳')
        project.save()

        # プロジェクトの下にフォルダを作成する
        folder = project.create_folder('三条')
        folder.save()
        folder.reload()

        # フォルダの下に色々と作成する
        frame = folder.create_frame('五条', io.BytesIO(b'I am frame data'))
        sub_folder = folder.create_folder('七条')
        frame.save()
        sub_folder.save()

        # フォルダの下の下にも作成する
        document = sub_folder.create_document('東福寺', io.BytesIO(b'I am document data'))
        document.save()

        # フォルダを複製する
        duplicated_folder = folder.duplicate('四条')
        duplicated_folder.reload()

        # 作成を確定する
        self.factory3.end()

        # 複製したフォルダを検証する
        self.assertIsNotNone(duplicated_folder.id)
        self.assertNotEqual(duplicated_folder.id, folder.id)
        self.assertEqual(duplicated_folder.parent_id, project.id)
        self.assertIsNotNone(duplicated_folder.uuid)
        self.assertNotEqual(duplicated_folder.uuid, folder.uuid)
        self.assertEqual(duplicated_folder.path, root.path / '出町柳/四条')
        self.assertEqual(duplicated_folder.type, 'folder')
        self.assertEqual(duplicated_folder.label, '四条')
        self.assertEqual(duplicated_folder.creator, self.USER3)
        self.assertEqual(duplicated_folder.modifier, self.USER3)
        self.assertIsNotNone(duplicated_folder.created_at)
        self.assertIsNotNone(duplicated_folder.modified_at)
        self.assertEqual(duplicated_folder.created_at, duplicated_folder.modified_at)

        # 権限設定が複製元と一致すること
        self.assert_auths_equal(duplicated_folder.id, folder.id, auths_len=4)

        # 子Datumも複製されていること
        children = duplicated_folder.find_children()
        self.assertEqual(len(children), 2)
        # folder
        duplicated_sub_folder = children[0]
        self.assertEqual(children[0].parent_id, duplicated_folder.id)
        self.assertNotEqual(children[0].uuid, sub_folder.uuid)
        self.assertEqual(children[0].path, root.path / '出町柳/四条/七条')
        self.assertEqual(children[0].type, 'folder')
        self.assertEqual(children[0].label, '七条')
        self.assertEqual(children[0].creator, self.USER3)
        self.assertEqual(children[0].modifier, self.USER3)
        # frame
        self.assertEqual(children[1].parent_id, duplicated_folder.id)
        self.assertNotEqual(children[1].uuid, frame.uuid)
        self.assertEqual(children[1].path, frame.path)
        self.assertEqual(children[1].type, 'frame')
        self.assertEqual(children[1].label, '五条')
        self.assertEqual(children[1].creator, self.USER3)
        self.assertEqual(children[1].modifier, self.USER3)

        # フォルダの下の下
        children = duplicated_sub_folder.find_children()
        self.assertEqual(len(children), 1)
        # document
        self.assertEqual(children[0].parent_id, duplicated_sub_folder.id)
        self.assertNotEqual(children[0].uuid, document.uuid)
        self.assertEqual(children[0].path, document.path)
        self.assertEqual(children[0].type, 'document')
        self.assertEqual(children[0].label, '東福寺')
        self.assertEqual(children[0].creator, self.USER3)
        self.assertEqual(children[0].modifier, self.USER3)

        # フォルダを削除する
        # (先に複製元フォルダを削除しても例外が送出されないこと)
        folder = self.factory.data.find_by_uuid(folder.uuid)
        folder.throw_away()
        self.factory.data.find_trashcan().trash_all()

        # 複製したフォルダを削除する
        duplicated_folder = self.factory.data.find_by_uuid(duplicated_folder.uuid)
        duplicated_folder.throw_away()
        self.factory.data.find_trashcan().trash_all()

    async def test_duplicate_project(self):
        """
        プロジェクトが複製できること
        """
        # ルートフォルダを取得する
        root = self.factory3.data.load_root()

        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('枚方')
        project.save()
        project.reload()

        # プロジェクトの下にフォルダを作成する
        folder = project.create_folder('香里園')
        folder.save()

        # プロジェクトの下にデータベースを作成する
        conn_json = {
            'dbms'     : "postgresql",
            'hostname' : "db", 
            'port'     : 5432, 
            'database' : "streamcat", 
            'userId'  : "streamcat", 
            'password' : 'my pass word'
        }
        db = folder.create_database('寝屋川市', DatabaseConn(conn_json))
        db.save()

        # プロジェクトを複製する
        duplicated_project = project.duplicate('樟葉')
        duplicated_project.reload()

        # 作成を確定する
        self.factory3.end()

        # 複製したプロジェクトを検証する
        self.assertIsNotNone(duplicated_project.id)
        self.assertNotEqual(duplicated_project.id, project.id)
        self.assertEqual(duplicated_project.parent_id, root.id)
        self.assertIsNotNone(duplicated_project.uuid)
        self.assertNotEqual(duplicated_project.uuid, project.uuid)
        self.assertEqual(duplicated_project.path, root.path / '樟葉')
        self.assertEqual(duplicated_project.type, 'project')
        self.assertEqual(duplicated_project.label, '樟葉')
        self.assertEqual(duplicated_project.creator, self.USER3)
        self.assertEqual(duplicated_project.modifier, self.USER3)
        self.assertIsNotNone(duplicated_project.created_at)
        self.assertIsNotNone(duplicated_project.modified_at)
        self.assertEqual(duplicated_project.created_at, duplicated_project.modified_at)
        # 権限設定が複製元と一致すること
        self.assert_auths_equal(duplicated_project.id, project.id, auths_len=4)

        # 子Datumも複製されていること
        children = duplicated_project.find_children()
        self.assertEqual(len(children), 1)
        # folder
        duplicated_sub_folder = children[0]
        self.assertEqual(children[0].parent_id, duplicated_project.id)
        self.assertNotEqual(children[0].uuid, folder.uuid)
        self.assertEqual(children[0].path, root.path / '樟葉/香里園')
        self.assertEqual(children[0].type, 'folder')
        self.assertEqual(children[0].label, '香里園')
        self.assertEqual(children[0].creator, self.USER3)
        self.assertEqual(children[0].modifier, self.USER3)
        # 権限設定が複製元と一致すること
        self.assert_auths_equal(children[0].id, folder.id, auths_len=4)

        # 孫Datumも複製されていること
        children = duplicated_sub_folder.find_children()
        self.assertEqual(len(children), 1)
        # database
        self.assertEqual(children[0].parent_id, duplicated_sub_folder.id)
        self.assertNotEqual(children[0].uuid, db.uuid)
        self.assertIsNone(children[0].path)
        self.assertEqual(children[0].type, 'database')
        self.assertEqual(children[0].label, '寝屋川市')
        self.assertEqual(children[0].creator, self.USER3)
        self.assertEqual(children[0].modifier, self.USER3)
        # 権限設定が複製元と一致すること
        self.assert_auths_equal(children[0].id, db.id)

        # プロジェクトを削除する
        # (先に複製元プロジェクトを削除しても例外が送出されないこと)
        project = self.factory.data.find_by_uuid(project.uuid)
        project.throw_away()
        self.factory.data.find_trashcan().trash_all()

        # 複製したプロジェクトを削除する
        duplicated_project = self.factory.data.find_by_uuid(duplicated_project.uuid)
        duplicated_project.throw_away()
        self.factory.data.find_trashcan().trash_all()
