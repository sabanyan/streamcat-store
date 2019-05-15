import uuid

from kskp.core import Datum

# TODO: kskp-data-storeに移す
class Store(Datum):
    """
    できたdatumを入れておく場所
    """
    def __init__(self):
        super().__init__()
        self.data = {} # dict keyはUUID、valはdatum？

    def issue_uuid(self):
        """
        uuidを発行する
        """
        new_uuid = str(uuid.uuid4())
        self.data[new_uuid] = None
        return new_uuid

    def set_datum(self, datum, uuid):
        """
        指定したuuidとdatumを対応づけて保存しておく
        """
        if self.data[uuid] is None:
            self.data[uuid] = datum
        else:
            # 上書きするか、Falseを返すかどうしよう？
            pass

        return True

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
    """
    def __init__(self):
        super().__init__()
        self.datum_list = []

    def save(self):
        for cache in self.datum_list:
            cache.save()

    def append(self, cache_point):
        self.datum_list.append(cache_point)


class NysolModule(Datum):
    """
    NysolModule1をラップするクラス
    """
    def __init__(self):
        super().__init__()
        self._content = None

    def set_uuid(self, uuid):
        self.uuid = uuid

    def set_content(self, module):
        self._content = module

    @property
    def content(self):
        return self._content
