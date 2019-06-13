import uuid
import json
from pathlib import Path
from kskps.core import Command, Datum
from datetime import datetime, timedelta, timezone

from .. import Library
from .. import FRAME_FOLDER_UUID
from .. import CACHE_FOLDER_UUID

from .store import Store, NysolModule

# # TODO: kskp-data-storeに移す
# class Store(Datum):
#     """
#     できたdatumを入れておく場所
#     """
#     def __init__(self):
#         super().__init__()
#         self.data = {} # dict keyはUUID、valはdatum？

#     def issue_uuid(self):
#         """
#         uuidを発行する
#         """
#         new_uuid = str(uuid.uuid4())
#         self.data[new_uuid] = None
#         return new_uuid

#     def set_datum(self, datum, uuid):
#         """
#         指定したuuidとdatumを対応づけて保存しておく
#         """
#         if self.data[uuid] is None:
#             self.data[uuid] = datum
#         else:
#             # 上書きするか、Falseを返すかどうしよう？
#             pass

#         return True

#     def save(self, datum):
#         """
#         override用
#         """
#         pass

#     def load(self, uuid):
#         """
#         override用
#         """
#         pass

class Folder(Store):
    """
    ディレクトリに保存するStore
    コンストラクタで指定したディレクトリに保存する
    指定したディレクトリパスはpathlibのPathオブジェクト
    """
    def __init__(self, dir_path):
        super().__init__()
        self.dir_path = dir_path

    ##
    def save(self, args, datum, uuid):
        import nysol.mcmd as nm
        self.set_datum(datum, uuid)

        args['frame_path'] = (self.dir_path / (uuid + '.csv'))

        frame = Library.save_frame(FRAME_FOLDER_UUID, uuid, args['frame_path'])

        command_args = {}
        command_args['i'] = datum
        # command_args['o'] = args['frame_path'].as_posix()
        command_args['o'] = frame.path

        return nm.m2tee(command_args)
    ##

    ##
    def load(self, uuid):
        import nysol.mcmd as nm

        # TODO: 本当はuuidを使ってdbからcsvの場所を取ってくる
        # 今はとりあえず直接取ってくる(uuid==csvのファイル名)
        # path = None
        # for frame_path in self.dir_path.iterdir():
        #     if frame_path.stem == uuid:
        #         path = frame_path
        #         break
        frame = Library.load_frame(uuid)
        if frame is None:
            raise Exception('No frame(%s) is found !' % uuid)
        path = frame.path_obj

        nysol_module = NysolModule()
        nysol_module.set_content(nm.m2tee({'i':path.as_posix()}))

        return nysol_module
    ##

    @property
    def content(self):
        return self

# class FrameStore(Store):
#     """
#     Frameを置いておくStore
#     """
#     def __init__(self):
#         super().__init__()
#         self.datum_list = []

#     def save(self):
#         for cache in self.datum_list:
#             cache.save()

#     def append(self, cache_point):
#         self.datum_list.append(cache_point)


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
        # キャッシュが作成されているか確認
        if not self.created:
            # とりあえずfalseを返す
            return False

        # dbに保存
        self.save_to_db()

    ##
    def save_to_db(self):
        # TODO: DBと連携するようになったら処理を記載する
        # この2つがあれば最低限登録できる・・・と思っている。。。
        # uuid・・・self.uuid
        # path・・・self.info.get('frame_path')（saverで付与済み）
        frame_path = self.info.get('frame_path')
        Library.save_frame(FRAME_FOLDER_UUID, 'フレームのラベル名', frame_path)
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

    ##
    def save_to_db(self):
        frame_path = self.info.get('frame_path')
        Library.save_frame(CACHE_FOLDER_UUID, 'キャッシュののラベル名', frame_path)
    ##

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
