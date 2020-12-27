import os
from sqlalchemy import Column, text, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import INTEGER, BOOLEAN, TIMESTAMP
from . import BaseModel

class UserRole(BaseModel):
    # テーブル名の定義
    __tablename__ = 'users_roles'

    # テーブル定義の設定
    __table_args__ = (
        # 複合キーの定義
        PrimaryKeyConstraint('user_id', 'role_id') ,
    ) + BaseModel.__table_args__

    # 列名と列のデータ型等の定義
    user_id      = Column(INTEGER, primary_key=True)
    role_id      = Column(INTEGER, primary_key=True)
    # ロールの所有権の有無
    owner        = Column(BOOLEAN, nullable=False)

    def __init__(self, session, user_id, role_id, owner=False):
        """
        コンストラクタ
        """
        super().__init__(session)

        self.user_id = user_id
        self.role_id = role_id

        # UserがRoleの所有権を持つ場合はTrue
        self.owner = owner

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
