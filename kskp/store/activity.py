import os
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

from . import ss as session
from kskp.core import Datum

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

        # data列の値を作成する
        self.result = {}
        self.data = {'time' : 0, 'flow_uuid' : flow_uuid, 'result': self.result}

    def add(self, point, result_frame):
        if point in self.result:
            raise Exception('Same point already Exists!')
        self.result[point] = result_frame

    def count_result(self):
        return len(self.result)



