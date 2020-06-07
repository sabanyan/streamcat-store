import os

from kskp.core import Datum

class Frame(Datum):

    __mapper_args__ = {
        'polymorphic_identity' : 'frame'
    }

    # 64MB
    READ_BUFFER_SIZE = 64 * 1024 * 1024

    # 文字コード変換テーブル
    ENCODING_CONV_TABLE = {'ascii':'ASCII', 'utf-8':'UTF-8', 'UTF-8-SIG':'UTF-8 BOM'}
    # 改行コード変換テーブル
    NEWLINE_CONV_TABLE = {'\n':'LF', '\r\n':'CR+LF', '\r':'CR', 'UNKNOWN':'UNKNOWN'}

    def __init__(self, session, parent, label, stream, creator=None):
        """
        コンストラクタ
        stream : Frameデータのファイルストリームを指定する
        """
        super().__init__(session, parent, Datum.FRAME_TYPE, label, creator)

        # ファイルストリームの文字コードを推測する
        if stream is not None and hasattr(stream, 'seek'):
            encoding = Frame._detect_encoding(stream)
            newline = Frame._detect_newline_code(stream)
        else:
            encoding = 'UNKNOWN'
            newline = 'UNKNOWN'

        # ファイルストリームを保持する
        self.stream = stream

        # data列の値を作成する
        self.data = {'encoding':encoding, 'newline':newline}

        # フローキャッシュの場合はTrue
        # data.type列='cache'を用意するべきだろうか？
        self.is_cache = False

    def save(self, file_path=None):
        """
        Frameを保存する
        """
        # 既にルートフォルダが存在する場合は、parent_id=NULLを許可しない
        from kskp.store.factory import DatumFactory
        if self.parent_id is None and DatumFactory(self.session).count_root() > 0:
            raise Exception('You can not add another root frame. A root already exists.')

        if file_path is None:
            # 既存のファイルと重複しないファイル名を取得する
            self.path = Datum.make_unique_path(self.path)
        elif file_path.exists():
            self.path = file_path
            # ファイルの文字コードを判定する
            with open(file_path, 'rb') as f:
                encoding = Frame._detect_encoding(f)
                newline = Frame._detect_newline_code(f)
            self.data = {'encoding':encoding, 'newline':newline}
        else:
            raise Exception(f'指定したファイル({file_path})が存在しないためFrameを保存できません')

        # 新規追加前にファイルパスを退避する
        self_path = self.path

        try:
            # Dataテーブルにレコードを新規追加する
            self.session.add(self)
            # ドキュメントに紐付くファイル(path列で指定されるファイル)がなければ作成する
            if file_path is None:
                self._make_file(self_path)
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            # 親フォルダのロックを解除する
            self.session.commit()

    # def add_entry_from_path(self, file_path):
    #     """
    #     指定されたパスのファイルをFrameとして登録する
    #     """
    #     # 既にルートフォルダが存在する場合は、parent_id=NULLを許可しない
    #     from kskp.store.factory import DatumFactory
    #     if self.parent_id is None and DatumFactory(self.session).count_root() > 0:
    #         raise Exception('You can not add another root frame. A root already exists!')
    #     self.path = file_path

    #     # ファイルの文字コードを判定する
    #     if file_path.exists():
    #         with open(file_path, 'rb') as f:
    #             encoding = Frame._detect_encoding(f)
    #             newline = Frame._detect_newline_code(f)
    #         self.data = {'encoding':encoding, 'newline':newline}

    #     try:
    #         # Dataテーブルにレコードを新規追加する
    #         self.session.add(self)
    #     except Exception as e:
    #         self.session.rollback()
    #         raise e
    #     finally:
    #         self.session.commit()

    def update_label(self, label, modifier=None):
        """
        Frameのdata列を更新する
        """
        # ラベルに'\0'が含まれていれば取り除く
        new_label = Datum.escape_label(label)

        # ラベル名からファイルパスを作成する
        old_path = self.path
        new_path = old_path.parent / Datum.escape_filename(new_label)
        new_path = Datum.make_unique_path(new_path, except_path=old_path)

        try:
            # 同じファイルに対応するドキュメントのpath列を、ファイル名の移動に合わせて変更する
            self._update_same_path(old_path, new_path, modifier)
            # label列を更新する
            self._update_label_imp(new_label, modifier)
            # ファイルを移動する
            Datum.move_file(old_path, new_path)
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.commit()

        return self

    def update_encoding_newline(self, encoding_str=None, newline_str=None, modifier=None):
        encoding = None
        if encoding_str is None:
            # 自身の持つファイルの文字コードを判定する
            if self.path.exists():
                with open(self.path, 'rb') as f:
                    encoding = Frame._detect_encoding(f)
        else:
            for key, value in Frame.ENCODING_CONV_TABLE.items():
                if value == encoding_str:
                    encoding = key
                    break
            if encoding is None:
                encoding = encoding_str

        newline = None
        if newline_str is None:
            # 自身の持つファイルの改行コードを判定する
            if self.path.exists():
                with open(self.path, 'rb') as f:
                    newline = Frame._detect_newline_code(f)
        else:
            for key, value in Frame.NEWLINE_CONV_TABLE.items():
                if value == newline_str:
                    newline = key
                    break
            if newline is None:
                raise Exception(f'文字改行コードの指定文字列({newline_str})が誤っています')

        try:
            self._data = {'encoding':encoding, 'newline':newline}
            self._modifier_id = (modifier or self.session.user).id
            self.session.update(self)
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.commit()

        return self

    def update_label_only(self, label, modifier=None):
        """
        Frameのlabel列を更新する
        (path及び対応ファイル名は変更しない)
        """
        # ラベルに'\0'が含まれていれば取り除く
        new_label = Datum.escape_label(label)

        try:
            self._update_label_imp(new_label, modifier)
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.commit()

    def _update_label_imp(self, new_label, modifier):
        # label列を更新する
        self._label = new_label
        self._modifier_id = (modifier or self.session.user).id
        self.session.update(self)

    def throw_away(self):
        """
        Frameをゴミ箱にほかす
        """
        from kskp.store.factory import DatumFactory
        factory = DatumFactory(self.session)
        trash_folder = factory.load_trash_folder()

        # 削除しようとするframeが、フローで使用されている場合は例外を送出する
        flow_labels = factory.get_flows_referencing_frame(self.uuid)
        if len(flow_labels) > 0:
            raise Exception(f'このCSVファイルはフロー({flow_labels[0]})で使用しているため削除できません')

        self.move(trash_folder.uuid)

    def delete(self):
        """
        Frameを削除する
        """
        # 削除しようとするframeが、DBに格納されているフローで使用されている場合は例外を送出する
        # 2019/07/29現在、以下の理由により一旦コメントアウト
        # 1. キャッシュ削除にもこのdeleteメソッドを使っており、キャッシュはどこかのフローで使用されているものなので、
        # 　　いつまで経っても削除できない
        # 2. frame削除APIでもframeを使っているかいないかをチェックしているので、こっちでしなくてもとりあえず大丈夫

        # using_flow_uuids = self.get_flow_uuids_using_me()
        # if len(using_flow_uuids) > 0:
        #     from kskp.store import Flow
        #     using_flow_label= Flow.find_by_uuid(using_flow_uuids[0]).label
        #     raise Exception('このCSVファイルはフロー(%s)で使用しているため削除できません' % using_flow_label)

        try:
            # フレームレコードを削除する
            self.session.delete(self)
            # ファイルを削除する
            self._remove_file()
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.commit()

    def remove_reference_only(self):
        """
        Frameを削除するが、対応するファイルは削除しない
        (テストにおいてテスト用ファイルを削除したくない場合に使用する)
        """
        try:
            # フレームレコードを削除する
            self.session.delete(self)
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.commit()

    @property
    def file_size(self):
        return self.path.stat().st_size

    @property
    def file_exists(self):
        return self.path.exists()

    @property
    def encoding(self):
        return self.data.get('encoding') or 'UNKNOWN'

    # @encoding.setter
    # def encoding(self, encoding):
    #     self.data['encoding'] = encoding

    @property
    def encoding_str(self):
        ret = self.ENCODING_CONV_TABLE.get(self.encoding)
        return ret or self.encoding

    @property
    def newline(self):
        return self.data.get('newline') or 'UNKNOWN'

    # @newline.setter
    # def newline(self, newline):
    #     self.data['newline'] = newline

    @property
    def newline_str(self):
        ret = self.NEWLINE_CONV_TABLE.get(self.newline)
        return ret or self.newline   

    @property
    def modified_at_str(self):
        import time
        wk = time.localtime(self.path.stat().st_mtime)
        return time.strftime('%Y/%m/%d %H:%M', wk)

    def _make_file(self, path):
        """
        Frameに対応するファイルを作成する
        """
        try:
            # 親ディレクトリがなければ作成する
            os.makedirs(path.parent, exist_ok=True)
            # ファイルを作成する
            self._save_file(path)
            return path
        except PermissionError as e:
            # ファイルに対する権限がない場合
            raise e

    def _remove_file(self):
        """
        Frameに対応するファイルを削除する
        """
        try:
            # ファイルが存在しなければ削除処理はしない
            if not self.path.exists():
                return
            # 自分以外で同じファイルを使用しているFrameがあれば削除しない
            if self._frame_path_exists(self.path, except_id=self.id):
                return
            if not self.path.is_file():
                raise Exception('Can not delete %s, because it is not reguler file.' % self.path)
            # ファイルを物理削除する
            self.path.unlink()
        except PermissionError as e:
            # ファイルに対する権限がない場合
            raise e

    def _save_file(self, path):
        with open(path, mode='wb') as f:
            while True:
                buff = self.stream.read(self.READ_BUFFER_SIZE)
                f.write(buff)
                if buff is None or len(buff)==0:
                    break

    def _frame_path_exists(self, path, except_id):
        rel_path = Datum._to_rel_path(path).as_posix()

        result = self.session.query(Datum._path).filter(Datum._path == rel_path)\
                                           .filter(Datum.type == Datum.FRAME_TYPE)\
                                           .filter(Datum.id != except_id).count()
        return result > 0

    @staticmethod
    def _detect_encoding(stream):
        """
        指定されたファイルの文字コードを判別する
        """
        from chardet.enums import LanguageFilter
        from chardet.universaldetector import UniversalDetector
        detector = UniversalDetector(lang_filter=LanguageFilter.CJK)

        max_feed_num = 100
        chunk_size = 1024

        for i in range(max_feed_num):
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            # 一定Byteずつ食わせる
            detector.feed(chunk)
            # 文字コード判定の信頼度がある一定を超えた場合に識別結果を返す
            if detector.done:
                break

        # streamの読み込み位置をリセットする
        stream.seek(0)
        detector.close()

        encoding = detector.result.get('encoding')
        if not encoding:
            # 今回の調査で我々は・・・何の成果も得られませんでした！！
            return 'UNKNOWN'

        return encoding

    @staticmethod
    def _detect_newline_code(stream):
        max_feed_num = 100
        chunk_size = 1024

        crlf_count = 0
        lf_count = 0
        cr_count = 0

        for i in range(max_feed_num):
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            crlf = chunk.count(b'\r\n')
            if crlf > 0:
                crlf_count += crlf
            else:
                lf_count += chunk.count(b'\n')
                cr_count += chunk.count(b'\r')

        # streamの読み込み位置をリセットする
        stream.seek(0)

        # 出現頻度の最も多い改行コードを返す
        if crlf_count > max(lf_count, cr_count):
            return '\r\n'
        elif lf_count > cr_count:
            return '\n'
        elif lf_count < cr_count:
            return '\r'
        else:
            return 'UNKNOWN'

    def to_json(self):
        ret =  {'uuid'      : self.uuid,
                'type'      : self.type,
                'label'     : self.label,
                'creator'   : self.creator_str,
                'createdAt' : self.created_at_str}

        if self.readable:
            ret['prevFolderPath'] = self.get_prev_folder_path()
            ret['encoding'] = self.encoding_str
            ret['newline'] = self.newline_str

        return ret

    def load_as_data_frame(self, offset, limit):
        """
        CSVの文字列を受け取り、
        いわゆるデータフレームの形式にして返す
        TODO: offsetはつかってない
        """
        result_text = ''
        result_data = {}
        column_list = []
        abs_path = self.path
        with abs_path.open(encoding='utf-8') as f:
            n = 0
            limit_count = 0

            for line in f:
                if limit is not None and limit_count == limit:
                    break

                if n == 0:
                    # 一行目はヘッダとみなす
                    # 重複文字があればインデックスをつける
                    column_list = Frame._replace_column_name(line.split(','))
                    for column_name in column_list:
                        result_data[column_name] = []
                else:
                    if offset < n:
                        for idx, column_data in enumerate(line.split(',')):
                            result_data[column_list[idx]].append(column_data)
                        limit_count += 1
                n += 1

        if n == 0:
            raise Exception('空のCSVを読み込みました。コマンド実行時にエラーが発生した可能性があります。')

        result_len = n

        # 行数も返すように変更
        return result_data, result_len

    @staticmethod
    def _replace_column_name(column_list):
        """
        受け取ったカラム名リストに重複している列名があれば
        連番をつける
        """
        def check_column_overlap(column_list):
            """
            受け取ったカラム名リストを走査する
            """
            index_dict = {}
            column_name_overlap = False

            for index, column_name in enumerate(column_list):
                if not column_name in index_dict:
                    index_dict[column_name] = []
                else:
                    column_name_overlap = True
                index_dict[column_name].append((index, len(index_dict[column_name])))

            return index_dict, column_name_overlap

        index_dict, column_name_overlap = check_column_overlap(column_list)

        if not column_name_overlap:
            return column_list

        for column_name, tuple_list in index_dict.items():
            if len(tuple_list) < 2:
                continue

            for tuple in tuple_list:
                # tuple[0]　インデックス（column_listの）
                # tuple[1]　連番
                if tuple[1] > 0:
                    column_list[tuple[0]] = column_name + '.' + str(tuple[1])

        return column_list

