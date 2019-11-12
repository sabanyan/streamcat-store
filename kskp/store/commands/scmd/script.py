# Store用コマンド
import os
import sys
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
        self.o_ports = [Port('o', 'mcmd'), Port('u', 'frame')]
        self.frame = None
        self.start_time = None

    def run(self, args, inputs):
        # Frameを作成する
        store = inputs['store']
        flow_label = args['flow_label']
        point = args['point']
        point_label = point.label if point.label is not None else point.id
        self.start_time = args['start_time']

        # UTC日時はここで現地時間(環境変数TZの値)に設定される
        start_time = self.start_time.astimezone()
        start_time_str1 = start_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        start_time_str2 = start_time.strftime('%Y%m%d.%H%M%S.%f')[:-3]
        folder = self.make_folder(store, flow_label, start_time_str1, start_time_str2)
        self.frame = self.make_frame(folder, point_label + '.csv')
        # ラベル名とファイル名はコンストラクタで別々に指定できるようにすれば
        # 改めてupdate_label_only()を行う必要はなくなる
        # もしくは、実行ログ一覧画面さえできれば別々に指定する必要もなくなるか？
        Frame.update_label_only(self.frame.uuid, point_label, None)

        # 1. storeにsaveする
        datum_module = folder.save_frame(self, args, inputs['i'], point_label + '.csv') 
        # 2. lasts用なのでコマンド実行のrunをする（繋げる必要はない）
        # result = datum_module.run(msg='on')

        self.frame.set_centext(args)
        self.frame.set_content(datum_module)

        return {'o': self.frame, 'u': self.frame.uuid}
        # TODO: FrameModuleを葬るためには、RunsCommandの後にSaverを付加するように変更する必要があるだろう
        # return {'o': datum_module, 'u': self.frame.uuid}

    def module(self, args, input):
        command_args = {}
        command_args['i'] = input
        command_args['o'] = args['frame_path'].as_posix()
        # return nm.m2tee(command_args)
        return nm.writecsv(command_args)

    def make_folder(self, store, folder1_label, folder2_label, folder2_file_name):
        from kskp.store import Datum, AwsS3

        # フロー名フォルダがなければ作成する
        results1 = Datum.find_by_parent_uuid_and_label(store.uuid, folder1_label)
        if results1 is None or len(results1)==0:
            folder1 = Folder(store.uuid, folder1_label, None)
            folder1.save()
        else:
            folder1 = results1[0]

        # 開始時間フォルダがなければ作成する
        results2 = Datum.find_by_parent_uuid_and_label(folder1.uuid, folder2_label)
        if results2 is None or len(results2)==0:
            folder2 = Folder(folder1.uuid, folder2_label, None)
            folder2.path = folder2.path.parent / folder2_file_name
            folder2.save()
        else:
            if results2[0].type == Datum.FOLDER_TYPE:
                folder2 = Folder.convert_to_folder(results2[0])
            elif results2[0].type == Datum.AWSS3_TYPE:
                folder2 = AwsS3.convert_to_awss3(results2[0])
            else:
                # 開始時間フォルダを作成できなかった場合はフロー名フォルダ直下に結果を作成する
                folder2 = folder1

        return folder2

    def make_frame(self, store, label):
        import io
        f = io.BytesIO(b'')
        self.frame = Frame(store.uuid, label, f)
        # RunsCommandの実行前にFrameを登録する
        self.frame.save()
        return self.frame

    def dtor(self):
        if self.frame is None:
            return
        # 出力フレームのラベルに終了時刻と所要時間を付加する
        from datetime import datetime, timezone
        end_time = datetime.utcnow().replace(tzinfo=timezone.utc)
        end_time_str = end_time.astimezone().strftime('%H:%M:%S')
        new_label = self.frame.label + ' 終了時刻' + end_time_str
        if self.start_time is not None:
            elapsed_time = (end_time - self.start_time).total_seconds()
            if elapsed_time < 60.0:
                elapsed_time_str = str(round(elapsed_time))
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

    def run(self, args, inputs):
        store = inputs['store']
        flow_label = args['flow_label']
        point = args['point']
        point_label = point.label if point.label is not None else point.id
        self.start_time = args['start_time']

        # UTC日時はここで現地時間(環境変数TZの値)に設定される
        start_time = self.start_time.astimezone()
        start_time_str = start_time.strftime('%Y%m%d.%H%M%S.%f')[:-3]
        
        # ラベル名を作成する
        cache_label = flow_label + '_' + point_label + '_' + start_time_str
        # Nysolの oオプションに空白のファイル名があるとエラーになるので、空白を置換する
        cache_label = cache_label.replace(' ', '_')

        # Cacheフレームを作成する
        self.frame = self.make_frame(store, cache_label)

        # 1. storeにsaveする
        datum_module = store.save_frame(self, args, inputs['i'], cache_label + '.csv') 

        self.frame.set_centext(args)
        self.frame.set_content(datum_module)

        # FlowのキャッシュUUIDを変更する
        # frame.set_centext(args)の後で行う必要がある
        self.frame.update_flow(modifier=None)

        return {'o': self.frame}

    def make_frame(self, store, label):
        import io
        f = io.BytesIO(b'')
        self.frame = Cache(store.uuid, label, f)
        # RunsCommandの実行前にFrameを登録する
        self.frame.save()
        return self.frame

    def dtor(self):
        pass

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

    def run(self, args, inputs):
        DbLoaderCommand._write_log('START')

        from kskp.store import Datum, Database
        if inputs['i'].type != Datum.DATABASE_TYPE:
            t = type(inputs['i'])
            raise Exception(f'DbLoaderの入力にDatabase Store以外のデータ型({t})が入力されました')
        else:
            database = Database.convert_to_database(inputs['i'])

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
        db_uri = database.conn.get_database_uri()

        # SQL文を作成する
        sql = DbLoaderCommand._make_sql(schema_name, table_name)

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


