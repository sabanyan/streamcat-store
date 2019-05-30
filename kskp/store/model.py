import json
import uuid
import sqlite3
import functools
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import g
from threading import Lock

from kskp.web import app
from kskp.library import (
    FRAME_FOLDER_UUID,
    FRAME_FOLDER_LABEL,
    CACHE_FOLDER_UUID,
    CACHE_FOLDER_LABEL
)

lock = Lock()

# app.config['DATABASE'] = app.root_path + '/data/kskp.db'
app.config['DATABASE'] = 'kskp/data/kskp.db'
# app.config.from_pyfile(app.root_path + '/settings.cfg')
app.config['FLOW_PATH'] = 'kskp/data/flows'

def create_user(email, password, name, creator):
    """
    新しいユーザを登録する
    パスワードはハッシュ化する
    """
    from kskp.web.api import auth
    sql = '''
    INSERT INTO users (email, password, name, creator) VALUES (?, ?, ?, ?)
    '''
    hashed_password = auth.get_password_hash(email, password)
    query_db(sql, (email, hashed_password, name, creator))

def get_user_id_by_email(email):
    """
    指定したemailのユーザレコードを返す
    """
    sql = '''
    SELECT id, name FROM users WHERE email = ?
    '''
    return query_db(sql, (email,), one=True)
#
def get_user_by_id(user_id):
    """
    指定したユーザIDのユーザレコードを返す
    """
    sql = '''
    SELECT * FROM users WHERE id = ?
    '''
    return query_db(sql, (user_id,), one=True)
#
# def get_all_users():
#     """
#     ユーザ一覧を取得する
#     """
#     pass
#
# def delete_user(email):
#     """
#     ユーザを削除する
#     """
#     sql = 'DELETE FROM users WHERE email = ?'
#     query_db(sql, (email,))
#
# def update_user_by_id(user_id, profile):
#     """
#     ユーザ情報を更新する
#     """
#     update_sql = []
#     update_list = []
#     for key, value in profile.items():
#         if key == 'current_password':
#             continue
#
#         if key == 'new_password':
#             email = None
#             if profile.get('email') is not None:
#                 email = profile.get('email')
#             else:
#                 email = model.get_user_by_id(user_id)['password']
#
#             update_sql.append('password= ?')
#             update_list.append(auth.get_password_hash(email, value))
#         else:
#             update_sql.append(key + '= ?')
#             update_list.append(value)
#
#     sql = '''
#     UPDATE users SET %s WHERE id = ?
#     ''' % ','.join(map(str, update_sql))
#     query_db(sql, tuple(update_list) + (user_id,))
#
# def get_current_user(session):
#     """
#     セッションからidを取得して、
#     ログイン状態のユーザ情報を返す
#     """
#     user_id = session['user_id']
#     user_record = get_user_by_id(user_id)
#     return User(user_id, user_record['email']) # 0にはユーザ名が入っている
#
#
# def create_project(name, session):
#     """
#     新しいプロジェクトを作成する
#     """
#
#     sql = '''
#     INSERT INTO projects (uuid, name, creator_id, creator) VALUES (?, ?, ?, ?)
#     '''
#     generated_uuid = str(uuid.uuid4())
#     user = get_current_user(session)
#     return query_db(sql, (generated_uuid, name, user.id, user.email))
#
#
# def add_info_for_users_x_projects(user_id, project_id):
#     """
#     ユーザと閲覧可能なプロジェクトの関係を表すレコードを追加する
#     """
#     sql = '''
#     INSERT INTO users_x_projects (user_id, project_id) VALUES (?, ?)
#     '''
#     query_db(sql, (user_id, project_id))
#
#
# def start_project(name, session):
#     """
#     単にprojectsにINSERTするだけではなく、画面上の一つの操作に対応して複数のSQLを実行する
#     この処理全体を一つのトランザクションとみなすため、
#     既存のcreate_project/add_info_for_users_x_projectsは使えない。
#
#     TODO:
#     できればトランザクションを制御する仕組み(with系)を作って
#     この部分をcreate_project/add_info_for_users_x_projectsを使う形にリファクタしたい
#     """
#
#     # 全体の準備
#     conn = get_connection()
#     cur = conn.cursor()
#
#     # projectsに行を挿入する
#     sql_projects = '''
#     INSERT INTO projects (uuid, name, creator_id, creator) VALUES (?, ?, ?, ?)
#     '''
#     generated_uuid = str(uuid.uuid4())
#     user = get_current_user(session)
#
#     cur.execute(sql_projects, (generated_uuid, name, user.id, user.email))
#
#     # 次にユーザ別の閲覧可能なプロジェクトを表すテーブルに行を挿入する
#     # ひとまず、自分が作ったプロジェクトは自分だけが見られるような仕様にしておく
#     sql_users_x_projects = '''
#     INSERT INTO users_x_projects VALUES (?, ?)
#     '''
#     cur.execute(sql_users_x_projects, (user.id, cur.lastrowid))
#
#     # 後片付け
#     conn.commit()
#     cur.close()
#
#
# def get_all_projects():
#     """
#     すべてのプロジェクトを取得する
#     """
#     sql = '''
#     SELECT id, uuid, name, creator_id FROM projects
#     '''
#     return query_db(sql)
#
def get_projects_by_user_id(user_id, search_string=None):
    """
    特定のユーザが閲覧可能なプロジェクト一覧を取得する
    """

    sql = '''
    SELECT p.uuid, p.name, p.creator_id, y.name as creator_name, p.created_at FROM projects p
     INNER JOIN users_x_projects x
        ON x.project_id = p.id
     INNER JOIN users y
        ON p.creator_id = y.id
     WHERE x.user_id = ?
     ORDER BY p.id
    '''

    args = (user_id,)
    if search_string is not None:
        sql += ' WHERE p.name LIKE ?'
        args = (user_id, '%' + search_string + '%')

    return query_db(sql, args)

