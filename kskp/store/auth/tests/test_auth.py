import io
import copy
import unittest
import pprint
from sqlalchemy.orm.exc import NoResultFound
from kskp.core import Datum
from kskp.store import ProjectFolder, FlowData, OptimisticLockException, EditLockedException, CommandException
from kskp.store.auth import Auth, Role, InvalidPassword, NotAuthorizedException, NoRoleOwnerException
from ...tests.test_case_base import TestCaseBase

class AuthTest(TestCaseBase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    # フローJSON
    # mnewnumber -> d(cache=on) -> mcut -> d1(out=on)
    flow_json = {
        "label": "flow", 
        "nodes": [
        {
            "id": "d", 
            "type": "frame", 
            "uuid": None, 
            "label": "d", 
            "makeCache": True, 
            "dataSource": "csv", 
            "cacheCreatedAt": None
        }, 
        {
            "id": "c", 
            "args": {
            "I": "1", 
            "S": "1", 
            "a": "a", 
            "l": "10"
            }, 
            "dsts": {
            "o": "d"
            },
            "srcs": {}, 
            "type": "command", 
            "label": "c", 
            "commandId": "mnewnumber", 
            "srcsOrder": []
        }, 
        {
            "id": "d1", 
            "type": "frame", 
            "uuid": None, 
            "label": "d1", 
            "makeCache": False, 
            "dataSource": "csv", 
            "cacheCreatedAt": None
        }, 
        {
            "id": "c1", 
            "args": {
            "f": "*"
            }, 
            "dsts": {
            "o": "d1"
            }, 
            "srcs": {
            "i": "d"
            }, 
            "type": "command", 
            "label": "c1", 
            "commandId": "mcut", 
            "srcsOrder": [
            "i"
            ]
        }
        ], 
        "ports": [
        [], 
        [
            {
            "type": "frame", 
            "label": "d1", 
            "nodeId": "d1"
            }
        ]
        ], 
        "params": [], 
        "creator": "ユーザー管理者", 
        "createdAt": "2020-10-04 17:45:16", 
        "projectId": None, 
        "description": ""
    }

    # d(in=on) -> column_unique_name -> d1(out=on)
    flow2_json = {
        "label": "flow2", 
        "nodes": [
        {
            "id": "d", 
            "type": "frame", 
            "value": [["顧客", "数量", "金額"],
                      ["A", 1, 10],
                      ["A", 2, 20],
                      ["B", 1, 30],
                      ["B", 3, 40],
                      ["B", 1, 50]],
            "label": "testData",
            "makeCache": False, 
            "dataSource": "csv", 
            "cacheCreatedAt": None
        }, 
        {
            "id": "d1", 
            "type": "frame", 
            "uuid": None, 
            "label": "d1", 
            "makeCache": False, 
            "dataSource": "csv", 
            "cacheCreatedAt": None
        }, 
        {
            "id": "c1", 
            "args": {
                "d": "^^"
            }, 
            "dsts": {
                "o": "d1"
            }, 
            "srcs": {
                "i": "d"
            }, 
            "type": "command", 
            "label": "c1", 
            "commandId": "column_unique_name", 
            "srcsOrder": [
                "i"
            ]
        }
        ], 
        "ports": [
        [
            {
                "type": "frame", 
                "label": "testData", 
                "nodeId": "d"
            }
        ], 
        [
            {
                "type": "frame", 
                "label": "d1", 
                "nodeId": "d1"
            }
        ]
        ], 
        "params": [], 
        "creator": "ユーザ管理者", 
        "createdAt": "2020-11-19 11:31:10", 
        "projectId": None, 
        "description": ""
    }

    # d(in=on) -> sub_flow -> d1(out=on)
    flow3_json = {
        "label": "flow3",
        "nodes": [
            {
                "id": "d",
                "type": "frame",
                "uuid": None,
                "label": "0byte",
                "makeCache": False,
                "dataSource": "csv",
                "cacheCreatedAt": None
            },
            {
                "id": "d1",
                "type": "frame",
                "uuid": None,
                "label": "d1",
                "makeCache": False,
                "dataSource": "csv",
                "cacheCreatedAt": None
            },
            {
                "id": "f1",
                "args": {},
                "dsts": {
                    "d1": "d1"
                },
                "srcs": {
                    "d": "d"
                },
                "type": "flow",
                "uuid": None,
                "label": "f1",
                "srcsOrder": [
                    "d"
                ]
            }
        ],
        "ports": [
            [],
            [
                {
                    "type": "frame",
                    "label": "d1",
                    "nodeId": "d1"
                }
            ]
        ],
        "params": [],
        "creator": "ユーザー管理者",
        "createdAt": "2020-11-20 09:20:50",
        "projectId": None,
        "description": ""
    }

    def get_flow3_json(self, subflow_uuid):
        """
        サブフローのUUIDを設定して、Flow3のJsonを取得する
        """
        flow3_json =  copy.deepcopy(self.flow3_json)

        # サブフローを指定されたUUIDに設定する
        for node in flow3_json['nodes']:
            if node.get('id') == 'f1':
                node['uuid'] = subflow_uuid
                break

        return flow3_json

    def get_frame_from_lasts(lasts):
        """
        lastsから出力結果Frameを1つ返す
        """
        from kskp.store import Activity
        activities = [ datum for point_id, datum in lasts.items() if isinstance(datum, Activity)]
        # Engineの実行により例外が発生した場合は送出する
        activities[0].raise_one()
        return activities[0].lasts[0][1]

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
        flow = root.create_flow('Flow!', FlowData())
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

    def test_failure_after_update_data(self):
        """
        原因不明
          save() -> update() -> find_by_id()/find_by_uuid()の順に実行すると
          find_by_id()/find_by_uuid()で参照権限Noneのためエラーになる

        AuthzSession.update()においてSession.exipre()を実行しても
        _permissions(=None)はExpireされないので、find_by_id()を実行時に
        Sessionにある_permissionsの値を参照している?
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()

        # 
        # フレームを新規作成する
        # 
        frame = root.create_frame('Frame!!!', io.BytesIO(b''))

        # フレームの参照と更新権限は付与されていること
        # (フレームなので実行権限はない)
        self.assertTrue(frame.readable)
        self.assertTrue(frame.writable)
        self.assertFalse(frame.executable)

        # フレームを保存する
        frame.save()

        # 保存後は全ての権限はNoneに設定される
        self.assertIsNone(frame.readable)
        self.assertIsNone(frame.writable)
        self.assertIsNone(frame.executable)

        # ここでSELECTを発行すると、下のfind_by_id()は成功する
        # self.factory.data.find_by_id(frame.id)

        # フレームを更新する
        # (SELECTを発行しない単純なUPDATE)
        frame.update_label_only('frame!!!')

        self.assertIsNone(frame.readable)
        self.assertIsNone(frame.writable)
        self.assertIsNone(frame.executable)

        # フォルダを再読み込みする
        # 参照権限がNoneのため、NotAuthorizedExceptionが送出される
        with self.assertRaises(NotAuthorizedException):
            self.factory.data.find_by_id(frame.id)

        # 
        # プロジェクトを新規作成する
        # 
        project = root.create_project_folder('Project!!!')

        # プロジェクトを保存する
        project.save()

        # プロジェクトの更新者IDと最終更新時刻を更新する
        project._update_timestamp()

        # プロジェクトを再読み込みする
        with self.assertRaises(NotAuthorizedException):
            self.factory.data.find_by_uuid(project.uuid)

    def test_success_after_update_data1(self):
        """
        原因不明
          save() -> find_by_id() -> update() -> find_by_id()の順に実行すると
          2回目のfind_by_id()で参照権限のエラーは送出されない
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()

        # 
        # フレームを新規作成する
        # 
        frame = root.create_frame('Frame!!!', io.BytesIO(b''))

        # フレームの参照と更新権限は付与されていること
        # (フレームなので実行権限はない)
        self.assertTrue(frame.readable)
        self.assertTrue(frame.writable)
        self.assertFalse(frame.executable)

        # フレームを保存する
        frame.save()

        # 保存後は全ての権限はNoneに設定される
        self.assertIsNone(frame.readable)
        self.assertIsNone(frame.writable)
        self.assertIsNone(frame.executable)

        # ここでSELECTを発行すると、下のreload()は成功する
        self.factory.data.find_by_id(frame.id)

        # フレームを更新する
        # (SELECTを発行しない単純なUPDATE)
        frame.update_label_only('frame!!!')

        self.assertTrue(frame.readable)
        self.assertTrue(frame.writable)
        self.assertFalse(frame.executable)

        # フォルダを再読み込みする
        self.factory.data.find_by_id(frame.id)

        # 
        # プロジェクトを新規作成する
        # 
        project = root.create_project_folder('Project!!!')

        # プロジェクトを保存する
        project.save()

        # ここでSELECTを発行すると、下のreload()は成功する
        self.factory.data.find_by_uuid(project.uuid)

        # プロジェクトの更新者IDと最終更新時刻を更新する
        project._update_timestamp()

        # プロジェクトを再読み込みする
        self.factory.data.find_by_uuid(project.uuid)

    def test_success_after_update_data2(self):
        """
        save() -> update() -> reload()の順に実行すると
        reload()で参照権限のエラーは送出されないこと
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()

        # 
        # フレームを新規作成する
        # 
        frame = root.create_frame('Frame!!!!', io.BytesIO(b''))

        # フレームの参照と更新権限は付与されていること
        # (フレームなので実行権限はない)
        self.assertTrue(frame.readable)
        self.assertTrue(frame.writable)
        self.assertFalse(frame.executable)

        # フレームを保存する
        frame.save()

        # 保存後は全ての権限はNoneに設定される
        self.assertIsNone(frame.readable)
        self.assertIsNone(frame.writable)
        self.assertIsNone(frame.executable)

        # フレームを更新する
        # (SELECTを発行しない単純なUPDATE)
        frame.update_label_only('frame!!!!')

        self.assertIsNone(frame.readable)
        self.assertIsNone(frame.writable)
        self.assertIsNone(frame.executable)

        # フォルダを再読み込みする
        #  reload()にて_permissionsをExpireしてからfind_by_id()を呼んでいるので、
        #  NotAuthorizedExceptionは送出されない
        frame.reload()

        # 
        # プロジェクトを新規作成する
        # 
        project = root.create_project_folder('Project!!!')

        # プロジェクトを保存する
        project.save()

        # プロジェクトの更新者IDと最終更新時刻を更新する
        project._update_timestamp()

        # プロジェクトを再読み込みする
        project.reload()

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

        # find_all()で全てのDatumを取得する
        data = self.factory.data.find_all()

        # Sessionクラスで_sessionプロパティが設定されること
        for datum in data:
            self.assertIs(datum._session, self.factory._session)

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
        # print('>> ', role.get_joined_users())
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
        new_user = self.factory.user.create('test-man@kskp.io', 'I AM TEST', '123abc(*)A')
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
        with self.assertRaises(Exception):
            self.factory.user.find_by_email('test-man@kskp.io')

    def test_create_user_by_user(self):
        """
        一般ユーザは、ユーザの作成ができないこと
        """
        # 新規ユーザを追加する
        new_user = self.factory2.user.create('test-man2@kskp.io', 'I AM TEST', '123abc(*)A')
        with self.assertRaises(NotAuthorizedException):
            new_user.save()

    def test_update_user_by_user(self):
        """
        一般ユーザは、他ユーザの変更ができないこと
        """
        # 新規ユーザを追加する
        new_user = self.factory.user.create('test-man3@kskp.io', 'I AM TEST', '123abc(*)C')
        new_user.save()

        # 他ユーザで再取得する
        new_user = self.factory2.user.find_by_uuid(new_user.uuid)
        new_user_password = new_user.password

        # E-Mailを変更する
        with self.assertRaises(NotAuthorizedException):
            new_user.update_email('abc@abc.com')

        # パスワードを変更する
        with self.assertRaises(NotAuthorizedException):
            new_user.update_password('abc!@#$%^&*()_+')

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
        new_user = self.factory.user.create('test-man4@kskp.io', 'I AM TEST', '123abc(*)D')
        new_user.save()

        # 他ユーザで再取得する
        new_user = self.factory2.user.find_by_uuid(new_user.uuid)

        # 新規ユーザを削除する
        with self.assertRaises(NotAuthorizedException):
            new_user.delete()

        # 削除後のユーザは取得できる
        new_user = self.factory.user.find_by_email('test-man4@kskp.io')
        self.assertIsNotNone(new_user)

    def test_cannot_set_same_email(self):
        """
        既に登録済みのemailと同じemailのユーザは作成できないこと
        既に登録済みのemailと同じemailに変更できないこと
        """
        # 新規ユーザを追加する
        new_user1 = self.factory.user.create('wow@kskp.io', 'I AM TEST', '123abc(*)C')
        new_user1.save()

        # 他のユーザと同じメールアドレスでユーザを作成できないこと
        with self.assertRaises(Exception):
            new_user2 = self.factory.user.create('wow@kskp.io', 'I AM TEST 2', None)
            new_user2.save()

        # 他のユーザと同じメールアドレスに変更できないこと
        with self.assertRaises(Exception):
            new_user2.update_email('wow@kskp.io')

        # ユーザを削除する
        new_user1.delete()

    def test_validate_email(self):
        """
        E-Mailの妥当性が検証されること
        """
        pass

    def test_validate_password(self):
        """
        パスワードの妥当性が検証されること
        """
        # 新規ユーザを追加する
        new_user = self.factory.user.create('suerp-mario@nintendo.com', 'ホッホ〜！', None)
        new_user.save()

        # ユーザを登録状態にする
        new_user.update_password('PassWord123@')        

        # パスワードはNoneにできないこと
        with self.assertRaises(InvalidPassword):
            new_user.update_password(None)

        # パスワードは空にできないこと
        with self.assertRaises(InvalidPassword):
            new_user.update_password('')

        # パスワードは10文字以上であること
        with self.assertRaises(InvalidPassword):
            new_user.update_password('123456789')

        # パスワードは64文字以下であること
        with self.assertRaises(InvalidPassword):
            new_user.update_password('12345678901234567890123456789012345678901234567890123456789012345')

        # パスワードに空白文字は使用できないこと
        with self.assertRaises(InvalidPassword):
            new_user.update_password('12345 67890')

        # パスワードに使用できる文字は半角英数と記号のみである
        with self.assertRaises(InvalidPassword):
            new_user.update_password('1234567890あう')
        with self.assertRaises(InvalidPassword):
            new_user.update_password('1234567890ＡＢＣ')
        with self.assertRaises(InvalidPassword):
            new_user.update_password('12345漢字67890')
        with self.assertRaises(InvalidPassword):
            new_user.update_password('12345🧨67890')
        with self.assertRaises(InvalidPassword):
            new_user.update_password('1234567890')

        # ユーザを削除する
        new_user.delete()

    def test_cannot_set_same_password(self):
        """
        変更前と同じパスワードに変更できないこと
        """
        # 新規ユーザを追加する
        new_user = self.factory.user.create('hato@love-and-peace.com', '鳩山 由紀夫', 'hatopoppo?_%')
        new_user.save()

        # 変更前と同じパスワードに変更できないこと(初期状態)
        with self.assertRaises(InvalidPassword):
            new_user.update_password('hatopoppo?_%')

        # ユーザを登録状態にする
        new_user.update_password('poppoppo?_%')

        # 変更前と同じパスワードに変更できないこと(登録状態)
        with self.assertRaises(InvalidPassword):
            new_user.update_password('poppoppo?_%')

        # ユーザを仮登録状態にする
        new_user.reset_password()

        # 変更前と同じパスワードに変更できないこと(仮登録状態)
        tmp_pass = new_user._get_decrypt_password(new_user.password)
        with self.assertRaises(InvalidPassword):
            new_user.update_password(tmp_pass)

        # ユーザを登録状態にする
        new_user.update_password('mamegahosiika?_%')

        # ユーザを削除する
        new_user.delete()

    def test_system_user_id(self):
        """
        システム管理者とユーザ管理者に付番されるIDを検証する
        (保守性向上のためシステムが用意するユーザのIDは固定したい)
        """
        sys_user = self.factory.user.find_by_email('Admin@kskp.io')
        usr_user = self.factory.user.find_by_email('admin@kskp.io')

        # システム管理者のIDは1、ユーザ管理者のIDは2
        self.assertEqual(sys_user.id, 1)
        self.assertEqual(usr_user.id, 2)

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
        new_role.join_member(Role.Member(self.USER2))

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
        new_role.leave_member(self.USER2)

    def test_join_role_on_no_auth(self):
        """
        Roleにユーザを追加できるのはユーザ管理者かRoleの所有者のみである
        """
        # ロールを作成する
        new_role = self.factory.role.create('ロール')
        new_role.save()

        # 管理者でもRoleの所有者でもないユーザは、
        # ユーザの追加操作はできない
        new_role = self.factory2.role.find_by_uuid(new_role.uuid)
        with self.assertRaises(NotAuthorizedException):
            new_role.join_member(Role.Member(self.USER2))

    def test_leave_role_on_no_auth(self):
        """
        Roleからユーザを削除できるのはユーザ管理者かRoleの所有者のみである
        """
        # ロールを作成する
        new_role = self.factory.role.create('ロール')
        new_role.save()

        # ロールにユーザを追加する
        new_role.join_member(Role.Member(self.USER2))

        # 管理者でもRoleの所有者でもないユーザは、
        # ユーザの削除操作はできない
        new_role = self.factory2.role.find_by_uuid(new_role.uuid)
        with self.assertRaises(NotAuthorizedException):
            new_role.leave_member(self.USER2)

    def test_cannot_delete_system_role(self):
        """
        システムロールは削除できないこと
        """
        # システムロールを取得する
        sys_admin_role = self.factory.role.load_sys_admin_role()
        usr_admin_role = self.factory.role.load_usr_admin_role()
        everyone_role = self.factory.role.load_everyone_role()
        edit_lock_role = self.factory.role.load_edit_lock_role()

        # システムロールは削除できないこと
        with self.assertRaises(Exception):
            sys_admin_role.delete()
        with self.assertRaises(Exception):
            usr_admin_role.delete()
        with self.assertRaises(Exception):
            everyone_role.delete()
        with self.assertRaises(Exception):
            edit_lock_role.delete()

    def test_join_usr_admin_role_without_owner(self):
        """
        ユーザ管理者ロールの所有者は必ず指定すること
        """
        # ユーザ管理者ロールを取得する
        usr_admin_role = self.factory.role.load_usr_admin_role()

        # メンバを設定する
        member1 = Role.Member(self.USER2)
        member2 = Role.Member(self.USER3, owner=False)
        with self.assertRaises(NoRoleOwnerException):
            usr_admin_role.init_members([member1, member2])

    def test_update_usr_admin_role_owner_to_false(self):
        """
        ユーザ管理者ロールの所属処理によってロール所有者が不在にならないこと
        """
        # ユーザ管理者ロールを取得する
        usr_admin_role = self.factory.role.load_usr_admin_role()

        # 所有権が不在になるようなメンバの更新はできないこと
        member1 = Role.Member(self.USER1, owner=False)
        with self.assertRaises(NoRoleOwnerException):
            usr_admin_role.join_member(member1)

    def test_cannot_delete_usr_admin_role_owner(self):
        """
        ユーザがユーザ管理者ロールの唯一の所有者の場合、そのユーザを削除できないこと
        """
        # ユーザ管理者ロールの所有者を削除できないこと
        with self.assertRaises(NoRoleOwnerException):
            self.USER1.throw_away()
        with self.assertRaises(NoRoleOwnerException):
            self.USER1.delete()

    def test_join_sys_admin_role_without_owner(self):
        """
        システム管理者ロールの所有者は指定する必要はない
        """
        # システム管理者ロールを取得する
        sys_admin_role = self.factory.role.load_sys_admin_role()

        # メンバを設定する
        member1 = Role.Member(self.USER2)
        member2 = Role.Member(self.USER3, owner=False)
        sys_admin_role.init_members([member1, member2])

        # メンバ設定を戻す
        sys_admin_role.init_members([Role.Member(self.USER0, owner=True)])

    def test_update_sys_admin_role_owner_to_false(self):
        """
        システム管理者ロールの所属処理によってロール所有者が不在でも良い
        """
        # システム管理者ロールを取得する
        sys_admin_role = self.factory.role.load_sys_admin_role()

        # 所有権が不在になるようなメンバの更新もできること
        member1 = Role.Member(self.USER0, owner=False)
        sys_admin_role.join_member(member1)

    def test_system_role_id(self):
        """
        everyoneと管理者ロールに付番されるIDを検証する
        (保守性向上のためシステムが用意するロールのIDは固定したい)
        """
        everyone_role = self.factory.role.load_everyone_role()
        edit_lock_role = self.factory.role.load_edit_lock_role()
        sys_admin_role = self.factory.role.load_sys_admin_role()
        usr_admin_role = self.factory.role.load_usr_admin_role()

        # TODO: 本当は以下のようにIDを採番したい
        # everyone  : 1
        # sys_admin : 2
        # usr_admin : 3
        # edit_lock : 4
        self.assertEqual(everyone_role.id, 1)
        self.assertEqual(edit_lock_role.id, 2)
        self.assertEqual(sys_admin_role.id, 3)
        self.assertEqual(usr_admin_role.id, 4)

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

        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('プロジェクト！！')
        project.save()

        # プロジェクトの下にフォルダを作成する
        folder = project.create_folder('フォルダS')
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

        # プロジェクトを削除する
        project.delete()

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
        folder = self.factory.data.find_by_id(folder.id)

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

        # フローは再取得できないこと
        with self.assertRaises(NotAuthorizedException):
            frame.reload()

        # 再取得が失敗してもpermissionsの値は更新される
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
        flow = folder.create_flow('フロー', FlowData())
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
        flow = folder.create_flow('フロー', FlowData())
        flow.save()
        flow = flow.reload()

        # フォルダの更新権限を全て削除する
        self.factory.auth.delete_all_by_datum_id(folder.id)

        # フローは更新不可
        with self.assertRaises(NotAuthorizedException):
            flow.update_data('WOW', FlowData())

        # フローは削除不可
        with self.assertRaises(NotAuthorizedException):
            flow.delete()

    def test_resolve_roles(self):
        """
        複数のロールで異なる権限判定の場合
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('プロジェクト💣')
        project.save()
        # everyoneにプロジェクトの参照・更新・実行権限を付与する
        everyone_role = self.factory2.role.load_everyone_role()
        everyone_role.init_authz(project.id, True, True, exec=True)

        # プロジェクトの下にフローを作成する
        flow = project.create_flow('フロー', FlowData())
        flow.save()

        # フローの参照権限を全て削除する
        self.factory.auth.delete_all_by_datum_id(flow.id)

        # ロールAを作成する
        roleA = self.factory.role.create('roleA')
        roleA.save()
        # ロールBを作成する
        roleB = self.factory.role.create('roleB')
        roleB.save()

        # ロールAにフローの更新・実行許可を付与する
        roleA.init_authz(flow.id, True, True, exec=True)
        # ロールBにフローの更新・実行不可を付与する
        roleB.init_authz(flow.id, True, False, exec=False)

        # TESTユーザをロールAとロールBに参加させる
        roleA.join_member(Role.Member(self.USER2))
        roleB.join_member(Role.Member(self.USER2))

        # フローを再取得する
        flow = flow.reload()

        # フローのwritable,executableはFalseであること
        self.assertTrue(flow.readable)
        self.assertFalse(flow.writable)
        self.assertFalse(flow.executable)

        # フローのnodesは取得できないこと
        with self.assertRaises(NotAuthorizedException):
            flow.flow_data.get_nodes(use_exec_auth=True)

        # フローは更新不可
        with self.assertRaises(NotAuthorizedException):
            flow.update_data('WOW!', FlowData())

        # フローは削除不可
        with self.assertRaises(NotAuthorizedException):
            flow.delete()

        # ロールBを削除する
        roleB.delete()

        # フローを削除する
        flow.delete()
        
        # プロジェクトを削除する
        project = project.reload()
        project.delete()

    @unittest.skip('参照権限のないDatumは取得できない仕様に変更されたため')
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

    @unittest.skip('参照権限のないDatumは取得できない仕様に変更されたため')
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
        flow = root.create_flow('所有者のみ参照できるフロー', FlowData())
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
        flow = root.create_flow('所有者のみ参照できるフロー', FlowData())
        flow.save()

        # フローの参照権限を全て削除する
        self.factory.auth.delete_all_by_datum_id(flow.id)

        # USER1の本人グループに参照権限を付与する
        self.USER1.load_self_role().init_authz(flow.id, True, False)

        # 他ユーザはフローを取得できないこと
        with self.assertRaises(NotAuthorizedException):
            self.factory2.data.find_by_id(flow.id)

    def test_write_flow_by_self_role(self):
        """
        本人グループにのみ更新可能なFlowを更新できること
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフローを作成する
        flow = root.create_flow('所有者のみ更新できるフロー', FlowData())
        flow.save()
        
        # フローの権限を全て削除する
        self.factory.auth.delete_all_by_datum_id(flow.id)

        # USER1の本人グループに更新権限を付与する
        self.USER1.load_self_role().init_authz(flow.id, False, True)

        # フローは更新可能
        flow.update_data('変更したフロー名', FlowData())

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
        flow = folder.create_flow('フロー', FlowData())
        flow.save()

        # フォルダとフローの権限を全て削除する
        self.factory.auth.delete_all_by_datum_id(folder.id)
        self.factory.auth.delete_all_by_datum_id(flow.id)

        # USER1の本人グループに更新権限を付与する
        self.USER1.load_self_role().init_authz(folder.id, False, True)
        self.USER1.load_self_role().init_authz(flow.id, False, True)

        # フローは更新可能
        flow.update_data('変更したフロー名2', FlowData())

        # フローは更新されていること
        self.assertEqual(flow.label, '変更したフロー名2')        

    def test_write_flow_by_other_role(self):
        """
        本人グループにのみ更新可能なFlowを他ユーザは更新できないこと
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフローを作成する
        flow = root.create_flow('所有者のみ更新できるフロー2', FlowData())
        flow.save()
        
        # フローの権限を全て削除する
        self.factory.auth.delete_all_by_datum_id(flow.id)

        # USER1の本人グループに更新権限を付与する
        self.USER1.load_self_role().init_authz(flow.id, None, True)

        # USER2の本人グループに参照権限を付与する
        user2_auth = self.factory.auth.create(self.USER2.load_self_role().id, flow.id, Auth.READ_OP, True)
        user2_auth.save()

        # USER2によりフローを取得する
        flow = self.factory2.data.find_by_id(flow.id)

        # フローは更新不可能
        with self.assertRaises(NotAuthorizedException):
            flow.update_data('変更したフロー名2', FlowData())

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
        flow = from_folder.create_flow('フローA', FlowData())
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
        flow = from_folder.create_flow('フローB', FlowData())
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
        flow = from_folder.create_flow('フローC', FlowData())
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
        flow = folder2.create_flow('myFlow', FlowData())
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
            flow.update_data('myFlow0', FlowData())

        # フォルダ2にフローを新規追加できないこと
        flow2 = folder2.create_flow('myFlow1', FlowData())
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
        flow1 = folder.create_flow('更新できないフロー', FlowData())
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
        flow = folder.create_flow('実行できないフロー', FlowData())
        flow.save()

        # フローを実行不可にする
        everyone_role = self.factory.role.load_everyone_role()
        everyone_role.init_authz(flow.id, True, True, exec=False)

        # フローJSONのnodesを取得できないこと
        with self.assertRaises(NotAuthorizedException):
            flow.flow_data.get_nodes(use_exec_auth=True)

        # フローを実行可にする
        everyone_role.init_authz(folder.id, True, False, exec=True)
        everyone_role.init_authz(flow.id, True, False, exec=True)

        # フローを再取得するまでは実行不可のママである
        with self.assertRaises(NotAuthorizedException):
            flow.flow_data.get_nodes(use_exec_auth=True)

        # フローを再取得する
        flow = flow.reload()

        # フローJSONのnodesを取得できること
        flow.flow_data.get_nodes(use_exec_auth=True)

    def test_own_frame_in_no_own_folder(self):
        """
        フレームの所有権は親フォルダの所有権に影響しないこと
        (フォルダの所有権はオーバーライドしない)
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()

        # ルートフォルダの下にフォルダを作成する (所有者はユーザ管理者)
        folder_a = root.create_folder('所有権の無いフォルダA')
        folder_a.save()

        # USER2にフォルダAの所有権を付与する
        user2 = self.factory.user.find_by_uuid(self.USER2.uuid)
        user2.load_self_role().init_authz(folder_a.id, read=True, write=True, exec=True, own=True)
        self.USER1.load_self_role().clear_authz(folder_a.id)

        # USER3にフォルダAの更新権限を付与する
        user3 = self.factory2.user.find_by_uuid(self.USER3.uuid)
        user3.load_self_role().init_authz(folder_a.id, read=True, write=True)

        # フォルダAの下にフレームAを作成する (所有者はUSER3)
        folder_a = self.factory3.data.find_by_uuid(folder_a.uuid)
        frame_a = folder_a.create_frame('My Frame A', io.BytesIO(b''))
        frame_a.save()

        # ルートフォルダの下にプロジェクトBを作成する (所有者はUSER3)
        root = self.factory3.data.load_root()
        project_b = root.create_project_folder('所有権の有るプロジェクトB')
        project_b.save()

        # プロジェクトBの下にフレームBを作成する (所有者はUSER3)
        frame_b = project_b.create_frame('My Frame B', io.BytesIO(b''))
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

        # フレームA,Bを削除する
        frame_a.delete()
        frame_b.delete()

        # NotAuthorizedExceptionの送出後のSession.rollback()により、
        # Expireが発生し、readable=Noneとなるため再読み込みする
        folder_a = self.factory2.data.find_by_id(folder_a.id)
        project_b = self.factory3.data.find_by_id(project_b.id)

        # フォルダA,Bを削除する
        folder_a.delete()
        project_b.delete()

    def test_override_all_permissions(self):
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
        # フレームは取得できないこと
        # 
        with self.assertRaises(NotAuthorizedException):
            frame.reload()

        # フレームのreadable,writable,executableは再取得により更新される
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
        # フローは取得できないこと
        # 
        with self.assertRaises(NotAuthorizedException):
            flow.reload()

        # フローのreadable,writable,executableは再取得により更新される
        self.assertFalse(flow.readable)
        self.assertFalse(flow.writable)
        self.assertFalse(flow.executable)

        # フローJSONのうちnodesキーは取得できないこと
        with self.assertRaises(NotAuthorizedException):
            flow.flow_data.get_nodes()

        # フローの更新はできないこと
        with self.assertRaises(NotAuthorizedException):
            flow.update_data('flame_file', FlowData())

        # フローは削除できないこと
        with self.assertRaises(NotAuthorizedException):
            flow.delete()

    def test_override_read_write_permissions(self):
        """
        更新・実行の権限がフォルダ階層においてオーバライドされること
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

        # フォルダ1の権限を全て削除する
        self.factory.auth.delete_all_by_datum_id(folder1.id)

        # フォルダ1に参照権限のみを付与する
        user1_role = self.USER1.load_self_role()
        user1_role.init_authz(folder1.id, True, None)

        # 
        # フレームを再取得する
        # 
        frame = frame.reload()

        # フレームのreadable,writable,executableを検証する
        self.assertTrue(frame.readable)
        self.assertFalse(frame.writable)
        self.assertFalse(frame.executable)

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

        # フローのreadable,writable,executableを検証する
        self.assertTrue(flow.readable)
        self.assertFalse(flow.writable)
        self.assertFalse(flow.executable)

        # フローJSONは取得できること
        self.assertEqual(flow.flow_data.label, 'フロー')
        self.assertEqual(flow.flow_data.description, '')
        self.assertEqual(flow.flow_data.ports, [[],[]])
        self.assertTrue(flow.flow_data.has_nodes)
        self.assertGreater(len(flow.flow_data.get_nodes()), 0)

        # フローの更新はできないこと
        with self.assertRaises(NotAuthorizedException):
            flow.update_data('flame_file', FlowData())

        # フローは削除できないこと
        with self.assertRaises(NotAuthorizedException):
            flow.delete()

    def test_count_readless_datum(self):
        """
        参照権限のないDatumでもcount()できること
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフォルダ1を作成する
        folder1 = root.create_folder('フォルダ1')
        folder1.save()
        # フォルダ1の下にフローを作成する
        flow = folder1.create_flow('myFlow', FlowData())
        flow.save()

        # フローを参照不可にする
        everyone_role = self.factory.role.load_everyone_role()
        everyone_role.init_authz(flow.id, False, True)

        # フローは参照不可なので取得できない
        self.assertEqual(len(folder1.find_children()), 0)

        # ただし、参照不可であってもcount()によって件数の取得は可能としている
        result = self.factory._session.query(Datum).filter(Datum.parent_id==folder1.id).count()
        self.assertEqual(result, 1)

        # フローとフォルダ1を削除する
        flow.delete()
        folder1.delete()

    def test_exists_readless_datum(self):
        """
        参照権限のないDatumでもexists()=Trueであること
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフォルダ1を作成する
        folder1 = root.create_folder('フォルダ1')
        folder1.save()
        # フォルダ1の下にフレームを作成する
        frame = folder1.create_frame('フレーム！', io.BytesIO(b'frame0frame0'))
        frame.save()

        # フローを参照不可にする
        everyone_role = self.factory.role.load_everyone_role()
        everyone_role.init_authz(frame.id, False, True)

        # フローは参照不可なので取得できない
        self.assertEqual(len(folder1.find_children()), 0)

        # ただし、参照不可であってもexists()によってその存在の判定は可能としている
        self.assertTrue(self.factory.data.exists(frame.uuid))
        self.assertTrue(self.factory.data.exists_by_id(frame.id))

        # フレームとフォルダ1を削除する
        frame.delete()
        folder1.delete()

    # 
    # Projects
    # 
    def test_create_get_delete_project(self):
        """
        Projectの作成・取得・削除を検証する
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()

        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('京阪乗る人おけいはん')
        project.save()
        project = project.reload()

        # 3つのプロジェクトロールが作成されていること
        readers_role = project._find_readers_role()
        writers_role = project._find_writers_role()
        owners_role = project._find_owners_role()
        self.assertIsInstance(readers_role.id, int)
        self.assertTrue(readers_role.delete_on_isolated)
        self.assertEqual(readers_role.name, '京阪乗る人おけい_readers')
        self.assertIsInstance(writers_role.id, int)
        self.assertTrue(writers_role.delete_on_isolated)
        self.assertEqual(writers_role.name, '京阪乗る人おけい_writers')
        self.assertTrue(owners_role.delete_on_isolated)
        self.assertIsInstance(owners_role.id, int)
        self.assertEqual(owners_role.name, '京阪乗る人おけい_owners')

        # users_rolesテーブルを検証する
        everyone_role = self.factory2.role.load_everyone_role()
        usr_admin_role = self.factory2.role.load_usr_admin_role()
        self_role = self.factory2.role.find_by_id(self.USER1.self_role_id)

        # ユーザ管理者に関係するusers_rolesテーブルのレコードを検証する
        user_roles = self.factory2.user_role.find_all_by_user_id(self.USER1.id)
        self.assertGreaterEqual(len(user_roles), 2)
        # everyoneロール
        user_role = self.factory2.user_role.find_by_id(self.USER1.id, everyone_role.id)
        self.assertTrue(user_role.owner)
        # ユーザ管理者ロール
        user_role = self.factory2.user_role.find_by_id(self.USER1.id, usr_admin_role.id)
        self.assertTrue(user_role.owner)
        # 本人ロールがusers_rolesテーブルに関係を持つことはない
        self.assertFalse(self.factory2.user_role.exists(self.USER1.id, self_role.id))

        # プロジェクト管理者(USER2)に関係するusers_rolesテーブルのレコードを検証する
        user_roles = self.factory2.user_role.find_all_by_user_id(self.USER2.id)
        self.assertGreaterEqual(len(user_roles), 4)
        # everyoneロール
        user_role = self.factory2.user_role.find_by_id(self.USER2.id, everyone_role.id)
        self.assertFalse(user_role.owner)
        # プロジェクトロール1
        user_role = self.factory2.user_role.find_by_id(self.USER2.id, readers_role.id)
        self.assertTrue(user_role.owner)
        # プロジェクトロール2
        user_role = self.factory2.user_role.find_by_id(self.USER2.id, writers_role.id)
        self.assertTrue(user_role.owner)
        # プロジェクトロール3
        user_role = self.factory2.user_role.find_by_id(self.USER2.id, owners_role.id)
        self.assertTrue(user_role.owner)
        # 本人ロールがusers_rolesテーブルに関係を持つことはない
        self.assertFalse(self.factory2.user_role.exists(self.USER2.id, self_role.id))
        
        # プロジェクトに関係するauthsテーブルのレコードを検証する
        auths = self.factory2.auth.find_all_by_datum_id(project.id)
        self.assertEqual(len(auths), 8)

        self.assertTrue(self.factory2.auth.find_by_id(usr_admin_role.id, project.id, Auth.READ_OP))
        self.assertTrue(self.factory2.auth.find_by_id(usr_admin_role.id, project.id, Auth.WRITE_OP))
        self.assertTrue(self.factory2.auth.find_by_id(usr_admin_role.id, project.id, Auth.EXEC_OP))
        self.assertTrue(self.factory2.auth.find_by_id(usr_admin_role.id, project.id, Auth.OWN_OP))
        self.assertTrue(self.factory2.auth.find_by_id(readers_role.id, project.id, Auth.READ_OP))
        self.assertTrue(self.factory2.auth.find_by_id(readers_role.id, project.id, Auth.EXEC_OP))
        self.assertTrue(self.factory2.auth.find_by_id(writers_role.id, project.id, Auth.WRITE_OP))
        self.assertTrue(self.factory2.auth.find_by_id(owners_role.id, project.id, Auth.OWN_OP))

        # プロジェクトを再度ほかして、ゴミ箱を空にする
        project.throw_away()
        self.factory.data.find_trashcan().trash_all()

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

    def test_update_project(self):
        """
        プロジェクトのラベル名はプロジェクト管理者のみが変更できること
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()

        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('半休電車')
        project.save()
        project = project.reload()

        # メンバを設定する
        member1 = ProjectFolder.Member(self.USER2, ProjectFolder.WRITER_MEMBER_TYPE)
        member2 = ProjectFolder.Member(self.USER3, ProjectFolder.READER_MEMBER_TYPE)
        project.init_members([member1, member2], last_modified_at=project.modified_at)

        # 編集者は、プロジェクトのラベルを変更できること
        project = self.factory2.data.find_by_uuid(project.uuid)
        with self.assertRaises(NotAuthorizedException):
            project.update_data('阪神電車')
        self.assertEqual(project.label, '半休電車')

        # 閲覧者は、プロジェクトのラベルを変更できないこと
        project = self.factory3.data.find_by_uuid(project.uuid)
        with self.assertRaises(NotAuthorizedException):
            project.update_data('近鉄電車')
        self.assertEqual(project.label, '半休電車')

        # プロジェクトをほかして、ゴミ箱を空にする
        project = self.factory.data.find_by_uuid(project.uuid)
        self.assertEqual(project.label, '半休電車')
        project.throw_away()
        self.factory.data.find_trashcan().trash_all()

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
        flow = project.create_flow('フロー', FlowData())
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

        # プロジェクトメンバ以外のユーザ(USER3)は参照できないこと
        with self.assertRaises(NotAuthorizedException):
            project = self.factory3.data.find_by_uuid(project.uuid)

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

    def test_join_project1(self):
        """
        プロジェクト管理者を交代する
        (元のプロジェクト管理者は削除する)
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('アイドルプロジェクト！')
        project.save()
        project = project.reload()

        # メンバを設定する
        member1 = ProjectFolder.Member(self.USER3, ProjectFolder.OWNER_MEMBER_TYPE)
        project.init_members([member1], last_modified_at=project.modified_at)

        # メンバを取得する
        members = project.get_joined_members()

        # 期待する結果が返ることを確認する
        usr_admin_member = ProjectFolder.Member(self.USER1, ProjectFolder.OWNER_MEMBER_TYPE)
        self.assertEqual(len(members), 2)
        self.assertEqual(members, [member1, usr_admin_member])

        # ユーザ管理者を除外して、メンバを取得する
        members = project.get_joined_members(except_role_uuid=Role.USR_ADMIN_ROLE_UUID)

        # 期待する結果が返ることを確認する
        self.assertEqual(len(members), 1)
        self.assertEqual(members, [member1])

        # 元のプロジェクト管理者は、プロジェクトを更新できないこと
        with self.assertRaises(NotAuthorizedException):
            project.update_data('ぷろじぇくと1')

    def test_join_project2(self):
        """
        プロジェクト管理者を交代する
        (元のプロジェクト管理者は閲覧者にする)
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('V作戦')
        project.save()
        project = project.reload()

        # メンバを設定する
        member1 = ProjectFolder.Member(self.USER2, ProjectFolder.READER_MEMBER_TYPE)
        member2 = ProjectFolder.Member(self.USER3, ProjectFolder.OWNER_MEMBER_TYPE)
        project.init_members([member1, member2], last_modified_at=project.modified_at)

        # メンバを取得する
        members = project.get_joined_members()

        # 期待する結果が返ることを確認する
        usr_admin_member = ProjectFolder.Member(self.USER1, ProjectFolder.OWNER_MEMBER_TYPE)
        self.assertEqual(len(members), 3)
        self.assertEqual(members, [member2, usr_admin_member, member1])

        # ユーザ管理者を除外して、メンバを取得する
        members = project.get_joined_members(except_role_uuid=Role.USR_ADMIN_ROLE_UUID)

        # 期待する結果が返ることを確認する
        self.assertEqual(len(members), 2)
        self.assertEqual(members, [member2, member1])

        # 元のプロジェクト管理者は、プロジェクトを更新できないこと
        with self.assertRaises(NotAuthorizedException):
            project.update_data('ぷろじぇくと1')

    def test_join_project3(self):
        """
        プロジェクト管理者を交代する
        (ユーザ管理者はプロジェクト管理者から外すことはできないこと)
        (元のプロジェクト管理者は削除する)
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('プロジェクト1')
        project.save()
        project = project.reload()

        # メンバを設定する
        member1 = ProjectFolder.Member(self.USER2, ProjectFolder.OWNER_MEMBER_TYPE)
        member2 = ProjectFolder.Member(self.USER3, ProjectFolder.READER_MEMBER_TYPE)
        project.init_members([member1, member2], last_modified_at=project.modified_at)

        # メンバを取得する
        members = project.get_joined_members()

        # 期待する結果が返ることを確認する
        usr_admin_member = ProjectFolder.Member(self.USER1, ProjectFolder.OWNER_MEMBER_TYPE)
        self.assertEqual(len(members), 3)
        self.assertEqual(members, [member1, usr_admin_member, member2])

        # ユーザ管理者を除外して、メンバを取得する
        members = project.get_joined_members(except_role_uuid=Role.USR_ADMIN_ROLE_UUID)

        # 期待する結果が返ることを確認する
        self.assertEqual(len(members), 2)
        self.assertEqual(members, [member1, member2])

        # ユーザ管理者は、プロジェクトは更新できること
        project.update_data('ぷろじぇくと1')

        # プロジェクトは削除する
        project.delete()

    def test_join_project4(self):
        """
        プロジェクト管理者を交代する
        (ユーザ管理者はプロジェクト管理者から外すことはできないこと)
        (元のプロジェクト管理者は閲覧者にする)
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('プロジェクト2')
        project.save()
        project = project.reload()

        # メンバを設定する
        member1 = ProjectFolder.Member(self.USER1, ProjectFolder.READER_MEMBER_TYPE)
        member2 = ProjectFolder.Member(self.USER3, ProjectFolder.OWNER_MEMBER_TYPE)
        project.init_members([member1, member2], last_modified_at=project.modified_at)

        # メンバを取得する
        members = project.get_joined_members()

        # 期待する結果が返ることを確認する
        usr_admin_member = ProjectFolder.Member(self.USER1, ProjectFolder.OWNER_MEMBER_TYPE)
        self.assertEqual(len(members), 2)
        self.assertEqual(members, [member2, usr_admin_member])

        # ユーザ管理者を除外して、メンバを取得する
        members = project.get_joined_members(except_role_uuid=Role.USR_ADMIN_ROLE_UUID)

        # 期待する結果が返ることを確認する
        self.assertEqual(len(members), 2)
        self.assertEqual(members, [member2, member1])

        # ユーザ管理者は、プロジェクトは更新できること
        project.update_data('ぷろじぇくと2')

        # プロジェクトは削除する
        project.delete()

    def test_join_project_without_owner(self):
        """
        プロジェクト管理者を設定しない
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('プロジェクト3')
        project.save()
        project = project.reload()

        # プロジェクト管理者を設定しない場合でもエラーにならないこと
        member1 = ProjectFolder.Member(self.USER2, ProjectFolder.READER_MEMBER_TYPE)
        member2 = ProjectFolder.Member(self.USER3, ProjectFolder.WRITER_MEMBER_TYPE)
        project.init_members([member1, member2], last_modified_at=project.modified_at)

        # プロジェクトは削除する
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
        project = project.reload()

        # メンバを設定する
        member1 = ProjectFolder.Member(self.USER2, ProjectFolder.READER_MEMBER_TYPE)
        member2 = ProjectFolder.Member(self.USER3, ProjectFolder.OTHER_MEMBER_TYPE)
        with self.assertRaises(Exception):
            project.init_members([member1, member2], last_modified_at=project.modified_at)

        # プロジェクトは削除する
        project.delete()

    def test_join_project_without_member(self):
        """
        プロジェクトメンバに誰も設定しない
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('プロジェクト5')
        project.save()
        project = project.reload()

        # 誰も設定しない場合でもエラーにならないこと
        project.init_members([], last_modified_at=project.modified_at)

        # プロジェクトは削除する
        project.delete()

    def test_sys_admin_has_permissions(self):
        """
        システム管理者は、プロジェクトの
        参照・更新・実行・所有権限を付与されていないこと
        """
        # ルートフォルダを取得する
        root = self.factory3.data.load_root()
        # USER3は、ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('きらら⭐️三大言っていない名言！')
        project.save()
        project = project.reload()

        # プロジェクトにシステム管理者の権限が付与されていないこと
        sys_admin_role = self.factory3.role.load_sys_admin_role()
        self.assertFalse(self.factory3.auth.exists(sys_admin_role.id, project.id))

        # USER3は、プロジェクトの下にフォルダを作成する
        folder = project.create_folder('うるさいですね💢')
        folder.save()
        folder = folder.reload()

        # USER3は、フォルダの下にフローを作成する
        flow = folder.create_flow('シャミ子が悪いんだよ💘', FlowData())
        flow.save()
        flow = flow.reload()

        # USER3は、フォルダの下にフレームを作成する
        frame = folder.create_frame('お前がそう思うんならそうなんだろう お前ん中ではな', io.BytesIO(b'hidamari'))
        frame.save()
        frame = frame.reload()

        # システム管理者は、フォルダの参照ができないこと
        with self.assertRaises(NotAuthorizedException):
            self.factory0.data.find_by_uuid(folder.uuid)

        # システム管理者は、フローの参照ができないこと
        with self.assertRaises(NotAuthorizedException):
            self.factory0.data.find_by_uuid(flow.uuid)

        # システム管理者は、フレームの参照ができないこと
        with self.assertRaises(NotAuthorizedException):
            self.factory0.data.find_by_uuid(frame.uuid)

        # プロジェクト以外のDatumにシステム管理者の権限が付与されていないこと
        self.assertFalse(self.factory0.auth.exists(sys_admin_role.id, folder.id))
        self.assertFalse(self.factory0.auth.exists(sys_admin_role.id, flow.id))
        self.assertFalse(self.factory0.auth.exists(sys_admin_role.id, frame.id))

        # プロジェクトをほかす
        project.throw_away()

        # ゴミ箱を空にする
        self.factory3.data.find_trashcan().trash_all()

    def test_usr_admin_has_permissions(self):
        """
        ユーザ管理者は、プロジェクトの
        参照・更新・実行・所有権限を付与されていること
        """
        # ルートフォルダを取得する
        root = self.factory3.data.load_root()
        # USER3は、ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('😒😞😔😟😕🙁☹️😣😖😫😩🥺😢😭😤🤲🏾👐🏼')
        project.save()
        project = project.reload()

        # プロジェクトにユーザ管理者の権限が付与されていること
        usr_admin_role = self.factory3.role.load_usr_admin_role()
        self.assertTrue(self.factory3.auth.exists(usr_admin_role.id, project.id))

        # プロジェクトにユーザ管理者の参照・更新・実行・所有権限が付与されていること
        self.assertTrue(self.factory3.auth.exists(usr_admin_role.id, project.id))
        read_auth = self.factory3.auth.find_by_id(usr_admin_role.id, project.id, Auth.READ_OP)
        self.assertTrue(read_auth.permission)
        write_auth = self.factory3.auth.find_by_id(usr_admin_role.id, project.id, Auth.WRITE_OP)
        self.assertTrue(write_auth.permission)
        exec_auth = self.factory3.auth.find_by_id(usr_admin_role.id, project.id, Auth.EXEC_OP)
        self.assertTrue(exec_auth.permission)
        own_auth = self.factory3.auth.find_by_id(usr_admin_role.id, project.id, Auth.OWN_OP)
        self.assertTrue(own_auth.permission)

        # USER3は、プロジェクトの下にフォルダを作成する
        folder = project.create_folder('厭離穢土欣求浄土')
        folder.save()
        folder = folder.reload()

        # USER3は、フォルダの下にフローを作成する
        flow = folder.create_flow('疾如風徐如林侵掠如火不動如山', FlowData())
        flow.save()
        flow = flow.reload()

        # USER3は、フォルダの下にフレームを作成する
        frame = folder.create_frame('是非に及ばず', io.BytesIO(b'honnouji'))
        frame.save()
        frame = frame.reload()

        # ユーザ管理者は、フォルダの参照・更新ができること
        folder = self.factory.data.find_by_uuid(folder.uuid)
        folder.update_data('德川家康')

        # ユーザ管理者は、フォルダの参照・更新・実行のプロパティがTrueであること
        self.assertTrue(folder.readable)
        self.assertTrue(folder.writable)
        self.assertTrue(folder.executable)

        # ユーザ管理者は、フローの参照・更新・実行ができること
        flow = self.factory.data.find_by_uuid(flow.uuid)
        flow.update_data('武田晴信', FlowData())
        flow.flow_data.get_nodes(use_exec_auth=True)

        # ユーザ管理者は、フローの参照・更新・実行のプロパティがTrueであること
        self.assertTrue(flow.readable)
        self.assertTrue(flow.writable)
        self.assertTrue(flow.executable)

        # ユーザ管理者は、フレームの参照・更新ができること
        frame = self.factory.data.find_by_uuid(frame.uuid)
        frame.update_label('織田信長')
        
        # ユーザ管理者は、フレームの参照・更新のプロパティがTrueであること
        self.assertTrue(frame.readable)
        self.assertTrue(frame.writable)
        self.assertFalse(frame.executable)

        # プロジェクト以外のDatumにユーザ管理者の権限が付与されていないこと
        self.assertFalse(self.factory.auth.exists(usr_admin_role.id, folder.id))
        self.assertFalse(self.factory.auth.exists(usr_admin_role.id, flow.id))
        self.assertFalse(self.factory.auth.exists(usr_admin_role.id, frame.id))

        # プロジェクトをほかす
        project.throw_away()

        # ゴミ箱を空にする
        self.factory3.data.find_trashcan().trash_all()

    def test_join_by_serial(self):
        """
        プロジェクトメンバの設定は、順次実行すればいずれも更新できる
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('ビッグカメラ')
        project.save()

        # USER2は、プロジェクトを取得する
        project = project.reload()

        # USER2は、メンバを設定する
        member1 = ProjectFolder.Member(self.USER2, ProjectFolder.OWNER_MEMBER_TYPE)
        project.init_members([member1], last_modified_at=project.modified_at)

        # USER1は、プロジェクトを取得する
        project2 = self.factory.data.find_by_uuid(project.uuid)

        # USER1は、メンバを設定する
        member1 = ProjectFolder.Member(self.USER2, ProjectFolder.OWNER_MEMBER_TYPE)
        project2.init_members([member1], last_modified_at=project2.modified_at)

        # プロジェクトは削除する
        project.delete()

    def test_cannot_join_by_late_user(self):
        """
        プロジェクトメンバの設定は、先にプロジェクトを更新した方が更新できる
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('ヨドバシカメラ')
        project.save()

        # USER2は、プロジェクトを取得する
        project = project.reload()

        # USER1は、プロジェクトを取得する
        project2 = self.factory.data.find_by_uuid(project.uuid)

        # USER1は、メンバを設定する
        member1 = ProjectFolder.Member(self.USER2, ProjectFolder.OWNER_MEMBER_TYPE)
        project2.init_members([member1], last_modified_at=project2.modified_at)

        # USER2は、メンバを設定する
        with self.assertRaises(OptimisticLockException):
            member1 = ProjectFolder.Member(self.USER2, ProjectFolder.OWNER_MEMBER_TYPE)
            project.init_members([member1], last_modified_at=project.modified_at)

        # プロジェクトは削除する
        project.delete()

    def test_cannot_join_by_late_user2(self):
        """
        プロジェクトメンバの設定は、先にプロジェクトを更新した方が更新できる
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('Joshin')
        project.save()

        # USER2は、プロジェクトを取得する
        project = project.reload()

        # USER1は、プロジェクトを取得する
        project2 = self.factory.data.find_by_uuid(project.uuid)

        # USER1は、メンバを追加する
        member1 = ProjectFolder.Member(self.USER2, ProjectFolder.OWNER_MEMBER_TYPE)
        project2.join_member(member1)

        # USER2は、メンバを設定する
        with self.assertRaises(OptimisticLockException):
            member1 = ProjectFolder.Member(self.USER2, ProjectFolder.OWNER_MEMBER_TYPE)
            project.init_members([member1], last_modified_at=project.modified_at)

        # プロジェクトは削除する
        project.delete()

    def test_cannot_join_by_late_user3(self):
        """
        プロジェクトメンバの設定は、先にプロジェクトを更新した方が更新できる
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('Ninomiya')
        project.save()

        # USER2は、プロジェクトを取得する
        project = project.reload()

        # USER2は、メンバを追加する
        member1 = ProjectFolder.Member(self.USER3, ProjectFolder.OWNER_MEMBER_TYPE)
        project.join_member(member1)

        # USER1は、プロジェクトを取得する
        project2 = self.factory.data.find_by_uuid(project.uuid)

        # USER1は、メンバを外す
        project2.leave_member(self.USER3)

        # USER2は、メンバを設定する
        with self.assertRaises(OptimisticLockException):
            member1 = ProjectFolder.Member(self.USER2, ProjectFolder.OWNER_MEMBER_TYPE)
            project.init_members([member1], last_modified_at=project.modified_at)

        # プロジェクトは削除する
        project.delete()

    def test_move_flow_with_cache1(self):
        """
        フローをプロジェクトを跨いで移動する場合は、
        紐づくキャッシュの権限も再設定されること
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()

        # ルートフォルダの下にプロジェクト1を作成する
        project1 = root.create_project_folder('UFO')
        project1.save()
        project1 = project1.reload()

        # ルートフォルダの下にプロジェクト2を作成する
        project2 = root.create_project_folder('ペヤング')
        project2.save()
        project2 = project2.reload()

        # プロジェクトの下にフローを作成する
        flow_data = FlowData(copy.deepcopy(self.flow_json))
        flow = project1.create_flow('どん兵衛', flow_data)
        flow.save()
        flow = flow.reload() 

        # フローを実行する
        from kskp.engine import execute, FlowCommand
        link = FlowCommand(flow)
        lasts = execute(runnable=link, args={}, inputs={})
        # フローの実行結果を取得する
        out_frame = AuthTest.get_frame_from_lasts(lasts)

        # プロジェクト管理者は、フローのキャッシュを参照できること
        cache_frame_uuid = flow.flow_data.get_cache_frame_uuids()[0]
        cache_frame = self.factory2.data.find_by_uuid(cache_frame_uuid)

        # フローをプロジェクト2に移動する
        flow.move(project2.uuid)

        # キャッシュの権限設定を検証する
        auths = self.factory.auth.find_all_by_datum_id(cache_frame.id)
        self.assertEqual(len(auths), 6)
        # 取得した権限を検証する
        usr_admin_role = self.factory.role.load_usr_admin_role()
        readers_role = project2._find_readers_role()
        writers_role = project2._find_writers_role()
        # ユーザ管理者ロールの参照権限
        self.assertEqual(auths[0].role_id, usr_admin_role.id)
        self.assertEqual(auths[0].datum_id, cache_frame.id)
        self.assertEqual(auths[0].operation, Auth.READ_OP)
        self.assertEqual(auths[0].permission, True)
        self.assertEqual(auths[0].creator, self.USER2)
        self.assertEqual(auths[0].modifier, self.USER2)
        self.assertIsNotNone(auths[0].created_at)
        self.assertIsNotNone(auths[0].modified_at)
        # ユーザ管理者ロールの更新権限
        self.assertEqual(auths[1].role_id, usr_admin_role.id)
        self.assertEqual(auths[1].datum_id, cache_frame.id)
        self.assertEqual(auths[1].operation, Auth.WRITE_OP)
        self.assertEqual(auths[1].permission, True)
        self.assertEqual(auths[1].creator, self.USER2)
        self.assertEqual(auths[1].modifier, self.USER2)
        self.assertIsNotNone(auths[1].created_at)
        self.assertIsNotNone(auths[1].modified_at)
        # ユーザ管理者ロールの所有権限
        self.assertEqual(auths[2].role_id, usr_admin_role.id)
        self.assertEqual(auths[2].datum_id, cache_frame.id)
        self.assertEqual(auths[2].operation, Auth.OWN_OP)
        self.assertEqual(auths[2].permission, True)
        self.assertEqual(auths[2].creator, self.USER2)
        self.assertEqual(auths[2].modifier, self.USER2)
        self.assertIsNotNone(auths[2].created_at)
        self.assertIsNotNone(auths[2].modified_at)
        # プロジェクト2のReadersロールの参照権限
        self.assertEqual(auths[3].role_id, readers_role.id)
        self.assertEqual(auths[3].datum_id, cache_frame.id)
        self.assertEqual(auths[3].operation, Auth.READ_OP)
        self.assertEqual(auths[3].permission, True)
        self.assertEqual(auths[3].creator, self.USER2)
        self.assertEqual(auths[3].modifier, self.USER2)
        self.assertIsNotNone(auths[3].created_at)
        self.assertIsNotNone(auths[3].modified_at)
        # プロジェクト2のWritersロールの更新権限
        self.assertEqual(auths[4].role_id, writers_role.id)
        self.assertEqual(auths[4].datum_id, cache_frame.id)
        self.assertEqual(auths[4].operation, Auth.WRITE_OP)
        self.assertEqual(auths[4].permission, True)
        self.assertEqual(auths[4].creator, self.USER2)
        self.assertEqual(auths[4].modifier, self.USER2)
        self.assertIsNotNone(auths[4].created_at)
        self.assertIsNotNone(auths[4].modified_at)
        # プロジェクト2のWritersロールの所有権限
        self.assertEqual(auths[5].role_id, writers_role.id)
        self.assertEqual(auths[5].datum_id, cache_frame.id)
        self.assertEqual(auths[5].operation, Auth.OWN_OP)
        self.assertEqual(auths[5].permission, True)
        self.assertEqual(auths[5].creator, self.USER2)
        self.assertEqual(auths[5].modifier, self.USER2)
        self.assertIsNotNone(auths[5].created_at)
        self.assertIsNotNone(auths[5].modified_at)

        # プロジェクトとキャッシュを削除する
        project1.throw_away()
        project2.throw_away()

        # ゴミ箱を空にする
        self.factory2.data.find_trashcan().trash_all()

        # 最後にキャッシュを削除する
        cache_frame.delete()

    def test_move_flow_with_cache2(self):
        """
        フローをプロジェクト内からプロジェクト外へ移動する場合は、
        紐づくキャッシュの権限も再設定されること
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()

        # ルートフォルダの下にプロジェクト1を作成する
        project1 = root.create_project_folder('ラ王')
        project1.save()
        project1 = project1.reload()

        # プロジェクトの下にフローを作成する
        flow_data = FlowData(copy.deepcopy(self.flow_json))
        flow = project1.create_flow('辛ラーメン', flow_data)
        flow.save()
        flow = flow.reload() 

        # フローを実行する
        from kskp.engine import execute, FlowCommand
        link = FlowCommand(flow)
        lasts = execute(runnable=link, args={}, inputs={})
        # フローの実行結果を取得する
        out_frame = AuthTest.get_frame_from_lasts(lasts)

        # プロジェクト管理者は、フローのキャッシュを参照できること
        cache_frame_uuid = flow.flow_data.get_cache_frame_uuids()[0]
        cache_frame = self.factory2.data.find_by_uuid(cache_frame_uuid)

        # フローをキャッシュフォルダに移動する
        flow.move(Datum.CACHE_FOLDER_UUID)

        # キャッシュの権限設定を検証する
        auths = self.factory.auth.find_all_by_datum_id(cache_frame.id)
        self.assertEqual(len(auths), 6)
        # 取得した権限を検証する
        usr_admin_role = self.factory.role.load_usr_admin_role()
        readers_role = project1._find_readers_role()
        writers_role = project1._find_writers_role()
        # ユーザ管理者ロールの参照権限
        self.assertEqual(auths[0].role_id, usr_admin_role.id)
        self.assertEqual(auths[0].datum_id, cache_frame.id)
        self.assertEqual(auths[0].operation, Auth.READ_OP)
        self.assertEqual(auths[0].permission, True)
        self.assertEqual(auths[0].creator, self.USER2)
        self.assertEqual(auths[0].modifier, self.USER2)
        self.assertIsNotNone(auths[0].created_at)
        self.assertIsNotNone(auths[0].modified_at)
        # ユーザ管理者ロールの更新権限
        self.assertEqual(auths[1].role_id, usr_admin_role.id)
        self.assertEqual(auths[1].datum_id, cache_frame.id)
        self.assertEqual(auths[1].operation, Auth.WRITE_OP)
        self.assertEqual(auths[1].permission, True)
        self.assertEqual(auths[1].creator, self.USER2)
        self.assertEqual(auths[1].modifier, self.USER2)
        self.assertIsNotNone(auths[1].created_at)
        self.assertIsNotNone(auths[1].modified_at)
        # ユーザ管理者ロールの所有権限
        self.assertEqual(auths[2].role_id, usr_admin_role.id)
        self.assertEqual(auths[2].datum_id, cache_frame.id)
        self.assertEqual(auths[2].operation, Auth.OWN_OP)
        self.assertEqual(auths[2].permission, True)
        self.assertEqual(auths[2].creator, self.USER2)
        self.assertEqual(auths[2].modifier, self.USER2)
        self.assertIsNotNone(auths[2].created_at)
        self.assertIsNotNone(auths[2].modified_at)
        # プロジェクト2のReadersロールの参照権限
        self.assertEqual(auths[3].role_id, readers_role.id)
        self.assertEqual(auths[3].datum_id, cache_frame.id)
        self.assertEqual(auths[3].operation, Auth.READ_OP)
        self.assertEqual(auths[3].permission, True)
        self.assertEqual(auths[3].creator, self.USER2)
        self.assertEqual(auths[3].modifier, self.USER2)
        self.assertIsNotNone(auths[3].created_at)
        self.assertIsNotNone(auths[3].modified_at)
        # プロジェクト2のWritersロールの更新権限
        self.assertEqual(auths[4].role_id, writers_role.id)
        self.assertEqual(auths[4].datum_id, cache_frame.id)
        self.assertEqual(auths[4].operation, Auth.WRITE_OP)
        self.assertEqual(auths[4].permission, True)
        self.assertEqual(auths[4].creator, self.USER2)
        self.assertEqual(auths[4].modifier, self.USER2)
        self.assertIsNotNone(auths[4].created_at)
        self.assertIsNotNone(auths[4].modified_at)
        # プロジェクト2のWritersロールの所有権限
        self.assertEqual(auths[5].role_id, writers_role.id)
        self.assertEqual(auths[5].datum_id, cache_frame.id)
        self.assertEqual(auths[5].operation, Auth.OWN_OP)
        self.assertEqual(auths[5].permission, True)
        self.assertEqual(auths[5].creator, self.USER2)
        self.assertEqual(auths[5].modifier, self.USER2)
        self.assertIsNotNone(auths[5].created_at)
        self.assertIsNotNone(auths[5].modified_at)

        # プロジェクトとキャッシュを削除する
        project1.throw_away()

        # ゴミ箱を空にする
        self.factory2.data.find_trashcan().trash_all()

        # 最後にキャッシュを削除する
        cache_frame.delete()

    # 
    # Edit Lock
    # 

    def test_edit_lock_on_root(self):
        """
        Flowの編集ロックをONにすると更新できないこと
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()
        # ルートフォルダの下にフレームを作成する
        frame = root.create_frame('だーれが', io.BytesIO(b''))
        frame.save()
        # ルートフォルダの下にフローを作成する
        flow = root.create_simple_flow('殺した', frame)
        flow.save()

        # フローを再取得する
        flow = flow.reload()

        # フローJSONのうちnodes以外のキーは取得できること
        self.assertEqual(flow.flow_data.label, '殺した')
        self.assertEqual(flow.flow_data.description, '')
        self.assertEqual(flow.flow_data.ports, [[],[]])
        self.assertTrue(flow.flow_data.has_nodes)
        self.assertEqual(len(flow.flow_data.get_nodes()), 1)

        # フローを編集ロックする
        flow.edit_lock = True
        self.assertTrue(flow.edit_lock)

        # 編集ロックされたフローは更新できないこと
        with self.assertRaises(EditLockedException):
            flow_data = FlowData(copy.deepcopy(self.flow_json))
            flow.update_data('ククロビン', flow_data)

        # 編集ロックされたフローは削除できないこと
        with self.assertRaises(EditLockedException):
            flow.delete()

        # Rollback後のpermissionはNoneになるのでフローを再取得する
        flow = flow.reload()

        # 編集ロックを解除する
        flow.edit_lock = False
        self.assertFalse(flow.edit_lock)

        # 編集ロックが解除されたフローは更新できること
        flow_data = FlowData(copy.deepcopy(self.flow_json))
        flow.update_data('だーれが殺したククロビン', flow_data)
        self.assertEqual(flow.label, 'だーれが殺したククロビン')

        # フローとフレームを削除する
        frame.delete()
        flow.delete()

    def test_cannot_turn_edit_lock_by_reader(self):
        """
        閲覧者は編集ロックの値を変更できないこと
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()

        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('花は爛漫咲き誇りー')
        project.save()
        project = project.reload()

        # プロジェクトの下にフローを作成する
        flow_data = FlowData(copy.deepcopy(self.flow_json))
        flow = project.create_flow('天下太平マリネラじゃー', flow_data)
        flow.save()
        flow = flow.reload()

        # メンバを設定する
        member1 = ProjectFolder.Member(self.USER2, ProjectFolder.OWNER_MEMBER_TYPE)
        member2 = ProjectFolder.Member(self.USER0, ProjectFolder.WRITER_MEMBER_TYPE)
        member3 = ProjectFolder.Member(self.USER3, ProjectFolder.READER_MEMBER_TYPE)
        project.init_members([member1, member2, member3], last_modified_at=project.modified_at)

        # フローを編集ロックする
        flow.edit_lock = True
        self.assertTrue(flow.edit_lock)

        # 編集ロックを解除する
        flow.edit_lock = False
        self.assertFalse(flow.edit_lock)

        # 閲覧者は編集ロックの値を変更できないこと
        flow = self.factory3.data.find_by_uuid(flow.uuid)
        with self.assertRaises(NotAuthorizedException):
            flow.edit_lock = True
        with self.assertRaises(NotAuthorizedException):
            flow.edit_lock = False
        
        # 閲覧者でも編集ロックの値を参照できること
        self.assertFalse(flow.edit_lock)

        # 編集者は編集ロックの値を変更できること
        flow = self.factory0.data.find_by_uuid(flow.uuid)
        flow.edit_lock = True
        self.assertTrue(flow.edit_lock)
        flow.edit_lock = False
        self.assertFalse(flow.edit_lock)
        
        # 編集者は編集ロックの値を参照できること
        self.assertFalse(flow.edit_lock)

        # プロジェクトを削除する
        project.throw_away()

        # ゴミ箱を空にする
        self.factory2.data.find_trashcan().trash_all()

    def test_cannot_move_edit_locked_flow(self):
        """
        編集ロックがONのFlowは移動できないこと
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()

        # ルートフォルダの下にプロジェクト1を作成する
        project1 = root.create_project_folder('あーの顔見ーたらどうしても')
        project1.save()
        project1 = project1.reload()

        # ルートフォルダの下にプロジェクト2を作成する
        project2 = root.create_project_folder('つぶれアンマン')
        project2.save()
        project2 = project1.reload()

        # プロジェクト1の下にフローを作成する
        flow_data = FlowData(copy.deepcopy(self.flow_json))
        flow = project1.create_flow('どうした、どうした', flow_data)
        flow.save()
        flow = flow.reload()

        # メンバを設定する
        member1 = ProjectFolder.Member(self.USER2, ProjectFolder.OWNER_MEMBER_TYPE)
        member2 = ProjectFolder.Member(self.USER3, ProjectFolder.WRITER_MEMBER_TYPE)
        project1.init_members([member1, member2], last_modified_at=project1.modified_at)

        # フローを編集ロックする
        flow.edit_lock = True
        self.assertTrue(flow.edit_lock)

        # 編集ロックされたフローは移動できないこと
        with self.assertRaises(EditLockedException):
            flow.move(project2.uuid)

        # Roleback後は権限情報がNoneになるので再読み込みする
        flow = flow.reload()

        # 編集ロックを解除する
        flow.edit_lock = False
        self.assertFalse(flow.edit_lock)

        # 設定した編集ロックに基づいた_permissionsの値を再設定する
        # (編集ロックの設定のたびにreload()するのはテストコードの記述者にとっては面倒だが
        #  APIでの処理においてはreload()は必要のない重たい処理なので、set_edit_lock()内では行わないこととする)
        flow = flow.reload()

        # プロジェクトを削除する
        project1.throw_away()

        # ゴミ箱を空にする
        self.factory2.data.find_trashcan().trash_all()

    #
    # Other Datum
    # 

    def test_cannot_move_datum_to_root(self):
        """
        プロジェクト以外のDatumはルートフォルダへ移動できないこと
        """
        # ルートフォルダを取得する
        root = self.factory3.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('猫ハウス📦')
        project.save()

        # プロジェクトの下にフレームを作成する
        frame = project.create_frame('にゃゴー', io.BytesIO(b''))
        frame.save()

        # フレームはルートの直下に移動できないこと
        with self.assertRaises(Exception):
            frame.move(root.uuid)

        # プロジェクトの下にフォルダを作成する
        folder = project.create_folder('にゃおーん🐱')
        folder.save()
        folder = folder.reload()

        # フォルダはルートの直下に移動できないこと
        with self.assertRaises(Exception):
            folder.move(root.uuid)

        # フレームとフォルダはゴミ箱へは移動できること
        frame.throw_away()
        folder.throw_away()

        # ゴミ箱を空にする
        self.factory3.data.find_trashcan().trash_all()

    def test_cannnot_move_system_folder(self):
        """
        システムフォルダは移動できないこと
        """
        # ルートフォルダを取得する
        root = self.factory3.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('そうiPhoneならね')
        project.save()
        project = project.reload()

        # ルートフォルダは移動できないこと
        with self.assertRaises(Exception):
            root.move(project.uuid)

        # キャッシュフォルダは移動できないこと
        cache_folder = self.factory.data.load_cache_folder()
        with self.assertRaises(Exception):
            cache_folder.move(project.uuid)

        # ゴミ箱は移動できないこと
        trashcan = self.factory.data.load_trash_folder()
        with self.assertRaises(Exception):
            trashcan.move(project.uuid)

        # プロジェクトをほかす
        project.throw_away()

        # ゴミ箱を空にする
        trashcan.trash_all()

    def test_cannot_save_datum_at_root(self):
        """
        ユーザ管理者以外は、ルートフォルダにプロジェクト以外のDatumを新規追加できないこと
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()

        # ユーザ管理者は、ルートフォルダの下にフレームを作成できること
        frame = root.create_frame('ワンワン🐕', io.BytesIO(b'wanwan'))
        frame.save()

        # フレームが作成されていること
        self.assertTrue(self.factory.data.exists(frame.uuid))

        # 一般ユーザは、ルートフォルダを取得する
        root = self.factory3.data.load_root()

        # 一般ユーザは、ルートフォルダの下にフローを作成できないこと
        flow = root.create_flow('ワオーン🐕‍🦺', FlowData())
        with self.assertRaises(Exception):
            flow.save()

        # フローは作成されていないこと
        self.assertFalse(self.factory3.data.exists(flow.uuid))

        # 一般ユーザは、ルートフォルダの下にフォルダを作成できないこと
        folder = root.create_folder('ワン！')
        with self.assertRaises(Exception):
            folder.save()

        # フォルダは作成されていないこと
        self.assertFalse(self.factory3.data.exists(folder.uuid))

        # フレームを削除する
        frame.delete()

    def test_everyone_has_permissions(self):
        """
        everyoneは、プロジェクト以外の全てのDatumの
        参照・更新・実行・所有権限を付与されていること
        """
        # ルートフォルダを取得する
        root = self.factory3.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('MacBook Pro')
        project.save()
        project = project.reload()

        # プロジェクトにeveryoneロールの権限を付与されていないこと
        everyone_role = self.factory3.role.load_everyone_role()
        self.assertFalse(self.factory3.auth.exists(everyone_role.id, project.id))

        # プロジェクトの下にフォルダを作成する
        folder = project.create_folder('Mac mini')
        folder.save()
        folder = folder.reload()

        # フォルダにeveryoneロールの参照・更新・実行権限が付与されていること
        self.assertTrue(self.factory3.auth.exists(everyone_role.id, folder.id))
        read_auth = self.factory3.auth.find_by_id(everyone_role.id, folder.id, Auth.READ_OP)
        self.assertTrue(read_auth.permission)
        write_auth = self.factory3.auth.find_by_id(everyone_role.id, folder.id, Auth.WRITE_OP)
        self.assertTrue(write_auth.permission)
        exec_auth = self.factory3.auth.find_by_id(everyone_role.id, folder.id, Auth.EXEC_OP)
        self.assertTrue(exec_auth.permission)
        own_auth = self.factory3.auth.find_by_id(everyone_role.id, folder.id, Auth.OWN_OP)
        self.assertTrue(own_auth.permission)

        # フォルダの下にフローを作成する
        flow = folder.create_flow('Mac pro', FlowData())
        flow.save()
        flow = flow.reload()

        # フローにeveryoneロールの参照・更新・実行権限が付与されていること
        self.assertTrue(self.factory3.auth.exists(everyone_role.id, flow.id))
        read_auth = self.factory3.auth.find_by_id(everyone_role.id, flow.id, Auth.READ_OP)
        self.assertTrue(read_auth.permission)
        write_auth = self.factory3.auth.find_by_id(everyone_role.id, flow.id, Auth.WRITE_OP)
        self.assertTrue(write_auth.permission)
        exec_auth = self.factory3.auth.find_by_id(everyone_role.id, flow.id, Auth.EXEC_OP)
        self.assertTrue(exec_auth.permission)
        own_auth = self.factory3.auth.find_by_id(everyone_role.id, flow.id, Auth.OWN_OP)
        self.assertTrue(own_auth.permission)

        # フォルダの下にフレームを作成する
        frame = folder.create_frame('iMac', io.BytesIO(b'mac'))
        frame.save()
        frame = frame.reload()

        # フレームにeveryoneロールの参照・更新権限が付与されていること
        self.assertTrue(self.factory3.auth.exists(everyone_role.id, frame.id))
        self.assertFalse(self.factory3.auth.exists(everyone_role.id, frame.id, Auth.EXEC_OP))
        read_auth = self.factory3.auth.find_by_id(everyone_role.id, frame.id, Auth.READ_OP)
        self.assertTrue(read_auth.permission)
        write_auth = self.factory3.auth.find_by_id(everyone_role.id, frame.id, Auth.WRITE_OP)
        self.assertTrue(write_auth.permission)
        own_auth = self.factory3.auth.find_by_id(everyone_role.id, frame.id, Auth.OWN_OP)
        self.assertTrue(own_auth.permission)

        # プロジェクトをほかす
        project.throw_away()

        # ゴミ箱を空にする
        self.factory3.data.find_trashcan().trash_all()

    def test_user_admin_has_permissoins(self):
        """
        ユーザ管理者は、全てのDatumの参照・更新ができること
        """
        # ルートフォルダを取得する
        root = self.factory3.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('そうだ！そうだ！金さんをだせ！')
        project.save()
        project = project.reload()

        # プロジェクトにユーザ管理者ロールの権限を付与されていること
        usr_admin_role = self.factory3.role.load_usr_admin_role()
        self.assertTrue(self.factory3.auth.exists(usr_admin_role.id, project.id))
        read_auth = self.factory3.auth.find_by_id(usr_admin_role.id, project.id, Auth.READ_OP)
        self.assertTrue(read_auth.permission)
        write_auth = self.factory3.auth.find_by_id(usr_admin_role.id, project.id, Auth.WRITE_OP)
        self.assertTrue(write_auth.permission)
        exec_auth = self.factory3.auth.find_by_id(usr_admin_role.id, project.id, Auth.EXEC_OP)
        self.assertTrue(exec_auth.permission)
        own_auth = self.factory3.auth.find_by_id(usr_admin_role.id, project.id, Auth.OWN_OP)
        self.assertTrue(own_auth.permission)

        # プロジェクトの下にフォルダを作成する
        folder = project.create_folder('おうおうおう、さっきから黙って聞いてりゃ、金さんだとぉ？')
        folder.save()
        folder = folder.reload()

        # フォルダにユーザ管理者ロールの参照・更新・実行権限が付与されていないこと
        self.assertFalse(self.factory3.auth.exists(usr_admin_role.id, folder.id))

        # フォルダの下にフローを作成する
        flow = folder.create_flow('テメエらの所業は御天道様がちゃーんと見ているぜ', FlowData())
        flow.save()
        flow = flow.reload()

        # フローにユーザ管理者ロールの参照・更新・実行権限が付与されていないこと
        self.assertFalse(self.factory3.auth.exists(usr_admin_role.id, flow.id))

        # フォルダの下にフレームを作成する
        frame = folder.create_frame('この桜吹雪散らせるもんなら散らしてみろおぃ！', io.BytesIO(b'babaaaan'))
        frame.save()
        frame = frame.reload()

        # フレームにユーザ管理者ロールの参照・更新・実行権限が付与されていないこと
        self.assertFalse(self.factory3.auth.exists(usr_admin_role.id, frame.id))

        # ユーザ管理者はフローの参照・更新ができること
        flow = self.factory.data.find_by_uuid(flow.uuid)
        flow.update_data('越後屋久兵衛、市中引き回しの上獄門！その他の者は終生遠島とする！ひったてい！', FlowData())

        # ユーザ管理者はフローをほかせること
        flow.throw_away()

        # ユーザ管理者はプロジェクトの参照・更新ができること
        project = self.factory.data.find_by_uuid(project.uuid)
        project.update_data('これにて一件落着')

        # ユーザ管理者はプロジェクトをほかせること
        project.throw_away()

        # ゴミ箱を空にする
        self.factory.data.find_trashcan().trash_all()

    def test_cannot_read_trash_by_other_user(self):
        """
        プロジェクトから捨てたゴミを、
        プロジェクトメンバ以外のユーザが参照できないこと(ゴミ漁り禁止!🚫)
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('ねこまんま')
        project.save()
        project = project.reload()

        # プロジェクトの下にフォルダを作成する
        folder = project.create_folder('猫ハウス')
        folder.save()
        folder = folder.reload()

        # フォルダの下にフローを作成する
        flow = folder.create_flow('かつお節', FlowData())
        flow.save()
        flow = flow.reload() 

        # フォルダをほかす
        folder.throw_away()

        # プロジェクトメンバ以外のユーザがゴミを参照できないこと
        with self.assertRaises(NotAuthorizedException):
            self.factory3.data.find_by_uuid(folder.uuid)
        with self.assertRaises(NotAuthorizedException):
            self.factory3.data.find_by_uuid(flow.uuid)
        
        # プロジェクトをほかす
        project.throw_away()

        # 先にプロジェクトを物理削除する
        project.delete()

        # プロジェクトメンバ以外のユーザがゴミを参照できないこと
        with self.assertRaises(NotAuthorizedException):
            self.factory3.data.find_by_uuid(folder.uuid)
        with self.assertRaises(NotAuthorizedException):
            self.factory3.data.find_by_uuid(flow.uuid)

        # フォルダを物理削除する
        flow.delete()
        folder.delete()

    def test_cannot_write_trash_by_reader(self):
        """
        プロジェクトから捨てたゴミを、
        閲覧者が更新したり元の位置に戻せないこと
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('ひとーーつ、人の世の生き血をすすり')
        project.save()
        project = project.reload()

        # メンバを設定する
        member1 = ProjectFolder.Member(self.USER2, ProjectFolder.OWNER_MEMBER_TYPE)
        member2 = ProjectFolder.Member(self.USER3, ProjectFolder.READER_MEMBER_TYPE)
        project.init_members([member1, member2], last_modified_at=project.modified_at)

        # プロジェクトの下にフォルダを作成する
        folder = project.create_folder('ふたつ、不埒な悪行三昧')
        folder.save()
        folder = folder.reload()

        # フォルダの下にフローを作成する
        flow = folder.create_flow('みっつ、醜い浮世の鬼を', FlowData({'label': '退治てくれよう桃太郎！'}))
        flow.save()
        flow = flow.reload() 

        # フォルダをほかす
        folder.throw_away()

        # 閲覧者はゴミを参照できること
        folder = self.factory3.data.find_by_uuid(folder.uuid)
        flow = self.factory3.data.find_by_uuid(flow.uuid)

        # 閲覧者はゴミを更新できないこと
        with self.assertRaises(NotAuthorizedException):
            folder.update_data('不埒な悪行三昧')
        with self.assertRaises(NotAuthorizedException):
            flow.update_data('醜い浮き世の鬼を', FlowData())

        # 閲覧者はゴミを元の場所に戻せないこと
        with self.assertRaises(NotAuthorizedException):
            folder.put_back()

        # 閲覧者はゴミを物理削除できないこと
        with self.assertRaises(NotAuthorizedException):
            folder.delete()
        with self.assertRaises(NotAuthorizedException):
            flow.delete()

        # プロジェクト管理者はゴミ箱を空にする
        trashcan = self.factory2.data.find_trashcan()
        trashcan.trash_all()

        # ゴミ箱は空になっていること
        children = trashcan.find_children()
        self.assertEqual(len(children), 0)

        # プロジェクトを削除する
        project.delete()

    def test_cannot_read_trashed_folder_by_other_user(self):
        """
        ゴミ箱に作成した形代フォルダは、
        プロジェクトメンバ以外のユーザが参照できないこと
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('人間五十年')
        project.save()
        project = project.reload()

        # プロジェクトの下にフォルダを作成する
        folder = project.create_folder('下天のうちに比べれば')
        folder.save()
        folder = folder.reload()

        # フォルダの下にデータソースを作成する
        source = folder.create_frame('夢のまた夢', io.BytesIO(b''))
        source.save()
        source = source.reload()

        # フォルダの下にもう一つフレームを作成する
        frame = folder.create_frame('是非もなし', io.BytesIO(b''))
        frame.save()
        frame = frame.reload()

        # プロジェクトの下にフローを作成する
        flow = project.create_simple_flow('難波のことも', source)
        flow.save()
        flow = flow.reload()

        # フォルダをほかす
        # (データソースはフローから参照されているので、ゴミ箱にフォルダの形代が作成される)
        trashed_folder = folder.throw_away()

        # プロジェクトメンバ以外のユーザは、形代フォルダを参照できないこと
        with self.assertRaises(NotAuthorizedException):
            self.factory3.data.find_by_uuid(trashed_folder.uuid)

        # 形代フォルダをほかす前の場所に戻す
        trashed_folder.put_back()

        # 形代フォルダはゴミ箱に残る
        self.assertEqual(trashed_folder.find_parent(), self.factory2.data.load_trash_folder())

        # 中のフォルダはほかす前の場所に戻っていること
        self.assertEqual(folder.find_parent(), project)

        # プロジェクトをゴミ箱にほかす
        project.throw_away()

        # ゴミ箱を空にする
        trashcan = self.factory2.data.find_trashcan()
        trashcan.trash_all()

        # ゴミ箱は空になっていること
        children = trashcan.find_children()
        self.assertEqual(len(children), 0)
        
    def test_cannot_write_trashed_folder_by_reader(self):
        """
        ゴミ箱に作成した形代フォルダは、
        閲覧者が更新したり元の位置に戻せないこと
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('中村主水')
        project.save()
        project = project.reload()

        # プロジェクトの下にフォルダを作成する
        folder = project.create_folder('婿殿！')
        folder.save()
        folder = folder.reload()

        # フォルダの下にデータソースを作成する
        source = folder.create_frame('あなたまた酔って帰ってきたんですね', io.BytesIO(b''))
        source.save()
        source = source.reload()

        # フォルダの下にもう一つフレームを作成する
        frame = folder.create_frame('この中村家は由緒正しき家柄それをこともあろうに・・', io.BytesIO(b''))
        frame.save()
        frame = frame.reload()

        # プロジェクトの下にフローを作成する
        flow = project.create_simple_flow('これといった手柄も立てず・・', source)
        flow.save()
        flow = flow.reload()

        # フォルダをほかす
        # (データソースはフローから参照されているので、ゴミ箱にフォルダの形代が作成される)
        trashed_folder = folder.throw_away()

        # USER3を閲覧者としてプロジェクトメンバに加える
        project.join_member(ProjectFolder.Member(self.USER3, ProjectFolder.READER_MEMBER_TYPE))

        # 閲覧者は、形代フォルダを参照できること
        trashed_folder = self.factory3.data.find_by_uuid(trashed_folder.uuid)

        # 閲覧者は、形代フォルダを更新できないこと
        with self.assertRaises(NotAuthorizedException):
            trashed_folder.update_data('お隣の田中さんまた出世されたんですってよ')

        # 閲覧者は、形代フォルダをほかす前の場所に戻せないこと
        with self.assertRaises(NotAuthorizedException):
            trashed_folder.put_back()

        # プロジェクトをゴミ箱にほかす
        project.throw_away()

        # ゴミ箱を空にする
        trashcan = self.factory2.data.find_trashcan()
        trashcan.trash_all()

        # ゴミ箱は空になっていること
        children = trashcan.find_children()
        self.assertEqual(len(children), 0)

    def test_putback_trash_by_writer(self):
        """
        プロジェクトから捨てたゴミを、
        編集者が更新したり元の位置に戻せること
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('こころぴょんぴょん待ち')
        project.save()
        project = project.reload()

        # メンバを設定する
        member1 = ProjectFolder.Member(self.USER2, ProjectFolder.OWNER_MEMBER_TYPE)
        member2 = ProjectFolder.Member(self.USER3, ProjectFolder.WRITER_MEMBER_TYPE)
        project.init_members([member1, member2], last_modified_at=project.modified_at)

        # プロジェクトの下にフォルダを作成する
        folder = project.create_folder('考えるフリして')
        folder.save()
        folder = folder.reload()

        # フォルダの下にフローを作成する
        flow = folder.create_flow('もうちょっとちーかづいちゃえ', FlowData())
        flow.save()
        flow = flow.reload() 

        # フォルダをほかす
        folder.throw_away()

        # 編集者はゴミを参照できること
        folder = self.factory3.data.find_by_uuid(folder.uuid)
        flow = self.factory3.data.find_by_uuid(flow.uuid)

        # 編集者はゴミを更新できること
        folder.update_data('簡単にはお〜しえないっ')
        flow.update_data('こんなに素敵なことを〜', FlowData())

        # 編集者はゴミを元の場所に戻せること
        folder.put_back()

        # 再びフォルダをほかす
        folder.throw_away()

        # 編集者はゴミ箱を空にできること
        trashcan = self.factory3.data.find_trashcan()
        trashcan.trash_all()

        # ゴミ箱は空になっていること
        children = trashcan.find_children()
        self.assertEqual(len(children), 0)

        # プロジェクトを削除する
        project.delete()

    def test_cannot_read_cache_by_other_user(self):
        """
        プロジェクトメンバ以外のユーザがキャッシュを参照できないこと
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('🌏プロジェクト🗻')
        project.save()
        project = project.reload()

        # プロジェクトの下にフローを作成する
        flow_data = FlowData(copy.deepcopy(self.flow_json))
        flow = project.create_flow('フロー🚅', flow_data)
        flow.save()
        flow = flow.reload() 

        # フローを実行する
        from kskp.engine import execute, FlowCommand
        link = FlowCommand(flow)
        lasts = execute(runnable=link, args={}, inputs={})
        # フローの実行結果を取得する
        out_frame = AuthTest.get_frame_from_lasts(lasts)

        # プロジェクト管理者は、フローの実行結果を参照できること
        out_frame = self.factory2.data.find_by_uuid(out_frame.uuid)
        # プロジェクト管理者は、フローの実行結果を更新できること
        out_frame.update_label('実行結果☢')
        self.assertEqual(out_frame.label, '実行結果☢')
        
        # プロジェクトメンバ以外のユーザは、フローの実行結果を参照できないこと
        with self.assertRaises(NotAuthorizedException):
            self.factory3.data.find_by_uuid(out_frame.uuid)

        # プロジェクト管理者は、フローのキャッシュを参照できること
        cache_frame_uuid = flow.flow_data.get_cache_frame_uuids()[0]
        cache_frame = self.factory2.data.find_by_uuid(cache_frame_uuid)
        # プロジェクト管理者は、フローのキャッシュを更新できること
        cache_frame.update_label('キャッシュ㊗')
        self.assertEqual(cache_frame.label, 'キャッシュ㊗')

        # プロジェクトメンバ以外のユーザは、フローのキャッシュを参照できないこと
        with self.assertRaises(NotAuthorizedException):
            self.factory3.data.find_by_uuid(cache_frame.uuid)

        # フローとキャッシュと実行結果を削除する
        flow.delete()
        cache_frame.delete()
        out_frame.delete()

    def test_cannot_write_cache_by_reader(self):
        """
        閲覧者がキャッシュを更新できないこと
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('京都⛩️')
        project.save()
        project = project.reload()

        # プロジェクトの下にフローを作成する
        flow_data = FlowData(copy.deepcopy(self.flow_json))
        flow = project.create_flow('大阪🏯', flow_data)
        flow.save()
        flow = flow.reload() 

        # フローを実行する
        from kskp.engine import execute, FlowCommand
        link = FlowCommand(flow)
        lasts = execute(runnable=link, args={}, inputs={})
        # フローの実行結果を取得する
        out_frame = AuthTest.get_frame_from_lasts(lasts)

        # プロジェクト管理者は、フローの実行結果を参照できること
        out_frame = self.factory2.data.find_by_uuid(out_frame.uuid)
        # プロジェクト管理者は、フローの実行結果を更新できること
        out_frame.update_label('神戸⚓️')
        self.assertEqual(out_frame.label, '神戸⚓️')
        
        # USER3を閲覧者に加える
        project.join_member(ProjectFolder.Member(self.USER3, ProjectFolder.READER_MEMBER_TYPE))

        # 閲覧者は、フローの実行結果を参照できること
        out_frame = self.factory3.data.find_by_uuid(out_frame.uuid)
        self.assertEqual(out_frame.label, '神戸⚓️')

        # プロジェクト管理者は、フローのキャッシュを参照できること
        cache_frame_uuid = flow.flow_data.get_cache_frame_uuids()[0]
        cache_frame = self.factory2.data.find_by_uuid(cache_frame_uuid)
        # プロジェクト管理者は、フローのキャッシュを更新できること
        cache_frame.update_label('琵琶湖🛥')
        self.assertEqual(cache_frame.label, '琵琶湖🛥')

        # 閲覧者は、フローのキャッシュを参照できること
        cache_frame = self.factory3.data.find_by_uuid(cache_frame.uuid)
        self.assertEqual(cache_frame.label, '琵琶湖🛥')

        # フローを削除する
        flow.delete()

        # 閲覧者は、キャッシュと実行結果を削除できないこと
        with self.assertRaises(NotAuthorizedException):
            cache_frame.delete()
        with self.assertRaises(NotAuthorizedException):
            out_frame.delete()

        # キャッシュと実行結果を削除する
        out_frame = self.factory2.data.find_by_uuid(out_frame.uuid)
        cache_frame = self.factory2.data.find_by_uuid(cache_frame_uuid)
        cache_frame.delete()
        out_frame.delete()

    def test_cannot_exec_cache_flow_by_reader(self):
        """
        残念ながら、閲覧者はフロー実行によるキャッシュ作成ができない
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()
        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('iPhone')
        project.save()
        project = project.reload()

        # プロジェクトの下にフローを作成する
        flow_data = FlowData(copy.deepcopy(self.flow_json))
        flow = project.create_flow('iPad', flow_data)
        flow.save()
        flow = flow.reload()

        # USER3を閲覧者に加える
        project.join_member(ProjectFolder.Member(self.USER3, ProjectFolder.READER_MEMBER_TYPE))

        # USER3は、フローにキャッシュのuuidを書き込めないので、フローを実行できない
        from kskp.engine import execute, FlowCommand
        flow = self.factory3.data.find_by_uuid(flow.uuid)
        link = FlowCommand(flow)
        with self.assertRaises(CommandException) as e:
            lasts = execute(runnable=link, args={}, inputs={})
            AuthTest.get_frame_from_lasts(lasts)
        # CommandExceptionはNotAuthorizedExceptionを再送出していること
        self.assertIsInstance(e.exception.innerException, NotAuthorizedException)
            
        # フローを削除する
        flow = self.factory2.data.find_by_uuid(flow.uuid)
        flow.delete()

        # プロジェクトを削除する
        project.delete()

    def test_duplicate_flow_with_cache(self):
        """
        キャッシュを持つフローを複製しても、
        キャッシュの権限はフローのプロジェクトに紐づいていること
        """
        # ROOTを取得する
        root = self.factory2.data.load_root()

        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('枕もシーツも')
        project.save()
        project = project.reload()

        # プロジェクト管理者は、プロジェクトメンバを設定する
        member1 = ProjectFolder.Member(self.USER2, ProjectFolder.OWNER_MEMBER_TYPE)
        member2 = ProjectFolder.Member(self.USER3, ProjectFolder.WRITER_MEMBER_TYPE)
        project.init_members([member1, member2], last_modified_at=project.modified_at)

        # 編集者は、フローを作成する
        flow_data = FlowData(copy.deepcopy(self.flow_json))
        flow = project.create_flow('堅くて眠れない〜♪', flow_data)
        flow.save()
        flow = flow.reload()

        # 編集者は、フローをプレビュー実行して、キャッシュファイルを作成する
        from kskp.engine import execute, FlowCommand
        vis_args = { "d1" : 
                        {"args" :
                            {"visualizer" : "csvtohtmltable",
                             "offset" : 0,
                             "limit"  : 100
                            }
                        }
                    }
        flow = self.factory3.data.find_by_uuid(flow.uuid)
        link = FlowCommand(flow, vis_args)
        lasts = execute(runnable=link, args={}, inputs={})

        # キャッシュのUUIDを取得する
        cache_frame_uuid = flow.flow_data.get_cache_frame_uuids()[0]
        cache_frame = self.factory3.data.find_by_uuid(cache_frame_uuid)

        # 編集者は、フローを複製する
        flow = self.factory3.data.find_by_uuid(flow.uuid)
        duplicated_flow = flow.duplicate('君も寝具にしてやろうか?😈')

        # 複製したキャッシュのUUIDを取得する
        duplicated_cache_frame_uuid = duplicated_flow.flow_data.get_cache_frame_uuids()[0]
        duplicated_cache_frame = self.factory3.data.find_by_uuid(duplicated_cache_frame_uuid)

        # キャッシュが複製されていることを検証する
        # (フローJSONに記録されたキャッシュのUUIDが異なることを検証する)
        self.assertNotEqual(duplicated_cache_frame_uuid, cache_frame_uuid)

        # キャッシュの権限設定を検証する
        auths = self.factory.auth.find_all_by_datum_id(duplicated_cache_frame.id)
        self.assertEqual(len(auths), 6)
        # 取得した権限を検証する
        usr_admin_role = self.factory.role.load_usr_admin_role()
        readers_role = project._find_readers_role()
        writers_role = project._find_writers_role()
        # ユーザ管理者ロールの参照権限
        self.assertEqual(auths[0].role_id, usr_admin_role.id)
        self.assertEqual(auths[0].datum_id, duplicated_cache_frame.id)
        self.assertEqual(auths[0].operation, Auth.READ_OP)
        self.assertEqual(auths[0].permission, True)
        self.assertEqual(auths[0].creator, self.USER3)
        self.assertEqual(auths[0].modifier, self.USER3)
        self.assertIsNotNone(auths[0].created_at)
        self.assertIsNotNone(auths[0].modified_at)
        # ユーザ管理者ロールの更新権限
        self.assertEqual(auths[1].role_id, usr_admin_role.id)
        self.assertEqual(auths[1].datum_id, duplicated_cache_frame.id)
        self.assertEqual(auths[1].operation, Auth.WRITE_OP)
        self.assertEqual(auths[1].permission, True)
        self.assertEqual(auths[1].creator, self.USER3)
        self.assertEqual(auths[1].modifier, self.USER3)
        self.assertIsNotNone(auths[1].created_at)
        self.assertIsNotNone(auths[1].modified_at)
        # ユーザ管理者ロールの所有権限
        self.assertEqual(auths[2].role_id, usr_admin_role.id)
        self.assertEqual(auths[2].datum_id, duplicated_cache_frame.id)
        self.assertEqual(auths[2].operation, Auth.OWN_OP)
        self.assertEqual(auths[2].permission, True)
        self.assertEqual(auths[2].creator, self.USER3)
        self.assertEqual(auths[2].modifier, self.USER3)
        self.assertIsNotNone(auths[2].created_at)
        self.assertIsNotNone(auths[2].modified_at)
        # プロジェクトのReadersロールの参照権限
        self.assertEqual(auths[3].role_id, readers_role.id)
        self.assertEqual(auths[3].datum_id, duplicated_cache_frame.id)
        self.assertEqual(auths[3].operation, Auth.READ_OP)
        self.assertEqual(auths[3].permission, True)
        self.assertEqual(auths[3].creator, self.USER3)
        self.assertEqual(auths[3].modifier, self.USER3)
        self.assertIsNotNone(auths[3].created_at)
        self.assertIsNotNone(auths[3].modified_at)
        # プロジェクトのWritersロールの更新権限
        self.assertEqual(auths[4].role_id, writers_role.id)
        self.assertEqual(auths[4].datum_id, duplicated_cache_frame.id)
        self.assertEqual(auths[4].operation, Auth.WRITE_OP)
        self.assertEqual(auths[4].permission, True)
        self.assertEqual(auths[4].creator, self.USER3)
        self.assertEqual(auths[4].modifier, self.USER3)
        self.assertIsNotNone(auths[4].created_at)
        self.assertIsNotNone(auths[4].modified_at)
        # プロジェクトのWritersロールの所有権限
        self.assertEqual(auths[5].role_id, writers_role.id)
        self.assertEqual(auths[5].datum_id, duplicated_cache_frame.id)
        self.assertEqual(auths[5].operation, Auth.OWN_OP)
        self.assertEqual(auths[5].permission, True)
        self.assertEqual(auths[5].creator, self.USER3)
        self.assertEqual(auths[5].modifier, self.USER3)
        self.assertIsNotNone(auths[5].created_at)
        self.assertIsNotNone(auths[5].modified_at)

        # 編集者は、複製したフローをプレビュー実行できること
        link = FlowCommand(duplicated_flow, vis_args)
        lasts = execute(runnable=link, args={}, inputs={})

        # プロジェクトに属さないユーザは、複製したフローを取得できないこと
        with self.assertRaises(NotAuthorizedException):
            self.factory0.data.find_by_uuid(duplicated_flow.uuid)

        # フローを削除する
        flow.delete()
        duplicated_flow.delete()

        # プロジェクトを削除する
        project.delete()
     
    def test_get_masked_flow(self):
        """
        参照権限のないサブフローノードやデータソースノードは、
        ラベルとuuidがマスキングされること
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()

        # USER2は、ルートフォルダの下にプロジェクトを作成する
        project1 = root.create_project_folder('プロジェクトX')
        project1.save()
        project1 = project1.reload()

        # USER2は、プロジェクトの下に共有フローを作成する
        flow_data = FlowData(copy.deepcopy(self.flow2_json))
        flow1 = project1.create_flow('共有フロー', flow_data)
        flow1.save()
        flow1 = flow1.reload()

        # USER2は、ルートフォルダの下にプロジェクトを作成する
        project2 = root.create_project_folder('プロジェクトY')
        project2.save()
        project2 = project2.reload()

        # USER2は、プロジェクトの下にメインフローを作成する
        flow_data = FlowData(self.get_flow3_json(flow1.uuid))
        flow2 = project2.create_flow('メインフロー', flow_data)
        flow2.save()
        flow2 = flow2.reload()

        # USER2は、USER3をプロジェクト2の編集者に追加する
        member1 = ProjectFolder.Member(self.USER3, ProjectFolder.OWNER_MEMBER_TYPE)
        project2.join_member(member1)

        # USER3は、メインフローを取得できるが、共有フローの参照権限がないので
        # その共有フローノードのラベルとuuidはマスキングされていること
        flow2 = self.factory3.data.find_by_uuid(flow2.uuid)
        masked_flow_data = flow2.flow_data.to_json()
        nodes = masked_flow_data['nodes']

        # フローJsonを検証する
        self.assertEqual(nodes[2]['id'], 'f1')
        self.assertEqual(nodes[2]['type'], 'flow')
        # uuidがマスキングされていること
        self.assertIsNone(nodes[2]['uuid'])
        # ラベルがマスキングされていること
        self.assertEqual(nodes[2]['label'], '******')
        self.assertEqual(nodes[2]['args'], {})
        self.assertEqual(nodes[2]['srcs'], {'d':'d'})
        self.assertEqual(nodes[2]['dsts'], {'d1':'d1'})
        self.assertEqual(nodes[2]['srcsOrder'], ['d'])
        # マスキングのフラグが設定されていること
        self.assertEqual(nodes[2]['masked'], True)

        # USER3は、マスキングされたフローJsonでも更新できること
        flow2.update_data('更新したフロー', FlowData(masked_flow_data))

        # USER2は、更新後のフローであってもマスキングされていないフローJsonを取得できること
        flow2 = self.factory2.data.find_by_uuid(flow2.uuid)
        masked_flow_data = flow2.flow_data.to_json()
        nodes = masked_flow_data['nodes']

        # 更新後のフローJsonを検証する
        self.assertEqual(flow2.label, '更新したフロー')
        self.assertEqual(nodes[2]['id'], 'f1')
        self.assertEqual(nodes[2]['type'], 'flow')
        # USER2は、参照権限があるのでマスキングされていないこと
        self.assertEqual(nodes[2]['uuid'], flow1.uuid)
        # USER2は、参照権限があるのでマスキングされていないこと
        self.assertEqual(nodes[2]['label'], 'f1')
        self.assertEqual(nodes[2]['args'], {})
        self.assertEqual(nodes[2]['srcs'], {'d':'d'})
        self.assertEqual(nodes[2]['dsts'], {'d1':'d1'})
        self.assertEqual(nodes[2]['srcsOrder'], ['d'])
        # マスキングのフラグが存在しないこと
        self.assertNotIn('masked', nodes[2])

        from kskp.engine import execute, FlowCommand
        vis_args = {
          "d1": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 108
            }
          }
        }

        # USER3は、メインフローを実行できないこと
        flow2 = self.factory3.data.find_by_uuid(flow2.uuid)
        link = FlowCommand(flow2, vis_args)
        with self.assertRaises(Exception):
            execute(runnable=link, args={}, inputs={})

        # USER2は、メインフローを実行できること
        flow2 = self.factory2.data.find_by_uuid(flow2.uuid)
        link = FlowCommand(flow2, vis_args)
        last = execute(runnable=link, args={}, inputs={})

        # フローを削除する
        flow2.delete()
        flow1.delete()

        # プロジェクトを削除する
        project1.delete()
        project2.delete()

    def test_move_from_root_to_project(self):
        """
        ルートフォルダからプロジェクトへファイルを移動した場合、
        ファイルの権限は移動先プロジェクトの権限に従うこと
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()
        # ルートフォルダの下にプロジェクトAを作成する
        project_a = root.create_project_folder('何奴！')
        project_a.save()
        project_a = project_a.reload()

        # ルートフォルダの下にフォルダを作成する
        root = self.factory.data.load_root()
        folder = root.create_folder('欲に目が眩んで主君の顔も忘れたか')
        folder.save()
        folder = folder.reload()

        # フォルダの下にフレームを作成する
        frame = folder.create_frame('何ぃ？！', io.BytesIO(b'ABARENBOU'))
        frame.save()
        frame = frame.reload()

        # フォルダをプロジェクトAに移動できること
        folder.move(project_a.uuid)
        self.assertEqual(folder.parent_id, project_a.id)

        # プロジェクトAのプロジェクト管理者はフォルダを参照できること
        folder = self.factory2.data.find_by_uuid(folder.uuid)

        # フォルダ内のフレームは移動後も権限は変わらない
        # そもそもルートフォルダでフォルダやファイルは作る想定ではないので、この仕様でよしとする
        with self.assertRaises(NotAuthorizedException):
            self.factory2.data.find_by_uuid(frame.uuid)

        # プロジェクトを削除する
        frame.delete()
        folder.delete()
        project_a.delete()

    def test_move_inter_projects(self):
        """
        プロジェクト間でファイルを移動した場合、
        ファイルの権限は移動先プロジェクトの権限に従うこと
        """
        # ルートフォルダを取得する
        root = self.factory0.data.load_root()
        # ルートフォルダの下にプロジェクトAを作成する
        project_a = root.create_project_folder('インド人はゼロを発明した')
        project_a.save()
        project_a = project_a.reload()

        # ルートフォルダを取得する
        root = self.factory2.data.load_root()
        # ルートフォルダの下にプロジェクトBを作成する
        project_b = root.create_project_folder('だが日本人はストロングゼロを発明した')
        project_b.save()
        project_b = project_b.reload()

        # USER3をプロジェクトAとBの編集者にする
        project_a.join_member(ProjectFolder.Member(self.USER3, ProjectFolder.WRITER_MEMBER_TYPE))
        project_b.join_member(ProjectFolder.Member(self.USER3, ProjectFolder.WRITER_MEMBER_TYPE))

        # プロジェクトAの下にフレームを作成する
        frame = project_a.create_frame('飲む福祉ストロングゼロ!', io.BytesIO(b'STRONGZERO'))
        frame.save()

        # USER3は、フレームをプロジェクトAからプロジェクトBへ移動できること
        frame = self.factory3.data.find_by_uuid(frame.uuid)
        frame.move(project_b.uuid)
        self.assertEqual(frame.parent_id, project_b.id)

        # プロジェクトAのメンバはフレームの参照できないこと
        with self.assertRaises(NotAuthorizedException):
            self.factory0.data.find_by_uuid(frame.uuid)

        # プロジェクトBのメンバはフレームの参照・更新ができること
        frame = self.factory2.data.find_by_uuid(frame.uuid)
        frame.update_label('美味しい魔法の水')
        self.assertEqual(frame.label, '美味しい魔法の水')

        # プロジェクトとフレームを削除する
        project_a.delete()
        frame.delete()
        project_b.delete()

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
