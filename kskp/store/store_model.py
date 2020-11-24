import os

from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import INTEGER, TIMESTAMP, JSONB, ENUM
from kskp.store import BaseModel

class Store(BaseModel):
    """
    Storeモデル
    """

    # テーブル名
    __tablename__ = 'stores'
    
    # # 定義先スキーマ
    # if 'KSKP_POSTGRESQL_SCHEMA_NAME' in os.environ:
    #     # テスト環境用のスキーマ
    #     __table_args__ = {'schema': os.environ['KSKP_POSTGRESQL_SCHEMA_NAME']}

    # カラム
    id           = Column(ENUM('Directory', 'PostgreSQL', 'MySql', 'ORACLE', name='store_type') ,primary_key=True)
    data         = Column(JSONB)
    # _creator_id  = Column('creator', INTEGER)
    # _modifier_id = Column('modifier', INTEGER)
    # created_at   = Column(TIMESTAMP, default=text('statement_timestamp()'))
    # modified_at  = Column(TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()'))

    def __init__(self, id=None, data=None, creator=None):
        self._session = None

        self.id = id
        self.data = data
        
        # creator, modifier
        if creator is not None:
            self._creator_id = creator.id
            self._modifier_id = creator.id

    # @property
    # def creator(self):
    #     from kskp.store.factory import UserFactory
    #     if self._creator_id is None:
    #         return None
    #     return UserFactory(self._session).find_by_id(self._creator_id, allow_no_result=True)

    # @property
    # def modifier(self):
    #     from kskp.store.factory import UserFactory
    #     if self._modifier_id is None:
    #         return None
    #     return UserFactory(self._session).find_by_id(self._modifier_id, allow_no_result=True)

    def save(self):
        self._session.add(self)
        self._session.commit()

    def delete(self):
        self._session.delete(self)
        self._session.commit()

    def __str__(self):
        return self.id

    def to_json(self):
        return {'id'          : self.id,
                'version'     : self.get('version'),
                'label'       : self.get('label'),
                'description' : self.get('description'),
                'url'         : self.get('url'),
                'params'      : self.get('params')
                }
