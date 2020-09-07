# Store用コマンド
import os
import sys
import nysol.mcmd as nm

from kskp.store import NysolModule, Datum, Store, Frame, Flow, Folder
from kskp.core import Command, Port
from flask import g

class SCommand(Command):
    pass

class SaverCommand(SCommand):
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
        flow_label = args['flow_label']
        point = args['point']
        point_label = point.label if point.label is not None else point.id
        start_time = args['start_time']

        # UTC日時はここで現地時間(環境変数TZの値)に設定される
        start_time = start_time.astimezone()
        start_time_str1 = start_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        start_time_str2 = start_time.strftime('%Y%m%d.%H%M%S.%f')[:-3]
        folder = self.make_folder(store, flow_label, start_time_str1, start_time_str2)
        frame = self.make_frame(folder, point_label)
        # ラベル名とファイル名はコンストラクタで別々に指定できるようにすれば
        # 改めてupdate_label_only()を行う必要はなくなる
        # もしくは、実行ログ一覧画面さえできれば別々に指定する必要もなくなるか？
        # frame.update_label_only(point_label)

        # NYSOLコマンドを作成する
        # if not isinstance(inputs['i'], NysolModule):
        #     raise Exception(f"Illegal type : {type(inputs['i'])}")
        cmd = inputs['i'].content
        cmd = self.append_writecsv_cmd(cmd, frame.path)
        # 出力フレームをRunsCommandに渡す
        nysol_module = NysolModule(cmd)
        nysol_module.context['frame'] = frame

        return {'o': nysol_module}

    def append_writecsv_cmd(self, cmd, frame_path):
        abs_frame_path = frame_path.as_posix()
        # リストが渡されても処理できるようi=に入力値を渡している
        # writecsvは0Byteデータが入力されるとエラーになるのでm2teeを使う
        return nm.m2tee(i=cmd, o=abs_frame_path)

    def make_folder(self, store, folder1_label, folder2_label, folder2_file_name):
        # フロー名フォルダがなければ作成する
        results1 = store.find_children_by_label(folder1_label, type=Datum.FOLDER_TYPE)
        if results1 is None or len(results1)==0:
            folder1 = store.create_folder(folder1_label)
            folder1.save()
            folder1 = folder1.reload()
        else:
            folder1 = results1[0]

        # 開始時間フォルダがなければ作成する
        results2 = folder1.find_children_by_label(folder2_label, type=Datum.FOLDER_TYPE)
        if results2 is None or len(results2)==0:
            folder2 = folder1.create_folder(folder2_label)
            folder2.save(file_path = folder2.path.parent / folder2_file_name)
            folder2 = folder2.reload()
        else:
            if isinstance(results2[0], Store):
                folder2 = results2[0]
            else:
                # 開始時間フォルダを作成できなかった場合はフロー名フォルダ直下に結果を作成する
                folder2 = folder1

        return folder2

    def make_frame(self, store, label):
        import io
        f = io.BytesIO(b'')
        frame = store.create_frame(label, f)
        # RunsCommandの実行前にFrameを登録する
        frame.save()
        return frame.reload()

class CacheSaverCommand(SaverCommand):
    """
    指定されているstoreに出力するコマンド（テスト用）
    キャッシュ作成用で、Cache型で返すので別クラスで作った
    """
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        store = inputs['store']
        flow_label = args['flow_label']
        point = args['point']
        point_label = point.label if point.label is not None else point.id
        start_time = args['start_time']

        # UTC日時はここで現地時間(環境変数TZの値)に設定される
        start_time = start_time.astimezone()
        start_time_str = start_time.strftime('%Y%m%d.%H%M%S.%f')[:-3]
        
        # ラベル名を作成する
        cache_label = flow_label + '_' + point_label + '_' + start_time_str
        # Nysolの oオプションに空白のファイル名があるとエラーになるので、空白を置換する
        cache_label = cache_label.replace(' ', '_')

        # Cacheフレームを作成する
        cache = self.make_frame(store, cache_label)

        # FlowのキャッシュUUIDを変更する
        # テスト実行の場合は実行するFlowをDBに保存していない
        if args['flow'] is not None:
            flow = args['flow']
            node_id = args['datum_id']
            # TODO: RunsCommand実行前にFlowにキャッシュありの情報を更新すると、同じフローの同時実行に支障があるだろう
            flow.set_cache(node_id, cache.uuid)
            flow.update_data(flow.label, flow.flow_data.to_json())

        # NYSOLコマンドを作成する
        cmd = inputs['i'].content
        cmd = self.append_writecsv_cmd(cmd, cache.path)
        # 出力フレームをRunsCommandに渡す
        nysol_module = NysolModule(cmd)
        nysol_module.context['frame'] = cache

        return {'o': nysol_module}

    def make_frame(self, store, label):
        import io
        f = io.BytesIO(b'')
        cache = store.create_cache(label, f)
        # RunsCommandの実行前にCacheを登録する
        cache.save()
        cache = cache.reload()
        # FrameとCacheを区別するためのフラグ
        cache.is_cache = True
        return cache