# def delete_project_by_uuid(project_uuid):
#     """
#     プロジェクトを削除する(uuidが基準)
#     """
#     sql = 'DELETE FROM projects WHERE uuid = ?'
#     query_db(sql, (project_uuid,))
#
# def rename_project_by_uuid(project_uuid, new_name):
#     """
#     プロジェクトの名前を変更する
#     """
#     sql = 'UPDATE projects SET name = ? WHERE uuid = ?'
#     query_db(sql, (new_name, project_uuid))
#
# def fecth_project(project_id):
#     """
#     プロジェクトを取得する（project_idが基準）
#     """
#     sql = 'SELECT uuid, name FROM projects WHERE id = ?'
#     return query_db(sql, (project_id,), one=True)
#
#
# def create_flow(request_json, user_id, data_source_name=None):
#     """
#     フローを作成する
#     TODO: 詳細は変更予定
#     """
#     if data_source_name is None:
#         data_source_name = str(uuid.uuid4())
#
#     def add_data_source_to_flow(source):
#         '''
#         フローに作成時にデータソースをつけるためのデコレータ
#         '''
#         def _deco(func):
#             @functools.wraps(func)
#             def deco():
#                 if source is None:
#                     return func()
#
#                 if not source.get('uuid'):
#                     return func()
#
#                 data = func()
#                 data_source = {
#                     "id": "i",
#                     "type": source.get('type'),
#                     "dataSource": "csv",
#                     "uuid": source.get('uuid'),
#                     "label": source.get('label')
#                 }
#
#                 data['nodes'] = []
#                 data['nodes'].append(data_source)
#                 return data
#             return deco
#         return _deco
#
#     def add_activity_to_flow(user_id):
#         '''
#         フローに作成時に作成履歴をつけるためのデコレータ
#         '''
#         def _deco(func):
#             @functools.wraps(func)
#             def deco():
#                 data = func()
#                 now = datetime.now()
#
#                 data['creator'] = get_user_by_id(user_id)['name']
#                 JST = timezone(timedelta(hours=+9), 'JST')
#                 data['createdAt'] = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')
#                 return data
#             return deco
#         return _deco
#
#     @add_data_source_to_flow(request_json.get('datasource'))
#     @add_activity_to_flow(user_id)
#     def make_flow_json():
#         data = {
#             'projectId': get_project_id_by_uuid(request_json.get('project_uuid')),
#             'label': request_json.get('name'),
#             'ports': [[],[]],
#             'params': [],
#             'description': ""
#         }
#         return data
#
#     data = make_flow_json()
#
#     write_data_to_json(make_flow_path(data_source_name), data)
#
#     return data
#
#
def fetch_flow_by_uuid(flow_uuid):
    """
    指定したフローの内容を返す
    """
    path = get_flow_path_by_uuid(flow_uuid)
    return json.loads(path.read_text())
