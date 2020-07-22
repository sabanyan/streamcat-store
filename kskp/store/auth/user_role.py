import os
from sqlalchemy import Column, text, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import INTEGER, TIMESTAMP
from kskp.store import BaseModel

class UserRole(BaseModel):
    # テーブル名の定義
    __tablename__ = 'users_roles'

    # テーブルの制約
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'role_id'),
    )

    # 定義先スキーマ
    if 'KSKP_POSTGRESQL_SCHEMA_NAME' in os.environ:
        # テスト環境用のスキーマ
        __table_args__ = __table_args__ + ({'schema': os.environ['KSKP_POSTGRESQL_SCHEMA_NAME']} ,)

    # 列名と列のデータ型等の定義
    user_id      = Column(INTEGER, primary_key=True)
    role_id     = Column(INTEGER, primary_key=True)
    _creator_id  = Column('creator', INTEGER)
    _modifier_id = Column('modifier', INTEGER)
    created_at   = Column(TIMESTAMP, default=text('statement_timestamp()'))
    modified_at  = Column(TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()'))

    def __init__(self, session, user_id, role_id):
        """
        コンストラクタ
        """
        # SQLAlchemy Session
        self._session = session

        self.user_id = user_id
        self.role_id = role_id

        # creator, modifier
        if session is not None and session.user is not None:
            self._creator_id = session.user.id
            self._modifier_id = session.user.id

    @property
    def creator(self):
        from kskp.store.factory import UserFactory
        if self._creator_id is None:
            return None
        return UserFactory(self._session).find_by_id(self._creator_id)

    @property
    def modifier(self):
        from kskp.store.factory import UserFactory
        if self._modifier_id is None:
            return None
        return UserFactory(self._session).find_by_id(self._modifier_id)

    def save(self):
        """
        UserRoleを保存する
        """
        self._session.add(self)
        self._session.commit()

    def delete(self):
        """
        UserRoleを削除する
        """
        self._session.delete(self)
        self._session.commit()
