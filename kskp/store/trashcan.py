import uuid

from . import ss as session

from kskp.core import Datum
from kskp.store import Folder

class TrashCan(Folder):

    def __init__(self, parent_uuid, creator=None):
        """
        コンストラクタ
        """
        super().__init__(parent_uuid, 'ゴミ箱', creator)

        # データタイプを設定する
        self.type = TrashCan.TRASH_TYPE

    @staticmethod
    def find():
        """
        指定されたuuidを持つゴミ箱を取得する
        """
        trashcan = session.query(TrashCan).filter(TrashCan.type==TrashCan.TRASH_TYPE).one_or_none()
        if trashcan is None:
            raise Exception('no trush can is found by designated id.')
        return trashcan

    @staticmethod
    def exists():
        """
        ゴミ箱が存在する場合はTrueを返す
        """
        result = session.query(TrashCan).filter(TrashCan.type==TrashCan.TRASH_TYPE).count()
        return result > 0

    @staticmethod
    def trashed(datum_uuid):
        """
        ゴミ箱の中にある場合はTrueを返す
        """
        sql = f"""
        WITH RECURSIVE R AS (
            SELECT id, parent_id, uuid, type, path FROM data WHERE uuid = '{datum_uuid}'
            UNION ALL
            SELECT D.id, D.parent_id, D.uuid, D.type, D.path FROM data D JOIN R ON D.id = R.parent_id
        )
        SELECT uuid, path, type FROM R
        WHERE type = '{Datum.TRASH_TYPE}'
        """
        try:
            results = session.execute(sql)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            pass

        return len([result for result in results]) > 0

    def save(self):
        """
        ゴミ箱を保存する
        """
        # 既にゴミ箱フォルダが存在する場合
        if TrashCan.exists():
            raise Exception('You can not add trash can. A trash can already exists.')
        # ゴミ箱フォルダを保存する
        super().save()
        
    @staticmethod
    def convert_to_trash_can(datum):
        parent_uuid = Datum.get_uuid_by_id(datum.parent_id)
        trash = TrashCan(parent_uuid, datum.creator)
        trash.id = datum.id
        trash.uuid = datum.uuid
        trash._path = datum._path
        trash.data = datum.data
        trash.modifier = datum.modifier
        trash.created_at = datum.created_at
        trash.modified_at = datum.modified_at
        return trash

    def to_json(self):
        return {'uuid'      : self.uuid,
                'type'      : TrashCan.TRASH_TYPE,
                'label'     : self.label,
                'prevFolderPath' : self.get_pref_folder_path(),
                'creator'   : Datum.get_user_name_by_user_id(self.creator),
                'createdAt' : self.created_at_str}
