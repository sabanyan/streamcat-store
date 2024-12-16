from streamcat.core import Datum, SavableDatum, SavableStore, Constraints
from .mountable import Mountable
from .remote_folder_conn import RemoteFolderConn

# Mountable.pathをDatum.pathより優先させるため、先にMountableを継承すること
class RemoteFolder(Mountable, SavableStore):

    __mapper_args__ = {
        'polymorphic_identity' : 'rfolder'
    }

    def __init__(self, session, parent, label, remoteFolderConn):
        """
        コンストラクタ
        """
        super().__init__(session, parent, SavableDatum.RFOLDER_TYPE, label)

        # data列の値を作成する
        if remoteFolderConn is None:
            raise Exception('remoteFolderConn引数がNoneです')
        self._data = {'conn' : remoteFolderConn.to_json(encrypt_password=True)}

    @Constraints.prohibit_save_on_root
    @Constraints.set_project_role_on_adding
    def save(self):
        """
        共有フォルダを保存する
        """
        # 既にルートフォルダが存在する場合は、parent_id=NULLを許可しない
        from streamcat.store.factory import DatumFactory
        if self.parent_id is None and DatumFactory(self._session).count_root() > 0:
            raise Exception('You can not add root remote folder. A root already exists.')

        # 既存のファイルと重複しないファイル名を取得する
        self._path = SavableDatum.make_unique_path(self._path)

        # 新規追加前にファイルパスを退避する
        self_path = self._path

        try:
            # Dataテーブルにレコードを新規追加する
            self._session.add(self)
            # マウントするには参照権限が必要だが、session.add()がself.permissionsをNoneにするため
            # reload()してpermissionsを再読み込みする
            self = self.reload()
            # フォルダに紐付くディレクトリ(path列で指定されるディレクトリ)がなければ作成する
            self._make_dir(self_path)
        except (Exception, OSError) as e:
            self.unmount(self_path)
            self._remove_dir(self_path)
            self._session.rollback()
            raise e

    def update_data(self, label, remoteFolderConn, modifier=None):
        """
        共有フォルダのlabel列を更新する
        (path及び対応ファイル名は変更しない)
        """
        # ラベルに'\0'が含まれていれば取り除く
        new_label = Datum.escape_label(label)

        try:
            # レコードを更新する
            self._label = new_label
            self._data['conn'] = remoteFolderConn.to_json(encrypt_password=True)
            self._modifier_id = (modifier or self._session.user).id
            self._session.update(self)

            # マウント中のディレクトリ名は変更できない
            # -> OSError: [Errno 16] Device or resource busy
            # Datum.move_file(old_path, new_path)
        except Exception as e:
            self._session.rollback()
            raise e

        return self

    @Constraints.delete_role_when_isolated
    def delete(self):
        """
        共有フォルダを削除する
        """
        # 自身のフォルダ以下のフレームが、自身のフォルダ以下以外にあるフローから参照されている場合は、例外を送出する
        using_flow_uuids = self.get_flow_uuids_using_me()
        if len(using_flow_uuids) > 0:
            raise Exception(f"このStoreはローダ・セーバ({using_flow_uuids[0]['reference_label']})で使用しているため削除できません")

        try:
            # TODO: ObjectDeletedError回避するためSession.delete()の前に_pathを参照する
            self._ref_path()
            # フォルダレコードを削除する
            self._session.delete(self)
            # 共有フォルダをマウント解除する
            self.unmount(self._path)
            # ディレクトリを削除する
            self._remove_dir(self._path)
        except (Exception, OSError) as e:
            self._session.rollback()
            raise e

    def duplicate(self, new_label, new_parent:Datum=None):
        """
        自身の複製を作成して保存する
        """
        # 複製元と同じフォルダに複製を作成する
        parent = new_parent or self.find_parent()
        new_folder = parent.create_remote_folder(new_label, self.conn.copy())
        # ライブラリに保存する
        new_folder.save()
        return new_folder

    @property
    def conn(self):
        return RemoteFolderConn(self._data['conn'], 
                                password_is_enctypted=True,
                                readable_or_raise=self._readable_or_raise)

    def valid_or_raise(self):
        """
        接続情報の形式チェックを行い、NGの場合は例外を送出する
        """
        database_conn = RemoteFolderConn(self._data['conn'])
        return database_conn.valid_or_raise()

    def _get_mount_cmd(self, mount_point_path):
        return self.conn.get_mount_cmd(mount_point_path)

    def to_json(self):
        ret = super().to_json()
        if self.readable:
            ret.update(self.conn.to_json())
        return ret
