from kskp.core import Datum

class Store(Datum):
    """
    Storeを表す
    (StoreとはLoaderの入力元となり得る、またはSaverの出力先となり得るもの)
    """
    def __init__(self, session, parent, type, label):
        super().__init__(session, parent, type, label)

    def find_children(self):
        """
        自分の直下の子Datumを全て取得する
        """
        from sqlalchemy import desc

        # 参照権限が無ければ直下の子Datumは取得できない
        self._readable_or_raise()

        data = self._session.query(Datum).filter(Datum.parent_id==self.id).\
                            order_by(Datum.type, desc(Datum.created_at)).all()

        # 
        # DatumについてEveryOneロールの権限設定がない場合、初期値を設定する
        # (後方互換、一覧表示の速度を結構遅くしている)
        # 
        # for datum in data:
        #     from kskp.store.factory import RoleFactory, AuthFactory
        #     from kskp.store.auth import Role
        #     everyone_role = RoleFactory(self._session).load_everyone_role()
        #     everyone_role.join_member(Role.Member(self._session.user))
        #     if not AuthFactory(self._session).exists(everyone_role.id, datum.id):
        #         from kskp.store import Folder, Flow
        #         # FolderまたはFlowの場合は実行権限を付与する
        #         folder_or_flow = isinstance(datum, Folder) or isinstance(datum, Flow) or None
        #         everyone_role.init_authz(datum.id, True, True, exec=folder_or_flow)

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
        while Store._label_exists_in_Data(label, children, except_uuid):
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

    def create_flow(self, label, flow_json):
        from kskp.store import Flow
        return Flow(self._session, self, label, flow_json)

    def create_simple_flow(self, label, data_source):
        from kskp.store import Flow
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
        return Flow(self._session, self, label, flow_json)

    def create_datasource(self, label, store, loader_step):
        from kskp.store import DataSource
        return DataSource(self._session, self, label, store, loader_step)

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

    def create_trashcan(self):
        from kskp.store import TrashCan
        return TrashCan(self._session, self)

    def is_system_folder(self):
        from kskp.core import Datum
        return self.uuid in (Datum.FLOW_FOLDER_UUID, Datum.RESULT_FOLDER_UUID, Datum.CACHE_FOLDER_UUID)

    # def save(self, datum):
    #     """
    #     override用
    #     """
    #     pass

    # def load(self, uuid):
    #     """
    #     override用
    #     """
    #     pass


class ModuleStore(Store):
    """
    Moduleを置いておくStore
    今は二又以上の独自コマンドを実行する際に、
    使わない方のoutput_moduleを保存しておくために使っている

    フローを実行するrunsに入れる（入れないと実行できない）
    """
    def __init__(self):
        super().__init__(None, None, 'modulestore', None)
        self.data = []

    def append(self, module):
        self.data.append(module)

    def extend(self, module_list):
        self.data.extend(module_list)

    @property
    def module_list(self):
        return self.data

class NysolModule(Datum):
    """
    NysolModuleをラップするクラス
    """
    def __init__(self, nysol_cmd=None):
        super().__init__(None, None, 'nm', None)
        self._content = nysol_cmd
        self._encoding = None

    def set_content(self, module):
        self._content = module

    @property
    def content(self):
        return self._content

    @property
    def encoding(self):
        return self._encoding

    @encoding.setter
    def encoding(self, encoding):
        self._encoding = encoding

    def __ilshift__(self, other):
        raise Exception(f'NysolModule({str(self._content)})に"<<="演算子は使えません')

class List(Datum):
    """
    リスト構造のデータを表す
    現在はテストのみで用いる
    """
    def __init__(self, content=None):
        super().__init__(None, None, 'list', None)
        self._content = content
        self._encoding = None

    def set_content(self, content):
        self._content = content

    @property
    def content(self):
        import nysol.mcmd as nm
        return nm.m2tee(i=self._content)

    @property
    def encoding(self):
        return self._encoding

    @encoding.setter
    def encoding(self, encoding):
        self._encoding = encoding

    def __ilshift__(self, other):
        raise Exception(f'List({str(self._content)})に"<<="演算子は使えません')

    def __getitem__(self, index):
        return self._content[index]
