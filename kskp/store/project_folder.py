from kskp.core import Datum
from kskp.store import Folder, OptimisticLockException

class ProjectFolder(Folder):

    class Member():
        """
        Userとプロジェクトへの参加タイプを纏める
        """
        def __init__(self, user, member_type):
            self.user = user
            self.type = member_type 

        def to_json(self):
            ret = self.user.to_json()
            ret.update({'type':self.type})
            return ret

        def __repr__(self):
            return f'Member({self.user.id}, {self.user.name}, {self.type})'

        def __eq__(self, other):
            return self.user == other.user and self.type == other.type

        def __ne__(self, other):
            return self.user != other.user or self.type != other.type

    __mapper_args__ = {
        'polymorphic_identity' : 'project'
    }

    READER_MEMBER_TYPE = 'Reader'
    WRITER_MEMBER_TYPE = 'Writer'
    OWNER_MEMBER_TYPE  = 'Owner'
    OTHER_MEMBER_TYPE  = 'Unkown'

    def __init__(self, session, parent, label):
        """
        コンストラクタ
        """
        super().__init__(session, parent, label)

        # データタイプを設定する
        self.type = Datum.PROJECT_TYPE

    def move(self, parent_uuid, modifier=None):
        """
        ゴミ箱へにほかされるか、ゴミ箱から元の場所に戻す場合を除いて
        プロジェクトは移動できない
        """
        from kskp.store.factory import DatumFactory
        factory = DatumFactory(self._session)
        trash_folder = factory.load_trash_folder()

        if parent_uuid == trash_folder.uuid:
            # ゴミ箱にほかされる場合
            return super().move(parent_uuid, modifier=modifier)
        elif self.prev_parent_id is not None and parent_uuid == factory.find_by_id(self.prev_parent_id).uuid:
            # 元の場所に戻す場合
            return super().move(parent_uuid, modifier=modifier)
        else:
            raise Exception('プロジェクトは移動できません')

    def save(self, file_path=None):
        """
        Projectを保存する
        """
        if self.is_root:
            raise Exception('プロジェクトはルートとして保存できません')
        if not self.find_parent().is_root:
            raise Exception('プロジェクトはライブラリ直下以外の場所に保存できません')

        # 保存処理はFolderクラスと同じ
        super().save()

        # ユーザ管理者は全てのDatumの参照・更新・実行、及び権限の変更ができること
        # (ProjectにRWXO権限を付与することでこれを実現する)
        # (ユーザ管理者をプロジェクト管理者から外すことはできない)
        from kskp.store.factory import RoleFactory
        usr_admin_role = RoleFactory(self._session).load_usr_admin_role()
        usr_admin_role.init_authz(self.id, True, True, exec=True, own=True)

        # プロジェクトロールを作成する
        # (作成者は各プロジェクトロールの所有者メンバになる)
        readers_role = self._load_readers_role()
        writers_role = self._load_writers_role()
        owners_role = self._load_owners_role()

        # 作成者はプロジェクトロールに所有者メンバとして参加する
        from kskp.store.auth import Role
        member = Role.Member(self._session.user, owner=True)
        readers_role.join_member(member)
        writers_role.join_member(member)
        owners_role.join_member(member)

        # 作成者(creator)の本人ロールからDatumの権限を削除する
        self_role = self.creator.load_self_role()
        self_role.clear_authz(self.id)

    def update_data(self, label, modifier=None):
        """
        Projectのlabel列を更新する
        """
        from kskp.store.auth import NotAuthorizedException
        if not self._session.ownership(self.id):
            raise NotAuthorizedException(f'プロジェクト管理者以外のメンバはプロジェクト({self.label})の名称を変更できません')

        # 更新処理はFolderクラスと同じ
        super().update_data(label, modifier=modifier)

    def _find_readers_role(self):
        """
        Readersロールを取得する
        """
        from sqlalchemy import exists, and_
        from kskp.store.auth import User, Role, Auth

        not_exists_self_role = ~exists().where(User.self_role_id==Role.id)
        exists_read      =  exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.READ_OP))
        not_exists_write = ~exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.WRITE_OP))
        exists_exec      =  exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.EXEC_OP))
        not_exists_own   = ~exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.OWN_OP))

        query = self._session.query(Role).\
                     filter(Role.uuid.notin_([Role.SYS_ADMIN_ROLE_UUID, Role.USR_ADMIN_ROLE_UUID, Role.EVERYONE_ROLE_UUID])).\
                     filter(not_exists_self_role).\
                     filter(exists_read).\
                     filter(not_exists_write).\
                     filter(exists_exec).\
                     filter(not_exists_own)
        
        # 複数のロールが紐づいている場合は、role_idが小さい方がプロジェクトロールのはず
        return query.order_by(Role.id).first()   

    def _find_writers_role(self):
        """
        Writersロールを取得する
        """
        from sqlalchemy import exists, and_
        from kskp.store.auth import User, Role, Auth

        not_exists_self_role = ~exists().where(User.self_role_id==Role.id)
        not_exists_read  = ~exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.READ_OP))
        exists_write     =  exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.WRITE_OP))
        not_exists_exec  = ~exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.EXEC_OP))
        not_exists_own   = ~exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.OWN_OP))

        query = self._session.query(Role).\
                     filter(Role.uuid.notin_([Role.SYS_ADMIN_ROLE_UUID, Role.USR_ADMIN_ROLE_UUID, Role.EVERYONE_ROLE_UUID])).\
                     filter(not_exists_self_role).\
                     filter(not_exists_read).\
                     filter(exists_write).\
                     filter(not_exists_exec).\
                     filter(not_exists_own)
        
        # 複数のロールが紐づいている場合は、role_idが小さい方がプロジェクトロールのはず
        return query.order_by(Role.id).first()   

    def _find_owners_role(self):
        """
        Ownersロールを取得する
        """
        from sqlalchemy import exists, and_
        from kskp.store.auth import User, Role, Auth

        not_exists_self_role = ~exists().where(User.self_role_id==Role.id)
        not_exists_read  = ~exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.READ_OP))
        not_exists_write = ~exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.WRITE_OP))
        not_exists_exec  = ~exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.EXEC_OP))
        exists_own       =  exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.OWN_OP))

        query = self._session.query(Role).\
                     filter(Role.uuid.notin_([Role.SYS_ADMIN_ROLE_UUID, Role.USR_ADMIN_ROLE_UUID, Role.EVERYONE_ROLE_UUID])).\
                     filter(not_exists_self_role).\
                     filter(not_exists_read).\
                     filter(not_exists_write).\
                     filter(not_exists_exec).\
                     filter(exists_own)
        
        # 複数のロールが紐づいている場合は、role_idが小さい方がプロジェクトロールのはず
        return query.order_by(Role.id).first()       

    def _load_readers_role(self):
        """
        Readersロールを取得する、存在しない場合は作成する
        """
        # Readersロールが無ければ作成する
        readers_role = self._find_readers_role()
        if readers_role is None:
            from kskp.store.factory import RoleFactory
            role_name = self.label[:8] + '_readers'
            readers_role = RoleFactory(self._session).create(role_name, delete_on_isolated=True)
            readers_role.save()
            readers_role.init_authz(self.id, read=True, write=None, exec=True)
        return readers_role

    def _load_writers_role(self):
        """
        Writersロールを取得する、存在しない場合は作成する
        """
        # Writersロールが無ければ作成する
        writers_role = self._find_writers_role()
        if writers_role is None:
            from kskp.store.factory import RoleFactory
            role_name = self.label[:8] + '_writers'
            writers_role = RoleFactory(self._session).create(role_name, delete_on_isolated=True)
            writers_role.save()
            writers_role.init_authz(self.id, read=None, write=True, exec=None)
        return writers_role

    def _load_owners_role(self):
        """
        Ownersロールを取得する、存在しない場合は作成する
        """
        # Ownersロールが無ければ作成する
        owners_role = self._find_owners_role()
        if owners_role is None:
            from kskp.store.factory import RoleFactory
            role_name = self.label[:8] + '_owners'
            owners_role = RoleFactory(self._session).create(role_name, delete_on_isolated=True)
            owners_role.save()
            owners_role.init_authz(self.id, read=None, write=None, exec=None, own=True)
        return owners_role

    def _update_timestamp(self):
        try:
            self._modifier_id = self._session.user.id
            self._session.update(self)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

    def throw_away(self):
        """
        プロジェクトをゴミ箱にほかす
        """
        from kskp.store.auth import NotAuthorizedException
        if not self._session.ownership(self.id):
            raise NotAuthorizedException(f'プロジェクト管理者以外のメンバはプロジェクト({self.label})を削除できません')

        # ほかす処理はFolderクラスと同じ
        return super().throw_away()

    def put_back(self):
        """
        直前の親のStoreの直下に戻す
        """
        from kskp.store.auth import NotAuthorizedException
        if not self._session.ownership(self.id):
            raise NotAuthorizedException('プロジェクト管理者以外のメンバはプロジェクトを元に戻せません')

        # 戻す処理はFolderクラスと同じ
        super().put_back()

    def delete(self):
        """
        プロジェクトを削除する
        """
        from kskp.store.auth import NotAuthorizedException
        if not self._session.ownership(self.id):
            raise NotAuthorizedException(f'プロジェクト管理者以外のメンバはプロジェクト({self.label})を削除できません')

        # 削除処理はFolderクラスと同じ
        super().delete()

    def is_joined_user(self, user):
        from sqlalchemy import exists, and_, or_
        from kskp.store.auth import User, Auth, UserRole

        exists_user_role = exists().where(and_(UserRole.user_id==user.id, UserRole.role_id==Auth.role_id))
        exists_user = exists().where(and_(User.self_role_id==Auth.role_id, User.id==user.id))

        query = self._session.query(Auth).\
                     filter(Auth.datum_id==self.id).\
                     filter(or_(exists_user_role, exists_user))

        return query.count() > 0

    def is_last_owner(self, user):
        """
        指定されたユーザがただ一人のプロジェクト管理者ならTrueを返す
        """
        owners_role = self._load_owners_role()
        return owners_role.is_joined_user(user) and owners_role.count_joined_users() <= 1

    def owner_exists(self, members):
        """
        指定されたメンバリストにプロジェクト管理者が存在する場合はTrueを返す
        """
        for member in members:
            if member.type == ProjectFolder.OWNER_MEMBER_TYPE:
                return True
        return False

    def join_member(self, member):
        """
        プロジェクトにユーザを所属させる
        """
        from kskp.store.auth import Role, NotAuthorizedException

        # 操作ユーザがプロジェクト管理者以外の場合はエラーとする
        self_user = self._session.user
        owners_role = self._load_owners_role()
        if not owners_role.is_joined_user(self_user) and not self._session.has_usr_admin():
            raise NotAuthorizedException('プロジェクト管理者以外のメンバはユーザの所属処理はできません')        

        # 最終更新時刻を用いた楽観的排他制御
        self._update_timestamp()

        # プロジェクトロールに所属させる
        # (1人のUserが複数種のプロジェクトロールに所属しないようにする)
        readers_role = self._load_readers_role()
        writers_role = self._load_writers_role()
        if member.type == ProjectFolder.READER_MEMBER_TYPE:
            role_member = Role.Member(member.user)
            readers_role.join_member(role_member)
            writers_role.leave_member(role_member.user)
            owners_role.leave_member(role_member.user)
        elif member.type == ProjectFolder.WRITER_MEMBER_TYPE:
            role_member = Role.Member(member.user)
            readers_role.join_member(role_member)
            writers_role.join_member(role_member)
            owners_role.leave_member(role_member.user)
        elif member.type == ProjectFolder.OWNER_MEMBER_TYPE:
            role_member = Role.Member(member.user, owner=True)
            readers_role.join_member(role_member)
            writers_role.join_member(role_member)
            owners_role.join_member(role_member)
        else:
            raise Exception('member.typeの値が誤っています')

    def leave_member(self, user):
        """
        プロジェクトからユーザを脱退させる
        """
        from kskp.store.auth import NotAuthorizedException

        # 操作ユーザがプロジェクト管理者以外の場合はエラーとする
        self_user = self._session.user
        owners_role = self._load_owners_role()
        if not owners_role.is_joined_user(self_user) and not self._session.has_usr_admin():
            raise NotAuthorizedException('プロジェクト管理者以外のメンバはユーザの脱退処理はできません')

        # 最終更新時刻を用いた楽観的排他制御
        self._update_timestamp()

        # 全てのプロジェクトロールから脱退させる
        readers_role = self._load_readers_role()
        writers_role = self._load_writers_role()
        readers_role.leave_member(user)
        writers_role.leave_member(user)
        owners_role.leave_member(user)

    def init_members(self, members, last_modified_at):
        """
        プロジェクトの所属ユーザを初期化する
        """
        from kskp.store.auth import Role, NotAuthorizedException

        # 
        # 指定されたメンバリストの妥当性を検証する
        # 
        users = set()
        for member in members:
            if member.user.is_inactive:
                raise Exception(f'削除状態のユーザー({member.user.name})が指定されました')

            if member.type not in (ProjectFolder.OWNER_MEMBER_TYPE, ProjectFolder.READER_MEMBER_TYPE, ProjectFolder.WRITER_MEMBER_TYPE):
                raise Exception(f'無効なmember.type({member.type})が指定されました')

            # 1人のUserが複数種のプロジェクトロールに所属する場合はエラーとする
            if member.user in users:
                raise Exception(f'ユーザー({member.user.name})が重複して指定されました')
            else:
                users.add(member.user)

        # 
        # 操作ユーザがプロジェクト管理者以外の場合はエラーとする
        # 
        self_user = self._session.user
        owners_role = self._load_owners_role()
        if not owners_role.is_joined_user(self_user) and not self._session.has_usr_admin():
            raise NotAuthorizedException('プロジェクト管理者以外のメンバは所属ユーザの初期化をできません')

        # 
        # 最終更新時刻を用いた楽観的排他制御
        # (メンバの更新はRoleの更新だが、3つのRoleの最終更新時刻をProjectを取得するたびに
        #  返すのはSQLのコストが高いと考え、Projectの最終更新時刻を利用することにした)
        # 
        result = self._session.query(ProjectFolder.modified_at).filter(ProjectFolder.id==self.id).one_or_none()
        if result is None or last_modified_at != result[0]:
            raise OptimisticLockException(f'プロジェクト({self.label})は他ユーザーが編集しているため更新できませんでした')
        # 最終更新時刻を更新する
        self._update_timestamp()

        # 
        # 自分以外のユーザを全て削除する
        # 
        readers_role = self._load_readers_role()
        writers_role = self._load_writers_role()
        readers_role.leave_others(except_user=self_user)
        writers_role.leave_others(except_user=self_user)
        owners_role.leave_others(except_user=self_user)

        # 
        # 自分以外のユーザをメンバ設定する
        # 
        self_member = None
        for member in members:
            if member.user == self_user:
                self_member = member
            elif member.type == ProjectFolder.READER_MEMBER_TYPE:
                role_member = Role.Member(member.user)
                readers_role.join_member(role_member)
            elif member.type == ProjectFolder.WRITER_MEMBER_TYPE:
                role_member = Role.Member(member.user)
                readers_role.join_member(role_member)
                writers_role.join_member(role_member)
            elif member.type == ProjectFolder.OWNER_MEMBER_TYPE:
                role_member = Role.Member(member.user, owner=True)
                readers_role.join_member(role_member)
                writers_role.join_member(role_member)
                owners_role.join_member(role_member)

        # 
        # 自分のメンバ設定をする
        # 
        if self_member is None:
            # 自分がプロジェクトメンバに指定されていない場合、自分を削除する
            readers_role.leave_member(self_user)
            writers_role.leave_member(self_user)
            owners_role.leave_member(self_user)
        elif self_member.type == ProjectFolder.READER_MEMBER_TYPE:
            # 自分が閲覧者に指定されている場合、readersロールの所有権を失う
            readers_role.join_member(Role.Member(self_user))
            writers_role.leave_member(self_user)
            owners_role.leave_member(self_user)
        elif self_member.type == ProjectFolder.WRITER_MEMBER_TYPE:
            # 自分が編集者に指定されている場合、readersとwritersロールの所有権を失う
            readers_role.join_member(Role.Member(self_user))
            writers_role.join_member(Role.Member(self_user))
            owners_role.leave_member(self_user)
        elif self_member.type == ProjectFolder.OWNER_MEMBER_TYPE:
            # 自分がプロジェクト管理者に指定されている場合、何もしない
            pass

    def get_joined_members(self, except_role_uuid=None):
        """
        所属する全てのユーザを返す
        """
        from sqlalchemy import select, func, case, exists, and_, or_, false
        from kskp.store.auth import User, Auth, Role, UserRole

        # 
        # プロジェクトの権限判定にのみ対応している(フォルダ権限をオーバーライドしない仕様)
        # Auth.datum_idにインデックスを設定することで速度は改善される
        # 

        # AuthのTableオブジェクト
        A = Auth.__table__
        
        exists_user_role = exists().where(and_(UserRole.user_id==User.id, UserRole.role_id==A.c.role_id))
        not_exists_role = ~exists().where(and_(Role.id==A.c.role_id, Role.uuid==except_role_uuid))

        AU = select([
                A.c.datum_id,
                A.c.operation,
                User.id.label('user_id'),
                func.coalesce(func.bool_and(A.c.permission),false()).label('permission')
             ]).\
             select_from(
                A.outerjoin(User, or_(exists_user_role, User.self_role_id==A.c.role_id))
             ).\
             where(A.c.datum_id==self.id)

        if except_role_uuid is None:
            AU = AU.where(A.c.datum_id==self.id)
        else:
            AU = AU.where(and_(A.c.datum_id==self.id, not_exists_role))

        AU = AU.group_by(A.c.datum_id, A.c.operation, User.id).alias('AU')

        # プロジェクトへの参加タイプと権限設定ののビットフラグの対応
        READER_PERMISSIONS = Datum.PERMISSION_READ | Datum.PERMISSION_EXEC
        WRITE_PERMISSIONS  = READER_PERMISSIONS | Datum.PERMISSION_WRITE
        OWNER_PERMISSIONS  = WRITE_PERMISSIONS  | Datum.PERMISSION_OWN

        query = self._session.query(
                    User,
                    case(
                        {READER_PERMISSIONS : ProjectFolder.READER_MEMBER_TYPE,
                         WRITE_PERMISSIONS  : ProjectFolder.WRITER_MEMBER_TYPE,
                         OWNER_PERMISSIONS  : ProjectFolder.OWNER_MEMBER_TYPE},
                        value=func.sum(
                                case([(AU.c.permission,
                                    case([(AU.c.operation=='read',  Datum.PERMISSION_READ),
                                          (AU.c.operation=='write', Datum.PERMISSION_WRITE),
                                          (AU.c.operation=='exec',  Datum.PERMISSION_EXEC),
                                          (AU.c.operation=='own',   Datum.PERMISSION_OWN)
                                    ])
                                )])
                              ),
                        else_=ProjectFolder.OTHER_MEMBER_TYPE
                    ).label('type')
                ).\
                select_from(AU).\
                join(User, User.id==AU.c.user_id).\
                group_by(User.id).\
                order_by('type', User.name)

        # Queryオブジェクトに代わりここでUserオブジェクトにsessionを設定する
        members = []
        for row in query.all():
            user = row[0]
            type = row[1]
            user._session = self._session
            members.append(ProjectFolder.Member(user, type))
        return members

    def to_json(self):
        ret = super().to_json()
        # メンバ設定の楽観的排他制御に最終更新時刻を用いる
        ret['modifiedAt'] = self.modified_at.strftime('%Y-%m-%d %H:%M:%S.%f')
        # プロジェクト管理者だけがプロジェクトの更新と削除とメンバ設定ができる
        ret['allowlist']['update'] = self.ownership
        ret['allowlist']['delete'] = self.ownership
        ret['allowlist']['move'] = False
        ret['allowlist']['findMember'] = self.ownership
        ret['allowlist']['updateMember'] = self.ownership
        return ret