# 1つ保存のsaverはどうなる？
# 普通なら、inputsできたものをargs情報を使って保存か
class LoaderCommand(SCommand):
    """
    指定したstoreからデータを取ってくる（テスト用）
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('store', 'store')]
        self.o_ports = [Port('o', 'mcmd')]
        self.name = 'loader'

    def run(self, args, inputs):
        if not isinstance(inputs['store'], Store):
            t = type(inputs['store'])
            raise Exception(f'Loaderの入力にStore以外のデータ型({t})が入力されました')
        folder = inputs['store']
        if not folder.path_exists:
            raise Exception(f'ディレクトリ({folder.path})が存在しません')

        # 指定したuuidのframeを取得する
        frame_uuid = args['uuid']
        frame = folder.find_child_by_uuid(frame_uuid)
        if frame is None:
            raise Exception('No frame(%s) is found !' % frame_uuid)
        path = frame.path.as_posix()

        if frame.encoding is None:
            # frameの文字コードが未判定の場合はここで判定する
            with open(path, 'rb') as f:
                encoding = Frame._detect_encoding(f)
        else:
            # frameの文字コードを取得する
            encoding = frame.encoding

        cmd = nm.m2tee(i=path)
        # mreadで存在しないファイルパスを指定するとDockerごと落ちる -> 0.3.10で修正済
        # mreadは巨大ファイルの読み込みが遅い(全行入力してる?)
        # cmd = nm.mread({'i':path, 'n':65535})
        nysol_module = NysolModule(cmd)
        # frameの文字コードを次のコマンドに渡す
        nysol_module.encoding = encoding
        return {'o': nysol_module}

class DbLoaderCommand(SCommand):
    """
    指定したDBからデータを取得するLoaderコマンド
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'store')]
        self.o_ports = [Port('o', 'mcmd')]
        self.name = 'db_loader'

    def run(self, args, inputs):
        DbLoaderCommand._write_log('START')

        from kskp.store import Datum
        if inputs['i'].type != Datum.DATABASE_TYPE:
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

        activity_uuid_kskp = None
        if 'activity_uuid_kskp' in args:
            activity_uuid_kskp = args['activity_uuid_kskp']

        # DBへの接続URIを作成する
        db_uri = database.conn.get_database_uri()

        # SQL文を作成する
        sql = DbLoaderCommand._make_sql(schema_name, table_name, activity_uuid_kskp)

        # runfunc()へ渡す関数の定義
        def results_getter(db_uri, dbms, sql):

            # NULL値を空文字に変換する、""で囲む
            def to_str(value):
                if value is None:
                    return ''
                else:
                    return f'"{str(value)}"'

            try:
                # DBへ接続する
                engine = DbLoaderCommand._connect_to_db(db_uri)
                # SQL文を発行し結果を取得する
                results = DbLoaderCommand._get_results(engine, dbms, sql)

                is_header = True
                for result in results:
                    if is_header:
                        print(','.join(result.keys()))
                        is_header = False
                    # NULL値を空白にする
                    str_result = map(to_str, result)
                    result_line = ','.join(str_result)
                    print(result_line)
                # flushをする
                sys.stdout.flush()
            except Exception as e:
                import traceback
                with open('/dev/stderr', 'w') as fpe:
                    traceback.print_exc(file=fpe)

        # flushをしないと、デバッグ用のprintなども入ってしまう
        sys.stdout.flush()

        # Nysol Pythonのrunfunc関数を作成する
        cmd = nm.runfunc(results_getter, db_uri=db_uri, dbms=database.dbms, sql=sql)

        return {'o': NysolModule(cmd)}

    @staticmethod
    def _make_sql(schema_name, table_name, activity_uuid_kskp):
        if schema_name == '':
            schema_and_table_name = table_name
        else:
            schema_and_table_name = schema_name + '.' + table_name

        sql = f'SELECT * FROM {schema_and_table_name}'

        if activity_uuid_kskp is None:
            where = ''
        else:
            where = f" WHERE activity_uuid_kskp='{activity_uuid_kskp}'"

        return sql + where

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
    def _get_results(engine, dbms, sql):
        """
        SQL文を発行し結果を取得する
        """
        from sqlalchemy import DDL, exc
        # 時間計測開始
        import time
        t1 = time.time()

        if dbms.upper() != 'ORACLE':
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
        # DbLoaderCommand._write_log(f"SQL実行時間：{elapsed} sec")

        return results

    @staticmethod
    def _write_log(message):
        indent = '  '
        sys.__stderr__.write(indent + 'db_loader' + ': <\n')
        sys.__stderr__.write(indent + '  ' + message + '\n')
        sys.__stderr__.write(indent + '>\n')

    def dtor(self):
        DbLoaderCommand._write_log('DTOR!')


