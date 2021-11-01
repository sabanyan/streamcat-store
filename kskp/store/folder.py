from kskp.core import Datum, Command, Constraints
from .store import Store

class Folder(Store):

    __mapper_args__ = {
        'polymorphic_identity' : 'folder'
    }

    def __init__(self, session, parent, label):
        """
        コンストラクタ
        """
        super().__init__(session, parent, Datum.FOLDER_TYPE, label)

        # DBに保存する前のFolderへの参照と更新と実行権限は制限しない
        self._permissions = Datum.PERMISSION_READ | Datum.PERMISSION_WRITE | Datum.PERMISSION_EXEC

    @Constraints.prohibit_save_on_root
    @Constraints.set_project_role_on_adding
    def save(self, file_path=None):
        """
        Folderを保存する
        """
        # 既にルートフォルダが存在する場合は、parent_id=NULLを許可しない
        from kskp.store.factory import DatumFactory
        if self.parent_id is None and DatumFactory(self._session).count_root() > 0:
            raise Exception('You can not add root folder. A root already exists.')

        if file_path is None:
            # 既存のファイルと重複しないファイル名を取得する
            self._path = Datum.make_unique_path(self._path)
        else:
            self._path = file_path

        # # 新規追加前にファイルパスを退避する
        # self_path = self.path

        try:
            # Dataテーブルにレコードを新規追加する
            self._session.add(self)
            # ドキュメントに紐付くファイル(path列で指定されるファイル)がなければ作成する
            if file_path is None:
                self._make_dir(self._path)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

    def update_data(self, label, modifier=None):
        """
        Folderのlabel列を更新する
        """
        # ラベルに'\0'が含まれていれば取り除く
        new_label = Datum.escape_label(label)

        # ラベル名からファイルパスを作成する    
        old_path = self._path
        new_path = old_path.parent / Datum.escape_filename(new_label)
        new_path = Datum.make_unique_path(new_path, except_path=old_path)

        try:
            # ディレクトリ名の移動によって他のDatumのpathが変更が必要であれば変更する
            self._update_same_path(old_path, new_path, modifier)
            self._update_include_path(old_path, new_path, modifier)
            # レコードを更新する
            self._label = new_label
            self._modifier_id = (modifier or self._session.user).id
            self._session.update(self)
            # ファイルを移動する
            Datum.move_file(old_path, new_path)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

        return self

    @Constraints.set_role_to_trashed_folder
    def throw_away(self):
        """
        Folderを中身のファイルも一緒にゴミ箱にほかす
        """
        from kskp.store.factory import DatumFactory
        factory = DatumFactory(self._session)
        trash_folder = factory.load_trash_folder()

        if self.parent_id is None:
            raise Exception('ルートフォルダは削除できません')

        # if self.get_flow_uuids_using_me():
        #     raise Exception('別のフローで使用しているため削除できませんでした')

        thrown_count, obstacle_count, trashed_folder = self._throw_away_inner(trash_folder, self)

        if obstacle_count == 0 and not self.is_system_folder():
            # 中のファイル全て削除可能であればフォルダ(ファイル)ごとゴミ箱へ移動する
            self.move(trash_folder.uuid)
            thrown_count += 1

        if thrown_count == 0:
            raise Exception('削除できませんでした')

        return trashed_folder

    def _throw_away_inner(self, parent, datum):
        from kskp.store.lock import lock_manager

        if isinstance(datum, Folder):
            # フォルダ直下のフォルダとデータベースとドキュメントを取得する
            children = datum.find_children()

            # ゴミ箱に捨てても削除前の階層構造を維持するため、削除対象フォルダの形代をゴミ箱に作成する
            trashed_folder = parent.create_folder(datum.label)
            trashed_folder.save()
            trashed_folder = trashed_folder.reload()

            throwables = []
            thrown_count = 0
            obstacle_count = 0

            for child in children:
                child_thrown_count, child_obstacle_count, child_trashed_folder = self._throw_away_inner(trashed_folder, child)
                # 削除可能リストの作成
                if child_obstacle_count == 0:
                    throwables.append(child)
                # 削除ファイルと削除不可ファイルを集計する
                thrown_count += child_thrown_count
                obstacle_count += child_obstacle_count

            # 形代フォルダの削除済みフラグ
            trashed_folder_is_deleted = False

            if obstacle_count == 0 and not datum.is_system_folder():
                # 全部捨る場合はフォルダごとゴミ箱へ移動する
                trashed_folder.delete()
                trashed_folder_is_deleted = True

            else:
                # 一部捨てる場合はそれらを形代フォルダへ移動する
                for throwable in throwables:
                    throwable.move(trashed_folder.uuid)
                    thrown_count += 1
                # 捨るものがなかった場合は形代フォルダを作らない
                if thrown_count == 0:
                    trashed_folder.delete()
                    trashed_folder_is_deleted = True

            # 形代フォルダを作る場合は返り値として返す、作らない場合はNoneを返す
            return thrown_count, obstacle_count, None if trashed_folder_is_deleted else trashed_folder

        elif datum.type == Datum.FRAME_TYPE or datum.type == Datum.FLOW_TYPE:
            import warnings
            # 削除しようとするフレーム/サブフローの更新権限がない場合は削除できない
            if not self._session.writable(datum):
                warnings.warn(f'{datum} is not thrown, not writable')
                return 0, 1, None
            # 削除しようとするサブフローが排他ロック中の場合は削除できない
            if lock_manager.containts_target(datum.uuid):
                warnings.warn(f'{datum} is not thrown, exclusive locked')
                return 0, 1, None
            # 削除しようとするフレーム/サブフローが、削除対象のフォルダ外のフローで使用されてる場合は削除できない
            using_flow_uuids = self.get_flow_uuids_using_me()
            for using_flow_uuid in using_flow_uuids:
                if datum.uuid == using_flow_uuid['referenced_uuid']:
                    warnings.warn(f'{datum} is not thrown, referenced by other flows')
                    return 0, 1, None
            # 削除可能!
            return 0, 0, None

        else:
            # データベース接続、リモートフォルダ接続
            return 0, 0, None

    @Constraints.delete_role_when_isolated
    def delete(self):
        """
        Folderを削除する
        """
        # 削除対象のフォルダの下にフォルダまたはファイルが存在する場合は例外を送出する
        if self.count_children() > 0:
            raise Exception(f'空でないフォルダは削除できません')
        try:
            # フォルダレコードを削除する
            self._session.delete(self)
            # ディレクトリを削除する
            self._remove_dir(self._path)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

    def remove_reference_only(self):
        """
        _remove_reference_only_recursivelyのエイリアスです
        """
        self._remove_reference_only_recursively()

    def _remove_reference_only_recursively(self):
        """
        エントリを削除するが、対応するファイルは削除しない
        この処理は自身と自身のエントリ以下の全てのエントリが対象である
        """
        from sqlalchemy import text

        sql=text(f"""
        WITH RECURSIVE R AS (
            SELECT id FROM data WHERE id = {id}
            UNION ALL
            SELECT data.id FROM data JOIN R ON data.parent_id = R.id
        )
        DELETE FROM data D
        WHERE EXISTS (SELECT * FROM R
                      WHERE R.id = D.id);
        """)

        try:
            # フォルダレコードを削除する
            self._session.delete(self)
            self._session.execute(sql)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

    def get_folder_path(self):
        """
        現在のフォルダ階層パスをリスト型で返す(APIのFolderPath属性の作成で用いる)
        """
        from kskp.store.auth import NotAuthorizedException

        datum = self
        path_to_root = [{'type':datum.type, 'uuid':datum.uuid, 'label':datum.label}]
        parent_id = datum.parent_id
        # 自分からルートフォルダまでのfolderレコードをリストに順に保存する
        while parent_id != None:
            try:
                datum = datum.find_parent()
            except NotAuthorizedException:
                # 参照権限がないため親Datumが取得できない場合、空リストを返す
                return []
            path_to_root.append({'type':datum.type, 'uuid':datum.uuid, 'label':datum.label})
            parent_id = datum.parent_id
        # 保存したリストの並びを逆にする
        path_to_root.reverse()
        return path_to_root

    def to_json(self):
        ret = super().to_json()

        if self.is_cache_folder() or self.is_activity_folder():
            # キャッシュフォルダ・アクティビティフォルダ直下では新規作成はできない
            # キャッシュフォルダ・アクティビティフォルダの変更・削除・移動もできない
            ret['allowlist']['createProject'] = False
            ret['allowlist']['createFolder'] = False
            ret['allowlist']['createFile'] = False
            ret['allowlist']['upload'] = False
            ret['allowlist']['import'] = False
            ret['allowlist']['update'] = False
            ret['allowlist']['delete'] = False
            ret['allowlist']['move'] = False
        else:
            # ルートフォルダ直下はプロジェクトのみが作成できる
            # それ以外ではプロジェクト以外が作成できる
            ret['allowlist']['createProject'] = self.is_root and self.writable
            ret['allowlist']['createFolder'] = not self.is_root and self.writable
            ret['allowlist']['createFile'] = not self.is_root and self.writable
            ret['allowlist']['upload'] = not self.is_root and self.writable
            has_usr_admin = self._session.has_usr_admin()
            ret['allowlist']['import'] = has_usr_admin
            ret['allowlist']['export'] = has_usr_admin
        return ret

    # 
    # Create Methods
    # 

    def find_children(self, prev_folder_path=False):
        """
        自分の直下の子Datumを全て取得する
        """
        from sqlalchemy import desc

        # 参照権限が無ければ直下の子Datumは取得できない
        self._readable_or_raise()

        data = self._session.query(Datum, prev_folder_path=prev_folder_path).\
                             filter(Datum.parent_id==self.id).\
                             order_by(Datum.type, desc(Datum.created_at)).all()
        return data

    def find_children_by_label(self, label, type=None):
        """
        指定したuuidの親と指定したラベル名のレコードを全て取得する
        """
        from sqlalchemy import desc
        from sqlalchemy.orm import aliased

        # 参照権限が無ければ直下の子Datumは取得できない
        self._readable_or_raise()

        f2 = aliased(Datum)
        sub_query = self._session.query(f2)
        query = self._session.query(Datum)\
                        .filter(sub_query.filter(f2.id==Datum.parent_id)
                                         .filter(f2.uuid==self.uuid).exists())\
                        .filter(Datum._label==label)

        if type is not None:
            query = query.filter(Datum.type==type)

        # フロー名フォルダが重複している場合は最も新しいフォルダに結果を格納する
        query = query.order_by(Datum.type, desc(Datum.created_at))

        return query.all()

    def find_child_by_uuid(self, uuid):
        """
        自分の直下の子から指定されたUUIDのDatumを取得する
        """

        # 参照権限が無ければ直下の子Datumは取得できない
        self._readable_or_raise()

        # UUID値の形式チェックをする
        Datum.valid_uuid_or_raise(uuid)

        data = self._session.query(Datum).filter(Datum.parent_id==self.id).\
                            filter(Datum.uuid==uuid).one()

        return data

    def count_children(self):
        # 参照権限が無ければ直下の子Datumは取得できない
        self._readable_or_raise()
        return self._session.query(Datum).filter(Datum.parent_id==self.id).count()

    def make_unique_label(self, label, except_uuid=None):
        """
        指定する親データストア内で、同じ名称のラベルがすでにある場合、末尾に数字を付加したラベル名を返す
        """
        children = self.find_children()
        while Folder._label_exists_in_Data(label, children, except_uuid):
            # 後ろから1番目の'_'でラベル名を区切る
            label_elems = label.rsplit('_', 1)
            if len(label_elems) == 2 and label_elems[1].isdecimal():
                nextNumber = int(label_elems[1]) + 1
                label = label_elems[0] + '_' + str(nextNumber)
            else:
                # 開始番号は1を飛び越して2?!
                label = label + '_2'
        return label

    @staticmethod
    def _label_exists_in_Data(label, data, except_uuid):
        """
        dataの中にlabelを使用しているdatumがあればTrueを返す
        """
        for datum in data:
            if datum.label == label and (except_uuid is None or datum.uuid != except_uuid):
                return True
        return False

    def create_folder(self, label):
        from kskp.store import Folder
        return Folder(self._session, self, label)

    def create_project_folder(self, label):
        from kskp.store import ProjectFolder
        return ProjectFolder(self._session, self, label)

    def create_awss3(self, label, bucket_name):
        from kskp.store import AwsS3
        return AwsS3(self._session, self, label, bucket_name)

    def create_database(self, label, database_conn):
        from kskp.store import Database
        return Database(self._session, self, label, database_conn)

    def create_remote_folder(self, label, remoteFolderConn):
        from kskp.store import RemoteFolder
        return RemoteFolder(self._session, self, label, remoteFolderConn)

    def create_flow(self, label, flow_data):
        from kskp.store import Flow
        return Flow(self._session, self, label, flow_data)

    def create_simple_flow(self, label, data_source):
        from kskp.store import Flow, FlowData
        flow_json = {
                        "label": label,
                        "nodes": [
                            {
                                "id": "d",
                                "type": "frame",
                                "uuid": data_source.uuid,
                                "error": {},
                                "label": data_source.label,
                                "invalid": {},
                                "makeCache": False,
                                "dataSource": "csv",
                                "cacheCreatedAt": None
                            }
                        ],
                        "ports": [[],[]],
                        "params": [],
                        "creator": self._session.user.name,
                        "createdAt": data_source.created_at_str,
                        "projectId": None,
                        "description": ""
                    }
        return Flow(self._session, self, label, FlowData(flow_json))

    def create_datasource(self, label:str, store:Datum, loader:Command, loader_args:dict={}, params:list=[]):
        """
        コンストラクタ
        """
        from datetime import datetime
        from kskp.store import Flow, FlowData

        if len(loader.i_ports) != 1 or len(loader.o_ports) != 1 :
            raise Exception('指定できるローダは1入力1出力のコマンドです')

        # PointとStepの繫がりを探索するFlowVisitorを使えばスマートに、Jsonデータを取得できるだろう
        flow_json = {
            "label": label,
            "description": "",
            "projectId": None,
            "params": params,
            "ports": [
                [],
                [
                    {
                        "label": "o",
                        "nodeId": "d",
                        "type": "frame"
                    }
                ]
            ],
            "nodes": [
                {
                    "id": "s",
                    "label": store.label,
                    "type": "store",
                    "uuid": store.uuid,
                },
                {
                    "id": "c1",
                    "label": "c1",
                    "type": "command",
                    "commandId": loader.name,
                    "args": loader_args,
                    "srcs": {
                        loader.i_ports[0].label : "s"
                    },
                    "dsts": {
                        "o": "d"
                    }
                },
                {
                    "id": "d",
                    "label": "d",
                    "type": "frame",
                    "dataSource": "csv"
                }
            ],
            "creator": self._session.user.name,
            "createdAt": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        return Flow(self._session, self, label, FlowData(flow_json))

    def create_datadest(self, label:str, store:Datum, saver:Command, saver_args:dict={}, params:list=[]):
        """
        コンストラクタ
        """
        from datetime import datetime
        from kskp.store import Flow, FlowData

        if len(saver.i_ports) != 2 or len(saver.o_ports) != 1 :
            raise Exception(f'指定できるセーバは2入力1出力のコマンドです')

        # PointとStepの繫がりを探索するFlowVisitorを使えばスマートに、Jsonデータを取得できるだろう
        flow_json = {
            "label": label,
            "description": "",
            "projectId": None,
            "params": params,
            "ports": [
                [
                    {
                        "label": "i",
                        "nodeId": "d",
                        "type": "frame"
                    }
                ],
                []
            ],
            "nodes": [
                {
                    "id": "d",
                    "label": "d",
                    "type": "frame",
                    "dataSource": "csv"
                },
                {
                    "id": "s",
                    "label": store.label,
                    "type": "store",
                    "uuid": store.uuid,
                },
                {
                    "id": "c1",
                    "label": "c1",
                    "type": "command",
                    "commandId": saver.name,
                    "args": saver_args,
                    "srcs": {
                        saver.i_ports[0].label : "d",
                        saver.i_ports[1].label : "s"
                    },
                    "dsts": {
                        "o": "d1"
                    }
                },
                {
                    "id": "d1",
                    "label": "d1",
                    "type": "frame",
                    "dataSource": "csv"
                }
            ],
            "creator": self._session.user.name,
            "createdAt": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        return Flow(self._session, self, label, FlowData(flow_json))

    def create_file(self, label, stream, maybe_csv=False):
        """
        ファイルストリームからファイルタイプを判定して
        FrameまたはDocumentを作成する
        """
        from kskp.store import File
        content_type = File.detect_content_type(stream)

        if content_type == 'text/csv':
            return self.create_frame(label, stream)
        elif content_type == 'text/plain' and maybe_csv:
            # テキストファイル、かつ多分CSVだと指定されたらCSVと判定する
            return self.create_frame(label, stream)
        else:
            return self.create_document(label, stream)

    def create_frame(self, label, stream):
        from kskp.store import Frame
        return Frame(self._session, self, label, stream)

    def create_cache(self, label, stream):
        # Cacheクラスはtype='frame'なので保存時にSQLAlchemyエラーになる
        # そのためキャッシュにはFrameクラスを用いる
        from kskp.store import Frame
        cache = Frame(self._session, self, label, stream)
        cache.is_cache = True
        return cache

    def create_document(self, label, stream):
        from kskp.store import Document
        return Document(self._session, self, label, stream)

    def create_schedule(self, label:str, runnable_uuid:str, args={}, inputs={}, trigger={}):
        from kskp.store.scheduler import Schedule
        return Schedule(self._session, self, label, runnable_uuid, args, inputs, trigger)

    def create_activity(self, label:str, flow):
        from kskp.store import Activity
        return Activity(self._session, self, label, flow)

    def create_trashcan(self):
        from kskp.store import TrashCan
        return TrashCan(self._session, self)

    def is_system_folder(self):
        from kskp.core import Datum
        return self.uuid in (Datum.FLOW_FOLDER_UUID, Datum.RESULT_FOLDER_UUID, Datum.CACHE_FOLDER_UUID, Datum.ACTIVITY_FOLDER_UUID)

    def is_cache_folder(self):
        from kskp.core import Datum
        return self.uuid == Datum.CACHE_FOLDER_UUID

    def is_activity_folder(self):
        from kskp.core import Datum
        return self.uuid == Datum.ACTIVITY_FOLDER_UUID
