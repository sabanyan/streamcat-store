import uuid
import json

from pathlib import Path
from kskp.core import Datum

# StoreはFolderとFrameStoreが継承している
# そのうちFolderについては、キャッシュと結果データは決め打ちのUUIDの指定でLibrary.save_frame()で保存できないか
# →できました。
# また、それ以外のフォルダがエンジン側で必要な場合は、Library.save_folder()で任意に作成できる
# -> Libraryに移管できないか？
#
# TODO: kskp-data-storeに移す
class Store(Datum):
    """
    できたdatumを入れておく場所
    """
    def __init__(self):
        super().__init__(None, 'store', None)

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

#
# FrameStoreはFrameとCacheの保存に用いているので
# FrameStoreを消滅させて、Library.save_frame()にその機能を移管できないか？
#
class FrameStore(Store):
    """
    Frameを置いておくStore
    """
    def __init__(self):
        super().__init__()
        self.data = {}

    def save(self):
        for frame in self.data.values():
            frame.save_result()

    def append(self, point_id, cache_point):
        self.data[point_id] = cache_point

class Folder(Store):
    """
    ディレクトリに保存するStore
    コンストラクタで指定したディレクトリに保存する
    指定したディレクトリパスはpathlibのPathオブジェクト
    """
    def __init__(self, dir_path):
        super().__init__()
        self.dir_path = dir_path

    def save(self, command, args, datum):
        args['frame_path'] = (self.dir_path / (str(uuid.uuid4()) + '.csv'))
        return command.module(args, datum)

    def load(self, uuid):
        import nysol.mcmd as nm
        from kskp.store import Library

        frame = Library.load_frame(uuid)
        if frame is None:
            raise Exception('No frame(%s) is found !' % uuid)
        path = frame.path_obj

        return nm.m2tee({'i':path.as_posix()})

    @property
    def content(self):
        return self

class NysolModule(Datum):
    """
    NysolModule1をラップするクラス
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
