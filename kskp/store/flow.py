
import os
import json

from . import ss as session
from kskp.core import Datum
from kskp.store import Frame

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
        self.data = {'label' : label, 'flow' : flow_data}

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
            datum_data = datum.data2['flow']
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
        parent_uuid = datum.parent_uuid or Datum.get_uuid_by_id(datum.parent_id)
        flow_data = datum.data2['flow']
        flow = Flow(parent_uuid, datum.label, flow_data, datum.creator)
        flow.id = datum.id
        flow.uuid = datum.uuid
        flow._path = datum._path
        flow.modifier = datum.modifier
        flow.created_at = datum.created_at
        flow.modified_at = datum.modified_at
        return flow

    @staticmethod
    def create_simple_flow(parent_uuid, label, data_source, creator=None):
        flow_data = {
                        "label": label,
                        "nodes": [
                            {
                                "id": "d",
                                "type": "frame",
                                "uuid": data_source.uuid,
                                "error": {},
                                "label": data_source.label,
                                "invalid": {},
                                "makeCache": False,
                                "dataSource": "csv",
                                "cacheCreatedAt": None
                            }
                        ],
                        "ports": [[],[]],
                        "params": [],
                        "creator": "",
                        "createdAt": data_source.created_at_str,
                        "projectId": None,
                        "description": ""
                    }
        return Flow(parent_uuid, label, flow_data, creator)

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
        flow = Flow.convert_to_flow(datum)

        # ラベルに'\0'が含まれていれば取り除く
        new_label = Datum.escape_label(label)
        # 更新データを作成する
        data = {'label' : new_label, 'flow' : flow_data}
        flow.data = data

        # 参照するフレームがライブラリに存在することを確認する
        for frame_uuid in flow.get_src_frame_uuids():
            if not Frame.exists(frame_uuid):
                raise Exception(f'フレーム({frame_uuid})がライブラリにありません')

        # 参照するサブフローがライブラリに存在することを確認する
        for flow_uuid in flow.get_sub_flow_uuids():
            if not Flow.exists(flow_uuid):
                raise Exception(f'フロー({flow_uuid})がライブラリにありません')

        try:
            # レコードを更新する
            session.query(Datum).filter(Datum.uuid==uuid).update({'_label'   :new_label,
                                                                  'data'     :data,
                                                                  'modifier' :modifier})
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.commit()

        return flow

    def move(self, parent_uuid, modifier):
        """
        指定されたStoreの直下に移動する
        """
        # UUID値の形式チェックをする
        Datum.valid_uuid_or_raise(parent_uuid)

        try:
            from kskp.store import Folder
            to_folder = Folder.find_by_uuid(parent_uuid)
        except Exception as e:
            raise Exception('移動先の指定はフォルダのUUIDしか許可していません')

        if parent_uuid == self.uuid:
            raise Exception('移動先と移動元の指定が同じです')

        try:
            # レコードを更新する
            session.query(Datum).filter(Datum.id==self.id).update({'parent_id': to_folder.id
                                                                  ,'modifier' : modifier})
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.commit()

        return self
        
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
            
    def remove_reference_only(self):
        """
        念の為Flowは削除しない
        """
        pass

    @property
    def flow_data(self):
        return self.data2['flow']

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

    def get_src_frame_uuids(self):
        """
        参照する入力frameを全て取得する
        """
        ret = []
        flow_json = self.flow_data
        
        if 'nodes' not in flow_json:
            return ret

        for node in flow_json['nodes']:
            if node['type'] != 'frame':
                continue
            if 'cacheCreatedAt' is node and\
                node['cacheCreatedAt'] is not None and\
                node['cacheCreatedAt'] != '':
                # cacheCreatedAtに日時が入っている場合はキャッシュである
                continue
            if 'uuid' not in node or node['uuid'] is None or node['uuid'] == '':
                continue
            if node['uuid'] in ret:
                continue
            ret.append(node['uuid'])
        return ret

    def get_cache_frame_uuids(self):
        """
        参照するキャッシュframeを全て取得する
        """
        ret = []
        flow_json = self.flow_data
        
        if 'nodes' not in flow_json:
            return ret

        for node in flow_json['nodes']:
            if node['type'] != 'frame':
                continue
            if 'cacheCreatedAt' is not node or\
                node['cacheCreatedAt'] is None or\
                node['cacheCreatedAt'] == '':
                # cacheCreatedAtに日時が入っていない場合は入力フレームである
                continue
            if 'uuid' not in node or node['uuid'] is None or node['uuid'] == '':
                continue
            if node['uuid'] in ret:
                continue
            ret.append(node['uuid'])
        return ret

    def get_sub_flow_uuids(self):
        """
        参照するSub Flowを全て取得する
        """
        ret = []
        flow_json = self.flow_data

        if 'nodes' not in flow_json:
            return ret

        for node in flow_json['nodes']:
            if node['type'] != 'flow':
                continue
            if 'uuid' not in node or node['uuid'] is None or node['uuid'] == '':
                continue
            if node['uuid'] in ret:
                continue
            ret.append(node['uuid'])
        return ret

    def get_store_uuids(self):
        """
        参照するStoreを全て取得する
        """
        ret = []
        flow_json = self.flow_data

        for node in flow_json['nodes']:
            if node['type'] != 'store':
                continue
            if 'uuid' not in node or node['uuid'] is None or node['uuid'] == '':
                continue
            if node['uuid'] in ret:
                continue
            ret.append(node['uuid'])
        return ret

    def replace_uuid(self, old_uuid, new_uuid, user_id):
        """
        参照uuidを置き換える
        """
        flow_data = self.flow_data
        for node in flow_data['nodes']:
            if 'uuid' in node and node['uuid'] == old_uuid:
                node['uuid'] = new_uuid
        Flow.update_data(self.uuid, self.label, flow_data, user_id)

    def set_cache(self, node_id, cache_uuid, user_id):
        from datetime import datetime, timedelta, timezone

        flow_data = self.flow_data
        for node in flow_data['nodes']:
            if node['id'] == node_id:
                node['uuid'] = cache_uuid
                # 記録時間はUTC、表示時間は現地時間にすべきでは？？
                node['cacheCreatedAt'] = datetime.now(timezone(timedelta(hours=+9), 'JST')).strftime('%Y-%m-%d %H:%M:%S')
        Flow.update_data(self.uuid, self.label, flow_data, user_id)

    def to_json(self):
        return {'uuid'      : self.uuid,
                'type'      : Datum.FLOW_TYPE,
                'label'     : self.label,
                'creator'   : Datum.get_user_name_by_user_id(self.creator),
                'createdAt' : self.created_at_str}
