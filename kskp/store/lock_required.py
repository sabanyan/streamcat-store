
import functools
from kskp.store import lock_manager, LockedDatumException

def lock_required(func):
    """
    指定されたLockのuuidをLockManagerが持っているか確認する
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # self
        myself = args[0]

        if 'ignore_lock' in kwargs and kwargs['ignore_lock'] == True:
            # ロックによる排他制御をしない
            return func(*args, **kwargs)
        if 'lock_uuid' in kwargs and kwargs['lock_uuid'] is not None:
            # 引数で指定されたロックの有無を判定する
            if not lock_manager.contains(kwargs['lock_uuid']):
                raise LockedDatumException('ロックが強制解除された、または有効期限が切れました')
            return func(*args, **kwargs)
        else:
            # 引数でロックのuuidが指定されなかった場合は、ここでロックを取得する
            lock = lock_manager.lock(myself.uuid, creator=myself._session.user)
            onetime_lock_uuid = lock.uuid
            # funcを実行する
            try:
                result = func(*args, **kwargs)
            finally:
                # ロックを解除する
                lock_manager.unlock(onetime_lock_uuid)
            return result

    return wrapper
