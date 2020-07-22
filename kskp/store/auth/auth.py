import os
from kskp.store import BaseModel
from sqlalchemy import Column, String, text, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import INTEGER, BOOLEAN, TIMESTAMP, ENUM

class Auth(BaseModel):
    READ_OP = 'read'
    WRITE_OP = 'write'
    DELETE_OP = 'delete'
    EXEC_OP = 'exec'
    OWN_OP = 'own'

    # テーブル名の定義
    __tablename__ = 'auths'

    # テーブルの制約
    __table_args__ = (
        PrimaryKeyConstraint('role_id', 'datum_id', 'operation'),
    )

    # 定義先スキーマ
    if 'KSKP_POSTGRESQL_SCHEMA_NAME' in os.environ:
        # テスト環境用のスキーマ
        __table_args__ = __table_args__ + ({'schema': os.environ['KSKP_POSTGRESQL_SCHEMA_NAME']} ,)

    # 列名と列のデータ型等の定義
    role_id     = Column(INTEGER, primary_key=True)
    datum_id     = Column(INTEGER, primary_key=True)
    operation    = Column(ENUM(READ_OP, WRITE_OP, DELETE_OP, EXEC_OP, OWN_OP, name='op_type'), primary_key=True)
    permission   = Column(BOOLEAN, nullable=False)
    _creator_id  = Column('creator', INTEGER)
    _modifier_id = Column('modifier', INTEGER)
    created_at   = Column(TIMESTAMP, default=text('statement_timestamp()'))
    modified_at  = Column(TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()'))

    def __init__(self, session, role_id, datum_id, operation, permission):
        """
        コンストラクタ
        """
        # SQLAlchemy Session
        self._session = session

        self.role_id = role_id
        self.datum_id = datum_id
        self.operation = operation
        self.permission = permission

        # creator, modifier
        if session is not None and session.user is not None:
            self._creator_id = session.user.id
            self._modifier_id = session.user.id

    @property
    def creator(self):
        from kskp.store.factory import UserFactory
        if self._creator_id is None:
            return None
        return UserFactory(self._session).find_by_id(self._creator_id, allow_no_result=True)

    @property
    def modifier(self):
        from kskp.store.factory import UserFactory
        if self._modifier_id is None:
            return None
        return UserFactory(self._session).find_by_id(self._modifier_id, allow_no_result=True)
        
    def save(self):
        """
        Authを保存する
        """
        # Authテーブルにレコードを新規追加する
        self._session.add(self)
        self._session.commit()

    def update(self, permission):
        try:
            # レコードを更新する
            self.permission = permission
            self._modifier_id = self._session.user and self._session.user.id
            self._session.update(self)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

    def delete(self):
        """
        Authを削除する
        """
        self._session.delete(self)
        self._session.commit()
