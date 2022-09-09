from streamcat.core import Datum
from .store import Matrix, Store

class ApparentOut(Store):
    """
    フローの出力ポートと出力結果を保持する
    (フローエディタから見た見かけのout)
    """
    def __init__(self, out_point, datum:Datum, exs=None):
        super().__init__(None, None, 'out', None)
        self.out_point = out_point
        self.datum = datum
        self.exs = exs

    @property
    def has_exs(self):
        return self.exs is not None and len(self.exs) > 0

    @property
    def has_datum(self):
        return self.datum is not None

    @property
    def has_list(self):
        return self.datum is not None and isinstance(self.datum, Matrix)

    @property
    def has_frame(self):
        from streamcat.store import Frame
        return self.datum is not None and isinstance(self.datum, Frame)

    @property
    def has_cache(self):
        from streamcat.store import Frame
        return self.datum is not None and isinstance(self.datum, Frame) and self.datum.is_cache

    def to_json(self):
        ret = {'id': self.out_point.id, 'label': self.out_point.label}
        if not self.has_cache and self.has_exs:
            # 出力Pointで例外が発生した場合
            ret['message'] = str(self.exs[0])
        elif self.datum is not None:
            # 出力Pointで結果を出力した場合
            ret['datum'] = self.datum.uuid
        return ret

class ApparentOuts():
    """
    ApparentOutのリストを表す
    """
    def __init__(self) -> None:
        # NOTE: 同じpointインスタンスの場合もあることに注意!!
        self._outs:list[ApparentOut] = []

    def __len__(self):
        return len(self._outs)

    def __iter__(self):
        yield from self._outs

    def add(self, out:ApparentOut):
        self._outs.append(out)

    @property
    def outs(self):
        # Cacheは返さない
        # 同じPointにCacheとFrame(CacheとVis)が紐づくとややこしい
        return [out for out in self._outs if not out.has_cache and not out.has_exs]

    @property
    def caches(self):
        """
        作成したキャッシュのリストを返す
        """
        return [out for out in self._outs if out.has_cache]

    @property
    def exs(self):
        # return [(out.out_point, out.exs) for out in self._outs if not out.has_cache and out.has_exs]
        return [out for out in self._outs if not out.has_cache and out.has_exs]

    @property
    def data(self):
        """
        作成したDatumのリストを返す
        """
        return [(out.out_point, out.datum) for out in self._outs if out.has_datum]

    @property
    def is_success(self):
        for out in self._outs:
            if out.has_exs:
                return False
        return True

    def raise_one(self):
        """
        例外があれば、そのうち一つを送出する
        """
        for out in self._outs:
            if out.has_exs:
                raise out.exs[0]
        return

    def delete_all_frames(self):
        """
        全てのFrame(Cache含む)を削除する
        """
        for out in self._outs:
            if out.has_frame:
                out.datum.delete()
                out.datum = None

    def to_json(self):
        return {
            'outs'  : [out.to_json() for out in self.outs],
            'caches': [cache.to_json() for cache in self.caches],
            'exs'   : [ex.to_json() for ex in self.exs]
        }
