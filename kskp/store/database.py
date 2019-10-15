from . import ss as session

from kskp.core import Datum
from kskp.store import Store, Flow, DatabaseConn, STORE_DIR

class Database(Store):
    """
    Databaseへの接続を表すStore
    """
    def __init__(self, parent_uuid, label, database_conn, creator=None):
        """
        コンストラクタ
        """
        super().__init__(parent_uuid, Datum.DATABASE_TYPE, label, creator)
 
        # 接続情報はデータベースに保存する
        self._path = ''

        # data列の値を作成する
        if database_conn is None:
            raise Exception('database_conn引数がNoneです')
        self.data = {'conn' : database_conn.to_json()}

    @staticmethod
    def find_by_uuid(uuid):
        """
        指定されたuuidを持つDatabaseを取得する
        """
        datum = session.query(Datum).filter(Datum.uuid==uuid)\
                                    .filter(Datum.type==Datum.DATABASE_TYPE).one_or_none()
        if datum is None:
            raise Exception('no database is found by designated id.')
        return Database.convert_to_database(datum)

    @staticmethod
    def exists(uuid):
        """
        指定されたuuidを持つDatabaseが存在する場合はTrueを返す
        """
        # UUID値の形式チェックをする
        if not Datum.is_valid_uuid(uuid):
            return False
        result = session.query(Datum).filter(Datum.uuid==uuid)\
                                     .filter(Datum.type==Datum.DATABASE_TYPE).count()
        return result > 0

    @staticmethod
    def convert_to_database(datum):
        parent_uuid = Datum.get_uuid_by_id(datum.parent_id)
        database_conn = DatabaseConn.from_json(datum.data2['conn'])
        database = Database(parent_uuid, datum.label, database_conn, datum.creator)
        database.id = datum.id
        database.uuid = datum.uuid
        database._path = datum._path
        database.modifier = datum.modifier
        database.created_at = datum.created_at
        database.modified_at = datum.modified_at
        return database

    def save(self):
        """
        Databaseを保存する
        """
        # 既にルートフォルダが存在する場合は、parent_id=NULLを許可しない
        if self.parent_id is None and Datum.count_root() > 0:
            raise Exception('You can not add root folder. A root already exists.')
        try:
            # Dataテーブルにレコードを新規追加する
            session.add(self)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.commit()

    @staticmethod
    def update_data(uuid, label, database_conn, modifier):
        """
        Databaseのdata列を更新する
        """
        # UUID値の形式チェックをする
        Datum.valid_uuid_or_raise(uuid)
        # レコードを取得する
        datum = session.query(Datum).filter(Datum.uuid==uuid)\
                                    .filter(Datum.type==Datum.DATABASE_TYPE).one_or_none()
        if datum is None:
            raise Exception('no database is found by designated id.')

        # ラベルに'\0'が含まれていれば取り除く
        new_label = Datum.escape_label(label)

        try:
            # レコードを更新する
            data = {'conn' : database_conn.to_json()}
            session.query(Datum).filter(Datum.uuid==uuid).update({'_label'   :new_label,
                                                                  'data'     :data,
                                                                  'modifier' :modifier})
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.commit()

        return Database.convert_to_database(datum)

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
        Databaseを削除する
        """
        # 削除しようとするDatabaseが、DBに格納されているフローで使用されている場合は例外を送出する
        using_flow_uuids = Datum.get_flow_uuids_using_other_datum(self.uuid)
        if len(using_flow_uuids) > 0:
            using_flow_label= Flow.find_by_uuid(using_flow_uuids[0]).label
            raise Exception('このStoreはローダ・セーバ(%s)で使用しているため削除できません' % using_flow_label)

        try:
            # Databaseレコードを削除する
            session.query(Datum).filter(Datum.id==self.id)\
                                .filter(Datum.type==Datum.DATABASE_TYPE).delete()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.commit()

    def remove_reference_only(self):
        """
        念の為Databaseも削除しない
        """
        pass

    def get_database_uri(self):
        database_conn = DatabaseConn.from_json(self.data2['conn'])
        return database_conn.get_database_uri()

    def valid_or_raise(self):
        """
        DB接続情報の形式チェックを行い、NGの場合は例外を送出する
        """
        database_conn = DatabaseConn.from_json(self.data2['conn'])
        return database_conn.valid_or_raise()

    def to_json(self):
        database_conn = DatabaseConn.from_json(self.data2['conn'])
        
        return {'uuid'      : self.uuid,
                'type'      : Datum.DATABASE_TYPE,
                'label'     : self.label,
                'dbms'      : database_conn.dbms,
                'hostname'  : database_conn.hostname,
                'port'      : database_conn.port,
                'database'  : database_conn.database,
                'user_id'   : database_conn.user_id,
                'password'  : database_conn.password,
                'creator'   : Datum.get_user_name_by_user_id(self.creator),
                'createdAt' : self.created_at_str}

    @property
    def content(self):
        return self