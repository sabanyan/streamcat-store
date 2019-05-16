# import sqlalchemy
# from flask import Flask, session, jsonify
# from flask_sqlalchemy import SQLAlchemy

# ToDo: Flask-SqlAlchemyからFlaskを分離する
# app = Flask('kskp/library')

# from .. import app

# app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:@db/kskp"
# app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://tanakahiroshi:@localhost/kskp"
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data/kskp_alchemy.db"
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///kskp/data/kskp.db"
# 起動時のWarningを抑制するため以下の設定値をTrueにする
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
# db = SQLAlchemy(app)

FRAME_FOLDER_UUID = 'fffffd73-75d7-440f-b459-b49b3449d655'
FRAME_FOLDER_LABEL = 'フロー実行結果'
CACHE_FOLDER_UUID = 'ccd66c48-f69a-4a7d-8855-9faec4eafccf'
CACHE_FOLDER_LABEL = 'フロー実行キャッシュ'

# データベースへの接続
# echo=TrueでSQLログがコンソールに出力される
from sqlalchemy import create_engine
engine = create_engine("sqlite:///kskp/data/kskp.db", echo=False)
# ベースクラスをつくる
from sqlalchemy.ext.declarative import declarative_base
BaseModel = declarative_base()
# セッションをつくる
from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)
session = Session()

from .store import Store
from .datum import Datum
from .folder import Folder
from .frame import Frame
from .library import Library


# テーブルを作成する
BaseModel.metadata.create_all(bind=engine, checkfirst=True)

# from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID, JSONB, ENUM

# フレームを格納するフォルダがなければ作成する
Library._init_library_folders()



# # 最初にアクセスが発生した時にのみ実行される
# @app.before_first_request
# def session_setup():
#     # SQLAlchemyで使用するテーブルが存在しない場合は作成する
#     db.create_all()
