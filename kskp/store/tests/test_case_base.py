import os
import unittest
import pprint

from kskp.store.factory import Factory, UnAuthzFactory

class TestCaseBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 管理者ユーザを取得する
        from kskp.store.auth import Auth, Role, User
        with UnAuthzFactory() as factory:
            admin_user = factory.find_user_by_email('admin@kskp.io')
        # 管理者ユーザのFactoryをOpenする
        cls.factory = Factory(admin_user)
        # AuthzSessionをUserオブジェクトに格納する
        admin_user._session = cls.factory._session
        # テストユーザ1を作成する
        test_user = cls.factory.user.create('test@kskp.io', 'testpass', 'Test')
        test_user.save()
        # テストユーザ2を作成する
        test_user2 = cls.factory.user.create('test2@kskp.io', 'testpass2', 'Test2')
        test_user2.save()
        # 仮登録状態から登録状態にする
        admin_user.update_password('adminpass0')
        test_user.update_password('testpass0')
        test_user2.update_password('testpass20')
        # EveryOneロールにテストユーザを加える
        everyone_role = cls.factory.role.load_everyone_role()
        everyone_role.join_user(test_user)
        everyone_role.join_user(test_user2)
        # テストユーザのFactoryをOpenする
        cls.factory2 = Factory(test_user)
        cls.factory3 = Factory(test_user2)
        # クラス変数に設定する
        cls.USER1 = admin_user
        cls.USER2 = test_user
        cls.USER3 = test_user2

    @classmethod
    def tearDownClass(cls):
        # ライブラリフォルダを削除する
        library_path = cls.factory.data.load_root().path
        import shutil
        shutil.rmtree(library_path.as_posix())
        # FactoryをCloseする
        cls.factory.close()
        cls.factory2.close()
        cls.factory3.close()
        # スキーマを破棄する
        from kskp.store import engine
        from sqlalchemy import DDL
        engine.execute(DDL('DROP SCHEMA IF EXISTS %s CASCADE' % os.environ['KSKP_POSTGRESQL_SCHEMA_NAME']))
