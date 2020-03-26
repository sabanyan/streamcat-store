from .exceptions import NotAuthorizedException

class AuthzQuery():

    _query = None

    def __init__(self, query, user):
        if user is None:
            raise Exception('AuthzSessionに設定したuserがNoneです')
        self._query = query
        self._user = user

    def get(self, ident):
        return self._query.get(ident)

    def filter(self, *criterion):
        return AuthzQuery(self._query.filter(*criterion), self._user)

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

        # 権限がない場合はUPDATEのWHEREはFalseとなる
        ta = table('auths').\
             join(table('groups'), text('auths.group_id=groups.id')).\
             join(table('users_groups'), text(f'groups.id=users_groups.group_id and users_groups.user_id={self._user.id}'))
        
        tb = select([text('bool_and(auths.write) AS write')]).select_from(ta).where(text('auths.datum_id=data.id')).alias('V')

        stmt = exists(select([1]).select_from(tb).where(text('write=True')))
        
        return stmt