class DbSaverCommand(SaverCommand):
    """
    指定したDBへデータを格納するSaverコマンド
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame'), Port('store', 'store'), Port('folder', 'store')]
        self.o_ports = [Port('o', 'mcmd')]
        self._tmp_file_path = None

    def run(self, args, inputs):
        DbSaverCommand._write_log('START')

        from kskp.store import Datum
        if inputs['store'].type != Datum.DATABASE_TYPE:
            t = type(inputs['store'])
            raise Exception(f'DbSaverの入力にDatabase Store以外のデータ型({t})が入力されました')
        else:
            database = inputs['store']

        if inputs['folder'].type != Datum.FOLDER_TYPE:
            t = type(inputs['folder'])
            raise Exception(f'DbSaverの入力にFolder以外のデータ型({t})が入力されました')
        else:
            folder = inputs['folder']

        # DB接続情報に漏れがないか確認し、漏れがあれば例外を送出する
        database.valid_or_raise()

        # 抽出元スキーマ名とテーブル名を取得する
        if 'schema_name' not in args or args['schema_name'] is None:
            schema_name = ''
        else:
            schema_name = args['schema_name']

        if 'table_name' not in args:
            raise Exception('DB接続の格納先テーブル名が必要です')
        table_name = args['table_name']

        # Tmpファイル名を決定する
        # self._tmp_file_path = DbSaverCommand._get_tmp_file_name()

        # 指定されたテーブルがデータを格納可能か判定する → どうやって？
        # (所定の列が存在して、それら列が所定の順序に並んでいて、、)

        def bulk_inserter(database, schema_name, table_name):
            try:
                # DBへ接続する
                db_uri = database.conn.get_database_uri()
                engine = DbSaverCommand._connect_to_db(db_uri)

                # CSVのヘッダ行を取得する
                csv_columns = DbSaverCommand._get_csv_column_names(sys.stdin)

                # インポート先テーブルが無ければ作成する
                if not DbSaverCommand._table_exists(engine, schema_name, table_name):
                    DbSaverCommand._create_table(engine, database.dbms, schema_name, table_name, csv_columns)

                # CSVデータのインポートコマンドを発行する
                DbSaverCommand._import_to_table(database, schema_name, table_name, csv_columns, sys.stdin)
            except Exception as e:
                with open('/dev/stderr', 'w') as fpe:
                    import traceback
                    traceback.print_exc(file=fpe)
            finally:
                engine.dispose()

        # flushをしないと、デバッグ用のprintなども入ってしまう
        sys.stdout.flush()

        # Nysol Pythonのrunfunc関数を作成する
        cmd = inputs['i'].content
        cmd <<= nm.msetstr(v=args["activity_uuid"], a='activity_uuid_kskp')
        cmd <<= nm.runfunc(bulk_inserter, database=database, schema_name=schema_name, table_name=table_name)

        # DataSourceを保存するフォルダを用意する
        flow_label = args['flow_label']
        start_time = args['start_time'].astimezone()
        start_time_str1 = start_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        start_time_str2 = start_time.strftime('%Y%m%d.%H%M%S.%f')[:-3]
        result_folder = self.make_folder(folder, flow_label, start_time_str1, start_time_str2)

        # 出力結果を取得するDataSourceをライブラリに登録する
        # TODO: point_idどっからとってこよう
        datasource = self._create_data_source(result_folder, database, 'point_id', schema_name, table_name, args['activity_uuid'])
        datasource.save()

        # 出力DataSourceをRunsCommandに渡す
        nysol_module = NysolModule(cmd)
        nysol_module.context['frame'] = datasource

        return {'o': nysol_module}  
        
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
    def _get_csv_column_names(f):
        for header in f:
            import csv
            csv_header = csv.reader(csv.StringIO(header), delimiter=',', quotechar='"')
            # CSV列名を取得する
            for csv_column_names in csv_header:
                return csv_column_names

    @staticmethod
    def _get_csv_reader(f):
        for csv_data in f:
            import csv
            csv_data = csv.reader(csv.StringIO(csv_data), delimiter=',', quotechar='"')
            for csv_values in csv_data:
                yield csv_values

    @staticmethod
    def _table_exists(engine, schema_name, table_name):
        if schema_name == '':
            return engine.dialect.has_table(engine, table_name)
        else:
            return engine.dialect.has_table(engine, table_name, schema=schema_name)

    @staticmethod
    def _create_table(engine, dbms, schema_name, table_name, csv_columns):
        schema_and_table_name = schema_name + '.' + table_name if schema_name != '' else table_name

        column_defs = ''
        if dbms.upper() == 'POSTGRESQL':
            column_defs = 'id_kskp SERIAL'
            for column in csv_columns:
                column_defs += f',"{column}" TEXT'
        elif dbms.upper() == 'ORACLE':
            column_defs = 'id_kskp NUMBER GENERATED ALWAYS AS IDENTITY'
            for column in csv_columns:
                column_defs += f',"{column}" NVARCHAR2(4000 BYTE)'
        else:
            raise Exception('DBMS種別が判定できませんでした')

        # 列名の重複を避ける仕組みを作らなければならない
        creata_table = f"""
        CREATE TABLE {schema_and_table_name} (
            {column_defs}
        )
        """
        if dbms.upper() != 'ORACLE':
            creata_table += ';'
        from sqlalchemy import DDL, exc
        try:
            engine.execute(DDL(creata_table))
        except exc.SQLAlchemyError as e:
            raise Exception('DBのテーブル作成に失敗しました(%s)' % str(e))

    @staticmethod
    def _import_to_table(database, schema_name, table_name, csv_columns, csv_input):
        try:
            if database.dbms.upper() == 'POSTGRESQL':
                db_uri = database.conn.get_database_uri()
                DbSaverCommand._import_to_table_postgresql(db_uri, schema_name, table_name, csv_columns, csv_input)
            elif database.dbms.upper() == 'ORACLE':
                DbSaverCommand._import_to_table_oracle(database, schema_name, table_name, csv_columns, csv_input)
            else:
                raise Exception('DBのインポート先DBMS種別が判定できませんでした')
        except Exception as e:
            raise Exception('DBのテーブルへのインポートに失敗しました(%s)' % str(e))

    @staticmethod
    def _import_to_table_postgresql(db_uri, schema_name, table_name, csv_columns, csv_input):
        schema_and_table_name = schema_name + '.' + table_name if schema_name != '' else table_name

        # psycopg2からはCOPY文を発行できないようである
        import io, psycopg2
        with psycopg2.connect(db_uri) as conn:
            with conn.cursor() as cursor:
                column_name_list = ','.join(csv_columns)
                sql = f'COPY {schema_and_table_name} ({column_name_list}) FROM STDIN WITH CSV HEADER'
                cursor.copy_expert(sql, sys.stdin, size=8192)

        # 入力データを標準入力へ渡す
        for line in csv_input:
            print(line)
        # 入力データの終わりを告げる
        print(r'\.', end='')

    @staticmethod
    def _import_to_table_oracle(database, schema_name, table_name, csv_columns, csv_input):
        """
        ORACLE 12c以降に対応する
        """
        schema_and_table_name = schema_name + '.' + table_name if schema_name != '' else table_name

        # INSERT文のテーブル列名リストとVALUESのプレースホルダリストを作成する
        i = 0
        is_first = True
        column_list = ''
        placeholder_list = ''
        for csv_column in csv_columns:
            i += 1
            if is_first:
                column_list = f'"{csv_column}"'
                placeholder_list = f':{str(i)}'
                is_first = False
                continue
            column_list += f',"{csv_column}"'
            placeholder_list += f',:{str(i)}'

        import cx_Oracle

        # 一括してINSERTする行数
        batch_rows = 10000

        user_id = database.conn.user_id
        password = database.conn.password
        dsnStr = cx_Oracle.makedsn(database.conn.hostname, database.conn.port, database.conn.database)
        with cx_Oracle.connect(user_id, password, dsnStr, encoding='UTF-8', nencoding='UTF-8') as conn:
            with conn.cursor() as cursor:
                # Predefine the memory areas to match the table definition
                cursor.setinputsizes(None, 25)
                # ORACLEではSQL文の最後の;は不要
                sql = f'INSERT INTO {schema_and_table_name} ({column_list}) VALUES ({placeholder_list})'

                values_list = []
                for values in DbSaverCommand._get_csv_reader(csv_input):
                    values_list.append(values)
                    if len(values_list) % batch_rows == 0:
                        # batch_rowsの行数のデータを一括してINSERTする
                        cursor.executemany(sql, values_list)
                        values_list = []
                if values_list: 
                    cursor.executemany(sql, values_list)

            conn.commit()

    @staticmethod
    def _create_data_source(parent, database, label, schema_name, table_name, activity_uuid):
        import uuid
        from kskp.engine import Step
        from kskp.depo.std.commands import CommandLink
        args = {'schema_name':schema_name, 'table_name':table_name, 'activity_uuid_kskp':activity_uuid}
        loader_step = Step(str(uuid.uuid4()), CommandLink('db_loader').resolve(), args)
        return parent.create_datasource(label, database, loader_step)

    @staticmethod
    def _get_tmp_file_name():
        import uuid
        from pathlib import Path
        tmp_dir_path  = Path('/tmp')
        tmp_file_name = str(uuid.uuid4()) + '.csv'
        return tmp_dir_path / tmp_file_name

    @staticmethod
    def _write_log(message):
        indent = '  '
        sys.__stderr__.write(indent + 'db_saver' + ': <\n')
        sys.__stderr__.write(indent + '  ' + message + '\n')
        sys.__stderr__.write(indent + '>\n')

    def dtor(self):
        DbSaverCommand._write_log('DTOR!')
        # Tmpファイルを削除する
        import os
        if self._tmp_file_path is not None and self._tmp_file_path.exists():
            self._tmp_file_path.unlink()


class RemoteFolderLoaderCommand(SCommand):
    """
    指定したリモートフォルダからデータを取得するLoaderコマンド
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'store')]
        self.o_ports = [Port('o', 'mcmd')]
        self.name = 'remotefolder_loader'

    def run(self, args, inputs):
        from kskp.store import Datum
        if inputs['i'].type != Datum.RFOLDER_TYPE:
            t = type(inputs['i'])
            raise Exception(f'Remotefolder_loaderの入力にRemote Folder Store以外のデータ型({t})が入力されました')
        else:
            folder = inputs['i']

        # 接続情報に漏れがないか確認し、漏れがあれば例外を送出する
        folder.valid_or_raise()

        # ファイル名を取得する
        if 'file_path' not in args:
            raise Exception('リモートフォルダ接続の取得元ファイル名が必要です')
        file_path = args['file_path']

        # ファイルパスを取得する
        path = folder.path / file_path.lstrip('/')
        path_str = path.as_posix()

        cmd = nm.m2tee({'i':path_str})
        # mreadで存在しないファイルパスを指定するとDockerごと落ちる ->　
        # return nm.mread({'i':path})
        return {'o': NysolModule(cmd)}

