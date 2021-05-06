from .exceptions import NotAuthorizedException

class Query():

    def __init__(self, query, session):
        self._query = query
        self._session = session
        self._user = session.user

    def __str__(self):
        # パラメタに値をバインドした後のSQL文を返す
        return str(self._query.statement.compile(compile_kwargs={"literal_binds": True}))

    @staticmethod
    def _is_base_model(obj):
        from kskp.core import KSKPBaseModel
        return obj is not None and isinstance(obj, KSKPBaseModel)

    # @staticmethod
    # def _is_base_model(obj):
    #     from sqlalchemy.orm.base import object_mapper
    #     from sqlalchemy.orm.exc import UnmappedInstanceError
    #     try:
    #         object_mapper(obj)
    #     except UnmappedInstanceError:
    #         return False
    #     return True

    def _create_query(self, query, session):
        return Query(query, session)

    # def get(self, ident):
    #     result = self._query.get(ident)
    #     if Query._is_base_model(result):
    #         result._session = self._session
    #     return result

    def one(self):
        result = self._query.one()
        if Query._is_base_model(result):
            result._session = self._session
        return result

    def one_or_none(self):
        result = self._query.one_or_none()
        if Query._is_base_model(result):
            result._session = self._session
        return result

    def first(self):
        result = self._query.first()
        if Query._is_base_model(result):
            result._session = self._session
        return result

    def all(self):
        results = self._query.all()
        if results is not None and len(results) > 0 and Query._is_base_model(results[0]):
            for result in results:
                result._session = self._session
        return results

    def count(self) -> int:
        return self._query.count()

    def filter(self, *criterion):
        return self._create_query(self._query.filter(*criterion), self._session)

    def select_from(self, *from_obj):
        return self._create_query(self._query.select_from(*from_obj), self._session)

    def join(self, *props, **kwargs):
        return self._create_query(self._query.join(*props, **kwargs), self._session)

    def outerjoin(self, *props, **kwargs):
        return self._create_query(self._query.outerjoin(*props, **kwargs), self._session)

    def exists(self):
        return self._query.exists()

    def group_by(self, *criterion):
        return self._create_query(self._query.group_by(*criterion), self._session)

    def order_by(self, *criterion):
        return self._create_query(self._query.order_by(*criterion), self._session)

    def update(self, values, update_args=None):
        # synchronize_session='fetch'でSQLを2回発行するらしい
        result = self._query.update(values, update_args=update_args)
        return result

    def delete(self, synchronize_session='evaluate'):
        result = self._query.delete(synchronize_session)
        return result

class AuthzDatumQuery(Query):

    def _create_query(self, query, session):
        return AuthzDatumQuery(query, session)

    # def get(self, ident):
    #     from kskp.core import Datum
    #     result = self._query.get(ident)
    #     if Query._is_base_model(result):
    #         result._session = self._session
    #         # 参照権限のないDatumの場合はNoneを返す
    #         if isinstance(result, Datum) and not result.readable:
    #             return None
    #     return result

    def one(self):
        from kskp.core import Datum
        result = self._query.one()
        if Query._is_base_model(result):
            result._session = self._session
            # 参照権限のないDatumの場合は例外を送出する
            isinstance(result, Datum) and result._readable_or_raise()
        return result

    def one_or_none(self):
        from kskp.core import Datum
        result = self._query.one_or_none()
        if Query._is_base_model(result):
            result._session = self._session
            # 参照権限のないDatumの場合はNoneを返す
            if isinstance(result, Datum) and not result.readable:
                return None
        return result

    def all(self, ignore_authz=False):
        from kskp.core import Datum
        results = self._query.all()
        if results is not None and len(results) > 0 and Query._is_base_model(results[0]):
            rets = []
            for result in results:
                # 参照権限のないDatumは返さない
                if not ignore_authz and isinstance(result, Datum) and not result.readable:
                    continue
                result._session = self._session
                rets.append(result)
            return rets
        return results

    def filter(self, *criterion):
        return AuthzDatumQuery(self._query.filter(*criterion), self._session)

    def update(self, values, update_args=None):
        """
        実は今は使っていないようだ
        一括更新に使うかもしれない
        """

        # 権限がない場合はUPDATEのWHEREはFalseとなる
        exists_stmt = self._get_authz_exists_stmt()
        
        # synchronize_session='fetch'でSQLを2回発行するらしい
        result = self._query.filter(exists_stmt).\
                             update(values, synchronize_session='fetch', update_args=update_args)

        # 権限がない(更新件数=0件)場合は例外を送出する
        if result == 0:
            raise  NotAuthorizedException((f'{self._user.name}は更新権限がありません'))

        return result

    def _get_authz_exists_stmt(self):
        """
        Dataテーブルと相関し、Datumにwrite権限があることを抽出条件とするExists句を返す
        """
        from sqlalchemy import func, text, column, select, exists, table
        from .auth import Auth

        # 権限がない場合はUPDATEのWHEREはFalseとなる
        ta = table('auths').\
             join(table('roles'), text('auths.role_id=roles.id')).\
             join(table('users_roles'), text(f'roles.id=users_roles.role_id and users_roles.user_id={self._user.id}'))
        
        tb = select([text('bool_and(auths.permission) AS write')]).select_from(ta).\
             where(text(f"auths.datum_id=data.id AND auths.operation='{Auth.WRITE_OP}' ")).alias('V')

        stmt = exists(select([1]).select_from(tb).where(text('write=True')))
        
        return stmt