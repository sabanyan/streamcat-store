"""
いわゆるルートクラスであるDatumを定義している
"""
import os
import uuid
import random
import platform
import datetime
from kskp.store import BaseModel, ss as session
from kskp.store import STORE_DIR
from pathlib import Path
from sqlalchemy.orm import aliased
from sqlalchemy import Column, Integer, String, text
from sqlalchemy.dialects.postgresql import INTEGER, TIMESTAMP, JSONB, ENUM, UUID

class Datum(BaseModel):
    """
    KSKPで扱う対象を扱ううち、「第一級」であるものの頂点のクラス。
    """
    # TODO: とりあえずFrameだけ
    # csv以外も出た時は改めて考えねば
    DEFAULT_LIBRARY_PATH = (STORE_DIR / 'frames/csv').as_posix()
    # DEFAULT_LIBRARY_PATH = (STORE_DIR / 'frames/csv').relative_to(STORE_DIR.parent.parent).as_posix()
    AWSS3_TYPE  = 'awss3'
    FOLDER_TYPE = 'folder'
    FLOW_TYPE   = 'flow'
    FRAME_TYPE  = 'frame'

    # テーブル名の定義
    __tablename__ = 'data'

    # 定義先スキーマ
    if 'KSKP_POSTGRESQL_SCHEMA_NAME' in os.environ:
        # テスト環境用のスキーマ
        __table_args__ = {'schema': os.environ['KSKP_POSTGRESQL_SCHEMA_NAME']}

    # 列名と列のデータ型等の定義
    id          = Column(INTEGER, primary_key=True, autoincrement=True)
    parent_id   = Column(INTEGER)
    uuid        = Column(UUID, nullable=False, unique=True)
    _path       = Column('path', String, nullable=False)
    # PostgreSQLのENUM型の要素を変更してもSQLAlchemyから自動的に変更がかからないので手動で変更する必要がある
    type        = Column(ENUM(AWSS3_TYPE, FOLDER_TYPE, FLOW_TYPE, FRAME_TYPE, name='data_type'), nullable=False)
    data        = Column(JSONB, nullable=False)
    creator     = Column(INTEGER)
    modifier    = Column(INTEGER)
    created_at  = Column(TIMESTAMP, default=text('CURRENT_TIMESTAMP'))
    modified_at = Column(TIMESTAMP, default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'))

    def __init__(self, parent_uuid, datum_type, label, creator=None):
        """
        コンストラクタ
        """
        # parent_uuidからparent_idを取得する
        if parent_uuid is None:
            parent = None
        else:
            # UUID値の形式チェックをする
            Datum.valid_uuid_or_raise(parent_uuid)
            parent = session.query(Datum.id, Datum._path)\
                            .filter(Datum.uuid==parent_uuid).one_or_none()
            if parent is None:
                raise Exception('No parent folder is found!')
            else:
                self.parent_id = parent.id
                self.parent_uuid = parent_uuid

        # UUIDを採番する
        self.uuid = str(uuid.uuid4())

        # pathは親フォルダのpathを引き継ぐ
        if parent is None:
            # 親フォルダがない場合はデフォルトパスとする
            self._path = self.DEFAULT_LIBRARY_PATH
        else:
            dir_name = Datum.escape_filename(label)
            self._path = os.path.join(parent._path, dir_name)

        # type
        self.type = datum_type

        # creator, modifier
        self.creator = creator
        self.modifier = creator

        self.context = {}


    @property
    def path(self):
        path_obj = self.path_obj
        if path_obj.exists():
            # ここで_pathがマウントポイントで、かつUnmount状態のとき、そのまま_pathを返してしまうと、
            # children_getter._synchronize()によりS3バケットが空になってしまうので以下の場合分けを行う
            if path_obj.is_dir():
                if self.type == Datum.AWSS3_TYPE:
                    # _pathがディレクトリで、かつマウントポイントの場合、再マウント処理をする
                    Datum.remount(self.id)
                    return self._path
                else:
                    # _pathがディレクトリで、かつマウントポイントでない場合は、再マウント処理はしない
                    return self._path
            else:
                # _pathが(ディレクトリでない)ファイルで、かつ存在する場合は、再マウント処理はしない
                return self._path
        else:
            if self.id is None:
                # 再マウント処理ができない場合
                return self._path
            # pathに対応するファイルまたはディレクトリが無い場合、再マウント処理する
            Datum.remount(self.id)
            if not path_obj.exists():
                # 再マウント処理をしてもファイルまたはディレクトリがない場合は、例外を送出する
                # (ここで例外を送出するとexists(path)で存在チェックができなくなる)
                # raise Exception('No file or directory of the path property exists.')
                pass
            return self._path

    @path.setter
    def path(self, value):
        self._path = value

    @property
    def path_obj(self):
        if self._path is None:
            raise Exception('path attribute must not be None in path_obj property.')
        return Path(self._path)

    @path_obj.setter
    def path_obj(self, value):
        if value is None:
            raise Exception('setting value must not be None in path_obj property.')
        self._path = value.as_posix()

    @property
    def created_at_str(self):
        created_at_utc = self.created_at.astimezone(datetime.timezone.utc)
        created_at_local = created_at_utc.astimezone()
        return created_at_local.strftime('%Y-%m-%d %H:%M:%S')

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
        from sqlalchemy import desc

        # UUID値の形式チェックをする
        Datum.valid_uuid_or_raise(parent_uuid)

        f2 = aliased(Datum)
        sub_query = session.query(f2)
        datum = session.query(Datum)\
                        .filter(sub_query.filter(f2.id==Datum.parent_id)
                                         .filter(f2.uuid==parent_uuid).exists())\
                        .order_by(Datum.type,desc(Datum.created_at)).all()
        return datum

    @staticmethod
    def find_parent(uuid):
        """
        指定したuuidの親を取得する
        """
        # UUID値の形式チェックをする
        Datum.valid_uuid_or_raise(uuid)

        f2 = aliased(Datum)
        sub_query = session.query(f2)
        return session.query(Datum)\
                      .filter(sub_query.filter(f2.parent_id==Datum.id)
                                       .filter(f2.uuid==uuid).exists()).one_or_none()

    @staticmethod
    def get_flow_uuids_using_other_datum(datum_uuid):
        """      .......
        指定されたDatumのuuidを参照するFlowを取得する
        """
        # FIXIT : PostgreSQLのJSONB演算子が何故か機能しない、誰か教えてください。
        sql = """
        select uuid from data
        where type='flow'
          and to_tsvector(data) @@ to_tsquery('{datum_uuid}')
        """.format(datum_uuid=str(datum_uuid))
        # SQLを発行する
        results = session.execute(sql)
        return [str(result[0]) for result in results]

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
    def get_another_label_name(label, parent_uuid):
        """
        指定する親データストア内で、同じ名称のラベルがすでにある場合、末尾に数字を付加したラベル名を返す
        """
        children = Datum.find_by_parent_uuid(parent_uuid)
        while Datum._label_exists_in_Data(label, children):
            if label[-1:].isdecimal():
                nextNumber = int(label[-1:]) + 1
            else:
                # 開始番号は1を飛び越して2?!
                nextNumber = 2
            label = label + str(nextNumber)
        return label

    @staticmethod
    def _label_exists_in_Data(label, data):
        """
        dataの中にlabelを使用しているdatumがあればTrueを返す
        """
        import json
        for datum in data:
            datum_data = json.loads(datum.data, encoding='utf-8')
            if 'label' in datum.data:
                if datum_data['label'] == label:
                    return True
        return False

    @staticmethod
    def get_uuid_by_id(id):
        result = session.query(Datum.uuid).filter(Datum.id==id).one_or_none()
        if result is None:
            Exception('No datum is found by designated id')
        else:
            return result.uuid

    @staticmethod
    def is_valid_uuid(uuid):
        """
        uuidの形式チェック
        """
        if uuid is None:
            return False
        import re
        return re.match("[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}", uuid)

    @staticmethod
    def valid_uuid_or_raise(uuid):
        """
        uuidの形式チェックの結果、正しくないuuidの場合は例外を送出する
        """
        if not Datum.is_valid_uuid(uuid):
            raise Exception(
                'The value is not UUID type. The comparison to UUID type column needs for uuid value in PostgreSQL.')

    @staticmethod
    def remount(id):
        """
        ルートデータストアから指定されたidのDatumまでの経路において、
        マウントされていないマウントポイントがあればマウントし直す
        """
        sql = """
        WITH RECURSIVE R AS (
            SELECT id, parent_id, uuid, type, path FROM data WHERE id = {id}
            UNION ALL
            SELECT D.id, D.parent_id, D.uuid, D.type, D.path FROM data D JOIN R ON D.id = R.parent_id
        )
        SELECT uuid, path FROM R
        WHERE type = 'awss3'
        ORDER BY id
        """.format(id=id)
        try:
            results = session.execute(sql)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.commit()

        for result in results:
            mount_point_dir = result[1]
            if not Datum.is_mount(Path(mount_point_dir)):
                uuid = str(result[0])
                from kskp.store import AwsS3
                awss3 = AwsS3.find_by_uuid(uuid)
                awss3.mount()

    @staticmethod
    def is_mount(path_obj):
        """
        Check if this path is a POSIX mount point
        """
        # Need to exist and be a dir
        if not path_obj.exists() or not path_obj.is_dir():
            return False

        parent = Path(path_obj.parent)
        try:
            parent_dev = parent.stat().st_dev
        except OSError:
            return False

        dev = path_obj.stat().st_dev
        if dev != parent_dev:
            return True
        ino = path_obj.stat().st_ino
        parent_ino = parent.stat().st_ino
        return ino == parent_ino
