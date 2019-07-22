import uuid
import json

from pathlib import Path
from kskp.core import Datum

class Store(Datum):
    """
    datumを入れておく場所
    """
    def __init__(self, parent_uuid, type, label, creator=None, modifier=None):
        super().__init__(parent_uuid, type, label, creator=None, modifier=None)

    def save(self, datum):
        """
        override用
        """
        pass

    def load(self, uuid):
        """
        override用
        """
        pass

class FrameStore(Store):
    """
    Frameを置いておくStore
    将来的にはなくす予定
    """
    def __init__(self):
        super().__init__(None, 'framestore', None)
        self.data = {}

    def save(self):
        for frame in self.data.values():
            frame.save_result()

    def append(self, point_id, cache_point):
        self.data[point_id] = cache_point

class ModuleStore(Store):
    """
    Moduleを置いておくStore
    今は二又以上の独自コマンドを実行する際に、
    使わない方のoutput_moduleを保存しておくために使っている

    フローを実行するrunsに入れる（入れないと実行できない）
    """
    def __init__(self):
        super().__init__(None, 'modulestore', None)
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
    NysolModuleをラップするクラス
    """
    def __init__(self):
        super().__init__(None, 'nm', None)
        self._content = None

    def set_uuid(self, uuid):
        self.uuid = uuid

    def set_content(self, module):
        self._content = module

    @property
    def content(self):
        return self._content
