"""
KSKP独自コマンド雛形  1入力１出力型
ver 0.4.0

16進数バイナリフラグ項目の列展開コマンド
指定された列を２進数変換して、参照データの列並びと照合し、指定にある列の値を抽出する。

●引数
argsのキー     型    省略      UI表示                       説明
hex         文字列   不可    バイナリ項目                    ここで指定した入力データの列をフラグに変換する
f           文字列   不可    追加列                         ここで指定した参照データの列をフラグとして出力する
comp    bool    可     桁数一致しない場合異常値とみなす   参照と列数が一致しない値は異常値とみなす。この場合、参照の列名の重複は許容されない        


●入力（ファイルディスクリプタとして受け取り）
引数      省略    UI表示名            説明
i_fd      不可    i(入力ポート)      展開したい列を持ったデータ
m_fd      不可     m               バイナリ列内の並びと対応した列名を持ったデータ

●出力（ファイルディスクリプタとして受け取り）
引数      省略    UI表示名            説明
o_df      不可      O              バイナリ列を追加したデータ

●引数ルール
f            Nysolのワイルドカード指定可能
comp    デフォルトでTrue指定


●処理ルール
    １，参照ファイルの列名を指定列名の対応を見て取得する位置を決める
    ２，左から、各文字を16進数へ変換する。
       16進数表記にない文字はnullとみなす。
    3，変換した文字列の該当箇所を出力する。

    ●完全一致指定（comp=True)の処理
    １．参照列名重複の許容
      部分一致    許容され、重複している列名を指定した場合は、一番左にある列を対象とする
      完全一致    許容されない（例外出力）
    ２. Null出力
      部分一致    変換後の0/1文字列のなかで、参照位置の値がないか、Nullの場合にNullとして出力する。
      完全一致    参照列数と対象の値の長さが合わない場合にNullを出力する

    ●ワイルドカード指定 Nysol仕様に準拠
    【指定方法】
        ●複数指定可能（例：A*,B?)
        ●通常列名指定と併用できる（例：AB,C*)
    【エラー処理】
        ワイルドカード指定  対象がない場合はエラーにならない
        通常列名指定       対象がない場合はエラーになるい

●パフォーマンス
    実装時は、動くことを優先したため、正直あまり効率的な実装とは言えない。
    実装方法を見直せば効率化できることは多いと思う。
    パフォーマンスが問題になった場合は、以下を優先して検討してほしい。
    確実にパフォーマンス向上が見込める。

    1.HEX→BIN変換
        現状１文字単位変換。
        値を一括して変換にすれば、イテレーションと処理回数が桁違いに減る
        →【問題】異常値対応

    2.変換対象を絞る
        現状は変換後、対象に該当する部分を取っている。
        対象該当部のみ取ってから変換すると、処理量が減る。
        ユーザー想定の処理量にも合うので、こうすべきだと思うが実力不足でやめた。
        →仕様への影響はなし。インデックスをうまく反映させればOK


●前提情報の共有
    実装見直し時に考慮事項にしてほしいと考えて、前提としたことを記載した。
    前提を見直すと、品質向上や処理速度改善が見込めると思うが、そうしていいかは熟慮してほしい。

    ■値は全て同じ長さで来るとは限らない
    ■値にNullを示す空白文字が混ざっているかも →変換できない文字列があったら、Nullとする
    ■値は左詰で挿入される。→左からの順番が同じであれば、同じ項目とみなしている
"""

import sys
import csv
import traceback
import re

ErrMsg = {
    '1': 'バイナリ項目を指定してください',
    '2': 'バイナリ項目は複数指定できません',
    '3': '指定された列名が参照データにありません',
    '4': '指定された列名が入力データにありません',
    '5': 'バイナリ項目の値と、参照データの列数が合いません',
    '6': '出力データに重複列名が発生するため、処理を停止しました',
    '7': '参照データの列名に重複があります',
    '8': '入力データの列名に重複があります',
    '9': '抽出対象になる参照データ列名を指定してください',
    '10': '参照データ列名の指定が正しくありません',
    '11': '入力データに列数の異なる行が含まれていたため、処理を停止しました',
    '12': '参照データに列名以外の値が含まれています'
}


