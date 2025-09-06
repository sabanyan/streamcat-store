import os
import unittest
import uuid
import pprint
from datetime import datetime
from streamcat.core import SavableDatum
from streamcat.store import RemoteFolderConn
from .test_case_base import TestCaseBase

class LibraryTest(TestCaseBase, unittest.IsolatedAsyncioTestCase):
    # テスト用ユーザID
    # USER_ID1 = 88
    # USER_ID2 = 99

    conn_json = {
        'protocol' : 'smb',
        'hostname' : "15.168.34.0",
        'domain'   : "WORKGROUP",
        'directory': "share",
        'userId'  : "samba",
        'password' : "kskanalytics"
    }

    def save(self, file_path):
        file_path = file_path
        with open(file_path, "w") as f:
            f.write("I am a frame data for test cases.")

    def delete(self, file_path):
        if os.path.exists(file_path):
            os.unlink(file_path)

    def save_frame(self, parent, label, path):
        import io
        new_frame = parent.create_frame(label, io.BytesIO(b''))
        # documentレコードをDBに格納する
        new_frame.save(file_path=path)
        # save()によりreadable=Noneになるため再取得する
        return self.finder.data.find_by_uuid(new_frame.uuid)

    def save2_frame(self, parent, label, stream):
        new_frame = parent.create_frame(label, stream)
        # documentレコードをDBに格納する
        new_frame.save()
        # save()によりreadable=Noneになるため再取得する
        return self.finder.data.find_by_uuid(new_frame.uuid)

    def save_folder(self, parent, label):
        new_folder = parent.create_folder(label)
        new_folder.save()
        # save()によりreadable=Noneになるため再取得する
        return self.finder.data.find_by_uuid(new_folder.uuid)

    def save_rfolder(self, parent, label, conn):
        new_folder = parent.create_remote_folder(label, conn)
        new_folder.save()
        # save()によりreadable=Noneになるため再取得する
        return self.finder.data.find_by_uuid(new_folder.uuid)

    def save_flow(self, parent, label, flow_json):
        from streamcat.store import FlowData
        new_flow = parent.create_flow(label, FlowData(flow_json))
        new_flow.save()
        # save()によりreadable=Noneになるため再取得する
        return self.finder.data.find_by_uuid(new_flow.uuid)


    async def test_save_and_load(self):
        # ルートデータストアを取得する
        root = self.finder.data.load_root()
        # フレームデータを格納するファイルを作成する
        frame_file_path = root.path / str(uuid.uuid4())
        self.save(frame_file_path)
        # 指定したファイルをフレームとしてライブラリに登録する
        new_frame = self.save_frame(root, 'テストフレーム', frame_file_path)
        # 登録したフレームを取得する
        saved_frame = self.finder.data.find_by_uuid(new_frame.uuid)
        # 作成したフレームを削除する
        saved_frame.delete()

    async def test_get_root(self):
        """
        ルートフォルダを取得する
        """
        # ルートデータストアを取得する
        root = self.finder.data.load_root()
        # 取得したルートデータストアの値を検証する
        self.assertIsNotNone(root.id)
        self.assertIsNone(root.parent_id)
        self.assertIsNotNone(root.uuid)
        self.assertIsNotNone(root.path)
        self.assertEqual(root.type, 'folder')
        self.assertTrue(root.data_is_empty)
        self.assertIsNotNone(root.creator)
        self.assertIsNotNone(root.modifier)
        self.assertIsNotNone(root.created_at)
        self.assertIsNotNone(root.modified_at)

    async def test_get_folder(self):
        """
        フォルダを取得する
        """
        # ルートデータストアを取得する
        root = self.finder.data.load_root()
        # ルートデータストアをフォルダとして取得する
        folder = self.finder.data.find_by_uuid(root.uuid, type=SavableDatum.FOLDER_TYPE)
        # 取得したフォルダの値を検証する
        self.assertIsNotNone(folder.id)
        self.assertIsNone(folder.parent_id)
        self.assertIsNotNone(folder.uuid)
        self.assertIsNotNone(folder.path)
        self.assertEqual(folder.type, 'folder')
        self.assertTrue(root.data_is_empty)
        self.assertIsNotNone(folder.creator)
        self.assertIsNotNone(folder.modifier)
        self.assertIsNotNone(folder.created_at)
        self.assertIsNotNone(folder.modified_at)

    async def test_update_folder(self):
        """
        フォルダのラベルを変更する
        """
        # ルートデータストアを取得する
        root = self.finder.data.load_root()
        # ルートデータストアの直下にフォルダを作成する
        folder = self.save_folder(root, 'フォルダ0')
        # 作成したフォルダのラベルを変更する
        updated_folder = folder.update_label('新しいフォルダ', self.USER2)
        # ラベルとディレクトリパスのみが変更されることを検証する
        self.assertEqual(updated_folder.id, folder.id)
        self.assertEqual(updated_folder.parent_id, folder.parent_id)
        self.assertEqual(updated_folder.uuid, folder.uuid)
        self.assertEqual(updated_folder.path, root.path / '新しいフォルダ')
        self.assertEqual(updated_folder.type, folder.type)
        self.assertEqual(updated_folder.label, '新しいフォルダ')
        self.assertEqual(updated_folder.creator, self.USER1)
        self.assertEqual(updated_folder.modifier, self.USER2)
        self.assertEqual(updated_folder.created_at, folder.created_at)
        self.assertIsNotNone(updated_folder.modified_at)
        # 作成したフォルダを削除する
        folder.delete()

    async def test_cannot_move_folder_into_inner(self):
        """
        フォルダを自身の中に移動できないこと
        """
        # ルートデータストアを取得する
        root = self.finder.data.load_root()
        # ルートデータストアの直下にフォルダ1を作成する
        folder1 = self.save_folder(root, 'Apple')
        # フォルダ1の直下にフォルダ2を作成する
        folder2 = self.save_folder(folder1, 'iMac')

        # 作成を確定する
        self.finder.end()

        # 移動先に、移動元のフォルダの子フォルダを指定したら例外を送出すること
        with self.assertRaises(OSError):
            folder1.move(folder2.uuid)

        # Rollbackを確定する
        self.finder.end()

        # 移動が失敗した場合はDBは更新されていないこと
        self.assertEqual(folder1.created_at, folder1.modified_at)
        self.assertEqual(folder2.created_at, folder2.modified_at)
        self.assertIsNone(folder1.prev_parent_id)

        # 例外送出によりSQLAlchemyのSessionがRollbackされるため
        # Datumの参照権限がNoneになる、そのため再読み込みする
        folder1 = folder1.reload()
        folder2 = folder2.reload()

        # 作成したフォルダを削除する
        folder2.delete()
        folder1.delete()

    async def test_save_folder(self):
        """
        フォルダを作成する
        """
        # ルートデータストアを取得する
        root = self.finder.data.load_root()
        # ルートデータストアの直下にフォルダを作成する
        folder = self.save_folder(root, 'フォルダ')
        # 作成したフォルダの値を検証する
        self.assertIsNotNone(folder.id)
        self.assertEqual(folder.parent_id, root.id)
        self.assertIsNotNone(folder.uuid)
        self.assertEqual(folder.path, root.path / 'フォルダ')
        self.assertEqual(folder.type, 'folder')
        self.assertEqual(folder.label, 'フォルダ')
        self.assertEqual(folder.creator, self.USER1)
        self.assertEqual(folder.modifier, self.USER1)
        self.assertEqual(folder.creator, folder.modifier)
        self.assertIsNotNone(folder.created_at)
        self.assertIsNotNone(folder.modified_at)
        self.assertEqual(folder.created_at, folder.modified_at)
        # 作成したフォルダを削除する
        folder.delete()


    async def test_get_rfolder(self):
        """
        リモートフォルダを取得する
        """
        try:
            # ルートデータストアを取得する
            root = self.finder.data.load_root()
            # ルートデータストアの直下にリモートフォルダを作成する
            conn = RemoteFolderConn(self.conn_json)
            folder = self.save_rfolder(root, 'リモートフォルダ', conn)
            # 取得したフォルダの値を検証する
            self.assertIsNotNone(folder.id)
            self.assertEqual(folder.parent_id, root.id)
            self.assertIsNotNone(folder.uuid)
            self.assertEqual(folder.path, root.path / 'リモートフォルダ')
            self.assertEqual(folder.type, 'rfolder')
            self.assertEqual(folder.label, 'リモートフォルダ')
            self.assertEqual(folder.creator, self.USER1)
            self.assertEqual(folder.modifier, self.USER1)
            self.assertIsNotNone(folder.created_at)
            self.assertIsNotNone(folder.modified_at)
        finally:
            # 作成したフォルダを削除する
            folder.delete()

    # @unittest.skip
    async def test_update_rfolder(self):
        """
        リモートフォルダのラベルを変更する
        """
        try:
            # ルートデータストアを取得する
            root = self.finder.data.load_root()
            # ルートデータストアの直下にリモートフォルダを作成する
            conn = RemoteFolderConn(self.conn_json)
            folder = self.save_rfolder(root, 'リモートフォルダ2', conn)
            # 作成したフォルダのラベルを変更する
            folder.update_data('新しいリモートフォルダ2', conn, self.USER2)
            # ラベルとディレクトリパスのみが変更されることを検証する
            self.assertEqual(folder.id, folder.id)
            self.assertEqual(folder.parent_id, folder.parent_id)
            self.assertEqual(folder.uuid, folder.uuid)
            # ラベル名を変更してもマウントポイントは変わらない
            self.assertEqual(folder.path, root.path / 'リモートフォルダ2')
            self.assertEqual(folder.type, folder.type)
            self.assertEqual(folder.label, '新しいリモートフォルダ2')
            self.assertEqual(folder.creator, self.USER1)
            self.assertEqual(folder.modifier, self.USER2)
            self.assertEqual(folder.created_at, folder.created_at)
            self.assertIsNotNone(folder.modified_at)
        finally:
            # 作成したフォルダを削除する
            folder.delete()


    @unittest.skip('AWS S3のパスワードないのでエラーになる')
    async def test_get_awss3(self):
        """
        AWS S3フォルダを取得する
        """
        try:
            # ルートデータストアを取得する
            root = self.finder.data.load_root()
            # ルートデータストアの直下にAWS S3フォルダを作成する
            folder = root.create_awss3('S3フォルダ1', 'streamcat-test')
            folder.save()
            folder.reload()

            # 作成したAWS S3フォルダを取得する
            self.finder.data.find_by_uuid(folder.uuid)

            # 取得したフォルダの値を検証する
            self.assertIsNotNone(folder.id)
            self.assertEqual(folder.parent_id, root.id)
            self.assertIsNotNone(folder.uuid)
            self.assertEqual(folder.path, root.path / 'S3フォルダ1')
            self.assertEqual(folder.type, 'awss3')
            self.assertEqual(folder.label, 'S3フォルダ1')
            self.assertEqual(folder.creator, self.USER1)
            self.assertEqual(folder.modifier, self.USER1)
            self.assertIsNotNone(folder.created_at)
            self.assertIsNotNone(folder.modified_at)
        finally:
            # 作成したフォルダを削除する
            folder.delete()

    @unittest.skip('AWS S3のパスワードないのでエラーになる')
    async def test_update_awss3(self):
        """
        AWS S3フォルダのラベルを変更する
        """
        try:
            # ルートデータストアを取得する
            root = self.finder.data.load_root()
            # ルートデータストアの直下にAWS S3フォルダを作成する
            folder = root.create_awss3('S3フォルダ2', 'streamcat-test')
            folder.save()
            folder.reload()

            # 作成したフォルダのラベルを変更する
            updated_folder = folder.update_data('新しいS3フォルダ', 'streamcat-test', self.USER2)

            # ラベルとディレクトリパスのみが変更されることを検証する
            self.assertEqual(updated_folder.id, folder.id)
            self.assertEqual(updated_folder.parent_id, folder.parent_id)
            self.assertEqual(updated_folder.uuid, folder.uuid)
            self.assertEqual(updated_folder.path, root.path / '新しいS3フォルダ')
            self.assertEqual(updated_folder.type, folder.type)
            self.assertEqual(updated_folder.label, '新しいS3フォルダ')
            self.assertEqual(updated_folder.creator, self.USER1)
            self.assertEqual(updated_folder.modifier, self.USER2)
            self.assertEqual(updated_folder.created_at, folder.created_at)
            self.assertIsNotNone(updated_folder.modified_at)
        finally:
            # 作成したフォルダを削除する
            folder.delete()

    @unittest.skip('AWS S3のパスワードないのでエラーになる')
    async def test_save_awss3(self):
        """
        AWS S3フォルダを作成する
        """
        try:
            # ルートデータストアを取得する
            root = self.finder.data.load_root()
            # ルートデータストアの直下にAWS S3フォルダを作成する
            folder = root.create_awss3('S3フォルダ3', 'streamcat-test')
            folder.save()
            folder.reload()

            # 作成したフォルダの値を検証する
            self.assertIsNotNone(folder.id)
            self.assertEqual(folder.parent_id, root.id)
            self.assertIsNotNone(folder.uuid)
            self.assertEqual(folder.path, root.path / 'S3フォルダ3')
            self.assertEqual(folder.type, 'awss3')
            self.assertEqual(folder.label, 'S3フォルダ3')
            self.assertEqual(folder.creator, self.USER1)
            self.assertEqual(folder.modifier, self.USER1)
            self.assertEqual(folder.creator, folder.modifier)
            self.assertIsNotNone(folder.created_at)
            self.assertIsNotNone(folder.modified_at)
            self.assertEqual(folder.created_at, folder.modified_at)
        finally:
            # 作成したフォルダを削除する
            folder.delete()


    async def test_get_frame(self):
        """
        フレームを取得する
        """
        # ルートデータストアを取得する
        root = self.finder.data.load_root()
        root_path = root.path
        # フレームデータを格納するファイルを作成する
        self.save(root_path / 'aaaa.csv')
        # ルートデータストアの直下にフレームを作成する
        frame = self.save_frame(root, 'フレームデータ', root_path / 'aaaa.csv')
        # 作成したフレームを取得する
        frame = self.finder.data.find_by_uuid(frame.uuid)
        # 作成したフレームの値を検証する
        self.assertIsNotNone(frame.id)
        self.assertEqual(frame.parent_id, root.id)
        self.assertIsNotNone(frame.uuid)
        self.assertEqual(frame.path, root_path / 'aaaa.csv')
        self.assertEqual(frame.type, 'frame')
        self.assertEqual(frame.label, 'フレームデータ')
        self.assertEqual(frame.creator, self.USER1)
        self.assertEqual(frame.modifier, self.USER1)
        self.assertEqual(frame.creator, frame.modifier)
        self.assertIsNotNone(frame.created_at)
        self.assertIsNotNone(frame.modified_at)
        self.assertEqual(frame.created_at, frame.modified_at)
        # 作成したフレームを削除する
        frame.delete()

    async def test_update_frame(self):
        """
        フレームのラベルを変更する
        """
        # ルートデータストアを取得する
        root = self.finder.data.load_root()
        root_path = root.path
        # フレームデータを格納するファイルを作成する
        self.save(root_path / 'aaaa1.csv')
        # ルートデータストアの直下にフレームを作成する
        frame = self.save_frame(root, 'フレームデータ', root_path / 'aaaa1.csv')
        # 作成したフレームのラベルを変更する
        updated_frame = frame.update_label('新しいフレームデータ', self.USER2)
        # ラベルとディレクトリパスのみが変更されることを検証する
        self.assertEqual(updated_frame.id, frame.id)
        self.assertEqual(updated_frame.parent_id, frame.parent_id)
        self.assertEqual(updated_frame.uuid, frame.uuid)
        # self.assertEqual(updated_frame.path, os.path.join(root.path, '新しいフレームデータ'))
        self.assertEqual(updated_frame.type, frame.type)
        self.assertEqual(updated_frame.label, '新しいフレームデータ')
        self.assertEqual(frame.creator, self.USER1)
        self.assertEqual(frame.modifier, self.USER2)
        self.assertEqual(updated_frame.created_at, frame.created_at)
        self.assertIsNotNone(updated_frame.modified_at)
        # 作成したフレームを削除する
        updated_frame.delete()

    async def test_save_frame(self):
        """
        フレームを追加する
        """
        # ルートデータストアを取得する
        root = self.finder.data.load_root()
        root_path = root.path
        # フレームデータを格納するファイルを作成する
        self.save(root_path / 'aaaa2.csv')
        # ルートデータストアの直下にフレームを作成する
        frame = self.save_frame(root, 'フレームデータ', root_path / 'aaaa2.csv')
        # 作成したフレームの値を検証する
        self.assertIsNotNone(frame.id)
        self.assertEqual(frame.parent_id, root.id)
        self.assertIsNotNone(frame.uuid)
        self.assertEqual(frame.path, root_path / 'aaaa2.csv')
        self.assertEqual(frame.type, 'frame')
        self.assertEqual(frame.label, 'フレームデータ')
        self.assertEqual(frame.creator, self.USER1)
        self.assertEqual(frame.modifier, self.USER1)
        self.assertEqual(frame.creator, frame.modifier)
        self.assertIsNotNone(frame.created_at)
        self.assertIsNotNone(frame.modified_at)
        self.assertEqual(frame.created_at, frame.modified_at)
        # 作成したフレームを削除する
        frame.delete()

    async def test_save2_frame(self):
        """
        フレームを作成する
        """
        # ルートデータストアを取得する
        root = self.finder.data.load_root()
        root_path = root.path
        # フレームデータを格納するファイルを作成する
        self.save(root_path / 'aaaa3.csv')
        with open(root_path / 'aaaa3.csv', mode='rb') as stream:
            # ルートデータストアの直下にフレームを作成する
            frame = self.save2_frame(root, 'フレームデータ', stream)
            
        # 作成したフレームの値を検証する
        self.assertIsNotNone(frame.id)
        self.assertEqual(frame.parent_id, root.id)
        self.assertIsNotNone(frame.uuid)
        # self.assertEqual(frame.path, os.path.join(root.path, 'フレームデータ'))
        self.assertEqual(frame.type, 'frame')
        self.assertEqual(frame.label, 'フレームデータ')
        self.assertEqual(frame.creator, self.USER1)
        self.assertEqual(frame.modifier, self.USER1)
        self.assertEqual(frame.creator, frame.modifier)
        self.assertIsNotNone(frame.created_at)
        self.assertIsNotNone(frame.modified_at)
        self.assertEqual(frame.created_at, frame.modified_at)
        # 作成したフレームを削除する
        frame.delete()
        # 作成したファイルを削除する
        self.delete(root_path / 'aaaa3.csv')


    async def test_get_flow(self):
        """
        フローを取得する
        """
        # ルートデータストアを取得する
        root = self.finder.data.load_root()
        root_path = root.path
        # フレームデータを格納するファイルを作成する
        self.save(root_path / 'frame_for_flow.csv')
        # ルートデータストアの直下にフレームを作成する
        frame = self.save_frame(root, 'フレームデータ',
                                   root_path / 'frame_for_flow.csv')
        # フローデータを作成する
        flow_json = {
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
        flow = self.save_flow(root, 'フロー', flow_json)
        # 作成したフローを取得する
        flow = self.finder.data.find_by_uuid(flow.uuid)
        # 作成したフローの値を検証する
        self.assertIsNotNone(flow.id)
        self.assertEqual(flow.parent_id, root.id)
        self.assertIsNotNone(flow.uuid)
        self.assertIsNone(flow.path)
        self.assertEqual(flow.type, 'flow')
        self.assertEqual(flow.label, 'フロー')
        self.assertEqual(flow.flow_data.to_json(), flow_json)
        self.assertEqual(flow.creator, self.USER1)
        self.assertEqual(flow.modifier, self.USER1)
        self.assertEqual(flow.creator, flow.modifier)
        self.assertIsNotNone(flow.created_at)
        self.assertIsNotNone(flow.modified_at)
        self.assertEqual(flow.created_at, flow.modified_at)
        # 作成したフローを削除する
        flow.delete()
        # 作成したファイルを削除する
        self.delete(root_path / 'frame_for_flow.csv')

    async def test_update_flow(self):
        """
        フローを変更する
        """
        # ルートデータストアを取得する
        root = self.finder.data.load_root()
        root_path = root.path
        # フレームデータを格納するファイルを作成する
        self.save(root_path / 'frame_for_flow2.csv')
        # ルートデータストアの直下にフレームを作成する
        frame = self.save_frame(root, 'フレームデータ',
                                   root_path / 'frame_for_flow2.csv')
        # フローデータを作成する
        flow_json = {
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
        flow = self.save_flow(root, 'フロー', flow_json)

        new_flow_json = {
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
        from streamcat.store import FlowData
        new_flow_data = FlowData(new_flow_json)
        updated_flow = flow.update_data('新しいフロー', new_flow_data, modifier=self.USER2)

        # ラベルとディレクトリパスのみが変更されることを検証する
        self.assertEqual(updated_flow.id, flow.id)
        self.assertEqual(updated_flow.parent_id, flow.parent_id)
        self.assertEqual(updated_flow.uuid, flow.uuid)
        self.assertIsNone(updated_flow.path)
        self.assertEqual(updated_flow.type, flow.type)
        self.assertEqual(updated_flow.label, '新しいフロー')
        self.assertEqual(updated_flow.flow_data, new_flow_data)
        self.assertEqual(updated_flow.creator, self.USER1)
        self.assertEqual(updated_flow.modifier, self.USER2)
        self.assertEqual(updated_flow.created_at, flow.created_at)
        self.assertIsNotNone(updated_flow.modified_at)
        # 作成したフレームを削除する
        updated_flow.delete()
        # 作成したファイルを削除する
        self.delete(root_path / 'frame_for_flow2.csv')

    async def test_save_flow(self):
        """
        フローを追加する
        """
        # ルートデータストアを取得する
        root = self.finder.data.load_root()
        # フローデータを作成する
        flow_json = {
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
        flow = self.save_flow(root, 'フロー', flow_json)

        # 作成したフレームの値を検証する
        self.assertIsNotNone(flow.id)
        self.assertEqual(flow.parent_id, root.id)
        self.assertIsNotNone(flow.uuid)
        self.assertIsNone(flow.path)
        self.assertEqual(flow.type, 'flow')
        self.assertEqual(flow.label, 'フロー')
        self.assertEqual(flow.creator, self.USER1)
        self.assertEqual(flow.modifier, self.USER1)
        self.assertEqual(flow.creator, flow.modifier)
        self.assertIsNotNone(flow.created_at)
        self.assertIsNotNone(flow.modified_at)
        self.assertEqual(flow.created_at, flow.modified_at)
        # 作成したフレームを削除する
        flow.delete()


    async def test_get_no_folder(self):
        """
        存在しないDatumを取得しようとすると例外を送出する
        """
        with self.assertRaises(Exception) as e:
            self.finder.data.find_by_uuid('00000000-0000-0000-0000-000000000000')

    async def test_update_to_illigal_folder_name(self):
        """
        '/'や'\0'を含むディレクトリパスは、それぞれ'／'と''に変換される
        """
        # ルートデータストアを取得する
        root = self.finder.data.load_root()
        # ルートデータストアの直下にフォルダを作成する
        folder = self.save_folder(root, 'フォルダB')
        # 作成したフォルダのラベルを変更する
        updated_folder = folder.update_label('/新しい\0フォルダ/', self.USER2)
        # ラベルとディレクトリパスでは'/'や'\0'は使われない
        self.assertEqual(updated_folder.path, root.path / '／新しいフォルダ／')
        self.assertEqual(updated_folder.label, '/新しいフォルダ/')
        # 作成したフォルダを削除する
        folder.delete()

    async def test_update_folder_refer_to_file_other_frame_refering(self):
        """
        二つのフォルダが一つのディレクトリに対応している場合に、
        何れか一つのフォルダのラベル名を変更しても、不整合は発生しない
        """
        pass

    async def test_update_frame_refer_to_file_other_frame_refering(self):
        """
        二つのフレームが一つのCSVファイルに対応している場合に、
        何れか一つのフレームのラベル名を変更しても、不整合は発生しない
        """
        # ルートデータストアを取得する
        root = self.finder.data.load_root()
        root_path = root.path
        # フレームデータを格納するファイルを作成する
        self.save(root_path / 'abc.csv')
        # ルートデータストアの直下にフレーム1を作成する
        frame1 = self.save_frame(root, 'フレームデータ', root_path / 'abc.csv')
        # ルートデータストアの直下にフレーム2を作成する
        frame2 = self.save_frame(root, 'フレームデータ', root_path / 'abc.csv')
        # フレーム1のラベル名を変更する
        frame1.update_label('新しいフレームデータ1', self.USER2)
        # フレーム1のラベル名の変更に従って、CSVファイル名が変更されていることを検証する
        self.assertEqual(frame1.path, root_path / '新しいフレームデータ1')
        self.assertEqual(frame2.path, root_path / '新しいフレームデータ1')
        self.assertTrue (os.path.isfile(root_path / '新しいフレームデータ1'))
        self.assertFalse(os.path.isfile(root_path / 'abc.csv'))
        # フレーム1を削除する
        frame1.delete()
        # フレーム2を削除する
        frame2.delete()

    async def test_frame_file_collision(self):
        """
        3つのフレームでCSVファイル名が重複した場合は、異なるCSVファイル名が使われる
        """
        # ルートデータストアを取得する
        root = self.finder.data.load_root()
        root_path = root.path
        # フレームデータを格納するファイルを作成する
        self.save(root_path / 'bar.csv')
        with open(root_path / 'bar.csv', mode='rb') as stream:
            # ルートデータストアの直下にフレーム1を作成する
            frame1 = self.save2_frame(root, 'フレームデータ', stream)
            # ルートデータストアの直下にフレーム2を作成する
            frame2 = self.save2_frame(root, 'フレームデータ', stream)
            # ルートデータストアの直下にフレーム3を作成する
            frame3 = self.save2_frame(root, 'フレームデータ', stream)
        # フレーム2に対応するファイルパスはフレームデータ_1であることを検証する
        self.assertEqual(frame1.path, root_path / 'フレームデータ')
        self.assertEqual(frame2.path, root_path / 'フレームデータ_1')
        self.assertEqual(frame3.path, root_path / 'フレームデータ_2')
        # フレーム1を削除する
        frame1.delete()
        # フレーム2を削除する
        frame2.delete()
        # フレーム3を削除する
        frame3.delete()
        # 作成したファイルを削除する
        self.delete(root_path / 'bar.csv')