class DbSaverCommand(Command):
    """
    指定したDBへデータを格納するSaverコマンド
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame'), Port('store', 'store')]
        self.o_ports = [Port('o', 'mcmd')]
        self._tmp_file_path = None

    def run(self, args, inputs):
        DbSaverCommand._write_log('START')

        from kskp.store import Datum, Database
        if inputs['store'].type != Datum.DATABASE_TYPE:
            t = type(inputs['store'])
            raise Exception(f'DbSaverの入力にDatabase Store以外のデータ型({t})が入力されました')
        else:
            database = Database.convert_to_database(inputs['store'])

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
        cmd = inputs['i']
        cmd <<= nm.runfunc(bulk_inserter, database=database, schema_name=schema_name, table_name=table_name)

        # 結果はFrameに入れて返す
        from kskp.store import Frame
        frame = Frame(None, 'db_saver', None)
        frame.set_centext(args)
        frame.set_content(cmd)

        return {'o': frame}  
        
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
                column_defs += f',"{column}" VARCHAR2(4000 BYTE)'
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
                cursor.copy_from(csv_input, schema_and_table_name, sep=',', null=r'', size=8192, columns=csv_columns)       

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
    def _save_as_data_source(database, label):
        from kskp.store import Flow
        pass

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

class RunsCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('*', 'mcmd')]
        self.o_ports = [Port('*', 'datum?')]

    def run(self, args, inputs):

        nm_list = []
        for nysol_module in inputs.values():
            nm_list.append(nysol_module)

        # NYSOL Pythonを実行する
        import nysol.mcmd as nm
        # results = nm_list[0].drawModelD3("autoadd_list.html")
        results = nm.runs(nm_list, msg='on')

        if len(results) != len(inputs):
            raise Exception('RunsCommandの入力ポートと出力ポートの数が異なります')

        # resultsの要素はnm_listへのappend順に対応している?ため
        # 入力ポートと出力ポートは同じキーで対応付ける
        i = 0
        ret = {}
        for i_port_name in inputs.keys():
            ret[i_port_name] = results[i]
            i += 1

        return ret

from kskp.store import Activity

class ActivityCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('*', 'datum')]
        self.o_ports = [Port('o', 'activity')]
        self.activity = None

    def run(self, args, inputs):
        # raise Exception('activity RUN!')

        if self.activity is None:
            flow_uuid = args['flow_uuid']
            self.activity = Activity(None, 'activity', flow_uuid)

        for port_id, datum in inputs.items():
            point = args['points'][port_id]
            self.activity.add(point, datum)

        return {'o': self.activity}

