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

        # datum_typeがDatumクラスかDatumを継承するクラスか否かを判定する
        # TODO: もう少し確実な判定方法に変更したい
        if inspect.isclass(datum_type) and hasattr(datum_type, '__tablename__') and datum_type.__tablename__ == 'data':

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
        from sqlalchemy.sql.expression import select, func, literal_column, text, false
        from kskp.core import Datum
        from .auth import Auth
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
                                outerjoin(UserRole, UserRole.role_id==Auth.role_id).\
                                filter(UserRole.user_id==self.user.id).\
                                filter(Auth.datum_id==R.c.id).\
                                filter(Auth.operation==Auth.READ_OP).label('')

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
        from kskp.store import Folder
        from .role import Role

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

            # everyoneロールが無ければ作成し、ユーザをeveryoneロールに所属させる
            from kskp.store.factory import RoleFactory
            everyone_role = RoleFactory(self).load_everyone_role()
            everyone_role.join_user(self.user)
            # everyoneロールへ追加データの権限を付与する
            everyone_role.init_authz(obj.id, True, True)

            # 本人ロールが無ければ作成し、ユーザを本人ロールに所属させる
            self_role = self.user.load_self_role()
            # 本人ロールへ追加データの権限を付与する
            self_role.init_authz(obj.id, True, True)

        else:
            if not self.has_admin():
                # Datum以外の書き込みは管理者権限が必要
                raise NotAuthorizedException('no anthz!')       
            self._session.add(obj)

    def update(self, obj):
        from kskp.core import Datum
        if isinstance(obj, Datum):
            # Datumの変更権限を判定する
            if not self.writable(obj):
                raise NotAuthorizedException((f'{self.user.name}は更新権限がないため{obj.label}を更新できません'))
            if obj._data is not None:
                # JSON列への変更はflag_modified()を使ってSQLAlchemyに知らせないとDBに反映されない
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(obj, "_data")
        elif not self.has_admin():
            # Datum以外の書き込みは管理者権限が必要
            raise NotAuthorizedException('no anthz!')

        # objをSessionに格納する
        self._session.add(obj)
        # SessionにあるobjをDBに格納する
        self.flush(obj)
        # Sessionにあるobjを期限切れ状態にすることで、objの参照時にDBからリロードされるようにする
        self.expire(obj)


    def delete(self, obj):
        from kskp.core import Datum
        if isinstance(obj, Datum):
            if self.writable(obj):
                # 削除データの権限を全て削除する
                from kskp.store.factory import AuthFactory
                AuthFactory(self).delete_all_by_datum_id(obj.id)
            else:
                raise NotAuthorizedException((f'{self.user.name}は更新権限がないため{obj.label}を削除できません'))

        elif not self.has_admin():
            # Datum以外の書き込みは管理者権限が必要
            raise NotAuthorizedException('no anthz!')   

        # 削除する
        self._session.delete(obj)

    def writable(self, datum) -> bool:
        """
        ユーザIDとDatumについて書き込み権限の有無を判定する
        """
        from sqlalchemy import func, false
        from sqlalchemy.orm import aliased
        from .auth import Auth
        from .user_role import UserRole

        A = aliased(Auth, name='A')
        UG = aliased(UserRole, name='UG')

        query = self._session.query(func.coalesce(func.bool_and(A.permission),false()).label("write")).\
                              outerjoin(UG, UG.role_id==A.role_id).\
                              filter(UG.user_id==self.user.id).\
                              filter(A.operation==A.WRITE_OP)

        if datum.parent_id is None:
            # ルートフォルダの場合は親フォルダの権限判定をしない
            query = query.filter(A.datum_id==datum.id)
        elif datum.id is None:
            # Datumの新規追加の場合(datum.id=None)は親フォルダの書き込み権限だけを判定する
            query = query.filter(A.datum_id==datum.parent_id)
        else:
            # 親フォルダとDatumの両方の書き込み権限がある場合にのみ、書き込みOKの判定をする
            A0 = aliased(Auth, name='A0')
            UG0 = aliased(UserRole, name='UG0')

            subquery = self._session.query(func.coalesce(func.bool_and(A0.permission),false()).label('write')).\
                        select_from(UG0).outerjoin(A0, UG0.role_id==A0.role_id).\
                        filter(UG0.user_id==UG.user_id).\
                        filter(A0.operation==A.operation).\
                        filter(A0.datum_id==datum.parent_id).label('')

            query = query.filter(A.datum_id==datum.id).\
                          filter(True == subquery)
                                         
        result = query.one_or_none()

        return result.write == True

    def has_admin(self):
        from .user_role import UserRole
        from .role import Role

        subquery = self._session.query(Role).\
                                 outerjoin(UserRole, UserRole.role_id==Role.id).\
                                 filter(Role.uuid == Role.ADMIN_ROLE_UUID).\
                                 filter(UserRole.user_id==self.user.id)

        ret = self._session.query(subquery.exists())

        return ret