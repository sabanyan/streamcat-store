import os
import pprint
from sqlalchemy import Column, String, text
from sqlalchemy.dialects.postgresql import INTEGER, TIMESTAMP
from .. import BaseModel

class User(BaseModel):
    # テーブル名の定義
    __tablename__ = 'users'

    # 定義先スキーマ
    if 'KSKP_POSTGRESQL_SCHEMA_NAME' in os.environ:
        # テスト環境用のスキーマ
        __table_args__ = {'schema': os.environ['KSKP_POSTGRESQL_SCHEMA_NAME']}

    # 列名と列のデータ型等の定義
    id          = Column(INTEGER, primary_key=True, autoincrement=True)
    email       = Column(String, nullable=False, unique=True)
    password    = Column(String)
    name        = Column(String, nullable=False)
    # 本人グループのGroupId
    self_group_id = Column(INTEGER, nullable=True)
    creator     = Column(INTEGER)
    modifier    = Column(INTEGER)
    created_at  = Column(TIMESTAMP, default=text('statement_timestamp()'))
    modified_at = Column(TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()'))

    def __init__(self, email, password, name, creator=None):
        """
        コンストラクタ
        """
        self.email = email
        self.password = password
        self.name = name

        # creator, modifier
        self.creator = creator
        self.modifier = creator
    
    # def _require_admin_auth(func):
    #     """
    #     操作ユーザがadminグループに所属していない場合は例外を送出する
    #     """
    #     @functools.wraps(func)
    #     def wrapper(self, *args, **kwargs):
    #         sql = """
    #         select count(is_admin) from groups G
    #         where is_admin = 1
    #           and exists (select * from users_groups UG
    #                        from UG join G using (id)
    #                        where exists (select * from users U
    #                                       where U.id = UG.user_id
    #                                         and U.id = {creator}) )
    #         """.format(creator=str(self.creator))
    #         # SQLを発行する
    #         count = session.execute(sql).scalar()
    #         # creatorはadminグループに所属していない場合は0件となる
    #         if count == 0:
    #             pprint.pprint(func)
    #             raise Exception("user id (%s) is not authorized to call function (%s.%s)." 
    #                             % (self.creator, func.__module__, func.__name__))
            
    #         return func(self, *args, **kwargs)
    #     return wrapper

    from .authz_required import add_print

    @staticmethod
    def find_by_id(user_id):
        from kskp.store import ss as session
        user = session.query(User).filter(User.id==user_id).one_or_none()
        return user

    @staticmethod
    @add_print("files")
    def find_by_email(email):
        """
        指定されたuuidを持つFrameを取得する
        """
        from kskp.store import ss as session
        user = session.query(User).filter(User.email==email).one_or_none()
        return user

    @staticmethod
    def exists(user_id):
        from kskp.store import ss as session
        count = session.query(User).filter(User.id==user_id).count()
        return count > 0

    def save(self):
        """
        Userを保存する
        """
        from kskp.store import ss as session
        # Usersテーブルにレコードを新規追加する
        session.add(self)
        session.commit()

    def update_email(self, new_email, modifier):
        """
        Userのemail列を更新する
        """
        from kskp.store import ss as session
        session.query(User).filter(User.id==self.id)\
                           .update({'email'      :new_email,
                                    'modifier'   :modifier,
                                    'modified_at':BaseModel.get_current_time_str()})
        session.commit()

    def update_password(self, new_password, modifier):
        pass

    def update_name(self, new_name, modifier):
        from kskp.store import ss as session
        session.query(User).filter(User.id==self.id)\
                           .update({'name'       :new_name,
                                    'modifier'   :modifier,
                                    'modified_at':BaseModel.get_current_time_str()})
        session.commit()

    # @_require_admin_auth
    def delete(self):
        """
        Userを削除する
        """
        from kskp.store import ss as session
        from .user_group import UserGroup
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
        #               where D.id = A.datum_id
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


    def load_self_group(self):
        """
        本人グループを取得する
        """
        from .group import Group
        
        if Group.exists(self.self_group_id):
            self_group = Group.find_by_id(self.self_group_id)
        else:
            self_group = Group(self.name, creator=self.id)
            self_group.save()

        self_group.join_user(self.id, creator=self.id)

        return self_group
