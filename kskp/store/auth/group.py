import os
import uuid
import random
import platform
import datetime

from pathlib import Path
from sqlalchemy.orm import aliased
from sqlalchemy import Column, Integer, String, text
from sqlalchemy.dialects.postgresql import INTEGER

from kskp.core import Datum
from kskp.store import BaseModel
from .user_group import UserGroup
from kskp.store import ss as session


class Group(BaseModel):
    # テーブル名の定義
    __tablename__ = 'groups'

    # 列名と列のデータ型等の定義
    id          = Column(INTEGER, primary_key=True, autoincrement=True)
    name        = Column(String, nullable=False)
    is_admin    = Column(Integer, default=0, nullable=False)
    creator     = Column(INTEGER)
    modifier    = Column(INTEGER)
    created_at  = Column(String, default=text('CURRENT_TIMESTAMP'))
    modified_at = Column(String, default=text('CURRENT_TIMESTAMP'))

    MAX_DATUM_ID = 9000000000000000000
        
    def __init__(self, name, is_admin=0, creator=None):
        """
        コンストラクタ
        """
        # SQLiteではidは乱数で採番する
        # self.id = random.randint(0, self.MAX_DATUM_ID)
        self.name = name
        self.is_admin = is_admin

        # creator, modifier
        self.creator = creator
        self.modifier = creator

    @staticmethod
    def find_by_id(id):
        group = session.query()

    def save(self):
        """
        Groupを保存する
        """
        # Groupsテーブルにレコードを新規追加する
        session.add(self)
        session.commit()

    def update_name(self, new_name):
        pass

    def delete(self):
        # グループに一人以上のユーザが所属している場合は例外を送出する
        count = session.query(UserGroup).filter(UserGroup.group_id==self.id).count()
        if count > 0:
            raise Exception('Can not delete the group that has user(s).')
        # 削除によってどのグループからも所有されなくなるデータがある場合は例外を送出する
        count = session.query(Auths).filter(Auths.group_id==self.id)\
                                    .filter(Auths.own==1).count()
        # 削除グループに対する権限情報をauthsテーブルから全て削除する

        # グループを削除する
        session.query(Group).filter(Group.id==self.id).delete()
        session.commit()

    def join_user(self, user_id, creator):
        """
        グループにユーザを所属させる
        """
        user_group = UserGroup(user_id, self.id, creator=creator)
        user_group.save()
    
    def leave_user(self, user_id):
        """
        グループからユーザを脱退させる
        """
        user_group = UserGroup(user_id, self.id)
        user_group.delete()

    @property
    def created_at_str(self):
        if self.created_at is None:
            return ''
        # DBに格納されている日時はUTCなので、タイムゾーンをUTCに設定する
        created_at_utc = self.created_at.replace(tzinfo=datetime.timezone.utc)
        # UTC日時はここで現地時間(環境変数TZの値)に設定される
        created_at_local = created_at_utc.astimezone()
        return created_at_local.strftime('%Y-%m-%d %H:%M:%S')

    def to_json(self):
        return {'name'      : self.name,
                'is_admin'  : self.is_admin,                
                'creator'   : Datum.get_user_name_by_user_id(self.creator),
                'createdAt' : self.created_at_str}
