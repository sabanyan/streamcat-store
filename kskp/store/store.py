import uuid
import json

from pathlib import Path
from kskp.core import Datum

class Store(Datum):
    """
    Storeを表す
    (StoreとはLoaderの入力元となり得る、またはSaverの出力先となり得るもの)
    """
    def __init__(self, parent_uuid, type, label, creator=None):
        super().__init__(parent_uuid, type, label, creator)

    @staticmethod
    def find_by_uuid(uuid):
        """
        指定されたuuidを持つStoreレコードを取得する
        """
        from kskp.store import ss as session
        store = session.query(Datum).filter(Datum.uuid==uuid)\
                                    .filter(Datum.type!=Datum.FRAME_TYPE)\
                                    .filter(Datum.type!=Datum.FLOW_TYPE).one_or_none()
        if store is None:
            raise Exception('no store is found by designated id.')
        return Store.convert_to_store(store)

    @staticmethod
    def convert_to_store(datum):
        parent_uuid = Datum.get_uuid_by_id(datum.parent_id)
        store = Store(parent_uuid, datum.type, datum.label, datum.creator)
        store.id = datum.id
        store.uuid = datum.uuid
        store._path = datum._path
        store.data = datum.data
        store.modifier = datum.modifier
        store.created_at = datum.created_at
        store.modified_at = datum.modified_at
        return store

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

    def append(self, point_id, datum):
        self.data[point_id] = datum

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
