import os
from pathlib import Path


FRAME_FOLDER_UUID = 'fffffd73-75d7-440f-b459-b49b3449d655'
FRAME_FOLDER_LABEL = 'フロー実行結果'
CACHE_FOLDER_UUID = 'ccd66c48-f69a-4a7d-8855-9faec4eafccf'
CACHE_FOLDER_LABEL = 'フロー実行キャッシュ'
DEFAULT_FLOW_FOLDE_UUID = '32b859c1-5268-4075-9b28-8514d180a508'
DEFAULT_FLOW_FOLDE_LABEL = '新しいフローフォルダ'
RESQUE_FLOW_FOLDER_UUID = '4e946b0d-90ab-4a14-aa29-e77e37d126ad'
RESQUE_FLOW_FOLDER_LABEL = '御救いフローフォルダ'

# フローがDBに保存されるようになるまでは下記のパスをstoreが持っておく
STORE_DIR = Path(__file__).parent.parent / 'store'
FLOW_PATH = (STORE_DIR / 'flows/json').as_posix()


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



# データベースへの接続
# echo=TrueでSQLログがコンソールに出力される
from sqlalchemy import create_engine
# SQLite用
# os.environ['SQLITE_PATH'] = os.getenv('SQLITE_PATH', (STORE_DIR / 'kskp.db').as_posix())
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
from sqlalchemy.ext.declarative import declarative_base
BaseModel = declarative_base()
# セッションをつくる
from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)
# 変数名がsessionだとwebでimportした時にflaskのsessionと被るので、一応ssにしている
ss = Session()

from kskp.core import Datum, Port, Command

from .store import Store, FrameStore, NysolModule, ModuleStore
from .frame import Frame, Cache
from .flow import Flow
from .folder import Folder
from .awss3 import AwsS3

from .library import Library
from .store_model import Store as StoreModel
from .flows import FlowLink
from .commands import CommandLink, CommandsPathLink, CommandsPathFileSource, RunfuncCommand
from .model import *

# テーブルを作成する
BaseModel.metadata.create_all(bind=engine, checkfirst=True)

# フレームを格納するフォルダがなければ作成する
import pprint
pprint.pprint('Init library folder')
Library._init_library_folders()
