import os

from . import ss as session

from kskp.core import Datum
from kskp.store import Folder

class ProjectFolder(Folder):

    # __mapper_args__ = {
    #     'polymorphic_identity' : 'project'
    # }

    def __init__(self, parent_uuid, label, creator=None):
        """
        コンストラクタ
        """
        super().__init__(parent_uuid, label, creator)

        # データタイプを設定する
        self.type = Datum.PROJECT_TYPE

        # data列の値を作成する
        # self.data = {}

    @staticmethod
    def find_by_id(id):
        """
        指定されたidを持つFolderを取得する
        """
        folder = session.query(Folder).filter(Folder.id==id).one_or_none()
        if folder is None:
            raise Exception('no folder is found by designated id.')
        return folder

    @staticmethod
    def find_by_uuid(uuid):
        """
        指定されたuuidを持つFolderを取得する
        """
        datum = session.query(Datum).filter(Datum.uuid==uuid)\
                                    .filter(Datum.type==Datum.PROJECT_TYPE).one_or_none()
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
                                     .filter(Datum.type==Datum.PROJECT_TYPE).count()
        return result > 0

    @staticmethod
    def is_system_folder(uuid):
        from kskp.store import FLOW_FOLDER_UUID, RESULT_FOLDER_UUID, CACHE_FOLDER_UUID
        return uuid in (FLOW_FOLDER_UUID, RESULT_FOLDER_UUID, CACHE_FOLDER_UUID)

    @staticmethod
    def convert_to_folder(datum):
        parent_uuid = Datum.get_uuid_by_id(datum.parent_id)
        folder = ProjectFolder(parent_uuid, datum.label, datum.creator)
        folder.id = datum.id
        folder.uuid = datum.uuid
        folder._path = datum._path
        folder.data = datum.data
        folder.modifier = datum.modifier
        folder.created_at = datum.created_at
        folder.modified_at = datum.modified_at
        return folder

    @staticmethod
    def update_data(uuid, label, modifier):
        """
        Folderのdata列を更新する
        """
        # UUID値の形式チェックをする
        Datum.valid_uuid_or_raise(uuid)
        # レコードを取得する
        datum = session.query(Datum).filter(Datum.uuid==uuid)\
                                    .filter(Datum.type==Datum.PROJECT_TYPE).one_or_none()
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
            session.query(Datum).filter(Datum.uuid==uuid).update({'_label'  :new_label
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
                                .filter(Datum.type==Datum.PROJECT_TYPE).delete()
            # ディレクトリを削除する
            self._remove_dir()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.commit()

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
                                .filter(Datum.type==Datum.PROJECT_TYPE).delete()
            session.execute(sql)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.commit()