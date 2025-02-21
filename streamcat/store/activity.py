from streamcat.core import SavableDatum, Constraints, SCatBaseModel
from streamcat.store import ApparentOuts

class Activity(SavableDatum):
    """
    実行結果情報を表す
    """

    __mapper_args__ = {
        'polymorphic_identity' : 'activity'
    }

    def __init__(self, session, parent, label:str, flow, args:dict={}):
        """
        コンストラクタ
        """
        super().__init__(session, parent, SavableDatum.ACTIVITY_TYPE, label)

        # Activityはファイルに保存せず、データベースに保存する
        self._path = None

        # 対象のフローを保持する
        self._flow = flow

        # 処理の開始時刻を取得する
        from datetime import datetime, timezone
        self._start_at = datetime.now(timezone.utc).replace(tzinfo=timezone.utc)

        # data列の値を作成する
        self._data = {'flowUuid': flow.uuid,
                      'args': args,
                      'startAt': SCatBaseModel.isoformat(self._start_at),
                      'endAt' : '',
                      'outs'  : [],
                      'caches': [],
                      'exs'   : []}

    @Constraints.prohibit_save_on_root
    @Constraints.set_project_role_on_adding_activity
    def save(self):
        try:
            # Dataテーブルにレコードを新規追加する
            self._session.add(self)
        except Exception as e:
            self._session.rollback()
            raise e

    @Constraints.set_project_role_on_updating_activity
    def update_data(self, outs:ApparentOuts, modifier=None):
        from datetime import datetime, timezone

        # 現在時刻を取得する
        end_at = datetime.now(timezone.utc).replace(tzinfo=timezone.utc)

        for point, datum in outs.data:
            # 結果Datumのラベル名を変更する
            self._update_label(datum, end_at)
            # 結果DatumがFrameの場合、対応ファイルの文字コードと改行コードを推測してその結果を登録する
            datum.type == SavableDatum.FRAME_TYPE and datum.update_encoding_newline()

        try:
            # 現在時刻を格納する
            # NOTE: Safariでは、JavaScriptのDateオブジェクトの日付時刻の解析に区切り文字'T'が必要
            self._data['endAt'] = SCatBaseModel.isoformat(end_at)
            # 出力情報を格納する
            self._data.update(outs.to_json())
            # Dataテーブルのレコードを更新する
            self._modifier_id = (modifier or self._session.user).id
            self._session.update(self)
        except Exception as e:
            self._session.rollback()
            raise e

    def _update_label(self, datum:SavableDatum, end_at):
        """
        結果Datumのラベル名を変更する
        """
        from streamcat.store import Flow, Frame

        end_time_str = end_at.astimezone().strftime('%H:%M:%S')
        new_label = datum.label + ' 終了時刻' + end_time_str

        elapsed_time = (end_at - self._start_at).total_seconds()
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
        from streamcat.store.factory import DatumFactory
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

    def to_json(self):

        # 後方互換のため旧名称のキーでの取得も試みる
        def get_value(primary_key:str, secondary_key:str):
            if primary_key in self._data:
                return self._data[primary_key]
            elif secondary_key in self._data:
                return self._data[secondary_key]
            else:
                return None

        ret = super().to_json()
        # 
        ret['flowUuid'] = get_value('flowUuid', 'flow_uuid')
        ret['args']     = self._data.get('args', {})
        ret['startAt']  = get_value('startAt', 'start_time')
        ret['endAt']    = get_value('endAt', 'end_time')
        ret['outs']     = self._data.get('outs', [])
        ret['caches']   = self._data.get('caches', [])
        ret['exs']      = self._data.get('exs', [])
        # allowlist
        ret['allowlist']['update'] = False
        ret['allowlist']['delete'] = False
        ret['allowlist']['move'] = False
        ret['allowlist']['copy'] = False 
        ret['allowlist']['download'] = False
        return ret
