import os
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

from . import ss as session
from kskp.core import Datum
from kskp.store import Frame, Cache, DataSource

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
        # (同じインスタンスのpointの場合もあることに注意!!)
        # [(point, datum)]
        self._results = []
        self.data = {'start_time' : start_time, 'flow_uuid' : flow_uuid, 'result': self._results}

    def add(self, point, result_frame):
        self._results.append((point, result_frame))

    @property
    def result(self):
        # Cacheは返さない
        # 同じPointにCacheとFrame(CacheとVis)が紐づくとややこしい
        return [(point, datum) for point, datum in self._results if type(datum) != Cache]

    def count_result(self):
        return len(self._results)

    def save(self):
        # 現在時刻を取得する
        from datetime import datetime, timezone
        end_time = datetime.utcnow().replace(tzinfo=timezone.utc)
        end_time_str = end_time.astimezone().strftime('%H:%M:%S')
        # 出力フレームのラベルに終了時刻と所要時間を付加する
        for point, datum in self._results:
            new_label = datum.label + ' 終了時刻' + end_time_str
            elapsed_time = (end_time - self.data['start_time']).total_seconds()
            if elapsed_time < 60.0:
                elapsed_time_str = str(round(elapsed_time))
                new_label = new_label + ' 全体処理時間' + elapsed_time_str + '秒'
            else:
                elapsed_time_str = str(round(elapsed_time / 60, 2))
                new_label = new_label + ' 全体処理時間' + elapsed_time_str + '分'

            if type(datum) is Frame and Frame.exists(datum.uuid):
                # 
                # Frameの場合
                # 
                # 対応ファイルの文字コードと改行コードを推測してその結果を登録する
                datum.add_entry_from_path(datum.path)
                Frame.update_label_only(datum.uuid, new_label, None)
            elif type(datum) is Cache and Cache.exists(datum.uuid):
                # 
                # Cacheの場合
                # 
                # 対応ファイルの文字コードと改行コードを推測してその結果を登録する
                datum.add_entry_from_path(datum.path)
            elif type(datum) is DataSource:
                DataSource.update_data(datum.uuid, new_label, datum.flow_data, None)




