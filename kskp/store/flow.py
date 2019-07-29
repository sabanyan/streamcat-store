
import os
import json

from . import ss as session
from kskp.core import Datum

class Flow(Datum):

    def __init__(self, parent_uuid, label, flow_data, creator=None):
        """
        コンストラクタ
        flow_data : Flowデータを指定する
        """
        super().__init__(parent_uuid, Datum.FLOW_TYPE, label, creator)

        # フローデータはファイルに保存せず、データベースに保存する
        self._path = ''

        # data列の値を作成する
        self.data = json.dumps({'label' : label, 'flow' : flow_data})

    @staticmethod
    def find_all_flows():
        """
        全てのフローを取得する
        """
        data = session.query(Datum).filter(Datum.type==Datum.FLOW_TYPE).all()
        return data

    @staticmethod
    def find_by_uuid(uuid):
        """
        指定されたuuidを持つFlowを取得する
        """
        # UUID値の形式チェックをする
        Datum.valid_uuid_or_raise(uuid)
        datum = session.query(Datum).filter(Datum.uuid==uuid)\
                                    .filter(Datum.type==Datum.FLOW_TYPE).one_or_none()
        if datum is None:
            raise Exception('no flow is found by designated id(%s).' % uuid)
        return Flow.convert_to_flow(datum)

    @staticmethod
    def find_all_subflows(no_inputs=True, no_outputs=True):
        """
        サブフローを取得する
        no_inputs  =False : 入力ポートのないサブフローは取得しない
        no_outputs =False : 出力ポートのないサブフローは取得しない
        """
        # FIXIT : PostgreSQLのJSONB演算子を用いればSQLのみでサブフローを抽出できるはず
        data = session.query(Datum).filter(Datum.type==Datum.FLOW_TYPE).all()

        subflows = []
        for datum in data:
            datum_data = json.loads(datum.data, encoding='utf-8')['flow']
            # onの時にno_inputs（＝inputsがない）のサブフローは出さない
            if no_inputs:
                if len(datum_data['ports'][0]) == 0:
                    continue

            # onの時にno_outputs（＝outputsがない）のサブフローは出さない
            if no_outputs:
                if len(datum_data['ports'][1]) == 0:
                    continue

            if len(datum_data['ports'][0]) > 0 or len(datum_data['ports'][1]) > 0:
                subflows.append(datum)

        return subflows

    @staticmethod
    def exists(uuid):
        """
        指定されたuuidを持つFlowが存在する場合はTrueを返す
        """
        # UUID値の形式チェックをする
        if not Datum.is_valid_uuid(uuid):
            return False
        result = session.query(Datum).filter(Datum.uuid==uuid)\
                                     .filter(Datum.type==Datum.FLOW_TYPE).count()
        return result > 0

    @staticmethod
    def convert_to_flow(datum):
        parent_uuid = Datum.get_uuid_by_id(datum.parent_id)
        label = json.loads(datum.data, encoding='utf-8')['label']
        flow_data = json.loads(datum.data, encoding='utf-8')['flow']
        flow = Flow(parent_uuid, label, flow_data, datum.creator)
        flow.id = datum.id
        flow.uuid = datum.uuid
        flow._path = datum._path
        flow.modifier = datum.modifier
        flow.created_at = datum.created_at
        flow.modified_at = datum.modified_at
        return flow

    def save(self):
        """
        Flowを保存する
        """
        # 既にルートフォルダが存在する場合は、parent_id=NULLを許可しない
        if self.parent_id is None and Datum.count_root() > 0:
            raise Exception('You can not add another root flow. A root already exists.')
        try:
            # Dataテーブルにレコードを新規追加する
            session.add(self)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.commit()

    @staticmethod
    def update_data(uuid, label, flow_data, modifier):
        """
        Flowのdata列を更新する
        """
        # UUID値の形式チェックをする
        Datum.valid_uuid_or_raise(uuid)
        # レコードを取得する
        datum = session.query(Datum).filter(Datum.uuid==uuid)\
                                    .filter(Datum.type==Datum.FLOW_TYPE).one_or_none()
        if datum is None:
            raise Exception('no flow is found by designated id.')

        try:
            # レコードを更新する
            data = json.dumps({'label' : label, 'flow' : flow_data})
            session.query(Datum).filter(Datum.uuid==uuid).update({'data'     :data,
                                                                  'modifier' :modifier})
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.commit()

        return Flow.convert_to_flow(datum)

    def delete(self):
        """
        Flowを削除する
        """
        # 削除しようとするFlowが、DBに格納されているフローで使用されている場合は例外を送出する
        # 2019/07/29現在下記のコードはpostgres9.6では動かない、postgres11.1では動作確認している
        using_flow_uuids = Datum.get_flow_uuids_using_other_datum(self.uuid)
        if len(using_flow_uuids) > 0:
            using_flow_label= Flow.find_by_uuid(using_flow_uuids[0]).label
            raise Exception('このフローはフロー(%s)でサブフローとして使用しているため削除できません' % using_flow_label)

        try:
            # フレームレコードを削除する
            session.query(Datum).filter(Datum.id==self.id)\
                                .filter(Datum.type==Datum.FLOW_TYPE).delete()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.commit()

    @property
    def label(self):
        return json.loads(self.data, encoding='utf-8')['label']

    @property
    def flow_data(self):
        return json.loads(self.data, encoding='utf-8')['flow']

    def duplicate(self, new_label, user_id):
        """
        自身の複製を作成する
        """
        # ラベルと作成者については、指定された値を新たに設定する
        new_flow_data = self.flow_data
        new_flow_data['label'] = new_label
        new_flow_data['creator'] = Datum.get_user_name_by_user_id(user_id)
        # FIXIT : Dataテーブルのcreated_at列と時刻を合わせたい
        from datetime import datetime, timedelta, timezone
        JST = timezone(timedelta(hours=+9), 'JST')
        new_flow_data['createdAt'] = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')
        # 複製を作成する
        new_flow = Flow(self.parent_uuid, new_label, new_flow_data, user_id)
        return new_flow

    def to_json(self):
        return {'uuid'      : self.uuid,
                'type'      : Datum.FLOW_TYPE,
                'label'     : self.label,
                'creator'   : Datum.get_user_name_by_user_id(self.creator),
                'createdAt' : self.created_at_str}