#
# def copy_flow_by_uuid(original_flow_uuid, user_id, data_source_name=None):
#     """
#     指定したフローのuuidを元に
#     コピーしたフローを作成し、その内容を返す
#     """
#     new_flow_uuid = str(uuid.uuid4()) if data_source_name is None else data_source_name
#     new_flow_path = Path(app.config['FLOW_PATH']) / (new_flow_uuid + '.json')
#     original_flow_path = get_flow_path_by_uuid(original_flow_uuid)
#
#     # 中身の読み込み
#     with open(original_flow_path) as original_f:
#         flow_json = json.load(original_f)
#
#     # 中身の書き換え
#     with open(new_flow_path, 'w') as new_f:
#         flow_json['label'] = generate_flow_name(flow_json.get('projectId'), flow_json.get('label'))
#         flow_json['creator'] = get_user_by_id(user_id)['name']
#         JST = timezone(timedelta(hours=+9), 'JST')
#         flow_json['createdAt'] = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')
#         json.dump(flow_json, new_f, indent=2, ensure_ascii=False)
#
#     return flow_json
#
# def generate_flow_name(project_id, flow_name, serial_number=1):
#     """
#     コピーしたフローの名前（label）を生成する
#     コピーフローの名前ルール
#     ・基本的にはコピー元のフローの名前の後ろに「のコピー」をつける
#     ・「のコピー」をつけた名前がそのプロジェクト内で重複していた場合、後ろに連番（２〜）をつける
#     """
#     multi_flag = False
#     new_flow_name = ''
#
#     if serial_number == 1:
#         # 引数で「のコピー」付きのflow_nameを渡してもいいかなと思ったけど、
#         # それも含めてここでやったほうが纏まってていいかなと思ったので、ここで行なっている
#
#         # 引数で、後ろに付ける文字列（ここでは「のコピー」）を渡せるようにした方が柔軟性は上がるが、
#         # 今はいいや、その時が来たらそうする。
#         flow_name = flow_name + ' のコピー'
#         new_flow_name = flow_name
#     elif serial_number > 1:
#         new_flow_name = flow_name + str(serial_number)
#
#     for path in Path(app.config['FLOW_PATH']).iterdir():
#         try:
#             if not path.suffix == '.json':
#                 continue
#             data = json.loads(path.read_text())
#         except json.JSONDecodeError as e:
#             # JSONのフォーマットに則していないファイルは無視
#             continue
#
#         # プロジェクトが存在するかのチェック
#         project = fecth_project(project_id)
#         if project is None:
#             continue
#
#         # プロジェクトが同じかどうかのチェック
#         # 別プロジェクトのフローとは名前が重複してもいいので。
#         if data['projectId'] != project_id:
#             continue
#
#         if data['label'] == new_flow_name:
#             multi_flag = True
#             break
#
#     if multi_flag:
#         return generate_flow_name(project_id, flow_name, serial_number + 1)
#     else:
#         return new_flow_name
#
# def fetch_subflows_all_projects(request_args):
#     """
#     指定したプロジェクトの持つサブフロー一覧の内容リストをuuidを付け加えて返す
#     """
#     subflow_list = []
#     for path in Path(app.config['FLOW_PATH']).iterdir():
#         try:
#             if not path.suffix == '.json':
#                 continue
#             data = json.loads(path.read_text())
#         except json.JSONDecodeError as e:
#             # JSONのフォーマットに則していない場合
#             continue
#
#         project = fecth_project(data['projectId'])
#         if project is None:
#             continue
#
#         data['uuid'] = path.stem
#         data['projectName'] = project['name']
#         # onの時にno_inputs（＝inputsがない）のサブフローは出さない
#         if request_args.get('no_inputs') == 'on':
#             if len(data['ports'][0]) == 0:
#                 continue
#
#         # onの時にno_outputs（＝outputsがない）のサブフローは出さない
#         if request_args.get('no_outputs') == 'on':
#             if len(data['ports'][1]) == 0:
#                 continue
#
#         if len(data['ports'][0]) > 0 or len(data['ports'][1]) > 0:
#             subflow_list.append(data)
#
#     return subflow_list
#
def fetch_flows_by_project_uuid(project_uuid):
    """
    指定したプロジェクトの持つフロー一覧の内容リストをuuidを付け加えて返す
    """
    paths = get_flow_paths_by_project_uuid(project_uuid)

    flow_list = []
    for path in paths:
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            # JSONのフォーマットに則していない場合
            continue

        data['uuid'] = path.stem
        flow_list.append(data)
    return flow_list

