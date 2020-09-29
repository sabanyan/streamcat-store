from kskp.core import Datum
from kskp.store import Folder

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

        # Ownersロールを作成する
        owners_role = self._load_owners_role()

        # 作成者はOwnersロールに参加する
        self_user = self._session.user
        owners_role.join_user(self_user)

        # 作成者(creator)の本人ロールからDatumの権限を削除する
        self_role = self.creator.load_self_role()
        self_role.clear_authz(self.id)

    def _find_readers_role(self):
        """
        Readersロールを取得する
        """
        from sqlalchemy import exists, and_
        from kskp.store.auth import User, Role, Auth

        not_exists_self_role = ~exists().where(User.self_role_id==Role.id)
        exists_read  = exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.READ_OP))
        not_exists_write = ~exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.WRITE_OP))
        exists_exec  = exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.EXEC_OP))
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
        exists_read  = exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.READ_OP))
        exists_write = exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.WRITE_OP))
        exists_exec  = exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.EXEC_OP))
        not_exists_own = ~exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.OWN_OP))

        query = self._session.query(Role).\
                     filter(Role.uuid.notin_([Role.SYS_ADMIN_ROLE_UUID, Role.USR_ADMIN_ROLE_UUID, Role.EVERYONE_ROLE_UUID])).\
                     filter(not_exists_self_role).\
                     filter(exists_read).\
                     filter(exists_write).\
                     filter(exists_exec).\
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
        exists_read  = exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.READ_OP))
        exists_write = exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.WRITE_OP))
        exists_exec  = exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.EXEC_OP))
        exists_own   = exists().where(and_(Auth.datum_id==self.id, Auth.role_id==Role.id, Auth.operation==Auth.OWN_OP))

        query = self._session.query(Role).\
                     filter(Role.uuid.notin_([Role.SYS_ADMIN_ROLE_UUID, Role.USR_ADMIN_ROLE_UUID, Role.EVERYONE_ROLE_UUID])).\
                     filter(not_exists_self_role).\
                     filter(exists_read).\
                     filter(exists_write).\
                     filter(exists_exec).\
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
            readers_role = RoleFactory(self._session).create(self.label[:8] + '_readers')
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
            writers_role = RoleFactory(self._session).create(self.label[:8] + '_writers')
            writers_role.save()
            writers_role.init_authz(self.id, read=True, write=True, exec=True)
        return writers_role

    def _load_owners_role(self):
        """
        Ownersロールを取得する、存在しない場合は作成する
        """
        # Ownersロールが無ければ作成する
        owners_role = self._find_owners_role()
        if owners_role is None:
            from kskp.store.factory import RoleFactory
            owners_role = RoleFactory(self._session).create(self.label[:8] + '_owners')
            owners_role.save()
            owners_role.init_authz(self.id, read=True, write=True, exec=True, own=True)
        return owners_role

    def throw_away(self):
        """
        プロジェクトをほかす
        """
        from kskp.store.auth import NotAuthorizedException
        if not self._session.ownership(self.id):
            raise NotAuthorizedException('プロジェクト管理者以外のメンバはプロジェクトを削除できません')

        # ほかす処理はFolderクラスと同じ
        super().throw_away()

    def delete(self):
        """
        プロジェクトを削除する
        """
        from kskp.store.auth import NotAuthorizedException
        if not self._session.ownership(self.id):
            raise NotAuthorizedException('プロジェクト管理者以外のメンバはプロジェクトを削除できません')

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

    def join_member(self, member):
        """
        プロジェクトにユーザを所属させる
        """
        from kskp.store.auth import NotAuthorizedException

        # 操作ユーザがプロジェクト管理者以外の場合はエラーとする
        self_user = self._session.user
        owners_role = self._load_owners_role()
        if not owners_role.is_joined_user(self_user):
            raise NotAuthorizedException('プロジェクト管理者以外のメンバはユーザの所属処理はできません')        

        # この所属によって、プロジェクトに管理者が居なくなる場合(ユーザ管理者は除外)はエラーとする
        if member.type != ProjectFolder.OWNER_MEMBER_TYPE and \
           owners_role.is_joined_user(member.user) and \
           owners_role.count_joined_users() <= 2:
            raise Exception('この所属処理でプロジェクト管理者がいなくなります')

        # プロジェクトロールに所属させる
        # (1人のUserが複数種のプロジェクトロールに所属しないようにする)
        readers_role = self._load_readers_role()
        writers_role = self._load_writers_role()
        if member.type == ProjectFolder.READER_MEMBER_TYPE:
            readers_role.join_user(member.user)
            writers_role.leave_user(member.user)
            owners_role.leave_user(member.user)
        elif member.type == ProjectFolder.WRITER_MEMBER_TYPE:
            writers_role.join_user(member.user)
            readers_role.leave_user(member.user)
            owners_role.leave_user(member.user)
        elif member.type == ProjectFolder.OWNER_MEMBER_TYPE:
            owners_role.join_user(member.user)
            readers_role.leave_user(member.user)
            writers_role.leave_user(member.user)
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
        if not owners_role.is_joined_user(self_user):
            raise NotAuthorizedException('プロジェクト管理者以外のメンバはユーザの脱退処理はできません')

        # この脱退によって、プロジェクトに管理者が居なくなる場合(ユーザ管理者は除外)はエラーとする
        if owners_role.is_joined_user(user) and owners_role.count_joined_users() <= 2:
            raise Exception('この脱退処理でプロジェクト管理者がいなくなります')

        # 全てのプロジェクトロールから脱退させる
        readers_role = self._load_readers_role()
        writers_role = self._load_writers_role()
        readers_role.leave_user(user)
        writers_role.leave_user(user)
        owners_role.leave_user(user)

    def init_members(self, members):
        """
        プロジェクトの所属ユーザを初期化する
        """
        from kskp.store.auth import NotAuthorizedException

        # 指定されたメンバリストの妥当性を検証する
        users = set()
        owner_exists = False
        for member in members:
            # プロジェクト管理者が設定されない場合はエラーとする
            if member.type == ProjectFolder.OWNER_MEMBER_TYPE:
                owner_exists = True
            elif member.type not in (ProjectFolder.READER_MEMBER_TYPE, ProjectFolder.WRITER_MEMBER_TYPE):
                raise Exception(f'無効なmember.type({member.type})が指定されました')

            # 1人のUserが複数種のプロジェクトロールに所属する場合はエラーとする
            if member.user in users:
                raise Exception(f'ユーザ({member.user.name})が重複して指定されました')
            else:
                users.add(member.user)

        if not owner_exists:
            raise Exception('プロジェクト管理者が設定されていません')

        # 操作ユーザがプロジェクト管理者以外の場合はエラーとする
        self_user = self._session.user
        owners_role = self._load_owners_role()
        if not owners_role.is_joined_user(self_user):
            raise NotAuthorizedException('プロジェクト管理者以外のメンバは所属ユーザの初期化をできません')

        # 自分以外のユーザを全て削除する
        readers_role = self._load_readers_role()
        writers_role = self._load_writers_role()
        readers_role.leave_all_users()
        writers_role.leave_all_users()
        
        # Ownersプロジェクトロールから、自分以外のユーザを全て削除する
        for user in owners_role.get_joined_users():
            if user == self_user:
                continue
            owners_role.leave_user(user)

        # 自分以外のユーザを全て設定する
        self_member = None
        for member in members:
            if member.type == ProjectFolder.READER_MEMBER_TYPE:
                readers_role.join_user(member.user)
            elif member.type == ProjectFolder.WRITER_MEMBER_TYPE:
                writers_role.join_user(member.user)
            elif member.type == ProjectFolder.OWNER_MEMBER_TYPE:
                if member.user == self_user:
                    self_member = member
                else:
                    owners_role.join_user(member.user)

        # メンバリストに自分が指定されていない場合は自分を削除する
        if self_member is None:
            owners_role.leave_user(self_user) 

    def get_joined_members(self):
        """
        所属する全てのユーザを返す
        """
        from sqlalchemy import select, func, case, exists, and_, or_, false
        from kskp.store.auth import User, Auth, UserRole

        # 
        # プロジェクトの権限判定にのみ対応している(フォルダ権限をオーバーライドしない仕様)
        # Auth.datum_idにインデックスを設定することで速度は改善される
        # 

        # AuthのTableオブジェクト
        A = Auth.metadata.sorted_tables[0]
        
        exists_user_role = exists().where(and_(UserRole.user_id==User.id, UserRole.role_id==Auth.role_id))

        AU = select([
                A.c.datum_id,
                A.c.operation,
                User.id.label('user_id'),
                func.coalesce(func.bool_and(A.c.permission),false()).label('permission')
             ]).\
             select_from(
                A.outerjoin(User, or_(exists_user_role, User.self_role_id==A.c.role_id))
             ).\
             where(A.c.datum_id==self.id).\
             group_by(A.c.datum_id, A.c.operation, User.id).alias('AU')

        query = self._session.query(
                    User,
                    case(
                        {0b1010 : ProjectFolder.READER_MEMBER_TYPE,
                         0b1110 : ProjectFolder.WRITER_MEMBER_TYPE,
                         0b1111 : ProjectFolder.OWNER_MEMBER_TYPE},
                        value=func.sum(
                                case([(AU.c.permission,
                                    case([(AU.c.operation=='read', 0b1000),
                                          (AU.c.operation=='write', 0b100),
                                          (AU.c.operation=='exec',   0b10),
                                          (AU.c.operation=='own',     0b1)
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
        ret['allowlist']['findMember'] = self.ownership
        ret['allowlist']['updateMember'] = self.ownership
        return ret
