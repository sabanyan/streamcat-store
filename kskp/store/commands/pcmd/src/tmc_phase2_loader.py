
'''
tmcローダー_ph2 ver1.0

概要
複数あるファイルをワイルド−カードで指定してマージする
ヘッダの列名差を吸収してマージすることができる

注意
●ASCII & LFにしか対応していない

※このバージョンでは、ファイル名追加オプションに対応できていない。
オプション指定時は、２行目が空行になったファイルができる。

●入出力
入力：なし（targetオプションで対象になるファイルを読み込む）
出力：{'o': nysol_module_o}

●オプション
argsのキー      型   指定必須 説明
target        str   Y       入力ファイル指定（globモジュールの指定方法が使える）
isSort        bool  N       ファイル作成日時でソート（昇順）       （デフォルトはFalse）
hasHeaderDiff bool  N       ヘッダーが異なるファイルを列名で併合する （デフォルトはFalse)
needFilenames bool  N       ファイル名を値として取り込む           （デフォルトはFalse)
tmp_Path      str   N       作業パス指定

o             str   Y       出力ファイル名（テストのときにつけていた）

要件
●ヘッダが異なるCSVを、列名でマージして出力する
●後の処理効率を考えて、出力ファイルは時刻昇順でマージする
●ファイルの検索条件を指定できる
●ファイル検索は、サブディレクトリも対象にできる
●ファイル名を値として追加できる

前提
●列名が同じ列は、同じ意味
●行の並びは、時刻昇順になっている
●ヘッダは必ずファイルの１行目に存在する。また、１行目以外の値は、全て観測値とみなして良い
●ファイルは全て、CSV形式を満たしている

処理の概要
１．指定されたファイルを検索し、ファイルリストを作成する
２．ファイルリストをファイル作成時刻で昇順ソートする
３．全ての列名を持ったファイルを作成する
４．全ての列名を持ったファイルと、ファイルリストのファイルを併合する

注意
●ヘッダの差があるファイルを読み込む際に、hasHeaderDiff=Falseとした場合
→読み込み順先頭のファイルの列名で出力される。

要検討：ファイルヘッダー差有無をエラー処理で出力
●エラー処理で、ファイルのヘッダ不一致を確認する仕様も考えたが
 全ファイルのヘッダを取る処理は重いため、しないことにした。

'''

import os
import sys
import csv
import pathlib
from operator import itemgetter
import nysol.mcmd as nm
from ordered_set import OrderedSet
import tempfile
from datetime import datetime 


ErrMsg = {
    '1': '対象ファイルがありません。指定を見直してください。'
}

def check_args(args):
    '''
    argsのデフォルト値を追加する関数
    '''

    # bool型
    args_bool = ['isSort', 'hasHeaderDiff', 'needFilenames']

    # falseを追加
    for arg in args_bool:
        if args.get(arg) == '' or args.get(arg) is None:
            args[arg] = False
    
    return args


def makeFilelist(args):
    '''
    ファイルパスジェネレータを作成する
    ジェネレータはファイルパスと作成時間が入ったタプルを返す
    （開発用）：取得するファイル情報を見直す場合は、この関数に追加するといい
    '''
    p = pathlib.Path("{}".format(args['tmp_Path']))
    sys.stderr.write("{}\n".format(args['target']))
    f_info_gnt = ((path, path.stat().st_mtime) for path in p.glob("{}".format(args['target'])))

    return f_info_gnt


def makeMergelist(args,f_info_gnt):
    '''
    pathリストを出す
    作成時刻昇順ソートする場合は、ソートする
    '''
    filelist = list(f_info_gnt)

    if args['isSort'] == True:
        # filelist = list(f_info_gnt)
        filelist.sort(key = itemgetter(1))
    
    mergelist = [file_info[0] for file_info in filelist]
    del filelist

    return mergelist


def makeOutHeader(mergelist):
    '''
    全ファイルの列名を集約したリストをつくる
    '''

    def csv_line_gnt(r_fd):
        '''
        CSVファイルを１行ずつ出すジェネレータを返す
        '''
        # reader = csv.reader(r_fd, delimiter=',',quotechar='"',lineterminator='\r\n') # win形式
        reader = csv.reader(r_fd, delimiter=',',quotechar='"',lineterminator='\n')
        for row in reader:
            yield row

    def getHeader(path):
        '''
        ファイルのヘッダ（１行目）を取得する
        '''
        sys.stderr.write("Collecting Header : {}\n".format(path))
        # r_fd = open(path,'r',newline='',encoding='cp932')#Widowsファイルを読むため
        r_fd = open(path,'r',newline='') #UTF-8前提
        row_gnt = csv_line_gnt(r_fd)
        header = next(row_gnt)
        r_fd.close()

        return header

    whole_header = []

    for path in mergelist:
        header = getHeader(path)
        whole_header = OrderedSet(list(whole_header) + header)
        # 後で扱いやすくするためリスト化した
    return list(whole_header)

def writeOutHeader(whole_header):
    '''
    ヘッダのみのファイルを出力し、そのパスを返す
    【注意】ヘッダのみファイルの末尾
    mcatが、headerのみファイルの最後が改行で終わっていると、なぜか２行目があると読み取ってしまい
    出力データの列名の対応関係が、間違った状態になった。
    ヘッダのみファイルの行末が、改行にならないように文字列で出すとうまくいった。
    '''

    # tmpファイル作成(delete＝Falseにしないと、後で開けない)
    tmp_fd = tempfile.NamedTemporaryFile(mode="w", delete=False, newline='') 

    # 行末に改行が入らないよう、文字列として書き出す
    tmp_fd.write(",".join(whole_header))
    tmp_fd.close()

    return tmp_fd.name

def main(args):
    '''
    ヘッダ差ありのときは、吸収のための処理をしている指定の有無で処理を分けた
    '''

    args = check_args(args)

    sys.stderr.write("#START# tmc_loader {0} {1}\n".format(args,datetime.now().strftime("%Y/%m/%d %H:%M:%S")))
    
    f_info_gnt = makeFilelist(args)
    mergelist = makeMergelist(args, f_info_gnt)  # 読み込み順にソートされたリスト

    # 読み込むファイルが無いときは、処理を止めてエラーを出す
    if len(mergelist) == 0:
        raise Exception(ErrMsg['1'])

    if args['hasHeaderDiff'] == True:
        whole_header = makeOutHeader(mergelist)
        head_path = writeOutHeader(whole_header)

    mergelist = list(map(lambda path:str(path), mergelist))


    if args['hasHeaderDiff'] == True:
        mergelist.insert(0, head_path)

    ## 実装時テスト（ファイル出力化）
    # nm.mcat(nostop=args['hasHeaderDiff'], add_fname=args['needFilenames'], i=','.join(mergelist), o=args['o']).run(runlimit=128)

    # Nysolのストリームとして出力する
    cmd_o = nm.mcat(nostop=args['hasHeaderDiff'], add_fname=args['needFilenames'], i=','.join(mergelist))
    sys.stderr.write("{0}\n".format(','.join(mergelist)))
    sys.stderr.write("#END#  tmc_loader {0} {1}\n".format(args,datetime.now().strftime("%Y/%m/%d %H:%M:%S")))

    return cmd_o, head_path
