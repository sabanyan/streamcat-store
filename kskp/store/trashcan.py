from kskp.core import Datum
from kskp.store import Folder

class TrashCan(Folder):

    __mapper_args__ = {
        'polymorphic_identity' : 'trash'
    }

    def __init__(self, session, parent):
        """
        コンストラクタ
        """
        super().__init__(session, parent, 'ゴミ箱')

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

    def trash_all(self):
        """
        ゴミ箱を空にする
        """
        # ゴミ箱直下のフォルダとファイルを削除する
        for child in self.find_children():
            self._trash_all_inner(child)

    def _trash_all_inner(self, datum):
        if isinstance(datum, Folder):
            # フォルダ直下のフォルダとファイルを削除する
            for child in datum.find_children():
                self._trash_all_inner(child)
            # フォルダを削除する
            datum.delete()
        else:
            # ファイルを削除する
            datum.delete()

