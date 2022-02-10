# Store用コマンド
import os
import sys
import nysol.mcmd as nm
from kskp.core import Datum, Command, Port
from kskp.store import NysolModule, Store

class SCommand(Command):
    pass

# 1つ保存のsaverはどうなる？
# 普通なら、inputsできたものをargs情報を使って保存か
class LoaderCommand(SCommand):
    """
    指定したstoreからデータを取ってくる（テスト用）
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('folder', 'store')]
        self.o_ports = [Port('o', 'mcmd')]
        self.name = 'loader'

    def run(self, args, inputs):
        # ファイルパスと文字コードを取得する
        path, encoding = self._get_frame(args)

        cmd = nm.m2tee(i=path)
        # mreadで存在しないファイルパスを指定するとDockerごと落ちる -> 0.3.10で修正済
        # mreadは巨大ファイルの読み込みが遅い(全行入力してる?)
        # cmd = nm.mread({'i':path, 'n':65535})
        nysol_module = NysolModule(cmd)
        # frameの文字コードを次のコマンドに渡す
        nysol_module.encoding = encoding
        return {'o': nysol_module}

    def _get_frame(self, args):
        datum_factory = args['datum_factory']

        # 指定したuuidのframeを取得する
        frame_uuid = args['uuid']
        if frame_uuid is None or frame_uuid=='':
            raise Exception('入力ファイルを指定してください')
        # frame = folder.find_child_by_uuid(frame_uuid)
        frame = datum_factory.find_by_uuid(frame_uuid, type=Datum.FRAME_TYPE)
        path = frame.path.as_posix()

        if frame.encoding is None:
            from kskp.store import Frame
            # frameの文字コードが未判定の場合はここで判定する
            with open(path, 'rb') as f:
                encoding = Frame._detect_encoding(f)
        else:
            # frameの文字コードを取得する
            encoding = frame.encoding

        # ファイルパスと文字コードを返す
        return path, encoding

class SaverCommand(SCommand):
    """
    指定されているstoreに出力するコマンド（テスト用）
    基本的にはlastsを保存するためにある
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame'), Port('folder', 'store')]
        self.o_ports = [Port('o', 'mcmd')]
        self.name = 'saver'

    def run(self, args, inputs):
        # Frameを作成する
        folder = self.get_result_folder(args)
        flow_label = args['flow_label']
        start_at = args['start_at']

        point = args.get('point')
        if point is None:
            point_label = self.get_label(args.get('src_point'))
        else:
            point_label = point.label if point.label is not None else point.id

        # UTC日時はここで現地時間(環境変数TZの値)に設定される
        start_at = start_at.astimezone()
        start_at_str1 = start_at.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        start_at_str2 = start_at.strftime('%Y%m%d.%H%M%S.%f')[:-3]
        sub_folder = self.make_folder(folder, flow_label, start_at_str1, start_at_str2)
        frame = self.make_frame(sub_folder, point_label)
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

    def get_result_folder(self, args):
        # 
        # NOTE: ライブラリの出力結果フォルダは、argsで貰うこととする
        # 
        # ・出力結果フォルダは実行フローと同じ階層のフォルダとしているが、
        #   フローJSONにフォルダの相対パスを指定する記法がない(uuidの指定しかできない)
        # ・SaverCommandのinputsを実行時に決定するには、SaverCommandにIn指定のポイントを繋げることになるが
        #   データデストに対して、実行結果フォルダStoreを取得するデータデストを指定することになってしまう
        # ・出力結果フォルダのuuidは実行時に決定される値なので、出力結果フォルダをSaverCommandの引数指定することとした
        #
        from kskp.store import Folder
        if 'result_folder' not in args:
            class_name = self.__class__.__name__
            raise Exception(f'{class_name}の引数(args)にresult_folderキーが存在しません')
        elif not isinstance(args['result_folder'], Folder):
            t = type(args['result_folder'])
            class_name = self.__class__.__name__
            raise Exception(f'{class_name}の引数(args)にFolder以外のデータ型({t})が入力されました')
        # Folderオブジェクトを返す
        return args['result_folder']

    def get_label(self, point):
        """
        出力ファイルのラベルを取得する
        """
        if point is None:
            return ''
        else:
            return point.label or point.id

    def append_writecsv_cmd(self, cmd, frame_path):
        abs_frame_path = frame_path.as_posix()
        # リストが渡されても処理できるようi=に入力値を渡している
        # writecsvは0Byteデータが入力されるとエラーになるのでm2teeを使う
        return nm.m2tee(i=cmd, o=abs_frame_path)

    def make_folder(self, parent, folder1_label, folder2_label, folder2_file_name):
        # フロー名フォルダがなければ作成する
        results1 = parent.find_children_by_label(folder1_label, type=Datum.FOLDER_TYPE)
        if results1 is None or len(results1)==0:
            folder1 = parent.create_folder(folder1_label)
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

    def make_frame(self, parent, label):
        import io
        f = io.BytesIO(b'')
        frame = parent.create_frame(label, f)
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
        self.o_ports = [Port('o', 'mcmd'), Port('u', 'frame')]

    def run(self, args, inputs):
        import warnings
        from kskp.store import ApparentOut
        from kskp.store.lock import LockedDatumException
        from kskp.store.auth import NotAuthorizedException

        folder = self.get_result_folder(args)
        flow = args['flow']
        flow_label = args['flow_label']
        point = args['point']
        point_label = point.label if point.label is not None else point.id
        start_at = args['start_at']

        # UTC日時はここで現地時間(環境変数TZの値)に設定される
        start_at = start_at.astimezone()
        start_at_str = start_at.strftime('%Y%m%d.%H%M%S.%f')[:-3]
        
        # ラベル名を作成する
        cache_label = flow_label + '_' + point_label + '_' + start_at_str
        # Nysolの oオプションに空白のファイル名があるとエラーになるので、空白を置換する
        cache_label = cache_label.replace(' ', '_')

        # FlowのキャッシュUUIDを変更する
        # テスト実行の場合は実行するFlowをDBに保存していない
        if flow.writable:
            node_id = args['point_id']
            lock_uuid = args['lock_uuid']
            # Cacheフレームを作成する
            cache = self.make_frame(folder, cache_label)
            try:
                flow.set_cache(node_id, cache, lock_uuid=lock_uuid)
            except (LockedDatumException, NotAuthorizedException) as e:
                # フローにキャッシュのUUIDを書き込めなくてもフローの実行は中断しない
                warnings.warn(str(e) + '、キャッシュは作成できませんでした')
                # 作成したCacheを削除する
                cache.writable and cache.delete()
                cache = None
        else:
            warnings.warn(f'フロー({flow.label})の更新権限が無いため、キャッシュは作成できませんでした.')
            cache = None

        # NYSOLコマンドを作成する
        cmd = inputs['i'].content
        if cache is not None:
            cmd = self.append_writecsv_cmd(cmd, cache.path)
        # 出力フレームをRunsCommandに渡す
        nysol_module = NysolModule(cmd)
        nysol_module.context['frame'] = cache

        # 出力Port(u)はActivityコマンドに繋げてCacheフレームを渡す
        return {'o': nysol_module, 'u': ApparentOut(point, cache)}

    def make_frame(self, parent, label):
        import io
        f = io.BytesIO(b'')
        cache = parent.create_cache(label, f)
        # RunsCommandの実行前にCacheを登録する
        cache.save()
        cache = cache.reload()
        # FrameとCacheを区別するためのフラグ
        cache.is_cache = True
        return cache


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

        from kskp.core import Datum
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
                        print(','.join(result._fields))
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
                    print(f'#ERROR# {str(e)}; DbLoaderCommand; ; ; ', file=fpe)
                raise e

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
        from sqlalchemy import exc
        from sqlalchemy import text
        # 時間計測開始
        import time
        t1 = time.time()

        # if dbms.upper() != 'ORACLE':
        #     try:
        #         engine.execute('BEGIN')
        #     except exc.SQLAlchemyError as e:
        #         engine.execute('ROLLBACK')
        #         raise Exception('トランザクションの開始に失敗しました(%s)' % str(e))

        # try:
        #     results = engine.execute(sql)
        # except exc.SQLAlchemyError as e:
        #     engine.execute('ROLLBACK')
        #     raise Exception('SQLの実行に失敗しました %s' % sql)
        # finally:
        #     engine.execute('COMMIT')

        try:
            with engine.begin() as conn:
                results = conn.execute(text(sql))
        except exc.SQLAlchemyError as e:
            raise Exception('SQLの実行に失敗しました %s' % sql)

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

    def dtor(self, args):
        DbLoaderCommand._write_log('DTOR!')

