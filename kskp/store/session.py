import os
from sqlalchemy import create_engine

class Session():
    """
    SQLAlchemyのSessionを保持する(とりあえずこの目的ね)
    """

    # データベースへの接続
    # echo=TrueでSQLログがコンソールに出力される
    _engine = create_engine(os.environ['SQLALCHEMY_DATABASE_URI'], echo=False)

    def __init__(self, user=None):
        from sqlalchemy.orm import sessionmaker
        from kskp.store.auth.authz_session import AuthzSession

        # セッションをつくる
        # session.commit()によるExpireでquery_expression()で設定されているreadableがNoneになる
        # これを回避するためexpire_on_commit=Falseとする、autoflush=Falseも必要!
        session_maker = sessionmaker(bind=Session._engine, expire_on_commit=False, autoflush=False)

        # セッションを保持する
        self._session = AuthzSession(session_maker, user)

        self._data = DatumFactory(self._session)
        self._store = StoreFactory(self._session)
        self._user = UserFactory(self._session)

    def __enter__(self):
        return self

    def __exit__(self, ex_type, ex_value, trace):
        self.close()

    def close(self):
        self._session.close()

    @property
    def data(self):
        return self._data

    @property
    def store(self):
        return self._store

    @property
    def user(self):
        return self._user


class UnAuthzSessoin():
    
    def __init__(self):
        from sqlalchemy.orm import sessionmaker
        session_maker = sessionmaker(Session._engine)
        self._session = session_maker()

    def create_admin_user(self):
        from kskp.store.auth import User
        return User(self._session, 'admin@kskp.io', 'adminpass', '管理者')

    def find_user_by_email(self, email):
        user = UserFactory(self._session).find_by_email(email)
        user.session = self._session
        return user

    def find_user_by_id(self, user_id):
        user = UserFactory(self._session).find_by_id(user_id)
        user.session = self._session
        return user

    def load_admin_group(self):
        group = GroupFactory(self._session).load_admin_group()
        group.session = self._session
        return group

    def __enter__(self):
        return self

    def __exit__(self, ex_type, ex_value, trace):
        self.close()

    def close(self):
        self._session.close()


class DatumFactory():
    # Factoryのような役割になってきたのでDatumFactoryに名前を変えたい

    def __init__(self, session):
        self._session = session
    
    def create_folder(self, parent_uuid, label, creator=None):
        from kskp.store import Folder
        return Folder(self._session, parent_uuid, label, creator)

    def create_frame(self, parent_uuid, label, stream, creator=None):
        from kskp.store import Frame
        return Frame(self._session, parent_uuid, label, stream, creator)

    def create_datasource(self, parent_uuid, label, store, loader_step, creator=None):
        from kskp.store import DataSource
        return DataSource(self._session, parent_uuid, label, store, loader_step, creator)

    def create_simple_flow(self, parent_uuid, label, data_source, creator=None):
        from kskp.store import Flow
        flow_data = {
                        "label": label,
                        "nodes": [
                            {
                                "id": "d",
                                "type": "frame",
                                "uuid": data_source.uuid,
                                "error": {},
                                "label": data_source.label,
                                "invalid": {},
                                "makeCache": False,
                                "dataSource": "csv",
                                "cacheCreatedAt": None
                            }
                        ],
                        "ports": [[],[]],
                        "params": [],
                        "creator": "",
                        "createdAt": data_source.created_at_str,
                        "projectId": None,
                        "description": ""
                    }
        return Flow(self._session, parent_uuid, label, flow_data, creator)

    def find_by_uuid(self, uuid, type=None):
        """
        指定されたuuidを持つDatumを取得する
        """
        from kskp.store import Datum
        query = self._session.query(Datum).filter(Datum.uuid==uuid)

        if type is not None:
            query.filter(Datum.type==type)

        # 結果が1件以外の場合はNoResultFoundが送出される
        datum = query.one()
        datum.session = self._session

        return datum

    def find_root(self):
        """
        親を持たないfolderレコードを全て取得する
        """
        from kskp.store import Datum
        roots = self._session.query(Datum).filter(Datum.parent_id == None).all()

        if len(roots) == 0 :
            # ルートフォルダがない場合はNoneを返す
            return None
        elif len(roots) > 1:
            raise Exception('More than 2 roots exist!!')

        roots[0].session = self._session
        
        return roots[0]

    def find_all_subflows(self, no_inputs=True, no_outputs=True):
        """
        サブフローを取得する
        no_inputs  =False : 入力ポートのないサブフローは取得しない
        no_outputs =False : 出力ポートのないサブフローは取得しない
        """
        from kskp.store import Datum
        # FIXIT : PostgreSQLのJSONB演算子を用いればSQLのみでサブフローを抽出できるはず
        flows = self._session.query(Datum).filter(Datum.type==Datum.FLOW_TYPE).all()

        subflows = []
        for flow in flows:
            
            # 参照権限のないフローはサブフローか否かの判定ができない
            if not flow.readable:
                continue

            flow_data = flow.data['flow']
            # onの時にno_inputs（＝inputsがない）のサブフローは出さない
            if no_inputs:
                if len(flow_data['ports'][0]) == 0:
                    continue

            # onの時にno_outputs（＝outputsがない）のサブフローは出さない
            if no_outputs:
                if len(flow_data['ports'][1]) == 0:
                    continue

            if len(flow_data['ports'][0]) > 0 or len(flow_data['ports'][1]) > 0:
                flow.session = self._session
                subflows.append(flow)

        return subflows

    def get_flows_referencing_frame(self, frame_uuid):
        """
        参照する入力frameとキャッシュframeを全て取得する
        """
        from sqlalchemy import select, text
        from sqlalchemy.sql import alias
        from kskp.store import Flow

        sql = Flow._get_select_stmt_for_nodes()
        sql = select(['*']).select_from(sql.alias('F')).where(text(f"uuid='{frame_uuid}'"))

        results = self._session.execute(sql)
        return [str(result['label']) for result in results]

    def exists(self, uuid, type=None):
        """
        指定されたuuidを持つDatumが存在する場合はTrueを返す
        """
        from kskp.store import Datum
        # UUID値の形式チェックをする
        if not Datum.is_valid_uuid(uuid):
            return False

        query = self._session.query(Datum).filter(Datum.uuid==uuid)

        if type is not None:
            query.filter(Datum.type==type)

        return query.count() > 0


