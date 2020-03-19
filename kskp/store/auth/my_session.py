class MySession():

    _session = None

    def __init__(self, session, user_id=None):
        self._session = session
        self.user_id = user_id

    def commit(self):
        """
        COMMIT前に権限を判定し、権限がなかったらrollbackして例外を送出する
        """
        self._session.commit()

    def rollback(self):
        self._session.rollback()

    def query(self, datum_type, *args):
        """
        参照用途でquery()を使用する場合は、AuthsテーブルとJOINする

        pathとdataプロパティは参照された時に権限を判定し、NGなら例外を送出する
        """
        from sqlalchemy import and_
        from sqlalchemy.orm import with_expression
        # from kskp.store import ss as session
        from .user_group import UserGroup


        from kskp.core import Datum
        from .auth import Auth
        import inspect

        if inspect.isclass(datum_type) and datum_type.__tablename__ == 'data':

            print('Session:', self.user_id)

            group_id = self._session.query(UserGroup.group_id).filter(UserGroup.user_id==self.user_id).one_or_none()
            return self._session.query(datum_type).\
                   options(with_expression(Datum.readable, Auth.read)).\
                   outerjoin(Auth, and_(Datum.id==Auth.data_id, Auth.group_id==group_id))
        else:
            return self._session.query(datum_type, *args)

    def w_query(self, uuid):
        """
        更新用途でquery()を使用する場合は、この関数内で権限判定を行う

        仮にこの関数で抽出操作を行っても、Datum.authプロパティが空なので取得はできない
        """
        if not self.writable(self.user_id, uuid):
            raise Exception('no anthz!')

        from kskp.core import Datum
        return self._session.query(Datum)
    
    def add(self, obj):
        from kskp.core import Datum
        if isinstance(obj, Datum):
            if not self.writable(self.user_id, obj.uuid):
                raise Exception('no anthz!')
        else:
            if not self.has_admin():
                raise Exception('no anthz!')

        self._session.add(obj)

    def update(self, uuid, label, data):
        if not self.writable(self.user_id, uuid):
            raise Exception('no anthz!')

        from kskp.core import Datum
        self._session.query(Datum).filter(Datum.uuid==uuid).update({'_label'  : label,
                                                              'data'    : data,
                                                              'modifier': self.user_id})

    def delete(self, id):
        if not self.writable(self.user_id, id):
            raise Exception('no anthz!')

        from kskp.core import Datum
        self._session.query(Datum).filter(Datum.id==id)\
                            .filter(Datum.type==Datum.FRAME_TYPE).delete()

    def execute(self, sql):
        return self._session.execute(sql)

    def writable(self, user_id, uuid):
        """
        ユーザIDとDatumについて書き込み権限の有無を判定する
        """
        return True

    def has_admin(self):
        return True