from collections import Iterator
from streamcat.core import Datum, Store, SCatBaseModel

class ModuleStore(Store):
    """
    Moduleを置いておくStore
    今は二又以上の独自コマンドを実行する際に、
    使わない方のoutput_moduleを保存しておくために使っている

    フローを実行するrunsに入れる（入れないと実行できない）
    """
    def __init__(self):
        super().__init__('modulestore', None)
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
        super().__init__('mcmd', self._get_name(nysol_cmd))
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
    def __init__(self, ptransform=None):
        super().__init__('beam', self._get_name(ptransform))
        self._content = ptransform
        self._encoding = None

    def _get_name(self, ptransform):
        if ptransform is None:
            return None
        else:
            return ptransform.__class__.__name__

    @property
    def content(self):
        return self._content

    @property
    def encoding(self):
        return self._encoding

    @encoding.setter
    def encoding(self, encoding):
        self._encoding = encoding

class Matrix(Datum):
    """
    行列型のデータを表す
    """
    def __init__(self, content:list=None):
        super().__init__('matrix', None)
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
        super().__init__('stream', None)
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