class StoreFactory():

    def __init__(self, session):
        self._session = session

    def create(self, id, version=None, label=None, description=None, url=None, params=None, creator=None):
        from kskp.store import StoreModel as Store
        data = {'version'    : version,
                'label'      : label,
                'description': description,
                'url'        : url,
                'params'     : params}
        store = Store(id, data, creator)
        store.session = self._session
        return store

    def find_all(self):
        from kskp.store import StoreModel as Store
        return self._session.query(Store).all()

    def find_by_id(self, id):
        from kskp.store import StoreModel as Store
        result = self._session.query(Store).filter(Store.id==id).one_or_none()
        if result is None:
            raise Exception('No store is found by designated store id')
        return result

class AuthFactory():
    def __init__(self, session):
        self._session = session

    def create(self, group_id, datum_id, read=None, write=None, exec=None, creator=None):
        from kskp.store.auth import Auth
        return Auth(self._session, group_id, datum_id, read=read, write=write, exec=exec, creator=creator)

    def find_by_id(self, group_id, datum_id):
        from kskp.store.auth import Auth
        # SQLAlchemyのidentity mapにキャッシュされていればそれを返す
        authz = self._session.query(Auth).get((group_id, datum_id))
        return authz

    def exists(self, group_id, datum_id):
        from kskp.store.auth import Auth
        count = self._session.query(Auth).filter(Auth.group_id==group_id)\
                                   .filter(Auth.datum_id==datum_id).count()
        return count > 0

from kskp.store.auth import Group

class GroupFactory():
    def __init__(self, session):
        self._session = session

    def create(self, name, creator=None):
        from kskp.store.auth import Group
        return Group(self._session, name, creator)

    def find_by_id(self, group_id):
        return self._session.query(Group).filter(Group.id == group_id).one()

    def find_by_uuid(self, uuid):
        return self._session.query(Group).filter(Group.uuid == uuid).one()

    def find_all(self):
        """
        全件取得する
        """
        return self._session.query(Group).all()

    def load_admin_group(self):
        if self.exists(Group.ADMIN_GROUP_UUID):
            admin_group = self.find_by_uuid(Group.ADMIN_GROUP_UUID)
        else:
            admin_group = Group(self._session, Group.ADMIN_GROUP_LABEL)
            # コンストラクタで付番したUUIDを捨てて、特定用途のUUIDを格納する
            admin_group.uuid = Group.ADMIN_GROUP_UUID
            admin_group.save()
        return admin_group

    def load_everyone_group(self):
        if self.exists(Group.EVERYONE_GROUP_UUID):
            everyone_group = self.find_by_uuid(Group.EVERYONE_GROUP_UUID)
        else:
            everyone_group = Group(self._session, Group.EVERYONE_GROUP_LABEL)
            # コンストラクタで付番したUUIDを捨てて、特定用途のUUIDを格納する
            everyone_group.uuid = Group.EVERYONE_GROUP_UUID
            everyone_group.save()

        return everyone_group

    def exists(self, uuid):
        count = self._session.query(Group).filter(Group.uuid==uuid).count()
        return count > 0

from kskp.store.auth import UserGroup

class UserGroupFactory():
    def __init__(self, session):
        self._session = session

    def find_by_id(self, user_id, group_id):
        return self._session.query(UserGroup).\
                       filter(UserGroup.user_id==user_id).\
                       filter(UserGroup.group_id==group_id).\
                       one_or_none()

    def delete_all_by_user_id(self, user_id):
        """
        UsersGroupsテーブルから指定したユーザの所属情報を全て削除する
        """
        self._session.query(UserGroup).filter(UserGroup.user_id==user_id).delete()
        self._session.commit()


from kskp.store.auth import User

class UserFactory():
    def __init__(self, session):
        self._session = session

    def find_by_id(self, user_id):
        # SQLAlchemyのidentity mapにキャッシュされていればそれを返す
        user = self._session.query(User).get(user_id)
        return user

    def find_by_uuid(self, uuid):
        user = self._session.query(User).filter(User.uuid==uuid).one_or_none()
        return user

    def find_by_email(self, email):
        """
        指定されたuuidを持つFrameを取得する
        """
        user = self._session.query(User).filter(User.email==email).one_or_none()
        return user

    def exists(self, uuid):
        count = self._session.query(User).filter(User.uuid==uuid).count()
        return count > 0
