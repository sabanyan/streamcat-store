from kskp.core import Datum
from kskp.store import Folder

class TrashCan(Folder):

    __mapper_args__ = {
        'polymorphic_identity' : 'trash'
    }

    def __init__(self, session, parent, creator=None):
        """
        コンストラクタ
        """
        super().__init__(session, parent, 'ゴミ箱', creator)

        # データタイプを設定する
        self.type = Datum.TRASH_TYPE

    def _exists(self):
        """
        ゴミ箱が存在する場合はTrueを返す
        """
        result = self.session.query(Datum).filter(Datum.type==Datum.TRASH_TYPE).count()
        return result > 0

    def save(self):
        """
        ゴミ箱を保存する
        """
        from kskp.store.factory import DatumFactory
        # 既にゴミ箱フォルダが存在する場合
        factory = DatumFactory(self.session)
        if factory.trashcan_exists():
            raise Exception('You can not add trash can. A trash can already exists.')
        # ゴミ箱フォルダを保存する
        super().save()
