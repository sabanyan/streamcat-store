from . import db
import uuid
import sqlalchemy
import json
import ast
from sqlalchemy import TypeDecorator, types
from sqlalchemy.dialects.postgresql import JSONB

# sqlalchemyのgithubを見ると、sqliteのjsonを追加したものが最新ソースに上がっているが
# 最新版のsqlalchemy(2018/10/23現在：ver1.2.12)にはまだ更新されていない模様（Pyplのpkgが更新されていない？）
# 下記importがエラーになる
# from sqlalchemy.dialects.sqlite import JSON

class Json(TypeDecorator):
    """
    unittestのsqlite用Jsonクラス
    jsonを受け取り、DBにはStringで保存、使うときはjsonに再び変換して返す
    """
    @property
    def python_type(self):
        return object

    impl = types.String

    def process_bind_param(self, value, dialect):
        return json.dumps(value)

    def process_literal_param(self, value, dialect):
        return value

    def process_result_value(self, value, dialect):
        try:
            return ast.literal_eval(value)
        except (ValueError, TypeError):
            return None

class Users(db.Model):
    """
    Usersモデル
    """
    __tablename__ = 'users'
    # カラム
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_id = db.Column(db.ForeignKey('groups.id'))
    name = db.Column(db.String(64))
    email = db.Column(db.String(256), unique=True)
    password = db.Column(db.String(64))
    creatable_projects = db.Column(db.Boolean)
    # リレーション
    userpermissions_project = db.relationship('UserPermissions_Project')
    userpermissions_flow = db.relationship('UserPermissions_Flow')

    def __init__(self, username, email, password, creatable_projects):
        self.name = username
        self.email = email
        self.password = password
        self.creatable_projects = creatable_projects

class Groups(db.Model):
    """
    Groupsモデル
    """
    __tablename__ = 'groups'
    # カラム
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64))
    creatable_projects = db.Column(db.Boolean)
    # グループにプロジェクト作成権限はいらないかも。
    # グループにはユーザ（DB上に存在する）が所属する。
    # また、ユーザにはプロジェクト作成に関する権限が設定されており、
    # ユーザの権限がグループの権限より優先されることから、グループに所属しているいないに関わらずユーザのプロジェクト作成権限が存在するのでそれが使われる。
    # →入れておく

    # リレーション
    grouppermissions_project = db.relationship('GroupPermissions_Project')
    grouppermissions_flow = db.relationship('GroupPermissions_Flow')

    def __init__(self, group_name, creatable_projects):
        self.name = group_name
        self.creatable_projects = creatable_projects

class Projects(db.Model):
    """
    Projectsモデル
    """
    __tablename__ = 'projects'
    # カラム
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64))
    uuid = db.Column(db.String(256), unique=True)
    creator_id = db.Column(db.Integer)
    # リレーション
    userpermissions_project = db.relationship('UserPermissions_Project')
    grouppermissions_project = db.relationship('GroupPermissions_Project')
    flows = db.relationship('Flows')

    def __init__(self, name, uuid, creator_id):
        self.name = name
        self.uuid = uuid
        self.creator_id = creator_id

class Flows(db.Model):
    """
    Flowsモデル
    他にも入れる必要のあるものあるけど(createdAt)、最低限で…
    """
    __tablename__ = 'flows'

    def get_flow_json_column_type(db_name):
        if db_name == 'postgresql':
            return db.Column(JSONB)
        elif db_name == 'sqlite':
            return db.Column(Json)
        else:
            # 適当
            return db.Column(db.JSON)

    # カラム
    # id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 一応既存のkskpの合わせるためにflow_uuidを主キーにしてみる
    uuid = db.Column(db.String, primary_key=True)
    json = get_flow_json_column_type(db.engine.name)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    creator_id = db.Column(db.Integer)
    # リレーション
    userpermissions_flow = db.relationship('UserPermissions_Flow')
    grouppermissions_flow = db.relationship('GroupPermissions_Flow')

    def __init__(self, flow_uuid, flow_json, project_id, creator_id):
        self.uuid = flow_uuid
        self.json = flow_json
        self.project_id = project_id
        self.creator_id = creator_id