#
# def delete_flow_by_uuid(flow_uuid):
#     """
#     フローを削除する
#     """
#     get_flow_path_by_uuid(flow_uuid).unlink()
#
#
# def update_flow_by_uuid(flow_uuid, data):
#     """
#     指定したフローの内容を渡されたdataの内容と結合する
#     同じキーが含まれる場合は新しいもので上書きされる
#     """
#     path = get_flow_path_by_uuid(flow_uuid)
#     current = json.loads(path.read_text())
#     current.update(data)
#
#     write_data_to_json(path, current)
#
#     return current
#
#
def get_flow_path_by_uuid(flow_uuid):
    """
    指定したUUIDをファイル名にもつフローファイルのパスを返すヘルパー
    """
    for flow_path in Path(app.config['FLOW_PATH']).iterdir():
        if not flow_path.suffix == '.json':
            continue
        if flow_path.stem == flow_uuid:
            return flow_path
#
def get_flow_paths_by_project_uuid(project_uuid):
    """
    指定したプロジェクトのUUIDを持つフローファイルのパス群を返すヘルパー
    """
    flow_path_list = []
    project_id = get_project_id_by_uuid(project_uuid)

    def validate_flow_json(data):
        """
        flowのjsonが正しい形式かを確かめるメソッド
        """
        required_key_list = ['label', 'creator', 'createdAt', 'projectId', 'description']
        additional_key_list = ['params', 'ports', 'nodes']

        # flowチェック（flow一覧表示時）
        # 1. flowがprojectに所属しているか（projectIdがついているか）
        # 2. flowのプロジェクトが指定したプロジェクトと同じかどうか
        if data.get('projectId') == project_id:
            # 3. flowのキーチェック
            # 中身のチェックについて、2つのチェックが必要だと考えている。
            # 最低限必要なものが存在しているか、必要でないものが存在していないかの2つである

            # 最低限必要なものはフロー作成時に生成されるキーのことだと考えて問題なさそう。
            # 必要でないものは、上記のフロー作成時に生成されるものに
            # 3つのキー（params, ports, nodes)を加えたもの以外のキー

            # ひとまず中身のチェックとしてはその2つについて考慮すればいいとする

            def contain_require_keys(json_data, requires_key_list):
                """
                最低限必要なものが存在しているかのチェック
                """
                def has_arribute(data, attribute):
                    return attribute in data and data[attribute] is not None

                for json_key in required_key_list:
                    if not has_arribute(json_data, json_key):
                        return False
                return True

            def has_disallow_key_in_json(json_data, list):
                """
                必要でないものが存在していないかのチェック
                """
                for data_key in json_data.keys():
                    if not data_key in list:
                        return True
                return False

            # 2つのメソッドの形が似ているので、もう少し綺麗になりそうかもと思いながら
            # 思い浮かんでいないので、綺麗にできる方いたらして下さいm(_ _)m
            if contain_require_keys(data, required_key_list):
                if not has_disallow_key_in_json(data, required_key_list + additional_key_list):
                    return True
            return False

    for flow_path in Path(app.config['FLOW_PATH']).iterdir():
        try:
            if not flow_path.suffix == '.json':
                continue
            data = json.loads(flow_path.read_text(encoding='utf-8'))
        except json.JSONDecodeError as e:
            # JSONのフォーマットに則していない場合は飛ばす
            continue

        if validate_flow_json(data):
            flow_path_list.append(flow_path)

    return flow_path_list
