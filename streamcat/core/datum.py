"""
いわゆるルートクラスであるDatumを定義している
"""
import sqlalchemy.types
from pathlib import Path
from sqlalchemy import Column, String
from sqlalchemy.sql import operators
from sqlalchemy.orm import query_expression
from sqlalchemy.dialects.postgresql import INTEGER, JSONB, ENUM, UUID
from . import BaseModel
from .constraints import Constraints

class Datum(BaseModel):
    """
    StreamCatで扱う対象を扱ううち、「第一級」であるものの頂点のクラス。
    """

    class PathType(sqlalchemy.types.TypeDecorator):
        """
        SQLAlchemyにおいてpath列をpathオブジェクトで参照・登録できるようにする
        """
        impl = sqlalchemy.types.String
        # キャッシュを許可する
        cache_ok = True

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
            if op in (operators.like_op, operators.notlike_op, operators.startswith_op):
                return String()
            else:
                return self

    # ルートフォルダのPath
    DEFAULT_LIBRARY_PATH = Path('cmn')

    # type列の値の定義
    PROJECT_TYPE  = 'project'
    FOLDER_TYPE   = 'folder'
    AWSS3_TYPE    = 'awss3'
    RFOLDER_TYPE  = 'rfolder'
    DATABASE_TYPE = 'database'
    FLOW_TYPE     = 'flow'
    COMMAND_TYPE  = 'command'
    SCHEDULE_TYPE = 'schedule'
    ACTIVITY_TYPE = 'activity'
    FRAME_TYPE    = 'frame'
    DOCUMENT_TYPE = 'document'
    # 将来の拡張のために予約するtype値
    APPLICATION_TYPE = 'app'
    EXCEL_TYPE = 'excel'
    PDF_TYPE   = 'pdf'
    ZIP_TYPE   = 'zip'
    VIDEO_TYPE = 'video'
    IMAGE_TYPE = 'image'
    TEXT_TYPE  = 'text'
    HTML_TYPE  = 'html'
    TRASH_TYPE = 'trash'
    UNKNOWN_TYPE = 'unknown'

    RESULT_FOLDER_UUID  = 'aacb4914-0695-40fc-b14b-95b7f1f81707'
    RESULT_FOLDER_LABEL = '実行結果'
    CACHE_FOLDER_UUID   = 'cc9f050d-b007-414e-a6e0-6d31a9c13395'
    CACHE_FOLDER_LABEL  = 'キャッシュ'
    FLOW_FOLDER_UUID    = 'ff37fe34-9c25-4ad0-b74a-affda3712a45'
    FLOW_FOLDER_LABEL   = 'フロー'
    ACTIVITY_FOLDER_UUID  = 'aa2799ba-798e-4fa3-984c-b3fad92fd162'
    ACTIVITY_FOLDER_LABEL = 'アクティビティ'

    # AuthzSessionが返す権限設定ののビットフラグ(_permissions)
    PERMISSION_READ   = 0b1_00_0_0
    PERMISSION_WRITE  = 0b0_10_0_0
    # 編集ロック値を除外した更新権限(編集者フラグ)
    PERMISSION_WRITER = 0b0_01_0_0
    PERMISSION_EXEC   = 0b0_00_1_0
    PERMISSION_OWN    = 0b0_00_0_1

    # Datum.pathの基点ディレクトリ
    STORE_DIR = Path(__file__).parent.parent / 'depo/files'

    # テーブル名の定義
    __tablename__ = 'data'

    # 列名と列のデータ型等の定義
    id           = Column(INTEGER, primary_key=True, autoincrement=True)
    parent_id    = Column(INTEGER)
    prev_parent_id = Column(INTEGER)
    uuid         = Column(UUID, nullable=False, unique=True)
    # PostgreSQLのENUM型の要素を変更してもSQLAlchemyから自動的に変更がかからないので手動で変更する必要がある
    type         = Column(ENUM( PROJECT_TYPE,
                                FOLDER_TYPE,
                                AWSS3_TYPE,
                                RFOLDER_TYPE,
                                DATABASE_TYPE,
                                FLOW_TYPE,
                                COMMAND_TYPE,
                                SCHEDULE_TYPE,
                                ACTIVITY_TYPE,
                                FRAME_TYPE,
                                DOCUMENT_TYPE,
                                APPLICATION_TYPE,
                                EXCEL_TYPE,
                                PDF_TYPE,
                                ZIP_TYPE,
                                VIDEO_TYPE,
                                IMAGE_TYPE,
                                TEXT_TYPE,
                                HTML_TYPE,
                                TRASH_TYPE,
                                UNKNOWN_TYPE,
                                name='data_type'), nullable=False)
    _label       = Column('label', String)
    _path        = Column('path', PathType, nullable=False)
    _data        = Column('data', JSONB)
    _desc        = Column('desc', String)

    # 各種権限(queryで追加した列の結果を格納する)
    _permissions = query_expression()
    # 所有権(queryで追加した列の結果を格納する)
    _ownership   = query_expression()
    # 親フォルダのuuid(queryで追加した列の結果を格納する)
    _parent_uuid = query_expression()
    # フォルダパス
    _folder_path = query_expression()
    # 移動前のフォルダパス
    _prev_folder_path = query_expression()

    # これを設定することで、session.query(Datum).all()でもサブクラスの型で結果を得ることができる
    __mapper_args__ = {
        'polymorphic_on' : type
    }

    def __init__(self, session, parent, datum_type, label):
        """
        コンストラクタ
        """
        super().__init__(session)

        # parent_id
        # (rootのみparent_idはNoneである)
        if parent is not None:
            self.parent_id = parent.id

        # UUIDを採番する
        import uuid
        self.uuid = str(uuid.uuid4())

        # type
        self.type = datum_type

        # label
        self._label = Datum.escape_label(label)

        # pathは親フォルダのpathを引き継ぐ
        if parent is None:
            # 親フォルダがない場合はデフォルトパスとする
            self._path = Datum._to_abs_path(self.DEFAULT_LIBRARY_PATH)
        else:
            dir_name = Datum.escape_filename(label)
            self._path = parent._path / dir_name

        # DBに保存する前のDatumへの参照と更新権限は制限しない
        self._permissions = Datum.PERMISSION_READ | Datum.PERMISSION_WRITE

        # DBに保存する前は空文字を設定する
        self._folder_path = ''

        # Engineから参照する
        self.context = {}

    @property
    def label(self):
        if self._label is None or self._label == '':
            if self._data is None:
                return ''
            return self._data.get('label') or ''
        else:
            return self._label

    @property
    def path(self):
        # 参照権限が無ければ例外を送出する
        self._readable_or_raise()

        if self._path is None or self._path == '':
            return None

        # 絶対パスを返す
        return Datum._to_abs_path(self._path)

    @property
    def path_exists(self):
        return self._path.exists()

    @property
    def desc(self):
        return self._desc or ''

    @property
    def readable(self):
        p = self._permissions
        return p if p is None else (p & Datum.PERMISSION_READ) > 0

    @property
    def writable(self):
        p = self._permissions
        return p if p is None else (p & Datum.PERMISSION_WRITE) > 0

    @property
    def writable_without_edit_lock(self):
        """
        このDatumの編集ロックを考慮しないself.writable
        """
        p = self._permissions
        return p if p is None else (p & Datum.PERMISSION_WRITER) > 0

    @property
    def executable(self):
        p = self._permissions
        return p if p is None else (p & Datum.PERMISSION_EXEC) > 0

    @property
    def ownership(self):
        return self._ownership

    @property
    def parent_uuid(self):
        """
        自身の親フォルダのUUIDを返す
        """
        if self._parent_uuid is None:
            if self.is_root:
                return None
            else:
                return self.find_parent().uuid
        else:
            return self._parent_uuid

    @property
    def folder_path(self):
        """
        自身の親フォルダまでのフォルダパスを返す
        """
        # _folder_path=''の場合は、DataumがDBに保存されてないので
        # その場合は親フォルダのfolder_pathと親フォルダのラベルからフォルダパス文字列を作成する
        # (TODO: この機能は削除したい)
        if self._folder_path=='':
            parent = self.find_parent()
            if parent.is_root:
                return '/' + parent.label
            else:
                parent_folder_path = parent.folder_path
                # 親フォルダのフォルダパスが取得できない場合はNoneを返す
                return parent_folder_path and (parent_folder_path + '/' + parent.label)
        else:
            return self._folder_path

    @property
    def prev_folder_path(self):
        """
        移動前の親フォルダまでのフォルダパスを返す
        """
        # 一度も移動していない場合はNoneを返す
        return self._prev_folder_path

    @property
    def is_root(self):
        return self.parent_id is None

    @property
    def data_is_empty(self):
        return self._data is None or self._data == {}

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
        from streamcat.store import ProjectFolder

        # cte: Common Table Expression WITH句のこと
        D0 = aliased(Datum, name='D0')
        R = select(D0.id, D0.parent_id, D0.type).select_from(D0).\
            where(D0.id==self.id).\
            cte(name='R', recursive=True)

        # WITH句にUNION ALLを用いて再帰クエリとする
        D = aliased(Datum, name='D')
        R = R.union_all(
                select(D.id, D.parent_id, D.type).\
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
        from streamcat.store.factory import DatumFactory
        factory = DatumFactory(self._session)
        # Sessionにあるself._permissionsを期限切れ状態にしてDBからリロードされるようにする
        factory._session._session.expire(self, ['_permissions'])
        return factory.find_by_id(self.id)

    def update_label(self, label, modifier=None):
        """
        Datumのラベルを更新する
        """
        # ラベルに'\0'が含まれていれば取り除く
        new_label = Datum.escape_label(label)

        try:
            # ラベルを更新する
            self._label = new_label
            self._modifier_id = (modifier or self._session.user).id
            self._session.update(self)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()
        return self

    @Constraints.prohibit_move_to_root
    @Constraints.prohibit_move_system_folder
    @Constraints.set_project_role_on_moving
    @Constraints.set_project_role_on_moving_flow
    def move(self, parent_uuid, modifier=None):
        """
        指定されたStoreの直下に移動する
        """
        from streamcat.store import Mountable, Folder
        from streamcat.store.factory import DatumFactory
        from streamcat.store.auth import NotAuthorizedException

        # UUID値の形式チェックをする
        Datum.valid_uuid_or_raise(parent_uuid)

        # 移動元フォルダのIDを控えておく
        from_folder_id = self.parent_id

        to_folder = DatumFactory(self._session).find_by_uuid(parent_uuid)
        if not isinstance(to_folder, Folder):
            raise Exception('移動先の指定はフォルダ、プロジェクトまたはゴミ箱のUUIDしか許可していません')
        elif not self._session.writable(to_folder):
            raise NotAuthorizedException((f'{self._session.user}は{to_folder.label}の更新権限がないため{self.label}を移動できません'))

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
            self.prev_parent_id = self.parent_id
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
        except (Exception, OSError) as e:
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
        from streamcat.store.factory import DatumFactory
        factory = DatumFactory(self._session)
        trash_folder = factory.load_trash_folder()

        # 削除しようとするDatumが、フローで使用されている場合は例外を送出する
        using_flow_uuids = self.get_flow_uuids_using_me()
        if len(using_flow_uuids) > 0:
            raise Exception(f"このファイルはフロー({using_flow_uuids[0]['reference_label']})で使用しているため削除できません")

        return self.move(trash_folder.uuid)

    def put_back(self):
        """
        直前の親のStoreの直下に戻す
        """
        moved_data, exps = self._put_back_inner(self)
        if len(moved_data) == 0:
            if len(exps) == 0:
                from streamcat.store import NothingToPutbackException
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
        from streamcat.store import Folder
        from streamcat.store.factory import DatumFactory

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
                    'update' : not self.is_root and self.writable,
                    'delete' : not self.is_root and self.writable,
                    'execute': False,
                    'move'   : not self.is_root and self.writable,
                    'copy'   : not self.is_root and self.writable_without_edit_lock,
                    # 閲覧者以外はDownload可能なのでwritableで判定する
                    'download'    : not self.is_root and self.writable,
                    'export'      : False,
                    'findMember'  : False,
                    'updateMember': False,
                    'lock'   : False,
                },
                'folderPath' : self.folder_path,
                'folderUuid' : self.parent_uuid,
                'prevFolderPath' : self.prev_folder_path,
                'creator'   : self.creator_str,
                'createdAt' : self.created_at_str }

    def _readable_or_raise(self):
        from streamcat.store.auth import NotAuthorizedException
        if self.readable is None:
            raise NotAuthorizedException(f'{self.label}の参照権限がNoneです(save後またはrollback後のDatumオブジェクトは参照権限がNoneになります)')
        if not self.readable:
            raise NotAuthorizedException(f'{self._session.user.name}は{self.label}の参照権限がありません({self.readable})')

    def _update_same_path(self, old_path, new_path, modifier):
        # 同じファイルに対応するフォルダのpath列を、ファイル名の移動に合わせて変更する
        results = self._session.query(Datum).filter(Datum._path == old_path).all(ignore_authz=True)
        for result in results:
            result._path = Datum._to_rel_path(new_path)
            result._modifier_id = (modifier or self._session.user).id
            self._session.update(result, ignore_authz=True)

    def _update_include_path(self, old_path, new_path, modifier=None):
        import re
        # 同じディレクトリを含むpath列を、ディレクトリの移動に合わせて変更する
        rel_old_path = Datum._to_rel_path(old_path).as_posix()
        # ファイルパスに正規表現文字が含まれていればエスケープする
        old_path_pattern = '^' + re.escape(rel_old_path) + '/'
        # autoescape=True : LIKEのワイルドカード%と_をエスケープする
        results = self._session.query(Datum)\
                      .filter(Datum._path!=None)\
                      .filter(Datum._path.startswith(rel_old_path, autoescape=True))\
                      .all(ignore_authz=True)

        for result in results:
            rel_new_path = Datum._to_rel_path(new_path).as_posix() + '/'
            rel_result_path = Datum._to_rel_path(result._path).as_posix()
            replaced_path = re.sub(old_path_pattern, rel_new_path, rel_result_path)

            result._path = Path(replaced_path)
            result._modifier_id = (modifier or self._session.user).id
            self._session.update(result, ignore_authz=True)

    def get_flow_uuids_using_me_old(self):
        """      .......
        指定されたDatumのuuidを参照するFlowを取得する
        """
        from sqlalchemy.sql.expression import select, func, and_

        sql = f"""
        select uuid from data
        where type='flow'
          and uuid<>'{self.uuid}'
          and to_tsvector(data) @@ to_tsquery('{self.uuid}')
        """

        # DataのTableオブジェクト
        D = Datum.__table__

        select_stmt = select(Datum.uuid).\
                      select_from(D).\
                      where(and_(Datum.type==Datum.FLOW_TYPE,
                                 Datum.uuid!=self.uuid, 
                                 func.to_tsvector(Datum._data).match(self.uuid)))

        # SQLを発行する
        results = self._session.execute(select_stmt)
        return [str(result[0]) for result in results]

    def get_flow_uuids_using_me(self):
        """
        自身のエントリ以下にあるDatumが、自身のエントリ以下以外にあるFlowから参照される、
        そのようなFlowを全て返す
        """
        from sqlalchemy.orm import aliased
        from sqlalchemy.sql.expression import select, func, exists, and_, cast, text

        sql = """
        WITH RECURSIVE
            R AS (
                SELECT id, uuid FROM data WHERE id = self.id
                UNION ALL
                SELECT data.id, data.uuid FROM data JOIN R ON data.parent_id = R.id
            ),
            T AS (
                SELECT id, uuid FROM data WHERE type = 'trash'
                UNION ALL
                SELECT data.id, data.uuid FROM data JOIN T ON data.parent_id = T.id
            )
        SELECT U.uuid, U.label
        FROM (SELECT D.uuid as uuid,
                     D.label as label,
                     COALESCE(ref_uuid0, ref_uuid1) AS ref_uuid
              FROM (SELECT D.uuid  AS uuid,
                           D.label AS label
                           JSONB_PATH_QUERY(
                                D.data,
                                '$.flow.nodes?(@.type != "command" && @.type != "note").uuid?(@!=null)'
                           ) AS ref_uuid0,
                           JSONB_PATH_QUERY(
                                D.data,
                                '$.flow.nodes?(@.type == "flow").*.uuid?(@!=null)'
                           ) AS ref_uuid1
                    FROM
                        data) D

              WHERE D.type = 'flow'
                AND NOT EXISTS (SELECT * FROM R WHERE R.id = D.id)) U
        WHERE EXISTS (SELECT * FROM R
                      WHERE U.ref_uuid #>> '{}' = CAST(R.uuid AS VARCHAR))
        """

        # id : 検索対象Datumから葉ノードへの経路の全てのDatumのid
        D0 = aliased(Datum, name='D0')
        R = select(D0.id, D0.uuid).\
            select_from(D0).\
            where(D0.id==self.id).\
            cte(name='R', recursive=True) 
            # cte: Common Table Expression WITH句のこと

        # WITH句にUNION ALLを用いて再帰クエリとする
        D1 = aliased(Datum, name='D1')
        R = R.union_all(
                select(D1.id, D1.uuid).\
                select_from(R.join(D1, D1.parent_id==R.c.id))
            )

        # ゴミ箱の中のDatumを全て取得する再帰クエリ
        T = select(D0.id, D0.uuid).\
            select_from(D0).\
            where(D0.type==Datum.TRASH_TYPE).\
            cte(name='T', recursive=True)
        T = T.union_all(
                select(D1.id, D1.uuid).\
                select_from(T.join(D1, D1.parent_id==T.c.id))
            )

        # DataのTableオブジェクト
        D = Datum.__table__

        # 自分と自分の子孫は抽出対象外である
        not_exists_inner = ~exists().where(R.c.id==D.c.id)

        # 参照元がゴミ箱内のフローの場合は抽出対象外である
        not_exists_trash = ~exists().where(T.c.id==D.c.id)

        # 自分と自分の子孫以外のFlowから参照する、自分と自分の子孫のuuidのリストを取得する
        #  R : 自分と自分の子孫
        #  U : 自分と自分の子孫以外のFlow
        #  U.ref_uuid : 自分と自分の子孫以外のFlowが参照しているuuid

        # ノードから参照するUUID
        # ..property : 指定されたプロパティ名を再帰的に検索し、このプロパティ名を持つすべての値の配列を返す
        #              (ただしPostgreSQLでは .**.property で指定するようだ)
        jsonpath = '$.flow.nodes?(@.type != "command" && @.type != "note").**.uuid?(@!=null)'

        # NOTE: jsonb_path_query()をcoalesce()の引数に指定できない
        U = select(D.c.uuid,
                   D.c.label,
                   func.jsonb_path_query(D.c.data, jsonpath).label('ref_uuid')).\
            select_from(D).\
            where(and_(D.c.type==Datum.FLOW_TYPE, not_exists_inner, not_exists_trash)).\
            alias('U')

        # 自分の子孫以外のFlowから参照する、自分と自分の子孫
        U_ref_uuid = str(U.c.ref_uuid.compile())
        predicate = text("%s #>> '{}'" % U_ref_uuid)==cast(R.c.uuid, String)
        exists_inner = exists().where(predicate)

        # メインSQL
        select_stmt = select(U.c.uuid,U.c.label,U.c.ref_uuid).\
                      select_from(U).\
                      where(exists_inner).\
                      distinct()

        # SQLを発行する
        results = self._session.execute(select_stmt)
        return [{'reference_uuid' :result[0],
                 'reference_label':result[1],
                 'referenced_uuid':result[2]} for result in results]

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
            import errno
            if e.errno == errno.EINVAL:
                raise OSError(e.errno, f'移動先が無効なため、{old_path.name}を移動できませんでした')
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
    def make_unique_path(path:Path, except_path=None) -> Path:
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
        import os
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
    def _to_abs_path(path:Path):
        if path.is_absolute():
            return path
        else:
            return Datum.STORE_DIR / path

    @staticmethod
    def _to_rel_path(path:Path):
        # if path.startswith('/'):
        if path.is_absolute():
            # ディレクトリトラバーサルには対応していない
            return path.relative_to(Datum.STORE_DIR)
        else:
            return path

    @staticmethod
    def is_valid_uuid(uuid) -> bool:
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
