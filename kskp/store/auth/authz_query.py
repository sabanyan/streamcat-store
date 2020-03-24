from .exceptions import NotAuthorizedException

class AuthzQuery():

    _query = None

    def __init__(self, query, user_id):
        if user_id is None:
            raise Exception('AuthzSessionに設定したuser_idがNoneです')
        self._query = query
        self.user_id = user_id

    def filter(self, *criterion):
        return AuthzQuery(self._query.filter(*criterion), self.user_id)

    def count(self):
        return self._query.count()

    def all(self):
        return self._query.all()

    def exists(self):
        return self._query.exists()

    def order_by(self, *criterion):
        return self._query.order_by(*criterion)

    def one_or_none(self):
        return self._query.one_or_none()

    def update(self, values, update_args=None):
        # 権限がない場合はUPDATEのWHEREはFalseとなる
        exists_stmt = self._get_authz_exists_stmt()
        
        # synchronize_session='fetch'でSQLを2回発行するらしい
        result = self._query.filter(exists_stmt).\
                             update(values, synchronize_session=False, update_args=update_args)

        # 権限がない(更新件数=0件)場合は例外を送出する
        if result == 0:
            raise  NotAuthorizedException((f'{self.user_id}は更新権限がありません'))

        return result

    def _get_authz_exists_stmt(self):
        """
        Dataテーブルと相関し、Datumにwrite権限があることを抽出条件とするExists句を返す
        """
        from sqlalchemy import func, text, column, select, exists, table

        # 権限がない場合はUPDATEのWHEREはFalseとなる
        ta = table('auths').\
             join(table('groups'), text('auths.group_id=groups.id')).\
             join(table('users_groups'), text(f'groups.id=users_groups.group_id and users_groups.user_id={self.user_id}'))
        
        tb = select([text('bool_and(auths.write) AS write')]).select_from(ta).where(text('auths.datum_id=data.id')).alias('V')

        stmt = exists(select([1]).select_from(tb).where(text('write=True')))
        
        return stmt
