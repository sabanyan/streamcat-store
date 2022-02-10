import unittest
import pprint
import time
import io

from kskp.store import FlowData, DatabaseConn, RemoteFolderConn
from kskp.depo.std.commands import DumpCommand, RestoreCommand
from .test_case_base import TestCaseBase

class DumpTest(TestCaseBase):
    """
    DumpCommandとRestoreCommandをテストする
    """
    conn_json = {
      'dbms'     : "postgresql",
      'hostname' : "kskp.cr4gfi5zl5xm.ap-northeast-1.rds.amazonaws.com", 
      'port'     : 5432, 
      'database' : "kskp", 
      'user_id'  : "kskp", 
      'password' : r'J2-pH|%B'
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

    def test_basic(self):
        """
        StreamCatのバックアップとリストアが実行できること
        """
        # ルートを取得する
        root = self.factory2.data.load_root()

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
        outs = DumpCommand().run({'datum_factory': self.factory.data}, {})

        print(outs)

    def test_auth(self):
        """
        ユーザ管理者以外はバックアップとリストアが実行できないこと
        """

    def test_invalid_file(self):
        """
        不正なDumpファイルでリストアを実行できないこと
        """

    def test_dump_simultaneously(self):
        """
        同時にバックアップを実行できること
        """

    def test_restore_simultaneously(self):
        """
        同時にリストアを実行できること
        """

    def test_dump_restore_simultaneously(self):
        """
        同時にバックアップとリストアを実行できること
        """
