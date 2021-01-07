from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB, ENUM
from kskp.core import BaseModel

class Store(BaseModel):
    """
    Storeモデル
    """

    # テーブル名
    __tablename__ = 'stores'

    # カラム
    id           = Column(ENUM('Directory', 'PostgreSQL', 'MySql', 'ORACLE', name='store_type') ,primary_key=True)
    data         = Column(JSONB)

    def __init__(self, id=None, data=None, creator=None):
        self._session = None

        self.id = id
        self.data = data
        
        # creator, modifier
        if creator is not None:
            self._creator_id = creator.id
            self._modifier_id = creator.id

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
                'version'     : self.data.get('version'),
                'label'       : self.data.get('label'),
                'description' : self.data.get('description'),
                'url'         : self.data.get('url'),
                'params'      : self.data.get('params')
               }
