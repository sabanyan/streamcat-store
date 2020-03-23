from .exceptions import NotAuthorizedException

class AuthzQuery():

    _query = None

    def __init__(self, query, user_id=None):
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

    def update(self, values, synchronize_session='evaluate', update_args=None):
        return self._query.update(values, synchronize_session=synchronize_session, update_args=update_args)

    def delete(self, synchronize_session='evaluate'):
        return self._query.delete(synchronize_session=synchronize_session)
