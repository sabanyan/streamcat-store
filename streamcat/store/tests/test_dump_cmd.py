import io
import pprint
import unittest
from streamcat.store import DatabaseConn, RemoteFolderConn
from streamcat.depo.std.commands import DumpCommand
from .test_case_base import TestCaseBase

class DumpTest(TestCaseBase, unittest.IsolatedAsyncioTestCase):
    """
    DumpCommandとRestoreCommandをテストする
    """
    conn_json = {
      'dbms'     : "postgresql",
      'hostname' : "kskp.cr4gfi5zl5xm.ap-northeast-1.rds.amazonaws.com", 
      'port'     : 5432, 
      'database' : "kskp", 
      'user_id'  : "kskp", 
      'password' : 'my-pass-word'
    }
    database_conn = DatabaseConn(conn_json)

    conn_json = {
        'protocol' : 'smb',
        'hostname' : "18.178.64.116",
        'domain'   : "WORKGROUP",
        'directory': "share",
        'user_id'  : "samba",
        'password' : "kskanalytics"
    }
    remote_folder_conn = RemoteFolderConn(conn_json)

    async def test_basic(self):
        """
        StreamCatのバックアップとリストアが実行できること
        FIXME: テストコードの実行環境でGET /dumpを呼び出すと、LOCK TABLEの発行時に
        "LOCK TABLE can only be used in transaction blocks"の例外が送出される。原因不明
        """
        # ルートを取得する
        root = self.finder2.data.load_root()

        # プロジェクトを作成する
        project = root.create_project_folder('徳川家康')
        project.save()

        # フォルダを作成する
        folder = project.create_folder('前田利家')
        folder.save()

        # データベースを作成する
        database = folder.create_database('毛利輝元', self.database_conn)
        database.save()

        # リモートフォルダを作成する
        rfolder = folder.create_remote_folder('宇喜多秀家', self.remote_folder_conn)
        rfolder.save()

        # フレームを作成する
        frame = folder.create_frame('上杉景勝', io.BytesIO(b'abcdef'))
        frame.save()

        # フローを作成する
        flow = folder.create_simple_flow('石田三成', frame)
        flow.save()

        # Dumpコマンドを実行する
        outs = DumpCommand().run({'datum_finder': self.finder0.data}, {})

        print(outs)

    async def test_auth(self):
        """
        システム管理者以外はバックアップとリストアが実行できないこと
        """

    async def test_invalid_file(self):
        """
        不正なDumpファイルでリストアを実行できないこと
        """

    async def test_dump_simultaneously(self):
        """
        同時にバックアップを実行できること
        """

    async def test_restore_simultaneously(self):
        """
        同時にリストアを実行できること
        """

    async def test_dump_restore_simultaneously(self):
        """
        同時にバックアップとリストアを実行できること
        """