class DbSaverCommand(SaverCommand):
    """
    指定したDBへデータを格納するSaverコマンド
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', ['mcmd','matrix']), Port('store', 'store')]
        self.o_ports = [Port('o', 'mcmd')]
        self.name = 'db_saver'

    def run(self, args, inputs):
        DbSaverCommand._write_log('START')

        from kskp.core import Datum
        if inputs['store'].type != Datum.DATABASE_TYPE:
            t = type(inputs['store'])
            raise Exception(f'DbSaverの入力にDatabase Store以外のデータ型({t})が入力されました')
        else:
            database = inputs['store']

        # DataSourceを保存するフォルダを取得する
        folder = self.get_result_folder(args)

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

        # 指定されたテーブルがデータを格納可能か判定する → どうやって？
        # (所定の列が存在して、それら列が所定の順序に並んでいて、、)

        def bulk_inserter(database_conn, schema_name, table_name):
            engine = None
            try:
                # DBへ接続する
                db_uri = database_conn['database_uri']
                engine = DbSaverCommand._connect_to_db(db_uri)

                # CSVのヘッダ行を取得する
                csv_columns = DbSaverCommand._get_csv_column_names(sys.stdin)

                # インポート先テーブルが無ければ作成する
                if not DbSaverCommand._table_exists(engine, schema_name, table_name):
                    DbSaverCommand._create_table(engine, database_conn['dbms'], schema_name, table_name, csv_columns)

                # CSVデータのインポートコマンドを発行する
                DbSaverCommand._import_to_table(database_conn, schema_name, table_name, csv_columns, sys.stdin)
            except Exception as e:
                with open('/dev/stderr', 'w') as fpe:
                    import traceback
                    traceback.print_exc(file=fpe)
                    print(f'#ERROR# {str(e)}; DbSaverCommand; ; ; ', file=fpe)
                raise e
            finally:
                engine and engine.dispose()

        # flushをしないと、デバッグ用のprintなども入ってしまう
        sys.stdout.flush()

        # runfuncに渡す引数の値はcopy.deepcopy()されるため
        # deepcopyできないdatabase.connをdict型に変換する
        database_conn = database.conn.to_json()
        database_conn['database_uri'] = database.conn.get_database_uri()

        # Nysol Pythonのrunfunc関数を作成する
        cmd = nm.msetstr(v=args['activity_uuid'], a='activity_uuid_kskp', i=inputs['i'].content)
        cmd <<= nm.runfunc(bulk_inserter, database_conn=database_conn, schema_name=schema_name, table_name=table_name)

        # DataSourceを保存するフォルダを用意する
        flow_label = args['flow_label']
        start_at = args['start_at'].astimezone()
        start_at_str1 = start_at.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        start_at_str2 = start_at.strftime('%Y%m%d.%H%M%S.%f')[:-3]
        result_folder = self.make_folder(folder, flow_label, start_at_str1, start_at_str2)

        # 出力結果を取得するDataSourceをライブラリに登録する
        label = self.get_label(args.get('src_point'))
        datasource = self._create_data_source(result_folder, database, label, schema_name, table_name, args['activity_uuid'])
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
                # PostgreSQLでは列名に%を含められないようだ
                return [name.replace('%','÷') for name in csv_column_names]

    @staticmethod
    def _get_csv_reader(f):
        for csv_data in f:
            import csv
            csv_data = csv.reader(csv.StringIO(csv_data), delimiter=',', quotechar='"')
            for csv_values in csv_data:
                yield csv_values

    @staticmethod
    def _table_exists(engine, schema_name, table_name):
        from sqlalchemy import inspect
        inspector = inspect(engine)
        if schema_name == '':
            return inspector.has_table(table_name)
        else:
            return inspector.has_table(table_name, schema=schema_name)

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
        CREATE TABLE IF NOT EXISTS {schema_and_table_name} (
            {column_defs}
        )
        """
        if dbms.upper() != 'ORACLE':
            creata_table += ';'
        from sqlalchemy import DDL, exc
        try:
            with engine.begin() as conn:
                conn.execute(DDL(creata_table))
        except exc.IntegrityError as e:
            # 同時に同じ名称のテーブルを作成するとUniqueViolationの例外が送出される
            # テーブル作成が完了すれば、他の接続での作成が失敗しても問題ではないので、例外を無視する
            # PostgreSQLのSequenceはCSVのインポート処理などに置いて同期できないことが関係している?
            # https://stackoverflow.com/questions/4448340/postgresql-duplicate-key-violates-unique-constraint
            import psycopg2
            if dbms.upper() == 'POSTGRESQL' and isinstance(e.__cause__, psycopg2.errors.UniqueViolation):
                pass
            else:
                raise e
        except exc.SQLAlchemyError as e:
            raise Exception(f'DBのテーブル作成に失敗しました({str(e)})')

    @staticmethod
    def _import_to_table(database_conn, schema_name, table_name, csv_columns, csv_input):
        try:
            if database_conn['dbms'].upper() == 'POSTGRESQL':
                db_uri = database_conn['database_uri']
                DbSaverCommand._import_to_table_postgresql(db_uri, schema_name, table_name, csv_columns, csv_input)
            elif database_conn['dbms'].upper() == 'ORACLE':
                DbSaverCommand._import_to_table_oracle(database_conn, schema_name, table_name, csv_columns, csv_input)
            else:
                raise Exception('DBのインポート先DBMS種別が判定できませんでした')
        except Exception as e:
            raise Exception(f'DBのテーブルへのインポートに失敗しました({str(e)})')

    @staticmethod
    def _import_to_table_postgresql(db_uri, schema_name, table_name, csv_columns, csv_input):
        schema_and_table_name = schema_name + '.' + table_name if schema_name != '' else table_name

        # psycopg2からはCOPY文を発行できないようである
        import psycopg2
        with psycopg2.connect(db_uri) as conn:
            with conn.cursor() as cursor:
                # 指定する列名を".."でエスケープする
                column_name_list = '"' + '","'.join(csv_columns) + '"'
                sql = f'COPY {schema_and_table_name} ({column_name_list}) FROM STDIN WITH CSV HEADER'
                cursor.copy_expert(sql, sys.stdin, size=8192)

        # 入力データを標準入力へ渡す
        for line in csv_input:
            print(line)
        # 入力データの終わりを告げる
        print(r'\.', end='')

    @staticmethod
    def _import_to_table_oracle(database_conn, schema_name, table_name, csv_columns, csv_input):
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

        user_id = database_conn['userId']
        password = database_conn['password']
        dsnStr = cx_Oracle.makedsn(database_conn['hostname'], database_conn['port'], database_conn['database'])
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
        from kskp.depo.std.commands import CommandLink
        args = {'schema_name':schema_name, 'table_name':table_name, 'activity_uuid_kskp':activity_uuid}
        loader_cmd = CommandLink('db_loader').resolve()
        return parent.create_datasource(label, database, loader_cmd, args)

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

    def dtor(self, args):
        DbSaverCommand._write_log('DTOR!')


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
        from kskp.core import Datum
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
        self.i_ports = [Port('i', 'frame'), Port('store', 'store')]
        self.o_ports = [Port('o', 'mcmd')]
        self.name = 'remotefolder_saver'

    def run(self, args, inputs):
        from kskp.core import Datum
        if inputs['store'].type != Datum.RFOLDER_TYPE:
            t = type(inputs['store'])
            raise Exception(f'RemoteFolderSaverの入力にRemoteFolderStore以外のデータ型({t})が入力されました')
        else:
            rfolder = inputs['store']

        # DataSourceを保存するフォルダを取得する
        folder = self.get_result_folder(args)

        # 接続情報に漏れがないか確認し、漏れがあれば例外を送出する
        rfolder.valid_or_raise()

        # ファイル名を取得する
        if 'dir_path' not in args:
            raise Exception('リモートフォルダ接続の格納先ディレクトリ名が必要です')
        dir_path = args['dir_path']

        # 出力ファイルパスを作成する
        label = self.get_label(args.get('src_point'))
        file_path = rfolder.path / dir_path.strip('/') / label
        file_path = Datum.make_unique_path(file_path)
        path_str = file_path.as_posix()

        # Nysol Python
        cmd = inputs['i'].content
        cmd <<= nm.m2tee(o=path_str)

        # NYSOL-Pythonの=oオプションはファイルは作成するが、ディレクトリは作成しない
        # そのため、NYSOL-Pythonの実行前にディレクトリを作成する必要がある
        # (なお、runfuncの実行時点で作成してもエラーになった)
        self._make_dir(file_path.parent)

        # DataSourceを保存するフォルダを用意する
        flow_label = args['flow_label']
        start_at = args['start_at'].astimezone()
        start_at_str1 = start_at.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        start_at_str2 = start_at.strftime('%Y%m%d.%H%M%S.%f')[:-3]
        result_folder = self.make_folder(folder, flow_label, start_at_str1, start_at_str2)

        # 出力結果を取得するDataSourceをライブラリに登録する
        datasource = self._create_data_source(result_folder, rfolder, label, path_str)
        datasource.save()

        # 出力DataSourceをRunsCommandに渡す
        nysol_module = NysolModule(cmd)
        nysol_module.context['frame'] = datasource

        return {'o': nysol_module}  

    @staticmethod
    def _make_dir(path):
        """
        ディレクトリを作成する
        """
        try:
            # ディレクトリ(path列で指定されるディレクトリ)がなければ作成する
            if not path.is_dir():
                os.makedirs(path, exist_ok=True)
            return path
        except PermissionError as e:
            # ファイルに対する権限がない場合
            raise e

    @staticmethod
    def _create_data_source(parent, rfolder, label, file_path_str):
        from kskp.depo.std.commands import CommandLink
        args = {'file_path':file_path_str}
        loader_cmd = CommandLink('remotefolder_loader').resolve()
        return parent.create_datasource(label, rfolder, loader_cmd, args)



