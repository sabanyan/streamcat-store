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
    group_id     = Column(INTEGER, primary_key=True)
    datum_id     = Column(INTEGER, primary_key=True)
    read         = Column(BOOLEAN, default=None, nullable=True)
    write        = Column(BOOLEAN, default=None, nullable=True)
    exec         = Column(BOOLEAN, default=None, nullable=True)
    # own         = Column(BOOLEAN, default=None, nullable=True)
    _creator_id  = Column('creator', INTEGER)
    _modifier_id = Column('modifier', INTEGER)
    created_at   = Column(TIMESTAMP, default=text('statement_timestamp()'))
    modified_at  = Column(TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()'))

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
        if creator is not None:
            self._creator_id = creator.id
            self._modifier_id = creator.id

    @property
    def creator(self):
        from kskp.store.auth import User
        if self._creator_id is None:
            return None
        return User.find_by_id(self._creator_id)

    @property
    def modifier(self):
        from kskp.store.auth import User
        if self._modifier_id is None:
            return None
        return User.find_by_id(self._modifier_id)
    
    @staticmethod
    def find_by_id(group_id, datum_id):
        from kskp.store import ss as session
        # SQLAlchemyのidentity mapにキャッシュされていればそれを返す
        authz = session.query(Auth).get((group_id, datum_id))
        return authz
        
    def save(self):
        """
        Authを保存する
        """
        # Authテーブルにレコードを新規追加する
        from kskp.store import ss as session
        session.add(self)
        session.commit()

    def update(self, read, write, exec, modifier=modifier):
        from kskp.store import ss as session
        try:
            # レコードを更新する
            self.read = read
            self.write = write
            self.exec = exec
            self._modifier_id = modifier and modifier.id
            session.update(self)
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