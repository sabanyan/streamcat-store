"""
いわゆるルートクラスであるDatumを定義している
"""
import os
from pathlib import Path
from kskp.store import BaseModel
from sqlalchemy import Column, Integer, String, text, select
from sqlalchemy.orm import column_property, query_expression
from sqlalchemy.dialects.postgresql import INTEGER, TIMESTAMP, JSONB, ENUM, UUID

class Datum(BaseModel):
    """
    KSKPで扱う対象を扱ううち、「第一級」であるものの頂点のクラス。
    """
    # TODO: とりあえずFrameだけ
    # csv以外も出た時は改めて考えねば
    # DEFAULT_LIBRARY_PATH = (STORE_DIR / 'frames/csv').relative_to(STORE_DIR.parent.parent).as_posix()
    # DEFAULT_LIBRARY_PATH = (STORE_DIR / 'frames/csv').as_posix()
    DEFAULT_LIBRARY_PATH = 'cmn'
    FOLDER_TYPE = 'folder'
    PROJECT_TYPE = 'project'
    AWSS3_TYPE  = 'awss3'
    RFOLDER_TYPE = 'rfolder'
    DATABASE_TYPE = 'database'
    FLOW_TYPE   = 'flow'
    FRAME_TYPE  = 'frame'
    TRASH_TYPE = 'trash'

    # Datum.pathの基点ディレクトリ
    STORE_DIR = Path(__file__).parent.parent / 'depo/files'

    # テーブル名の定義
    __tablename__ = 'data'

    # 定義先スキーマ
    if 'KSKP_POSTGRESQL_SCHEMA_NAME' in os.environ:
        # テスト環境用のスキーマ
        __table_args__ = {'schema': os.environ['KSKP_POSTGRESQL_SCHEMA_NAME']}

    # 列名と列のデータ型等の定義
    id           = Column(INTEGER, primary_key=True, autoincrement=True)
    parent_id    = Column(INTEGER)
    uuid         = Column(UUID, nullable=False, unique=True)
    _path        = Column('path', String, nullable=False)
    _label       = Column('label', String)
    # PostgreSQLのENUM型の要素を変更してもSQLAlchemyから自動的に変更がかからないので手動で変更する必要がある
    type         = Column(ENUM(FOLDER_TYPE, PROJECT_TYPE, AWSS3_TYPE, RFOLDER_TYPE, DATABASE_TYPE, FLOW_TYPE, FRAME_TYPE, TRASH_TYPE, name='data_type'), nullable=False)
    _data        = Column('data', JSONB)
    _creator_id  = Column('creator', INTEGER)
    _modifier_id = Column('modifier', INTEGER)
    created_at   = Column(TIMESTAMP, default=text('statement_timestamp()'))
    modified_at  = Column(TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()'))
    # read権限(queryで追加した列の結果を格納する)
    readable     = query_expression()

    user = query_expression()

    # from sqlalchemy import func, and_
    # from sqlalchemy.orm import Query
    # from kskp.store.auth import Auth, Group, UserGroup
    # readable2 = column_property(
    #     select([func.bool_and(Auth.read)]).\
    #         where(
    #             and_(
    #                 Group.id==Auth.group_id,
    #                 UserGroup.group_id==Group.id,
    #                 UserGroup.user_id==self.session.user.id
    #             )
    #         )
    # )

    # これを設定することで、session.query(Datum).all()でもサブクラスの型で結果を得ることができる
    __mapper_args__ = {
        'polymorphic_on' : type
    }

    # conver_to_xxx()によるキャスト処理で余分にSQLを発行しないためにparent_uuidを保持する
    # _parent_uuid = None

    def __init__(self, session, parent, datum_type, label, creator=None):
        """
        コンストラクタ
        """
        # SQLAlchemy Session
        self.session = session

        # parent_uuidからparent_idを取得する
        # if parent_uuid is None:
        #     parent = None
        # else:
        #     # UUID値の形式チェックをする
        #     Datum.valid_uuid_or_raise(parent_uuid)
        #     parent = self.session.query(Datum.id, Datum._path)\
        #                     .filter(Datum.uuid==parent_uuid).one_or_none()
        #     if parent is None:
        #         raise Exception('No parent folder is found!')
        #     else:
        #         self.parent_id = parent.id
        #         # self.parent_uuid = parent_uuid
        #
        # self._parent_uuid = parent_uuid

        # parent_id
        # (rootのみparent_idはNoneである)
        if parent is not None:
            self.parent_id = parent.id

        # UUIDを採番する
        import uuid
        self.uuid = str(uuid.uuid4())

        # pathは親フォルダのpathを引き継ぐ
        if parent is None:
            # 親フォルダがない場合はデフォルトパスとする
            self._path = self.DEFAULT_LIBRARY_PATH
        else:
            dir_name = Datum.escape_filename(label)
            self._path = os.path.join(parent._path, dir_name)

        # label
        self._label = Datum.escape_label(label)

        # type
        self.type = datum_type

        # creator, modifier
        if creator is not None:
            self._creator_id = creator.id
            self._modifier_id = creator.id

        # DBに保存する前のDatumへの参照権限は制限しない
        self.readable = True

        # Engineから参照する
        self.context = {}

    # @property
    # def parent_uuid(self):
    #     if self._parent_uuid is None:
    #         self._parent_uuid = self.find_parent().uuid
    #     return self._parent_uuid

    @property
    def path(self):
        from kskp.store import Mountable

        # 参照権限が無ければ例外を送出する
        self._readable_or_raise()

        if self._path is None or self._path == '':
            return None

        if os.path.exists(self._path):
            # ここで_pathがマウントポイントで、かつUnmount状態のとき、そのまま_pathを返してしまうと、
            # children_getter._synchronize()によりS3バケットが空になってしまうので以下の場合分けを行う
            if os.path.isdir(self._path):
                if isinstance(self, Mountable):
                    # _pathがディレクトリで、かつマウントポイントの場合、再マウント処理をする
                    Mountable.remount(self.session, self.id)
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
                Mountable.remount(self.session, self.id)
                if not os.path.exists(self._path):
                    # 再マウント処理をしてもファイルまたはディレクトリがない場合は、例外を送出する
                    # (ここで例外を送出するとexists(path)で存在チェックができなくなる)
                    # raise Exception('No file or directory of the path property exists.')
                    pass
                # return Path(self._path)
                pass

        # 必ず相対pathを返す
        # return Path(self._to_rel_path(self._path))

        # 絶対パスを返す
        return Path(Datum._to_abs_path(self._path))

    @path.setter
    def path(self, path):
        # Pathオブジェクトを受け取る
        self._path = Datum._to_rel_path(path).as_posix()

    @property
    def path_exists(self):
        path = Datum._to_abs_path(self._path)
        return os.path.exists(path)

    @property
    def label(self):
        if self._label is None or self._label == '':
            if self.data is None:
                return ''
            return self.data.get('label') or ''
        else:
            return self._label

    @property
    def prev_parent_id(self):
        if self.data is None:
            return None
        return self.data.get('prev_parent_id')

    @prev_parent_id.setter
    def prev_parent_id(self, id):
        self.data['prev_parent_id'] = id

    @property
    def data(self):
        # 参照権限が無ければ例外を送出する
        self._readable_or_raise()
        return self._data

    @data.setter
    def data(self, data):
        self._data = data

    # @property
    # def content(self):
    #     """
    #     Engineから参照する
    #     """
    #     return self

    @property
    def created_at_str(self):
        import datetime
        if self.created_at is None:
            return ''
        # DBに格納されている日時はUTCなので、タイムゾーンをUTCに設定する
        created_at_utc = self.created_at.replace(tzinfo=datetime.timezone.utc)
        # UTC日時はここで現地時間(環境変数TZの値)に設定される
        created_at_local = created_at_utc.astimezone()
        return created_at_local.strftime('%Y-%m-%d %H:%M:%S')

    @property
    def modified_at_str(self):
        import datetime
        if self.modified_at is None:
            return ''
        # DBに格納されている日時はUTCなので、タイムゾーンをUTCに設定する
        modified_at_utc = self.modified_at.replace(tzinfo=datetime.timezone.utc)
        # UTC日時はここで現地時間(環境変数TZの値)に設定される
        modified_at_utc = modified_at_utc.astimezone()
        return modified_at_utc.strftime('%Y-%m-%d %H:%M:%S')

    @property
    def creator(self):
        from kskp.store.factory import UserFactory
        if self._creator_id is None:
            return None
        return UserFactory(self.session).find_by_id(self._creator_id)

    @property
    def modifier(self):
        from kskp.store.factory import UserFactory
        if self._modifier_id is None:
            return None
        return UserFactory(self.session).find_by_id(self._modifier_id)

    @modifier.setter
    def modifier(self, modifier):
        self._modifier = modifier

    @property
    def creator_str(self):
        if self.creator is None:
            return ''
        return self.creator.name

    @property
    def modifier_str(self):
        if self.modifier is None:
            return ''
        return self.modifier.name

    def find_parent(self):
        """
        自分の親を取得する
        """
        datum = self.session.query(Datum)\
                            .filter(Datum.id==self.parent_id).one()

        datum.session = self.session
        return datum

    def move(self, parent_uuid, modifier=None):
        """
        指定されたStoreの直下に移動する
        """
        from kskp.store import Store
        from kskp.store.factory import DatumFactory

        # UUID値の形式チェックをする
        Datum.valid_uuid_or_raise(parent_uuid)

        to_folder = DatumFactory(self.session).find_by_uuid(parent_uuid)
        if to_folder.type != Datum.FOLDER_TYPE and to_folder.type != Datum.TRASH_TYPE:
            raise Exception('移動先の指定はフォルダまたはゴミ箱のUUIDしか許可していません')

        # # 移動対象がマウントポイントの場合は、path列を変更することはマウントポイントを変更することになるので
        # # とりあえずエラーとする
        # from kskp.store import Mountable
        # if isinstance(self, Mountable):
        #     raise Exception('マウントポイントフォルダを移動することはできません')

        if parent_uuid == self.uuid:
            raise Exception('移動先と移動元の指定が同じです')

        # 移動先が移動元フォルダの配下になる場合は例外を送出する
        if self.type == Datum.FOLDER_TYPE:
            pass

        # 移動元フォルダのidを覚えておく
        if self.data is None:
            new_data = {}
        else:
            new_data = self.data.copy()
        new_data['prev_parent_id'] = self.parent_id

        # 移動後にラベル名が衝突したらラベル名を変更する
        new_label = to_folder.get_another_label_name(self.label, except_uuid=self.uuid)

        try:
            if self.path is None:
                new_path_str = ''
            else:
                # ファイルを移動する
                old_path = self.path
                new_path = to_folder.path / self.path.name

                # 移動対象がマウントポイントの場合は、path列を変更することはマウントポイントを変更することになるので
                # parent_idとラベル名だけの変更になる, 移動対象がpath列を持たない場合も同じ処理になる
                new_path = Datum.move_file(old_path, new_path)

                # ファイル名の移動によって他のDatumのpathが変更が必要であれば変更する
                self._update_same_path(old_path, new_path, modifier)
                if isinstance(self, Store):
                    self._update_include_path(old_path, new_path, modifier)
                new_path_str = Datum._to_rel_path(new_path).as_posix()

            # レコードを更新する
            self.parent_id = to_folder.id
            self._path = new_path_str
            self._label = new_label
            self._data = new_data
            self._modifier_id = (modifier or self.session.user).id
            self.session.update(self)
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.commit()

        return self

    def put_back(self, modifier):
        """
        直前の親のStoreの直下に移動する
        """
        if self.prev_parent_id is None:
            raise Exception(f'このDatum({self.label})は移動したことがありません')

        from kskp.store.factory import DatumFactory
        factory = DatumFactory(self.session)

        prev_parent_uuid = factory.find_by_id(self.prev_parent_id).uuid

        from kskp.store import TrashCan
        if not factory.exists(prev_parent_uuid):
            raise Exception('戻り先フォルダが削除されたため移動できません')
        elif factory.trashed(prev_parent_uuid):
            raise Exception('戻り先フォルダがゴミ箱の中なので移動できません')

        return self.move(prev_parent_uuid, modifier)

    def get_prev_folder_path(self):
        from kskp.store.factory import DatumFactory
        if self.prev_parent_id is None:
            return None
        else:
            prev_parent = DatumFactory(self.session).find_by_id(self.prev_parent_id)
            return '/' + '/'.join([folder.get('label') for folder in prev_parent.get_folder_path()])

    def __repr__(self):
        return f'Datum({self.id}, {self._label}, {self.type})'

    def to_json(self):
        return {'uuid'      : self.uuid,
                'type'      : self.type,
                'label'     : self.label,
                'prevFolderPath' : self.get_prev_folder_path(),
                'creator'   : self.creator_str,
                'createdAt' : self.created_at_str}

    def _readable_or_raise(self):
        from kskp.store.auth import NotAuthorizedException
        if self.readable is None:
            raise NotAuthorizedException(f'{self.label}の参照権限がNoneです(save後のDatumオブジェクトは参照権限がNoneになります)')
        if not self.readable:
            raise NotAuthorizedException(f'{self.session.user.name} ({self.user})は{self.label}の参照権限がありません({self.readable})')

    def _update_same_path(self, old_path, new_path, modifier):
        # 同じファイルに対応するフォルダのpath列を、ファイル名の移動に合わせて変更する
        rel_old_path = Datum._to_rel_path(old_path).as_posix()

        results = self.session.query(Datum).filter(Datum._path == rel_old_path).all()
        for result in results:
            result._path = Datum._to_rel_path(new_path).as_posix()
            result._modifier_id = (modifier or self.session.user).id
            self.session.update(result)

    def _update_include_path(self, old_path, new_path, modifier=None):
        import re
        # 同じディレクトリを含むpath列を、ディレクトリの移動に合わせて変更する
        rel_old_path = Datum._to_rel_path(old_path).as_posix()
        # ファイルパスに正規表現文字が含まれていればエスケープする
        old_path_pattern = '^' + re.escape(rel_old_path)
        # SQLのワイルドカード%と_をエスケープする
        results = self.session.query(Datum)\
                         .filter(Datum._path!=None)\
                         .filter(Datum._path.startswith(rel_old_path + '/', autoescape=True)).all()
        for result in results:
            rel_new_path = Datum._to_rel_path(new_path).as_posix()
            replaced_path = re.sub('^'+old_path_pattern, rel_new_path, result._path)

            result._path = replaced_path
            result._modifier_id = (modifier or self.session.user).id
            self.session.update(result)

    def get_flow_uuids_using_me(self):
        """      .......
        指定されたDatumのuuidを参照するFlowを取得する
        """
        sql = f"""
        select uuid from data
        where type='flow'
          and uuid<>'{self.uuid}'
          and to_tsvector(data) @@ to_tsquery('{self.uuid}')
        """
        # SQLを発行する
        results = self.session.execute(sql)
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
            # ファイルを移動する(マウントポイントは移動できない)
            from kskp.store import Mountable
            if old_path.exists() and not Mountable.is_mount(old_path):
                # 同じ名称のファイルが既に存在する場合、末尾に数字を付加したファイル名で作成する
                new_path = Datum.get_another_file_path(new_path, except_path=old_path)
                old_path.rename(new_path)
                return new_path
            else:
                return old_path
        except PermissionError as e:
            # ファイルに対する権限がない場合
            raise e
        except OSError as e:
            # ファイルパス指定に誤りがある場合
            # (循環参照になる場合など)
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
    def get_another_file_path(path, except_path=None):
        """
        同じ名称のファイルが既に存在する場合、末尾に数字を付加したファイル名で作成する
        except_path : 存在チェックを除外するファイル名
        """
        while path.exists() and path != except_path:
            filename = path.name
            dir_path = path.parent
            new_filename = Datum._get_another_file_name(filename)
            path = dir_path / new_filename
        return path

    @staticmethod
    def _to_abs_path(path):
        if path.startswith('/'):
            return path
        else:
            return (Datum.STORE_DIR / path).as_posix()

    @staticmethod
    def _to_rel_path(path):
        # if path.startswith('/'):
        if path.is_absolute():
            # ディレクトリトラバーサルには対応していない
            return path.relative_to(Datum.STORE_DIR)
        else:
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
