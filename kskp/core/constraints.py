import functools

class Constraints():
    """
    プロジェクト単位での権限設定をするための機能
    権限の基盤機能と分けるためDecoratorとする
    """

    @staticmethod
    def prohibit_movement_to_root(func):
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
    def prohibit_save_under_root(func):
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
    def set_permissions_for_everyone(func):
        """
        プロジェクト以外のDatumを新規追加した後、everyoneにRWXを追加設定する
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
            from kskp.store.factory import RoleFactory
            everyone_role = RoleFactory(myself._session).load_everyone_role()
            everyone_role.init_authz(myself.id, True, True, exec=folder_or_flow)

            # プロジェクト管理者と編集者がDatumをゴミ箱にほかせるようにするため
            # Writersプロジェクトロールに所有権を付与する
            # (編集者がDatumの権限を自由に設定できてしまうが、
            #  Datumの権限を設定するAPIは用意していないので、問題にはならないだろう)
            writers_role = my_project._load_writers_role()
            writers_role.init_authz(myself.id, read=None, write=True, exec=None, own=True)

            # 本人ロールから追加データの権限を削除する
            creator = myself._session.user
            creator_role = creator.load_self_role()
            creator_role.clear_authz(myself.id)

            return result
        return wrapper

    @staticmethod
    def set_project_role_on_throwing_away(func):
        """
        ゴミ箱にほかす時にプロジェクトロールを設定する
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from sqlalchemy.orm.exc import NoResultFound

            if func.__name__ != 'throw_away':
                raise Exception('このDecoratorはthrow_away()以外をデコレートできません')

            # self
            myself = args[0]

            try:
                # 自分のプロジェクトを取得する
                my_project = myself.find_my_project()
            except NoResultFound:
                # 自分のプロジェクトがない場合はプロジェクトロールを設定しない
                return func(*args, **kwargs)

            # ゴミにプロジェクトロールを設定する
            readers_role = my_project._load_readers_role()
            readers_role.init_authz(myself.id, read=True, write=None)

            # ユーザ管理者は全てのDatumの参照・更新・実行、及び権限の変更ができること
            from kskp.store.factory import RoleFactory
            usr_admin_role = RoleFactory(myself._session).load_usr_admin_role()
            usr_admin_role.init_authz(myself.id, True, True, own=True)

            # everyoneロールからゴミの権限を全て削除する
            everyone_role = RoleFactory(myself._session).load_everyone_role()
            everyone_role.clear_authz(myself.id)

            # ゴミ箱へ行ってらっしゃい! 元気でね-(≧∇≦)ﾉﾞ
            return func(*args, **kwargs)

        return wrapper

    @staticmethod
    def unset_project_role_on_put_back(func):
        """
        ゴミ箱から戻す時にプロジェクトロールを戻す
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from sqlalchemy.orm.exc import NoResultFound

            if func.__name__ != 'put_back':
                raise Exception('このDecoratorはput_back()以外をデコレートできません')

            # ゴミ箱からただいま〜
            result = func(*args, **kwargs)

            # self
            myself = args[0]

            try:
                # 自分のプロジェクトを取得する
                my_project = myself.find_my_project()
            except NoResultFound:
                # 自分のプロジェクトがない場合はプロジェクトロールを設定しない
                return result

            # FolderまたはFlowの場合は実行権限を付与する
            from kskp.store import Folder, Flow
            folder_or_flow = isinstance(myself, Folder) or isinstance(myself, Flow) or None

            # プロジェクトロールを元に戻す
            readers_role = my_project._load_readers_role()
            readers_role.clear_authz(myself.id)

            # usr_adminロールの権限を全て削除する
            from kskp.store.factory import RoleFactory
            usr_admin_role = RoleFactory(myself._session).load_usr_admin_role()
            usr_admin_role.clear_authz(myself.id)

            # everyoneロールへ権限を再び付与する
            everyone_role = RoleFactory(myself._session).load_everyone_role()
            everyone_role.init_authz(myself.id, True, True, exec=folder_or_flow)

            return result
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
