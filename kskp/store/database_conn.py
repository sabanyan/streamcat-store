class DatabaseConn():
    """
    DBへの接続情報を保持する
    """

    def __init__(self, dbms, hostname, port, database, user_id, password):
        self.dbms = dbms
        self.hostname = hostname
        self.port = port
        self.database = database
        self.user_id = user_id
        self.password = password

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
        dbms     = self.dbms
        user_id  = self.user_id
        password = self.password
        hostname = self.hostname
        port     = self.port
        database = self.database
        
        if dbms.upper() == 'ORACLE':
            import cx_Oracle
            dsnStr = cx_Oracle.makedsn(hostname, port, database)
            dsnStr = dsnStr.replace('SID', 'SERVICE_NAME')
            return f'oracle://{user_id}:{password}@{dsnStr}'
        else:
            return f'{dbms}://{user_id}:{password}@{hostname}:{port}/{database}'

    @staticmethod
    def from_json(conn):
        return DatabaseConn(conn['dbms'],
                            conn['hostname'],
                            conn['port'],
                            conn['database'],
                            conn['user_id'],
                            conn['password'])

    def to_json(self):
        return {'dbms'     : self.dbms,
                'hostname' : self.hostname,
                'port'     : self.port,
                'database' : self.database,
                'user_id'  : self.user_id,
                'password' : self.password}
