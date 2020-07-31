from typing import Union
from kskp.core import Datum
from kskp.store.folder import Folder
from kskp.store.trashcan import TrashCan

class Factory():
    """
    SQLAlchemyのSessionを保持する(とりあえずこの目的ね)
    """
    def __init__(self, user=None):
        from sqlalchemy.orm import sessionmaker
        from kskp.store import engine
        from kskp.store.auth.authz_session import AuthzSession

        # セッションをつくる
        # session.commit()によるExpireでquery_expression()で設定されているreadableがNoneになる
        # これを回避するためexpire_on_commit=Falseとする、autoflush=Falseも必要!
        session_maker = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)

        # セッションを保持する
        self._session = AuthzSession(session_maker, user)

        self._data = DatumFactory(self._session)
        self._store = StoreFactory(self._session)
        self._auth = AuthFactory(self._session)
        self._role = RoleFactory(self._session)
        self._user_role = UserRoleFactory(self._session)
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
    def auth(self):
        return self._auth

    @property
    def role(self):
        return self._role

    @property
    def user_role(self):
        return self._user_role

    @property
    def user(self):
        return self._user


class UnAuthzFactory():
    
    def __init__(self):
        from sqlalchemy.orm import sessionmaker
        from kskp.store import engine
        from kskp.store.auth.authz_session import Session

        # セッションをつくる
        session_maker = sessionmaker(engine)

        # セッションを保持する
        self._session = Session(session_maker, user=None)

    def create_admin_user(self):
        from kskp.store.auth import User
        # FIXIT:管理者パスワードはどうする？
        return User(self._session, 'admin@kskp.io', 'adminpass', '管理者')

    def find_user_by_email(self, email):
        user = UserFactory(self._session).find_by_email(email)
        # if user is not None:
        #     user.session = self._session
        return user

    def find_user_by_id(self, user_id):
        user = UserFactory(self._session).find_by_id(user_id)
        # if user is not None:
        #     user.session = self._session
        return user

    def load_admin_role(self):
        role = RoleFactory(self._session).load_admin_role()
        # if role is not None:
        #     role.session = self._session
        return role

    def __enter__(self):
        return self

    def __exit__(self, ex_type, ex_value, trace):
        self.close()

    def close(self):
        self._session.close()