class UserPermissions_Project(db.Model):
    """
    UserPermissions_Projectモデル
    """
    __tablename__ = 'userpermissions_project'
    __table_args__ = (
        db.PrimaryKeyConstraint('user_id', 'project_id'),
    )
    # カラム
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    deletable_project = db.Column(db.Boolean, default=True)
    creatable_flows = db.Column(db.Boolean, default=True)
    deletable_flows = db.Column(db.Boolean, default=True)
    readable_flows = db.Column(db.Boolean, default=True)

    def __init__(self, user_id, project_id, deletable_project=True, creatable_flows=True,
                 deletable_flows=True, readable_flows=True):
        self.user_id = user_id
        self.project_id = project_id
        self.deletable_project = deletable_project
        self.creatable_flows = creatable_flows
        self.deletable_flows = deletable_flows
        self.readable_flows = readable_flows

class GroupPermissions_Project(db.Model):
    """
    GroupPermissions_Projectモデル
    """
    __tablename__ = 'grouppermissions_project'
    __table_args__ = (
        db.PrimaryKeyConstraint('group_id', 'project_id'),
    )
    # カラム
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    # プロジェクトを削除できるか
    deletable_project = db.Column(db.Boolean, default=False)
    # 配下にフローを作成できるか
    creatable_flows = db.Column(db.Boolean, default=False)
    # 配下のフローを削除できるか
    deletable_flows = db.Column(db.Boolean, default=False)
    # 配下のフロー一覧の表示
    readable_flows = db.Column(db.Boolean, default=True)

    # グループの初期パーミッションをlinuxのディレクトリの初期パーミッションと同じにするなら、
    # linuxは初期umaskが022でグループのパーミッションは5(r-x)になるので、
    # できることは、プロジェクト配下の「フロー一覧が見える」となり
    # それ以外はFalseになる、とりあえずこの方向で。

    def __init__(self, group_id, project_id, deletable_project=False, creatable_flows=False,
                 deletable_flows=False, readable_flows=True):
        self.group_id = group_id
        self.project_id = project_id
        self.deletable_project = deletable_project
        self.creatable_flows = creatable_flows
        self.deletable_flows = deletable_flows
        self.readable_flows = readable_flows

class UserPermissions_Flow(db.Model):
    """
    UserPermissions_Flowモデル
    """
    __tablename__ = 'userpermissions_flow'
    __table_args__ = (
        db.PrimaryKeyConstraint('user_id', 'flow_uuid'),
    )
    # カラム
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    flow_uuid = db.Column(db.String, db.ForeignKey('flows.uuid'))
    # フローデザイナへアクセスできるか
    readable_flow = db.Column(db.Boolean, default=True)
    # フローを編集できるか
    updatable_flow = db.Column(db.Boolean, default=True)
    # フローを実行できるか
    executable_flow = db.Column(db.Boolean, default=True)

    # linuxでは初期パーミッションはユーザ（所有者）の場合は、実行許可を除く６だが
    # 流石に実行できるべきであるので７（全て許可）にしておく

    def __init__(self, user_id, flow_uuid, updatable_flow=True,
                 readable_flow=True, executable_flow=True):
        self.user_id = user_id
        self.flow_uuid = flow_uuid
        self.updatable_flow = updatable_flow
        self.readable_flow = readable_flow
        self.executable_flow = executable_flow

class GroupPermissions_Flow(db.Model):
    """
    GroupPermissions_Flowモデル
    """
    __tablename__ = 'grouppermissions_flow'
    __table_args__ = (
        db.PrimaryKeyConstraint('group_id', 'flow_uuid'),
    )
    # カラム
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    flow_uuid = db.Column(db.String, db.ForeignKey('flows.uuid'))
    updatable_flow = db.Column(db.Boolean, default=False)
    readable_flow = db.Column(db.Boolean, default=True)
    executable_flow = db.Column(db.Boolean, default=True)

    # linuxでは初期パーミッションはグループの場合は、読み取り可能のみの４だが
    # 実行もできた方がいいと思い（実行後は結果ができるだけなので、大きな悪影響はないと思われるため）
    # とりあえず５（実行とフローデザイナ閲覧）にしておく

    def __init__(self, group_id, flow_uuid, updatable_flow=False,
                 readable_flow=True, executable_flow=True):
        self.group_id = group_id
        self.flow_uuid = flow_uuid
        self.updatable_flow = updatable_flow
        self.readable_flow = readable_flow
        self.executable_flow = executable_flow

