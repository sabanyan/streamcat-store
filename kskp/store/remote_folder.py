import os
import json
import shutil
import shlex
import subprocess
from time import sleep
from pathlib import Path

from kskp.core import Datum
from . import ss as session
from kskp.store import Folder, RemoteFolderConn, Mountable

class RemoteFolder(Folder, Mountable):

    def __init__(self, parent_uuid, label, remoteFolderConn, creator=None):
        """
        コンストラクタ
        """
        super().__init__(parent_uuid, label, creator)

        # データタイプを設定する
        self.type = Datum.RFOLDER_TYPE

        # data列の値を作成する
        if remoteFolderConn is None:
            raise Exception('remoteFolderConn引数がNoneです')
        self.data = {'conn' : remoteFolderConn.to_json()}

    @staticmethod
    def find_by_uuid(uuid):
        """
        指定されたuuidを持つ共有フォルダを取得する
        """
        # UUID値の形式チェックをする
        Datum.valid_uuid_or_raise(uuid)
        datum = session.query(Datum).filter(Datum.uuid==uuid)\
                                    .filter(Datum.type==Datum.RFOLDER_TYPE).one_or_none()
        if datum is None:
            raise Exception('no remote folder is found by designated id.')
        return RemoteFolder.convert_to_remote_folder(datum)

    @staticmethod
    def exists(uuid):
        """
        指定されたuuidを持つ共有フォルダが存在する場合はTrueを返す
        """
        # UUID値の形式チェックをする
        if not Datum.is_valid_uuid(uuid):
            return False
        result = session.query(Datum).filter(Datum.uuid==uuid)\
                                     .filter(Datum.type==Datum.RFOLDER_TYPE).count()
        return result > 0

    @staticmethod
    def convert_to_remote_folder(datum):
        parent_uuid = Datum.get_uuid_by_id(datum.parent_id)
        remote_folder_conn = RemoteFolderConn.from_json(datum.data2['conn'])
        folder = RemoteFolder(parent_uuid, datum.label, remote_folder_conn, datum.creator)
        folder.id = datum.id
        folder.uuid = datum.uuid
        folder._path = datum._path
        folder.data = datum.data
        folder.modifier = datum.modifier
        folder.created_at = datum.created_at
        folder.modified_at = datum.modified_at
        return folder

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
            session.add(self)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.commit()

    @staticmethod
    def update_data(uuid, label, remoteFolderConn, modifier):
        """
        共有フォルダのdata列を更新する
        """
        # UUID値の形式チェックをする
        Datum.valid_uuid_or_raise(uuid)
        # レコードを取得する
        datum = session.query(Datum).filter(Datum.uuid==uuid)\
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
            Datum.update_same_path(old_path, new_path, modifier)
            Datum.update_include_path(old_path, new_path, modifier)

            # レコードを更新する
            data = {'conn' : remoteFolderConn.to_json()}
            session.query(Datum).filter(Datum.uuid==uuid).update({'_label'   :new_label
                                                                 ,'data'    :data
                                                                 ,'modifier':modifier})
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.commit()

        return RemoteFolder.convert_to_remote_folder(datum)

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
            session.rollback()
            raise e
        finally:
            session.commit()

    def valid_or_raise(self):
        """
        接続情報の形式チェックを行い、NGの場合は例外を送出する
        """
        database_conn = RemoteFolderConn.from_json(self.data2['conn'])
        return database_conn.valid_or_raise()

    def _get_mount_cmd(self, mount_point_path):
        remote_folder_conn = RemoteFolderConn.from_json(self.data2['conn'])
        return remote_folder_conn.get_mount_cmd(mount_point_path)

    def to_json(self):
        remote_folder_conn = RemoteFolderConn.from_json(self.data2['conn'])

        return {'uuid'      : self.uuid,
                'type'      : Datum.RFOLDER_TYPE,
                'label'     : self.label,
                'protocol'  : remote_folder_conn.protocol,
                'hostname'  : remote_folder_conn.hostname,
                'domain'    : remote_folder_conn.domain,
                'directory' : remote_folder_conn.directory,
                'user_id'   : remote_folder_conn.user_id,
                'password'  : remote_folder_conn.password,
                'creator'   : Datum.get_user_name_by_user_id(self.creator),
                'createdAt' : self.created_at_str}
