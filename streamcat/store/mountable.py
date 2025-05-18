import subprocess
from time import sleep
from streamcat.core import SavableDatum

class Mountable():
    """
    マウント可能データストア
    """

    def __init__(self):
        # moving()とmoved()の呼び出しの間でマウントポイントパスを受け渡しする
        self._mount_point_path = None

    @property
    def path(self):
        # 参照権限が無ければ例外を送出する
        self._readable_or_raise()

        if self._path is None or self._path == '':
            return None

        if self.id is None:
            # 絶対パスを返す
            # DBに未保存の場合は、マウントしない
            return self._path

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
        return self._path

    def is_mountable(self):
        from streamcat.core import Tmp
        # Mount処理確認用のマウントポイントを作成する
        mount_point_path = Tmp.create_file()
        mount_point_path.mkdir(exist_ok=True)
        # Mount処理を行って例外送出の有無でマウントが可能か判定する
        try:
            self.mount(mount_point_path)
            return True
        except Exception as e:
            return False
        finally:
            # 確認後はマウントポイントを削除する
            self.unmount(mount_point_path)
            mount_point_path.exists() and mount_point_path.rmdir()

    def mount(self, mount_point_path=None):
        # 引数(mount_point_path)にpathプロパティを指定する時にMount処理が発生するのを防ぐため
        # 引数(mount_point_path)が設定されない場合は、自身の_pathを使用する
        if mount_point_path is None:
            mount_point_path = self._path

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
            mount_point_path = self._path

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
            rows = self._session.execute(sql).all()
            return [row.uuid for row in rows]
        except Exception as e:
            self._session.rollback()
            raise e

    @staticmethod
    def _exec_command(command_line:str, env:dict=None):
        import shlex
        # mountコマンドの有無を確認する
        sub = subprocess.run(shlex.split(command_line), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if sub.returncode==0:
            # 出力結果を返す
            return sub
        else:
            # サブプロセスのリターンコードがNGの場合は例外を送出する
            raise Exception(str(sub.stderr))

    @staticmethod
    def _has_children(dir_path):
        for file in dir_path.glob("*"):
            return True
        return False

    @staticmethod
    def remount(session, id:int):
        """
        ルートデータストアから指定されたidのDatumまでの経路において、
        マウントされていないマウントポイントがあればマウントし直す
        """
        from pathlib import Path
        from sqlalchemy import select
        from sqlalchemy.orm import aliased
        from streamcat.store.finder import DatumFactory

        # id : 検索対象DatumからRootDatumへの経路の全てのDatumのid
        D0 = aliased(SavableDatum, name='D0')
        R = select(D0.id, D0.parent_id, D0.uuid, D0.type, D0._path).\
            where(D0.id==id).\
            cte(name='R', recursive=True)
            # cte: Common Table Expression WITH句のこと

        # WITH句にUNION ALLを用いて再帰クエリとする
        D = aliased(SavableDatum, name='D')
        R = R.union_all(
                select(D.id, D.parent_id, D.uuid, D.type, D._path).\
                join(R, D.id==R.c.parent_id)
            )

        stmt =  select(R.c.uuid, R.c._path, R.c.type).\
                where(R.c.type.in_(['awss3', 'rfolder'])).\
                order_by(R.c.id)

        try:
            rows = session.execute(stmt).all()
        except Exception as e:
            session.rollback()
            raise e

        factory = DatumFactory(session)

        for row in rows:
            mount_point_path = Path(row[1])
            if not Mountable.is_mount(mount_point_path):
                uuid = str(row.uuid)
                type = str(row.type)
                if type == SavableDatum.AWSS3_TYPE:
                    awss3 = factory.find_by_uuid(uuid)
                    awss3.mount(mount_point_path)
                elif type == SavableDatum.RFOLDER_TYPE:
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

    def moving(self, parent_uuid, prev_parent_id, lock_uuid=None, modifier=None):
        """
        ゴミ箱へほかされるか、ゴミ箱から元の場所に戻す場合を除いて場合を除いて
        マウント中の場合は移動できない
        TODO: Linuxのmountコマンドの--moveオプションを使えばマウント中の
              ディレクトリポイントを移動できるらしいが、間に合わせの実装として移動を禁止する
        """
        from streamcat.store.finder import DatumFactory
        factory = DatumFactory(self._session)
        trash_folder = factory.load_trash_folder()

        if parent_uuid==trash_folder.uuid or prev_parent_id==trash_folder.id:
            # ゴミ箱へほかされる、またはゴミ箱から戻される場合、
            # moved()で参照するために更新前のマウントパスを保持しておく
            self._mount_point_path = self._path
        elif Mountable.is_mount(self._path):
            # マウント中のリモートフォルダは移動できない
            raise Exception('マウント中のリモートフォルダは移動できません')
        # 
        super().moving(parent_uuid, prev_parent_id, lock_uuid=lock_uuid, modifier=modifier)

    def moved(self, parent_uuid, prev_parent_id, modifier=None):
        """
        ゴミ箱へほかされた場合は、マウントを解除する
        """
        from streamcat.store.finder import DatumFactory
        factory = DatumFactory(self._session)
        trash_folder = factory.load_trash_folder()

        if parent_uuid==trash_folder.uuid or prev_parent_id==trash_folder.id:
            # ゴミ箱へほかされた、またはゴミ箱から戻された場合、マウントを解除する
            # NOTE: DB更新後に実行されるので更新前のpathである_mount_point_pathを参照する
            self.unmount(self._mount_point_path)
            self._mount_point_path = None

        return super().moved(parent_uuid, prev_parent_id, modifier=modifier)
