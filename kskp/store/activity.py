from datetime import datetime, timedelta, timezone

from kskp.core import Datum
from kskp.store import Frame, DataSource

class Activity(Datum):
    """
    実行結果情報を表す
    """

    __mapper_args__ = {
        'polymorphic_identity' : 'activity'
    }

    TYPE = 'activity'

    def __init__(self, session, parent, label, flow_uuid):
        """
        コンストラクタ
        """
        super().__init__(session, parent, Activity.TYPE, label)

        # Activityはファイルに保存せず、データベースに保存する
        self._path = None

        # 処理の開始時刻を取得する
        from datetime import datetime, timezone
        start_time = datetime.utcnow().replace(tzinfo=timezone.utc)

        # data列の値を作成する
        # (同じインスタンスのpointの場合もあることに注意!!)
        # [(point, datum)]
        self._results = []
        self._data = {'start_time' : start_time, 'flow_uuid' : flow_uuid, 'result': self._results}

    def add(self, point, result_frame):
        self._results.append((point, result_frame))

    @property
    def results(self):
        def is_cache(datum):
            return type(datum) == Frame and datum.is_cache
        # Cacheは返さない
        # 同じPointにCacheとFrame(CacheとVis)が紐づくとややこしい
        return [(point, datum) for point, datum in self._results if not is_cache(datum)]

    def count_results(self):
        return len(self._results)

    def save(self):
        # 現在時刻を取得する
        from datetime import datetime, timezone
        end_time = datetime.utcnow().replace(tzinfo=timezone.utc)
        end_time_str = end_time.astimezone().strftime('%H:%M:%S')
        # 出力フレームのラベルに終了時刻と所要時間を付加する
        for point, datum in self._results:
            new_label = datum.label + ' 終了時刻' + end_time_str
            elapsed_time = (end_time - self._data['start_time']).total_seconds()
            if elapsed_time < 60.0:
                elapsed_time_str = str(round(elapsed_time))
                new_label = new_label + ' 全体処理時間' + elapsed_time_str + '秒'
            else:
                elapsed_time_str = str(round(elapsed_time / 60, 2))
                new_label = new_label + ' 全体処理時間' + elapsed_time_str + '分'

            if isinstance(datum, Frame):
                if datum.is_cache:
                    # Cacheの場合
                    # 対応ファイルの文字コードと改行コードを推測してその結果を登録する
                    datum.update_encoding_newline()
                else:
                    # Frameの場合
                    # 対応ファイルの文字コードと改行コードを推測してその結果を登録する
                    datum.update_encoding_newline()
                    datum.update_label_only(new_label)
            elif isinstance(datum, DataSource):
                datum.update_data(new_label, datum.flow_data.to_json())




