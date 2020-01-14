import os
import uuid
import random
import platform
import datetime
from kskp.store import BaseModel
from pathlib import Path
from sqlalchemy.orm import aliased
from sqlalchemy import Column, Integer, String, text, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import INTEGER, TIMESTAMP

class Auth(BaseModel):
    # テーブル名の定義
    __tablename__ = 'auths'

    # テーブルの制約
    __table_args__ = (
        PrimaryKeyConstraint('group_id', 'data_id'),
    )

    # 列名と列のデータ型等の定義
    group_id    = Column(INTEGER, primary_key=True)
    data_id     = Column(INTEGER, primary_key=True)
    read        = Column(Integer, default=0, nullable=False)
    # write       = Column(Integer, default=0, nullable=False)
    # exec        = Column(Integer, default=0, nullable=False)
    # own         = Column(Integer, default=0, nullable=False)
    creator     = Column(INTEGER)
    modifier    = Column(INTEGER)
    created_at  = Column(TIMESTAMP, default=text('statement_timestamp()'))
    modified_at = Column(TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()'))
    
