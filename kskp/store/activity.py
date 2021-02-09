from kskp.core import Datum

class Activity(Datum):
    """
    実行結果情報を表す
    """

    __mapper_args__ = {
        'polymorphic_identity' : 'activity'
    }

    def __init__(self, session, parent, label, flow_uuid):
        """
        コンストラクタ
        """
        super().__init__(session, parent, Datum.ACTIVITY_TYPE, label)

        # Activityはファイルに保存せず、データベースに保存する
        self._path = None

        # 処理の開始時刻を取得する
        from datetime import datetime, timezone
        start_time = datetime.utcnow().replace(tzinfo=timezone.utc)

        # data列の値を作成する
        # (同じインスタンスのpointの場合もあることに注意!!)
        # [ApparentLast(point, datum, exs)]
        self._lasts = []
        self._data = {'start_time' : start_time, 'flow_uuid' : flow_uuid}

    def add(self, last):
        self._lasts.append(last)

    @property
    def is_success(self):
        for last in self._lasts:
            if last.has_exs:
                return False
        return True

    def raise_one(self):
        """
        例外があれば、そのうち一つを送出する
        """
        for last in self._lasts:
            if last.has_exs:
                raise last.exs[0]
        return

    def delete_all_frames(self):
        """
        全てのFrame(Cache含む)を削除する
        """
        for last in self._lasts:
            if last.has_frame:
                last.datum.delete()
                last.datum = None

    @property
    def exs(self):
        return [(last.out_point, last.exs) for last in self._lasts if not last.has_cache and last.has_exs]

    @property
    def lasts(self):
        # Cacheは返さない
        # 同じPointにCacheとFrame(CacheとVis)が紐づくとややこしい
        return [(last.out_point, last.datum) for last in self._lasts if not last.has_cache]

    def count_lasts(self):
        return len(self._lasts)

    def save(self):
        from datetime import datetime, timezone
        from kskp.store import Flow, Frame
        # 現在時刻を取得する
        end_time = datetime.utcnow().replace(tzinfo=timezone.utc)
        end_time_str = end_time.astimezone().strftime('%H:%M:%S')
        # 出力フレームのラベルに終了時刻と所要時間を付加する
        for last in self._lasts:
            if last.datum is None or last.datum.label is None:
                # エラーが発生した、またはプレビューのlastはframeのlabelの変更は必要ない
                continue

            new_label = last.datum.label + ' 終了時刻' + end_time_str
            elapsed_time = (end_time - self._data['start_time']).total_seconds()
            if elapsed_time < 60.0:
                elapsed_time_str = str(round(elapsed_time))
                new_label = new_label + ' 全体処理時間' + elapsed_time_str + '秒'
            else:
                elapsed_time_str = str(round(elapsed_time / 60, 2))
                new_label = new_label + ' 全体処理時間' + elapsed_time_str + '分'

            if isinstance(last.datum, Frame):
                if last.datum.is_cache:
                    # Cacheの場合
                    # 対応ファイルの文字コードと改行コードを推測してその結果を登録する
                    last.datum.update_encoding_newline()
                else:
                    # Frameの場合
                    # 対応ファイルの文字コードと改行コードを推測してその結果を登録する
                    last.datum.update_encoding_newline()
                    last.datum.update_label_only(new_label)
            elif isinstance(last.datum, Flow):
                last.datum.update_label(new_label)
