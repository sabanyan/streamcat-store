from . import BaseModel
from sqlalchemy import Column, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import INTEGER, BOOLEAN, ENUM

class Auth(BaseModel):
    FIND_OP = 'find'
    READ_OP = 'read'
    WRITE_OP = 'write'
    DELETE_OP = 'delete'
    EXEC_OP = 'exec'
    OWN_OP = 'own'

    # テーブル名の定義
    __tablename__ = 'auths'

    # テーブル定義の設定
    __table_args__ = (
        # 複合キーの定義
        PrimaryKeyConstraint('role_id', 'datum_id', 'operation') ,
    ) + BaseModel.__table_args__

    # 列名と列のデータ型等の定義
    # ProjectFolder.get_joined_members()で発行するSQLでdatum_idへのインデックスを利用するため、datum_idを1列目に配置する
    datum_id     = Column(INTEGER, primary_key=True)
    role_id      = Column(INTEGER, primary_key=True)
    operation    = Column(ENUM(FIND_OP, READ_OP, WRITE_OP, DELETE_OP, EXEC_OP, OWN_OP, name='op_type'), primary_key=True)
    permission   = Column(BOOLEAN, nullable=False)

    def __init__(self, session, role_id, datum_id, operation, permission):
        """
        コンストラクタ
        """
        super().__init__(session)

        self.role_id = role_id
        self.datum_id = datum_id
        self.operation = operation
        self.permission = permission

    def save(self):
        """
        Authを保存する
        """
        try:
            # Authテーブルにレコードを新規追加する
            self._session.add(self)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

    def update(self, permission):
        # 同じ値への更新であれば何もしない
        if permission == self.permission:
            return self

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

        return self

    def delete(self):
        """
        Authを削除する
        """
        try:
            self._session.delete(self)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

    def __repr__(self):
        return f'Auth(role:{self.role_id}, datum:{self.datum_id}, {self.operation}, {self.permission})'
