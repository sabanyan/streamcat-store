from streamcat.core import Datum, Constraints
from .lock import lock_required
from .flow_data import FlowData

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
            raise Exception(f'Flow.__init__()の引数flow_dataに{type(flow_data).__name__}型が渡されましたFlowData型を渡してください.')

        self._data = {'label':label, 'flow':flow_data.to_json()}

        # DBに保存する前のFlowへの参照と更新と実行権限は制限しない
        self._permissions = Datum.PERMISSION_READ | Datum.PERMISSION_WRITE | Datum.PERMISSION_EXEC

        # フローデータの妥当性を検証する
        # self.valid_uuids_in_flowdata_or_raise()

    @property
    def flow_data(self):
        from typing import List

        def select_unreadables(uuids:List[str]) -> List[str]:
            """
            指定したuuidのうち参照権限の無いuuidを返す
            """
            results = self._session.query(Datum).filter(Datum.uuid.in_(uuids)).all(ignore_authz=True)
            return [result.uuid for result in results if not result.readable]

        def select_unexecutables(uuids:List[str]) -> List[str]:
            """
            指定したuuidのうち実行権限の無いuuidを返す
            """
            results = self._session.query(Datum).filter(Datum.uuid.in_(uuids)).all(ignore_authz=True)
            return [result.uuid for result in results if not result.executable]

        return FlowData(self._data['flow'], select_unreadables, select_unexecutables, self._readable_or_raise, self._executable_or_raise)

    def _executable_or_raise(self):
        from streamcat.store.auth import NotAuthorizedException
        if self.executable is None:
            raise NotAuthorizedException(f'{self.label}の実行権限がNoneです(save後のDatumオブジェクトは実行権限がNoneになります)')
        if not self.executable:
            raise NotAuthorizedException(f'{self._session.user.name}は{self.label}の実行権限がありません')

    @Constraints.prohibit_save_on_root
    @Constraints.set_project_role_on_adding
    def save(self, disable_validate_reference=False):
        """
        Flowを保存する
        """
        # 既にルートフォルダが存在する場合は、parent_id=NULLを許可しない
        from streamcat.store.factory import DatumFactory
        if self.parent_id is None and DatumFactory(self._session).count_root() > 0:
            raise Exception('You can not add another root flow. A root already exists.')

        # 
        # TODO: フローJSONの書式修正による後方互換!
        # 
        self.flow_data.remove_uuid_from_param()

        # 不正なフローJSONがDBに格納されないよう、ここで書式の検証をする
        self.flow_data.valid_flow_json_or_raise()

        # フローデータの妥当性を検証する
        # NOTE: フローのインポート時はファイルのインポート順によっては例外が発生するため、
        #       disable_validate_reference=Trueにしている
        disable_validate_reference or self.valid_uuids_in_flowdata_or_raise()

        try:
            # Dataテーブルにレコードを新規追加する
            self._session.add(self)
        except Exception as e:
            self._session.rollback()
            if self.edit_lock:
                # 編集ロックにより更新できなかった場合
                from streamcat.store import EditLockedException
                raise EditLockedException('編集ロックが掛かっているため新規追加できません')
            else:
                raise e
        finally:
            self._session.commit()

    @lock_required
    def update_label(self, label, lock_uuid=None, modifier=None):
        """
        Flowのラベルを更新する
        """
        # ラベルに'\0'が含まれていれば取り除く
        new_label = Datum.escape_label(label)

        try:
            # ラベルを更新する
            self._label = new_label
            # フローJsonにあるlabelは廃止予定だが、label列と同期しておく
            self._data['flow']['label'] = new_label
            self._modifier_id = (modifier or self._session.user).id
            self._session.update(self)
        except Exception as e:
            self._session.rollback()
            if self.edit_lock:
                # 編集ロックにより更新できなかった場合
                from streamcat.store import EditLockedException
                raise EditLockedException('編集ロックが掛かっているため更新できません')
            else:
                raise e
        finally:
            self._session.commit()

        return self

    @lock_required
    def update_data(self, label, flow_data, ignore_lock=False, lock_uuid=None, modifier=None):
        """
        Flowのdata列を更新する
        """
        if not isinstance(flow_data, FlowData):
            raise Exception(f'Flow.update_data()の引数flow_dataに{type(flow_data).__name__}型が渡されましたFlowData型を渡してください.')

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

        # マスクされたノードがあればマスクを外す
        flow_data.unmask_nodes(prev_flow_json=self._data['flow'])

        # 
        # TODO: フローJSONの書式修正による後方互換!
        # 
        flow_data.remove_uuid_from_param()

        # 不正なフローJSONがDBに格納されないよう、ここで書式の検証をする
        flow_data.valid_flow_json_or_raise()

        # フローデータの妥当性を検証する
        self.valid_uuids_in_flowdata_or_raise()

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
                from streamcat.store import EditLockedException
                raise EditLockedException('編集ロックが掛かっているため更新できません')
            else:
                raise e
        finally:
            self._session.commit()

        # ここでflowを返すとtest_model.pyでテストが通らない
        return self

    @lock_required
    def move(self, parent_uuid, lock_uuid=None, modifier=None):
        from streamcat.store.auth import NotAuthorizedException

        try:
            return super().move(parent_uuid, modifier)
        except NotAuthorizedException as e:
            if self.edit_lock:
                # 編集ロックにより移動できなかった場合
                from streamcat.store import EditLockedException
                raise EditLockedException('編集ロックが掛かっているため移動できません')
            else:
                raise e

    def throw_away(self, lock_uuid=None):
        """
        Flowをゴミ箱にほかす
        """
        from streamcat.store.factory import DatumFactory
        factory = DatumFactory(self._session)
        trash_folder = factory.load_trash_folder()

        # 削除しようとするflowが、フローで使用されている場合は例外を送出する
        using_flow_uuids = self.get_flow_uuids_using_me()
        if len(using_flow_uuids) > 0:
            raise Exception(f"このフローは別のフロー({using_flow_uuids[0]['reference_label']})で使用しているため削除できません")

        try:
            return self.move(trash_folder.uuid ,lock_uuid=lock_uuid)
        except Exception as e:
            if self.edit_lock:
                # 編集ロックにより更新できなかった場合
                from streamcat.store import EditLockedException
                raise EditLockedException('編集ロックが掛かっているため削除できません')
            else:
                raise e

    @lock_required
    @Constraints.delete_role_when_isolated
    def delete(self, lock_uuid=None):
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
                from streamcat.store import EditLockedException
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
        自身の複製を作成して保存する
        NOTE: 自分の複製をメモリに作成することをcopy、
              ライブラリに作成することをduplicateと呼称する
        """
        # ラベルと作成者については、指定された値を新たに設定する
        new_flow_data = self.flow_data.copy()
        new_flow_data.label = new_label
        new_flow_data.creator = self._session.user.name
        # FIXIT : Dataテーブルのcreated_at列と時刻を合わせたい
        from datetime import datetime, timedelta, timezone
        JST = timezone(timedelta(hours=+9), 'JST')
        new_flow_data.createdAt = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')
        # 複製を作成する
        parent = self.find_parent()
        new_flow = parent.create_flow(new_label, new_flow_data)
        # new_flow._replace_cache()のデコレータが機能するにはnew_flowのidを採番する必要がある
        new_flow.save()
        new_flow = new_flow.reload()

        # フロー間でキャッシュを共有すると、キャッシュ削除操作により不整合が発生する
        # そのためフローを複製する時はキャッシュも複製する
        import io
        from streamcat.store.factory import DatumFactory
        for cache_uuid in new_flow.flow_data.get_cache_frame_uuids():
            factory = DatumFactory(self._session)
            if not factory.exists(cache_uuid):
                continue
            cache = factory.find_by_uuid(cache_uuid)
            # キャッシュを複製する(ファイルは複製されない)
            parent = cache.find_parent()
            new_cache = parent.create_frame(cache.label + ' のコピー', io.BytesIO(b''))
            # ファイルは複製元と共有する(浅いコピー)
            new_cache.save(file_path=cache.path)
            # フローのキャッシュUUIDに新しいキャッシュを設定する
            new_flow._replace_cache(cache_uuid, new_cache)

        return new_flow.update_data(new_flow.label, new_flow.flow_data)

    @property
    def edit_lock(self):
        """
        編集ロックの値を取得する
        """
        from streamcat.store.factory import RoleFactory, AuthFactory
        from streamcat.store.auth import Auth
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
        self.set_edit_lock(value)        

    @lock_required
    def set_edit_lock(self, value:bool, lock_uuid=None):
        """
        編集ロックを設定する
        """
        from streamcat.store.auth import NotAuthorizedException
        # 閲覧者には編集ロックの値を変更させない
        if self.writable_without_edit_lock is None:
            raise NotAuthorizedException(f'{self.label}の更新権限がNoneです(save後またはrollback後のDatumオブジェクトは更新権限がNoneになります)')
        elif not self.writable_without_edit_lock:
            raise NotAuthorizedException(f'({self._session.user.name})は{self.label}の編集ロックの更新権限がありません')

        from streamcat.store.factory import RoleFactory
        factory = RoleFactory(self._session)
        edit_lock_role = factory.load_edit_lock_role()
        # write=Falseでedit_lock_roleに参加する全てのユーザはこのフローの更新権限を失う
        edit_lock_value = not value and None
        edit_lock_role.init_authz(self.id, read=None, write=edit_lock_value)

        # self._permissionsを更新する
        # (編集ロックとself.writableの値を同期させる)
        self.reload()

    def valid_uuids_in_flowdata_or_raise(self):
        from streamcat.store.factory import DatumFactory
        factory = DatumFactory(self._session)
        # 参照するフレームがゴミ箱に存在しないことを確認する
        # (ignore_authz=True: ノードUUIDのマスキングをしない)
        for frame_uuid in self.flow_data.get_src_frame_uuids(ignore_authz=True):
            if not factory.exists(frame_uuid):
                raise Exception(f'参照するフレーム({frame_uuid})は存在しません')
            elif factory.trashed(frame_uuid):
                frame = factory.find_by_uuid(frame_uuid)
                raise Exception(f'ゴミ箱にあるフレーム({frame.label})は使用できません')

        # 参照するサブフローがゴミ箱に存在しないことを確認する
        # (ignore_authz=True: ノードUUIDのマスキングをしない)
        for flow_uuid in self.flow_data.get_sub_flow_uuids(ignore_authz=True):
            if not factory.exists(flow_uuid):
                raise Exception(f'参照するフロー({flow_uuid})は存在しません')
            elif factory.trashed(flow_uuid):
                flow = factory.find_by_uuid(flow_uuid)
                raise Exception(f'ゴミ箱にあるフロー({flow.label})は使用できません')

    @Constraints.set_project_role_on_set_cache
    def set_cache(self, node_id, cache, lock_uuid=None):
        """
        指定するノードidにキャッシュを設定する
        """
        self.flow_data._set_cache(node_id, cache.uuid)
        self.update_data(self.label, self.flow_data, lock_uuid=lock_uuid)

    def unset_cache(self, node_id, ignore_lock=False, lock_uuid=None) -> str:
        """
        指定するノードidのキャッシュを削除する
        """
        unset_cache_uuid = self.flow_data._unset_cache(node_id)
        if unset_cache_uuid is None:
            return None
        self.update_data(self.label, self.flow_data, ignore_lock=ignore_lock, lock_uuid=lock_uuid)
        return unset_cache_uuid

    def unset_all_caches(self, lock_uuid=None):
        """
        全てのキャッシュを削除する
        """
        unset_cache_uuids = []
        for node in self.flow_data.get_nodes():
            unset_cache_uuid = self.flow_data._unset_cache(node['id'])
            if unset_cache_uuid is None:
                continue
            unset_cache_uuids.append(unset_cache_uuid)
        self.update_data(self.label, self.flow_data, lock_uuid=lock_uuid)
        return unset_cache_uuids

    @Constraints.set_project_role_on_set_cache
    def _replace_cache(self, old_uuid, cache):
        """
        指定するuuidのノードにキャッシュを設定する
        """
        self.flow_data._replace_uuid(old_uuid, cache.uuid)

    def replace_uuids(self, uuid_conv_table):
        """
        指定するuuidのノードのuuidを置き換える
        uuid_conv_table: {old_uuid : new_uuid}
        """
        for old_uuid, new_uuid in uuid_conv_table.items():
            self.flow_data._replace_uuid(old_uuid, new_uuid)

    def to_json(self):
        ret = super().to_json()
        # 排他ロックの再取得の判定に最終更新時刻を用いる
        ret['modifiedAt'] = self.modified_at.strftime('%Y-%m-%d %H:%M:%S.%f')
        ret['editLock'] = self.edit_lock
        ret['allowlist']['execute'] = self.executable
        ret['allowlist']['export'] = self._session.has_usr_admin()
        ret['allowlist']['lock'] = self.writable_without_edit_lock
        return ret
