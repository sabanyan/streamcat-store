from .datum import Datum
from . import db
import os
import re
import json

class Folder(Datum):

    def __init__(self, parent_uuid, label, creator=None, modifier=None):
        """
        コンストラクタ
        """
        super().__init__(parent_uuid, Datum.FOLDER_TYPE, label, creator, modifier)

        # data列の値を作成する
        self.data = json.dumps({'label' : label})

    @staticmethod
    def find_by_uuid(uuid):
        """
        指定されたuuidを持つFolderを取得する
        """
        datum = db.session.query(Datum).filter(Datum.uuid==uuid)\
                                       .filter(Datum.type==Datum.FOLDER_TYPE).one_or_none()
        if datum is None:
            raise Exception('no folder is found by designated id.')
        return Folder.convert_to_folder(datum)

    @staticmethod
    def exists(uuid):
        """
        指定されたuuidを持つFolderが存在する場合はTrueを返す
        """
        result = db.session.query(Datum).filter(Datum.uuid==uuid)\
                                         .filter(Datum.type==Datum.FOLDER_TYPE).count()
        return result > 0

    @staticmethod
    def convert_to_folder(datum):
        parent_uuid = Datum.get_uuid_by_id(datum.parent_id)
        label = json.loads(datum.data, encoding='utf-8')['label']
        folder = Folder(parent_uuid, label, datum.creator, datum.modifier)
        folder.id = datum.id
        folder.uuid = datum.uuid
        folder.path = datum.path
        folder.created_at = datum.created_at
        folder.modified_at = datum.modified_at
        return folder

    def save(self):
        """
        Folderを保存する
        """
        # 既にルートフォルダが存在する場合は、parent_id=NULLを許可しない
        if self.parent_id is None and Datum.count_root() > 0:
            raise Exception('You can not add root folder. A root already exists.')
        # フォルダに紐付くディレクトリ(path列で指定されるディレクトリ)がなければ作成する
        path = self._make_dir()
        self.path = path
        try:
            # Dataテーブルにレコードを新規追加する
            db.session.add(self)
        except Exception as e:
            db.session.rollback()
            raise e
        finally:
            db.session.commit()

    @staticmethod
    def update_data(uuid, label, modifier):
        """
        Folderのdata列を更新する
        """
        # レコードを取得する
        datum = db.session.query(Datum).filter(Datum.uuid==uuid)\
                                       .filter(Datum.type==Datum.FOLDER_TYPE).one_or_none()
        if datum is None:
            raise Exception('no folder is found by designated id.')

        # ファイルを移動する
        old_path = datum.path
        new_path = os.path.join(os.path.dirname(old_path), Datum.escape_filename(label))
        new_path = Datum.move_file(old_path, new_path)

        try:
            # 同じディレクトリに対応するフォルダのpath列を、ディレクトリ名の移動に合わせて変更する
            db.session.query(Datum).filter(Datum.path==old_path).update({'path': new_path})
            # 同じディレクトリを含むpath列を、ディレクトリの移動に合わせて変更する
            results = db.session.query(Datum.id, Datum.path).filter(Datum.path.like(old_path+'/%')).all()
            for result in results:
                replaced_path = re.sub('^'+old_path, new_path, result.path)
                db.session.query(Datum).filter(Datum.id==result.id).update({'path'       :replaced_path
                                                                          , 'modifier'   :modifier
                                                                          , 'modified_at':Datum.get_current_time_str()})
            # レコードを更新する
            data = json.dumps({'label' : label})
            db.session.query(Datum).filter(Datum.uuid==uuid).update({'data'       :data
                                                                   , 'modifier'   :modifier
                                                                   , 'modified_at':Datum.get_current_time_str()})
        except Exception as e:
            db.session.rollback()
            raise e
        finally:
            db.session.commit()

        return Folder.convert_to_folder(datum)

    def delete(self):
        """
        Folderを削除する
        """
        # 削除対象のフォルダの下にフォルダまたはファイルが存在する場合は例外を送出する
        if len(Datum.find_by_parent_uuid(self.uuid)) > 0:
            raise Exception('Can not delete folder that has child file or folder.')
        try:
            # フォルダレコードを削除する
            db.session.query(Datum).filter(Datum.id==self.id)\
                                   .filter(Datum.type==Datum.FOLDER_TYPE).delete()
            # ディレクトリを削除する
            self._remove_dir()
        except Exception as e:
            db.session.rollback()
            raise e
        finally:
            db.session.commit()

    def get_folder_path(self):
        """
        現在のフォルダ階層パスをリスト型で返す(APIのFolderPath属性の作成で用いる)
        """
        # 指定されたUUIDのfolerレコードを取得する
        result = db.session.query(Datum.uuid, Datum.parent_id, Datum.data)\
                           .filter(Datum.uuid==self.uuid)\
                           .filter(Datum.type==Datum.FOLDER_TYPE).one_or_none()

        parent_id = result.parent_id
        path_to_root = [{'uuid':result.uuid, 'label':json.loads(result.data, encoding='utf-8')['label']}]
        # 取得したレコードから外部キー’parent_id’をたどり、途中のfolderレコードをリストに順に保存する
        while parent_id != None:
            result = db.session.query(Datum.uuid, Datum.parent_id, Datum.data).filter(Datum.id==parent_id).one_or_none()
            path_to_root.append({'uuid':result.uuid, 'label':json.loads(result.data, encoding='utf-8')['label']})
            parent_id = result.parent_id
        # 保存したリストの並びを逆にする
        path_to_root.reverse()
        return path_to_root

    def _make_dir(self):
        """
        Folderに対応するディレクトリを作成する
        """
        try:
            # 同じ名称のファイルが既に存在する場合、末尾に数字を付加したディレクトリ名で作成する
            path = Folder.get_another_file_path(self.path)
            # フォルダに紐付くディレクトリ(path列で指定されるディレクトリ)がなければ作成する
            if not os.path.isdir(path):
                os.makedirs(path, exist_ok=True)
            return path
        except PermissionError as e:
            # ファイルに対する権限がない場合
            raise e

    def _remove_dir(self):
        """
        Folderに対応するディレクトリを削除する
        """
        try:
            # 全てのフォルダから紐づかないディレクトリは物理削除する
            dir_path = self.path.rstrip(os.pathsep)
            while dir_path != '' and dir_path != '/' and dir_path != 'kskp/data':
                # 自分以外で同じディレクトリパスを使用しているフォルダの有無を確認する
                if Folder._dir_path_exists(dir_path, except_id=self.id):
                    break
                else:
                    if os.path.isdir(dir_path):
                        os.rmdir(dir_path)
                    dir_path = os.path.dirname(dir_path)
        except PermissionError as e:
            # ファイルに対する権限がない場合
            raise e

    @staticmethod
    def _dir_path_exists(dir_path, except_id):
        results = db.session.query(Datum.path).filter(Datum.path.like(dir_path + '%'))\
                                              .filter(Datum.id != except_id).all()
        for result in results:
            if result.path == dir_path:
                return True
            elif os.path.commonpath([result.path, dir_path]) == dir_path:
                return True
        return False

    def to_json(self):
        return {'uuid'      : self.uuid,
                'type'      : Datum.FOLDER_TYPE,
                'label'     : json.loads(self.data, encoding='utf-8')['label'],
                'creator'   : Datum.get_user_name_by_user_id(self.creator),
                'createdAt' : self.created_at}
