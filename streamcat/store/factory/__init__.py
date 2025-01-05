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

async def init_admin_users():
    async with UnAuthzFactory() as ufactory:
        from streamcat.store.auth import Role

        # システム管理者とユーザ管理者を作成する
        sys_admin_user = await ufactory.load_sys_admin_user()
        usr_admin_user = await ufactory.load_usr_admin_user(activate_if_inactive=True)

        sys_factory = ufactory.create_authz_factory(sys_admin_user)
        sys_admin_role = sys_factory.role.load_sys_admin_role()
        if sys_admin_user.is_init:
            # システム管理者を新規作成した場合は、システム管理者ロールの一般メンバに加える
            sys_admin_role.join_member(Role.Member(sys_admin_user, owner=False))

        usr_factory = ufactory.create_authz_factory(usr_admin_user)
        # ユーザ管理者ロールを作成する
        # (ロールを新規作成した場合は作成者がロールの所有者になる)
        usr_factory.role.load_usr_admin_role()

        # everyoneロールにユーザ管理者を所有者として参加させる
        # (unauthz_factoryからロールを新規追加された場合、作成者はロールに参加されない)
        # (ユーザ管理者ロールを作成した後に処理すること)
        everyone_role = usr_factory.role.load_everyone_role()
        # edit_lock_roleロールにユーザ管理者を所有者として参加させる
        edit_lock_role = usr_factory.role.load_edit_lock_role()
        if usr_admin_user.is_init:
            # ユーザ管理者を新規作成した場合は、ユーザ管理者ロールの所有者メンバに加える
            everyone_role.join_member(Role.Member(usr_admin_user, owner=True))
            # 編集ロックロールの所有者メンバに加える
            edit_lock_role.join_member(Role.Member(usr_admin_user, owner=True))

        # システムフォルダを作成する
        usr_factory.data.load_cache_folder()
        usr_factory.data.load_activity_folder()
        usr_factory.data.load_trash_folder()

        # ライブラリにある全てのスケジュールをスケジューラに登録する
        from ..scheduler import schedule_manager
        schedule_manager.load_from_library(usr_factory.data)
