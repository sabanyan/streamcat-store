from typing import Union
from sqlalchemy.orm.exc import NoResultFound
from streamcat.core import Datum, SavableDatum
from streamcat.store import Folder, TrashCan
from streamcat.store.auth import User, Role, UserRole


class UnAuthzFactory():

    def __init__(self):
        from sqlalchemy.orm import sessionmaker
        from streamcat.store.auth.authz_session import Session
        from . import engine

        # セッションをつくる
        # ・future=True : SQLAlchemy2.0スタイルのトランザクションおよびエンジンの動作を使用する
        session_maker = sessionmaker(engine, expire_on_commit=False, autoflush=False, future=True)

        # セッションを保持する
        self._session = Session(session_maker, user=None)

    def find_user_by_email(self, email):
        return UserFactory(self._session).find_by_email(email)

    def find_user_by_uuid(self, user_uuid):
        return UserFactory(self._session).find_by_uuid(user_uuid)

    def load_sys_admin_user(self, activate_if_inactive=False):
        """
        システム管理者を取得する、存在しない場合は作成する
        """
        from streamcat.store.auth import User, Role

        SYS_ADMIN_USER_EMAIL = 'Admin@streamcat.io'
        SYS_ADMIN_USER_NAME = 'システム管理者'

        user_factory = UserFactory(self._session)
        role_factory = RoleFactory(self._session)

        # 管理者ユーザが存在する場合は、それを返す
        if user_factory.exists_by_email(SYS_ADMIN_USER_EMAIL, except_states=[User.INACTIVE_STATE]):
            return user_factory.find_by_email(SYS_ADMIN_USER_EMAIL, except_states=[User.INACTIVE_STATE])

        # 管理者ロールが存在する場合は、そのロールの中でidが最も小さいユーザを取得する
        if role_factory.exists(Role.SYS_ADMIN_ROLE_UUID):
            sys_admin_role = role_factory.find_by_uuid(Role.SYS_ADMIN_ROLE_UUID)
            joined_users = sys_admin_role.get_joined_users(except_states=[User.INACTIVE_STATE])
            if len(joined_users) > 0:
                return joined_users[0]

        # デフォルトの管理者ユーザが論理削除されている場合は、そのまま返すか、登録状態に戻して返す
        if user_factory.exists_by_email(SYS_ADMIN_USER_EMAIL):
            sys_admin_user = user_factory.find_by_email(SYS_ADMIN_USER_EMAIL)
            activate_if_inactive and sys_admin_user.put_back()
            return sys_admin_user

        # 管理者ロールが無い場合は、デフォルトの管理者ユーザを作成する
        sys_admin_user = user_factory.create(SYS_ADMIN_USER_EMAIL, SYS_ADMIN_USER_NAME, 'adminpass0')
        sys_admin_user.save()
        return sys_admin_user

    def load_usr_admin_user(self, activate_if_inactive=False):
        """
        ユーザ管理者を取得する、存在しない場合は作成する
        """
        from streamcat.store.auth import Role

        USR_ADMIN_USER_EMAIL = 'admin@streamcat.io'
        USR_ADMIN_USER_NAME = 'ユーザー管理者'

        user_factory = UserFactory(self._session)
        role_factory = RoleFactory(self._session)

        if user_factory.exists_by_email(USR_ADMIN_USER_EMAIL, except_states=[User.INACTIVE_STATE]):
            return user_factory.find_by_email(USR_ADMIN_USER_EMAIL, except_states=[User.INACTIVE_STATE])

        if role_factory.exists(Role.USR_ADMIN_ROLE_UUID):
            usr_admin_role = role_factory.find_by_uuid(Role.USR_ADMIN_ROLE_UUID)
            joined_users = usr_admin_role.get_joined_users(except_states=[User.INACTIVE_STATE])
            if len(joined_users) > 0:
                return joined_users[0]

        if user_factory.exists_by_email(USR_ADMIN_USER_EMAIL):
            usr_admin_user = user_factory.find_by_email(USR_ADMIN_USER_EMAIL)
            activate_if_inactive and usr_admin_user.put_back()
            return usr_admin_user

        usr_admin_user = user_factory.create(USR_ADMIN_USER_EMAIL, USR_ADMIN_USER_NAME, 'adminpass0')
        usr_admin_user.save()
        return usr_admin_user

    def __enter__(self):
        return self

    def __exit__(self, ex_type, ex_value, trace):
        self.close()

    def close(self):
        self._session.end()
        self._session.close()


