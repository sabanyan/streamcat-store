from .authz_result import Result
from .exceptions import NotAuthorizedException

class Session():
    """
    権限判定をしないSession
    DatumとそのサブクラスはSession.userに依存するので、
    インタフェースとしてこのクラスを定義する
    """

    def __init__(self, session, user):
        self._session = session
        self._user = user
        self._rollback = False

    @property
    def user(self):
        return self._user

    def print(self, stmt):
        """
        SQL文を出力する
        """
        from sqlalchemy.dialects import postgresql
        # paramstyle='named' : %, _, / などの特殊文字を重複して出力しない
        sql = str(stmt.compile(dialect=postgresql.dialect(paramstyle='named'), compile_kwargs={'literal_binds':True}))
        print(sql)

    def end(self):
        if self._rollback:
            self._session.rollback()
        else:
            self._session.commit()

    def expire(self, obj):
        from streamcat.core import SavableDatum
        if isinstance(obj, SavableDatum):
            tmp = obj._permissions
            self._session.expire(obj)
            obj._permissions = tmp
        else:
            self._session.expire(obj)

    def flush(self, obj):
        from streamcat.core import SavableDatum
        if isinstance(obj, SavableDatum):
            tmp = obj._permissions
            self._session.flush([obj])
            obj._permissions = tmp
        else:
            self._session.flush([obj])

    def rollback(self):
        # RollbackはSessionをclose()する時に行う
        self._rollback = True

    def close(self):
        self._session.close()

    def execute(self, stmt, synchronize_session='evaluate'):
        """
        SQLを実行する
        """
        # テスト実行で二つのSessionを用いた時、片方のSessionで
        # search_pathが設定されないので、execute()の度に設定することにする
        from sqlalchemy import TextClause, text
        from streamcat.core import _is_unittest, SCHEMA_NAME

        # selectか否かを判定する
        stmt_is_select = Session._is_select_stmt(stmt)

        # テスト実行で二つのSessionを用いた時、片方のSessionで
        # search_pathが設定されないので、execute()の度に設定することにする
        if _is_unittest() and isinstance(stmt, TextClause):
            # カレントスキーマを設定する
            # (コミットされると、セッションが終了するまでその設定が持続する)
            sql1 = text(f'SET search_path = {SCHEMA_NAME};')
            self._session.execute(sql1)

        # updateまたはdeleteを実行する場合
        if not stmt_is_select:
            # synchronize_session='fetch'でSQLを2回発行するらしい
            stmt = stmt.execution_options(synchronize_session=synchronize_session)

        # SQLを実行する
        result = self._session.execute(stmt)

        # select文の場合はResultオブジェクトに入れて返す
        return Result(result, self) if stmt_is_select else result

    @staticmethod
    def _is_select_stmt(stmt):
        """
        stmtがselectの場合はTrueを返す
        """
        from sqlalchemy.sql.expression import Select
        return isinstance(stmt, Select)

    def scalars(self, stmt):
        return Result(self._session.scalars(stmt), self)

    def get(self, datum_type, ident):
        result = self._session.get(datum_type, ident)
        if Result._is_base_model(result):
            result._session = self
        return result

    def add(self, obj, ignore_authz=False):
        self._session.add(obj)
        # 新規追加したobjをDBに反映する
        self.flush(obj)

    def update(self, obj):
        raise NotAuthorizedException('認証なき更新はできません')

    def delete(self, obj):
        raise NotAuthorizedException('認証なき削除はできません')

    @property
    def deleted(self):
        # return self._session.deleted
        raise NotImplemented('session.deletedを使った削除済み判定は何故かできない')

