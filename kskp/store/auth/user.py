import os
import uuid
import pprint
from sqlalchemy import Column, String, text
from sqlalchemy.dialects.postgresql import INTEGER, TIMESTAMP, UUID
from .. import BaseModel

class User(BaseModel):
    # テーブル名の定義
    __tablename__ = 'users'

    # 定義先スキーマ
    if 'KSKP_POSTGRESQL_SCHEMA_NAME' in os.environ:
        # テスト環境用のスキーマ
        __table_args__ = {'schema': os.environ['KSKP_POSTGRESQL_SCHEMA_NAME']}

    # 列名と列のデータ型等の定義
    id            = Column(INTEGER, primary_key=True, autoincrement=True)
    uuid          = Column(UUID, nullable=False, unique=True)
    email         = Column(String, nullable=False, unique=True)
    password      = Column(String)
    name          = Column(String, nullable=False)
    # 本人グループのGroupId
    self_group_id = Column(INTEGER, nullable=True)
    _creator_id   = Column('creator', INTEGER)
    _modifier_id  = Column('modifier', INTEGER)
    created_at    = Column(TIMESTAMP, default=text('statement_timestamp()'))
    modified_at   = Column(TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()'))

    def __init__(self, email, password, name, creator=None):
        """
        コンストラクタ
        """
        # UUIDを採番する
        self.uuid = str(uuid.uuid4())

        self.email = email
        self.password = password
        self.name = name

        # creator, modifier
        if creator is not None:
            self._creator_id = creator.id
            self._modifier_id = creator.id

    @property
    def creator(self):
        if self._creator_id is None:
            return None
        return User.find_by_id(self._creator_id)

    @property
    def modifier(self):
        if self._modifier_id is None:
            return None
        return User.find_by_id(self._modifier_id)

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

    @staticmethod
    def find_by_id(user_id):
        from kskp.store import ss as session
        # user = session.query(User).filter(User.id==user_id).one_or_none()

        # SQLAlchemyのidentity mapにキャッシュされていればそれを返す
        user = session.query(User).get(user_id)
        return user

    @staticmethod
    def find_by_uuid(uuid):
        from kskp.store import ss as session
        user = session.query(User).filter(User.uuid==uuid).one_or_none()
        return user

    @staticmethod
    def find_by_email(email):
        """
        指定されたuuidを持つFrameを取得する
        """
        from kskp.store import ss as session
        user = session.query(User).filter(User.email==email).one_or_none()
        return user

    @staticmethod
    def exists(uuid):
        from kskp.store import ss as session
        count = session.query(User).filter(User.uuid==uuid).count()
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
        self.email = new_email
        self._modifier_id = modifier.id
        session.update(self)
        session.commit()

    def update_password(self, new_password, modifier):
        pass

    def update_name(self, new_name, modifier):
        from kskp.store import ss as session
        self.name = new_name
        self._modifier_id = modifier.id
        session.update(self)
        session.commit()

    def update_self_group_id(self, new_group_id, modifier=None):
        from kskp.store import ss as session
        self.self_group_id = new_group_id
        self._modifier_id = modifier and modifier.id
        session.update(self)
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
        session.delete(self)
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

        if self.self_group_id is None:
            # 本人グループを作成する
            self_group = Group(self.name, creator=self)
            self_group.save()
            # 本人グループを設定する
            self.update_self_group_id(self_group.id)
        else:
            self_group = Group.find_by_id(self.self_group_id)
            if self_group is None:
                raise Exception(f'本人グループ({self.self_group_id})は存在しません')

        self_group.join_user(self, creator=self)

        return self_group

    def __repr__(self):
        return f'User({self.id}, {self.name})'

    def __eq__(self, other):
        return self.uuid == other.uuid

    def __ne__(self, other):
        return self.uuid != other.uuid
