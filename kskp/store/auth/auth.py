import os
from kskp.store import BaseModel
from sqlalchemy import Column, String, text, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import INTEGER, BOOLEAN, TIMESTAMP

class Auth(BaseModel):
    # テーブル名の定義
    __tablename__ = 'auths'

    # 定義先スキーマ
    if 'KSKP_POSTGRESQL_SCHEMA_NAME' in os.environ:
        # テスト環境用のスキーマ
        __table_args__ = {'schema': os.environ['KSKP_POSTGRESQL_SCHEMA_NAME']}

    # テーブルの制約
    __table_args__ = (
        PrimaryKeyConstraint('group_id', 'datum_id'),
    )

    # 列名と列のデータ型等の定義
    group_id    = Column(INTEGER, primary_key=True)
    datum_id    = Column(INTEGER, primary_key=True)
    read        = Column(BOOLEAN, default=None, nullable=True)
    write       = Column(BOOLEAN, default=None, nullable=True)
    exec        = Column(BOOLEAN, default=None, nullable=True)
    # own         = Column(BOOLEAN, default=None, nullable=True)
    creator     = Column(INTEGER)
    modifier    = Column(INTEGER)
    created_at  = Column(TIMESTAMP, default=text('statement_timestamp()'))
    modified_at = Column(TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()'))
    
    def __init__(self, group_id, datum_id, read=None, write=None, exec=None, creator=None):
        """
        コンストラクタ
        """
        self.group_id = group_id
        self.datum_id = datum_id
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
        from kskp.store import ss as session
        session.add(self)
        session.commit()

    @staticmethod
    def update(group_id, datum_id, read, write, exec, modifier=modifier):
        from kskp.store import ss as session
        try:
            # レコードを更新する
            session.query(Auth).filter(Auth.group_id==group_id)\
                               .filter(Auth.datum_id==datum_id).update({'read' :read,
                                                                        'write':write,
                                                                        'exec' :exec,
                                                                        'modifier':modifier})
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.commit()

    @staticmethod
    def exists(group_id, datum_id):
        from kskp.store import ss as session
        count = session.query(Auth).filter(Auth.group_id==group_id)\
                                   .filter(Auth.datum_id==datum_id).count()
        return count > 0