from kskp.core import Datum, Constraints
from kskp.store import FlowData

class Flow(Datum):

    __mapper_args__ = {
        'polymorphic_identity' : 'flow'
    }

    def __init__(self, session, parent, label, flow_data):
        """
        コンストラクタ
        flow_data : FlowDataオブジェクトを指定する
        """
        super().__init__(session, parent, Datum.FLOW_TYPE, label)

        # フローデータはファイルに保存せず、データベースに保存する
        self._path = None

        # data列の値を作成する
        if not isinstance(flow_data, FlowData):
            raise Exception(f'flow_dataはFlowDataではありません')
        self._data = {'label' : label, 'flow' : flow_data.to_json()}

        # DBに保存する前のFlowへの参照と更新と実行権限は制限しない
        self._permissions = 0b1110

        # フローデータの妥当性を検証する
        self.valid_uuids_in_flowdata_or_raise()

    @property
    def flow_data(self):
        def is_readable(uuid):
            """
            指定されたuuidのDatumのreadableの値を取得する
            """
            data = self._session.query(Datum).filter(Datum.uuid==uuid).all(ignore_authz=True)
            if len(data) == 0:
                return False
            return data[0].readable

        return FlowData(self._data['flow'], is_readable, self._readable_or_raise, self._executable_or_raise)

    # @property
    # def executable(self) -> bool:
    #     # DBに保存する前のFlowの実行権限は制限しない
    #     return self.id is None or self._session.executable(self)

    def _executable_or_raise(self):
        from kskp.store.auth import NotAuthorizedException
        if self.executable is None:
            raise NotAuthorizedException(f'{self.label}の実行権限がNoneです(save後のDatumオブジェクトは実行権限がNoneになります)')
        if not self.executable:
            raise NotAuthorizedException(f'{self._session.user.name}は{self.label}の実行権限がありません')

    @Constraints.prohibit_save_on_root
    @Constraints.set_project_role_on_adding
    def save(self):
        """
        Flowを保存する
        """
        # 既にルートフォルダが存在する場合は、parent_id=NULLを許可しない
        from kskp.store.factory import DatumFactory
        if self.parent_id is None and DatumFactory(self._session).count_root() > 0:
            raise Exception('You can not add another root flow. A root already exists.')
        try:
            # Dataテーブルにレコードを新規追加する
            self._session.add(self)
        except Exception as e:
            self._session.rollback()
            if self.edit_lock:
                # 編集ロックにより更新できなかった場合
                from kskp.store import EditLockedException
                raise EditLockedException('編集ロックが掛かっているため新規追加できません')
            else:
                raise e
        finally:
            self._session.commit()

    def update_data(self, label, flow_data, modifier=None):
        """
        Flowのdata列を更新する
        """

        if not isinstance(flow_data, FlowData):
            raise Exception(f'flow_dataはFlowDataではありません.')

        # # 参照するフレームがライブラリに存在することを確認する
        # for frame_uuid in self.get_src_frame_uuids():
        #     if not Frame.exists(frame_uuid):
        #         raise Exception(f'フレーム({frame_uuid})がライブラリにありません')

        # # 参照するサブフローがライブラリに存在することを確認する
        # for flow_uuid in self.get_sub_flow_uuids():
        #     if not Flow.exists(flow_uuid):
        #         raise Exception(f'フロー({flow_uuid})がライブラリにありません')

        # フローデータの妥当性を検証する
        self.valid_uuids_in_flowdata_or_raise()

        # ラベルに'\0'が含まれていれば取り除く
        new_label = Datum.escape_label(label)
        # 更新データを作成する
        # data = {'label' : new_label, 'flow' : flow_json}
        # data = self.data.copy()
        # data['flow'] = flow_json
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
            self._data['flow'] = flow_data.to_json()
            self._modifier_id = (modifier or self._session.user).id
            self._session.update(self)
        except Exception as e:
            self._session.rollback()
            if self.edit_lock:
                # 編集ロックにより更新できなかった場合
                from kskp.store import EditLockedException
                raise EditLockedException('編集ロックが掛かっているため更新できません')
            else:
                raise e
        finally:
            self._session.commit()

        # ここでflowを返すとtest_model.pyでテストが通らない
        return self

    def move(self, parent_uuid, modifier=None):
        from kskp.store.auth import NotAuthorizedException

        try:
            return super().move(parent_uuid, modifier)
        except NotAuthorizedException as e:
            if self.edit_lock:
                # 編集ロックにより移動できなかった場合
                from kskp.store import EditLockedException
                raise EditLockedException('編集ロックが掛かっているため移動できません')
            else:
                raise e

    def throw_away(self):
        """
        Flowをゴミ箱にほかす
        """
        from kskp.store.factory import DatumFactory
        factory = DatumFactory(self._session)
        trash_folder = factory.load_trash_folder()

        # 削除しようとするflowが、フローで使用されている場合は例外を送出する
        using_flow_uuids = self.get_flow_uuids_using_me()
        if len(using_flow_uuids) > 0:
            raise Exception(f"このフローは別のフロー({using_flow_uuids[0]['reference_label']})で使用しているため削除できません")

        try:
            return self.move(trash_folder.uuid)
        except Exception as e:
            if self.edit_lock:
                # 編集ロックにより更新できなかった場合
                from kskp.store import EditLockedException
                raise EditLockedException('編集ロックが掛かっているため削除できません')
            else:
                raise e

    @Constraints.delete_role_when_isolated
    def delete(self):
        """
        Flowを削除する
        """
        # 削除しようとするFlowが、DBに格納されているフローで使用されている場合は例外を送出する
        # 2019/07/29現在下記のコードはpostgres9.6では動かない、postgres11.1では動作確認している
        using_flow_uuids = self.get_flow_uuids_using_me()
        if len(using_flow_uuids) > 0:
            raise Exception(f"このフローは別のフロー({using_flow_uuids[0]['reference_label']})で使用しているため削除できません")

        try:
            # フレームレコードを削除する
            self._session.delete(self)
        except Exception as e:
            self._session.rollback()
            if self.edit_lock:
                # 編集ロックにより更新できなかった場合
                from kskp.store import EditLockedException
                raise EditLockedException('編集ロックが掛かっているため削除できません')
            else:
                raise e
        finally:
            self._session.commit()
            
    def remove_reference_only(self):
        """
        念の為Flowは削除しない
        """
        pass

    def duplicate(self, new_label):
        """
        自身の複製を作成する
        """
        # ラベルと作成者については、指定された値を新たに設定する
        new_flow_json = self.flow_data.to_json()
        new_flow_json['label'] = new_label
        new_flow_json['creator'] = self._session.user.name
        # FIXIT : Dataテーブルのcreated_at列と時刻を合わせたい
        from datetime import datetime, timedelta, timezone
        JST = timezone(timedelta(hours=+9), 'JST')
        new_flow_json['createdAt'] = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')
        # 複製を作成する
        parent = self.find_parent()
        new_flow = parent.create_flow(new_label, FlowData(new_flow_json))

        # フロー間でキャッシュを共有すると、キャッシュ削除操作により不整合が発生する
        # そのためフローを複製する時はキャッシュも複製する
        import io
        from kskp.store.factory import DatumFactory
        old_new_uuid_pairs = {}
        for cache_uuid in new_flow.get_cache_frame_uuids():
            factory = DatumFactory(self._session)
            if not factory.exists(cache_uuid):
                continue
            cache = factory.find_by_uuid(cache_uuid)
            # キャッシュを複製する(ファイルは複製されない)
            parent = cache.find_parent()
            new_cache = parent.create_frame(cache.label + ' のコピー', io.BytesIO(b''))
            # ファイルは複製元と共有する(浅いコピー)
            new_cache.save(file_path=cache.path)
            # 新旧キャッシュの対応リストに記録する
            old_new_uuid_pairs[cache_uuid] = new_cache.uuid
        # フローのキャッシュUUIDを新しいキャッシュUUIDに置き換える
        new_flow.replace_uuids(old_new_uuid_pairs)

        return new_flow

    @property
    def edit_lock(self):
        """
        編集ロックの値を取得する
        """
        from kskp.store.factory import RoleFactory, AuthFactory
        from kskp.store.auth import Auth
        role_factory = RoleFactory(self._session)
        auth_factory = AuthFactory(self._session)
        edit_lock_role = role_factory.load_edit_lock_role()

        if auth_factory.exists(edit_lock_role.id, self.id, Auth.WRITE_OP):
            auth = auth_factory.find_by_id(edit_lock_role.id, self.id, Auth.WRITE_OP)
            # permission=Falseであれば編集ロックが掛かっている
            return not auth.permission
        else:
            # 権限レコードが存在しなければ編集ロックは掛かっていない
            return False

    @edit_lock.setter
    def edit_lock(self, value:bool):
        """
        編集ロックを設定する
        """
        from kskp.store.auth import NotAuthorizedException
        if not self._session.writable(self, ignore_self_edit_lock=True):
            raise NotAuthorizedException(f'({self._session.user.name})は{self.label}の編集ロックの更新権限がありません')

        from kskp.store.factory import RoleFactory
        factory = RoleFactory(self._session)
        edit_lock_role = factory.load_edit_lock_role()
        # write=Falseでedit_lock_roleに参加する全てのユーザはこのフローの更新権限を失う
        edit_lock_value = not value and None
        edit_lock_role.init_authz(self.id, read=None, write=edit_lock_value)

    @staticmethod
    def _get_select_stmt_for_nodes():
        from sqlalchemy import select, literal_column, text, String
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

        # DatumのTableオブジェクト
        D = Datum.__table__

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
                           ])
                    .select_from(D)
                    .where(Datum.type==Datum.FLOW_TYPE).alias('F0')
              )

        return sql

    def valid_uuids_in_flowdata_or_raise(self):
        from kskp.store.factory import DatumFactory
        factory = DatumFactory(self._session)
        # 参照するフレームがゴミ箱に存在しないことを確認する
        for frame_uuid in self.get_src_frame_uuids():
            if factory.trashed(frame_uuid):
                frame = factory.find_by_uuid(frame_uuid)
                raise Exception(f'ゴミ箱にあるフレーム({frame.label})は使用できません')

        # 参照するサブフローがゴミ箱に存在しないことを確認する
        for flow_uuid in self.get_sub_flow_uuids():
            if factory.trashed(flow_uuid):
                flow = factory.find_by_uuid(flow_uuid)
                raise Exception(f'ゴミ箱にあるフロー({flow.label})は使用できません')

    def get_src_frame_uuids(self):
        """
        参照する入力frameを全て取得する
        """
        ret = []
        flow_data = self.flow_data
        
        if not flow_data.has_nodes:
            return ret

        for node in flow_data.get_nodes():
            if node['type'] != 'frame':
                continue
            if 'cacheCreatedAt' in node and\
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
        flow_data = self.flow_data
        
        if not flow_data.has_nodes:
            return ret

        for node in flow_data.get_nodes():
            if node['type'] != 'frame':
                continue
            if 'cacheCreatedAt' not in node or\
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
        flow_data = self.flow_data

        if not flow_data.has_nodes:
            return ret

        for node in flow_data.get_nodes():
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
        flow_data = self.flow_data

        if not flow_data.has_nodes:
            return ret

        for node in flow_data.get_nodes():
            if node['type'] != 'store':
                continue
            if 'uuid' not in node or node['uuid'] is None or node['uuid'] == '':
                continue
            if node['uuid'] in ret:
                continue
            ret.append(node['uuid'])
        return ret

    # def replace_uuid(self, old_uuid, new_uuid):
    #     """
    #     参照uuidを置き換える
    #     """
    #     flow_data = self.flow_data
    #     for node in flow_data['nodes']:
    #         if 'uuid' in node and node['uuid'] == old_uuid:
    #             node['uuid'] = new_uuid
    #     self.update_data(self.label, flow_data)

    def replace_uuids(self, old_new_uuid_pairs):
        """
        参照uuidを置き換える
        """
        flow_data = self.flow_data

        if not flow_data.has_nodes:
            return

        for node in flow_data.get_nodes():
            for old_uuid, new_uuid in old_new_uuid_pairs.items():
                if 'uuid' in node and node['uuid'] == old_uuid:
                    node['uuid'] = new_uuid
                    break

    @Constraints.set_project_role_on_set_cache
    def set_cache(self, node_id, cache):
        from datetime import datetime, timedelta, timezone

        flow_data = self.flow_data

        if not flow_data.has_nodes:
            return

        for node in flow_data.get_nodes():
            if node['id'] == node_id:
                node['uuid'] = cache.uuid
                # 記録時間はUTC、表示時間は現地時間にすべきでは？？
                node['cacheCreatedAt'] = datetime.now(timezone(timedelta(hours=+9), 'JST')).strftime('%Y-%m-%d %H:%M:%S')
        # self.update_data(self.label, flow_data)

    def to_json(self):
        ret = super().to_json()
        ret['editLock'] = self.edit_lock
        ret['allowlist']['execute'] = self.executable
        ret['allowlist']['lock'] = self.writable
        return ret

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

        return FlowData(data)
