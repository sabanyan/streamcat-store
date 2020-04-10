import uuid
from pathlib import Path
from kskp.core import Datum

class Store(Datum):
    """
    Storeを表す
    (StoreとはLoaderの入力元となり得る、またはSaverの出力先となり得るもの)
    """
    def __init__(self, session, parent_uuid, type, label, creator=None):
        super().__init__(session, parent_uuid, type, label, creator)

    def find_children(self):
        """
        自分の直下の子Datumを全て取得する
        """
        from sqlalchemy import desc

        # UUID値の形式チェックをする
        Datum.valid_uuid_or_raise(self.uuid)

        data = self.session.query(Datum).filter(Datum.parent_id==self.id).\
                            order_by(Datum.type, desc(Datum.created_at)).all()

        # 
        # DatumについてEveryOneグループの権限設定がない場合、初期値を設定する
        # (後方互換、一覧表示の速度を結構遅くしている)
        # 
        for datum in data:
            from kskp.store.factory import GroupFactory, AuthFactory
            everyone_group = GroupFactory(self.session).load_everyone_group()
            everyone_group.join_user(self.session.user)
            if not AuthFactory(self.session).exists(everyone_group.id, datum.id):
                everyone_group.init_authz(datum.id, True, True, True)

        return data

    def find_children_by_label(self, label):
        """
        指定したuuidの親と指定したラベル名のレコードを全て取得する
        """
        from sqlalchemy import desc
        from sqlalchemy.orm import aliased

        # UUID値の形式チェックをする
        Datum.valid_uuid_or_raise(self.uuid)

        f2 = aliased(Datum)
        sub_query = self.session.query(f2)
        data = self.session.query(Datum)\
                        .filter(sub_query.filter(f2.id==Datum.parent_id)
                                         .filter(f2.uuid==self.uuid).exists())\
                        .filter(Datum._label==label)\
                        .order_by(Datum.type, desc(Datum.created_at)).all()

        return data

    def find_child_by_uuid(self, uuid):
        """
        自分の直下の子から指定されたUUIDのDatumを取得する
        """
        # UUID値の形式チェックをする
        Datum.valid_uuid_or_raise(self.uuid)

        data = self.session.query(Datum).filter(Datum.parent_id==self.id).\
                            filter(Datum.uuid==uuid).one()

        return data

    def get_another_label_name(self, label, except_uuid=None):
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
        return Folder(self.session, self.uuid, label, self.session.user)

    def create_awss3(self, label, bucket_name):
        from kskp.store import AwsS3
        return AwsS3(self._session, self.uuid, label, bucket_name, self.session.user)

    def create_database(self, label, database_conn):
        from kskp.store import Database
        return Database(self.session, self.uuid, label, database_conn, self.session.user)

    def create_remote_folder(self, label, remoteFolderConn):
        from kskp.store import RemoteFolder
        return RemoteFolder(self.session, self.uuid, label, remoteFolderConn, self.session.user)

    def create_flow(self, label, flow_data):
        from kskp.store import Flow
        return Flow(self.session, self.uuid, label, flow_data, self.session.user)

    def create_datasource(self, label, store, loader_step):
        from kskp.store import DataSource
        return DataSource(self.session, self.uuid, label, store, loader_step, self.session.user)

    def create_frame(self, label, stream):
        from kskp.store import Frame
        return Frame(self.session, self.uuid, label, stream, self.session.user)

    def create_cache(self, label, stream):
        # Cacheクラスはtype='frame'なので保存時にSQLAlchemyエラーになる
        # そのためキャッシュにはFrameクラスを用いる
        from kskp.store import Frame
        cache = Frame(self.session, self.uuid, label, stream, self.session.user)
        cache.is_cache = True
        return cache

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
