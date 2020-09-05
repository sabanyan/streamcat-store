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
        print("-act-inputs----") 
        print(inputs)
        print("-act-args----") 
        print(args)
        print("------")
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
        # print("\n\n---test\n\ntest\n\ntest\n----") 
        
    def run(self, args, inputs):
        import uuid
        import difflib
        import subprocess
        from pathlib import Path
        from subprocess import PIPE
        import sys, csv


        def test_py(tmp_path):
            import sys, csv
            f = None
            sys.stdout.flush()
            with open (tmp_path) as data:
                print(data.read()) 
            sys.stdout.flush()

        def report_diff(diff_args):
            """
            差分の取得および出力データのインタフェース
            """
            try:
                dlimit = diff_args["dlimit"]
                comp_path = diff_args["comp_path"]
                ret_diff = None
                # 差分の取得を行う
                # test_py(comp_path[0])

                ret_diff = diff_getter(comp_path[0],comp_path[1],dlimit)
                # if dlimit == 0:
                #     ret_diff = diff_perfect_match(comp_path[0],comp_path[1])
                # else:
                #     ret_diff = diff_partial(comp_path[0],comp_path[1],dlimit)

                # CSVを構築して、標準出力へ渡す
                sys.stdout.flush()

                # print(ret_diff)
                # print(len(ret_diff))
                diff_csv_maker(ret_diff)
                # test_py(comp_path[0])
                # print('["顧客", "数量", "金額"]')
                sys.stdout.flush()

            except Exception as e:
                import traceback
                with open('dev/stderr', 'w')as fpe:
                    traceback.print_exc(file=fpe)

        # def diff_perfect_match(comp_path1, comp_path2):
        #     """
        #     ファイル完全一致であるかの判定を行う
        #     ２ファイルのハッシュ値での比較
        #     """
        #     import hashlib
        #     import filecmp

        #     # return filecmp.cmpfiles(C)
        #     # compare = filecmp()
        #     if filecmp.cmp(comp_path1, comp_path2):
        #         return True
        #     else:
        #         return ["A difference was found between the output data to be compared."]

        #     # with open(comp_path1)as com_l:
        #     #     with open (comp_path2)as com_r:
        #     #         hash_l = hashlib.sha1()
        #     #         hash_r = hashlib.sha1()
        #     #         while len(chunk_l) == 0 or len(chunk_r) == 0:
        #     #             chunk_l = com_l.read(2048 * hash_l.block_size)
        #     #             chunk_r = com_r.read(2048 * hash_r.block_size)

        #     #             if len(chunk_l) == 0 or len(chunk_r) == 0:
        #     #                 break
                        
        #     #             hash_l.update(chunk_l)
        #     #             hash_r.update(chunk_r)
                    
        #             # if str(hash_l) == str(hash_r):
        #             #     return None
        #             # else:
        #             #     return ["A difference was found between the output data to be compared."]
        #     # test_py(tmp_path_i.as_posix())

        def diff_getter(comp_path1, comp_path2, dlimit):
            """
            2ファイル間での差分取得を行う
            省メモリ化のため一行ずつ比較
            dlimitは差分検出上限数、これを超えたら全体が間違っていると判断する
            """
            import difflib
            from itertools import zip_longest
            check = []
            with open(comp_path1)as com_l:
                with open(comp_path2)as com_r:
                    row_number = 0
                    for s,t in zip_longest(com_l, com_r, fillvalue='null'):
                        
                        if s != t:
                            diff_one_row = []
                            # check.append("".join(d.compare(s, t)))
                            diff_one_row.append(row_number)

                            diff_l = s.strip().replace("\"", "\"\"")
                            diff_l = "\"" + diff_l + "\""
                            # print(diff_l)
                            # diff_one_row.append('\"' + diff_l + '\"')
                            diff_one_row.append(diff_l)
                            diff_r = t.strip().replace("\"", "\"\"")
                            diff_r = "\"" + diff_r + "\""
                            # diff_one_row.append('\"' + diff_r + '\"')
                            diff_one_row.append(diff_r)
                            
                            check.append(diff_one_row)

                            # 差分検出上限数チェック
                            if len(check) > int(dlimit):
                                # break
                                return ["Due to a number of differences、 the output could not be completed."]
                        row_number += 1
            return check

        def diff_csv_maker(diff_result):
            """
            差分取得の処理結果をもとに、コマンドとしての返却データを作成
            runfuncを使用した場合、対象のコマンドでは標準出力にcsv形式のデータを渡す必要がある。（逆に、runfuncに対して、return を通してデータを返さない）
            """
            # 出力データの列
            # output_columns = ["flow_UUID","parent_project_UUID", "date", "T/F", "diff"]
            output_columns = [  "flow_label",
                                "flow_uuid",
                                "flow_path",
                                "parent_uuid",
                                "parent_label",
                                "date",
                                ## "serial_number",
                                "point_id",
                                "test_result",
                                "raise_error",
                                "row_number",
                                "row_result",
                                "row_answer"
            ]
            output_columns = ["flow_uuid","flow_path", "parent_uuid","parent_label","date","point_id", "isTrue","diff_row_number", "diff-result", "diff-answer"]

            print(",".join(output_columns))
            # print(",".join(output_columns))

            # データ列を初期化
            flow_uuid = args["flow_uuid"]
            # parent_project_UUID = "None"
            date = "None"
            TorF = "None"
            diff = "undifined"



            import inspect
            # print(flow_data)
            # for m in inspect.getmembers(flow_data):
            #     print(m)

            # 各カラムパラメータ設定
            flow_label = args["flow_label"] # ok
            flow_uuid = args["flow_uuid"] # ok
            flow_path = None # g.factory,data.find_by_uuid (datum) -> get_current_folder_path これができない
            parent_uuid = None # flow_pathからの連携を考えている
            parent_label = None # flow_pathからの連携を考えている
            date = None # ok
            ## serial number
            point_id = None # Activity.pyから情報を取得できない、何か方法はないだろうか
            test_result = None # ok
            raise_error = None # ok
            row_number = None # ok
            row_result = None # ok
            row_answer = None # ok


            # flow_D = g.factory.data.find_by_uuid(flow_uuid)
            
            # print(type(flow_data))
            # if not isinstance(flow_data, Flow):
            #     raise Exception(f'これフローのDatumではありません')
            
            # timeの設定
            # from datetime import datetime, timezone, timedelta
            # JST = timezone(timedelta(hours=+9), 'JST')
            # date = datetime.now(JST)
            date = args['start_time']


            
            # def get_parent_path(datum_data, label_list=[]):
            #     # print(datum_data)
            #     # return datum_data.label
            #     if datum.parent_id == None:
            #         file_path = '/' + '/'.join(label_list.reverse())
            #         return file_path
            #     else:
            #         label_list.append(datum_data.label)
            #     #     parent_datum = datum_data.find_parent()
            #         get_parent_path(parent_datum.find_parent(), label_list)

            # 特急で作成した、フローのパス情報（まさかprev_parent_pathを生かせず、自分で１から作ることになるとは...）
            flow_path = "kari_path"
            datum_list = []
            datum_data = args['flow']
            while True:
                datum_list.append(datum_data)
                if datum_data.parent_id is None:
                    break
                datum_data = datum_data.find_parent()
            datum_list.reverse()
            # flow_path = '/' + '/'.join(datum_list)
            datum_path_labels = [x.label for x in datum_list]
            flow_path = '/' + '/'.join(datum_path_labels)

            # # parent_label
            parent_label = datum_list[1].label
            parent_uuid = datum_list[1].uuid

            from kskp.store import Activity
            # sq = Activity(None,None,flow_label,flow_uuid)
            # print(sq.resultsTest())
            
            point_id = args['asserted_point']


            # print(type(self.o_ports[0]))

            # flow_path = get_parent_path(args['flow'], [])
            # print(args['flow'].find_parent().find_parent().parent_id)
            
            # flow_path = str(args['flow'].get_folder_path())
            # flow_path = '/' + '/'.join([folder.get('label') for folder in args['flow'].get_folder_path()])
            # flow_path = args['flow'].get_current_folder_path(flow_uuid)

            # from kskp.store.factory import DatumFactory
            # dat = g.factory.data.find_by_uuid(flow_uuid)

            # isTrueの判定 & diffの出力
            if diff_result == [] or diff_result == None:
                isTrue = "True"
                # print("true,1,2,3,4,5")
                diff = ["nothing","nothing","nothing"]
            else:
                isTrue = "False"
                diff = diff_result

            output_datas = [flow_uuid, flow_path, parent_uuid, parent_label, str(date),point_id, isTrue]
            # with open("../../out8899998.txt", "w+")as f:
            #     for s in diff_result:
            #         f.write(",".join(output_datas).replace('\n','') + "," + ",".join(s))

            # isFirst = True

            if isinstance(diff, list):
                if isinstance(diff[0], list):
                # print(diff)
                    for output_diff in diff:
                        # if isFirst:
                        row_data = output_datas + output_diff
                        # row_data = list(','.join(row_data))
                        # print(chr(39))
                        # print(output_diff.split(chr(39)))
                        # print(",".join(row_data))
                        data_str = ",".join(map(str, row_data))
                        print(data_str)

                        # print(list(",".join(row_data).strip()))

                        # row_str = ""
                        # for s in row_data:
                        #     row_str += s
                        # print(row_str)
                        # print(''.join(row_data))

                        # print(",".join(output_datas) + "," + ",".join(output_diff))
                        #     isFirst = False
                        # else:
                        #     print(",,," + output_diff)
                else:
                    # print("str,4,3,2,1,5")
                    e = 0
                    print(",".join(map(str, output_datas)) + "," + ",".join(map(str, diff)))
            else:
                # error messsage
                output_datas.append(diff)
                print(output_datas)
                # print(",".join(map(str, row_data)))


        # print("assert開始-----\nassert\n")

        if 'i' not in inputs:
            raise Exception('AssertCommandの入力ポートiに値が入力されていません')
        if 'm' not in inputs:
            raise Exception('AssertCommandの入力ポートmに値が入力されていません')

        # if not (isinstance(inputs['i'], NysolModule) or isinstance(inputs['i'], List)):
        #     raise Exception('入力ポートiのAssertCommandの入力データ型が異なります')
        # if not (isinstance(inputs['m'], NysolModule) or isinstance(inputs['m'], List)):
        #     raise Exception('入力ポートmのAssertCommandの入力データ型が異なります')


        #inputs から一時変数に格納する
        nysol_cmd_i = inputs['i'].content
        nysol_cmd_m = inputs['m'].content
        # print("inputチェック")
        # # print(inputs['i'].content)   #<Nysol_Mfifo at 0x7f1c6df3d3c8>        
        # print(inputs['i'])# -> Datum(None, None, nm)
        # print(inputs['m'].content)   #<Nysol_Mcal at 0x7f1c6df3dd68>         
        # print(inputs['m'])# -> Datum(None, None, nm)
        # print("inputチェック")
        # print("thanks")
        # print(inputs['i'].content)
        # print(inputs['m'].content)
        # print("thanks")
        # print(args['flow_uuid'])#getできた

        # 一時ファイル作成用path
        # tmp_path_i = Path("/tmp/" + str(uuid.uuid4()) + "_i.csv")
        # tmp_path_m = Path("/tmp/" + str(uuid.uuid4()) + "_m.csv")
        tmp_path_i = Path("/tmp/" + str(1) + "_i.csv")
        tmp_path_m = Path("/tmp/" + str(1) + "_m.csv")

        # 一時ファイルを作成する
        nysol_cmd_i <<= nm.m2tee(o=tmp_path_i.as_posix())
        nysol_cmd_m <<= nm.m2tee(o=tmp_path_m.as_posix())
        
        # 一時ファイル生成までを実行する
        runs_cmd_i = RunsCommand()
        i_port_runs = runs_cmd_i.run({}, {'i':NysolModule(nysol_cmd_i)})
        # activity_cmd = ActivityCommand()
        # runs_cmd_i_append = ActivityCommand()
        # args, points = 出力ポイントのこと　これを渡す
        # s = ActivityCommand().run({}, {'i': i_port_runs})
        runs_cmd_m = RunsCommand()
        m_port_runs = runs_cmd_m.run({}, {'m':NysolModule(nysol_cmd_m)})

        print("script.py l.1275")
        print(i_port_runs)
        print(m_port_runs)
        print()


        # 比較コマンド以前のフロー実行が失敗していたら、ファイル出力がなされない
        if not (tmp_path_i.exists() and tmp_path_m.exists()):
            raise Exception('入力ファイルを一時ファイルに書き出せませんでした')
        # else:
        #     print("create temp file complete")
        #     with open(tmp_path_i.as_posix())as f:
        #         print(f.read())

        # print(args.keys())

        # print(i_port_runs['i'])
        # print(type(m_port_runs['m']))
        # print(s)
        # 比較コマンド以前のフロー実行が失敗していたら、ファイル出力がなされない
        if not tmp_path_i.exists():
            print("入力iのデータが出力されませんでした。今一度フローの構成が正しいかを確認してみてください")
            print("出力がなされなかったというデータを代わりに使用します")
            with nysol_cmd_i.open(mode="w")as f:
                f.write("flow before i_port is not working properly")


        if not tmp_path_m.exists():
            print("入力mのデータが出力されませんでした。今一度フローの構成が正しいかを確認してみてください")
            print("出力がなされなかったというデータを代わりに使用します")
            with nysol_cmd_m.open(mode="w")as f:
                f.write("flow before m_port is not working properly")



        # 作成した２ファイルから差分を算出する
        


        # diff_list = diff_check(tmp_path_i, tmp_path_m, args['dlimit'])
        new_cmd_list = None
        # new_cmd_list <<= nm.runfunc(report_diff(tmp_path_i.as_posix(), tmp_path_m.as_posix(), args['dlimit']))
            
        diff_args = {
            "dlimit" : args["dlimit"],
            "comp_path" : [tmp_path_i.as_posix(),tmp_path_m.as_posix()]
        }

        datum_list = []
        datum_data = args['flow']
        # while datum_data.parent_id is not None:
        #     datum_list.append(datum_data.label)
        #     datum_data = datum_data.find_parent()
        # file_path = '/' + '/'.join(datum_list)
        # print(file_path)

        # while True:
        #     datum_list.append(datum_data.label)
        #     if datum_data.parent_id is None:
        #         break
        #     datum_data = datum_data.find_parent()
        # file_path = '/' + '/'.join(datum_list)
        # print(file_path)


        print("check開始........！")
        new_cmd_list <<= nm.runfunc(report_diff, diff_args=diff_args)
        # new_cmd_list <<= nm.runfunc(test_py, tmp_path_i.as_posix())
        # print(new_cmd_list)
        # new_cmd_list <<= nm.cmd('diff ' + tmp_path_i.as_posix() + ' ' + tmp_path_m.as_posix())
        # new_cmd_list <<= nm.cmd('sed -e "s/,/、/g"')
        # new_cmd_list <<= nm.cmd('sed -e ":loop;N;$!b loop;s/\n/ /g"')
        # print("check")
        # print(RunsCommand().run({}, {'o':NysolModule(new_cmd_list)}))
        # print("checked")
        return {'o': NysolModule(new_cmd_list)}# PCommandの方法を参照




    
    # # def run_old(self, args, inputs):
    #     import difflib
    #     import subprocess
    #     from subprocess import PIPE
    #     def diff_check(f1, f2, dlimit=10):
    #         if dlimit == 0:
    #             path = " " + f1 + " " + f2
    #             return subprocess.Popen("diff -q" + str(path), shell=True, stdout=PIPE, stderr=PIPE)
    #         else:
    #             com_l = open(f1, "r")
    #             com_r = open(f2, "r")
                
    #             d = difflib.Differ()
    #             check = []
    #             count = 0
    #             for s,t in zip(com_l, com_r):
    #                 if s != t and count < dlimit:
    #                     check.append("\n".join(d.compare(s, t)))
    #                     count += 1
    #             com_l.close()
    #             com_r.close()
    #             return check


    #     def diff_all(f1, f2):
    #         start = time.time()

    #         path = " " + f1 + " " + f2
    #         subprocess.Popen("diff -q" + str(path), shell=True, stdout=PIPE, stderr=PIPE)
    #         # このコマンドに与えられたデータは一度ファイルに保存されて、それを読み出す形でテストを行う
    #         # saverCmd -> RunsCmd -> flow_testの入力 の流れ
    #         # dlimit = kwargs.get('dlimit')# diff-limit
    #         # dlimit = args['dlimit']
            

    #     import time
    #     tmp_path_i = "/tmp/" + str(time.time) + "_i.csv"
    #     tmp_path_m = "/tmp/" + str(time.time) + "_m.csv"
        
    #     nysol_module_i = NysolModule()
    #     runs_cmd_i = RunsCommand()

    #     #inputs から一時変数に格納する
    #     test_i = inputs['i'].content
    #     test_flow_cmds_i = None
    #     test_flow_cmds_i <<= nm.m2tee(i=test_i, o=tmp_path_i)

    #     nysol_module_i.set_content(test_flow_cmds_i)
    #     results_i = runs_cmd_i.run(args={}, inputs={'o': nysol_module_i})


    #     # print("test-12394")

    #     # print(results_i)
    #     # print(type(results_i))
    #     # print(results_i['o'])# この時点でactivityが返ってくるかは調査
    #     # print(type(results_i['o']))

    #     # print("test-12394")
    #     # print(args)
    #     # print("test-12394")

    #     #inputs から一時変数に格納する
    #     test_m = inputs['m'].content
    #     test_flow_cmds_m = None
    #     test_flow_cmds_m <<= nm.m2tee(i=test_m, o=tmp_path_m)

    #     nysol_module_m = NysolModule()
    #     runs_cmd_m = RunsCommand()
    #     nysol_module_m.set_content(test_flow_cmds_m)

    #     results_m = runs_cmd_m.run(args={}, inputs={'': nysol_module_m})
    #     return results_m
    #     # results = saver_cmd.run(args={}, inputs={'i':test_flow_cmds, 'store'})#inputs['i']=nysol_module()?
    #     # results_m
    #     # nysol_module_diff = NysolModule()
    #     new_cmd_list = None
    #     # diff_list = diff_check(tmp_path_i, tmp_path_m, args['dlimit'])
    #     new_cmd_list <<= nm.runfunc(diff_check(tmp_path_i, tmp_path_m, args['dlimit']))

    #     nysol_mod = NysolModule()
    #     return {'o': nysol_mod.set_content(new_cmd_list)}# PCommandの方法を参照
    
    # def run(self, args, inputs):
        
    #     import time
        
    #     nysol_module_i = NysolModule()
    #     runs_cmd = RunsCommand()

    #     #inputs から一時変数に格納する
    #     test_flow_cmds = args.copy()
    #     test_flow_cmds['i']  = inputs['i'].content
    #     tmp_path_i = "/tmp/" + str(time.time) + "_i.csv"
    #     test_flow_cmds <<= nm.m2tee(o=tmp_path_i)

    #     # nysol_module_i.set_content(test_flow_cmds_i)
    #     # results_i = runs_cmd.run(args={}, inputs={'i': nysol_module_i})

    #     #inputs から一時変数に格納する
    #     test_flow_cmds['m'] = inputs['m'].content
    #     tmp_path_m = "/tmp/" + str(time.time) + "_m.csv"
    #     test_flow_cmds <<= nm.m2tee(o=tmp_path_m)

    #     # nysol_module_m = NysolModule()
    #     # nysol_module_m.set_content(test_flow_cmds_m)

    #     # results_m = runs_cmd.run(args={}, inputs={'m': nysol_module_m})
    #     test_flow_cmds <<= nm.runfunc(self.diff_check(tmp_path_i, tmp_path_m, args['dlimit']))
    #     nysol_mod = NysolModule()
    #     return {'o': nysol_mod.set_content(test_flow_cmds)}# PCommandの方法を参照
    

    

    
    # def run(self, args, inputs):
    #     import difflib
    #     import subprocess
    #     from subprocess import PIPE
    #     def diff_check(f1, f2, dlimit=10):
    #         if dlimit == 0:
    #             path = " " + f1 + " " + f2
    #             return subprocess.Popen("diff -q" + str(path), shell=True, stdout=PIPE, stderr=PIPE)
    #         else:
    #             com_l = open(f1, "r")
    #             com_r = open(f2, "r")
                
    #             d = difflib.Differ()
    #             check = []
    #             count = 0
    #             for s,t in zip(com_l, com_r):
    #                 if s != t and count < dlimit:
    #                     check.append("\n".join(d.compare(s, t)))
    #                     count += 1
    #             com_l.close()
    #             com_r.close()
    #             return check


    #     def diff_all(f1, f2):
    #         start = time.time()

    #         path = " " + f1 + " " + f2
    #         subprocess.Popen("diff -q" + str(path), shell=True, stdout=PIPE, stderr=PIPE)
    #         # このコマンドに与えられたデータは一度ファイルに保存されて、それを読み出す形でテストを行う
    #         # saverCmd -> RunsCmd -> flow_testの入力 の流れ
    #         # dlimit = kwargs.get('dlimit')# diff-limit
    #         # dlimit = args['dlimit']
            

    #     import time
    #     tmp_path_i = "/tmp/" + str(time.time) + "_i.csv"
    #     tmp_path_m = "/tmp/" + str(time.time) + "_m.csv"
        
    #     nysol_module_i = NysolModule()
    #     runs_cmd_i = RunsCommand()

    #     #inputs から一時変数に格納する
    #     test_i = inputs['i'].content
    #     test_flow_cmds_i = None
    #     test_flow_cmds_i <<= nm.m2tee(i=test_i, o=tmp_path_i)

    #     nysol_module_i.set_content(test_flow_cmds_i)
    #     results_i = runs_cmd_i.run(args={}, inputs={'o': nysol_module_i})


    #     # print("test-12394")

    #     # print(results_i)
    #     # print(type(results_i))
    #     # print(results_i['o'])# この時点でactivityが返ってくるかは調査
    #     # print(type(results_i['o']))

    #     # print("test-12394")
    #     # print(args)
    #     # print("test-12394")

    #     #inputs から一時変数に格納する
    #     test_m = inputs['m'].content
    #     test_flow_cmds_m = None
    #     test_flow_cmds_m <<= nm.m2tee(i=test_m, o=tmp_path_m)

    #     nysol_module_m = NysolModule()
    #     runs_cmd_m = RunsCommand()
    #     nysol_module_m.set_content(test_flow_cmds_m)

    #     results_m = runs_cmd_m.run(args={}, inputs={'': nysol_module_m})
    #     # results = saver_cmd.run(args={}, inputs={'i':test_flow_cmds, 'store'})#inputs['i']=nysol_module()?
    #     # results_m
    #     # nysol_module_diff = NysolModule()
    #     new_cmd_list = None
    #     # diff_list = diff_check(tmp_path_i, tmp_path_m, args['dlimit'])
    #     new_cmd_list <<= nm.runfunc(diff_check(tmp_path_i, tmp_path_m, args['dlimit']))

    #     # sss = '"diff ' + str(tmp_path_i) + " " + str(tmp_path_m)
    #     # new_cmd_list <<= nm.cmd(sss)

    #     # for input_data in ['i', 'm']:
    #     #     # ファイルのsaveを行う
    #     #     save_cmd = SaverCommand()#instance
    #     #     run_cmd = RunsCommand()
    #     #     #save, return{'o': nysol_module}
    #     #     nysol_module = nysolModule()
    #     #     nysol_module <<= saverCommand()


    #     #     cmd_o[input_data] <<= save_cmd.run(args, inputs)
    #     #     cmd_o[input_data] <<= run_cmd.run(args, inputs)

    #     #     # save_cmd.run(args, inputs[input_data].content)
    #     #     # run_cmd.run(args, inputs[input_data].content)


    #     #     # 将来的に、入力にはactivityの情報が渡される
    #     #     my_args = args.copy()
    #     #     my_args['i'] = inputs['i'].activity.path # 仮の記述、未実装
        

    #     # ここから比較の動作定義

    #     # 結果が出たら、一時書き出したファイルの削除を行う
    #     # del(i_path)
    #     nysol_mod = NysolModule()
    #     return {'o': nysol_mod.set_content(new_cmd_list)}# PCommandの方法を参照
    