class Factory():
    """
    SQLAlchemyのSessionを保持する(とりあえずこの目的ね)
    """
    def __init__(self, user:User=None):
        from sqlalchemy.orm import sessionmaker
        from streamcat.store.auth.authz_session import AuthzSession
        from . import engine

        # セッションを生成する
        # ・session.commit()によるExpireでquery_expression()で設定されているreadableがNoneになる
        # ・これを回避するためexpire_on_commit=Falseとする、autoflush=Falseも必要!
        # ・session.rollback()によるExprireを回避する方法はない
        # ・future=True : SQLAlchemy2.0スタイルのトランザクションおよびエンジンの動作を使用する
        session_maker = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False, future=True)

        # セッションを保持する
        self._session = AuthzSession(session_maker, user)

        self._data = DatumFactory(self._session)
        self._store = StoreFactory(self._session)
        self._auth = AuthFactory(self._session)
        self._role = RoleFactory(self._session)
        self._user_role = UserRoleFactory(self._session)
        self._user = UserFactory(self._session)

        # 生成したセッションからUserオブジェクトを取得し、セッションに再設定する
        self._session.user = self._user.find_by_id(user.id)

    def __enter__(self):
        return self

    def __exit__(self, ex_type, ex_value, trace):
        self.close()

    def end(self):
        self._session.end()

    def close(self):
        self._session.end()
        self._session.close()

    def get_active_connections(self):
        """
        PostgreSQLへのActive状態の接続の有無を確認する
        """
        from sqlalchemy import text

        database_name = 'streamcat'

        sql = text(f"""
        SELECT
            pid,
            query_start,
            client_addr,
            application_name,
            query
        FROM
            pg_stat_activity
        WHERE
            /* このSQLの実行で用いる接続は除外する */
            pid <>  pg_backend_pid()
        AND datname = '{database_name}'
        AND state = 'active'
        """)

        try:
            return self._session.execute(sql)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            pass

    @property
    def myself(self) -> User:
        return self._session.user

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


