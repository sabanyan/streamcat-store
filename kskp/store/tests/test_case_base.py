import os
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
        from kskp.store import engine
        from sqlalchemy import DDL
        engine.execute(DDL('DROP SCHEMA IF EXISTS %s CASCADE' % os.environ['KSKP_POSTGRESQL_SCHEMA_NAME']))
