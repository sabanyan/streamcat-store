class NotAuthorizedException(Exception):
    """
    処理する権限がないことを通知する例外
    """
    pass

class InvalidPassword(Exception):
    """
    不正なパスワード文字列であることを通知する例外
    """
    pass

class NoRoleOwnerException(Exception):
    """
    ロールの所有者がいなくなることを通知する例外
    """
    pass
