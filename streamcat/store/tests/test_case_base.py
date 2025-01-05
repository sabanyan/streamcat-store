import unittest
import pprint
import logging
from typing import Callable
from streamcat.store.factory import Factory, UnAuthzFactory, init_admin_users

class TestCaseBase(unittest.IsolatedAsyncioTestCase):
    @classmethod
    async def asyncSetUpClass(cls):
        # asyncioから以下のようなWarningが多量に出力されるため表示から除外する
        # Executing ... took 0.208 seconds
        def filter(record):
            return record.msg != 'Executing %s took %.3f seconds'
        logging.getLogger('asyncio').addFilter(filter)

        # システム管理者とユーザ管理者を作成する
        await init_admin_users()

        # ユーザ管理者を取得する
        async with UnAuthzFactory() as ufactory:
            sys_admin_user = await ufactory.find_user_by_email('Admin@streamcat.io')
            usr_admin_user = await ufactory.find_user_by_email('admin@streamcat.io')

            usr_factory = await ufactory.create_authz_factory(usr_admin_user)
            # テストユーザ1を作成する
            test_user = usr_factory.user.create('test@streamcat.io', 'Test', '123abc(*)A')
            test_user.save()
            # テストユーザ2を作成する
            test_user2 = usr_factory.user.create('test2@streamcat.io', 'Test2', '123abc(*)B')
            test_user2.save()

            # システム管理者を登録状態にする
            sys_factory = await ufactory.create_authz_factory(sys_admin_user)
            # FactoryでUserオブジェクトを再取得する
            sys_admin_user = sys_factory.user.find_by_id(sys_admin_user.id)
            # 仮登録状態から登録状態にする
            sys_admin_user.update_password('adminpass1')
            sys_admin_user = sys_factory.user.find_by_id(sys_admin_user.id)

            # ユーザ管理者を登録状態にする
            usr_admin_user = usr_factory.user.find_by_id(usr_admin_user.id)
            usr_admin_user.update_password('adminpass1')
            usr_admin_user = usr_factory.user.find_by_id(usr_admin_user.id)

            # テストユーザ1を登録状態にする
            test1_factory = await ufactory.create_authz_factory(test_user)
            test_user = test1_factory.user.find_by_id(test_user.id)
            test_user.update_password('testpass00')
            test_user = test1_factory.user.find_by_id(test_user.id)

            # テストユーザ2を登録状態にする
            test2_factory = await ufactory.create_authz_factory(test_user2)
            test_user2 = test2_factory.user.find_by_id(test_user2.id)
            test_user2.update_password('testpass20')
            test_user2 = test2_factory.user.find_by_id(test_user2.id)

            # クラス変数を設定する
            cls.USER0 = sys_admin_user
            cls.USER1 = usr_admin_user
            cls.USER2 = test_user
            cls.USER3 = test_user2

            # ライブラリデータデストを作成する
            cls.root = usr_factory.data.load_root()
            cls.data_dst = cls._create_data_dst(cls.root)

    @classmethod
    async def asynTearDownClass(cls):
        # USERオブジェクトに対する操作によってトランザクションが設定されるため
        # ここでそれらのトランザクションを終了する
        cls.USER0._session.close()
        cls.USER1._session.close()
        cls.USER2._session.close()
        cls.USER3._session.close()

        # ライブラリフォルダを削除する
        async with UnAuthzFactory() as ufactory:
            import shutil
            factory = await ufactory.create_authz_factory(cls.USER1)
            library_path = factory.data.load_root().path
            shutil.rmtree(library_path.as_posix())

        # スキーマを破棄する
        from sqlalchemy import DDL
        from streamcat.core import engine, SCHEMA_NAME
        with engine.begin() as conn:
            conn.execute(DDL(f'DROP SCHEMA IF EXISTS {SCHEMA_NAME} CASCADE'))

    @classmethod
    def setUpClass(cls):
        # テスト環境を構築する
        cls._call_async_func(cls.asyncSetUpClass)

    @classmethod
    def tearDownClass(cls):
        cls._call_async_func(cls.asynTearDownClass)

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

    def _call_async_func(func:Callable, **kwargs):
        import asyncio
        return asyncio.run(func(**kwargs))

    async def asyncSetUp(self) -> None:
        # テスト実行ごとにトランザクションを設定する
        self.factory0 = await UnAuthzFactory().create_authz_factory(self.USER0)
        self.factory = await UnAuthzFactory().create_authz_factory(self.USER1)
        self.factory2 = await UnAuthzFactory().create_authz_factory(self.USER2)
        self.factory3 = await UnAuthzFactory().create_authz_factory(self.USER3)

    async def asyncTearDown(self) -> None:
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
