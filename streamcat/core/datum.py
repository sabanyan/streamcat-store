class Datum:
    """
    StreamCatで扱うデータを表す
    """

    def __init__(self, datum_type:str, label:str):
        """
        コンストラクタ
        """
        # UUIDを採番する
        import uuid
        self.uuid = str(uuid.uuid4())

        # type
        self.type = datum_type

        # label
        self._label = Datum.escape_label(label)

        # Engineから参照する
        self.context = {}

    @property
    def label(self):
        return self._label or ''

    def __repr__(self):
        return f'Datum({self._label}, {self.type})'

    def __eq__(self, other):
        return self.uuid == other.uuid

    def __ne__(self, other):
        return self.uuid != other.uuid

    def __hash__(self) -> int:
        return hash(self.uuid)

    @staticmethod
    def is_valid_uuid(uuid) -> bool:
        """
        uuidの形式チェック
        """
        if uuid is None:
            return False
        import re
        return re.match('^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$', uuid)

    @staticmethod
    def valid_uuid_or_raise(uuid):
        """
        uuidの形式チェックの結果、正しくないuuidの場合は例外を送出する
        """
        if uuid is None or uuid == '':
            raise Exception(f'The UUID value is empty')
        if not Datum.is_valid_uuid(uuid):
            raise Exception(f'The UUID({uuid}) value is not valid format.')

    @staticmethod
    def escape_label(label):
        if label is None:
            return label
        # '\0'は少なくともPostgreSQLのVARCHARに格納できない
        trans_table = str.maketrans({'\0' : ''})
        return label.translate(trans_table)
