import os
from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import INTEGER, TIMESTAMP
from sqlalchemy.ext.declarative import declared_attr

class KSKPBaseModel(object):
    """
    SQLAlchemyの全てのモデルクラスのベースモデルの親クラスを定義する
    """

    KEY_OF_TMP_PASS = b'yImzJql25MsreO5E1mQJfNh6ci-oIgSVCSamULEUOnA='

    @declared_attr
    def __table_args__(cls):
        # 定義先スキーマ
        if 'KSKP_POSTGRESQL_SCHEMA_NAME' in os.environ:
            return ({'schema': os.environ['KSKP_POSTGRESQL_SCHEMA_NAME']},)
        else:
            return ()

    # 
    # モデルクラスに共通の列を定義する
    # (@declared_attrを用いて列をテーブルの最後に配置する)
    # 
    @declared_attr
    def _creator_id(cls):
        return Column('creator', INTEGER)

    @declared_attr
    def _modifier_id(cls):
        return Column('modifier', INTEGER)

    @declared_attr
    def created_at(cls):
        return Column(TIMESTAMP, default=text('statement_timestamp()'))

    @declared_attr
    def modified_at(cls):
        return Column(TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()'))

    def __init__(self, session):
        # SQLAlchemy Session
        self._session = session
        
        # creator, modifier
        if session is not None and session.user is not None:
            self._creator_id = session.user.id
            self._modifier_id = session.user.id

    @staticmethod
    def _get_encrypt_password(password):
        """
        パスワードを暗号化する
        """
        from cryptography.fernet import Fernet
        # UTF-8で符号化してByte列で出力
        b_password = password.encode()
        # 暗号化
        cipher_suite = Fernet(KSKPBaseModel.KEY_OF_TMP_PASS)
        cipher_text = cipher_suite.encrypt(b_password)
        return cipher_text.decode()

    @staticmethod
    def _get_decrypt_password(password):
        """
        暗号化されたパスワードを復号する
        """
        from cryptography.fernet import Fernet, InvalidToken
        # 復号化
        cipher_suite = Fernet(KSKPBaseModel.KEY_OF_TMP_PASS)
        try:
            # 仮パスワードの有効期間が切れても復号化は可能である
            return cipher_suite.decrypt(password.encode()).decode()
        except InvalidToken:
            # 復号に失敗しても処理は続行する
            import warnings
            warnings.warn('無効な暗号化パスワードです')
            return None

    @staticmethod
    def _datetime_to_local_time_str(d):
        import datetime
        if d is None:
            return ''
        # DBに格納されている日時はUTCなので、タイムゾーンをUTCに設定する
        d_at_utc = d.replace(tzinfo=datetime.timezone.utc)
        # UTC日時はここで現地時間(環境変数TZの値)に設定される
        d_at_local = d_at_utc.astimezone()
        return d_at_local.strftime('%Y-%m-%d %H:%M:%S')

    @property
    def creator(self):
        from kskp.store.factory import UserFactory
        if self._creator_id is None:
            return None
        return UserFactory(self._session).find_by_id(self._creator_id, allow_no_result=True)

    @property
    def modifier(self):
        from kskp.store.factory import UserFactory
        if self._modifier_id is None:
            return None
        return UserFactory(self._session).find_by_id(self._modifier_id, allow_no_result=True)

    @modifier.setter
    def modifier(self, modifier):
        self._modifier = modifier

    @property
    def creator_str(self):
        if self.creator is None:
            return ''
        return self.creator.name

    @property
    def modifier_str(self):
        if self.modifier is None:
            return ''
        return self.modifier.name

    @property
    def created_at_str(self):
        return KSKPBaseModel._datetime_to_local_time_str(self.created_at)

    @property
    def modified_at_str(self):
        return KSKPBaseModel._datetime_to_local_time_str(self.modified_at)
