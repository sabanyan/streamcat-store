from kskp.core import Datum
from kskp.store import Folder

class ProjectFolder(Folder):

    __mapper_args__ = {
        'polymorphic_identity' : 'project'
    }

    def __init__(self, session, parent, label):
        """
        コンストラクタ
        """
        super().__init__(session, parent, label)

        # データタイプを設定する
        self.type = Datum.PROJECT_TYPE

    def get_joined_users(self):
        """
        所属する全てのユーザを返す
        """
        pass