class DatumFactory():

    def __init__(self, session):
        self._session = session

    def create_root(self, label):
        from streamcat.store import Folder
        return Folder(self._session, None, label)

    def find_by_id(self, id, type=None) -> SavableDatum:
        """
        指定されたidを持つDatumを取得する
        """
        query = self._session.query(SavableDatum).filter(SavableDatum.id==id)

        if type is not None:
            query = query.filter(SavableDatum.type==type)

        # 結果が1件以外の場合はNoResultFoundが送出される
        try:
            datum = query.one()
        except NoResultFound:
            raise Exception(f'指定したDatum({id})は存在しませんでした')

        return datum

    def find_by_uuid(self, uuid, type=None, folder_path=False) -> SavableDatum:
        """
        指定されたuuidを持つDatumを取得する
        """
        # UUID値の形式チェックをする
        Datum.valid_uuid_or_raise(uuid)

        query = self._session.query(SavableDatum, folder_path=folder_path).filter(SavableDatum.uuid==uuid)

        if type is not None:
            query = query.filter(SavableDatum.type==type)

        # 結果が1件以外の場合はNoResultFoundが送出される
        try:
            datum = query.one()
        except NoResultFound:
            raise Exception(f'指定したDatum({uuid})は存在しませんでした')

        return datum

    def find_all(self, type=None, except_trash=False, except_label=None) -> SavableDatum:
        """
        全てのDatumを取得する
        """
        from sqlalchemy import desc
        query = self._session.query(SavableDatum)
        if type is not None:
            query = query.filter(SavableDatum.type==type)
        if except_trash:
            # ゴミ箱にほかされたDatumは除外する
            # NOTE: この条件を付与するとかなり遅くなる
            query = query.filter(~self._make_exists_trashed(SavableDatum.uuid))
        if except_label is not None:
            query = query.filter(SavableDatum._label!=except_label)
        return query.order_by(SavableDatum.type, desc(SavableDatum.created_at)).all()

    def count_root(self) -> int:
        return self._session.query(SavableDatum).filter(SavableDatum.parent_id == None).count()

    def find_root(self) -> Union[Folder, None]:
        """
        親を持たないfolderレコードを全て取得する
        """
        roots = self._session.query(SavableDatum).filter(SavableDatum.parent_id == None).all()

        if len(roots) == 0 :
            # ルートフォルダがない場合はNoneを返す
            return None
        elif len(roots) > 1:
            raise Exception('More than 2 roots exist!!')
        
        return roots[0]

    def find_trashcan(self) -> TrashCan:
        """
        ゴミ箱を取得する
        """
        trashcan = self._session.query(SavableDatum).filter(SavableDatum.type==SavableDatum.TRASH_TYPE).one_or_none()
        if trashcan is None:
            raise Exception('no trush can is found by designated id.')
        return trashcan

    def find_all_projects(self, on_root:bool=False, except_label:str=None):
        """
        プロジェクトを全て取得する
        """
        query = self._session.query(SavableDatum).\
                filter(SavableDatum.type==SavableDatum.PROJECT_TYPE)
        if on_root:
            query = query.filter(self._make_exists_on_root(SavableDatum.parent_id))
        if except_label is not None:
            query = query.filter(SavableDatum._label!=except_label)
        # 速度向上のため、order_byを指定しない
        return query.all()

    def find_my_project(self, id) -> SavableDatum:
        """
        指定するidのDatumが属するプロジェクトを取得する
        """
        from sqlalchemy.orm import aliased
        from sqlalchemy.sql.expression import select, exists, and_
        from streamcat.store import ProjectFolder

        # cte: Common Table Expression WITH句のこと
        D0 = aliased(SavableDatum, name='D0')
        R = select(D0.id, D0.parent_id, D0.type).select_from(D0).\
            where(D0.id==id).\
            cte(name='R', recursive=True)

        # WITH句にUNION ALLを用いて再帰クエリとする
        D = aliased(SavableDatum, name='D')
        R = R.union_all(
                select(D.id, D.parent_id, D.type).\
                select_from(R.join(D, and_(D.id==R.c.parent_id,
                                           R.c.type!=SavableDatum.PROJECT_TYPE)))
            )

        # プロジェクトを取得する
        exists_project = exists().where(and_(R.c.id==ProjectFolder.id, R.c.type==SavableDatum.PROJECT_TYPE))
        query = self._session.query(ProjectFolder).filter(exists_project)
        return query.one()

    def find_all_subflows(self):
        """
        サブフローを取得する
        """
        from sqlalchemy import exists, and_, literal
        from streamcat.store.auth import Auth

        # 検索対象のDatumの編集ロックを権限の判定条件に含める条件
        exists_edit_lock = exists().where(and_(Auth.datum_id==SavableDatum.id,
                                               Auth.role_id==Role.id,
                                               Role.uuid==literal(Role.EDIT_LOCK_ROLE_UUID)))
        # 編集ロック=ONのフローをサブフローとして抽出する
        return self._session.query(SavableDatum).filter(SavableDatum.type==SavableDatum.FLOW_TYPE)\
                                         .filter(exists_edit_lock)\
                                         .order_by(SavableDatum._label, SavableDatum.id)\
                                         .all()

    def find_all_stores(self):
        """
        データストアを全て取得する
        """
        return self._session.query(SavableDatum).filter(
                                                SavableDatum.type.in_([SavableDatum.DATABASE_TYPE,
                                                                SavableDatum.RFOLDER_TYPE])
                                          )\
                                         .order_by(SavableDatum._label, SavableDatum.id)\
                                         .all()

    def load_root(self):
        """
        ルートデータストアを取得する、存在しない場合は作成する
        """
        root = self.find_root()
        if root is None:
            # find_root()はルートフォルダの参照権限が無いとNoneを返すので、
            # 参照権限を無視するcount_root()で参照権限の無いルートフォルダが無いことを確認する
            if self.count_root() > 0:
                raise Exception(f'{self._session.user} has no authz of root.')
            # ルートフォルダが存在しない場合はルートフォルダを作成する
            # (最初にライブラリ画面にアクセスする時はルートフォルダ自身も存在しません)
            new_root = self.create_root(label='ライブラリ')
            # folderレコードをDBに格納する
            new_root.save()
            # Rootフォルダは、everyoneにRWX権限、usr_adminにO権限を設定する
            self._permit_to_everyone(new_root.id, read=True, write=True, exec=True)
            self._permit_to_usradmin(new_root.id, own=True)
            # 作成ユーザの権限を全て削除する
            self._delete_self_auth(new_root)
            # 参照権限設定後にもう一度取得し直す
            root = new_root.reload()
        return root

    def load_cache_folder(self) -> Folder:
        """
        キャッシュフォルダを取得する、存在しない場合は作成する
        """
        # 特定用途のフォルダのUUIDは決め打ちである
        uuid = SavableDatum.CACHE_FOLDER_UUID
        label = SavableDatum.CACHE_FOLDER_LABEL

        if self.exists(uuid):
            return self.find_by_uuid(uuid)
        else:
            folder = self._make_system_folder(uuid, label)
            # キャッシュフォルダは、everyoneにRW権限、user_admin権限にOを設定する
            self._permit_to_everyone(folder.id, read=True, write=True)
            self._permit_to_usradmin(folder.id, own=True)
            # 作成ユーザの権限を全て削除する
            self._delete_self_auth(folder)
            # 参照権限設定後にもう一度取得し直す
            return folder.reload()

    def load_activity_folder(self) -> Folder:
        """
        アクティビティフォルダを取得する、存在しない場合は作成する
        """
        # 特定用途のフォルダのUUIDは決め打ちである
        uuid = SavableDatum.ACTIVITY_FOLDER_UUID
        label = SavableDatum.ACTIVITY_FOLDER_LABEL

        if self.exists(uuid):
            return self.find_by_uuid(uuid)
        else:
            folder = self._make_system_folder(uuid, label)
            # アクティビティフォルダは、everyoneにRW権限、user_admin権限にOを設定する
            self._permit_to_everyone(folder.id, read=True, write=True)
            self._permit_to_usradmin(folder.id, own=True)
            # 作成ユーザの権限を全て削除する
            self._delete_self_auth(folder)
            # 参照権限設定後にもう一度取得し直す
            return folder.reload()    

    def load_flow_folder(self):
        """
        フローフォルダを取得する、存在しない場合は作成する
        TODO: フローフォルダは使わなくなりました(廃止予定)
        """
        # 特定用途のフォルダのUUIDは決め打ちである
        uuid = SavableDatum.FLOW_FOLDER_UUID
        label = SavableDatum.FLOW_FOLDER_LABEL

        if self.exists(uuid):
            return self.find_by_uuid(uuid)
        else:
            folder = self._make_system_folder(uuid, label)
            return folder.reload()

    def load_trash_folder(self):
        """
        ゴミ箱フォルダを取得する、存在しない場合は作成する
        """
        from streamcat.store import TrashCan
        if self.trashcan_exists():
            return self.find_trashcan()
        else:
            # ゴミ箱が無い場合は作成する
            root = self.load_root()
            trash = root.create_trashcan()
            trash.save()
            # ゴミ箱は、everyoneにRW権限、user_admin権限にOを設定する
            self._permit_to_everyone(trash.id, read=True, write=True)
            self._permit_to_usradmin(trash.id, own=True)
            # 作成ユーザの権限を全て削除する
            self._delete_self_auth(trash)
            # 参照権限設定後にもう一度取得し直す
            return trash.reload()

    def _make_system_folder(self, uuid, label):
        # UUID値の形式チェックをする
        Datum.valid_uuid_or_raise(uuid)
        # フォルダを作成する
        root = self.load_root()
        folder = root.create_folder(label)
        # Folderのコンストラクタで付番したUUIDを捨てて、特定用途のフォルダのUUIDを格納する
        folder.uuid = uuid
        folder.save()
        return folder

    def _permit_to_usradmin(self, datum_id, read=None, write=None, exec=None, own=None):
        # usr_adminロールを取得する
        usr_admin_role = RoleFactory(self._session).load_usr_admin_role()
        # usr_adminロールへDatumの権限を付与する
        usr_admin_role.init_authz(datum_id, read=read, write=write, exec=exec, own=own)

    def _permit_to_everyone(self, datum_id, read=None, write=None, exec=None):
        # everyoneロールを取得する
        everyone_role = RoleFactory(self._session).load_everyone_role()
        # everyoneロールへDatumの権限を付与する
        everyone_role.init_authz(datum_id, read=read, write=write, exec=exec)

    def _delete_self_auth(self, datum):
        # 作成者(creator)の本人ロールからDatumの権限を削除する
        self_role = datum.creator.load_self_role()
        self_role.clear_authz(datum.id)

    def exists(self, uuid, type=None) -> bool:
        """
        指定されたuuidを持つDatumが存在する場合はTrueを返す
        """
        # UUID値の形式チェックをする
        if not Datum.is_valid_uuid(uuid):
            return False

        query = self._session.query(SavableDatum).filter(SavableDatum.uuid==uuid)

        if type is not None:
            query = query.filter(SavableDatum.type==type)

        return query.count() > 0

    def exists_by_id(self, id, type=None) -> bool:
        """
        指定されたidを持つDatumが存在する場合はTrueを返す
        """
        query = self._session.query(SavableDatum).filter(SavableDatum.id==id)

        if type is not None:
            query = query.filter(SavableDatum.type==type)

        return query.count() > 0

    def trashcan_exists(self) -> bool:
        """
        ゴミ箱が存在する場合はTrueを返す
        """
        result = self._session.query(SavableDatum).filter(SavableDatum.type==SavableDatum.TRASH_TYPE).count()
        return result > 0

    def trashed(self, uuid) -> bool:
        """
        ゴミ箱の中にある場合はTrueを返す
        """
        result = self._session.query(SavableDatum).\
                 filter(SavableDatum.uuid==uuid).\
                 filter(self._make_exists_trashed(uuid)).count()
        return result > 0

    def _make_exists_on_root(self, parent_id:str):
        from sqlalchemy import select, exists
        from sqlalchemy.orm import aliased

        # ルートフォルダ直下のDatumを全て取得するクエリ
        D0 = aliased(SavableDatum, name='D0')
        T = select(D0.id).\
            select_from(D0).\
            where(D0.parent_id == None)

        # 指定されたUUIDのDatumがルートフォルダ直下に存在する場合は抽出する
        return exists().where(T.c.id==parent_id)

    def _make_exists_trashed(self, uuid:str):
        from sqlalchemy import select, exists
        from sqlalchemy.orm import aliased

        # ゴミ箱の中のDatumを全て取得する再帰クエリ
        D0 = aliased(SavableDatum, name='D0')
        D1 = aliased(SavableDatum, name='D1')
        T = select(D0.id, D0.uuid).\
            select_from(D0).\
            where(D0.type==SavableDatum.TRASH_TYPE).\
            cte(name='T', recursive=True)
        T = T.union_all(
                select(D1.id, D1.uuid).\
                select_from(T.join(D1, D1.parent_id==T.c.id))
            )

        # 指定されたUUIDのDatumがゴミ箱内に存在する場合は抽出する
        return exists().where(T.c.uuid==uuid)

    def unmount_all(self):
        """
        全てのマウント可能データストアのマウントを解除する
        """
        # 全てのマウント可能データストアを取得する
        mountables = self._session.query(SavableDatum).filter(
                                                    SavableDatum.type.in_([SavableDatum.RFOLDER_TYPE])
                                                ).all()
        # マウント解除する
        for mountable in mountables:
            mountable.unmount()

