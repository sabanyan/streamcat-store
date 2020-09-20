import os

from kskp.core import Datum
from kskp.store import Store

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
        self._permissions = 0b1110

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

    # def add_entry_from_path(self, file_path):
    #     """
    #     指定されたパスのファイルをFolderとして登録する
    #     """
    #     # 既にルートフォルダが存在する場合は、parent_id=NULLを許可しない
    #     from kskp.store.factory import DatumFactory
    #     if self.parent_id is None and DatumFactory(self.session).count_root() > 0:
    #         raise Exception('You can not add another root folder. A root already exists!')
    #     self.path = file_path
    #     try:
    #         # Dataテーブルにレコードを新規追加する
    #         self.session.add(self)
    #     except Exception as e:
    #         self.session.rollback()
    #         raise e
    #     finally:
    #         self.session.commit()

    def update_data(self, label, modifier=None):
        """
        Folderのdata列を更新する
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


    def throw_away(self):
        """
        Folderを中身のファイルも一緒にゴミ箱にほかす
        """
        from kskp.store.factory import DatumFactory
        factory = DatumFactory(self._session)
        trash_folder = factory.load_trash_folder()

        if self.parent_id is None:
            raise Exception('ルートフォルダは削除できません')

        thrown_count, obstacle_count = self._throw_away_inner(trash_folder, self)

        if obstacle_count == 0 and not self.is_system_folder():
            # 中のファイル全て削除可能であればフォルダ(ファイル)ごとゴミ箱へ移動する
            self.move(trash_folder.uuid)
            thrown_count += 1

        if thrown_count == 0:
            raise Exception('削除できませんでした')

    def _throw_away_inner(self, parent, datum):
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
                child_thrown_count, child_obstacle_count = self._throw_away_inner(trashed_folder, child)
                # 削除可能リストの作成
                if child_obstacle_count == 0:
                    throwables.append(child)
                # 削除ファイルと削除不可ファイルを集計する
                thrown_count += child_thrown_count
                obstacle_count += child_obstacle_count

            if obstacle_count == 0 and not datum.is_system_folder():
                # 全部捨る場合はフォルダごとゴミ箱へ移動する
                trashed_folder.delete()
            else:
                # 一部捨てる場合はそれらを形代フォルダへ移動する
                for throwable in throwables:
                    throwable.move(trashed_folder.uuid)
                    thrown_count += 1
                # 捨るものがなかった場合は形代フォルダを作らない
                if thrown_count == 0:
                    trashed_folder.delete()

            return thrown_count, obstacle_count

        elif datum.type == Datum.FRAME_TYPE or datum.type == Datum.FLOW_TYPE:
            # 削除しようとするフレーム/サブフローの更新権限がない場合は削除できない
            if not self._session.writable(datum):
                return 0, 1
            # 削除しようとするフレーム/サブフローが、フローで使用されてる場合は削除できない
            using_flow_uuids = datum.get_flow_uuids_using_me()
            if len(using_flow_uuids) > 0:
                return 0, 1
            # 削除可能!
            return 0, 0

        else:
            # データベース接続、リモートフォルダ接続
            return 0, 0

    def delete(self):
        """
        Folderを削除する
        """
        # 削除対象のフォルダの下にフォルダまたはファイルが存在する場合は例外を送出する
        if len(self.find_children()) > 0:
            raise Exception('空でないフォルダは削除できません')
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
        sql="""
        WITH RECURSIVE R AS (
            SELECT id FROM data WHERE id = {id}
            UNION ALL
            SELECT data.id FROM data JOIN R ON data.parent_id = R.id
        )
        DELETE FROM data D
        WHERE EXISTS (SELECT * FROM R
                      WHERE R.id = D.id);
        """.format(id=self.id)

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
        # 指定されたUUIDのfolerレコードを取得する
        datum = self._session.query(Datum).filter(Datum.uuid==self.uuid).one_or_none()

        parent_id = datum.parent_id
        path_to_root = [{'type':datum.type, 'uuid':datum.uuid, 'label':datum.label}]
        # 取得したレコードから外部キー’parent_id’をたどり、途中のfolderレコードをリストに順に保存する
        while parent_id != None:
            datum = self._session.query(Datum).filter(Datum.id==parent_id).one_or_none()
            path_to_root.append({'type':datum.type, 'uuid':datum.uuid, 'label':datum.label})
            parent_id = datum.parent_id
        # 保存したリストの並びを逆にする
        path_to_root.reverse()
        return path_to_root

    def _make_dir(self, path):
        """
        Folderに対応するディレクトリを作成する
        """
        try:
            # フォルダに紐付くディレクトリ(path列で指定されるディレクトリ)がなければ作成する
            if not path.is_dir():
                os.makedirs(path, exist_ok=True)
            return path
        except PermissionError as e:
            # ファイルに対する権限がない場合
            raise e

    def _remove_dir(self, path):
        """
        Folderに対応するディレクトリを削除する
        """
        from kskp.store import Mountable
        
        try:
            # 全てのフォルダから紐づかないディレクトリは物理削除する
            dir_path = path

            while dir_path != '' and dir_path != '/':
                # 自分以外で同じディレクトリパス(相対パス)を使用しているフォルダの有無を確認する
                if self._dir_path_exists(dir_path, except_id=self.id):
                    break
                elif Mountable.is_mount(dir_path):
                    # マウント中のフォルダは削除しない
                    break
                else:
                    if dir_path.is_dir():
                        dir_path.rmdir()
                    dir_path = dir_path.parent
        except PermissionError as e:
            # ディレクトリに対する権限がない場合
            raise e
        except OSError as e:
            raise e

    def _dir_path_exists(self, dir_path, except_id):
        rel_path = Datum._to_rel_path(dir_path)

        results = self._session.query(Datum._path)\
                 .filter(Datum._path.like(rel_path.as_posix() + '%'))\
                 .filter(Datum.id != except_id).all()

        for result in results:
            if result._path == dir_path:
                return True
            if os.path.commonpath([result._path, dir_path]) == dir_path:
                return True
        return False

