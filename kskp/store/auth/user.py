from hashlib import new
import os
import uuid
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

    # 列名と列のデータ型等の定義
    id            = Column(INTEGER, primary_key=True, autoincrement=True)
    uuid          = Column(UUID, nullable=False, unique=True)
    email         = Column(String, nullable=False, unique=True)
    password      = Column(String)
    name          = Column(String, nullable=False)
    # ユーザ状態
    state         = Column(ENUM(TMP_STATE, ACTIVE_STATE, INACTIVE_STATE, name='user_state'), nullable=False)
    # 本人ロールのRoleId
    self_role_id  = Column(INTEGER, nullable=True)
    _creator_id   = Column('creator', INTEGER)
    _modifier_id  = Column('modifier', INTEGER)
    created_at    = Column(TIMESTAMP, default=text('statement_timestamp()'))
    modified_at   = Column(TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()'))

    def __init__(self, session, email, password, name):
        """
        コンストラクタ
        """
        # SQLAlchemy Session
        self._session = session

        # UUIDを採番する
        self.uuid = str(uuid.uuid4())

        self.email = email
        self.password = self._get_password_hash(self.uuid, password)
        self.name = name

        # 本パスワードに変更する前は仮登録状態である
        self.state = User.TMP_STATE

        # creator, modifier
        if session is not None and session.user is not None:
            self._creator_id = session.user.id
            self._modifier_id = session.user.id

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

    @property
    def is_temp(self):
        return self.state == User.TMP_STATE

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

    # def _require_admin_auth(func):
    #     """
    #     操作ユーザがadminロールに所属していない場合は例外を送出する
    #     """
    #     @functools.wraps(func)
    #     def wrapper(self, *args, **kwargs):
    #         sql = """
    #         select count(is_admin) from groups G
    #         where is_admin = 1
    #           and exists (select * from users_groups UG
    #                        from UG join G using (id)
    #                        where exists (select * from users U
    #                                       where U.id = UG.user_id
    #                                         and U.id = {creator}) )
    #         """.format(creator=str(self.creator))
    #         # SQLを発行する
    #         count = session.execute(sql).scalar()
    #         # creatorはadminロールに所属していない場合は0件となる
    #         if count == 0:
    #             pprint.pprint(func)
    #             raise Exception("user id (%s) is not authorized to call function (%s.%s)." 
    #                             % (self.creator, func.__module__, func.__name__))
            
    #         return func(self, *args, **kwargs)
    #     return wrapper

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

    def update_email(self, new_email, modifier=None):
        """
        Userのemail列を更新する
        """
        try:
            self.email = new_email
            self._modifier_id = (modifier or self._session.user).id
            self._session.update(self)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

    def update_password(self, new_password, modifier=None):
        from .exceptions import InvalidPassword
        
        if new_password is None or new_password == '':
            raise InvalidPassword('空のパスワードに変更できません')
        if self._get_password_hash(self.uuid, new_password) == self.password:
            raise InvalidPassword('同じパスワードに変更できません')

        try:
            # 登録状態に変更する
            self.state = User.ACTIVE_STATE
            self.password = self._get_password_hash(self.uuid, new_password)
            self._modifier_id = (modifier or self._session.user).id
            self._session.update(self)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

    def update_name(self, new_name, modifier=None):
        try:
            self.name = new_name
            self._modifier_id = (modifier or self._session.user).id
            self._session.update(self)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

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

    def reset_password(self, modifier=None):
        """
        管理者がパスワードをリセットする
        """
        new_password = str(uuid.uuid4)[0:8]
        # 仮登録状態に変更する
        self.state = User.ACTIVE_STATE
        self.update_password(new_password, modifier=modifier)
        return new_password

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


    def authenticate(self, password):
        """
        IDとパスワードを元に認証処理を行う
        認証の成功時にはTrueを、失敗すればFalseを返す
        """
        if self.password is None:
            # そもそもユーザが存在しない場合
            return False

        # パスワード判定処理
        return self._get_password_hash(self.uuid, password) == self.password

    def has_read_authority(self, uuid):
        # select 
        #      A.read
        # from auths A
        # where exists (select * from data D
        #               where D.id = A.datum_id
        #                 and D.uuid = uuid)
        #   and exists (select * from groups G
        #               where G.id = A.role_id
        #                 and exists (select * from users_groups UG
        #                             where UG.role_id = G.id
        #                               and exists (select * from users U
        #                                           where U.id = UG.user_id
        #                                             and U.id = self.id) ))

        # このメソッドはUserとDatumのどちらに持たせたほうがいい？
        pass


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

    def __repr__(self):
        return f'User({self.id}, {self.name})'

    def __eq__(self, other):
        return self.uuid == other.uuid

    def __ne__(self, other):
        return self.uuid != other.uuid
