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

    def is_joined_member(self, user):
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
        from kskp.store.factory import RoleFactory
        
        # ユーザの本人ロールが無ければ作成する
        member.user.load_self_role()
        # ユーザの本人ロールを取得する
        # (member.user.load_self_role()で取得できるRoleはユーザのsession持つので、操作者のsessionでRoleを再取得する)
        factory = RoleFactory(self._session)
        self_role = factory.find_by_id(member.user.self_role_id)

        if member.type == ProjectFolder.READER_MEMBER_TYPE:
            self_role.init_authz(self.id, read=True, write=None, exec=True)
        elif member.type == ProjectFolder.WRITER_MEMBER_TYPE:
            self_role.init_authz(self.id, read=True, write=True, exec=True)
        elif member.type == ProjectFolder.OWNER_MEMBER_TYPE:
            self_role.init_authz(self.id, read=True, write=True, exec=True, own=True)
        else:
            raise Exception('member.typeの値が誤っています')
    
    def leave_member(self, user):
        """
        プロジェクトからユーザを脱退させる
        """
        # この脱退によって、プロジェクトに管理者が居なくなる場合はエラーとする
        owner_exists = False
        for member in self.get_joined_members():
            if member.type == ProjectFolder.OWNER_MEMBER_TYPE:
                owner_exists = True
                break
        if not owner_exists:
            raise Exception('この脱退処理でプロジェクト管理者がいなくなります')
        
        self_role = user.load_self_role()
        self_role.clear_authz(self.id)    

    def init_members(self, members):
        """
        プロジェクトの所属ユーザを初期化する
        """
        from kskp.store.auth import Auth

        # プロジェクト管理者が設定されない場合はエラーとする
        owner_exists = False
        for member in members:
            if member.type == ProjectFolder.OWNER_MEMBER_TYPE:
                owner_exists = True
            elif member.type not in (ProjectFolder.READER_MEMBER_TYPE, ProjectFolder.WRITER_MEMBER_TYPE):
                raise Exception(f'無効なmember.type({member.type})が指定されました')
        if not owner_exists:
            raise Exception('プロジェクト管理者が設定されていません')

        self_user = self._session.user

        try:
            # 自分以外のユーザを全て削除する
            self_role = self_user.load_self_role()
            del_query = self._session.query(Auth).filter(Auth.datum_id==self.id).filter(Auth.role_id!=self_role.id)
            del_query.delete()
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

        # 自分以外のユーザを全て設定する
        self_member = None
        for member in members:
            if member.user == self_user:
                self_member = member
                continue
            self.join_member(member)

        if self_member is None:
            # メンバリストに自分が指定されていない場合は自分を削除する
            self_role = self_user.load_self_role()
            self_role.clear_authz(self.id) 
        else:
            # メンバリストに自分が指定されている場合は改めて追加する
            self.join_member(self_member)

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
