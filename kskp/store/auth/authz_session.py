from kskp.store.auth.authz_query import Query
from .exceptions import NotAuthorizedException

class Session():
    """
    権限判定をしないSession
    DatumとそのサブクラスはSession.userに依存するので、
    インタフェースとしてこのクラスを定義する
    """

    def __init__(self, session_factory, user):
        self._session = session_factory()
        self._user = user

    @property
    def user(self):
        return self._user

    def commit(self):
        self._session.commit()

    def expire(self, obj):
        from kskp.core import Datum
        if isinstance(obj, Datum):
            tmp = obj.readable
            self._session.expire(obj)
            obj.readable = tmp
        else:
            self._session.expire(obj)

    def flush(self, obj):
        from kskp.core import Datum
        if isinstance(obj, Datum):
            tmp = obj.readable
            self._session.flush([obj])
            obj.readable = tmp
        else:
            self._session.flush([obj])

    def rollback(self):
        self._session.rollback()

    def close(self):
        self._session.close()

    def execute(self, sql):
        # テスト実行で二つのSessionを用いた時、片方のSessionで
        # search_pathが設定されないので、execute()の度に設定することにする
        import os
        from kskp.store import _is_unittest
        if _is_unittest():
            # カレントスキーマを設定する
            # (コミットされると、セッションが終了するまでその設定が持続する)
            sql1 = """
            SET search_path = {schema}; commit;
            """.format(schema=os.environ['KSKP_POSTGRESQL_SCHEMA_NAME'])
            self._session.execute(sql1)

        return self._session.execute(sql)

    def query(self, datum_type, *args):
        query = self._session.query(datum_type, *args)
        return Query(query, self)

    def add(self, obj):
        self._session.add(obj)

    def update(self, obj):
        raise NotAuthorizedException('認証なき更新はできません')

    def delete(self, obj):
        raise NotAuthorizedException('認証なき削除はできません')