class RemoteFolderSaverCommand(SaverCommand):
    """
    指定したリモートフォルダへデータを格納するSaverコマンド
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame'), Port('store', 'store'), Port('folder', 'store')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        from kskp.store import Datum
        if inputs['store'].type != Datum.RFOLDER_TYPE:
            t = type(inputs['store'])
            raise Exception(f'RemoteFolderSaverの入力にRemoteFolderStore以外のデータ型({t})が入力されました')
        else:
            rfolder = inputs['store']

        if inputs['folder'].type != Datum.FOLDER_TYPE:
            t = type(inputs['folder'])
            raise Exception(f'RemoteFolderSaverの入力にFolder以外のデータ型({t})が入力されました')
        else:
            folder = inputs['folder']

        # 接続情報に漏れがないか確認し、漏れがあれば例外を送出する
        rfolder.valid_or_raise()

        # ファイル名を取得する
        if 'dir_path' not in args:
            raise Exception('リモートフォルダ接続の格納先ディレクトリ名が必要です')
        dir_path = args['dir_path']

        # 出力ファイルパスを作成する
        file_path = rfolder.path / dir_path.strip('/') / 'point_id' 
        file_path = Datum.make_unique_path(file_path)
        path_str = file_path.as_posix()

        # Nysol Python
        cmd = inputs['i'].content
        cmd <<= nm.m2tee(o=path_str)

        # DataSourceを保存するフォルダを用意する
        flow_label = args['flow_label']
        start_time = args['start_time'].astimezone()
        start_time_str1 = start_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        start_time_str2 = start_time.strftime('%Y%m%d.%H%M%S.%f')[:-3]
        result_folder = self.make_folder(folder, flow_label, start_time_str1, start_time_str2)

        # 出力結果を取得するDataSourceをライブラリに登録する
        # TODO: point_idどっからとってこよう
        datasource = self._create_data_source(result_folder, rfolder, 'point_id', path_str)
        datasource.save()

        # 出力DataSourceをRunsCommandに渡す
        nysol_module = NysolModule(cmd)
        nysol_module.context['frame'] = datasource

        return {'o': NysolModule(cmd)}  

    @staticmethod
    def _create_data_source(parent, rfolder, label, file_path_str):
        import uuid
        from kskp.engine import Step
        from kskp.depo.std.commands import CommandLink
        args = {'file_path':file_path_str}
        loader_step = Step(str(uuid.uuid4()), CommandLink('remotefolder_loader').resolve(), args)
        return parent.create_datasource(label, rfolder, loader_step)

class RunsCommand(SCommand):

    # 最低必要ディスクサイズ(1Mbyte)
    MIN_REQUIRED_DISK_SIZE = 1024 * 1024

    def __init__(self):
        super().__init__()
        self.i_ports = [Port('*', 'mcmd')]
        self.o_ports = [Port('*', 'datum?')]

    def run_nysol(self, nm_list):
        # NYSOL Pythonを実行する
        ret = nm.runs(nm_list, msg='on', throwexc=True)
        return ret

    def run(self, args, inputs):
        import psutil
        from multiprocessing import Process, Manager, Pipe
        from kskp.store import List

        def do_runs(nm_list, results, exs, out):
            """
            NYSOL Pythonを実行する
            """
            try:
                # multiprocessing.Processで閉じられる標準入力を開き直す
                import sys
                sys.stdin = open(0, closefd=False)

                import nysol.mcmd as nm
                # nm.drawModelsD3(fname='aaabbbccc.html', val=nm_list)

                # 標準エラー出力のファイル記述子(No.2)を親プロセスへのPIPEに変更する
                os.dup2(out.fileno(), sys.stderr.fileno())
                # NYSOL Pythonを実行する
                # ret = nm.runs(nm_list, msg='on', throwexc=True)
                ret = self.run_nysol(nm_list)
                results.extend(ret)
            except Exception as e:
                with open('/dev/stderr', 'w') as fpe:
                    import traceback
                    traceback.print_exc(file=fpe)
                exs.append(e)

        # ディスクの空き容量を確認する
        # (Managerがtmpファイルを作成するが容量不足の時にその旨の例外を返さないので事前に確認する)
        disk_info = psutil.disk_usage('/')
        if disk_info.free < RunsCommand.MIN_REQUIRED_DISK_SIZE:
            raise Exception('ディスクの空き容量がありません')

        # NYSOLコマンドのリストを作成する
        nm_list = [nysol_module.content for nysol_module in inputs.values()]

        with Manager() as manager:
            try:
                # サブプロセスの戻値を取得するための共有メモリ
                results = manager.list()
                # サブプロセスの例外を取得するための共有メモリ
                exs = manager.list()
                # サブプロセスの標準エラー出力を取得するためのPIPE
                recv_conn, send_conn = Pipe(duplex=False)
                # PIPEをNon-Blockingにして受信処理が待ち状態になるのを防ぐ
                import fcntl
                fl = fcntl.fcntl(recv_conn.fileno(), fcntl.F_GETFL)
                fl = fl | os.O_NONBLOCK
                fcntl.fcntl(recv_conn.fileno(), fcntl.F_SETFL, fl)

                # Flask内でrunfuncを含むフローをnm.runs()で実行すると処理が固まることがある
                # これを回避するためにサププロセス内でnm.runs()を実行する
                p = Process(target=do_runs, kwargs={'nm_list':nm_list, 'results':results, 'exs':exs, 'out':send_conn})
                # サブプロセスを開始する
                p.start()
                
                mcmd_errors = []
                while True:
                    # サブプロセスが終了するまで待つ(単位は秒)
                    p.join(timeout=1)

                    # 標準エラー出力から出力内容を取得する
                    # (出力バッファがFULLになるとサブプロセスが終了しないので注意)
                    # (既に開いているファイル記述子をWrapするためにopenを用いている
                    #  recv_connオブジェクトでcloseするのでclosefd=Falseとする)
                    for line in open(recv_conn.fileno(), mode='r', closefd=False):
                        print(line, end='', file=sys.stderr)
                        sys.stderr.flush()
                        if line.startswith('#ERROR#') and 'script RUN KGERROR runmain on kgshell' not in line:
                            mcmd_errors.append(line)

                    # 子プロセスがまだ終了していない場合はNoneが返されます
                    if p.exitcode is not None:
                        break

            except Exception:
                raise
            finally:
                # Processオブジェクトを閉じ、関連付けられていたすべてのリソースを開放する
                # Python3.6.0にはない (T_T
                # p.close()
                recv_conn.close()
                send_conn.close()

            # 例外リスト
            exs_list = []

            # NYSOL-Pythonから"#ERROR#"形式のエラーが出力された場合
            from .mcmd_error_info import MCMDErrorInfo, MCMDError
            for mcmd_error in mcmd_errors:
                mcmd_error_info = MCMDErrorInfo.parse_stderr(mcmd_error)
                exs_list.append(MCMDError(mcmd_error_info))

            # "#ERROR#"形式のエラーは無く、例外が送出された場合
            if len(exs_list) == 0:
                exs_list.extend(exs)

            # NYSOL-Pythonからエラーは無く、期待する結果数が返らなかった場合
            if len(exs_list) == 0 and len(results) != len(inputs):
                exs_list.append(Exception(f'RunsCommandの入力ポート数({len(inputs)})と出力ポート数({len(results)})が異なります'))

            # resultsの要素はnm_listへのappend順に対応している?ため
            # 入力ポートと出力ポートは同じキーで対応付ける
            i = 0
            ret = {}
            for i_port_name, nysol_module in inputs.items():
                if len(exs_list) == 0:
                    frame = nysol_module.context.get('frame')
                    list = List(results[i])
                    ret[i_port_name] = frame or list
                else:
                    ret[i_port_name] = exs_list
                i += 1

            return ret


class FieldNamesCommand(RunsCommand):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('*', 'mcmd')]
        self.o_ports = [Port('*', 'datum?')]

    def run_nysol(self, nm_list):
        ret = []
        for nm_flow in nm_list:
            # ヘッダ行の取得を実行する
            ret.append(nm_flow.fldname())
        return ret


class ActivityCommand(SCommand):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('*', 'datum')]
        self.o_ports = [Port('o', 'activity')]


    def run(self, args, inputs):
        activity = args['activity']
        points = args['points']
        
        # 例外オブジェクトがあればActivityに保存する
        for datum in inputs.values():
            if isinstance(datum, list):
                activity.add_exs(datum)
                # Activityを出力Pointに渡し、処理を終了する
                return {'o': activity}
            elif isinstance(datum, Exception):
                activity.add_exs([datum])
                return {'o': activity}

        for port_id, datum in inputs.items():
            point = points[port_id]
            activity.add(point, datum)

        if activity.count_results() == len(points):
            # Activityを全て集め終えたら実行結果情報を保存する
            # (今は出力ファイル名にその情報を刻んでいる)
            activity.save()
            # Activityを出力Pointに渡し、処理を終了する
            return {'o': activity}
        else:
            # Noneを渡して、再びrun()を実行してもらう
            return {'o': None}

    def dtor(self):
        # TODO:
        # Stepからargsとsuccessフラグをもらって、実行失敗の場合は
        # ここでSaverが出力したファイルを削除する

        # 本当はSaver自身が削除すべきだが、Saverが作成したファイルを自身で覚えていない
        pass


class AssertCommand(SCommand):
    """
    フローテストコマンド
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame'), Port('m', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]
        
    def run(self, args, inputs):
        import uuid
        import difflib
        from pathlib import Path
        from itertools import zip_longest


        def report_diff(diff_args):
            """
            差分の取得および出力データのインタフェース
            """
            try:
                dlimit = diff_args["dlimit"]
                i_tmp_path = diff_args["i_tmp_path"]
                m_tmp_path = diff_args["m_tmp_path"]
                i_port_exs = diff_args["i_port_exs"]
                m_port_exs = diff_args["m_port_exs"]
                res_diff = None

                # 差分の取得を行う
                if i_port_exs and m_port_exs:
                    res_diff = create_exs_diff_list(i_tmp_path, m_tmp_path, dlimit)
                else:
                    res_diff = create_diff_list(i_tmp_path, m_tmp_path, dlimit)

                # CSVを構築して、標準出力へ渡す
                sys.stdout.flush()

                raise_exs = i_port_exs or m_port_exs
                diff_csv_maker(res_diff, raise_exs)
                
                sys.stdout.flush()

            except Exception as e:
                import traceback
                with open('dev/stderr', 'w')as fpe:
                    traceback.print_exc(file=fpe)

        def create_exs_diff_list(i_tmp_path, m_tmp_path, dlimit):
            """
            2ファイル間での差分取得を行う
            2入力どちらもエラーの場合のみ
            各入力で違うエラーが発生した場合に差分として出力する
            """
            check = []
            with open(i_tmp_path)as i_tmp:
                with open(m_tmp_path)as m_tmp:
                    i_list = i_tmp.read().splitlines()
                    m_list = m_tmp.read().splitlines()

                    get_diff = list(set(i_list) & set(m_list))
                    i_diff_elem = list(set(i_list) - set(get_diff))
                    m_diff_elem = list(set(m_list) - set(get_diff))

                    row_number = None
                    if (i_diff_elem == [] and m_diff_elem == []):
                        return []
                    else:
                        for s, t in zip_longest(i_diff_elem, m_diff_elem, fillvalue='null'):
                            diff_rows = []
                            diff_rows.append(row_number)

                            # エスケープ処理
                            i_diff = s.strip().replace("\"", "\"\"")
                            i_diff = "\"" + i_diff + "\""
                            diff_rows.append(i_diff)

                            m_diff = t.strip().replace("\"", "\"\"")
                            m_diff = "\"" + m_diff + "\""
                            diff_rows.append(m_diff)

                            # 差分検出上限数チェック
                            check.append(diff_rows)
                            if len(check) > int(dlimit):
                                return ["The output limit has been exceeded"]
            return check


        def create_diff_list(i_tmp_path, m_tmp_path, dlimit):
            """
            2ファイル間での差分取得を行う
            省メモリ化のため一行ずつ比較
            dlimitは差分検出上限数、これを超えたら全体が間違っていると判断する
            """
            check = []
            with open(i_tmp_path)as i_tmp:
                with open(m_tmp_path)as m_tmp:
                    row_number = 0
                    for s, t in zip_longest(i_tmp, m_tmp, fillvalue='null'):
                        
                        if s != t:
                            diff_rows = []
                            diff_rows.append(row_number)

                            i_diff = s.strip().replace("\"", "\"\"")
                            i_diff = "\"" + i_diff + "\""
                            diff_rows.append(i_diff)

                            m_diff = t.strip().replace("\"", "\"\"")
                            m_diff = "\"" + m_diff + "\""
                            diff_rows.append(m_diff)
                            
                            check.append(diff_rows)

                            # 差分検出上限数チェック
                            if len(check) > int(dlimit):
                                return ["The output limit has been exceeded"]
                        row_number += 1
            return check

        def diff_csv_maker(diff_result, raise_exs):
            """
            差分取得の処理結果をもとに、コマンドとしての返却データを作成
            runfuncを使用した場合、対象のコマンドでは標準出力にcsv形式のデータを渡す必要がある。（逆に、runfuncに対して、return を通してデータを返さない）
            """
            # 出力データの列
            output_columns = [  
                "flow_label",
                "flow_uuid",
                "flow_path",
                "parent_uuid",
                "parent_label",
                "date",
                # "serial_number",
                "point_id",
                "is_true",
                "raise_exs",
                "diff_row_number",
                "diff_result",
                "diff_answer"
            ]

            print(",".join(output_columns))

            # 各カラムパラメータ定義
            flow_label = args["flow_label"]
            flow_uuid = args["flow_uuid"]
            flow_path = None
            parent_uuid = None
            parent_label = None
            date = args['start_time']
            # serial number
            point_id = args['asserted_point']
            is_true = None
            raise_exs = raise_exs 


            # parentの情報を取得
            datum_list = []
            datum_data = args['flow']
            while True:
                datum_list.append(datum_data)
                if datum_data.parent_id is None:
                    break
                datum_data = datum_data.find_parent()
            datum_list.reverse()
            datum_path_labels = [x.label for x in datum_list]
            flow_path = '/' + '/'.join(datum_path_labels)

            parent_label = datum_list[1].label
            parent_uuid = datum_list[1].uuid


            # is_trueの判定 と diffの出力
            if diff_result == [] or diff_result == None:
                is_true = "True"
                diff = ["nothing","nothing","nothing"]
            else:
                is_true = "False"
                diff = diff_result

            output_datas = [
                flow_label,
                flow_uuid,
                flow_path,
                parent_uuid,
                parent_label,
                date,
                point_id,
                is_true,
                raise_exs
            ]


            # csv出力処理
            if isinstance(diff, list):
                if isinstance(diff[0], list):
                    for output_diff in diff:
                        row_data = output_datas + output_diff
                        data_str = ",".join(map(str, row_data))
                        print(data_str)
                else:
                    e = 0
                    print(",".join(map(str, output_datas)) + "," + ",".join(map(str, diff)))
            else:
                output_datas.append(diff)
                print(output_datas)



        if 'i' not in inputs:
            raise Exception('AssertCommandの入力ポートiに値が入力されていません')
        if 'm' not in inputs:
            raise Exception('AssertCommandの入力ポートmに値が入力されていません')

        # if not (isinstance(inputs['i'], NysolModule) or isinstance(inputs['i'], List)):
        #     raise Exception('入力ポートiのAssertCommandの入力データ型が異なります')
        # if not (isinstance(inputs['m'], NysolModule) or isinstance(inputs['m'], List)):
        #     raise Exception('入力ポートmのAssertCommandの入力データ型が異なります')


        # 一時ファイル作成用path
        i_tmp_path = Path("/tmp/" + str(uuid.uuid4()) + "_i.csv")
        m_tmp_path = Path("/tmp/" + str(uuid.uuid4()) + "_m.csv")


        # assertCommand以前のフローを実行する
        i_port_runs = {}
        m_port_runs = {}
        if not isinstance(inputs['i'], Exception):
            nysol_cmd_i = inputs['i'].content
            i_port_runs = RunsCommand().run({}, {'i':NysolModule(nysol_cmd_i)})
        else:
            i_port_runs['i'] = [inputs['i']]

        if not isinstance(inputs['m'], Exception):
            nysol_cmd_m = inputs['m'].content
            m_port_runs = RunsCommand().run({}, {'m':NysolModule(nysol_cmd_m)})
        else:
            m_port_runs['m'] = [inputs['m']]


        # 一時ファイルを作成する
        i_port_exs = isinstance(i_port_runs['i'], list)
        m_port_exs = isinstance(m_port_runs['m'], list)
        if i_port_exs:
            with i_tmp_path.open(mode="w")as f:
                s = [str(x) for x in i_port_runs['i']]
                f.write('\n'.join(s))
        else:
            i_make_tmp = None
            i_make_tmp <<= i_port_runs['i'].content
            i_make_tmp <<= nm.m2tee(o=i_tmp_path.as_posix())
            RunsCommand().run({}, {'i':NysolModule(i_make_tmp)})

        if m_port_exs:
            with m_tmp_path.open(mode="w")as f:
                s = [str(x) for x in m_port_runs['m']]
                f.write('\n'.join(s))
        else:
            m_make_tmp = None
            m_make_tmp <<= m_port_runs['m'].content
            m_make_tmp <<= nm.m2tee(o=m_tmp_path.as_posix())
            RunsCommand().run({}, {'m':NysolModule(m_make_tmp)})


        # 比較コマンド以前のフロー実行が失敗していたら、代わりのメッセージを出力
        if not i_tmp_path.exists():
            with nysol_cmd_i.open(mode="w")as f:
                f.write("flow before i_port is not working properly")

        if not m_tmp_path.exists():
            with nysol_cmd_m.open(mode="w")as f:
                f.write("flow before m_port is not working properly")


        # 作成した一時ファイルから差分を算出する
        new_cmd_list = None
        diff_args = {
            "dlimit" : args["dlimit"],
            "i_tmp_path" : i_tmp_path.as_posix(),
            "m_tmp_path" : m_tmp_path.as_posix(),
            "i_port_exs" : i_port_exs,
            "m_port_exs" : m_port_exs
        }

        new_cmd_list <<= nm.runfunc(report_diff, diff_args=diff_args)
        return {'o': NysolModule(new_cmd_list)}# PCommandの方法を参照
