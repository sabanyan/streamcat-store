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

class OptimisticLockException(Exception):
    """
    楽観的排他制御によりDatumの更新に失敗したことを通知する例外
    """
    pass
