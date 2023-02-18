from streamcat.core import SavableDatum
from streamcat.store import File

class Document(File):

    __mapper_args__ = {
        'polymorphic_identity' : 'document'
    }

    def __init__(self, session, parent, label, stream):
        """
        コンストラクタ
        stream : データのファイルストリームを指定する
        """
        super().__init__(session, parent, SavableDatum.DOCUMENT_TYPE, label, stream)

