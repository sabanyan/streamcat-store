from sqlalchemy import select, func
from sqlalchemy.orm.exc import NoResultFound
from streamcat.core import Datum, SavableDatum
from streamcat.store import Folder, TrashCan
from streamcat.store.auth import User, Role, UserRole


class UnAuthzFinder():

    def __init__(self):
        from sqlalchemy.orm import sessionmaker
        from streamcat.store.auth.authz_session import Session
        from . import engine

        # セッションを生成する
        # ・session.commit()によるExpireでquery_expression()で設定されているreadableがNoneになる
        # ・これを回避するためexpire_on_commit=Falseとする、autoflush=Falseも必要!
        # ・session.rollback()によるExprireを回避する方法はない
        # ・future=True : SQLAlchemy2.0スタイルのトランザクションおよびエンジンの動作を使用する
        session_maker = sessionmaker(engine, expire_on_commit=False, autoflush=False, future=True)

        # セッションを保持する
        self._session = Session(session_maker(), user=None)

    async def create_authz_finder(self, user:User):
        """
        Finderを生成する
        """
        return Finder(self._session._session, user)

    async def find_user_by_email(self, email):
        return UserFinder(self._session).find_by_email(email)

    async def find_user_by_uuid(self, user_uuid):
        return UserFinder(self._session).find_by_uuid(user_uuid)

    async def load_sys_admin_user(self, activate_if_inactive=False):
        """
        システム管理者を取得する、存在しない場合は作成する
        """
        from streamcat.store.auth import User, Role

        SYS_ADMIN_USER_EMAIL = 'Admin@streamcat.io'
        SYS_ADMIN_USER_NAME = 'システム管理者'

        user_finder = UserFinder(self._session)
        role_finder = RoleFinder(self._session)

        # 管理者ユーザが存在する場合は、それを返す
        if user_finder.exists_by_email(SYS_ADMIN_USER_EMAIL, except_states=[User.INACTIVE_STATE]):
            return user_finder.find_by_email(SYS_ADMIN_USER_EMAIL, except_states=[User.INACTIVE_STATE])

        # 管理者ロールが存在する場合は、そのロールの中でidが最も小さいユーザを取得する
        if role_finder.exists(Role.SYS_ADMIN_ROLE_UUID):
            sys_admin_role = role_finder.find_by_uuid(Role.SYS_ADMIN_ROLE_UUID)
            joined_users = sys_admin_role.get_joined_users(except_states=[User.INACTIVE_STATE])
            if len(joined_users) > 0:
                return joined_users[0]

        # デフォルトの管理者ユーザが論理削除されている場合は、そのまま返すか、登録状態に戻して返す
        if user_finder.exists_by_email(SYS_ADMIN_USER_EMAIL):
            sys_admin_user = user_finder.find_by_email(SYS_ADMIN_USER_EMAIL)
            activate_if_inactive and sys_admin_user.put_back()
            return sys_admin_user

        # 管理者ロールが無い場合は、デフォルトの管理者ユーザを作成する
        sys_admin_user = user_finder.create(SYS_ADMIN_USER_EMAIL, SYS_ADMIN_USER_NAME, 'adminpass0')
        sys_admin_user.save()
        return sys_admin_user

    async def load_usr_admin_user(self, activate_if_inactive=False):
        """
        ユーザ管理者を取得する、存在しない場合は作成する
        """
        from streamcat.store.auth import Role

        USR_ADMIN_USER_EMAIL = 'admin@streamcat.io'
        USR_ADMIN_USER_NAME = 'ユーザー管理者'

        user_finder = UserFinder(self._session)
        role_finder = RoleFinder(self._session)

        if user_finder.exists_by_email(USR_ADMIN_USER_EMAIL, except_states=[User.INACTIVE_STATE]):
            return user_finder.find_by_email(USR_ADMIN_USER_EMAIL, except_states=[User.INACTIVE_STATE])

        if role_finder.exists(Role.USR_ADMIN_ROLE_UUID):
            usr_admin_role = role_finder.find_by_uuid(Role.USR_ADMIN_ROLE_UUID)
            joined_users = usr_admin_role.get_joined_users(except_states=[User.INACTIVE_STATE])
            if len(joined_users) > 0:
                return joined_users[0]

        if user_finder.exists_by_email(USR_ADMIN_USER_EMAIL):
            usr_admin_user = user_finder.find_by_email(USR_ADMIN_USER_EMAIL)
            activate_if_inactive and usr_admin_user.put_back()
            return usr_admin_user

        usr_admin_user = user_finder.create(USR_ADMIN_USER_EMAIL, USR_ADMIN_USER_NAME, 'adminpass0')
        usr_admin_user.save()
        return usr_admin_user

    async def __aenter__(self):
        return self

    async def __aexit__(self, ex_type, ex_value, trace):
        await self.close()

    async def close(self):
        self._session.end()
        self._session.close()


