import pprint
from .test_case_base import TestCaseBase

class DatumTest(TestCaseBase):
    """
    Datumクラスの検証をする
    """

    def test_folder_path(self):
        """
        folder_pathプロパティはライブラリにおける階層パスを返すこと
        """
        # ルートフォルダを取得する
        root = self.factory.data.load_root()

        # ルートフォルダのfolder_pathの値を取得できること
        self.assertEqual(root.folder_path, '/')

        # ルートフォルダの下にフォルダ1を作成する
        folder1 = root.create_folder('テストフォルダ1')

        # DBに保存する前のフォルダであっても、folder_pathの値を取得できること
        self.assertEqual(folder1.folder_path, '/' + root.label)

        # フォルダ1を保存する
        folder1.save()

        # 保存直後(reload前)であっても、folder_pathの値を取得できること
        self.assertEqual(folder1.folder_path, '/' + root.label)

        # フォルダ1をリロードする
        folder1 = folder1.reload()

        # folder_pathの値を取得できること
        self.assertEqual(folder1.folder_path, '/' + root.label)

        # フォルダ1の下にフォルダ2を作成する
        folder2 = folder1.create_folder('テストフォルダ1')
        self.assertEqual(folder2.folder_path, '/' + root.label + '/' + folder1.label)

        # フォルダ2を保存する
        folder2.save()
        self.assertEqual(folder2.folder_path, '/' + root.label + '/' + folder1.label)

        # フォルダ2をリロードする
        folder2 = folder2.reload()
        self.assertEqual(folder2.folder_path, '/' + root.label + '/' + folder1.label)

        # フォルダ2をほかす
        folder2.throw_away()

        # フォルダ2を削除する
        folder2.delete()        

        # フォルダ1をほかす
        folder1.throw_away()

        # フォルダ1を削除する
        folder1.delete()