# Region　APIで使うパブリックメソッド

def fetch_projects(user_id):
    """
    APIで返すプロジェクト一覧を取得する
    返す形式：
        {
            projects:[
                {
                    プロジェクト情報や権限
                },
                …
            ],
            creatable: True or False（プロジェクト作成できるか）
        }
    """
    data = {}

    projects = get_projects_with_permission(user_id)
    user = get_user_by_id(user_id)

    data['projects'] = projects
    data['creatable'] = user.creatable_projects

    return data

def create_project(user_id, project_name):
    """
    指定したユーザが作成できるかを調べ、作成可能ならばプロジェクトを作成する
    返す形式：
        True or False
        （Falseの場合はロールバックしてから返す）
    """
    user = get_user_by_id(user_id)
    if not user.creatable_projects:
        return False

    result = create_project_with_permission(project_name, user_id)
    return result

def delete_project(user_id, project_uuid):
    """
    指定したユーザの権限を調べ、削除可能ならば指定したプロジェクトを削除する
    返す形式：
        True or False
        （Falseの場合はロールバックしてから返す）
    """
    # 権限の取得
    project_permission = get_permissions_project(user_id, project_uuid)

    if project_permission is None:
        # 指定したユーザと所属しているグループ、プロジェクトの間にはなんの権限もない
        return False

    if not project_permission.deletable_project:
        return False

    result = delete_project_with_permission_by_uuid(project_uuid)
    return result

def fetch_flows(user_id, project_uuid):
    """
    APIで返す権限つきフロー一覧を取得する
    返す形：
        {
            flows:[
                flowモデル,
                flow各々に対する権限（readable, updatable, executable）
            ],
            creatable_flows:（フローを作成できるか）,
            deletable_flows:（フローを削除できるか）
        }
    """
    # プロジェクトidの取得
    project = db.session.query(Projects).filter_by(uuid=project_uuid).first()

    # フローの、作成・削除権限を取得する
    project_permission = get_permissions_project(user_id, project_uuid).__dict__
    flows = get_flows_with_permission(project.id, user_id)
    return {'flow':flows, 'edit_permission':{'creatable_flows':project_permission['creatable_flows'],
                                             'deletable_flows':project_permission['deletable_flows']}}

def create_flow(flow_name, user_id, project, flow_uuid=None):
    """
    指定したユーザが作成できるかを調べ、作成可能ならばフローを作成する
    返す形式：
        True or False
        （Falseの場合はロールバックしてから返す）
    """
    if not project.creatable_flows:
        return False

    return create_flow_with_permission(flow_name, get_user_by_id(user_id), project.id)

def fetch_flow(user_id, flow_uuid):
    """
    指定したユーザがフロー内容を取得可能であれば、フローを取得する
    返す形式：
        {
            flow_uuid:フローのUUID,
            json: {
                フローのjson
                } ,
            project_id: プロジェクトのID,
            creator_id: ユーザのID,
            …
        }
    flow_uuidやproject_idなどはもともとflowのjson内に記述してあったが、外に出してみた。
    外に出しても良さそうなものは他にもlabelとかcreatedAtかな？
    """
    flow_permission = get_permissions_flow(user_id, flow_uuid)
    if flow_permission is None:
        return None

    if not flow_permission.readable_flow:
        return None

    flow_model = fetch_flow_by_uuid(flow_uuid)
    return make_dict_from_model(flow_model)

