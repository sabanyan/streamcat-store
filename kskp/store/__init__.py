import os

def _is_unittest():
    # python3 -m unittestで実行した場合は、is_unittest=Trueとなる
    import sys
    return '__main__' in sys.modules and \
            hasattr(sys.modules['__main__'], '__unittest') and \
            sys.modules['__main__'].__unittest

def _get_db_engine(database_uri_candidates):
    """
    SQLAlchemyのEnginオブジェクトを作成する
    """
    def _check_connection(database_uri):
        from sqlalchemy import create_engine
        from sqlalchemy.exc import OperationalError
        try:
            # DBに接続する
            # echo=TrueでSQLログがコンソールに出力される
            engine = create_engine(database_uri, echo=False)
            # DBへの接続を確認する
            engine.execute('SELECT 1')
            return engine
        except OperationalError as e:
            # DBに接続できなかった場合
            return None
        except Exception:
            raise

    for database_uri_candidate in database_uri_candidates:
        engine = _check_connection(database_uri_candidate)
        if engine is None:
            continue
        else:
            return engine

    raise Exception('💽 PostgreSQLに接続できませんでした 💽')

def _make_test_schema(engine):
    """
    テストケース実行で使用するデータベーススキーマを作成する
    """
    def _get_test_schema_name():
        # スキーマ名はランダム文字列を命名して他のテスト実行処理とDBスキーマを分ける
        import uuid
        schema_name = 'schema_' + str(uuid.uuid4()).upper()[0:6]
        return schema_name.lower()

    def _create_schema(engine, schema_name):
        # スキーマを作成する
        from sqlalchemy import DDL, exc
        try:
            engine.execute(DDL(f'CREATE SCHEMA IF NOT EXISTS {schema_name}'))
        except exc.OperationalError as e:
            raise Exception('テストケース実行で使用するデータベーススキーマを作成できませんでした')

    # テスト用スキーマ名を設定する
    test_schema_name = _get_test_schema_name()
    # テスト用スキーマを作成する
    _create_schema(engine, test_schema_name)
    return test_schema_name


# バージョンを取得する
from pathlib import Path
kskp_ver_file = Path('/etc/kskp_ver')
if kskp_ver_file.exists() and kskp_ver_file.stat().st_size < 20:
    KSKP_VER = kskp_ver_file.read_text(errors='ignore').strip()
else:
    KSKP_VER = None


db_password = 'ZQZtVgL6G32Vy6p6WJtG3C3K84yuJ4zz'

if _is_unittest():
    # テストスクリプト実行時のDB接続先
    db_port = int(os.getenv('KSKP_DB_PORT', 5432))
    database_uri_candidates=[
        f'postgresql://kskp:{db_password}@localhost:{db_port}/kskp',
        f'postgresql://kskp:{db_password}@db/kskp',
        f'postgresql://kskp:{"J2-pH|%B"}@kskp.cr4gfi5zl5xm.ap-northeast-1.rds.amazonaws.com/kskp'
    ]
    # DBに接続する
    engine = _get_db_engine(database_uri_candidates)

    # テスト用スキーマ名を設定する
    SCHEMA_NAME = _make_test_schema(engine)
    # カレントスキーマを設定する
    # (コミットされると、セッションが終了するまでその設定が持続する)
    sql = f'SET SESSION search_path = {SCHEMA_NAME}; commit;'
    engine.execute(sql)

else:
    # 通常実行時のDB接続先
    database_uri_candidates=[
        f'postgresql://kskp:{db_password}@db/kskp'
    ]
    # DBに接続する
    engine = _get_db_engine(database_uri_candidates)
    # デフォルトスキーマを用いる
    SCHEMA_NAME = None


from .kskp_base_model import KSKPBaseModel
from sqlalchemy.ext.declarative import declarative_base
# ベースモデルにスキーマ名を設定する
KSKPBaseModel.schema_name = SCHEMA_NAME
# SQLAlchemyの全てのモデルクラスのベースモデルを作成する
BaseModel = declarative_base(cls=KSKPBaseModel, constructor=KSKPBaseModel.__init__, name='KSKPBase')

from kskp.core import Datum, Port, Command

from .lock_manager import LockManager, LockedDatumException

