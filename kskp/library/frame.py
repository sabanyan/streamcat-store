from kskp.core import Datum
import os
import json

from . import session

class Frame(Datum):

    # 64MB
    READ_BUFFER_SIZE = 64 * 1024 * 1024

    def __init__(self, parent_uuid, label, stream, creator=None, modifier=None):
        """
        コンストラクタ
        stream : Frameデータのファイルストリームを指定する
        """
        super().__init__(parent_uuid, Datum.FRAME_TYPE, label, creator, modifier)

        # data列の値を作成する
        self.data = json.dumps({'label' : label})

        # ファイルストリームを保持する
        self.stream = stream

    @staticmethod
    def find_by_uuid(uuid):
        """
        指定されたuuidを持つFrameを取得する
        """
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
        result = session.query(Datum).filter(Datum.uuid==uuid)\
                                        .filter(Datum.type==Datum.FRAME_TYPE).count()
        return result > 0

    @staticmethod
    def convert_to_frame(datum):
        parent_uuid = Datum.get_uuid_by_id(datum.parent_id)
        label = json.loads(datum.data, encoding='utf-8')['label']
        frame = Frame(parent_uuid, label, None, datum.creator, datum.modifier)
        frame.id = datum.id
        frame.uuid = datum.uuid
        frame.path = datum.path
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
        self.path = path
        try:
            # 親フォルダが削除されないようロックする

            # 親フォルダの存在を確認する

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
        self.path = file_path
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
            session.query(Datum).filter(Datum.path==old_path).update({'path'       :new_path,
                                                                         'modifier'   :modifier,
                                                                         'modified_at':Datum.get_current_time_str()})
            # レコードを更新する
            data = json.dumps({'label' : label})
            session.query(Datum).filter(Datum.uuid==uuid).update({'data'       :data,
                                                                     'modifier'   :modifier,
                                                                     'modified_at':Datum.get_current_time_str()})
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

    def _make_file(self):
        """
        Frameに対応するファイルを作成する
        """
        try:
            # 同じ名称のファイルが既に存在する場合、末尾に数字を付加したファイル名で作成する
            path = Datum.get_another_file_path(self.path)
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
            if os.path.exists(self.path):
                if not os.path.isfile(self.path):
                    raise Exception('Can not delete %s, because it is not reguler file.' % self.path)
                # ファイルを物理削除する
                os.remove(self.path)
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

    def to_json(self):
        return {'uuid'      : self.uuid,
                'type'      : Datum.FRAME_TYPE,
                'label'     : json.loads(self.data, encoding='utf-8')['label'],
                'creator'   : Datum.get_user_name_by_user_id(self.creator),
                'createdAt' : self.created_at}