class AuthzSession(Session):

    def __init__(self, session_factory, user):
        super().__init__(session_factory, user)

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

    def scalars(self, stmt, **kwargs):
        """
        参照用途でquery()を使用する場合は、AuthsテーブルとJOINする
        pathとdataプロパティは参照された時に権限を判定し、NGなら例外を送出する
        """
        from sqlalchemy.orm import with_expression
        from sqlalchemy.sql.expression import null
        from streamcat.core import SavableDatum
        from .authz_result import AuthzDatumResult

        if not Session._is_select_stmt(stmt):
            raise TypeError('scalars()にSelect以外のstmtを指定できません')

        # selectの列情報を取得する
        column_descs = stmt.column_descriptions

        if len(column_descs) > 1:
            raise ValueError('scalars()には複数の列を抽出するSelectを指定できません')

        if AuthzSession._contains_model_column(column_descs, SavableDatum):
            # 下記を両方満たす場合にのみpermission=Trueとする
            # ・ユーザが属する全てのロールについて、DatumのpermissionがTrue
            # ・Datumが属する全ての親フォルダについて、DatumのpermissionがTrue

            # read,write,execのpermissionの値を取得する
            select_permissions = self._make_select_permissions()

            # ownのpermissionsの値を取得する
            select_ownership = self._make_select_ownership(SavableDatum.id)

            # Datumの親フォルダのuuidを取得する
            select_parent_uuid = self._make_select_parent_uuid()

            # Datumのフォルダパスを取得する
            if kwargs.get('folder_path'):
                select_folder_path = self._make_select_folder_path(SavableDatum.parent_id)
            else:
                select_folder_path = null()

            # Datumの移動前のフォルダパスを取得する
            if kwargs.get('prev_folder_path'):
                select_prev_folder_path = self._make_select_folder_path(SavableDatum.prev_parent_id)
            else:
                select_prev_folder_path = null()

            # read=TrueのDatumのみ抽出する
            # exists_readable = self._make_exists_readable()

            # Datumを抽出するSelect
            select_stmt =  stmt.options(with_expression(SavableDatum._permissions, select_permissions.label('permissions'))).\
                                options(with_expression(SavableDatum._ownership, select_ownership.label('ownership'))).\
                                options(with_expression(SavableDatum._parent_uuid, select_parent_uuid.label('parent_uuid'))).\
                                options(with_expression(SavableDatum._folder_path, select_folder_path.label('folder_path'))).\
                                options(with_expression(SavableDatum._prev_folder_path, select_prev_folder_path.label('prev_folder_path')))

            return AuthzDatumResult(self._session.scalars(select_stmt), self)
        else:
            return Result(self._session.scalars(stmt), self)

    def execute(self, stmt, synchronize_session='evaluate'):
        """
        SQLを実行する
        """
        from streamcat.core import SavableDatum

        if Session._is_select_stmt(stmt):
            colunm_descs = stmt.column_descriptions
            if AuthzSession._contains_model_column(colunm_descs, SavableDatum):
                raise ValueError('SelectにDatumを含む列がある場合、scalars()を使用してください')
        # SQLを実行する
        return super().execute(stmt, synchronize_session)

    @staticmethod
    def _contains_model_column(descs:list[dict], model_type):
        """
        model_typeオブジェクトを抽出するSelectの場合はTrueを返す
        NOTE: SavableDatumを継承するModelクラスはDataテーブルから抽出する
        """
        import inspect
        select_types = [d.get('type') for d in descs]
        # Select句にmodel_typeを継承するクラス型が指定されているか判定する
        model_type_contains = any(inspect.isclass(t) and issubclass(t, model_type) for t in select_types)
        return model_type_contains

    def _make_select_permissions(self):
        from sqlalchemy.sql.expression import select, literal_column
        
        select_stmt = self._make_select_permissions_inner().scalar_subquery()

        # SELECT句内にWITH句を記述する必要があるが、SQLAlchemyではそれができないようだ
        # そのため、ここでWITH句を含むSELECT文をtextで記述してこれをメインのSELECT文に含める
        select_stmt_str = str(select_stmt.compile(compile_kwargs={'literal_binds': True}))

        # query.count()でSQLAlchemyがエラーを送出するため、
        # これを回避するためtextをselectオブジェクトでラップする
        return select(literal_column(select_stmt_str))

    def _make_exists_readable(self):
        from sqlalchemy.sql.expression import exists, literal, text
        from streamcat.core import SavableDatum

        # label()は括弧で囲むが何故かAlias名(RA1)が付かない
        select_stmt = self._make_select_permissions_inner().label('RA1')

        # SELECT句内にWITH句を記述する必要があるが、SQLAlchemyではそれができないようだ
        # そのため、ここでWITH句を含むSELECT文をtextで記述してこれをメインのSELECT文に含める
        select_stmt_str = str(select_stmt.compile(compile_kwargs={'literal_binds': True}))

        # label()でAlias名が付かないのでSQL文の末尾に付ける
        return exists().select_from(text(select_stmt_str + ' RA1')).\
                        where(text('RA1.permissions') >= literal(SavableDatum.PERMISSION_READ))

    def _make_select_permissions_inner(self, datum_id=None):
        from sqlalchemy.orm import aliased
        from sqlalchemy.sql.expression import select, func, case, literal, true, false, and_, any_, text
        from streamcat.core import SavableDatum
        from .auth import Auth
        from .user import User
        from .role import Role
        from .user_role import UserRole

        # datum_id=Noneの場合は、親クエリのdataテーブルとの相関クエリとする
        if datum_id is None:
            # 相関条件を記述するとSQLAlchemyがFROM句にdataテーブルを追加するので、
            # それを回避するためtextで記述する
            datum_id = text(str(SavableDatum.id.compile()))

        # leaf_id : 検索対象Datumのid
        # id      : 検索対象DatumからRootDatumへの経路の全てのDatumのid
        # depth   : RootDatumからの深さ(検索対象Datum=1)
        D0 = aliased(SavableDatum, name='D0')
        R = select(D0.id.label('leaf_id'), D0.id, D0.parent_id, literal(1).label('depth')).\
            select_from(D0).\
            where(D0.id==datum_id).\
            cte(name='R', recursive=True)
            # cte: Common Table Expression WITH句のこと

        # WITH句にUNION ALLを用いて再帰クエリとする
        D = aliased(SavableDatum, name='D')
        R = R.union_all(
                select(R.c.leaf_id, D.id, D.parent_id, (R.c.depth+literal(1)).label('depth')).\
                select_from(R.join(D, D.id==R.c.parent_id))
            )

        # AuthのTableオブジェクト
        A0 = Auth.__table__

        # 検索対象のDatumの編集ロックを権限の判定条件に含める条件
        # TODO: permission_without_edit_lock列の追加でSELECT文が有意に遅くなっている
        datum_is_edit_locked = and_(A0.c.datum_id==datum_id,
                                    A0.c.role_id==select(Role.id).\
                                                  select_from(Role).\
                                                  where(Role.uuid==literal(Role.EDIT_LOCK_ROLE_UUID)).\
                                                  scalar_subquery())

        # 操作ユーザの所属するロールを抽出するクエリ
        UR = select(UserRole.role_id).select_from(UserRole).where(UserRole.user_id==self.user.id)
        U  = select(User.self_role_id).select_from(User).where(User.id==self.user.id)

        # 操作ユーザが複数のロールに所属する場合、対象のDatumの操作権限を判定する
        A = select(
                A0.c.datum_id,
                A0.c.operation,
                func.coalesce(func.bool_and(A0.c.permission),false()).label('permission'),
                func.bool_and(
                    case((
                        datum_is_edit_locked,
                        true()
                    ), else_=A0.c.permission)
                ).label('permission_without_edit_lock')
            ).\
            select_from(A0).\
            where(
                and_(
                    A0.c.operation.in_([Auth.READ_OP, Auth.WRITE_OP, Auth.EXEC_OP]),
                    # 以下のようなORを含む条件はインデックスを参照しないためUNIONを用いる
                    # or_(exists_user_role, exists_user)
                    A0.c.role_id==any_(UR.union_all(U).scalar_subquery())
                )
            ).\
            group_by(A0.c.datum_id, A0.c.operation).\
            alias('A')

        def auth_bool_and(column_of_A):
            """
            権限のオーバライドを演算する関数
            """
            return  func.coalesce(
                        # 各operationについて、自身からルート迄の各Datumに1つでも権限レコードが欠けている場合、
                        # そのoperationの権限はFalseである(経路の数=権限レコードの数)
                        and_(func.bool_and(column_of_A), func.max(R.c.depth)==func.count()),
                        false()
                    )

        # フォルダ権限のオーバライドを判定する
        RA = select(
                case((
                    # 編集ロック値を考慮しない権限の判定結果
                    auth_bool_and(A.c.permission_without_edit_lock),
                    case(
                        {'read' : SavableDatum.PERMISSION_READ ,
                         # 更新権限は、編集ロック値を考慮しない権限と、考慮する権限の二つの判定結果を返す
                         'write': case((auth_bool_and(A.c.permission), 
                                        SavableDatum.PERMISSION_WRITE | SavableDatum.PERMISSION_WRITER),
                                        else_=SavableDatum.PERMISSION_WRITER),
                         'exec' : SavableDatum.PERMISSION_EXEC},
                        value=A.c.operation,
                        else_=0
                    )
                ), else_=0).label('permission')
             ).\
             select_from(
                 R.outerjoin(A, R.c.id==A.c.datum_id)
             ).\
             where(R.c.leaf_id==datum_id).\
             group_by(A.c.operation).\
             alias('RA')

        # 権限フラグのAND演算をする(SQLの集計関数を入れ子にできないのでSELECT文でラップする)
        return select(func.sum(RA.c.permission).label('permissions')).select_from(RA)

    def _make_select_ownership(self, datum_id):
        """
        操作ユーザがDatumの所有権を有するか判定する
        (フォルダの所有権はオーバーライドしない)
        """
        from sqlalchemy import select, func, false, and_, any_
        from sqlalchemy.orm import aliased
        from .auth import Auth
        from .user import User
        from .user_role import UserRole

        A = aliased(Auth, name='A')

        # 操作ユーザの所属するロールを抽出するクエリ
        UR = select(UserRole.role_id).select_from(UserRole).where(UserRole.user_id==self.user.id)
        U  = select(User.self_role_id).select_from(User).where(User.id==self.user.id)

        select_stmt = select(func.coalesce(func.bool_and(A.permission),false()).label('owner')).\
                            select_from(A).\
                            where(
                                and_(
                                    A.datum_id==datum_id,
                                    A.operation==Auth.OWN_OP,
                                    A.role_id==any_(UR.union_all(U).scalar_subquery())
                                )
                            )
        return select_stmt

    def _make_select_parent_uuid(self):
        """
        Datumの親フォルダのuuidを取得する
        """
        from sqlalchemy import select, text
        from sqlalchemy.orm import aliased
        from streamcat.core import SavableDatum

        # 相関条件を記述するとSQLAlchemyがFROM句にdataテーブルを追加するので、
        # それを回避するためtextで記述する
        datum_parent_id_column = text(str(SavableDatum.parent_id.compile()))

        D = aliased(SavableDatum, name='D')

        select_stmt = select(D.uuid).\
                      select_from(D).\
                      where(D.id==datum_parent_id_column)
        return select_stmt

    def _make_select_folder_path(self, datum_parent_id):
        """
        Datumのフォルダパスを取得する
        """
        from sqlalchemy import select, func, text
        from sqlalchemy.orm import aliased
        from sqlalchemy.sql.expression import literal_column, case
        from streamcat.core import SavableDatum

        # 相関条件を記述するとSQLAlchemyがFROM句にdataテーブルを追加するので、
        # それを回避するためtextで記述する
        datum_parent_id_column = text(str(datum_parent_id.compile()))

        # label : 検索対象Datumのlabel
        # id    : 検索対象DatumからRootDatumへの経路の全てのDatumのid
        D0 = aliased(SavableDatum, name='D0')
        R = select(D0._label.label('label'), D0.id, D0.parent_id).\
            select_from(D0).\
            where(D0.id==datum_parent_id_column).\
            cte(name='R', recursive=True) 
            # cte: Common Table Expression WITH句のこと

        # WITH句にUNION ALLを用いて再帰クエリとする
        D = aliased(SavableDatum, name='D')
        R = R.union_all(
                select(D._label, D.id, D.parent_id).\
                select_from(R.join(D, D.id==R.c.parent_id))
            )

        Labels = select(R.c.label).\
                 select_from(R).\
                 order_by(R.c.id).scalar_subquery()
                 # フォルダ階層順にソートするためidでソートする 
                 # as_scalar()を指定しないとメインのSELECT文にFROM句が付加されてしまう

        # PostgreSQLにはGROUP_CONCATが無いので代わりに、ARRAY_TO_STRINGとARRAYを用いる
        func_exp = func.array_to_string(func.array(Labels), '/')

        # フォルダパスの先頭に'/'を付加する、フォルダパスがない場合はNULLを返す   
        func_exp = case(
                         # Labelsの件数が0件の場合、ARRAY_TO_STRING関数は空文字を返す
                        # NOTE: SQLAlchemy2.0対応 (RemovedIn20Warningの抑止)
                        # {'': None},
                        # value=func_exp,
                        (func_exp=='', None),
                        else_=func.concat('/', func_exp)
                    )

        # WITH句を含むSELECT文をtextで記述してこれをメインのSELECT文に含める
        func_exp_str = str(func_exp.compile(compile_kwargs={'literal_binds': True}))

        return select(literal_column(func_exp_str))

    def get(self, datum_type, ident):
        from streamcat.core import SavableDatum
        result = self._session.get(datum_type, ident)
        if Result._is_base_model(result):
            result._session = self
            # 参照権限のないDatumの場合はNoneを返す
            if isinstance(result, SavableDatum) and not result.readable:
                return None
        return result

    def add(self, obj, ignore_authz=False):
        from streamcat.core import SavableDatum
        from streamcat.store import Folder, Flow
        from streamcat.store.auth import User, Role, UserRole, Auth

        if isinstance(obj, SavableDatum):
            # Datumの新規追加時はその親フォルダの変更権限を判定する
            # (ROOTフォルダの新規追加の場合は変更を許可する)
            if obj.parent_id is not None and not self.writable(obj):
                parent = obj.find_parent()
                raise NotAuthorizedException(f'{self.user.name}は{parent.label}の変更権限がないため{obj.label}を新規追加できませんでした')

            # Datumを新規追加する
            self._session.add(obj)

            # 新規追加したDatumのpermissionsはNoneにする
            self._session.flush([obj])
            self._session.expire(obj, ['_permissions'])

            # 本人ロールが無ければ作成し、ユーザを本人ロールに所属させる
            self_role = self.user.load_self_role()
            # Datumを新規追加したユーザには無条件に所有権を付与する
            from streamcat.store.finder import AuthFinder
            own_auth = AuthFinder(self).create(self_role.id, obj.id, Auth.OWN_OP, True)
            self._session.add(own_auth)
            self._session.flush([own_auth])

            # FolderまたはFlowの場合は実行権限を付与する
            folder_or_flow = isinstance(obj, Folder) or isinstance(obj, Flow) or None
            # 本人ロールへ追加データの権限を付与する
            self_role.init_authz(obj.id, True, True, exec=folder_or_flow, own=True)

            # # usr_adminロールへ追加データの権限を付与する
            # from streamcat.store.factory import RoleFactory
            # usr_admin_role = RoleFactory(self).load_usr_admin_role()
            # usr_admin_role.init_authz(obj.id, True, True, exec=folder_or_flow)

        elif isinstance(obj, User):
            # ユーザ管理者のみユーザを新規追加できる
            if not self.has_usr_admin():
                raise NotAuthorizedException(f'ユーザー({obj})を作成できませんでした')
            self._session.add(obj)
            self.flush(obj)

        elif isinstance(obj, UserRole):
            # ユーザ管理者かロールの所有者のみ、ロールにユーザを追加できる
            if not ignore_authz and not self.is_role_owner(obj.role_id) and not self.has_usr_admin():
                from streamcat.store.finder import UserFinder, RoleFinder
                role = RoleFinder(self).find_by_id(obj.role_id)
                user = UserFinder(self).find_by_id(obj.user_id)
                raise NotAuthorizedException(f'{self.user}はロール({role})にユーザー({user})を追加できませんでした')
            self._session.add(obj)
            self.flush(obj)

        elif isinstance(obj, Role):
            # ロールの新規作成は誰でもできる
            self._session.add(obj)
            self.flush(obj)

            # # 新規追加したロールをDBに反映する
            # self._session.flush([obj])
            # self._session.expire(obj)

            # # ロールを新規作成したユーザには無条件にロールの所有権を付与する
            # from .user_role import UserRole
            # user_role = UserRole(self, obj.creator.id, obj.id, owner=True)
            # self._session.add(user_role)

        elif isinstance(obj, Auth):
            # ユーザ管理者かデータの所有者のみ、その権限を追加できる
            if not self.ownership(obj.datum_id) and not self.has_usr_admin():
                datum = self._session.get(SavableDatum, obj.datum_id)
                raise NotAuthorizedException(f'{self.user}は{datum.label}に{obj.operation}権限を追加できませんでした')
            self._session.add(obj)
            self.flush(obj)

        else:
            if not self.has_sys_admin():
                # 上記以外の書き込みはシステム管理者権限が必要
                raise NotAuthorizedException('no anthz!', str(obj))       
            self._session.add(obj)
            self.flush(obj)

    def update(self, obj, ignore_authz=False):
        from streamcat.core import SavableDatum
        from .auth import Auth
        from .user_role import UserRole
        from .role import Role
        from .user import User

        try:
            if isinstance(obj, SavableDatum):
                # Datumの変更権限を判定する
                if not ignore_authz and not self.writable(obj):
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

                # ユーザ管理者かロールの所有者のみ、ロールの所有権を変更できる
                if not self.is_role_owner(obj.role_id) and not self.has_usr_admin():
                    from streamcat.store.finder import UserFinder, RoleFinder
                    role = RoleFinder(self).find_by_id(obj.role_id)
                    user = UserFinder(self).find_by_id(obj.user_id)
                    raise NotAuthorizedException(f'{self.user}はロール({role})についてユーザ({user})の所有権を変更できませんでした')

            elif isinstance(obj, Role):
                # ユーザ管理者かロールの所有者のみ、ロールを変更できる
                if not self.is_role_owner(obj.id) and not self.has_usr_admin():
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

        finally:
            # Sessionにあるobjを期限切れ状態にすることで、objの参照時にDBからリロードされるようにする
            self.expire(obj)

    def delete(self, obj):
        from streamcat.core import SavableDatum
        from .auth import Auth
        from .user_role import UserRole
        from .role import Role
        from .user import User

        if isinstance(obj, SavableDatum):
            if self.writable(obj):
                # 削除データの権限を全て削除する
                from streamcat.store.finder import AuthFinder
                AuthFinder(self).delete_all_by_datum_id(obj.id)
            else:
                raise NotAuthorizedException((f'{self.user.name}は更新権限がないため{obj.label}を削除できません'))

        elif isinstance(obj, User):
            # ユーザ管理者のみ、ユーザを削除できる
            if not self.has_usr_admin():
                raise NotAuthorizedException('ユーザを削除できませんでした')

        elif isinstance(obj, UserRole):
            # ユーザ管理者かロールの所有者のみ、ロールからユーザを削除できる
            if not self.is_role_owner(obj.role_id) and not self.has_usr_admin():
                raise NotAuthorizedException('ロールからユーザを削除できませんでした')

        elif isinstance(obj, Role):
            # ユーザ管理者かロールの所有者のみ、ロールを削除できる
            if not self.is_role_owner(obj.id) and not self.has_usr_admin():
                raise NotAuthorizedException(f'{self.user}はロール({obj})を削除できませんでした')

        elif isinstance(obj, Auth):
            # ユーザ管理者かデータの所有者のみ、その権限を削除できる
            if not self.ownership(obj.datum_id) and not self.has_usr_admin():
                raise NotAuthorizedException('権限を削除できませんでした')

        elif not self.has_sys_admin():
            # 上記以外の書き込みはシステム管理者権限が必要
            raise NotAuthorizedException('no anthz!')   

        # 削除する
        self._session.delete(obj)
        # 削除したobjをDBに反映する
        self.flush(obj)

    def readable(self, datum) -> bool:
        """
        UserによるDatumの参照権限の有無を判定する
        """
        from streamcat.core import SavableDatum

        if datum.id is None:
            # save()してないDatumの参照権限はFalseとする
            return False
        else:
            datum_id = datum.id

        select_permissions = self._make_select_permissions_inner(datum_id)
        permissons = self._session.scalars(select_permissions).one()
        
        return (permissons & SavableDatum.PERMISSION_READ) > 0

    def writable(self, datum, ignore_self_edit_lock=False) -> bool:
        """
        UserによるDatumの更新権限の有無を判定する
        """
        from streamcat.core import SavableDatum

        if datum.id is None:
            # Datumの新規追加の場合(datum.id=None)は親フォルダのoperation権限だけを判定する
            datum_id = datum.parent_id
        else:
            datum_id = datum.id

        select_permissions = self._make_select_permissions_inner(datum_id)
        permissons = self._session.scalars(select_permissions).one()

        if ignore_self_edit_lock:
            # 更新権限の判定に編集ロックの値を含めいない場合
           return (permissons & SavableDatum.PERMISSION_WRITER) > 0
        else:
            # 更新権限の判定に編集ロックの値も含める場合
            return (permissons & SavableDatum.PERMISSION_WRITE) > 0

    def executable(self, datum) -> bool:
        """
        UserによるDatumの実行権限の有無を判定する
        """
        from streamcat.core import SavableDatum

        if datum.id is None:
            # save()してないFlowの場合(datum.id=None)は親フォルダのoperation権限だけを判定する
            datum_id = datum.parent_id
        else:
            datum_id = datum.id

        select_permissions = self._make_select_permissions_inner(datum_id)
        permissons = self._session.scalars(select_permissions).one()
        return (permissons & SavableDatum.PERMISSION_EXEC) > 0

    def ownership(self, datum_id) -> bool:
        """
        UserによるDatumの所有権の有無を判定する
        """
        # from streamcat.core import Datum
        # from .auth import Auth
        # # ここでfind_by_id・find_by_uuidを使うとdatum.readableがFalseに何故かなってしまう
        # # query(Datum).get()を使うとdatum.readableがNoneに何故かなってしまう
        # result = self._session.query(Datum.id, Datum.parent_id).where(Datum.id==datum_id).one_or_none()
        # if result is None:
        #     raise Exception('datum is None')
        # 
        # return self._operatable(result, Auth.OWN_OP)

        select_stmt = self._make_select_ownership(datum_id)
        return self._session.scalars(select_stmt).one_or_none() == True

    def has_sys_admin(self) -> bool:
        from sqlalchemy import select, func
        from sqlalchemy.sql.expression import literal
        from .user_role import UserRole
        from .role import Role

        stmt =  select(func.count(Role.id)).\
                outerjoin(UserRole, UserRole.role_id==Role.id).\
                where(Role.uuid == literal(Role.SYS_ADMIN_ROLE_UUID)).\
                where(UserRole.user_id==self.user.id)
        return self._session.scalars(stmt).one() > 0

    def has_usr_admin(self) -> bool:
        from sqlalchemy import select, func
        from sqlalchemy.sql.expression import literal
        from .user_role import UserRole
        from .role import Role

        stmt =  select(func.count(Role.id)).\
                outerjoin(UserRole, UserRole.role_id==Role.id).\
                where(Role.uuid == literal(Role.USR_ADMIN_ROLE_UUID)).\
                where(UserRole.user_id==self.user.id)
        return self._session.scalars(stmt).one() > 0

    def is_role_creator(self, role_id) -> bool:
        """
        操作ユーザがRoleの作成者であればTrueを返す
        """
        from sqlalchemy import select, func
        from .role import Role
        stmt =  select(func.count(Role.id)).\
                where(Role.id==role_id).where(Role._creator_id==self.user.id)
        return self._session.scalars(stmt).one() > 0

    def is_role_owner(self, role_id) -> bool:
        """
        操作ユーザがRoleの所有者であればTrueを返す
        """
        from sqlalchemy import select, func
        from .role import UserRole
        stmt =  select(func.count(UserRole.user_id)).\
                where(UserRole.role_id==role_id).\
                where(UserRole.user_id==self.user.id).\
                where(UserRole.owner==True)
        return self._session.scalars(stmt).one() > 0

    def is_self_user(self, user_id) -> bool:
        """
        操作ユーザがUserの本人であればTrueを返す
        """
        return user_id == self.user.id

    def is_datum_creator(self, datum_id) -> bool:
        """
        操作ユーザがDatumの作成者であればTrueを返す
        """
        from sqlalchemy import select, func
        from streamcat.core import SavableDatum
        stmt =  select(func.count(SavableDatum.id)).\
                where(SavableDatum.id==datum_id).where(SavableDatum._creator_id==self.user.id)
        return self._session.scalars(stmt).one() > 0
