import io
import unittest
import pprint
from sqlalchemy.orm.exc import NoResultFound
from kskp.core import Datum
from kskp.store import ProjectFolder
from kskp.store.auth import Auth, NotAuthorizedException
from ...tests.test_case_base import TestCaseBase

class AuthTest(TestCaseBase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    # 
    # SQLAlchemy Session
    # 

    def test_after_create_data(self):
        """
        新規作成したDatumはDBに保存するまで権限フリーであること
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフォルダを作成する
        folder = root.create_folder('Folder!')
        # ルートフォルダの下にFlowを作成する
        flow = root.create_flow('Flow!', {})
        # ルートフォルダの下にフレームを作成する
        frame = root.create_frame('Frame!', io.BytesIO(b''))

        # フォルダの参照と更新と実行権限は付与されていること
        self.assertTrue(folder.readable)
        self.assertTrue(folder.writable)
        self.assertTrue(folder.executable)

        # Flowの参照と更新と実行権限は付与されていること
        self.assertTrue(flow.readable)
        self.assertTrue(flow.writable)
        self.assertTrue(flow.executable)

        # フレームの参照と更新権限は付与されていること
        # (フレームなので実行権限はない)
        self.assertTrue(frame.readable)
        self.assertTrue(frame.writable)
        self.assertFalse(frame.executable)

        # フォルダを保存する
        folder.save()
        # Flowを保存する
        flow.save()
        # フレームを保存する
        frame.save()

        # 保存後は全ての権限はNoneに設定される
        self.assertIsNone(folder.readable)
        self.assertIsNone(folder.writable)
        self.assertIsNone(folder.executable)
        self.assertIsNone(flow.readable)
        self.assertIsNone(flow.writable)
        self.assertIsNone(flow.executable)
        self.assertIsNone(frame.readable)
        self.assertIsNone(frame.writable)
        self.assertIsNone(frame.executable)

        # フォルダを再読み込みする
        folder.reload()
        # Flowを再読み込みする
        flow.reload()
        # フレームを再読み込みする
        frame.reload()

        # フォルダを削除する
        folder.delete()
        # Flowを削除する
        flow.delete()
        # フレームを削除する
        frame.delete()

    def test_set_session_datum_property(self):
        """
        SessionからDatumを抽出したら
        Datum._sessionプロパティにSessionが設定されていること
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフレームを作成する
        frame = root.create_frame('Frame!', io.BytesIO(b''))

        # 新規作成したら_sessionプロパティが設定されること
        self.assertIs(frame._session, self.factory._session)

        # フレームを保存する
        frame.save()

        # 保存後も_sessionプロパティを取得できること
        self.assertIs(frame._session, self.factory._session)

        # find_by_id()でフレームを取得する
        frame = self.factory.data.find_by_id(frame.id)

        # Sessionクラスで_sessionプロパティが設定されること
        self.assertIs(frame._session, self.factory._session)

        # find_by_uuid()でフレームを取得する
        frame = self.factory.data.find_by_uuid(frame.uuid)

        # Sessionクラスで_sessionプロパティが設定されること
        self.assertIs(frame._session, self.factory._session)

        # フレームを削除する
        frame.delete()

    def test_set_session_role_property(self):
        """
        SessionからRoleを抽出したら
        Role._sessionプロパティにSessionが設定されていること
        """
        # ロールを作成する
        role = self.factory.role.create('Role!')

        # 新規作成したら_sessionプロパティが設定されること
        self.assertIs(role._session, self.factory._session)

        # ロールを保存する
        role.save()

        # 保存後も_sessionプロパティを取得できること
        self.assertIs(role._session, self.factory._session)

        # frame_by_id()でロールを取得する
        role = self.factory.role.find_by_id(role.id)

        # Sessionクラスで_sessionプロパティが設定されること
        self.assertIs(role._session, self.factory._session)

        # frame_by_uuid()でロールを取得する
        role = self.factory.role.find_by_uuid(role.uuid)

        # Sessionクラスで_sessionプロパティが設定されること
        self.assertIs(role._session, self.factory._session)

        # ロールを全権取得する、全てのロールに_sessionプロパティが設定される
        for role in self.factory.role.find_all():
            self.assertIs(role._session, self.factory._session)

        # ロールを削除する
        role.delete()

    def test_session_rollback(self):
        """
        SQLAlchemyのSession.rollback()によりExpireが発生し、
        全てのDatum._permissionsがNoneになってしまう
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()

        # ルートフォルダの下にフォルダを作成する
        folder = root.create_folder('FOLDER')
        folder.save()
        folder = folder.reload()

        # reload直後はDatum._permissions=True
        self.assertTrue(folder.readable)
        self.assertTrue(folder.writable)
        self.assertTrue(folder.executable)

        # Session.rollback()
        folder._session.rollback()

        # Datum._permissionsがNoneに変化してしまう
        self.assertIsNone(folder.readable)
        self.assertIsNone(folder.writable)
        self.assertIsNone(folder.executable)

        # フォルダを再読み込みした後、削除する
        folder = folder.reload()
        folder.delete()

    # 
    # Users
    # 

    def test_create_get_delete_user(self):
        """
        Userの作成・取得・削除を検証する
        """
        # 新規ユーザを追加する
        new_user = self.factory.user.create('test-man@kskp.io', 'I AM TEST', 'tesepass')
        new_user.save()

        # 新規ユーザを取得する
        new_user = self.factory.user.find_by_email('test-man@kskp.io')
        # 取得したユーザの値を検証する
        self.assertIsNotNone(new_user.id)
        self.assertIsNotNone(new_user.uuid)
        self.assertEqual(new_user.email, 'test-man@kskp.io')
        self.assertEqual(new_user.name, 'I AM TEST')
        self.assertIsNone(new_user.self_role_id)
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

    def test_create_user_by_user(self):
        """
        一般ユーザは、ユーザの作成ができないこと
        """
        # 新規ユーザを追加する
        new_user = self.factory2.user.create('test-man2@kskp.io', 'I AM TEST', 'tesepass')
        with self.assertRaises(NotAuthorizedException):
            new_user.save()

    def test_update_user_by_user(self):
        """
        一般ユーザは、他ユーザの変更ができないこと
        """
        # 新規ユーザを追加する
        new_user = self.factory.user.create('test-man3@kskp.io', 'I AM TEST', 'tesepass')
        new_user.save()

        # 他ユーザで再取得する
        new_user = self.factory2.user.find_by_uuid(new_user.uuid)
        new_user_password = new_user.password

        # E-Mailを変更する
        with self.assertRaises(NotAuthorizedException):
            new_user.update_email('abc@abc.com')

        # パスワードを変更する
        with self.assertRaises(NotAuthorizedException):
            new_user.update_password('abc')

        # ユーザ名を変更する
        with self.assertRaises(NotAuthorizedException):
            new_user.update_name('new name')

        # ユーザ名・E-Mail・パスワードは変更されていないこと
        self.assertEqual(new_user.email, 'test-man3@kskp.io')
        self.assertEqual(new_user.password, new_user_password)
        self.assertEqual(new_user.name, 'I AM TEST')

    def test_delete_user_by_user(self):
        """
        一般ユーザは、他ユーザの削除ができないこと
        """
        # 新規ユーザを追加する
        new_user = self.factory.user.create('test-man4@kskp.io', 'I AM TEST', 'tesepass')
        new_user.save()

        # 他ユーザで再取得する
        new_user = self.factory2.user.find_by_uuid(new_user.uuid)

        # 新規ユーザを削除する
        with self.assertRaises(NotAuthorizedException):
            new_user.delete()

        # 削除後のユーザは取得できる
        new_user = self.factory.user.find_by_email('test-man4@kskp.io')
        self.assertIsNotNone(new_user)

    # 
    # Roles
    # 

    def test_create_get_delete_role(self):
        """
        Roleの作成・取得・削除を検証する
        """
        # 新規ロールを追加する
        new_role = self.factory.role.create('TEST ROLE')
        new_role.save()

        # 新規ロールを取得する
        new_role = self.factory.role.find_by_id(new_role.id)
        # 取得したロールの値を検証する
        self.assertIsNotNone(new_role.id)
        self.assertIsNotNone(new_role.uuid)
        self.assertEqual(new_role.name, 'TEST ROLE')
        self.assertEqual(new_role.creator, self.USER1)
        self.assertEqual(new_role.modifier, self.USER1)
        self.assertIsNotNone(new_role.created_at)
        self.assertIsNotNone(new_role.modified_at)
        self.assertEqual(new_role.created_at, new_role.modified_at)

        # 新規ロールを削除する
        new_role.delete()
        # 削除後のロールは取得できない
        with self.assertRaises(NoResultFound):
            self.factory.role.find_by_uuid(new_role.uuid)

    def test_create_get_delete_role_by_user(self):
        """
        一般ユーザは、自身が作成したRoleの取得・更新・削除をできること
        """
        # ロールを追加する
        new_role = self.factory2.role.create('MY ROLE')
        new_role.save()

        # ロールを取得する
        new_role = self.factory2.role.find_by_id(new_role.id)

        # ロール名を変更する
        new_role.update_name('my role')

        # 変更したロール名を検証する
        new_role = self.factory2.role.find_by_id(new_role.id)
        self.assertEqual(new_role.name, 'my role')

        # 新規ロールを削除する
        new_role.delete()
        # 削除後のロールは取得できない
        with self.assertRaises(NoResultFound):
            self.factory2.role.find_by_uuid(new_role.uuid)
  
    def test_join_leave_role(self):
        """
        Roleへの参加と脱退を検証する
        """
        # 新規ロールを追加する
        new_role = self.factory.role.create('ロール')
        new_role.save()

        # 新規ロールにユーザを参加させる
        new_role.join_user(self.USER2)

        # UserRoleを取得する
        user_role = self.factory.user_role.find_by_id(self.USER2.id, new_role.id)
        # 取得したUserRoleを検証する
        self.assertIsNotNone(user_role.user_id, self.USER2.id)
        self.assertIsNotNone(user_role.role_id, new_role.id)
        self.assertEqual(user_role.creator, self.USER1)
        self.assertEqual(user_role.modifier, self.USER1)
        self.assertIsNotNone(user_role.created_at)
        self.assertIsNotNone(user_role.modified_at)
        self.assertEqual(user_role.created_at, user_role.modified_at)
        
        # ユーザを脱退させる
        new_role.leave_user(self.USER2)

    def test_join_role_on_no_auth(self):
        """
        Roleにユーザを追加できるのは管理者かRoleの作成者のみである
        """
        # ロールを作成する
        new_role = self.factory.role.create('ロール')
        new_role.save()

        # 管理者でもRoleの作成者でもないユーザは、
        # ユーザの追加操作はできない
        new_role = self.factory2.role.find_by_uuid(new_role.uuid)
        with self.assertRaises(NotAuthorizedException):
            new_role.join_user(self.USER2)

    def test_leave_role_on_no_auth(self):
        """
        Roleからユーザを削除できるのは管理者かRoleの作成者のみである
        """
        # ロールを作成する
        new_role = self.factory.role.create('ロール')
        new_role.save()

        # ロールにユーザを追加する
        new_role.join_user(self.USER2)

        # 管理者でもRoleの作成者でもないユーザは、
        # ユーザの削除操作はできない
        new_role = self.factory2.role.find_by_uuid(new_role.uuid)
        with self.assertRaises(NotAuthorizedException):
            new_role.leave_user(self.USER2)

    # 
    # Auths
    # 

    def test_create_get_delete_auth(self):
        """
        Authの作成・取得・削除を検証する
        """
        # 新規ロールを追加する
        new_role = self.factory.role.create('権限ロール')
        new_role.save()

        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフォルダを作成する
        folder = root.create_folder('フォルダQ')
        folder.save()
        folder = self.factory.data.find_by_id(folder.id)

        # 新規権限を追加する
        new_auth = self.factory.auth.create(new_role.id, folder.id, Auth.WRITE_OP, True)
        new_auth.save()

        # 新規権限を取得する
        new_auth = self.factory.auth.find_by_id(new_role.id, folder.id, Auth.WRITE_OP)
        # 取得した権限を検証する
        self.assertIsNotNone(new_auth.role_id, new_role.id)
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
            self.factory.auth.find_by_id(new_role.id, folder.id, Auth.WRITE_OP)

    def test_create_get_delete_auth_by_user(self):
        """
        一般ユーザは、自身が作成したDatumの権限を取得・更新・削除をできること
        """
        # 新規ロールを追加する
        new_role = self.factory2.role.create('権限ロール')
        new_role.save()

        # ルートフォルダを取得する
        root = self.factory2.data.load_root()
        # ルートフォルダの下にフォルダを作成する
        folder = root.create_folder('フォルダS')
        folder.save()
        folder = self.factory2.data.find_by_id(folder.id)

        # 新規権限を追加する
        new_auth = self.factory2.auth.create(new_role.id, folder.id, Auth.WRITE_OP, True)
        new_auth.save()

        # 新規権限を取得する
        new_auth = self.factory2.auth.find_by_id(new_role.id, folder.id, Auth.WRITE_OP)

        # 新規権限を削除する
        folder.delete()
        # 削除後の権限は取得できない
        with self.assertRaises(Exception):
            self.factory2.auth.find_by_id(new_role.id, folder.id, Auth.WRITE_OP)

    def test_create_get_delete_auth_by_other_user(self):
        """
        一般ユーザは、他ユーザが作成したDatumの権限を取得・更新・削除をできないこと
        """
        # 新規ロールを追加する
        new_role = self.factory2.role.create('権限ロール')
        new_role.save()

        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフォルダを作成する
        folder = root.create_folder('フォルダT')
        folder.save()

        # フォルダを取得する
        folder = self.factory2.data.find_by_id(folder.id)

        # 新規権限を追加する
        new_auth = self.factory3.auth.create(new_role.id, folder.id, Auth.WRITE_OP, True)
        with self.assertRaises(NotAuthorizedException):
            new_auth.save()

        # 新規権限を取得する
        with self.assertRaises(Exception):
            self.factory3.auth.find_by_id(new_role.id, folder.id, Auth.WRITE_OP)

        # 新規権限を削除する
        with self.assertRaises(NotAuthorizedException):
            new_auth.delete()

    def test_no_authz(self):
        """
        権限レコードのないFrameは読み取れないことを検証する
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフレームを作成する
        frame = root.create_frame('CSV', io.BytesIO(b''))
        frame.save()

        # フレームの参照権限を全て削除する
        self.factory.auth.delete_all_by_datum_id(frame.id)

        # フローを再取得する
        frame = frame.reload()

        # フレームのpermissionsはNoneであること
        self.assertFalse(frame.readable)
        self.assertFalse(frame.writable)
        self.assertFalse(frame.executable)

        # フレームのpathは取得できないこと
        with self.assertRaises(NotAuthorizedException):
            frame.path

        # フレームは更新できないこと
        with self.assertRaises(NotAuthorizedException):
            frame.update_label('csv')

        # フレームは削除できないこと
        with self.assertRaises(NotAuthorizedException):
            frame.delete()

    def test_readless_frame(self):
        """
        参照権限のないFrameは読み取れないことを検証する
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフレームを作成する
        frame = root.create_frame('CSV', io.BytesIO(b''))
        frame.save()
        frame = frame.reload()

        # フレームの参照権限を全て削除する
        self.factory.auth.delete_all_by_datum_id(frame.id)




        # 
        # 参照権限の削除後にframeオブジェクトのpermissionsをexpireした方がいい？
        #         
        persistent_obj = self.factory._session._session.identity_map.values()
        for obj in persistent_obj:
            if isinstance(obj, Datum):
                self.factory._session._session.expire(obj, ['_permissions'])



        # フレームのpermissionsはNoneであること
        self.assertIsNone(frame.readable)
        self.assertIsNone(frame.writable)
        self.assertIsNone(frame.executable)

        # フレームのpathは取得できないこと
        with self.assertRaises(NotAuthorizedException):
            frame.path

    def test_writeless_frame(self):
        """
        更新権限のないFrameは更新できないことを検証する
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフレームを作成する
        frame = root.create_frame('CSV', io.BytesIO(b''))
        frame.save()
        frame = frame.reload()

        # フレームの更新権限を全て削除する
        self.factory.auth.delete_all_by_datum_id(frame.id)

         # フレームは更新不可
        with self.assertRaises(NotAuthorizedException):
            frame.update_label('WOW')
        with self.assertRaises(NotAuthorizedException):
            frame.update_label_only('WOW')
        with self.assertRaises(NotAuthorizedException):
            frame.update_encoding_newline(encoding_str='S_JIS', newline_str='CR')

        # フレームは削除不可
        with self.assertRaises(NotAuthorizedException):
            frame.delete()

    def test_readless_folder(self):
        """
        参照権限のないFolderは読み取れないことを検証する
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフォルダを作成する
        folder = root.create_folder('参照権限のないフォルダ')
        folder.save()
        folder = folder.reload()
        # フォルダの下にフローを作成する
        flow = folder.create_flow('フロー', {})
        flow.save()
        flow = flow.reload()

        # フォルダの参照権限を全て削除する
        self.factory.auth.delete_all_by_datum_id(folder.id)


        # 
        # 参照権限の削除後にframeオブジェクトのpermissionsをexpireした方がいい？
        #         
        persistent_obj = self.factory._session._session.identity_map.values()
        for obj in persistent_obj:
            if isinstance(obj, Datum):
                self.factory._session._session.expire(obj, ['_permissions'])


        # フローのpermissionsはNoneであること
        self.assertIsNone(flow.readable)
        self.assertIsNone(flow.writable)
        self.assertIsNone(flow.executable)

        # フォルダ内のDatumは参照できないこと
        with self.assertRaises(NotAuthorizedException):
            folder.find_children()
        with self.assertRaises(NotAuthorizedException):
            folder.find_children_by_label('フロー')
        with self.assertRaises(NotAuthorizedException):
            folder.find_child_by_uuid(flow.uuid)

    def test_writeless_folder(self):
        """
        更新権限のないFolderは更新できないことを検証する
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフォルダを作成する
        folder = root.create_folder('更新権限のないフォルダ')
        folder.save()
        folder = folder.reload()
        # フォルダの下にフローを作成する
        flow = folder.create_flow('フロー', {})
        flow.save()
        flow = flow.reload()

        # フォルダの更新権限を全て削除する
        self.factory.auth.delete_all_by_datum_id(folder.id)

        # フローは更新不可
        with self.assertRaises(NotAuthorizedException):
            flow.update_data('WOW', {})

        # フローは削除不可
        with self.assertRaises(NotAuthorizedException):
            flow.delete()

    def test_resolve_roles(self):
        """
        複数のロールで異なる権限判定の場合
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフローを作成する
        flow = root.create_flow('フロー', {})
        flow.save()

        # フローの参照権限を全て削除する
        self.factory.auth.delete_all_by_datum_id(flow.id)

        # ロールAを作成する
        roleA = self.factory.role.create('roleA')
        roleA.save()
        # ロールBを作成する
        roleB = self.factory.role.create('roleB')
        roleB.save()

        # ロールAにフローの参照・更新許可を付与する
        roleA.init_authz(flow.id, True, True)
        # ロールBにフローの参照・更新不可を付与する
        roleB.init_authz(flow.id, False, False)

        # TESTユーザをロールAとロールBに参加させる
        roleA.join_user(self.USER2)
        roleB.join_user(self.USER2)

        # フローを再取得する
        flow = flow.reload()

        # フローのreadable,writable,executableはFalseであること
        self.assertFalse(flow.readable)
        self.assertFalse(flow.writable)
        self.assertFalse(flow.executable)

        # フレームのpathは取得できないこと
        with self.assertRaises(NotAuthorizedException):
            flow.path

        # フローは更新不可
        with self.assertRaises(NotAuthorizedException):
            flow.update_data('WOW!', {})

        # フローは削除不可
        with self.assertRaises(NotAuthorizedException):
            flow.delete()

    def test_read_data_of_frame(self):
        """
        参照権限のないFrameでもdataプロパティは読み取れること
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフレームを作成する
        frame = root.create_frame('CSV2', io.BytesIO(b''))
        frame.save()

        # フレームの参照権限を全て削除する
        self.factory.auth.delete_all_by_datum_id(frame.id)

        # フローを再取得する
        frame = frame.reload()

        # フレームのreadable,writable,executableはFalseであること
        self.assertFalse(frame.readable)
        self.assertFalse(frame.writable)
        self.assertFalse(frame.executable)

        # フレームのメタデータは取得できること
        self.assertEqual(frame.encoding_str, 'UNKNOWN')
        self.assertEqual(frame.newline_str, 'UNKNOWN')

    def test_read_data_of_flow(self):
        """
        参照権限のないFlowのnodesキーは読み取れないこと
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフレームを作成する
        frame = root.create_frame('CSV2', io.BytesIO(b''))
        frame.save()
        # ルートフォルダの下にフローを作成する
        flow = root.create_simple_flow('フロー', frame)
        flow.save()

        # フレームの参照権限を全て削除する
        self.factory.auth.delete_all_by_datum_id(flow.id)

        # フローを再取得する
        flow = flow.reload()

        # フローJSONのうちnodes以外のキーは取得できること
        self.assertEqual(flow.flow_data.label, 'フロー')
        self.assertEqual(flow.flow_data.description, '')
        self.assertEqual(flow.flow_data.ports, [[],[]])
        self.assertTrue(flow.flow_data.has_nodes)

        # フローJSONのうちnodesキーは取得できないこと
        with self.assertRaises(NotAuthorizedException):
            flow.flow_data.get_nodes()

    def test_read_flow_by_self_role(self):
        """
        本人グループにのみ参照可能なFlowを参照できること
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフローを作成する
        flow = root.create_flow('所有者のみ参照できるフロー', {})
        flow.save()
        
        # フローの参照権限を全て削除する
        self.factory.auth.delete_all_by_datum_id(flow.id)

        # USER1の本人グループに参照権限を付与する
        self.USER1.load_self_role().init_authz(flow.id, True, False)

        # フローを再取得する
        flow = flow.reload()

        # フローは参照可能
        self.assertTrue(flow.readable)
        # フローは更新、実行不可
        self.assertFalse(flow.writable)
        self.assertFalse(flow.executable)

    def test_read_flow_by_other_role(self):
        """
        本人グループにのみ参照可能なFlowを他ユーザは参照できないこと
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフローを作成する
        flow = root.create_flow('所有者のみ参照できるフロー', {})
        flow.save()

        # フローの参照権限を全て削除する
        self.factory.auth.delete_all_by_datum_id(flow.id)

        # USER1の本人グループに参照権限を付与する
        self.USER1.load_self_role().init_authz(flow.id, True, False)

        # 他ユーザによりフローを取得する
        flow = self.factory2.data.find_by_id(flow.id)

        # フローは参照不可能
        self.assertFalse(flow.readable)
        # フローは更新、実行不可
        self.assertFalse(flow.writable)
        self.assertFalse(flow.executable)

    def test_write_flow_by_self_role(self):
        """
        本人グループにのみ更新可能なFlowを更新できること
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフローを作成する
        flow = root.create_flow('所有者のみ更新できるフロー', {})
        flow.save()
        
        # フローの権限を全て削除する
        self.factory.auth.delete_all_by_datum_id(flow.id)

        # USER1の本人グループに更新権限を付与する
        self.USER1.load_self_role().init_authz(flow.id, False, True)

        # フローを再取得する
        flow = flow.reload()

        # フローは更新可能
        flow.update_data('変更したフロー名', {})

        # フローは更新されていること
        self.assertEqual(flow.label, '変更したフロー名')

    def test_write_flow_by_self_role2(self):
        """
        本人グループにのみ更新可能なフォルダ内にあるFlowを更新できること
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフォルダを作成する
        folder = root.create_folder('所有者のみ更新できるフォルダ')
        folder.save()
        # フォルダの下にフローを作成する
        flow = folder.create_flow('フロー', {})
        flow.save()

        # フォルダとフローの権限を全て削除する
        self.factory.auth.delete_all_by_datum_id(folder.id)
        self.factory.auth.delete_all_by_datum_id(flow.id)

        # USER1の本人グループに更新権限を付与する
        self.USER1.load_self_role().init_authz(folder.id, False, True)
        self.USER1.load_self_role().init_authz(flow.id, False, True)

        # フォルダとフローを再取得する
        folder = folder.reload()
        flow = flow.reload()

        # フローは更新可能
        flow.update_data('変更したフロー名2', {})

        # フローは更新されていること
        self.assertEqual(flow.label, '変更したフロー名2')        

    def test_write_flow_by_other_role(self):
        """
        本人グループにのみ参照可能なFlowを他ユーザは更新できないこと
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフローを作成する
        flow = root.create_flow('所有者のみ更新できるフロー2', {})
        flow.save()
        
        # フローの権限を全て削除する
        self.factory.auth.delete_all_by_datum_id(flow.id)

        # USER1の本人グループに更新権限を付与する
        self.USER1.load_self_role().init_authz(flow.id, False, True)

        # 他ユーザによりフローを取得する
        flow = self.factory2.data.find_by_id(flow.id)

        # フローは更新不可能
        with self.assertRaises(NotAuthorizedException):
            flow.update_data('変更したフロー名2', {})

        # フローは更新されていないこと
        self.assertEqual(flow.label, '所有者のみ更新できるフロー2')

    def test_move(self):
        """
        必要最小限の権限設定でFlowを移動できること
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下に移動元フォルダを作成する
        from_folder = root.create_folder('移動元フォルダ')
        from_folder.save()
        # ルートフォルダの下に移動元フォルダを作成する
        to_folder = root.create_folder('移動先フォルダ')
        to_folder.save()
        # 移動元フォルダの直下にフローを作成する
        flow = from_folder.create_flow('フローA', {})
        flow.save()

        # 移動元フォルダを参照不可にする
        everyone_role = self.factory.role.load_everyone_role()
        everyone_role.init_authz(from_folder.id, False, True)
        # 移動先フォルダを参照・更新可能にする
        everyone_role.init_authz(to_folder.id, True, True)
        # フローを参照不可にする
        everyone_role.init_authz(flow.id, False, True)

        # フローを移動する
        flow.move(to_folder.uuid)

        # フローが移動できること
        self.assertEqual(flow.parent_id, to_folder.id)

    def test_move_from_writeless_folder(self):
        """
        更新権限のないFolderからFlowは移動できないこと
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下に移動元フォルダを作成する
        from_folder = root.create_folder('移動元フォルダ')
        from_folder.save()
        # ルートフォルダの下に移動元フォルダを作成する
        to_folder = root.create_folder('移動先フォルダ')
        to_folder.save()
        # 移動元フォルダの直下にフローを作成する
        flow = from_folder.create_flow('フローB', {})
        flow.save()
        
        # 移動元フォルダを更新不可にする
        everyone_role = self.factory.role.load_everyone_role()
        everyone_role.init_authz(from_folder.id, True, False)
        # 移動先フォルダを更新不可にする
        everyone_role.init_authz(to_folder.id, True, True)
        # フローを参照・更新可能にする
        everyone_role.init_authz(flow.id, True, True)

        # フローを移動する
        # 移動元フォルダが更新不可→フローBの更新不可なので、フローBの更新エラーが発生する
        with self.assertRaises(NotAuthorizedException):
            flow.move(to_folder.uuid)

        # フローが移動していないこと
        self.assertEqual(flow.parent_id, from_folder.id)

    def test_move_to_writeless_folder(self):
        """
        更新権限のないFolderへFlowは移動できないこと
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下に移動元フォルダを作成する
        from_folder = root.create_folder('移動元フォルダ')
        from_folder.save()
        # ルートフォルダの下に移動元フォルダを作成する
        to_folder = root.create_folder('移動先フォルダ')
        to_folder.save()
        # 移動元フォルダの直下にフローを作成する
        flow = from_folder.create_flow('フローC', {})
        flow.save()

        # 移動先フォルダを更新不可にする
        everyone_role = self.factory.role.load_everyone_role()
        everyone_role.init_authz(to_folder.id, True, False)
        # フローを参照・更新可能にする
        everyone_role.init_authz(flow.id, True, True)

        # フローを移動する
        # to_folderが更新不可なのでエラーが発生する
        with self.assertRaises(NotAuthorizedException):
            flow.move(to_folder.uuid)

        # フローが移動していないこと
        self.assertEqual(flow.parent_id, from_folder.id)

    def test_folder_in_writeless_folder(self):
        """
        更新権限のないFolderの直下のFolder内にあるFlowは更新できないこと
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフォルダ1を作成する
        folder1 = root.create_folder('フォルダ1')
        folder1.save()
        # フォルダ1の下にフォルダ2を作成する
        folder2 = folder1.create_folder('フォルダ2')
        folder2.save()
        # フォルダ2の下にフローを作成する
        flow = folder2.create_flow('myFlow', {})
        flow.save()

        # フォルダ1を更新不可にする
        everyone_role = self.factory.role.load_everyone_role()
        everyone_role.init_authz(folder1.id, True, False)
        
        # フォルダ1は更新できない
        with self.assertRaises(NotAuthorizedException):
            folder1.update_data('フォルダ10')

        # フォルダ2は更新できない
        with self.assertRaises(NotAuthorizedException):
            folder2.update_data('フォルダ20')

        # フローは更新できないこと
        with self.assertRaises(NotAuthorizedException):
            flow.update_data('myFlow0', {})

        # フォルダ2にフローを新規追加できないこと
        flow2 = folder2.create_flow('myFlow1', {})
        with self.assertRaises(NotAuthorizedException):
            flow2.save()

    def test_del_folder_has_writeless_flow(self):
        """
        更新権限のないFlowは親フォルダごと削除できないこと
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフォルダAを作成する
        folder = root.create_folder('フォルダA')
        folder.save()
        folder = folder.reload()
        # フォルダAの下にフロー1を作成する
        flow1 = folder.create_flow('更新できないフロー', {})
        flow1.save()

        # フローを更新不可にする
        everyone_role = self.factory.role.load_everyone_role()
        everyone_role.init_authz(flow1.id, True, False)

        # フォルダAをほかす
        # (削除できませんでした)
        # (なお、フォルダ内のファイルが1つでもほかすことができたら例外は送出しない)
        with self.assertRaises(Exception):
            folder.throw_away()

        # フォルダAを削除する
        # (空でないフォルダは削除できません)
        with self.assertRaises(Exception):
            folder.delete()

        # flow1はほかされていないこと
        self.assertTrue(self.factory.data.exists(flow1.uuid))
        self.assertEqual(flow1.parent_id, folder.id)
        self.assertEqual(folder.parent_id, root.id)

    def test_exec_execless_flow(self):
        """
        実行権限のないFlowは実行できないこと
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフォルダAを作成する
        folder = root.create_folder('フォルダA')
        folder.save()
        # フォルダAの下にフロー1を作成する
        flow = folder.create_flow('実行できないフロー', {})
        flow.save()

        # フローを実行不可にする
        everyone_role = self.factory.role.load_everyone_role()
        everyone_role.init_authz(flow.id, True, True, exec=False)

        # フローJSONのnodesを取得する
        with self.assertRaises(NotAuthorizedException):
            flow.flow_data.get_nodes(use_exec_auth=True)

        # フローを実行可にする
        everyone_role.init_authz(folder.id, False, False, exec=True)
        everyone_role.init_authz(flow.id, False, False, exec=True)

        # フローを再取得するまでは実行不可のママである
        with self.assertRaises(NotAuthorizedException):
            flow.flow_data.get_nodes(use_exec_auth=True)

        # フローを再取得する
        flow = flow.reload()

        # フローJSONのnodesを取得dekirukoto
        flow.flow_data.get_nodes(use_exec_auth=True)

    def test_own_frame_in_no_own_folder(self):
        """
        フレームの所有権は親フォルダの所有権に影響しないこと
        (フォルダの所有権はオーバーライドされない)
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()

        # ルートフォルダの下にフォルダAを作成する (所有者はUSER2)
        folder_a = root.create_folder('所有権の無いフォルダA')
        folder_a.save()

        # USER3にフォルダAの更新権限を付与する
        user3 = self.factory2.user.find_by_uuid(self.USER3.uuid)
        user3.load_self_role().init_authz(folder_a.id, read=True, write=True)

        # フォルダAの下にフレームAを作成する (所有者はUSER3)
        folder_a = self.factory3.data.find_by_uuid(folder_a.uuid)
        frame_a = folder_a.create_frame('My Frame A', io.BytesIO(b''))
        frame_a.save()

        # ルートフォルダの下にフォルダBを作成する (所有者はUSER3)
        root = self.factory3.data.load_root()
        folder_b = root.create_folder('所有権の有るフォルダB')
        folder_b.save()

        # フォルダBの下にフレームBを作成する (所有者はUSER3)
        frame_b = folder_b.create_frame('My Frame B', io.BytesIO(b''))
        frame_b.save()

        # フレームAの所有者は権限を変更できること
        self_role = self.USER3.load_self_role()
        self_role.init_authz(frame_a.id, read=None, write=False, own=True)

        # フレームBの所有者は権限を変更できること
        self_role.init_authz(frame_b.id, read=None, write=False, own=True)

        # 更新権限が否定されたのでフレームA,Bは削除できないこと
        with self.assertRaises(NotAuthorizedException):
            frame_a.delete()
        with self.assertRaises(NotAuthorizedException):
            frame_b.delete()

        # フレームA,Bに更新権限を付与する
        self_role.init_authz(frame_a.id, read=None, write=True)
        self_role.init_authz(frame_b.id, read=None, write=True)

        # # フレームA,Bを削除する
        frame_a.delete()
        frame_b.delete()

        # NotAuthorizedExceptionの送出後のSession.rollback()により、
        # Expireが発生し、readable=Noneとなるため再読み込みする
        folder_a = folder_a.reload()
        folder_b = folder_b.reload()

        # フォルダA,Bを削除する
        folder_a.delete()
        folder_b.delete()

    def test_override_permissions(self):
        """
        参照・更新・実行の権限がフォルダ階層においてオーバライドされること
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()

        # ルートフォルダの下にフォルダ1を作成する
        folder1 = root.create_folder('folder 1')
        folder1.save()
        # フォルダ1の下にフォルダ2を作成する
        folder2 = folder1.create_folder('folder 2')
        folder2.save()
        # フォルダ2の下にフォルダ3を作成する
        folder3 = folder2.create_folder('folder 3')
        folder3.save()
        # フォルダ3の下にフォルダ4を作成する
        folder4 = folder3.create_folder('folder 4')
        folder4.save()

        # フォルダ4の下にフレームを作成する
        frame = folder4.create_frame('フレームファイル♪', io.BytesIO(b'abc'))
        frame.save()

        # ルートフォルダの下にフローを作成する
        flow = folder4.create_simple_flow('フロー', frame)
        flow.save()

        # フォルダ1の参照権限を全て削除する
        self.factory.auth.delete_all_by_datum_id(folder1.id)

        # 
        # フレームを再取得する
        # 
        frame = frame.reload()

        # フレームのreadable,writable,executableはFalseであること
        self.assertFalse(frame.readable)
        self.assertFalse(frame.writable)
        self.assertFalse(frame.executable)

        # フレームのpathは取得できないこと
        with self.assertRaises(NotAuthorizedException):
            frame.path

        # フレームの更新はできないこと
        with self.assertRaises(NotAuthorizedException):
            frame.update_label('flame_file')

        # フレームは削除できないこと
        with self.assertRaises(NotAuthorizedException):
            frame.delete()

        # 
        # フローを再取得する
        # 
        flow = flow.reload()

        # フローのreadable,writable,executableはFalseであること
        self.assertFalse(flow.readable)
        self.assertFalse(flow.writable)
        self.assertFalse(flow.executable)

        # フローJSONのうちnodes以外のキーは取得できること
        self.assertEqual(flow.flow_data.label, 'フロー')
        self.assertEqual(flow.flow_data.description, '')
        self.assertEqual(flow.flow_data.ports, [[],[]])
        self.assertTrue(flow.flow_data.has_nodes)

        # フローJSONのうちnodesキーは取得できないこと
        with self.assertRaises(NotAuthorizedException):
            flow.flow_data.get_nodes()

        # フローの更新はできないこと
        with self.assertRaises(NotAuthorizedException):
            flow.update_data('flame_file', {})

        # フローは削除できないこと
        with self.assertRaises(NotAuthorizedException):
            flow.delete()

    # 
    # Projects
    # 

    def test_cannot_save_project_outside_root(self):
        """
        プロジェクトはルートフォルダ直下にしか保存できないこと
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()

        # ルートフォルダの下にプロジェクトを作成する
        project0 = root.create_project_folder('プロジェクト0')
        project0.save()
        project0 = project0.reload()
        # プロジェクトの下にプロジェクトを作成する
        with self.assertRaises(Exception):
            sub_project0 = project0.create_project_folder('Subプロジェクト0')
            sub_project0.save()

        # ルートフォルダの下にフォルダを作成する
        folder = root.create_folder('フォルダ0')
        folder.save()
        folder = folder.reload()
        # フォルダの下にプロジェクトを作成する
        with self.assertRaises(Exception):
            sub_project0 = folder.create_project_folder('Subプロジェクト0')
            sub_project0.save()

    def test_cannot_move_project(self):
        """
        ゴミ箱へにほかされるか、ゴミ箱から元の場所に戻す場合を除いて、プロジェクトは移動できない
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()

        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('移動できないぜProject')
        project.save()
        project = project.reload()

        # ルートフォルダの下にフォルダを作成する
        folder = root.create_folder('フォルダだぜ')
        folder.save()
        folder = folder.reload()

        # プロジェクトをフォルダの下に移動する
        with self.assertRaises(Exception):
            project.move(folder.uuid)

    def test_throw_away_project(self):
        """
        プロジェクトはゴミ箱にほかせること
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()

        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('ゴミプロジェクト')
        project.save()
        project = project.reload()

        # プロジェクトの下にフローを作成する
        flow = project.create_flow('フロー', {})
        flow.save()
        flow = flow.reload()

        # プロジェクトの下にフレームを作成する
        frame = project.create_frame('フレーム', io.BytesIO(b''))
        frame.save()
        frame = frame.reload()

        # プロジェクトをほかす
        project.throw_away()

        # プロジェクトがゴミ箱に存在すること
        self.assertTrue(self.factory.data.trashed(project.uuid))
        self.assertTrue(self.factory.data.trashed(flow.uuid))
        self.assertTrue(self.factory.data.trashed(frame.uuid))

        # プロジェクトを元の場所に戻す
        project.put_back()

        # プロジェクトが元の場所に存在すること
        self.assertEqual(project.find_parent().id, root.id)

        # プロジェクトを再度ほかして、ゴミ箱を空にする
        project.throw_away()
        self.factory.data.find_trashcan().trash_all()

        # プロジェクトは削除されていること
        self.assertFalse(self.factory.data.exists(project.uuid))
        self.assertFalse(self.factory.data.exists(flow.uuid))
        self.assertFalse(self.factory.data.exists(frame.uuid))

    def test_cannot_move_datum(self):
        """
        プロジェクト以外のDatumはルートフォルダへ移動できない
        """
        pass

    def test_delete_project(self):
        """
        プロジェクト管理者はプロジェクトを削除できる
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()

        # ルートフォルダの下にプロジェクトを作成する
        # 作成者(=プロジェクト管理者)はUSER2
        project = root.create_project_folder('捨てるよプロジェクト🗑')
        project.save()
        project = project.reload()

        # プロジェクト管理者(USER2)がプロジェクトをほかす
        project.throw_away()

        # プロジェクトがゴミ箱に存在すること
        self.assertTrue(self.factory.data.trashed(project.uuid))

        # プロジェクト管理者(USER2)がプロジェクトを削除する
        project.delete()

        # プロジェクトは削除されていること
        self.assertFalse(self.factory.data.exists(project.uuid))

    def test_cannot_delete_project(self):
        """
        プロジェクト管理者以外はプロジェクトを削除できない
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()

        # ルートフォルダの下にプロジェクトを作成する
        # 作成者(=プロジェクト管理者)はUSER2
        project = root.create_project_folder('捨てるなプロジェクト🚯')
        project.save()
        project = project.reload()

        # プロジェクトメンバ以外のユーザ(USER3)が削除を試みる
        project = self.factory3.data.find_by_uuid(project.uuid)
        with self.assertRaises(NotAuthorizedException):
            project.throw_away()
        with self.assertRaises(NotAuthorizedException):
            project.delete()

        # USER3をプロジェクトの編集者メンバとして追加する
        project = self.factory2.data.find_by_id(project.id)
        user3_member = ProjectFolder.Member(self.USER3, ProjectFolder.WRITER_MEMBER_TYPE)
        project.join_member(user3_member)

        # 編集者メンバ(USER3)がプロジェクトの削除を試みる
        project = self.factory3.data.find_by_uuid(project.uuid)
        with self.assertRaises(NotAuthorizedException):
            project.throw_away()
        with self.assertRaises(NotAuthorizedException):
            project.delete()

        # プロジェクトは削除されていないこと
        self.assertTrue(self.factory.data.exists_by_id(project.id))

    def test_join_project(self):
        """
        プロジェクト管理者を交代する
        (元のプロジェクト管理者は削除する)
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('プロジェクト1')
        project.save()

        # メンバを設定する
        member1 = ProjectFolder.Member(self.USER2, ProjectFolder.OWNER_MEMBER_TYPE)
        member2 = ProjectFolder.Member(self.USER3, ProjectFolder.READER_MEMBER_TYPE)
        project.init_members([member1, member2])

        # メンバを取得する
        members = project.get_joined_members()

        # 期待する結果が返ることを確認する
        self.assertEqual(len(members), 2)
        self.assertEqual(members, [member1, member2])

        # プロジェクトは更新できない
        with self.assertRaises(NotAuthorizedException):
            project = project.reload()
            project.update_data('ぷろじぇくと1')

    def test_join_project2(self):
        """
        プロジェクト管理者を交代する
        (元のプロジェクト管理者は閲覧者にする)
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('プロジェクト2')
        project.save()

        # メンバを設定する
        member1 = ProjectFolder.Member(self.USER1, ProjectFolder.READER_MEMBER_TYPE)
        member2 = ProjectFolder.Member(self.USER3, ProjectFolder.OWNER_MEMBER_TYPE)
        project.init_members([member1, member2])

        # メンバを取得する
        members = project.get_joined_members()

        # 期待する結果が返ることを確認する
        self.assertEqual(len(members), 2)
        self.assertEqual(members, [member2, member1])

        # プロジェクトは更新できない
        with self.assertRaises(NotAuthorizedException):
            project = project.reload()
            project.update_data('ぷろじぇくと2')

    def test_join_project_without_owner(self):
        """
        プロジェクト管理者は必ず指定すること
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('プロジェクト3')
        project.save()

        # メンバを設定する
        member1 = ProjectFolder.Member(self.USER2, ProjectFolder.READER_MEMBER_TYPE)
        member2 = ProjectFolder.Member(self.USER3, ProjectFolder.WRITER_MEMBER_TYPE)
        with self.assertRaises(Exception):
            project.init_members([member1, member2])

        # プロジェクトは削除する
        project = project.reload()
        project.delete()

    def test_join_project_with_other_type(self):
        """
        プロジェクトに規定のユーザタイプ以外を指定できないこと
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('プロジェクト4')
        project.save()

        # メンバを設定する
        member1 = ProjectFolder.Member(self.USER2, ProjectFolder.READER_MEMBER_TYPE)
        member2 = ProjectFolder.Member(self.USER3, ProjectFolder.OTHER_MEMBER_TYPE)
        with self.assertRaises(Exception):
            project.init_members([member1, member2])

        # プロジェクトは削除する
        project = project.reload()
        project.delete()

    def test_join_project_without_member(self):
        """
        プロジェクトメンバは必ず指定すること
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('プロジェクト5')
        project.save()

        # メンバを設定する
        with self.assertRaises(Exception):
            project.init_members([])

        # プロジェクトは削除する
        project = project.reload()
        project.delete()

    # 
    # System Folders
    # 

    def test_root_folder_auths(self):
        """
        ルートフォルダの権限設定を検証する
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()

        # ルートフォルダの権限を取得する
        root_auths = self.factory.auth.find_all_by_datum_id(root.id)

        # システムロールを取得する
        everyone_role = self.factory.role.load_everyone_role()
        usr_admin_role = self.factory.role.load_usr_admin_role()

        # ルートフォルダには、everyoneにRWX権限が設定されること
        # システムフォルダには、usr_adminにO権限が設定されること
        # システムフォルダには、作成者の本人ロールの権限が設定されていないこと

        # 権限設定の数は正しいこと
        self.assertEqual(len(root_auths), 4)

        # everyone read
        role = self.factory.role.find_by_id(root_auths[0].role_id)
        self.assertEqual(role, everyone_role)
        self.assertEqual(root_auths[0].operation, 'read')
        self.assertEqual(root_auths[0].permission, True)

        # everyone write
        role = self.factory.role.find_by_id(root_auths[1].role_id)
        self.assertEqual(role, everyone_role)
        self.assertEqual(root_auths[1].operation, 'write')
        self.assertEqual(root_auths[1].permission, True)

        # everyone exec
        role = self.factory.role.find_by_id(root_auths[2].role_id)
        self.assertEqual(role, everyone_role)
        self.assertEqual(root_auths[2].operation, 'exec')
        self.assertEqual(root_auths[2].permission, True)

        # usr_admin own
        role = self.factory.role.find_by_id(root_auths[3].role_id)
        self.assertEqual(role, usr_admin_role)
        self.assertEqual(root_auths[3].operation, 'own')
        self.assertEqual(root_auths[3].permission, True)

    def test_cache_folder_auths(self):
        """
        キャッシュフォルダの権限設定を検証する
        """
        # キャッシュフォルダを取得する
        cache = self.factory.data.load_cache_folder()

        # キャッシュフォルダの権限を取得する
        cache_auths = self.factory.auth.find_all_by_datum_id(cache.id)

        # システムロールを取得する
        everyone_role = self.factory.role.load_everyone_role()
        usr_admin_role = self.factory.role.load_usr_admin_role()
        
        # キャッシュフォルダには、everyoneにRW権限が設定されること
        # システムフォルダには、usr_adminにO権限が設定されること
        # システムフォルダには、作成者の本人ロールの権限が設定されていないこと

        # 権限設定の数は正しいこと
        self.assertEqual(len(cache_auths), 3)

        # everyone read
        role = self.factory.role.find_by_id(cache_auths[0].role_id)
        self.assertEqual(role, everyone_role)
        self.assertEqual(cache_auths[0].operation, 'read')
        self.assertEqual(cache_auths[0].permission, True)

        # everyone write
        role = self.factory.role.find_by_id(cache_auths[1].role_id)
        self.assertEqual(role, everyone_role)
        self.assertEqual(cache_auths[1].operation, 'write')
        self.assertEqual(cache_auths[1].permission, True)

        # usr_admin own
        role = self.factory.role.find_by_id(cache_auths[2].role_id)
        self.assertEqual(role, usr_admin_role)
        self.assertEqual(cache_auths[2].operation, 'own')
        self.assertEqual(cache_auths[2].permission, True)

    def test_trash_folder_auths(self):
        """
        ゴミ箱フォルダの権限設定を検証する
        """
        # ゴミ箱フォルダを取得する
        trash = self.factory.data.load_trash_folder()

        # ゴミ箱フォルダの権限を取得する
        trash_auths = self.factory.auth.find_all_by_datum_id(trash.id)

        # システムロールを取得する
        everyone_role = self.factory.role.load_everyone_role()
        usr_admin_role = self.factory.role.load_usr_admin_role()
        
        # ゴミ箱フォルダには、everyoneにRW権限が設定されること
        # システムフォルダには、usr_adminにO権限が設定されること
        # システムフォルダには、作成者の本人ロールの権限が設定されていないこと

        # 権限設定の数は正しいこと
        self.assertEqual(len(trash_auths), 3)

        # everyone read
        role = self.factory.role.find_by_id(trash_auths[0].role_id)
        self.assertEqual(role, everyone_role)
        self.assertEqual(trash_auths[0].operation, 'read')
        self.assertEqual(trash_auths[0].permission, True)

        # everyone write
        role = self.factory.role.find_by_id(trash_auths[1].role_id)
        self.assertEqual(role, everyone_role)
        self.assertEqual(trash_auths[1].operation, 'write')
        self.assertEqual(trash_auths[1].permission, True)

        # usr_admin own
        role = self.factory.role.find_by_id(trash_auths[2].role_id)
        self.assertEqual(role, usr_admin_role)
        self.assertEqual(trash_auths[2].operation, 'own')
        self.assertEqual(trash_auths[2].permission, True)
