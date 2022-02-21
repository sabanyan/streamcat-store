from typing import Callable
from streamcat.core import SCatBaseModel

class RemoteFolderConn():
    """
    リモートフォルダの接続情報を保持する
    """
    def __init__(self, conn_json:dict, password_is_enctypted=False, readable_or_raise:Callable[[],None] = None):
        self._conn_json = conn_json

        # パスワードを暗号化する
        if password_is_enctypted:
            self._encrypted_password = conn_json.get('password')
        else:
            password = conn_json.get('password')
            self._encrypted_password = SCatBaseModel._get_encrypt_password(password)

        # readable_or_raise()が指定されない場合は権限判定をしない
        empty_func = lambda: None
        self._readable_or_raise = readable_or_raise or empty_func

    @property
    def protocol(self) -> str:
        # 参照権限が無ければ例外を送出する
        self._readable_or_raise()
        return self._conn_json.get('protocol')

    @property
    def hostname(self) -> str:
        self._readable_or_raise()
        return self._conn_json.get('hostname')

    @property
    def domain(self) -> str:
        self._readable_or_raise()
        return self._conn_json.get('domain')

    @property
    def directory(self) -> str:
        self._readable_or_raise()
        return self._conn_json.get('directory')

    @property
    def user_id(self) -> str:
        self._readable_or_raise()
        return self._conn_json.get('userId')

    @property
    def password(self) -> str:
        self._readable_or_raise()
        return SCatBaseModel._get_decrypt_password(self._encrypted_password)

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
        import sys
        if self.protocol == 'smb':
            if sys.platform == 'linux':
                return f'sudo mount -t cifs -o "user={self.user_id},pass={self.password},domain={self.domain},uid=streamcat,gid=streamcat" ' +\
                       f'"//{self.hostname}/{self.directory}" "{mount_point_path.as_posix()}"'    
            elif sys.platform == 'darwin':
                # macOS
                return f'mount -t smbfs "//{self.user_id}:{self.password}@{self.hostname}/{self.directory}" "{mount_point_path.as_posix()}"'
            else:
                raise Exception(f'このOS({sys.platform})で実行するmountコマンドの引数指定が定義されていません')
        else:
            raise Exception(f'{self.protocol} is undefined protocol')

    def to_json(self, encrypt_password=False):
        # encrypt_password=Trueの場合は暗号化したpasswordを返す
        password = self._encrypted_password if encrypt_password else self.password

        # self._conn_jsonに他のキーが入っている場合もあるので
        # 改めてJSONデータを作成する
        return {'protocol' : self.protocol,
                'hostname' : self.hostname,
                'domain'   : self.domain,
                'directory': self.directory,
                'userId'   : self.user_id,
                'password' : password}
