from sqlalchemy import event, DDL

from kskp.store import engine, BaseModel

from .exceptions import NotAuthorizedException, InvalidPassword
from .auth import Auth
from .user_role import UserRole
from .role import Role
from .user import User

@event.listens_for(BaseModel.metadata, 'after_create')
def receive_after_create(target, connection, tables, **kw):
    "listen for the 'after_create' event"

    if 'users' in tables and 'roles' in tables and 'users_roles' in tables:
        create_useful_views()
        if 'data' in tables and 'auths' in tables:
            create_ud_view()

def create_useful_views():
    """
    ユーザとロールの対応の一覧を表示するVIEWを作成する
    (開発及び運用時に閲覧するために用意しておく)
    """
    ug_view = """
    create view ug as
    select U.id as user_id, U.name as user_name, G.id as role_id, G.name as group_name
    from roles G left join users U
    on exists (select * from Users_Roles UG
               where UG.user_id = U.id and UG.role_id = G.id)
    """
    engine.execute(DDL('drop view if exists ug'))
    engine.execute(DDL(ug_view))

def create_ud_view():
    """
    ユーザとデータの権限対応の一覧を表示するVIEWを作成する
    (開発及び運用時に閲覧するために用意しておく)
    """
    ud_view = """
    create view ud as
    select U.id, U.name, D.uuid, D.label, D.path, D.type
    from Data D left join Users U
    on exists (select * from Auths A
                join Data D on A.datum_id = D.id
                where exists (select * from Roles G
                             where exists (select * from users_roles UG
                                           where UG.role_id = G.id
                                             and UG.user_id = U.id) ))

    """
    engine.execute(DDL('drop view if exists ud'))
    engine.execute(DDL(ud_view))

def admin_exists():
    """
    管理者ロールに所属するユーザがいる場合はTrueを返す
    """

    sql = f"""
    select count(*) from roles G
    where G.uuid = '{Role.SYS_ADMIN_ROLE_UUID}'
      and exists (select * from users_roles UG
                  where UG.role_id = G.id
                    and exists (select * from users U
                                where U.id = UG.user_id) )
    """
    # adminロールに所属するユーザ数をカウントする
    count = engine.execute(sql).scalar()
    return count > 0

# テーブルを作成する
# BaseModel.metadata.create_all(bind=engine, checkfirst=True)

def add_admin_user_and_role(factory):
    """
    デフォルト管理者ユーザと管理者ロールを作成する
    """
    # 管理者ロールが存在しない場合は作成する
    sys_admin_role = factory.load_sys_admin_role()

    # 管理者ユーザが存在しない場合はデフォルト管理者ユーザを作成する
    if not sys_admin_role.has_joined_user():
        # 初期管理者ユーザを作成する
        sys_admin_user = factory.create_admin_user()
        sys_admin_user.save()
        # 初期管理者ユーザを管理者ロールに参加させる
        sys_admin_role.join_user(sys_admin_user)


