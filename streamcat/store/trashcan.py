from streamcat.core import SavableDatum
from .folder import Folder

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
        self.type = SavableDatum.TRASH_TYPE

    def _exists(self):
        """
        ゴミ箱が存在する場合はTrueを返す
        """
        from sqlalchemy import select, func
        stmt = select(func.count(SavableDatum.id)).where(SavableDatum.type==SavableDatum.TRASH_TYPE)
        return self._session.scalars(stmt).one() > 0

    def save(self):
        """
        ゴミ箱を保存する
        """
        from streamcat.store.factory import DatumFactory
        # 既にゴミ箱フォルダが存在する場合
        factory = DatumFactory(self._session)
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
        if isinstance(datum, Folder) and datum.writable:
            # フォルダ直下のフォルダとファイルを削除する
            for child in datum.find_children():
                self._trash_all_inner(child)
            # フォルダを削除する
            datum.delete()
        elif datum.writable:
            # ファイルを削除する
            datum.delete()
        else:
            # 更新権限のないファイルは削除しない
            # import warnings
            # warnings.warn(f'{datum} is not deleted, {datum.writable}')
            pass

    def to_json(self):
        ret = super().to_json()

        # ゴミ箱直下では新規作成はできない
        # ゴミ箱の変更・削除・移動もできない
        ret['allowlist']['createProject'] = False
        ret['allowlist']['createFolder'] = False
        ret['allowlist']['createFile'] = False
        ret['allowlist']['upload'] = False
        ret['allowlist']['import'] = False
        ret['allowlist']['download'] = False
        ret['allowlist']['export'] = False
        ret['allowlist']['update'] = False
        # ret['allowlist']['delete'] = False
        ret['allowlist']['move'] = False
        ret['allowlist']['copy'] = False
        return ret
