import os
from sqlalchemy import Column, text, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import INTEGER, BOOLEAN, TIMESTAMP
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
    role_id      = Column(INTEGER, primary_key=True)
    # ロールの所有権の有無
    owner        = Column(BOOLEAN, nullable=False)
    _creator_id  = Column('creator', INTEGER)
    _modifier_id = Column('modifier', INTEGER)
    created_at   = Column(TIMESTAMP, default=text('statement_timestamp()'))
    modified_at  = Column(TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()'))

    def __init__(self, session, user_id, role_id, owner=False):
        """
        コンストラクタ
        """
        # SQLAlchemy Session
        self._session = session

        self.user_id = user_id
        self.role_id = role_id

        # UserがRoleの所有権を持つ場合はTrue
        self.owner = owner

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

    def save(self, ignore_authz=False):
        """
        UserRoleを保存する
        """
        try:
            self._session.add(self, ignore_authz=ignore_authz)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

    def update_owner(self, owner, modifier=None):
        """
        UserRoleの所有権フラグを更新する
        """
        # 同じ値への更新であれば何もしない
        if owner == self.owner:
            return self

        try:
            self.owner = owner
            self._modifier_id = (modifier or self._session.user).id
            self._session.update(self)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

        return self

    def delete(self):
        """
        UserRoleを削除する
        """
        try:
            self._session.delete(self)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

    def __repr__(self):
        return f'UserRole(user:{self.user_id}, role:{self.role_id}, owner:{self.owner})'