class StoreFactory():

    def __init__(self, session):
        self._session = session

    def create(self, id, version=None, label=None, description=None, url=None, params=None):
        from streamcat.store import StoreModel as Store
        data = {'version'    : version,
                'label'      : label,
                'description': description,
                'url'        : url,
                'params'     : params}
        store = Store(id, data, self._session.user)
        store._session = self._session
        return store

    def find_all(self):
        from streamcat.store import StoreModel as Store
        return self._session.query(Store).all()

    def find_by_id(self, id):
        from streamcat.store import StoreModel as Store
        result = self._session.query(Store).filter(Store.id==id).one_or_none()
        if result is None:
            raise Exception('No store is found by designated store id')
        return result


class AuthFactory():
    from streamcat.store.auth import Auth

    def __init__(self, session):
        self._session = session

    def create(self, role_id, datum_id, operation, permission):
        from streamcat.store.auth import Auth
        return Auth(self._session, role_id, datum_id, operation, permission)

    def find_by_id(self, role_id, datum_id, operation) -> Auth:
        from streamcat.store.auth import Auth
        # SQLAlchemyのidentity mapにキャッシュされていればそれを返す
        authz = self._session.get(Auth, (role_id, datum_id, operation))
        if authz is None:
            raise Exception('No authz is found by designated id')
        return authz

    def find_all_by_datum_id(self, datum_id) -> list[Auth]:
        from streamcat.store.auth import Auth
        query = self._session.query(Auth).filter(Auth.datum_id==datum_id)
        return query.order_by(Auth.role_id, Auth.operation).all()

    def exists(self, role_id, datum_id, operation=None) -> bool:
        from streamcat.store.auth import Auth
        query = self._session.query(Auth).filter(Auth.role_id==role_id)\
                                         .filter(Auth.datum_id==datum_id)
        if operation is not None:
            query = query.filter(Auth.operation==operation)

        return query.count() > 0

    def delete_all_by_datum_id(self, datum_id, except_role_uuids=None):
        """
        Authzテーブルから指定したDatumの権限情報を全て削除する
        """
        from sqlalchemy import exists, and_
        from streamcat.store.auth import Auth, Role

        query = self._session.query(Auth).filter(Auth.datum_id==datum_id)
        if except_role_uuids is None or len(except_role_uuids) == 0:
            synchronize_session = 'evaluate'
        else:
            not_exists_except_role = ~exists().where(and_(Role.id==Auth.role_id, Role.uuid.in_(except_role_uuids)))
            query = query.filter(not_exists_except_role)
            synchronize_session = 'fetch'

        try:
            # 抽出条件にサブクエリなどを使ってDELETEする場合は
            # synchronize_sessionにFalseか'fetch'の指定が必要
            query.delete(synchronize_session=synchronize_session)
        except Exception as e:
            self._session.rollback()
            raise e


