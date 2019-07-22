import os
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

from . import ss as session
from kskp.core import Datum

class Frame(Datum):

    # 64MB
    READ_BUFFER_SIZE = 64 * 1024 * 1024

    def __init__(self, parent_uuid, label, stream, creator=None):
        """
        コンストラクタ
        stream : Frameデータのファイルストリームを指定する
        """
        super().__init__(parent_uuid, Datum.FRAME_TYPE, label, creator)

        # data列の値を作成する
        self.data = json.dumps({'label' : label})

        # ファイルストリームを保持する
        self.stream = stream

    @staticmethod
    def find_by_uuid(uuid):
        """
        指定されたuuidを持つFrameを取得する
        """
        # UUID値の形式チェックをする
        Datum.valid_uuid_or_raise(uuid)
        datum = session.query(Datum).filter(Datum.uuid==uuid)\
                                    .filter(Datum.type==Datum.FRAME_TYPE).one_or_none()
        if datum is None:
            # FIXIT : fetch_frame()の現在の実装ではデータの無い場合はエラーにしていない為
            # raise Exception('no frame is found by designated id.')
            return None
        return Frame.convert_to_frame(datum)

    @staticmethod
    def exists(uuid):
        """
        指定されたuuidを持つFrameが存在する場合はTrueを返す
        """
        # UUID値の形式チェックをする
        if not Datum.is_valid_uuid(uuid):
            return False
        result = session.query(Datum).filter(Datum.uuid==uuid)\
                                     .filter(Datum.type==Datum.FRAME_TYPE).count()
        return result > 0

    @staticmethod
    def convert_to_frame(datum):
        parent_uuid = Datum.get_uuid_by_id(datum.parent_id)
        label = json.loads(datum.data, encoding='utf-8')['label']
        frame = Frame(parent_uuid, label, None, datum.creator)
        frame.id = datum.id
        frame.uuid = datum.uuid
        frame._path = datum._path
        frame.modifier = datum.modifier
        frame.created_at = datum.created_at
        frame.modified_at = datum.modified_at
        return frame

    def save(self):
        """
        Frameを保存する
        """
        # 既にルートフォルダが存在する場合は、parent_id=NULLを許可しない
        if self.parent_id is None and Datum.count_root() > 0:
            raise Exception('You can not add another root frame. A root already exists.')
        # ドキュメントに紐付くファイル(path列で指定されるファイル)がなければ作成する
        path = self._make_file()
        self._path = path
        try:
            # Dataテーブルにレコードを新規追加する
            session.add(self)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            # 親フォルダのロックを解除する
            session.commit()

    def add_entry_from_path(self, file_path):
        """
        指定されたパスのファイルをFrameとして登録する
        """
        # 既にルートフォルダが存在する場合は、parent_id=NULLを許可しない
        if self.parent_id is None and Datum.count_root() > 0:
            raise Exception('You can not add another root frame. A root already exists!')
        self._path = file_path
        try:
            # Dataテーブルにレコードを新規追加する
            session.add(self)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.commit()

    @staticmethod
    def update_data(uuid, label, modifier):
        """
        Frameのdata列を更新する
        """
        # レコードを取得する
        datum = session.query(Datum).filter(Datum.uuid==uuid)\
                                    .filter(Datum.type==Datum.FRAME_TYPE).one_or_none()
        if datum is None:
            raise Exception('no frame is found by designated id.')

        # ファイルを移動する
        old_path = datum.path
        new_path = os.path.join(os.path.dirname(old_path), Datum.escape_filename(label))
        new_path = Datum.move_file(old_path, new_path)

        try:
            # 同じファイルに対応するドキュメントのpath列を、ファイル名の移動に合わせて変更する
            session.query(Datum).filter(Datum._path==old_path).update({'_path'   :new_path,
                                                                       'modifier':modifier})
            # レコードを更新する
            data = json.dumps({'label' : label})
            session.query(Datum).filter(Datum.uuid==uuid).update({'data'    :data,
                                                                  'modifier':modifier})
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.commit()

        return Frame.convert_to_frame(datum)

    def delete(self):
        """
        Frameを削除する
        """
        # 削除しようとするframeが、DBに格納されているフローで使用されている場合は例外を送出する
        using_flow_uuids = Datum.get_flow_uuids_using_other_datum(self.uuid)
        if len(using_flow_uuids) > 0:
            from kskp.store import Flow
            using_flow_label= Flow.find_by_uuid(using_flow_uuids[0]).label
            raise Exception('このCSVファイルはフロー(%s)で使用しているため削除できません' % using_flow_label)

        try:
            # フレームレコードを削除する
            session.query(Datum).filter(Datum.id==self.id)\
                                .filter(Datum.type==Datum.FRAME_TYPE).delete()
            # ファイルを削除する
            self._remove_file()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.commit()

    def remove_reference_only(self):
        """
        Frameを削除するが、対応するファイルは削除しない
        (テストにおいてテスト用ファイルを削除したくない場合に使用する)
        """
        try:
            # フレームレコードを削除する
            session.query(Datum).filter(Datum.id==self.id)\
                                .filter(Datum.type==Datum.FRAME_TYPE).delete()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.commit()

    @property
    def label(self):
        return json.loads(self.data, encoding='utf-8')['label']

    def _make_file(self):
        """
        Frameに対応するファイルを作成する
        """
        try:
            # 同じ名称のファイルが既に存在する場合、末尾に数字を付加したファイル名で作成する
            path = Datum.get_another_file_path(self._path)
            # ドキュメントに紐付くファイル(path列で指定されるファイル)がなければ作成する
            dir_name = os.path.dirname(path)
            os.makedirs(dir_name, exist_ok=True)
            # ファイルを作成する
            self._save_file(path)
            return path
        except PermissionError as e:
            # ファイルに対する権限がない場合
            raise e

    def _remove_file(self):
        """
        Frameに対応するファイルを削除する
        """
        try:
            # ファイルが存在しなければ削除処理はしない
            if not os.path.exists(self._path):
                return
            # 自分以外で同じファイルを使用しているFrameがあれば削除しない
            if Frame._frame_path_exists(self._path, except_id=self.id):
                return
            if not os.path.isfile(self._path):
                raise Exception('Can not delete %s, because it is not reguler file.' % self._path)
            # ファイルを物理削除する
            os.remove(self._path)
        except PermissionError as e:
            # ファイルに対する権限がない場合
            raise e

    def _save_file(self, path):
        with open(path, mode='wb') as f:
            while True:
                buff = self.stream.read(self.READ_BUFFER_SIZE)
                f.write(buff)
                if buff is None or len(buff)==0:
                    break

    @staticmethod
    def _frame_path_exists(path, except_id):
        result = session.query(Datum._path).filter(Datum._path == path)\
                                           .filter(Datum.type == Datum.FRAME_TYPE)\
                                           .filter(Datum.id != except_id).count()
        return result > 0

    def to_json(self):
        return {'uuid'      : self.uuid,
                'type'      : Datum.FRAME_TYPE,
                'label'     : json.loads(self.data, encoding='utf-8')['label'],
                'creator'   : Datum.get_user_name_by_user_id(self.creator),
                'createdAt' : self.created_at_str}

    # for engine
    def set_centext(self, params):
        self.context = params

    def save_result(self):
        # フレームが作成されているか確認(run後なので作成されているはず、作成されていないと作れない)
        if not self.created:
            # とりあえずfalseを返す
            return False

        # dbに保存
        self.save_to_db()

    def save_to_db(self):
        self.data = json.dumps({'label' : self.context.get('label')})
        self.add_entry_from_path(self.context.get('frame_path').as_posix())

    def set_content(self, module):
        self._content = module

    @property
    def content(self):
        return self._content

    @property
    def created(self):
        if self.context.get('frame_path') is not None:
            return self.context.get('frame_path').exists()
        else:
            return False

