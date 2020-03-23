from sqlalchemy import event, DDL

from kskp.store import engine, BaseModel

from .exceptions import NotAuthorizedException
from .auth import Auth
from .user_group import UserGroup
from .system_group import SystemGroup
from .group import Group
from .user import User

@event.listens_for(BaseModel.metadata, 'after_create')
def receive_after_create(target, connection, tables, **kw):
    "listen for the 'after_create' event"

    if 'users' in tables and 'groups' in tables and 'users_groups' in tables:
        create_useful_views()
        if 'data' in tables and 'auths' in tables:
            create_ud_view()

def create_useful_views():
    """
    ユーザとグループの対応の一覧を表示するVIEWを作成する
    (開発及び運用時に閲覧するために用意しておく)
    """
    ug_view = """
    create view ug as
    select U.id as user_id, U.name as user_name, G.id as group_id, G.name as group_name
    from groups G left join users U
    on exists (select * from Users_Groups UG
               where UG.user_id = U.id and UG.group_id = G.id)
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
                where exists (select * from Groups G
                             where exists (select * from users_groups UG
                                           where UG.group_id = G.id
                                             and UG.user_id = U.id) ))

    """
    engine.execute(DDL('drop view if exists ud'))
    engine.execute(DDL(ud_view))

def admin_exists():
    """
    管理者グループに所属するユーザがいる場合はTrueを返す
    """

    sql = f"""
    select count(*) from groups G
    where exists (select * from system_groups SG
                  where SG.type = '{SystemGroup.ADMIN_TYPE}'
                    and SG.group_id = G.id)
      and exists (select * from users_groups UG
                  where UG.group_id = G.id
                    and exists (select * from users U
                                where U.id = UG.user_id) )
    """
    # adminグループに所属するユーザ数をカウントする
    count = engine.execute(sql).scalar()
    return count > 0

def add_admin_user_and_group():
    """
    デフォルト管理者ユーザと管理者グループを作成する
    """
    # 管理者グループが存在しない場合は作成する
    admin_group = Group.load_admin_group()

    # 管理者ユーザが存在しない場合はデフォルト管理者ユーザを作成する
    if not admin_group.has_joined_user():
        # 初期管理者ユーザを作成する
        admin_user = User('admin@kskp.io', 'adminpass', 'Admin')
        admin_user.save()
        # 初期管理者ユーザを管理者グループに参加させる
        admin_group.join_user(admin_user.id)

# テーブルを作成する
BaseModel.metadata.create_all(bind=engine, checkfirst=True)

