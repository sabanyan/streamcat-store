from sqlalchemy import event, DDL

from kskps.library import session
from kskps.library import engine
from kskps.library import BaseModel

from .user_group import UserGroup
from .group import Group
from .user import User
from .auth import Auth

@event.listens_for(BaseModel.metadata, 'after_create')
def receive_after_create(target, connection, tables, **kw):
    "listen for the 'after_create' event"

    if tables:
        print('tables were created')
    else:
        print('tables were not created')

    create_useful_views()
    create_ud_view()

def create_useful_views():
    """
    ユーザとグループの対応の一覧を表示するVIEWを作成する
    (開発及び運用時に閲覧するために用意しておく)
    """
    ug_view = """
    create view ug as
    select U.id, U.name, G.id, G.name
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
    select U.id, U.name, D.uuid, D.path
    from Data D left join Users U
    on exists (select * from Auths A
               where A.data_id = D.id
                 and exists (select * from Groups G
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
    sql = """
    select count(*) from groups G
    where is_admin = 1
      and exists (select * from users_groups UG
                  where UG.group_id = G.id
                    and exists (select * from users U
                                where U.id = UG.user_id) )
    """
    # adminグループに所属するユーザ数をカウントする
    count = session.execute(sql).scalar()
    return count > 0

def add_admin_user_and_group():
    """
    デフォルト管理者ユーザとデフォルト管理者グループを作成する
    """
    # 初期管理者ユーザを作成する
    admin_user = User('dev@kskp.io', 'devpass', 'Admin')
    # 管理者ユーザの作成者は管理者自身である
    admin_user.creator = admin_user.id
    # 初期管理者グループを作成する
    admin_group = Group('Admin', is_admin=1, creator=admin_user.id)
    # 初期管理者ユーザを初期管理者グループに所属させる
    user_group = UserGroup(admin_user.id, admin_group.id, creator=admin_user.id)
    # DBに格納する
    session.add(admin_user)
    session.add(admin_group)
    session.add(user_group)
    session.commit()


# テーブルを作成する
BaseModel.metadata.create_all(bind=engine, checkfirst=True)

# 管理者グループに所属するユーザが存在しない場合は、
# デフォルト管理者ユーザとデフォルト管理者グループを作成する
if not admin_exists():
    add_admin_user_and_group()