class RoleFactory():
    def __init__(self, session):
        self._session = session

    def create(self, name, delete_on_isolated=False):
        from streamcat.store.auth import Role
        return Role(self._session, name, delete_on_isolated)

    def find_by_id(self, role_id) -> Role:
        return self._session.query(Role).filter(Role.id == role_id).one()

    def find_by_uuid(self, uuid) -> Role:
        return self._session.query(Role).filter(Role.uuid == uuid).one()

    def find_all(self):
        """
        全件取得する
        """
        return self._session.query(Role).all()

    def find_isolated(self, delete_on_isolated=False):
        """
        どのDatumにも紐づかない場合はTrueを返す
        """
        from sqlalchemy import exists
        from streamcat.store.auth import Auth

        query = self._session.query(Role).\
                filter(~exists().where(Auth.role_id==Role.id))
        if delete_on_isolated:
            query = query.filter(Role._delete_on_isolated==True)

        return query.all()

    def load_sys_admin_role(self):
        if self.exists(Role.SYS_ADMIN_ROLE_UUID):
            sys_admin_role = self.find_by_uuid(Role.SYS_ADMIN_ROLE_UUID)
        else:
            sys_admin_role = Role(self._session, Role.SYS_ADMIN_ROLE_LABEL)
            # コンストラクタで付番したUUIDを捨てて、特定用途のUUIDを格納する
            sys_admin_role.uuid = Role.SYS_ADMIN_ROLE_UUID
            sys_admin_role.save()
        return sys_admin_role

    def load_usr_admin_role(self):
        if self.exists(Role.USR_ADMIN_ROLE_UUID):
            usr_admin_role = self.find_by_uuid(Role.USR_ADMIN_ROLE_UUID)
        else:
            usr_admin_role = Role(self._session, Role.USR_ADMIN_ROLE_LABEL)
            # コンストラクタで付番したUUIDを捨てて、特定用途のUUIDを格納する
            usr_admin_role.uuid = Role.USR_ADMIN_ROLE_UUID
            usr_admin_role.save()
        return usr_admin_role

    def load_everyone_role(self):
        if self.exists(Role.EVERYONE_ROLE_UUID):
            everyone_role = self.find_by_uuid(Role.EVERYONE_ROLE_UUID)
        else:
            everyone_role = Role(self._session, Role.EVERYONE_ROLE_LABEL)
            # コンストラクタで付番したUUIDを捨てて、特定用途のUUIDを格納する
            everyone_role.uuid = Role.EVERYONE_ROLE_UUID
            everyone_role.save()

        return everyone_role

    def load_edit_lock_role(self):
        if self.exists(Role.EDIT_LOCK_ROLE_UUID):
            edit_lock_role = self.find_by_uuid(Role.EDIT_LOCK_ROLE_UUID)
        else:
            edit_lock_role = Role(self._session, Role.EDIT_LOCK_ROLE_LABEL)
            # コンストラクタで付番したUUIDを捨てて、特定用途のUUIDを格納する
            edit_lock_role.uuid = Role.EDIT_LOCK_ROLE_UUID
            edit_lock_role.save()
        return edit_lock_role

    def exists(self, uuid) -> bool:
        count = self._session.query(Role).filter(Role.uuid==uuid).count()
        return count > 0


