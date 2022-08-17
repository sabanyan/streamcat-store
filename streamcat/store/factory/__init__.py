from .factory import (
    Factory,
    UnAuthzFactory,
    DatumFactory,
    StoreFactory,
    AuthFactory,
    RoleFactory,
    UserRoleFactory,
    UserFactory
)

# 
# 全てのテーブルを作成する
# 
from streamcat.core import BaseModel, engine
BaseModel.metadata.create_all(bind=engine, checkfirst=True)


with UnAuthzFactory() as unauthz_factory:
    from streamcat.store.auth import Role

    # システム管理者とユーザ管理者を作成する
    sys_admin_user = unauthz_factory.load_sys_admin_user()
    usr_admin_user = unauthz_factory.load_usr_admin_user(activate_if_inactive=True)

with Factory(sys_admin_user) as factory:
    sys_admin_role = factory.role.load_sys_admin_role()
    if sys_admin_user.is_init:
        # システム管理者を新規作成した場合は、システム管理者ロールの一般メンバに加える
        sys_admin_role.join_member(Role.Member(sys_admin_user, owner=False))

with Factory(usr_admin_user) as factory:
    # ユーザ管理者ロールを作成する
    # (ロールを新規作成した場合は作成者がロールの所有者になる)
    factory.role.load_usr_admin_role()

    # everyoneロールにユーザ管理者を所有者として参加させる
    # (unauthz_factoryからロールを新規追加された場合、作成者はロールに参加されない)
    # (ユーザ管理者ロールを作成した後に処理すること)
    everyone_role = factory.role.load_everyone_role()
    # edit_lock_roleロールにユーザ管理者を所有者として参加させる
    edit_lock_role = factory.role.load_edit_lock_role()
    if usr_admin_user.is_init:
        # ユーザ管理者を新規作成した場合は、ユーザ管理者ロールの所有者メンバに加える
        everyone_role.join_member(Role.Member(usr_admin_user, owner=True))
        # 編集ロックロールの所有者メンバに加える
        edit_lock_role.join_member(Role.Member(usr_admin_user, owner=True))

    # システムフォルダを作成する
    factory.data.load_cache_folder()
    factory.data.load_activity_folder()
    factory.data.load_trash_folder()

    # ライブラリにある全てのスケジュールをスケジューラに登録する
    from ..scheduler import schedule_manager
    schedule_manager.load_from_library(factory.data)
