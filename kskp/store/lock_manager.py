import uuid
import threading
from datetime import datetime, timedelta

class LockedDatumException(Exception):
    """
    Datumをロックするのに失敗したことを通知する例外
    """
    pass

class Lock():
    """
    ロック情報
    """
    def __init__(self, target, creator, created_at):
        """
        uuid     : ロックのuuid
        target   : ロック対象のuuid
        creator  : ロックの作成者
        created_at : ロックの作成時刻
        """
        self.uuid = str(uuid.uuid4())
        self.target = target
        self.creator = creator
        self.created_at = created_at
        self.modified_at = created_at
    
    def to_json(self):
        return {'uuid'       : self.uuid,
                'target'     : self.target,
                'creator'    : self.creator.name,
                'created_at' : self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'modified_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')}

class LockManager():
    """
    ロックを管理する(スレッドセーフ)
    """
    def __init__(self, valid_seconds):
        self._lock = threading.Lock()
        self._lock_data = {}
        self._valid_seconds = valid_seconds

    def lock(self, target, creator):
        with self._lock:
            # 有効期間切れのロックを削除する
            self._unlock_expired_locks()

            for lock in self._lock_data.values():
                if lock.target == target:
                    # ロック失敗 (T_T
                    raise LockedDatumException(f'Datum ({target}) is already locked')
            # ロック成功 !
            new_lock = Lock(target, creator, datetime.utcnow())
            self._lock_data[new_lock.uuid] = new_lock
            return new_lock

    def contains(self, lock_uuid):
        with self._lock:
            # 有効期間切れのロックを削除する
            self._unlock_expired_locks()

            # ロックの有無を判定する
            if lock_uuid in self._lock_data:
                # ロックの有効期間を延長する
                self._lock_data[lock_uuid].modified_at = datetime.utcnow()
                return True
            else:
                return False

    def unlock(self, lock_uuid):
        with self._lock:
            try:
                # ロックを削除する
                unlocked_lock = self._lock_data.get(lock_uuid)
                del self._lock_data[lock_uuid]
                return unlocked_lock
            except KeyError:
                raise Exception('No lock is found!')

    def unlock_target(self, target_uuid):
        for lock in list(self._lock_data.values()):
            if lock.target == target_uuid:
                self.unlock(lock.uuid)
                return lock
        return None

    def unlock_all(self):
        with self._lock:
            # ロックを削除する
            unlocked_locks = list(self._lock_data.values())
            self._lock_data.clear()
            return unlocked_locks

    def _unlock_expired_locks(self):
        """
        有効期間切れのロックを削除する
        """
        expired_time = datetime.utcnow() - timedelta(seconds=self._valid_seconds)
        unlock_locks = []
        for expired_lock in self._lock_data.values():
            if expired_lock.modified_at <= expired_time:
                unlock_locks.append(expired_lock)

        for unlock_lock in unlock_locks:
            del self._lock_data[unlock_lock.uuid]

        return unlock_locks
