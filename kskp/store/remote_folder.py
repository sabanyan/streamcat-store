from kskp.core import Datum
from kskp.store import Folder, RemoteFolderConn, Mountable

# 
# TODO: 継承元をFolderからStoreに変更する。
# Folderは下にファイルやフォルダを作成できるものという定義なので
# 
class RemoteFolder(Folder, Mountable):

    __mapper_args__ = {
        'polymorphic_identity' : 'rfolder'
    }

    def __init__(self, session, parent, label, remoteFolderConn, creator=None):
        """
        コンストラクタ
        """
        super().__init__(session, parent, label, creator)

        # データタイプを設定する
        self.type = Datum.RFOLDER_TYPE

        # data列の値を作成する
        if remoteFolderConn is None:
            raise Exception('remoteFolderConn引数がNoneです')
        self.data = {'conn' : remoteFolderConn.to_json()}

    def save(self):
        """
        共有フォルダを保存する
        """
        # 既にルートフォルダが存在する場合は、parent_id=NULLを許可しない
        from kskp.store.factory import DatumFactory
        if self.parent_id is None and DatumFactory(self.session).count_root() > 0:
            raise Exception('You can not add root remote folder. A root already exists.')

        # 既存のファイルと重複しないファイル名を取得する
        self._path = Datum.make_unique_path(self._path)

        # 新規追加前にファイルパスを退避する
        self_path = self._path

        try:
            # Dataテーブルにレコードを新規追加する
            self.session.add(self)
            # フォルダに紐付くディレクトリ(path列で指定されるディレクトリ)がなければ作成する
            self._make_dir(self_path)
            # ここでリモートフォルダをマウントする
            self.mount(self_path)
        except Exception as e:
            self.unmount(self_path)
            self._remove_dir(self_path)
            self.session.rollback()
            raise e
        finally:
            self.session.commit()

    def update_data(self, label, remoteFolderConn, modifier=None):
        """
        共有フォルダのdata列を更新する
        """
        # ラベルに'\0'が含まれていれば取り除く
        new_label = Datum.escape_label(label)

        # ラベル名からファイルパスを作成する
        old_path = self._path
        new_path = old_path.parent / Datum.escape_filename(new_label)
        new_path = Datum.make_unique_path(new_path, except_path=old_path)

        try:
            # ディレクトリ名の移動によって他のDatumのpathが変更が必要であれば変更する
            self._update_same_path(old_path, new_path, modifier)
            self._update_include_path(old_path, new_path, modifier)

            # レコードを更新する
            # data = {'conn' : remoteFolderConn.to_json()}
            # data = self.data.copy()
            # data['conn'] = remoteFolderConn.to_json()
            self._label = new_label
            self.data['conn'] = remoteFolderConn.to_json()
            self._modifier_id = (modifier or self.session.user).id
            self.session.update(self)

            # ファイルを移動する
            Datum.move_file(old_path, new_path)
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.commit()

        return self

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
            self._remove_dir(self._path)
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.commit()

    def valid_or_raise(self):
        """
        接続情報の形式チェックを行い、NGの場合は例外を送出する
        """
        database_conn = RemoteFolderConn(self.data['conn'])
        return database_conn.valid_or_raise()

    def _get_mount_cmd(self, mount_point_path):
        remote_folder_conn = RemoteFolderConn(self.data['conn'])
        return remote_folder_conn.get_mount_cmd(mount_point_path)

    def to_json(self):
        ret =  {'uuid'      : self.uuid,
                'type'      : Datum.RFOLDER_TYPE,
                'label'     : self.label,
                'creator'   : self.creator_str,
                'createdAt' : self.created_at_str}

        if self.readable:
            ret['prevFolderPath'] = self.get_prev_folder_path()
            remote_folder_conn = RemoteFolderConn(self.data['conn'])
            ret.update(remote_folder_conn.to_json())

        return ret