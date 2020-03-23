import os
from sqlalchemy import Column, String, text
from sqlalchemy.dialects.postgresql import INTEGER, TIMESTAMP
from kskp.store import BaseModel
from .system_group import SystemGroup
from .user_group import UserGroup

class Group(BaseModel):
    # テーブル名の定義
    __tablename__ = 'groups'

    # 定義先スキーマ
    if 'KSKP_POSTGRESQL_SCHEMA_NAME' in os.environ:
        # テスト環境用のスキーマ
        __table_args__ = {'schema': os.environ['KSKP_POSTGRESQL_SCHEMA_NAME']}

    # 列名と列のデータ型等の定義
    id          = Column(INTEGER, primary_key=True, autoincrement=True)
    name        = Column(String, nullable=False)
    # is_admin    = Column(INTEGER, default=0, nullable=False)
    creator     = Column(INTEGER)
    modifier    = Column(INTEGER)
    created_at  = Column(TIMESTAMP, default=text('statement_timestamp()'))
    modified_at = Column(TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()'))

    def __init__(self, name, creator=None):
        """
        コンストラクタ
        """
        self.name = name
        # self.is_admin = is_admin

        # creator, modifier
        self.creator = creator
        self.modifier = creator

    @staticmethod
    def find_by_id(id):
        from kskp.store import ss as session
        return session.query(Group).filter(Group.id == id).one_or_none()

    @staticmethod
    def load_admin_group():
        from kskp.store import ss as session
        group_id = session.query(SystemGroup.group_id).filter(SystemGroup.type==SystemGroup.ADMIN_TYPE).one_or_none()
        if group_id is None:
            admin_group = Group('ADMIN')
            admin_group.save()
            system_group = SystemGroup(SystemGroup.ADMIN_TYPE, admin_group.id)
            system_group.save()
        else:
            admin_group = Group.find_by_id(group_id)
        return admin_group

    @staticmethod
    def load_everyone_group():
        from kskp.store import ss as session
        group_id = session.query(SystemGroup.group_id).filter(SystemGroup.type==SystemGroup.EVERYONE_TYPE).one_or_none()
        if group_id is None:
            everyone_group = Group('EVERYONE')
            everyone_group.save()
            system_group = SystemGroup(SystemGroup.EVERYONE_TYPE, everyone_group.id)
            system_group.save()
        else:
            everyone_group = Group.find_by_id(group_id)
        return everyone_group

    @staticmethod
    def exists(group_id):
        from kskp.store import ss as session
        count = session.query(Group).filter(Group.id==group_id).count()
        return count > 0

    @staticmethod
    def all():
        """
        全件取得する
        """
        from kskp.store import ss as session
        return session.query(Group).all()

    def save(self):
        """
        Groupを保存する
        """
        from kskp.store import ss as session
        # Groupsテーブルにレコードを新規追加する
        session.add(self)
        session.commit()

    def update_name(self, new_name):
        pass

    def delete(self):
        from kskp.store import ss as session
        from .auth import Auth

        # グループに一人以上のユーザが所属している場合は例外を送出する
        count = session.query(UserGroup).filter(UserGroup.group_id == self.id).count()
        if count > 0:
            raise Exception('Can not delete the group that has user(s).')
        # 削除によってどのグループからも所有されなくなるデータがある場合は例外を送出する
        count = session.query(Auth).filter(Auth.group_id == self.id)\
                                    .filter(Auth.own == 1).count()
        # 削除グループに対する権限情報をauthsテーブルから全て削除する

        # グループを削除する
        # sys.__stderr__.write(f"self.id: {self.id}\n")
        session.delete(self)
        session.commit()

    def is_joined_user(self, user_id):
        from kskp.store import ss as session
        count = session.query(UserGroup).filter(UserGroup.group_id==self.id).filter(UserGroup.user_id==user_id).count()
        return count > 0

    def has_joined_user(self):
        from kskp.store import ss as session
        count = session.query(UserGroup).filter(UserGroup.group_id==self.id).count()
        return count > 0

    def join_user(self, user_id, creator=None):
        """
        グループにユーザを所属させる
        """
        if not self.is_joined_user(user_id):
            user_group = UserGroup(user_id, self.id, creator=creator)
            user_group.save()
    
    def leave_user(self, user_id):
        """
        グループからユーザを脱退させる
        """
        if self.is_joined_user(user_id):
            user_group = UserGroup.find_by_id(user_id, self.id)
            user_group.delete()

    def init_authz(self, datum_id, read, write, exec, creator=None):
        from .auth import Auth

        if Auth.exists(self.id, datum_id):
            Auth.update(self.id, datum_id, read, write, exec, modifier=creator)
        else:
            authz = Auth(self.id, datum_id, read=read, write=write, exec=exec, creator=creator)
            authz.save()

    @property
    def created_at_str(self):
        import datetime
        if self.created_at is None:
            return ''
        # DBに格納されている日時はUTCなので、タイムゾーンをUTCに設定する
        created_at_utc = self.created_at.replace(tzinfo=datetime.timezone.utc)
        # UTC日時はここで現地時間(環境変数TZの値)に設定される
        created_at_local = created_at_utc.astimezone()
        return created_at_local.strftime('%Y-%m-%d %H:%M:%S')

    def to_json(self):
        from kskp.store import Datum
        return {
            'id'       : self.id,
            'name'     : self.name,
            'is_admin' : self.is_admin,               
            'creator'  : self.creator_str,
            'createdAt': self.created_at_str
        }
