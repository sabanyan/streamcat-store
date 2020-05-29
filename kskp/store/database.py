from kskp.core import Datum
from kskp.store import Store, DatabaseConn

class Database(Store):
    """
    Databaseへの接続を表すStore
    """

    __mapper_args__ = {
        'polymorphic_identity' : 'database'
    }

    def __init__(self, session, parent, label, database_conn, creator=None):
        """
        コンストラクタ
        """
        super().__init__(session, parent, Datum.DATABASE_TYPE, label, creator)
 
        # 接続情報はデータベースに保存する
        self._path = ''

        # data列の値を作成する
        if database_conn is None:
            raise Exception('database_conn引数がNoneです')
        self.data = {'conn' : database_conn.to_json()}

    def save(self):
        """
        Databaseを保存する
        """
        # 既にルートフォルダが存在する場合は、parent_id=NULLを許可しない
        from kskp.store.factory import DatumFactory
        if self.parent_id is None and DatumFactory(self.session).count_root() > 0:
            raise Exception('You can not add root folder. A root already exists.')
        try:
            # Dataテーブルにレコードを新規追加する
            self.session.add(self)
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.commit()

    def update_data(self, label, database_conn, modifier=None):
        """
        Databaseのdata列を更新する
        """
        # レコードを取得する
        datum = self.session.query(Datum).filter(Datum.uuid==self.uuid)\
                                    .filter(Datum.type==Datum.DATABASE_TYPE).one_or_none()
        if datum is None:
            raise Exception('no database is found by designated id.')

        # ラベルに'\0'が含まれていれば取り除く
        new_label = Datum.escape_label(label)

        try:
            # レコードを更新する
            # data = {'conn' : database_conn.to_json()}
            data = datum.data.copy()
            data['conn'] = database_conn.to_json()
            result = self.session.query(Datum).filter(Datum.uuid==self.uuid).one_or_none()
            if result is not None:
                result._label = new_label
                result._data = data
                result._modifier_id = (modifier or self.session.user).id
                self.session.update(result)
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.commit()

        return datum

    # def move(self, parent_uuid, modifier=None):
    #     """
    #     指定されたStoreの直下に移動する
    #     """
    #     # UUID値の形式チェックをする
    #     Datum.valid_uuid_or_raise(parent_uuid)

    #     from kskp.store.factory import DatumFactory
    #     to_folder = DatumFactory(self.session).find_by_uuid(parent_uuid)
    #     if to_folder.type != Datum.FOLDER_TYPE and to_folder.type != Datum.TRASH_TYPE:
    #         raise Exception('移動先の指定はフォルダまたはゴミ箱のUUIDしか許可していません')

    #     if parent_uuid == self.uuid:
    #         raise Exception('移動先と移動元の指定が同じです')

    #     # 移動元フォルダのidを覚えておく
    #     data = self.data.copy()
    #     data['prev_parent_id'] = self.parent_id

    #     try:
    #         # レコードを更新する
    #         # self.session.query(Datum).filter(Datum.id==self.id).update({'parent_id'   :to_folder.id
    #         #                                                       ,'_modifier_id':modifier.id})
    #         self.parent_id = to_folder.id
    #         self._data = data
    #         self._modifier_id = (modifier or self.session.user).id
    #         self.session.update(self)
    #     except Exception as e:
    #         self.session.rollback()
    #         raise e
    #     finally:
    #         self.session.commit()

    #     return self
        
    def delete(self):
        """
        Databaseを削除する
        """
        # 削除しようとするDatabaseが、DBに格納されているフローで使用されている場合は例外を送出する
        using_flow_uuids = self.get_flow_uuids_using_me()
        if len(using_flow_uuids) > 0:
            from kskp.store.factory import DatumFactory
            using_flow_label = DatumFactory(self.session).find_by_uuid(using_flow_uuids[0]).label
            raise Exception('このStoreはローダ・セーバ(%s)で使用しているため削除できません' % using_flow_label)

        try:
            # Databaseレコードを削除する
            self.session.delete(self)
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.commit()

    def remove_reference_only(self):
        """
        念の為Databaseも削除しない
        """
        pass

    @property
    def dbms(self):
        return self.conn.dbms

    @property
    def conn(self):
        return DatabaseConn.from_json(self.data['conn'])

    def valid_or_raise(self):
        """
        DB接続情報の形式チェックを行い、NGの場合は例外を送出する
        """
        database_conn = DatabaseConn.from_json(self.data['conn'])
        return database_conn.valid_or_raise()

    def to_json(self):
        ret =  {'uuid'      : self.uuid,
                'type'      : Datum.DATABASE_TYPE,
                'label'     : self.label,
                'creator'   : self.creator_str,
                'createdAt' : self.created_at_str}

        if self.readable:
            ret['prevFolderPath'] = self.get_prev_folder_path()
            database_conn = DatabaseConn.from_json(self.data['conn'])
            ret.update(database_conn.to_json())

        return ret