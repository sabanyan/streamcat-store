import os
import unittest
import pprint

from kskp.store import STORE_DIR
from kskp.store.factory import Factory, UnAuthzFactory

class TestCaseBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 管理者ユーザを取得する
        from kskp.store.auth import Auth, Group, User
        with UnAuthzFactory() as factory:
            admin_user = factory.find_user_by_email('admin@kskp.io')
        # 管理者ユーザのFactoryをOpenする
        cls.factory = Factory(admin_user)
        # AuthzSessionをUserオブジェクトに格納する
        admin_user.session = cls.factory._session
        # テストユーザを作成する
        test_user = cls.factory.user.create('test@kskp.io', 'testpass', 'Test')
        test_user.save()
        # EveryOneグループにテストユーザを加える
        everyone_group = cls.factory.group.load_everyone_group()
        everyone_group.join_user(test_user)
        # テストユーザのFactoryをOpenする
        cls.factory2 = Factory(test_user)
        # クラス変数に設定する
        cls.USER1 = admin_user
        cls.USER2 = test_user

    @classmethod
    def tearDownClass(cls):
        # ライブラリフォルダを削除する
        library_path = STORE_DIR / cls.factory.data.load_root().path
        import shutil
        shutil.rmtree(library_path.as_posix())
        # FactoryをCloseする
        cls.factory.close()
        cls.factory2.close()
        # スキーマを破棄する
        from kskp.store import engine
        from sqlalchemy import DDL
        engine.execute(DDL('DROP SCHEMA IF EXISTS %s CASCADE' % os.environ['KSKP_POSTGRESQL_SCHEMA_NAME']))
