from kskp.core import Datum
from kskp.store import Folder, Mountable

class AwsS3(Folder, Mountable):

    __mapper_args__ = {
        'polymorphic_identity' : 'awss3'
    }

    def __init__(self, session, parent, label, bucket_name, creator=None):
        """
        コンストラクタ
        bucket_name : AWS S3のバケットネームを指定する
        """
        super().__init__(session, parent, label, creator)

        # データタイプを設定する
        self.type = Datum.AWSS3_TYPE

        # data列の値を作成する
        self.data = {'bucket' : bucket_name}

        # S3のオブジェクトを用意する
        # self._s3 = boto3.resource('s3')

    def save(self):
        """
        バケットを保存する
        """
        # 既にルートフォルダが存在する場合は、parent_id=NULLを許可しない
        from kskp.store.factory import DatumFactory
        if self.parent_id is None and DatumFactory(self.session).count_root() > 0:
            raise Exception('You can not add root bucket. A root already exists.')
        # フォルダに紐付くディレクトリ(path列で指定されるディレクトリ)がなければ作成する
        self.path = self._make_dir()
        # ここでAWS S3 バケットをマウントする
        self.mount(self._path)
        try:
            # Dataテーブルにレコードを新規追加する
            self.session.add(self)
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.commit()

    def update_data(self, label, bucket_name, modifier=None):
        """
        バケットのdata列を更新する
        """
        # レコードを取得する
        datum = self.session.query(Datum).filter(Datum.uuid==self.uuid)\
                                    .filter(Datum.type==Datum.AWSS3_TYPE).one_or_none()
        if datum is None:
            raise Exception('no bucket is found by designated id.')

        # ラベルに'\0'が含まれていれば取り除く
        new_label = Datum.escape_label(label)

        # ファイルを移動する
        old_path = datum._path
        new_path = Folder._move_dir(old_path, new_label)

        try:
            # ディレクトリ名の移動によって他のDatumのpathが変更が必要であれば変更する
            self._update_same_path(old_path, new_path, modifier)
            self._update_include_path(old_path, new_path, modifier)

            # レコードを更新する
            # data = {'bucket' : bucket_name}
            data = datum.data.copy()
            data['bucket'] = bucket_name
            result = self.session.query(Datum).filter(Datum.uuid==self.uuid).one_or_none()
            if result is not None:
                result._label = new_label
                result._data = data
                result._modifier_id = (modifier or self.session.user).id
                self.session.update(result)
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.commit()

        return datum

    def delete(self):
        """
        バケットを削除する
        """
        # 自身のフォルダ以下のフレームが、自身のフォルダ以下以外にあるフローから参照されている場合は、例外を送出する
        uuids = self._get_flow_uuids_using_other_datum(self.id)
        if len(uuids) > 0:
            raise Exception(
                'フロー(%s)で使用しているCSVファイルが登録解除対象になっているため削除できません' % uuids[0])

        try:
            # フレームレコードを削除する
            # session.delete(self)

            # 自身のフォルダ以下の全てのフォルダとドキュメントをエントリーから削除する
            self._remove_reference_only_recursively()

            # AWS S3 バケットをマウント解除する
            self.unmount(self._path)
            # ディレクトリを削除する
            self._remove_dir()
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.commit()

    @property
    def bucket_name(self):
        return self.data['bucket']

    def _get_mount_cmd(self, mount_point_path):
        import shutil
        # S3をマウントするgoofysコマンドの有無を確認する
        goofys_path = shutil.which('goofys')
        if goofys_path is None:
            raise Exception('AWS S3 mount command, goofys is not found.')
        return goofys_path + ' %s %s' % (self.bucket_name, mount_point_path)


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
        ret =  {'uuid'      : self.uuid,
                'type'      : Datum.AWSS3_TYPE,
                'label'     : self.label,
                'bucket'    : self.bucket_name,
                'creator'   : self.creator_str,
                'createdAt' : self.created_at_str}
        if self.readable:
            ret['prevFolderPath'] = self.get_prev_folder_path()
            ret['bucket'] = self.bucket_name
        return ret
