
import os
import json

from kskp.core import Datum
from kskp.store import Frame

class Flow(Datum):

    __mapper_args__ = {
        'polymorphic_identity' : 'flow'
    }

    def __init__(self, session, parent_uuid, label, flow_data, creator=None):
        """
        コンストラクタ
        flow_data : Flowデータを指定する
        """
        super().__init__(session, parent_uuid, Datum.FLOW_TYPE, label, creator)

        # フローデータはファイルに保存せず、データベースに保存する
        self._path = ''

        # data列の値を作成する
        self.data = {'label' : label, 'flow' : flow_data}

    # @staticmethod
    # def find_all_flows():
    #     """
    #     全てのフローを取得する
    #     """
    #     flows = session.query(Flow).filter(Flow.type==Flow.FLOW_TYPE).all()
    #     return flows

    # @staticmethod
    # def find_by_uuid(uuid):
    #     """
    #     指定されたuuidを持つFlowを取得する
    #     """
    #     # UUID値の形式チェックをする
    #     Datum.valid_uuid_or_raise(uuid)
    #     flow = session.query(Flow).filter(Flow.uuid==uuid)\
    #                               .filter(Flow.type==Flow.FLOW_TYPE).one_or_none()
    #     if flow is None:
    #         raise Exception('no flow is found by designated id(%s).' % uuid)
    #     return flow

    # @staticmethod
    # def find_all_subflows(no_inputs=True, no_outputs=True):
    #     """
    #     サブフローを取得する
    #     no_inputs  =False : 入力ポートのないサブフローは取得しない
    #     no_outputs =False : 出力ポートのないサブフローは取得しない
    #     """
    #     # FIXIT : PostgreSQLのJSONB演算子を用いればSQLのみでサブフローを抽出できるはず
    #     flows = session.query(Flow).filter(Flow.type==Flow.FLOW_TYPE).all()

    #     subflows = []
    #     for flow in flows:
            
    #         # 参照権限のないフローはサブフローか否かの判定ができない
    #         if not flow.readable:
    #             continue

    #         flow_data = flow.data['flow']
    #         # onの時にno_inputs（＝inputsがない）のサブフローは出さない
    #         if no_inputs:
    #             if len(flow_data['ports'][0]) == 0:
    #                 continue

    #         # onの時にno_outputs（＝outputsがない）のサブフローは出さない
    #         if no_outputs:
    #             if len(flow_data['ports'][1]) == 0:
    #                 continue

    #         if len(flow_data['ports'][0]) > 0 or len(flow_data['ports'][1]) > 0:
    #             subflows.append(flow)

    #     return subflows

    # @staticmethod
    # def exists(uuid):
    #     """
    #     指定されたuuidを持つFlowが存在する場合はTrueを返す
    #     """
    #     # UUID値の形式チェックをする
    #     if not Datum.is_valid_uuid(uuid):
    #         return False
    #     result = session.query(Flow).filter(Flow.uuid==uuid)\
    #                                 .filter(Flow.type==Flow.FLOW_TYPE).count()
    #     return result > 0

    # @staticmethod
    # def create_simple_flow(parent_uuid, label, data_source, creator=None):
    #     flow_data = {
    #                     "label": label,
    #                     "nodes": [
    #                         {
    #                             "id": "d",
    #                             "type": "frame",
    #                             "uuid": data_source.uuid,
    #                             "error": {},
    #                             "label": data_source.label,
    #                             "invalid": {},
    #                             "makeCache": False,
    #                             "dataSource": "csv",
    #                             "cacheCreatedAt": None
    #                         }
    #                     ],
    #                     "ports": [[],[]],
    #                     "params": [],
    #                     "creator": "",
    #                     "createdAt": data_source.created_at_str,
    #                     "projectId": None,
    #                     "description": ""
    #                 }
    #     return Flow(parent_uuid, label, flow_data, creator)

    def save(self):
        """
        Flowを保存する
        """
        # 既にルートフォルダが存在する場合は、parent_id=NULLを許可しない
        if self.parent_id is None and Datum.count_root() > 0:
            raise Exception('You can not add another root flow. A root already exists.')
        try:
            # Dataテーブルにレコードを新規追加する
            self.session.add(self)
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.commit()

    def update_data(self, label, flow_data):
        """
        Flowのdata列を更新する
        """
        # # 参照するフレームがライブラリに存在することを確認する
        # for frame_uuid in self.get_src_frame_uuids():
        #     if not Frame.exists(frame_uuid):
        #         raise Exception(f'フレーム({frame_uuid})がライブラリにありません')

        # # 参照するサブフローがライブラリに存在することを確認する
        # for flow_uuid in self.get_sub_flow_uuids():
        #     if not Flow.exists(flow_uuid):
        #         raise Exception(f'フロー({flow_uuid})がライブラリにありません')

        # ラベルに'\0'が含まれていれば取り除く
        new_label = Datum.escape_label(label)
        # 更新データを作成する
        data = {'label' : new_label, 'flow' : flow_data}
        # flow.data = data

        # フローのインポート処理で引っかかるので以下のチェックを一旦外す
        # 
        # # 参照するフレームがライブラリに存在することを確認する
        # for frame_uuid in self.get_src_frame_uuids():
        #     if not Frame.exists(frame_uuid):
        #         raise Exception(f'フレーム({frame_uuid})がライブラリにありません')

        # # 参照するサブフローがライブラリに存在することを確認する
        # for flow_uuid in self.get_sub_flow_uuids():
        #     if not Flow.exists(flow_uuid):
        #         raise Exception(f'フロー({flow_uuid})がライブラリにありません')

        try:
            # レコードを更新する
            self._label = new_label
            self._data = data
            self._modifier_id = self.session.user.id
            self.session.update(self)
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.commit()

        # ここでflowを返すとtest_model.pyでテストが通らない
        return self

    def move(self, parent_uuid):
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
            # self.session.query(Datum).filter(Datum.id==self.id).update({'parent_id'   :to_folder.id
            #                                                       ,'_modifier_id':modifier.id})
            self.parent_id = to_folder.id
            self._modifier_id = self.session.user.id
            self.session.update(self)
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.commit()

        return self
        
    def delete(self):
        """
        Flowを削除する
        """
        # 削除しようとするFlowが、DBに格納されているフローで使用されている場合は例外を送出する
        # 2019/07/29現在下記のコードはpostgres9.6では動かない、postgres11.1では動作確認している
        using_flow_uuids = self.get_flow_uuids_using_me()
        if len(using_flow_uuids) > 0:
            using_flow_label= Flow.find_by_uuid(using_flow_uuids[0]).label
            raise Exception('このフローはフロー(%s)でサブフローとして使用しているため削除できません' % using_flow_label)

        try:
            # フレームレコードを削除する
            self.session.delete(self)
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.commit()
            
    def remove_reference_only(self):
        """
        念の為Flowは削除しない
        """
        pass

    @property
    def flow_data(self):
        return self.data['flow']

    def duplicate(self, new_label):
        """
        自身の複製を作成する
        """
        # ラベルと作成者については、指定された値を新たに設定する
        new_flow_data = self.flow_data
        new_flow_data['label'] = new_label
        new_flow_data['creator'] = self.session.user.name
        # FIXIT : Dataテーブルのcreated_at列と時刻を合わせたい
        from datetime import datetime, timedelta, timezone
        JST = timezone(timedelta(hours=+9), 'JST')
        new_flow_data['createdAt'] = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')
        # 複製を作成する
        new_flow = Flow(self.session, self.parent_uuid, new_label, new_flow_data, self.session.user)
        return new_flow

    @staticmethod
    def _get_select_stmt_for_nodes():
        from sqlalchemy import select, literal_column, table, text, String
        from sqlalchemy.sql import alias
        from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID

        """
        select distinct
               label as label,
               node ->> 'uuid' as uuid,
               node ->> 'type' as type,
               node ->> 'cacheCreatedAt' as cacheCreatedAt
        from  (select label,
                      uuid,
                      jsonb_array_elements(data #> '{flow,nodes}') as node
                from data
                where type='flow') F0
        )
        """
        sql = select([literal_column("label as label", type_=String),
                      literal_column("node ->> 'uuid' as uuid", type_=UUID),
                      literal_column("node ->> 'type' as type", type_=String),
                      literal_column("node ->> 'cacheCreatedAt' as cacheCreatedAt", type_=TIMESTAMP)
                     ],
                     distinct=True,
              ).select_from(
                    select([literal_column("label"),
                            literal_column("uuid"),
                            literal_column("jsonb_array_elements(data #> '{flow,nodes}') as node")
                           ],
                           table('data'))
                    .where(text("type='flow'")).alias('F0')
              )

        return sql

    # @staticmethod
    # def get_flows_referencing_frame(frame_uuid):
    #     """
    #     参照する入力frameとキャッシュframeを全て取得する
    #     """
    #     from sqlalchemy import select, text
    #     from sqlalchemy.sql import alias

    #     sql = Flow._get_select_stmt_for_nodes()
    #     sql = select(['*']).select_from(sql.alias('F')).where(text(f"uuid='{frame_uuid}'"))

    #     results = session.execute(sql)
    #     return [str(result['label']) for result in results]

    def get_src_frame_uuids(self):
        """
        参照する入力frameを全て取得する
        """
        from sqlalchemy import select, column, text, String
        from sqlalchemy.sql import alias

        inner_sql = Flow._get_select_stmt_for_nodes().\
                         where(text(f"uuid = '{self.uuid}' ")).\
                         alias('F')
        sql = select([column('uuid', String)], distinct=True).select_from(inner_sql).\
              where(text(f"type = 'frame'")).\
              where(text(f"(cacheCreatedAt is null or cacheCreatedAt = '' )")).\
              where(text(f"uuid is not null and uuid <> '' "))

        results = self.session.execute(sql)
        return [str(result['uuid']) for result in results]

    def get_cache_frame_uuids(self):
        """
        参照するキャッシュframeを全て取得する
        """
        from sqlalchemy import select, column, text, String
        from sqlalchemy.sql import alias

        inner_sql = Flow._get_select_stmt_for_nodes().\
                         where(text(f"uuid = '{self.uuid}' ")).\
                         alias('F')
        sql = select([column('uuid', String)], distinct=True).select_from(inner_sql).\
              where(text(f"type = 'frame'")).\
              where(text(f"(cacheCreatedAt is not null and cacheCreatedAt <> '' )")).\
              where(text(f"uuid is not null and uuid <> '' "))

        results = self.session.execute(sql)
        return [str(result['uuid']) for result in results]

    def get_sub_flow_uuids(self):
        """
        参照するSub Flowを全て取得する
        """
        from sqlalchemy import select, column, text, String
        from sqlalchemy.sql import alias

        inner_sql = Flow._get_select_stmt_for_nodes().\
                         where(text(f"uuid = '{self.uuid}' ")).\
                         alias('F')
        sql = select([column('uuid', String)], distinct=True).select_from(inner_sql).\
              where(text(f"type = 'flow'")).\
              where(text(f"uuid is not null and uuid <> '' "))

        results = self.session.execute(sql)
        return [str(result['uuid']) for result in results]

    def get_store_uuids(self):
        """
        参照するStoreを全て取得する
        """
        from sqlalchemy import select, column, text, String
        from sqlalchemy.sql import alias

        inner_sql = Flow._get_select_stmt_for_nodes().\
                         where(text(f"uuid = '{self.uuid}' ")).\
                         alias('F')
        sql = select([column('uuid', String)], distinct=True).select_from(inner_sql).\
              where(text(f"type = 'store'")).\
              where(text(f"uuid is not null and uuid <> '' "))

        results = self.session.execute(sql)
        return [str(result['uuid']) for result in results]

    def replace_uuid(self, old_uuid, new_uuid):
        """
        参照uuidを置き換える
        """
        flow_data = self.flow_data
        for node in flow_data['nodes']:
            if 'uuid' in node and node['uuid'] == old_uuid:
                node['uuid'] = new_uuid
        self.update_data(self.label, flow_data)

    def set_cache(self, node_id, cache_uuid):
        from datetime import datetime, timedelta, timezone

        flow_data = self.flow_data
        for node in flow_data['nodes']:
            if node['id'] == node_id:
                node['uuid'] = cache_uuid
                # 記録時間はUTC、表示時間は現地時間にすべきでは？？
                node['cacheCreatedAt'] = datetime.now(timezone(timedelta(hours=+9), 'JST')).strftime('%Y-%m-%d %H:%M:%S')
        self.update_data(self.label, flow_data)

    def to_json(self):
        return {'uuid'      : self.uuid,
                'type'      : Datum.FLOW_TYPE,
                'label'     : self.label,
                'creator'   : self.creator_str,
                'createdAt' : self.created_at_str}

    @staticmethod
    def create_flow(request_json, creator, data_source_name=None):
        """
        フローを作成する
        TODO: とりあえず、model.pyから移動した
        """
        import uuid
        import functools
        from datetime import datetime, timedelta, timezone

        if data_source_name is None:
            data_source_name = str(uuid.uuid4())

        def add_data_source_to_flow(source):
            '''
            フローに作成時にデータソースをつけるためのデコレータ
            '''
            def _deco(func):
                @functools.wraps(func)
                def deco():
                    if source is None:
                        return func()

                    if not source.get('uuid'):
                        return func()

                    data = func()
                    data_source = {
                        "id": "i",
                        "type": source.get('type'),
                        "dataSource": "csv",
                        "uuid": source.get('uuid'),
                        "label": source.get('label')
                    }

                    data['nodes'] = []
                    data['nodes'].append(data_source)
                    return data
                return deco
            return _deco

        def add_activity_to_flow(creator):
            '''
            フローに作成時に作成履歴をつけるためのデコレータ
            '''
            def _deco(func):
                @functools.wraps(func)
                def deco():
                    data = func()
                    data['creator'] = creator.name
                    JST = timezone(timedelta(hours=+9), 'JST')
                    data['createdAt'] = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')
                    return data
                return deco
            return _deco

        @add_data_source_to_flow(request_json.get('datasource'))
        @add_activity_to_flow(creator)
        def make_flow_json():
            data = {
                # 'projectId': get_project_by_uuid(request_json.get('project_uuid')),
                'projectId': None,
                'label': request_json.get('name'),
                'ports': [[],[]],
                'params': [],
                'description': ""
            }
            return data

        data = make_flow_json()

        return data
