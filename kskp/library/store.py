# from sqlalchemy.dialects.postgresql import TIMESTAMP, JSONB, ENUM
import json
from . import db

class Store(db.Model):
    """
    Storeモデル
    """

    # テーブル名
    __tablename__ = 'stores'
    
    # カラム
    # id          = db.Column(ENUM('Directory', 'PostgreSQL', 'MySql', 'ORACLE', name='server_type') ,primary_key=True)
    # data        = db.Column(JSONB)
    # create_at   = db.Column(TIMESTAMP, default=db.text('CURRENT_TIMESTAMP'))
    # modified_at = db.Column(TIMESTAMP, default=db.text('CURRENT_TIMESTAMP'))
    id          = db.Column(db.String, primary_key=True)
    data        = db.Column(db.String)
    create_at   = db.Column(db.String, default=db.text('CURRENT_TIMESTAMP'))
    modified_at = db.Column(db.String, default=db.text('CURRENT_TIMESTAMP'))
    creator     = db.Column(db.Integer)
    modifier    = db.Column(db.Integer)

    def __init__(self, id=None, data=None, creator=None):
        self.id = id
        self.data = data
        self.creator = creator
        self.modifier = creator

    @classmethod
    def create(cls, id, version=None, label=None, description=None, url=None, params=None, creator=None):
        data = json.dumps({'version'    : version,
                           'label'      : label,
                           'description': description,
                           'url'        : url,
                           'params'     : params})
        return Store(id, data, creator)

    @classmethod
    def find_all(cls):
        results = db.session.query(Store.id,
                                   Store.data,
                                   Store.create_at,
                                   Store.modified_at,
                                   Store.creator,
                                   Store.modifier).all()
        return [Store(result.id, result.data, result.creator) for result in results]

    @classmethod
    def find_by_id(cls, id):
        result = db.session.query(Store.id,
                                  Store.data,
                                  Store.create_at,
                                  Store.modified_at,
                                  Store.creator,
                                  Store.modifier).filter(Store.id==id).one_or_none()
        if result is None:
            raise Exception('No store is found by designated store id')
        return Store(result.id, result.data, result.creator)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.query(Store).filter(Store.id==self.id).delete()
        db.session.commit()

    def __str__(self):
        return self.id

    def to_json(self):
        return {'id'          : self.id,
                'version'     : json.loads(self.data)['version'],
                'label'       : json.loads(self.data)['label'],
                'description' : json.loads(self.data)['description'],
                'url'         : json.loads(self.data)['url'],
                'params'      : json.loads(self.data)['params']
                }