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
        # [ApparentOut(point, datum, exs)]
        self._outs = []
        self._data = {'start_time' : start_time, 'flow_uuid' : flow_uuid}

    def add(self, out):
        self._outs.append(out)

    @property
    def is_success(self):
        for out in self._outs:
            if out.has_exs:
                return False
        return True

    def raise_one(self):
        """
        例外があれば、そのうち一つを送出する
        """
        for out in self._outs:
            if out.has_exs:
                raise out.exs[0]
        return

    def delete_all_frames(self):
        """
        全てのFrame(Cache含む)を削除する
        """
        for out in self._outs:
            if out.has_frame:
                out.datum.delete()
                out.datum = None

    @property
    def exs(self):
        return [(out.out_point, out.exs) for out in self._outs if not out.has_cache and out.has_exs]

    @property
    def outs(self):
        # Cacheは返さない
        # 同じPointにCacheとFrame(CacheとVis)が紐づくとややこしい
        return [(out.out_point, out.datum) for out in self._outs if not out.has_cache]

    @property
    def frames(self):
        """
        作成したフレームのリストを返す
        """
        return [(out.out_point, out.datum) for out in self._outs if not out.has_cache and out.has_frame]

    @property
    def caches(self):
        """
        作成したキャッシュのリストを返す
        """
        return [(out.out_point, out.datum) for out in self._outs if out.has_cache]

    def count_outs(self):
        return len(self._outs)

    def save(self):
        from datetime import datetime, timezone
        from kskp.store import Flow, Frame
        # 現在時刻を取得する
        end_time = datetime.utcnow().replace(tzinfo=timezone.utc)
        end_time_str = end_time.astimezone().strftime('%H:%M:%S')
        # 出力フレームのラベルに終了時刻と所要時間を付加する
        for out in self._outs:
            if out.datum is None or out.datum.label is None:
                # エラーが発生した、またはプレビューのlastはframeのlabelの変更は必要ない
                continue

            new_label = out.datum.label + ' 終了時刻' + end_time_str
            elapsed_time = (end_time - self._data['start_time']).total_seconds()
            if elapsed_time < 60.0:
                elapsed_time_str = str(round(elapsed_time))
                new_label = new_label + ' 全体処理時間' + elapsed_time_str + '秒'
            else:
                elapsed_time_str = str(round(elapsed_time / 60, 2))
                new_label = new_label + ' 全体処理時間' + elapsed_time_str + '分'

            if isinstance(out.datum, Frame):
                if out.datum.is_cache:
                    # Cacheの場合
                    # 対応ファイルの文字コードと改行コードを推測してその結果を登録する
                    out.datum.update_encoding_newline()
                else:
                    # Frameの場合
                    # 対応ファイルの文字コードと改行コードを推測してその結果を登録する
                    out.datum.update_encoding_newline()
                    out.datum.update_label_only(new_label)
            elif isinstance(out.datum, Flow):
                out.datum.update_label(new_label)
