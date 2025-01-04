import io
from streamcat.store import Mountable, RemoteFolderConn
from .test_case_base import TestCaseBase

class MoveTest(TestCaseBase):
    """
    移動処理を検証する
    """

    conn_json = {
        'protocol' : 'smb',
        'hostname' : '18.178.64.116',
        'domain'   : 'WORKGROUP',
        'directory': 'share',
        'userId'  : 'samba',
        'password' : 'kskanalytics'
    }
    remote_folder_conn = RemoteFolderConn(conn_json)

    async def test_move_child_data_has_escape_chars(self):
        """
        ファイル名にエスケープ文字が含まれるFrameを含むフォルダを移動できること
        """
        # ルートフォルダを取得する
        root = self.factory3.data.load_root()

        # ルートフォルダの下にプロジェクト1を作成する
        project1 = root.create_project_folder('京橋')
        project1.save()

        # ルートフォルダの下にプロジェクト2を作成する
        project2 = root.create_project_folder('天満橋')
        project2.save()

        # プロジェクト1の下にフォルダ1を作成する
        folder1 = project1.create_folder(r'^FO\LDER-%-_-/')
        folder1.save()

        # フォルダ1の下にFrameを作成する
        frame1 = folder1.create_frame(r'^FR\AME-%-_-/', io.BytesIO(b'okeihan'))
        frame1.save()
        frame1.reload()

        # プロジェクト2の下にフォルダを作成する
        folder2 = project2.create_folder('私の\\フォ\\nル&ダ*')
        folder2.save()

        # フォルダ2の下にFrameを作成する
        frame2 = folder2.create_frame('私の\\フレー\\nム', io.BytesIO(b'okeihan'))
        frame2.save()
        frame2.reload()

        # 作成を確定する
        self.factory3.end()

        # フォルダ1を移動する
        folder1.move(project2.uuid)

        # フォルダ1の移動に成功すること
        # (labelに含まれる'/'はpathに反映される時に'／'に変換される)
        self.assertEqual(folder1.path, root.path / '天満橋' / r'^FO\LDER-%-_-／')
        self.assertEqual(frame1.path, folder1.path / r'^FR\AME-%-_-／')

        # フォルダ2を移動する
        folder2.move(project2.uuid)

        # フォルダ2の移動に成功すること
        self.assertEqual(folder2.path, root.path / '天満橋' / '私の\\フォ\\nル&ダ*')
        self.assertEqual(frame2.path, folder2.path / '私の\\フレー\\nム')

        # ファイルを削除する
        frame2.delete()
        frame1.delete()

        # フォルダを削除する
        folder2.delete()
        folder1.delete()

        # プロジェクトを削除する
        project2.delete()
        project1.delete()

    async def test_move_remote_folder(self):
        """
        マウント状態のリモートフォルダを移動できないこと
        """
        # ルートフォルダを取得する
        root = self.factory3.data.load_root()

        # ルートフォルダの下にプロジェクト1を作成する
        project1 = root.create_project_folder('あいうえお')
        project1.save()

        # ルートフォルダの下にプロジェクト2を作成する
        project2 = root.create_project_folder('かきくけこ')
        project2.save()

        # プロジェクトの下にリモートフォルダを作成する
        remote_folder = project1.create_remote_folder('リモートフォルダ', self.remote_folder_conn)
        remote_folder.save()
        remote_folder.reload()

        # 作成を確定する
        self.factory3.end()

        # 
        # pathを参照してリモートフォルダをマウントする
        # 
        self.assertEqual(remote_folder.path, root.path / 'あいうえお' / 'リモートフォルダ')
        self.assertTrue(Mountable.is_mount(remote_folder._path))

        # マウント中のリモートフォルダは移動できないこと
        with self.assertRaises(Exception):
            remote_folder.move(project2.uuid)

        # 引き続きマウント状態であること
        # NOTE: pathプロパティを参照しただけでマウントされることに注意
        self.assertTrue(Mountable.is_mount(remote_folder._path))
        # リモートフォルダは移動されていないこと
        self.assertEqual(remote_folder.parent_id, project1.id)
        self.assertEqual(remote_folder.parent_uuid, project1.uuid)
        self.assertEqual(remote_folder._path, root.path / 'あいうえお' / 'リモートフォルダ')
        # マウントポイントのディレクトリが移動されていないこと
        self.assertTrue(remote_folder._path.is_dir())
        self.assertEqual(remote_folder.created_at, remote_folder.modified_at)

        # 移動を確定する
        self.factory3.end()

        # 
        # マウントを解除する
        # 
        remote_folder.unmount()

        # マウント解除後のリモートフォルダは移動できること
        remote_folder.move(project2.uuid)

        # 引き続きマウント解除状態であること
        # NOTE: pathプロパティを参照しただけでマウントされることに注意
        self.assertFalse(Mountable.is_mount(remote_folder._path))
        # リモートフォルダが移動されていること
        self.assertEqual(remote_folder.parent_id, project2.id)
        self.assertEqual(remote_folder.parent_uuid, project2.uuid)
        self.assertEqual(remote_folder._path, root.path / 'かきくけこ' / 'リモートフォルダ')
        # マウントポイントのディレクトリが移動されていること
        self.assertTrue(remote_folder._path.is_dir())
        self.assertNotEqual(remote_folder.created_at, remote_folder.modified_at)

        # リモートフォルダを削除する
        remote_folder.delete()

        # プロジェクトを削除する
        project2.delete()
        project1.delete()

    async def test_trash_remote_folder_in_folder(self):
        """
        マウント状態のリモートフォルダを含むフォルダをゴミ箱に捨てるとマウントが解除されること
        """
        # ルートフォルダを取得する
        root = self.factory3.data.load_root()

        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('私のプロジェクト')
        project.save()

        # プロジェクトの下にフォルダを作成する
        folder = project.create_folder('私のフォルダ')
        folder.save()

        # フォルダの下にサブフォルダを作成する
        sub_folder = folder.create_folder('私のサブフォルダ')
        sub_folder.save()

        # サブフォルダの下にリモートフォルダを作成する
        remote_folder = sub_folder.create_remote_folder('私のリモートフォルダ', self.remote_folder_conn)
        remote_folder.save()
        remote_folder.reload()

        # 作成を確定する
        self.factory3.end()

        # 
        # pathを参照してリモートフォルダをマウントする
        # 
        self.assertEqual(remote_folder.path, root.path/'私のプロジェクト'/'私のフォルダ'/'私のサブフォルダ'/'私のリモートフォルダ')
        self.assertTrue(Mountable.is_mount(remote_folder._path))

        # 
        # フォルダをゴミ箱にほかす
        # 
        folder.throw_away()

        # リモートフォルダがゴミ箱にほかされていること
        self.assertTrue(self.factory3.data.trashed(remote_folder.uuid))
        # マウントが解除されていること
        self.assertFalse(Mountable.is_mount(remote_folder._path))
        self.assertEqual(remote_folder._path, root.path/'ゴミ箱'/'私のフォルダ'/'私のサブフォルダ'/'私のリモートフォルダ')
        # マウントポイントのディレクトリが移動されていること
        self.assertTrue(remote_folder._path.is_dir())
        self.assertNotEqual(remote_folder.created_at, remote_folder.modified_at)

        # 
        # フォルダをゴミ箱から戻す
        # 
        folder.put_back()

        # リモートフォルダがゴミ箱に存在しないこと
        self.assertFalse(self.factory3.data.trashed(remote_folder.uuid))
        # マウントは解除状態のままであること
        self.assertFalse(Mountable.is_mount(remote_folder._path))
        self.assertEqual(remote_folder._path, root.path/'私のプロジェクト'/'私のフォルダ'/'私のサブフォルダ'/'私のリモートフォルダ')
        # マウントポイントのディレクトリが移動されていること
        self.assertTrue(remote_folder._path.is_dir())
        self.assertNotEqual(remote_folder.created_at, remote_folder.modified_at)

        # リモートフォルダを削除する
        remote_folder.delete()

        # プロジェクトを削除する
        sub_folder.delete()
        folder.delete()
        project.delete()

    async def test_move_duplicated_frames(self):
        """
        複製したFrameのうち片方を移動すると、対応する実ファイルも移動されること
        """
        # ルートフォルダを取得する
        root = self.factory3.data.load_root()

        # ルートフォルダの下にプロジェクト1を作成する
        project1 = root.create_project_folder('丹波橋')
        project1.save()

        # ルートフォルダの下にプロジェクト2を作成する
        project2 = root.create_project_folder('中書島')
        project2.save()

        # ルートフォルダの下にプロジェクト3を作成する
        project3 = root.create_project_folder('葛葉')
        project3.save()

        # プロジェクト1の下にFrameを作成する
        frame = project1.create_frame('伏見桃山', io.BytesIO(b'okeihan'))
        frame.save()
        frame.reload()

        # Frameを複製する
        duplicated_frame = frame.duplicate('墨染')
        duplicated_frame.reload()

        # 作成を確定する
        self.factory3.end()

        # 複製したFrameと元のFrameに対応するファイルは同じであること
        # (Frameを複製しても対応するファイルは共有する)
        self.assertEqual(frame.path, duplicated_frame.path)
        self.assertEqual(frame.created_at, frame.modified_at)
        self.assertEqual(duplicated_frame.created_at, duplicated_frame.modified_at)

        # 複製元Frameをプロジェクト2へ移動する
        frame.move(project2.uuid)

        # 複製元Frameの移動によって実ファイルが移動されること
        self.assertEqual(frame.path, root.path / '中書島' / '伏見桃山')
        self.assertNotEqual(frame.created_at, frame.modified_at)
        self.assertEqual(duplicated_frame.path, frame.path)
        self.assertNotEqual(duplicated_frame.created_at, duplicated_frame.modified_at)

        # 複製Frameをプロジェクト3へ移動する
        duplicated_frame.move(project3.uuid)

        # 複製Frameの移動によって実ファイルが移動されること
        self.assertEqual(duplicated_frame.path, root.path / '葛葉' / '伏見桃山')
        self.assertNotEqual(frame.created_at, frame.modified_at)
        self.assertEqual(duplicated_frame.path, frame.path)
        self.assertNotEqual(duplicated_frame.created_at, duplicated_frame.modified_at)

        # Frameを削除する
        duplicated_frame.delete()
        frame.delete()

        # プロジェクトを削除する
        project3.delete()
        project2.delete()
        project1.delete()

    async def test_move_duplicated_remote_folder(self):
        """
        複製したリモートフォルダのうち片方を移動しても、リモートフォルダに対応するファイルは移動されないこと
        """
        # ルートフォルダを取得する
        root = self.factory3.data.load_root()

        # ルートフォルダの下にプロジェクト1を作成する
        project1 = root.create_project_folder('PRJ1')
        project1.save()

        # ルートフォルダの下にプロジェクト2を作成する
        project2 = root.create_project_folder('PRJ2')
        project2.save()

        # プロジェクト1の下にリモートフォルダを作成する
        remote_folder = project1.create_remote_folder('REMOTE_FOLDER', self.remote_folder_conn)
        remote_folder.save()

        # リモートフォルダを複製する
        duplicated_remote_folder = remote_folder.duplicate('REMOTE_FOLDER_COPY')
        duplicated_remote_folder.reload()

        # 作成を確定する
        self.factory3.end()

        # 複製したリモートフォルダと元のリモートフォルダに対応するファイルは異なること
        # (リモートフォルダを複製すると対応する実ディレクトリを新たに作成する)
        self.assertEqual(remote_folder.path, root.path / 'PRJ1' / 'REMOTE_FOLDER')
        self.assertEqual(duplicated_remote_folder.path, root.path / 'PRJ1' / 'REMOTE_FOLDER_COPY')
        self.assertNotEqual(remote_folder.path, duplicated_remote_folder.path)

        # 移動前にマウント解除する
        remote_folder.unmount()

        # 複製元リモートフォルダをプロジェクト2へ移動する
        remote_folder.move(project2.uuid)

        # 複製元リモートフォルダの移動によって複製したリモートフォルダの実ディレクトリが移動されないこと
        self.assertEqual(remote_folder.path, root.path / 'PRJ2' / 'REMOTE_FOLDER')
        self.assertEqual(duplicated_remote_folder.path, root.path / 'PRJ1' / 'REMOTE_FOLDER_COPY')

        # リモートフォルダを削除する
        remote_folder.delete()
        duplicated_remote_folder.delete()

        # プロジェクトを削除する
        project2.delete()
        project1.delete()

    async def test_move_folder_contains_frames(self):
        """
        Frameを含むフォルダを移動すると、対応する実ファイルも移動されること
        """
        # ルートフォルダを取得する
        root = self.factory3.data.load_root()

        # ルートフォルダの下にプロジェクト1を作成する
        project1 = root.create_project_folder('枚方市')
        project1.save()

        # ルートフォルダの下にプロジェクト2を作成する
        project2 = root.create_project_folder('香里園')
        project2.save()

        # プロジェクト1の下にフォルダを作成する
        folder = project1.create_folder('枚方公園')
        folder.save()

        # プロジェクト1の下にFrameを作成する
        frame1 = folder.create_frame('石清水八幡宮', io.BytesIO(b'okeihan1'))
        frame1.save()
        frame1.reload()

        # プロジェクト1の下にFrameを作成する
        frame2 = folder.create_frame('橋本', io.BytesIO(b'okeihan2'))
        frame2.save()
        frame2.reload()

        # プロジェクト1の下にFrameを作成する
        frame3 = folder.create_frame('淀', io.BytesIO(b'okeihan3'))
        frame3.save()
        frame3.reload()

        # 作成を確定する
        self.factory3.end()

        # フォルダを移動する
        folder.move(project2.uuid)

        # フォルダの移動によって実ファイルが移動されること
        self.assertEqual(folder.path, root.path / '香里園' / '枚方公園')
        self.assertEqual(frame1.path, folder.path / '石清水八幡宮')
        self.assertEqual(frame2.path, folder.path / '橋本')
        self.assertEqual(frame3.path, folder.path / '淀')

        # ファイルを削除する
        frame3.delete()
        frame2.delete()
        frame1.delete()

        # フォルダを削除する
        folder.delete()

        # プロジェクトを削除する
        project2.delete()
        project1.delete()

    async def test_move_folder_contains_any_type_data(self):
        """
        Document,Folderを含むフォルダを移動すると、対応する実ファイルも移動されること
        """
        # ルートフォルダを取得する
        root = self.factory3.data.load_root()

        # ルートフォルダの下にプロジェクト1を作成する
        project1 = root.create_project_folder('京橋')
        project1.save()

        # ルートフォルダの下にプロジェクト2を作成する
        project2 = root.create_project_folder('天満橋')
        project2.save()

        # プロジェクト1の下にフォルダを作成する
        folder = project1.create_folder('香里園')
        folder.save()

        # プロジェクト1の下にDocumentを作成する
        document1 = folder.create_document('守口市', io.BytesIO(b'okeihan'))
        document1.save()

        # プロジェクト1の下にFolderを作成する
        subfolder = folder.create_folder('土井')
        subfolder.save()

        # プロジェクト1の下にDocumentを作成する
        document2 = subfolder.create_document('滝井', io.BytesIO(b'okeihan'))
        document2.save()

        # 作成を確定する
        self.factory3.end()

        # フォルダを移動する
        folder.move(project2.uuid)

        # フォルダの移動によって実ファイルが移動されること
        self.assertEqual(folder.path, root.path / '天満橋' / '香里園')
        self.assertEqual(document1.path, folder.path / '守口市')
        self.assertEqual(subfolder.path, folder.path / '土井')
        self.assertEqual(document2.path, subfolder.path / '滝井')

        # ファイルを削除する
        document2.delete()
        document1.delete()

        # フォルダを削除する
        subfolder.delete()
        folder.delete()

        # プロジェクトを削除する
        project2.delete()
        project1.delete()

    async def test_move_folder_contains_remote_folder(self):
        """
        リモートフォルダを含むフォルダは移動できないこと
        """
        # ルートフォルダを取得する
        root = self.factory3.data.load_root()

        # ルートフォルダの下にプロジェクト1を作成する
        project1 = root.create_project_folder('京橋')
        project1.save()

        # ルートフォルダの下にプロジェクト2を作成する
        project2 = root.create_project_folder('天満橋')
        project2.save()

        # プロジェクト1の下にフォルダを作成する
        folder = project1.create_folder('香里園')
        folder.save()

        # プロジェクト1の下にリモートフォルダを作成する
        remote_folder = folder.create_remote_folder('土井', self.remote_folder_conn)
        remote_folder.save()

        # 作成を確定する
        self.factory3.end()

        # 作成直後のリモートフォルダのマウントは解除状態であること
        self.assertFalse(Mountable.is_mount(remote_folder._path))

        # リモートフォルダはそのpathプロパティを参照するとMountされる
        self.assertEqual(remote_folder.path, root.path / '京橋' / '香里園' / '土井')

        # pathプロパティの参照によりマウント状態であること
        self.assertTrue(Mountable.is_mount(remote_folder._path))

        # マウント中のリモートフォルダを含むフォルダは移動できないこと
        with self.assertRaises(Exception):
            folder.move(project2.uuid)

        # ロールバックを確定する
        self.factory3.end()

        # フォルダの移動によって実ディレクトリが移動されないこと
        self.assertEqual(folder.path, root.path / '京橋' / '香里園')
        self.assertEqual(remote_folder.path, root.path / '京橋' / '香里園' / '土井')

        # マウント中のリモートフォルダが存在する場合はフォルダごと削除できないこと
        with self.assertRaises(Exception):  
            folder.delete()

        # フォルダを削除する
        remote_folder.delete()
        folder.delete()

        # プロジェクトを削除する
        project2.delete()
        project1.delete()

    async def test_move_to_self_inner_folder(self):
        """
        フォルダを自身の内部フォルダに移動できないこと
        """
        # ルートフォルダを取得する
        root = self.factory3.data.load_root()

        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('寝屋川市')
        project.save()

        # プロジェクトの下にフォルダを作成する
        folder = project.create_folder('FOLDER')
        folder.save()

        # フォルダの下にFrameを作成する
        frame = folder.create_frame('FRAME', io.BytesIO(b'okeihan'))
        frame.save()

        # フォルダの下にサブフォルダを作成する
        sub_folder = folder.create_folder('SUB_FOLDER')
        sub_folder.save()

        # 作成を確定する
        self.factory3.end()

        # フォルダを自身の内部フォルダに移動できないこと
        with self.assertRaises(Exception):
            # 例外送出時にDBへの変更はロールバックされる
            folder.move(sub_folder.uuid)

        # ロールバックを確定する
        self.factory3.end()

        # ロールバック後に参照権限の値が消えるので、ここで再取得する
        root.reload()
        project.reload()
        folder.reload()
        frame.reload()
        sub_folder.reload()

        # フォルダは移動されていないこと
        self.assertEqual(folder.parent_id, project.id)
        self.assertEqual(folder.parent_uuid, project.uuid)
        # # フォルダに対応する実ファイルは移動されていないこと
        self.assertEqual(folder.path, root.path / '寝屋川市' / 'FOLDER')
        self.assertEqual(folder.created_at, folder.modified_at)

        # フォルダの下に配置されたFrameも移動されていないこと
        self.assertEqual(frame.parent_id, folder.id)
        self.assertEqual(frame.parent_uuid, folder.uuid)
        self.assertEqual(frame.path, folder.path / 'FRAME')
        self.assertEqual(frame.created_at, frame.modified_at)

        # フォルダの下に配置されたサブフォルダも移動されていないこと
        self.assertEqual(sub_folder.parent_id, folder.id)
        self.assertEqual(sub_folder.parent_uuid, folder.uuid)
        self.assertEqual(sub_folder.path, folder.path / 'SUB_FOLDER')
        self.assertEqual(sub_folder.created_at, sub_folder.modified_at)

        # フォルダを削除する
        frame.delete()
        sub_folder.delete()
        folder.delete()

        # プロジェクトを削除する
        project.delete()

    async def test_move_then_delete_frame(self):
        """
        Frameをフォルダごと移動した後にFrameを削除できること
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()

        # ルートフォルダの下にプロジェクトAを作成する
        project_a = root.create_project_folder('PRJ_A')
        project_a.save()
        project_a.reload()

        # ルートフォルダの下にプロジェクトBを作成する
        project_b = root.create_project_folder('PRJ_B')
        project_b.save()
        project_b.reload()

        # プロジェクトAの下にフォルダを作成する
        folder = project_a.create_folder('MyFolder')
        folder.save()
        folder.reload()

        # フォルダの下にフレームを作成する
        frame = folder.create_frame('MyFrame', io.BytesIO(b'qerty'))
        frame.save()
        frame.reload()

        # フォルダをプロジェクトBに移動できること
        folder.move(project_b.uuid)
        self.assertEqual(folder.parent_id, project_b.id)

        # 変更を確定する
        self.factory2.end()

        # 
        # フレームを削除する
        # 
        # 以下のエラーが送出されないことを確認する
        #   sqlalchemy.orm.exc.ObjectDeletedError:
        #   Instance has been deleted, or its row is otherwise not present.
        frame.delete()

        # プロジェクトを削除する
        folder.delete()
        project_b.delete()
        project_a.delete()

    async def test_move_then_delete_folder(self):
        """
        フォルダをプロジェクトごと移動した後にフォルダを削除できること
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()

        # ルートフォルダの下にプロジェクトAを作成する
        project_a = root.create_project_folder('PRJ_A')
        project_a.save()
        project_a.reload()

        # ルートフォルダの下にプロジェクトBを作成する
        project_b = root.create_project_folder('PRJ_B')
        project_b.save()
        project_b.reload()

        # プロジェクトAの下にフォルダを作成する
        folder = project_a.create_folder('MyFolder')
        folder.save()
        folder.reload()

        # フォルダの下にサブフォルダを作成する
        sub_folder = folder.create_folder('MySubFolder')
        sub_folder.save()
        sub_folder.reload()

        # フォルダをプロジェクトBに移動できること
        folder.move(project_b.uuid)
        self.assertEqual(folder.parent_id, project_b.id)

        # 変更を確定する
        self.factory2.end()

        # 
        # サブフォルダを削除する
        # 
        # 以下のエラーが送出されないことを確認する
        #   sqlalchemy.orm.exc.ObjectDeletedError:
        #   Instance has been deleted, or its row is otherwise not present.
        sub_folder.delete()

        # プロジェクトを削除する
        folder.delete()
        project_b.delete()
        project_a.delete()

    async def test_move_then_delete_remote_folder(self):
        """
        リモートフォルダをプロジェクトごと移動した後にリモートフォルダを削除できること
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()

        # ルートフォルダの下にプロジェクトAを作成する
        project_a = root.create_project_folder('PRJ_A')
        project_a.save()
        project_a.reload()

        # ルートフォルダの下にプロジェクトBを作成する
        project_b = root.create_project_folder('PRJ_B')
        project_b.save()
        project_b.reload()

        # プロジェクトAの下にフォルダを作成する
        folder = project_a.create_folder('MyFolder')
        folder.save()
        folder.reload()

        # フォルダの下にリモートフォルダを作成する
        remote_folder = folder.create_remote_folder('MyRemoteFolder', self.remote_folder_conn)
        remote_folder.save()
        remote_folder.reload()

        # フォルダをプロジェクトBに移動できること
        folder.move(project_b.uuid)
        self.assertEqual(folder.parent_id, project_b.id)

        # 変更を確定する
        self.factory2.end()

        # 
        # リモートフォルダを削除する
        # 
        # 以下のエラーが送出されないことを確認する
        #   sqlalchemy.orm.exc.ObjectDeletedError:
        #   Instance has been deleted, or its row is otherwise not present.
        remote_folder.delete()

        # プロジェクトを削除する
        folder.delete()
        project_b.delete()
        project_a.delete()
