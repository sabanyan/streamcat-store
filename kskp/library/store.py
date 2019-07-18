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
