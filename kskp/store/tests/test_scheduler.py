import unittest
import pprint
import time

from kskp.store import FlowData
from .test_case_base import TestCaseBase

class SchdulerTest(TestCaseBase):
    """
    Schdulerをテストする
    """

    flow_json = {
        "label": "test", 
        "nodes": [
            {
                "id": "d",
                "label": "d",
                "type": "frame", 
                "value": [["顧客", "数量", "金額"],
                            ["x", 1, 10],
                            ["x", 2, 20],
                            ["y", 1, 30],
                            ["y", 3, 40],
                            ["z", 1, 50]],
                "dataSource": "csv"
            }, 
            {
                "id": "c1", 
                "label": "c1", 
                "type": "command", 
                # このコマンドが実行されれば無条件に例外を送出する
                "commandId": "raise", 
                "args": {'message': '@[message]'},
                "srcs": {
                    "i": "d"
                }, 
                "dsts": {
                    "o": "d1"
                }
            }, 
            {
                "id": "d1", 
                "label": "d1", 
                "type": "frame"
            }
        ], 
        "ports": [
            [
                {
                    "type": "frame", 
                    "label": "d", 
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
        "params": [
            {
                "name": "message", 
                "type": "string", 
                "label": "message"
            }
        ], 
        "creator": "ユーザー管理者", 
        "createdAt": "2021-03-17 11:35:39"
    }


    def test_date(self):
        """
        スケジュールの登録と解除
        """
        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # ルートデータストアの下にプロジェクト1を作成する
        project1 = root.create_project_folder('プロジェクト1')
        project1.save()

        # 例外を送出するフローを作成する
        flow = project1.create_flow('test', FlowData(self.flow_json))
        flow.save()

        # スケジュールを作成する
        trigger1 = {
            'type' : 'date',
            'date' : '2021-06-29 12:00:00'
        }
        schedule = project1.create_schedule('一度限り', flow.uuid, trigger=trigger1)
        schedule.save()

        # プロジェクトを削除する
        schedule.delete()
        flow.delete()
        project1.delete()

    def test_interval(self):
        """
        スケジュールの登録と解除
        """
        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # ルートデータストアの下にプロジェクト1を作成する
        project1 = root.create_project_folder('プロジェクト1')
        project1.save()

        # 例外を送出するフローを作成する
        flow = project1.create_flow('test', FlowData(self.flow_json))
        flow.save()

        # スケジュールを作成する
        trigger1 = {
            'type' : 'interval',
            'start_date' : '2021-06-29 12:00:00',
            'end_date'   : '3021-06-29 12:00:00',
            'weeks'  : 0,
            'days'   : 0,
            'hours'  : 0,
            'minutes': 0,
            'seconds': 1
        }
        args = {'params': {'message': '⭐️Exception❕⭐️'}}
        schedule = project1.create_schedule('一度限り', flow.uuid, args, trigger=trigger1)
        schedule.save()

        # プロジェクトを削除する
        schedule.delete()
        flow.delete()
        project1.delete()

    def test_cron(self):
        """
        スケジュールの登録と解除
        """
        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # ルートデータストアの下にプロジェクト1を作成する
        project1 = root.create_project_folder('プロジェクト1')
        project1.save()

        # 例外を送出するフローを作成する
        flow = project1.create_flow('test', FlowData(self.flow_json))
        flow.save()

        # スケジュールを作成する
        trigger1 = {
            'type' : 'cron',
            'start_date' : '2021-06-29 12:00:00',
            'end_date'   : '3021-06-29 12:00:00',
            'year'  : 2021,
            'month' : 12,
            'week'  : 1,
            'day_of_week': 1,
            'day'   : 1,
            'hour'  : 1,
            'minute': 1,
            'second': 1
        }
        args = {'params': {'message': '⭐️Exception❕⭐️'}}
        schedule = project1.create_schedule('一度限り', flow.uuid, args, trigger=trigger1)
        schedule.save()

        # プロジェクトを削除する
        schedule.delete()
        flow.delete()
        project1.delete()

    def test_trashed_schedule(self):
        """
        ゴミ箱に捨てたスケジュールはスケジューラから解除されること
        """
        pass

    def test_trash_executed_schedule(self):
        """
        起動中のスケジュールをゴミ箱に捨てられないこと
        """
        pass
