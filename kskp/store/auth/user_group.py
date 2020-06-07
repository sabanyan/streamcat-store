import os
from sqlalchemy import Column, text, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import INTEGER, TIMESTAMP
from kskp.store import BaseModel

class UserGroup(BaseModel):
    # テーブル名の定義
    __tablename__ = 'users_groups'

    # テーブルの制約
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'group_id'),
    )

    # 定義先スキーマ
    if 'KSKP_POSTGRESQL_SCHEMA_NAME' in os.environ:
        # テスト環境用のスキーマ
        __table_args__ = __table_args__ + ({'schema': os.environ['KSKP_POSTGRESQL_SCHEMA_NAME']} ,)

    # 列名と列のデータ型等の定義
    user_id      = Column(INTEGER, primary_key=True)
    group_id     = Column(INTEGER, primary_key=True)
    _creator_id  = Column('creator', INTEGER)
    _modifier_id = Column('modifier', INTEGER)
    created_at   = Column(TIMESTAMP, default=text('statement_timestamp()'))
    modified_at  = Column(TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()'))

    def __init__(self, session, user_id, group_id, creator=None):
        """
        コンストラクタ
        """
        # SQLAlchemy Session
        self.session = session

        self.user_id = user_id
        self.group_id = group_id

        # creator, modifier
        if creator is not None:
            self._creator_id = creator.id
            self._modifier_id = creator.id

    @property
    def creator(self):
        from kskp.store.factory import UserFactory
        if self._creator_id is None:
            return None
        return UserFactory(self.session).find_by_id(self._creator_id)

    @property
    def modifier(self):
        from kskp.store.factory import UserFactory
        if self._modifier_id is None:
            return None
        return UserFactory(self.session).find_by_id(self._modifier_id)

    def save(self):
        """
        UserGroupを保存する
        """
        self.session.add(self)
        self.session.commit()

    def delete(self):
        """
        UserGroupを削除する
        """
        self.session.delete(self)
        self.session.commit()
