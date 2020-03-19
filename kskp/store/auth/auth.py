import os
from kskp.store import BaseModel
from sqlalchemy import Column, String, text, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import INTEGER, TIMESTAMP

class Auth(BaseModel):
    # テーブル名の定義
    __tablename__ = 'auths'

    # 定義先スキーマ
    if 'KSKP_POSTGRESQL_SCHEMA_NAME' in os.environ:
        # テスト環境用のスキーマ
        __table_args__ = {'schema': os.environ['KSKP_POSTGRESQL_SCHEMA_NAME']}

    # テーブルの制約
    __table_args__ = (
        PrimaryKeyConstraint('group_id', 'data_id'),
    )

    # 列名と列のデータ型等の定義
    group_id    = Column(INTEGER, primary_key=True)
    data_id     = Column(INTEGER, primary_key=True)
    read        = Column(INTEGER, default=0, nullable=False)
    write       = Column(INTEGER, default=0, nullable=False)
    exec        = Column(INTEGER, default=0, nullable=False)
    # own         = Column(INTEGER, default=0, nullable=False)
    creator     = Column(INTEGER)
    modifier    = Column(INTEGER)
    created_at  = Column(TIMESTAMP, default=text('statement_timestamp()'))
    modified_at = Column(TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()'))
    
    def __init__(self, group_id, data_id, read=0, write=0, exec=0, creator=None):
        """
        コンストラクタ
        """
        self.group_id = group_id
        self.data_id = data_id
        self.read = read
        self.write = write
        self.exec = exec

        # creator, modifier
        self.creator = creator
        self.modifier = creator
    
    def save(self):
        """
        Authを保存する
        """
        # Authテーブルにレコードを新規追加する
        from . import session
        session.add(self)
        session.commit()
