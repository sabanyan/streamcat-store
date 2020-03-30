import shlex
import subprocess
from time import sleep
from pathlib import Path

from kskp.core import Datum

class Mountable():
    """
    mount可能な抽象クラス
    """
    def mount(self, mount_point_path):
        self_abs_path = Datum._to_abs_path(mount_point_path)
        path = Path(self_abs_path)
        if not path.exists():
            raise Exception('mount point(%s) does not exist' % self_abs_path)
        elif not path.is_dir():
            raise Exception('mount point(%s) is not directory' % self_abs_path)
        elif Mountable._has_children(path):
            raise Exception('mount point(%s) has files' % self_abs_path)
        elif Mountable.is_mount(path):
            # python3.7でis_mount()は追加される
            raise Exception('mount point(%s) already mounted on' % self_abs_path)

        # mountコマンドを作成する
        mount_cmd = self._get_mount_cmd(self_abs_path)
        
        try:
            # 共有フォルダをマウントする
            # (sudoで実行するとテストでしくじる?)
            mount_ret = Mountable._exec_command(mount_cmd)
            # 念のためWAITを入れています
            sleep(1)
        except subprocess.CalledProcessError as e:
            raise Exception('"mount" command returned error --> ' + str(e))

    def unmount(self, mount_point_path):
        self_abs_path = Datum._to_abs_path(mount_point_path)
        path = Path(self_abs_path)
        if not path.exists():
            raise Exception('sudo mount point(%s) does not exist' % self_abs_path)

        # python3.7でis_mount()は追加される
        if not Mountable.is_mount(path):
            return

        try:
            # マウント解除を実行する
            # (/etc/sudoersに %admin ALL = (ALL) NOPASSWD:/sbin/umount
            #  を追加するとテスト実行時にはパスワードを聞かれない)
            umount_cmd = 'sudo umount %s' % self_abs_path
            umount_ret= Mountable._exec_command(umount_cmd)

            # 念のためWAITを入れています
            sleep(1)
        except subprocess.CalledProcessError as e:
            raise Exception('"umount" command returned error --> ' + str(e))

    def _get_mount_cmd(self, mount_point_path):
        return ''

    def _get_flow_uuids_using_other_datum(self, self_id):
        """
        自身のエントリ以下にあるFrameとFlowが、自身のエントリ以下以外にあるFlowから参照される、
        そのようなFlowを全て返す
        """
        sql = """
        WITH RECURSIVE R AS (
            SELECT id, uuid FROM data WHERE id = {id}
            UNION ALL
            SELECT data.id, data.uuid FROM data JOIN R ON data.parent_id = R.id
        )
        SELECT uuid FROM data D
        WHERE type = 'flow'
        AND NOT
            EXISTS (SELECT * FROM R
                    WHERE R.id = D.id)
        AND EXISTS (SELECT * FROM R
                    WHERE type in ('flow','frame')
                      AND to_tsvector(D.data) @@ to_tsquery(cast(R.uuid AS VARCHAR)))
        """.format(id=self_id)
        try:
            results = self.session.execute(sql)
            return [result[0] for result in results]
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.commit()

    @staticmethod
    def _exec_command(command_line):
        # mountコマンドの有無を確認する
        sub = subprocess.run(shlex.split(command_line), stdout = subprocess.PIPE, stderr=subprocess.PIPE)
        # サブプロセスのリターンコードがNGの場合は例外を送出する
        sub.check_returncode()
        # 出力結果を返す
        return sub

    @staticmethod
    def _has_children(dir_path):
        for file in dir_path.glob("*"):
            return True
        return False

    @staticmethod
    def remount(session, id):
        """
        ルートデータストアから指定されたidのDatumまでの経路において、
        マウントされていないマウントポイントがあればマウントし直す
        """
        sql = """
        WITH RECURSIVE R AS (
            SELECT id, parent_id, uuid, type, path FROM data WHERE id = {id}
            UNION ALL
            SELECT D.id, D.parent_id, D.uuid, D.type, D.path FROM data D JOIN R ON D.id = R.parent_id
        )
        SELECT uuid, path, type FROM R
        WHERE type = 'awss3' or type = 'rfolder'
        ORDER BY id
        """.format(id=id)
        try:
            results = session.execute(sql)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            # session.commit()
            pass

        for result in results:
            mount_point_dir = result[1]
            if not Mountable.is_mount(Path(mount_point_dir)):
                uuid = str(result[0])
                type = str(result[2])
                from kskp.store import AwsS3, RemoteFolder
                if type == Datum.AWSS3_TYPE:
                    awss3 = AwsS3.find_by_uuid(uuid)
                    awss3.mount(mount_point_dir)
                elif type == Datum.RFOLDER_TYPE:
                    folder = RemoteFolder.find_by_uuid(uuid)
                    folder.mount(mount_point_dir)
                else:
                    raise Exception('undefined type found!')

    @staticmethod
    def is_mount(path):
        """
        Check if this path is a POSIX mount point
        """
        abs_path = Path(Datum._to_abs_path(path.as_posix()))

        # Need to exist and be a dir
        if not abs_path.exists() or not abs_path.is_dir():
            return False

        parent = abs_path.parent
        try:
            parent_dev = parent.stat().st_dev
        except OSError:
            return False

        dev = abs_path.stat().st_dev
        if dev != parent_dev:
            return True
        ino = abs_path.stat().st_ino
        parent_ino = parent.stat().st_ino
        return ino == parent_ino
