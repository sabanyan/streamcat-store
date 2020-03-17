class MCMDError(Exception):
    """
    NYSOL Pythonのエラーを通知する例外
    """
    pass

class MCMDErrorInfo():
    def __init__(self, description, input_n, output_n, called_at):
        self.description = description
        self.number_of_input = input_n
        self.number_of_output = output_n
        self.called_at = called_at  

    @classmethod
    def parse_stderr(cls, s):
        """
        以下のようなMCMDの実行時のエラー文字列をparseしてオブジェクトに起こす
        '#ERROR# field name not found: `c' in a.csv (kgcut); kgcut f=c i=a.csv; IN=0 OUT=0; 2018/06/14 20:57:21'
        """
        # s = "#ERROR# field name not found: `c' in a.csv (kgcut); kgcut f=c i=a.csv; IN=1253 OUT=5624; 2018/06/14 20:57:21"
        # まず、セミコロンで区切る
        ss = s.split(';')

        # 入力と出力の件数をパースする
        if len(ss) >= 3:
            import re
            result = re.search(r'IN=(\d+) OUT=(\d+)', ss[2])
            if result is not None:
                io = result.groups()
                return cls(ss[0].replace('#ERROR#', ''), int(io[0]), int(io[1]), ss[3])
            else:
                return cls(s, -1, -1, '')
        else:
            print('re:', s)

    def __repr__(self):
        return f'MCMDError:{self.description}'