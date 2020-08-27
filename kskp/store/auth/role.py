import os
import uuid
from sqlalchemy import Column, String, text
from sqlalchemy.dialects.postgresql import INTEGER, TIMESTAMP, UUID
from kskp.store import BaseModel
from .user_role import UserRole

class Role(BaseModel):
    # テーブル名の定義
    __tablename__ = 'roles'

    # 定義先スキーマ
    if 'KSKP_POSTGRESQL_SCHEMA_NAME' in os.environ:
        # テスト環境用のスキーマ
        __table_args__ = {'schema': os.environ['KSKP_POSTGRESQL_SCHEMA_NAME']}

    # 列名と列のデータ型等の定義
    id           = Column(INTEGER, primary_key=True, autoincrement=True)
    uuid         = Column(UUID, nullable=False, unique=True)
    name         = Column(String, nullable=False)
    _creator_id  = Column('creator', INTEGER)
    _modifier_id = Column('modifier', INTEGER)
    created_at   = Column(TIMESTAMP, default=text('statement_timestamp()'))
    modified_at  = Column(TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()'))

    SYS_ADMIN_ROLE_UUID  = 'aa19bfb3-1409-4082-98e3-c497849d6235'
    SYS_ADMIN_ROLE_LABEL = 'SYS_ADMIN'
    USR_ADMIN_ROLE_UUID  = 'aa2d8136-dcb7-4b6f-bd00-e9290c51b2a1'
    USR_ADMIN_ROLE_LABEL = 'USR_ADMIN'    
    EVERYONE_ROLE_UUID   = 'ee16239b-5ffd-447c-9d05-411906ad7364'
    EVERYONE_ROLE_LABEL  = 'EVERYONE'

    def __init__(self, session, name):
        """
        コンストラクタ
        """
        # SQLAlchemy Session
        self._session = session

        # UUIDを採番する
        self.uuid = str(uuid.uuid4())

        self.name = name
        # self.is_admin = is_admin

        # creator, modifier
        if session is not None and session.user is not None:
            self._creator_id = session.user.id
            self._modifier_id = session.user.id

    @property
    def creator(self):
        from kskp.store.factory import UserFactory
        if self._creator_id is None:
            return None
        return UserFactory(self._session).find_by_id(self._creator_id, allow_no_result=True)

    @property
    def modifier(self):
        from kskp.store.factory import UserFactory
        if self._modifier_id is None:
            return None
        return UserFactory(self._session).find_by_id(self._modifier_id, allow_no_result=True)

    @property
    def creator_str(self):
        if self.creator is None:
            return ''
        return self.creator.name

    @property
    def created_at_str(self):
        from kskp.core import Util
        return Util.datetime_to_local_time_str(self.created_at)

    @property
    def is_sys_admin(self):
        return self.uuid == Role.SYS_ADMIN_ROLE_UUID

    @property
    def is_usr_admin(self):
        return self.uuid == Role.USR_ADMIN_ROLE_UUID

    @property
    def is_everyone(self):
        return self.uuid == Role.EVERYONE_ROLE_UUID

    def _get_system_role_label(self):
        if self.is_sys_admin:
            return Role.SYS_ADMIN_ROLE_LABEL
        elif self.is_usr_admin:
            return Role.USR_ADMIN_ROLE_LABEL
        elif self.is_everyone:
            return Role.EVERYONE_ROLE_LABEL
        else:
            return ''

    def save(self):
        """
        Roleを保存する
        """
        try:
            # Rolesテーブルにレコードを新規追加する
            self._session.add(self)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

    def update_name(self, new_name, modifier=None):
        try:
            self.name = new_name
            self._modifier_id = (modifier or self._session.user).id
            self._session.update(self)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

        return self

    def delete(self):
        from .auth import Auth

        # ロールに一人以上のユーザが所属している場合は例外を送出する
        count = self._session.query(UserRole).filter(UserRole.role_id == self.id).count()
        if count > 0:
            raise Exception('Can not delete the role that has user(s).')

        # 
        # 削除によってどのロールからも所有されなくなるデータがある場合は例外を送出する
        # (所有権は未実装なので、このチェックも未実装である
        #  現在はDatum.creatorが所有者となっている)
        # 
        # count = self._session.query(Auth).filter(Auth.role_id == self.id)\
        #                                  .filter(Auth.own == 1).count()

        try:
            # 削除ロールに対する権限情報をauthsテーブルから全て削除する
            self._session.query(Auth).filter(Auth.role_id==self.id).delete()
            # ロールを削除する
            self._session.delete(self)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

    def is_joined_user(self, user):
        count = self._session.query(UserRole).filter(UserRole.role_id==self.id).filter(UserRole.user_id==user.id).count()
        return count > 0

    def has_joined_user(self):
        count = self._session.query(UserRole).filter(UserRole.role_id==self.id).count()
        return count > 0

    def get_joined_users(self):
        """
        ロールに所属する全てのユーザを返す
        (ユーザID順で返す)
        """
        from .user import User
        query = self._session.query(User).\
                              filter(User.id==UserRole.user_id).\
                              filter(UserRole.role_id==self.id).\
                              order_by(User.id)
        return query.all()

    def join_user(self, user):
        """
        ロールにユーザを所属させる
        """
        if not self.is_joined_user(user):
            user_role = UserRole(self._session, user.id, self.id)
            user_role.save()
    
    def leave_user(self, user):
        """
        ロールからユーザを脱退させる
        """
        if self.is_joined_user(user):
            from kskp.store.factory import UserRoleFactory
            user_role = UserRoleFactory(self._session).find_by_id(user.id, self.id)
            user_role.delete()

    def init_authz(self, datum_id, read, write, exec=None):
        from .auth import Auth
        self._init_authz_inner(datum_id, Auth.READ_OP, permission=read)
        self._init_authz_inner(datum_id, Auth.WRITE_OP, permission=write)
        if exec is not None:
            self._init_authz_inner(datum_id, Auth.EXEC_OP, permission=exec)

    def _init_authz_inner(self, datum_id, operation, permission):
        from kskp.store.factory import AuthFactory
        auth_factory = AuthFactory(self._session)

        if auth_factory.exists(self.id, datum_id, operation):
            auth = auth_factory.find_by_id(self.id, datum_id, operation)
            auth.update(permission)
        else:
            authz = auth_factory.create(self.id, datum_id, operation, permission=permission)
            authz.save()

    @property
    def created_at_str(self):
        from kskp.core import Util
        return Util.datetime_to_local_time_str(self.created_at)

    def to_json(self):
        return {
            'uuid'     : self.uuid,
            'name'     : self.name,
            'systemRole' : self._get_system_role_label(),
            'creator'  : self.creator_str,
            'createdAt': self.created_at_str
        }
