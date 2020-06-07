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