def delete_flow(user_id, flow_uuid):
    """
    指定したユーザの権限を調べ、削除可能ならば指定したプロジェクトを削除する
    返す形式：
        True or False
        （Falseの場合はロールバックしてから返す）
    """
    # 権限の取得
    # flowのプロジェクトIDを取得
    flow = fetch_flow_by_uuid(flow_uuid)
    project_permission = get_permissions_project(user_id, flow.project_id)

    if project_permission is None:
        # 指定したユーザと所属しているグループ、プロジェクトの間にはなんの権限もない
        return False

    if not project_permission.deletable_project:
        return False

    result = delete_flow_with_permission_by_uuid(flow_uuid)
    return result

def update_flow(user_id, flow_uuid, data):
    """
    指定したユーザのフロー更新権限を調べ、更新可能なら更新する
    返す形式：
        True or False
        （Falseの場合はロールバックしてから返す）
    """
    flow_permission = get_permissions_flow(user_id, flow_uuid)
    if flow_permission is None:
        return False

    if not flow_permission.updatable_flow:
        return False

    result = update_flow_by_uuid(flow_uuid ,data)
    return result

# EndRegion　APIで使うパブリックメソッド

def create_user(name, email, password, creatable_projects=True):
    """
    ユーザを作成する
    プロジェクト作成権限はとりあえずデフォルトでTrueに。
    """
    user = Users(name, email, password, creatable_projects)
    db.session.add(user)
    db.session.commit()

def get_user_by_id(user_id):
    """
    ユーザのIDからユーザ情報を取得する
    """
    user = db.session.query(Users).filter_by(id=user_id).first()
    return user

def create_group(name, creatable_projects=True):
    """
    グループを作成する
    """
    group = Groups(name, creatable_projects)
    db.session.add(group)
    db.session.commit()

def delete_group_by_id(group_id):
    """
    指定したグループを削除する
    """
    group = get_group_by_id(group_id)
    db.session.delete(group)
    db.session.commit()

def get_group_by_id(id):
    """
    グループのIDからユーザ情報を取得する
    """
    group = db.session.query(Groups).filter_by(id=id).first()
    return group

def replace_user_email_with_old_email(new_email, old_email):
    """
    ユーザのemailを更新する
    """
    user = db.session.query(Users).filter_by(email=old_email).first()
    user.email = new_email
    db.session.add(user)
    db.session.commit()

def get_group_from_user_id(user_id):
    """
    指定したユーザが所属しているグループを取得する
    """
    user = get_user_by_id(user_id)
    if user is None:
        return None

    group = get_group_by_id(user.group_id)
    return group

def assign_user_to_group(user_id, group_id):
    """
    指定したユーザを指定したグループに所属させる
    すでに所属していた場合は上書きする（ひとまずの仕様）
    """
    user = get_user_by_id(user_id)
    user.group_id = group_id
    db.session.add(user)
    db.session.commit()

def get_projects_with_permission(user_id):
    """
    プロジェクト一覧を権限付きで返す

    UserPermissions_ProjectとProjectsを結合したもの
    GroupPermissions_ProjectとProjectsを結合したもの
    2つの結果を基に作成している

    ユーザのパーミッションの方が優先なので、
    まずUserPermissions_ProjectとProjectsを結合したものを、返すリストに設定し
    GroupPermissions_Projectにのみ設定されているプロジェクト情報を
    返すリストに追加している
    """
    projects = []
    project_id_list = []

    # ユーザ権限がついたプロジェクトを取得する
    projects_additional_user_permissions = fetch_readable_projects_by_user_id(user_id)
    for project in projects_additional_user_permissions:
        project_id_list.append(project.id)
        projects.append(project._asdict())

    # グループに所属しているか
    group = get_group_from_user_id(user_id)
    if group is None:
        return projects

    # グループ権限がついたプロジェクトを取得する
    projects_additional_group_permissions = fetch_readable_projects_by_group_id(group.id)
    if len(projects_additional_group_permissions) == 0:
        return projects

    # ユーザ×プロジェクトに存在しないプロジェクトを新規に追加する
    for project in projects_additional_group_permissions:
        project_dict = project._asdict()
        if not project_dict.get('id') in project_id_list:
            projects.append(project_dict)
    return projects