class Finder():
    """
    SQLAlchemyのSessionを保持する(とりあえずこの目的ね)
    """
    def __init__(self, sqlalchemy_session, user:User=None):
        from streamcat.store.auth.authz_session import AuthzSession
        # Sessionを保持する
        self._session = AuthzSession(sqlalchemy_session, user)
        # AuthzSession.userが保持するSessionをAuthzSessionでラップする
        # NOTE: AuthzSession.userが循環参照になっているが問題にはならないだろう
        self._session._user._session = AuthzSession(sqlalchemy_session, self._session._user)

        # 各Finderを保持する
        self._data = DatumFinder(self._session)
        self._store = StoreFinder(self._session)
        self._auth = AuthFinder(self._session)
        self._role = RoleFinder(self._session)
        self._user_role = UserRoleFinder(self._session)
        self._user = UserFinder(self._session)

    def end(self):
        self._session.end()

    def close(self):
        self._session.end()
        self._session.close()

    async def get_active_connections(self):
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
            return self._session.execute(sql).all()
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            pass

    @staticmethod
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


class DatumFinder():

    def __init__(self, session):
        self._session = session

    def create_root(self, label):
        from streamcat.store import Folder
        return Folder(self._session, None, label)

    def find_by_id(self, id, type=None) -> SavableDatum:
        """
        指定されたidを持つDatumを取得する
        """
        stmt = select(SavableDatum).where(SavableDatum.id==id)

        if type is not None:
            stmt = stmt.where(SavableDatum.type==type)

        # 結果が1件以外の場合はNoResultFoundが送出される
        try:
            datum = self._session.scalars(stmt).one()
        except NoResultFound:
            raise Exception(f'指定したDatum({id})は存在しませんでした')

        return datum

    def find_by_uuid(self, uuid, type=None, folder_path=False, for_update=False) -> SavableDatum:
        """
        指定されたuuidを持つDatumを取得する
        """
        # UUID値の形式チェックをする
        Datum.valid_uuid_or_raise(uuid)

        stmt = select(SavableDatum).where(SavableDatum.uuid==uuid)

        if type is not None:
            stmt = stmt.where(SavableDatum.type==type)

        if for_update:
            # DBの排他ロックをかける
            stmt = stmt.with_for_update(of=SavableDatum)

        # 結果が1件以外の場合はNoResultFoundが送出される
        try:
            datum = self._session.scalars(stmt, folder_path=folder_path).one()
        except NoResultFound:
            raise Exception(f'指定したDatum({uuid})は存在しませんでした')

        return datum

    def find_by_keyword(self, keyword, type=None, except_trash=False, offset:int=None, limit:int=None):
        """
        キーワードを含むラベルのDatumを取得する
        """
        from sqlalchemy import desc
        from sqlalchemy.sql.expression import and_, or_
        stmt = select(SavableDatum)

        if type is not None:
            stmt = stmt.where(SavableDatum.type==type)
        if except_trash:
            # ゴミ箱にほかされたDatumは除外する
            # NOTE: この条件を付与するとかなり遅くなる
            stmt = stmt.where(~self._make_exists_trashed(SavableDatum.uuid))

        like_predicates = []
        for search_keyword in Finder.split_keyword(keyword):
            # 検索語の大文字小文字の区別はしない
            like_predicates.append(or_(SavableDatum._label.icontains(search_keyword),
                                       SavableDatum._desc.icontains(search_keyword)))

        stmt = stmt.where(and_(*like_predicates))

        stmt = stmt.order_by(SavableDatum.type, desc(SavableDatum.created_at)).\
                    offset(offset).limit(limit)
        return self._session.scalars(stmt).all()

    def find_all(self, type=None, except_trash=False, except_label=None) -> SavableDatum:
        """
        全てのDatumを取得する
        """
        from sqlalchemy import desc
        stmt = select(SavableDatum)
        if type is not None:
            stmt = stmt.where(SavableDatum.type==type)
        if except_trash:
            # ゴミ箱にほかされたDatumは除外する
            # NOTE: この条件を付与するとかなり遅くなる
            stmt = stmt.where(~self._make_exists_trashed(SavableDatum.uuid))
        if except_label is not None:
            stmt = stmt.where(SavableDatum._label!=except_label)
        stmt = stmt.order_by(SavableDatum.type, desc(SavableDatum.created_at))
        return self._session.scalars(stmt).all()

    def count_root(self) -> int:
        stmt = select(func.count(SavableDatum.id)).where(SavableDatum.parent_id == None)
        return self._session.scalars(stmt).one()

    def find_root(self) -> Folder|None:
        """
        親を持たないfolderレコードを全て取得する
        """
        stmt = select(SavableDatum).where(SavableDatum.parent_id == None)
        roots = self._session.scalars(stmt).all()

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
        stmt = select(SavableDatum).where(SavableDatum.type==SavableDatum.TRASH_TYPE)
        trashcan = self._session.scalars(stmt).one_or_none()
        if trashcan is None:
            raise Exception('no trush can is found by designated id.')
        return trashcan

    def find_all_projects(self, on_root:bool=False, except_label:str=None):
        """
        プロジェクトを全て取得する
        """
        stmt = select(SavableDatum).where(SavableDatum.type==SavableDatum.PROJECT_TYPE)
        if on_root:
            stmt = stmt.where(self._make_exists_on_root(SavableDatum.parent_id))
        if except_label is not None:
            stmt = stmt.where(SavableDatum._label!=except_label)
        # 速度向上のため、order_byを指定しない
        return self._session.scalars(stmt).all()

    def find_my_project(self, id) -> SavableDatum:
        """
        指定するidのDatumが属するプロジェクトを取得する
        """
        from sqlalchemy.orm import aliased
        from sqlalchemy.sql.expression import exists, and_
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
        stmt = select(ProjectFolder).where(exists_project)
        return self._session.scalars(stmt).one()

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
        stmt =  select(SavableDatum).\
                where(SavableDatum.type==SavableDatum.FLOW_TYPE).\
                where(exists_edit_lock).\
                order_by(SavableDatum._label, SavableDatum.id)
        return self._session.scalars(stmt).all()

    def find_all_stores(self, except_trash=False):
        """
        データストアを全て取得する
        """
        stmt =  select(SavableDatum).\
                where(SavableDatum.type.in_([SavableDatum.DATABASE_TYPE,SavableDatum.RFOLDER_TYPE])).\
                order_by(SavableDatum._label, SavableDatum.id)
        if except_trash:
            # ゴミ箱にほかされたデータストアは除外する
            stmt = stmt.where(~self._make_exists_trashed(SavableDatum.uuid))
        return self._session.scalars(stmt).all()

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
        usr_admin_role = RoleFinder(self._session).load_usr_admin_role()
        # usr_adminロールへDatumの権限を付与する
        usr_admin_role.init_authz(datum_id, read=read, write=write, exec=exec, own=own)

    def _permit_to_everyone(self, datum_id, read=None, write=None, exec=None):
        # everyoneロールを取得する
        everyone_role = RoleFinder(self._session).load_everyone_role()
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

        stmt = select(func.count(SavableDatum.id)).where(SavableDatum.uuid==uuid)
        if type is not None:
            stmt = stmt.where(SavableDatum.type==type)

        return self._session.scalars(stmt).one() > 0

    def exists_by_id(self, id, type=None) -> bool:
        """
        指定されたidを持つDatumが存在する場合はTrueを返す
        """
        stmt = select(func.count(SavableDatum.id)).where(SavableDatum.id==id)
        if type is not None:
            stmt = stmt.where(SavableDatum.type==type)

        return self._session.scalars(stmt).one() > 0

    def trashcan_exists(self) -> bool:
        """
        ゴミ箱が存在する場合はTrueを返す
        """
        stmt = select(func.count(SavableDatum.id)).where(SavableDatum.type==SavableDatum.TRASH_TYPE)
        return self._session.scalars(stmt).one() > 0

    def trashed(self, uuid) -> bool:
        """
        ゴミ箱の中にある場合はTrueを返す
        """
        stmt =  select(func.count(SavableDatum.id)).\
                where(SavableDatum.uuid==uuid).\
                where(self._make_exists_trashed(uuid))
        return self._session.scalars(stmt).one() > 0

    def _make_exists_on_root(self, parent_id:str):
        from sqlalchemy import exists
        from sqlalchemy.orm import aliased

        # ルートフォルダ直下のDatumを全て取得するクエリ
        D0 = aliased(SavableDatum, name='D0')
        T = select(D0.id).\
            select_from(D0).\
            where(D0.parent_id == None)

        # 指定されたUUIDのDatumがルートフォルダ直下に存在する場合は抽出する
        return exists().where(T.c.id==parent_id)

    def _make_exists_trashed(self, uuid:str):
        from sqlalchemy import exists
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
        stmt = select(SavableDatum).where(SavableDatum.type.in_([SavableDatum.RFOLDER_TYPE]))
        mountables = self._session.scalars(stmt).all()
        # マウント解除する
        for mountable in mountables:
            mountable.unmount()

