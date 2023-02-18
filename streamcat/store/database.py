from streamcat.core import SavableDatum, Constraints
from .store import Store
from .database_conn import DatabaseConn

class Database(Store):
    """
    Databaseへの接続を表すStore
    """

    __mapper_args__ = {
        'polymorphic_identity' : 'database'
    }

    def __init__(self, session, parent, label, database_conn):
        """
        コンストラクタ
        """
        super().__init__(session, parent, SavableDatum.DATABASE_TYPE, label)
 
        # 接続情報はデータベースに保存する
        self._path = None

        # data列の値を作成する
        if database_conn is None:
            raise Exception('database_conn引数がNoneです')
        self._data = {'conn' : database_conn.to_json(encrypt_password=True)}

    @Constraints.prohibit_save_on_root
    @Constraints.set_project_role_on_adding
    def save(self):
        """
        Databaseを保存する
        """
        # 既にルートフォルダが存在する場合は、parent_id=NULLを許可しない
        from streamcat.store.factory import DatumFactory
        if self.parent_id is None and DatumFactory(self._session).count_root() > 0:
            raise Exception('You can not add root folder. A root already exists.')
        try:
            # Dataテーブルにレコードを新規追加する
            self._session.add(self)
        except Exception as e:
            self._session.rollback()
            raise e

    def update_data(self, label, database_conn, modifier=None):
        """
        Databaseのdata列を更新する
        """
        # ラベルに'\0'が含まれていれば取り除く
        new_label = SavableDatum.escape_label(label)

        try:
            # レコードを更新する
            self._label = new_label
            self._data['conn'] = database_conn.to_json(encrypt_password=True)
            self._modifier_id = (modifier or self._session.user).id
            self._session.update(self)
        except Exception as e:
            self._session.rollback()
            raise e

        return self

    @Constraints.delete_role_when_isolated     
    def delete(self):
        """
        Databaseを削除する
        """
        # 削除しようとするDatabaseが、DBに格納されているフローで使用されている場合は例外を送出する
        using_flow_uuids = self.get_flow_uuids_using_me()
        if len(using_flow_uuids) > 0:
            raise Exception(f"このStoreはローダ・セーバ({using_flow_uuids[0]['reference_label']})で使用しているため削除できません")

        try:
            # Databaseレコードを削除する
            self._session.delete(self)
        except Exception as e:
            self._session.rollback()
            raise e

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
        return DatabaseConn(self._data['conn'],
                            password_is_enctypted=True,
                            readable_or_raise=self._readable_or_raise)

    def valid_or_raise(self):
        """
        DB接続情報の形式チェックを行い、NGの場合は例外を送出する
        """
        database_conn = DatabaseConn(self._data['conn'], password_is_enctypted=True)
        return database_conn.valid_or_raise()

    def to_json(self):
        ret =  super().to_json()
        if self.readable:
            ret.update(self.conn.to_json())
        return ret
