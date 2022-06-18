import unittest
import pprint
import time

from streamcat.store import FlowData
from .test_case_base import TestCaseBase
from streamcat.store.scheduler import schedule_manager

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
        スケジュールの登録と取得と解除
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

        # 作成したスケジュールを取得する
        schedule = self.factory.data.find_by_uuid(schedule.uuid)

        # 取得したスケジュールの値を検証する
        self.assertIsNotNone(schedule.id)
        self.assertEqual(schedule.parent_id, project1.id)
        self.assertIsNotNone(schedule.uuid)
        self.assertIsNone(schedule.path)
        self.assertEqual(schedule.type, 'schedule')
        self.assertEqual(schedule.label, '一度限り')
        self.assertEqual(schedule.creator, self.USER1)
        self.assertEqual(schedule.modifier, self.USER1)
        self.assertIsNotNone(schedule.created_at)
        self.assertIsNotNone(schedule.modified_at)
        self.assertEqual(schedule.runnable_uuid, flow.uuid)
        self.assertEqual(schedule.args, {})
        self.assertEqual(schedule.inputs, {})
        self.assertEqual(schedule.trigger, trigger1)

        # プロジェクトを削除する
        schedule.delete()
        flow.delete()
        project1.delete()

    def test_interval(self):
        """
        スケジュールの登録と取得と解除
        """
        # ルートデータストアを取得する
        root = self.factory2.data.load_root()

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
        schedule = project1.create_schedule('一定間隔', flow.uuid, args, trigger=trigger1)
        schedule.save()

        # 作成を確定する
        self.factory2.end()

        # 作成したスケジュールを取得する
        schedule = self.factory.data.find_by_uuid(schedule.uuid)

        # 取得したスケジュールの値を検証する
        self.assertIsNotNone(schedule.id)
        self.assertEqual(schedule.parent_id, project1.id)
        self.assertIsNotNone(schedule.uuid)
        self.assertIsNone(schedule.path)
        self.assertEqual(schedule.type, 'schedule')
        self.assertEqual(schedule.label, '一定間隔')
        self.assertEqual(schedule.creator, self.USER2)
        self.assertEqual(schedule.modifier, self.USER2)
        self.assertIsNotNone(schedule.created_at)
        self.assertIsNotNone(schedule.modified_at)
        self.assertEqual(schedule.runnable_uuid, flow.uuid)
        self.assertEqual(schedule.args, args)
        self.assertEqual(schedule.inputs, {})
        self.assertEqual(schedule.trigger, trigger1)

        # プロジェクトを削除する
        schedule.delete()
        # 削除を確定する
        self.factory.end()

        # フローとプロジェクトを削除する
        flow.delete()
        project1.delete()

    def test_cron(self):
        """
        スケジュールの登録と取得と解除
        """
        # ルートデータストアを取得する
        root = self.factory3.data.load_root()

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
        schedule = project1.create_schedule('指定日時', flow.uuid, args, trigger=trigger1)
        schedule.save()

        # 作成を確定する
        self.factory3.end()

        # 作成したスケジュールを取得する
        schedule = self.factory.data.find_by_uuid(schedule.uuid)

        # 取得したスケジュールの値を検証する
        self.assertIsNotNone(schedule.id)
        self.assertEqual(schedule.parent_id, project1.id)
        self.assertIsNotNone(schedule.uuid)
        self.assertIsNone(schedule.path)
        self.assertEqual(schedule.type, 'schedule')
        self.assertEqual(schedule.label, '指定日時')
        self.assertEqual(schedule.creator, self.USER3)
        self.assertEqual(schedule.modifier, self.USER3)
        self.assertIsNotNone(schedule.created_at)
        self.assertIsNotNone(schedule.modified_at)
        self.assertEqual(schedule.runnable_uuid, flow.uuid)
        self.assertEqual(schedule.args, args)
        self.assertEqual(schedule.inputs, {})
        self.assertEqual(schedule.trigger, trigger1)

        # プロジェクトを削除する
        schedule.delete()
        # 削除を確定する
        self.factory.end()

        # フローとプロジェクトを削除する
        flow.delete()
        project1.delete()

    def test_update_label(self):
        """
        スケジュールのラベルを変更する
        """
        # ルートデータストアを取得する
        root = self.factory0.data.load_root()

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

        # 作成したスケジュールのラベルを変更する
        schedule.update_label('一度限りですよ', self.USER1)

        # 変更を確定する
        self.factory0.end()

        # 変更したスケジュールを取得する
        updated = self.factory.data.find_by_id(schedule.id)

        # ラベルのみが変更されることを検証する
        self.assertEqual(updated.id, schedule.id)
        self.assertEqual(updated.parent_id, schedule.parent_id)
        self.assertEqual(updated.uuid, schedule.uuid)
        self.assertIsNone(updated.path)
        self.assertEqual(updated.runnable_uuid, schedule.runnable_uuid)
        self.assertEqual(updated.args, schedule.args)
        self.assertEqual(updated.inputs, schedule.inputs)
        self.assertEqual(updated.trigger, schedule.trigger)
        self.assertEqual(updated.type, 'schedule')
        self.assertEqual(updated.label, '一度限りですよ')
        self.assertEqual(updated.creator, self.USER0)
        self.assertEqual(updated.modifier, self.USER1)
        self.assertEqual(updated.created_at, schedule.created_at)
        self.assertIsNotNone(updated.modified_at)

        # プロジェクトを削除する
        schedule.delete()
        flow.delete()
        project1.delete()

    def test_update_schedule(self):
        """
        スケジュールを変更する
        """
        # ルートデータストアを取得する
        root = self.factory0.data.load_root()

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

        # 別のフローを作成する
        flow2 = project1.create_flow('AnotherFlow', FlowData(self.flow_json))
        flow2.save()

        # 作成したスケジュールを変更する
        args2 = {'params': {'message': '変更後のメッセージ'}}
        inputs2 = {'input1': '変更後の入力1'}
        trigger2 = {
            'type'       : 'cron',
            'start_date' : '2021-06-29 12:00:00',
            'end_date'   : '3021-06-29 12:00:00',
            'day'        : 31,
        }
        schedule.update_data('変更後のスケジュール', flow2.uuid, args2, inputs2, trigger2, self.USER1)

        # 変更を確定する
        self.factory0.end()

        # 変更したスケジュールを取得する
        updated = self.factory.data.find_by_id(schedule.id)

        # 変更されることを検証する
        self.assertEqual(updated.id, schedule.id)
        self.assertEqual(updated.parent_id, schedule.parent_id)
        self.assertEqual(updated.uuid, schedule.uuid)
        self.assertIsNone(updated.path)
        self.assertEqual(updated.runnable_uuid, flow2.uuid)
        self.assertEqual(updated.args, args2)
        self.assertEqual(updated.inputs, inputs2)
        self.assertEqual(updated.trigger, trigger2)
        self.assertEqual(updated.type, 'schedule')
        self.assertEqual(updated.label, '変更後のスケジュール')
        self.assertEqual(updated.creator, self.USER0)
        self.assertEqual(updated.modifier, self.USER1)
        self.assertEqual(updated.created_at, schedule.created_at)
        self.assertIsNotNone(updated.modified_at)

        # 
        # スケジューラに登録した設定も変更されること
        # 

        # プロジェクトを削除する
        schedule.delete()
        flow.delete()
        flow2.delete()
        project1.delete()

    def test_move_schedule(self):
        """
        スケジュールを移動する
        """
        # ルートデータストアを取得する
        root = self.factory0.data.load_root()

        # ルートデータストアの下にプロジェクト1を作成する
        project1 = root.create_project_folder('プロジェクト1')
        project1.save()

        # ルートデータストアの下にプロジェクト2を作成する
        project2 = root.create_project_folder('プロジェクト2')
        project2.save()

        # 例外を送出するフローをプロジェクト1の下に作成する
        flow = project1.create_flow('フロー1', FlowData(self.flow_json))
        flow.save()

        # スケジュールをプロジェクト1の下に作成する
        trigger1 = {
            'type' : 'date',
            'date' : '2021-06-29 12:00:00'
        }
        schedule = project1.create_schedule('スケジュール1', flow.uuid, trigger=trigger1)
        schedule.save()

        # スケジュール1をプロジェクト2へ移動する
        moved = schedule.move(project2.uuid, modifier=self.USER2)

        # parent_id, modifierが変更されることを検証する
        self.assertEqual(moved.id, schedule.id)
        self.assertEqual(moved.parent_id, project2.id)
        self.assertEqual(moved.uuid, schedule.uuid)
        self.assertEqual(moved.type, schedule.type)
        self.assertEqual(moved.label, 'スケジュール1')
        self.assertEqual(moved.creator, self.USER0)
        self.assertEqual(moved.modifier, self.USER2)
        self.assertEqual(moved.created_at, schedule.created_at)
        self.assertIsNotNone(moved.modified_at)

        """
        スケジュールの移動を元に戻す
        """
        backed = moved.put_back()[0]
        # parent_id, modifierが変更されることを検証する
        self.assertEqual(backed.id, moved.id)
        self.assertEqual(backed.parent_id, project1.id)
        self.assertEqual(backed.uuid, moved.uuid)
        self.assertEqual(backed.type, moved.type)
        self.assertEqual(backed.label, 'スケジュール1')
        self.assertEqual(backed.creator, self.USER0)
        self.assertEqual(backed.modifier, self.USER0)
        self.assertEqual(backed.created_at, moved.created_at)
        self.assertIsNotNone(backed.modified_at)

        # プロジェクトを削除する
        schedule.delete()
        flow.delete()
        project1.delete()
        project2.delete()

    def test_exec_by_creator(self):
        """
        スケジュールの作成者(Creator)の権限でフローが実行されること
        """

    def test_invalid_runnable_uuid(self):
        """
        存在しないフローのUUIDでスケジュールを作成できないこと
        """
        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # ルートデータストアの下にプロジェクト1を作成する
        project1 = root.create_project_folder('プロジェクト1')
        project1.save()

        # 例外を送出するフローを作成する
        flow = project1.create_flow('test', FlowData(self.flow_json))
        flow.save()

        # フローを削除する
        flow.delete()

        # スケジュールを作成する
        trigger1 = {
            'type' : 'date',
            'date' : '2021-06-29 12:00:00'
        }
        # 存在しないフローのUUIDでスケジュールを作成しようとすると例外を送出する
        with self.assertRaises(Exception):
            project1.create_schedule('一度限り', flow.uuid, trigger=trigger1)

    def test_unreadable_runnable_uuid(self):
        """
        参照権限が無いフローのUUIDでスケジュールを作成できないこと
        """
        # ルートデータストアを取得する
        root = self.factory2.data.load_root()

        # ルートデータストアの下にプロジェクト1を作成する
        project1 = root.create_project_folder('プロジェクト1')
        project1.save()

        # ルートデータストアの下にプロジェクト2を作成する
        project2 = root.create_project_folder('プロジェクト2')
        project2.save()

        # プロジェクト1の下にフローを作成する
        flow = project1.create_flow('test', FlowData(self.flow_json))
        flow.save()

        # プロジェクト1からUser2の参照権限を外す
        project1.leave_member(self.USER2)

        # 参照権限が無いフローのUUIDでスケジュールを登録しようとすると例外を送出する
        trigger1 = {
            'type' : 'date',
            'date' : '2021-06-29 12:00:00'
        }
        with self.assertRaises(Exception):
            project2.create_schedule('スケジュール', flow.uuid, trigger=trigger1)

    def test_not_move_runnable_to_unreadable_project(self):
        """
        フローを参照権限が無いプロジェクトへ移動できないこと
        """

    def test_trashed_runnable_uuid(self):
        """
        ゴミ箱に捨てたフローのUUIDでスケジュールを登録できないこと
        """
        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # ルートデータストアの下にプロジェクト1を作成する
        project1 = root.create_project_folder('プロジェクト1')
        project1.save()

        # 例外を送出するフローを作成する
        flow = project1.create_flow('test', FlowData(self.flow_json))
        flow.save()

        # フローをゴミ箱にほかす
        flow.throw_away()

        # スケジュールを作成する
        trigger1 = {
            'type' : 'date',
            'date' : '2021-06-29 12:00:00'
        }
        # ゴミ箱に捨てたフローのUUIDでスケジュールを作成しようとすると例外を送出する
        with self.assertRaises(Exception):
            project1.create_schedule('一度限り', flow.uuid, trigger=trigger1)

    def test_trashed_schedule(self):
        """
        ゴミ箱に捨てたスケジュールはスケジューラから解除されること
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
            'date' : '2221-06-29 12:00:00'
        }
        schedule = project1.create_schedule('一度限り', flow.uuid, trigger=trigger1)
        schedule.save()

        # スケジュールはスケジューラに登録されること
        self.assertTrue(schedule_manager.contains(schedule.uuid))

        # スケジュールをゴミ箱にほかす
        schedule.throw_away()

        # ゴミ箱に捨てたスケジュールはスケジューラから解除されること
        self.assertFalse(schedule_manager.contains(schedule.uuid))

        # スケジュールをゴミ箱から戻す
        schedule.put_back()

        # ゴミ箱にから戻したスケジュールはスケジューラに再登録されること
        self.assertTrue(schedule_manager.contains(schedule.uuid))

    def test_trash_schedule_in_folder(self):
        """
        スケジュールを含むフォルダをゴミ箱に捨てると、スケジューラから解放されること
        """
        # ルートフォルダを取得する
        root = self.factory2.data.load_root()

        # ルートフォルダの下にプロジェクト1を作成する
        project1 = root.create_project_folder('プロジェクト1')
        project1.save()
        project1 = project1.reload()

        # プロジェクト1の下にフォルダを作成する
        folder = project1.create_folder('フォルダ')
        folder.save()
        folder = folder.reload()

        # フォルダの下にフローを作成する
        flow = folder.create_flow('フロー', FlowData({}))
        flow.save()
        flow = flow.reload()

        # フォルダの下にスケジュールを作成する
        trigger1 = {
            'type' : 'date',
            'date' : '2222-05-15 12:00:00'
        }
        schedule = folder.create_schedule('スケジュール', flow.uuid, trigger=trigger1)
        schedule.save()
        schedule = schedule.reload()

        # スケジュールはスケジューラに登録されること
        self.assertTrue(schedule_manager.contains(schedule.uuid))

        # フォルダをゴミ箱へほかす
        moved_folder = folder.throw_away()

        # ゴミ箱を取得する
        trashcan = self.factory2.data.load_trash_folder()

        # 移動後のフォルダを検証する
        # parent_id, path, modifierが変更されることを検証する
        self.assertEqual(moved_folder.id, folder.id)
        self.assertEqual(moved_folder.parent_id, trashcan.id)
        self.assertEqual(moved_folder.uuid, folder.uuid)
        self.assertEqual(moved_folder.type, 'folder')
        self.assertEqual(moved_folder.label, 'フォルダ')
        self.assertEqual(moved_folder.path, trashcan.path / folder.label)
        self.assertEqual(moved_folder.creator, self.USER2)
        self.assertEqual(moved_folder.modifier, self.USER2)
        self.assertEqual(moved_folder.created_at, folder.created_at)
        self.assertGreater(moved_folder.modified_at, moved_folder.created_at)

        # 移動後のスケジュールを検証する
        self.assertIsNotNone(moved_folder.id)
        self.assertEqual(schedule.parent_id, moved_folder.id)
        self.assertIsNotNone(schedule.uuid)
        self.assertEqual(schedule.type, 'schedule')
        self.assertEqual(schedule.label, 'スケジュール')
        self.assertEqual(schedule.creator, schedule.modifier)
        self.assertEqual(schedule.created_at, schedule.modified_at)

        # ゴミ箱に捨てたスケジュールはスケジューラから解除されること
        self.assertFalse(schedule_manager.contains(schedule.uuid))

        # フォルダをゴミ箱から戻す
        moved_folder.put_back()

        # ゴミ箱にから戻したスケジュールはスケジューラに再登録されること
        self.assertTrue(schedule_manager.contains(schedule.uuid))

        # プロジェクトを削除する
        project1.throw_away()

        # ゴミ箱を空にする
        self.factory2.data.find_trashcan().trash_all()


    def test_trash_scheduled_flow(self):
        """
        スケジュールされたフローはゴミ箱に捨てられないこと
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

        # フローをゴミ箱にほかそうとすると送出がされること
        with self.assertRaises(Exception):
            flow.throw_away()

        # フローを削除しようとすると例外が送出されること
        with self.assertRaises(Exception):
            flow.delete()

        # スケジュールをゴミ箱へほかす
        schedule.throw_away()

        # スケジュールを削除した後はフローをゴミ箱にほかせること
        flow.throw_away()

        # スケジュールを削除した後はフローを削除できること
        flow.delete()

    def test_trash_executed_schedule(self):
        """
        起動中のスケジュールをゴミ箱に捨てられないこと
        """
        pass

    def test_load_schedule_on_restarting(self):
        """
        システム再起動時にスケジュールがスケジューラに再登録されること
        """

    def test_not_load_trashed_schedule_on_restarting(self):
        """
        ゴミ箱に捨てたスケジュールはシステム再起動時にスケジューラに再登録されないこと
        """