def fetch_readable_projects_by_user_id(user_id):
    """
    指定したユーザが閲覧できるプロジェクト一覧を取得する
    型はリスト（行データのリスト）になっている
    行データは_asdict()でdict化できる
    """
    # projects = db.session.query(Projects).filter(Projects.id.in_(db.session.query(UserPermissions_Project.project_id).filter(UserPermissions_Project.user_id==user_id)))
    projects = db.session.query(Projects.id, Projects.name, Projects.uuid, Projects.creator_id,
                                UserPermissions_Project.deletable_project, UserPermissions_Project.readable_flows) \
                                .join(UserPermissions_Project, Projects.id==UserPermissions_Project.project_id) \
                                .filter(UserPermissions_Project.user_id==user_id).all()
    return projects

def fetch_readable_projects_by_group_id(group_id):
    """
    指定したグループが閲覧できるプロジェクト一覧を取得する
    型はリスト（行データのリスト）になっている
    """
    projects = db.session.query(Projects.id, Projects.name, Projects.uuid, Projects.creator_id,
                                GroupPermissions_Project.deletable_project, GroupPermissions_Project.readable_flows) \
                                .join(GroupPermissions_Project, Projects.id==GroupPermissions_Project.project_id) \
                                .filter(GroupPermissions_Project.group_id==group_id).all()
    return projects

def create_project_with_permission(project_name, user_id):
    """
    プロジェクトを作成する
    それと同時にユーザ×プロジェクトも作成する
    また、ユーザがグループに所属していた場合、グループ×プロジェクトも作成する
    """
    # プロジェクト作成
    project = Projects(project_name, str(uuid.uuid4()), user_id)
    db.session.add(project)

    try:
        db.session.commit()
    except:
        # 今は適当、エラー内容も返すかな
        return False

    # ユーザ×プロジェクト作成
    # プロジェクト作成をcommitしてからでないと、idを取得できない（できれば一斉にcommitしたいなぁ）
    userpermission_project = UserPermissions_Project(user_id, project.id)
    db.session.add(userpermission_project)

    # ユーザがグループに所属していた場合、グループ×プロジェクトも作成する
    user = get_user_by_id(user_id)
    if not user.group_id is None:
        grouppermission_project = GroupPermissions_Project(user.group_id, project.id)
        db.session.add(grouppermission_project)

    # コミット
    try:
        db.session.commit()
    except:
        db.session.rollback()
        db.session.delete(project)
        db.session.commit()
        return False

    return True

def get_permissions_project(user_id, project_uuid):
    """
    適切なプロジェクト権限を返す
    ユーザ権限が存在する場合はそちらを優先する
    返す権限が存在しなければ、Noneを返す（とりあえず）
    """
    # プロジェクトを取得
    project = db.session.query(Projects).filter_by(uuid=project_uuid).first()

    # ユーザ×プロジェクトがあればそれを返す
    userpermission_project = get_userpermissions_project(user_id, project.id)
    if not userpermission_project is None:
        return userpermission_project

    # グループに所属しているか調べる
    group = get_group_from_user_id(user_id)
    # 所属していなければ、返す権限が存在しないのでNoneを返す
    if group is None:
        return None

    # ユーザ×プロジェクトがなく、グループ×プロジェクトがあればそれを返す
    grouppermission_project = get_grouppermissions_project(group.id, project.id)
    if not grouppermission_project is None:
        return grouppermission_project

    return None

def get_userpermissions_project(user_id, project_id):
    """
    指定したユーザ×プロジェクト情報を取得する
    """
    userproject = db.session.query(UserPermissions_Project).filter_by(project_id=project_id, user_id=user_id).first()
    return userproject

def get_grouppermissions_project(group_id, project_id):
    """
    指定したグループ×プロジェクトを返す
    """
    groupproject = db.session.query(GroupPermissions_Project).filter_by(project_id=project_id, group_id=group_id).first()
    return groupproject