class DatumFactory():

    def __init__(self, session):
        self._session = session

    def create_root(self, label):
        from kskp.store import Folder
        return Folder(self._session, None, label)

    def create_datasource(self, parent, label, store, loader_step):
        from kskp.store import DataSource
        return DataSource(self._session, parent, label, store, loader_step)

    def find_by_id(self, id, type=None) -> Datum:
        """
        指定されたidを持つDatumを取得する
        """
        from kskp.store import NoResultFound
        from kskp.core import Datum
        query = self._session.query(Datum).filter(Datum.id==id)

        if type is not None:
            query = query.filter(Datum.type==type)

        # 結果が1件以外の場合はNoResultFoundが送出される
        try:
            datum = query.one()
        except NoResultFound:
            raise Exception(f'指定したDatum({id})は存在しませんでした')
        # datum.session = self._session

        return datum

    def find_by_uuid(self, uuid, type=None) -> Datum:
        """
        指定されたuuidを持つDatumを取得する
        """
        # UUID値の形式チェックをする
        from kskp.core import Datum
        from kskp.store import NoResultFound
        Datum.valid_uuid_or_raise(uuid)

        from kskp.store import Datum
        query = self._session.query(Datum).filter(Datum.uuid==uuid)

        if type is not None:
            query = query.filter(Datum.type==type)

        # 結果が1件以外の場合はNoResultFoundが送出される
        try:
            datum = query.one()
        except NoResultFound:
            raise Exception(f'指定したDatum({uuid})は存在しませんでした')
        # datum.session = self._session

        return datum

    def count_root(self) -> int:
        from kskp.store import Datum
        return self._session.query(Datum).filter(Datum.parent_id == None).count()

    def find_root(self) -> Union[Folder, None]:
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

        # roots[0].session = self._session
        
        return roots[0]

    def find_trashcan(self) -> TrashCan:
        """
        ゴミ箱を取得する
        """
        from kskp.store import Datum
        trashcan = self._session.query(Datum).filter(Datum.type==Datum.TRASH_TYPE).one_or_none()
        if trashcan is None:
            raise Exception('no trush can is found by designated id.')
        return trashcan

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

            flow_data = flow.flow_data
            # onの時にno_inputs（＝inputsがない）のサブフローは出さない
            if no_inputs:
                if len(flow_data.ports[0]) == 0:
                    continue

            # onの時にno_outputs（＝outputsがない）のサブフローは出さない
            if no_outputs:
                if len(flow_data.ports[1]) == 0:
                    continue

            if len(flow_data.ports[0]) > 0 or len(flow_data.ports[1]) > 0:
                # flow.session = self._session
                subflows.append(flow)

        return subflows

    def load_root(self):
        """
        ルートデータストアを取得する、存在しない場合は作成する
        """
        root = self.find_root()
        # ルートフォルダが存在しない場合はルートフォルダを作成する
        # (最初にライブラリ画面にアクセスする時はルートフォルダ自身も存在しません)
        if root is None:
            new_root = self.create_root(label='ライブラリ')
            # folderレコードをDBに格納する
            new_root.save()

            # 
            # ルートフォルダにAdminロールの権限設定がない場合、初期値を設定する
            # (後方互換)
            # 
            from kskp.store.factory import RoleFactory, AuthFactory
            role_factory = RoleFactory(self._session)
            auth_factory = AuthFactory(self._session)

            admin_role = role_factory.load_admin_role()
            admin_role.join_user(self._session.user)
            if not auth_factory.exists(admin_role.id, new_root.id):
                admin_role.init_authz(new_root.id, True, True, exec=True)

            # 
            # ルートフォルダにEveryOneロールの権限設定がない場合、初期値を設定する
            # (後方互換)
            # 
            everyone_role = role_factory.load_everyone_role()
            everyone_role.join_user(self._session.user)
            if not auth_factory.exists(everyone_role.id, new_root.id):
                everyone_role.init_authz(new_root.id, True, True, exec=True)

            # 参照権限設定後にもう一度取得し直す
            root = self.find_by_uuid(new_root.uuid)
        return root

    def load_result_folder(self):
        """
        実行結果フォルダを取得する、存在しない場合は作成する
        """
        from kskp.core import Datum
        return self._get_or_make_dir_path(Datum.RESULT_FOLDER_UUID, Datum.RESULT_FOLDER_LABEL)

    def load_cache_folder(self):
        """
        キャッシュフォルダを取得する、存在しない場合は作成する
        """
        from kskp.core import Datum
        return self._get_or_make_dir_path(Datum.CACHE_FOLDER_UUID, Datum.CACHE_FOLDER_LABEL)

    def load_flow_folder(self):
        """
        フローフォルダを取得する、存在しない場合は作成する
        """
        from kskp.core import Datum
        return self._get_or_make_dir_path(Datum.FLOW_FOLDER_UUID, Datum.FLOW_FOLDER_LABEL)

    def load_trash_folder(self):
        """
        ゴミ箱フォルダを取得する、存在しない場合は作成する
        """
        from kskp.store import TrashCan
        if self.trashcan_exists():
            return self.find_trashcan()
        else:
            # ゴミ箱が無い場合は作成する
            root = self.load_root()
            trash = root.create_trashcan()
            trash.save()
            return trash.reload()

    def _get_or_make_dir_path(self, uuid, label) -> Folder:
        # 特定用途のフォルダのUUIDは決め打ちである
        if self.exists(uuid):
            return self.find_by_uuid(uuid)
        else:
            # UUID値の形式チェックをする
            from kskp.core import Datum
            Datum.valid_uuid_or_raise(uuid)

            # フォルダが無い場合は作成する
            root = self.load_root()
            folder = root.create_folder(label)
            # Folderのコンストラクタで付番したUUIDを捨てて、特定用途のフォルダのUUIDを格納する
            folder.uuid = uuid
            folder.save()
            return folder.reload()

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

    def exists(self, uuid, type=None) -> bool:
        """
        指定されたuuidを持つDatumが存在する場合はTrueを返す
        """
        from kskp.store import Datum
        # UUID値の形式チェックをする
        if not Datum.is_valid_uuid(uuid):
            return False

        query = self._session.query(Datum).filter(Datum.uuid==uuid)

        if type is not None:
            query = query.filter(Datum.type==type)

        return query.count() > 0

    def exists_by_id(self, id, type=None) -> bool:
        """
        指定されたidを持つDatumが存在する場合はTrueを返す
        """
        from kskp.store import Datum
        query = self._session.query(Datum).filter(Datum.id==id)

        if type is not None:
            query = query.filter(Datum.type==type)

        return query.count() > 0

    def trashcan_exists(self) -> bool:
        """
        ゴミ箱が存在する場合はTrueを返す
        """
        from kskp.store import Datum
        result = self._session.query(Datum).filter(Datum.type==Datum.TRASH_TYPE).count()
        return result > 0

    def trashed(self, uuid):
        """
        ゴミ箱の中にある場合はTrueを返す
        """
        from kskp.store import Datum
        sql = f"""
        WITH RECURSIVE R AS (
            SELECT id, parent_id, uuid, type, path FROM data WHERE uuid = '{uuid}'
            UNION ALL
            SELECT D.id, D.parent_id, D.uuid, D.type, D.path FROM data D JOIN R ON D.id = R.parent_id
        )
        SELECT uuid, path, type FROM R
        WHERE type = '{Datum.TRASH_TYPE}'
        """
        try:
            results = self._session.execute(sql)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            pass

        return len([result for result in results]) > 0