def check_args_empty(args):
    """
    引数が入力されてない場合の受け渡しに一貫性を持たせる関数

    例:AとBが文字列型、Xがbool型のとき
        args={"A":"","B":1,"X":""}  => args={"B":1,"X":False}
    とする。

    ●処理ルールの変更は不可
        特別な理由がない限りは上記に合わせる。
        理論上、個々のコマンドで決めても問題はないが、将来の改修性を考慮した。

    ●設定の経緯
    現状、引数に設定がない場合の受け渡し仕様が定まっていないため
    引数自体が渡されない場合と、値が""で渡される場合がある

    理想型は仕様を統一することだが、仕様変更にかかる時間と、機能的安全性から
    コマンド側でも確認する方が望ましいと判断した。

    なお、bool型では常に"A":Falseになっているが、引数の型によって対応を分けることで
    将来的に別の問題を引き起こす可能性があると考えて、処理対象とした。
    """

    # 文字列渡し引数のリスト
    args_str = ["hex", "f"]

    for arg in args_str:
        if args.get(arg) == '':
            args.pop(arg)

    args_bool = ["comp"]

    for arg in args_bool:
        if args.get(arg) == '' or args.get(arg) is None:
            args[arg] = True
    return args


def check_args(args):
    """
    引数の型を変更とエラー処理をする関数
    （コマンド固有の内容）
    """

    # 入力のバイナリデータ項目指定条件（必須）
    hex = args.get('hex')
    if not hex:
        raise Exception(ErrMsg['1'])

    # 1項目のみ指定させたい
    if not re.search('^[^,]+$|^$', hex):
        raise Exception(ErrMsg['2'])

    # 参照列名指定（必須項目）
    f = args.get('f')
    if not f:
        raise Exception(ErrMsg['9'])

    # 処理できない条件以外（mcutのfと同じ条件にする）
    if not re.search("^[^,:]+(:[^,:]+)?(,[^,:]+(:[^,:]+)?)*$", f):
        raise Exception(ErrMsg['10'])

    # 指定が重複している場合
    f_tmp = f.split(",")
    if len(f_tmp) != len(set(f_tmp)):
        # debug_msg("# f #",f_tmp)
        raise Exception(ErrMsg['10'])
    del f_tmp

    return args


def debug_msg(msg, val):
    """
    エラー出力したい項目があったら使う
    """

    if msg is None:
        msg = ""
    if val is None:
        val = ""
    sys.__stderr__.write("{0}:{1}\n".format(msg, val))


def readline(in_file):
    """
    入力をCSVとして１行ずつ取得するジェネレータ
    （共通の内容）
    """

    reader = csv.reader(in_file, delimiter=',', quotechar='"', strict=True)
    # print(reader)
    for line in reader:
        yield line


def ny_wildcard(wc_str):
    """
    ワイルドカード文字列を正規表現に変換する関数
    """

    # re_wc = []
    # for wc_str in wc_str:
    re_str = ''
    for c in wc_str:
        if c == '*':
            re_str += '\w*'
        elif c == '?':
            re_str += '\w'
        else:
            re_str += c

        # re_wc.append(re_str)

    return re_str

def is_hex(val):
    '''
    値が16進数文字列として正しいことを判断する関数
    '''
    import re
    regex = '^[0-9A-Fa-f]+$'
    match = re.fullmatch(regex,val)
    
    return match


