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
        from sqlalchemy import create_engine, select
        from sqlalchemy.exc import OperationalError
        try:
            # DBに接続する
            # echo=TrueでSQLログがコンソールに出力される
            engine = create_engine(database_uri, echo=False, future=True)
            # engine.begin()  : close()でCOMMITを発行する
            # engine.connect(): close()でROLLBACKを発行する
            with engine.connect() as conn:
                # DBへの接続を確認する (SELECT 1)
                conn.execute(select(1))
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
        from sqlalchemy import inspect, exc
        from sqlalchemy.schema import CreateSchema
        # スキーマが既に作成ずみならば作成しない
        if inspect(engine).get_sequence_names(schema=schema_name):
            return
        try:
            with engine.begin() as conn:
                conn.execute(CreateSchema(schema_name))
        except exc.OperationalError as e:
            raise Exception('テストケース実行で使用するデータベーススキーマを作成できませんでした')

    # テスト用スキーマ名を設定する
    test_schema_name = _get_test_schema_name()
    # テスト用スキーマを作成する
    _create_schema(engine, test_schema_name)
    return test_schema_name

# バージョンを取得する
from pathlib import Path
_streamcat_ver_file = Path('/etc/streamcat_ver')
if _streamcat_ver_file.exists() and _streamcat_ver_file.stat().st_size < 20:
    STREAMCAT_VER = _streamcat_ver_file.read_text(errors='ignore').strip()
else:
    STREAMCAT_VER = None

_db_password = 'ZQZtVgL6G32Vy6p6WJtG3C3K84yuJ4zz'

if _is_unittest():
    # テストスクリプト実行時のDB接続先
    db_port = int(os.getenv('STREAMCAT_DB_PORT', 5432))
    database_uri_candidates=[
        f'postgresql://streamcat:{_db_password}@localhost:{db_port}/streamcat?application_name=StreamCat-Test',
        f'postgresql://streamcat:{_db_password}@db/streamcat?application_name=StreamCat-Test',
        f'postgresql://kskp:{"J2-pH|%B"}@kskp.cr4gfi5zl5xm.ap-northeast-1.rds.amazonaws.com/kskp?application_name=StreamCat-Test'
    ]
    # DBに接続する
    engine = _get_db_engine(database_uri_candidates)
    # テスト用スキーマ名を設定する
    SCHEMA_NAME = _make_test_schema(engine)
    # デフォルトのスキーマを設定したengineを作成する
    engine = engine.execution_options(schema_translate_map={None: SCHEMA_NAME})

else:
    # 通常実行時のDB接続先
    database_uri_candidates=[
        f'postgresql://streamcat:{_db_password}@db/streamcat?connect_timeout=10&application_name=StreamCat'
    ]
    # DBに接続する
    engine = _get_db_engine(database_uri_candidates)
    # デフォルトスキーマを用いる
    SCHEMA_NAME = None

#
# TODO: 後方互換性を保つためにprev_parent_id列がない場合は列を追加する
#
try:
    from sqlalchemy import DDL
    alter_sql = DDL(f'ALTER TABLE data ADD COLUMN IF NOT EXISTS prev_parent_id INTEGER;')
    with engine.begin() as conn:
        conn.execute(alter_sql)
except:
    pass

#
# TODO: 後方互換性を保つためにissuerとsubject列がない場合は列を追加する
try:
    from sqlalchemy import DDL
    alter_sql = DDL(f'ALTER TABLE users ADD COLUMN IF NOT EXISTS issuer VARCHAR;')
    with engine.begin() as conn:
        conn.execute(alter_sql)
    alter_sql = DDL(f'ALTER TABLE users ADD COLUMN IF NOT EXISTS subject VARCHAR;')
    with engine.begin() as conn:
        conn.execute(alter_sql)
except:
    pass

from .scat_base_model import SCatBaseModel
from sqlalchemy.ext.declarative import declarative_base
# ベースモデルにスキーマ名を設定する
SCatBaseModel.schema_name = SCHEMA_NAME

# SQLAlchemyの全てのモデルクラスのベースモデルを作成する
BaseModel = declarative_base(cls=SCatBaseModel, constructor=SCatBaseModel.__init__, name='StreamCatBase')

from .savable_datum import SavableDatum
from .runnable import Command, Port, Parameter
from .tmp import Tmp
from .constraints import Constraints