#
#
# def make_flow_path(file_name):
#     """
#     フローファイルのパス作成用ヘルパー
#     """
#     return Path(app.config['FLOW_PATH']) / Path('%s.json' % file_name)
#
# def get_frame_dir_path(user_id):
#     # フレーム格納フォルダを取得する
#     return _get_or_make_dir_path(FRAME_FOLDER_UUID, FRAME_FOLDER_LABEL, user_id)
#
# def get_cache_dir_path(user_id):
#     # キャッシュ格納フォルダを取得する
#     return _get_or_make_dir_path(CACHE_FOLDER_UUID, CACHE_FOLDER_LABEL, user_id)
#
# def _get_or_make_dir_path(uuid, label, user_id):
#     from .library import Folder
#     from .lib import get_library
#     # 特定用途のフォルダのUUIDは決め打ちである
#     if Folder.exists(uuid):
#         folder = Folder.find_by_uuid(uuid)
#     else:
#         # フォルダが無い場合は作成する
#         root = get_library(user_id)
#         folder = Folder(root.uuid,
#                         label,
#                         user_id,
#                         user_id)
#         # Folderのコンストラクタで付番したUUIDを捨てて、特定用途のフォルダのUUIDを格納する
#         folder.uuid = uuid
#         folder.save()
#     return folder
#
# def get_all_frame_uuid_in_frame(flow_uuid):
#     """
#     指定するフローのJSONファイルにおいて、フレームノードで参照するフレームUUIDを全て取得する
#     """
#     return [node['uuid'] for id, node in get_flow_nodes_by_uuid(flow_uuid).items() if node['type'] == 'frame']
#
def get_project_id_by_uuid(project_uuid):
    """
    指定したUUIDを持つプロジェクトを返す
    該当プロジェクトが存在しない場合はNoneを返す
    """
    sql = 'SELECT id FROM projects WHERE uuid = ?'

    result = query_db(sql, (project_uuid,), one=True)

    return result['id'] if result is not None else None
#
# def get_project_name_by_uuid(project_uuid):
#     """
#     指定したUUIDを持つプロジェクト名を返す
#     該当プロジェクトが存在しない場合はNoneを返す
#     get_project_id_by_uuidと纏められるが、後で。
#     """
#     sql = 'SELECT name FROM projects WHERE uuid = ?'
#
#     result = query_db(sql, (project_uuid,), one=True)
#
#     return result['name'] if result is not None else None
#
# def write_data_to_json(path, data):
#     """
#     データをJSONとしてファイルに書き込むヘルパー
#     """
#     lock.acquire()
#     try:
#         path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
#     finally:
#         lock.release() #release lock
#
def get_flow_nodes_by_uuid(flow_uuid):
    """
    flowのjsonを受け取り、idをkey、valueをnodeとした連想配列を返す
    """
    data = fetch_flow_by_uuid(flow_uuid)
    if data.get('nodes') is None:
        return {}
    return {node['id']:node for node in data['nodes']}
#
def query_db(query, args=(), one=False):
    """
    指定されたSQLを実行して、その結果を返却する
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.execute(query, args)
    conn.commit()
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv
#
#
def get_connection():
    """
    現在のappcontext内のコネクションを取得する
    存在しなければDBを開いてから取得する
    """
    conn = getattr(g, '_database', None)
    if conn is None:
        is_first_use = not Path(app.config['DATABASE']).exists()

        conn = g._database = sqlite3.connect(app.config['DATABASE'])

        if is_first_use:
            init_db()

    return conn
#
def init_db():
    conn = get_connection()
    sql_path = Path(__file__).resolve().parent / 'sql/schema.sql'
    with app.open_resource(sql_path.as_posix(), mode='r') as f:
        conn.cursor().executescript(f.read())
    conn.commit()
#
#
# @app.teardown_appcontext
# def close_connection(exception):
#     """
#     appcontext終了時にコネクションを閉じる
#     """
#     conn = getattr(g, '_database', None)
#     if conn is not None:
#         conn.close()
#
# class User:
#     def __init__(self, id, email):
#         self.id = id
#         self.email = email
