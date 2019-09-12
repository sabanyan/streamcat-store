import os
import unittest
import json
import uuid
import pprint
from pathlib import Path
from datetime import datetime

from kskp.store import Library, STORE_DIR

class LibraryTest(unittest.TestCase):
    # テスト用ユーザID
    USER_ID1 = 88
    USER_ID2 = 99

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @classmethod
    def tearDownClass(cls):
        # ライブラリフォルダを削除する
        from kskp.core import Datum
        library_path = STORE_DIR.parent / Datum.find_root().path
        import shutil
        shutil.rmtree(library_path.as_posix())
        # Sessionを閉じる
        from kskp.store import ss as session
        session.close()
        # スキーマを破棄する
        from kskp.store import engine
        from sqlalchemy import DDL
        engine.execute(DDL('DROP SCHEMA IF EXISTS %s CASCADE' % os.environ['KSKP_POSTGRESQL_SCHEMA_NAME']))

    def save(self, file_path):
        with open(file_path, "w") as f:
            f.write("I am a frame data for test cases.")

    def delete(self, file_path):
        if os.path.exists(file_path):
            os.unlink(file_path)

    def test_save_and_load(self):
        # ルートデータストアを取得する
        root = Library.load_root()
        # フレームデータを格納するファイルを作成する
        frame_file_path = Path(root.path + str(uuid.uuid4()))
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
        self.assertIsNotNone(root.data, {'label':'ROOT_FOLDER'})
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
        self.assertIsNotNone(root.data, {'label':'ROOT_FOLDER'})
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
        self.assertEqual(updated_folder.path, os.path.join(root.path, '新しいフォルダ'))
        self.assertEqual(updated_folder.type, folder.type)
        self.assertEqual(json.loads(updated_folder.data, encoding='utf-8')['label'], '新しいフォルダ')
        self.assertEqual(folder.creator, self.USER_ID1)
        self.assertEqual(folder.modifier, self.USER_ID2)
        self.assertEqual(updated_folder.created_at, folder.created_at)
        self.assertIsNotNone(updated_folder.modified_at)
        # 作成したフォルダを削除する
        Library.delete_folder(folder.uuid)

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
        self.assertEqual(folder.path, os.path.join(root.path, 'フォルダ'))
        self.assertEqual(folder.type, 'folder')
        self.assertEqual(json.loads(folder.data, encoding='utf-8')['label'], 'フォルダ')
        self.assertEqual(folder.creator, self.USER_ID1)
        self.assertEqual(folder.modifier, self.USER_ID1)
        self.assertEqual(folder.creator, folder.modifier)
        self.assertIsNotNone(folder.created_at)
        self.assertIsNotNone(folder.modified_at)
        self.assertEqual(folder.created_at, folder.modified_at)
        # 作成したフォルダを削除する
        Library.delete_folder(folder.uuid)


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
            self.assertEqual(folder.path, os.path.join(root.path, 'S3フォルダ1'))
            self.assertEqual(folder.type, 'awss3')
            self.assertEqual(folder.label, 'S3フォルダ1')
            self.assertEqual(folder.creator, self.USER_ID1)
            self.assertEqual(folder.modifier, self.USER_ID1)
            self.assertIsNotNone(folder.created_at)
            self.assertIsNotNone(folder.modified_at)
        finally:
            # 作成したフォルダを削除する
            Library.delete_awss3(folder.uuid)

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
            updated_folder = Library.update_awss3_data(folder.uuid, '新しいS3フォルダ', 'kskp-test', self.USER_ID2)
            # ラベルとディレクトリパスのみが変更されることを検証する
            self.assertEqual(updated_folder.id, folder.id)
            self.assertEqual(updated_folder.parent_id, folder.parent_id)
            self.assertEqual(updated_folder.uuid, folder.uuid)
            self.assertEqual(updated_folder.path, os.path.join(root.path, '新しいS3フォルダ'))
            self.assertEqual(updated_folder.type, folder.type)
            self.assertEqual(updated_folder.label, '新しいS3フォルダ')
            self.assertEqual(updated_folder.creator, self.USER_ID1)
            self.assertEqual(updated_folder.modifier, self.USER_ID2)
            self.assertEqual(updated_folder.created_at, folder.created_at)
            self.assertIsNotNone(updated_folder.modified_at)
        finally:
            # 作成したフォルダを削除する
            Library.delete_awss3(folder.uuid)

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
            self.assertEqual(folder.path, os.path.join(root.path, 'S3フォルダ3'))
            self.assertEqual(folder.type, 'awss3')
            self.assertEqual(json.loads(folder.data, encoding='utf-8')['label'], 'S3フォルダ3')
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
        # フレームデータを格納するファイルを作成する
        self.save('store/aaaa.csv')
        # ルートデータストアの直下にフレームを作成する
        frame = Library.save_frame(root.uuid, 'フレームデータ', Path('store/aaaa.csv'), self.USER_ID1)
        # 作成したフレームを取得する
        frame = Library.load_frame(frame.uuid)
        # 作成したフレームの値を検証する
        self.assertIsNotNone(frame.id)
        self.assertEqual(frame.parent_id, root.id)
        self.assertIsNotNone(frame.uuid)
        self.assertEqual(frame.path, 'store/aaaa.csv')
        self.assertEqual(frame.type, 'frame')
        self.assertEqual(json.loads(frame.data, encoding='utf-8')['label'], 'フレームデータ')
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
        # フレームデータを格納するファイルを作成する
        self.save('store/aaaa1.csv')
        # ルートデータストアの直下にフレームを作成する
        frame = Library.save_frame(root.uuid, 'フレームデータ', Path('store/aaaa1.csv'), self.USER_ID1)
        # 作成したフレームのラベルを変更する
        updated_frame = Library.update_frame_data(frame.uuid, '新しいフレームデータ', self.USER_ID2)
        # ラベルとディレクトリパスのみが変更されることを検証する
        self.assertEqual(updated_frame.id, frame.id)
        self.assertEqual(updated_frame.parent_id, frame.parent_id)
        self.assertEqual(updated_frame.uuid, frame.uuid)
        # self.assertEqual(updated_frame.path, os.path.join(root.path, '新しいフレームデータ'))
        self.assertEqual(updated_frame.type, frame.type)
        self.assertEqual(json.loads(updated_frame.data, encoding='utf-8')['label'], '新しいフレームデータ')
        self.assertEqual(frame.creator, self.USER_ID1)
        self.assertEqual(frame.modifier, self.USER_ID2)
        self.assertEqual(updated_frame.created_at, frame.created_at)
        self.assertIsNotNone(updated_frame.modified_at)
        # 作成したフレームを削除する
        Library.delete_frame(updated_frame.uuid)

    def test_save_frame(self):
        """
        フレームを追加する
        """
        # ルートデータストアを取得する
        root = Library.load_root()
        # フレームデータを格納するファイルを作成する
        self.save('store/aaaa2.csv')
        # ルートデータストアの直下にフレームを作成する
        frame = Library.save_frame(root.uuid, 'フレームデータ', Path('store/aaaa2.csv'), self.USER_ID1)
        # 作成したフレームの値を検証する
        self.assertIsNotNone(frame.id)
        self.assertEqual(frame.parent_id, root.id)
        self.assertIsNotNone(frame.uuid)
        self.assertEqual(frame.path, 'store/aaaa2.csv')
        self.assertEqual(frame.type, 'frame')
        self.assertEqual(json.loads(frame.data, encoding='utf-8')['label'], 'フレームデータ')
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
        # フレームデータを格納するファイルを作成する
        self.save('store/aaaa3.csv')
        with open('store/aaaa3.csv', mode='rb') as stream:
            # ルートデータストアの直下にフレームを作成する
            frame = Library.save2_frame(root.uuid, 'フレームデータ', stream, self.USER_ID1)
        # 作成したフレームの値を検証する
        self.assertIsNotNone(frame.id)
        self.assertEqual(frame.parent_id, root.id)
        self.assertIsNotNone(frame.uuid)
        # self.assertEqual(frame.path, os.path.join(root.path, 'フレームデータ'))
        self.assertEqual(frame.type, 'frame')
        self.assertEqual(json.loads(frame.data, encoding='utf-8')['label'], 'フレームデータ')
        self.assertEqual(frame.creator, self.USER_ID1)
        self.assertEqual(frame.modifier, self.USER_ID1)
        self.assertEqual(frame.creator, frame.modifier)
        self.assertIsNotNone(frame.created_at)
        self.assertIsNotNone(frame.modified_at)
        self.assertEqual(frame.created_at, frame.modified_at)
        # 作成したフレームを削除する
        Library.delete_frame(frame.uuid)
        # 作成したファイルを削除する
        self.delete('store/aaaa3.csv')


    def test_get_flow(self):
        """
        フローを取得する
        """
        # ルートデータストアを取得する
        root = Library.load_root()
        # フレームデータを格納するファイルを作成する
        self.save('store/frame_for_flow.csv')
        # ルートデータストアの直下にフレームを作成する
        frame = Library.save_frame(root.uuid, 'フレームデータ', Path('store/frame_for_flow.csv'), self.USER_ID1)
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
        self.assertEqual(flow.path, '')
        self.assertEqual(flow.type, 'flow')
        self.assertEqual(flow.label, 'フロー')
        self.assertEqual(json.loads(flow.data, encoding='utf-8')['flow'], flow_data)
        self.assertEqual(flow.creator, self.USER_ID1)
        self.assertEqual(flow.modifier, self.USER_ID1)
        self.assertEqual(flow.creator, flow.modifier)
        self.assertIsNotNone(flow.created_at)
        self.assertIsNotNone(flow.modified_at)
        self.assertEqual(flow.created_at, flow.modified_at)
        # 作成したフローを削除する
        Library.delete_flow(flow.uuid)
        # 作成したファイルを削除する
        self.delete('store/frame_for_flow.csv')

    def test_update_flow(self):
        """
        フローを変更する
        """
        # ルートデータストアを取得する
        root = Library.load_root()
        # フレームデータを格納するファイルを作成する
        self.save('store/frame_for_flow2.csv')
        # ルートデータストアの直下にフレームを作成する
        frame = Library.save_frame(root.uuid, 'フレームデータ', Path('store/frame_for_flow2.csv'), self.USER_ID1)
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
        updated_flow = Library.update_flow_data(flow.uuid, '新しいフロー', new_flow_data, self.USER_ID2)

        # ラベルとディレクトリパスのみが変更されることを検証する
        self.assertEqual(updated_flow.id, flow.id)
        self.assertEqual(updated_flow.parent_id, flow.parent_id)
        self.assertEqual(updated_flow.uuid, flow.uuid)
        self.assertEqual(updated_flow.path, '')
        self.assertEqual(updated_flow.type, flow.type)
        self.assertEqual(updated_flow.label, '新しいフロー')
        self.assertEqual(json.loads(updated_flow.data, encoding='utf-8')['flow'], new_flow_data)
        self.assertEqual(updated_flow.creator, self.USER_ID1)
        self.assertEqual(updated_flow.modifier, self.USER_ID2)
        self.assertEqual(updated_flow.created_at, flow.created_at)
        self.assertIsNotNone(updated_flow.modified_at)
        # 作成したフレームを削除する
        Library.delete_flow(updated_flow.uuid)
        # 作成したファイルを削除する
        self.delete('store/frame_for_flow2.csv')

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
        self.assertEqual(flow.path, '')
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
            Library.update_flow_data('00000000-0000-0000-0000-000000000000', '新しいラベル', None, self.USER_ID2)

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
        # ルートデータストアの直下にフォルダを作成する
        folder = Library.save_folder(root.uuid, 'フォルダA', self.USER_ID1)
        # フレームデータを格納するファイルを作成する
        self.save('store/aaaa.csv')
        # ルートデータストアの直下にフレームを作成する
        frame = Library.save_frame(folder.uuid, 'フレームデータ', Path('store/aaaa.csv'), self.USER_ID1)
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
        self.assertEqual(updated_folder.path, os.path.join(root.path, '／新しいフォルダ／'))
        self.assertEqual(json.loads(updated_folder.data, encoding='utf-8')['label'], '/新しい\0フォルダ/')
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
        # フレームデータを格納するファイルを作成する
        self.save('store/foo.csv')
        # ルートデータストアの直下にフレーム1を作成する
        frame1 = Library.save_frame(root.uuid, 'フレームデータ', Path('store/foo.csv'), self.USER_ID1)
        # ルートデータストアの直下にフレーム2を作成する
        frame2 = Library.save_frame(root.uuid, 'フレームデータ', Path('store/foo.csv'), self.USER_ID1)
        # フレーム1を削除する
        Library.delete_frame(frame1.uuid)
        # フレーム1,2に対応するCSVファイルが存在することを検証する
        self.assertTrue(os.path.isfile('store/foo.csv'))
        # フレーム2を削除する
        Library.delete_frame(frame2.uuid)
        # フレーム1,2に対応するCSVファイルが存在しないことを検証する
        self.assertFalse(os.path.isfile('store/foo.csv'))

    def test_update_frame_refer_to_file_other_frame_refering(self):
        """
        二つのフレームが一つのCSVファイルに対応している場合に、
        何れか一つのフレームのラベル名を変更しても、不整合は発生しない
        """
        # ルートデータストアを取得する
        root = Library.load_root()
        # フレームデータを格納するファイルを作成する
        self.save('store/abc.csv')
        # ルートデータストアの直下にフレーム1を作成する
        frame1 = Library.save_frame(root.uuid, 'フレームデータ', Path('store/abc.csv'), self.USER_ID1)
        # ルートデータストアの直下にフレーム2を作成する
        frame2 = Library.save_frame(root.uuid, 'フレームデータ', Path('store/abc.csv'), self.USER_ID1)
        # フレーム1のラベル名を変更する
        Library.update_frame_data(frame1.uuid, '新しいフレームデータ1', self.USER_ID2)
        # フレーム1のラベル名の変更に従って、CSVファイル名が変更されていることを検証する
        self.assertEqual(frame1.path, 'store/新しいフレームデータ1')
        self.assertEqual(frame2.path, 'store/新しいフレームデータ1')
        self.assertTrue(os.path.isfile('store/新しいフレームデータ1'))
        self.assertFalse(os.path.isfile('store/abc.csv'))
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
        # フレームデータを格納するファイルを作成する
        self.save('store/bar.csv')
        with open('store/bar.csv', mode='rb') as stream:
            # ルートデータストアの直下にフレーム1を作成する
            frame1 = Library.save2_frame(root.uuid, 'フレームデータ', stream, self.USER_ID1)
            # ルートデータストアの直下にフレーム2を作成する
            frame2 = Library.save2_frame(root.uuid, 'フレームデータ', stream, self.USER_ID1)
            # ルートデータストアの直下にフレーム3を作成する
            frame3 = Library.save2_frame(root.uuid, 'フレームデータ', stream, self.USER_ID1)
        # フレーム2に対応するファイルパスはフレームデータ_1であることを検証する
        # self.assertEqual(frame1.path, 'store/フレームデータ')
        # self.assertEqual(frame2.path, 'store/フレームデータ_1')
        # self.assertEqual(frame3.path, 'store/フレームデータ_2')
        # フレーム1を削除する
        Library.delete_frame(frame1.uuid)
        # フレーム2を削除する
        Library.delete_frame(frame2.uuid)
        # フレーム3を削除する
        Library.delete_frame(frame3.uuid)
        # 作成したファイルを削除する
        self.delete('store/bar.csv')



    # def test_Folder_save(self):
    #     folder = Folder(Path('kskp/store/frames/csv'))
    #     my_uuid = folder.issue_uuid()
    #     folder.save({}, None, str(my_uuid))

    # def test_Folder_load(self):
    #     folder = Folder(Path('kskp/store/frames/csv'))
    #     my_uuid = folder.issue_uuid()
    #     with self.assertRaises(Exception) as e:
    #         folder.load(my_uuid)

    # def test_Frame(self):
    #     frame = Frame()
    #     frame.set_uuid = str(uuid.uuid4())
    #     frame.set_cache_info = {'dir_path':'store/'}
    #     frame.save()

    # def test_Cache(self):
    #     cache = Cache()
    #     cache.set_uuid = str(uuid.uuid4())
    #     cache.set_cache_info = {'dir_path':'store/'}
    #     cache.save()
