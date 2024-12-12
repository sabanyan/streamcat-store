class Result():

    def __init__(self, result, session):
        self._result = result
        self._session = session
        self._user = session.user

    def __str__(self):
        # パラメタに値をバインドした後のSQL文を返す
        return str(self._result.statement.compile(compile_kwargs={"literal_binds": True}))

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

    # def get(self, ident):
    #     result = self._query.get(ident)
    #     if Query._is_base_model(result):
    #         result._session = self._session
    #     return result

    def one(self):
        row = self._result.one()
        if Result._is_base_model(row):
            row._session = self._session
        return row

    def one_or_none(self):
        row = self._result.one_or_none()
        if Result._is_base_model(row):
            row._session = self._session
        return row

    def first(self):
        row = self._result.first()
        if Result._is_base_model(row):
            row._session = self._session
        return row

    def all(self):
        rows = self._result.all()
        if rows is not None and len(rows) > 0 and Result._is_base_model(rows[0]):
            for result in rows:
                result._session = self._session
        return rows

class AuthzDatumResult(Result):
    # def get(self, ident):
    #     from streamcat.core import Datum
    #     result = self._result.get(ident)
    #     if Query._is_base_model(result):
    #         result._session = self._session
    #         # 参照権限のないDatumの場合はNoneを返す
    #         if isinstance(result, Datum) and not result.readable:
    #             return None
    #     return result

    def one(self):
        from streamcat.core import SavableDatum
        row = self._result.one()
        if Result._is_base_model(row):
            row._session = self._session
            # 参照権限のないDatumの場合は例外を送出する
            isinstance(row, SavableDatum) and row._readable_or_raise()
        return row

    def one_or_none(self):
        from streamcat.core import SavableDatum
        row = self._result.one_or_none()
        if Result._is_base_model(row):
            row._session = self._session
            # 参照権限のないDatumの場合はNoneを返す
            if isinstance(row, SavableDatum) and not row.readable:
                return None
        return row

    def all(self, ignore_authz=False):
        from streamcat.core import SavableDatum
        rows = self._result.all()
        if rows is not None and len(rows) > 0 and Result._is_base_model(rows[0]):
            rets = []
            for result in rows:
                # 参照権限のないDatumは返さない
                if not ignore_authz and isinstance(result, SavableDatum) and not result.readable:
                    continue
                result._session = self._session
                rets.append(result)
            return rets
        return rows
