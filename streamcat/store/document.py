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

    def duplicate(self, new_label, new_parent=None):
        """
        自身の複製を作成して保存する
        """
        import io
        # 複製元と同じフォルダに複製を作成する
        parent = new_parent or self.find_parent()
        new_document = parent.create_document(new_label, io.BytesIO(b''))
        # ファイルは複製元と共有する(浅いコピー)
        new_document.save(file_path=self.path, content_type=self.content_type)
        return new_document
