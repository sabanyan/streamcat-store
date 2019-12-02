#!/usr/bin/env python3

# 2019.07.12 Version 0.3

"""
CSV要素の抽出コマンド
入力されたプレーンテキストデータから、CSV要素（観測値、列名）を抽出する
将来的には、属性は分けて出力する※現状出力されない

●抽出のルール
    １.観測値開始位置を指定する
    2.観測値より上では、列名行と列属性を取得する
      列名は観測値とともに出す。
      属性は出力しない
    ３．観測値範囲内では、不要行の指定に一致した部分を除く
    　　不要行指定に一致する条件が繰り返し出現する場合には、その全てが対象になる

●引数
 辞書argsとして与えられる。オプション、入出力は所定のキー項目の値を受け取る
    ●オプション(UI表示順)
    argsのキー            型     省略    UI表示名                     説明
    field               int    可      列名行(1始まり行番号)          ここで指定した行を列名行とする(１行のみ指定)

    attr                 str    可      列属性(1始まり行番号範囲)     ここで指定した範囲を列属性とみなす。行番号範囲で指定する。(例：3, 例: 1-10)

    observe              int    不可    観測値開始行(1始まり行番号)    ここで指定した行以降を観測値とみなす

    except_chr          str    可      不要行開始条件：文字列指定        ここで指定した条件に一致する行から、終了条件に一致する範囲を不要行とみなす。
                                                                    終了条件が指定されてない場合には、ここで指定された条件に一致する行のみを不要行範囲とみなす
                                                                    条件は正規表現で指定する

    except_null         bool   可      不要行開始条件：空行指定         開始行条件に空行を指定する場合に指定する

    except_end_chr       str    可      不要行終了条件：文字列指定      不要行範囲終了条件指定する。指定方法は、開始からの行数か、正規表現で指定する
                                                                    終了行が指定されてない場合には、開始行のみを範囲とみなす

    except_end_range     int    可      不要行終了条件：固定行数指定      終了条件を、開始からの行数で指定したい場合に使用する

    except_end_null      bool   可      不要行終了条件：空行指定         終了行条件に空行を指定したい場合に使用する

    ●入出力
    argsのキー   型   省略   UI表示名   説明       
    i          str  不可    入力      CSVであれば受付できる
    o          str  不可    出力      NYSOLで受け付ける形式を満たさない場合がある

●引数間のルール
 不要行開始条件、不要行終了条件     それぞれ１つしか指定できない

 列名行、列属性行指定   観測値開始行より上で指定する

●不要行開始条件、終了条件の判断
 開始判断がされた行は終了判断の対象にはしない。
 そのため、開始と終了条件が同じ場合は、先頭からの出現順で、奇数番目から偶数番目までを不要と判断する

例：開始、終了条件がどちらも"==="のとき
=== (不要) 
1,2 (不要)
=== (不要)
3,4
=== (不要)
5,6 (不要)

"""
import csv
import sys
import traceback
import re

ErrMsg={
        '1':"観測値開始行を行番号で入力してください",
        '2':"列名行は行番号で指定してください",
        '3':"列名行は観測値開始行より上で設定してください",
        '4':"属性行は行番号で指定してください",
        '5':"属性行は観測値開始行より上で指定してください",
        '6':"不要行開始条件を指定してください",
        '7':"不要行開始条件が複数指定されています",
        '8':"不要行終了条件が複数指定されています",
        '9':"不要範囲指定は行数で行ってください"
        }

def check_args_empty(args):
    """
    引数の値に、""が来た場合の処理を書く関数

    文字列で指定する引数にユーザー指定がない場合、項目がargsに存在しない場合と、項目はあるが値が""で渡される場合がある。
    この問題はKSKPの仕様の問題で、将来的にはどちらかに統一されるが
    暫定処置兼安全策として、コマンド側でもどちらかに合わせることになった。

    このコマンドでの対応
        文字列引数　・・・　"A":"" なら、項目自体を削除
        ブーリアン  ・・・　"A":"" なら、"A":false
    　ブーリアンの場合は問題発生していないが、念の為入れる。
    """
    #文字列渡し引数のリスト
    args_str = ["observe","field",'attr','except_chr','except_end_chr','except_end_range']
    
    for arg in args_str:
        if args.get(arg) is '':
            args.pop(arg)
    
    # bool渡し引数のリスト
    args_bool = ["except_null","except_end_null"]

    for arg in args_bool:
        if args.get(arg) is '':
            args[arg] = False
    
    return args