# 環境変数からロックの有効期間(分)を取得する
# (設定値がない場合は1時間とする)
lock_expire_minutes = int(os.getenv('LOCK_EXPIRE_MIN', 60))
# LockManagerオブジェクトを作成する
lock_manager = LockManager(60 * lock_expire_minutes)

from .lock_required import lock_required

from .exceptions import (
    NothingToPutbackException,
    NoResultsException,
    OptimisticLockException,
    EditLockedException,
    CommandException,
    GroupBy2Exception,
    ColumnNameException,
    FieldNotFoundException,
    FieldConflictException,
    EmptyFieldException,
    FieldForbiddenCharacterException
)
from .store import Store, NysolModule, ModuleStore, List, ApparentLast
from .database_conn import DatabaseConn
from .remote_folder_conn import RemoteFolderConn
from .mountable import Mountable
from .frame import Frame
# from .cache import Cache
from .flow_data import FlowData
from .flow import Flow
from .folder import Folder
from .project_folder import ProjectFolder
from .awss3 import AwsS3
from .remote_folder import RemoteFolder
from .trashcan import TrashCan
from .vis import Vis, BokehPlotVis
from .datasource import DataSource
from .activity import Activity
from .database import Database
from .children_getter import ChildrenGetter
from .flow_dumper import FlowDumper

from .library import Library
from .store_model import Store as StoreModel

from ..depo.std.commands import CommandLink, CommandsPathLink, CommandsPathFileSource, RunfuncCommand

# factory.data.find_by_uuid()等で参照しているので、
# 管理者ユーザの作成等の処理の前に記述する必要がある
# from sqlalchemy.orm.exc import NoResultFound


# テーブルを作成する
BaseModel.metadata.create_all(bind=engine, checkfirst=True)


from kskp.store.factory import UnAuthzFactory, Factory
with UnAuthzFactory() as unauthz_factory:
    from kskp.store.auth import Role

    # システム管理者とユーザ管理者を作成する
    sys_admin_user = unauthz_factory.load_sys_admin_user()
    usr_admin_user = unauthz_factory.load_usr_admin_user(activate_if_inactive=True)

    with Factory(sys_admin_user) as factory:
        sys_admin_role = factory.role.load_sys_admin_role()
        if sys_admin_user.is_init:
            # システム管理者を新規作成した場合は、システム管理者ロールの一般メンバに加える
            sys_admin_role.join_member(Role.Member(sys_admin_user, owner=False))

    with Factory(usr_admin_user) as factory:
        # ユーザ管理者ロールを作成する
        # (ロールを新規作成した場合は作成者がロールの所有者になる)
        factory.role.load_usr_admin_role()

        # everyoneロールにユーザ管理者を所有者として参加させる
        # (unauthz_factoryからロールを新規追加された場合、作成者はロールに参加されない)
        # (ユーザ管理者ロールを作成した後に処理すること)
        everyone_role = factory.role.load_everyone_role()
        # edit_lock_roleロールにユーザ管理者を所有者として参加させる
        edit_lock_role = factory.role.load_edit_lock_role()
        if usr_admin_user.is_init:
            # ユーザ管理者を新規作成した場合は、ユーザ管理者ロールの所有者メンバに加える
            everyone_role.join_member(Role.Member(usr_admin_user, owner=True))
            # 編集ロックロールの所有者メンバに加える
            edit_lock_role.join_member(Role.Member(usr_admin_user, owner=True))

        # システムフォルダを作成する
        factory.data.load_cache_folder()
        factory.data.load_trash_folder()


from sqlalchemy import event, DDL, exc

@event.listens_for(BaseModel.metadata, 'after_create')
def receive_after_create(target, connection, tables, **kw):
    "listen for the 'after_create' event"

    if 'data' in tables:
        # tables were created.
        create_d_view()

def create_d_view():
    """
    データの一覧を表示するVIEWを作成する
    (開発及び運用時に閲覧するために用意しておく)
    """
    d_view = """
    create view d as
    select id, parent_id, uuid, path, label, type, date_trunc('second', created_at) as created_at
    from data order by type, id
    """
    engine.execute(DDL('drop view if exists d'))
    engine.execute(DDL(d_view))
