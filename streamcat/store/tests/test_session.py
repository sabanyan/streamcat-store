import pprint
import unittest
from .test_case_base import TestCaseBase
from streamcat.store import FlowData

class SessionTest(TestCaseBase, unittest.IsolatedAsyncioTestCase):
    """
    SQLAlchemyのSessionを検証する
    """

    async def test_rollback(self):
        """
        Datumの新規追加操作をRollBackできること
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()

        # ルートフォルダの下にプロジェクト1を作成する
        project1 = root.create_project_folder('Session-Test')
        project1.save()

        # フローを作成する
        flow1 = project1.create_flow('test', FlowData({}))
        flow1.save()

        # 作成を確定する
        self.factory2.end()

        # スケジュールを作成する
        trigger1 = {
            'type' : 'date',
            'date' : '2021-06-29 12:00:00'
        }
        schedule1 = project1.create_schedule('schedule1', flow1.uuid, trigger=trigger1)
        schedule1.save()

        # プロジェクト1、フローとスケジュールの作成をRollbackする
        self.factory2._session._session.rollback()
        self.factory2.end()

        # Rollbackによって各権限情報はNoneになる
        self.assertIsNone(project1.readable)
        self.assertIsNone(project1.writable)
        self.assertIsNone(project1.executable)
        self.assertIsNone(project1.ownership)

        # project1をreloadする
        project1 = project1.reload()

        # reload後には各権限は再読み込みされる
        self.assertTrue(project1.readable)
        self.assertTrue(project1.writable)
        self.assertTrue(project1.executable)
        self.assertTrue(project1.ownership)

        # プロジェクト1をほかす
        project1.throw_away()

        # ゴミ箱を空にする
        trashcan = self.factory.data.load_trash_folder()
        trashcan.trash_all()

    async def test_rollback_to_add_user(self):
        """
        Userの新規追加操作をRollBackできること
        """
        # Userを作成する
        user = self.factory.user.create('aaa@bbb', 'USR', 'ababababababababab')
        user.save()

        # Userの作成をRollbackする
        self.factory._session.rollback()
        self.factory.end()

        # UserはDBに作成されていないこと
        self.assertFalse(self.factory2.user.exists(user.uuid))
        with self.assertRaises(Exception):
            self.factory2.user.find_by_id(user.id)

    async def test_rollback_to_add_project(self):
        """
        Projectの新規追加操作をRollBackできること
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()

        # ルートフォルダの下にプロジェクト1を作成する
        project1 = root.create_project_folder('P1')
        project1.save()

        # プロジェクト1の作成をRollbackする
        self.factory._session.rollback()
        self.factory.end()

        # プロジェクト1はDBに作成されていないこと
        self.assertFalse(self.factory2.data.exists(project1.uuid))
        with self.assertRaises(Exception):
            self.factory2.data.find_by_id(project1.id)

    async def test_rollback_to_add_flow(self):
        """
        Flowの新規追加操作をRollBackできること
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()

        # ルートフォルダの下にプロジェクト1を作成する
        project1 = root.create_project_folder('P1')
        project1.save()

        # フローを作成する
        flow1 = project1.create_flow('test', FlowData({}))
        flow1.save()

        # プロジェクト1とフローの作成をRollbackする
        self.factory._session.rollback()
        self.factory.end()

        # プロジェクト1はDBに作成されていないこと
        self.assertFalse(self.factory2.data.exists(project1.uuid))
        with self.assertRaises(Exception):
            self.factory2.data.find_by_id(project1.id)

        # フローはDBに作成されていないこと
        self.assertFalse(self.factory2.data.exists(flow1.uuid))
        with self.assertRaises(Exception):
            self.factory2.data.find_by_id(flow1.id)

    async def test_rollback_to_add_scheduler(self):
        """
        Schedulerの新規追加操作をRollBackできること
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()

        # ルートフォルダの下にプロジェクト1を作成する
        project1 = root.create_project_folder('P1')
        project1.save()

        # フローを作成する
        flow1 = project1.create_flow('test', FlowData({}))
        flow1.save()

        # スケジュールを作成する
        trigger1 = {
            'type' : 'date',
            'date' : '2022-05-30 14:42:00'
        }
        schedule1 = project1.create_schedule('schedule1', flow1.uuid, trigger=trigger1)

        # プロジェクト1、フローとスケジュールの作成をRollbackする
        self.factory._session.rollback()
        self.factory.end()

        # プロジェクト1はDBに作成されていないこと
        self.assertFalse(self.factory2.data.exists(project1.uuid))
        with self.assertRaises(Exception):
            self.factory2.data.find_by_id(project1.id)

        # フローはDBに作成されていないこと
        self.assertFalse(self.factory2.data.exists(flow1.uuid))
        with self.assertRaises(Exception):
            self.factory2.data.find_by_id(flow1.id)

        # スケジュールはDBに作成されていないこと
        self.assertFalse(self.factory2.data.exists(schedule1.uuid))
        with self.assertRaises(Exception):
            self.factory2.data.find_by_id(schedule1.id)
