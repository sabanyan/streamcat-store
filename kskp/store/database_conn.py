from typing import Callable

class DatabaseConn():
    """
    DBへの接続情報を保持する
    """
    def __init__(self, conn_json:dict, readable_or_raise:Callable[[],None] = None):
        self._conn_json = conn_json

        # readable_or_raise()が指定されない場合は権限判定をしない
        empty_func = lambda: None
        self._readable_or_raise = readable_or_raise or empty_func

    @property
    def dbms(self) -> str:
        # 参照権限が無ければ例外を送出する
        self._readable_or_raise()
        return self._conn_json.get('dbms')

    @property
    def hostname(self) -> str:
        self._readable_or_raise()
        return self._conn_json.get('hostname')

    @property
    def port(self) -> str:
        self._readable_or_raise()
        return self._conn_json.get('port')

    @property
    def database(self) -> str:
        self._readable_or_raise()
        return self._conn_json.get('database')

    @property
    def user_id(self) -> str:
        self._readable_or_raise()
        return self._conn_json.get('user_id')

    @property
    def password(self) -> str:
        self._readable_or_raise()
        return self._conn_json.get('password')

    def valid_or_raise(self):
        if self.dbms is None or self.dbms =='':
            raise Exception('DB種別の指定が必要です')

        if self.hostname is None or self.hostname =='':
            raise Exception('DBのホスト名またはIPアドレスの指定が必要です')

        if self.port is None or self.port =='':
            raise Exception('DB接続のポート番号の指定が必要です')

        # if self.database is None or self.database =='':
        #     raise Exception('DB接続のデータベース名の指定が必要です')

    def get_database_uri(self):
        """
        RDBへの接続URIを返す
        """
        import urllib.parse
        
        # URLエンコードを行う
        dbms     = self.dbms
        user_id  = urllib.parse.quote(self.user_id)
        password = urllib.parse.quote(self.password)
        hostname = self.hostname
        port     = self.port
        database = urllib.parse.quote(self.database)
        
        if dbms.upper() == 'ORACLE':
            import cx_Oracle
            dsnStr = cx_Oracle.makedsn(hostname, port, database)
            dsnStr = dsnStr.replace('SID', 'SERVICE_NAME')
            return f'oracle://{user_id}:{password}@{dsnStr}'
        else:
            return f'{dbms}://{user_id}:{password}@{hostname}:{port}/{database}'

    def to_json(self):
        # self._conn_jsonに他のキーが入っている場合もあるので
        # 改めてJSONデータを作成する
        return {'dbms'     : self.dbms,
                'hostname' : self.hostname,
                'port'     : self.port,
                'database' : self.database,
                'user_id'  : self.user_id,
                'password' : self.password}
