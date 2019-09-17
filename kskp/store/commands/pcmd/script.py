# 独自コマンド
import sys
import nysol.mcmd as nm
from pathlib import Path

from kskp.store import NysolModule
from kskp.core import Command, Port

PCMD_DIR = Path(__file__).resolve().parent

class PCommand(Command):
    """
    独自コマンドのスーパークラス
    TODO: そういえばいつから独自コマンドはpcmdに。。。？
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]

    def replace_args(self, args):
        """
        nm.cmdで実行可能なargsに変換（文字列にして並べる）
        """
        args_string = ''
        for key, value in args.items():
            if isinstance(value, bool):
                if value == True:
                    args_string +=  ' -' + key
            else:
                args_string += ' %s=%s' % (key, value)

        return args_string

    def module(self, flow_obj, args):
        """
        moduleでラップする
        """
        import nysol.mcmd as nm
        flow_obj <<= nm.cmd(args)

        nysol_module = NysolModule()
        nysol_module.set_content(flow_obj)

        return nysol_module

    def run(self, args, inputs):
        """
        実際実行(for override)
        """
        pass


class SmlModelingCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/sml_modeling.sh').as_posix()
        args_string += ' kcmd_path=' + (PCMD_DIR.parent / 'kcmd/src').as_posix()
        args_string += ' temp_path=' + (PCMD_DIR / 'tmp').as_posix()
        args_string += ' model_data_path=' + (PCMD_DIR / 'model').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}

class ColumnListCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/column_list.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}

class ColumnGroupingNameCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/column_grouping_name.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}


class ColumnBlankNameCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/column_blank_name.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}


class ColumnsToRowsCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/columns_to_rows.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}

class ColumnUniqueNameCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/column_unique_name.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}

class ColumnNameCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/column_name.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}

class GroupbyColumnsCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/groupby_columns.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}

class GroupbyCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/groupby.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}

class CheckDuplicateRowsCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/check_duplicate_rows.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}


class MergeFSCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/merge_FS.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}


class MergeIbutsuCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/merge_ibutsu.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}


class WinCp932ReadCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        # f = None
        # f <<= inputs['i']

        # args_string = (PCMD_DIR / 'src/windows_cp932_csv_read.sh').as_posix()
        # args_string += self.replace_args(args)

        # return {'o': self.module(f, args_string)}

        # pythonによる変換
        # 不安定なので無効化しておく

        def Cp932_to_utf8():
            """
            ストリームでcp932→utf8に変換するコマンド
            """
            import traceback
            import io
        
            try:
                # stdinのencodingがデフォルトでutf-8なので、設定し直す。
                input_stream = io.TextIOWrapper(sys.stdin.buffer, encoding='cp932')
                for line in input_stream:
                    # 標準出力するときも自動でutf-8に変換されるので、printだけでいい
                    print(line, end='')
                # flushをする
                sys.stdout.flush()
            except Exception as e:
                with open('/dev/stderr', 'w') as fpe:
                    traceback.print_exc(file=fpe)
        
        # flushをしないと、デバッグ用のprintなども入ってしまう
        sys.stdout.flush()
        f = None
        f <<= inputs['i']
        f <<= nm.runfunc(Cp932_to_utf8)
        
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(f)
        
        return {'o': nysol_module_o}

class Utf8ToCp932Command(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/utf8_to_cp932.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}

        # pythonによる変換
        # 不安定なので無効化しておく

        # def utf8_to_Cp932():
        #     """
        #     ストリームでutf-8→cp932に変換するコマンド
        #     """
        #     import traceback
        #     import io
        #
        #     try:
        #         sys.stdout = open(sys.stdout.fileno(), 'w', encoding='cp932', closefd=False)
        #         for line in sys.stdin:
        #             # 改行コードは変えてくれなさそうなのでここで変える
        #             print(line.strip() + '\r\n', end='')
        #     except Exception as e:
        #         with open('/dev/stderr', 'w') as fpe:
        #             traceback.print_exc(file=fpe)
        #
        # sys.stdout.flush()
        # f = None
        # f <<= inputs['i']
        # f <<= nm.runfunc(utf8_to_Cp932)
        #
        # nysol_module_o= NysolModule()
        # nysol_module_o.set_content(f)
        #
        # return {'o': nysol_module_o}

class RunfuncCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        """
        実際実行(for override)
        """
        pass

class SelRowCommand(RunfuncCommand):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'mcmd'), Port('u', 'mcmd')]

    def run(self, args, inputs):
        from .src import mod

        import uuid
        import os
        import errno

        FIFO = str(uuid.uuid4())
        try:
            os.mkfifo(FIFO)
        except OSError as oe:
            if oe.errno != errno.EEXIST:
                raise

        f = inputs['i']
        f2 = None

        f <<= nm.runfunc(mod, FIFO, args)
        # runfuncの後にm2teeをしないと、f（ここでのport名はo)を使わなかった時にコンソール上に表示されてしまう
        f <<= nm.m2tee()
        f2 <<= nm.m2tee(i=FIFO)

        nysol_module_o= NysolModule()
        nysol_module_o.set_content(f)
        nysol_module_u= NysolModule()
        nysol_module_u.set_content(f2)

        return {'o': nysol_module_o, 'u': nysol_module_u}


class PlcLoaderCommand(Command):
    """
    日本特殊陶業様用に急遽作成したローダ
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]
        self.name = 'plc_loader'
        # self.i_ports = [{'name': 'i', 'type': 'frame'}]
        # self.o_ports = [{'name': 'o', 'type': 'frame'}]
        # self.description = '条件に適合したフレームファイルを抽出し、それらを1つのフレームへ結合する'

    def run(self, args, inputs):
         # 処理開始
        self._write_current_time('START')

        all_file_paths = self._select_file_paths(args, inputs)

        # 抽出対象ファイルのログ出力
        self._write_file_paths(all_file_paths)

        # 抽出対象ファイルを連結する
        cmd_o = nm.m2cat(i=all_file_paths)
        # cmd.run()

        # UTF-8へ文字コード返還する
        # tmp_file_utf8 = self._convert_to_utf8(tmp_file_path)
        # cmd_o = nm.m2tee(i=tmp_file_utf8)
        
        # args =(PCMD_DIR / 'src/windows_cp932_csv_read.sh').as_posix()
        # cmd_o <<= nm.cmd(args)

        def cp932_to_utf8():
            """
            ストリームでcp932→utf8に変換するコマンド
            """
            import traceback
            import io

            try:
                # stdinのencodingがデフォルトでutf-8なので、設定し直す。
                for line in io.TextIOWrapper(sys.stdin.buffer, encoding='cp932'):
                    # 標準出力するときも自動でutf-8に変換されるので、printだけでいい
                    print(line, end='')

                # flushをする
                sys.stdout.flush()
            except Exception as e:
                with open('/dev/stderr', 'w') as fpe:
                    traceback.print_exc(file=fpe)

        # flushをしないと、デバッグ用のprintなども入ってしまう
        # sys.stdout.flush()
        # cmd_o <<= nm.runfunc(cp932_to_utf8)

        # nysol_module_o = NysolModule()
        # nysol_module_o.set_content(cmd_o)

        # 処理終了
        self._write_current_time('END')

        return WinCp932ReadCommand().run({}, {'i': cmd_o})

        # return {'o': nysol_module_o}

    def _select_file_paths(self, args, inputs):
        from datetime import datetime

        import os
        import re
        import glob
        import uuid

        # 取得ファイルの正規表現指定
        file_name_regx = args['file_name_regx'] if 'file_name_regx' in args else '.*'
        (file_name_regx, date_regx) = self._parse_date_extended_regx(file_name_regx)
        if date_regx is None or date_regx == '':
            raise Exception('取得ファイルの正規表現指定には日時指定表現を含めて下さい')

        # 取得ディレクトリパスの直下からファイルを取得するフラグ
        get_directly_from_dir_path = args['get_directly_from_source_dir_path'] \
                                     if 'get_directly_from_source_dir_path' in args else False

        # 各ディレクトリ内で最新のファイルだけを取得するフラグ
        get_latest_file = args['get_latest_file'] if 'get_latest_file' in args else False

        # 取得ディレクトリパス
        source_dir_path = args['source_dir_path'] if 'source_dir_path' in args else ''

        # CSVのタイトル行は最初の1ファイルのタイトル行だけを採用する場合はTrue
        cut_line1 = args['cut_line1'] if 'cut_line1' in args else False

        if len(inputs) > 0:
            # 入力ストリームがあれば、そこから着手日時と完了日時を取得する
            (start_datetime, end_datetime) = self._get_term_date_from_frame(inputs['i'])

        # パラメタから日時指定されていれば、入力ストリームから取得した日時よりも優先する
        if 'start' in args and args['start'] is not None and args['start'] != '':
            start_datetime = datetime.strptime(args['start'],'%Y%m%d%H%M%S')

        if 'end' in args and args['end'] is not None and args['end'] != '':
            end_datetime = datetime.strptime(args['end'], '%Y%m%d%H%M%S')

        if start_datetime is None or end_datetime is None:
            raise Exception('着手日時または完了日時の指定が必要です')

        # 着手と完了年月
        start_ym = self._get_first_day_of_month(start_datetime)
        end_ym = self._get_last_day_of_month(end_datetime)

        # TempPathFileSourceを作成する
        tmp_dir_path  = '/tmp'
        tmp_file_uuid = str(uuid.uuid4())
        tmp_file_name = tmp_file_uuid + ".csv"

        # Tempファイルパス
        tmp_file_path = (Path(tmp_dir_path) / tmp_file_name).as_posix()

        all_file_paths = []
        last_file_paths = []

        if get_directly_from_dir_path:
            # 対象ディレクトリの直下からファイルを取得する
            dir_path_pattern = source_dir_path
        else:
            # 対象ディレクトリ内のサブディレクトリから、着手から完了日時に掛かるフォルダ名を取得する
            dir_path_pattern = (Path(source_dir_path) / '[0-9][0-9][0-9][0-9][0-9][0-9]').as_posix()

        for dir_path in glob.glob(dir_path_pattern):

            if not get_directly_from_dir_path:
                # ディレクトリ名から年月を取得する(月初日)
                dir_ym = datetime.strptime(os.path.basename(dir_path), '%Y%m')

                # 着手日時 <= ディレクトリ年月 <= 完了日時 か？
                if not self._is_between(dir_ym, start_ym, end_ym):
                    continue

            pre_file_path = None
            latest_file_path = None
            for file_path in glob.glob(dir_path + '/*'):
                # ファイル名の正規表現マッチング
                pattern = re.compile(file_name_regx)
                match = pattern.search(os.path.basename(file_path))
                if match is None:
                    continue
                # ファイル名から指定された日時部分を抜き出す
                date_str = ''
                for i in range(pattern.groups):
                    date_str += match.group(i+1)

                # 着手日時 <= ファイル名の日時 <= 完了日時 か？
                file_datetime = datetime.strptime(date_str, date_regx)
                if date_str =='' or not self._is_between(file_datetime, start_datetime, end_datetime):
                    continue

                latest_file_path = self._max_modified_time_file(pre_file_path, file_path)
                pre_file_path = file_path
                all_file_paths.append(file_path)

            # 各フォルダ内で最も最近に更新されたファイルを集める
            if latest_file_path is not None:
                last_file_paths.append(latest_file_path)

        # "ディレクトリ内で最新のファイルだけを取得する"オプションが指定されている場合
        if get_latest_file:
            all_file_paths = last_file_paths

        # ファイル名の日時順にソートする
        all_file_paths = sorted(all_file_paths)

        if len(all_file_paths) == 0:
            raise Exception('CSVファイルが見つかりませんでした')

        return all_file_paths

    def _get_term_date_from_frame(self, frame):
        import os
        from datetime import datetime

        if frame is None:
            raise Exception('着手日時と完了日時の入力がありません')
        try:
            # Tmpファイルに入力コマンドストリームの結果を出力する
            out_temp_file_path = '/tmp/mes_date_gdfo324ursf.csv'
            frame <<= nm.m2tee(o=out_temp_file_path)
            frame.run()
            # 出力した結果をメモリに格納する
            with open(out_temp_file_path) as infile:
                for line in infile:
                    latest_date_line = line
            # Tmpファイルの削除
            os.remove(out_temp_file_path)

            # 着手と完了日時を取得する
            latest_dates = latest_date_line.split(',')
            start_datetime = datetime.strptime(latest_dates[0].strip(), '%Y%m%d%H%M%S')
            end_datetime   = datetime.strptime(latest_dates[1].strip(), '%Y%m%d%H%M%S')
        except Exception as e:
            raise Exception('着手日時と完了日時の取得に失敗しました')

        return (start_datetime, end_datetime)

    def _is_between(self, datetime, start, end):
        return start <= datetime and datetime <= end

    def _get_first_day_of_month(self, datetime):
        return datetime.replace(day=1, hour=0, minute=0, second=0)

    def _get_last_day_of_month(self, datetime):
        import calendar
        last_day = calendar.monthrange(datetime.year, datetime.month)[1]
        # うるう秒のことは考えないでおこう、、
        return datetime.replace(day=last_day, hour=23, minute=59, second=59)

    def _convert_to_utf8(self, file_path):
        import os
        import subprocess
        # Shellコマンドラインを作成する
        tmp_file_path = '/tmp/' + os.path.basename(file_path) + '_utf8.tmp'
        command_str = (PCMD_DIR / 'src/windows_cp932_csv_read.sh').as_posix()
        command_arg1 = 'i=' + file_path
        command_arg2 = 'o=' + tmp_file_path
        args = [command_str, command_arg1, command_arg2]

        try:
            res = subprocess.check_call(args)
        except Exception as e:
            raise Exception("windows_cp932_csv_read.shによる文字コード返還に失敗しました!")

        return tmp_file_path

    def _max_modified_time_file(self, file_path1, file_path2):
        import os

        if file_path1 is None:
            return file_path2
        elif file_path2 is None:
            return file_path1

        mtime1 = os.path.getmtime(file_path1)
        mtime2 = os.path.getmtime(file_path2)
        if mtime1 > mtime2:
            return file_path1
        else:
            return file_path2

    def _parse_date_extended_regx(self, extended_pattern):
        in_date_pattern_state = 0
        file_regx = ""
        date_regx = ""

        for char in str(extended_pattern):
            if in_date_pattern_state > 0:
                if char == 'Y':
                    file_regx += '[0-9][0-9][0-9]'
                    date_regx += char
                elif char in '%ymdHMS':
                    file_regx += '[0-9]'
                    date_regx += char
                elif char == ')':
                    file_regx += char
                else:
                    raise Exception('取得ファイルの正規表現指定に誤りがあります')
            else:
                file_regx += char

            if char == '(':
                in_date_pattern_state += 1
            elif char == ')':
                in_date_pattern_state -= 1
        return (file_regx, date_regx)

    def _write_file_paths(self, file_paths):
        indent = '  '
        sys.__stderr__.write(indent + self.name + ': <\n')
        for file_path in file_paths:
            sys.__stderr__.write(indent + '  ' + file_path + '\n')
        sys.__stderr__.write(indent + '>\n')

    def _write_current_time(self, message):
        from datetime import datetime, timedelta, timezone

        indent = '  '
        sys.__stderr__.write(indent + self.name + ': <\n')
        JST = timezone(timedelta(hours=+9), 'JST')
        current = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')
        sys.__stderr__.write(indent + '  ' + message + ': ' + current + '\n')
        sys.__stderr__.write(indent + '>\n')       


class DaifukuLoaderCommand(PlcLoaderCommand):
    """
    ダイフク様用に急遽作成したローダ
    (ストリーム対応)
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]
        self.name = 'daifuku_loader'

    def run(self, args, inputs):
        all_file_paths = self._select_file_paths(args, inputs)

        # 抽出対象ファイルのログ出力
        self._write_file_paths(all_file_paths)

        def filter(file_paths):
            """
            CSVの各値を空白Trimして、先頭以外のヘッダ行を除外して、複数ファイルを連結する
            """
            import csv
            import traceback
        
            try:
                skip_count = 0
                is_first_file = True

                for file_path in file_paths:
                    from ctypes import cdll, c_char_p
                    lib = cdll.LoadLibrary("/home/kskp/kskp-data-store/kskp/store/commands/pcmd/libdaifuku.so")
                    lib.daifuku_loader.argtypes = (c_char_p,)
                    lib.daifuku_loader(bytes(file_path, encoding='utf-8'))
                    # # 入力ファイルの改行コードはCRLF
                    # with open(file_path, 'r', newline=None) as csv_file:
                    #     reader = csv.reader(csv_file, delimiter=',')

                    #     for values in reader:
                            
                    #         if len(values) == 0 or (0 < skip_count and skip_count < 3):
                    #             # 改行コードのみの行の場合、
                    #             # 改行コードのみの行から2行目までのヘッダ行を除外する
                    #             skip_count += 1
                    #             if is_first_file and skip_count==2:
                    #                 # 先頭ファイルのヘッダ行は除外しない
                    #                 pass
                    #             else:
                    #                 continue
                    #         else:
                    #             # 普通の行
                    #             skip_count = 0

                    #         first_loop = True
                    #         for value in values:
                    #             if first_loop:
                    #                 print(value.strip(), end='')
                    #                 first_loop = False
                    #             else:
                    #                 print(',' + value.strip(), end='')
                    #         print('') # 改行(LF)

                is_first_file = False

                # flushをする
                # sys.stdout.flush()
            except Exception as e:
                with open('/dev/stderr', 'w') as fpe:
                    traceback.print_exc(file=fpe)
        
        # flushをしないと、デバッグ用のprintなども入ってしまう
        sys.stdout.flush()

        f = None
        f <<= nm.runfunc(filter, file_paths=all_file_paths)
        # runfuncの引数には引数名が必ず必要！！

        nysol_module_o= NysolModule()
        nysol_module_o.set_content(f)
        
         # 処理終了
        self._write_current_time('END')

        return {'o': nysol_module_o}

class Hex2binCommand(Command):
    """
    16進数バイナリフラグ項目の列展開コマンド
    (ダイフク様用)
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]
        self.name = 'hex2bin'

    def run(self, args, inputs):
        import os

        # 取得ディレクトリパス
        source_dir_path = args['file_path'] if 'file_path' in args else ''
        if source_dir_path is None:
            raise Exception('バイナリ項目名取得パスを設定してください')
        if not os.path.exists(source_dir_path):
            raise Exception('%s が見つかりませんでした' % source_dir_path)

        def hex2bin(source_dir_path, args):
            # runfunc用の関数のimport
            from kskp.store.commands.pcmd.src import hex2bin
            with open(source_dir_path, 'r') as b:
                hex2bin.main(args, sys.stdin, b, sys.stdout)
                # flushをする
                sys.stdout.flush() 
        
        # flushをしないと、デバッグ用のprintなども入ってしまう
        sys.stdout.flush()

        f = inputs['i']
        f <<= nm.runfunc(hex2bin, source_dir_path=source_dir_path, args=args)

        nysol_module_o= NysolModule()
        nysol_module_o.set_content(f)  
        return {'o': nysol_module_o}
