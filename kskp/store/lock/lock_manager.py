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
    def __init__(self, target_uuid, creator, created_at):
        """
        uuid        : ロックのuuid
        target_uuid : ロック対象のuuid
        creator     : ロックの作成者
        created_at  : ロックの作成時刻
        """
        self.uuid = str(uuid.uuid4())
        self.target_uuid = target_uuid
        self.creator = creator
        self.created_at = created_at
        self.modified_at = created_at
    
    def to_json(self):
        return {'uuid'      : self.uuid,
                'target'    : self.target_uuid,
                'creator'   : self.creator.name,
                'createdAt' : self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'modifiedAt': self.modified_at.strftime('%Y-%m-%d %H:%M:%S')}

class LockManager():
    """
    ロックを管理する(スレッドセーフ)
    """
    def __init__(self, valid_seconds):
        self._thread_lock = threading.Lock()
        self._lock_data = {}
        self._valid_seconds = valid_seconds

    def lock(self, target_uuid, creator):
        with self._thread_lock:
            return self._lock(target_uuid, creator)

    def relock(self, target, lastModifiedAt, creator):
        """
        有効期限切れや手動解除などにより解除されたロックを再度取得する場合に使用する
        """
        with self._thread_lock:
            # 解除された後に他ユーザがロック対象を編集した場合はエラーとする
            # (レアケースだろうが、modifiedの判定後にフローが編集される可能性が0ではないので、with self._thread_lockする)
            if lastModifiedAt < target.modified_at:
                raise LockedDatumException(f'他ユーザー({target.modifier.name})がフローを編集した可能性があります')
            # ロックを獲得する
            return self._lock(target.uuid, creator)

    def _lock(self, target_uuid, creator):
        # 有効期間切れのロックを削除する
        self._unlock_expired_locks()

        for lock in self._lock_data.values():
            if lock.target_uuid == target_uuid:
                # ロック失敗 (T_T
                raise LockedDatumException(f'ユーザー({lock.creator.name})がフローを編集中です')
                
        # ロック成功 !
        new_lock = Lock(target_uuid, creator, datetime.utcnow())
        self._lock_data[new_lock.uuid] = new_lock
        return new_lock

    def contains(self, lock_uuid):
        with self._thread_lock:
            # 有効期間切れのロックを削除する
            self._unlock_expired_locks()

            # ロックの有無を判定する
            if lock_uuid in self._lock_data:
                # ロックの有効期間を延長する
                self._lock_data[lock_uuid].modified_at = datetime.utcnow()
                return True
            else:
                return False

    def containts_target(self, target_uuid):
        with self._thread_lock:
            # 有効期間切れのロックを削除する
            self._unlock_expired_locks()

        for lock in list(self._lock_data.values()):
            if lock.target_uuid == target_uuid:
                # ロックの有効期間を延長する
                self._lock_data[lock.uuid].modified_at = datetime.utcnow()
                return True
        return False

    def unlock(self, lock_uuid):
        with self._thread_lock:
            # ロックを削除する
            unlocked_lock = self._lock_data.get(lock_uuid)
            if unlocked_lock is None:
                raise Exception('No lock is found!')
            del self._lock_data[unlocked_lock.uuid]
            return unlocked_lock

    def unlock_target(self, target_uuid):
        for lock in list(self._lock_data.values()):
            if lock.target_uuid == target_uuid:
                self.unlock(lock.uuid)
                return lock
        return None

    def unlock_all(self):
        with self._thread_lock:
            # ロックを削除する
            unlocked_locks = list(self._lock_data.values())
            self._lock_data.clear()
            return unlocked_locks

    def _unlock_expired_locks(self):
        """
        有効期間切れのロックを削除する
        """
        expired_time = datetime.utcnow() - timedelta(seconds=self._valid_seconds)
        expired_locks = []
        for unlocked_lock in self._lock_data.values():
            if unlocked_lock.modified_at <= expired_time:
                expired_locks.append(unlocked_lock)

        for expired_lock in expired_locks:
            del self._lock_data[expired_lock.uuid]

        return expired_locks
