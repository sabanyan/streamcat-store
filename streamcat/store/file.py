import os
from pathlib import Path
from streamcat.core import Datum, SavableDatum, Constraints

class File(SavableDatum):
    """
    データをファイルに保存する抽象クラス
    """

    # 64MB
    READ_BUFFER_SIZE = 64 * 1024 * 1024

    # SQLAlchemyにおいてdataテーブルからのマッピング対象クラスでないことを定義する
    __mapper_args__ = {
        'polymorphic_identity' : 'i_am_not_mapping_class_1'
    }

    def __init__(self, session, parent, datum_type, label, stream):
        """
        コンストラクタ
        stream : Frameデータのファイルストリームを指定する
        """
        # TODO: とりあえずUNKNOWN_TYPE
        super().__init__(session, parent, datum_type, label)

        # ファイルストリームからファイルタイプを判定する
        content_type = File.detect_content_type(stream)

        # data列の値を作成する
        self._data = {'content_type':content_type}

        # ファイルストリームを保持する
        self.stream = stream

    @Constraints.prohibit_save_on_root
    @Constraints.set_project_role_on_adding
    def save(self, file_path:Path=None, content_type:str=None):
        """
        Fileを保存する
        """
        # 既にルートフォルダが存在する場合は、parent_id=NULLを許可しない
        from streamcat.store.factory import DatumFactory
        if self.parent_id is None and DatumFactory(self._session).count_root() > 0:
            raise Exception('You can not add another root frame. A root already exists.')

        if file_path is None:
            # 既存のファイルと重複しないファイル名を取得する
            self._path = SavableDatum.make_unique_path(self._path)
        elif file_path.exists():
            self._path = file_path
            if content_type is not None:
                self._data.update({'content_type':content_type})
        else:
            raise Exception(f'指定したファイル({file_path})が存在しないためFrameを保存できません')

        try:
            # Dataテーブルにレコードを新規追加する
            self._session.add(self)
            # ドキュメントに紐付くファイル(path列で指定されるファイル)がなければ作成する
            if file_path is None:
                self._make_file(self._path)
        except (Exception, OSError) as e:
            self._session.rollback()
            raise e

    def update_label(self, label:str, modifier=None):
        """
        Fileのdata列を更新する
        """
        # ラベルに'\0'が含まれていれば取り除く
        new_label = Datum.escape_label(label)

        # ラベル名からファイルパスを作成する
        old_path = self._path
        new_path = old_path.parent / SavableDatum.escape_filename(new_label)
        new_path = SavableDatum.make_unique_path(new_path, except_path=old_path)

        try:
            # 同じファイルに対応するドキュメントのpath列を、ファイル名の移動に合わせて変更する
            self._update_same_path(old_path, new_path, modifier)
            # label列を更新する
            self._update_label_imp(new_label, modifier)
            # ファイルを移動する
            SavableDatum.move_file(old_path, new_path)
        except (Exception, OSError) as e:
            self._session.rollback()
            raise e

        return self

    def update_label_only(self, label:str, modifier=None):
        """
        Fileのlabel列を更新する
        (path及び対応ファイル名は変更しない)
        """
        # ラベルに'\0'が含まれていれば取り除く
        new_label = Datum.escape_label(label)

        try:
            self._update_label_imp(new_label, modifier)
        except (Exception, OSError) as e:
            self._session.rollback()
            raise e

    def _update_label_imp(self, new_label:str, modifier):
        # label列を更新する
        self._label = new_label
        self._modifier_id = (modifier or self._session.user).id
        self._session.update(self)

    @Constraints.delete_role_when_isolated
    def delete(self):
        """
        Fileを削除する
        """
        # 削除しようとするFileが、フローで使用されている場合は例外を送出する
        using_flow_uuids = self.get_flow_uuids_using_me()
        if len(using_flow_uuids) > 0:
            raise Exception(f"このファイルはフロー({using_flow_uuids[0]['reference_label']})で使用しているため削除できません")

        try:
            # フレームレコードを削除する
            self._session.delete(self)
            # ファイルを削除する
            self._remove_file()
        except (Exception, OSError) as e:
            self._session.rollback()
            raise e

    def duplicate(self, new_label):
        """
        自身の複製を作成して保存する
        """
        import io
        # 複製元と同じフォルダに複製を作成する
        parent = self.find_parent()
        new_file = parent.create_frame(new_label, io.BytesIO(b''))
        # ファイルは複製元と共有する(浅いコピー)
        new_file.save(file_path=self.path, content_type=self.content_type)
        return new_file

    @property
    def content_type(self):
        return self._data.get('content_type', '')

    @property
    def file_size(self):
        if self.file_exists:
            return self._path.stat().st_size
        else:
            import warnings
            warnings.warn(f'Not Exists file path : {self._path}')
            return 0

    @property
    def file_exists(self):
        return self._path.exists()

    @property
    def modified_at_str(self):
        import time
        wk = time.localtime(self._path.stat().st_mtime)
        return time.strftime('%Y/%m/%d %H:%M', wk)

    @staticmethod
    def detect_content_type(stream):
        """
        指定されたファイルのファイルタイプを判別する
        """
        import magic

        CHUNK_SIZE = 1024

        # 0Byteファイルの場合はCSVファイルとして扱う
        if stream is None or not hasattr(stream, 'seek'):          
            return 'text/csv'

        # ファイルストリームからファイルタイプを判定する
        chunk = stream.read(CHUNK_SIZE)
        if not chunk:
            # 0Byteファイルの場合はCSVファイルとして扱う
            return 'text/csv'
        content_type = magic.from_buffer(chunk, mime=True)

        # streamの読み込み位置をリセットする
        stream.seek(0)

        # NOTE: CSVのmimetypeはCentOSとDebianで異なる?
        if content_type == 'application/csv':
            content_type = 'text/csv'

        return content_type

    def _make_file(self, path:Path):
        """
        Frameに対応するファイルを作成する
        """
        try:
            # 親ディレクトリがなければ作成する
            os.makedirs(path.parent, exist_ok=True)
            # ファイルを作成する
            self._save_file(path)
            return path
        except PermissionError as e:
            # ファイルに対する権限がない場合
            raise e
        except OSError as e:
            import errno
            # エラー発生時はファイルを削除する
            path.unlink(missing_ok=True)
            if e.errno == errno.ENOSPC:
                raise OSError(e.errno, f'ディスクに空き容量が無いため、{self.label}を作成できませんでした')
            raise e

    def _remove_file(self):
        """
        Frameに対応するファイルを削除する
        """
        try:
            # ファイルが存在しなければ削除処理はしない
            if not self._path.exists():
                import warnings
                warnings.warn(f'Not Exists file path : {self._path}')
                return
            # 自分以外で同じファイルを使用しているFrameがあれば削除しない
            if self._frame_path_exists(self._path, except_id=self.id):
                return
            if not self._path.is_file():
                raise Exception(f'Can not delete {self._path}, because it is not reguler file.')
            # ファイルを物理削除する
            self._path.unlink()
        except PermissionError as e:
            # ファイルに対する権限がない場合
            raise e

    def _save_file(self, path:Path):
        with open(path, mode='wb') as f:
            while True:
                buff = self.stream.read(self.READ_BUFFER_SIZE)
                f.write(buff)
                if buff is None or len(buff)==0:
                    break

    def _frame_path_exists(self, path:Path, except_id:int):
        result = self._session.query(SavableDatum._path).filter(SavableDatum._path == path)\
                                                .filter(SavableDatum.type == SavableDatum.FRAME_TYPE)\
                                                .filter(SavableDatum.id != except_id).count()
        return result > 0

    def to_json(self):
        ret = super().to_json()
        ret['fileSize'] = self.file_size
        return ret

