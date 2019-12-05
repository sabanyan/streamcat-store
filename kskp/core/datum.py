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
    # DEFAULT_LIBRARY_PATH = (STORE_DIR / 'frames/csv').relative_to(STORE_DIR.parent.parent).as_posix()
    # DEFAULT_LIBRARY_PATH = (STORE_DIR / 'frames/csv').as_posix()
    DEFAULT_LIBRARY_PATH = 'lib'
    FOLDER_TYPE = 'folder'
    AWSS3_TYPE  = 'awss3'
    RFOLDER_TYPE = 'rfolder'
    DATABASE_TYPE = 'database'
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
    _label      = Column('label', String)
    # PostgreSQLのENUM型の要素を変更してもSQLAlchemyから自動的に変更がかからないので手動で変更する必要がある
    type        = Column(ENUM(FOLDER_TYPE, AWSS3_TYPE, RFOLDER_TYPE, DATABASE_TYPE, FLOW_TYPE, FRAME_TYPE, name='data_type'), nullable=False)
    data        = Column(JSONB)
    creator     = Column(INTEGER)
    modifier    = Column(INTEGER)
    created_at  = Column(TIMESTAMP, default=text('statement_timestamp()'))
    modified_at = Column(TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()'))

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
            rel_parent_path = self._to_rel_path(parent._path)
            self._path = os.path.join(rel_parent_path, dir_name)

        # label
        self._label = Datum.escape_label(label)

        # type
        self.type = datum_type

        # creator, modifier
        self.creator = creator
        self.modifier = creator

        self.context = {}


    @property
    def path(self):
        from kskp.store import Mountable

        if self._path == '':
            return None

        if os.path.exists(self._path):
            # ここで_pathがマウントポイントで、かつUnmount状態のとき、そのまま_pathを返してしまうと、
            # children_getter._synchronize()によりS3バケットが空になってしまうので以下の場合分けを行う
            if os.path.isdir(self._path):
                if isinstance(self, Mountable):
                    # _pathがディレクトリで、かつマウントポイントの場合、再マウント処理をする
                    Mountable.remount(self.id)
                    # return Path(self._path)
                else:
                    # _pathがディレクトリで、かつマウントポイントでない場合は、再マウント処理はしない
                    # return Path(self._path)
                    pass
            else:
                # _pathが(ディレクトリでない)ファイルで、かつ存在する場合は、再マウント処理はしない
                # return Path(self._path)
                pass
        else:
            if self.id is None:
                # 再マウント処理ができない場合
                # return Path(self._path)
                pass
            else:
                # pathに対応するファイルまたはディレクトリが無い場合、再マウント処理する
                Mountable.remount(self.id)
                if not os.path.exists(self._path):
                    # 再マウント処理をしてもファイルまたはディレクトリがない場合は、例外を送出する
                    # (ここで例外を送出するとexists(path)で存在チェックができなくなる)
                    # raise Exception('No file or directory of the path property exists.')
                    pass
                # return Path(self._path)
                pass

        # 必ず相対pathを返す
        return Path(self._to_rel_path(self._path))

    @path.setter
    def path(self, path):
        # Pathオブジェクトを受け取る
        self._path = path.as_posix()

    @property
    def path_exists(self):
        path = self._to_abs_path(self._path)
        return os.path.exists(path)

    @property
    def label(self):
        if self._label is None or self._label == '':
            return self.data2['label'] or ''
        else:
            return self._label

    @property
    def data2(self):
        import json
        try:
            # data列の後方互換性
            ret = json.loads(self.data, encoding='utf-8')
        except Exception as e:
            ret = self.data
        return ret

    @property
    def content(self):
        """
        Engineから参照する
        """
        return self

    @property
    def created_at_str(self):
        # DBに格納されている日時はUTCなので、タイムゾーンをUTCに設定する
        created_at_utc = self.created_at.replace(tzinfo=datetime.timezone.utc)
        # UTC日時はここで現地時間(環境変数TZの値)に設定される
        created_at_local = created_at_utc.astimezone()
        return created_at_local.strftime('%Y-%m-%d %H:%M:%S')

    def move(self, parent_uuid, modifier):
        """
        指定されたStoreの直下に移動する
        """
        # UUID値の形式チェックをする
        Datum.valid_uuid_or_raise(parent_uuid)

        try:
            from kskp.store import Folder
            to_folder = Folder.find_by_uuid(parent_uuid)
        except Exception as e:
            raise Exception('移動先の指定はフォルダのUUIDしか許可していません')

        # 移動対象がマウントポイントの場合は、path列を変更することはマウントポイントを変更することになるので
        # とりあえずエラーとする
        from kskp.store import Mountable
        if isinstance(self, Mountable):
            raise Exception('マウントポイントフォルダを移動することはできません')

        if parent_uuid == self.uuid:
            raise Exception('移動先と移動元の指定が同じです')

        # 移動先が移動元フォルダの配下になる場合は例外を送出する
        if self.type == Datum.FOLDER_TYPE:
            pass

        # ファイルを移動する
        old_path = self._path
        new_path = os.path.join(to_folder._path, os.path.basename(self._path))
        new_path = Datum.move_file(old_path, new_path)
        new_label = Datum.get_another_label_name(self.label, self.parent_uuid, except_uuid=self.uuid)

        try:
            # ファイル名の移動によって他のDatumのpathが変更が必要であれば変更する
            Datum.update_same_path(old_path, new_path, modifier)
            if isinstance(self, Folder):
                Datum.update_include_path(old_path, new_path, modifier)
            # レコードを更新する
            session.query(Datum).filter(Datum.id==self.id).update({'parent_id': to_folder.id
                                                                  ,'_path'    : new_path
                                                                  ,'_label'   : new_label
                                                                  ,'modifier' : modifier})
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.commit()

        return self

    @staticmethod
    def update_same_path(old_path, new_path, modifier):
        # 同じファイルに対応するフォルダのpath列を、ファイル名の移動に合わせて変更する
        rel_old_path = Datum._to_rel_path(old_path)
        abs_old_path = Datum._to_abs_path(old_path)
        from sqlalchemy import or_
        session.query(Datum).filter(or_(Datum._path == rel_old_path, \
                                        Datum._path == abs_old_path)).update({'_path'   : new_path
                                                                            , 'modifier': modifier})
    @staticmethod
    def update_include_path(old_path, new_path, modifier):
        # 同じディレクトリを含むpath列を、ディレクトリの移動に合わせて変更する
        rel_old_path = Datum._to_rel_path(old_path)
        abs_old_path = Datum._to_abs_path(old_path)
        from sqlalchemy import or_
        results = session.query(Datum.id, Datum._path)\
                         .filter(Datum.type!=Datum.FLOW_TYPE)\
                         .filter(or_(Datum._path.like(rel_old_path + '/%'),\
                                     Datum._path.like(abs_old_path + '/%'))).all()
        import re
        for result in results:
            if result._path.startswith('/'):
                replaced_path = re.sub('^'+abs_old_path, new_path, result._path)
            else:
                replaced_path = re.sub('^'+rel_old_path, new_path, result._path)
            session.query(Datum).filter(Datum.id==result.id).update({'_path'   : replaced_path
                                                                    ,'modifier': modifier})

    @staticmethod
    def _to_abs_path(path):
        if path.startswith('/'):
            return path
        else:
            # return (STORE_DIR.parent / path).as_posix()
            return (STORE_DIR / path).as_posix()

    @staticmethod
    def _to_rel_path(path):
        if path.startswith('/'):
            # ディレクトリトラバーサルには対応していない
            return Path(path).relative_to(STORE_DIR).as_posix()
        else:
            return path

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
                        .order_by(Datum.type, desc(Datum.created_at)).all()
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
    def find_by_parent_uuid_and_label(parent_uuid, label):
        """
        指定したuuidの親と指定したラベル名のレコードを全て取得する
        """
        from sqlalchemy import desc

        # UUID値の形式チェックをする
        Datum.valid_uuid_or_raise(parent_uuid)

        f2 = aliased(Datum)
        sub_query = session.query(f2)
        datum = session.query(Datum)\
                        .filter(sub_query.filter(f2.id==Datum.parent_id)
                                         .filter(f2.uuid==parent_uuid).exists())\
                        .filter(Datum._label==label)\
                        .order_by(Datum.type, desc(Datum.created_at)).all()
        return datum

    @staticmethod
    def get_flow_uuids_using_other_datum(datum_uuid):
        """      .......
        指定されたDatumのuuidを参照するFlowを取得する
        """
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
        if old_path is None or old_path == '':
            raise Exception('move_file(): 移動元のファイルパスが指定されていません')
        if new_path is None or new_path == '':
            raise Exception('move_file(): 移動先のファイルパスが指定されていません')
        
        try:
            # 同じ名称のファイルが既に存在する場合、末尾に数字を付加したファイル名で作成する
            new_path = Datum.get_another_file_path(new_path, except_path=old_path)
            # ファイルを移動する
            if os.path.exists(Datum._to_abs_path(old_path)):
                os.rename(Datum._to_abs_path(old_path), Datum._to_abs_path(new_path))
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
    def escape_label(label):
        if label is None:
            return label
        # '\0'は少なくともPostgreSQLのVARCHARに格納できない
        trans_table = str.maketrans({'\0' : ''})
        return label.translate(trans_table)

    @staticmethod
    def get_user_name_by_user_id(user_id):
        """
        FIXIT: usersテーブルへのアクセスはSQLAlchemyを用いる予定なので、以下のコードは暫定実装である
        """
        from ..store.model import get_user_by_id
        user = get_user_by_id(user_id)
        if user is None:
            Exception('No user is found by designated user id')
        else:
            return user['name']

    @staticmethod
    def get_another_file_path(path, except_path=None):
        """
        同じ名称のファイルが既に存在する場合、末尾に数字を付加したファイル名で作成する
        except_path : 存在チェックを除外するファイル名
        """
        while os.path.exists(Datum._to_abs_path(path)) and path != except_path:
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
    def get_another_label_name(label, parent_uuid, except_uuid=None):
        """
        指定する親データストア内で、同じ名称のラベルがすでにある場合、末尾に数字を付加したラベル名を返す
        """
        children = Datum.find_by_parent_uuid(parent_uuid)
        while Datum._label_exists_in_Data(label, children, except_uuid):
            # 後ろから1番目の'_'でラベル名を区切る
            label_elems = label.rsplit('_', 1)
            if len(label_elems) == 2 and label_elems[1].isdecimal():
                nextNumber = int(label_elems[1]) + 1
                label = label_elems[0] + '_' + str(nextNumber)
            else:
                # 開始番号は1を飛び越して2?!
                label = label + '_2'
        return label

    @staticmethod
    def _label_exists_in_Data(label, data, except_uuid):
        """
        dataの中にlabelを使用しているdatumがあればTrueを返す
        """
        import json
        for datum in data:
            if datum.label == label and (except_uuid is None or datum.uuid != except_uuid):
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
        if uuid is None or uuid == '':
            raise Exception(f'The UUID value is empty')
        if not Datum.is_valid_uuid(uuid):
            raise Exception(f'The UUID({uuid}) value is not valid format.')
