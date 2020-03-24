import os
import time
import unittest
import json
import uuid
import pprint
from pathlib import Path
from datetime import datetime

from kskp.store import LockManager, LockedDatumException, STORE_DIR, Library

class LockManagerTest(unittest.TestCase):
    """
    Lock Managerをテストする
    """

    # Lock Managerを作成する
    lock_manager = LockManager(1)

    @classmethod
    def tearDownClass(cls):
        # ライブラリフォルダを削除する
        from kskp.core import Datum
        library_path = STORE_DIR / Library.load_root().path
        import shutil
        shutil.rmtree(library_path.as_posix())
        # Sessionを閉じる
        from kskp.store import ss as session
        session.close()
        # スキーマを破棄する
        from kskp.store import engine
        from sqlalchemy import DDL
        engine.execute(DDL('DROP SCHEMA IF EXISTS %s CASCADE' % os.environ['KSKP_POSTGRESQL_SCHEMA_NAME']))

    def test_simple(self):
        """
        ロックの取得と解除
        """
        # ロックを取得する
        target = str(uuid.uuid4())
        lock = self.lock_manager.lock(target, creator=1)
        # 正常にロックが取得できることを確認する
        self.assertIsNotNone(lock.uuid)
        self.assertEqual(lock.target, target)
        self.assertEqual(lock.creator, 1)
        self.assertIsNotNone(lock.created_at)
        # 取得したロックUUIDはLockManagerが管理している
        self.assertTrue(self.lock_manager.contains(lock.uuid))
        # ロックを解除する
        self.lock_manager.unlock(lock.uuid)
        # 解除したロックはLockManagerは管理しない
        self.assertFalse(self.lock_manager.contains(lock.uuid))

    def test_conflict(self):
        """
        複数回のロックはできない
        """
        # ロックを取得する
        target = str(uuid.uuid4())
        lock = self.lock_manager.lock(target, creator=1)
        # 正常にロックが取得できることを確認する
        self.assertIsNotNone(lock.uuid)
        self.assertEqual(lock.target, target)
        self.assertEqual(lock.creator, 1)
        self.assertIsNotNone(lock.created_at)
        # 同じユーザで、同じDatum UUIDでも複数回ロックはできない
        with self.assertRaises(LockedDatumException):
            self.lock_manager.lock(target, creator=1)
        # ロックを解除する
        self.lock_manager.unlock(lock.uuid)

    def test_invalid_unlock(self):
        """
        誤まったロック解除
        """
        # 存在しないUUIDでロックを解除すると例外が送出される
        with self.assertRaises(Exception):
            self.lock_manager.unlock(uuid.uuid4())

    def test_lock_after_unlock(self):
        """
        ロック解除後はロックできる
        """
        # ロックを取得する
        target = str(uuid.uuid4())
        lock = self.lock_manager.lock(target, creator=1)
        # 正常にロックが取得できることを確認する
        self.assertIsNotNone(lock.uuid)
        self.assertEqual(lock.target, target)
        self.assertEqual(lock.creator, 1)
        self.assertIsNotNone(lock.created_at)
        # ロックを解除する
        self.lock_manager.unlock(lock.uuid)
        # 同じデータを再びロックする
        lock = self.lock_manager.lock(target, creator=1)
        # 正常にロックが取得できることを確認する
        self.assertIsNotNone(lock.uuid)
        self.assertEqual(lock.target, target)
        self.assertEqual(lock.creator, 1)
        self.assertIsNotNone(lock.created_at)

    def test_unlock_target(self):
        """
        ロック対象を指定してロック解除する
        """
        # ロックを取得する
        target = str(uuid.uuid4())
        lock = self.lock_manager.lock(target, creator=1)
        # ロック対象を指定してロック解除する
        result = self.lock_manager.unlock_target(target)
        self.assertEqual(result.uuid, lock.uuid)
        self.assertEqual(result.target, target)
        # 解除したロックはLockManagerは管理しない
        self.assertFalse(self.lock_manager.contains(lock.uuid))

    def test_expire_lock1(self):
        """
        有効期間(1sec)を過ぎたロックは解除される
        """
        # ロックを取得する
        target = str(uuid.uuid4())
        lock = self.lock_manager.lock(target, creator=1)
        # 2sec待つ
        time.sleep(2)
        # 有効期間が過ぎたロックはLockManagerは管理しない
        self.assertFalse(self.lock_manager.contains(lock.uuid))
        # ロックを解除しようとする
        with self.assertRaises(Exception):
            self.lock_manager.unlock(lock.uuid)

    def test_expire_lock2(self):
        """
        有効期間(1sec)を過ぎたロックは解除される
        """
        # ロックを取得する
        target = str(uuid.uuid4())
        lock = self.lock_manager.lock(target, creator=1)
        # 2sec待つ
        time.sleep(2)
        # 有効期間が過ぎたロックはLockManagerは管理しない
        self.lock_manager.lock(str(uuid.uuid4()), creator=1)
        # ロックを解除しようとする
        with self.assertRaises(Exception):
            self.lock_manager.unlock(lock.uuid)

    def test_simulutaneous_lock(self):
        """
        同時にロック取得と解除を繰り返す
        """
        from threading import Thread
        class LockRunner(Thread):
            # Lock Managerを作成する
            lock_manager = LockManager(60)

            def run(self):
                print(f'Begin : {self.getName()}')
                # ロッを取得する
                print(f'Lock  : {self.getName()}')
                target = str(uuid.uuid4())
                lock = self.lock_manager.lock(target, 1)
                # ロックを解除する
                print(f'Unlock: {self.getName()}')
                self.lock_manager.unlock(lock.uuid)

        for i in range(10):
            LockRunner(name=str(i)).start()

    def test_simulutaneous_lock2(self):
        from kskp.store import Datum, Folder, Flow
        from threading import Thread
        class Worker():
            # Lock Managerを作成する
            lock_manager = LockManager(60)

            def run(self, q):
                # ロッを取得する
                print(f'Lock')
                lock = self.lock_manager.lock(str(uuid.uuid4()), 1)
                # 寝る
                import time
                time.sleep(1)
                # ロックを解除する
                print(f'Unlock')
                self.lock_manager.unlock(lock.uuid)
                # 
                q.get()
                q.task_done()

        worker = Worker()

        import multiprocessing
        q =  multiprocessing.JoinableQueue()

        # マルチスレッドテストを実行する
        for i in range(10):
            from kskp.store import ss
            q.put(i)
            process = multiprocessing.Process(target=worker.run, name=str(i), args=(q, ))
            process.start()

        # 全てのスレッドの終了をまつ
        q.join()

