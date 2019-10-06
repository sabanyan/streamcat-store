# Store用コマンド
import os
import nysol.mcmd as nm

from kskp.store import NysolModule, Cache, Folder, Frame
from kskp.core import Command, Port



class SaverCommand(Command):
    """
    指定されているstoreに出力するコマンド（テスト用）
    基本的にはlastsを保存するためにある
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame'), Port('store', 'store')]
        self.o_ports = [Port('o', 'mcmd')]
        self.frame = None
        self.start_time = None

    def run(self, args, inputs):
        # Frameを作成する
        store = inputs['store']
        flow_label = args['flow_label']
        point_label = args['point_label']
        self.start_time = args['start_time']

        # UTC日時はここで現地時間(環境変数TZの値)に設定される
        start_time = self.start_time.astimezone()
        start_time_str1 = start_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        start_time_str2 = start_time.strftime('%Y%m%d.%H%M%S.%f')[:-3]
        folder = self.make_folder(store, flow_label, start_time_str1, start_time_str2)
        self.frame = self.make_frame(folder, point_label)

        # 1. storeにsaveする
        datum_module = folder.save_frame(self, args, inputs['i'], point_label + '.csv') 
        # 2. lasts用なのでコマンド実行のrunをする（繋げる必要はない）
        # result = datum_module.run(msg='on')

        return {'o': self.wrap_with_frame(self.frame, datum_module, args)}

    def module(self, args, input):
        command_args = {}
        command_args['i'] = input
        command_args['o'] = args['frame_path'].as_posix()
        return nm.m2tee(command_args)

    def make_folder(self, store, folder1_label, folder2_label, folder2_file_name):
        from kskp.store import Datum
        # フロー名フォルダがなければ作成する
        results = Datum.find_by_parent_uuid_and_label(store.uuid, folder1_label)
        if results is None or len(results)==0:
            folder1 = Folder(store.uuid, folder1_label, None)
            folder1.save()
        else:
            folder1 = results[0]
        # 開始時間フォルダを作成する
        folder2 = Folder(folder1.uuid, folder2_label, None)
        folder2.path = folder2.path.parent / folder2_file_name
        folder2.save()
        return folder2

    def make_frame(self, store, label):
        return Frame(store.uuid, label, None)

    def wrap_with_frame(self, frame, datum_module, args):
        frame.set_centext(args)
        frame.set_content(datum_module)
        return frame

    def dtor(self):
        if self.frame is None:
            return
        # 出力フレームのラベルに終了時刻と所要時間を付加する
        from datetime import datetime, timezone
        end_time = datetime.utcnow().replace(tzinfo=timezone.utc)
        end_time_str = end_time.astimezone().strftime('%H:%M:%S.%f')[:-3]
        new_label = self.frame.label + ' 終了時刻' + end_time_str
        if self.start_time is not None:
            elapsed_time = (end_time - self.start_time).total_seconds()
            if elapsed_time < 60.0:
                elapsed_time_str = str(round(elapsed_time, 2))
                new_label = new_label + ' 全体処理時間' + elapsed_time_str + '秒'
            else:
                elapsed_time_str = str(round(elapsed_time / 60, 2))
                new_label = new_label + ' 全体処理時間' + elapsed_time_str + '分'
        Frame.update_label_only(self.frame.uuid, new_label, None)

class CacheSaverCommand(SaverCommand):
    """
    指定されているstoreに出力するコマンド（テスト用）
    キャッシュ作成用で、Cache型で返すので別クラスで作った
    """
    def __init__(self):
        super().__init__()

    def make_frame(self, store, label):
        from kskp.store import Library
        return Cache(store.uuid, label, None)

class RunsSaver(Command):
    """
    nm.runsを行うSaverコマンド
    ※未完成
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('*', 'nm')]
        self.o_ports = [Port('?', '?')]

    def run(self, args, inputs):
        result = {}
        import nysol.mcmd as nm
        nm_list = []
        for nysol_module in inputs.values():
            nm_list.append(nysol_module)

        nm.runs(nm_list, msg='on')
        return {'o': result}

class Frame2DBSaver(Command):
    """
    frameをdbへの保存を行うsaver
    ※未完成
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'result')]
        self.o_ports = [Port('o', 'result')]

    def run(self, args, inputs):
        result = {}
        from kskp.store import Library

        for value in inputs['i'].values():
            save_datum_args = args.get(value)
            frame = Library.save_frame(save_datum_args.get('folder_uuid'),
                                       save_datum_args.get('label'),
                                       save_datum_args.get('frame_path'))

            if save_datum_args.get('type') == 'cache':
                # キャッシュ保存処理
                pass

        return {'o': result}

# 1つ保存のsaverはどうなる？
# 普通なら、inputsできたものをargs情報を使って保存か
class LoaderCommand(Command):
    """
    指定したstoreからデータを取ってくる（テスト用）
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('store', 'store')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        nysol_module = NysolModule()
        nysol_module.set_content(inputs['store'].load_frame(args['uuid']))
        return {'o': nysol_module}