class Cache(Frame):
    """
    FrameもCacheもどちらも実ファイルを生成するdatumであり、
    違いはflowのjsonを書き換えるか書き換えないか（今の所）
    ということでFrameを継承したものにしてみた。
    """
    def __init__(self, parent_uuid, label, stream, creator=None):
        super().__init__(parent_uuid, label, stream, creator)

    def save_result(self):
        # キャッシュが作成されているか確認
        if not self.created:
            # とりあえずfalseを返す
            return False

        # dbに保存
        self.save_to_db()

        # jsonのnodeのuuidを変更
        # self.update_json_flow()
        self.update_flow(self.creator)

    # def update_json_flow(self):
    #     if self.context.get('flow_uuid') is None:
    #         return

    #     from kskp.store import FLOW_PATH

    #     flow_path = [path for path in Path(FLOW_PATH).iterdir() if path.stem == self.context.get('flow_uuid')][0]
    #     flow_json = json.loads(flow_path.read_text())
    #     self._update_node(flow_json)
    #     flow_path.write_text(json.dumps(flow_json, ensure_ascii=False, indent=2), encoding='utf-8')

    def update_flow(self, modifier):
        from kskp.store import Flow
        if self.context.get('flow_uuid') is None:
            return
        flow = Flow.find_by_uuid(self.context.get('flow_uuid'))
        flow_json = json.loads(flow.data, encoding='utf-8')['flow']
        self._update_node(flow_json)
        Flow.update_data(flow.uuid, flow.label, flow_json, modifier)

    def _update_node(self, flow_json):
        for node in flow_json['nodes']:
            if node['id'] == self.context.get('datum_id'):
                node['uuid'] = self.uuid
                node['cacheCreatedAt'] = datetime.now(timezone(timedelta(hours=+9), 'JST')).strftime('%Y-%m-%d %H:%M:%S')