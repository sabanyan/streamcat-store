from typing import Callable

class RemoteFolderConn():
    """
    リモートフォルダの接続情報を保持する
    """
    def __init__(self, conn_json:dict, readable_or_raise:Callable[[],None] = None):
        self._conn_json = conn_json

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
        return self._conn_json.get('user_id')

    @property
    def password(self) -> str:
        self._readable_or_raise()
        return self._conn_json.get('password')

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
                return f'mount -t smbfs //{self.user_id}:{self.password}@{self.hostname}/{self.directory} {mount_point_path.as_posix()}'
            else:
                return f'sudo mount -t cifs -o username={self.user_id},password={self.password},domain={self.domain} //{self.hostname}/{self.directory} {mount_point_path.as_posix()}'
            
        else:
            raise Exception('undefined remote protocol found')

    def to_json(self):
        # self._conn_jsonに他のキーが入っている場合もあるので
        # 改めてJSONデータを作成する
        return {'protocol' : self.protocol,
                'hostname' : self.hostname,
                'domain'   : self.domain,
                'directory': self.directory,
                'user_id'  : self.user_id,
                'password' : self.password}