class AuthzSession(Session):

    def __init__(self, session_factory, user):
        super().__init__(session_factory, user)
        self._readable_query = self._make_readable_query()

    @property
    def user(self):
        if self._user is None:
            raise Exception('AuthzSessionにuserが設定されていません')
        return self._user

    @user.setter
    def user(self, user):
        if user is None:
            raise Exception('AuthzSessionに設定したuserがNoneです')
        self._user = user

    def query(self, datum_type, *args):
        """
        参照用途でquery()を使用する場合は、AuthsテーブルとJOINする
        pathとdataプロパティは参照された時に権限を判定し、NGなら例外を送出する
        """
        import inspect
        from sqlalchemy.orm import with_expression
        from sqlalchemy.sql.expression import literal_column
        from kskp.core import Datum
        from .authz_query import Query, AuthzDatumQuery

        def is_type(obj_type, table_name):
            # datum_typeがDatumクラスかDatumを継承するクラスか否かを判定する
            # TODO: もう少し確実な判定方法に変更したい
            return inspect.isclass(obj_type) and hasattr(obj_type, '__tablename__') and obj_type.__tablename__ == table_name

        if is_type(datum_type, 'data'):
            # 下記を両方満たす場合にのみreadable=Trueとする
            # ・ユーザが属する全てのロールについて、Datumを参照する権限がTrue
            # ・Datumが属する全ての親フォルダについて、Datumを参照する権限がTrue
            readable_query = self._readable_query

            query = self._session.query(Datum).\
                                  options(with_expression(Datum.readable, readable_query.label('readable'))).\
                                  options(with_expression(Datum.user, literal_column(f"'{self.user.name}'")))

            return AuthzDatumQuery(query, self)

        else:
            query = self._session.query(datum_type, *args)
            return Query(query, self)
    
    def _make_readable_query(self):
        from sqlalchemy.orm import aliased
        from sqlalchemy.sql.expression import select, func, literal_column, text, false, and_, or_
        from kskp.core import Datum
        from .auth import Auth
        from .user import User
        from .user_role import UserRole

        # 相関条件を記述するとSQLAlchemyがFROM句にdataテーブルを追加するので、
        # それを回避するためtextで記述する
        Datum_id = text(str(Datum.id.compile()))

        # cte: Common Table Expression WITH句のこと
        D0 = aliased(Datum, name='D0')
        R = select([D0.id.label('leaf_id'), D0.id, D0.parent_id]).select_from(D0).\
            where(D0.id==Datum_id).\
            cte(name='R', recursive=True)

        # WITH句にUNION ALLを用いて再帰クエリとする
        D = aliased(Datum, name='D')
        R = R.union_all(
                select([R.c.leaf_id, D.id, D.parent_id]).\
                select_from(R.join(D, D.id==R.c.parent_id))
            )

        # select_from(Auth.join(Role, ...))と記述できないので、select()が使えない、そのためquery()を使う
        subquery = self._session.query(func.coalesce(func.bool_and(Auth.permission),false()).label("read")).\
                                outerjoin(UserRole, and_(UserRole.role_id==Auth.role_id, UserRole.user_id==self.user.id)).\
                                outerjoin(User, and_(User.self_role_id==Auth.role_id, User.id==self.user.id)).\
                                filter(Auth.datum_id==R.c.id).\
                                filter(Auth.operation==Auth.READ_OP).\
                                filter(or_(UserRole.user_id!=None, User.id!=None)).label('')

        subquery = select([func.bool_and(subquery).label('readable')]).select_from(R).\
                   where(R.c.leaf_id==Datum_id).as_scalar()


        # SELECT句内にWITH句を記述する必要があるが、SQLAlchemyではそれができないようだ
        # そのため、ここでWITH句を含むSELECT文をtextで記述してこれをメインのSELECT文に含める
        subquery = str(subquery.compile(compile_kwargs={"literal_binds": True}))

        # query.count()でSQLAlchemyがエラーを送出するため、
        # これを回避するためtextをselectオブジェクトでラップする
        return select([literal_column(subquery)]).as_scalar()

    def add(self, obj):
        from kskp.core import Datum
        from kskp.store import Folder, Flow
        from kskp.store.auth import User, Role, UserRole, Auth
                
        if isinstance(obj, Datum):
            # Datumの新規追加時はその親フォルダの変更権限を判定する
            # (ROOTフォルダの新規追加の場合は変更を許可する)
            if obj.parent_id is not None and not self.writable(obj):
                parent = obj.find_parent()
                raise NotAuthorizedException(f'{self.user.name}は{parent.label}の変更権限がないため{obj.label}を新規追加できませんでした')

            # Datumを新規追加する
            self._session.add(obj)

            # 新規追加したDatumのreadableはNoneにする
            self._session.flush([obj])
            self._session.expire(obj, ['readable'])

            # 本人ロールが無ければ作成し、ユーザを本人ロールに所属させる
            self_role = self.user.load_self_role()
            # Datumを新規追加したユーザには無条件に所有権を付与する
            from kskp.store.factory import AuthFactory
            own_auth = AuthFactory(self).create(self_role.id, obj.id, Auth.OWN_OP, True)
            self._session.add(own_auth)
            self._session.flush([own_auth])

            # FolderまたはFlowの場合は実行権限を付与する
            folder_or_flow = isinstance(obj, Folder) or isinstance(obj, Flow) or None
            # 本人ロールへ追加データの権限を付与する
            self_role.init_authz(obj.id, True, True, exec=folder_or_flow, own=True)

            # everyoneロールが無ければ作成し、ユーザをeveryoneロールに所属させる
            from kskp.store.factory import RoleFactory
            everyone_role = RoleFactory(self).load_everyone_role()
            everyone_role.join_user(self.user)
            # everyoneロールへ追加データの権限を付与する
            everyone_role.init_authz(obj.id, True, True, exec=folder_or_flow)

        elif isinstance(obj, User):
            # ユーザ管理者のみユーザを新規追加できる
            if not self.has_usr_admin():
                raise NotAuthorizedException('ユーザを作成できませんでした')
            self._session.add(obj)

        elif isinstance(obj, UserRole):
            # ユーザ管理者かロールの作成者のみ、ロールにユーザを追加できる
            if not self.is_role_creator(obj.role_id) and not self.has_usr_admin():
                raise NotAuthorizedException('ロールにユーザを追加できませんでした')
            self._session.add(obj)

        elif isinstance(obj, Role):
            # ロールの新規作成は誰でもできる
            self._session.add(obj)

        elif isinstance(obj, Auth):
            # ユーザ管理者かデータの所有者のみ、その権限を追加できる
            if not self.ownership(obj.datum_id) and not self.has_usr_admin():
                datum = self._session.query(Datum).get(obj.datum_id)
                raise NotAuthorizedException(f'{self.user}は{datum.label}に{obj.operation}権限を追加できませんでした')
            self._session.add(obj)

        else:
            if not self.has_sys_admin():
                # 上記以外の書き込みはシステム管理者権限が必要
                raise NotAuthorizedException('no anthz!', str(obj))       
            self._session.add(obj)

    def update(self, obj):
        from kskp.core import Datum
        from kskp.store.auth import User, Role, UserRole, Auth

        if isinstance(obj, Datum):
            # Datumの変更権限を判定する
            if not self.writable(obj):
                raise NotAuthorizedException((f'{self.user.name}は更新権限がないため{obj.label}を更新できません'))
            if obj._data is not None:
                # JSON列への変更はflag_modified()を使ってSQLAlchemyに知らせないとDBに反映されない
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(obj, "_data")

        elif isinstance(obj, User):
            # ユーザ管理者か本人のみ、ユーザを変更できる
            if not self.is_self_user(obj.id) and not self.has_usr_admin():
                raise NotAuthorizedException(f'{self.user.name}は更新権限がないためユーザ({obj})を変更できませんでした')

        elif isinstance(obj, UserRole):
            raise NotAuthorizedException('UserRoleは更新できません')

        elif isinstance(obj, Role):
            # ユーザ管理者かロールの作成者のみ、ロールを変更できる
            if not self.is_role_creator(obj.id) and not self.has_usr_admin():
                raise NotAuthorizedException('ロールを変更できませんでした')

        elif isinstance(obj, Auth):
            # ユーザ管理者かデータの所有者のみ、その権限を変更できる
            if not self.ownership(obj.datum_id) and not self.has_usr_admin():
                raise NotAuthorizedException('権限を変更できませんでした')

        elif not self.has_sys_admin():
            # 上記以外の書き込みはシステム管理者権限が必要
            raise NotAuthorizedException('no anthz!')

        # objをSessionに格納する
        self._session.add(obj)
        # SessionにあるobjをDBに格納する
        self.flush(obj)
        # Sessionにあるobjを期限切れ状態にすることで、objの参照時にDBからリロードされるようにする
        self.expire(obj)

    def delete(self, obj):
        from kskp.core import Datum
        from kskp.store.auth import User, Role, UserRole, Auth

        if isinstance(obj, Datum):
            if self.writable(obj):
                # 削除データの権限を全て削除する
                from kskp.store.factory import AuthFactory
                AuthFactory(self).delete_all_by_datum_id(obj.id)
            else:
                raise NotAuthorizedException((f'{self.user.name}は更新権限がないため{obj.label}を削除できません'))

        elif isinstance(obj, User):
            # ユーザ管理者のみ、ユーザを削除できる
            if not self.has_usr_admin():
                raise NotAuthorizedException('ユーザを削除できませんでした')

        elif isinstance(obj, UserRole):
            # ユーザ管理者かロールの作成者のみ、ロールからユーザを削除できる
            if not self.is_role_creator(obj.role_id) and not self.has_usr_admin():
                raise NotAuthorizedException('ロールからユーザを削除できませんでした')

        elif isinstance(obj, Role):
            # ユーザ管理者かロールの作成者のみ、ロールを削除できる
            if not self.is_role_creator(obj.id) and not self.has_usr_admin():
                raise NotAuthorizedException('ロールを削除できませんでした')

        elif isinstance(obj, Auth):
            # ユーザ管理者かデータの所有者のみ、その権限を削除できる
            if not self.ownership(obj.datum_id) and not self.has_usr_admin():
                raise NotAuthorizedException('権限を削除できませんでした')

        elif not self.has_sys_admin():
            # 上記以外の書き込みはシステム管理者権限が必要
            raise NotAuthorizedException('no anthz!')   

        # 削除する
        self._session.delete(obj)


    def writable(self, datum) -> bool:
        """
        ユーザIDとDatumについて書き込み権限の有無を判定する
        """
        from .auth import Auth
        return self._operatable(datum, Auth.WRITE_OP)

    def executable(self, datum) -> bool:
        """
        ユーザIDとDatumについて実行権限の有無を判定する
        """
        from .auth import Auth
        return self._operatable(datum, Auth.EXEC_OP)

    def ownership(self, datum_id) -> bool:
        """
        ユーザIDとDatumについて所有権の有無を判定する
        """
        from kskp.core import Datum
        from .auth import Auth
        # ここでfind_by_id・find_by_uuidを使うとdatum.readableがFalseに何故かなってしまう
        # query(Datum).get()を使うとdatum.readableがNoneに何故かなってしまう
        result = self._session.query(Datum.id, Datum.parent_id).filter(Datum.id==datum_id).one_or_none()
        if result is None:
            raise Exception('datum is None')
        return self._operatable(result, Auth.OWN_OP)

    def is_addition_root_by_sysadmin(self, datum_id, operation) -> bool:
        """
        システム管理者がルートフォルダの所有権を操作する場合、Trueを返す
        """
        from kskp.store.factory import DatumFactory
        from .auth import Auth
        datum = DatumFactory(self).find_by_id(datum_id)
        return datum.parent_id is None and operation == Auth.OWN_OP and self.has_sys_admin()

    def _operatable(self, datum, operation) -> bool:
        """
        ユーザIDとDatumについてoperation権限の有無を判定する
        """
        from sqlalchemy import func, false, and_, or_
        from sqlalchemy.orm import aliased
        from .auth import Auth
        from .user import User
        from .user_role import UserRole

        A = aliased(Auth, name='A')
        U = aliased(User, name='U')
        UR = aliased(UserRole, name='UR')

        query = self._session.query(func.coalesce(func.bool_and(A.permission),false()).label('operation')).\
                              outerjoin(UR, and_(UR.role_id==A.role_id, UR.user_id==self.user.id)).\
                              outerjoin(U,  and_(U.self_role_id==A.role_id, U.id==self.user.id)).\
                              filter(A.operation==operation).\
                              filter(or_(UR.user_id!=None, U.id!=None))

        if datum.parent_id is None:
            # ルートフォルダの場合は親フォルダの権限判定をしない
            query = query.filter(A.datum_id==datum.id)
        elif datum.id is None:
            # Datumの新規追加の場合(datum.id=None)は親フォルダのoperation権限だけを判定する
            query = query.filter(A.datum_id==datum.parent_id)
        else:
            # 親フォルダとDatumの両方のoperation権限がある場合にのみ、operationの実行がOKの判定をする
            A0 = aliased(Auth, name='A0')
            U0 = aliased(User, name='U0')
            UR0 = aliased(UserRole, name='UR0')

            subquery = self._session.query(func.coalesce(func.bool_and(A0.permission),false()).label('operation_of_parent')).\
                        select_from(A0).outerjoin(UR0, and_(UR0.role_id==A0.role_id, UR0.user_id==self.user.id)).\
                        outerjoin(U0, and_(U0.self_role_id==U.self_role_id, U0.id==self.user.id)).\
                        filter(A0.operation==A.operation).\
                        filter(A0.datum_id==datum.parent_id).\
                        filter(or_(UR0.user_id!=None, U0.id!=None)).label('')

            query = query.filter(A.datum_id==datum.id).\
                          filter(True == subquery)

        result = query.one_or_none()

        return result.operation == True

    def has_sys_admin(self) -> bool:
        from .user_role import UserRole
        from .role import Role
        query = self._session.query(Role).\
                            outerjoin(UserRole, UserRole.role_id==Role.id).\
                            filter(Role.uuid == Role.SYS_ADMIN_ROLE_UUID).\
                            filter(UserRole.user_id==self.user.id)
        return query.count() > 0

    def has_usr_admin(self) -> bool:
        from .user_role import UserRole
        from .role import Role
        query = self._session.query(Role).\
                            outerjoin(UserRole, UserRole.role_id==Role.id).\
                            filter(Role.uuid == Role.USR_ADMIN_ROLE_UUID).\
                            filter(UserRole.user_id==self.user.id)
        return query.count() > 0       

    def is_role_creator(self, role_id) -> bool:
        """
        操作ユーザがRoleの作成者であればTrueを返す
        """
        from .role import Role
        query = self._session.query(Role).\
                filter(Role.id==role_id).filter(Role._creator_id==self.user.id)

        return query.count() > 0

    def is_self_user(self, user_id) -> bool:
        """
        操作ユーザがUserの本人であればTrueを返す
        """
        return user_id == self.user.id

    def is_datum_creator(self, datum_id) -> bool:
        """
        操作ユーザがDatumの作成者であればTrueを返す
        """
        from kskp.core import Datum
        query = self._session.query(Datum).\
                filter(Datum.id==datum_id).filter(Datum._creator_id==self.user.id)

        return query.count() > 0
