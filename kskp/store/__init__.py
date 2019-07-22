import os
from pathlib import Path


FRAME_FOLDER_UUID = 'fffffd73-75d7-440f-b459-b49b3449d655'
FRAME_FOLDER_LABEL = 'フロー実行結果'
CACHE_FOLDER_UUID = 'ccd66c48-f69a-4a7d-8855-9faec4eafccf'
CACHE_FOLDER_LABEL = 'フロー実行キャッシュ'

# フローがDBに保存されるようになるまでは下記のパスをstoreが持っておく
STORE_DIR = Path(__file__).parent.parent / 'store'
FLOW_PATH = (STORE_DIR / 'flows/json').as_posix()

# データベースへの接続
# echo=TrueでSQLログがコンソールに出力される
from sqlalchemy import create_engine
# SQLite用
os.environ['SQLITE_PATH'] = os.getenv('SQLITE_PATH', (STORE_DIR / 'kskp.db').as_posix())
os.environ['DATABASE_URI'] = "sqlite:///" + os.environ['SQLITE_PATH']
# check_same_threadをFalseにすることで、sessionをスレッドをまたいで使うことができるようになる（デフォルトはTrue）
engine = create_engine(os.environ['DATABASE_URI'], connect_args={'check_same_thread': False}, echo=False)

# ベースクラスをつくる
from sqlalchemy.ext.declarative import declarative_base
BaseModel = declarative_base()
# セッションをつくる
from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)
# 変数名がsessionだとwebでimportした時にflaskのsessionと被るので、一応ssにしている
ss = Session()

# テーブルを作成する
BaseModel.metadata.create_all(bind=engine, checkfirst=True)

from kskp.core import Datum, Port, Command

from .store import Store, FrameStore, NysolModule, ModuleStore
from .frame import Frame, Cache
from .folder import Folder

from .library import Library
from .store_model import Store as StoreModel
from .flows import FlowLink
from .commands import CommandLink, CommandsPathLink, CommandsPathFileSource, RunfuncCommand
from .model import *

# フレームを格納するフォルダがなければ作成する
import pprint
pprint.pprint('Init library folder')
Library._init_library_folders()
