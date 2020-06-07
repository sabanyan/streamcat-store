
from sqlalchemy import Column, Integer, text
from sqlalchemy.dialects.postgresql import INTEGER, TIMESTAMP

class Stamp():
    _creator_id  = Column('creator',  INTEGER)
    _modifier_id = Column('modifier', INTEGER)
    created_at   = Column(TIMESTAMP, default=text('statement_timestamp()'))
    modified_at  = Column(TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()'))