class ContinuousLoaderCommand(SCommand):
    """
    指定したファイルから入力データを待ち受ける
    """
    def __init__(self):
        super().__init__()
        self.i_ports = []
        self.o_ports = [Port('o', 'mcmd')]
        self.name = 'cloader'

    def run(self, args, inputs):
        # オプション指定されたファイルパスを取得する
        file_path = args.get('file_path')
        if file_path is None:
            raise Exception('file_pathがNoneです')
 
        # tail -f コマンドでファイルから入力を待ち受ける
        cmd = nm.cmd(f'tail -n 20000 -f {file_path}')

        return {'o': NysolModule(cmd)}

class RunsCommand(SCommand):

    # 最低必要ディスクサイズ(1Mbyte)
    MIN_REQUIRED_DISK_SIZE = 1024 * 1024

    # 環境変数からPythonの再帰呼び出しの制限回数を取得する
    RECURSION_LIMIT = int(os.getenv('STREAMCAT_NYSOL_RECURSION_LIMIT', 2**20))

    def __init__(self):
        super().__init__()
        self.i_ports = [Port('*', 'mcmd')]
        self.o_ports = [Port('*', 'out')]

    def run_nysol(self, nm_list):
        # NYSOL Pythonを実行する
        ret = nm.runs(nm_list, msg='on', throwexc=True)
        return ret

    def run(self, args, inputs):
        import psutil
        from multiprocessing import Process, Manager, Pipe
        from kskp.store import Matrix, ApparentOut, CommandException

        def do_runs(nm_list, results, exs, out):
            """
            NYSOL Pythonを実行する
            """
            try:
                # NYSOL-Pythonは、処理フローのグラフを組み立てる時と、処理メソッドをスケジューリングする時に
                # 再帰呼び出しの制限回数がPythonの初期制限値を超えるので、ここで制限値を上げる
                # (サブプロセスの制限回数を上げても親プロセスの制限回数は変わらない)
                sys.setrecursionlimit(self.RECURSION_LIMIT)

                # multiprocessing.Processで閉じられる標準入力を開き直す
                sys.stdin = open(0, closefd=False)

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

        # 
        # CommandExceptionが1つでも入力された場合は処理を中断する
        # (例外が入力されたら対応する出力ポートに渡す)
        # 
        rets = {}
        exception_exists = False
        for i_port_name, input in inputs.items():
            if isinstance(input, CommandException):
                rets[i_port_name] = ApparentOut(None, None, [input])
                exception_exists = True
            elif isinstance(input, (NysolModule, Matrix)):
                rets[i_port_name] = ApparentOut(None, input.context.get('frame'))
            else:
                raise Exception(f'RunsCommandにNysolModuleまたはCommandException以外のデータ型({input})が入力されました')

        if exception_exists:
            # ActivityCommandにSaverが生成したFrameと例外を渡す
            return rets

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
            rets = {}
            for i_port_name, nysol_module in inputs.items():
                # プレビューの場合はframe=Noneである
                frame = nysol_module.context.get('frame')
                if len(exs_list) == 0:
                    matrix = Matrix(results[i])
                    rets[i_port_name] = ApparentOut(None, frame or matrix)
                else:
                    rets[i_port_name] = ApparentOut(None, frame, exs=exs_list)
                i += 1

            return rets

