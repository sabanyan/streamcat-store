import io
import pprint
import unittest
from streamcat.core import SCatBaseModel
from streamcat.store import Mountable, FlowData, DatabaseConn, RemoteFolderConn
from .test_case_base import TestCaseBase

class DelTest(TestCaseBase, unittest.IsolatedAsyncioTestCase):
    """
    削除制約を検証する
    """

    conn_json = {
      'dbms'     : "postgresql",
      'hostname' : "kskp.cr4gfi5zl5xm.ap-northeast-1.rds.amazonaws.com", 
      'port'     : 5432, 
      'database' : "kskp", 
      'userId'  : "kskp", 
      'password' : 'my-pass-word'
    }
    database_conn = DatabaseConn(conn_json)

    conn_json = {
        'protocol' : 'smb',
        'hostname' : "18.178.64.116",
        'domain'   : "WORKGROUP",
        'directory': "share",
        'userId'  : "samba",
        'password' : "kskanalytics"
    }
    remote_folder_conn = RemoteFolderConn(conn_json)

    def create_file(self, file_path):
        with open(file_path, 'w') as f:
            f.write('I am a frame data for test cases.')

    def create_flow_json(self, in_frame1, in_frame2, out_database, out_rfolder, sub_flow):
        """
        テスト対象のフローを作成する
        """
        return {
            "label": "tst", 
            "params": [], 
            "creator": "カイザー・ヴィルヘルム2", 
            "createdAt": "2021-06-19 15:24:00",
            "description": "",
            "nodes": [
                {
                    "id": "i", 
                    "label": "ライブラリ",
                    "type": "flow", 
                    "classification": "data_source",
                    "args": {
                        "uuid": in_frame1.uuid
                    }, 
                    "srcs": {},
                    "dsts": {
                        "d": "d"
                    }, 
                    "flow": {
                        "label": "ライブラリ", 
                        "creator": "ベートマン・ホルヴェーク", 
                        "createdAt": "2021-06-19 15:24:02", 
                        "description": "",
                        "nodes": [
                            {
                                "id": "s",
                                "label": "ライブラリ",
                                "type": "store",
                                "uuid": self.root.uuid
                            }, 
                            {
                                "id": "c1",
                                "label": "c1",
                                "type": "command",
                                "commandId": "loader",
                                "args": {
                                    "uuid": "@[uuid]"
                                },
                                "srcs": {
                                    "folder": "s"
                                },
                                "dsts": {
                                    "o": "d"
                                }
                            }, 
                            {
                                "id": "d",
                                "label": "d",
                                "type": "frame",
                                "dataSource": "csv"
                            }
                        ], 
                        "ports": [[], 
                            [
                                {
                                    "label": "o", 
                                    "nodeId": "d",
                                    "type": "frame"
                                }
                            ]
                        ], 
                        "params": [
                            {
                                "name": "uuid",
                                "label": "ファイルを指定する",
                                "type": "frame",
                                "optional": False
                            }
                        ]
                    }
                },
                {
                    "id": "d", 
                    "label": "d",
                    "type": "frame", 
                },
                {
                    "id": "d1", 
                    "label": "d1",
                    "type": "frame",
                    "uuid": in_frame2.uuid
                },
                {
                    "id": "c1",
                    "label": "c1",
                    "type": "command",
                    "commandId": "mpaste",
                    "args": {
                        "f": "customer:customer1,date:date1,amount:amount1"
                    }, 
                    "srcs": {
                        "i": "d", 
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
                    "dataSource": "csv"
                },
                {
                    "id": "o",
                    "label": "私のDB",
                    "type": "flow",
                    "classification": "data_dest",
                    "args": {
                        "table": "result"
                    },
                    "srcs": {
                        "d": "d2"
                    },
                    "dsts": {}, 
                    "flow": {
                        "label": "私のDB",
                        "creator": "ジョルジュ・クレマンソー",
                        "createdAt": "2021-06-19 15:24:03",
                        "description": "",
                        "nodes": [
                            {
                                "id": "d",
                                "label": "d",
                                "type": "frame",
                                "dataSource": "csv"
                            }, 
                            {
                                "id": "s",
                                "label": "私のDB",
                                "type": "store",
                                "uuid": out_database.uuid
                            }, 
                            {
                                "id": "c1",
                                "label": "c1",
                                "type": "command",
                                "commandId": "db_saver",
                                "args": {
                                    "table_name": "@[table]",
                                    "schema_name": "@[schema]"
                                },
                                "srcs": {
                                    "i": "d",
                                    "store": "s"
                                }, 
                                "dsts": {
                                    "o": "d1"
                                },
                            },
                            {
                                "id": "d1",
                                "label": "d1",
                                "type": "frame",
                                "dataSource": "csv"
                            }
                        ], 
                        "ports": [
                            [
                                {
                                    "label": "i",
                                    "nodeId": "d",
                                    "type": "frame"
                                }
                            ], 
                            []
                        ], 
                        "params": [
                            {
                                "name": "schema",
                                "type": "string",
                                "label": "スキーマ名を指定する",
                                "optional": True
                            },
                            {
                                "name": "table",
                                "type": "string",
                                "label": "テーブル名を指定する",
                                "optional": False
                            }
                        ]
                    }, 
                },
                {
                    "id": "o1",
                    "label": "私のリモートフォルダ",
                    "type": "flow",
                    "classification": "data_dest",
                    "args": {
                        "dirPath": "result.csv"
                    },
                    "srcs": {
                        "d": "d2"
                    },
                    "dsts": {},
                    "flow": {
                        "label": "私のリモートフォルダ",
                        "creator": "レイモン・ポアンカレ",
                        "createdAt": "2021-06-19 15:24:03",
                        "description": "",
                        "nodes": [
                            {
                                "id": "d",
                                "label": "d",
                                "type": "frame",
                                "dataSource": "csv"
                            }, 
                            {
                                "id": "s",
                                "label": "私のリモートフォルダ",
                                "type": "store",
                                "uuid": out_rfolder.uuid
                            }, 
                            {
                                "id": "c1",
                                "type": "command",
                                "label": "c1",
                                "commandId": "remotefolder_saver",
                                "args": {
                                    "dir_path": "@[dirPath]"
                                },
                                "srcs": {
                                    "i": "d",
                                    "store": "s"
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
                        "ports": [
                            [
                                {
                                    "label": "i",
                                    "nodeId": "d",
                                    "type": "frame"
                                }
                            ], 
                            []
                        ], 
                        "params": [
                            {
                                "name": "dirPath",
                                "type": "string",
                                "label": "フォルダパスを指定する",
                                "optional": False
                            }
                        ]
                    }
                },
                {
                    "id": "f1", 
                    "label": "f1",
                    "type": "flow",
                    "args": {},
                    "srcs": {},
                    "dsts": {},
                    "uuid": sub_flow.uuid
                }
            ], 
            "ports": [
                [
                    {
                        "label": "d",
                        "nodeId": "d",
                        "type": "frame"
                        
                    },
                    {
                        "label": "d1",
                        "nodeId": "d1",
                        "type": "frame"
                    }
                ],
                [
                    {
                        "label": "d2",
                        "nodeId": "d2",
                        "type": "frame"
                    }
                ]
            ]
        }

    async def test_throw_away_datum(self):
        """
        フローから参照されているDatumは削除できないこと
        """
        # ルートフォルダを取得する
        root = self.finder.data.load_root()

        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('WW1')
        project.save()

        # CSVデータを作成する
        l = [['customer','date','amount'],
             ['ドイツ帝国','19140801','177'],
             ['オーストリア','19140728','120'],
             ['フランス','19140801','135'],
             ['イギリス','19140804','90'],
             ['ロシア','19140801','170']]
        csv_str = '\n'.join([SCatBaseModel.join(line) for line in l])
        f = io.StringIO(csv_str)
        f = io.BytesIO(bytes(f.read(), encoding='utf-8'))

        # プロジェクトの下にフレーム1を作成する
        frame1 = project.create_frame('小モルトケ', f)
        frame1.save()

        # プロジェクトの下にフレーム2を作成する
        frame2 = project.create_frame('エーリッヒ・フォン・ファルケンハイン', f)
        frame2.save()

        # プロジェクトの下にデータベースを作成する
        database = project.create_database('ルーデンドルフ', self.database_conn)
        database.save()

        # プロジェクトの下にリモートフォルダを作成する
        rfolder = project.create_remote_folder('ジョフル', self.remote_folder_conn)
        rfolder.save()

        # プロジェクトの下にサブフローを作成する
        subflow = project.create_flow('フィリップ・ペタン', FlowData({}))
        subflow.save()

        # プロジェクトの下にフレームを参照するフローを作成する
        flow_json =self.create_flow_json(frame1, frame2, database, rfolder, subflow)
        flow = project.create_flow('ダグラス・ヘイグ', FlowData(flow_json))
        flow.save()

        # 
        # ゴミ箱へほかすのを試みる
        # 

        # フレーム1はほかせないこと
        with self.assertRaises(Exception):
            frame1.throw_away()

        # フレーム2はほかせないこと
        with self.assertRaises(Exception):
            frame2.throw_away()

        # データベースはほかせないこと
        with self.assertRaises(Exception):
            database.throw_away()

        # リモートフォルダはほかせないこと
        with self.assertRaises(Exception):
            rfolder.throw_away()

        # サブフローはほかせないこと
        with self.assertRaises(Exception):
            subflow.throw_away()

        # 
        # 削除を試みる
        # 

        # データベースは削除できないこと
        with self.assertRaises(Exception):
            database.delete()

        # リモートフォルダは削除できないこと
        with self.assertRaises(Exception):
            rfolder.delete()

        # サブフローは削除できないこと
        with self.assertRaises(Exception):
            subflow.delete()

        # 参照元のフローをほかす
        flow.throw_away()

        # 参照先のDatumをほかせること
        frame1.throw_away()
        frame2.throw_away()
        database.throw_away()
        rfolder.throw_away()
        subflow.throw_away()

        # 参照先のDatumを削除できること
        frame1.delete()
        frame2.delete()
        database.delete()
        rfolder.delete()
        subflow.delete()

        # 参照元のフローを削除する
        flow.delete()

    async def test_throw_away_project(self):
        """
        参照元フローと参照先Datumをフォルダ丸ごと一緒に削除できること
        """
        # ルートフォルダを取得する
        root = self.finder.data.load_root()

        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('シュリーフェンプラン')
        project.save()

        # CSVデータを作成する
        l = [['軍','将軍'],
             ['第1軍','クルック'],
             ['第2軍','ビューロウ'],
             ['第3軍','ハウゼン'],
             ['第4軍','ヴュルテンベルク公爵'],
             ['第5軍','ヴィルヘルム皇太子'],
             ['第6軍','ループレヒト王太子'],
             ['第7軍','ヒーリンゲン '],
             ['第8軍','プリットヴィッツ']]
        csv_str = '\n'.join([SCatBaseModel.join(line) for line in l])
        f = io.StringIO(csv_str)
        f = io.BytesIO(bytes(f.read(), encoding='utf-8'))

        # プロジェクトの下にフレーム1を作成する
        frame1 = project.create_frame('リエージュ', f)
        frame1.save()

        # プロジェクトの下にフレーム2を作成する
        frame2 = project.create_frame('マルヌ', f)
        frame2.save()

        # プロジェクトの下にデータベースを作成する
        database = project.create_database('タンネンベルク', self.database_conn)
        database.save()

        # プロジェクトの下にリモートフォルダを作成する
        rfolder = project.create_remote_folder('ヴェルダン', self.remote_folder_conn)
        rfolder.save()

        # プロジェクトの下にサブフローを作成する
        subflow = project.create_flow('ソンム', FlowData({}))
        subflow.save()

        # プロジェクトの下にフレームを参照するフローを作成する
        flow_json =self.create_flow_json(frame1, frame2, database, rfolder, subflow)
        flow = project.create_flow('パッシェンデール', FlowData(flow_json))
        flow.save()

        # プロジェクトをゴミ箱にほかせること
        project.throw_away()

        # ゴミ箱を空にできること
        trashcan = self.finder.data.load_trash_folder()
        trashcan.trash_all()

    async def test_trash_remote_folder_in_folder(self):
        """
        マウント状態のリモートフォルダを含むフォルダをゴミ箱に捨てるとマウントが解除されること
        """
        # ルートフォルダを取得する
        root = self.finder3.data.load_root()

        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('私のプロジェクト')
        project.save()

        # プロジェクトの下にフォルダを作成する
        folder = project.create_folder('私のフォルダ')
        folder.save()

        # フォルダの下にサブフォルダを作成する
        sub_folder = folder.create_folder('私のサブフォルダ')
        sub_folder.save()

        # サブフォルダの下にリモートフォルダを作成する
        remote_folder = sub_folder.create_remote_folder('私のリモートフォルダ', self.remote_folder_conn)
        remote_folder.save()
        remote_folder.reload()

        # 作成を確定する
        self.finder3.end()

        # 
        # pathを参照してリモートフォルダをマウントする
        # 
        self.assertEqual(remote_folder.path, root.path/'私のプロジェクト'/'私のフォルダ'/'私のサブフォルダ'/'私のリモートフォルダ')
        self.assertTrue(Mountable.is_mount(remote_folder._path))

        # 
        # フォルダをゴミ箱にほかす
        # 
        folder.throw_away()

        # リモートフォルダがゴミ箱にほかされていること
        self.assertTrue(self.finder3.data.trashed(remote_folder.uuid))
        # マウントが解除されていること
        self.assertFalse(Mountable.is_mount(remote_folder._path))
        self.assertEqual(remote_folder._path, root.path/'ゴミ箱'/'私のフォルダ'/'私のサブフォルダ'/'私のリモートフォルダ')
        # マウントポイントのディレクトリが移動されていること
        self.assertTrue(remote_folder._path.is_dir())
        self.assertNotEqual(remote_folder.created_at, remote_folder.modified_at)

        # 
        # フォルダをゴミ箱から戻す
        # 
        folder.put_back()

        # リモートフォルダがゴミ箱に存在しないこと
        self.assertFalse(self.finder3.data.trashed(remote_folder.uuid))
        # マウントは解除状態のままであること
        self.assertFalse(Mountable.is_mount(remote_folder._path))
        self.assertEqual(remote_folder._path, root.path/'私のプロジェクト'/'私のフォルダ'/'私のサブフォルダ'/'私のリモートフォルダ')
        # マウントポイントのディレクトリが移動されていること
        self.assertTrue(remote_folder._path.is_dir())
        self.assertNotEqual(remote_folder.created_at, remote_folder.modified_at)

        # リモートフォルダを削除する
        remote_folder.delete()

        # プロジェクトを削除する
        sub_folder.delete()
        folder.delete()
        project.delete()

    async def test_delete_folder_has_child(self):
        """
        フレームを内包するフォルダを削除しようとすると例外を送出する
        """
        # ルートデータストアを取得する
        root = self.finder.data.load_root()
        root_path = root.path

        # ルートデータストアの直下にフォルダを作成する
        folder = root.create_folder('フォルダA')
        folder.save()

        # フレームデータを格納するファイルを作成する
        self.create_file(root_path / 'aaaa.csv')
        # ルートデータストアの直下にフレームを作成する
        frame = folder.create_frame('フレームデータ', None)
        frame.save(file_path=root_path / 'aaaa.csv')

        # フレームを内包するフォルダを削除しようとする
        with self.assertRaises(Exception) as e:
            folder.delete()

        # 作成したフレームを削除する
        frame.delete()
        # 作成したフォルダを削除する
        folder.delete()

    async def test_delete_frame_refer_to_file_other_frame_refering(self):
        """
        二つのフレームが一つのCSVファイルに対応している場合に、
        何れか一つのフレームを削除しても、CSVファイルは削除されない
        """
        # ルートデータストアを取得する
        root = self.finder.data.load_root()
        root_path = root.path

        # フレームデータを格納するファイルを作成する
        self.create_file(root_path / 'foo.csv')
        # ルートデータストアの直下にフレーム1を作成する
        frame1 = root.create_frame('フレームデータ', None)
        frame1.save(file_path=root_path / 'foo.csv')

        # ルートデータストアの直下にフレーム2を作成する
        frame2 = root.create_frame('フレームデータ', None)
        frame2.save(file_path=root_path / 'foo.csv')

        # フレーム1を削除する
        frame1.delete()
        # フレーム1,2に対応するCSVファイルが存在することを検証する
        self.assertTrue((root_path / 'foo.csv').is_file())

        # フレーム2を削除する
        frame2.delete()
        # フレーム1,2に対応するCSVファイルが存在しないことを検証する
        self.assertFalse((root_path / 'foo.csv').is_file())

    async def test_delete_folder_refer_to_file_other_frame_refering(self):
        """
        二つのフォルダが一つのディレクトリに対応している場合に、
        何れか一つのフォルダを削除しても、ディレクトリは削除されない
        """
        pass
