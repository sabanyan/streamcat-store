# kskpからそのまま持ってきて、
# kskp-webのapi部分の処理で使わなかったものはコメントアウトされている
import os
import json
import uuid
import sqlite3
import functools
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import g
from threading import Lock

# lock = Lock()

def create_user(email, password, name, creator):
    """
    新しいユーザを登録する
    パスワードはハッシュ化する
    """
    from kskp.web.backend.api import auth
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

#     TODO:
#     できればトランザクションを制御する仕組み(with系)を作って
#     この部分をcreate_project/add_info_for_users_x_projectsを使う形にリファクタしたい
#     """

#     # 全体の準備
#     conn = get_connection()
#     cur = conn.cursor()

#     # projectsに行を挿入する
#     sql_projects = '''
#     INSERT INTO projects (uuid, name, creator_id, creator) VALUES (?, ?, ?, ?)
#     '''
#     generated_uuid = str(uuid.uuid4())
#     user = get_current_user(session)

#     cur.execute(sql_projects, (generated_uuid, name, user.id, user.email))

#     # 次にユーザ別の閲覧可能なプロジェクトを表すテーブルに行を挿入する
#     # ひとまず、自分が作ったプロジェクトは自分だけが見られるような仕様にしておく
#     sql_users_x_projects = '''
#     INSERT INTO users_x_projects VALUES (?, ?)
#     '''
#     cur.execute(sql_users_x_projects, (user.id, cur.lastrowid))

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
# def get_projects_by_user_id(user_id, search_string=None):
#     """
#     特定のユーザが閲覧可能なプロジェクト一覧を取得する
#     """

#     sql = '''
#     SELECT p.uuid, p.name, p.creator_id, y.name as creator_name, p.created_at FROM projects p
#      INNER JOIN users_x_projects x
#         ON x.project_id = p.id
#      INNER JOIN users y
#         ON p.creator_id = y.id
#      WHERE x.user_id = ?
#      ORDER BY p.id
#     '''

#     args = (user_id,)
#     if search_string is not None:
#         sql += ' WHERE p.name LIKE ?'
#         args = (user_id, '%' + search_string + '%')

#     return query_db(sql, args)

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
def create_flow(request_json, user_id, data_source_name=None):
    """
    フローを作成する
    TODO: 詳細は変更予定
    """
    if data_source_name is None:
        data_source_name = str(uuid.uuid4())

    def add_data_source_to_flow(source):
        '''
        フローに作成時にデータソースをつけるためのデコレータ
        '''
        def _deco(func):
            @functools.wraps(func)
            def deco():
                if source is None:
                    return func()

                if not source.get('uuid'):
                    return func()

                data = func()
                data_source = {
                    "id": "i",
                    "type": source.get('type'),
                    "dataSource": "csv",
                    "uuid": source.get('uuid'),
                    "label": source.get('label')
                }

                data['nodes'] = []
                data['nodes'].append(data_source)
                return data
            return deco
        return _deco

    def add_activity_to_flow(user_id):
        '''
        フローに作成時に作成履歴をつけるためのデコレータ
        '''
        def _deco(func):
            @functools.wraps(func)
            def deco():
                data = func()
                data['creator'] = get_user_by_id(user_id)['name']
                JST = timezone(timedelta(hours=+9), 'JST')
                data['createdAt'] = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')
                return data
            return deco
        return _deco

    @add_data_source_to_flow(request_json.get('datasource'))
    @add_activity_to_flow(user_id)
    def make_flow_json():
        data = {
            # 'projectId': get_project_by_uuid(request_json.get('project_uuid')),
            'projectId': None,
            'label': request_json.get('name'),
            'ports': [[],[]],
            'params': [],
            'description': ""
        }
        return data

    data = make_flow_json()

    return data
#
#
# def fetch_flow_by_uuid(flow_uuid):
#     """
#     指定したフローの内容を返す
#     """
#     # from kskp.store import FlowLink
#     # return FlowLink(flow_uuid).resolve()
#     from kskp.store import Flow
#     return Flow.find_by_uuid(flow_uuid).flow_data

#
# def get_frame_dir_path(user_id):
#     # フレーム格納フォルダを取得する
#     return _get_or_make_dir_path(FRAME_FOLDER_UUID, FRAME_FOLDER_LABEL, user_id)
#
# def get_cache_dir_path(user_id):
#     # キャッシュ格納フォルダを取得する
#     return _get_or_make_dir_path(CACHE_FOLDER_UUID, CACHE_FOLDER_LABEL, user_id)
#

# def get_flow_dir_path(user_id):
#     # フロー格納フォルダを取得する
#     from kskp.store import FLOW_FOLDER_UUID, FLOW_FOLDER_LABEL
#     return _get_or_make_dir_path(FLOW_FOLDER_UUID, FLOW_FOLDER_LABEL, user_id)

# def _get_or_make_dir_path(uuid, label, user_id):
#     from kskp.store import Folder
#     from kskp.store import Library
#     # 特定用途のフォルダのUUIDは決め打ちである
#     if Folder.exists(uuid):
#         folder = Folder.find_by_uuid(uuid)
#     else:
#         # フォルダが無い場合は作成する
#         root = Library.load_root(user_id)
#         folder = Folder(root.uuid,
#                         label,
#                         user_id)
#         # Folderのコンストラクタで付番したUUIDを捨てて、特定用途のフォルダのUUIDを格納する
#         folder.uuid = uuid
#         folder.save()
#     return folder

# def get_all_frame_uuid_in_frame(flow_uuid):
#     """
#     指定するフローのJSONファイルにおいて、フレームノードで参照するフレームUUIDを全て取得する
#     """
#     return [node['uuid'] for id, node in get_flow_nodes_by_uuid(flow_uuid).items() if node['type'] == 'frame']
#

# def get_project_by_uuid(project_uuid):
#     """
#     指定したUUIDを持つプロジェクトを返す
#     該当プロジェクトが存在しない場合はNoneを返す
#     """
#     sql = 'SELECT * FROM projects WHERE uuid = ?'

#     result = query_db(sql, (project_uuid,), one=True)

#     return result if result is not None else None
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
# def get_flow_nodes_by_uuid(flow_uuid):
#     """
#     flowのjsonを受け取り、idをkey、valueをnodeとした連想配列を返す
#     """
#     data = fetch_flow_by_uuid(flow_uuid)
#     if data.get('nodes') is None:
#         return {}
#     return {node['id']:node for node in data['nodes']}
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
        is_first_use = not Path(os.environ['SQLITE_PATH']).exists()

        conn = g._database = sqlite3.connect(os.environ['SQLITE_PATH'])

        if is_first_use:
            init_db()

    return conn
#
def init_db():
    conn = get_connection()
    sql_path = Path(__file__).resolve().parent / 'sql/schema.sql'
    with open(sql_path.as_posix(), mode='r') as f:
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