class FieldNamesCommand(RunsCommand):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('*', 'mcmd')]
        self.o_ports = [Port('*', 'out')]

    def run_nysol(self, nm_list):
        ret = []
        for nm_flow in nm_list:
            # ヘッダ行の取得を実行する
            ret.append(nm_flow.fldname())
        return ret

class ActivityCommand(SCommand):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('*', 'out')]
        self.o_ports = [Port('o', 'activity')]

    def run(self, args, inputs):
        from kskp.store import ApparentOut
        from kskp.store import CommandException

        activity = args['activity']
        points = args['points']
        is_vis = args['is_vis']

        for port_id, input in inputs.items():
            # 出力ポイント
            out_point = points[port_id]

            if isinstance(input, CommandException):
                # RunsCommandの前のコマンドで例外が送出された場合はframeは生成されない
                out = ApparentOut(out_point, None, [input])
            elif isinstance(input, ApparentOut):
                out = input
                out.out_point = out_point
            else:
                raise Exception(f'ActivityCommandにApparentLastまたはCommandException以外のデータ型({input})が入力されました')

            # Activityにoutを追加する
            activity.add(out)

        if activity.count_outs() == len(points):
            # プレビュー実行以外の場合
            # Activityを全て集め終えたら実行結果情報を保存する
            # (今は出力ファイル名にその情報を刻んでいる)
            not is_vis and activity.save()
            # Activityを出力Pointに渡し、処理を終了する
            return {'o': activity}
        else:
            # Noneを渡して、再びrun()を実行してもらう
            return {'o': None}

    def dtor(self, args):
        activity = args['activity']

        # フローの実行に成功した場合は、何もしない
        if activity.is_success:
            return

        # フローの実行に失敗した場合は、ここでSaverが出力したファイルを削除する
        # (本当はSaver自身が削除すべきだが、Saverは作成したファイルを自身で覚えていない)
        activity.delete_all_frames()


