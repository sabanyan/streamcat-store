import os
import uuid
import random
import platform
import datetime
import functools
import pprint

from pathlib import Path
from sqlalchemy.orm import aliased
from sqlalchemy import Column, Integer, String, text
from sqlalchemy.dialects.postgresql import INTEGER, TIMESTAMP

from .. import BaseModel
from .group import Group
from .user_group import UserGroup
from kskp.store import ss as session

class User(BaseModel):
    # テーブル名の定義
    __tablename__ = 'users'

    # 列名と列のデータ型等の定義
    id          = Column(INTEGER, primary_key=True, autoincrement=True)
    email       = Column(String, nullable=False, unique=True)
    password    = Column(String)
    name        = Column(String, nullable=False)
    creator     = Column(INTEGER)
    modifier    = Column(INTEGER)
    created_at  = Column(TIMESTAMP, default=text('statement_timestamp()'))
    modified_at = Column(TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()'))

    MAX_DATUM_ID = 9000000000000000000

    def __init__(self, email, password, name, creator=None):
        """
        コンストラクタ
        """
        # SQLiteではidは乱数で採番する
        # self.id = random.randint(0, self.MAX_DATUM_ID)

        self.email = email
        self.password = password
        self.name = name

        # creator, modifier
        self.creator = creator
        self.modifier = creator
    
    def _require_admin_auth(func):
        """
        操作ユーザがadminグループに所属していない場合は例外を送出する
        """
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            sql = """
            select count(is_admin) from groups G
            where is_admin = 1
              and exists (select * from users_groups UG
                           from UG join G using (id)
                           where exists (select * from users U
                                          where U.id = UG.user_id
                                            and U.id = {creator}) )
            """.format(creator=str(self.creator))
            # SQLを発行する
            count = session.execute(sql).scalar()
            # creatorはadminグループに所属していない場合は0件となる
            if count == 0:
                pprint.pprint(func)
                raise Exception("user id (%s) is not authorized to call function (%s.%s)." 
                                % (self.creator, func.__module__, func.__name__))
            
            return func(self, *args, **kwargs)
        return wrapper

    @staticmethod
    def find_by_email(email):
        """
        指定されたuuidを持つFrameを取得する
        """
        user = session.query(User).filter(User.email==email).one_or_none()
        return user

    @_require_admin_auth
    def save(self):
        """
        Userを保存する
        """
        # Usersテーブルにレコードを新規追加する
        session.add(self)
        session.commit()

    def update_email(self, new_email, modifier):
        """
        Userのemail列を更新する
        """
        session.query(User).filter(User.id==self.id)\
                           .update({'email'      :new_email,
                                    'modifier'   :modifier,
                                    'modified_at':BaseModel.get_current_time_str()})
        session.commit()

    def update_password(self, new_password, modifier):
        pass

    def update_name(self, new_name, modifier):
        session.query(User).filter(User.id==self.id)\
                           .update({'name'       :new_name,
                                    'modifier'   :modifier,
                                    'modified_at':BaseModel.get_current_time_str()})
        session.commit()

    @_require_admin_auth
    def delete(self):
        """
        Userを削除する
        """
        # users_groupsテーブルから全ての削除ユーザの行を削除する
        UserGroup.delete_all_by_user_id(self.id)
        # usersテーブルから削除ユーザの行を削除する
        session.query(User).filter(User.id==self.id).delete()
        session.commit()


    def authenticate(self):
        pass

    def has_read_authority(self, uuid):
        # select 
        #      A.read
        # from auths A
        # where exists (select * from data D
        #               where D.id = A.data_id
        #                 and D.uuid = uuid)
        #   and exists (select * from groups G
        #               where G.id = A.group_id
        #                 and exists (select * from users_groups UG
        #                             where UG.group_id = G.id
        #                               and exists (select * from users U
        #                                           where U.id = UG.user_id
        #                                             and U.id = self.id) ))

        # このメソッドはUserとDatumのどちらに持たせたほうがいい？
        pass


