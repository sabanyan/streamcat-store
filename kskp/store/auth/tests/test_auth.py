import unittest
import pprint
from sqlalchemy.orm.exc import NoResultFound
from kskp.core import Datum
from kskp.store.auth import Auth, NotAuthorizedException
from ...tests.test_case_base import TestCaseBase

class AuthTest(TestCaseBase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_create_get_delete_user(self):
        """
        Userの作成・取得・削除を検証する
        """
        # 新規ユーザを追加する
        new_user = self.factory.user.create('test-man@kskp.io', 'tesepass', 'I AM TEST')
        new_user.save()

        # 新規ユーザを取得する
        new_user = self.factory.user.find_by_email('test-man@kskp.io')
        # 取得したユーザの値を検証する
        self.assertIsNotNone(new_user.id)
        self.assertIsNotNone(new_user.uuid)
        self.assertEqual(new_user.email, 'test-man@kskp.io')
        self.assertEqual(new_user.password, 'a7c87fc346ff10b75e7b83a3bf0f51cf449b6dcdc626a9ddffc0a88ec2d7bd91')
        self.assertEqual(new_user.name, 'I AM TEST')
        self.assertIsNone(new_user.self_group_id)
        self.assertEqual(new_user.creator, self.USER1)
        self.assertEqual(new_user.modifier, self.USER1)
        self.assertIsNotNone(new_user.created_at)
        self.assertIsNotNone(new_user.modified_at)
        self.assertEqual(new_user.created_at, new_user.modified_at)

        # 新規ユーザを削除する
        new_user.delete()
        # 削除後のユーザは取得できない
        with self.assertRaises(NoResultFound):
            self.factory.user.find_by_email('test-man@kskp.io')

    def test_create_get_delete_group(self):
        """
        Groupの作成・取得・削除を検証する
        """
        # 新規グループを追加する
        new_group = self.factory.group.create('TEST GROUP')
        new_group.save()

        # 新規グループを取得する
        new_group = self.factory.group.find_by_id(new_group.id)
        # 取得したグループの値を検証する
        self.assertIsNotNone(new_group.id)
        self.assertIsNotNone(new_group.uuid)
        self.assertEqual(new_group.name, 'TEST GROUP')
        self.assertEqual(new_group.creator, self.USER1)
        self.assertEqual(new_group.modifier, self.USER1)
        self.assertIsNotNone(new_group.created_at)
        self.assertIsNotNone(new_group.modified_at)
        self.assertEqual(new_group.created_at, new_group.modified_at)

        # 新規ユーザを削除する
        new_group.delete()
        # 削除後のユーザは取得できない
        with self.assertRaises(NoResultFound):
            self.factory.group.find_by_uuid(new_group.uuid)
    
    def test_join_leave_group(self):
        """
        Groupへの参加と脱退を検証する
        """
        # 新規グループを追加する
        new_group = self.factory.group.create('グループ')
        new_group.save()

        # 新規グループにユーザを参加させる
        new_group.join_user(self.USER2)

        # UserGroupを取得する
        user_group = self.factory.user_group.find_by_id(self.USER2.id, new_group.id)
        # 取得したUserGroupを検証する
        self.assertIsNotNone(user_group.user_id, self.USER2.id)
        self.assertIsNotNone(user_group.group_id, new_group.id)
        self.assertEqual(user_group.creator, self.USER1)
        self.assertEqual(user_group.modifier, self.USER1)
        self.assertIsNotNone(user_group.created_at)
        self.assertIsNotNone(user_group.modified_at)
        self.assertEqual(user_group.created_at, user_group.modified_at)
        
        # ユーザを脱退させる
        new_group.leave_user(self.USER2)

    def test_create_get_delete_auth(self):
        """
        Authの作成・取得・削除を検証する
        """
        # 新規グループを追加する
        new_group = self.factory.group.create('権限グループ')
        new_group.save()

        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフォルダを作成する
        folder = root.create_folder('フォルダQ')
        folder.save()
        folder = self.factory.data.find_by_id(folder.id)

        # 新規権限を追加する
        new_auth = self.factory.auth.create(new_group.id, folder.id, Auth.WRITE_OP, True)
        new_auth.save()

        # 新規権限を取得する
        new_auth = self.factory.auth.find_by_id(new_group.id, folder.id, Auth.WRITE_OP)
        # 取得した権限を検証する
        self.assertIsNotNone(new_auth.group_id, new_group.id)
        self.assertIsNotNone(new_auth.datum_id, folder.id)
        self.assertIsNotNone(new_auth.operation, Auth.WRITE_OP)
        self.assertIsNotNone(new_auth.permission, True)
        self.assertEqual(new_auth.creator, self.USER1)
        self.assertEqual(new_auth.modifier, self.USER1)
        self.assertIsNotNone(new_auth.created_at)
        self.assertIsNotNone(new_auth.modified_at)
        self.assertEqual(new_auth.created_at, new_auth.modified_at)

        # 新規権限を削除する
        folder.delete()
        # 削除後の権限は取得できない
        with self.assertRaises(Exception):
            self.factory.auth.find_by_id(new_group.id, folder.id, Auth.WRITE_OP)

    def test_readless_frame(self):
        """
        参照権限のないFrameは読み取れないことを検証する
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフレームを作成する
        import io
        f = io.BytesIO(b'')
        frame = root.create_frame('CSV', f)
        frame.save()
        frame = self.factory.data.find_by_id(frame.id)

        # フレームの参照権限を全て削除する
        self.factory.auth.delete_all_by_datum_id(frame.id)

        # 
        # 参照権限の削除後にframeオブジェクトのreadableをexpireした方がいい？
        # 
        # from kskp.core import Datum
        # d = self._session.query(Datum).filter(Datum.id==datum_id).one()
        # self._session._session.expire(d, ['readable'])
        # # 
        

        # フレームのreadableはFalseであること
        self.assertFalse(frame.readable)

        # フレームのpathは取得できないこと
        with self.assertRaises(NotAuthorizedException):
            frame.path

        # フレームは更新可能
        frame.update_label('WOW')
        frame.update_label_only('WOW')
        frame.update_encoding_newline(encoding_str='S_JIS', newline_str='\r')

        # フレームは削除可能
        frame.delete()
