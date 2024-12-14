import uuid
from sqlalchemy import select, delete, func, Column, String
from sqlalchemy.dialects.postgresql import INTEGER, BOOLEAN, UUID
from .user_role import UserRole
from . import BaseModel

class Role(BaseModel):

    class Member():
        """
        Userとロールへの参加タイプを纏める
        """
        def __init__(self, user, owner:bool=False):
            self.user = user
            self.owner = owner

        def to_json(self):
            ret = self.user.to_json()
            ret.update({'owner':self.owner})
            return ret

        def __repr__(self):
            return f'Member({self.user.id}, {self.user.name}, {self.owner})'

        def __eq__(self, other):
            return self.user == other.user and self.owner == other.owner

        def __ne__(self, other):
            return self.user != other.user or self.owner != other.owner

    # テーブル名の定義
    __tablename__ = 'roles'

    # 列名と列のデータ型等の定義
    id           = Column(INTEGER, primary_key=True, autoincrement=True)
    # NOTE: as_uuid=Trueの場合はPythonのuuidオブジェクトに変換されるが、StreamCatではUUIDを文字列で保持しているのでFalseにする必要がある
    uuid         = Column(UUID(as_uuid=False), nullable=False, unique=True)
    name         = Column(String, nullable=False)
    _delete_on_isolated = Column('delete_on_isolated', BOOLEAN, nullable=False)

    SYS_ADMIN_ROLE_UUID  = 'aa19bfb3-1409-4082-98e3-c497849d6235'
    SYS_ADMIN_ROLE_LABEL = 'SYS_ADMIN'
    USR_ADMIN_ROLE_UUID  = 'aa2d8136-dcb7-4b6f-bd00-e9290c51b2a1'
    USR_ADMIN_ROLE_LABEL = 'USR_ADMIN'    
    EVERYONE_ROLE_UUID   = 'ee16239b-5ffd-447c-9d05-411906ad7364'
    EVERYONE_ROLE_LABEL  = 'EVERYONE'
    EDIT_LOCK_ROLE_UUID  = 'e1743f1e-24c0-4022-9de3-e607637c30fe'
    EDIT_LOCK_ROLE_LABEL = 'EDIT_LOCK'

    def __init__(self, session, name, delete_on_isolated=False):
        """
        コンストラクタ
        """
        super().__init__(session)

        # UUIDを採番する
        self.uuid = str(uuid.uuid4())

        # ロール名
        self.name = name

        # Trueの場合、紐づくDatumが存在しなくなったらこのロールを削除する
        # (このロールの所有者以外のユーザがDatumを削除した時でも削除する)
        self._delete_on_isolated = delete_on_isolated

    @property
    def delete_on_isolated(self):
        return self._delete_on_isolated

    @property
    def is_sys_admin(self):
        return self.uuid == Role.SYS_ADMIN_ROLE_UUID

    @property
    def is_usr_admin(self):
        return self.uuid == Role.USR_ADMIN_ROLE_UUID

    @property
    def is_everyone(self):
        return self.uuid == Role.EVERYONE_ROLE_UUID

    @property
    def is_edit_lock(self):
        return self.uuid == Role.EDIT_LOCK_ROLE_UUID

    @property
    def is_system_role(self):
        return self.is_sys_admin or self.is_usr_admin or self.is_everyone or self.is_edit_lock

    def _get_system_role_label(self):
        if self.is_sys_admin:
            return Role.SYS_ADMIN_ROLE_LABEL
        elif self.is_usr_admin:
            return Role.USR_ADMIN_ROLE_LABEL
        elif self.is_everyone:
            return Role.EVERYONE_ROLE_LABEL
        elif self.is_edit_lock:
            return Role.EDIT_LOCK_ROLE_LABEL
        else:
            return ''

    def raise_no_role_owner_exception(self):
        from .exceptions import NoRoleOwnerException
        if self.is_sys_admin:
            raise NoRoleOwnerException('システム管理者権限を持つユーザがいなくなるのでこの操作はできません')
        elif self.is_usr_admin:
            raise NoRoleOwnerException('ユーザー管理者権限を持つユーザがいなくなるのでこの操作はできません')
        elif self.is_everyone:
            raise NoRoleOwnerException('ユーザー管理者権限を持つユーザがいなくなるのでこの操作はできません')
        elif self.is_edit_lock:
            raise NoRoleOwnerException('ユーザー管理者権限を持つユーザがいなくなるのでこの操作はできません')
        else:
            raise NoRoleOwnerException('ロール所有者がいなくなるのでこの操作はできません')

    def save(self, for_self_role=False):
        """
        Roleを保存する
        """
        try:
            # Rolesテーブルにレコードを新規追加する
            self._session.add(self)
        except Exception as e:
            self._session.rollback()
            raise e

        # 本人ロール以外のロールを新規作成したユーザにはロールの所有権を付与する
        if not for_self_role and self._session.user is not None:
            from .user_role import UserRole
            user_role = UserRole(self._session, self._session.user.id, self.id, owner=True)
            user_role.save(ignore_authz=True)

    def update_name(self, new_name, modifier=None):
        try:
            self.name = new_name
            self._modifier_id = (modifier or self._session.user).id
            self._session.update(self)
        except Exception as e:
            self._session.rollback()
            raise e

        return self

    def delete(self):
        from .auth import Auth

        # # ロールに一人以上のユーザが所属している場合は例外を送出する
        # if self.has_joined_user() > 0:
        #     raise Exception('Can not delete the role that has user(s).')

        # 
        # 削除によってどのロールからも所有されなくなるデータがある場合は例外を送出する
        # (所有権は未実装なので、このチェックも未実装である
        #  現在はDatum.creatorが所有者となっている)
        # 
        # count = self._session.query(Auth).filter(Auth.role_id == self.id)\
        #                                  .filter(Auth.own == 1).count()

        if self.is_system_role:
            raise Exception(f'ロール({self.name})はシステムロールなので削除できません')

        try:
            self_id = self.id
            # 削除ロールに対する権限情報をauthsテーブルから全て削除する
            del_auth_stmt = delete(Auth).where(Auth.role_id==self.id)
            self._session.execute(del_auth_stmt)
            # ロールを削除する
            self._session.delete(self)
            # 削除ロールから全てのユーザを脱退させる
            # (ロールの削除はロールの所有権が必要なので、
            #  所有権フラグを持つUserRoleはロール削除の後に削除すること)
            del_userrole_stmt = delete(UserRole).where(UserRole.role_id==self_id)
            self._session.execute(del_userrole_stmt)
        except Exception as e:
            self._session.rollback()
            raise e

    def is_self_role(self) -> bool:
        """
        本人ロールの場合はTrueを返す
        """
        from .user import User
        stmt = select(func.count(User.id)).where(User.self_role_id==self.id)
        return self._session.scalars(stmt).one() > 0

    def is_joined_user(self, user) -> bool:
        from .user import User
        stmt1 = select(func.count(User.id)).where(User.self_role_id==self.id).where(User.id==user.id)
        stmt2 = select(func.count(UserRole.user_id)).where(UserRole.role_id==self.id).where(UserRole.user_id==user.id)
        count1 = self._session.scalars(stmt1).one()
        count2 = self._session.scalars(stmt2).one()
        return count1 + count2 > 0

    def count_joined_users(self) -> int:
        from .user import User
        stmt1 = select(func.count(User.id)).where(User.self_role_id==self.id)
        stmt2 = select(func.count(UserRole.user_id)).where(UserRole.role_id==self.id)
        count1 = self._session.scalars(stmt1).one()
        count2 = self._session.scalars(stmt2).one()
        return count1 + count2

    def is_owner(self, user) -> bool:
        stmt =  select(func.count(UserRole.user_id)).\
                where(UserRole.role_id==self.id).\
                where(UserRole.user_id==user.id).\
                where(UserRole.owner==True)
        return self._session.scalars(stmt).one() > 0

    def count_owners(self) -> int:
        stmt =  select(func.count(UserRole.user_id)).\
                where(UserRole.role_id==self.id).\
                where(UserRole.owner==True)
        return self._session.scalars(stmt).one()

    def has_joined_user(self) -> bool:
        return self.count_joined_users() > 0

    def get_joined_users(self, except_states=None):
        """
        ロールに所属する全てのユーザを返す
        (ユーザID順で返す)
        """
        from sqlalchemy import select, exists, and_, or_
        from streamcat.store.factory import UserFactory
        from .user import User

        exists_user_role = exists().where(and_(UserRole.role_id==self.id, UserRole.user_id==User.id))

        stmt =  select(User).\
                filter(or_(exists_user_role, User.self_role_id==self.id))
        stmt =  UserFactory(self._session)._add_except_states_criteria(stmt, except_states)
        stmt =  stmt.order_by(User.id)

        return self._session.scalars(stmt).all()

    def get_joined_members(self, except_states=None):
        """
        ロールに所属する全てのメンバを返す
        (ユーザID順で返す)
        """
        from streamcat.store.factory import UserFactory
        from .user import User

        stmt =  select(User, UserRole.owner).\
                outerjoin(UserRole, UserRole.user_id==User.id).\
                filter(UserRole.role_id==self.id)
        stmt =  UserFactory(self._session)._add_except_states_criteria(stmt, except_states)
        stmt =  stmt.order_by(User.id)

        results = self._session.execute(stmt).all()

        members = []
        for result in results:
            user = result[0]
            # Queryクラスは、query(User, ...)の結果にsessionを設定しないのでここで設定する
            user._session = self._session
            members.append(Role.Member(user, owner=result[1]))

        return members

    def is_last_owner(self, user):
        """
        指定されたユーザがただ一人の所有者ならTrueを返す
        """
        return self.is_owner(user) and self.count_owners() <= 1

    def owner_exists(self, members):
        """
        指定されたメンバリストに所有者が存在する場合はTrueを返す
        """
        for member in members:
            if member.owner:
                return True
        return False

    def join_member(self, member):
        """
        ロールにユーザを所属させる
        """
        if self.is_self_role():
            raise Exception('本人ロールに本人以外のユーザを所属させることはできません')

        if member.user.is_inactive:
            raise Exception('削除状態のユーザを所属させることはできません')

        from ..factory import UserRoleFactory
        factory = UserRoleFactory(self._session)

        if factory.exists(member.user.id, self.id):
            # ユーザ管理ロールが、この所属によって、ロールに所有者が居なくなる場合はエラーとする
            if self.is_usr_admin and member.owner == False and self.is_last_owner(member.user):
                self.raise_no_role_owner_exception()

            # 既にメンバの場合は所有権フラグを更新する
            user_role = factory.find_by_id(member.user.id, self.id)
            user_role.update_owner(member.owner)
        else:
            # ロールにメンバを追加する
            user_role = UserRole(self._session, member.user.id, self.id, member.owner)
            user_role.save()

    def leave_member(self, user):
        """
        ロールからユーザを脱退させる
        """
        if self.is_self_role():
            raise Exception('本人ロールからユーザを脱退させることはできません')

        from streamcat.store.factory import UserRoleFactory
        factory = UserRoleFactory(self._session)

        if factory.exists(user.id, self.id):
            # ユーザ管理ロールが、この脱退によって、ロールに所有者が居なくなる場合はエラーとする
            if self.is_usr_admin and self.is_last_owner(user):
                self.raise_no_role_owner_exception()
            # ロールからメンバを削除する
            user_role = factory.find_by_id(user.id, self.id)
            user_role.delete()

    def leave_others(self, except_user):
        """
        指定する1人を除いて、ロールから他のユーザを全て脱退させる
        """
        if self.is_self_role():
            raise Exception('本人ロールからユーザを脱退させることはできません')

        # ユーザ管理ロールが、この脱退によって、ロールに所有者が居なくなる場合はエラーとする
        if self.is_usr_admin and not self.is_owner(except_user):
            self.raise_no_role_owner_exception()

        from streamcat.store.factory import UserRoleFactory
        UserRoleFactory(self._session).delete_all_by_role_id(self.id, except_user_id=except_user.id)

    def init_members(self, members):
        """
        ロールの所属ユーザを初期化する
        """
        from .exceptions import NotAuthorizedException

        # 
        # 指定されたメンバリストの妥当性を検証する
        # 
        users = set()
        owner_exists = False
        for member in members:
            if member.user.is_inactive:
                raise Exception('削除状態のユーザを所属させることはできません')

            # 1人のUserが重複指定された場合はエラーとする
            if member.user in users:
                raise Exception(f'ユーザー({member.user.name})が重複して指定されました')
            else:
                users.add(member.user)

            # ロール所有者が設定されない場合はエラーとする
            if member.owner:
                owner_exists = True

        # ユーザ管理ロールが、この初期化によって、ロールに所有者が居なくなる場合はエラーとする
        if self.is_usr_admin and not owner_exists:
            self.raise_no_role_owner_exception()

        # 操作ユーザがロール所有者やユーザ管理者以外の場合はエラーとする
        self_user = self._session.user
        if not self.is_owner(self_user) and not self._session.has_usr_admin:
            raise NotAuthorizedException(f'ロール所有者またはユーザ管理者以外のユーザ({self_user})は所属ユーザの初期化をできません')

        # ロールから、自分以外のユーザを全て削除する
        for user in self.get_joined_users():
            if user == self_user:
                continue
            self.leave_member(user)

        # 自分以外のユーザを全て設定する
        self_member = None
        for member in members:
            if member.user == self_user:
                self_member = member
            else:
                self.join_member(member)

        if self_member is None:
            # 自分がメンバに指定されていない場合は自分を削除する
            self.leave_member(self_user)
        else:
            # 自分がメンバに指定されている場合は改めて追加する
            self.join_member(self_member)

    def init_authz(self, datum_id, read, write, exec=None, own=None):
        from .auth import Auth
        # own=Trueの場合は他の権限が設定できるよう先に設定する
        if own:
            self._init_authz_inner(datum_id, Auth.OWN_OP, permission=own)
        self._init_authz_inner(datum_id, Auth.READ_OP, permission=read)
        self._init_authz_inner(datum_id, Auth.WRITE_OP, permission=write)
        self._init_authz_inner(datum_id, Auth.EXEC_OP, permission=exec)
        # own=False, Noneの場合は他の権限の設定を終えた後に設定する
        if not own:
            self._init_authz_inner(datum_id, Auth.OWN_OP, permission=own)

    def clear_authz(self, datum_id):
        self.init_authz(datum_id, None, None, None, None)

    def _init_authz_inner(self, datum_id, operation, permission):
        from streamcat.store.factory import AuthFactory
        auth_factory = AuthFactory(self._session)

        if auth_factory.exists(self.id, datum_id, operation):
            auth = auth_factory.find_by_id(self.id, datum_id, operation)
            if permission is None:
                # permission=Noneが指定された場合はAuthレコードを削除する
                auth.delete()
            elif auth.permission != permission:
                auth.update(permission)
        elif permission is None:
            # permission=Noneが指定された場合は何もしない
            pass
        else:
            auth = auth_factory.create(self.id, datum_id, operation, permission=permission)
            auth.save()

    def to_json(self):
        return {
            'uuid'     : self.uuid,
            'name'     : self.name,
            'systemRole' : self._get_system_role_label(),
            'creator'  : self.creator_str,
            'createdAt': self.created_at_str
        }

    def __repr__(self):
        return f'Role({self.id}, {self.name})'

    def __eq__(self, other):
        return self.uuid == other.uuid

    def __ne__(self, other):
        return self.uuid != other.uuid

    def __hash__(self) -> int:
        return hash(self.uuid)
