import os
import json

from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import INTEGER, TIMESTAMP, JSONB, ENUM
from kskp.store import BaseModel, ss as session

class Store(BaseModel):
    """
    Storeモデル
    """

    # テーブル名
    __tablename__ = 'stores'
    
    # 定義先スキーマ
    if 'KSKP_POSTGRESQL_SCHEMA_NAME' in os.environ:
        # テスト環境用のスキーマ
        __table_args__ = {'schema': os.environ['KSKP_POSTGRESQL_SCHEMA_NAME']}

    # カラム
    id          = Column(ENUM('Directory', 'PostgreSQL', 'MySql', 'ORACLE', name='store_type') ,primary_key=True)
    data        = Column(JSONB)
    creator     = Column(INTEGER)
    modifier    = Column(INTEGER)
    created_at  = Column(TIMESTAMP, default=text('statement_timestamp()'))
    modified_at = Column(TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()'))

    def __init__(self, id=None, data=None, creator=None):
        self.id = id
        self.data = data
        
        # creator, modifier
        if creator is not None:
            self.creator = creator.id
            self.modifier = creator.id

    @classmethod
    def create(cls, id, version=None, label=None, description=None, url=None, params=None, creator=None):
        data = {'version'    : version,
                'label'      : label,
                'description': description,
                'url'        : url,
                'params'     : params}
        return Store(id, data, creator)

    @classmethod
    def find_all(cls):
        results = session.query(Store.id,
                                Store.data,
                                Store.created_at,
                                Store.modified_at,
                                Store.creator,
                                Store.modifier).all()
        return [Store(result.id, result.data, result.creator) for result in results]

    @classmethod
    def find_by_id(cls, id):
        result = session.query(Store.id,
                               Store.data,
                               Store.created_at,
                               Store.modified_at,
                               Store.creator,
                               Store.modifier).filter(Store.id==id).one_or_none()
        if result is None:
            raise Exception('No store is found by designated store id')
        return Store(result.id, result.data, result.creator)

    def save(self):
        session.add(self)
        session.commit()

    def delete(self):
        session.delete(self)
        session.commit()

    def __str__(self):
        return self.id

    def to_json(self):
        return {'id'          : self.id,
                'version'     : self.data['version'],
                'label'       : self.data['label'],
                'description' : self.data['description'],
                'url'         : self.data['url'],
                'params'      : self.data['params']
                }