def delete_project_with_permission_by_uuid(project_uuid):
    """
    指定したプロジェクトを削除する
    ユーザ×プロジェクトも削除する
    グループ×プロジェクトも削除する
    """
    project = db.session.query(Projects).filter_by(uuid=project_uuid).first()
    db.session.query(UserPermissions_Project).filter_by(project_id=project.id).delete()
    db.session.query(GroupPermissions_Project).filter_by(project_id=project.id).delete()
    db.session.delete(project)

    try:
        db.session.commit()
    except:
        db.session.rollback()
        return False

    return True

def fetch_project_by_uuid(poject_uuid):
    """
    指定したUUIDのプロジェクトを取得する
    """
    project = db.session.query(Projects).filter_by(uuid=poject_uuid).first()
    return project

def get_flows_with_permission(project_id, user_id):
    """
    フロー一覧を権限付きで返す
    """
    flows = []
    flow_uuid_list = []

    # ユーザ権限がついたフローを取得する
    flows_additional_user_permissions = fetch_readable_flows_by_project_id_and_user_id(project_id, user_id)
    for flow in flows_additional_user_permissions:
        flow_uuid_list.append(flow.uuid)
        flows.append(flow._asdict())

    # グループに所属しているか
    group = get_group_from_user_id(user_id)
    if group is None:
        return flows

    # グループ権限がついたフローを取得する
    flows_additional_group_permissions = fetch_readable_flows_by_project_id_and_group_id(project_id, group.id)
    if flows_additional_group_permissions is None:
        return flows

    # ユーザ×プロジェクトに存在しないフローを新規に追加する
    for flow in flows_additional_group_permissions:
        flow_dict = flow._asdict()
        if not flow_dict.get('uuid') in flow_uuid_list:
            flows.append(flow_dict)
    return flows

def fetch_readable_flows_by_project_id_and_user_id(project_id, user_id):
    """
    指定したプロジェクトが持ち、指定したユーザが見れるフロー一覧の内容リストをuuidを付け加えて返す
    """
    flows = db.session.query(Flows.uuid, Flows.json, Flows.creator_id, Flows.project_id,
                             UserPermissions_Flow.readable_flow, UserPermissions_Flow.updatable_flow, UserPermissions_Flow.executable_flow) \
                                .join(UserPermissions_Flow, Flows.uuid==UserPermissions_Flow.flow_uuid) \
                                .filter(UserPermissions_Flow.user_id==user_id, Flows.project_id==project_id).all()

    return flows

def fetch_readable_flows_by_project_id_and_group_id(project_id, group_id):
    """
    指定したプロジェクトが持ち、指定したグループが見れるフロー一覧の内容リストをuuidを付け加えて返す
    """
    flows = db.session.query(Flows.uuid, Flows.json, Flows.creator_id, Flows.project_id,
                             UserPermissions_Flow.readable_flow, UserPermissions_Flow.updatable_flow, UserPermissions_Flow.executable_flow) \
                                .join(GroupPermissions_Flow, Flows.uuid==GroupPermissions_Flow.flow_uuid) \
                                .filter(GroupPermissions_Flow.group_id==group_id, Flows.project_id==project_id).all()

    return flows

def create_flow_with_permission(flow_name, user, project_id, flow_uuid=None):
    """
    新規フローを作成し、DBに保存する
    それと同時にユーザ×フローも作成する
    また、ユーザがグループに所属していた場合、グループ×フローも作成する
    返す形式：
        True or False
        （Falseの場合はロールバックしてから返す）
    """
    if flow_uuid is None:
        flow_uuid = str(uuid.uuid4())

    def make_flow_json(flow_name):
        """
        新規フローのJSONを作成する
        """
        data = {
            'label': flow_name,
            'ports': [[],[]],
            'params': [],
            'description': ""
        }
        return json.dumps(data)

    # flowのjsonを作成する
    flow_json = make_flow_json(flow_name)

    # DBのflowデータを作成する
    flow = Flows(flow_uuid, flow_json, project_id, user.id)
    db.session.add(flow)

    # ユーザ×フロー作成
    userpermission_flow = UserPermissions_Flow(user.id, flow_uuid)
    db.session.add(userpermission_flow)

    # グループ×フロー作成
    if not user.group_id is None:
        grouppermission_flow = GroupPermissions_Flow(user.group_id, flow_uuid)
        db.session.add(grouppermission_flow)

    # コミット
    try:
        db.session.commit()
    except:
        db.session.rollback()
        return False

    return True

