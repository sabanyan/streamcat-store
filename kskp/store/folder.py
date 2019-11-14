import os
import re
import json
import uuid

from pathlib import Path

from . import ss as session

from kskp.core import Datum
from kskp.store import Store, STORE_DIR

class Folder(Store):

    def __init__(self, parent_uuid, label, creator=None):
        """
        コンストラクタ
        """
        super().__init__(parent_uuid, Datum.FOLDER_TYPE, label, creator)

        # data列の値を作成する
        self.data = {'label' : label}

    @staticmethod
    def find_by_uuid(uuid):
        """
        指定されたuuidを持つFolderを取得する
        """
        datum = session.query(Datum).filter(Datum.uuid==uuid)\
                                    .filter(Datum.type==Datum.FOLDER_TYPE).one_or_none()
        if datum is None:
            raise Exception('no folder is found by designated id.')
        return Folder.convert_to_folder(datum)

    @staticmethod
    def exists(uuid):
        """
        指定されたuuidを持つFolderが存在する場合はTrueを返す
        """
        # UUID値の形式チェックをする
        if not Datum.is_valid_uuid(uuid):
            return False
        result = session.query(Datum).filter(Datum.uuid==uuid)\
                                     .filter(Datum.type==Datum.FOLDER_TYPE).count()
        return result > 0

    @staticmethod
    def convert_to_folder(datum):
        parent_uuid = Datum.get_uuid_by_id(datum.parent_id)
        # label = json.loads(datum.data, encoding='utf-8')['label']
        folder = Folder(parent_uuid, datum.label, datum.creator)
        folder.id = datum.id
        folder.uuid = datum.uuid
        folder._path = datum._path
        folder.modifier = datum.modifier
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
        self._path = path
        try:
            # Dataテーブルにレコードを新規追加する
            session.add(self)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.commit()

    def add_entry_from_path(self, file_path):
        """
        指定されたパスのファイルをFolderとして登録する
        """
        # 既にルートフォルダが存在する場合は、parent_id=NULLを許可しない
        if self.parent_id is None and Datum.count_root() > 0:
            raise Exception('You can not add another root folder. A root already exists!')
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
        Folderのdata列を更新する
        """
        # UUID値の形式チェックをする
        Datum.valid_uuid_or_raise(uuid)
        # レコードを取得する
        datum = session.query(Datum).filter(Datum.uuid==uuid)\
                                    .filter(Datum.type==Datum.FOLDER_TYPE).one_or_none()
        if datum is None:
            raise Exception('no folder is found by designated id.')

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
            data ={'label' : new_label}
            session.query(Datum).filter(Datum.uuid==uuid).update({'_label'  :new_label
                                                                 ,'data'    :data
                                                                 ,'modifier':modifier})
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.commit()

        return Folder.convert_to_folder(datum)

    def delete(self):
        """
        Folderを削除する
        """
        # 削除対象のフォルダの下にフォルダまたはファイルが存在する場合は例外を送出する
        if len(Datum.find_by_parent_uuid(self.uuid)) > 0:
            raise Exception('空でないフォルダは削除できません')
        try:
            # フォルダレコードを削除する
            session.query(Datum).filter(Datum.id==self.id)\
                                .filter(Datum.type==Datum.FOLDER_TYPE).delete()
            # ディレクトリを削除する
            self._remove_dir()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.commit()

    def remove_reference_only(self):
        """
        _remove_reference_only_recursivelyのエイリアスです
        """
        self._remove_reference_only_recursively()

    def _remove_reference_only_recursively(self):
        """
        エントリを削除するが、対応するファイルは削除しない
        この処理は自身と自身のエントリ以下の全てのエントリが対象である
        """
        sql="""
        WITH RECURSIVE R AS (
            SELECT id FROM data WHERE id = {id}
            UNION ALL
            SELECT data.id FROM data JOIN R ON data.parent_id = R.id
        )
        DELETE FROM data D
        WHERE EXISTS (SELECT * FROM R
                      WHERE R.id = D.id);
        """.format(id=self.id)

        try:
            # フォルダレコードを削除する
            session.query(Datum).filter(Datum.id==self.id)\
                                .filter(Datum.type==Datum.FOLDER_TYPE).delete()
            session.execute(sql)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.commit()

    def get_folder_path(self):
        """
        現在のフォルダ階層パスをリスト型で返す(APIのFolderPath属性の作成で用いる)
        """
        # 指定されたUUIDのfolerレコードを取得する
        datum = session.query(Datum).filter(Datum.uuid==self.uuid).one_or_none()

        parent_id = datum.parent_id
        path_to_root = [{'type':datum.type, 'uuid':datum.uuid, 'label':datum.label}]
        # 取得したレコードから外部キー’parent_id’をたどり、途中のfolderレコードをリストに順に保存する
        while parent_id != None:
            datum = session.query(Datum).filter(Datum.id==parent_id).one_or_none()
            path_to_root.append({'type':datum.type, 'uuid':datum.uuid, 'label':datum.label})
            parent_id = datum.parent_id
        # 保存したリストの並びを逆にする
        path_to_root.reverse()
        return path_to_root

    def _make_dir(self):
        """
        Folderに対応するディレクトリを作成する
        """
        try:
            # 同じ名称のファイルが既に存在する場合、末尾に数字を付加したディレクトリ名で作成する
            path = Folder.get_another_file_path(self._path)
            # フォルダに紐付くディレクトリ(path列で指定されるディレクトリ)がなければ作成する
            if not os.path.isdir(Datum._to_abs_path(path)):
                os.makedirs(Datum._to_abs_path(path), exist_ok=True)
            return path
        except PermissionError as e:
            # ファイルに対する権限がない場合
            raise e

    def _remove_dir(self):
        """
        Folderに対応するディレクトリを削除する
        """
        from kskp.store import Mountable
        
        try:
            # 全てのフォルダから紐づかないディレクトリは物理削除する
            dir_path = self._path.rstrip(os.pathsep)
            abs_dir_path = Datum._to_abs_path(dir_path)
            while dir_path != '' and dir_path != '/':
                # 自分以外で同じディレクトリパス(相対パス)を使用しているフォルダの有無を確認する
                if Folder._dir_path_exists(dir_path, except_id=self.id):
                    break
                elif Mountable.is_mount(Path(dir_path)):
                    # マウント中のフォルダは削除しない
                    break
                else:
                    if os.path.isdir(abs_dir_path):
                        os.rmdir(abs_dir_path)
                    dir_path = os.path.dirname(dir_path)
                    abs_dir_path = os.path.dirname(abs_dir_path)
        except PermissionError as e:
            # ファイルに対する権限がない場合
            raise e

    @staticmethod
    def _move_dir(old_path, new_label):
        """
        Folderのラベルに対応するディレクトリへ移動する
        """
        # ファイルを移動する
        new_path = os.path.join(os.path.dirname(old_path), Datum.escape_filename(new_label))
        new_path = Datum.move_file(old_path, new_path)
        return new_path

    @staticmethod
    def _dir_path_exists(dir_path, except_id):
        rel_path = Datum._to_rel_path(dir_path)
        abs_path = Datum._to_abs_path(dir_path)

        from sqlalchemy import or_
        results = session.query(Datum._path)\
                 .filter(or_(Datum._path.like(rel_path + '%'), Datum._path.like(abs_path + '%')))\
                 .filter(Datum.id != except_id).all()

        for result in results:
            if Datum._to_rel_path(result._path) == rel_path:
                return True
            if os.path.commonpath([Datum._to_rel_path(result._path), rel_path]) == rel_path:
                return True
        return False

    def to_json(self):
        return {'uuid'      : self.uuid,
                'type'      : Datum.FOLDER_TYPE,
                'label'     : self.label,
                'creator'   : Datum.get_user_name_by_user_id(self.creator),
                'createdAt' : self.created_at_str}

    # def save_frame(self, command, args, datum, file_name):
    #     """
    #     engine用
    #     保存するframeへのパスを作成する
    #     """
    #     # args['frame_path'] = (Path(Datum._to_abs_path(self.path)) / (str(uuid.uuid4()) + '.csv'))
    #     args['frame_path'] = Path(Datum._to_abs_path(self.path.as_posix())) / file_name
    #     return command.module(args, datum)

    @staticmethod
    def load_frame(uuid):
        """
        指定したuuidのframeを取得する
        """
        import nysol.mcmd as nm
        from kskp.store import Library

        frame = Library.load_frame(uuid)
        if frame is None:
            raise Exception('No frame(%s) is found !' % uuid)
        path = Datum._to_abs_path(frame.path.as_posix())

        return nm.m2tee({'i':path})

    @property
    def content(self):
        return self