class RaiseCommand(SCommand):
    """
    例外送出コマンド
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        # 例外を送出する
        if 'message' in args:
            raise Exception(args['message'])
        else:
            raise Exception(f'The Raise Command raises exception! ⚡️')

class AssertCommand(SCommand):
    """
    フローテストコマンド
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame'), Port('m', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):

        def write_to_file(inputs, port_name, output_path):
            """
            一時ファイルへフローの結果を書き出し
            エラー発生もここで確認する
            """
            from kskp.store import Matrix

            # 入力値
            input = inputs[port_name]

            result = {}
            is_exs = False
            nysol_cmd = None

            if isinstance(input, Exception):
                result = [input]
                is_exs = True
            elif isinstance(input, (NysolModule, Matrix)):
                # RunsCommand を確認したら、実行結果にエラーがない場合にはframeが返却され、エラーが発生した場合はlistが返却される
                # この後の型による分岐で、エラーのもののみの対応を行っているの問題はないのでは
                nysol_cmd = nm.m2tee(i=input.content, o=output_path.as_posix())
                result = RunsCommand().run({}, {port_name:NysolModule(nysol_cmd)})[port_name]
            else:
                raise Exception("入力ポート" + port_name + "に <type: " + str(type(input)) + " >は対応していません")

            # i_portからの出力がエラーであることを判定する
            if isinstance(result, list):
                is_exs = True
            elif result.has_exs:
                result = result.exs
                is_exs = True
            
            # もしエラーが発生していたら、それまでの出力に関わらずエラー文章を比較対象とする。
            if is_exs:
                # エラーメッセージを一時ファイルへ書き出す
                with output_path.open(mode="w")as f:
                    exs_list = [str(x).strip().replace("\n", "") for x in result]
                    f.write('\n'.join(exs_list))  
                
            return is_exs

        def create_diff_list(i_output_path, m_output_path, i_is_exs, m_is_exs, dlimit, inputs):
            """
            2ファイル間での差分取得を行う
            dlimitは差分検出上限数、これを超えたら全体が間違っていると判断する
            NOTE: 2入力のrunfuncが作成できるか不明なため、この差分取得関数はrunfuncで実行しないこととした
            """
            def escape_csv(val_list):
                """
                AssertCommandの出力項目の中に、入力i,mのデータを行１つ分出力する項目があり、
                AssertCommandの出力データが、入力i,mのcsv文章中のコンマや改行のような特殊文字によって壊れることを、
                ダブルクォーテーションを設定するエスケープ 処理によって防ぐ
                """
                escaped_list = []
                for val in val_list:
                    ret = val.strip().replace("\"", "\"\"")
                    ret = "\"" + ret + "\""
                    escaped_list.append(ret)
                return escaped_list

            from itertools import zip_longest

            # 差分情報格納
            diff_list = []
            # 差分取得総数の取得
            diff_limit = 0
            # 差分取得上限数超過判定
            exceed_limit = False

            # 入力データの文字コードを取得する
            i_source_encoding = inputs['i'].encoding
            m_source_encoding = inputs['m'].encoding

            with i_output_path.open(encoding=i_source_encoding)as i_tmp:
                with m_output_path.open(encoding=m_source_encoding)as m_tmp:
                    row_number = None
                    i_port_output = i_tmp
                    m_port_output = m_tmp
                    
                    # 比較対象ともにエラー出力か、そうでないかで処理分け
                    if i_is_exs and m_is_exs:
                        i_list = i_port_output.read().splitlines()
                        m_list = m_port_output.read().splitlines()

                        # ２つの入力で違うエラーを算出する
                        get_diff = list(set(i_list) & set(m_list))
                        i_port_output = list(set(i_list) - set(get_diff))
                        m_port_output = list(set(m_list) - set(get_diff))
                    else:
                        row_number = 1

                    # 差分情報をリスト形式で取得
                    for i_row, m_row in zip_longest(i_port_output, m_port_output, fillvalue=''):
                        if i_row != m_row:
                            diff_row = [str(row_number)]
                            escaped_list = escape_csv([i_row, m_row])
                            diff_row.extend(escaped_list)
                            diff_list.append(diff_row)
                            diff_limit += 1

                            # エラー検知上限数を超えたら検出処理を途中でやめ、各差分情報の代わりに上限超えの旨を出力情報にする
                            if diff_limit > dlimit:
                                exceed_limit = True
                                break
                        if isinstance(row_number, int):
                            row_number += 1
            return diff_list, exceed_limit

        def format_to_csv(diff_list, parent_path, verbose, exceed_limit):
            """
            差分取得の処理結果をもとに、コマンドとしての返却データを作成
            runfuncを使用した場合、対象のコマンドでは標準出力にcsv形式のデータを渡す必要がある。（逆に、runfuncに対して、return を通してデータを返さない）
            """
            from kskp.core import SCatBaseModel

            try:
                # NysolPythonのrunfunc関数の出力は標準出力を使用する、
                # その出力のタイミングを確定させる
                sys.stdout.flush()

                # 出力データの列
                output_columns = [
                    "フローUUID",  # テスト対象フローのuuid
                    "フローのパス", # StreamCat上での、テスト対象フローまでのパス
                    "出力ノードID", # assert commandのデータノードのID
                    "差分なし",     # 入力データの差分がない場合True
                    "例外送出",     # テスト対象のフローが例外を出力したか
                    "行番号",       # 各入力における、csv情報が違う行番号
                    "入力iのデータ", # i_portのdiff_row_number 行目を抜き出す
                    "入力mのデータ", # m_portのdiff_row_number 行目を抜き出す
                    "差分取得限界数超過", # オプションで指定した差分取得限界数を超えたかどうか
                    "実行日時"      # 実行日時
                ]

                # CSVヘッダ行を出力する
                print(",".join(output_columns))

                # 各カラムパラメータ定義
                flow_label = args["flow_label"]
                flow_uuid = args["flow_uuid"]
                # フローの親フォルダのパス
                flow_path = parent_path + '/' + flow_label
                point_id = args['asserted_point']
                is_true = False
                raise_exs = i_is_exs or m_is_exs
                time_str = SCatBaseModel._datetime_to_local_time_str(args['start_at'])
                exceed_limit_str = str(exceed_limit)

                # is_trueの判定 と diffの出力
                if diff_list == [] or diff_list == None:
                    # 二つの入力データに差分がない場合
                    if verbose:
                        is_true = "True"
                        diff = ["","",""]
                    else:
                        # 差分情報を出力しない
                        return
                else:
                    is_true = "False"
                    diff = diff_list

                output_datas = [
                    flow_uuid,
                    flow_path,
                    point_id,
                    is_true,
                    raise_exs,
                ]

                # csv出力処理
                if isinstance(diff, list):
                    if isinstance(diff[0], list):
                        for output_diff in diff:
                            row_data = output_datas + output_diff
                            data_str = ",".join(map(str, row_data)) + "," + exceed_limit_str + "," + time_str
                            print(data_str)
                    else:
                        print(",".join(map(str, output_datas)) + "," + ",".join(map(str, diff)) + "," + exceed_limit_str + "," + time_str)
                else:
                    output_datas.append(diff)
                    output_datas.append(exceed_limit_str)
                    output_datas.append(time_str)
                    print(output_datas)

                # NysolPythonのrunfunc関数の出力は標準出力を使用する、
                # その出力のタイミングを確定させる
                sys.stdout.flush()

            except Exception as e:
                with open('/dev/stderr', 'w') as fpe:
                    import traceback
                    traceback.print_exc(file=fpe)

        if 'i' not in inputs:
            raise Exception('AssertCommandの入力ポートiに値が入力されていません')
        if 'm' not in inputs:
            raise Exception('AssertCommandの入力ポートmに値が入力されていません')

        # 
        # オプションの値が正常であるかを処理前に判定
        # 

        # verbose : Trueの場合、比較が一致しても差分情報を出力する
        if 'verbose' in args:
            if isinstance(args['verbose'], bool):
                verbose = args['verbose']
            else:
                Exception('verboseにはTrue/Falseを指定してください')
        else:
            verbose = False


        # dlimit : エラー検知上限数 -> 整数
        # dlimit未入力の場合、制限をかけない
        dlimit = 0
        if 'dlimit' in args:
            if isinstance(args["dlimit"], int):
                dlimit = args["dlimit"]
            elif isinstance(args["dlimit"], str) and args["dlimit"].isdecimal():
                dlimit = int(args["dlimit"])
            elif args["dlimit"] == '':
                # 制限をかけない
                dlimit == sys.maxsize
            else:
                raise Exception('dlimitには0以上の整数を指定してください')
        else:
            # 制限をかけない
            dlimit == sys.maxsize

        # それぞれの入力portの処理結果の一時書き出し先ファイル
        from kskp.core import Tmp
        i_output_path = Tmp.create_file()
        m_output_path = Tmp.create_file()
        
        # それぞれの入力portの処理結果を一時ファイルに出力する
        # 処理中に例外が送出された場合はTrueを返す
        i_is_exs = write_to_file(inputs, 'i', i_output_path)
        m_is_exs = write_to_file(inputs, 'm', m_output_path)

        # それぞれの入力portから得られたCSVを比較し、その差分を取得する
        diff_list, exceed_limit = create_diff_list(i_output_path, m_output_path, i_is_exs, m_is_exs, dlimit, inputs)
        
        # フローの親フォルダのパスを取得する
        # NOTE: runfunc内でDBにアクセスすると、psycopg2.OperationalErrorが送出される
        parent_path = args['flow'].folder_path

        # 差分をCSVで出力する
        cmd = nm.runfunc(format_to_csv, diff_list=diff_list, parent_path=parent_path, verbose=verbose, exceed_limit=exceed_limit)
        return {'o': NysolModule(cmd)}