def fetch_flow_by_uuid(flow_uuid):
    """
    指定したフローのモデルオブジェクトを返す
    """
    flow = db.session.query(Flows).filter_by(uuid=flow_uuid).first()
    return flow

def delete_flow_with_permission_by_uuid(flow_uuid):
    """
    フローを削除する
    ユーザ×フローとグループ×フローも削除する
    """
    flow = fetch_flow_by_uuid(flow_uuid)
    db.session.query(UserPermissions_Flow).filter_by(flow_uuid=flow_uuid).delete()
    db.session.query(GroupPermissions_Flow).filter_by(flow_uuid=flow_uuid).delete()
    db.session.delete(flow)

    try:
        db.session.commit()
    except:
        return False

    return True

def update_flow_by_uuid(flow_uuid, data):
    """
    フローを更新する
    """
    # flow_uuidを元にflowのjsonを取得
    flow = db.session.query(Flows).filter(Flows.uuid==flow_uuid).first()
    # JSON文字列で取得されるので一旦dictに変更してupdate、json文字列に戻して更新している
    json_dict = json.loads(flow.json)
    json_dict.update(data)
    flow.json = json.dumps(json_dict)

    try:
        db.session.commit()
    except:
        db.session.rollback()
        return False

    return True

def get_permissions_flow(user_id, flow_uuid):
    """
    適切なフロー権限を返す
    ユーザ権限が存在する場合はそちらを優先する
    返す権限が存在しなければ、Noneを返す（とりあえず）
    """
    # ユーザ×プロジェクトがあればそれを返す
    userpermission_flow = get_userpermissions_flow(user_id, flow_uuid)
    if not userpermission_flow is None:
        return userpermission_flow

    # グループに所属しているか調べる
    group = get_group_from_user_id(user_id)
    # 所属していなければ、返す権限が存在しないのでNoneを返す
    if group is None:
        return None

    # ユーザ×プロジェクトがなく、グループ×プロジェクトがあればそれを返す
    grouppermission_flow = get_grouppermissions_flow(group.id, flow_uuid)
    if not grouppermission_flow is None:
        return grouppermission_flow

    return None

def get_userpermissions_flow(user_id, flow_uuid):
    """
    指定したユーザ×フロー情報を取得する
    """
    userproject = db.session.query(UserPermissions_Flow).filter_by(user_id=user_id, flow_uuid=flow_uuid).first()
    return userproject

def get_grouppermissions_flow(group_id, flow_uuid):
    """
    指定したグループ×フローを取得する
    """
    groupproject = db.session.query(GroupPermissions_Flow).filter_by(group_id=group_id, flow_uuid=flow_uuid).first()
    return groupproject

def grant_user_to_project(user_id, project_id, deletable_project=True, creatable_flows=True,
                               deletable_flows=True, updatable_flows=True, executable_flows=True, readable_flows=True):
    """
    指定したユーザとプロジェクトに対する権限を新規作成する
    """
    userpermission_project = UserPermissions_Project(user_id, project_id,
                                                    deletable_project,
                                                    creatable_flows, deletable_flows, readable_flows)
    db.session.add(userpermission_project)
    db.session.commit()

def grant_group_to_project(group_id, project_id, deletable_project=False, creatable_flows=False,
                                deletable_flows=False, readable_flows=True):
    """
    指定したグループとプロジェクトに対する権限を新規作成する
    """
    grouppermission_project = GroupPermissions_Project(group_id, project_id,
                                                      deletable_project,
                                                      creatable_flows, deletable_flows, readable_flows)
    db.session.add(grouppermission_project)
    db.session.commit()

def make_dict_from_model(model):
    """
    指定したsqlalchemyのmodelオブジェクトをdictに変換する
    """
    return { column.name : getattr(model, column.name) for column in model.__table__.columns }
