import os
from .lock_manager import Lock, LockManager, LockedDatumException

# 環境変数から排他ロックの有効期間(分)を取得する
# (設定値がない場合は5分とする)
lock_expire_minutes = int(os.getenv('KSKP_LOCK_EXPIRE_MIN', 5))
# LockManagerオブジェクトを作成する
lock_manager = LockManager(60 * lock_expire_minutes)

from .lock_required import lock_required
