from typing import Iterator
from streamcat.core import Datum, SCatBaseModel

class Store(Datum):
    """
    Storeを表す
    (StoreとはLoaderの入力元となり得る、またはSaverの出力先となり得るもの)
    """
    def __init__(self, session, parent, type, label):
        super().__init__(session, parent, type, label)

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

        rel_path = Datum._to_rel_path(dir_path)

        results = self._session.query(Datum._path)\
                 .filter(Datum._path.like(rel_path.as_posix() + '%'))\
                 .filter(Datum.id != except_id).all()

        for result in results:
            if result._path == dir_path:
                return True
            if os.path.commonpath([result._path, dir_path]) == dir_path:
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


class ModuleStore(Store):
    """
    Moduleを置いておくStore
    今は二又以上の独自コマンドを実行する際に、
    使わない方のoutput_moduleを保存しておくために使っている

    フローを実行するrunsに入れる（入れないと実行できない）
    """
    def __init__(self):
        super().__init__(None, None, 'modulestore', None)
        self.data = []

    def append(self, module):
        self.data.append(module)

    def extend(self, module_list):
        self.data.extend(module_list)

    @property
    def module_list(self):
        return self.data

class NysolModule(Datum):
    """
    nysol_pythonコマンドをラップするクラス
    """
    def __init__(self, nysol_cmd=None):
        super().__init__(None, None, 'mcmd', self._get_name(nysol_cmd))
        self._content = nysol_cmd
        self._encoding = None

    def set_content(self, module):
        self._content = module

    def _get_name(self, nysol_cmd):
        if nysol_cmd is None:
            return None
        else:
            return nysol_cmd.__class__.__name__

    @property
    def content(self):
        return self._content

    @property
    def encoding(self):
        return self._encoding

    @encoding.setter
    def encoding(self, encoding):
        self._encoding = encoding

    def __ilshift__(self, other):
        raise Exception(f'NysolModule({str(self._content)})に"<<="演算子は使えません')

class BeamModule(Datum):
    """
    Apache Beam PTransformをラップするクラス
    """
    def __init__(self, beam_cmd=None):
        super().__init__(None, None, 'beam', self._get_name(beam_cmd))
        self._content = beam_cmd

    def _get_name(self, beam_cmd):
        if beam_cmd is None:
            return None
        else:
            return beam_cmd.__class__.__name__

    @property
    def content(self):
        return self._content

class Matrix(Datum):
    """
    行列型のデータを表す
    """
    def __init__(self, content:list=None):
        super().__init__(None, None, 'matrix', None)
        self._content = content
        self._encoding = None

    def set_content(self, content):
        self._content = content

    @property
    def content(self):
        # import nysol.mcmd as nm
        # return nm.m2tee(i=self._content)
        return self._content

    @property
    def encoding(self):
        return self._encoding

    @encoding.setter
    def encoding(self, encoding):
        self._encoding = encoding

    def __ilshift__(self, other):
        raise Exception(f'Matrix({str(self._content)})に"<<="演算子は使えません')

    def __getitem__(self, index):
        return self._content[index]

    def __len__(self):
        return len(self._content)

class Stream(Datum):
    """
    ストリーム構造のデータを表す
    """
    def __init__(self, connection=None):
        super().__init__(None, None, 'stream', None)
        self._content = connection
        self._encoding = None

    def set_content(self, content):
        self._content = content

    @property
    def content(self):
        raise NotImplementedError('content')

    @property
    def encoding(self):
        return self._encoding

    @encoding.setter
    def encoding(self, encoding):
        self._encoding = encoding

    def __ilshift__(self, other):
        raise Exception(f'List({str(self._content)})に"<<="演算子は使えません')

    def __iter__(self) -> Iterator[list]:
        for line in open(self._content):
            yield SCatBaseModel.split(line)

    def dtor(self):
        """
        終了処理
        """
        # 名前付きパイプを削除する
        self._content.unlink()

class ApparentOut(Store):
    """
    フローの出力ポートと出力結果を保持する
    (フローエディタから見た見かけのout)
    """
    def __init__(self, out_point, datum, exs=None):
        super().__init__(None, None, 'out', None)
        self.out_point = out_point
        self.datum = datum
        self.exs = exs

    @property
    def has_exs(self):
        return self.exs is not None and len(self.exs) > 0

    @property
    def has_list(self):
        return self.datum is not None and isinstance(self.datum, Matrix)

    @property
    def has_frame(self):
        from streamcat.store import Frame
        return self.datum is not None and isinstance(self.datum, Frame)

    @property
    def has_cache(self):
        from streamcat.store import Frame
        return self.datum is not None and isinstance(self.datum, Frame) and self.datum.is_cache
