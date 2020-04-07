import os
import json
import shutil
import shlex
import subprocess
from time import sleep
from pathlib import Path

from kskp.core import Datum
from kskp.store import Folder, RemoteFolderConn, Mountable

class RemoteFolder(Folder, Mountable):

    __mapper_args__ = {
        'polymorphic_identity' : 'rfolder'
    }

    def __init__(self, session, parent_uuid, label, remoteFolderConn, creator=None):
        """
        コンストラクタ
        """
        super().__init__(session, parent_uuid, label, creator)

        # データタイプを設定する
        self.type = Datum.RFOLDER_TYPE

        # data列の値を作成する
        if remoteFolderConn is None:
            raise Exception('remoteFolderConn引数がNoneです')
        self.data = {'conn' : remoteFolderConn.to_json()}

    # @staticmethod
    # def find_by_uuid(uuid):
    #     """
    #     指定されたuuidを持つ共有フォルダを取得する
    #     """
    #     # UUID値の形式チェックをする
    #     Datum.valid_uuid_or_raise(uuid)
    #     remote_folder = session.query(RemoteFolder).filter(RemoteFolder.uuid==uuid)\
    #                                                .filter(RemoteFolder.type==RemoteFolder.RFOLDER_TYPE).one_or_none()
    #     if remote_folder is None:
    #         raise Exception('no remote folder is found by designated id.')
    #     return remote_folder

    # @staticmethod
    # def exists(uuid):
    #     """
    #     指定されたuuidを持つ共有フォルダが存在する場合はTrueを返す
    #     """
    #     # UUID値の形式チェックをする
    #     if not Datum.is_valid_uuid(uuid):
    #         return False
    #     result = session.query(Datum).filter(Datum.uuid==uuid)\
    #                                  .filter(Datum.type==Datum.RFOLDER_TYPE).count()
    #     return result > 0

    def save(self):
        """
        共有フォルダを保存する
        """
        # 既にルートフォルダが存在する場合は、parent_id=NULLを許可しない
        if self.parent_id is None and Datum.count_root() > 0:
            raise Exception('You can not add root remote folder. A root already exists.')
        # フォルダに紐付くディレクトリ(path列で指定されるディレクトリ)がなければ作成する
        self.path = Path(self._make_dir())
        # ここでリモートフォルダをマウントする
        self.mount(self._path)
        try:
            # Dataテーブルにレコードを新規追加する
            self.session.add(self)
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.commit()

    def update_data(self, label, remoteFolderConn):
        """
        共有フォルダのdata列を更新する
        """
        # UUID値の形式チェックをする
        Datum.valid_uuid_or_raise(self.uuid)
        # レコードを取得する
        datum = self.session.query(Datum).filter(Datum.uuid==self.uuid)\
                                    .filter(Datum.type==Datum.RFOLDER_TYPE).one_or_none()
        if datum is None:
            raise Exception('no remote folder is found by designated id.')

        # ラベルに'\0'が含まれていれば取り除く
        new_label = Datum.escape_label(label)

        # ファイルを移動する
        old_path = datum._path
        new_path = Folder._move_dir(old_path, new_label)

        try:
            # ディレクトリ名の移動によって他のDatumのpathが変更が必要であれば変更する
            self._update_same_path(old_path, new_path)
            self._update_include_path(old_path, new_path)

            # レコードを更新する
            data = {'conn' : remoteFolderConn.to_json()}
            result = self.session.query(Datum).filter(Datum.uuid==self.uuid).one_or_none()
            if result is not None:
                result._label = new_label
                result._data = data
                result._modifier_id = self.session.user.id
                self.session.update(result)
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.commit()

        return datum

    def delete(self):
        """
        共有フォルダを削除する
        """
        # 自身のフォルダ以下のフレームが、自身のフォルダ以下以外にあるフローから参照されている場合は、例外を送出する
        uuids = self._get_flow_uuids_using_other_datum(self.id)
        if len(uuids) > 0:
            raise Exception(
                'フロー(%s)で使用しているCSVファイルが登録解除対象になっているため削除できません' % uuids[0])
        try:
            # 自身のフォルダ以下の全てのフォルダとドキュメントをエントリーから削除する
            self._remove_reference_only_recursively()

            # 共有フォルダをマウント解除する
            self.unmount(self._path)
            # ディレクトリを削除する
            self._remove_dir()
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.commit()

    def valid_or_raise(self):
        """
        接続情報の形式チェックを行い、NGの場合は例外を送出する
        """
        database_conn = RemoteFolderConn.from_json(self.data['conn'])
        return database_conn.valid_or_raise()

    def _get_mount_cmd(self, mount_point_path):
        remote_folder_conn = RemoteFolderConn.from_json(self.data['conn'])
        return remote_folder_conn.get_mount_cmd(mount_point_path)

    def to_json(self):
        ret =  {'uuid'      : self.uuid,
                'type'      : Datum.RFOLDER_TYPE,
                'label'     : self.label,
                'creator'   : self.creator_str,
                'createdAt' : self.created_at_str}

        if self.readable:
            remote_folder_conn = RemoteFolderConn.from_json(self.data['conn'])
            ret.update(remote_folder_conn.to_json())

        return ret