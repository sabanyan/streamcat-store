import os
import uuid
from kskp.store.auth.exceptions import NotAuthorizedException
from sqlalchemy import Column, String, text
from sqlalchemy.dialects.postgresql import INTEGER, TIMESTAMP, UUID, ENUM
from .. import BaseModel

class User(BaseModel):
    # テーブル名の定義
    __tablename__ = 'users'

    # 定義先スキーマ
    if 'KSKP_POSTGRESQL_SCHEMA_NAME' in os.environ:
        # テスト環境用のスキーマ
        __table_args__ = {'schema': os.environ['KSKP_POSTGRESQL_SCHEMA_NAME']}

    TMP_STATE      = 'tmp'      # 仮登録状態
    ACTIVE_STATE   = 'active'   # 登録状態
    INACTIVE_STATE = 'inactive' # 論理削除状態

    # 仮パスワードの有効期間(14日間)
    VALID_SECOND_OF_TMP_PASS = 14 * 24 * 60 * 60
    KEY_OF_TMP_PASS = b'yImzJql25MsreO5E1mQJfNh6ci-oIgSVCSamULEUOnA='

    # 列名と列のデータ型等の定義
    id            = Column(INTEGER, primary_key=True, autoincrement=True)
    uuid          = Column(UUID, nullable=False, unique=True)
    email         = Column(String, nullable=False, unique=True)
    name          = Column(String, nullable=False)
    password      = Column(String)
    # ユーザ状態
    state         = Column(ENUM(TMP_STATE, ACTIVE_STATE, INACTIVE_STATE, name='user_state'), nullable=False)
    # 本人ロールのRoleId
    self_role_id  = Column(INTEGER, nullable=True)
    _creator_id   = Column('creator', INTEGER)
    _modifier_id  = Column('modifier', INTEGER)
    created_at    = Column(TIMESTAMP, default=text('statement_timestamp()'))
    modified_at   = Column(TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()'))

    def __init__(self, session, email, name, password=None):
        """
        コンストラクタ
        """
        # SQLAlchemy Session
        self._session = session

        # UUIDを採番する
        self.uuid = str(uuid.uuid4())

        # E-Mailを設定する
        self._valid_email_or_raise(email)
        self.email = email

        # ユーザ名を設定する
        self._valid_name_or_raise(name)
        self.name = name

        # パスワードを設定する
        new_password = password or self._generate_password()
        self.password = self._get_encrypt_password(new_password)

        # 本パスワードに変更する前は仮登録状態である
        self.state = User.TMP_STATE

        # creator, modifier
        if session is not None and session.user is not None:
            self._creator_id = session.user.id
            self._modifier_id = session.user.id

    def _valid_email_or_raise(self, email):
        if email is None or email=='':
            raise Exception('E-Mailに空文字を指定できません')

    def _valid_name_or_raise(self, name):
        if name is None or name=='':
            raise Exception('ユーザ名に空文字を指定できません')

    def _valid_password_or_raise(self, password):
        from .exceptions import InvalidPassword
        if password is None or password == '':
            raise InvalidPassword('空のパスワードに変更できません')
        if self.is_temp:
            if self._get_encrypt_password(password) == self.password:
                raise InvalidPassword('同じパスワードに変更できません')
        else:
            if self._get_password_hash(self.uuid, password) == self.password:
                raise InvalidPassword('同じパスワードに変更できません')

    def _get_password_hash(self, uuid, password):
        """
        パスワードのハッシュを作成する
        """ 
        def get_salt(uuid):
            """
            固定ソルトとユーザUUID
            """
            FIXED_SALT = b'd0d68c0d5bb78d78265c0d588f23bc60'
            user_id_bytes = bytes(str(uuid), encoding='utf-8')
            return user_id_bytes + FIXED_SALT

        import hashlib
        STRETCH_COUNT = 100
        salt = get_salt(uuid)
        current_hash = b''
        password_bytes = bytes(password, encoding='utf-8')
        for _ in range(1, STRETCH_COUNT):
            hash_target = current_hash + password_bytes + salt
            current_hash = bytes(hashlib.sha256(hash_target).hexdigest(), 'ascii')
        return str(current_hash, encoding='utf-8')

    def _get_encrypt_password(self, password):
        from cryptography.fernet import Fernet
        # UTF-8で符号化してByte列で出力
        b_password = password.encode()
        # 暗号化
        cipher_suite = Fernet(self.KEY_OF_TMP_PASS)
        cipher_text = cipher_suite.encrypt(b_password)
        return cipher_text.decode()

    def _get_decrypt_password(self, password):
        from cryptography.fernet import Fernet, InvalidToken
        # 復号化
        cipher_suite = Fernet(self.KEY_OF_TMP_PASS)
        try:
            return cipher_suite.decrypt(password.encode(),ttl=self.VALID_SECOND_OF_TMP_PASS).decode()
        except InvalidToken:
            raise Exception('仮パスワードの有効期間が切れました、仮パスワードをリセットして下さい')

    def _generate_password(self):
        # パスワードを自動生成する
        return str(uuid.uuid4())[0:8]

    def _set_state(self, next_state):
        if self.state == User.TMP_STATE and next_state == User.INACTIVE_STATE:
            raise Exception('誤ったユーザの状態遷移が指定されました')
        if self.state == User.INACTIVE_STATE and next_state == User.TMP_STATE:
            raise Exception('誤ったユーザの状態遷移が指定されました')

        if self.state == User.TMP_STATE and next_state == User.ACTIVE_STATE:
            # 仮登録状態から登録状態へ遷移する場合
            pass

        self.state = next_state

    def _get_admin_role_flags(self):
        from sqlalchemy import func, case, null
        from .role import Role
        from .user_role import UserRole

        query = self._session.query(
                        func.count(
                            case([(Role.uuid == Role.SYS_ADMIN_ROLE_UUID,1)],else_=null())
                        ).label('sys_admin'),
                        func.count(
                            case([(Role.uuid == Role.USR_ADMIN_ROLE_UUID,1)],else_=null())
                        ).label('usr_admin')
                    ).\
                    select_from(Role).\
                    outerjoin(UserRole, UserRole.role_id==Role.id).\
                    filter(Role.uuid.in_([Role.SYS_ADMIN_ROLE_UUID,Role.USR_ADMIN_ROLE_UUID])).\
                    filter(UserRole.user_id==self.id)

        result = query.one()

        # 戻り値の作成
        return {Role.SYS_ADMIN_ROLE_LABEL:result.sys_admin > 0, Role.USR_ADMIN_ROLE_LABEL:result.usr_admin > 0}

    @property
    def is_temp(self):
        return self.state == User.TMP_STATE

    @property
    def is_inactive(self):
        return self.state == User.INACTIVE_STATE

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

    @property
    def creator_str(self):
        if self.creator is None:
            return ''
        return self.creator.name

    @property
    def created_at_str(self):
        from kskp.core import Util
        return Util.datetime_to_local_time_str(self.created_at)

    def save(self):
        """
        Userを保存する
        """
        try:
            # Usersテーブルにレコードを新規追加する
            self._session.add(self)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()
            # everyoneロールに所属させる
            from kskp.store.factory import RoleFactory
            role_factory = RoleFactory(self._session)
            everyone_role = role_factory.load_everyone_role()
            everyone_role.join_user(self)

    def update_email(self, new_email, modifier=None):
        """
        Userのemail列を更新する
        """
        # 妥当なE-Mailでない場合は例外を送出する
        self._valid_email_or_raise(new_email)

        try:
            self.email = new_email
            self._modifier_id = (modifier or self._session.user).id
            self._session.update(self)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

        return self

    def update_password(self, new_password, modifier=None):
        # 妥当なパスワードでない場合は例外を送出する
        self._valid_password_or_raise(new_password)

        try:
            # 登録状態に変更する
            self._set_state(User.ACTIVE_STATE)
            self.password = self._get_password_hash(self.uuid, new_password)
            self._modifier_id = (modifier or self._session.user).id
            self._session.update(self)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()
        
        return self

    def reset_password(self, modifier=None):
        """
        管理者がパスワードをリセットする
        """
        if not self._session.has_usr_admin():
            raise NotAuthorizedException('ユーザ管理者以外のユーザはパスワードをリセットできません')
        
        # パスワードを自動生成する
        new_password = self._generate_password()

        # 妥当なパスワードでない場合は例外を送出する
        self._valid_password_or_raise(new_password)

        try:
            # 仮登録状態に変更する
            self._set_state(User.TMP_STATE)
            self.password = self._get_encrypt_password(new_password)
            self._modifier_id = (modifier or self._session.user).id
            self._session.update(self)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()
        
        return self

    def update_name(self, new_name, modifier=None):
        # 妥当なユーザ名でない場合は例外を送出する
        self._valid_name_or_raise(new_name)

        try:
            self.name = new_name
            self._modifier_id = (modifier or self._session.user).id
            self._session.update(self)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()
        
        return self

    def update_self_role_id(self, new_role_id, modifier=None):
        try:
            self.self_role_id = new_role_id
            if modifier or self._session.user:
                self._modifier_id = (modifier or self._session.user).id
            self._session.update(self)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()
        
        return self

    def delete(self):
        """
        Userを削除する
        """
        from kskp.store.factory import UserRoleFactory
        user_role_factory = UserRoleFactory(self._session)
        
        try:
            # users_rolesテーブルから全ての削除ユーザの行を削除する
            user_role_factory.delete_all_by_user_id(self.id)
            # usersテーブルから削除ユーザの行を削除する
            self._session.delete(self)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

    def throw_away(self, modifier=None):
        """
        登録Userを論理削除する
        """
        # 仮登録Userは物理削除する
        if self.is_temp:
            self.delete()
            return

        try:
            # 論理削除状態に変更する
            self._set_state(User.INACTIVE_STATE)
            self._modifier_id = (modifier or self._session.user).id
            self._session.update(self)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

    def put_back(self, modifier=None):
        """
        論理削除Userを復帰する
        """
        if self.is_temp:
            raise Exception('仮登録ユーザを復帰させることはできません')

        try:
            # 登録状態に変更する
            self._set_state(User.ACTIVE_STATE)
            self._modifier_id = (modifier or self._session.user).id
            self._session.update(self)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

        return self

    def authenticate(self, password):
        """
        IDとパスワードを元に認証処理を行う
        認証の成功時にはTrueを、失敗すればFalseを返す
        """
        if self.password is None:
            # そもそもユーザが存在しない場合
            return False
        elif self.is_inactive:
            # 論理削除ユーザは認証できない
            return False
        # パスワード判定処理
        elif self.is_temp:
            return password == self._get_decrypt_password(self.password)
        else:
            return self._get_password_hash(self.uuid, password) == self.password

    def load_self_role(self):
        """
        本人ロールを取得する
        """
        from kskp.store.factory import RoleFactory
        role_factory = RoleFactory(self._session)

        if self.self_role_id is None:
            # 本人ロールを作成する
            self_role = role_factory.create(self.name)
            self_role.save()
            # 本人ロールを設定する
            self.update_self_role_id(self_role.id)
        else:
            self_role = role_factory.find_by_id(self.self_role_id)

        return self_role

    def to_json(self):
        ret = {
            'uuid'     : self.uuid,
            'email'    : self.email,
            'name'     : self.name,
            'state'    : self.state,
            'creator'  : self.creator_str,
            'createdAt': self.created_at_str
        }

        # 仮登録状態、かつ操作ユーザがユーザ管理者権限を持つ場合は仮パスワードも返す
        if self.is_temp and self._session.has_usr_admin():
            ret.update({'password': self._get_decrypt_password(self.password)})

        return ret

    def __repr__(self):
        return f'User({self.id}, {self.name})'

    def __eq__(self, other):
        return self.uuid == other.uuid

    def __ne__(self, other):
        return self.uuid != other.uuid
