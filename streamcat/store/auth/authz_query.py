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
        from streamcat.core import SCatBaseModel
        return obj is not None and isinstance(obj, SCatBaseModel)

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

    def offset(self, offset:int):
        return self._create_query(self._query.offset(offset), self._session)

    def limit(self, limit:int):
        return self._create_query(self._query.limit(limit), self._session)

    def delete(self, synchronize_session='evaluate'):
        # synchronize_session='fetch'でSQLを2回発行するらしい
        result = self._query.delete(synchronize_session)
        return result

class AuthzDatumQuery(Query):

    def _create_query(self, query, session):
        return AuthzDatumQuery(query, session)

    # def get(self, ident):
    #     from streamcat.core import Datum
    #     result = self._query.get(ident)
    #     if Query._is_base_model(result):
    #         result._session = self._session
    #         # 参照権限のないDatumの場合はNoneを返す
    #         if isinstance(result, Datum) and not result.readable:
    #             return None
    #     return result

    def one(self):
        from streamcat.core import SavableDatum
        result = self._query.one()
        if Query._is_base_model(result):
            result._session = self._session
            # 参照権限のないDatumの場合は例外を送出する
            isinstance(result, SavableDatum) and result._readable_or_raise()
        return result

    def one_or_none(self):
        from streamcat.core import SavableDatum
        result = self._query.one_or_none()
        if Query._is_base_model(result):
            result._session = self._session
            # 参照権限のないDatumの場合はNoneを返す
            if isinstance(result, SavableDatum) and not result.readable:
                return None
        return result

    def all(self, ignore_authz=False):
        from streamcat.core import SavableDatum
        results = self._query.all()
        if results is not None and len(results) > 0 and Query._is_base_model(results[0]):
            rets = []
            for result in results:
                # 参照権限のないDatumは返さない
                if not ignore_authz and isinstance(result, SavableDatum) and not result.readable:
                    continue
                result._session = self._session
                rets.append(result)
            return rets
        return results

    def filter(self, *criterion):
        return AuthzDatumQuery(self._query.filter(*criterion), self._session)
