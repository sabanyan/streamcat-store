# Store用コマンド
import os
import sys
import nysol.mcmd as nm

from kskp.store import NysolModule, Cache, Frame
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

    def run(self, args, inputs):
        # Frameを作成する
        store = inputs['store']
        label = args['label']
        frame = self.get_datum_obj(store, label)

        # 1. storeにsaveする
        datum_module = store.save_frame(self, args, inputs['i'], frame.uuid + '.csv') 
        # 2. lasts用なのでコマンド実行のrunをする（繋げる必要はない）
        # result = datum_module.run(msg='on')

        return {'o': self.wrap_with_frame(frame, datum_module, args)}

    def module(self, args, input):
        command_args = {}
        command_args['i'] = input
        command_args['o'] = args['frame_path'].as_posix()
        return nm.m2tee(command_args)

    def get_datum_obj(self, store, label):
        from kskp.store import Library
        return Frame(store.uuid, label, None)

    def wrap_with_frame(self, frame, datum_module, args):
        frame.set_centext(args)
        frame.set_content(datum_module)
        return frame

class CacheSaverCommand(SaverCommand):
    """
    指定されているstoreに出力するコマンド（テスト用）
    キャッシュ作成用で、Cache型で返すので別クラスで作った
    """
    def __init__(self):
        super().__init__()

    def get_datum_obj(self, store, label):
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


class DbLoaderCommand(Command):
    """
    指定したDBからデータを取得するLoaderコマンド
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'store')]
        self.o_ports = [Port('o', 'mcmd')]
        self.name = 'db_loader'
        self._tmp_file_path = None

    def run(self, args, inputs):
        DbLoaderCommand._write_log('START')

        from kskp.store import Database
        if not isinstance(inputs['i'], Database):
            t = type(inputs['i'])
            raise Exception(f'DbLoaderの入力にDatabase Store以外のデータ型({t})が入力されました')
        else:
            database = inputs['i']

        # DB接続情報に漏れがないか確認し、漏れがあれば例外を送出する
        database.valid_or_raise()

        # 抽出元スキーマ名とテーブル名を取得する
        if 'schema_name' not in args or args['schema_name'] is None:
            schema_name = ''
        else:
            schema_name = args['schema_name']

        if 'table_name' not in args:
            raise Exception('DB接続の取得元テーブル名が必要です')
        table_name = args['table_name']

        # DBへの接続URIを作成する
        db_uri = database.get_database_uri()

        # DBへ接続する
        engine = DbLoaderCommand._connect_to_db(db_uri)

        # SQL文を作成する
        sql = DbLoaderCommand._make_sql(schema_name, table_name)

        # SQL文を発行し結果を取得する
        results = DbLoaderCommand._get_results(engine, sql)

        # Tmpファイル名を決定する
        import uuid
        tmp_dir_path  = '/tmp'
        tmp_file_name = str(uuid.uuid4())
        self._tmp_file_path = tmp_dir_path + '/' + tmp_file_name + '.csv'

        # 結果をTmpファイルに出力する
        self._write_to_file_from_results(results, self._tmp_file_path)

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
        return f'SELECT * FROM {schema_and_table_name}'

    @staticmethod
    def _connect_to_db(db_uri):
        # データベースへの接続
        from sqlalchemy import create_engine, exc
        # echo=TrueでSQLログがコンソールに出力される
        try:
            engine = create_engine(db_uri, echo=False)
        except exc.SQLAlchemyError as e:
            raise Exception('DBへの接続に失敗しました(%s)' % str(e))
        return engine

    @staticmethod
    def _get_results(engine, sql):
        """
        SQL文を発行し結果を取得する
        """
        from sqlalchemy import DDL, exc
        # 時間計測開始
        import time
        t1 = time.time()

        try:
            engine.execute('BEGIN')
        except exc.SQLAlchemyError as e:
            engine.execute('ROLLBACK')
            raise Exception('トランザクションの開始に失敗しました(%s)' % str(e))

        try:
            results = engine.execute(sql)
        except exc.SQLAlchemyError as e:
            engine.execute('ROLLBACK')
            raise Exception('SQLの実行に失敗しました %s' % sql)
        finally:
            engine.execute('COMMIT')

        # 時間計測終了
        t2 = time.time()
        elapsed = t2-t1
        DbLoaderCommand._write_log(f"SQL実行時間：{elapsed} sec")

        return results

    def _write_to_file_from_results(self, results, file_path):
        def to_str(value):
            if value is None:
                return ''
            else:
                return str(value)

        # 結果をファイルに出力する
        with open(file_path, 'w') as f:
            is_header = True
            for result in results:
                if is_header:
                    f.write(','.join(result.keys()))
                    f.write('\n')
                    is_header = False
                # NULL値を空白にする
                str_result = map(to_str, result)
                result_line = ','.join(str_result)
                f.write(result_line + '\n')

    def _write_log(message):
        indent = '  '
        sys.__stderr__.write(indent + 'db_loader' + ': <\n')
        sys.__stderr__.write(indent + '  ' + message + '\n')
        sys.__stderr__.write(indent + '>\n')

    def dtor(self):
        DbLoaderCommand._write_log('DTOR!')
        # Tmpファイルを削除する
        import os
        if self._tmp_file_path is not None and os.path.exists(self._tmp_file_path):
            os.unlink(self._tmp_file_path)
