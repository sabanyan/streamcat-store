from kskp.core import Datum
from kskp.store import File

class Document(File):

    __mapper_args__ = {
        'polymorphic_identity' : 'document'
    }

    def __init__(self, session, parent, label, content_type, stream):
        """
        コンストラクタ
        stream : データのファイルストリームを指定する
        """
        super().__init__(session, parent, Datum.DOCUMENT_TYPE, label, content_type, stream)

