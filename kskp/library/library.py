from pathlib import Path

from kskp.library import FRAME_FOLDER_UUID, FRAME_FOLDER_LABEL
from kskp.library import CACHE_FOLDER_UUID, CACHE_FOLDER_LABEL

from kskp.library import Datum
from kskp.library import Frame
from kskp.library import Folder

class Library:

    @staticmethod
    def save_frame(parent_uuid, label, path, creator=None, modifier=None):
        """
        フレームを保存する

        parent_uuid : 親フォルダのUUID
        label       : ラベル名
        path        : フレームファイルのパス
        戻り値       : Frameオブジェクト
        """
        # フレームを格納するフォルダがなければ作成する
        Library._init_library_folders()

        new_frame = Frame(parent_uuid,
                          label,
                          None,
                          creator,
                          modifier)
        # documentレコードをDBに格納する
        new_frame.add_entry_from_path(path.as_posix())
        return new_frame

    @staticmethod
    def load_frame(frame_uuid):
        """
        フレームを取得する

        frame_uuid : フレームのUUID
        戻り値      : Frameオブジェクト
        """
        # フレームを格納するフォルダがなければ作成する
        Library._init_library_folders()

        return Frame.find_by_uuid(frame_uuid)

    @staticmethod
    def delete_frame(frame_uuid):
        """
        フレームを削除する

        frame_uuid : フレームのUUID
        戻り値      : なし
        """
        # フレームを格納するフォルダがなければ作成する
        Library._init_library_folders()

        frame = Frame.find_by_uuid(frame_uuid)
        if frame is None:
            raise Exception('no frame exists.')

        # フレームを削除する
        frame.delete()

    @staticmethod
    def _init_library_folders():
        Library._get_frame_dir_path()
        Library._get_cache_dir_path()

    @staticmethod
    def _get_frame_dir_path(user_id=None):
        # フレーム格納フォルダを取得する
        return Library._get_or_make_dir_path(FRAME_FOLDER_UUID, FRAME_FOLDER_LABEL, user_id)

    @staticmethod
    def _get_cache_dir_path(user_id=None):
        # キャッシュ格納フォルダを取得する
        return Library._get_or_make_dir_path(CACHE_FOLDER_UUID, CACHE_FOLDER_LABEL, user_id)

    @staticmethod
    def _get_or_make_dir_path(uuid, label, user_id=None):

        # 特定用途のフォルダのUUIDは決め打ちである
        if Folder.exists(uuid):
            folder = Folder.find_by_uuid(uuid)
        else:
            # フォルダが無い場合は作成する
            root = Library._get_library(user_id)
            folder = Folder(root.uuid,
                            label,
                            user_id,
                            user_id)
            # Folderのコンストラクタで付番したUUIDを捨てて、特定用途のフォルダのUUIDを格納する
            folder.uuid = uuid
            folder.save()
        return folder

    @staticmethod
    def _get_library(user_id):
        """
        ルートデータストアを取得する、存在しない場合は作成する
        """
        root = Library._convert_type(Datum.find_root())
        # ルートフォルダが存在しない場合はルートフォルダを作成する
        # (最初にライブラリ画面にアクセスする時はルートフォルダ自身も存在しません)
        if root is None:
            new_root = Folder(parent_uuid=None,
                              label='ROOT_FOLDER',
                              creator=user_id,
                              modifier=user_id)
            # folderレコードをDBに格納する
            new_root.save()
            root = new_root
        return root

    @staticmethod
    def _convert_type(datum):
        if datum is None:
            return None
        elif datum.type == Datum.FOLDER_TYPE:
            return Folder.convert_to_folder(datum)
        elif datum.type == Datum.FRAME_TYPE:
            return Frame.convert_to_frame(datum)
        else:
            raise Exception('Undefined type of datum is found!')