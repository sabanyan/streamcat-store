from pathlib import Path

from kskp.store import RESULT_FOLDER_UUID, RESULT_FOLDER_LABEL
from kskp.store import CACHE_FOLDER_UUID, CACHE_FOLDER_LABEL

from kskp.core  import Datum
from kskp.store import Folder
from kskp.store import AwsS3
from kskp.store import Frame
from kskp.store import Flow

class Library:
    """
    ライブラリ機能のFacadeパターン
    """

    @staticmethod
    def load_root(creator=None):
        """
        ルートデータストアを取得する
        """
        return Library._get_library(creator)

    @staticmethod
    def load_result_folder(creator=None):
        return Library._get_result_dir_path(creator)

    @staticmethod
    def load_cache_folder(creator=None):
        """
        キャッシュフォルダを取得する
        """
        return Library._get_cache_dir_path(creator)

    @staticmethod
    def load_flow_folder(creator=None):
        """
        フローフォルダを取得する
        """
        return Library._get_flow_dir_path(creator)

    @staticmethod
    def load_trash_folder(creator=None):
        """
        ゴミ箱フォルダを取得する
        """
        return Library._get_trash_dir_path(creator)

    @staticmethod
    def load_frame(frame_uuid):
        """
        フレームを取得する

        frame_uuid : フレームのUUID
        戻り値      : Frameオブジェクト
        """
        return Frame.find_by_uuid(frame_uuid)

    @staticmethod
    def save_frame(parent_uuid, label, path, creator=None):
        """
        フレームを追加する

        parent_uuid : 親フォルダのUUID
        label       : ラベル名
        path        : フレームファイルのパス
        戻り値       : Frameオブジェクト

        Fix it : add_frameに改名した方が良いか？
        """
        import io
        new_frame = Frame(parent_uuid,
                          label,
                          io.BytesIO(b''),
                          creator)
        # documentレコードをDBに格納する
        new_frame.add_entry_from_path(path)
        return new_frame

    @staticmethod
    def save2_frame(parent_uuid, label, stream, creator=None):
        """
        フレームを作成する
        """
        new_frame = Frame(parent_uuid,
                          label,
                          stream,
                          creator)
        # documentレコードをDBに格納する
        new_frame.save()
        return new_frame

    @staticmethod
    def update_frame_data(frame_uuid, label, modifier=None):
        """
        フレームのラベル名を変更する
        """
        return Frame.update_data(frame_uuid, label, modifier)

    @staticmethod
    def delete_frame(frame_uuid):
        """
        フレームを削除する

        frame_uuid : フレームのUUID
        戻り値      : なし
        """
        frame = Frame.find_by_uuid(frame_uuid)
        if frame is None:
            raise Exception('no frame exists.')

        # フレームを削除する
        frame.delete()


    @staticmethod
    def load_flow(flow_uuid):
        """
        フローを取得する

        flow_uuid  : フローのUUID
        戻り値      : Flowオブジェクト
        """
        return Flow.find_by_uuid(flow_uuid)

    @staticmethod
    def save_flow(parent_uuid, label, flow_data, creator=None):
        """
        フローを追加する

        parent_uuid : 親フォルダのUUID
        label       : ラベル名
        flow_data   : フローデータ
        戻り値       : Flowオブジェクト
        """
        new_flow = Flow(parent_uuid,
                        label,
                        flow_data,
                        creator)
        new_flow.save()
        return new_flow

    @staticmethod
    def update_flow_data(flow_uuid, label, flow_data, modifier=None):
        """
        フローのを変更する
        """
        return Flow.update_data(flow_uuid, label, flow_data, modifier)

    @staticmethod
    def delete_flow(flow_uuid):
        """
        フレームを削除する

        flow_uuid  : フローのUUID
        戻り値      : なし
        """
        flow = Flow.find_by_uuid(flow_uuid)
        if flow is None:
            raise Exception('no flow exists.')

        # フレームを削除する
        flow.delete()


    @staticmethod
    def load_folder(folder_uuid):
        """
        フォルダを取得する
        """
        return Folder.find_by_uuid(folder_uuid)

    @staticmethod
    def update_folder_data(folder_uuid, label, modifier=None):
        """
        フォルダのラベル名を変更する
        """
        return Folder.update_data(folder_uuid, label, modifier)

    @staticmethod
    def save_folder(parent_uuid, label, creator=None):
        """
        フォルダを作成する
        """
        new_folder = Folder(parent_uuid,
                            label,
                            creator)
        new_folder.save()
        return new_folder

    @staticmethod
    def delete_folder(folder_uuid):
        """
        フォルダを削除する
        """
        folder = Folder.find_by_uuid(folder_uuid)
        folder.delete()

    @staticmethod
    def load_awss3(awss3_uuid):
        """
        AWS S3フォルダを取得する
        """
        return AwsS3.find_by_uuid(awss3_uuid)

    @staticmethod
    def update_awss3_data(awss3_uuid, label, bucket, modifier=None):
        """
        AWS S3フォルダのラベル名を変更する
        """
        return AwsS3.update_data(awss3_uuid, label, bucket, modifier)

    @staticmethod
    def save_awss3(parent_uuid, label, bucket, creator=None):
        """
        AWS S3フォルダを作成する
        """
        new_awss3 = AwsS3(parent_uuid,
                          label,
                          bucket,
                          creator)
        new_awss3.save()
        return new_awss3

    @staticmethod
    def delete_awss3(awss3_uuid):
        """
        AWS S3フォルダを削除する
        """
        awss3 = AwsS3.find_by_uuid(awss3_uuid)
        awss3.delete()


    @staticmethod
    def _init_library_folders():
        Library._get_result_dir_path()
        Library._get_cache_dir_path()
        Library._get_flow_dir_path()
        Library._get_trash_dir_path()

    @staticmethod
    def _get_flow_dir_path(user_id=None):
        # フロー格納フォルダを取得する
        from kskp.store import FLOW_FOLDER_UUID, FLOW_FOLDER_LABEL
        return Library._get_or_make_dir_path(FLOW_FOLDER_UUID, FLOW_FOLDER_LABEL, user_id)

    @staticmethod
    def _get_result_dir_path(user_id=None):
        # フレーム格納フォルダを取得する
        return Library._get_or_make_dir_path(RESULT_FOLDER_UUID, RESULT_FOLDER_LABEL, user_id)

    @staticmethod
    def _get_cache_dir_path(user_id=None):
        # キャッシュ格納フォルダを取得する
        return Library._get_or_make_dir_path(CACHE_FOLDER_UUID, CACHE_FOLDER_LABEL, user_id)

    @staticmethod
    def _get_trash_dir_path(user_id=None):
        # ゴミ箱フォルダを取得する
        from kskp.store import TRASH_FOLDER_UUID, TRASH_FOLDER_LABEL
        return Library._get_or_make_dir_path(TRASH_FOLDER_UUID, TRASH_FOLDER_LABEL, user_id)

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
                            user_id)
            # Folderのコンストラクタで付番したUUIDを捨てて、特定用途のフォルダのUUIDを格納する
            folder.uuid = uuid
            folder.save()
        return folder

    @staticmethod
    def _get_library(user_id=None):
        """
        ルートデータストアを取得する、存在しない場合は作成する
        """
        root = Library._convert_type(Datum.find_root())
        # ルートフォルダが存在しない場合はルートフォルダを作成する
        # (最初にライブラリ画面にアクセスする時はルートフォルダ自身も存在しません)
        if root is None:
            new_root = Folder(parent_uuid=None,
                              label='ROOT_FOLDER',
                              creator=user_id)
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
        elif datum.type == Datum.AWSS3_TYPE:
            return AwsS3.convert_to_awss3(datum)
        elif datum.type == Datum.FRAME_TYPE:
            return Frame.convert_to_frame(datum)
        elif datum.type == Datum.FLOW_TYPE:
            return Flow.convert_to_flow(datum)
        elif datum.type == Datum.DATABASE_TYPE:
            return Database.convert_to_database(datum)
        else:
            raise Exception('Undefined type of datum is found!')
