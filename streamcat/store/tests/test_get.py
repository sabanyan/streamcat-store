import io
import pprint
import unittest
from .test_case_base import TestCaseBase

class GetTest(TestCaseBase, unittest.IsolatedAsyncioTestCase):
    """
    取得処理を検証する
    """

    async def test_get_children(self):
        """
        プロジェクト直下のDatumを全て取得できること
        """
        # ルートフォルダを取得する
        root = self.finder.data.load_root()

        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('PRJ')
        project.save()

        # プロジェクトの下にフォルダを作成する
        folder = project.create_folder('FOLDER')
        folder.save()

        # プロジェクトの下にDatumを3つ作成する
        datum1 = project.create_frame('DATUM1', io.BytesIO(b'ABC'))
        datum2 = project.create_frame('DATUM2', io.BytesIO(b'DEF'))
        datum3 = project.create_frame('DATUM3', io.BytesIO(b'GHI'))
        datum1.save()
        datum2.save()
        datum3.save()

        # プロジェクト直下のDatumを全て取得する
        children = project.find_children()

        # 子要素が4つであることを確認する
        self.assertEqual(len(children), 4)
        # 子要素が作成したDatumであることを確認する
        self.assertIn(folder, children)
        self.assertIn(datum1, children)
        self.assertIn(datum2, children)
        self.assertIn(datum3, children)

        # プロジェクトを削除する
        project.throw_away()
        self.finder.data.find_trashcan().trash_all()

    async def test_get_none_children(self):
        """ 
        フォルダ直下にDatumが存在しない場合、空のリストが返されること
        """
        # ルートフォルダを取得する
        root = self.finder.data.load_root()

        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('PRJ')
        project.save()

        # プロジェクトフォルダの下にフォルダを作成する
        folder = project.create_folder('FOLDER')
        folder.save()
        folder = folder.reload()

        # フォルダの子要素を全て取得する
        children = folder.find_children()
        # 子要素が空であることを確認する
        self.assertEqual(len(children), 0)

        # プロジェクトを削除する
        project.throw_away()
        self.finder.data.find_trashcan().trash_all()

    async def test_get_paging_children(self):
        """
        プロジェクト直下のDatumをページネーション付きで取得できること
        """
        # ルートフォルダを取得する
        root = self.finder.data.load_root()

        # ルートフォルダの下にプロジェクトを作成する
        project = root.create_project_folder('PRJ')
        project.save()

        # プロジェクトの下にDatumを3つ作成する
        datum1 = project.create_frame('DATUM1', io.BytesIO(b'ABC'))
        datum2 = project.create_frame('DATUM2', io.BytesIO(b'DEF'))
        datum3 = project.create_frame('DATUM3', io.BytesIO(b'GHI'))
        datum4 = project.create_frame('DATUM4', io.BytesIO(b'JKL'))
        datum5 = project.create_frame('DATUM5', io.BytesIO(b'MNO'))
        datum1.save()
        datum2.save()
        datum3.save()
        datum4.save()
        datum5.save()

        # プロジェクト直下のDatumを2つずつ取得する(1ページ目)
        # Datumは種別順・作成時刻順でソートされる
        children = project.find_children(limit=2, offset=0)

        # 子要素が2つであることを確認する
        self.assertEqual(len(children), 2)
        # 子要素が作成したDatumであることを確認する
        self.assertIn(datum5, children)
        self.assertIn(datum4, children)

        # プロジェクト直下のDatumを2つずつ取得する(2ページ目)
        children = project.find_children(limit=2, offset=2)

        # 子要素が2つであることを確認する
        self.assertEqual(len(children), 2)
        # 子要素が作成したDatumであることを確認する
        self.assertIn(datum3, children)
        self.assertIn(datum2, children)

        # 子要素が1つであることを確認する
        children = project.find_children(limit=2, offset=4)
        self.assertEqual(len(children), 1)
        # 子要素が作成したDatumであることを確認する
        self.assertIn(datum1, children)

        # プロジェクトを削除する
        project.throw_away()
        self.finder.data.find_trashcan().trash_all()

    async def test_get_paging_children_by_reader(self):
        """
        プロジェクト直下の参照権限のあるDatumだけをページネーション付きで取得できること
        """
        # ルートフォルダを取得する
        root1 = self.finder.data.load_root()

        # USER1はルートフォルダの下にプロジェクトを作成する
        project1 = root1.create_project_folder('PRJ1')
        project2 = root1.create_project_folder('PRJ2')
        project3 = root1.create_project_folder('PRJ3')
        project4 = root1.create_project_folder('PRJ4')
        project5 = root1.create_project_folder('PRJ5')
        project1.save()
        project2.save()
        project3.save()
        project4.save()
        project5.save()
        project1 = project1.reload()
        project2 = project1.reload()
        project3 = project1.reload()
        project4 = project1.reload()
        project5 = project1.reload()

        # 作成を確定する
        self.finder.end()

        # システムフォルダを取得する
        datadst_project = self.finder.data.find_by_keyword('データデスト📂')[0]
        activity_folder = self.finder.data.load_activity_folder()
        cache_folder = self.finder.data.load_cache_folder()
        trashcan = self.finder.data.find_trashcan()

        # USER2はルート直下のプロジェクトを取得する
        root2 = self.finder2.data.load_root()
        children = root2.find_children()
        # 子要素が4つであることを確認する
        self.assertEqual(len(children), 4)
        # 子要素はシステムフォルダであることを確認する
        self.assertIn(datadst_project, children)
        self.assertIn(activity_folder, children)
        self.assertIn(cache_folder, children)
        self.assertIn(trashcan, children)

        # USER2はルート直下のプロジェクトを2つずつ取得する(1ページ目)
        root2 = self.finder2.data.load_root()
        children = root2.find_children(limit=2, offset=0, prev_folder_path=True)
        # 子要素が2つであることを確認する
        self.assertEqual(len(children), 2)
        # 子要素はシステムフォルダであることを確認する
        self.assertIn(datadst_project, children)
        self.assertIn(activity_folder, children)

        # プロジェクトを削除する
        project1.throw_away()
        project2.throw_away()
        project3.throw_away()
        project4.throw_away()
        project5.throw_away()
        self.finder.data.find_trashcan().trash_all()