class StoreFinder():

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
        return self._session.scalars(select(Store)).all()

    def find_by_id(self, id):
        from streamcat.store import StoreModel as Store
        store = self._session.get(Store, id)
        if store is None:
            raise Exception('No store is found by designated store id')
        return store


class AuthFinder():
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
        stmt = select(Auth).where(Auth.datum_id==datum_id).order_by(Auth.role_id, Auth.operation)
        return self._session.scalars(stmt).all()

    def exists(self, role_id, datum_id, operation=None) -> bool:
        from streamcat.store.auth import Auth

        stmt =  select(func.count(Auth.datum_id)).\
                where(Auth.role_id==role_id).\
                where(Auth.datum_id==datum_id)
        if operation is not None:
            stmt = stmt.where(Auth.operation==operation)

        return self._session.scalars(stmt).one() > 0

    def delete_all_by_datum_id(self, datum_id, except_role_uuids=None):
        """
        Authzテーブルから指定したDatumの権限情報を全て削除する
        """
        from sqlalchemy import delete, exists, and_
        from streamcat.store.auth import Auth, Role

        stmt = delete(Auth).where(Auth.datum_id==datum_id)
        if except_role_uuids is None or len(except_role_uuids) == 0:
            synchronize_session = 'evaluate'
        else:
            not_exists_except_role = ~exists().where(and_(Role.id==Auth.role_id, Role.uuid.in_(except_role_uuids)))
            stmt = stmt.where(not_exists_except_role)
            synchronize_session = 'fetch'

        try:
            # 抽出条件にサブクエリなどを使ってDELETEする場合は
            # synchronize_sessionにFalseか'fetch'の指定が必要
            self._session.execute(stmt, synchronize_session=synchronize_session)
        except Exception as e:
            self._session.rollback()
            raise e


