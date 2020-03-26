import os
import unittest
import json
import uuid
import pprint
from pathlib import Path
from datetime import datetime

from kskp.store import ss as session
from kskp.core import Datum
from kskp.store import Library, Flow, STORE_DIR, Library
from kskp.store.auth import User

class LibraryTest(unittest.TestCase):
    # テスト用ユーザID
    # USER_ID1 = 88
    # USER_ID2 = 99

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @classmethod
    def setUpClass(cls):
        from kskp.store.auth import Auth, Group, User
        # 管理者ユーザをSessionに設定する
        session.user = User.find_by_id(1)
        # テストユーザを作成する
        test_user = User('test@kskp.io', 'testpass', 'Test')
        test_user.save()
        # EveryOneグループにテストユーザを加える
        everyone_group = Group.load_everyone_group()
        everyone_group.join_user(test_user)
        # クラス変数に設定する
        LibraryTest.USER_ID1 = session.user
        LibraryTest.USER_ID2 = test_user

    @classmethod
    def tearDownClass(cls):
        # ライブラリフォルダを削除する
        from kskp.core import Datum
        library_path = STORE_DIR / Library.load_root().path
        import shutil
        shutil.rmtree(library_path.as_posix())
        # Sessionを閉じる
        session.close()
        # スキーマを破棄する
        from kskp.store import engine
        from sqlalchemy import DDL
        engine.execute(DDL('DROP SCHEMA IF EXISTS %s CASCADE' % os.environ['KSKP_POSTGRESQL_SCHEMA_NAME']))

    def save(self, file_path):
        file_path = Datum._to_abs_path(file_path.as_posix())
        with open(file_path, "w") as f:
            f.write("I am a frame data for test cases.")

    def delete(self, file_path):
        if os.path.exists(file_path):
            os.unlink(file_path)

    def test_save_and_load(self):
        # ルートデータストアを取得する
        root = Library.load_root()
        # フレームデータを格納するファイルを作成する
        frame_file_path = root.path / str(uuid.uuid4())
        self.save(frame_file_path)
        # 指定したファイルをフレームとしてライブラリに登録する
        new_frame = Library.save_frame(root.uuid, 'テストフレーム', frame_file_path, self.USER_ID1)
        # 登録したフレームを取得する
        saved_frame = Library.load_frame(new_frame.uuid)
        # 作成したフレームを削除する
        Library.delete_frame(saved_frame.uuid)

    def test_get_root(self):
        """
        ルートフォルダを取得する
        """
        # ルートデータストアを取得する
        root = Library.load_root()
        # 取得したルートデータストアの値を検証する
        self.assertIsNotNone(root.id)
        self.assertIsNone(root.parent_id)
        self.assertIsNotNone(root.uuid)
        self.assertIsNotNone(root.path)
        self.assertEqual(root.type, 'folder')
        self.assertIsNone(root.data)
        # self.assertIsNotNone(root.creator)
        # self.assertIsNotNone(root.modifier)
        self.assertIsNotNone(root.created_at)
        self.assertIsNotNone(root.modified_at)


    def test_get_folder(self):
        """
        フォルダを取得する
        """
        # ルートデータストアを取得する
        root = Library.load_root()
        # ルートデータストアをフォルダとして取得する
        folder = Library.load_folder(root.uuid)
        # 取得したフォルダの値を検証する
        self.assertIsNotNone(folder.id)
        self.assertIsNone(folder.parent_id)
        self.assertIsNotNone(folder.uuid)
        self.assertIsNotNone(folder.path)
        self.assertEqual(folder.type, 'folder')
        self.assertIsNone(root.data)
        # self.assertIsNotNone(folder.creator)
        # self.assertIsNotNone(folder.modifier)
        self.assertIsNotNone(folder.created_at)
        self.assertIsNotNone(folder.modified_at)

    def test_update_folder(self):
        """
        フォルダのラベルを変更する
        """
        # ルートデータストアを取得する
        root = Library.load_root()
        # ルートデータストアの直下にフォルダを作成する
        folder = Library.save_folder(root.uuid, 'フォルダ0', self.USER_ID1)
        # 作成したフォルダのラベルを変更する
        updated_folder = Library.update_folder_data(folder.uuid, '新しいフォルダ', self.USER_ID2)
        # ラベルとディレクトリパスのみが変更されることを検証する
        self.assertEqual(updated_folder.id, folder.id)
        self.assertEqual(updated_folder.parent_id, folder.parent_id)
        self.assertEqual(updated_folder.uuid, folder.uuid)
        self.assertEqual(updated_folder.path, root.path / '新しいフォルダ')
        self.assertEqual(updated_folder.type, folder.type)
        self.assertEqual(updated_folder.label, '新しいフォルダ')
        self.assertEqual(folder.creator, self.USER_ID1)
        self.assertEqual(folder.modifier, self.USER_ID2)
        self.assertEqual(updated_folder.created_at, folder.created_at)
        self.assertIsNotNone(updated_folder.modified_at)
        # 作成したフォルダを削除する
        Library.delete_folder(folder.uuid)

    def test_move_folder(self):
        """
        フォルダを移動する
        """
        # ルートデータストアを取得する
        root = Library.load_root()
        # ルートデータストアの直下にフォルダを作成する
        folder_src = Library.save_folder(root.uuid, 'フォルダSRC_AA', self.USER_ID1)
        # 上記フォルダの直下にフレームを作成する
        self.save(folder_src.path / 'aaaa1.csv')
        frame_src = Library.save_frame(root.uuid, 'フレームSRC', folder_src.path / 'aaaa1.csv', self.USER_ID1)
        # ルートデータストアの直下にフォルダを作成する
        folder_dst = Library.save_folder(root.uuid, 'フォルダDST', self.USER_ID1)
        # フォルダSRC_AAをフォルダDSTへ移動する
        updated_folder = folder_src.move(folder_dst.uuid, self.USER_ID2)
        # parent_id, path, modifierが変更されることを検証する
        self.assertEqual(updated_folder.id, folder_src.id)
        self.assertEqual(updated_folder.parent_id, folder_dst.id)
        self.assertEqual(updated_folder.uuid, folder_src.uuid)
        self.assertEqual(updated_folder.path, root.path / 'フォルダDST/フォルダSRC_AA')
        self.assertEqual(updated_folder.type, folder_src.type)
        self.assertEqual(updated_folder.label, 'フォルダSRC_AA')
        self.assertEqual(updated_folder.creator, self.USER_ID1)
        self.assertEqual(updated_folder.modifier, self.USER_ID2)
        self.assertEqual(updated_folder.created_at, folder_src.created_at)
        self.assertIsNotNone(updated_folder.modified_at)
        # 移動したフォルダ配下のファイルのpathが修正されていることを検証する
        self.assertEqual(frame_src.path, root.path / 'フォルダDST/フォルダSRC_AA/aaaa1.csv')
        self.assertEqual(updated_folder.creator, self.USER_ID1)
        self.assertEqual(updated_folder.modifier, self.USER_ID2)
        self.assertEqual(updated_folder.created_at, folder_src.created_at)
        self.assertIsNotNone(updated_folder.modified_at)
        # 作成したフォルダを削除する
        Library.delete_frame(frame_src.uuid)
        Library.delete_folder(updated_folder.uuid)
        Library.delete_folder(folder_dst.uuid)

    def test_save_folder(self):
        """
        フォルダを作成する
        """
        # ルートデータストアを取得する
        root = Library.load_root()
        # ルートデータストアの直下にフォルダを作成する
        folder = Library.save_folder(root.uuid, 'フォルダ', self.USER_ID1)
        # 作成したフォルダの値を検証する
        self.assertIsNotNone(folder.id)
        self.assertEqual(folder.parent_id, root.id)
        self.assertIsNotNone(folder.uuid)
        self.assertEqual(folder.path, root.path / 'フォルダ')
        self.assertEqual(folder.type, 'folder')
        self.assertEqual(folder.label, 'フォルダ')
        self.assertEqual(folder.creator, self.USER_ID1)
        self.assertEqual(folder.modifier, self.USER_ID1)
        self.assertEqual(folder.creator, folder.modifier)
        self.assertIsNotNone(folder.created_at)
        self.assertIsNotNone(folder.modified_at)
        self.assertEqual(folder.created_at, folder.modified_at)
        # 作成したフォルダを削除する
        Library.delete_folder(folder.uuid)

    @unittest.skip('AWS S3のパスワードないのでエラーになる')
    def test_get_awss3(self):
        """
        AWS S3フォルダを取得する
        """
        try:
            # ルートデータストアを取得する
            root = Library.load_root()
            # ルートデータストアの直下にAWS S3フォルダを作成する
            folder = Library.save_awss3(root.uuid, 'S3フォルダ1', 'kskp-test', self.USER_ID1)
            # 作成したAWS S3フォルダを取得する
            folder = Library.load_awss3(folder.uuid)
            # 取得したフォルダの値を検証する
            self.assertIsNotNone(folder.id)
            self.assertEqual(folder.parent_id, root.id)
            self.assertIsNotNone(folder.uuid)
            self.assertEqual(folder.path, root.path / 'S3フォルダ1')
            self.assertEqual(folder.type, 'awss3')
            self.assertEqual(folder.label, 'S3フォルダ1')
            self.assertEqual(folder.creator, self.USER_ID1)
            self.assertEqual(folder.modifier, self.USER_ID1)
            self.assertIsNotNone(folder.created_at)
            self.assertIsNotNone(folder.modified_at)
        finally:
            # 作成したフォルダを削除する
            Library.delete_awss3(folder.uuid)

    @unittest.skip('AWS S3のパスワードないのでエラーになる')
    def test_update_awss3(self):
        """
        AWS S3フォルダのラベルを変更する
        """
        try:
            # ルートデータストアを取得する
            root = Library.load_root()
            # ルートデータストアの直下にAWS S3フォルダを作成する
            folder = Library.save_awss3(root.uuid, 'S3フォルダ2', 'kskp-test', self.USER_ID1)
            # 作成したフォルダのラベルを変更する
            updated_folder = Library.update_awss3_data(folder.uuid,
                                                       '新しいS3フォルダ',
                                                       'kskp-test',
                                                       self.USER_ID2)
            # ラベルとディレクトリパスのみが変更されることを検証する
            self.assertEqual(updated_folder.id, folder.id)
            self.assertEqual(updated_folder.parent_id, folder.parent_id)
            self.assertEqual(updated_folder.uuid, folder.uuid)
            self.assertEqual(updated_folder.path, root.path / '新しいS3フォルダ')
            self.assertEqual(updated_folder.type, folder.type)
            self.assertEqual(updated_folder.label, '新しいS3フォルダ')
            self.assertEqual(updated_folder.creator, self.USER_ID1)
            self.assertEqual(updated_folder.modifier, self.USER_ID2)
            self.assertEqual(updated_folder.created_at, folder.created_at)
            self.assertIsNotNone(updated_folder.modified_at)
        finally:
            # 作成したフォルダを削除する
            Library.delete_awss3(folder.uuid)

    @unittest.skip('AWS S3のパスワードないのでエラーになる')
    def test_save_awss3(self):
        """
        AWS S3フォルダを作成する
        """
        try:
            # ルートデータストアを取得する
            root = Library.load_root()
            # ルートデータストアの直下にAWS S3フォルダを作成する
            folder = Library.save_awss3(root.uuid, 'S3フォルダ3', 'kskp-test', self.USER_ID1)
            # 作成したフォルダの値を検証する
            self.assertIsNotNone(folder.id)
            self.assertEqual(folder.parent_id, root.id)
            self.assertIsNotNone(folder.uuid)
            self.assertEqual(folder.path, root.path / 'S3フォルダ3')
            self.assertEqual(folder.type, 'awss3')
            self.assertEqual(folder.label, 'S3フォルダ3')
            self.assertEqual(folder.creator, self.USER_ID1)
            self.assertEqual(folder.modifier, self.USER_ID1)
            self.assertEqual(folder.creator, folder.modifier)
            self.assertIsNotNone(folder.created_at)
            self.assertIsNotNone(folder.modified_at)
            self.assertEqual(folder.created_at, folder.modified_at)
        finally:
            # 作成したフォルダを削除する
            Library.delete_awss3(folder.uuid)


    def test_get_frame(self):
        """
        フレームを取得する
        """
        # ルートデータストアを取得する
        root = Library.load_root()
        root_path = root.path
        # フレームデータを格納するファイルを作成する
        self.save(root_path / 'aaaa.csv')
        # ルートデータストアの直下にフレームを作成する
        frame = Library.save_frame(root.uuid, 'フレームデータ', root_path / 'aaaa.csv', self.USER_ID1)
        # 作成したフレームを取得する
        frame = Library.load_frame(frame.uuid)
        # 作成したフレームの値を検証する
        self.assertIsNotNone(frame.id)
        self.assertEqual(frame.parent_id, root.id)
        self.assertIsNotNone(frame.uuid)
        self.assertEqual(frame.path, root_path / 'aaaa.csv')
        self.assertEqual(frame.type, 'frame')
        self.assertEqual(frame.label, 'フレームデータ')
        self.assertEqual(frame.creator, self.USER_ID1)
        self.assertEqual(frame.modifier, self.USER_ID1)
        self.assertEqual(frame.creator, frame.modifier)
        self.assertIsNotNone(frame.created_at)
        self.assertIsNotNone(frame.modified_at)
        self.assertEqual(frame.created_at, frame.modified_at)
        # 作成したフレームを削除する
        Library.delete_frame(frame.uuid)

    def test_update_frame(self):
        """
        フレームのラベルを変更する
        """
        # ルートデータストアを取得する
        root = Library.load_root()
        root_path = root.path
        # フレームデータを格納するファイルを作成する
        self.save(root_path / 'aaaa1.csv')
        # ルートデータストアの直下にフレームを作成する
        frame = Library.save_frame(root.uuid, 'フレームデータ', root_path / 'aaaa1.csv', self.USER_ID1)
        # 作成したフレームのラベルを変更する
        updated_frame = Library.update_frame_data(frame.uuid, '新しいフレームデータ', self.USER_ID2)
        # ラベルとディレクトリパスのみが変更されることを検証する
        self.assertEqual(updated_frame.id, frame.id)
        self.assertEqual(updated_frame.parent_id, frame.parent_id)
        self.assertEqual(updated_frame.uuid, frame.uuid)
        # self.assertEqual(updated_frame.path, os.path.join(root.path, '新しいフレームデータ'))
        self.assertEqual(updated_frame.type, frame.type)
        self.assertEqual(updated_frame.label, '新しいフレームデータ')
        self.assertEqual(frame.creator, self.USER_ID1)
        self.assertEqual(frame.modifier, self.USER_ID2)
        self.assertEqual(updated_frame.created_at, frame.created_at)
        self.assertIsNotNone(updated_frame.modified_at)
        # 作成したフレームを削除する
        Library.delete_frame(updated_frame.uuid)

    def test_move_frame(self):
        """
        フレームを移動する
        """
        # ルートデータストアを取得する
        root = Library.load_root()
        # フレームデータを格納するファイルを作成する
        self.save(root.path / 'aiueo.csv')
        # ルートデータストアの直下にフレームを作成する
        frame_src = Library.save_frame(root.uuid, 'フレームSRC', root.path / 'aiueo.csv', self.USER_ID1)
        # ルートデータストアの直下にフォルダを作成する
        folder_dst = Library.save_folder(root.uuid, 'フォルダDST_A', self.USER_ID1)
        # フレームSRCをフォルダDSTへ移動する
        updated_frame = frame_src.move(folder_dst.uuid, self.USER_ID2)
        # parent_id, path, modifierが変更されることを検証する
        self.assertEqual(updated_frame.id, frame_src.id)
        self.assertEqual(updated_frame.parent_id, folder_dst.id)
        self.assertEqual(updated_frame.uuid, frame_src.uuid)
        self.assertEqual(updated_frame.path, root.path / 'フォルダDST_A/aiueo.csv')
        self.assertEqual(updated_frame.type, frame_src.type)
        self.assertEqual(updated_frame.label, 'フレームSRC')
        self.assertEqual(updated_frame.creator, self.USER_ID1)
        self.assertEqual(updated_frame.modifier, self.USER_ID2)
        self.assertEqual(updated_frame.created_at, frame_src.created_at)
        self.assertIsNotNone(updated_frame.modified_at)
        # 作成したフォルダを削除する
        Library.delete_frame(updated_frame.uuid)
        Library.delete_folder(folder_dst.uuid)

    def test_move_frame2(self):
        """
        フレームを移動する
        (異動先に同じファイル・ラベル名がある場合)
        """
        # ルートデータストアを取得する
        root = Library.load_root()
        # フレームデータを格納するファイルを作成する
        self.save(root.path / 'aiueo2.csv')
        # ルートデータストアの直下にフレームを作成する
        frame_src = Library.save_frame(root.uuid, 'フレームSRC2', root.path / 'aiueo2.csv', self.USER_ID1)
        # ルートデータストアの直下にフォルダを作成する
        folder_dst = Library.save_folder(root.uuid, 'フォルダDST_A2', self.USER_ID1)
        # フレームデータを格納するファイルを作成する
        self.save(folder_dst.path / 'aiueo2.csv')
        # フォルダDST_A2の直下に同じ名称でフレームを作成する
        frame_src2 = Library.save_frame(root.uuid, 'フレームSRC2', folder_dst.path / 'aiueo2.csv', self.USER_ID1)
        # フレームSRC2をフォルダDSTへ移動する
        updated_frame = frame_src.move(folder_dst.uuid, self.USER_ID2)
        # parent_id, path, modifierが変更されることを検証する
        self.assertEqual(updated_frame.id, frame_src.id)
        self.assertEqual(updated_frame.parent_id, folder_dst.id)
        self.assertEqual(updated_frame.uuid, frame_src.uuid)
        self.assertEqual(updated_frame.path, root.path / 'フォルダDST_A2/aiueo2_1.csv')
        self.assertEqual(updated_frame.type, frame_src.type)
        self.assertEqual(updated_frame.label, 'フレームSRC2_2')
        self.assertEqual(updated_frame.creator, self.USER_ID1)
        self.assertEqual(updated_frame.modifier, self.USER_ID2)
        self.assertEqual(updated_frame.created_at, frame_src.created_at)
        self.assertIsNotNone(updated_frame.modified_at)
        # 作成したフォルダを削除する
        Library.delete_frame(updated_frame.uuid)
        Library.delete_folder(folder_dst.uuid)

    def test_save_frame(self):
        """
        フレームを追加する
        """
        # ルートデータストアを取得する
        root = Library.load_root()
        root_path = root.path
        # フレームデータを格納するファイルを作成する
        self.save(root_path / 'aaaa2.csv')
        # ルートデータストアの直下にフレームを作成する
        frame = Library.save_frame(root.uuid, 'フレームデータ', root_path / 'aaaa2.csv', self.USER_ID1)
        # 作成したフレームの値を検証する
        self.assertIsNotNone(frame.id)
        self.assertEqual(frame.parent_id, root.id)
        self.assertIsNotNone(frame.uuid)
        self.assertEqual(frame.path, root_path / 'aaaa2.csv')
        self.assertEqual(frame.type, 'frame')
        self.assertEqual(frame.label, 'フレームデータ')
        self.assertEqual(frame.creator, self.USER_ID1)
        self.assertEqual(frame.modifier, self.USER_ID1)
        self.assertEqual(frame.creator, frame.modifier)
        self.assertIsNotNone(frame.created_at)
        self.assertIsNotNone(frame.modified_at)
        self.assertEqual(frame.created_at, frame.modified_at)
        # 作成したフレームを削除する
        Library.delete_frame(frame.uuid)

    def test_save2_frame(self):
        """
        フレームを作成する
        """
        # ルートデータストアを取得する
        root = Library.load_root()
        root_path = root.path
        # フレームデータを格納するファイルを作成する
        self.save(root_path / 'aaaa3.csv')
        with open(Path(Datum._to_abs_path(root_path.as_posix())) / 'aaaa3.csv', mode='rb') as stream:
            # ルートデータストアの直下にフレームを作成する
            frame = Library.save2_frame(root.uuid, 'フレームデータ', stream, self.USER_ID1)
        # 作成したフレームの値を検証する
        self.assertIsNotNone(frame.id)
        self.assertEqual(frame.parent_id, root.id)
        self.assertIsNotNone(frame.uuid)
        # self.assertEqual(frame.path, os.path.join(root.path, 'フレームデータ'))
        self.assertEqual(frame.type, 'frame')
        self.assertEqual(frame.label, 'フレームデータ')
        self.assertEqual(frame.creator, self.USER_ID1)
        self.assertEqual(frame.modifier, self.USER_ID1)
        self.assertEqual(frame.creator, frame.modifier)
        self.assertIsNotNone(frame.created_at)
        self.assertIsNotNone(frame.modified_at)
        self.assertEqual(frame.created_at, frame.modified_at)
        # 作成したフレームを削除する
        Library.delete_frame(frame.uuid)
        # 作成したファイルを削除する
        self.delete(root_path / 'aaaa3.csv')


    def test_get_flow(self):
        """
        フローを取得する
        """
        # ルートデータストアを取得する
        root = Library.load_root()
        root_path = root.path
        # フレームデータを格納するファイルを作成する
        self.save(root_path / 'frame_for_flow.csv')
        # ルートデータストアの直下にフレームを作成する
        frame = Library.save_frame(root.uuid, 'フレームデータ',
                                   root_path / 'frame_for_flow.csv', self.USER_ID1)
        # フローデータを作成する
        flow_data = {
            'projectId': 1,
            'label': 'テストフロー',
            'ports': [[],[]],
            'params': [],
            'description': "",
            'nodes' : [
                {
                    "id": "i",
                    "type": frame.type,
                    "dataSource": "csv",
                    "uuid": frame.uuid,
                    "label": frame.label
                }
            ],
            'creator': '織田信長',
            'createdAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        # ルートデータストアの直下にフローを作成する
        flow = Library.save_flow(root.uuid, 'フロー', flow_data, self.USER_ID1)
        # 作成したフローを取得する
        flow = Library.load_flow(flow.uuid)
        # 作成したフローの値を検証する
        self.assertIsNotNone(flow.id)
        self.assertEqual(flow.parent_id, root.id)
        self.assertIsNotNone(flow.uuid)
        self.assertIsNone(flow.path)
        self.assertEqual(flow.type, 'flow')
        self.assertEqual(flow.label, 'フロー')
        self.assertEqual(flow.flow_data, flow_data)
        self.assertEqual(flow.creator, self.USER_ID1)
        self.assertEqual(flow.modifier, self.USER_ID1)
        self.assertEqual(flow.creator, flow.modifier)
        self.assertIsNotNone(flow.created_at)
        self.assertIsNotNone(flow.modified_at)
        self.assertEqual(flow.created_at, flow.modified_at)
        # 作成したフローを削除する
        Library.delete_flow(flow.uuid)
        # 作成したファイルを削除する
        self.delete(root_path / 'frame_for_flow.csv')

    def test_update_flow(self):
        """
        フローを変更する
        """
        # ルートデータストアを取得する
        root = Library.load_root()
        root_path = root.path
        # フレームデータを格納するファイルを作成する
        self.save(root_path / 'frame_for_flow2.csv')
        # ルートデータストアの直下にフレームを作成する
        frame = Library.save_frame(root.uuid, 'フレームデータ',
                                   root_path / 'frame_for_flow2.csv', self.USER_ID1)
        # フローデータを作成する
        flow_data = {
            'projectId': 1,
            'label': 'テストフロー',
            'ports': [[],[]],
            'params': [],
            'description': "",
            'nodes' : [],
            'creator': '織田信長',
            'createdAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        # ルートデータストアの直下にフローを作成する
        flow = Library.save_flow(root.uuid, 'フロー', flow_data, self.USER_ID1)

        new_flow_data = {
            'projectId': 2,
            'label': '新しいテストフロー',
            'ports': [[],[]],
            'params': [],
            'description': "フローです",
            'nodes' : [
                {
                    "id": "i",
                    "type": frame.type,
                    "dataSource": "csv",
                    "uuid": frame.uuid,
                    "label": frame.label
                }
            ],
            'creator': '織田信雄',
            'createdAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        # 作成したフローを変更する
        updated_flow = Flow.update_data(flow.uuid, '新しいフロー', new_flow_data, self.USER_ID2)

        # ラベルとディレクトリパスのみが変更されることを検証する
        self.assertEqual(updated_flow.id, flow.id)
        self.assertEqual(updated_flow.parent_id, flow.parent_id)
        self.assertEqual(updated_flow.uuid, flow.uuid)
        self.assertIsNone(updated_flow.path)
        self.assertEqual(updated_flow.type, flow.type)
        self.assertEqual(updated_flow.label, '新しいフロー')
        self.assertEqual(updated_flow.flow_data, new_flow_data)
        self.assertEqual(updated_flow.creator, self.USER_ID1)
        self.assertEqual(updated_flow.modifier, self.USER_ID2)
        self.assertEqual(updated_flow.created_at, flow.created_at)
        self.assertIsNotNone(updated_flow.modified_at)
        # 作成したフレームを削除する
        Library.delete_flow(updated_flow.uuid)
        # 作成したファイルを削除する
        self.delete(root_path / 'frame_for_flow2.csv')

    def test_move_flow(self):
        """
        フローを移動する
        """
        # ルートデータストアを取得する
        root = Library.load_root()
        # ルートデータストアの直下にフローを作成する
        flow_data = {
            'projectId': 1,
            'label': 'フローSRC',
            'ports': [[],[]],
            'params': [],
            'description': "",
            'nodes' : [],
            'creator': '足利義教',
            'createdAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        flow_src = Library.save_flow(root.uuid, 'フローSRC', flow_data, self.USER_ID1)
        # ルートデータストアの直下にフォルダを作成する
        folder_dst = Library.save_folder(root.uuid, 'フォルダDST_B', self.USER_ID1)
        # フローSRCをフォルダDSTへ移動する
        updated_flow = flow_src.move(folder_dst.uuid, self.USER_ID2)
        # parent_id, path, modifierが変更されることを検証する
        self.assertEqual(updated_flow.id, flow_src.id)
        self.assertEqual(updated_flow.parent_id, folder_dst.id)
        self.assertEqual(updated_flow.uuid, flow_src.uuid)
        self.assertEqual(updated_flow.type, flow_src.type)
        self.assertEqual(updated_flow.label, 'フローSRC')
        self.assertEqual(updated_flow.creator, self.USER_ID1)
        self.assertEqual(updated_flow.modifier, self.USER_ID2)
        self.assertEqual(updated_flow.created_at, flow_src.created_at)
        self.assertIsNotNone(updated_flow.modified_at)
        # 作成したフォルダを削除する
        Library.delete_flow(updated_flow.uuid)
        Library.delete_folder(folder_dst.uuid)

    def test_save_flow(self):
        """
        フローを追加する
        """
        # ルートデータストアを取得する
        root = Library.load_root()
        # フローデータを作成する
        flow_data = {
            'projectId': 1,
            'label': 'テストフロー',
            'ports': [[],[]],
            'params': [],
            'description': "",
            'nodes' : [],
            'creator': '織田信長',
            'createdAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        # ルートデータストアの直下にフローを作成する
        flow = Library.save_flow(root.uuid, 'フロー', flow_data, self.USER_ID1)

        # 作成したフレームの値を検証する
        self.assertIsNotNone(flow.id)
        self.assertEqual(flow.parent_id, root.id)
        self.assertIsNotNone(flow.uuid)
        self.assertIsNone(flow.path)
        self.assertEqual(flow.type, 'flow')
        self.assertEqual(flow.label, 'フロー')
        self.assertEqual(flow.creator, self.USER_ID1)
        self.assertEqual(flow.modifier, self.USER_ID1)
        self.assertEqual(flow.creator, flow.modifier)
        self.assertIsNotNone(flow.created_at)
        self.assertIsNotNone(flow.modified_at)
        self.assertEqual(flow.created_at, flow.modified_at)
        # 作成したフレームを削除する
        Library.delete_flow(flow.uuid)


    def test_get_no_folder(self):
        """
        存在しないフォルダを取得しようとすると例外を送出する
        """
        with self.assertRaises(Exception) as e:
            Library.load_folder('00000000-0000-0000-0000-000000000000')

    def test_update_no_folder(self):
        """
        存在しないフォルダのラベルを変更しようとすると例外を送出する
        """
        with self.assertRaises(Exception) as e:
            Library.update_folder_data('00000000-0000-0000-0000-000000000000', '新しいフォルダ', self.USER_ID2)

    def test_delete_no_folder(self):
        """
        存在しないフォルダを削除しようとすると例外を送出する
        """
        with self.assertRaises(Exception) as e:
            Library.delete_folder('00000000-0000-0000-0000-000000000000')

    @unittest.skip
    def test_get_no_frame(self):
        """
        存在しないフレームを取得しようとすると例外を送出する
        """
        with self.assertRaises(Exception) as e:
            Library.load_frame('00000000-0000-0000-0000-000000000000')

    def test_update_no_frame(self):
        """
        存在しないフレームのラベルを変更しようとすると例外を送出する
        """
        with self.assertRaises(Exception) as e:
            Library.update_frame_data('00000000-0000-0000-0000-000000000000', '新しいラベル', self.USER_ID2)

    def test_delete_no_frame(self):
        """
        存在しないフレームを削除しようとすると例外を送出する
        """
        with self.assertRaises(Exception) as e:
            Library.delete_frame('00000000-0000-0000-0000-000000000000')

    def test_get_no_flow(self):
        """
        存在しないフローを取得しようとすると例外を送出する
        """
        with self.assertRaises(Exception) as e:
            Library.load_flow('00000000-0000-0000-0000-000000000000')

    def test_update_no_flow(self):
        """
        存在しないフローのラベルを変更しようとすると例外を送出する
        """
        with self.assertRaises(Exception) as e:
            Library.update_flow_data('00000000-0000-0000-0000-000000000000',
                                     '新しいラベル', None, self.USER_ID2)

    def test_delete_no_flow(self):
        """
        存在しないフローを削除しようとすると例外を送出する
        """
        with self.assertRaises(Exception) as e:
            Library.delete_flow('00000000-0000-0000-0000-000000000000')


    def test_delete_folder_has_child(self):
        """
        フレームを内包するフォルダを削除しようとすると例外を送出する
        """
        # ルートデータストアを取得する
        root = Library.load_root()
        root_path = root.path
        # ルートデータストアの直下にフォルダを作成する
        folder = Library.save_folder(root.uuid, 'フォルダA', self.USER_ID1)
        # フレームデータを格納するファイルを作成する
        self.save(root_path / 'aaaa.csv')
        # ルートデータストアの直下にフレームを作成する
        frame = Library.save_frame(folder.uuid, 'フレームデータ', root_path / 'aaaa.csv', self.USER_ID1)
        # フレームを内包するフォルダを削除しようとする
        with self.assertRaises(Exception) as e:
            Library.delete_folder(folder.uuid)
        # 作成したフレームを削除する
        Library.delete_frame(frame.uuid)
        # 作成したフォルダを削除する
        Library.delete_folder(folder.uuid)

    def test_update_to_illigal_folder_name(self):
        """
        '/'や'\0'を含むディレクトリパスは、それぞれ'／'と''に変換される
        """
        # ルートデータストアを取得する
        root = Library.load_root()
        # ルートデータストアの直下にフォルダを作成する
        folder = Library.save_folder(root.uuid, 'フォルダB', self.USER_ID1)
        # 作成したフォルダのラベルを変更する
        updated_folder = Library.update_folder_data(folder.uuid, '/新しい\0フォルダ/', self.USER_ID2)
        # ラベルとディレクトリパスでは'/'や'\0'は使われない
        self.assertEqual(updated_folder.path, root.path / '／新しいフォルダ／')
        self.assertEqual(updated_folder.label, '/新しいフォルダ/')
        # 作成したフォルダを削除する
        Library.delete_folder(folder.uuid)

    def test_delete_folder_refer_to_file_other_frame_refering(self):
        """
        二つのフォルダが一つのディレクトリに対応している場合に、
        何れか一つのフォルダを削除しても、ディレクトリは削除されない
        """
        pass

    def test_update_folder_refer_to_file_other_frame_refering(self):
        """
        二つのフォルダが一つのディレクトリに対応している場合に、
        何れか一つのフォルダのラベル名を変更しても、不整合は発生しない
        """
        pass

    def test_delete_frame_refer_to_file_other_frame_refering(self):
        """
        二つのフレームが一つのCSVファイルに対応している場合に、
        何れか一つのフレームを削除しても、CSVファイルは削除されない
        """
        # ルートデータストアを取得する
        root = Library.load_root()
        root_path = root.path
        # フレームデータを格納するファイルを作成する
        self.save(root_path / 'foo.csv')
        # ルートデータストアの直下にフレーム1を作成する
        frame1 = Library.save_frame(root.uuid, 'フレームデータ', root_path / 'foo.csv', self.USER_ID1)
        # ルートデータストアの直下にフレーム2を作成する
        frame2 = Library.save_frame(root.uuid, 'フレームデータ', root_path / 'foo.csv', self.USER_ID1)
        # フレーム1を削除する
        Library.delete_frame(frame1.uuid)
        # フレーム1,2に対応するCSVファイルが存在することを検証する
        self.assertTrue((Path(Datum._to_abs_path(root_path.as_posix())) / 'foo.csv').is_file())
        # フレーム2を削除する
        Library.delete_frame(frame2.uuid)
        # フレーム1,2に対応するCSVファイルが存在しないことを検証する
        self.assertFalse((root_path / 'foo.csv').is_file())

    def test_update_frame_refer_to_file_other_frame_refering(self):
        """
        二つのフレームが一つのCSVファイルに対応している場合に、
        何れか一つのフレームのラベル名を変更しても、不整合は発生しない
        """
        # ルートデータストアを取得する
        root = Library.load_root()
        root_path = root.path
        # フレームデータを格納するファイルを作成する
        self.save(root_path / 'abc.csv')
        # ルートデータストアの直下にフレーム1を作成する
        frame1 = Library.save_frame(root.uuid, 'フレームデータ', root_path / 'abc.csv', self.USER_ID1)
        # ルートデータストアの直下にフレーム2を作成する
        frame2 = Library.save_frame(root.uuid, 'フレームデータ', root_path / 'abc.csv', self.USER_ID1)
        # フレーム1のラベル名を変更する
        Library.update_frame_data(frame1.uuid, '新しいフレームデータ1', self.USER_ID2)
        # フレーム1のラベル名の変更に従って、CSVファイル名が変更されていることを検証する
        self.assertEqual(frame1.path, root_path / '新しいフレームデータ1')
        self.assertEqual(frame2.path, root_path / '新しいフレームデータ1')
        self.assertTrue (os.path.isfile(Path(Datum._to_abs_path(root_path.as_posix())) / '新しいフレームデータ1'))
        self.assertFalse(os.path.isfile(Path(Datum._to_abs_path(root_path.as_posix())) / 'abc.csv'))
        # フレーム1を削除する
        Library.delete_frame(frame1.uuid)
        # フレーム2を削除する
        Library.delete_frame(frame2.uuid)

    def test_frame_file_collision(self):
        """
        3つのフレームでCSVファイル名が重複した場合は、異なるCSVファイル名が使われる
        """
        # ルートデータストアを取得する
        root = Library.load_root()
        root_path = root.path
        # フレームデータを格納するファイルを作成する
        self.save(root_path / 'bar.csv')
        with open( Path(Datum._to_abs_path(root_path.as_posix())) / 'bar.csv', mode='rb') as stream:
            # ルートデータストアの直下にフレーム1を作成する
            frame1 = Library.save2_frame(root.uuid, 'フレームデータ', stream, self.USER_ID1)
            # ルートデータストアの直下にフレーム2を作成する
            frame2 = Library.save2_frame(root.uuid, 'フレームデータ', stream, self.USER_ID1)
            # ルートデータストアの直下にフレーム3を作成する
            frame3 = Library.save2_frame(root.uuid, 'フレームデータ', stream, self.USER_ID1)
        # フレーム2に対応するファイルパスはフレームデータ_1であることを検証する
        self.assertEqual(frame1.path, root_path / 'フレームデータ')
        self.assertEqual(frame2.path, root_path / 'フレームデータ_1')
        self.assertEqual(frame3.path, root_path / 'フレームデータ_2')
        # フレーム1を削除する
        Library.delete_frame(frame1.uuid)
        # フレーム2を削除する
        Library.delete_frame(frame2.uuid)
        # フレーム3を削除する
        Library.delete_frame(frame3.uuid)
        # 作成したファイルを削除する
        self.delete(root_path / 'bar.csv')