def check_args(args):
    """
    引数の型変更と、整合性を確認してエラー出力をする関数
    出力されるargs内の引数は、数値指定の場合は数値に置き換えている
    
    引数整合性確認変更時の注意：
    →コマンドJSONでもやってるので変更を反映させること
     ただし、属性範囲指定と観測値開始指定の比較はコマンドJSONの機能では不可能なためやっていない。
     （2−3のようなハイフン区切りをパースして条件をつくることができない）
    """
    # 指定判断の正規表現文字列
    re_Natural = '^[1-9][0-9]*$'
    re_natural_range = '^[1-9][0-9]*(-[1-9][0-9]*)?$'

    observe = args.get('observe')
    if observe is None:
        raise Exception(ErrMsg['1'])
    elif re.search(re_Natural,observe):
        args['observe'] = int(observe)
    else:
        raise Exception(ErrMsg['1'])

    field = args.get('field')
    if field is None:
        pass
    elif re.search(re_Natural,field):
        if int(field) >= args['observe']:
            raise Exception(ErrMsg['3'])
        else:
            args['field'] = int(field)
    else:
        raise Exception(ErrMsg['2'])

    attr = args.get('attr')
    if not attr:
        pass
    elif re.search(re_natural_range,attr):
        attr = list(map(int,attr.split("-")))
        if max(attr) >= args['observe']:
            raise Exception(ErrMsg['5'])
        else:
            args['attr'] = attr #リストを代入している
    else:
        raise Exception(ErrMsg['4'])

    # 不要行指定条件判断
    flg_start = 0
    if args.get('except_chr'):
        flg_start += 1
    if args.get('except_null'):
        flg_start += 1
    
    flg_end = 0
    if args.get('except_end_chr'):
        flg_end += 1
    if args.get('except_end_null'):
        flg_end += 1
    if args.get('except_end_range'):
        flg_end += 1
    
    if flg_start == 0:
        if flg_end >= 1:
            raise Exception(ErrMsg['6'])#不要行開始条件の指定がない
    elif flg_start >= 2:
        raise Exception(ErrMsg['7'])#不要行開始条件指定が複数ある
    else:
        if flg_end >= 2:
            raise Exception(ErrMsg['8'])#不要範囲終了条件が複数

    #不要行数指定の形式確認
    except_end_range = args.get('except_end_range')
    if except_end_range is None:
        pass
    elif re.search(re_Natural,except_end_range):
        args['except_end_range'] = int(except_end_range)
    else:
        raise Exception(ErrMsg['9'])

    return args


def readline(in_file):
    '''
    CSVを１行ずつ取得するジェネレータを作る
    '''
    reader = csv.reader(in_file, delimiter=',', quotechar='"', strict=True)
    for line in reader:
        yield line


def processAndwriteline(gen_reader, args, out_file):
    '''
    引数をもとに条件判断をして、合う行のみを出力する
    '''

    writer = csv.writer(out_file, delimiter=',', quotechar='"', strict=True)

    field = args.get('field')
    observe = args.get('observe')
    attr = args.get('attr')#例1:[2], 例2:[3,10], 例3:[10,3]
    
    except_chr = args.get('except_chr') 
    except_null = args.get('except_null')

    except_end_chr = args.get('except_end_chr')
    except_end_null = args.get('except_end_null')
    except_end_range = args.get('except_end_range')

    exceptline = False
    count_exceptline = 0

    for lineNo,line in enumerate(gen_reader,1):
        if lineNo < observe:
            if field:
                if lineNo == field:
                    writer.writerow(line)

            if attr:
                if min(attr) <= lineNo <= max (attr):
                    # 属性を分けて出力できるようになったら、ここに出力を書く。
                    pass
        else: #観測値の範囲内
            if not exceptline:
                # 不要範囲開始条件一致を判断
                if except_chr is not None:#空で正規表現マッチすると、常にマッチするので、除外している
                    match = re.search(except_chr,','.join(line))
                elif except_null:
                    match = re.search('^$',','.join(line))
                else:
                    match = None #指定がなかったとき。matchがないと、書き出し条件判断で失敗して例外がでる
                    # pass
                
                if not match:#書き出し条件判断
                    writer.writerow(line) # 一致していない場合は出力
                else:
                    exceptline = True #一致していたら出力しないで、除外フラグをたてる
                    count_exceptline = 1

            else:
                count_exceptline += 1
                if except_end_chr is not None:#空で正規表現マッチすると、常にマッチするので、除外している
                    end_match = re.search(except_end_chr,','.join(line))
                elif except_end_null:
                    end_match = re.search('^$',','.join(line))
                elif except_end_range is not None:
                    end_match = (count_exceptline == except_end_range)
                else :
                    end_match = (count_exceptline == 1)#指定なかったときの条件

                if end_match:
                    exceptline = False
                    count_exceptline = 0

def main(args,in_fd,out_fd):
    try:
        args = check_args_empty(args)
        args = check_args(args)
        # sys.stderr.write("args: {}\n".format(args))
        reader = readline(in_fd)
        processAndwriteline(reader, args, out_fd)

    except Exception :
        with open('/dev/stderr', 'w') as fpe:
            traceback.print_exc(file=fpe)