class RoleFinder():
    def __init__(self, session):
        self._session = session

    def create(self, name, delete_on_isolated=False):
        from streamcat.store.auth import Role
        return Role(self._session, name, delete_on_isolated)

    def find_by_id(self, role_id) -> Role:
        role = self._session.get(Role, role_id)
        if role is None:
            raise Exception('No role is found by designated role id')
        return role

    def find_by_uuid(self, uuid) -> Role:
        stmt = select(Role).where(Role.uuid==uuid)
        return self._session.scalars(stmt).one()

    def find_all(self):
        """
        全件取得する
        """
        return self._session.scalars(select(Role)).all()

    def find_isolated(self, delete_on_isolated=False):
        """
        どのDatumにも紐づかない場合はTrueを返す
        """
        from sqlalchemy import exists
        from streamcat.store.auth import Auth

        stmt =  select(Role).\
                where(~exists().where(Auth.role_id==Role.id))
        if delete_on_isolated:
            stmt = stmt.where(Role._delete_on_isolated==True)

        return self._session.scalars(stmt).all()

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
        stmt = select(func.count(Role.id)).where(Role.uuid==uuid)
        return self._session.scalars(stmt).one() > 0


class UserRoleFinder():
    def __init__(self, session):
        self._session = session

    def find_by_id(self, user_id, role_id) -> UserRole:
        user_role = self._session.get(UserRole, (user_id, role_id))
        if user_role is None:
            raise Exception('No user_role is found by designated user id and role id')
        return user_role

    def find_all_by_user_id(self, user_id, except_role_uuids=None):
        stmt = select(UserRole).where(UserRole.user_id==user_id)
        if except_role_uuids is not None and len(except_role_uuids) > 0:
            from sqlalchemy import exists, and_
            not_exists_role = ~exists().where(and_(Role.id==UserRole.role_id, Role.uuid.in_(except_role_uuids)))
            stmt = stmt.where(not_exists_role)
        return self._session.scalars(stmt).all()

    def exists(self, user_id, role_id=None) -> bool:
        stmt = select(func.count(UserRole.user_id)).where(UserRole.user_id==user_id)
        if role_id is not None:
            stmt = stmt.where(UserRole.role_id==role_id)
        return self._session.scalars(stmt).one() > 0

    def delete_all_by_user_id(self, user_id):
        """
        UsersRolesテーブルから指定したユーザの所属情報を全て削除する
        """
        from sqlalchemy import delete
        stmt = delete(UserRole).where(UserRole.user_id==user_id)
        try:
            self._session.execute(stmt)
        except Exception as e:
            self._session.rollback()
            raise e

    def delete_all_by_role_id(self, role_id, except_user_id=None):
        """
        UsersRolesテーブルから指定したロールの所属情報を全て削除する
        """
        from sqlalchemy import delete
        stmt = delete(UserRole).where(UserRole.role_id==role_id)
        # 削除から除外するユーザが指定されている場合
        if except_user_id is not None:
            stmt = stmt.where(UserRole.user_id!=except_user_id)
        try:
            self._session.execute(stmt)
        except Exception as e:
            self._session.rollback()
            raise e


