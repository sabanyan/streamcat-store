"""
いわゆるルートクラスであるDatumを定義している
"""
import os
import sqlalchemy.types
from pathlib import Path
from kskp.store import BaseModel
from sqlalchemy import Column, String, text
from sqlalchemy.sql import operators
from sqlalchemy.orm import query_expression
from sqlalchemy.dialects.postgresql import INTEGER, TIMESTAMP, JSONB, ENUM, UUID
from .constraints import Constraints

class Datum(BaseModel):
    """
    KSKPで扱う対象を扱ううち、「第一級」であるものの頂点のクラス。
    """

    class PathType(sqlalchemy.types.TypeDecorator):
        """
        SQLAlchemyにおいてpath列をpathオブジェクトで参照・登録できるようにする
        """
        impl = sqlalchemy.types.String

        def process_bind_param(self, value, dialect):
            if value is None:
                return ''
            # return value.as_posix()
            return Datum._to_rel_path(value).as_posix()

        def process_result_value(self, value, dialect):
            if value=='' or value is None:
                return None
            # return Path(value)
            return Datum._to_abs_path(Path(value))

        # _pathに対してLike式を用いる時に必要
        def coerce_compared_value(self, op, value):
            if op in (operators.like_op, operators.notlike_op):
                return String()
            else:
                return self

    # ルートフォルダのPath
    DEFAULT_LIBRARY_PATH = Path('cmn')

    FOLDER_TYPE = 'folder'
    PROJECT_TYPE = 'project'
    AWSS3_TYPE  = 'awss3'
    RFOLDER_TYPE = 'rfolder'
    DATABASE_TYPE = 'database'
    FLOW_TYPE   = 'flow'
    FRAME_TYPE  = 'frame'
    TRASH_TYPE = 'trash'
    COMMAND_TYPE = 'command'
    ACTIVITY_TYPE = 'activity'

    RESULT_FOLDER_UUID  = 'aacb4914-0695-40fc-b14b-95b7f1f81707'
    RESULT_FOLDER_LABEL = '実行結果'
    CACHE_FOLDER_UUID  = 'cc9f050d-b007-414e-a6e0-6d31a9c13395'
    CACHE_FOLDER_LABEL = 'キャッシュ'
    FLOW_FOLDER_UUID  = 'ff37fe34-9c25-4ad0-b74a-affda3712a45'
    FLOW_FOLDER_LABEL = 'フロー'

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
    _path        = Column('path', PathType, nullable=False)
    _label       = Column('label', String)
    # PostgreSQLのENUM型の要素を変更してもSQLAlchemyから自動的に変更がかからないので手動で変更する必要がある
    type         = Column(ENUM(FOLDER_TYPE, PROJECT_TYPE, AWSS3_TYPE, RFOLDER_TYPE, DATABASE_TYPE, FLOW_TYPE, FRAME_TYPE, TRASH_TYPE, COMMAND_TYPE, ACTIVITY_TYPE, name='data_type'), nullable=False)
    _data        = Column('data', JSONB)
    _creator_id  = Column('creator', INTEGER)
    _modifier_id = Column('modifier', INTEGER)
    created_at   = Column(TIMESTAMP, default=text('statement_timestamp()'))
    modified_at  = Column(TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()'))
    # 各種権限(queryで追加した列の結果を格納する)
    _permissions = query_expression()
    # 所有権(queryで追加した列の結果を格納する)
    _ownership = query_expression()

    user = query_expression()


    # これを設定することで、session.query(Datum).all()でもサブクラスの型で結果を得ることができる
    __mapper_args__ = {
        'polymorphic_on' : type
    }

    def __init__(self, session, parent, datum_type, label):
        """
        コンストラクタ
        """
        # SQLAlchemy Session
        self._session = session

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
            self._path = Datum._to_abs_path(self.DEFAULT_LIBRARY_PATH)
        else:
            dir_name = Datum.escape_filename(label)
            self._path = parent._path / dir_name

        # label
        self._label = Datum.escape_label(label)

        # type
        self.type = datum_type

        # creator, modifier
        if session is not None and session.user is not None:
            self._creator_id = session.user.id
            self._modifier_id = session.user.id

        # DBに保存する前のDatumへの参照と更新権限は制限しない
        self._permissions = 0b1100

        # Engineから参照する
        self.context = {}

    @property
    def path(self):
        from kskp.store import Mountable
        # 
        # TODO:
        # remount()処理はここに記述せずに、Mountable側でpathプロパティを再定義して
        # そこで、remount()処理を記述したいと思う。
        # 

        # 参照権限が無ければ例外を送出する
        self._readable_or_raise()

        if self._path is None or self._path == '':
            return None

        if self._path.exists():
            # ここで_pathがマウントポイントで、かつUnmount状態のとき、そのまま_pathを返してしまうと、
            # children_getter._synchronize()によりS3バケットが空になってしまうので以下の場合分けを行う
            if self._path.is_dir:
                if isinstance(self, Mountable):
                    # _pathがディレクトリで、かつマウントポイントの場合、再マウント処理をする
                    Mountable.remount(self._session, self.id)
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
                Mountable.remount(self._session, self.id)
                if not self._path.exists():
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

    # @path.setter
    # def path(self, path):
    #     # Pathオブジェクトを受け取る
    #     self._path = Datum._to_rel_path(path)

    @property
    def path_exists(self):
        return self._path.exists()

    @property
    def label(self):
        if self._label is None or self._label == '':
            if self._data is None:
                return ''
            return self._data.get('label') or ''
        else:
            return self._label

    @property
    def readable(self):
        p = self._permissions
        return p if p is None else (p & 0b1000) > 0

    @property
    def writable(self):
        p = self._permissions
        return p if p is None else (p & 0b0100) > 0

    @property
    def executable(self):
        p = self._permissions
        return p if p is None else (p & 0b0010) > 0

    @property
    def ownership(self):
        return self._ownership

    @property
    def is_root(self):
        return self.parent_id is None

    @property
    def prev_parent_id(self):
        if self._data is None:
            return None
        return self._data.get('prev_parent_id')

    @prev_parent_id.setter
    def prev_parent_id(self, id):
        self._data['prev_parent_id'] = id

    # @property
    # def data(self):
    #     # 参照権限が無ければ例外を送出する
    #     self._readable_or_raise()
    #     return self._data

    # @data.setter
    # def data(self, value):
    #     self._data = value

    @property
    def data_is_empty(self):
        return self._data is None or self._data == {}

    @property
    def created_at_str(self):
        from kskp.core import Util
        return Util.datetime_to_local_time_str(self.created_at)

    @property
    def modified_at_str(self):
        from kskp.core import Util
        return Util.datetime_to_local_time_str(self.modified_at)

    @property
    def creator(self):
        from kskp.store.factory import UserFactory
        if self._creator_id is None:
            return None
        return UserFactory(self._session).find_by_id(self._creator_id, allow_no_result=True)

    @property
    def modifier(self):
        from kskp.store.factory import UserFactory
        if self._modifier_id is None:
            return None
        return UserFactory(self._session).find_by_id(self._modifier_id, allow_no_result=True)

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
        return self._session.query(Datum)\
                            .filter(Datum.id==self.parent_id).one()

    def find_my_project(self):
        """
        自分のプロジェクトを取得する
        """
        from sqlalchemy.orm import aliased
        from sqlalchemy.sql.expression import select, exists, and_
        from kskp.store import ProjectFolder

        # cte: Common Table Expression WITH句のこと
        D0 = aliased(Datum, name='D0')
        R = select([D0.id, D0.parent_id, D0.type]).select_from(D0).\
            where(D0.id==self.id).\
            cte(name='R', recursive=True)

        # WITH句にUNION ALLを用いて再帰クエリとする
        D = aliased(Datum, name='D')
        R = R.union_all(
                select([D.id, D.parent_id, D.type]).\
                select_from(R.join(D, and_(D.id==R.c.parent_id,
                                           R.c.type!=Datum.PROJECT_TYPE)))
            )

        # プロジェクトを取得する
        exists_project = exists().where(and_(R.c.id==ProjectFolder.id, R.c.type==Datum.PROJECT_TYPE))
        query = self._session.query(ProjectFolder).filter(exists_project)
        return query.one()

    def reload(self):
        """
        自分を再読み込みする
        (save()後に行うとreadableを設定できる)
        """
        from kskp.store.factory import DatumFactory
        factory = DatumFactory(self._session)
        return factory.find_by_id(self.id)

    @Constraints.prohibit_move_to_root
    @Constraints.set_role_on_moving
    def move(self, parent_uuid, modifier=None):
        """
        指定されたStoreの直下に移動する
        """
        from kskp.store import Mountable, Folder
        from kskp.store.factory import DatumFactory
        from kskp.store.auth import NotAuthorizedException

        # UUID値の形式チェックをする
        Datum.valid_uuid_or_raise(parent_uuid)

        # 移動元フォルダのIDを控えておく
        from_folder_id = self.parent_id

        to_folder = DatumFactory(self._session).find_by_uuid(parent_uuid)
        if not isinstance(to_folder, Folder):
            raise Exception('移動先の指定はフォルダ、プロジェクトまたはゴミ箱のUUIDしか許可していません')
        elif not self._session.writable(to_folder):
            raise NotAuthorizedException((f'{self._session.user}は{to_folder.label}の更新権限がないため{self.label}を移動できません'))

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

        # # 移動元フォルダのidを覚えておく
        # if self.data is None:
        #     new_data = {}
        # else:
        #     new_data = self.data.copy()
        # new_data['prev_parent_id'] = self.parent_id

        # 移動後にラベル名が衝突したらラベル名を変更する
        new_label = to_folder.make_unique_label(self.label, except_uuid=self.uuid)

        try:
            if self._path is not None:
                # ファイルパスを作成する
                old_path = self._path
                if not old_path.exists() or Mountable.is_mount(old_path):
                    # 移動対象がマウントポイントの場合は、path列を変更することはマウントポイントを変更することになるので
                    # parent_idとラベル名だけの変更になる, 移動対象がpath列を持たない場合も同じ処理になる
                    new_path = old_path
                else:
                    # 移動先フォルダの参照権限は必要ということにした
                    new_path = to_folder.path / self._path.name
                    new_path = Datum.make_unique_path(new_path, except_path=old_path)
                    # ファイル名の移動によって他のDatumのpathが変更が必要であれば変更する
                    self._update_same_path(old_path, new_path, modifier)
                    if isinstance(self, Folder):
                        self._update_include_path(old_path, new_path, modifier)
            else:
                # PylanceのWarning対策
                old_path = None
                new_path = None

            # レコードを更新する
            if self._data is None:
                self._data = {}
            self._data['prev_parent_id'] = self.parent_id
            self.parent_id = to_folder.id
            if self._path is not None:
                self._path = new_path
            self._label = new_label
            self._modifier_id = (modifier or self._session.user).id
            self._session.update(self)

            # ファイルを移動する
            if self._path is not None:
                Datum.move_file(old_path, new_path)

        except NotAuthorizedException as e:
            # ROLLBACK
            self._session.rollback()

            user_name = self._session.user
            from_folder = DatumFactory(self._session).find_by_id(from_folder_id)
            if not self._session.writable(self):
                raise NotAuthorizedException((f'{user_name}は更新権限がないため{self.label}を移動できません'))
            elif not self._session.writable(from_folder):
                raise NotAuthorizedException((f'{user_name}は{from_folder.label}の更新権限がないため{self.label}を移動できません'))
            else:
                raise e
        except Exception as e:
            # ROLLBACK
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

        return self

    def throw_away(self):
        """
        ゴミ箱にほかす
        """
        from kskp.store.factory import DatumFactory
        factory = DatumFactory(self._session)
        trash_folder = factory.load_trash_folder()

        return self.move(trash_folder.uuid)

    def put_back(self):
        """
        直前の親のStoreの直下に戻す
        """
        moved_data, exps = self._put_back_inner(self)
        if len(moved_data) == 0:
            if len(exps) == 0:
                from kskp.store import NothingToPutbackException
                raise NothingToPutbackException('元に戻すファイルがありませんでした')
            elif len(exps) == 1:
                raise exps[0]
            else:
                raise Exception('全てのファイルを戻せませんでした')
        else:
            if len(exps) > 0:
                raise Exception('一部のファイルを戻せませんでした')
        return moved_data

    def _put_back_inner(self, datum):
        from kskp.store import Folder
        from kskp.store.factory import DatumFactory

        if isinstance(datum, Folder) and datum.prev_parent_id is None:
            # 移動対象がprev_parent_idを持たないフォルダの場合
            # その下のファイルを個別に移動する
            children = datum.find_children()
            moved_data = []
            exps = []
            for child in children:
                moved_datum, exp = self._put_back_inner(child)
                moved_data.extend(moved_datum)
                exps.extend(exp)
            return moved_data, exps
        else:
            try:
                if datum.prev_parent_id is None:
                    raise Exception(f'このDatum({datum.label})は移動したことがありません')

                factory = DatumFactory(self._session)
                prev_parent_uuid = factory.find_by_id(datum.prev_parent_id).uuid

                if not factory.exists(prev_parent_uuid):
                    raise Exception('戻り先フォルダが削除されたため移動できません')
                elif factory.trashed(prev_parent_uuid):
                    raise Exception('戻り先フォルダがゴミ箱の中なので移動できません')

                # 戻り先フォルダに移動する
                return [datum.move(prev_parent_uuid)], []
            except Exception as e:
                return [], [e]

    def get_prev_folder_path(self):
        from kskp.store.factory import DatumFactory
        factory = DatumFactory(self._session)
        if self.prev_parent_id is None or not factory.exists_by_id(self.prev_parent_id):
            return None
        else:
            prev_parent = factory.find_by_id(self.prev_parent_id)
            return '/' + '/'.join([folder.get('label') for folder in prev_parent.get_folder_path()])

    def __repr__(self):
        return f'Datum({self.id}, {self._label}, {self.type})'

    def __eq__(self, other):
        return self.uuid == other.uuid

    def __ne__(self, other):
        return self.uuid != other.uuid

    def __hash__(self) -> int:
        return hash(self.uuid)

    def to_json(self):
        return {'uuid'      : self.uuid,
                'type'      : self.type,
                'label'     : self.label,
                'allowlist' : {
                    'read'   : self.readable,
                    'update' : self.writable,
                    'delete' : self.writable,
                    'execute': False,
                    'move'   : self.writable,
                    'copy'   : self.writable,
                    # 閲覧者以外はDownload可能なのでwritableで判定する
                    'download'    : self.writable,
                    'findMember'  : False,
                    'updateMember': False,
                    'lock'   : False,
                },
                'prevFolderPath' : self.get_prev_folder_path(),
                'creator'   : self.creator_str,
                'createdAt' : self.created_at_str }

    def _readable_or_raise(self):
        from kskp.store.auth import NotAuthorizedException
        if self.readable is None:
            raise NotAuthorizedException(f'{self.label}の参照権限がNoneです(save後のDatumオブジェクトは参照権限がNoneになります)')
        if not self.readable:
            raise NotAuthorizedException(f'{self._session.user.name} ({self.user})は{self.label}の参照権限がありません({self.readable})')

    def _update_same_path(self, old_path, new_path, modifier):
        # 同じファイルに対応するフォルダのpath列を、ファイル名の移動に合わせて変更する
        results = self._session.query(Datum).filter(Datum._path == old_path).all()
        for result in results:
            result._path = Datum._to_rel_path(new_path)
            result._modifier_id = (modifier or self._session.user).id
            self._session.update(result)

    def _update_include_path(self, old_path, new_path, modifier=None):
        import re
        # 同じディレクトリを含むpath列を、ディレクトリの移動に合わせて変更する
        rel_old_path = Datum._to_rel_path(old_path).as_posix()
        # ファイルパスに正規表現文字が含まれていればエスケープする
        old_path_pattern = '^' + re.escape(rel_old_path) + '/'
        # SQLのワイルドカード%と_をエスケープする
        results = self._session.query(Datum)\
                         .filter(Datum._path!=None)\
                         .filter(Datum._path.like(rel_old_path + '/' + '%')).all()
        for result in results:
            rel_new_path = Datum._to_rel_path(new_path).as_posix() + '/'
            rel_result_path = Datum._to_rel_path(result._path).as_posix()
            replaced_path = re.sub(old_path_pattern, rel_new_path, rel_result_path)

            result._path = Path(replaced_path)
            result._modifier_id = (modifier or self._session.user).id
            self._session.update(result)

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
        results = self._session.execute(sql)
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
        
        # 移動元と移動先ファイルパスが同じ場合は移動しない
        if old_path == new_path:
            return new_path

        try:
            # ファイルを移動する
            old_path.rename(new_path)
            return new_path
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
    def make_unique_path(path, except_path=None):
        """
        同じ名称のファイルが既に存在する場合、末尾に数字を付加したファイル名で作成する
        except_path : 存在チェックを除外するファイル名
        """
        while path.exists() and path != except_path:
            filename = path.name
            dir_path = path.parent
            new_filename = Datum._increment_file_name(filename)
            path = dir_path / new_filename
        return path

    @staticmethod
    def _increment_file_name(filename):
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
    def _to_abs_path(path):
        if path.is_absolute():
            return path
        else:
            return Datum.STORE_DIR / path

    @staticmethod
    def _to_rel_path(path):
        # if path.startswith('/'):
        if path.is_absolute():
            # ディレクトリトラバーサルには対応していない
            return path.relative_to(Datum.STORE_DIR)
        else:
            return path

    @staticmethod
    def is_valid_uuid(uuid):
        """
        uuidの形式チェック
        """
        if uuid is None:
            return False
        import re
        return re.match('^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$', uuid)

    @staticmethod
    def valid_uuid_or_raise(uuid):
        """
        uuidの形式チェックの結果、正しくないuuidの場合は例外を送出する
        """
        if uuid is None or uuid == '':
            raise Exception(f'The UUID value is empty')
        if not Datum.is_valid_uuid(uuid):
            raise Exception(f'The UUID({uuid}) value is not valid format.')
