import os
from pathlib import Path

def _is_unittest():
    # python3 -m unittestで実行した場合は、is_unittest=Trueとなる
    import sys
    return '__main__' in sys.modules and \
            hasattr(sys.modules['__main__'], '__unittest') and \
            sys.modules['__main__'].__unittest

def _get_test_schema_name():
    # スキーマ名はランダム文字列を命名して他のテスト実行処理とDBスキーマを分ける
    import uuid
    schema_name = 'schema_' + str(uuid.uuid4()).upper()[0:6]
    return schema_name.lower()

def _make_schema(engine, schema_name):
    # スキーマを作成する
    from sqlalchemy import DDL, exc
    try:
        engine.execute(DDL('CREATE SCHEMA IF NOT EXISTS %s' % schema_name))
    except exc.OperationalError as e:
        raise Exception('💲💰テスト実行にはAWS RDSが起動している必要があります💲💰')


if 'DATABASE_URL' in os.environ:
    # HEROKU環境用の設定
    os.environ["SQLALCHEMY_DATABASE_URI"] = os.environ['DATABASE_URL']
elif _is_unittest():
    # テスト環境用の設定
    passwd = 'J2-pH|%B'
    database_uri = "postgresql://kskp:%s@kskp.cr4gfi5zl5xm.ap-northeast-1.rds.amazonaws.com/kskp" % passwd
    os.environ["SQLALCHEMY_DATABASE_URI"] = database_uri
else:
    # ローカル環境用の設定
    os.environ["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:@db/kskp"
    # os.environ["SQLALCHEMY_DATABASE_URI"] = "postgresql://kskp:ZQZtVgL6G32Vy6p6WJtG3C3K84yuJ4zz@db/kskp"

    # ローカルでpostgres専用コンテナを立ち上げる時のコマンド
    # docker run --name postgres -p 5432:5432 -e POSTGRES_USER=dev -e POSTGRES_DB=kskp -e POSTGRES_PASSWORD=secret -d postgres:11.1
    # os.environ["SQLALCHEMY_DATABASE_URI"] = 'postgresql://dev:secret@0.0.0.0:5432/kskp'


# データベースへの接続
# echo=TrueでSQLログがコンソールに出力される
from sqlalchemy import create_engine
# SQLite用
os.environ['SQLITE_PATH'] = os.getenv('SQLITE_PATH', (Path(__file__).parent.parent.parent / 'kskp.db').as_posix())
# os.environ['DATABASE_URI'] = "sqlite:///" + os.environ['SQLITE_PATH']
# check_same_threadをFalseにすることで、sessionをスレッドをまたいで使うことができるようになる（デフォルトはTrue）
# -> PostgreSQLにはこのオプションはない
engine = create_engine(os.environ['SQLALCHEMY_DATABASE_URI'], echo=False)

if _is_unittest():
    # テスト用スキーマ名を設定する
    os.environ['KSKP_POSTGRESQL_SCHEMA_NAME'] = _get_test_schema_name()
    # テスト用スキーマを作成する
    _make_schema(engine, os.environ['KSKP_POSTGRESQL_SCHEMA_NAME'])
    # カレントスキーマを設定する
    # (コミットされると、セッションが終了するまでその設定が持続する)
    sql = """
    SET SESSION search_path = {schema}; commit;
    """.format(schema=os.environ['KSKP_POSTGRESQL_SCHEMA_NAME'])
    engine.execute(sql)

# ベースクラスをつくる
class MyBase(object):
    @property
    def is_base_model(self):
        return True

from sqlalchemy.ext.declarative import declarative_base
BaseModel = declarative_base(cls=MyBase)

from kskp.core import Datum, Port, Command

from .exceptions import NothingToPutbackException, NoResultsException, CommandException, OptimisticLockException, EditLockedException
from .store import Store, NysolModule, ModuleStore, List, ApparentLast
from .database_conn import DatabaseConn
from .remote_folder_conn import RemoteFolderConn
from .mountable import Mountable
from .lock_manager import LockManager, LockedDatumException
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
# from .flows import FlowLink

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


from sqlalchemy import event, DDL

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
