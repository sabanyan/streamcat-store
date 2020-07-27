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

        # 新規ユーザを削除する
        new_role.delete()
        # 削除後のユーザは取得できない
        with self.assertRaises(NoResultFound):
            self.factory.role.find_by_uuid(new_role.uuid)
    
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


    def test_no_authz(self):
        """
        権限レコードのないFrameは読み取れないことを検証する
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフレームを作成する
        import io
        f = io.BytesIO(b'')
        frame = root.create_frame('CSV', f)
        frame.save()

        # フレームの参照権限を全て削除する
        self.factory.auth.delete_all_by_datum_id(frame.id)

        # フローを再取得する
        frame = frame.reload()

        # フレームのreadableはNoneであること
        self.assertFalse(frame.readable)

        # フレームのpathは取得できないこと
        with self.assertRaises(NotAuthorizedException):
            frame.path


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
        frame = frame.reload()

        # フレームの参照権限を全て削除する
        self.factory.auth.delete_all_by_datum_id(frame.id)




        # 
        # 参照権限の削除後にframeオブジェクトのreadableをexpireした方がいい？
        #         
        persistent_obj = self.factory._session._session.identity_map.values()
        for obj in persistent_obj:
            if isinstance(obj, Datum):
                self.factory._session._session.expire(obj, ['readable'])



        # フレームのreadableはNoneであること
        self.assertIsNone(frame.readable)

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
        import io
        f = io.BytesIO(b'')
        frame = root.create_frame('CSV', f)
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
        # 参照権限の削除後にframeオブジェクトのreadableをexpireした方がいい？
        #         
        persistent_obj = self.factory._session._session.identity_map.values()
        for obj in persistent_obj:
            if isinstance(obj, Datum):
                self.factory._session._session.expire(obj, ['readable'])


        # フローのreadableはNoneであること
        self.assertIsNone(flow.readable)

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

        # フォルダの参照権限を全て削除する
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

        # フローのreadableはFalseであること
        self.assertFalse(flow.readable)

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
        import io
        f = io.BytesIO(b'')
        frame = root.create_frame('CSV2', f)
        frame.save()

        # フレームの参照権限を全て削除する
        self.factory.auth.delete_all_by_datum_id(frame.id)

        # フローを再取得する
        frame = frame.reload()

        # フレームのreadableはNoneであること
        self.assertFalse(frame.readable)

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
        import io
        f = io.BytesIO(b'')
        frame = root.create_frame('CSV2', f)
        frame.save()
        # ルートフォルダの下にフローを作成する
        flow = root.create_simple_flow(root, 'フロー', frame)
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
            flow.flow_data.nodes

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
        everyone_role.init_authz(to_folder.id, True, False)
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
        # (フローCの更新エラーになる)
        with self.assertRaises(NotAuthorizedException):
            flow.move(to_folder.uuid)

        # フローが移動していないこと
        self.assertEqual(flow.parent_id, from_folder.id)


    def test_folder_in_writeless_folder(self):
        """
        更新権限のないFolderの直下のFolder内にあるFlowは更新できること
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

        # フローは更新できること
        flow.update_data('myFlow0', {})

        # フォルダ2にフローを新規追加できること
        flow2 = folder2.create_flow('myFlow1', {})
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

