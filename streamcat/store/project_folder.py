from streamcat.core import SavableDatum
from .folder import Folder

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
        self.type = SavableDatum.PROJECT_TYPE

    def moving(self, parent_uuid, prev_parent_id, lock_uuid=None, modifier=None):
        """
        ゴミ箱へほかされるか、ゴミ箱から元の場所に戻す場合を除いて
        プロジェクトは移動できない
        """
        from streamcat.store.finder import DatumFinder
        finder = DatumFinder(self._session)
        trash_folder = finder.load_trash_folder()

        if parent_uuid==trash_folder.uuid or prev_parent_id==trash_folder.id:
            # ゴミ箱へほかされる、またはゴミ箱から戻される場合
            pass
        else:
            raise Exception('プロジェクトは移動できません')
        # 
        super().moving(parent_uuid, prev_parent_id, lock_uuid=lock_uuid, modifier=modifier)

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
        from streamcat.store.finder import RoleFinder
        usr_admin_role = RoleFinder(self._session).load_usr_admin_role()
        usr_admin_role.init_authz(self.id, True, True, exec=True, own=True)

        # プロジェクトロールを作成する
        # (作成者は各プロジェクトロールの所有者メンバになる)
        readers_role = self._load_readers_role()
        writers_role = self._load_writers_role()
        owners_role = self._load_owners_role()

        # 作成者はプロジェクトロールに所有者メンバとして参加する
        from streamcat.store.auth import Role
        member = Role.Member(self._session.user, owner=True)
        readers_role.join_member(member)
        writers_role.join_member(member)
        owners_role.join_member(member)

        # 作成者(creator)の本人ロールからDatumの権限を削除する
        self_role = self.creator.load_self_role()
        self_role.clear_authz(self.id)

    def update_label(self, label, modifier=None):
        """
        Projectのlabel列を更新する
        """
        from streamcat.store.auth import NotAuthorizedException
        if not self._session.ownership(self.id):
            raise NotAuthorizedException(f'プロジェクト管理者以外のメンバはプロジェクト({self.label})の名称を変更できません')

        # 更新処理はFolderクラスと同じ
        return super().update_label(label, modifier=modifier)

    def _find_readers_role(self):
        """
        Readersロールを取得する
        """
        from sqlalchemy import select, exists, and_
        from streamcat.store.auth import User, Role, Auth

        not_exists_self_role = ~exists().where(User.self_role_id==Role.id)
        exists_read      =  exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.READ_OP))
        not_exists_write = ~exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.WRITE_OP))
        exists_exec      =  exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.EXEC_OP))
        not_exists_own   = ~exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.OWN_OP))

        stmt =  select(Role).\
                where(Role.uuid.notin_([Role.SYS_ADMIN_ROLE_UUID, Role.USR_ADMIN_ROLE_UUID, Role.EVERYONE_ROLE_UUID])).\
                where(not_exists_self_role).\
                where(exists_read).\
                where(not_exists_write).\
                where(exists_exec).\
                where(not_exists_own).\
                order_by(Role.id)

        # 複数のロールが紐づいている場合は、role_idが小さい方がプロジェクトロールのはず
        return self._session.scalars(stmt).first()

    def _find_writers_role(self):
        """
        Writersロールを取得する
        """
        from sqlalchemy import select, exists, and_
        from streamcat.store.auth import User, Role, Auth

        not_exists_self_role = ~exists().where(User.self_role_id==Role.id)
        not_exists_read  = ~exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.READ_OP))
        exists_write     =  exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.WRITE_OP))
        not_exists_exec  = ~exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.EXEC_OP))
        not_exists_own   = ~exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.OWN_OP))

        stmt =  select(Role).\
                where(Role.uuid.notin_([Role.SYS_ADMIN_ROLE_UUID, Role.USR_ADMIN_ROLE_UUID, Role.EVERYONE_ROLE_UUID])).\
                where(not_exists_self_role).\
                where(not_exists_read).\
                where(exists_write).\
                where(not_exists_exec).\
                where(not_exists_own).\
                order_by(Role.id)

        # 複数のロールが紐づいている場合は、role_idが小さい方がプロジェクトロールのはず
        return self._session.scalars(stmt).first()

    def _find_owners_role(self):
        """
        Ownersロールを取得する
        """
        from sqlalchemy import select, exists, and_
        from streamcat.store.auth import User, Role, Auth

        not_exists_self_role = ~exists().where(User.self_role_id==Role.id)
        not_exists_read  = ~exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.READ_OP))
        not_exists_write = ~exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.WRITE_OP))
        not_exists_exec  = ~exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.EXEC_OP))
        exists_own       =  exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.OWN_OP))

        stmt =  select(Role).\
                where(Role.uuid.notin_([Role.SYS_ADMIN_ROLE_UUID, Role.USR_ADMIN_ROLE_UUID, Role.EVERYONE_ROLE_UUID])).\
                where(not_exists_self_role).\
                where(not_exists_read).\
                where(not_exists_write).\
                where(not_exists_exec).\
                where(exists_own).\
                order_by(Role.id)

        # 複数のロールが紐づいている場合は、role_idが小さい方がプロジェクトロールのはず
        return self._session.scalars(stmt).first()

    def _load_readers_role(self):
        """
        Readersロールを取得する、存在しない場合は作成する
        """
        # Readersロールが無ければ作成する
        readers_role = self._find_readers_role()
        if readers_role is None:
            from streamcat.store.finder import RoleFinder
            role_name = self.label[:8] + '_readers'
            readers_role = RoleFinder(self._session).create(role_name, delete_on_isolated=True)
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
            from streamcat.store.finder import RoleFinder
            role_name = self.label[:8] + '_writers'
            writers_role = RoleFinder(self._session).create(role_name, delete_on_isolated=True)
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
            from streamcat.store.finder import RoleFinder
            role_name = self.label[:8] + '_owners'
            owners_role = RoleFinder(self._session).create(role_name, delete_on_isolated=True)
            owners_role.save()
            owners_role.init_authz(self.id, read=None, write=None, exec=None, own=True)
        return owners_role

    def _update_timestamp(self):
        try:
            # FIXME: ユーザIDに変更がなければタイプスタンプは更新されないようだ
            self._modifier_id = self._session.user.id
            self._session.update(self)
        except Exception as e:
            self._session.rollback()
            raise e

    def throw_away(self):
        """
        プロジェクトをゴミ箱にほかす
        """
        from streamcat.store.auth import NotAuthorizedException
        if not self._session.ownership(self.id):
            raise NotAuthorizedException(f'プロジェクト管理者以外のメンバはプロジェクト({self.label})を削除できません')

        # ほかす処理はFolderクラスと同じ
        return super().throw_away()

    def put_back(self):
        """
        直前の親のStoreの直下に戻す
        """
        from streamcat.store.auth import NotAuthorizedException
        if not self._session.ownership(self.id):
            raise NotAuthorizedException('プロジェクト管理者以外のメンバはプロジェクトを元に戻せません')

        # 戻す処理はFolderクラスと同じ
        return super().put_back()

    def delete(self):
        """
        プロジェクトを削除する
        """
        from streamcat.store.auth import NotAuthorizedException
        if not self._session.ownership(self.id):
            raise NotAuthorizedException(f'プロジェクト管理者以外のメンバはプロジェクト({self.label})を削除できません')

        # 削除処理はFolderクラスと同じ
        super().delete()

    def duplicate(self, new_label, new_parent:Folder=None):
        """
        自身の複製を作成して保存する
        """
        # 複製元と同じフォルダに複製を作成する
        parent = new_parent or self.find_parent()
        new_project = parent.create_project_folder(new_label)
        # ディレクトリファイルは共有しない
        new_project.save()
        # 子Datumを複製する
        self._duplicate_children(new_project)
        return new_project

    def is_joined_user(self, user):
        from sqlalchemy import select, func, any_
        from streamcat.store.auth import User, Auth, UserRole

        # 操作ユーザの所属するロールを抽出するクエリ
        UR = select(UserRole.role_id).select_from(UserRole).where(UserRole.user_id==user.id)
        U  = select(User.self_role_id).select_from(User).where(User.id==user.id)

        # ロールの抽出にはインデックスを参照させるためUNIONを用いる
        stmt =  select(func.count(Auth.id)).\
                where(Auth.datum_id==self.id).\
                where(Auth.role_id==any_(UR.union_all(U)).scalar_subquery())
        return self._session.scalars(stmt).one() > 0

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
        from streamcat.store.auth import Role, NotAuthorizedException

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
        from streamcat.store.auth import NotAuthorizedException

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
        from sqlalchemy import select
        from streamcat.store.auth import Role, NotAuthorizedException
        from .exceptions import OptimisticLockException

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
        stmt = select(ProjectFolder.modified_at).where(ProjectFolder.id==self.id)
        modified_at = self._session.scalars(stmt).one_or_none()
        if modified_at != last_modified_at:
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
            if owners_role.is_joined_user(self_user):
                # 自分がプロジェクト管理者に指定されている場合、
                # 変更前のプロジェクト管理者に必ず自分は含まれているのでメンバ設定する必要は無い
                pass
            else:
                # ユーザ管理者はプロジェクト管理者でなくと所属ユーザを変更できるため、
                # 変更前のプロジェクト管理者にユーザ管理者が存在しない場合がある
                readers_role.join_member(Role.Member(self_user))
                writers_role.join_member(Role.Member(self_user))
                owners_role.join_member(Role.Member(self_user))

    def get_joined_members(self, except_role_uuid=None):
        """
        所属する全てのユーザを返す
        """
        from sqlalchemy import select, func, case, exists, and_, or_, false
        from streamcat.store.auth import User, Auth, Role, UserRole

        # 
        # プロジェクトの権限判定にのみ対応している(フォルダ権限をオーバーライドしない仕様)
        # Auth.datum_idにインデックスを設定することで速度は改善される
        # 

        # AuthのTableオブジェクト
        A = Auth.__table__
        
        exists_user_role = exists().where(and_(UserRole.user_id==User.id, UserRole.role_id==A.c.role_id))
        not_exists_role = ~exists().where(and_(Role.id==A.c.role_id, Role.uuid==except_role_uuid))

        AU = select(
                A.c.datum_id,
                A.c.operation,
                User.id.label('user_id'),
                func.coalesce(func.bool_and(A.c.permission),false()).label('permission')
             ).\
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
        READER_PERMISSIONS = SavableDatum.PERMISSION_READ | SavableDatum.PERMISSION_EXEC
        WRITE_PERMISSIONS  = READER_PERMISSIONS | SavableDatum.PERMISSION_WRITE
        OWNER_PERMISSIONS  = WRITE_PERMISSIONS  | SavableDatum.PERMISSION_OWN

        # プロジェクトへの参加タイプのソート順を定義する
        MEMBER_TYPE_CONV = {0: ProjectFolder.OWNER_MEMBER_TYPE,
                            1: ProjectFolder.WRITER_MEMBER_TYPE,
                            2: ProjectFolder.READER_MEMBER_TYPE,
                            9: ProjectFolder.UNKNOWN_TYPE}

        stmt =  select(
                    User,
                    case(
                        {READER_PERMISSIONS : 2,
                         WRITE_PERMISSIONS  : 1,
                         OWNER_PERMISSIONS  : 0},
                        value=func.sum(
                                case((AU.c.permission,
                                    case((AU.c.operation=='read',  SavableDatum.PERMISSION_READ),
                                         (AU.c.operation=='write', SavableDatum.PERMISSION_WRITE),
                                         (AU.c.operation=='exec',  SavableDatum.PERMISSION_EXEC),
                                         (AU.c.operation=='own',   SavableDatum.PERMISSION_OWN)
                                    )
                                ))
                              ),
                        else_=9
                    ).label('int_type')
                ).\
                select_from(AU).\
                join(User, User.id==AU.c.user_id).\
                group_by(User.id).\
                order_by('int_type', User.name)

        # Resultクラスは、select(User, ...)の結果にsessionを設定しないのでここで設定する
        members = []
        for row in self._session.execute(stmt).all():
            user = row[0]
            type = MEMBER_TYPE_CONV.get(row[1])
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
