import uuid
import json

from pathlib import Path
from datetime import datetime, timedelta, timezone

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
        self.datum_list = []

    def save(self):
        for cache in self.datum_list:
            cache.save()

    def append(self, cache_point):
        self.datum_list.append(cache_point)

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
        import nysol.mcmd as nm
        # self.set_datum(datum, uuid)

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

class Frame(Datum):
    """
    実際の実行のrunではない時に作られ、DB保存の情報を持っている。
    storeに一旦集められてから、jobのdtorのタイミングでDBへの保存処理が走る。

    storeのメソッド内で保存しようと思ったけど、わざわざFrame（または下記のCache）クラスの中身を見て
    それを取り出して保存するのも手間が増えてるだけなので、今はstoreのsaveでこのクラスのsaveを呼び出すことにしている。
    """
    def __init__(self):
        super().__init__()
        self.info = {}

    def set_uuid(self, uuid):
        self.uuid = uuid

    def set_content(self, module):
        self._content = module

    @property
    def content(self):
        return self._content

    def set_cache_info(self, params):
        self.info = params

    def save(self):
        # フレームが作成されているか確認(run後なので作成されているはず、作成されていないと作れない)
        if not self.created:
            # とりあえずfalseを返す
            return False

        # dbに保存
        self.save_to_db()

    ##
    def save_to_db(self):
        from kskp.store import Library, FRAME_FOLDER_UUID

        frame_path = self.info.get('frame_path')
        label = self.info.get('label')
        frame = Library.save_frame(FRAME_FOLDER_UUID, label, frame_path)
        self.uuid = frame.uuid
    ##

    @property
    def created(self):
        if self.info.get('frame_path') is not None:
            return self.info.get('frame_path').exists()
        else:
            return False

class Cache(Frame):
    """
    FrameもCacheもどちらも実ファイルを生成するdatumであり、
    違いはflowのjsonを書き換えるか書き換えないか（今の所）
    ということでFrameを継承したものにしてみた。
    """
    def __init__(self):
        super().__init__()

    def save(self):
        # キャッシュが作成されているか確認
        if not self.created:
            # とりあえずfalseを返す
            return False

        # dbに保存
        self.save_to_db()

        # jsonのnodeのuuidを変更
        self.update_json_node()

    def save_to_db(self):
        from kskp.store import Library, CACHE_FOLDER_UUID

        frame_path = self.info.get('frame_path')
        label = self.info.get('label')
        frame = Library.save_frame(CACHE_FOLDER_UUID, label, frame_path)
        self.uuid = frame.uuid

    def update_json_node(self):
        if self.info.get('flow_uuid') is None:
            return

        flow_path = [path for path in Path('kskp/flows').iterdir() if path.stem == self.info.get('flow_uuid')][0]
        flow_json = json.loads(flow_path.read_text())
        for node in flow_json['nodes']:
            if node['id'] == self.info.get('datum_id'):
                node['uuid'] = self.uuid
                node['cacheCreatedAt'] = datetime.now(timezone(timedelta(hours=+9), 'JST')).strftime('%Y-%m-%d %H:%M:%S')
        flow_path.write_text(json.dumps(flow_json, ensure_ascii=False, indent=2), encoding='utf-8')

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