class UserRoleFactory():
    def __init__(self, session):
        self._session = session

    def find_by_id(self, user_id, role_id) -> UserRole:
        return self._session.query(UserRole).\
                       filter(UserRole.user_id==user_id).\
                       filter(UserRole.role_id==role_id).\
                       one()

    def find_all_by_user_id(self, user_id, except_role_uuids=None):
        query = self._session.query(UserRole).filter(UserRole.user_id==user_id)
        if except_role_uuids is not None and len(except_role_uuids) > 0:
            from sqlalchemy import exists, and_
            not_exists_role = ~exists().where(and_(Role.id==UserRole.role_id, Role.uuid.in_(except_role_uuids)))
            query = query.filter(not_exists_role)
        return query.all()

    def exists(self, user_id, role_id=None) -> bool:
        query = self._session.query(UserRole).filter(UserRole.user_id==user_id)
        if role_id is not None:
            query = query.filter(UserRole.role_id==role_id)
        return query.count() > 0

    def delete_all_by_user_id(self, user_id):
        """
        UsersRolesテーブルから指定したユーザの所属情報を全て削除する
        """
        try:
            self._session.query(UserRole).filter(UserRole.user_id==user_id).delete()
        except Exception as e:
            self._session.rollback()
            raise e

    def delete_all_by_role_id(self, role_id, except_user_id=None):
        """
        UsersRolesテーブルから指定したロールの所属情報を全て削除する
        """
        query = self._session.query(UserRole).filter(UserRole.role_id==role_id)

        # 削除から除外するユーザが指定されている場合
        if except_user_id is not None:
            query = query.filter(UserRole.user_id!=except_user_id)

        try:
            query.delete()
        except Exception as e:
            self._session.rollback()
            raise e


