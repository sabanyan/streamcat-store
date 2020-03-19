import os
from sqlalchemy import Column, text, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import INTEGER, TIMESTAMP
from kskp.store import BaseModel

class UserGroup(BaseModel):
    # テーブル名の定義
    __tablename__ = 'users_groups'

    # 定義先スキーマ
    if 'KSKP_POSTGRESQL_SCHEMA_NAME' in os.environ:
        # テスト環境用のスキーマ
        __table_args__ = {'schema': os.environ['KSKP_POSTGRESQL_SCHEMA_NAME']}

    # テーブルの制約
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'group_id'),
    )

    # 列名と列のデータ型等の定義
    user_id     = Column(INTEGER, primary_key=True)
    group_id    = Column(INTEGER, primary_key=True)
    creator     = Column(INTEGER)
    modifier    = Column(INTEGER)
    created_at  = Column(TIMESTAMP, default=text('statement_timestamp()'))
    modified_at = Column(TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()'))
    
    def __init__(self, user_id, group_id, creator=None):
        """
        コンストラクタ
        """
        self.user_id = user_id
        self.group_id = group_id

        # creator, modifier
        self.creator = creator
        self.modifier = creator

    def save(self):
        """
        UserGroupを保存する
        """
        from kskp.store import ss as session
        session.add(self)
        session.commit()

    def delete(self):
        """
        UserGroupを削除する
        """
        from kskp.store import ss as session
        session.query(UserGroup).filter(UserGroup.user_id==self.user_id)\
                                .filter(UserGroup.group_id==self.group_id).delete()
        session.commit()

    @staticmethod
    def delete_all_by_user_id(user_id):
        """
        UsersGroupsテーブルから指定したユーザの所属情報を全て削除する
        """
        from kskp.store import ss as session
        session.query(UserGroup).filter(UserGroup.user_id==user_id).delete()
        session.commit()