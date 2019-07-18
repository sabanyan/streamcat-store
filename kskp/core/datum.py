"""
いわゆるルートクラスであるDatumを定義している
"""
import os
import uuid
import random
import platform
import datetime
from kskp.library import BaseModel, session, STORE_DIR
from pathlib import Path
from sqlalchemy.orm import aliased
from sqlalchemy import Column, Integer, String, text

class Datum(BaseModel):
    """
    KSKPで扱う対象を扱ううち、「第一級」であるものの頂点のクラス。
    """
    # テーブル名の定義
    __tablename__ = 'data'

    # 列名と列のデータ型等の定義
    id          = Column(String, primary_key=True)
    parent_id   = Column(String)
    uuid        = Column(String, nullable=False, unique=True)
    path        = Column(String, nullable=False)
    type        = Column(String, nullable=False)
    data        = Column(String, nullable=False)
    creator     = Column(Integer)
    modifier    = Column(Integer)
    created_at  = Column(String, default=text('CURRENT_TIMESTAMP'))
    modified_at = Column(String, default=text('CURRENT_TIMESTAMP'))

    MAX_DATUM_ID = 9000000000000000000
    # TODO: とりあえずFrameだけ
    # csv以外も出た時は改めて考えねば
    DEFAULT_LIBRARY_PATH = (STORE_DIR / 'frames/csv').as_posix()
    FRAME_TYPE = 'frame'
    FOLDER_TYPE = 'folder'

    def __init__(self, parent_uuid, datum_type, label, creator=None, modifier=None):
        """
        コンストラクタ
        """
        # SQLiteではidは乱数で採番する
        self.id = random.randint(0, self.MAX_DATUM_ID)

        # parent_uuidからparent_idを取得する
        if parent_uuid is None:
            parent = None
        else:
            parent = session.query(Datum.id, Datum.path)\
                               .filter(Datum.uuid==parent_uuid).one_or_none()
            if parent is None:
                raise Exception('No parent folder is found!')
            else:
                self.parent_id = parent.id

        # UUIDを採番する
        self.uuid = str(uuid.uuid4())

        # pathは親フォルダのpathを引き継ぐ
        if parent is None:
            # 親フォルダがない場合はデフォルトパスとする
            self.path = self.DEFAULT_LIBRARY_PATH
        else:
            dir_name = Datum.escape_filename(label)
            self.path = os.path.join(parent.path, dir_name)

        # type
        self.type = datum_type

        # creator, modifier
        self.creator = creator
        self.modifier = modifier

        self.context = {}

    @property
    def path_obj(self):
        if self.path is None:
            raise Exception('path attribute must not be None in path_obj property.')
        return Path(self.path)

    @path_obj.setter
    def path_obj(self, value):
        if value is None:
            raise Exception('setting value must not be None in path_obj property.')
        self.path = value.as_posix()

    @staticmethod
    def find_root():
        """
        親を持たないfolderレコードを全て取得する
        """
        roots = session.query(Datum).filter(Datum.parent_id == None).all()

        if len(roots) == 0 :
            # ルートフォルダがない場合はNoneを返す
            return None
        elif len(roots) > 1:
            raise Exception('More than 2 roots exist!!')

        return roots[0]

    @staticmethod
    def count_root():
        return session.query(Datum).filter(Datum.parent_id == None).count()

    @staticmethod
    def find_by_parent_uuid(parent_uuid):
        """
        指定されたuuidの親をもつDatumレコードを全て取得する
        """
        f2 = aliased(Datum)
        sub_query = session.query(f2)
        datum = session.query(Datum) \
                          .filter(sub_query.filter(f2.id==Datum.parent_id)
                                           .filter(f2.uuid==parent_uuid).exists()).all()
        return datum

    @staticmethod
    def move_file(old_path, new_path):
        """
        ドキュメントまたはフォルダに対応するファイルまたはディレクトリを移動する
        """
        try:
            # 同じ名称のファイルが既に存在する場合、末尾に数字を付加したファイル名で作成する
            new_path = Datum.get_another_file_path(new_path, except_path=old_path)
            # ファイルを移動する
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
                return new_path
            else:
                return old_path
        except PermissionError as e:
            # ファイルに対する権限がない場合
            raise e

    # @staticmethod
    # def lock():
    #     session.execute("PRAGMA main.locking_mode = EXCLUSIVE")

    # @staticmethod
    # def unlock():
    #     session.execute("PRAGMA main.locking_mode = NORMAL")

    @staticmethod
    def escape_filename(filename):
        # '/'と'\0'はunixとmacOSではファイル名に使用できない
        trans_table = str.maketrans({'/' : '／', '\0' : ''})
        return filename.translate(trans_table)

    @staticmethod
    def get_user_name_by_user_id(user_id):
        """
        FIXIT: usersテーブルへのアクセスはSQLAlchemyを用いる予定なので、以下のコードは暫定実装である
        """
        # from ..model import get_user_by_id
        # user = get_user_by_id(user_id)
        # if user is None:
        #     Exception('No user is found by designated user id')
        # else:
        #     return user['name']
        return '開発者'

    @staticmethod
    def get_another_file_path(path, except_path=None):
        """
        同じ名称のファイルが既に存在する場合、末尾に数字を付加したファイル名で作成する
        except_path : 存在チェックを除外するファイル名
        """
        while os.path.exists(path) and path != except_path:
            filename = os.path.basename(path)
            dirname = os.path.dirname(path)
            new_filename = Datum._get_another_file_name(filename)
            path = os.path.join(dirname, new_filename)
        return path

    @staticmethod
    def _get_another_file_name(filename):
        """
        ファイル名の末尾に'_1'を付加する、既に'_数字'が末尾にある場合は数字をインクリメントする。
        """
        (body, ext) = os.path.splitext(filename)
        # 後ろから1番目の'_'でファイル名を区切る
        bodylist = body.rsplit('_', 1)

        # isdecimal()は全角数字もTrueになる
        if len(bodylist) == 2 and bodylist[1].isdecimal():
            nextNumber = int(bodylist[1]) + 1
            return bodylist[0] + '_' + str(nextNumber) + ext
        else:
            return body + '_1' + ext

    @staticmethod
    def get_uuid_by_id(id):
        result = session.query(Datum.uuid).filter(Datum.id==id).one_or_none()
        if result is None:
            Exception('No datum is found by designated id')
        else:
            return result.uuid

    @staticmethod
    def get_current_time_str():
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
