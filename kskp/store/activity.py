import os
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

from . import ss as session
from kskp.core import Datum
from kskp.store import Frame

class Activity(Datum):
    """
    実行結果情報を表す
    """

    TYPE = 'activity'

    def __init__(self, parent_uuid, label, flow_uuid, creator=None):
        """
        コンストラクタ
        """
        super().__init__(parent_uuid, Activity.TYPE, label, creator)

        # Activityはファイルに保存せず、データベースに保存する
        self._path = ''

        # 処理の開始時刻を取得する
        from datetime import datetime, timezone
        start_time = datetime.utcnow().replace(tzinfo=timezone.utc)

        # data列の値を作成する
        # [(point, frame)]
        self.result = []
        self.data = {'start_time' : start_time, 'flow_uuid' : flow_uuid, 'result': self.result}

    def add(self, point, result_frame):
        self.result.append((point, result_frame))

    def count_result(self):
        return len(self.result)

    def save(self):
        # 現在時刻を取得する
        from datetime import datetime, timezone
        end_time = datetime.utcnow().replace(tzinfo=timezone.utc)
        end_time_str = end_time.astimezone().strftime('%H:%M:%S')
        # 出力フレームのラベルに終了時刻と所要時間を付加する
        for point, frame in self.result:
            if type(frame) is not Frame or not Frame.exists(frame.uuid):
                # Frameが存在しなくてもエラーにはしない
                continue
            new_label = frame.label + ' 終了時刻' + end_time_str
            elapsed_time = (end_time - self.data['start_time']).total_seconds()
            if elapsed_time < 60.0:
                elapsed_time_str = str(round(elapsed_time))
                new_label = new_label + ' 全体処理時間' + elapsed_time_str + '秒'
            else:
                elapsed_time_str = str(round(elapsed_time / 60, 2))
                new_label = new_label + ' 全体処理時間' + elapsed_time_str + '分'
            Frame.update_label_only(frame.uuid, new_label, None)




