import os
import uuid
import sqlalchemy.types
from sqlalchemy import Column, String, text
from sqlalchemy.sql import operators
from sqlalchemy.dialects.postgresql import INTEGER, TIMESTAMP, UUID, ENUM
from .exceptions import NotAuthorizedException
from . import BaseModel

class User(BaseModel):
    # テーブル名の定義
    __tablename__ = 'users'

    class MyString(sqlalchemy.types.TypeDecorator):
        """
        SQLAlchemyにおいてString列のlike/ilike演算で検索語をエスケープする
        """
        impl = sqlalchemy.types.String

        class comparator_factory(String.Comparator):

            # LIKE検索語のエスケープ変換テーブル
            ESCAPE_TABLE = str.maketrans({
                                '%' : '\%',
                                '_' : '\_',
                                '\\': '\\\\'
                           })

            def icontains(self, other):
                """
                検索語を含むか否か判定する(大文字小文字の違いを無視する)
                """
                # 検索語をエスケープする
                escaped_search_str = other.translate(self.ESCAPE_TABLE)
                return self.operate(operators.ilike_op, '%' + escaped_search_str + '%', escape='\\')

    INIT_STATE     = 'init'     # 初期状態
    TMP_STATE      = 'tmp'      # 仮登録状態
    ACTIVE_STATE   = 'active'   # 登録状態
    INACTIVE_STATE = 'inactive' # 論理削除状態
    EXPIRED_STATE  = 'expired'  # 失効状態(表示のみに使用)

    # 仮パスワードの有効期間(14日間)

    # 環境変数から仮パスワードの有効日数を取得する
    # (設定値がない場合は14日間とする)
    TMP_PASS_EXPIRE_SECONDS = int(os.getenv('KSKP_TMP_PASS_EXPIRE_DAYS', 14)) * 24 * 60 * 60

    # 列名と列のデータ型等の定義
    id            = Column(INTEGER, primary_key=True, autoincrement=True)
    uuid          = Column(UUID, nullable=False, unique=True)
    email         = Column(MyString, nullable=False, unique=True)
    name          = Column(MyString, nullable=False)
    password      = Column(String, nullable=False)
    # ユーザ状態
    state         = Column(ENUM(INIT_STATE, TMP_STATE, ACTIVE_STATE, INACTIVE_STATE, name='user_state'), nullable=False)
    # 本人ロールのRoleId
    self_role_id  = Column(INTEGER, nullable=True)

    def __init__(self, session, email, name, password=None):
        """
        コンストラクタ
        """
        super().__init__(session)

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
        # 妥当なパスワードでない場合は例外を送出する
        self._valid_password_or_raise(new_password)
        self.password = self._get_encrypt_password(new_password)

        # 本パスワードに変更する前は初期状態である
        self.state = User.INIT_STATE

    def _init_on_activation(self):
        """
        登録状態に遷移した時の初期処理
        """
        # 本人ロールを作成する
        # (プロジェクトにユーザを所属させる処理(ProjectFolder.join_member)において
        #  他ユーザが本人ロールのIDを参照する必要があるため、ここで本人ロールを作成する)
        self.load_self_role()

    def _valid_email_or_raise(self, email):
        if email is None or email=='':
            raise Exception('E-Mailに空文字を指定できません')

    def _valid_name_or_raise(self, name):
        if name is None or name=='':
            raise Exception('ユーザ名に空文字を指定できません')

    def _valid_password_or_raise(self, password):
        import re
        from .exceptions import InvalidPassword
        if password is None or password == '':
            raise InvalidPassword('空のパスワードに変更できません')
        if len(password) < 10 or 64 < len(password):
            raise InvalidPassword('パスワードは10文字以上64文字以下にしてください')
        if not re.search(r'^[\x21-\x7E]+$', password):
            raise InvalidPassword('パスワードに使用できる文字は英数・記号(空白を除く)です')

        if self.is_init_or_temp:
            if password == self._get_decrypt_password(self.password):
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

    def _is_expired_password(self, password):
        """
        仮パスワードが有効期限を過ぎている場合はTrueを返す
        """
        import time
        from cryptography.fernet import Fernet, InvalidToken

        cipher_suite = Fernet(self.KEY_OF_TMP_PASS)
        try:
            # 仮パスワードを暗号化した時刻(Epoch Time)
            encrypted_at = cipher_suite.extract_timestamp(password.encode())
        except InvalidToken:
            # 復号に失敗しても処理は続行可能なので例外は送出しない
            import warnings
            warnings.warn(f'{self}の仮パスワードが無効なので有効期限を取得できませんでした')
            # 例外が発生した場合は、有効期間が過ぎていると扱う
            return True

        # 現在時刻(Epoch Time)
        current = time.time()
        return encrypted_at + self.TMP_PASS_EXPIRE_SECONDS < current

    def _generate_password(self):
        # パスワードを自動生成する
        return str(uuid.uuid4())[-10:]

    def _set_state(self, next_state):
        # if self.state == User.TMP_STATE and next_state == User.INACTIVE_STATE:
        #     raise Exception('誤ったユーザの状態遷移が指定されました')
        if self.state == User.INACTIVE_STATE and next_state == User.TMP_STATE:
            raise Exception('誤ったユーザの状態遷移が指定されました1')
        elif next_state == User.INIT_STATE:
            raise Exception('誤ったユーザの状態遷移が指定されました2')

        if self.state == User.INIT_STATE and next_state == User.ACTIVE_STATE:
            # 初期状態から登録状態へ遷移する場合
            self._init_on_activation()

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

    def _able_to_delete_user_or_raise(self):
        # ユーザ管理者のみ、ユーザを削除できる
        if not self._session.has_usr_admin():
            raise NotAuthorizedException('ユーザを削除できませんでした')

        # 削除ユーザが全てのロールから脱退できるか確認する(本人ロールを除く)
        for role in self.get_joined_roles():
            if role.is_usr_admin and role.is_last_owner(self):
                role.raise_no_role_owner_exception()

    def _join_everyone_role(self):
        # everyoneロールに所属させる
        # (everyoneロールの作成者であるユーザ管理者のみがユーザを追加できる)
        from .role import Role
        from ..factory import RoleFactory
        everyone_role = RoleFactory(self._session).load_everyone_role()
        everyone_role.join_member(Role.Member(self, False))

    def _join_edit_lock_role(self):
        # edit_lockロールに所属させる
        # (edit_lockロールの作成者であるユーザ管理者のみがユーザを追加できる)
        from .role import Role
        from ..factory import RoleFactory
        edit_lock_role = RoleFactory(self._session).load_edit_lock_role()
        edit_lock_role.join_member(Role.Member(self, False))

    @property
    def is_init(self):
        return self.state==User.INIT_STATE

    @property
    def is_init_or_temp(self):
        return self.state in (User.INIT_STATE, User.TMP_STATE)

    @property
    def is_inactive(self):
        return self.state == User.INACTIVE_STATE

    def password_expired(self):
        # 初期状態は仮登録状態と表示する
        if self.state in (User.TMP_STATE, User.INIT_STATE):
            return self._is_expired_password(self.password)
        else:
            return False

    def save(self):
        """
        Userを保存する
        """
        from sqlalchemy.exc import IntegrityError

        try:
            # Usersテーブルにレコードを新規追加する
            self._session.add(self)
        except IntegrityError:
            self._session.rollback()
            raise Exception(f'メールアドレス({self.email})は他のユーザーが使用中です')
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

        # everyoneロールに所属させる
        self._join_everyone_role()
        # edit_lock_roleに所属させる
        self._join_edit_lock_role()

    def update_email(self, new_email, modifier=None):
        """
        Userのemail列を更新する
        """
        from sqlalchemy.exc import IntegrityError

        # 妥当なE-Mailでない場合は例外を送出する
        self._valid_email_or_raise(new_email)

        try:
            self.email = new_email
            self._modifier_id = (modifier or self._session.user).id
            self._session.update(self)
        except IntegrityError:
            self._session.rollback()
            raise Exception(f'メールアドレス({new_email})は他のユーザーが使用中です')
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
        # 削除できない場合は例外を送出する
        self._able_to_delete_user_or_raise()

        try:
            # 全てのロールから脱退する(本人ロールと編集ロックロールを除く)
            for role in self.get_joined_roles():
                if not role.is_self_role() and not role.is_edit_lock:
                    role.leave_member(self)
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
        # 仮登録Userで、本人ロールと(everyoneとedit_lockを除く)自分が属するロールが存在していなければ物理削除する
        if self.is_init_or_temp and self.self_role_id is None:
            from kskp.store.auth import Role
            from kskp.store.factory import UserRoleFactory
            except_role_uuids = [Role.EVERYONE_ROLE_UUID, Role.EDIT_LOCK_ROLE_UUID]
            user_roles = UserRoleFactory(self._session).find_all_by_user_id(self.id, except_role_uuids)

            # everyoneとedit_lock以外の所属ロールが無ければ、Userを物理削除する
            if len(user_roles) == 0:
                self.delete()
                return

        # 削除できない場合は例外を送出する
        self._able_to_delete_user_or_raise()

        try:
            # 全てのロールから脱退する(本人ロールと編集ロックロールを除く)
            for role in self.get_joined_roles():
                if not role.is_self_role() and not role.is_edit_lock:
                    role.leave_member(self)
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
        if self.is_init_or_temp:
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

        # everyoneロールに復帰させる
        self._join_everyone_role()

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
        elif self.is_init_or_temp:
            if self._is_expired_password(self.password):
                # 仮パスワードの有効期間が過ぎている場合は認証できない
                return False
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
            self_role.save(for_self_role=True)
            # 本人ロールを設定する
            self.update_self_role_id(self_role.id)
        else:
            self_role = role_factory.find_by_id(self.self_role_id)

        return self_role

    def get_joined_roles(self):
        """
        所属する全てのロールを返す
        """
        from sqlalchemy import exists, and_, or_
        from .role import Role
        from .user_role import UserRole

        exists_user_role = exists().where(and_(UserRole.role_id==Role.id, UserRole.user_id==self.id))
        exists_user = exists().where(and_(User.self_role_id==Role.id, User.id==self.id))

        query = self._session.query(Role).\
                      filter(or_(exists_user_role, exists_user))
        return query.order_by(Role.name).all()

    def get_joined_projects(self):
        """
        所属する全てのプロジェクトを返す
        """
        from sqlalchemy import exists, and_, or_
        from kskp.core import Datum
        from kskp.store import ProjectFolder
        from .user_role import UserRole
        from .auth import Auth

        exists_user_role = exists().where(and_(UserRole.role_id==Auth.role_id, UserRole.user_id==self.id))
        exists_user = exists().where(and_(User.self_role_id==Auth.role_id, User.id==self.id))

        exists_stmt = exists().where(
                                        and_(Auth.datum_id==ProjectFolder.id,
                                             Auth.permission==True,
                                             or_(exists_user, exists_user_role)
                                        )
                                    )

        query = self._session.query(ProjectFolder).\
                              filter(ProjectFolder.type==Datum.PROJECT_TYPE).\
                              filter(exists_stmt)
        return query.order_by(ProjectFolder._label).all()

    def get_allowlist(self):
        """
        処理の許可リストを返す
        """
        has_usr_admin = self._session.has_usr_admin()
        return {
            'findUsers'      : has_usr_admin,
            'createUser'     : has_usr_admin,
            'updateUser'     : has_usr_admin,
            'updateSelfUser' : True,
            'readUserPassword' : has_usr_admin,
            'deleteUser'     : has_usr_admin,
        }

    def to_json(self):
        def display_state():
            """
            self.stateを表示状態に変換する
            """
            if self.password_expired():
                return self.EXPIRED_STATE
            elif self.is_init_or_temp:
                # 初期状態は仮登録状態と表示する
                return self.TMP_STATE
            else:
                return self.state

        ret = {
            'uuid'     : self.uuid,
            'email'    : self.email,
            'name'     : self.name,
            'state'    : display_state(),
            'creator'  : self.creator_str,
            'createdAt': self.created_at_str
        }

        # 仮登録状態、かつ操作ユーザがユーザ管理者権限を持つ場合は仮パスワードも返す
        if self.is_init_or_temp and self._session.has_usr_admin():
            ret.update({'password': self._get_decrypt_password(self.password)})

        return ret

    def __repr__(self):
        return f'User({self.id}, {self.name})'

    def __eq__(self, other):
        return self.uuid == other.uuid

    def __ne__(self, other):
        return self.uuid != other.uuid

    def __hash__(self) -> int:
        return hash(self.uuid)
