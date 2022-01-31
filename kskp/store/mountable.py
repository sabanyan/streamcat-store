import subprocess
from time import sleep
from kskp.core import Datum

class Mountable():
    """
    マウント可能データストア
    """

    @property
    def path(self):
        # 参照権限が無ければ例外を送出する
        self._readable_or_raise()

        if self._path is None or self._path == '':
            return None

        if self.id is None:
            # 絶対パスを返す
            # DBに未保存の場合は、マウントしない
            return Datum._to_abs_path(self._path)

        if not Mountable.is_mount(self._path):
            try:
                # マウントしていない場合は、ここでマウント処理する
                Mountable.remount(self._session, self.id)
            except Exception as e:
                # 再マウント処理に失敗しても例外を送出しない
                # (ここで例外を送出するとexists(path)で存在チェックができなくなる)
                import warnings
                warnings.warn(f'Mount処理に失敗しました {e}')

        # 絶対パスを返す
        return Datum._to_abs_path(self._path)

    def mount(self, mount_point_path=None):
        # 引数(mount_point_path)にpathプロパティを指定する時にMount処理が発生するのを防ぐため
        # 引数(mount_point_path)が設定されない場合は、自身の_pathを使用する
        if mount_point_path is None:
            mount_point_path = Datum._to_abs_path(self._path)

        if not mount_point_path.exists():
            raise Exception('mount point(%s) does not exist' % mount_point_path)
        elif not mount_point_path.is_dir():
            raise Exception('mount point(%s) is not directory' % mount_point_path)
        elif Mountable._has_children(mount_point_path):
            raise Exception('mount point(%s) has files' % mount_point_path)
        elif Mountable.is_mount(mount_point_path):
            # python3.7でis_mount()は追加される
            raise Exception('mount point(%s) already mounted on' % mount_point_path)

        # mountコマンドを作成する
        mount_cmd = self._get_mount_cmd(mount_point_path)
        
        try:
            # 共有フォルダをマウントする
            # (sudoで実行するとテストでしくじる?)
            mount_ret = Mountable._exec_command(mount_cmd)
            # 念のためWAITを入れています
            sleep(1)
        except subprocess.CalledProcessError as e:
            raise Exception('"mount" command returned error --> ' + str(e))

    def unmount(self, mount_point_path=None):
        # 引数(mount_point_path)にpathプロパティを指定する時にMount処理が発生するのを防ぐため
        # 引数(mount_point_path)が設定されない場合は、自身の_pathを使用する
        if mount_point_path is None:
            mount_point_path = Datum._to_abs_path(self._path)

        # マウントポイントがない場合は処理を終了する
        if not mount_point_path.exists():
            import warnings
            warnings.warn('mount point(%s) does not exist' % mount_point_path)
            return

        # python3.7でis_mount()は追加される
        if not Mountable.is_mount(mount_point_path):
            return

        try:
            # マウント解除を実行する
            # (/etc/sudoersに %admin ALL = (ALL) NOPASSWD:/sbin/umount
            #  を追加するとテスト実行時にはパスワードを聞かれない)
            umount_cmd = f'sudo umount "{mount_point_path.as_posix()}"'
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
        from sqlalchemy import text

        sql = text(f"""
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
        """)
        try:
            results = self._session.execute(sql)
            return [result[0] for result in results]
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

    @staticmethod
    def _exec_command(command_line:str, env:dict=None):
        import shlex
        # mountコマンドの有無を確認する
        sub = subprocess.run(shlex.split(command_line), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
        from pathlib import Path
        from sqlalchemy import text
        from kskp.store.factory import DatumFactory

        sql = text(f"""
        WITH RECURSIVE R AS (
            SELECT id, parent_id, uuid, type, path FROM data WHERE id = {id}
            UNION ALL
            SELECT D.id, D.parent_id, D.uuid, D.type, D.path FROM data D JOIN R ON D.id = R.parent_id
        )
        SELECT uuid, path, type FROM R
        WHERE type = 'awss3' or type = 'rfolder'
        ORDER BY id
        """)
        try:
            results = session.execute(sql)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            # session.commit()
            pass

        factory = DatumFactory(session)

        for result in results:
            mount_point_path = Datum._to_abs_path(Path(result[1]))
            if not Mountable.is_mount(mount_point_path):
                uuid = str(result[0])
                type = str(result[2])
                if type == Datum.AWSS3_TYPE:
                    awss3 = factory.find_by_uuid(uuid)
                    awss3.mount(mount_point_path)
                elif type == Datum.RFOLDER_TYPE:
                    folder = factory.find_by_uuid(uuid)
                    folder.mount(mount_point_path)
                else:
                    raise Exception('undefined type found!')

    @staticmethod
    def is_mount(path):
        """
        Check if this path is a POSIX mount point
        """
        abs_path = path

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
