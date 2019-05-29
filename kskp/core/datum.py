"""
いわゆるルートクラスであるDatumを定義している
"""

class Datum:
    """
    KSKPで扱う対象を扱ううち、「第一級」であるものの頂点のクラス。
    直接インスタンス化はしない想定。
    """

    def __init__(self):
        self.context = {}
        self.uuid = None