class StoreFactory():

    def __init__(self, session):
        self._session = session

    def create(self, id, version=None, label=None, description=None, url=None, params=None):
        from kskp.store import StoreModel as Store
        data = {'version'    : version,
                'label'      : label,
                'description': description,
                'url'        : url,
                'params'     : params}
        store = Store(id, data, self._session.user)
        store._session = self._session
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

    def create(self, role_id, datum_id, operation, permission):
        from kskp.store.auth import Auth
        return Auth(self._session, role_id, datum_id, operation, permission)

    def find_by_id(self, role_id, datum_id, operation):
        from kskp.store.auth import Auth
        # SQLAlchemyのidentity mapにキャッシュされていればそれを返す
        authz = self._session.query(Auth).get((role_id, datum_id, operation))
        if authz is None:
            raise Exception('No authz is found by designated id')
        return authz

    def exists(self, role_id, datum_id, operation=None) -> bool:
        from kskp.store.auth import Auth
        query = self._session.query(Auth).filter(Auth.role_id==role_id)\
                                         .filter(Auth.datum_id==datum_id)
        if operation is not None:
            query = query.filter(Auth.operation==operation)

        return query.count() > 0

    def delete_all_by_datum_id(self, datum_id):
        """
        Authzテーブルから指定したDatumの権限情報を全て削除する
        """
        from kskp.store.auth import Auth
        try:
            self._session.query(Auth).filter(Auth.datum_id==datum_id).delete()
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()


from kskp.store.auth import Role

class RoleFactory():
    def __init__(self, session):
        self._session = session

    def create(self, name):
        from kskp.store.auth import Role
        return Role(self._session, name)

    def find_by_id(self, role_id) -> Role:
        return self._session.query(Role).filter(Role.id == role_id).one()

    def find_by_uuid(self, uuid) -> Role:
        return self._session.query(Role).filter(Role.uuid == uuid).one()

    def find_all(self):
        """
        全件取得する
        """
        return self._session.query(Role).all()

    def load_admin_role(self):
        if self.exists(Role.ADMIN_ROLE_UUID):
            admin_role = self.find_by_uuid(Role.ADMIN_ROLE_UUID)
        else:
            admin_role = Role(self._session, Role.ADMIN_ROLE_LABEL)
            # コンストラクタで付番したUUIDを捨てて、特定用途のUUIDを格納する
            admin_role.uuid = Role.ADMIN_ROLE_UUID
            admin_role.save()
        return admin_role

    def load_everyone_role(self):
        if self.exists(Role.EVERYONE_ROLE_UUID):
            everyone_role = self.find_by_uuid(Role.EVERYONE_ROLE_UUID)
        else:
            everyone_role = Role(self._session, Role.EVERYONE_ROLE_LABEL)
            # コンストラクタで付番したUUIDを捨てて、特定用途のUUIDを格納する
            everyone_role.uuid = Role.EVERYONE_ROLE_UUID
            everyone_role.save()

        return everyone_role

    def exists(self, uuid) -> bool:
        count = self._session.query(Role).filter(Role.uuid==uuid).count()
        return count > 0

from kskp.store.auth import UserRole

class UserRoleFactory():
    def __init__(self, session):
        self._session = session

    def find_by_id(self, user_id, role_id) -> UserRole:
        return self._session.query(UserRole).\
                       filter(UserRole.user_id==user_id).\
                       filter(UserRole.role_id==role_id).\
                       one()

    def delete_all_by_user_id(self, user_id):
        """
        UsersRolesテーブルから指定したユーザの所属情報を全て削除する
        """
        try:
            self._session.query(UserRole).filter(UserRole.user_id==user_id).delete()
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

from kskp.store.auth import User

class UserFactory():
    def __init__(self, session):
        self._session = session

    def create(self, email, password, name):
        from kskp.store.auth import User
        return User(self._session, email, password, name)

    def find_by_id(self, user_id, allow_no_result=False) -> User:
        # SQLAlchemyのidentity mapにキャッシュされていればそれを返す
        user = self._session.query(User).get(user_id)
        if user is None and not allow_no_result:
            raise Exception(f'No user is found by designated user_id({user_id})')
        return user

    def find_by_uuid(self, uuid) -> User:
        # UUID値の形式チェックをする
        from kskp.core import Datum
        Datum.valid_uuid_or_raise(uuid)

        user = self._session.query(User).filter(User.uuid==uuid).one()
        return user

    def find_by_email(self, email) -> User:
        """
        指定されたuuidを持つFrameを取得する
        """
        user = self._session.query(User).filter(User.email==email).one()
        return user

    def exists(self, uuid) -> bool:
        count = self._session.query(User).filter(User.uuid==uuid).count()
        return count > 0