class DumpCommand(SCommand):
    """
    StreamCatシステムのDumpファイルを取得する
    """
    from pathlib import Path
    from tarfile import TarFile

    def __init__(self):
        super().__init__()
        self.i_ports = []
        self.o_ports = [Port('o', 'path')]
        self.META_FILE_NAME = 'meta.txt'

    def run(self, args, inputs):
        from pathlib import Path
        # Sessionを取得する
        if 'datum_factory' not in args:
            raise Exception('引数(datum_factory)にDatumFactoryを指定してください')
        session = args['datum_factory']._session

        if not session.has_usr_admin():
            raise Exception('ユーザー管理者以外は、StreamCatのバックアップデータを取得できません')

        try:
            # 全てのテーブルをLockする
            self._lock_all_tables(session)

            with self._open_archive() as archive:
                # ライブラリのディレクトリをDumpする
                #  --syncオプションでインストールした環境では、
                #  files/cmn/はマウントポイントになりDump対象にならない、そのためfiles/cmn/を指定する
                library_root_path = Datum.STORE_DIR / Datum.DEFAULT_LIBRARY_PATH
                self._add_files(archive, library_root_path)
                # PostgreSQLをDumpする
                self._add_meta(archive)

        except Exception as e:
            raise Exception(f'Dumpできませんでした ({e})')

        # アーカイブファイルのファイルパスを返す
        return {'o': Path(archive.name)}

    @staticmethod
    def _lock_all_tables(session):
        # 全てのテーブルをロックする
        # ・競合するロックが解除されるまで待機する
        # ・EXCLUSIVE MODE : このロックモードを保持するトランザクションと並行して実行できる処理は、テーブルの読み取りだけ
        session.execute('LOCK TABLE data,auths,roles,users_roles,users,stores IN EXCLUSIVE MODE;')

    def _open_archive(self):
        import tarfile
        from kskp.core import Tmp
        # アーカイブファイルを作成する
        tar_file_path = Tmp.create_file()
        # シンボリックリンクはリンク先ファイルを圧縮する
        return tarfile.open(tar_file_path, mode='w:gz', dereference=True)

    def _add_files(self, archive:TarFile, file_path:Path):
        """
        ライブラリのディレクトリをDumpする
        """
        from kskp.store import Mountable
        if not file_path.exists():
            # ファイルが存在しない場合はアーカイブに追加しない
            return
        elif file_path.is_dir() and not Mountable.is_mount(file_path):
            # 空のディレクトリでもアーカイブに追加する
            self._add_file(archive, file_path)
            # ディレクトリ以下のファイルを全てアーカイブに追加する
            for child_path in file_path.iterdir():
                self._add_files(archive, child_path)
        else:
            # ファイルをアーカイブに追加する
            # マウント中のマウントポイントの場合はそのディレクトリのみを追加する
            self._add_file(archive, file_path)

    def _add_file(self, archive:TarFile, file_path:Path):
        relative_path = Datum._to_rel_path(file_path)
        archive.add(file_path, arcname=relative_path, recursive=False)
                
    def _add_meta(self, archive:TarFile):
        """
        PostgreSQLをDumpする
        """
        from kskp.core import Tmp, _db_password
        from kskp.store import Mountable
        host = 'db'
        user = 'kskp'
        database = 'kskp'
        schema = 'public'
        dump_file = Tmp.create_file()
        # pg_dumpコマンドを実行する
        # --clean: データベースオブジェクトを作成するコマンドの前に、データベースオブジェクトを整理(削除)するコマンドを書き出す
        # --if-exists: データベースオブジェクトを初期化するときに、条件コマンドを使う(つまり、IF EXISTS句を追加する)
        pg_dump_command = f'pg_dump --clean --if-exists -f {dump_file} -h {host} -U {user} -n {schema} {database}'
        Mountable._exec_command(pg_dump_command, env={'PGPASSWORD':_db_password})
        # アーカイブに追加する
        archive.add(dump_file, arcname=self.META_FILE_NAME, recursive=False)

