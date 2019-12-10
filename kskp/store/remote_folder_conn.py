class RemoteFolderConn():
    """
    リモートフォルダの接続情報を保持する
    """

    def __init__(self, protocol, hostname, domain, directory, user_id, password):
        self.protocol = protocol
        self.hostname = hostname
        self.domain = domain
        self.directory = directory
        self.user_id = user_id
        self.password = password

    def valid_or_raise(self):
        if self.protocol is None or self.protocol =='':
            raise Exception('リモートフォルダの種別の指定が必要です')

        if self.hostname is None or self.hostname =='':
            raise Exception('リモートフォルダのホスト名またはIPアドレスの指定が必要です')

        if self.directory is None or self.directory =='':
            raise Exception('リモートフォルダのディレクトリの指定が必要です')

    def get_mount_cmd(self, mount_point_path):
        """
        リモートフォルダへの接続コマンドを返す
        """
        if self.protocol == 'smb':
            from kskp.store import _is_unittest
            if _is_unittest():
                # テスト実行では、macOS用のmountコマンドを用いる
                return f'mount -t smbfs //{self.user_id}:{self.password}@{self.hostname}/{self.directory} {mount_point_path}'
            else:
                return f'sudo mount -t cifs -o username={self.user_id},password={self.password},domain={self.domain} //{self.hostname}/{self.directory} {mount_point_path}'
            
        else:
            raise Exception('undefined remote protocol found')

    @staticmethod
    def from_json(conn):
        return RemoteFolderConn(conn['protocol'],
                                conn['hostname'],
                                conn['domain'],
                                conn['directory'],
                                conn['user_id'],
                                conn['password'])

    def to_json(self):
        return {'protocol' : self.protocol,
                'hostname' : self.hostname,
                'domain'   : self.domain,
                'directory': self.directory,
                'user_id'  : self.user_id,
                'password' : self.password}
