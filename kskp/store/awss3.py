import os
import json
import shutil
import shlex
import subprocess
from time import sleep
from pathlib import Path

from kskp.core import Datum
from . import ss as session
from kskp.store import Folder

class AwsS3(Folder):

    def __init__(self, parent_uuid, label, bucket_name, creator=None):
        """
        コンストラクタ
        bucket_name : AWS S3のバケットネームを指定する
        """
        super().__init__(parent_uuid, label, creator)

        # データタイプを設定する
        self.type = Datum.AWSS3_TYPE

        # data列の値を作成する
        self.data = json.dumps({'label' : label, 'bucket' : bucket_name})

        # S3のオブジェクトを用意する
        # self._s3 = boto3.resource('s3')

    @staticmethod
    def find_by_uuid(uuid):
        """
        指定されたuuidを持つバケットを取得する
        """
        # UUID値の形式チェックをする
        Datum.valid_uuid_or_raise(uuid)
        datum = session.query(Datum).filter(Datum.uuid==uuid)\
                                    .filter(Datum.type==Datum.AWSS3_TYPE).one_or_none()
        if datum is None:
            raise Exception('no bucket is found by designated id.')
        return AwsS3.convert_to_awss3(datum)

    @staticmethod
    def exists(uuid):
        """
        指定されたuuidを持つバケットが存在する場合はTrueを返す
        """
        # UUID値の形式チェックをする
        if not Datum.is_valid_uuid(uuid):
            return False
        result = session.query(Datum).filter(Datum.uuid==uuid)\
                                     .filter(Datum.type==Datum.AWSS3_TYPE).count()
        return result > 0

    @staticmethod
    def convert_to_awss3(datum):
        parent_uuid = Datum.get_uuid_by_id(datum.parent_id)
        # label = json.loads(datum.data, encoding='utf-8')['label']
        bucket_name = json.loads(datum.data, encoding='utf-8')['bucket']
        awss3 = AwsS3(parent_uuid, datum.label, bucket_name, datum.creator)
        awss3.id = datum.id
        awss3.uuid = datum.uuid
        awss3._path = datum._path
        awss3.modifier = datum.modifier
        awss3.created_at = datum.created_at
        awss3.modified_at = datum.modified_at
        return awss3

    def save(self):
        """
        バケットを保存する
        """
        # 既にルートフォルダが存在する場合は、parent_id=NULLを許可しない
        if self.parent_id is None and Datum.count_root() > 0:
            raise Exception('You can not add root bucket. A root already exists.')
        # フォルダに紐付くディレクトリ(path列で指定されるディレクトリ)がなければ作成する
        self.path = self._make_dir()
        # ここでAWS S3 バケットをマウントする
        self.mount()
        try:
            # Dataテーブルにレコードを新規追加する
            session.add(self)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.commit()

    @staticmethod
    def update_data(uuid, label, bucket_name, modifier):
        """
        バケットのdata列を更新する
        """
        # UUID値の形式チェックをする
        Datum.valid_uuid_or_raise(uuid)
        # レコードを取得する
        datum = session.query(Datum).filter(Datum.uuid==uuid)\
                                    .filter(Datum.type==Datum.AWSS3_TYPE).one_or_none()
        if datum is None:
            raise Exception('no bucket is found by designated id.')

        # ラベルに'\0'が含まれていれば取り除く
        new_label = Datum.escape_label(label)

        # ファイルを移動する
        old_path = datum.path
        new_path = Folder._move_dir(old_path, new_label)

        try:
            # ディレクトリ名の移動によって他のDatumのpathが変更が必要であれば変更する
            Datum.update_all_path(old_path, new_path, modifier)

            # レコードを更新する
            data = json.dumps({'label' : new_label, 'bucket' : bucket_name})
            session.query(Datum).filter(Datum.uuid==uuid).update({'_label'   :new_label
                                                                 ,'data'    :data
                                                                 ,'modifier':modifier})
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.commit()

        return AwsS3.convert_to_awss3(datum)

    def delete(self):
        """
        バケットを削除する
        """
        # 自身のフォルダ以下のフレームが、自身のフォルダ以下以外にあるフローから参照されている場合は、例外を送出する
        uuids = self._get_flow_uuids_using_other_datum()
        if len(uuids) > 0:
            raise Exception(
                'フロー(%s)で使用しているCSVファイルが登録解除対象になっているため削除できません' % uuids[0])

        try:
            # フレームレコードを削除する
            # session.query(Datum).filter(Datum.id==self.id)\
            #                        .filter(Datum.type==Datum.AWSS3_TYPE).delete()

            # 自身のフォルダ以下の全てのフォルダとドキュメントをエントリーから削除する
            self._remove_reference_only_recursively()

            # AWS S3 バケットをマウント解除する
            self.unmount()
            # ディレクトリを削除する
            self._remove_dir()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.commit()

    @property
    def bucket_name(self):
        return json.loads(self.data, encoding='utf-8')['bucket']

    def mount(self):
        path = Path(self._path)
        if not path.exists():
            raise Exception('mount point(%s) does not exist' % self._path)
        elif not path.is_dir():
            raise Exception('mount point(%s) is not directory' % self._path)
        elif AwsS3._has_children(path):
            raise Exception('mount point(%s) has files' % self._path)
        elif Datum.is_mount(path):
            # python3.7でis_mount()は追加される
            raise Exception('mount point(%s) already mounted on' % self._path)

        # S3をマウントするgoofysコマンドの有無を確認する
        goofys_path = shutil.which('goofys')
        if goofys_path is None:
            raise Exception('AWS S3 mount command, goofys is not found.')

        try:
            # goofysコマンドを実行してS3バケットをマウントする
            # (sudoで実行するとテストでしくじる)
            goofys_cmd = goofys_path + ' %s %s' % (self.bucket_name, self._path)
            goofys_ret = AwsS3._exec_command(goofys_cmd)
            # 念のためWAITを入れています
            sleep(1)
        except subprocess.CalledProcessError as e:
            # error_message = goofys_ret.stderr.decode('utf-8')
            raise Exception('"goofys" command returned error --> ' + str(e))

    def unmount(self):
        path = Path(self._path)
        if not path.exists():
            raise Exception('sudo mount point(%s) does not exist' % self._path)

        # python3.7でis_mount()は追加される
        if not Datum.is_mount(path):
            return

        try:
            # マウント解除を実行する
            # (/etc/sudoersに %admin ALL = (ALL) NOPASSWD:/sbin/umount
            #  を追加するとテスト実行時にはパスワードを聞かれない)
            umount_cmd = 'sudo umount %s' % self._path
            umount_ret= AwsS3._exec_command(umount_cmd)

            # 念のためWAITを入れています
            sleep(1)
        except subprocess.CalledProcessError as e:
            # error_message = umount_ret.stderr.decode('utf-8')
            raise Exception('"umount" command returned error --> ' + str(e))


    def _get_flow_uuids_using_other_datum(self):
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
        """.format(id=self.id)
        try:
            results = session.execute(sql)
            return [result[0] for result in results]
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.commit()

    # def _remove_reference_only_recursively(self):
    #     """
    #     エントリを削除するが、対応するファイルは削除しない
    #     この処理は自身と自身のエントリ以下の全てのエントリが対象である
    #     """
    #     sql="""
    #     WITH RECURSIVE R AS (
    #         SELECT id FROM data WHERE id = {id}
    #         UNION ALL
    #         SELECT data.id FROM data JOIN R ON data.parent_id = R.id
    #     )
    #     DELETE FROM data D
    #     WHERE EXISTS (SELECT * FROM R
    #                   WHERE R.id = D.id);
    #     """.format(id=self.id)
    #     try:
    #         session.execute(sql)
    #     except Exception as e:
    #         session.rollback()
    #         raise e
    #     finally:
    #         session.commit()

    @staticmethod
    def _exec_command(command_line):
        # S3をマウントするgoofysコマンドの有無を確認する
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

    # import boto3
    # import botocore.exceptions
    #
    # def _get(self, key):
    #     # 自オブジェクトに紐づくバケットオブジェクトを取得する
    #     bucket = self._s3.Bucket(self.bucket_name)
    #     # 指定されたキー名からオブジェクトを取得する
    #     obj = bucket.Object(key)
    #     # オブジェクトの内容を取得する
    #     try:
    #         response = obj.get()
    #     except botocore.exceptions.ClientError as e:
    #         if e.response['Error']['Code'] == 'NoSuchKey':
    #             raise Exception('No S3 key (%s) exists' % key)
    #         else:
    #             raise e
    #     return response['Body'].read()
    #
    #
    # def _put(self, key, stream):
    #     # 自オブジェクトに紐づくバケットオブジェクトを取得する
    #     bucket = self._s3.Bucket(self.bucket_name)
    #     # 指定されたキー名からオブジェクトを取得する
    #     obj = bucket.Object(key)
    #     # オブジェクトの内容を送信する
    #     obj.put(stream)
    #
    # def _exists(self, key):
    #     s3client = boto3.Session().client('s3')
    #     contents = s3client.list_objects(Prefix=key, Bucket=self.bucket_name).get("Contents")
    #     if contents:
    #         for content in contents:
    #             if content.get("Key") == key:
    #                 return True
    #     return False
    #
    # def get_another_key(self, key):
    #     """
    #     同じ名称のKeyが既に存在する場合、末尾に数字を付加したKey名を作成する
    #     """
    #     while self._exists(key):
    #         # ファイル名の末尾に'_1'を付加するメソッドを流用する
    #         key = Datum._get_another_file_name(key)
    #     return key

    def to_json(self):
        return {'uuid'      : self.uuid,
                'type'      : Datum.AWSS3_TYPE,
                'label'     : self.label,
                'bucket'    : self.bucket_name,
                'creator'   : Datum.get_user_name_by_user_id(self.creator),
                'createdAt' : self.created_at_str}
