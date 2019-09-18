class RdbConnInfo():
    """
    RDBへの接続情報を保持する
    """

    def __init__(self, dbms, hostname, port, database, user_id, password):
        self.dbms = dbms
        self.hostname = hostname
        self.port = port
        self.database = database
        self.user_id = user_id
        self.password = password
    
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
        return f"{dbms}://{user_id}:{password}@{hostname}:{port}/{database}"