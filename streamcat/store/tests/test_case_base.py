import unittest
import pprint
from streamcat.store.factory import Factory, UnAuthzFactory

class TestCaseBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # ユーザ管理者を取得する
        with UnAuthzFactory() as factory:
            sys_admin_user = factory.find_user_by_email('Admin@streamcat.io')
            usr_admin_user = factory.find_user_by_email('admin@streamcat.io')

        with Factory(usr_admin_user) as factory:
            # テストユーザ1を作成する
            test_user = factory.user.create('test@streamcat.io', 'Test', '123abc(*)A')
            test_user.save()
            # テストユーザ2を作成する
            test_user2 = factory.user.create('test2@streamcat.io', 'Test2', '123abc(*)B')
            test_user2.save()

        # システム管理者を登録状態にする
        with Factory(sys_admin_user) as factory:
            # FactoryでUserオブジェクトを再取得する
            sys_admin_user = factory.user.find_by_id(sys_admin_user.id)
            # 仮登録状態から登録状態にする
            sys_admin_user.update_password('adminpass1')
            sys_admin_user = factory.user.find_by_id(sys_admin_user.id)

        # ユーザ管理者を登録状態にする
        with Factory(usr_admin_user) as factory:
            usr_admin_user = factory.user.find_by_id(usr_admin_user.id)
            usr_admin_user.update_password('adminpass1')
            usr_admin_user = factory.user.find_by_id(usr_admin_user.id)

        # テストユーザ1を登録状態にする
        with Factory(test_user) as factory:
            test_user = factory.user.find_by_id(test_user.id)
            test_user.update_password('testpass00')
            test_user = factory.user.find_by_id(test_user.id)

        # テストユーザ2を登録状態にする
        with Factory(test_user2) as factory:
            test_user2 = factory.user.find_by_id(test_user2.id)
            test_user2.update_password('testpass20')
            test_user2 = factory.user.find_by_id(test_user2.id)

        # クラス変数を設定する
        cls.USER0 = sys_admin_user
        cls.USER1 = usr_admin_user
        cls.USER2 = test_user
        cls.USER3 = test_user2

        # ライブラリデータデストを作成する
        with Factory(usr_admin_user) as factory:
            cls.root = factory.data.load_root()
            cls.data_dst = cls._create_data_dst(cls.root)

    @classmethod
    def tearDownClass(cls):
        # USERオブジェクトに対する操作によってトランザクションが設定されるため
        # ここでそれらのトランザクションを終了する
        cls.USER0._session.close()
        cls.USER1._session.close()
        cls.USER2._session.close()
        cls.USER3._session.close()

        # ライブラリフォルダを削除する
        with Factory(cls.USER1) as factory:
            import shutil
            library_path = factory.data.load_root().path
            shutil.rmtree(library_path.as_posix())

        # スキーマを破棄する
        from sqlalchemy import DDL
        from streamcat.core import engine, SCHEMA_NAME
        with engine.begin() as conn:
            conn.execute(DDL(f'DROP SCHEMA IF EXISTS {SCHEMA_NAME} CASCADE'))

    @classmethod
    def _create_data_dst(cls, root):
        """
        ライブラリデータデストを作成する
        """
        from streamcat.store import ProjectFolder, FlowData
        # フォルダを作成する
        project = root.create_project_folder('データデスト📂')
        project.save()
        project = project.reload()

        # データデストフローを作成する
        data_dst_json = {
            "label": "ライブラリデータデスト💾",
            "ports": [
                [
                    {
                    "type": "frame", 
                    "label": "i", 
                    "nodeId": "d"
                    }
                ], 
                []
            ], 
            "params": [],
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
                    "uuid": root.uuid, 
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
            ]
        }
        data_dst_flow = project.create_flow('ライブラリデータデスト💾', FlowData(data_dst_json))
        data_dst_flow.save()

        # 全てのテストユーザが実行可能にする
        member0 = ProjectFolder.Member(cls.USER0, ProjectFolder.READER_MEMBER_TYPE)
        member1 = ProjectFolder.Member(cls.USER1, ProjectFolder.OWNER_MEMBER_TYPE)
        member2 = ProjectFolder.Member(cls.USER2, ProjectFolder.READER_MEMBER_TYPE)
        member3 = ProjectFolder.Member(cls.USER3, ProjectFolder.READER_MEMBER_TYPE)
        project.init_members([member0, member1, member2, member3], last_modified_at=project.modified_at)

        return data_dst_flow.reload()

    def setUp(self) -> None:
        super().setUp()        
        # テスト実行ごとにトランザクションを設定する
        self.factory0 = Factory(self.USER0)
        self.factory = Factory(self.USER1)
        self.factory2 = Factory(self.USER2)
        self.factory3 = Factory(self.USER3)

    def tearDown(self) -> None:
        super().tearDown()
        # FactoryをCloseする
        self.factory0.end()
        self.factory.end()
        self.factory2.end()
        self.factory3.end()

    def create_data_dst_node(self, src_node_id:str) -> dict:
        """
        ライブラリデータデストノードを作成する
        """
        return {
            "id": 'o_' + src_node_id, 
            "label": "ライブラリ", 
            "type": "flow", 
            "classification": "data_dest",
            "srcs": {
                "i": src_node_id
            },
            "dsts": {}, 
            "flow": {
                "label": "ライブラリ",
                "ports": [
                    [
                      {
                        "types": ["frame", "matrix"], 
                        "label": "i", 
                        "nodeId": "d"
                      }
                    ], 
                    []
                ], 
                "params": [],
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
                      "uuid": self.root.uuid, 
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
                ]
            }
        }
