import uuid
import threading
from datetime import datetime

class LockedDatumException(Exception):
    """
    Datumをロックするのに失敗したことを通知する例外
    """
    pass

class Lock():
    def __init__(self, lock_for, creator, created_at):
        """
        uuid     : ロックのuuid
        lock_for : ロック対象のuuid
        creator  : ロックの作成者
        created_at : ロックの作成時刻
        """
        self.uuid = str(uuid.uuid4())
        self.lock_for = lock_for
        self.creator = creator
        self.created_at = created_at
    
    def to_json(self):
        return {'uuid' : self.uuid}

class LockManager():
    """
    ロックを管理する(スレッドセーフ)
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._lock_data = {}

    def lock(self, lock_for, creator):
        with self._lock:
            for lock in self._lock_data.values():
                if lock.lock_for == lock_for:
                    # ロック失敗 (T_T
                    raise LockedDatumException(f'Datum ({lock_for}) is already locked')
            # ロック成功 !
            new_lock = Lock(lock_for, creator, datetime.utcnow())
            self._lock_data[new_lock.uuid] = new_lock
            return new_lock

    def contains(self, lock_uuid):
        with self._lock:
            return lock_uuid in self._lock_data

    def unlock(self, lock_uuid):
        with self._lock:
            try:
                # ロックを削除する
                del self._lock_data[lock_uuid]
            except KeyError:
                raise Exception('No lock is found!')

            
