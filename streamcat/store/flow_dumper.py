import json
from pathlib import Path
from streamcat.core import SavableDatum

class FlowDumper:
    def __init__(self, factory):
        # Factory
        self.factory = factory

        if not self.factory._session.has_usr_admin():
            raise Exception('ユーザー管理者以外は、フローのエクスポート/インポートはできません')

        # ルートフォルダはフォルダと区別して記録する
        self.ROOT_TYPE = 'root'

        import uuid
        self.tmp_path = Path('/tmp')
        self.gathering_path = self.tmp_path / str(uuid.uuid4())
        self.labels_path = self.gathering_path / 'labels.txt'

    def dump_archive(self, uuid):
        gathered_uuids = set()

        self.gathering_path.mkdir()

        if self.factory.data.exists(uuid, type=SavableDatum.FLOW_TYPE):
            archive_name = self.factory.data.find_by_uuid(uuid, type=SavableDatum.FLOW_TYPE).label
            self._get_flow(self.gathering_path, gathered_uuids, uuid)
        elif self.factory.data.exists(uuid):
            archive_name = self.factory.data.find_by_uuid(uuid).label
            self._get_folder(self.gathering_path, gathered_uuids, uuid)
        else:
            raise Exception(f'指定された({uuid})のフォルダまたはフローが存在しませんでした')

        # アーカイブファイルを作成する
        archive_path = self._make_archive()

        # アーカイブされたファイルを削除する
        if self.gathering_path.exists():
            import shutil
            shutil.rmtree(self.gathering_path)

        return (archive_path, archive_name)

    def _get_folder(self, parent_tmp_path:Path, gathered_uuids:set, folder_uuid):
        from .folder import Folder
        folder = self.factory.data.find_by_uuid(folder_uuid)
        if not isinstance(folder, Folder):
            raise Exception(f'{folder.label}はフォルダまたはプロジェクトではありません')
        children = folder.find_children()

        if len(children) == 0:
            return gathered_uuids

        tmp_path = parent_tmp_path / folder.path.name
        # exist_ok=True: 複数のフォルダが一つのディレクトリパスを共有する場合に備える
        tmp_path.mkdir(exist_ok=True)

        for child in children:
            if isinstance(child, Folder):
                gathered_uuids.union(self._get_folder(tmp_path, gathered_uuids, child.uuid))
            elif child.type == SavableDatum.FLOW_TYPE:
                gathered_uuids.union(self._get_flow(tmp_path, gathered_uuids, child.uuid))

        return gathered_uuids

    def _get_flow(self, parent_tmp_path:Path, gathered_uuids:set, flow_uuid):
        import os, warnings

        (args_uuids, frame_uuids, store_uuids, flow_uuids) = self._get_flows_and_frames(flow_uuid, exclude_uuids=gathered_uuids)

        # (UUID, type, label, edit_lock)
        uuid_type_label = []

        # argsで指定されたUUIDのtypeを判定する
        for args_uuid in args_uuids:
            if self.factory.data.exists(args_uuid):
                datum = self.factory.data.find_by_uuid(args_uuid)
                # type別に振り分けて、次の処理に丸投げする
                if datum.type == SavableDatum.FRAME_TYPE:
                    frame_uuids.append(datum.uuid)
                elif datum.type == SavableDatum.DATABASE_TYPE:
                    store_uuids.append(datum.uuid)
                elif datum.type == SavableDatum.RFOLDER_TYPE:
                    store_uuids.append(datum.uuid)
                elif datum.type == SavableDatum.FLOW_TYPE:
                    flow_uuids.append(datum.uuid)
            else:
                # Datumが存在しない場合はスキップする
                warnings.warn(f'Not Exists Datum : {args_uuid}')

        for frame_uuid in frame_uuids:
            frame = self.factory.data.find_by_uuid(frame_uuid, type=SavableDatum.FRAME_TYPE)
            if frame is None or not frame.file_exists:
                # フレームファイルが存在しない場合はスキップする
                warnings.warn(f'Not Exists file path : {frame._path}')
                continue
            tmp_frame_link = parent_tmp_path / (frame.uuid + '.csv')
            tmp_frame_json = parent_tmp_path / (frame.uuid + '.json')
            if not tmp_frame_link.exists():
                os.symlink(frame.path, tmp_frame_link)
            # 文字コードと改行コードの設定値をJSONファイルに保存する
            if not tmp_frame_json.exists():
                frame_json = {'encoding':frame.encoding_str, 'newline':frame.newline_str}
                with tmp_frame_json.open('w') as f:
                    f.write(json.dumps(frame_json, indent=2, ensure_ascii=True))
            uuid_type_label.append((frame.uuid, frame.type, frame.label, 'False'))

        for store_uuid in store_uuids:
            if self.factory.data.exists(store_uuid, type=SavableDatum.DATABASE_TYPE) or \
               self.factory.data.exists(store_uuid, type=SavableDatum.RFOLDER_TYPE):
                # データベースまたはリモートフォルダストアの場合
                store = self.factory.data.find_by_uuid(store_uuid)
                store_path = parent_tmp_path / (store.uuid + '.json')
                with store_path.open('w') as f:
                    f.write(json.dumps(store.conn.to_json(), indent=2, ensure_ascii=False))
                uuid_type_label.append((store.uuid, store.type, store.label, 'False'))
            elif self.factory.data.exists(store_uuid, type=SavableDatum.FOLDER_TYPE):
                # フォルダの場合
                store = self.factory.data.find_by_uuid(store_uuid)
                store_path = parent_tmp_path / (store.uuid + '.json')
                with store_path.open('w') as f:
                    # フォルダの場合は空ファイルを作成する
                    f.write('')
                # ルートフォルダの場合はtype='root'で記録する
                store_type = self.ROOT_TYPE if store.is_root else store.type
                uuid_type_label.append((store.uuid, store_type, store.label, 'False'))
            else:
                warnings.warn(f'Unknown type of store : {store_uuid}')
                continue

        for flow_uuid in flow_uuids:
            # フローの場合
            flow = self.factory.data.find_by_uuid(flow_uuid, type=SavableDatum.FLOW_TYPE)
            flow_path = parent_tmp_path / (flow.uuid + '.json')
            with flow_path.open('w') as f:
                f.write(json.dumps(flow.flow_data.to_json(), indent=2, ensure_ascii=False))
            uuid_type_label.append((flow.uuid, flow.type, flow.label, str(flow.edit_lock)))

        # uuidとlabelの対応表をファイルに出力する
        from streamcat.core import SCatBaseModel
        with self.labels_path.open('a') as f:
            for uuid, type, label, edit_lock in uuid_type_label:
                line = SCatBaseModel.join([uuid, type, label, edit_lock], doublequote=True)
                f.write(line)

        return gathered_uuids

    def _get_flows_and_frames(self, flow_uuid:str, exclude_uuids:set):
        flow = self.factory.data.find_by_uuid(flow_uuid, type=SavableDatum.FLOW_TYPE)

        args_uuids = flow.flow_data.get_args_uuids()
        src_frame_uuids = flow.flow_data.get_src_frame_uuids()
        cache_frame_uuids = flow.flow_data.get_cache_frame_uuids()
        store_uuids = flow.flow_data.get_store_uuids()
        sub_flow_uuids = flow.flow_data.get_sub_flow_uuids()

        reference_args = []
        reference_frames = []
        reference_stores = []
        reference_flows = []

        if flow_uuid not in exclude_uuids:
            reference_flows.append(flow_uuid)
            exclude_uuids.add(flow_uuid)

        for args_uuid in args_uuids:
            if args_uuid not in exclude_uuids:
                reference_args.append(args_uuid)
                exclude_uuids.add(args_uuid)

        for src_frame_uuid in src_frame_uuids:
            if src_frame_uuid not in exclude_uuids:
                reference_frames.append(src_frame_uuid)
                exclude_uuids.add(src_frame_uuid)

        for cache_frame_uuid in cache_frame_uuids:
            if cache_frame_uuid not in exclude_uuids:
                reference_frames.append(cache_frame_uuid)
                exclude_uuids.add(cache_frame_uuid)

        for store_uuid in store_uuids:
            if store_uuid not in exclude_uuids:
                reference_stores.append(store_uuid)
                exclude_uuids.add(store_uuid)

        for sub_flow_uuid in sub_flow_uuids:
            if sub_flow_uuid not in exclude_uuids:
                (args_uuids, frame_uuids, store_uuids, flow_uuids) = self._get_flows_and_frames(sub_flow_uuid, exclude_uuids)
                reference_args.extend(args_uuids)
                reference_frames.extend(frame_uuids)
                reference_stores.extend(store_uuids)
                reference_flows.extend(flow_uuids)
                exclude_uuids.union(args_uuids)
                exclude_uuids.union(frame_uuids)
                exclude_uuids.union(store_uuids)
                exclude_uuids.union(flow_uuids)

        return (reference_args, reference_frames, reference_stores, reference_flows)

    def _make_archive(self):
        # 圧縮ファイル名
        import uuid
        tar_file_path = self.tmp_path / (str(uuid.uuid4()) + '.tgz')

        # 圧縮処理
        import tarfile
        # シンボリックリンクはリンク先ファイルを圧縮する
        archive = tarfile.open(tar_file_path, mode='w:gz', dereference=True)
        for file_path in self.gathering_path.iterdir():
            archive.add(file_path, arcname=file_path.name, recursive=True)
        archive.close()

        return tar_file_path

    def restore_archive(self, parent, folder_label, file_name, stream):
        # 展開処理
        import uuid, warnings
        tar_dir_path = Path('/tmp') / str(uuid.uuid4())
        extracted_members = FlowDumper._extract_archive(tar_dir_path, stream)

        flow_uuids  = {}
        # uuidの変換テーブル {old_uuid : new_uuid}
        uuid_conv_table = {}

        # label.txtからuuidとlabelの対応を取得する
        type_labels = {}
        for member in extracted_members:
            file = tar_dir_path / member.name
            if file.name == 'labels.txt':
                type_labels = FlowDumper._read_labels(file)
                break
        if type_labels == {}:
            raise Exception('labels.txtが存在しません')

        # ライブラリに登録する
        default_top_folder = None
        folders = {}
        for member in extracted_members:
            file = tar_dir_path / member.name
            try:
                if file.name.startswith('.'):
                    # macOSのtarで作成した圧縮ファイルには.テキストのメタファイルがある
                    continue

                if file.name == 'labels.txt':
                    continue

                if file.is_dir():
                    if file.parent == tar_dir_path:
                        # アーカイブ内のトップディレクトリの場合、
                        # ルート直下にプロジェクトフォルダを作成する
                        folder = FlowDumper._create_folder(parent, folder_label or file.name)
                        folder.save()
                        folders[file] = folder
                    elif file.parent in folders:
                        file_parent = folders[file.parent]
                        folder = file_parent.create_folder(file.name)
                        folder.save()
                        folders[file] = folder
                    else:
                        raise Exception(f'parent folder of {file.name} is not found')
                    continue
                elif file.parent in folders:
                    folder = folders[file.parent]
                else:
                    # 親フォルダがない場合はルート直下に作る
                    if default_top_folder is None:
                        default_top_folder = FlowDumper._create_folder(parent, folder_label or file_name)
                        default_top_folder.save()
                    folder = default_top_folder

                (datum_type, label, edit_lock) = type_labels[file.stem]
                if datum_type == SavableDatum.FRAME_TYPE:
                    # FrameのJSONファイルの場合は読み飛ばす
                    if file.suffix == '.json':
                        continue
                    # FrameのJSONファイルがあれば読み込む
                    frame_json = file.parent / (file.stem + '.json')
                    data = {}
                    if frame_json.exists():
                        with frame_json.open('r') as f:
                            data = json.loads(f.read())
                    # Frameをライブラリに登録する
                    with file.open('rb') as f:
                        frame = folder.create_frame(label, f)
                        uuid_conv_table[file.stem] = frame.uuid
                        frame.save(encoding_str=data.get('encoding'), newline_str=data.get('newline'))
                elif datum_type == SavableDatum.DATABASE_TYPE:
                    from .database_conn import DatabaseConn
                    with file.open('r') as f:
                        db = json.loads(f.read())
                    db_conn = DatabaseConn(db)
                    database = folder.create_database(label, db_conn)
                    uuid_conv_table[file.stem] = database.uuid
                    database.save()
                elif datum_type == SavableDatum.RFOLDER_TYPE:
                    from .remote_folder_conn import RemoteFolderConn
                    with file.open('r') as f:
                        r = json.loads(f.read())
                    rfolder_conn = RemoteFolderConn(r)
                    rfolder = folder.create_remote_folder(label, rfolder_conn)
                    uuid_conv_table[file.stem] = rfolder.uuid
                    rfolder.save()
                elif datum_type == SavableDatum.FOLDER_TYPE:
                    folder = folder.create_folder(label)
                    uuid_conv_table[file.stem] = folder.uuid
                    folder.save()
                elif datum_type == self.ROOT_TYPE:
                    # インポート先のルートフォルダのUUIDに変換する
                    uuid_conv_table[file.stem] = self.factory.data.load_root().uuid
                elif datum_type == SavableDatum.FLOW_TYPE:
                    from .flow_data import FlowData
                    with file.open('r') as f:
                        flow_json = json.loads(f.read())
                    flow = folder.create_flow(label, FlowData(flow_json))
                    flow_uuids[file.stem] = (flow.uuid, edit_lock)
                    uuid_conv_table[file.stem] = flow.uuid
                    # 参照先Datumを先にライブラリに登録できるとは限らないので
                    # フローの保存時に参照先Datumの確認をしない
                    # 
                    # TODO: 編集ロック=ONにする時に確認することで、Publishなフローについては参照整合性を保証する
                    # 
                    flow.save(disable_validate_reference=True)
            except Exception as e:
                raise Exception(f'ERROR! at {file.name} : {str(e)}')

        # Flowの参照uuidを変更する
        for new_flow_uuid, flow_edit_lock in flow_uuids.values():
            flow = self.factory.data.find_by_uuid(new_flow_uuid, type=SavableDatum.FLOW_TYPE)
            flow.replace_uuids(uuid_conv_table)
            flow.update_data(flow.label, flow.flow_data)
            # 編集ロックを設定する
            try:
                flow.set_edit_lock(flow_edit_lock)
            except Exception as e:
                # 参照整合性が無いフローでもライブラリに登録する
                warnings.warn(f'Failed to set edit_lock : {flow.uuid}')

        # 展開したファイルを削除する
        import shutil
        shutil.rmtree(tar_dir_path)

    @staticmethod
    def _read_labels(file:Path):
        from streamcat.core import SCatBaseModel
        type_labels = {}
        try:
            with file.open('r') as f:
                import os
                line = f.readline().rstrip(os.linesep)
                while line:
                    columns = SCatBaseModel.split(line)
                    # uuidを読み込む
                    uuid = columns[0]
                    # typeを読み込む
                    type = columns[1]
                    # ラベル名を読み込む
                    label = columns[2]
                    # 編集ロックの有無を読み込む
                    if len(columns) > 3:
                        edit_lock = True if columns[3]=='True' else False
                    else:
                        edit_lock = False
                    # Dictを作成する
                    type_labels[uuid] = (type, label, edit_lock)
                    # 次の行を読み込む
                    line = f.readline().rstrip(os.linesep)
                return type_labels
        except Exception as e:
            raise Exception(f'ERROR! at {file.name} : {str(e)}')

    @staticmethod
    def _extract_archive(tar_dir_path:Path, stream):
        import tarfile
        # 'r|*' : 圧縮または無圧縮形式のアーカイブを読み込みモードで開く
        with tarfile.open(fileobj=stream, mode='r|*') as tar:
            tar.extractall(tar_dir_path)
            return [member for member in tar.getmembers()]

    @staticmethod
    def _create_folder(parent:SavableDatum, label:str) -> SavableDatum:
        """
        展開したファイルを格納するフォルダを作成する
        """
        if parent.is_root:
            # ルートフォルダにフォルダは作成できない
            return parent.create_project_folder(label)
        else:
            # ルートフォルダ以外にプロジェクトは作成できない
            return parent.create_folder(label)
