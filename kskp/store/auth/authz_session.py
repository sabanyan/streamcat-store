from .exceptions import NotAuthorizedException

class AuthzSession():

    _session = None

    def __init__(self, session_factory, user_uuid):
        self._session = session_factory()
        self._user_uuid = user_uuid

    @property
    def user_id(self):
        if self._user_id is None:
            raise Exception('AuthzSessionにuser_idが設定されていません')
        return self._user_id

    @user_id.setter
    def user_id(self, user_id):
        from .user import User
        if user_id is None:
            raise Exception('AuthzSessionに設定したuser_idがNoneです')
        # elif not User.exists(user_id):
        #     raise Exception(f'AuthzSessionに設定したuser_id({user_id})は存在しません')
        self._user_id = user_id

    @property
    def user_uuid(self):
        if self._user_uuid is None:
            raise Exception('AuthzSessionにuser_uuidが設定されていません')
        return self._user_uuid

    @user_uuid.setter
    def user_uuid(self, user_uuid):
        if user_uuid is None:
            raise Exception('AuthzSessionに設定したuser_uuidがNoneです')
        self._user_uuid = user_uuid

    def commit(self):
        self._session.commit()

    def rollback(self):
        self._session.rollback()

    def query(self, datum_type, *args):
        """
        参照用途でquery()を使用する場合は、AuthsテーブルとJOINする
        pathとdataプロパティは参照された時に権限を判定し、NGなら例外を送出する
        """
        import inspect
        from sqlalchemy import func, literal_column
        from sqlalchemy.orm import with_expression
        from sqlalchemy.dialects.postgresql import BOOLEAN
        from kskp.core import Datum
        from .authz_query import AuthzQuery
        from .auth import Auth
        from .user_group import UserGroup
        from .group import Group

        # datum_typeがDatumクラスかDatumを継承するクラスか否かを判定する
        # TODO: もう少し確実な判定方法に変更したい
        if inspect.isclass(datum_type) and hasattr(datum_type, '__tablename__') and datum_type.__tablename__ == 'data':
            # ユーザが属する全てのグループについて、Datumを参照する権限がTrueまたはNullの場合にのみ
            # Datum.readable=Trueとする
            subquery = self._session.query(func.bool_and(Auth.read).label("read")).\
                                     outerjoin(Group, Group.id==Auth.group_id).\
                                     outerjoin(UserGroup, UserGroup.group_id==Group.id).\
                                     filter(UserGroup.user_id==self.user_id)

            query = self._session.query(datum_type).\
                                  options(with_expression(Datum.readable, subquery.filter(Auth.datum_id==Datum.id).label('readable')))
            # query = self._session.query(datum_type).\
            #                       options(with_expression(Datum.readable, literal_column('false', type_=BOOLEAN).label('readable')))
            
            return AuthzQuery(query, self.user_id)

        else:
            return self._session.query(datum_type, *args)
    
    def add(self, obj):
        from kskp.core import Datum
        from kskp.store import Folder
        from .group import Group
        from .user import User

        if isinstance(obj, Datum):
            # Datumの新規追加時はその親フォルダの変更権限を判定する
            # (ROOTフォルダの新規追加の場合は変更を許可する)
            if obj.parent_id is not None and not self.writable_by_id(self.user_id, obj.parent_id):
                parent_uuid = Datum.get_uuid_by_id(obj.parent_id)
                parent = Folder.find_by_uuid(parent_uuid)
                raise NotAuthorizedException(f'{parent.label}の変更権限がないため{obj.label}を新規追加できませんでした')

            # Datumを新規追加する
            self._session.add(obj)

            # everyoneグループが無ければ作成し、ユーザをeveryoneグループに所属させる
            everyone_group = Group.load_everyone_group()
            everyone_group.join_user(self.user_id)
            # everyoneグループへ追加データの権限を付与する
            everyone_group.init_authz(obj.id, True, True, True)

            # 本人グループが無ければ作成し、ユーザを本人グループに所属させる
            user = User.find_by_uuid(self.user_uuid)
            if user is not None:
                self_group = user.load_self_group()
                # 本人グループへ追加データの権限を付与する
                self_group.init_authz(obj.id, True, True, True)

        else:
            if not self.has_admin():
                # Datum以外の書き込みは管理者権限が必要
                raise NotAuthorizedException('no anthz!')       
            self._session.add(obj)

    def delete(self, obj):
        from kskp.core import Datum
        if isinstance(obj, Datum):
            if not self.writable_by_id(self.user_id, obj.id):
                raise NotAuthorizedException((f'{self.user_id}は更新権限がないため{obj.label}を削除できません'))
        elif not self.has_admin():
            # Datum以外の書き込みは管理者権限が必要
            raise NotAuthorizedException('no anthz!')   

        # 削除する
        self._session.delete(obj)

    def execute(self, sql):
        return self._session.execute(sql)

    def writable(self, user_id, datum_uuid):
        """
        ユーザIDとDatumについて書き込み権限の有無を判定する
        """
        from kskp.core import Datum
        datum_id = Datum.get_id_by_uuid(datum_uuid)
        return self.writable_by_id(user_id, datum_id)

    def writable_by_id(self, user_id, datum_id):
        from sqlalchemy import func

        from .auth import Auth
        from .user_group import UserGroup
        from .group import Group

        query = self._session.query(func.bool_and(Auth.write).label("write")).\
                              outerjoin(Group, Group.id==Auth.group_id).\
                              outerjoin(UserGroup, UserGroup.group_id==Group.id).\
                              filter(UserGroup.user_id==self.user_id)

        result = query.filter(Auth.datum_id==datum_id).one_or_none()

        return result.write == True

    def has_admin(self):
        from .user_group import UserGroup
        from .group import Group

        subquery = self._session.query(Group).\
                                 outerjoin(UserGroup, UserGroup.group_id==Group.id).\
                                 filter(Group.uuid == Group.ADMIN_GROUP_UUID).\
                                 filter(UserGroup.user_id==self.user_id)

        ret = self._session.query(subquery.exists())

        return ret