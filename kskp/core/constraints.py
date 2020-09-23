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
            if func.__name__ != 'save':
                raise Exception('このDecoratorはsave()以外をデコレートできません')

            result = func(*args, **kwargs)

            # self
            myself = args[0]

            # Projectの場合は権限の追加設定をしない
            from kskp.store import ProjectFolder
            if isinstance(myself, ProjectFolder):
                return result

            # FolderまたはFlowの場合は実行権限を付与する
            from kskp.store import Folder, Flow
            folder_or_flow = isinstance(myself, Folder) or isinstance(myself, Flow) or None

            # everyoneロールへ追加データの権限を付与する
            from kskp.store.factory import RoleFactory
            everyone_role = RoleFactory(myself._session).load_everyone_role()
            everyone_role.init_authz(myself.id, True, True, exec=folder_or_flow)

            return result
        return wrapper
