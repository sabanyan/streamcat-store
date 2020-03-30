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

    def __init__(self, session, group_id, datum_id, read=None, write=None, exec=None, creator=None):
        """
        コンストラクタ
        """
        # SQLAlchemy Session
        self.session = session

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
        from kskp.store.session import UserFactory
        if self._creator_id is None:
            return None
        return UserFactory(self.session).find_by_id(self._creator_id)

    @property
    def modifier(self):
        from kskp.store.session import UserFactory
        if self._modifier_id is None:
            return None
        return UserFactory(self.session).find_by_id(self._modifier_id)
        
    def save(self):
        """
        Authを保存する
        """
        # Authテーブルにレコードを新規追加する
        self.session.add(self)
        self.session.commit()

    def update(self, read, write, exec, modifier=modifier):
        try:
            # レコードを更新する
            self.read = read
            self.write = write
            self.exec = exec
            self._modifier_id = modifier and modifier.id
            self.session.update(self)
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.commit()

