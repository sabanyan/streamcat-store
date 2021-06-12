import unittest
import pprint

from kskp.store.factory import Factory, UnAuthzFactory

class TestCaseBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # ユーザ管理者を取得する
        with UnAuthzFactory() as factory:
            sys_admin_user = factory.find_user_by_email('Admin@kskp.io')
            usr_admin_user = factory.find_user_by_email('admin@kskp.io')
        # 管理者ユーザのFactoryをOpenする
        cls.factory0 = Factory(sys_admin_user)
        cls.factory = Factory(usr_admin_user)
        # テストユーザ1を作成する
        test_user = cls.factory.user.create('test@kskp.io', 'Test', '123abc(*)A')
        test_user.save()
        # テストユーザ2を作成する
        test_user2 = cls.factory.user.create('test2@kskp.io', 'Test2', '123abc(*)B')
        test_user2.save()
        # テストユーザのFactoryをOpenする
        cls.factory2 = Factory(test_user)
        cls.factory3 = Factory(test_user2)
        # FactoryでUserオブジェクトを再取得する
        sys_admin_user = cls.factory0.user.find_by_id(sys_admin_user.id)
        usr_admin_user = cls.factory.user.find_by_id(usr_admin_user.id)
        test_user = cls.factory2.user.find_by_id(test_user.id)
        test_user2 = cls.factory3.user.find_by_id(test_user2.id)
        # 仮登録状態から登録状態にする
        sys_admin_user.update_password('adminpass1')
        usr_admin_user.update_password('adminpass1')
        test_user.update_password('testpass00')
        test_user2.update_password('testpass20')
        # クラス変数に設定する
        cls.USER0 = sys_admin_user
        cls.USER1 = usr_admin_user
        cls.USER2 = test_user
        cls.USER3 = test_user2

        # ルートフォルダを作成する
        cls.root = cls.factory.data.load_root()
        # ライブラリデータデストを作成する
        cls.data_dst = cls._create_data_dst(cls.root)

    @classmethod
    def tearDownClass(cls):
        # ライブラリフォルダを削除する
        library_path = cls.factory.data.load_root().path
        import shutil
        shutil.rmtree(library_path.as_posix())
        # FactoryをCloseする
        cls.factory0.close()
        cls.factory.close()
        cls.factory2.close()
        cls.factory3.close()
        # スキーマを破棄する
        from sqlalchemy import DDL
        from kskp.core import engine, SCHEMA_NAME
        with engine.begin() as conn:
            conn.execute(DDL(f'DROP SCHEMA IF EXISTS {SCHEMA_NAME} CASCADE'))

    @classmethod
    def _create_data_dst(cls, root):
        """
        ライブラリデータデストを作成する
        """
        from kskp.store import ProjectFolder, FlowData
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
                "d": src_node_id
            },
            "dsts": {}, 
            "flow": {
                "label": "ライブラリ",
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
