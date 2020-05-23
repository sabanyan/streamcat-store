import json
from pathlib import Path
from kskp.store import (
    Datum,
    DatabaseConn,
)

class FlowDumper:
    def __init__(self, factory):
        # SQLAlchemy Session
        self.factory = factory

        import uuid
        self.tmp_path = Path('/tmp')
        self.gathering_path = self.tmp_path / str(uuid.uuid4())
        self.labels_path = self.gathering_path / 'labels.txt'

    def dump_archive(self, uuid):
        gathered_uuids = set()

        self.gathering_path.mkdir()

        if self.factory.data.exists(uuid, type=Datum.FLOW_TYPE):
            archive_name = self.factory.data.find_by_uuid(uuid, type=Datum.FLOW_TYPE).label
            self._get_flow(self.gathering_path, gathered_uuids, uuid)
        elif self.factory.data.exists(uuid, type=Datum.FOLDER_TYPE):
            archive_name = self.factory.data.find_by_uuid(uuid, type=Datum.FOLDER_TYPE).label
            self._get_folder(self.gathering_path, gathered_uuids, uuid)

        # アーカイブファイルを作成する
        archive_path = self._make_archive(archive_name)

        # アーカイブされたファイルを削除する
        if self.gathering_path.exists():
            import shutil
            shutil.rmtree(self.gathering_path)

        return (archive_path, archive_name)

    def _get_folder(self, parent_tmp_path, gathered_uuids, folder_uuid):
        folder = self.factory.data.find_by_uuid(folder_uuid, type=Datum.FOLDER_TYPE)
        children = folder.find_children()

        if len(children) == 0:
            return gathered_uuids

        tmp_path = parent_tmp_path / folder.path.name
        tmp_path.mkdir()

        for child in children:
            if child.type == Datum.FOLDER_TYPE:
                gathered_uuids.union(self._get_folder(tmp_path, gathered_uuids, child.uuid))
            elif child.type == Datum.FLOW_TYPE:
                gathered_uuids.union(self._get_flow(tmp_path, gathered_uuids, child.uuid))

        return gathered_uuids

    def _get_flow(self, parent_tmp_path, gathered_uuids, flow_uuid):
        import os

        (frame_uuids, store_uuids, flow_uuids) = self._get_flows_and_frames(flow_uuid, exclude_uuids=gathered_uuids)

        uuid_type_label = []

        for frame_uuid in frame_uuids:
            frame = self.factory.data.find_by_uuid(frame_uuid, type=Datum.FRAME_TYPE)
            if frame is None or not frame.file_exists:
                # フレームファイルが存在しない場合はスキップする
                continue
            tmp_frame_link = parent_tmp_path / (frame.uuid + '.csv')
            if not tmp_frame_link.exists():
                os.symlink(frame.path, tmp_frame_link)
            uuid_type_label.append((frame.uuid, frame.type, frame.label))

        for store_uuid in store_uuids:
            if not self.factory.data.exists(store_uuid, type=Datum.DATABASE_TYPE):
                continue
            database = self.factory.data.find_by_uuid(store_uuid, type=Datum.DATABASE_TYPE)
            database_path = parent_tmp_path / (database.uuid + '.json')
            with database_path.open('w') as f:
                f.write(json.dumps(database.data['conn'], indent=2, ensure_ascii=False))
            uuid_type_label.append((database.uuid, database.type, database.label))   

        for flow_uuid in flow_uuids:
            flow = self.factory.data.find_by_uuid(flow_uuid, type=Datum.FLOW_TYPE)
            flow_path = parent_tmp_path / (flow.uuid + '.json')
            with flow_path.open('w') as f:
                f.write(json.dumps(flow.flow_data, indent=2, ensure_ascii=False))
            uuid_type_label.append((flow.uuid, flow.type, flow.label))

        # uuidとlabelの対応表をファイルに出力する
        with self.labels_path.open('a') as f:
            for uuid, type, label in uuid_type_label:
                f.write(uuid)
                f.write(',')
                f.write(type)
                f.write(',')
                f.write(label)
                f.write('\n')

        return gathered_uuids

    def _get_flows_and_frames(self, flow_uuid, exclude_uuids):
        flow = self.factory.data.find_by_uuid(flow_uuid, type=Datum.FLOW_TYPE)

        src_frame_uuids = flow.get_src_frame_uuids()
        cache_frame_uuids = flow.get_cache_frame_uuids()
        store_uuids = flow.get_store_uuids()
        sub_flow_uuids = flow.get_sub_flow_uuids()

        reference_frames = []
        reference_stores = []
        reference_flows = []

        if flow_uuid not in exclude_uuids:
            reference_flows.append(flow_uuid)
            exclude_uuids.add(flow_uuid)

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
                (frame_uuids, store_uuids, flow_uuids) = self._get_flows_and_frames(sub_flow_uuid, exclude_uuids)
                reference_frames.extend(frame_uuids)
                reference_stores.extend(store_uuids)
                reference_flows.extend(flow_uuids)
                exclude_uuids.union(frame_uuids)
                exclude_uuids.union(store_uuids)
                exclude_uuids.union(flow_uuids)

        return (reference_frames, reference_stores, reference_flows)

    def _make_archive(self, archive_name):
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

    def restore_archive(self, parent, stream):
        # 展開処理
        import uuid
        tar_dir_path = Path('/tmp') / str(uuid.uuid4())
        extracted_members = self._extract_archive(tar_dir_path, stream)

        # フレームの移行先フォルダを作成する
        frame_folder = parent.create_folder('FromOtherServer')
        frame_folder.save()
        # 保存後に参照権限を取得するためDBから取得する
        frame_folder = self.factory.data.find_by_uuid(frame_folder.uuid)

        # フローフォルダを取得する
        flow_folder = self.factory.data.load_flow_folder()
        folder_uuid = flow_folder.uuid

        flow_uuids  = {}
        uuids = {}

        # label.txtからuuidとlabelの対応を取得する
        for member in extracted_members:
            file = tar_dir_path / member.name
            if file.name == 'labels.txt':
                type_labels = self._read_labels(file)
                break

        # ライブラリに登録する
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
                    folder = flow_folder.create_folder(file.name)
                    folder_uuid = folder.uuid
                    folders[file] = folder_uuid
                    folder.save()
                    continue
                elif file.parent in folders:
                    folder_uuid = folders[file.parent]
                else:
                    # 親フォルダがない場合は作る
                    folder = flow_folder.create_folder('FromOtherServer')
                    folder_uuid = folder.uuid
                    folders[file] = folder_uuid
                    folder.save()

                (datum_type, label) = type_labels[file.stem]
                if datum_type == Datum.FRAME_TYPE:
                    file.parent
                    with file.open('rb') as f:
                        frame = frame_folder.create_frame(label, f)
                        uuids[file.stem] = frame.uuid
                        frame.save()
                elif datum_type == Datum.DATABASE_TYPE:
                    with file.open('r') as f:
                        d = f.read()
                        db = json.loads(d)
                    db_conn = DatabaseConn(db['dbms'], db['hostname'], db['port'], db['database'], db['user_id'], db['password'])
                    database = frame_folder.create_database(label, db_conn)
                    uuids[file.stem] = database.uuid
                    database.save()
                elif datum_type == Datum.FLOW_TYPE:
                    with file.open('r') as f:
                        d = f.read()
                        flow_data = json.loads(d)
                    flow = flow_folder.create_flow(label, flow_data)
                    flow_uuids[file.stem] = flow.uuid
                    uuids[file.stem] = flow.uuid
                    flow.save()
            except Exception as e:
                raise Exception(f'ERROR! at {file.name} : {str(e)}')

        # Flowの参照uuidを変更する
        for new_flow_uuid in flow_uuids.values():
            flow = self.factory.data.find_by_uuid(new_flow_uuid, type=Datum.FLOW_TYPE)
            flow.replace_uuids(uuids)
            flow.update_data(flow.label, flow.flow_data)

        # 展開したファイルを削除する
        import shutil
        shutil.rmtree(tar_dir_path)

    def _read_labels(self, file):
        type_labels = {}
        try:
            with file.open('r') as f:
                import os
                line = f.readline().rstrip(os.linesep)
                while line:
                    columns = line.split(',', maxsplit=2)
                    # uuidを読み込む
                    uuid = columns[0]
                    # typeを読み込む
                    type = columns[1]
                    # ラベル名を読み込む
                    label = columns[2]
                    type_labels[uuid] = (type, label)
                    # 次の行を読み込む
                    line = f.readline().rstrip(os.linesep)
                return type_labels
        except Exception as e:
            raise Exception(f'ERROR! at {file.name} : {str(e)}')

    def _extract_archive(self, tar_dir_path, stream):
        import tarfile
        with tarfile.open(fileobj=stream, mode='r|gz') as tar:
            tar.extractall(tar_dir_path)
            return [member for member in tar.getmembers()]
