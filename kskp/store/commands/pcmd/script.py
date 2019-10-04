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

class MultiMcalCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):

        # inputs = {'i' : 'input'}
        # args={
        #         'arglist': [
        #          {'a': 'col1', 'c': 'cal1'},
        #          {'a': 'col2', 'c': 'cal2'},
        #           ...
        #         ]
        #       }

        cmd_o = None
        first = True
        
        for arg in args['arglist']:
            # one mcal will be added to cmd_o for every pair of c and a arguments passed in a list

            # argdict = {**inputs, **arg}
            # sys.__stderr__.write(repr(argdict)+'\n')
            if first:
                cmd_o <<= nm.mcal({**inputs, **arg}) # {'i' : input, 'c': 'cal1', 'a' : 'col1'}
                first = False
            else:
                cmd_o <<= nm.mcal(arg)

        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MultiMcalWCCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
#         args format:
#             target column numbers: for now, can't figure out wildcard for column name, so just work with ranges first
#             c: operation to be done on each column, operations to be done per target columns should use the wildcard $$ 
#             a: output column name (string must include $$, default is 'new$$')

        import fnmatch as fn

        cmd_o = None
        first = True

        # get header list
        header = nm.mread(inputs).getline(header=True)
        header = next(header)

        # parse wildcard expression  
        targets_wc = args.pop('targets').split(',')

        targets = [a for a in header for target in targets_wc if fn.fnmatch(a, target)]
        #targets is now a list of column names to hit with calculation

        #iterate over entire list and replace the '$$' in c and a inputs with column number/name
        for target in targets:
            arg = args.copy()

            arg['a'] = arg['a'].replace('$$',target)
            arg['c'] = arg['c'].replace('$$',target)

            if first:
                cmd_o <<= nm.mcal({**inputs, **arg})
                first = False
            else:
                cmd_o <<= nm.mcal(arg)
        
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MultiMcalRangeCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
#         args format:
#             target column numbers: for now, can't figure out wildcard for column name, so just work with ranges first
#             c: operation to be done on each column, operations to be done per target columns should use the wildcard $$ 
#             a: output column name (string must include $$, default is 'new$$')

        args['x'] = True

        cmd_o = None
        first = True

        #parse number expressions to get list of target columns
        args['targets'] = args['targets'].split(',')

        targets = []
        for e in args['targets']:
            if '-' in e:
                targets += [*range(*[int(x) for x in e.split('-')])]
            else:
                targets.append(e)
            
        args.pop('targets')

        header = nm.mread(inputs).getline(header=True)
        header = next(header)

        #iterate over entire list and replace the '$$' in c and a inputs with column number/name
        for target in targets:
            arg = args.copy()

            arg['a'] = arg['a'].replace('$$',header[target])
            arg['c'] = arg['c'].replace('$$',str(target))

            if first:
                cmd_o <<= nm.mcal({**inputs, **arg})
                first = False
            else:
                cmd_o <<= nm.mcal(arg)
        
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}
        
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


class RdbLoaderCommand(Command):
    """
    指定したRDBからデータを取得するLoaderコマンド
    """
    def __init__(self):
        super().__init__()
        self.i_ports = []
        self.o_ports = [Port('o', 'mcmd')]
        self.name = 'rdb_loader'
        self._tmp_file_path = None

    def run(self, args, inputs):
        self._write_log('START')

        # RDBに接続する値を取得する
        if 'dbms' not in args:
            raise Exception('RDB種別の指定が必要です')
        dbms = args['dbms']

        if 'hostname' not in args:
            raise Exception('RDBのホスト名またはIPアドレスの指定が必要です')
        hostname = args['hostname']

        if 'port' not in args:
            raise Exception('RDB接続のポート番号の指定が必要です')
        port = args['port']  

        if 'database' not in args:
            raise Exception('RDB接続のデータベース名の指定が必要です')
        database = args['database']  

        if 'user_id' not in args:
            raise Exception('RDB接続のユーザIDが必要です')
        user_id = args['user_id'] 

        if 'password' not in args or args['password'] is None:
            password = ''
        else:
            password = args['password']

        if 'schema_name' not in args or args['schema_name'] is None:
            schema_name = ''
        else:
            schema_name = args['schema_name']

        if 'table_name' not in args:
            raise Exception('RDB接続の取得元テーブル名が必要です')
        table_name = args['table_name']

        # RDBへの接続URIを作成する
        from ...rdb_conn_info import RdbConnInfo
        connInfo = RdbConnInfo(dbms, hostname, port, database, user_id, password)

        # RDBへ接続する
        engine = RdbLoaderCommand._connect_to_rdb(connInfo)

        # SQL文を作成する
        sql = RdbLoaderCommand._make_sql(schema_name, table_name)

        # SQL文を発行し結果を取得する
        results = RdbLoaderCommand._get_results(engine, sql)

        # Tmpファイル名を決定する
        import uuid
        tmp_dir_path  = '/tmp'
        tmp_file_name = str(uuid.uuid4())
        self._tmp_file_path = tmp_dir_path + '/' + tmp_file_name + ".csv"

        # 結果をファイルに出力する
        def to_str(value):
            if value is None:
                return ''
            else:
                return str(value)

        with open(self._tmp_file_path, 'w') as f:
            is_header = True
            for result in results:
                if is_header:
                    f.write(','.join(result.keys()))
                    f.write('\n')
                    is_header = False
                str_result = map(to_str, result)
                result_line = ','.join(str_result)
                f.write(result_line + '\n')

        # 結果のファイルを入力とするm2teeコマンドを作成する
        cmd = nm.m2tee(i=self._tmp_file_path)

        nysol_module = NysolModule()
        nysol_module.set_content(cmd)
        return {'o': nysol_module}

    @staticmethod
    def _make_sql(schema_name, table_name):
        if schema_name == '':
            schema_and_table_name = table_name
        else:
            schema_and_table_name = schema_name + '.' + table_name
        return f"SELECT * FROM {schema_and_table_name}"

    @staticmethod
    def _connect_to_rdb(rdb_conn_info):
        # データベースへの接続
        from sqlalchemy import create_engine, exc
        # echo=TrueでSQLログがコンソールに出力される
        try:
            engine = create_engine(rdb_conn_info.get_database_uri(), echo=False)
        except exc.SQLAlchemyError as e:
            raise Exception('RDBへの接続に失敗しました %s' % sql)
        return engine

    @staticmethod
    def _get_results(engine, sql):
        """
        SQL文を発行し結果を取得する
        """
        from sqlalchemy import DDL, exc
        try:
            engine.execute('BEGIN')
        except exc.SQLAlchemyError as e:
            engine.execute('ROLLBACK')
            raise Exception('トランザクションの開始に失敗しました')

        try:
            results = engine.execute(sql)
        except exc.SQLAlchemyError as e:
            engine.execute('ROLLBACK')
            raise Exception('SQLの実行に失敗しました %s' % sql)
        finally:
            engine.execute('COMMIT')

        return results

    def _write_log(self, message):
        indent = '  '
        sys.__stderr__.write(indent + self.name + ': <\n')
        sys.__stderr__.write(indent + '  ' + message + '\n')
        sys.__stderr__.write(indent + '>\n')

    def dtor(self):
        self._write_log('DTOR!')
        # Tmpファイルを削除する
        import os
        if self._tmp_file_path is not None and os.path.exists(self._tmp_file_path):
            os.unlink(self._tmp_file_path)
