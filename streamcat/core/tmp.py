import os
from pathlib import Path

class Tmp():
    """
    Tmpファイルを扱う
    """
    # key   : unique_key
    # value : [file1, file2, ,,]
    _tmp = {}

    def __init__(self):
        """
        Tmpクラスはインスタンス化しないこと！
        """
        raise Exception('Tmpクラスはインスタンスを生成しません')

    @staticmethod
    def create_file():
        import uuid
        # 一意なファイル名を作成する
        key = Tmp._generate_unique_key()
        file_name  = '__SCATTMP_' + key + '_' + str(uuid.uuid4())[0:8]
        # TmpファイルPath
        new_tmp_file = Tmp._get_tmp_directory() / file_name
        # TmpファイルPathを覚えておく
        if key in Tmp._tmp:
            Tmp._tmp[key].append(new_tmp_file)
        else:
            Tmp._tmp[key] = [new_tmp_file]
        return new_tmp_file
    
    @staticmethod
    def remove_files():
        # キーを取得する
        key = Tmp._generate_unique_key()
        # キーに紐づくTmpファイルがあれば削除する
        if key not in Tmp._tmp:
            return
        tmp_files = Tmp._tmp.pop(key)
        # Tmpファイルを物理削除する
        for tmp_file in tmp_files:
            if tmp_file.exists():
                tmp_file.unlink()

    @staticmethod
    def _get_tmp_directory():
        # Tmpファイルの作成ディレクトリが環境変数で指定されていれば、
        # その場所に作成する
        if 'TMP' in os.environ :
            return Path(os.environ.get('TMP'))
        elif 'TEMP' in os.environ :
            return Path(os.environ.get('TEMP'))
        else:
            return Path('/tmp')

    @staticmethod
    def _generate_unique_key():
        import threading
        # 現在のプロセスIDとスレッドIDをキーとする
        process_id = os.getpid() 
        thread_id = threading.current_thread().ident
        return str(process_id) + '_' + str(thread_id)
