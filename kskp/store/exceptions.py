class NothingToPutbackException(Exception):
    """
    ゴミ箱から0個のDatumを戻した場合にお知らせする
    """
    pass

class NoResultsException(Exception):
    """
    実行結果がなかった場合にお知らせする
    """
    pass

class CommandException(Exception):
    """
    コマンドが送出する例外
    """
    def __init__(self, ex):
        self._ex = ex

    def __str__(self):
        return self._ex.__str__()
