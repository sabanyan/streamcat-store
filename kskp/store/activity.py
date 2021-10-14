from kskp.core import Datum, Constraints
from kskp.store import ApparentOut

class Activity(Datum):
    """
    実行結果情報を表す
    """

    __mapper_args__ = {
        'polymorphic_identity' : 'activity'
    }

    def __init__(self, session, parent, label, flow):
        """
        コンストラクタ
        """
        super().__init__(session, parent, Datum.ACTIVITY_TYPE, label)

        # Activityはファイルに保存せず、データベースに保存する
        self._path = None

        # 対象のフローを保持する
        self._flow = flow

        # 処理の開始時刻を取得する
        from datetime import datetime, timezone
        self._start_time = datetime.utcnow().replace(tzinfo=timezone.utc)

        # data列の値を作成する
        # (同じインスタンスのpointの場合もあることに注意!!)
        # [ApparentOut(point, datum, exs)]
        self._outs = []
        self._data = {'flow_uuid': flow.uuid, 'start_time': str(self._start_time)}

    def add(self, out:ApparentOut):
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

    @Constraints.prohibit_save_on_root
    @Constraints.set_project_role_on_adding_activity
    def save(self):
        from datetime import datetime, timezone
        from kskp.store import Frame

        # 現在時刻を取得する
        end_time = datetime.utcnow().replace(tzinfo=timezone.utc)

        outs = []
        caches = []
        exs = []
        for out in self._outs:
            out_item = {'id': out.out_point.id, 'label': out.out_point.label}

            if not out.has_cache and out.has_exs:
                # 出力Pointで例外が発生した場合
                out_item['message'] = str(out.exs[0])
                exs.append(out_item)
            else:
                out_item['datum'] = out.datum.uuid
                # 出力Pointで結果を出力した場合
                outs.append(out_item)
                # 出力PointでCacheを出力した場合
                if out.has_cache:
                    caches.append(out_item)
                # Frameの場合、対応ファイルの文字コードと改行コードを推測してその結果を登録する
                if isinstance(out.datum, Frame):
                    out.datum.update_encoding_newline()
                # 結果Datumのラベル名を変更する
                self._update_label(out.datum, end_time)

        # 現在時刻を格納する
        self._data['end_time'] = str(end_time)
        # 出力情報を格納する
        self._data['outs'] = outs
        self._data['caches'] = caches
        self._data['exs'] = exs

        try:
            # Dataテーブルにレコードを新規追加する
            self._session.add(self)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

    def _update_label(self, datum:Datum, end_time):
        """
        結果Datumのラベル名を変更する
        """
        from kskp.store import Flow, Frame

        end_time_str = end_time.astimezone().strftime('%H:%M:%S')
        new_label = datum.label + ' 終了時刻' + end_time_str

        elapsed_time = (end_time - self._start_time).total_seconds()
        if elapsed_time < 60.0:
            elapsed_time_str = str(round(elapsed_time))
            new_label = new_label + ' 全体処理時間' + elapsed_time_str + '秒'
        else:
            elapsed_time_str = str(round(elapsed_time / 60, 2))
            new_label = new_label + ' 全体処理時間' + elapsed_time_str + '分'

        if isinstance(datum, Frame):
            datum.update_label_only(new_label)
        elif isinstance(datum, Flow):
            datum.update_label(new_label)

    def throw_away(self, lock_uuid=None):
        """
        Activityをゴミ箱にほかす
        (テスト用)
        """
        from kskp.store.factory import DatumFactory
        factory = DatumFactory(self._session)
        trash_folder = factory.load_trash_folder()

        try:
            return self.move(trash_folder.uuid)
        except Exception as e:
            raise e

    @Constraints.delete_role_when_isolated
    def delete(self):
        """
        Activityを削除する
        (テスト用)
        """
        try:
            # Activityを削除する
            self._session.delete(self)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

    def to_json(self):
        ret = super().to_json()
        # 
        ret['flow_uuid']  = self._data['flow_uuid']
        ret['start_time'] = self._data['start_time']
        ret['end_time']   = self._data['end_time']
        ret['outs']       = self._data['outs']
        ret['caches']     = self._data['caches']
        ret['exs']        = self._data['exs']
        # allowlist
        ret['allowlist']['update'] = False
        ret['allowlist']['delete'] = False
        ret['allowlist']['move'] = False
        ret['allowlist']['copy'] = False 
        ret['allowlist']['download'] = False
        return ret
