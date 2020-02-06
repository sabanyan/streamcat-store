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
        self.type = Datum.TRASH_TYPE

    @staticmethod
    def find():
        """
        指定されたuuidを持つゴミ箱を取得する
        """
        datum = session.query(Datum).filter(Datum.type==Datum.TRASH_TYPE).one_or_none()
        if datum is None:
            raise Exception('no trush can is found by designated id.')
        return TrashCan.convert_to_trash_can(datum)

    @staticmethod
    def exists():
        """
        ゴミ箱が存在する場合はTrueを返す
        """
        result = session.query(Datum).filter(Datum.type==Datum.TRASH_TYPE).count()
        return result > 0

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
        trash.modifier = datum.modifier
        trash.created_at = datum.created_at
        trash.modified_at = datum.modified_at
        return trash

    def to_json(self):
        return {'uuid'      : self.uuid,
                'type'      : Datum.TRASH_TYPE,
                'label'     : self.label,
                'creator'   : Datum.get_user_name_by_user_id(self.creator),
                'createdAt' : self.created_at_str}

