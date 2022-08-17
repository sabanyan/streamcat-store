import io
import pprint
from .test_case_base import TestCaseBase
from streamcat.store import FlowData, DatabaseConn

class DatumTest(TestCaseBase):
    """
    Datumクラスの検証をする
    """

    def test_folder_path(self):
        """
        folder_pathプロパティはライブラリにおける階層パスを返すこと
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()

        # ルートフォルダの下にフォルダ1を作成する
        folder1 = root.create_folder('テストフォルダ1')

        # DBに保存する前のフォルダであっても、folder_pathの値を取得できること
        self.assertEqual(folder1.folder_path, '/' + root.label)

        # フォルダ1を保存する
        folder1.save()

        # 保存直後(reload前)であっても、folder_pathの値を取得できること
        self.assertEqual(folder1.folder_path, '/' + root.label)

        # フォルダ1をリロードする
        folder1 = self.factory.data.find_by_uuid(folder1.uuid, folder_path=True)

        # folder_pathの値を取得できること
        self.assertEqual(folder1.folder_path, '/' + root.label)

        # フォルダ1の下にフォルダ2を作成する
        folder2 = folder1.create_folder('テストフォルダ1')
        self.assertEqual(folder2.folder_path, '/' + root.label + '/' + folder1.label)

        # フォルダ2を保存する
        folder2.save()
        self.assertEqual(folder2.folder_path, '/' + root.label + '/' + folder1.label)

        # フォルダ2をリロードする
        folder2 = folder2.reload()
        self.assertEqual(folder2.folder_path, '/' + root.label + '/' + folder1.label)

        # フォルダ2をほかす
        folder2.throw_away()

        # フォルダ2を削除する
        folder2.delete()        

        # フォルダ1をほかす
        folder1.throw_away()

        # フォルダ1を削除する
        folder1.delete()

    def test_move_writeless_datum_in_folder(self):
        """
        更新権限のないDatumを含むフォルダは移動できる
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()

        # ルートフォルダの下にプロジェクト1を作成する
        project1 = root.create_project_folder('P1')
        project1.save()
        project1 = project1.reload()

        # ルートフォルダの下にプロジェクト2を作成する
        project2 = root.create_project_folder('P2')
        project2.save()
        project2 = project2.reload()

        # プロジェクト1の下にフォルダを作成する
        folder = project1.create_folder('F')
        folder.save()
        folder = folder.reload()

        # フォルダの下にデータベースを作成する
        conn_json = {
            'dbms'     : "postgresql",
            'hostname' : "db", 
            'port'     : 5432, 
            'database' : "streamcat", 
            'userId'   : "streamcat", 
            'password' : 'ZQZtVgL6G32Vy6p6WJtG3C3K84yuJ4zz'
        }
        database_conn = DatabaseConn(conn_json)
        database = folder.create_database('DB', database_conn)
        database.save()
        database = database.reload()

        # データベースの権限を全て削除する
        self.factory.auth.delete_all_by_datum_id(database.id)

        # フォルダをプロジェクト2の下に移動する
        moved_folder = folder.move(project2.uuid, modifier=self.USER3)

        # 移動後のフォルダを検証する
        # parent_id, path, modifierが変更されることを検証する
        self.assertEqual(moved_folder.id, folder.id)
        self.assertEqual(moved_folder.parent_id, project2.id)
        self.assertEqual(moved_folder.uuid, folder.uuid)
        self.assertEqual(moved_folder.type, 'folder')
        self.assertEqual(moved_folder.label, 'F')
        self.assertEqual(moved_folder.path, project2.path / folder.label)
        self.assertEqual(moved_folder.creator, self.USER2)
        self.assertEqual(moved_folder.modifier, self.USER3)
        self.assertEqual(moved_folder.created_at, folder.created_at)
        self.assertIsNotNone(moved_folder.modified_at)

        # 移動後のデータベースを検証する
        self.assertIsNotNone(database.id)
        self.assertEqual(database.parent_id, folder.id)
        self.assertIsNotNone(database.uuid)
        self.assertEqual(database.type, 'database')
        self.assertEqual(database.label, 'DB')
        self.assertEqual(database.creator, database.modifier)
        self.assertEqual(database.created_at, database.modified_at)

        # プロジェクトとキャッシュを削除する
        project1.throw_away()
        project2.throw_away()

        # ゴミ箱を空にする
        self.factory.data.find_trashcan().trash_all()

    def test_move_flow_in_folder(self):
        """
        フローを含むフォルダを移動する
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()

        # ルートフォルダの下にプロジェクト1を作成する
        project1 = root.create_project_folder('MIHOミュージアム')
        project1.save()
        project1 = project1.reload()

        # ルートフォルダの下にプロジェクト2を作成する
        project2 = root.create_project_folder('沖島')
        project2.save()
        project2 = project2.reload()

        # プロジェクト1の下にフォルダを作成する
        folder = project1.create_folder('竹生島')
        folder.save()
        folder = folder.reload()

        # フォルダの下にフローを作成する
        flow = folder.create_flow('ピエり守山', FlowData({}))
        flow.save()
        flow = flow.reload()

        # フローに編集ロックをかける
        flow.edit_lock=True

        # フォルダの下に移動付加なフローが在るので、フォルダは移動できないこと
        with self.assertRaises(Exception):
            folder.move(project2.uuid, self.USER3)

        # フローの編集ロックを解除する
        flow.edit_lock=False

        # フォルダをプロジェクト2の下に移動する
        moved_folder = folder.move(project2.uuid, modifier=self.USER3)

        # 移動後のフォルダを検証する
        # parent_id, path, modifierが変更されることを検証する
        self.assertEqual(moved_folder.id, folder.id)
        self.assertEqual(moved_folder.parent_id, project2.id)
        self.assertEqual(moved_folder.uuid, folder.uuid)
        self.assertEqual(moved_folder.type, 'folder')
        self.assertEqual(moved_folder.label, '竹生島')
        self.assertEqual(moved_folder.path, project2.path / folder.label)
        self.assertEqual(moved_folder.creator, self.USER2)
        self.assertEqual(moved_folder.modifier, self.USER3)
        self.assertEqual(moved_folder.created_at, folder.created_at)
        self.assertIsNotNone(moved_folder.modified_at)

        # 移動後のフローを検証する
        self.assertIsNotNone(moved_folder.id)
        self.assertEqual(flow.parent_id, moved_folder.id)
        self.assertIsNotNone(flow.uuid)
        self.assertEqual(flow.type, 'flow')
        self.assertEqual(flow.label, 'ピエり守山')
        self.assertEqual(flow.creator, flow.modifier)
        self.assertEqual(flow.created_at, flow.modified_at)

        # プロジェクトとキャッシュを削除する
        project1.throw_away()
        project2.throw_away()

        # ゴミ箱を空にする
        self.factory2.data.find_trashcan().trash_all()

    def test_move_frame_in_folder(self):
        """
        フレームを含むフォルダを移動する
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()

        # ルートフォルダの下にプロジェクト1を作成する
        project1 = root.create_project_folder('ベニテングタケ')
        project1.save()
        project1 = project1.reload()

        # ルートフォルダの下にプロジェクト2を作成する
        project2 = root.create_project_folder('ツキヨタケ')
        project2.save()
        project2 = project2.reload()

        # プロジェクト1の下にフォルダを作成する
        folder = project1.create_folder('ドクツルタケ')
        folder.save()
        folder = folder.reload()

        # フォルダの下にフレームを作成する
        frame = folder.create_frame('スギヒラタケ', io.BytesIO(b''))
        frame.save()
        frame = frame.reload()

        # フォルダをプロジェクト2の下に移動する
        moved_folder = folder.move(project2.uuid, modifier=self.USER3)

        # 移動後のフォルダを検証する
        # parent_id, path, modifierが変更されることを検証する
        self.assertEqual(moved_folder.id, folder.id)
        self.assertEqual(moved_folder.parent_id, project2.id)
        self.assertEqual(moved_folder.uuid, folder.uuid)
        self.assertEqual(moved_folder.type, 'folder')
        self.assertEqual(moved_folder.label, 'ドクツルタケ')
        self.assertEqual(moved_folder.path, project2.path / folder.label)
        self.assertEqual(moved_folder.creator, self.USER2)
        self.assertEqual(moved_folder.modifier, self.USER3)
        self.assertEqual(moved_folder.created_at, folder.created_at)
        self.assertIsNotNone(moved_folder.modified_at)

        # 移動後のフレームを検証する
        self.assertIsNotNone(moved_folder.id)
        self.assertEqual(frame.parent_id, moved_folder.id)
        self.assertIsNotNone(frame.uuid)
        self.assertEqual(frame.type, 'frame')
        self.assertEqual(frame.label, 'スギヒラタケ')
        self.assertEqual(frame.path, moved_folder.path / frame.label)
        # 移動処理にてpathが更新されるため、modifierとmodified_atは更新される
        self.assertEqual(frame.creator, self.USER2)
        self.assertEqual(frame.modifier, self.USER3)
        self.assertNotEqual(frame.created_at, frame.modified_at)

        # プロジェクトとキャッシュを削除する
        project1.throw_away()
        project2.throw_away()

        # ゴミ箱を空にする
        self.factory2.data.find_trashcan().trash_all()

    def test_move_schedule_in_folder(self):
        """
        スケジュールを含むフォルダを移動する
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()

        # ルートフォルダの下にプロジェクト1を作成する
        project1 = root.create_project_folder('姫路城')
        project1.save()
        project1 = project1.reload()

        # ルートフォルダの下にプロジェクト2を作成する
        project2 = root.create_project_folder('彦根城')
        project2.save()
        project2 = project2.reload()

        # プロジェクト1の下にフォルダを作成する
        folder = project1.create_folder('犬山城')
        folder.save()
        folder = folder.reload()

        # フォルダの下にフローを作成する
        flow = folder.create_flow('松山', FlowData({}))
        flow.save()
        flow = flow.reload()

        # フォルダの下にスケジュールを作成する
        trigger1 = {
            'type' : 'date',
            'date' : '2022-05-07 12:00:00'
        }
        schedule = folder.create_schedule('備中松山城', flow.uuid, trigger=trigger1)
        schedule.save()
        schedule = schedule.reload()

        # フォルダをプロジェクト2の下に移動する
        moved_folder = folder.move(project2.uuid, modifier=self.USER3)

        # 移動後のフォルダを検証する
        # parent_id, path, modifierが変更されることを検証する
        self.assertEqual(moved_folder.id, folder.id)
        self.assertEqual(moved_folder.parent_id, project2.id)
        self.assertEqual(moved_folder.uuid, folder.uuid)
        self.assertEqual(moved_folder.type, 'folder')
        self.assertEqual(moved_folder.label, '犬山城')
        self.assertEqual(moved_folder.path, project2.path / folder.label)
        self.assertEqual(moved_folder.creator, self.USER2)
        self.assertEqual(moved_folder.modifier, self.USER3)
        self.assertEqual(moved_folder.created_at, folder.created_at)
        self.assertIsNotNone(moved_folder.modified_at)

        # 移動後のスケジュールを検証する
        self.assertIsNotNone(moved_folder.id)
        self.assertEqual(schedule.parent_id, moved_folder.id)
        self.assertIsNotNone(schedule.uuid)
        self.assertEqual(schedule.type, 'schedule')
        self.assertEqual(schedule.label, '備中松山城')
        self.assertEqual(schedule.creator, schedule.modifier)
        self.assertEqual(schedule.created_at, schedule.modified_at)

        # プロジェクトとキャッシュを削除する
        project1.throw_away()
        project2.throw_away()

        # ゴミ箱を空にする
        self.factory2.data.find_trashcan().trash_all()