class UserFactory():
    def __init__(self, session):
        self._session = session

    def create(self, email, name, password, issuer=None, subject=None):
        from streamcat.store.auth import User
        return User(self._session, email, name, password, issuer=issuer, subject=subject)

    def find_all(self, except_states=None):
        query = self._session.query(User).order_by(User.email)
        query = UserFactory._add_except_states_criteria(query, except_states)
        return query.all()

    def find_by_id(self, user_id, except_states=None, allow_no_result=False) -> User:
        # SQLAlchemyのidentity mapにキャッシュされていればそれを返す
        user = self._session.get(User, user_id)

        if user is None and not allow_no_result:
            raise Exception(f'指定したUser({user_id})は存在しませんでした')

        if except_states is not None:
            if not isinstance(except_states, list):
                raise Exception(f'except_statesにはNoneかlist型を指定してください')
            if user.state in except_states:
                raise Exception(f'指定したUser({user_id})は存在しませんでした.')
        
        return user

    def find_by_uuid(self, uuid, except_states=None) -> User:
        # UUID値の形式チェックをする
        Datum.valid_uuid_or_raise(uuid)
        # 結果が1件以外の場合はNoResultFoundが送出される
        try:
            query = self._session.query(User).filter(User.uuid==uuid)
            query = UserFactory._add_except_states_criteria(query, except_states)
            return query.one()
        except NoResultFound:
            raise Exception(f'指定したUser({uuid})は存在しませんでした')

    def find_by_email(self, email, except_states=None) -> User:
        """
        指定されたuuidを持つUserを取得する
        """
        # 結果が1件以外の場合はNoResultFoundが送出される
        try:
            query = self._session.query(User).filter(User.email==email)
            query = UserFactory._add_except_states_criteria(query, except_states)
            return query.one()
        except NoResultFound:
            raise Exception(f'指定したUser({email})は存在しませんでした')

    def find_by_openid(self, issuer, subject, except_states=None) -> User:
        """
        指定されたissuerとsubjectのUserを取得する
        """
        try:
            query = self._session.query(User).filter(User.issuer==issuer, User.subject==subject)
            query = UserFactory._add_except_states_criteria(query, except_states)
            return query.one()
        except NoResultFound:
            raise Exception(f'指定したUser({subject})は存在しませんでした')

    def find_by_keyword(self, keyword, except_states=None):
        """
        キーワードを含むユーザ名またはE-MailのUserを取得する
        """
        def split_keyword(keyword):
            """
            空白区切りの検索語をリストに分割する
            """
            import csv
            striped_keyword = keyword.strip()
            # 検索語が空白のみの場合はその空白を検索語とする
            if striped_keyword == '':
                return [keyword]
            ret = csv.reader([striped_keyword], delimiter=" ", doublequote=True, quotechar='"', skipinitialspace=True)
            return next(ret)

        from sqlalchemy.sql.expression import and_, or_
        query = self._session.query(User)

        like_predicates = []
        for search_keyword in split_keyword(keyword):
            # 検索語の大文字小文字の区別はしない
            like_predicates.append(or_(User.name.icontains(search_keyword),
                                       User.email.icontains(search_keyword)))

        query = query.filter(and_(*like_predicates))
        query = UserFactory._add_except_states_criteria(query, except_states)

        return query.order_by(User.email).all()

    def exists(self, uuid, except_states=None) -> bool:
        query = self._session.query(User).filter(User.uuid==uuid)
        query = UserFactory._add_except_states_criteria(query, except_states)
        return query.count() > 0

    def exists_by_email(self, email, except_states=None) -> bool:
        query = self._session.query(User).filter(User.email==email)
        query = UserFactory._add_except_states_criteria(query, except_states)
        return query.count() > 0

    def exists_by_openid(self, issuer, subject, except_states=None) -> bool:
        query = self._session.query(User).filter(User.issuer==issuer, User.subject==subject)
        query = UserFactory._add_except_states_criteria(query, except_states)
        return query.count() > 0

    def load_openid_user(self, email, name, issuer, subject):
        """
        OpenID Connectのアクセストークンからユーザを取得する
        ユーザが存在しない場合は作成する
        """
        user_factory = UserFactory(self._session)

        # ユーザが存在する場合は、それを返す
        if user_factory.exists_by_openid(issuer, subject):
            user = user_factory.find_by_openid(issuer, subject)
            # ユーザが論理削除状態の場合は例外を送出する
            if user.is_inactive:
                raise Exception(f'指定したUser({email})は削除されました')
            else:
                return user

        # ユーザが存在しない場合は、新規にユーザを作成する
        # (passwordの指定がなければ自動生成する)
        new_user = user_factory.create(email, name, password=None, issuer=issuer, subject=subject)
        new_user.save()

        # ランダムなパスワードを設定してユーザを登録状態にする
        new_user.update_password(new_password=new_user._generate_password())

        return new_user

    @staticmethod
    def _add_except_states_criteria(query, except_states):
        if except_states is None:
            return query
        elif isinstance(except_states, list):
            return query.filter(User.state.notin_(except_states))
        else:
            raise Exception(f'except_statesにはNoneかlist型を指定してください')
