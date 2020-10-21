import functools

class Constraints():
    """
    プロジェクト単位での権限設定をするための機能
    権限の基盤機能と分けるためDecoratorとする
    """

    @staticmethod
    def prohibit_move_to_root(func):
        """
        プロジェクト以外のDatumは、Rootへ移動できないよう制限する
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if func.__name__ != 'move':
                raise Exception('このDecoratorはmove()以外をデコレートできません')

            # self
            myself = args[0]

            # 移動先の親フォルダのuuid
            if 'parent_uuid' in kwargs:
                parent_uuid = kwargs['parent_uuid']
            else:
                parent_uuid = args[1]


            # Rootに移動しようとした場合は例外を送出する
            from kskp.store import ProjectFolder
            if not isinstance(myself, ProjectFolder):
                # Rootを取得する
                from kskp.store.factory import DatumFactory
                root = DatumFactory(myself._session).load_root()
                if parent_uuid == root.uuid:
                    raise Exception('プロジェクト以外のDatumは、Rootへ移動できません')

            return func(*args, **kwargs)

        return wrapper

    @staticmethod
    def prohibit_save_on_root(func):
        """
        ユーザ管理者以外は、Rootフォルダにプロジェクト以外のDatumを新規追加できないよう制限する
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if func.__name__ != 'save':
                raise Exception('このDecoratorはsave()以外をデコレートできません')

            # self
            myself = args[0]

            # 移動先がRootの場合は移動をしない
            from kskp.store import ProjectFolder
            if not isinstance(myself, ProjectFolder) and \
               not myself.is_root and \
                   myself.find_parent().is_root and \
               not myself._session.has_usr_admin():
                raise Exception('ユーザ管理者以外は、Rootフォルダにプロジェクト以外のDatumを新規追加できません')

            return func(*args, **kwargs)

        return wrapper

    @staticmethod
    def set_project_role_on_adding(func):
        """
        プロジェクト以外のDatumを新規追加した場合、
        everyoneロールとプロジェクトロールを設定する
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from sqlalchemy.orm.exc import NoResultFound

            if func.__name__ != 'save':
                raise Exception('このDecoratorはsave()以外をデコレートできません')

            result = func(*args, **kwargs)

            # self
            myself = args[0]

            # Projectの場合は権限の追加設定をしない
            from kskp.store import ProjectFolder
            if isinstance(myself, ProjectFolder):
                return result

            try:
                # 自分のプロジェクトを取得する
                my_project = myself.find_my_project()
            except NoResultFound:
                # 自分のプロジェクトがない場合はプロジェクトロールを設定しない
                return result

            # FolderまたはFlowの場合は実行権限を付与する
            from kskp.store import Folder, Flow
            folder_or_flow = isinstance(myself, Folder) or isinstance(myself, Flow) or None

            # everyoneロールへ追加データの権限を付与する
            # (プロジェクト管理者と編集者がDatumをゴミ箱にほかせるようにするため
            #  everyoneロールに所有権を付与する)
            # (everyoneがDatumの権限を自由に設定できてしまうが、
            #  Datumの権限を設定するAPIは用意していないので、問題にはならないだろう)
            from kskp.store.factory import RoleFactory
            everyone_role = RoleFactory(myself._session).load_everyone_role()
            everyone_role.init_authz(myself.id, True, True, exec=folder_or_flow, own=True)

            # 本人ロールから追加データの権限を削除する
            creator = myself._session.user
            creator_role = creator.load_self_role()
            creator_role.clear_authz(myself.id)

            return result
        return wrapper

    @staticmethod
    def set_project_role_on_set_cache(func):
        """
        キャッシュを作成する時にプロジェクトロールを設定する
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from sqlalchemy.orm.exc import NoResultFound

            if func.__name__ != 'set_cache':
                raise Exception('このDecoratorはset_cache()以外をデコレートできません')

            # self
            myself = args[0]
            # node_id
            node_id = args[1]
            # cache_uuid
            cache = args[2]

            try:
                # 自分のプロジェクトを取得する
                my_project = myself.find_my_project()
            except NoResultFound:
                # 自分のプロジェクトがない場合はプロジェクトロールを設定しない
                return func(*args, **kwargs)

            # キャッシュにプロジェクトロールを設定する
            readers_role = my_project._load_readers_role()
            readers_role.init_authz(cache.id, read=True, write=None)
            writers_role = my_project._load_writers_role()
            writers_role.init_authz(cache.id, read=None, write=True, exec=None, own=True)

            # ユーザ管理者は全てのDatumの参照・更新・実行、及び権限の変更ができること
            from kskp.store.factory import RoleFactory
            usr_admin_role = RoleFactory(myself._session).load_usr_admin_role()
            usr_admin_role.init_authz(cache.id, True, True, own=True)

            # everyoneロールからキャッシュの権限を全て削除する
            everyone_role = RoleFactory(myself._session).load_everyone_role()
            everyone_role.clear_authz(cache.id)

            # キャッシュフォルダへ行ってらっしゃい! 頑張るんだぞ
            return func(*args, **kwargs)

        return wrapper

    @staticmethod
    def set_role_on_moving(func):
        """
        Datumをプロジェクトを跨いで移動する場合、プロジェクトロール等の設定をする
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from sqlalchemy.orm.exc import NoResultFound
            from kskp.core import Datum
            from kskp.store import Folder, Flow
            from kskp.store.factory import DatumFactory, RoleFactory, AuthFactory

            if func.__name__ != 'move':
                raise Exception('このDecoratorはmove()以外をデコレートできません')

            # self
            myself = args[0]
            # parent_uuid
            to_folder_uuid = args[1]

            # プロジェクト自身の移動の場合、権限設定の変更は必要ない
            if myself.type == Datum.PROJECT_TYPE:
                return func(*args, **kwargs)

            try:
                # 自分のプロジェクトを取得する
                my_project = myself.find_my_project()
            except NoResultFound:
                # 自分のプロジェクトがない場合はプロジェクトロールを設定しない
                my_project = None

            to_folder = DatumFactory(myself._session).find_by_uuid(to_folder_uuid)

            try:
                # 移動先のプロジェクトを取得する
                to_project = to_folder.find_my_project()
            except NoResultFound:
                # 移動先がプロジェクトでない場合
                to_project = None

            # 
            # 移動元がProject内で、移動先がProject外の場合、移動元の権限設定を引き継ぐ
            # 
            if my_project is not None and to_project is None:
                # FolderまたはFlowの場合は実行権限を付与する
                folder_or_flow = isinstance(myself, Folder) or isinstance(myself, Flow) or None

                # Datumにプロジェクトロールを設定する
                writers_role = my_project._load_writers_role()
                writers_role.init_authz(myself.id, read=None, write=True, exec=None, own=True)

                # ユーザ管理者は全てのDatumの参照・更新・実行、及び権限の変更ができること
                # (everyoneロールの更新権限を削除するとユーザ管理者は移動処理ができないので、移動処理の前に行う)
                usr_admin_role = RoleFactory(myself._session).load_usr_admin_role()
                usr_admin_role.init_authz(myself.id, True, True, exec=folder_or_flow, own=True)

                # everyoneロールからDatumの所有権以外を全て削除する
                # (移動処理とeveryoneロールの削除の間隙に全ユーザから丸見えになるので、移動処理の前に行う)
                # (移動処理の失敗時に権限設定を戻せるよう所有権はTrueのままにしておく)
                everyone_role = RoleFactory(myself._session).load_everyone_role()
                everyone_role.init_authz(myself.id, None, None, exec=None, own=True)

                try:
                    # 行ってらっしゃい! 元気でね-(≧∇≦)ﾉﾞ
                    result = func(*args, **kwargs)
                except Exception:
                    # 移動処理に失敗したらeveryoneとwriters_roleロールを戻す
                    everyone_role.init_authz(myself.id, True, True, exec=folder_or_flow, own=True)
                    usr_admin_role.clear_authz(myself.id)
                    writers_role.clear_authz(myself.id)
                    # 例外は再送出する
                    raise

                # everyoneロールからDatumの所有権を削除する
                everyone_role.clear_authz(myself.id)

                # Datumにプロジェクトロールを設定する
                readers_role = my_project._load_readers_role()
                readers_role.init_authz(myself.id, read=True, write=None, exec=folder_or_flow)

                return result

            # 
            # 移動元がProject外で、移動先がProject内の場合、移動先のProjectの権限設定に変更する
            # 
            elif my_project is None and to_project is not None:
                # ただいま〜
                result = func(*args, **kwargs)

                # FolderまたはFlowの場合は実行権限を付与する
                folder_or_flow = isinstance(myself, Folder) or isinstance(myself, Flow) or None

                # everyoneロールへ権限を付与する
                everyone_role = RoleFactory(myself._session).load_everyone_role()
                everyone_role.init_authz(myself.id, True, True, exec=folder_or_flow, own=True)

                # everyoneロール以外の全ての権限を削除する
                AuthFactory(myself._session).delete_all_by_datum_id(myself.id, except_role_uuid=everyone_role.uuid)

                return result

            # 
            # 移動元がProject内で、移動先が他のProject内の場合、移動先のProjectの権限設定に変更する
            # 
            elif my_project is not None and to_project is not None and my_project != to_project:
                # インターステラー
                return func(*args, **kwargs)

            # 
            # 同じプロジェクト内での移動、または移動元と移動先がプロジェクト外での移動の場合、権限設定は必要ない
            # 
            else:
                return func(*args, **kwargs)

        return wrapper

    @staticmethod
    def set_role_to_trashed_folder(func):
        """
        ゴミ箱に形代フォルダを作成した場合、
        形代フォルダにプロジェクトロールを設定する
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from sqlalchemy.orm.exc import NoResultFound

            if func.__name__ != 'throw_away':
                raise Exception('このDecoratorはthrow_away()以外をデコレートできません')

            trashed_folder = func(*args, **kwargs)

            # self
            myself = args[0]

            # 形代フォルダを作成しなかった場合、プロジェクトロールを設定しない
            if trashed_folder is None:
                return trashed_folder

            try:
                # 自分のプロジェクトを取得する
                my_project = myself.find_my_project()
            except NoResultFound:
                # 自分のプロジェクトがない場合はプロジェクトロールを設定しない
                return trashed_folder

            # 形代フォルダを、Projectの権限設定に変更する
            writers_role = my_project._load_writers_role()
            writers_role.init_authz(trashed_folder.id, read=None, write=True, exec=None, own=True)
            readers_role = my_project._load_readers_role()
            readers_role.init_authz(trashed_folder.id, read=True, write=None, exec=True)

            # ユーザ管理者は全てのDatumの参照・更新・実行、及び権限の変更ができること
            from kskp.store.factory import RoleFactory
            usr_admin_role = RoleFactory(trashed_folder._session).load_usr_admin_role()
            usr_admin_role.init_authz(trashed_folder.id, True, True, exec=True, own=True)

            # 本人ロールから形代フォルダの権限を削除する
            creator = trashed_folder._session.user
            creator_role = creator.load_self_role()
            creator_role.clear_authz(trashed_folder.id)

            return trashed_folder

        return wrapper

    @staticmethod
    def delete_role_when_isolated(func):
        """
        Datumを削除した後に、どのDatumにも紐づかないRoleがあれば削除する
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from kskp.store.auth import NotAuthorizedException

            if func.__name__ != 'delete':
                raise Exception('このDecoratorはdelete()以外をデコレートできません')

            # Datumを削除する
            result = func(*args, **kwargs)

            # self
            myself = args[0]

            # どのDatumにも紐づかないRole、かつ削除していいよフラグのあるRoleを取得する
            from kskp.store.factory import RoleFactory
            delete_roles = RoleFactory(myself._session).find_isolated(delete_on_isolated=True)
            
            # Roleから全てのユーザを外す
            for delete_role in delete_roles:
                # Roleを削除する権限が無い場合は、Roleを削除しない
                session = delete_role._session
                if session.is_role_owner(delete_role.id) or session.has_usr_admin():
                    delete_role.delete()

            return result
        return wrapper