def processAndwriteline(gen_reader_i, gen_reader_m, args, out_file):
    """
    ■処理の流れ
    以下の流れ＆目的で処理
    １.参照データ処理
        対象となる列名と列番号取得
    ２．入力データ処理（列名）
        対象となる列名と、列番号取得
    ３．入力データ処理（値）
        値を全て変換し、指定された部分を取る
        ●部分一致指定と、異常値対応を考え、１文字単位で処理
        （一度に変換すると、異常値が途中に混ざっていた場合に対応できない）
        ●16進数変換可能な値は変換、それ以外はNull置換
        ●部分一致指定ない場合は、値全体をNull置換
    
    ■処理の基準は列番号
        行単位処理で列名との対応とれないので、ヘッダで取った列名＝列番号対応をもとに処理している

    ■エラー処理
        列名と列数に関するエラー処理を、なるべく早いタイミングで入れている
        順番変更は後処理の前提が満たされなくなるので注意
        エラー処理条件は、
            列名： 重複発生、指定がない場合にエラー
            列数： 列数不一致が発生した場合（ヘッダを基準に判断）
    """

    hex = args['hex']
    flds = args['f']
    comp = args['comp']

    flds = flds.split(",")

    # コマンド共通
    writer = csv.writer(out_file, delimiter=',', quotechar='"', strict=True)

    # 参照データの処理
    header = True
    m_cols = ''  # 参照ファイルの列数

    # 取得する列名とインデックスのリスト
    sel_dgts = []  # 抜き出す位置のインデックスリスト
    sel_flds = []  # 抜き出す列名のリスト

    for line in gen_reader_m:
        # debug_msg("参照のヘッダ",line)
        if header:
            flds_tmp = []
            for fld in flds:
                # debug_msg("@@@ fld type",fld)
                # ワイルドカード指定
                if '*' in fld or '?' in fld:
                    re_str = ny_wildcard(fld)  # 正規表現文字列に変換

                    flds_wc = []
                    for m_fld in line:
                        if re.fullmatch(re_str, m_fld):
                            flds_wc.append(m_fld)

                    if len(flds_wc) > 0:
                        flds_tmp.extend(flds_wc)

                # 通常の列名指定
                else:
                    if fld in line:
                        flds_tmp.append(fld)
                    else:
                        # 対象がない場合はエラーにする
                        raise Exception(ErrMsg['3'])

            flds = flds_tmp

            # 例外処理 指定列名がない場合
            # debug_msg("# flds 完成# ",flds)
            if len(flds) == 0:
                raise Exception(ErrMsg['3'])

            if comp:
                # 例外処理 参照列名重複
                if len(line) != len(set(line)):
                    raise Exception(ErrMsg['7'])

                # 参照列数取得（あとで測定値の長さと照合したい）
                m_cols = len(line)

            for m_idx, m_name in enumerate(line):
                for fld in flds:
                    if fld in line:
                        # 部分一致指定で、参照列名に重複があった場合は、先に取った列が優先される
                        # 完全一致指定の場合は、重複解消されずに、出力列名重複エラーになる
                        if m_name == fld and m_name not in sel_flds:
                            sel_flds.append(m_name)
                            sel_dgts.append(m_idx)

            # debug_msg("選択した列#",sel_flds)#消しても処理には影響しない

            header = False
        else:
            # 参照にヘッダ以外があったときはエラーを出す
            raise Exception(ErrMsg['12'])

    # 例外：参照データに該当列名がない
    # 参照データが空のときもここで処理する(ジェネレータは空データを取るときは何も返さないので)
    if sel_flds == []:
        raise Exception(ErrMsg['3'])

    # 入力データの処理
    header = True
    for line in gen_reader_i:
        # ヘッダの条件を確認し、出力データのヘッダをつくる
        if header:
            # debug_msg("入力行",line)
            # 重複列名がある場合は、エラーを出す
            if len(line) != len(set(line)):
                raise Exception(ErrMsg['8'])

            if hex in line:
                # 対象列インデックス取得
                hex_idx = line.index(hex)
            else:
                # 対象列名がない場合は、エラーを出す
                raise Exception(ErrMsg['4'])

            # 入力データ列数基準値
            input_col_num = len(line)

            # 対象の列名を削除、出力データの列名を作成
            # del line[hex_idx]
            line.extend(sel_flds)

            # 列名重複確認
            if len(line) != len(set(line)):
                raise Exception(ErrMsg['6'])

            # 出力データのヘッダを出力
            writer.writerow(line)

            header = False

        # 変換処理
        else:
            # 例外処理；列数不一致
            if len(line) != input_col_num:
                raise Exception(ErrMsg['11'])

            # 入力から対象値取得
            val = line[hex_idx]
            bit_val = []  # 0/1文字列のリスト

            #16進数文字列に含まれない値は
            if is_hex(val):
                # 全体一致指定時は、桁数が合わない場合はNullにする
                if comp and len(val) * 4 != m_cols:
                    bit_val = ' ' * len(line)

                else:
                    bit_val = format(int(val, 16), '0{}b'.format(len(val)*4))
 
            else:
                bit_val = ' ' * len(val) * 4 # 変換できない値はnull置換して出す


            # debug_msg("ビット列 ",bit_val)
                # bit_val.append(B)

                # bit_val = ''.join(bit_val)  # 文字列として結合してビット列にする



                # for hex_val in val:  # 1文字単位で変換
                #     try:
                #         B = format(int(hex_val, 16), '04b')
                #         # bit_val.append(B)
                #     except ValueError:
                #         B = ' ' * 4  # 変換できない値はnull置換して出す

                #     bit_val.append(B)

                # bit_val = ''.join(bit_val)  # 文字列として結合してビット列にする



            # 出力するビットを選ぶ
            sel_vals = []
            for b_idx, b in enumerate(bit_val):
                if b_idx in sel_dgts:  # 左からの位置が合うものを取っている
                    if b == ' ':
                        sel_vals.append('')  # 空白をnullで出す
                    else:
                        sel_vals.append(int(b))

            while len(sel_vals) < len(sel_flds):  # 出力の列数と合っていない場合は、不足分のNullを足す
                sel_vals.append('')

            # del line[hex_idx]  # 元の値を消す
            line.extend(sel_vals)  # 行末にビット列追加

            writer.writerow(line)  # 出力


def main(args, in_fd, m_fd, out_fd):
    try:
        args = check_args_empty(args)
        args = check_args(args)

        reader_i = readline(in_fd)  # コマンド共通
        reader_m = readline(m_fd)
        processAndwriteline(reader_i, reader_m, args, out_fd)

    except Exception:
        with open('/dev/stderr', 'w') as fpe:
            traceback.print_exc(file=fpe)
