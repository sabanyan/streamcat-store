from streamcat.core import Datum
from streamcat.store import File

class Frame(File):

    __mapper_args__ = {
        'polymorphic_identity' : 'frame'
    }

    # 文字コード変換テーブル
    ENCODING_CONV_TABLE = {'ascii':'ASCII', 'utf-8':'UTF-8', 'UTF-8-SIG':'UTF-8 BOM'}
    # 改行コード変換テーブル
    NEWLINE_CONV_TABLE = {'\n':'LF', '\r\n':'CR+LF', '\r':'CR', 'UNKNOWN':'UNKNOWN'}

    def __init__(self, session, parent, label, stream):
        """
        コンストラクタ
        stream : Frameデータのファイルストリームを指定する
        """
        super().__init__(session, parent, Datum.FRAME_TYPE, label, stream)

        # python-magicはCSVファイルを'text/plain'と判定するため、'text/csv'に変更する
        if 'content_type' in self._data and self._data['content_type'] == 'text/plain':
            self._data['content_type'] = 'text/csv'

        # ファイルストリームの文字コードと改行コードを推測する
        encoding = Frame._detect_encoding(stream)
        newline = Frame._detect_newline_code(stream)

        # data列に追記する
        self._data.update({'encoding':encoding, 'newline':newline})

        # フローキャッシュの場合はTrue
        # data.type列='cache'を用意するべきだろうか？
        self.is_cache = False

    def save(self, file_path=None):
        """
        Frameを保存する
        """        
        if file_path is not None and file_path.exists():
            # ファイルの文字コードを判定して記録する
            with open(file_path, 'rb') as f:
                encoding = Frame._detect_encoding(f)
                newline = Frame._detect_newline_code(f)
            self._data.update({'encoding':encoding, 'newline':newline})

        try:
            # DBに保存する
            super().save(file_path=file_path)
        except (Exception, OSError) as e:
            self._session.rollback()
            raise e

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
            self._data.update({'encoding':encoding, 'newline':newline})
            self._modifier_id = (modifier or self._session.user).id
            self._session.update(self)
        except Exception as e:
            self._session.rollback()
            raise e
        finally:
            self._session.commit()

        return self

    @property
    def encoding(self):
        return self._data.get('encoding') or 'UNKNOWN'

    @property
    def encoding_str(self):
        ret = self.ENCODING_CONV_TABLE.get(self.encoding)
        return ret or self.encoding

    @property
    def newline(self):
        return self._data.get('newline') or 'UNKNOWN'

    @property
    def newline_str(self):
        ret = self.NEWLINE_CONV_TABLE.get(self.newline)
        return ret or self.newline   

    @staticmethod
    def _detect_encoding(stream):
        """
        指定されたファイルの文字コードを判別する
        """
        from chardet.enums import LanguageFilter
        from chardet.universaldetector import UniversalDetector
        detector = UniversalDetector(lang_filter=LanguageFilter.CJK)

        MAX_FEED_NUM = 100
        CHUNK_SIZE = 1024

        # ファイルストリームの文字コードを推測する
        if stream is None and not hasattr(stream, 'seek'):
            return 'UNKNOWN'

        for i in range(MAX_FEED_NUM):
            chunk = stream.read(CHUNK_SIZE)
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
        MAX_FEED_NUM = 100
        CHUNK_SIZE = 1024

        crlf_count = 0
        lf_count = 0
        cr_count = 0

        # ファイルストリームの文字コードを推測する
        if stream is None and not hasattr(stream, 'seek'):
            return 'UNKNOWN'

        for i in range(MAX_FEED_NUM):
            chunk = stream.read(CHUNK_SIZE)
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
        ret = super().to_json()
        ret['encoding'] = self.encoding_str
        ret['newline'] = self.newline_str
        return ret

