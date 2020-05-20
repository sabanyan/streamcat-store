import os

from kskp.core import Datum
from kskp.store import Folder

class ProjectFolder(Folder):

    __mapper_args__ = {
        'polymorphic_identity' : 'project'
    }

    def __init__(self, session, parent, label, creator=None):
        """
        コンストラクタ
        """
        super().__init__(session, parent, label, creator)

        # データタイプを設定する
        self.type = Datum.PROJECT_TYPE

        # data列の値を作成する
        # self.data = {}