class UserFinder():
    def __init__(self, session):
        self._session = session

    def create(self, email, name, password, issuer=None, subject=None):
        from streamcat.store.auth import User
        return User(self._session, email, name, password, issuer=issuer, subject=subject)

    def find_all(self, except_states=None):
        stmt = select(User).order_by(User.email)
        stmt = UserFinder._add_except_states_criteria(stmt, except_states)
        return self._session.scalars(stmt).all()

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
            stmt = select(User).where(User.uuid==uuid)
            stmt = UserFinder._add_except_states_criteria(stmt, except_states)
            return self._session.scalars(stmt).one()
        except NoResultFound:
            raise Exception(f'指定したUser({uuid})は存在しませんでした')

    def find_by_email(self, email, except_states=None) -> User:
        """
        指定されたuuidを持つUserを取得する
        """
        # 結果が1件以外の場合はNoResultFoundが送出される
        try:
            stmt = select(User).where(User.email==email)
            stmt = UserFinder._add_except_states_criteria(stmt, except_states)
            return self._session.scalars(stmt).one()
        except NoResultFound:
            raise Exception(f'指定したUser({email})は存在しませんでした')

    def find_by_openid(self, issuer, subject, except_states=None) -> User:
        """
        指定されたissuerとsubjectのUserを取得する
        """
        try:
            stmt = select(User).where(User.issuer==issuer, User.subject==subject)
            stmt = UserFinder._add_except_states_criteria(stmt, except_states)
            return self._session.scalars(stmt).one()
        except NoResultFound:
            raise Exception(f'指定したUser({subject})は存在しませんでした')

    def find_by_keyword(self, keyword, except_states=None):
        """
        キーワードを含むユーザ名またはE-MailのUserを取得する
        """
        from sqlalchemy.sql.expression import and_, or_
        stmt = select(User)

        like_predicates = []
        for search_keyword in Finder.split_keyword(keyword):
            # 検索語の大文字小文字の区別はしない
            like_predicates.append(or_(User.name.icontains(search_keyword),
                                       User.email.icontains(search_keyword)))

        stmt = stmt.where(and_(*like_predicates))
        stmt = UserFinder._add_except_states_criteria(stmt, except_states)
        stmt = stmt.order_by(User.email)

        return self._session.scalars(stmt).all()

    def exists(self, uuid, except_states=None) -> bool:
        stmt = select(func.count(User.id)).where(User.uuid==uuid)
        stmt = UserFinder._add_except_states_criteria(stmt, except_states)
        return self._session.scalars(stmt).one() > 0

    def exists_by_email(self, email, except_states=None) -> bool:
        stmt = select(func.count(User.id)).where(User.email==email)
        stmt = UserFinder._add_except_states_criteria(stmt, except_states)
        return self._session.scalars(stmt).one() > 0

    def exists_by_openid(self, issuer, subject, except_states=None) -> bool:
        stmt = select(func.count(User.id)).where(User.issuer==issuer, User.subject==subject)
        stmt = UserFinder._add_except_states_criteria(stmt, except_states)
        return self._session.scalars(stmt).one() > 0

    def load_openid_user(self, email, name, issuer, subject):
        """
        OpenID Connectのアクセストークンからユーザを取得する
        ユーザが存在しない場合は作成する
        """
        user_finder = UserFinder(self._session)

        # ユーザが存在する場合は、それを返す
        if user_finder.exists_by_openid(issuer, subject):
            user = user_finder.find_by_openid(issuer, subject)
            # ユーザが論理削除状態の場合は例外を送出する
            if user.is_inactive:
                raise Exception(f'指定したUser({email})は削除されました')
            else:
                return user

        # ユーザが存在しない場合は、新規にユーザを作成する
        # (passwordの指定がなければ自動生成する)
        new_user = user_finder.create(email, name, password=None, issuer=issuer, subject=subject)
        new_user.save()

        # ランダムなパスワードを設定してユーザを登録状態にする
        new_user.update_password(new_password=new_user._generate_password())

        return new_user

    @staticmethod
    def _add_except_states_criteria(stmt, except_states):
        if except_states is None:
            return stmt
        elif isinstance(except_states, list):
            return stmt.where(User.state.notin_(except_states))
        else:
            raise Exception(f'except_statesにはNoneかlist型を指定してください')
