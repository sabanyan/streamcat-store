from pathlib import Path

from kskp.core  import Datum
from kskp.store import Folder
from kskp.store import AwsS3
from kskp.store import Frame
from kskp.store import Flow

from kskp.store.factory import Factory, UnAuthzFactory

class Library:
    """
    古いのでもう使わないで！
    """

    @staticmethod
    def load_root(creator=None):
        """
        ルートデータストアを取得する
        """
        with Factory(creator) as factory:
            return factory.data.load_root()

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
    def load_frame(frame_uuid):
        """
        フレームを取得する

        frame_uuid : フレームのUUID
        戻り値      : Frameオブジェクト
        """
        with UnAuthzFactory() as factory:
            admin_user = factory.find_user_by_email('admin@kskp.io')
        with Factory(admin_user) as factory:
            return factory.data.find_by_uuid(frame_uuid)

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
        with Factory(creator) as factory:
            parent = factory.data.find_by_uuid(parent_uuid)
            new_frame = parent.create_frame(label, io.BytesIO(b''))
            # documentレコードをDBに格納する
            new_frame.add_entry_from_path(path)
            # save()によりreadable=Noneになるため再取得する
            return factory.data.find_by_uuid(new_frame.uuid)

    @staticmethod
    def save2_frame(parent_uuid, label, stream, creator=None):
        """
        フレームを作成する
        """
        with Factory(creator) as factory:
            parent = factory.data.find_by_uuid(parent_uuid)
            new_frame = parent.create_frame(label, stream)
            # documentレコードをDBに格納する
            new_frame.save()
            # save()によりreadable=Noneになるため再取得する
            return factory.data.find_by_uuid(new_frame.uuid)

    @staticmethod
    def update_frame_data(frame_uuid, label, modifier=None):
        """
        フレームのラベル名を変更する
        """
        with Factory(modifier) as factory:
            frame = factory.data.find_by_uuid(frame_uuid)
            return frame.update_data(label)

    @staticmethod
    def delete_frame(frame_uuid):
        """
        フレームを削除する

        frame_uuid : フレームのUUID
        戻り値      : なし
        """
        with UnAuthzFactory() as factory:
            admin_user = factory.find_user_by_email('admin@kskp.io')
        with Factory(admin_user) as factory:
            frame = factory.data.find_by_uuid(frame_uuid)
            frame.delete()

    @staticmethod
    def load_flow(flow_uuid):
        """
        フローを取得する

        flow_uuid  : フローのUUID
        戻り値      : Flowオブジェクト
        """
        with UnAuthzFactory() as factory:
            admin_user = factory.find_user_by_email('admin@kskp.io')
        with Factory(admin_user) as factory:
            return factory.data.find_by_uuid(flow_uuid)

    @staticmethod
    def save_flow(parent_uuid, label, flow_data, creator=None):
        """
        フローを追加する

        parent_uuid : 親フォルダのUUID
        label       : ラベル名
        flow_data   : フローデータ
        戻り値       : Flowオブジェクト
        """
        with Factory(creator) as factory:
            parent = factory.data.find_by_uuid(parent_uuid)
            new_flow = parent.create_flow(label, flow_data)
            new_flow.save()
            # save()によりreadable=Noneになるため再取得する
            return factory.data.find_by_uuid(new_flow.uuid)

    @staticmethod
    def update_flow_data(flow_uuid, label, flow_data, modifier=None):
        """
        フローのを変更する
        """
        with Factory(modifier) as factory:
            flow = factory.data.find_by_uuid(flow_uuid)
            return flow.update_data(label, flow_data)

    @staticmethod
    def delete_flow(flow_uuid):
        """
        フレームを削除する

        flow_uuid  : フローのUUID
        戻り値      : なし
        """
        with UnAuthzFactory() as factory:
            admin_user = factory.find_user_by_email('admin@kskp.io')
        with Factory(admin_user) as factory:
            flow = factory.data.find_by_uuid(flow_uuid)
            flow.delete()


    @staticmethod
    def load_folder(folder_uuid):
        """
        フォルダを取得する
        """
        with UnAuthzFactory() as factory:
            admin_user = factory.find_user_by_email('admin@kskp.io')
        with Factory(admin_user) as factory:
            return factory.data.find_by_uuid(folder_uuid)

    @staticmethod
    def update_folder_data(folder_uuid, label, modifier=None):
        """
        フォルダのラベル名を変更する
        """
        with Factory(modifier) as factory:
            folder = factory.data.find_by_uuid(folder_uuid)
            return folder.update_data(label)

    @staticmethod
    def save_folder(parent_uuid, label, creator=None):
        """
        フォルダを作成する
        """
        with Factory(creator) as factory:
            parent = factory.data.find_by_uuid(parent_uuid)
            new_folder = parent.create_folder(label)
            new_folder.save()
            # save()によりreadable=Noneになるため再取得する
            return factory.data.find_by_uuid(new_folder.uuid)

    @staticmethod
    def delete_folder(folder_uuid):
        """
        フォルダを削除する
        """
        with UnAuthzFactory() as factory:
            admin_user = factory.find_user_by_email('admin@kskp.io')
        with Factory(admin_user) as factory:
            folder = factory.data.find_by_uuid(folder_uuid)
            folder.delete()

    @staticmethod
    def load_awss3(awss3_uuid):
        """
        AWS S3フォルダを取得する
        """
        with UnAuthzFactory() as factory:
            admin_user = factory.find_user_by_email('admin@kskp.io')
        with Factory(admin_user) as factory:
            return factory.data.find_by_uuid(awss3_uuid)

    @staticmethod
    def update_awss3_data(awss3_uuid, label, bucket, modifier=None):
        """
        AWS S3フォルダのラベル名を変更する
        """
        with Factory(modifier) as factory:
            awss3 = factory.data.find_by_uuid(awss3_uuid)
            return awss3.update_data(label, bucket)

    @staticmethod
    def save_awss3(parent_uuid, label, bucket, creator=None):
        """
        AWS S3フォルダを作成する
        """
        with Factory(creator) as factory:
            parent = factory.data.find_by_uuid(parent_uuid)
            new_awss3 = parent.create_awss3(label, bucket)
            new_awss3.save()
            # save()によりreadable=Noneになるため再取得する
            return factory.data.find_by_uuid(new_awss3.uuid)

    @staticmethod
    def delete_awss3(awss3_uuid):
        """
        AWS S3フォルダを削除する
        """
        with UnAuthzFactory() as factory:
            admin_user = factory.find_user_by_email('admin@kskp.io')
        with Factory(admin_user) as factory:
            awss3 = factory.data.find_by_uuid(awss3_uuid)
            awss3.delete()

    @classmethod
    def create_admin_user():
        pass

    @staticmethod
    def _init_library_folders():
        Library._get_result_dir_path()
        Library._get_cache_dir_path()
        Library._get_flow_dir_path()

    @staticmethod
    def _get_flow_dir_path(user=None):
        # フロー格納フォルダを取得する
        from kskp.store import FLOW_FOLDER_UUID, FLOW_FOLDER_LABEL
        return Library._get_or_make_dir_path(FLOW_FOLDER_UUID, FLOW_FOLDER_LABEL, user)

    @staticmethod
    def _get_result_dir_path(user=None):
        # フレーム格納フォルダを取得する
        return Library._get_or_make_dir_path(RESULT_FOLDER_UUID, RESULT_FOLDER_LABEL, user)

    @staticmethod
    def _get_cache_dir_path(user=None):
        # キャッシュ格納フォルダを取得する
        return Library._get_or_make_dir_path(CACHE_FOLDER_UUID, CACHE_FOLDER_LABEL, user)

    @staticmethod
    def _get_or_make_dir_path(uuid, label, user=None):
        with Factory(user) as factory:
            # 特定用途のフォルダのUUIDは決め打ちである
            if factory.data.exists(uuid):
                folder = factory.data.find_by_uuid(uuid)
            else:
                # フォルダが無い場合は作成する
                root = factory.data.find_root()
                folder = Folder(root.uuid,
                                label,
                                user)
                # Folderのコンストラクタで付番したUUIDを捨てて、特定用途のフォルダのUUIDを格納する
                folder.uuid = uuid
                folder.save()
                # saveのあとはreadableがNoneになるので再取得する
                folder = factory.data.find_by_uuid(uuid)
            return folder

    # @staticmethod
    # def _get_library(user=None):
    #     """
    #     ルートデータストアを取得する、存在しない場合は作成する
    #     """
    #     root = Datum.find_root()
    #     # ルートフォルダが存在しない場合はルートフォルダを作成する
    #     # (最初にライブラリ画面にアクセスする時はルートフォルダ自身も存在しません)
    #     if root is None:
    #         new_root = Folder(parent_uuid=None,
    #                           label='ROOT_FOLDER',
    #                           creator=user)
    #         # folderレコードをDBに格納する
    #         new_root.save()

    #         # 
    #         # ルートフォルダにAdminグループの権限設定がない場合、初期値を設定する
    #         # (後方互換)
    #         # 
    #         from kskp.store import ss
    #         from kskp.store.auth import Auth, Group
    #         admin_group = Group.load_admin_group()
    #         admin_group.join_user(ss.user)
    #         if not Auth.exists(admin_group.id, new_root.id):
    #             admin_group.init_authz(new_root.id, True, True, False)

    #         # 
    #         # ルートフォルダにEveryOneグループの権限設定がない場合、初期値を設定する
    #         # (後方互換)
    #         # 
    #         everyone_group = Group.load_everyone_group()
    #         everyone_group.join_user(ss.user)
    #         if not Auth.exists(everyone_group.id, new_root.id):
    #             everyone_group.init_authz(new_root.id, True, True, False)

    #         # 参照権限設定後にもう一度取得し直す
    #         root = Folder.find_by_uuid(new_root.uuid)
    #     return root