class RestoreCommand(SCommand):
    """
    StreamCatシステムのDumpファイルを復元する
    """
    from typing import List
    from pathlib import Path
    from tarfile import TarInfo

    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'stream')]
        self.o_ports = [Port('o', 'bool')]
        self.META_FILE_NAME = 'meta.txt'
        self.META_FILE_PATH = Datum.STORE_DIR / self.META_FILE_NAME
        # 
        import threading
        self._thread_lock = threading.Lock()

    def run(self, args, inputs):
        # Factoryを取得する
        if 'factory' not in args:
            raise Exception('引数(factory)にFactoryを指定してください')
        factory = args['factory']

        if not factory._session.has_usr_admin():
            raise Exception('ユーザー管理者以外は、StreamCatを復元できません')

        # ファイルストリームを取得する
        stream = inputs['i']
        if stream is None:
            raise Exception('復元するDumpデータが空です')

        # 復元処理をスレッドセーフで実行する
        with self._thread_lock:
            self._restore_all(factory, stream)

        # Noneは返せないのでとりあえずTrueを返す
        return {'o': True}

    def _restore_all(self, factory, stream):
        """
        StreamCatを復元する
        """
        import shutil
        from datetime import datetime

        try:
            # マウントポイントは移動・削除できないので、ここで全てのマウントを解除する
            factory.data.unmount_all()
            # psqlコマンドでリストアする前に全てのDBコネクションを閉じる必要がある
            factory.close()
        except Exception as e:
            raise Exception(f'マウントが解除できませんでした ({e})')

        # PostgreSQLへのActive状態の接続があれば例外を送出する
        active_connections = [result for result in factory.get_active_connections()]
        if len(active_connections) > 0:
            application_name = active_connections[0]['application_name']
            client_addr = active_connections[0]['client_addr']
            raise Exception(f'PostgreSQLへのActive状態の接続({application_name}@{client_addr})が存在するため復元できません')

        try:
            # ライブラリのルートディレクトリ名を用意する
            library_root_path = Datum.STORE_DIR / Datum.DEFAULT_LIBRARY_PATH
            # ライブラリの退避後のディレクトリ名を作成する
            library_backup_dir_name = Datum.DEFAULT_LIBRARY_PATH.name + '_backup' + datetime.now().strftime('%Y%m%d')
            library_backup_path = Datum.STORE_DIR / library_backup_dir_name

            # ライブラリの既存ルートディレクトリが在れば退避する
            if library_root_path.exists():
                # ディレクトリ名が重複する場合はリネームする
                library_backup_path = Datum.make_unique_path(library_backup_path)
                # ライブラリのルートディレクトリ名を変更して退避する
                Datum.move_file(library_root_path, library_backup_path)

            # ライブラリのディレクトリを復元する
            from kskp.store import FlowDumper
            extracted_members = FlowDumper._extract_archive(Datum.STORE_DIR, stream)

            # StreamCatのDumpファイルが妥当であることを確認する
            self._members_are_valid_or_raise(extracted_members)

            # PostgreSQLのpublicスキーマを復元する
            self._restore_meta(self.META_FILE_PATH)
        except Exception as e:
            # PostgreSQLのDumpファイルを削除する
            self.META_FILE_PATH.unlink(missing_ok=True)
            # 退避したライブラリのルートディレクトリを復帰する
            if library_root_path.exists() and library_backup_path.exists():
                # ライブラリのルートディレクトリと退避したディレクトリが両方存在すれば、
                # ルートディレクトリへの展開が失敗している可能性があるので削除する
                shutil.rmtree(library_root_path)
            if not library_root_path.exists() and library_backup_path.exists():
                # 退避したライブラリのルートディレクトリが存在すれば、それを復帰する
                Datum.move_file(library_backup_path, library_root_path)
            raise Exception(f'復元できませんでした! ({e})')

        try:
            # PostgreSQLのDumpファイルを削除する
            self.META_FILE_PATH.unlink()
        except Exception as e:
            import warnings
            warnings.warn(f'PostgreSQLのDumpファイル({self.META_FILE_PATH})を削除できませんでした ({e})')

        try:
            # 退避したライブラリの既存ディレクトリを削除する
            library_backup_path.exists() and shutil.rmtree(library_backup_path)
        except Exception as e:
            import warnings
            warnings.warn(f'退避したライブラリのディレクトリ({library_backup_path})を削除できませんでした ({e})')

    def _members_are_valid_or_raise(self, members:List[TarInfo]):
        member_paths = [member.name for member in members]
        # meta.txtが含まれていること
        if self.META_FILE_NAME not in member_paths:
            raise Exception(f'StreamCatのDumpファイルに{self.META_FILE_NAME}が存在しません')
        # ライブラリルートが存在すること
        if Datum.DEFAULT_LIBRARY_PATH.name not in member_paths:
            raise Exception(f'StreamCatのDumpファイルに{self.DEFAULT_LIBRARY_PATH}が存在しません')

    def _restore_meta(self, dump_file:Path):
        import subprocess
        from kskp.core import _db_password
        from kskp.store import Mountable
        if not dump_file.is_file():
            raise Exception(f'{self.META_FILE_NAME}がテキストファイルではありません')
        host = 'db'
        user = 'kskp'
        database = 'kskp'
        # コマンド文字列を作成する
        # --no-psqlrc : ~/.psqlrcを読み込まない (指定しない場合returncode=1でエラーになる)
        # --single-transaction : リストア処理を1トランザクションで実行する
        # NOTE: Schema名はDumpファイル内で指定されている
        pg_restore_command = f'psql --no-psqlrc --single-transaction -f {dump_file} -h {host} -U {user} -d {database}'
        try:
            # psqlコマンドを実行する
            Mountable._exec_command(pg_restore_command, env={'PGPASSWORD':_db_password})
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                raise Exception(f'A fatal error of its own occurs (e.g., out of memory, file not found) ({e})')
            elif e.returncode == 2:
                raise Exception(f'The connection to the server went bad and the session was not interactive ({e})')
            elif e.returncode == 3:
                raise Exception(f'An error occurred in a script and the variable ON_ERROR_STOP was set ({e})')
            else:
                raise e

