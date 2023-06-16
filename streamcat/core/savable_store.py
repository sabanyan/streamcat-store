from .store import Store
from .savable_datum import SavableDatum

class SavableStore(Store, SavableDatum):
    """
    データベースに保存可能なStore
    """

    # SQLAlchemyにおいてdataテーブルからのマッピング対象クラスでないことを定義する
    __mapper_args__ = {
        'polymorphic_identity' : 'i_am_not_mapping_class_0'
    }

    def __init__(self, session, parent, type, label):
        # Store, SavableDatumの順に親クラスのコンストラクタを実行する
        Store.__init__(self, type, label)
        SavableDatum.__init__(self, session, parent, type, label)

    def _make_dir(self, path):
        """
        Folderに対応するディレクトリを作成する
        """
        import os
        try:
            # フォルダに紐付くディレクトリ(path列で指定されるディレクトリ)がなければ作成する
            if not path.is_dir():
                os.makedirs(path, exist_ok=True)
            return path
        except PermissionError as e:
            # ファイルに対する権限がない場合
            raise e

    def _remove_dir(self, path):
        """
        Folderに対応するディレクトリを削除する
        """
        from streamcat.store import Mountable

        # 全てのフォルダから紐づかないディレクトリは物理削除する
        dir_path = path
        try:
            while dir_path != '' and dir_path != '/':
                # 自分以外で同じディレクトリパス(相対パス)を使用しているフォルダの有無を確認する
                if self._dir_path_exists(dir_path, except_id=self.id):
                    break
                elif Mountable.is_mount(dir_path):
                    # マウント中のフォルダは削除しない
                    break
                else:
                    if dir_path.is_dir():
                        dir_path.rmdir()
                    dir_path = dir_path.parent
        except PermissionError as e:
            # ディレクトリに対する権限がない場合
            raise e
        except OSError as e:
            import errno
            if e.errno == errno.ENOTEMPTY:
                # [Errno 39] Directory not empty
                file_path = next(dir_path.glob('*'))
                raise OSError(e.errno, f'Directory({dir_path}) is not removed. File({file_path}) exists in Directory')
            raise e

    def _dir_path_exists(self, dir_path, except_id):
        import os

        rel_path = SavableDatum._to_rel_path(dir_path)

        results = self._session.query(SavableDatum._path)\
                 .filter(SavableDatum._path.like(rel_path.as_posix() + '%'))\
                 .filter(SavableDatum.id != except_id).all()

        for result in results:
            if result._path == dir_path:
                return True
            if os.path.commonpath([result._path, dir_path]) == dir_path.as_posix():
                return True
        return False

    # def save(self, datum):
    #     """
    #     override用
    #     """
    #     pass

    # def load(self, uuid):
    #     """
    #     override用
    #     """
    #     pass
