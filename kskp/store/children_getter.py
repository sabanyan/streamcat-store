import os
import datetime

# from .abc_command import AbcCommand
from kskp.store import Datum, Folder, Frame, Flow, Database, RemoteFolder, TrashCan

class ChildrenGetter:

    def execute(self, args, inputs):
        user = args
        folder = inputs
        # フォルダとディレクトリの同期処理をする
        # ChildrenGetter._synchronize(folder, folder.path.as_posix(), user)
        # フォルダ直下のデータを全てリストアップして返す
        children = Datum.find_by_parent_uuid(folder.uuid)
        return [ChildrenGetter._convert_type(child) for child in children]

    @staticmethod
    def _synchronize(folder, dir_path, user):
        from pathlib import Path
        
        # バケットからファイルが削除されても、OSのファイルシステムに即反映されないので、ここでsync()する
        os.sync()

        # ドキュメント/フォルダ --> ファイル
        folder_children = Datum.find_by_parent_uuid(folder.uuid)
        for folder_child in folder_children:
            if not folder_child.path_exists:
                # フォルダ直下のデータについて、pathに値が設定されており、かつ対応するファイルが存在しない場合は、DBエントリから削除する
                ChildrenGetter._convert_type(folder_child).remove_reference_only()

        # ファイル --> ドキュメント/フォルダ
        folder_children_path = [child.path.as_posix() for child in folder_children]
        for child_file in os.listdir(Datum._to_abs_path(dir_path)):
            # 既に対応するエントリが存在するファイルの可能性もある
            # その場合はこの処理の後、一つのファイルが複数のエントリに対応する事になる
            child_path = os.path.join(dir_path, child_file)

            if child_path not in folder_children_path:
                # ディレクトリを登録する
                if os.path.isdir(Datum._to_abs_path(child_path)):
                    new_child = Folder(folder.uuid, os.path.basename(child_path), user)
                    new_child.add_entry_from_path(Path(child_path))
                    continue
                # FIXIT: 暫定的にデータタイプは拡張子をみて判断することにする
                ext = os.path.splitext(child_path)[1]
                if ext == '.csv':
                    new_child = Frame(folder.uuid, os.path.basename(child_path), None, user)
                    new_child.add_entry_from_path(Path(child_path))
                elif ext == '.json':
                    with open(child_path) as f:
                        flow_data = f.read()
                    new_child = Flow(folder.uuid, os.path.basename(child_path), flow_data, user)
                    new_child.save()

    @staticmethod
    def _convert_type(datum):
        if datum is None:
            return None
        elif datum.type == Datum.FOLDER_TYPE:
            return Folder.convert_to_folder(datum)
        elif datum.type == Datum.FRAME_TYPE:
            return Frame.convert_to_frame(datum)
        elif datum.type == Datum.FLOW_TYPE:
            return Flow.convert_to_flow(datum)
        elif datum.type == Datum.DATABASE_TYPE:
            return Database.convert_to_database(datum)
        elif datum.type == Datum.RFOLDER_TYPE:
            return RemoteFolder.convert_to_remote_folder(datum)
        elif datum.type == Datum.TRASH_TYPE:
            return TrashCan.convert_to_trash_can(datum)
        elif datum.type == Datum.AWSS3_TYPE:
            raise Exception('AWS S3 store can not store in same type.')
        else:
            raise Exception('Undefined type of datum(%s) is found!' % datum.type)
