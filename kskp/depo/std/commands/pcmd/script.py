# 独自コマンド
import sys
import copy
import uuid
import nysol.mcmd as nm
import numpy as np
import nysol.util.mtemp as mtemp
from nysol.util._utillib import mcsvout as mcsvout
from pathlib import Path

from kskp.store import NysolModule
from kskp.core import Command, Port

PCMD_DIR = Path(__file__).resolve().parent

class PCommand(Command):
    """
    独自コマンドのスーパークラス
    TODO: そういえばいつから独自コマンドはpcmdに。。。？
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]

    def replace_args(self, args):
        """
        nm.cmdで実行可能なargsに変換（文字列にして並べる）
        """
        args_string = ''
        for key, value in args.items():
            if isinstance(value, bool):
                if value == True:
                    args_string +=  ' -' + key
            else:
                args_string += ' %s=%s' % (key, value)

        return args_string

    def module(self, flow_obj, args):
        """
        moduleでラップする
        """
        import nysol.mcmd as nm
        flow_obj <<= nm.cmd(args)

        nysol_module = NysolModule()
        nysol_module.set_content(flow_obj)

        return nysol_module

    def get_field_names(self, nysol_module):
        """
        NYSOLフローの結果データのヘッダ行を取得する
        """
        # ヘッダ行を取得するときに標準エラーに出力されるエラーメッセージを取得するため
        # FieldNamesCommandを用いる
        from kskp.depo.std.commands import FieldNamesCommand
        fldNamesCmd = FieldNamesCommand()
        results = fldNamesCmd.run(args={}, inputs={'i': nysol_module})
        # 'i'キーへの入力結果は'i'キーを指定して取得する
        return results['i']

    def run(self, args, inputs):
        """
        実際実行(for override)
        """
        pass


class SmlModelingCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i'].content

        args_string = (PCMD_DIR / 'src/sml_modeling.sh').as_posix()
        args_string += ' kcmd_path=' + (PCMD_DIR.parent / 'kcmd/src').as_posix()
        args_string += ' temp_path=' + (PCMD_DIR / 'tmp').as_posix()
        args_string += ' model_data_path=' + (PCMD_DIR / 'model').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}


class ColumnListCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i'].content

        args_string = (PCMD_DIR / 'src/column_list.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}


class ColumnGroupingNameCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i'].content

        args_string = (PCMD_DIR / 'src/column_grouping_name.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}


class ColumnBlankNameCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i'].content

        args_string = (PCMD_DIR / 'src/column_blank_name.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}


class ColumnsToRowsCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i'].content

        args_string = (PCMD_DIR / 'src/columns_to_rows.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}


class ColumnUniqueNameCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i'].content

        args_string = (PCMD_DIR / 'src/column_unique_name.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}


class ColumnNameCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i'].content

        args_string = (PCMD_DIR / 'src/column_name.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}


class GroupbyCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i'].content

        args_string = (PCMD_DIR / 'src/groupby.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}


class GroupbyColumnsCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i'].content

        args_string = (PCMD_DIR / 'src/groupby_columns.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}


class CheckDuplicateRowsCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):

        COLNUM = '__colnumber__'
        DUPCOUNT = '__duplicate_row_count__'
        DUPNUM = '__duplicate_number__'
        
        targetcols = args.get('k')
        
        
        cmd_i = None
        cmd_i <<= inputs['i'].content

        # number each line
        cmd_i <<= nm.mcal(a = COLNUM, c = 'line()+1')
        
        cmd = None
        cmd <<= nm.mcut(i = cmd_i, f = targetcols)
        
        # count dupes
        cmd <<= nm.mnumber(k = targetcols, s = targetcols, a = DUPCOUNT, S = 1)
        
        # select rows with more than one instance
        cmd <<= nm.msel(c = f'${{{DUPCOUNT}}}>=2')
        
        cmd <<= nm.mstats(k = targetcols, f = DUPCOUNT, c = 'max')
        

        cmd_o = None
        cmd_o <<= nm.mnjoin(i = cmd_i, m = cmd, k = targetcols)
        cmd_o <<= nm.mnumber(k = targetcols, s = targetcols, a = DUPNUM, S = 1)

        cmd_o <<= nm.mfldname(q = True)
        
        # pass output
        nysol_module_o = NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}
        
        # f = None
        # f <<= inputs['i'].content

        # args_string = (PCMD_DIR / 'src/check_duplicate_rows.sh').as_posix()
        # args_string += self.replace_args(args)

        # return {'o': self.module(f, args_string)}


class MergeFSCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i'].content

        args_string = (PCMD_DIR / 'src/merge_FS.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}


class MergeIbutsuCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i'].content

        args_string = (PCMD_DIR / 'src/merge_ibutsu.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}


class WinCp932ReadCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i'].content

        args_string = (PCMD_DIR / 'src/windows_cp932_csv_read.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}

       #pythonによる変換
       #不安定なので無効化しておく

       #def Cp932_to_utf8():
       #    """
       #    ストリームでcp932→utf8に変換するコマンド
       #    """
       #    import traceback
       #    import io
        
       #    try:
       #        # stdinのencodingがデフォルトでutf-8なので、設定し直す。
       #        input_stream = io.TextIOWrapper(sys.stdin.buffer, encoding='cp932')
       #        for line in input_stream:
       #            # 標準出力するときも自動でutf-8に変換されるので、printだけでいい
       #            print(line, end='')
       #        # flushをする
       #        sys.stdout.flush()
       #    except Exception as e:
       #        with open('/dev/stderr', 'w') as fpe:
       #            traceback.print_exc(file=fpe)
        
       ## flushをしないと、デバッグ用のprintなども入ってしまう
       #sys.stdout.flush()
       #f = None
       #f <<= inputs['i']
       #f <<= nm.runfunc(Cp932_to_utf8)
        
       #nysol_module_o= NysolModule()
       #nysol_module_o.set_content(f)
        
       #return {'o': nysol_module_o}


class Utf8ToCp932Command(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i'].content

        args_string = (PCMD_DIR / 'src/utf8_to_cp932.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}

        # pythonによる変換
        # 不安定なので無効化しておく

        # def utf8_to_Cp932():
        #     """
        #     ストリームでutf-8→cp932に変換するコマンド
        #     """
        #     import traceback
        #     import io
        #
        #     try:
        #         sys.stdout = open(sys.stdout.fileno(), 'w', encoding='cp932', closefd=False)
        #         for line in sys.stdin:
        #             # 改行コードは変えてくれなさそうなのでここで変える
        #             print(line.strip() + '\r\n', end='')
        #     except Exception as e:
        #         with open('/dev/stderr', 'w') as fpe:
        #             traceback.print_exc(file=fpe)
        #
        # sys.stdout.flush()
        # f = None
        # f <<= inputs['i']
        # f <<= nm.runfunc(utf8_to_Cp932)
        #
        # nysol_module_o= NysolModule()
        # nysol_module_o.set_content(f)
        #
        # return {'o': nysol_module_o}


class RunfuncCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        """
        実際実行(for override)
        """
        pass


class GroupBy2Command(PCommand):

    # クラス変数
    commandname = '特徴量の計算' # 将来、コマンド名はCmdJSONから取得（？）
    errormessages = {
        'FieldNotFoundError' : '指定した項目名は存在しません。${fieldinput}',

        # キー項目指定に関わるエラー
        'KeyFieldForbiddenCharacterError' : '半角の%と&は、キー項目名に使用できません。 ${fieldinput} ',
        'KeyFieldConflictError' : 'キー項目名が重複しています。${fieldinput}',
        'EmptyKeyFieldError' : '空文字列でキー項目名が指定されています。${fieldinput}',
        'KeyTargetConflictError' : 'キー項目名と計算対項目名が重複しています。計算対象項目には、キー項目を指定できません。${fieldinput}',
        'UnknownKeyFieldError' : 'キー項目の指定は正しくありません。${fieldinput}',
        
        # 時間軸に関わるエラー
        'TimecolForbiddenCharacterError' : '半角の（ *　?　[　]　,　:　\\　&　％ ）は、時間軸の項目の指定に使用できません。${fieldinput}',
        'EmptyTimecolFieldError' : '空文字列で時間軸の項目名が指定されています。${fieldinput}',
        'UnknownTimecolFieldError' : 'キー項目の指定は正しくありません。${fieldinput}',

        # 項目名指定に関わるエラー
        'TargetFieldForbiddenCharacterError':'半角の%と&は、項目名に使用できません。 ${fieldinput} ',
        'TargetFieldConflictError' : '項目名が重複しています。 ${fieldinput}',
        'EmptyTargetFieldError' : '空文字列で項目名が指定されています。 ${fieldinput}',
        'MultipleRowsTargetError' : '複数の項目名は指定できません。 ${fieldinput}',
        'UnknownTargetFieldError' : '項目名の指定が正しくありません。${fieldinput}',
        
        # 結果列指定に関わるエラー
        'ResultsColForbiddenCharacterError' : '半角の（ *　?　[　]　,　:　\\ \' \"）は、項目名に使用できません。${fieldinput}',
        'ResultsColConflictError' : '出力項目名が重複しています。%指定、&指定、ワイルドカード指定など、重複する出力項目名となる設定がないかを、確認してください。${fieldinput}',
        'UnknownResultsColError' : '名前付けルールの設定の指定が正しくありません。${fieldinput}',
        
        # 統計量指定に関わるエラー
        'CalcNotFoundError' : '指定は、有効な統計量指定子ではありません。${fieldinput}',
        # 'CalcNotFoundError' : '＜その値＞は、有効な統計量指定子ではありません。${fieldinput}',
        'CalcConflictError' : '統計量が重複しています。${fieldinput}',
        'EmptyCalcNewNameError' : ':指定で、別名が指定されましたが、別名が空文字列です。${fieldinput}',
        'EmptyCalcError' : '空文字列で統計量が指定されています。${fieldinput}',
        'MultipleParamCalcError' : 'パラメータ有りの統計量では、複数の統計量は指定できません。${fieldinput}',
        'UnknownCalcError' : '統計量の指定が正しくありません。${fieldinput}',
        
        # パラメータ指定に関わるエラー
        'ParameterConflictError' : 'パラメータが重複しています。${fieldinput}',
        'ParameterTypeError'  : '${calc} のパラメータへの ${fieldinput} 指定が正しくありません。${correct_type} を指定してください',
        'ParameterOutOfBoundsError' : '${calc} のパラメータへの ${fieldinput} 指定が正しくありません。 ${correct_value} で指定してください',
        'ParameterFormatError' : '${calc} のパラメータへの ${fieldinput} 指定が正しくありません。${correct_format}で指定してください',
        'UnknownParameterError' : '${calc} のパラメータへの ${fieldinput} 指定が正しくありません'
        }

    # このdictは、パラメータの情報が入ってる
    # {
    # '統計量キー' : { 'correct_type' : パラメータの正しいデータ型,
    #                'correct_value' : パラメータの正しい範囲,
    #                'correct_format' : パラメータの正しい書き方が（ある場合）
    #               }
    # }
    param_info = {
        'value_count' : {'correct_type' : '全ての文字列',
                            'correct_value' : '数値か文字列'},
        'sym_looking' : {'correct_type' : '数値', 
                            'correct_value' : '正の数値'},
        'large_sd' : {'correct_type' : '数値', 
                        'correct_value' : '正の数値'},
        'ratio_beyond_rsigma' : {'correct_type' : '数値', 
                                    'correct_value' : '正の数値'},
        'binned_entropy' : {'correct_type' : '数値', 
                            'correct_value' : '２以上の整数'},
        'quantile' : {'correct_type' : '数値', 
                        'correct_value' : '０−１の数値'},
        'range_count' : {'correct_type' : '数値;数値', 
                            'correct_value' : '全ての数値', 
                            'correct_format' : '開始＜終了の;区切り'},
        'autocorr' : {'correct_type' : '数値', 
                        'correct_value' : '１以上の整数' },
        'crossing_m' : {'correct_type' : '数値', 
                        'correct_value' : '全ての数値'},
        'peaks' : {'correct_type' : '数値', 
                    'correct_value' : '１以上の整数'},
        'imq' : {'correct_type' : '数値', 
                    'correct_value' : '０−１の数値'}
    }

    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def generateCommandErrorMessage(self, errcode, errfield, errinput = '', param_calc = ''):
        '''
        Function for creating error messages. 
        '''
        from string import Template

        if param_calc != '':
            # パラメータに関わるエラーの場合、パラメータの情報もエラーメッセージに含む
            template_strings = {'fieldinput' : errinput, 'calc' : param_calc, **self.param_info[param_calc]}
        else:
            template_strings = {'fieldinput' : errinput}


        message = Template(self.errormessages[errcode]).safe_substitute(template_strings)

        return f'【コマンド：{self.commandname}】【オプション欄：{errfield}】{message}'

    def expandWildCards(self, to_expand):
        """
        takes a comma separated string and parses wildcard expressions within.
        
        """
        import fnmatch as fn
        expanded = []
        
        for elem in to_expand.split(','):
            matched = False
            for col in self.header:
                if fn.fnmatch(col, elem):
                    expanded += [col]
                    matched = True
                    
            if not matched:
                # notfound error
                return 'FieldNotFoundError'
        
        return expanded
        

    def fixtimecolumn(self, flow, col, dateformat = 'date'):
        if dateformat == 'date':
            # details for this regex in https://kskds.docbase.io/posts/1317416
            flow <<= nm.mcal(a = "__isvalidformat",
                             c= f'regexm($s{{{col}}},"^(((([0-9]{{2}}(([2468][048])|([13579][26])|(0[48])))|((([02468][048])|([13579][26])|(0[048]))(00)))((((0[13578])|(1[02]))((0[1-9])|([1-2][0-9])|(3[01])))|(((0[469])|(11))((0[1-9])|([1-2][0-9])|(30)))|((02)((0[1-9])|([1-2][0-9])))))|([0-9]{{4}}((((0[13578])|(1[02]))((0[1-9])|([0-2][0-9])|(3[01])))|(((0[469])|(11))((0[1-9])|([0-2][0-9])|(30)))|((02)((0[1-9])|(1[0-9])|(2[0-8]))))))((([0-1][0-9])|(2[0-3]))([0-5][0-9]){{2}})([.][0-9]{{1,6}})?$")')

            flow <<= nm.mcal(a = '__int__',
                             c = f'if($s{{__isvalidformat}}=="1",regexstr($s{{{col}}},"^.{{14,14}}"),nulls())')
        
            flow <<= nm.mcal(a = f'__UXT__', 
                    c = 'uxt( s2t($s{__int__}))')
            
            flow <<= nm.mcal(a = '__FLAC__', 
                    c = f'if($s{{__isvalidformat}}=="1",regexstr($s{{{col}}},"[.][0-9]{{1,6}}$"),nulls())')
            
            flow <<= nm.mcal(a = 'uxt',
                    c = 'if( isnull($s{__FLAC__}), $s{__UXT__}, $s{__UXT__}+$s{__FLAC__} )')
            
            flow <<= nm.mcut(f = '__UXT__,__FLAC__,__isvalidformat', r = True)
        else:
            flow <<= nm.mcal(a = "__isvalidformat",
                             c = f'regexm($s{{{col}}},"^[+,-]?([0-9]+|(([0-9]+[.][0-9]*)|([0-9]*[.][0-9]+))([E,e][+,-]?[0-9]*)?)$")')
            flow <<= nm.mcal(a = 'uxt',
                             c = f'if($s{{__isvalidformat}}=="1",${{{col}}},nulln())')
            flow <<= nm.mcut(f = '__isvalidformat', r = True)
            
        flow <<= nm.mdelnull(f = 'uxt')
        
        return flow

    def remove_nonnumber(self, flow, cols):
        """
        ●NYSOLの数値の表記の仕様
        KSKP全体でみたときに不整合な状態にならないように
        NYSOLが数値と判断するものだけを数値とみなすために、仕様の確認を行った。

        当初はマニュアルの例を参考にしたが、
        マニュアルの例から想像できないパターンも数値と判断されることがわかったため
        実際にデータを作って確認し、推測した仕様をもとに実装した。

        ●数値と判断される文字列の例
        12, -12, +12, 12., 12.00, 0.12, .12, +.12, 0.12e, 0.12E, -.12E2, .12e+01

        ●推測された仕様
        条件(1)~(4)のいずれかを満たした文字列は、数値とみなす
        (1)下記条件①と②の両方を満たす文字列
        ①先頭に1個以下の符号(+または-)
        ②1個以下の小数点(.)と、1個以上の数字(0-9)を持つ文字列
        (2)(1)の末尾に、1個の指数記号(Eまたはe)を持つ文字列
        (3)(2)の末尾に、1個以下の符号(+または-)を持つ文字列
        (4)(3)の末尾に、０個以上の数字（0-9)を持つ文字列

        ●数値判定のための正規表現(mcalのcオプションの引数として使う)
        regexm($s{値},"^[+,-]?([0-9]+|(([0-9]+[.][0-9]*)|([0-9]*[.][0-9]+))([E,e][+,-]?[0-9]*)?)$")

        【補足】条件との対応関係
        条件      正規表現
        (1)①      ^[+,-]?
        (1)②      [0-9]+|(([0-9]+[.][0-9]*)|([0-9]*[.][0-9]+))
        (2-4)    ([E,e][+,-]?[0-9]*)?
        """
        flow = copy.deepcopy(flow)
        
        if isinstance(cols, str):
            cols = cols.split(',')
        
        for col in cols:
            # mark non-number rows
            flow <<= nm.mcal(a = f'__numflag{col}__',
              c = f'regexm($s{{{col}}},"^[+,-]?([0-9]+|(([0-9]+[.][0-9]*)|([0-9]*[.][0-9]+))([E,e][+,-]?[0-9]*)?)$")')
            flow <<= nm.mcal(a = f'__notnullflag{col}__',
              c = f'not(isnull(${{{col}}}))')
            
            # make new col with only number values and NULL
            flow <<= nm.mcal(a = f'__new{col}__',
                             c = f'if(${{__numflag{col}__}}==1,$s{{{col}}},nulls())')
        
        # delete old cols
        flow <<= nm.mcut(f = cols, r = True)
        flow <<= nm.mcut(f = '__numflag*__,__notnullflag*__', r = True)
        
        # rename new cols
        flow <<= nm.mfldname(f = [f'__new{col}__:{col}' for col in cols])

        return flow
        
        
    def rows(self, subcmd, **kwargs):
        try:
            a = kwargs.get('a')
            fld = kwargs.get('fld')
            k = kwargs.get('k')
            
            subcmd <<= nm.mcount(k = k, a = a)
            subcmd <<= nm.mcal(a = 'fld', c = f'"{fld}"')
            subcmd <<= nm.mcut(f = f'{k},fld,{a}')

            return subcmd
        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    # --------------- 1 var -----------------------
    
    def missingdata(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')

            allrows = None
            
            allrows <<= nm.mcount(i = subcmd, k = k, a = '__allrows')

            subcmd <<= nm.msummary(k = k, f = f, c = 'count:__count')
            subcmd <<= nm.mnjoin(k = k, m = allrows, f = '__allrows')

            subcmd <<= nm.mcal(a = '__missingcount', c = '${__allrows}-${__count}')
            subcmd <<= nm.mcal(a = a, c = '$s{__missingcount}')

            subcmd <<= nm.mcut(f = f'{k},fld,{a}')

            return subcmd

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def hasduplicate(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')

            fs = f.split(',')
            total = [None] * len(fs)
            msummary = [None] * len(fs)
            targets = [None] * len(fs)
            subcmd_o = None

            for i, fld in enumerate(fs):

                total[i] <<= nm.mcount(k = f'{k},{fld}', a = '__dcnt', i = subcmd)
                msummary[i] <<= nm.msummary(k = k, f = fld, c = 'count:__count',
                                            i = subcmd)

                targets[i] <<= nm.mcount(k = k, a = '__ddcnt', i = total[i])
                targets[i] <<= nm.msetstr(a = 'fld', v = fld)
                targets[i] <<= nm.mnjoin(k = f'{k},fld', f = '__count', 
                                         m = msummary[i])
                targets[i] <<= nm.mcal(c = '${__ddcnt}!=${__count}', a = a)
                targets[i] <<= nm.mcut(f = f'{k},fld,{a}')

            subcmd_o <<= nm.m2cat(i = targets)

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def hasduplicatemin(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')

            fs = f.split(',')
            targets = [None] * len(fs)
            subcmd_o = None

            for i, fld in enumerate(fs):

                targets[i] <<= nm.mcount(k = f'{k},{fld}', a = '__dcnt', 
                                         i = subcmd)
                targets[i] <<= nm.mbest(k = k, s = f'{fld}%n', size = 1)    
                targets[i] <<= nm.mcal(c = '${__dcnt}>1', a = a)
                targets[i] <<= nm.msetstr(a = 'fld', v = fld)
                targets[i] <<= nm.mcut(f = f'{k},fld,{a}')

            subcmd_o <<= nm.m2cat(i = targets)

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def hasduplicatemax(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')

            fs = f.split(',')
            targets = [None] * len(fs)
            subcmd_o = None

            for i, fld in enumerate(fs):

                targets[i] <<= nm.mcount(k = f'{k},{fld}', a = '__dcnt', 
                                         i = subcmd)
                targets[i] <<= nm.mbest(k = k, s = f'{fld}%nr', size = 1)    
                targets[i] <<= nm.mcal(c = '${__dcnt}>1', a = a)
                targets[i] <<= nm.msetstr(a = 'fld', v = fld)
                targets[i] <<= nm.mcut(f = f'{k},fld,{a}')

            subcmd_o <<= nm.m2cat(i = targets)

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def rootmeansquare(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')
            precision = kwargs.get('precision')
            
            # k gives key fields
            # f gives target fields
            # a gives output field name

            # subcmd = None
            # subcmd <<= nm.mstdin()
            # mcal to square
            fs = f.split(',')

            for fld in fs:
                subcmd <<= nm.mcal(a = f'{fld}_temp', c = f'${{{fld}}}^2',
                                precision = precision)
                subcmd <<= nm.mcut(f = fld, r = True)
                subcmd <<= nm.mfldname(f = f'{fld}_temp:{fld}')
            
            # msummary to sum
            subcmd <<= nm.msummary(c = 'sum,count', f = f, k = k,
                                precision = precision)

            # mcal to sqrt
            subcmd <<= nm.mcal(a = a, c = 'sqrt(${sum}/${count})',
                            precision = precision)

            # mcut to remove old row
            finalcols = ','.join([k,'fld',a])
            subcmd <<= nm.mcut(f = finalcols)

            return subcmd
            # subcmd <<= nm.mstdout()
            # subcmd.run()

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def geometricmean(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')
            precision = kwargs.get('precision')
            
            # positive numbers only
            # subcmd = None
            # subcmd <<= nm.mstdin()

            fs = f.split(',')

            flags = None
            flags <<= nm.msummary(i = subcmd, c = 'min', k = k, f = f)
            flags <<= nm.mcal(a = '__hasnegative', c = '${min}<0')
            flags <<= nm.mcal(a = '__haszero', c = '${min}==0') 
            
            for fld in fs:
                subcmd <<= nm.mcal(a = f'{fld}_ln', c = f'ln(${{{fld}}})',
                                precision = precision)
                subcmd <<= nm.mcut(f = fld, r = True)
                subcmd <<= nm.mfldname(f = f'{fld}_ln:{fld}')

            subcmd <<= nm.msummary(c = 'mean', f = f, k = k,
                                precision = precision)
            
            subcmd <<= nm.mjoin(k = f'{k},fld', m = flags, f = '__hasnegative,__haszero')

            subcmd <<= nm.mcal(a = a, c = 'if($b{__hasnegative},nulln(),if($b{__haszero},0,exp(${mean})))', 
                            precision = precision)

            finalcols = f'{k},fld,{a}'
            subcmd <<= nm.mcut(f = finalcols)
            
            return subcmd
            # subcmd <<= nm.mstdout()
            # subcmd.run()

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def harmonicmean(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')
            precision = kwargs.get('precision')
            
            # subcmd = None
            # subcmd <<= nm.mstdin()

            flags = None
            fs = f.split(',')


            flags <<= nm.msummary(i = subcmd, c = 'min', k = k, f = f)
            flags <<= nm.mcal(a = '__hasnegative', c = '${min}<0')
            flags <<= nm.mcal(a = '__haszero', c = '${min}==0') 

            for fld in fs:
                subcmd <<= nm.mcal(a = f'{fld}_inv', c = f'1/${{{fld}}}',
                                precision = precision)
                subcmd <<= nm.mcut(f = fld, r = True)
                subcmd <<= nm.mfldname(f = f'{fld}_inv:{fld}')

            subcmd <<= nm.msummary(c = 'sum,count', f = f, k = k,
                                precision = precision)

            subcmd <<= nm.mjoin(k = f'{k},fld', m = flags, f = '__hasnegative,__haszero')
            
            subcmd <<= nm.mcal(a = a, c = 'if(${__hasnegative}==1,nulln(),if(${__haszero}==1,0,${count}/${sum}))',
                               precision = precision)

            finalcols = ','.join([k,'fld',a])
            subcmd <<= nm.mcut(f = finalcols)
            
            return subcmd
            # subcmd <<= nm.mstdout()
            # subcmd.run()

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def variance_larger_than_sd(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')
            
            # fs = f.split(',')
            subcmd_o = None
            # subcmd <<= nm.msummary(k = k, f = f, c = 'var:__var,sd:__sd')
            condition = [f'($s{{fld}}=="{fld}")' for fld in f.split(',')]
            subcmd_o <<= nm.msel(i = self.all_msums, c = '||'.join(condition))
            subcmd_o <<= nm.mcal(c = 'if(isnull(${__var}),nullb(),${__var}>${__sd})', a = a)
            subcmd_o <<= nm.mcut(f = f'{k},fld,{a}')

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)
                
    def strmax(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')
            
            fs = f.split(',')
            targets = [None] * len(fs)

            subcmd_o = None

            for i, fld in enumerate(fs):
                targets[i] <<= nm.mkeybreak(i = subcmd, k = k, s = fld)
                targets[i] <<= nm.mcal(a = 'fld', c = f'if($s{{bot}}=="1","{fld}",nulls())')
                targets[i] <<= nm.mcal(a = a, c = f'if($s{{bot}}=="1",$s{{{fld}}},nulls())')
                targets[i] <<= nm.msel(c = f'$s{{bot}}=="1"')
                # targets[i] <<= nm.mdelnull(f = a)

            subcmd_o <<= nm.m2cat(i = targets)
            subcmd_o <<= nm.mcut(f = f'{k},fld,{a}')

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def strmin(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')

            fs = f.split(',')
            targets = [None] * len(fs)

            subcmd_o = None

            for i, fld in enumerate(fs):
                targets[i] <<= nm.mkeybreak(i = subcmd, k = k, s = fld)
                targets[i] <<= nm.mcal(a = 'fld', c = f'if($s{{top}}=="1","{fld}",nulls())')
                targets[i] <<= nm.mcal(a = a, c = f'if($s{{top}}=="1",$s{{{fld}}},nulls())')
                targets[i] <<= nm.msel(c = f'$s{{top}}=="1"')
                # targets[i] <<= nm.mdelnull(f = a)

            subcmd_o <<= nm.m2cat(i = targets)
            subcmd_o <<= nm.mcut(f = f'{k},fld,{a}')

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def strucount(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')

            fs = f.split(',')

            subcmd_o = None
            subcmds = [None] * len(fs)

            for i, fld in enumerate(fs):
                subcmds[i] <<= nm.muniq(i = subcmd, k = f'{k},{fld}') 
                subcmds[i] <<= nm.mcount(k = k, a = f'{a}')
                subcmds[i] <<= nm.mcal(a = 'fld', c = f'"{fld}"')
                subcmds[i] <<= nm.mcut(f = f'{k},fld,{a}')

            subcmd_o <<= nm.m2cat(i = subcmds)
            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def abs_energy(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')
            precision = kwargs.get('precision')

            fs = f.split(',')

            for fld in fs:
                subcmd <<= nm.mcal(c = f'${{{fld}}}*${{{fld}}}', a = f'__tmp{fld}')
                subcmd <<= nm.mcut(f = fld, r = True)
                subcmd <<= nm.mfldname(f = f'__tmp{fld}:{fld}')
            
            subcmd <<= nm.msummary(k = k, c = f'sum:{a}', f = f, precision = precision)

            return subcmd

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def meanabsolutedeviation(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')
            precision = kwargs.get('precision')
            
            meancalc = None

            # meancalc <<= nm.msummary(i = subcmd, k = k, f = f, c = '__mean',
            #                         precision = precision)
            condition = [f'($s{{fld}}=="{fld}")' for fld in f.split(',')]
            meancalc <<= nm.msel(i = self.all_msums, c = '||'.join(condition))
            meancalc <<= nm.m2cross(f = '__mean', a = 'type,value', k = k + ',fld')
            meancalc <<= nm.mcal(a = 'colnames', c = '$s{fld}+"_mean"',
                                precision = precision)
            meancalc <<= nm.mcross(f = 'value', s= 'colnames', k = k)

            flds = f.split(',')
            fldnames = [fld + '_mean' for fld in flds]

            subcmd <<= nm.mjoin(k = k, K = k, m = meancalc, 
                                f = ','.join(fldnames))

            for fld in flds:
                subcmd <<= nm.mcal(a = f'{fld}_diff', 
                                c = f'abs(${{{fld}}}-${{{fld+"_mean"}}})',
                                precision = precision)
                subcmd <<= nm.mcut(f = fld, r = True)
                subcmd <<= nm.mfldname(f = f'{fld}_diff:{fld}')

            subcmd <<= nm.msummary(k = k, c = f'mean:{a}', f = f, 
                                precision = precision)
            
            return subcmd

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)
        
    def medianabsolutedeviation(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')
            precision = kwargs.get('precision')
            
            meancalc = None

            condition = [f'($s{{fld}}=="{fld}")' for fld in f.split(',')]
            meancalc <<= nm.msel(i = self.all_msums, c = '||'.join(condition))
            meancalc <<= nm.m2cross(f = '__median', a = 'type,value', k = k + ',fld')
            meancalc <<= nm.mcal(a = 'colnames', c = '$s{fld}+"_median"',
                                precision = precision)
            meancalc <<= nm.mcross(f = 'value', s= 'colnames', k = k)

            flds = f.split(',')
            fldnames = [fld + '_median' for fld in flds]
            subcmd <<= nm.mjoin(k = k, K = k, m = meancalc, 
                                f = ','.join(fldnames))

            for fld in flds:
                subcmd <<= nm.mcal(a = f'{fld}_diff', 
                                c = f'abs(${{{fld}}}-${{{fld+"_median"}}})',
                                precision = precision)
                subcmd <<= nm.mcut(f = fld, r = True)
                subcmd <<= nm.mfldname(f = f'{fld}_diff:{fld}')

            subcmd <<= nm.msummary(k = k, c = f'mean:{a}', f = f, 
                                precision = precision)
            
            return subcmd

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def reoccurringdatapoints(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')
            precision = kwargs.get('precision')

            fs = f.split(',')
            targets = [None] * len(fs)

            subcmd_o = None

            for i, fld in enumerate(fs):
                targets[i] <<= nm.mcount(k = f'{k},{fld}', a = '__count__',
                                         i = subcmd)
                targets[i] <<= nm.mfldname(f = f'{fld}:___')
                targets[i] <<= nm.mcal(a = fld, c = '${__count__}>1')
                targets[i] <<= nm.msummary(k = k, f = f'{fld}', 
                                           c = 'sum:__sum__,count:__count__')
                targets[i] <<= nm.mcal(c = '${__sum__}/${__count__}', a = a,
                                       precision = precision)

            subcmd_o <<= nm.m2cat(i = targets)
            subcmd_o <<= nm.mcut(f = f'{k},fld,{a}')

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def reoccurringvalues(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')
            precision = kwargs.get('precision')

            fs = f.split(',')
            targets = [None] * len(fs)
            mcount = [None] * len(fs)

            subcmd_o = None

            for i, fld in enumerate(fs):
                mcount[i] <<= nm.mcount(k = f'{k}', a ='__total__', 
                                        i = subcmd)

                targets[i] <<= nm.mcount(k = f'{k},{fld}', a = '__count__',
                                         i = subcmd)
                targets[i] <<= nm.mcal(a = '__repeat__', c = 'if(${__count__}>1,${__count__},0)')
                targets[i] <<= nm.msum(k = k, f = '__repeat__')

                targets[i] <<= nm.mjoin(m = mcount[i], f = '__total__', k = k)
                targets[i] <<= nm.mcal(a = a, c = '${__repeat__}/${__total__}',
                                       precision = precision)
                targets[i] <<= nm.mcal(a = 'fld', c = f'"{fld}"')

            subcmd_o <<= nm.m2cat(i = targets)
            subcmd_o <<= nm.mcut(f = f'{k},fld,{a}')

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)
                
    def sumofreoccurringdatapoints(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')
            precision = kwargs.get('precision')

            fs = f.split(',')
            targets = [None] * len(fs)

            subcmd_o = None

            for i, fld in enumerate(fs):
                targets[i] <<= nm.mcount(k = f'{k},{fld}', a = '__count__',
                                         i = subcmd)
                targets[i] <<= nm.mcal(c = f'if(${{__count__}}==1,0,${{__count__}}*${{{fld}}})', a = '__sumperval__', 
                                       precision = precision)
                targets[i] <<= nm.mcut(f = fld, r = True)
                targets[i] <<= nm.msum(k = k, f = f'__sumperval__:{fld}', 
                                       precision = precision)
                targets[i] <<= nm.m2cross(a = f'fld,{a}', f = fld, k = k)

            subcmd_o <<= nm.m2cat(i = targets)
            subcmd_o <<= nm.mcut(f = f'{k},fld,{a}')

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def sumofreoccurringvalues(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')
            precision = kwargs.get('precision')

            fs = f.split(',')
            targets = [None] * len(fs)

            subcmd_o = None

            for i, fld in enumerate(fs):
                targets[i] <<= nm.mcount(k = f'{k},{fld}', a = '__count__',
                                         i = subcmd)
                targets[i] <<= nm.mcal(c = f'if(${{__count__}}==1,0,${{{fld}}})', 
                                       a = '__sumperval__')
                targets[i] <<= nm.mcut(f = fld, r = True)
                targets[i] <<= nm.msum(k = k, f = f'__sumperval__:{fld}', 
                                       precision = precision)
                targets[i] <<= nm.m2cross(a = f'fld,{a}', f = fld, k = k)

            subcmd_o <<= nm.m2cat(i = targets)
            subcmd_o <<= nm.mcut(f = f'{k},fld,{a}')

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)
    
    def ratio_value_number_to_series_length(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')

            fs = f.split(',')
            targets = [None] * len(fs)

            subcmd_o = None

            condition = [f'($s{{fld}}=="{fld}")' for fld in f.split(',')]
            subcmd_o <<= nm.msel(i = self.all_msums, c = '||'.join(condition))
            subcmd_o <<= nm.mcal(c = '${__ucount}/${__count}', a = a)
            subcmd_o <<= nm.mcut(f = f'{k},fld,{a}')

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def countabovemean(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')

            fs = f.split(',')
            targets = [None] * len(fs)

            subcmd_o = None

            # condition = [f'($s{{fld}}=="{fld}")' for fld in f.split(',')]
            # msumres <<= nm.msel(i = self.all_msums, c = '||'.join(condition))

            subcmd <<= nm.mnjoin(k = k, f = 'fld,__mean', m = self.all_msums)

            for i, fld in enumerate(fs):
                targets[i] <<= nm.msel(i = subcmd, c = f'$s{{fld}}=="{fld}"')
                targets[i] <<= nm.mcal(c = f'${{{fld}}}>${{__mean}}', a = a)
                targets[i] <<= nm.msum(k = f'{k},fld', f = a)
                
            subcmd_o <<= nm.mcut(i = targets, f = f'{k},fld,{a}')

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def countbelowmean(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')

            fs = f.split(',')
            targets = [None] * len(fs)

            subcmd_o = None

            subcmd <<= nm.mnjoin(k = k, f = 'fld,__mean', m = self.all_msums)

            for i, fld in enumerate(fs):
                targets[i] <<= nm.msel(i = subcmd, c = f'$s{{fld}}=="{fld}"')
                targets[i] <<= nm.mcal(c = f'${{{fld}}}<${{__mean}}', a = a)
                targets[i] <<= nm.msum(k = f'{k},fld', f = a)
                
            subcmd_o <<= nm.mcut(i = targets, f = f'{k},fld,{a}')

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def symmetry_looking(self,subcmd, **kwargs):
        f = kwargs.get('f')
        a = kwargs.get('a')
        k = kwargs.get('k')
        n = kwargs.get('n')

        calcid = 'sym_looking'

        try:
            param = float(n)
            if param <= 0:
                errmsg = self.generateCommandErrorMessage('ParameterOutOfBoundsError', 'n', n, param_calc = calcid)
                raise Exception(errmsg)
        except ValueError:
            errmsg = self.generateCommandErrorMessage('ParameterTypeError', 'n', n, param_calc = calcid)
            raise Exception(errmsg)

        msumres = None
        condition = [f'($s{{fld}}=="{fld}")' for fld in f.split(',')]
        msumres <<= nm.msel(i = self.all_msums, c = '||'.join(condition))

        subcmd <<= nm.mnjoin(k = k, f = 'fld,__mean,__median,__max,__min',
                                m = msumres)
        # subcmd <<= nm.msummary(f = f, k = k, 
        #             c = 'mean:__mean,median:__median,max:__max,min:__min')
        subcmd <<= nm.mcal(c = '${__max}-${__min}',
                            a = 'max_min')
        subcmd <<= nm.mcal(c = 'abs(${__mean}-${__median})',
                            a = 'mean_median')
        subcmd <<= nm.mcal(c = f'${{mean_median}}<${{max_min}}*{n}', 
                            a = f'{a}_{n}')

        subcmd <<= nm.mcut(f = f'{k},fld,{a}_{n}')

        return subcmd
        
    def large_standard_dev(self,subcmd, **kwargs):
        f = kwargs.get('f')
        a = kwargs.get('a')
        k = kwargs.get('k')
        n = kwargs.get('n')

        calcid = 'large_sd'

        try:
            # check if float
            param = float(n)
            
            # check if negative
            if param <= 0:
                errmsg = self.generateCommandErrorMessage('ParameterOutOfBoundsError', 'n', n, param_calc = calcid)
                raise Exception(errmsg)
        except ValueError:
            errmsg = self.generateCommandErrorMessage('ParameterTypeError', 'n', n, param_calc = calcid)
            raise Exception(errmsg)
        
        
        msumres = None
        condition = [f'($s{{fld}}=="{fld}")' for fld in f.split(',')]
        msumres <<= nm.msel(i = self.all_msums, c = '||'.join(condition))

        subcmd <<= nm.mnjoin(k = k, f = 'fld,__sd,__max,__min',
                                m = msumres)
        # subcmd <<= nm.msummary(f = f, k = k, 
        #             c = 'sd:__sd,max:__max,min:__min')
        subcmd <<= nm.mcal(c = '${__max}-${__min}', a = '__diff')
        subcmd <<= nm.mcal(c = f'${{__sd}}>${{__diff}}*{n}', 
                            a = f'{a}_{n}')

        subcmd <<= nm.mcut(f = f'{k},fld,{a}_{n}')

        return subcmd

    def value_count(self,subcmd, **kwargs):
        f = kwargs.get('f')
        a = kwargs.get('a')
        k = kwargs.get('k')
        n = kwargs.get('n')

        calcid = 'value_count'
        
        # TODO: 関数化？
        strparam = False
        try:
            n = float(n)
            if n%1 == 0:
                n = int(n)
        except ValueError:
            strparam = True
            if n == '':
                errmsg = self.generateCommandErrorMessage('ParameterOutOfBoundsError', 'n', n, param_calc = calcid)
                raise Exception(errmsg)
            
        subcmd <<= nm.m2cross(k = k, a = 'fld,__val', f = f)

        if strparam:
            subcmd <<= nm.mcal(a = '__eq', c = f'$s{{__val}}=="{n}"')
        else:
            subcmd <<= nm.mcal(a = '__eq', c = f'${{__val}}=={n}')

        subcmd <<= nm.msum(k = f'{k},fld', f = f'__eq:{a}_{n}')

        subcmd <<= nm.mcut(f = f'{k},fld,{a}_{n}')

        return subcmd

    def range_count(self,subcmd, **kwargs):
        f = kwargs.get('f')
        a = kwargs.get('a')
        k = kwargs.get('k')
        n = kwargs.get('n')

        calcid = 'range_count'

        try:
            nmin, nmax = n.split(';')
        except ValueError:
            errmsg = self.generateCommandErrorMessage('ParameterFormatError', 'n', n, param_calc = calcid)
            raise Exception(errmsg)

        try:
            # check if float
            param_min = float(nmin)
            param_max = float(nmax)
        except ValueError:
            errmsg = self.generateCommandErrorMessage('ParameterTypeError', 'n', n, param_calc = calcid)
            raise Exception(errmsg)
            
            # check if outside 0-1
        if param_min >= param_max:
            errmsg = self.generateCommandErrorMessage('ParameterFormatError', 'n', n, param_calc = calcid)
            raise Exception(errmsg)

        
        subcmd <<= nm.m2cross(k = k, a = 'fld,__val', f = f)
        subcmd <<= nm.mcal(a = '__inrange',
            c = f'${{__val}}>={float(nmin)} && ${{__val}} < {float(nmax)}')
        subcmd <<= nm.msum(k = f'{k},fld', f = f'__inrange:{a}_{n}')

        subcmd <<= nm.mcut(f = f'{k},fld,{a}_{n}')

        return subcmd

    def ratio_beyond_rsigma(self,subcmd, **kwargs):
        f = kwargs.get('f')
        a = kwargs.get('a')
        k = kwargs.get('k')
        n = kwargs.get('n')

        calcid = 'ratio_beyond_rsigma'

        try:
            # check if float (not str)
            param = float(n)
            
            # check if negative or 0
            if param <= 0:
                errmsg = self.generateCommandErrorMessage('ParameterOutOfBoundsError', 'n', n, param_calc = calcid)
                raise Exception(errmsg)
        except ValueError:
            errmsg = self.generateCommandErrorMessage('ParameterTypeError', 'n', n, param_calc = calcid)
            raise Exception(errmsg)

        fs = f.split(',')
        targets = [None] * len(fs)
        subcmd_o = None

        subcmd <<= nm.mnjoin(k = k, m = self.all_msums, f = 'fld,__mean,__sd,__count')

        for i, fld in enumerate(fs):
            targets[i] <<= nm.msel(c = f'$s{{fld}}=="{fld}"', i = subcmd)
            targets[i] <<= nm.mcal(c = f'(abs(${{{fld}}}-${{__mean}}))>=({n}*${{__sd}})', 
                                    a = f'__ratio')

        subcmd_o <<= nm.msum(k = f'{k},fld', f = f'__ratio', i = targets)
        subcmd_o <<= nm.mcal(c = '${__ratio}/${__count}', a = f'{a}_{n}')

        subcmd_o <<= nm.mcut(f = f'{k},fld,{a}_{n}')

        return subcmd_o

    def quantile(self,subcmd, **kwargs):
        f = kwargs.get('f')
        a = kwargs.get('a')
        k = kwargs.get('k')
        n = kwargs.get('n')

        calcid = 'quantile'

        try:
            # check if float
            param = float(n)
            
            # check if outside 0-1
            if param < 0 or param > 1:
                errmsg = self.generateCommandErrorMessage('ParameterOutOfBoundsError', 'n', n, param_calc = calcid)
                raise Exception(errmsg)
        except ValueError:
            errmsg = self.generateCommandErrorMessage('ParameterTypeError', 'n', n, param_calc = calcid)
            raise Exception(errmsg)

        fs = f.split(',')
        targets = [None] * len(fs)
        precalcs = [None] * len(fs)
        tcalcs = None
        subcmd_o = None

        # take starting key columns
        _keys = None
        _keys <<= nm.mcut(f = k, i = subcmd)
        _keys <<= nm.muniq(k = k)

        # tcalcs <<= nm.msummary(f = f, c = 'count:__count',
        #                          k = k, i = subcmd)
        msumres = None
        condition = [f'($s{{fld}}=="{fld}")' for fld in f.split(',')]
        msumres <<= nm.msel(i = self.all_msums, c = '||'.join(condition))

        tcalcs <<= nm.mnjoin(i = subcmd, k = k, f = 'fld,__count',
                                m = msumres)
        tcalcs <<= nm.mcal(a = '__qtRate', c = f'if(${{__count}}==0,nulln(),{n})')
        tcalcs <<= nm.mcal(a = '__T', c = '1-${__qtRate}+${__count}*${__qtRate}')
        tcalcs <<= nm.mcal(a = '__T1', c = 'int(${__T})')
        tcalcs <<= nm.mcal(a = '__T2', c = 'if(fract(${__T})==0,${__T1},${__T1}+1)')

        for i, fld in enumerate(fs):
            precalcs[i] <<= nm.mnumber(i = subcmd, s = f'{fld}%n', k = k, 
                                        a = '__qtNo', S = 1)
            precalcs[i] <<= nm.msortf(f = f'{k},__qtNo')

            targets[i] <<= nm.mnjoin(i = tcalcs, k = f'{k},__T1', K = f'{k},__qtNo',
                                    f = f'{fld}:__{fld}X1', m = precalcs[i], n = True)
            targets[i] <<= nm.mnjoin(k = f'{k},__T2', K = f'{k},__qtNo',
                                    f = f'{fld}:__{fld}X2', m = precalcs[i], n = True)
            targets[i] <<= nm.msel(c = f'$s{{fld}}=="{fld}"')
            targets[i] <<= nm.mcal(a = f'{a}_{n}', c = f'if(${{__T1}}==${{__T2}},${{__{fld}X1}},(${{__T2}}-${{__T}})*${{__{fld}X1}}+(${{__T}}-${{__T1}})*${{__{fld}X2}})')
            targets[i] <<= nm.mcut(f = f'{k},fld,{a}_{n}')

        # subcmd_o <<= nm.m2cat(i = targets)
        subcmd_o <<= nm.mnjoin(i = _keys, k = k, m = targets, n = True)

        return subcmd_o

    def binned_entropy(self,subcmd, **kwargs):
        f = kwargs.get('f')
        a = kwargs.get('a')
        k = kwargs.get('k')
        n = kwargs.get('n')

        calcid = 'binned_entropy'

        try:
            # check if float
            param = float(n)
            
            # check if not integer or less than 2
            if (not param.is_integer()) or param < 2:
                errmsg = self.generateCommandErrorMessage('ParameterOutOfBoundsError', 'n', n, param_calc = calcid)
                raise Exception(errmsg)
        except ValueError:
            errmsg = self.generateCommandErrorMessage('ParameterTypeError', 'n', n, param_calc = calcid)
            raise Exception(errmsg)
        
        
        fs = f.split(',')
        targets = [None] * len(fs)
        msummary = None
        subcmd_o = None

        # msummary <<= nm.mcut(i = self.all_msums, f = f'{k},fld,__count')
        condition = [f'($s{{fld}}=="{fld}")' for fld in f.split(',')]
        msummary <<= nm.msel(i = self.all_msums, c = '||'.join(condition))

        subcmd <<= nm.mbucket(k = k, f = [f'{fld}:__{fld}_no' for fld in fs],
                                n = n, rng = True)

        for i, fld in enumerate(fs):
            targets[i] <<= nm.mcount(k = f'{k},__{fld}_no', a = f'__{fld}hcount',
                                    i = subcmd)

            targets[i] <<= nm.mnjoin(k = k, m = msummary, f = 'fld,__count')
            targets[i] <<= nm.msel(c = f'$s{{fld}}=="{fld}"')
            targets[i] <<= nm.mcal(c = f'(${{__{fld}hcount}}/${{__count}})*ln(${{__{fld}hcount}}/${{__count}})',
                                    a = '__probs')
            targets[i] <<= nm.mcut(f = f'{k},fld,__probs')

        subcmd_o <<= nm.msum(k = f'{k},fld', f = '__probs', i = targets)
        subcmd_o <<= nm.mcal(c = '${__probs}*-1', a = f'{a}_{n}')

        subcmd_o <<= nm.mcut(f = f'{k},fld,{a}_{n}')

        return subcmd_o

    def energy_ratio_by_chunks(self,subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')
            s = kwargs.get('s')
            n = kwargs.get('n')
            segments, focus = n.split(';')

            fs = f.split(',')
            targets = [None] * len(fs)
            msummary = None
            abs_energy = None
            subcmd_o = None

            # msummary <<= nm.msummary(i = subcmd, f = f, k = k, 
            #                          c = 'count:__count,sd:__sd')
            condition = [f'($s{{fld}}=="{fld}")' for fld in f.split(',')]
            msummary <<= nm.msel(i = self.all_msums, c = '||'.join(condition))

            abs_energy = self.abs_energy(subcmd, f = f, k = k, a = '__sqsum')

            subcmd <<= nm.mnjoin(k = k, m = msummary, f ='fld,__count,__sd')
            subcmd <<= nm.mnjoin(k = f'{k},fld', m = abs_energy, f ='__sqsum')

            subcmd <<= nm.mcal(c = f'int(${{__count}}/{segments})', a = '__sl')
            subcmd <<= nm.mcal(a = '__st,__ed', 
                    c = f'{focus}*${{__sl}},min({int(focus)+1}*${{__sl}},${{__count}})')
            subcmd <<= nm.msel(c = f'${{{s}}}>=${{__st}}&&${{{s}}}<${{__ed}}')

            for i, fld in enumerate(fs):
                targets[i] <<= nm.msel(c = f'$s{{fld}}=="{fld}"', i = subcmd)
                targets[i] <<= nm.mcal(c = f'${{{fld}}}^2', a = f'__d2')

            subcmd_o <<= nm.msum(i = targets, k = f'{k},fld', f = '__d2')
            subcmd_o <<= nm.mcal(c = '${__d2}/${__sqsum}', a = f'{a}_{n}')
            subcmd_o <<= nm.mcut(f = f'{k},fld,{a}_{n}')

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    # --------------- 2 vars -----------------------

    def integral(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            x = kwargs.get('x')
            k = kwargs.get('k')
            precision = kwargs.get('precision')

            dateformat = kwargs.pop('dateformat') 

            fs = f.split(',')

            # get keybreak points
            subcmd <<= nm.msortf(f = k)
            subcmd <<= nm.mkeybreak(k = k, s = f'{x}%n')
            
            # fix time column
            subcmd = self.fixtimecolumn(subcmd, x, dateformat)

            # if not top of section, get time step length, else null
            subcmd <<= nm.mcal(a = 'time_step', 
                            c = f'if(isnull(${{top}}),${{uxt}}-#{{uxt}},nulln())')

            # if not top of section, add current and previous value, else null
            for fld in fs:
                subcmd <<= nm.mcal(a = f'{fld}_partial_sum', 
                        c = f'if(isnull(${{top}}),${{{fld}}}+#{{{fld}}},nulln())')

                # trapezoid rule: (((partialsum)/2)*step size)
                subcmd <<= nm.mcal(a = f'{fld}_trap', 
                        c = f'(${{{fld}_partial_sum}}/2)*${{time_step}}')

                subcmd <<= nm.mcut(f = fld, r = True)
                subcmd <<= nm.mfldname(f = f'{fld}_trap:{fld}')

            # sum over each key
            subcmd <<= nm.msummary(k = k, c = f'sum:{a}', f = f,
                                precision = precision)

            return subcmd

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def meanfrequency(self, **kwargs):
        # body of this method adapted from:
        # github.com/nysol/nysol_python/blob/master/scripts/sample/mkfeature.py
        try:
            import math
            import numpy as np
            
            f = kwargs.get('f')
            a = kwargs.get('a')
            x = 'uxt' # kwargs.get('x')
            k = kwargs.get('k')
            precision = kwargs.get('precision')

            headerline = True

            for dlist in nm.mstdin().keyblock(f'{k}', f'{x}%n', header = True):
                id = ','.join(dlist[0][:len(k.split(','))])

                if headerline:
                    header = dlist[0]
                    print(f'{k},fld,{a}')
                    headerline = False

                else:
                    for fld in f.split(','):
                        f_loc = header.index(fld)

                        # valuetype check goes here
                        targetcol = []
                        for line in dlist:
                            # input cleanup goes here
                            try:
                                # if the value can be converted to float, included
                                targetcol.append(float(line[f_loc]))
                            except ValueError:
                                # otherwise, place nan
                                targetcol.append(float('nan'))

                        if targetcol == []:
                            print(f'{id},{fld},')
                        else:
                            y = np.abs(np.fft.rfft(targetcol))

                            mean = y.dot(np.arange(len(y)))/y.sum()

                            # output cleanup goes here
                            if (mean is None) or (mean == '') or (mean ==  'None'):
                                # print empty string
                                print(f'{id},{fld},')
                            else:
                                if np.isfinite(float(mean)):
                                    print(f'{id},{fld},{mean:.{precision}g}')
                                else:
                                    print(f'{id},{fld},')

            sys.__stdout__.flush()#not needed for bigger data

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def frequencyvar(self, **kwargs):
        # body of this method adapted from:
        # github.com/nysol/nysol_python/blob/master/scripts/sample/mkfeature.py
        try:
            import math
            import numpy as np
            
            f = kwargs.get('f')
            a = kwargs.get('a')
            x = 'uxt' # kwargs.get('x')
            k = kwargs.get('k')
            precision = kwargs.get('precision')

            headerline = True

            for dlist in nm.mstdin().keyblock(f'{k}', f'{x}%n', header = True):
                id = ','.join(dlist[0][:len(k.split(','))])

                if headerline:
                    header = dlist[0]
                    print(f'{k},fld,{a}')
                    headerline = False

                else:
                    for fld in f.split(','):
                        f_loc = header.index(fld)

                        # valuetype check goes here
                        targetcol = []
                        for line in dlist:
                            # input cleanup goes here
                            try:
                                # if the value can be converted to float, included
                                targetcol.append(float(line[f_loc]))
                            except ValueError:
                                # otherwise, place nan
                                targetcol.append(float('nan'))

                        if targetcol == []:
                            print(f'{id},{fld},')
                        else:
                            y = np.abs(np.fft.rfft(targetcol))

                            mean = y.dot(np.arange(len(y)))/y.sum()

                            moment2 = y.dot(np.arange(len(y))**2)/y.sum()
                            variance = moment2 - mean ** 2

                            # output cleanup goes here
                            if (variance is None) or (variance == '') or (variance ==  'None'):
                                # print empty string
                                print(f'{id},{fld},')
                            else:
                                if np.isfinite(float(variance)):
                                    print(f'{id},{fld},{variance:.{precision}g}')
                                else:
                                    print(f'{id},{fld},')
                                    
                                
            sys.__stdout__.flush()#not needed for bigger data

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def fft_agg(self, **kwargs):
        # body of this method adapted from:
        # github.com/nysol/nysol_python/blob/master/scripts/sample/mkfeature.py
        try:
            import numpy as np
            
            f = kwargs.get('f')
            a = kwargs.get('a')
            x = kwargs.get('x')
            k = kwargs.get('k')
            precision = kwargs.get('precision')

            headerline = True

            for dlist in nm.mstdin().keyblock(k, x, header = True):
                id = ','.join(dlist[0][:len(k.split(','))])

                if headerline:
                    header = dlist[0]
                    print(f'{k},fld,{a}_centroid,{a}_var,{a}_skew,{a}_kurtosis')
                    headerline = False

                else:
                    for fld in f.split(','):
                        f_loc = header.index(fld)

                        y = np.abs(np.fft.rfft([float(xdlist[f_loc]) 
                                                for xdlist in dlist]))

                        centroid = y.dot(np.arange(len(y)))/y.sum()
                        moment2 = y.dot(np.arange(len(y))**2)/y.sum()
                        variance = moment2 - centroid ** 2

                        if variance < 0.5:
                            skew = np.nan
                            kurtosis = np.nan
                        else:
                            moment3 = y.dot(np.arange(len(y))**3) / y.sum()
                            skew = ( moment3 - 3 * centroid * variance - centroid**3 ) / variance**(1.5)
                                        
                            kurtosis =( (y.dot(np.arange(len(y))**4) / y.sum()) - 4 * centroid * moment3
                                + 6 * moment2 * centroid**2 - 3*centroid) / variance**2


                        print(f'{id},{fld},{centroid:.{precision}g},{variance:.{precision}g},{skew:.{precision}g},{kurtosis:.{precision}g}')
            sys.__stdout__.flush()#not needed for bigger data

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def slope(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            x = kwargs.get('x')
            k = kwargs.get('k')
            precision = kwargs.get('precision')

            dateformat = kwargs.pop('dateformat')

            fs = f.split(',')

            # fix time column
            subcmd = self.fixtimecolumn(subcmd, x, dateformat)

            for fld in fs: 
                subcmd <<= nm.mcal(a = f'{fld}_prod',c = f'${{{fld}}}*${{uxt}}')
            
            prod_fldnames = ','.join([f'{fld}_prod' for fld in fs])
            
            subcmd <<= nm.msummary(k = k, f = f'{prod_fldnames},{f},uxt',
                                c = 'mean,var')
        
            subcmd <<= nm.m2cross(k = f'{k},fld', f = 'mean,var', a = f'type,{a}')
            subcmd <<= nm.mcal(a = 'tmp_colnames', c = '$s{fld}+"_"+$s{type}')
            subcmd <<= nm.mcross(f = f'{a}', s = 'tmp_colnames', k = k)
            for fld in fs:
                subcmd <<= nm.mcal(a = fld, precision = precision,
                    c = f'(${{{fld}_prod_mean}}-(${{{fld}_mean}}*${{uxt_mean}}))/${{uxt_var}}')
            
            subcmd <<= nm.mcross(f = f, s = 'fld', k = k)
            subcmd <<= nm.mcut(f = f'{k},fld,{a}')
            
            return subcmd

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def pearson(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            x = kwargs.get('x')
            k = kwargs.get('k')
            precision = kwargs.get('precision')
            dateformat = kwargs.pop('dateformat')

            fs = f.split(',')

            sims = [None] * len(fs)
            subcmd_o = None

            subcmd = self.fixtimecolumn(subcmd, x, dateformat)
            x = 'uxt'
            
            for i,fld in enumerate(fs): 
                sims[i] <<= nm.msim(i = subcmd, k = k, c = 'pearson', 
                                    f = f'{x},{fld}', a = 'fld2,fld')
            
            subcmd_o <<= nm.m2cat(i = sims)
            subcmd_o <<= nm.mfldname(f = f'pearson:{a}')
            
            subcmd_o <<= nm.mcut(f = f'{k},fld,{a}')

            return subcmd_o
            
        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def linear_trend(self, subcmd, **kwargs):
        try:
            _temp = mtemp.Mtemp().file()

            f = kwargs.get('f')
            a = kwargs.get('a')
            x = kwargs.get('x')
            k = kwargs.get('k')
            
            flags = kwargs.get('flags')
            finalcols = [a[flag] for flag in flags]

            precision = kwargs.get('precision')
            
            dateformat = kwargs.pop('dateformat')

            fs = f.split(',')
            targets = [None] * len(fs)
            covars = [None] * len(fs)
            counts = [None] * len(fs)
            subcmd_mid = None
            subcmd_o = None

            # fix time column
            subcmd = self.fixtimecolumn(subcmd, x, dateformat)


            meanval = nm.mstats(k = k, i = subcmd, f = f'uxt,{f}', c = 'mean')

            for i, fld in enumerate(fs):
                counts[i] <<= nm.msel(i = self.all_msums, 
                                      c = f'$s{{fld}}=="{fld}"')

                covars[i] <<= nm.msim(k = k, i = subcmd, f = f'uxt,{fld}', 
                                   c = 'covar:__covar')

                targets[i] <<= nm.mstats(k = k, i = subcmd, c = 'var',
                                         f = f'uxt:__Sxx,{fld}:__Syy')
                targets[i] <<= nm.mcal(c = 'sqrt(${__Sxx}*${__Syy})', a = '__rden')
                targets[i] <<= nm.mjoin(k = k, m = covars[i], f = '__covar')
                targets[i] <<= nm.mnjoin(k = k, m = counts[i], f = 'fld,__count')
                targets[i] <<= nm.mjoin(k = k, m = meanval, f = f'uxt:__xmean,{fld}:__ymean')
                targets[i] <<= nm.mcal(c = '${__count}-2', a = '__df')

                targets[i] <<= nm.mcal(c = 'if(${__rden}==0,0,${__covar}/${__rden})',
                                       a = f'{a["linregress_rvalue"]}',
                                       precision = precision)
                targets[i] <<= nm.mcal(c = '${__covar}/${__Sxx}', 
                                       a = f'{a["slope"]}',
                                       precision = precision)
                targets[i] <<= nm.mcal(c = f'${{__ymean}}-(${{{a["slope"]}}}*${{__xmean}})',
                                       a = f'{a["y_int"]}',
                                       precision = precision)
                targets[i] <<= nm.mcal(c = f'${{{a["linregress_rvalue"]}}}*sqrt(${{__df}}/((1-${{{a["linregress_rvalue"]}}})*(1+${{{a["linregress_rvalue"]}}})))',
                                       a = '__t',
                                       precision = precision)
                targets[i] <<= nm.mcal(c = f'sqrt((1-${{{a["linregress_rvalue"]}}}^2)*${{__Syy}}/${{__Sxx}}/${{__df}})',
                                       a = f'{a["linregress_stderr"]}',
                                       precision = precision)

                _cval = ['fld', '__Syy', '__Sxx', '__rden', '__covar', 
                         '__count', '__xmean', '__ymean', '__df', f'{a["linregress_rvalue"]}', 
                         f'{a["slope"]}', f'{a["y_int"]}', '__t', f'{a["linregress_stderr"]}']
                targets[i] <<= nm.mcut(f= k.split(',') + _cval)

            if 'linregress_pvalue' in flags:
                subcmd_mid <<= nm.mread(i = targets)

                # with nm.mstdout() as tmpfile:
                with mcsvout(_temp, f = k.split(',') + _cval + [f'{a}_pvalue']) as tmpfile:
                    from scipy.stats import distributions
                    headerline = True
                    for line in subcmd_mid.getline(header = True):
                        if headerline:
                            header = line
                            headerline = False
                        else:
                            t = float(line[header.index('__t')])
                            df = float(line[header.index('__df')])
                            
                            line.append(2 * distributions.t.sf(np.abs(t),df))
                            
                            tmpfile.write(line)
                
                subcmd_o <<= nm.mcut(i = _temp, f = [k, 'fld'] + finalcols)
            else:
                
                subcmd_o <<= nm.mcut(i = targets, f = [k, 'fld'] + finalcols)

            
            return subcmd_o
            
        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def firstmin(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            x = kwargs.get('x')
            k = kwargs.get('k')
            precision = kwargs.get('precision')

            dateformat = kwargs.pop('dateformat')

            subcmd_o = None

            fs = f.split(',')
            targets = [None] * len(fs) 
            msum = [None] * len(fs) 

            # fix time column
            subcmd = self.fixtimecolumn(subcmd, x, dateformat)

            for i, fld in enumerate(fs):
                msum[i] <<= nm.msummary(c = 'min,range', k = k,
                                        f = 'uxt', i = subcmd)
                msum[i] <<= nm.m2cross(f = 'min,range', 
                                       a = '__type__,__val__',
                                       k = f'{k},fld')
                msum[i] <<= nm.mcal(a = '__tmpcol__',
                                    c = f'$s{{fld}}+"_"+$s{{__type__}}')
                msum[i] <<= nm.mcross(k = k, f = '__val__', s = '__tmpcol__')
                

                targets[i] <<= nm.mbest(k = k, s = f'{fld}%n,uxt%n',
                                        i = subcmd)
                targets[i] <<= nm.mjoin(k = k, m = msum[i], f = f'uxt_min,uxt_range')
                targets[i] <<= nm.mcal(c = '(${uxt}-${uxt_min})/${uxt_range}',
                                       a = a, precision = precision)
                targets[i] <<= nm.mcal(c = f'"{fld}"', a = 'fld')

            subcmd_o <<= nm.mcut(i = targets, f = f'{k},fld,{a}')

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def firstmax(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            x = kwargs.get('x')
            k = kwargs.get('k')
            precision = kwargs.get('precision')

            dateformat = kwargs.pop('dateformat')

            subcmd_o = None

            fs = f.split(',')
            targets = [None] * len(fs) 
            msum = [None] * len(fs) 

            # fix time column
            subcmd = self.fixtimecolumn(subcmd, x, dateformat)

            for i, fld in enumerate(fs):
                msum[i] <<= nm.msummary(c = 'min,range', k = k,
                                        f = 'uxt', i = subcmd)
                msum[i] <<= nm.m2cross(f = 'min,range', 
                                       a = '__type__,__val__',
                                       k = f'{k},fld')
                msum[i] <<= nm.mcal(a = '__tmpcol__',
                                    c = f'$s{{fld}}+"_"+$s{{__type__}}')
                msum[i] <<= nm.mcross(k = k, f = '__val__', s = '__tmpcol__')
                

                targets[i] <<= nm.mbest(k = k, s = f'{fld}%nr,uxt%n',
                                        i = subcmd)
                targets[i] <<= nm.mjoin(k = k, m = msum[i], f = f'uxt_min,uxt_range')
                targets[i] <<= nm.mcal(c = '(${uxt}-${uxt_min})/${uxt_range}',
                                       a = a, precision = precision)
                targets[i] <<= nm.mcal(c = f'"{fld}"', a = 'fld')

            subcmd_o <<= nm.mcut(i = targets, f = f'{k},fld,{a}')

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def lastmin(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            x = kwargs.get('x')
            k = kwargs.get('k')
            precision = kwargs.get('precision')

            dateformat = kwargs.pop('dateformat')

            subcmd_o = None

            fs = f.split(',')
            targets = [None] * len(fs) 
            msum = [None] * len(fs) 

            # fix time column
            subcmd = self.fixtimecolumn(subcmd, x, dateformat)

            for i, fld in enumerate(fs):
                msum[i] <<= nm.msummary(c = 'min,range', k = k,
                                        f = 'uxt', i = subcmd)
                msum[i] <<= nm.m2cross(f = 'min,range', 
                                       a = '__type__,__val__',
                                       k = f'{k},fld')
                msum[i] <<= nm.mcal(a = '__tmpcol__',
                                    c = f'$s{{fld}}+"_"+$s{{__type__}}')
                msum[i] <<= nm.mcross(k = k, f = '__val__', s = '__tmpcol__')
                

                targets[i] <<= nm.mbest(k = k, s = f'{fld}%n,uxt%nr',
                                        i = subcmd)
                targets[i] <<= nm.mjoin(k = k, m = msum[i], f = f'uxt_min,uxt_range')
                targets[i] <<= nm.mcal(c = '(${uxt}-${uxt_min})/${uxt_range}',
                                       a = a, precision = precision)
                targets[i] <<= nm.mcal(c = f'"{fld}"', a = 'fld')

            subcmd_o <<= nm.mcut(i = targets, f = f'{k},fld,{a}')

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def lastmax(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            x = kwargs.get('x')
            k = kwargs.get('k')
            precision = kwargs.get('precision')

            dateformat = kwargs.pop('dateformat')
           
            subcmd_o = None

            fs = f.split(',')
            targets = [None] * len(fs) 
            msum = [None] * len(fs) 

            # fix time column
            subcmd = self.fixtimecolumn(subcmd, x, dateformat)

            for i, fld in enumerate(fs):
                msum[i] <<= nm.msummary(c = 'min,range', k = k,
                                        f = 'uxt', i = subcmd)
                msum[i] <<= nm.m2cross(f = 'min,range', 
                                       a = '__type__,__val__',
                                       k = f'{k},fld')
                msum[i] <<= nm.mcal(a = '__tmpcol__',
                                    c = f'$s{{fld}}+"_"+$s{{__type__}}')
                msum[i] <<= nm.mcross(k = k, f = '__val__', s = '__tmpcol__')

                targets[i] <<= nm.mbest(k = k, s = f'{fld}%nr,uxt%nr',
                                        i = subcmd)
                targets[i] <<= nm.mjoin(k = k, m = msum[i], f = f'uxt_min,uxt_range')
                targets[i] <<= nm.mcal(c = '(${uxt}-${uxt_min})/${uxt_range}',
                                       a = a, precision = precision)
                targets[i] <<= nm.mcal(c = f'"{fld}"', a = 'fld')

            subcmd_o <<= nm.mcut(i = targets, f = f'{k},fld,{a}')

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def meanchange(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            x = kwargs.get('x')
            k = kwargs.get('k')
            precision = kwargs.get('precision')

            dateformat = kwargs.pop('dateformat')

            fs = f.split(',')
            targets = [None] * len(fs)

            subcmd_o = None

            # fix time column
            subcmd = self.fixtimecolumn(subcmd, x, dateformat)

            for i, fld in enumerate(fs):
                targets[i] <<= nm.mslide(k = k, s = 'uxt%n', i = subcmd, 
                                         f = f'{fld}:__shifted{fld}')
                targets[i] <<= nm.mcal(c = f'${{__shifted{fld}}}-${{{fld}}}', 
                                       a = a)
                targets[i] <<= nm.mavg(k = k, f = a, precision = precision)

                targets[i] <<= nm.msetstr(a = 'fld', v = fld)
                targets[i] <<= nm.mcut(f = f'{k},fld,{a}')

            subcmd_o <<= nm.m2cat(i = targets)

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def meanabschange(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            x = kwargs.get('x')
            k = kwargs.get('k')
            precision = kwargs.get('precision')

            dateformat = kwargs.pop('dateformat')

            fs = f.split(',')
            targets = [None] * len(fs)

            subcmd_o = None

            # fix time column
            subcmd = self.fixtimecolumn(subcmd, x, dateformat)

            for i, fld in enumerate(fs):
                targets[i] <<= nm.mslide(k = k, s = 'uxt%n', i = subcmd, 
                                         f = f'{fld}:__shifted{fld}')
                targets[i] <<= nm.mcal(c = f'abs(${{__shifted{fld}}}-${{{fld}}})', 
                                       a = a)
                targets[i] <<= nm.mavg(k = k, f = a, precision = precision)

                targets[i] <<= nm.msetstr(a = 'fld', v = fld)
                targets[i] <<= nm.mcut(f = f'{k},fld,{a}')

            subcmd_o <<= nm.m2cat(i = targets)

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def abs_sum_of_changes(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            x = kwargs.get('x')
            k = kwargs.get('k')
            precision = kwargs.get('precision')

            dateformat = kwargs.pop('dateformat')

            fs = f.split(',')

            # fix time column
            subcmd = self.fixtimecolumn(subcmd, x, dateformat)

            for fld in fs:
                subcmd <<= nm.msortf(f = f'{k},uxt%n')
                subcmd <<= nm.mcal(c = f'abs(${{{fld}}}-#{{{fld}}})', a = f'__tmp{fld}__')
                subcmd <<= nm.mcut(f = fld, r = True)
                subcmd <<= nm.mfldname(f = f'__tmp{fld}__:{fld}')
            
            subcmd <<= nm.msummary(k = k, c = f'sum:{a}', f = f, 
                                   precision = precision)

            return subcmd

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def autocorrelation_agg(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            x = kwargs.get('x')
            k = kwargs.get('k')
            precision = kwargs.get('precision')

            dateformat = kwargs.pop('dateformat')

            fs = f.split(',')
            subcmd_o = None

            targets = [None] * len(fs) 
            msummary = [None] * len(fs) 

            # fix time column
            subcmd = self.fixtimecolumn(subcmd, x, dateformat)

            for i, fld in enumerate(fs):
                msummary[i] <<= nm.msummary(k = k, c = 'mean,var,count', f =fld, 
                                          i = subcmd)
                
                targets[i] <<= nm.mcut(f = f'{k},uxt', i = subcmd)
                targets[i] <<= nm.mjoin(k = k, m = msummary[i], f = 'mean,var,count')
                targets[i] <<= nm.mcombi(k = k, f = 'uxt', a = 't1,t2', n = 2)
                targets[i] <<= nm.mfsort(f = 't1,t2', n = True)
                targets[i] <<= nm.mcal(c = '${t2}-${t1}', a = 'rag')

                targets[i] <<= nm.mjoin(k = f'{k},t1', m = subcmd, 
                                        K = f'{k},uxt', f = f'{fld}:{fld}_t1')
                targets[i] <<= nm.mjoin(k = f'{k},t2', m = subcmd, 
                                        K = f'{k},uxt', f = f'{fld}:{fld}_t2')
                targets[i] <<= nm.mcal(a = 'sub_t1t2',
                    c = f'(${{{fld}_t1}}-${{mean}})*(${{{fld}_t2}}-${{mean}})')
                targets[i] <<= nm.msum(k = f'{k},rag', f = 'sub_t1t2')
                targets[i] <<= nm.mcal(a = fld, 
                                     c = '${sub_t1t2}/(${count}-${rag})/${var}')
                targets[i] <<= nm.msummary(k = k, f = fld, precision = precision,
                        c = f'mean:{a}_mean,median:{a}_median,var:{a}_var')

            subcmd_o <<= nm.mcut(i = targets, f = f'{k},fld,{a}_*')

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def longeststrikeabovemean(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            x = kwargs.get('x')
            k = kwargs.get('k')

            dateformat = kwargs.pop('dateformat')

            fs = f.split(',')
            targets = [None] * len(fs)
            msummary = None

            subcmd_o = None

            # fix time column
            subcmd = self.fixtimecolumn(subcmd, x, dateformat)

            condition = [f'($s{{fld}}=="{fld}")' for fld in fs]
            msummary <<= nm.msel(i = self.all_msums, c = '||'.join(condition))

            for i, fld in enumerate(fs):

                targets[i] <<= nm.mnjoin(i = subcmd, m = msummary, k = k, 
                                        f = 'fld,__mean')
                targets[i] <<= nm.msel(c = f'$s{{fld}}=="{fld}"')

                targets[i] <<= nm.msortf(f = f'{k},uxt%n')
                targets[i] <<= nm.mcal(c = f'${{__mean}}<=${{{fld}}}', a = '__above')
                targets[i] <<= nm.mcount(q = True, k = f'{k},__above', a = '__a_count')
                targets[i] <<= nm.mbest(k = k, s = '__above%nr,__a_count%nr', size = 1)
                targets[i] <<= nm.mcal(c = 'if(${__above}==0,0,${__a_count})', a = a)
                targets[i] <<= nm.mcut(f = f'{k},fld,{a}')

            subcmd_o <<= nm.m2cat(i = targets)
            
            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def longeststrikebelowmean(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            x = kwargs.get('x')
            k = kwargs.get('k')

            dateformat = kwargs.pop('dateformat')

            fs = f.split(',')
            targets = [None] * len(fs)
            msummary = None

            subcmd_o = None

            # fix time column
            subcmd = self.fixtimecolumn(subcmd, x, dateformat)
            
            condition = [f'($s{{fld}}=="{fld}")' for fld in fs]
            msummary <<= nm.msel(i = self.all_msums, c = '||'.join(condition))

            for i, fld in enumerate(fs):
                targets[i] <<= nm.mnjoin(i = subcmd, m = msummary, k = k, 
                                        f = 'fld,__mean')
                targets[i] <<= nm.msel(c = f'$s{{fld}}=="{fld}"')

                targets[i] <<= nm.msortf(f = f'{k},uxt%n')
                targets[i] <<= nm.mcal(c = f'${{__mean}}<=${{{fld}}}', a = '__below')
                targets[i] <<= nm.mcount(q = True, k = f'{k},__below', a = '__b_count')
                targets[i] <<= nm.mbest(k = k, s = '__below%nr,__b_count%nr', size = 1)
                targets[i] <<= nm.mcal(c = 'if(${__below}==0,0,${__b_count})', a = a)
                targets[i] <<= nm.mcut(f = f'{k},fld,{a}')

            subcmd_o <<= nm.m2cat(i = targets)

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def mean2ndderivative_central(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            x = kwargs.get('x')
            k = kwargs.get('k')
            precision = kwargs.get('precision')

            dateformat = kwargs.pop('dateformat')

            fs = f.split(',')
            targets = [None] * len(fs)

            subcmd_o = None

            # fix time column
            subcmd = self.fixtimecolumn(subcmd, x, dateformat)

            for i, fld in enumerate(fs):
                targets[i] <<= nm.mslide(k = k, s = 'uxt%n', f = f'{fld}:__shifted{fld}',
                                         t = 2, i = subcmd)
                targets[i] <<= nm.mcal(c = f'(${{__shifted{fld}2}}-2*${{__shifted{fld}1}}+${{{fld}}})',
                                       a = a)
                targets[i] <<= nm.mavg(k = k, f = a, precision = precision)
                targets[i] <<= nm.msetstr(a = 'fld', v = fld)
                targets[i] <<= nm.mcut(f = f'{k},fld,{a}')

            subcmd_o <<= nm.m2cat(i = targets)
            
            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    # --------------- 3 vars -----------------------

    def index_mass_quantile(self,subcmd, **kwargs):
        f = kwargs.get('f')
        a = kwargs.get('a')
        k = kwargs.get('k')
        x = kwargs.get('x')
        n = kwargs.get('n')
        precision = kwargs.get('precision')
        dateformat = kwargs.pop('dateformat')

        calcid = 'imq' 

        try:
            # check if float
            param = float(n)
            
            # check if out of bounds
            if param < 0 or param > 1:
                errmsg = self.generateCommandErrorMessage('ParameterOutOfBoundsError', 'n', n, param_calc = calcid)
                raise Exception(errmsg)
        except ValueError:
            errmsg = self.generateCommandErrorMessage('ParameterTypeError', 'n', n, param_calc = calcid)
            raise Exception(errmsg)

        fs = f.split(',')
        targets = [None] * len(fs)
        mcal = [None] * len(fs)
        msum = [None] * len(fs)
        msummary = [None] * len(fs)

        subcmd_o = None

        # fix time column
        subcmd = self.fixtimecolumn(subcmd, x, dateformat)
        x = 'uxt'

        for i, fld in enumerate(fs):
            mcal[i] <<= nm.mcal(c = f'abs(${{{fld}}})', a = f'__abs{fld}', 
                                i = subcmd)
            msum[i] <<= mcal[i].msum(k = k, f = f'__abs{fld}')

            msummary[i] <<= nm.msummary(i = subcmd, k = k, f = fld,
                                    c = 'count:__count')

            targets[i] <<= nm.maccum(k = k, s = f'{x}%n', f = f'__abs{fld}:__abs{fld}_a',
                                        i = mcal[i])
            targets[i] <<= nm.mjoin(k = k, f = f'__abs{fld}:__abs{fld}_ttl',
                                    m = msum[i])
            targets[i] <<= nm.mnjoin(k = k, f = f'fld,__count', m = msummary[i])
            targets[i] <<= nm.mcal(c = f'(${{__abs{fld}_a}}/${{__abs{fld}_ttl}})>={n}',
                                    a = '__mc')
            targets[i] <<= nm.mbest(k = k, s = f'__mc%nr,{x}%n', size = 1)
            targets[i] <<= nm.mcal(c = f'(${{{x}}})/${{__count}}', a = f'{a}_{n}',
                                    precision = precision)

            targets[i] <<= nm.mcut(f = f'{k},fld,{a}_{n}')

        subcmd_o <<= nm.m2cat(i = targets)

        return subcmd_o

    def numbercrossing(self, subcmd, **kwargs):
        f = kwargs.get('f')
        a = kwargs.get('a')
        x = kwargs.get('x')
        k = kwargs.get('k')
        n = kwargs.get('n')

        calcid = 'crossing_m'

        try:
            # check if float
            param = float(n)
        except ValueError:
            errmsg = self.generateCommandErrorMessage('ParameterTypeError', 'n', n, param_calc = calcid)
            raise Exception(errmsg)

        dateformat = kwargs.pop('dateformat')

        subcmd_o = None

        fs = f.split(',')
        targets = [None] * len(fs) 

        # fix time column
        subcmd = self.fixtimecolumn(subcmd, x, dateformat)

        for i, fld in enumerate(fs):
            targets[i] <<= nm.mcal(c = f'${{{fld}}}>{n}', a = '__pos', 
                                i = subcmd)
            targets[i] <<= nm.mslide(k = k, s = 'uxt%n', f = '__pos:__posN')
            targets[i] <<= nm.mcal(c = '${__pos}!=${__posN}', a = '__diffT')
            targets[i] <<= nm.mcount(k = k + ',__diffT', a = '__cnt')
            targets[i] <<= nm.mbest(k = k, s = '__diffT%nr', size = 1)
            targets[i] <<= nm.mcal(c = 'if(${__diffT}==0,0,${__cnt})', 
                                    a = f'{a}_{n}')
            targets[i] <<= nm.msetstr(a = 'fld', v = fld)

        subcmd_o <<= nm.mcut(i = targets, f = f'{k},fld,{a}_{n}')

        return subcmd_o

    def countpeaks(self, subcmd, **kwargs):
        f = kwargs.get('f')
        a = kwargs.get('a')
        x = kwargs.get('x')
        k = kwargs.get('k')
        n = kwargs.get('n')

        calcid = 'peaks'

        try:
            # check if float
            param = float(n)
            
            # check if not integer or less than 1
            if (not param.is_integer()) or param < 1:
                errmsg = self.generateCommandErrorMessage('ParameterOutOfBoundsError', 'n', n, param_calc = calcid)
                raise Exception(errmsg)
        except ValueError:
            errmsg = self.generateCommandErrorMessage('ParameterTypeError', 'n', n, param_calc = calcid)
            raise Exception(errmsg)

        dateformat = kwargs.pop('dateformat')

        subcmd_o = None

        fs = f.split(',')
        targets = [None] * len(fs) 
        mslide = [None] * len(fs) 

        # fix time column
        subcmd = self.fixtimecolumn(subcmd, x, dateformat)

        # # take starting key columns
        # _keys = None
        # _keys <<= nm.mcut(f = k, i = subcmd)
        # _keys <<= nm.muniq(k = k)

        for i, fld in enumerate(fs):
            mslide[i] <<= nm.mslide(k = k, s = 'uxt%n', t = n, r = True, 
                                    f = f'{fld}:{fld}_up_', i = subcmd)

            targets[i] <<= nm.mslide(k = k, s = 'uxt%n', t = n,
                                        f = f'{fld}:{fld}_down_', i = subcmd)
            
            targets[i] <<= nm.mjoin(k = f'{k},uxt', f = f'{fld}_up_*',
                                    m = mslide[i], n = True)
            # targets[i] <<= nm.mdelnull(f = f'{fld}_up_*,{fld}_down_*')
            targets[i] <<= nm.mcal(c = f'max(${{{fld}_up*}},${{{fld}_down_*}})',
                                    a = '__rollmax__')
            targets[i] <<= nm.mcal(c = f'${{{fld}}}>${{__rollmax__}}',
                                    a = f'{a}_{n}')

            targets[i] <<= nm.msum(k = k, f = f'{a}_{n}')
            targets[i] <<= nm.mcal(a = 'fld', c = f'"{fld}"')
            targets[i] <<= nm.mcut(f = f'{k},fld,{a}_{n}')


        subcmd_o <<= nm.mread(i = targets)
        # subcmd_o <<= nm.mnjoin(i = _keys, k = k, m = targets, n = True)

        return subcmd_o

    def autocorrelation(self, subcmd, **kwargs):
        f = kwargs.get('f')
        a = kwargs.get('a')
        x = kwargs.get('x')
        k = kwargs.get('k')
        n = kwargs.get('n')
        precision = kwargs.get('precision')

        calcid = 'autocorr'

        try:
            # check if float
            param = float(n)
            
            # check if not integer
            if (not param.is_integer()) or param < 1:
                errmsg = self.generateCommandErrorMessage('ParameterOutOfBoundsError', 'n', n, param_calc = calcid)
                raise Exception(errmsg)
        except ValueError:
            errmsg = self.generateCommandErrorMessage('ParameterTypeError', 'n', n, param_calc = calcid)
            raise Exception(errmsg)

        dateformat = kwargs.pop('dateformat')

        subcmd_o = None

        fs = f.split(',')
        targets = [None] * len(fs)
        msummary = [None] * len(fs)

        # fix time column
        subcmd = self.fixtimecolumn(subcmd, x, dateformat)

        for i, fld in enumerate(fs):
            if n == 0:
                targets[i] <<= nm.muniq(k = k, i = subcmd)
                targets[i] <<= nm.mcut(f = k)
                targets[i] <<= nm.msetstr(v = fld, a = 'fld') 
                targets[i] <<= nm.msetstr(v = 1, a = a)
            else:
                msummary[i] <<= nm.msummary(i = subcmd, k = k, f = fld,
                                    c = f'mean:__mean,var:__var,count:__count')

                targets[i] <<= nm.mjoin(i = subcmd, m = msummary[i], k = k,
                        f = 'fld,__mean,__var,__count')

                targets[i] <<= nm.mslide(k = k, s = 'uxt%n', t = n, l = True, 
                                        f = f'{fld}:__{fld}_L')
                targets[i] <<= nm.mcal(c = f'(${{{fld}}}-${{__mean}})*(${{__{fld}_L}}-${{__mean}})',
                                        a = f'__{fld}_m')
                targets[i] <<= nm.msum(k = k, f = f'__{fld}_m')
                targets[i] <<= nm.msetstr(a = '__lag', v = n)
                targets[i] <<= nm.mcal(a = f'{a}_{n}', precision = precision,
                    c = f'${{__{fld}_m}}/(${{__count}}-${{__lag}})/${{__var}}')
                targets[i] <<= nm.mcut(f = f'{k},fld,{a}_{n}')

        subcmd_o <<= nm.m2cat(i = targets)

        return subcmd_o
    
    def c3(self,subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')
            s = kwargs.get('s')
            n = kwargs.get('n')

            fs = f.split(',')
            targets = [None] * len(fs)
            subcmd_o = None

            fldsL = [f'{fld}:__{fld}_L' for fld in fs]
            fldsL2 = [f'{fld}:__{fld}_L2' for fld in fs]
            flds_ = [f'__{fld}_*' for fld in fs]

            subcmd <<= nm.mslide(k = k, s = s, f = fldsL, 
                                        n = True, l = True)
            subcmd <<= nm.mslide(k = k, s = s, f = fldsL2,
                                        t = int(n)*2, l = True)

            for i, fld in enumerate(fs):
                targets[i] <<= nm.mcal(c=f'${{{fld}}}*${{__{fld}_L}}*${{__{fld}_L2}}',
                                       a = '__tmp', i = subcmd)
                targets[i] <<= nm.mcut(f = flds_ + [fld], r = True)
                targets[i] <<= nm.mfldname(f = f'__tmp:{fld}')

            subcmd_o <<= nm.msummary(k = k, c = f'mean:{a}_{n}', f = f, 
                                     i = targets)

            subcmd_o <<= nm.mcut(f = f'{k},fld,{a}_{n}')

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)
    
    def time_reversal_asymmetry(self,subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')
            s = kwargs.get('s')
            n = kwargs.get('n')

            fs = f.split(',')
            targets = [None] * len(fs)
            subcmd_o = None

            fldsn = [f'{fld}:__{fld}n' for fld in fs]
            fldsnn = [f'{fld}:__{fld}nn' for fld in fs]
            flds_ = [f'__{fld}*' for fld in fs]

            subcmd <<= nm.mslide(k = k, s = s, f = fldsn, 
                                 t = n, n = True, l = True)
            subcmd <<= nm.mslide(k = k, s = s, f = fldsnn,
                                 t = int(n)*2, l = True)

            for i, fld in enumerate(fs):
                targets[i] <<= nm.mcal(c=f'${{__{fld}nn}}^2*${{__{fld}n}}-${{{fld}}}^2*${{__{fld}n}}',
                                       a = f'{a}_{n}', i = subcmd)
                targets[i] <<= nm.mavg(k = k, f = f'{a}_{n}')
                targets[i] <<= nm.mcut(f = flds_, r = True)
                targets[i] <<= nm.msetstr(a = 'fld', v = fld)

            subcmd_o <<= nm.mcut(f = f'{k},fld,{a}_{n}', i = targets)

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    # ## Template
    # subcmd = None
    # subcmd <<= nm.mstdin()

    # subcmd <<= nm.mstdout()
    # subcmd.run()

    def run(self, args, inputs):
        import fnmatch as fn

        _args = copy.deepcopy(args)
        
        msummaryoptions = [
            'sum',
            'mean',
            'count',
            'ucount',
            'devsq',
            'var',
            'uvar',
            'sd',
            'usd',
            'cv',
            'min',
            'qtile1',
            'median',
            'qtile3',
            'max',
            'range',
            'qrange',
            'mode',
            'skew',
            'uskew',
            'kurt',
            'ukurt'
        ]

        nysol_calcs = {
            # 0 fields (input k, a, fld)
            'rows' : self.rows,
            # 1 field (input k, a, f)
            'miss' : self.missingdata,
            'rms' : self.rootmeansquare,
            'hmean' : self.harmonicmean,
            'gmean' : self.geometricmean,
            'var_gt_sd' : self.variance_larger_than_sd,
            'strmax' : self.strmax,
            'strmin' : self.strmin,
            'strucount' : self.strucount,
            'abs_energy' : self.abs_energy, 
            'has_dup' : self.hasduplicate,    
            'has_dup_max' : self.hasduplicatemin,
            'has_dup_min' : self.hasduplicatemax,
            'mean_ad' : self.meanabsolutedeviation,
            'median_ad' : self.medianabsolutedeviation,
            'repeatdata' : self.reoccurringdatapoints,
            'repeatvalues' : self.reoccurringvalues,
            'sum_repeatdata' : self.sumofreoccurringdatapoints,
            'sum_repeatvalues' : self.sumofreoccurringvalues,
            'ratio_unique' : self.ratio_value_number_to_series_length,
            'count_above_mean' : self.countabovemean,
            'count_below_mean' : self.countbelowmean,
            'sym_looking' : self.symmetry_looking,
            'large_sd' : self.large_standard_dev,
            'value_count' : self.value_count,
            'range_count' : self.range_count,
            'ratio_beyond_rsigma' : self.ratio_beyond_rsigma,
            'quantile' : self.quantile,
            'binned_entropy' : self.binned_entropy,
            # 1 field + time (input k, a, f, x)
            'integral' : self.integral,
            'meanf' : self.meanfrequency,
            'varf' : self.frequencyvar,
            'fft_agg' : self.fft_agg,
            'slope' : self.slope,
            'slope_pearson' : self.pearson,
            'firstmin' : self.firstmin,
            'firstmax' : self.firstmax,
            'lastmin' : self.lastmin,
            'lastmax' : self.lastmax,
            'mean_change' : self.meanchange,
            'mean_abs_change' : self.meanabschange,
            'abs_sum_changes' : self.abs_sum_of_changes, 
            'autocorr_agg' : self.autocorrelation_agg,
            'longest_strike_above_mean' : self.longeststrikeabovemean,
            'longest_strike_below_mean' : self.longeststrikebelowmean,
            'mean_second_derivative_central' : self.mean2ndderivative_central,
            'energy_ratio_by_chunks' : self.energy_ratio_by_chunks,
            # 2+1 fields
            'imq' : self.index_mass_quantile,
            'crossing_m' : self.numbercrossing,
            'peaks' : self.countpeaks,
            'autocorr' : self.autocorrelation,
            'c3' : self.c3,
            'time_reversal_asymmetry' : self.time_reversal_asymmetry,
            # aggregate functions
            'linregress' : self.linear_trend
        }

        python_calcs = [
            'meanf',
            'varf',
            'fft_agg'
        ]

        grouped_calcs = {
            'linregress': [
                'slope',
                'y_int',
                'linregress_pvalue',
                'linregress_rvalue',
                'linregress_stderr'
            ]
        }

        msum_dependencies = {
            'has_dup' : ['count'], 
            'var_gt_sd' : ['var','sd'],
            'mean_ad' : ['mean'], 
            'median_ad' : ['median'], 
            'ratio_unique' : ['count', 'ucount'], 
            'count_above_mean' : ['mean'], 
            'count_below_mean' : ['mean'], 
            'sym_looking' : ['mean', 'median', 'max', 'min'],
            'large_sd' : ['sd', 'max', 'min'],
            'ratio_beyond_rsigma' : ['mean', 'sd', 'count'],
            'quantile' : ['count'],
            'binned_entropy' : ['count'],
            'energy_ratio_by_chunks': ['count','sd'],
            'longest_strike_above_mean' : ['mean'],
            'longest_strike_below_mean' : ['mean'],
            'linregress': ['count']
        } 

        supports_str = [
            'rows',
            'miss',
            'strmin',
            'strmax',
            'strucount',
            'has_dup',
            'value_count'
        ]

        msum_prereqs = set()

        sys.setrecursionlimit(2**20)

        # self.header = inputs['i'].content.getline(header=True)
        # self.header = next(self.header)

        # ヘッダ行を取得する
        self.header = self.get_field_names(inputs['i'])

        k = _args.get('k')
        prec = _args.get('precision')
        formatstring = _args.pop('format')

        # check format string for errors
        if any(char in formatstring for char in '*?[],:\\\"\' '):
            errmsg = self.generateCommandErrorMessage('ResultsColForbiddenCharacterError', 'format', formatstring)
            raise Exception(errmsg)

        # check keystring here
        # if empty, pass
        if not k:
            pass
        # if not empty
        else:
            # check forbidden characters
            if any(char in k for char in '%&'):
                errmsg = self.generateCommandErrorMessage('KeyFieldForbiddenCharacterError', 'k', k)
                raise Exception(errmsg)

            k_list = k.split(',')
            if len(k_list) > len(set(k_list)):
                # check conflict
                errmsg = self.generateCommandErrorMessage('KeyFieldConflictError', 'k', k)
                raise Exception(errmsg)
            if '' in k_list:
                # check empty
                errmsg = self.generateCommandErrorMessage('EmptyKeyFieldError', 'k', k)
                raise Exception(errmsg)
            for _keycol in k_list:
                # if not wildcard expression
                if not any(char in _keycol for char in '*?[]'):
                    if _keycol not in self.header:
                        errmsg = self.generateCommandErrorMessage('FieldNotFoundError', 'k', _keycol)
                        raise Exception(errmsg)
                

        xs = []

        calclist = []
        all_fs = []
        final_fs = []
        
        allargs = (_args.get('clist') + 
                   _args.get('fclist') +
                   _args.get('nfclist') +
                   _args.get('xfclist') + 
                   _args.get('xfcnlist'))

        # parse inputs into list-of-dictionaries form
        for arglist in allargs:
            if arglist.get('fld'):
                rows_fld = arglist.get('fld')
                if ',' in rows_fld:
                    errmsg = self.generateCommandErrorMessage('MultipleRowsTargetError', 'fld', rows_fld)
                    raise Exception(errmsg)
                
            if arglist.get('c'):
                # sys.__stderr__.write(repr(arglist))

                x = arglist.get('x')
                s = arglist.get('s')

                if x == '':
                    errmsg = self.generateCommandErrorMessage('EmptyTimecolFieldError', 'x', x)
                    raise Exception(errmsg)
                
                if x or s: 
                    # test for forbidden characters in time setting
                    if any(char in x for char in '*?[],:\&％'):
                        errmsg = self.generateCommandErrorMessage('TimecolForbiddenCharacterError', 'x', x)
                        raise Exception(errmsg)
                    x_list = x.split(',')
                    
                    for _xcol in x_list:
                        if _xcol == '':
                            errmsg = self.generateCommandErrorMessage('EmptyTimecolFieldError', 'x', x)
                            raise Exception(errmsg)
                        if _xcol not in self.header:
                            errmsg = self.generateCommandErrorMessage('FieldNotFoundError', 'x', _xcol)
                            raise Exception(errmsg)
                    
                    arglist['dateformat'] = _args['dateformat']

                    if x and x not in xs:
                        xs.append(x)
                    if s: 
                        scols = s.split(',')
                        for col in scols:
                            if col.split('%')[0] not in xs:
                                xs.append(col)

                fs = arglist.get('f')
                if fs:
                    fs_list = fs.split(',')
                    if ('%' in fs) or ('&' in fs): 
                        errmsg = self.generateCommandErrorMessage('TargetFieldForbiddenCharacterError', 'f', fs)
                        raise Exception(errmsg)

                    if len(fs_list) > len(set(fs_list)):
                        errmsg = self.generateCommandErrorMessage('TargetFieldConflictError', 'f', fs)
                        raise Exception(errmsg)

                    for _fcol in fs_list:
                        if _fcol == '':
                            errmsg = self.generateCommandErrorMessage('EmptyTargetFieldError', 'f', fs)
                            raise Exception(errmsg)
                        # if not wildcard expression
                        if not any(char in _fcol for char in '*?[]'):
                            if _fcol not in self.header:
                                errmsg = self.generateCommandErrorMessage('FieldNotFoundError', 'f', _fcol)
                                raise Exception(errmsg)
                        
                    # expand wildcard
                    fs = self.expandWildCards(fs)
                    
                    if type(fs) == str:
                        errmsg = self.generateCommandErrorMessage('FieldNotFoundError', 'f', arglist['f'])
                        raise Exception(errmsg)
                    
                    all_fs += [f for f in fs if f not in all_fs]
                    arglist['f'] = ','.join(fs)

                cs = arglist.pop('c').split(',')
                
                if '' in cs:
                    errmsg = self.generateCommandErrorMessage('EmptyCalcError', 'c', ','.join(cs))
                    raise Exception(errmsg)
                
                if len(cs) > len(set(cs)):
                    errmsg = self.generateCommandErrorMessage('CalcConflictError', 'c', ','.join(cs))
                    raise Exception(errmsg)
                
                cs_msummary = []
                cs_custom_nysol = []
                cs_grouped = []

                for i,c in enumerate(cs):
                    if ':' in c:
                        cleft, cright = c.split(':')

                        if cright == '':
                            errmsg = self.generateCommandErrorMessage('EmptyCalcNewNameError', 'c', c)
                            raise Exception(errmsg)
                        
                        final_fs.append(cright)
                    elif c:
                        cleft = c
                        final_fs.append(cleft)
                        
                    
                    if cleft in msummaryoptions:
                        cs_msummary.append(cs[i])
                    elif cleft in (x for y in grouped_calcs.values() for x in y):
                        cs_grouped.append(cs[i])
                    elif cleft in nysol_calcs:
                        cs_custom_nysol.append(cs[i])
                    else:
                        errmsg = self.generateCommandErrorMessage('CalcNotFoundError', c, cleft)
                        raise Exception(errmsg)

                    if cleft in msum_dependencies:
                        msum_prereqs.update(msum_dependencies[cleft])

                if 'count' in cs_msummary:
                    # remove count
                    cs_msummary.remove('count')
                    # make separate entry for count
                    calclist.append({'c': 'count', 
                                'optype' : 'msummary',
                                **arglist})

                if cs_msummary:
                    calclist.append({'c': ','.join(cs_msummary), 
                                'optype' : 'msummary',
                                **arglist})

                ns = arglist.get('n')
                if ns:
                    ns = ns.split(',')
                    if len(ns) > len(set(ns)):
                        errmsg = self.generateCommandErrorMessage('ParameterConflictError', 'n', ','.join(ns))
                        raise Exception(errmsg)
                    
                    if len(cs) > 1:
                        errmsg = self.generateCommandErrorMessage('MultipleParamCalcError', 'c', ','.join(cs))
                        raise Exception(errmsg)

                for calc in cs_custom_nysol:
                    if ns:
                        for n in ns:
                            arglist['n'] = n
                            calclist.append({'c': calc, 
                                        'optype' : 'custom',
                                        **arglist})
                    else:
                        calclist.append({'c': calc, 
                                    'optype' : 'custom',
                                    **arglist})
                
                for group in grouped_calcs:
                    arglist['group'] = group
                    _thisgroup = []
                    for calc in cs_grouped:
                        if calc.split(':')[0] in grouped_calcs[group]:
                            _thisgroup.append(calc)

                    if _thisgroup:
                        if group in grouped_calcs:
                            msum_prereqs.update(msum_dependencies[group])

                        if ns:
                            for n in ns:
                                arglist['n'] = n
                                calclist.append({'c': _thisgroup, 
                                            'optype' : 'aggregate',
                                            **arglist})
                        else:
                            calclist.append({'c': _thisgroup, 
                                        'optype' : 'aggregate',
                                        **arglist})

            elif all(value != '' for value in arglist.values()):
                # if c is empty and the rest is not empty
                errmsg = self.generateCommandErrorMessage('EmptyTargetFieldError', 'c', "''")
                raise Exception(errmsg)
            
        # sys.__stderr__.write(repr(calclist))

        # check for conflicting final result column names here
        resultcols = []
        for calcdict in calclist:
            optype = calcdict.get('optype')
            if 'fld' in calcdict.keys():
                if ':' in calcdict['c']:
                    calcname = calcdict['c'].split(':')[1]
                else:
                    calcname = calcdict['c']
                finalname = formatstring.replace('%', calcname).replace('&', calcdict['fld'])
                resultcols.append(finalname)
                
            elif optype == 'msummary':
                for c_opt in calcdict['c'].split(','):
                    for f_opt in calcdict['f'].split(','):
                        # construct list of final colnames
                        if ':' in c_opt:
                            calcname = c_opt.split(':')[1]
                        else:
                            calcname = c_opt
                            
                        finalname = formatstring.replace('%', calcname).replace('&', f_opt)
                        resultcols.append(finalname)

            elif optype == 'custom':
                if ':' in calcdict['c']:
                    calcname = calcdict['c'].split(':')[1]
                else:
                    calcname = calcdict['c']
                    
                if calcdict.get('x'):
                    fldname = calcdict['f'] + '_' + calcdict['x'] 
                else:
                    fldname = calcdict['f']
                    
                # if calc has parameter, append to end
                if calcdict.get('n'):
                    # set string for calcname (& substitution)
                    calcname += f'_{calcdict["n"]}'
                    
                finalname = formatstring.replace('%', calcname).replace('&', fldname)
                resultcols.append(finalname)
                
            elif optype == 'aggregate':
                for c_opt in calcdict['c']:
                    if ':' in c_opt:
                        calcname = c_opt.split(':')[1]
                    else:
                        calcname = c_opt

                    if calcdict.get('x'):
                        fldname = calcdict['f'] + '_' + calcdict['x'] 
                    else:
                        fldname = calcdict['f']

                    # if calc has parameter, append to end
                    if calcdict.get('n'):
                        # set string for calcname (& substitution)
                        calcname += f'_{calcdict["n"]}'
                        
                    finalname = formatstring.replace('%', calcname).replace('&', fldname)
                    resultcols.append(finalname)

        
        # test for duplicates in resultcolumns
        if len(resultcols) > len(set(resultcols)):
            errmsg = self.generateCommandErrorMessage('ResultsColConflictError', 'format, c, f, n')
            raise Exception(errmsg)
        
        # sys.__stderr__.write(repr(resultcols))
                
        

        cmd = [None] * len(calclist)
        cmd_o = None
        keys = None


        cmd_i = inputs['i'].content

        # take the wanted columns only (the key columns and the value columns)
        # generate string of columns to cut

        colstocut = xs + [f for f in all_fs if f not in xs]

        if k:
            # expand key list
            k_list = self.expandWildCards(k)
            if type(k_list) == str:
                errmsg = self.generateCommandErrorMessage('FieldNotFoundError', 'k', k)
                raise Exception(errmsg)
                
            k = ','.join(k_list)
        else:
            k = '__key__'
            cmd_i <<= nm.mcal(a = k, c = '"all"')

        # check if there is conflict in key column and data column settings
        if any(_keycol in colstocut for _keycol in k.split(',')):
            errmsg = self.generateCommandErrorMessage('KeyTargetConflictError', 'k', k)
            raise Exception(errmsg)
            
        # replace null key values with uuid
        tmp_key = '!!' + str(uuid.uuid4())
        cmd_i <<= nm.mnullto(f = k, v = tmp_key)
        
        keys <<= nm.mcut(f = k, i = cmd_i)
        keys <<= nm.muniq(k = k)

        expanded_k = ','.join([k,'fld'])

        self.all_msums = None

        if msum_prereqs:
            premsums = [f'{f}:__{f}' for f in msum_prereqs]
            # sys.__stderr__.write(repr(premsums)+'\n\n')
            self.all_msums = self.remove_nonnumber(cmd_i, all_fs)
            self.all_msums <<= nm.msummary(k = k, f = all_fs, 
                                c = premsums, precision = prec)

        cmd_i <<= nm.mcut(f = f'{k}{","+",".join(colstocut) if len(colstocut) > 0 else ""}')

        ##### calculation portion:
        for i, calcdict in enumerate(calclist):

            cs = calcdict.get('c')
            n = calcdict.get('n')
            optype = calcdict.pop('optype')

            calcdict['precision'] = prec
            calcdict['k'] = k

            # take the required stats for the required columns
            if optype == 'msummary':
                if cs is not 'count':
                    cmd[i] = self.remove_nonnumber(cmd_i, calcdict['f'])
                    cmd[i] <<= nm.msummary(**calcdict)
                else:
                    cmd[i] <<= nm.msummary(i = cmd_i, **calcdict)

                final_cs = [c.split(':')[-1] for c in cs.split(',')]

            elif optype == 'custom':
                if ':' in cs:
                    cs, calcdict['a'] = cs.split(':')
                else:
                    calcdict['a'] = cs

                cmd[i] <<= nm.mread(i=cmd_i)
                
                # sanitize if needed
                if cs not in supports_str:
                    cmd[i] = self.remove_nonnumber(cmd[i], calcdict['f'])

                if cs in python_calcs:
                    # sys.__stderr__.write(repr(calcdict)+'\n')
                    if calcdict.get('x'):
                        cmd[i] = self.fixtimecolumn(cmd[i], calcdict.get('x'), calcdict.get('dateformat'))
                    cmd[i] <<= nm.runfunc(nysol_calcs[cs], **calcdict)
                else:
                    cmd[i] = nysol_calcs[cs](cmd[i], **calcdict)

                if cs == 'autocorr_agg':
                    final_cs = [f'{calcdict["a"]}_{suff}' for suff in ['mean','median','var']]
                elif cs == 'fft_agg':
                    final_cs = [f'{calcdict["a"]}_{suff}' for suff in ['centroid','var','skew','kurtosis']]
                elif n:
                    final_cs = [f'{calcdict["a"]}_{calcdict["n"]}']
                # elif cs == 'slope_pearson':
                #     final_cs = [f'{calcdict["a"]}({calcdict["x"]})']
                else:
                    final_cs = [calcdict['a']]
            
            elif optype == 'aggregate':
                _grp = calcdict.pop('group')
                calcdict['a'] = {out : out for out in grouped_calcs[_grp]}
                calcdict['flags'] = []

                for c in cs:
                    if ':' in c:
                        cleft, cright = c.split(':')
                        calcdict['a'][cleft] = cright
                    else:
                        cleft = c
                        calcdict['a'][cleft] = cleft
                    calcdict['flags'].append(cleft)
                # sys.__stderr__.write(repr(calcdict))

                cmd[i] <<= nm.mread(i=cmd_i)
                
                # sanitize if needed
                if cs not in supports_str:
                    cmd[i] = self.remove_nonnumber(cmd[i], calcdict['f'])

                # run thing
                cmd[i] = nysol_calcs[_grp](cmd[i], **calcdict)                
                
                # prep final_fs
                final_cs = [calcdict['a'][col] for col in calcdict['flags']]
                    

            cmd[i] <<= nm.m2cross(k = expanded_k, f= final_cs, 
                    a = '__type__,__val__')
            
            if calcdict.get('x'):
                #add timecol to fld
                x = calcdict['x']
                cmd[i] <<= nm.mcal(a = 'fldname', c = f'$s{{fld}}+"_{x}"')
                cmd[i] <<= nm.mcut(f = 'fld', r = True)
                cmd[i] <<= nm.mfldname(f = 'fldname:fld')
                

        
        # cmd_o <<= nm.m2cat(i = cmd)
        # sys.__stderr__.write(repr(cmd)+'\n\n')
        # cmd_o <<= nm.mdelnull(i = cmd, f = '__val__')

        colformat = ['']

        for char in formatstring:
            if char == '&':
                colformat.append('$s{fld}')
                colformat.append('')
            elif char == '%':
                colformat.append('$s{__type__}')
                colformat.append('')
            else:
                colformat[-1] += char

        for i, sub in enumerate(colformat):
            if not sub.startswith('$'):
                colformat[i] = f'"{sub}"' 

        cmd_o <<= nm.mcal(i = cmd, a = 'unique_cols', c = '+'.join(colformat))
        cmd_o <<= nm.mcross(f = '__val__', s = 'unique_cols', k = k)
        cmd_o <<= nm.mcut(r = True, f = 'fld', nfno = _args.get('nfno'))
        
        # return tmp_key to null
        cmd_final = None
        cmd_final <<= nm.mnjoin(i = keys, k = k, m = cmd_o, N = True)
        cmd_final <<= nm.mchgstr(f = k, c = f'{tmp_key}:', F = True)

        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_final)
        return {'o': nysol_module_o}


class MultiMcalCommand(PCommand):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):

        # inputs = {'i' : 'input'}
        # args={
        #         'arglist': [
        #          {'a': 'col1', 'c': 'cal1'},
        #          {'a': 'col2', 'c': 'cal2'},
        #           ...
        #         ]
        #       }
        _args = copy.deepcopy(args)
        cmd_o = None
        first = True

        aclist = _args.pop('arglist')
        for acarg in aclist:
            # one mcal will be added to cmd_o for every pair of c and a arguments passed in a list

            if first:
                cmd_o <<= nm.mcal(i=inputs['i'].content, **acarg, **_args) # {'i' : input, 'c': 'cal1', 'a' : 'col1'}
                first = False
            else:
                cmd_o <<= nm.mcal({**acarg,**_args})


        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}


class MultiMcalWCCommand(PCommand):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def parse(self, exp):
        if '-' in exp:
            lims = [self.parse(num) for num in exp.split('-')]
            if lims[0] < lims[1]:
                return range(lims[0], lims[1]+1) 
            else: 
                return range(lims[0], lims[1] - 1, -1)
        elif 'L' in exp:
            return len(self.header) - int(exp.strip('L')) - 1
        else:
            return int(exp)
            
    def run(self, args, inputs):
        # args format:
        #     target columns: expressions can use wildcards, and can be separated with commas
        #     c: operation to be done on each column, operations to be done per target columns should use the token &, which represents the old column name 
        #     a: output column name (string must include &, default is 'new&')

        import fnmatch as fn
        _args = copy.deepcopy(args)
        cmd_o = None
        first = True

        # ヘッダ行を取得する
        self.header = self.get_field_names(inputs['i'])

        xoption = _args.pop('x') if 'x' in _args else False
        
        targs = _args.pop('targets').split(',')
        if xoption:
            # parse number expression

            targets = []
            for f in targs:
                f = self.parse(f)
                targets += list(f) if type(f) is range else [f]

            colnames = [self.header[num] for num in targets]
        else:   
            # parse wildcard expression  
            colnames = [a for a in self.header for target in targs 
                if fn.fnmatch(a, target)]


        # redundancy check
        targets_final = [a for a in colnames 
            if _args['a'].replace('&',a) not in self.header]
        #targets is now a list of column names to hit with calculation

        #iterate over entire list and replace the '&' in c and a inputs with column number/name
        for target in targets_final:
            arg = _args.copy()
            # sys.__stderr__.write(repr(arg)+'\n')

            arg['a'] = arg['a'].replace('&', target)
            arg['c'] = arg['c'].replace('&',str(target))

            if first:
                cmd_o <<= nm.mcal(i = inputs['i'].content, **arg)
                first = False
            else:
                cmd_o <<= nm.mcal(arg)
        
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}
        

class MvAvgCommand(PCommand):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def parse(self, exp):
        if '-' in exp:
            lims = [self.parse(num) for num in exp.split('-')]
            if lims[0] < lims[1]:
                return range(lims[0], lims[1]+1) 
            else: 
                return range(lims[0], lims[1] - 1, -1)
        elif 'L' in exp:
            return len(self.header) - int(exp.strip('L')) - 1
        else:
            return int(exp)

    def run(self, args, inputs):
        import fnmatch as fn

        _args = copy.deepcopy(args)
        
        cmd_o = None
        cmd_o <<= inputs['i'].content

        if (not _args.get('s')) or (_args['s'] == ''):
            _args['q'] = True

        xoption = _args.get('x')
        
        # ヘッダ行を取得する
        self.header = self.get_field_names(inputs['i'])

        fatlist = []

        for fatargs in _args.pop('fatlist'):
            fs = fatargs.pop('f').split(',')
            aexp = fatargs.pop('a')
            ts = fatargs.pop('t').split(',')
            if xoption:
                # parsing number expressions
                targets = []
                for f in fs:
                    f = self.parse(f)
                    targets += list(f) if type(f) is range else [f]

                colnames = [self.header[num] for num in targets]

            else:
                # parse wildcard/list expressions here

                colnames = [a for a in self.header for f in fs 
                    if fn.fnmatch(a, f)]
                
            for colname in colnames:
                for interval in ts:
                    fatlist.append({'f': colname, 
                        'a': aexp.replace('&', colname).replace('#', interval), 
                        't': interval})

        mvavgtype = _args.pop('type')
        if mvavgtype != 'simple':
            _args[mvavgtype] = True
        if mvavgtype != 'exp' and 'alpha' in _args:
            del _args['alpha']

        # copy target  column into 'a' field
        for fatdict in fatlist:
            cmd_o <<= nm.mcal(a = fatdict['a'], c = f'${{{fatdict["f"]}}}') 
            
            fatdict['f'] = fatdict.pop('a')

            # arg['t'] = fatdict['t']

            # perform mmvavg on field specified by 'a' field, with skip = 0
            cmd_o <<= nm.mmvavg({'skip': 0, **_args, **fatdict})

        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}


class MvStatsCommand(PCommand):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def parse(self, exp):
        if '-' in exp:
            lims = [self.parse(num) for num in exp.split('-')]
            if lims[0] < lims[1]:
                return range(lims[0], lims[1]+1) 
            else: 
                return range(lims[0], lims[1] - 1, -1)
        elif 'L' in exp:
            return len(self.header) - int(exp.strip('L')) - 1
        else:
            return int(exp)


    def run(self, args, inputs):
        import fnmatch as fn

        _args = copy.deepcopy(args)
        cmd_o = None

        cmd_o <<= inputs['i'].content
            
        # sorting parameters
        if 's' not in _args or (_args['s'] == ''):
            _args['q'] = True

        # ヘッダ行を取得する
        self.header = self.get_field_names(inputs['i'])

        xoption = _args.pop('x') if 'x' in _args else False

        # f is a wildcard/number expression
        # a is a colname that may have & in it
        # c specifies the statistic to be taken (list not allowed)
        factlist = []
        for arglist in _args.pop('factlist'):
            fs = arglist.pop('f').split(',')
            aexp = arglist.pop('a')
            ops = arglist.pop('c').split(',')
            ts = arglist.pop('t').split(',')

            if xoption:
                # parse number expression
                targets = []
                for f in fs:
                    f = self.parse(f)
                    targets += list(f) if type(f) is range else [f]

                colnames = [self.header[num] for num in targets]

            else:
                # parse wildcard, list expression
                colnames = [a for a in self.header for f in fs 
                    if fn.fnmatch(a, f)]
                
            for colname in colnames:
                for op in ops:
                    for t in ts:
                        factlist.append({'f': colname, 
                            'a': aexp.replace('&', colname).replace('%', op).replace('#',t), 
                            'c': op,
                            't': t})


        # faclist is now a list of dictionaries of fac options:
        # [{'f': 'f1', 'a': 'a1', 'c': 'c1'},
        #  {'f': 'f2', 'a': 'a2', 'c': 'c2'},
        #  ...]
        for factdict in factlist:
            # arg = args.copy()

            cmd_o <<= nm.mcal(a = factdict['a'], c = f'${{{factdict["f"]}}}')
            
            factdict['f'] = factdict.pop('a')

            # perform mmvstats on field specified by 'a' field, with skip = 0
            cmd_o <<= nm.mmvstats({'skip': 0, **_args, **factdict})

        # pass output
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}


class MvSimCommand(PCommand):
    
    commandname = '複数の移動窓の類似度の計算'
    errormessages = {
        
        # キー列に対するエラー
        'KeyConflictError' : '項目名が重複しています。${fieldinput}',
        'KeyNumberConflictError' : '項目番号が重複しています。${fieldinput}',
        'KeyNumberSettingError' : 'キー項目番号の指定は正しくありません。${fieldinput}',
        'KeyFieldNotFoundError' : '指定した項目名は存在しません。${fieldinput}',
        'KeyFieldNumberNotFoundError' : '指定した項目番号は存在しません。${fieldinput}',
        'EmptyKeyFieldError' : '空文字列でキー項目名が指定されています。${fieldinput}',
        'KeyFieldForbiddenCharacterError' : '半角の（ :　\　&　％　＃ ）は、キー項目の指定に使用できません。${fieldinput}',
        
        # ソート設定に対するエラー
        'SortFieldConflictError' : '項目名が重複しています。${fieldinput}',
        'SortFieldNumberConflictError' : '項目番号が重複しています。${fieldinput}',
        'SortFieldNumberSettingError' : 'ソート項目番号の指定は正しくありません。${fieldinput}',
        'SortFieldNotFoundError' : '指定した項目名は存在しません。${fieldinput}',
        'SortFieldNumberNotFoundError' : '指定した項目番号は存在しません。${fieldinput}',
        'SortFieldForbiddenCharacterError': '半角の（ :　\　&　＃ ）は、ソートの項目名の指定に使用できません。${fieldinput}',
        'EmptySortFieldError' : '空文字列でソートが指定されています。${fieldinput}',
        'SortFieldOrderError' : 'ソート順の指定は正しくありません。指定可能なのは、（%n、%r、%nr）です。${fieldinput}',
        
        # 結果列名設定に対するエラー
        'EmptyResultsColNameError' : '空文字列で結果項目名が指定されてます。${fieldinput}',
        'ResultsColNameForbiddenCharacterError': '半角の（ :　\　,　*　?　[　] ）は、結果項目名の指定に使用できません。${fieldinput}',
        
        # 計算対象列に対するエラー
        'Target1FieldNotFoundError' : '指定した項目名は存在しません。${fieldinput}',
        'Target1FieldNumberNotFoundError' : '指定した項目番号は存在しません。${fieldinput}',
        'Target1MultipleFieldError' : '１つ目の計算対象項目指定で、複数の項目名を指定できません。${fieldinput}',
        'Target1MultipleFieldNumberError' : '１つ目の計算対象項目指定で、複数の項目番号を指定できません。${fieldinput}',
        'Target1ForbiddenCharacterError' : '半角の（ :　\　&　％　＃ ）は、計算対象項目の指定に使用できません。${fieldinput}',
        'Target1FieldNumberSettingError' : '計算対象項目番号の指定は正しくありません。${fieldinput}',
        'Target1EmptyError' : '空文字列で計算対象項目が指定されています。${fieldinput}',
        
        'Target2ConflictError' : '項目名が重複しています。${fieldinput}',
        'Target2FieldNotFoundError' : '指定した項目名は存在しません。${fieldinput}',
        'Target2FieldNumberNotFoundError' : '指定した項目番号は存在しません。${fieldinput}',
        'Target2FieldNumberSettingError' : '計算対象項目番号の指定は正しくありません。${fieldinput}',
        'Target2ForbiddenCharacterError' : '半角の（ :　\　&　％　＃ ）は、計算対象項目の指定に使用できません。${fieldinput}',
        'Target2EmptyError' : '空文字列で計算対象項目が指定されています。${fieldinput}',
        
        # 類似度指定に対するエラー
        'SimConflictError': '類似度が重複しています。${fieldinput}',
        'SimNotFoundError' : '${fieldinput} は、有効な類似度指定子ではありません。',
        'SimEmptyError' : '空文字列で類似度が指定されています。${fieldinput}',
        
        # 期間数指定に対するエラー
        'WindowSizeConflictError' : '対象行数が重複しています。${fieldinput}',
        'WindowSizeFormatError' : '対象行数への ${fieldinput} 指定が正しくありません。２以上の整数を指定してください',
        'WindowSizeValueError' : '対象行数への ${fieldinput} 指定が正しくありません。２以上の整数で指定してください',
        'WindowSizeEmptyError' : '空文字列で対象行数が指定されています。${fieldinput}',

        # 結果列重複エラー
        'ResultsColConflictError' : '出力項目名が重複しています。%指定、&指定、#指定、ワイルドカード指定など、重複する出力項目名となる設定がないかを、確認してください。${fieldinput}',
        
        
        'TestError' : 'This is a test'
    }
    
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]
        

    def parse(self, exp):
        if '-' in exp:
            lims = [self.parse(num) for num in exp.split('-')]
            if lims[0] < lims[1]:
                return range(lims[0], lims[1]+1) 
            else: 
                return range(lims[0], lims[1] - 1, -1)
        elif 'L' in exp:
            return len(self.header) - int(exp.strip('L')) - 1
        else:
            return int(exp)

    def numberExpIsValid(self, exp):
        allowed = set('0123456789-L')
        return set(exp) <= allowed
    
    def numberExpOutOfRange(self, exp):
        keynums = exp.strip('L').split('-')
        for num in keynums:
            if int(num) > len(self.header):
                return True
        
        return False

    def containsAny(self, exp, str):
        return any(char in exp for char in str)

    def generateCommandErrorMessage(self, *args):
        # とりあえず、エラー処理機能は特徴量の計算のコマンドの実装を参照する
        # TODO：　親コマンドレベルに機能の実装を移動する
        errhandler = GroupBy2Command()
        errhandler.commandname = self.commandname
        errhandler.errormessages = self.errormessages

        return errhandler.generateCommandErrorMessage(*args)

    def run(self, args, inputs):
        import fnmatch as fn
        _args = copy.deepcopy(args)

        
        cmd_o = None
        cmd_o <<= inputs['i'].content

        # ヘッダ行を取得する
        self.header = self.get_field_names(inputs['i'])

        xoption = _args.get('x')

        # 共通オプションの処理・エラー処理
        # 集計キー指定
        
        # if key setting is not empty
        k = _args.get('k')
        if k:
            k_list = k.split(',')
            
            if xoption:
                for key in k_list:
                    if not self.numberExpIsValid(key):
                        errmsg = self.generateCommandErrorMessage('KeyNumberSettingError', 'k', key)
                        raise Exception(errmsg)
                    
                    if key == '':
                        errmsg = self.generateCommandErrorMessage('EmptyKeyFieldError', 'k', key)
                        raise Exception(errmsg)

                    if self.numberExpOutOfRange(key):
                        errmsg = self.generateCommandErrorMessage('KeyFieldNumberNotFoundError', 'k', key)
                        raise Exception(errmsg)
                    
                if len(k_list) != len(set(k_list)):
                    errmsg = self.generateCommandErrorMessage('KeyNumberConflictError', 'k', k)
                    raise Exception(errmsg)
                
            else:
                if len(k_list) != len(set(k_list)):
                    errmsg = self.generateCommandErrorMessage('KeyConflictError', 'k', k)
                    raise Exception(errmsg)
                
                for key in k_list:
                    # forbidden characters
                    if self.containsAny(key, ':\\%&#'):
                        errmsg = self.generateCommandErrorMessage('KeyFieldForbiddenCharacterError', 'k', key)
                        raise Exception(errmsg)
                    
                    if key == '':
                        errmsg = self.generateCommandErrorMessage('EmptyKeyFieldError', 'k', key)
                        raise Exception(errmsg)
                        
                    if key not in self.header:
                        errmsg = self.generateCommandErrorMessage('KeyFieldNotFoundError', 'k', key)
                        raise Exception(errmsg)
        
        
        # ソートする列指定
        # if no sort column setting, set q flag (no sort) to true 
        if 's' not in _args or (_args['s'] == ''):
            _args['q'] = True
        else:
            s_opt = _args['s']
            
            s_list = []
            s_columns = []
            
            # separate column and sort order input
            for elem in s_opt.split(','):
                parts = elem.split('%')
                
                s_columns.append(parts[0])
                
                if parts[0] == '':
                    errmsg = self.generateCommandErrorMessage('EmptySortFieldError', 's', s_opt)
                    raise Exception(errmsg)

                if xoption:
                    if not self.numberExpIsValid(parts[0]):
                        errmsg = self.generateCommandErrorMessage('SortFieldNumberSettingError', 's', s_opt)
                        raise Exception(errmsg)
                    
                    if self.numberExpOutOfRange(parts[0]):
                        errmsg = self.generateCommandErrorMessage('SortFieldNumberNotFoundError', 's', s_opt)
                        raise Exception(errmsg)
                else:
                    if self.containsAny(parts[0], ':\\&#'):
                        errmsg = self.generateCommandErrorMessage('SortFieldForbiddenCharacterError', 's', s_opt)
                        raise Exception(errmsg)
                        
                    if parts[0] not in self.header:
                        errmsg = self.generateCommandErrorMessage('SortFieldNotFoundError', 's', s_opt)
                        raise Exception(errmsg)
                
                if len(parts) > 1:
                    if parts[1] not in ['', 'n', 'r', 'nr']:
                        errmsg = self.generateCommandErrorMessage('SortFieldOrderError', 's', s_opt)
                        raise Exception(errmsg)
                    
                

                if len(parts) == 2:
                    # there is both column and sort order
                    s_list.append(parts)
                elif len(parts) == 1:
                    # there is only column
                    s_list.append(parts + [''])
                else:
                    pass # format error
            
            # check for duplicates
            if len(s_columns) != len(set(s_columns)):
                if xoption:
                    errmsg = self.generateCommandErrorMessage('SortFieldConflictError', 's', s_opt)
                else:
                    errmsg = self.generateCommandErrorMessage('SortFieldNumberConflictError', 's', s_opt)
                raise Exception(errmsg)
                

            # s_list is now a list of lists containing the column and sort order
            # user inputs:
            # s_list = [['col1', 'n'], ['col2', ''], ...]
            
            _args['s'] = ['%'.join(elem) for elem in s_list]
            # _args['s'] = ['col1%n', 'col2', ...]
            

        # f is a wildcard/number expression
        # a is a colname that may have & in it
        # c specifies the statistic to be taken 
        factlist = []
        final_cols = []
        
        # errmsg = self.generateCommandErrorMessage('TestError', 'x')
        # raise Exception(errmsg)
        
        try:
            output_rule = _args.pop('a')
            
            if self.containsAny(output_rule, ':\\,*?[]'):
                errmsg = self.generateCommandErrorMessage('ResultsColNameForbiddenCharacterError', 'a', output_rule)
                raise Exception(errmsg)
                
        except KeyError:
            errmsg = self.generateCommandErrorMessage('EmptyResultsColNameError', 'a')
            raise Exception(errmsg)
        
        
        for arglist in _args.pop('fctlist'):
            f1 = arglist.get('f1')
            
            if not f1:
                errmsg = self.generateCommandErrorMessage('Target1EmptyError', 'f1', f1)
                raise Exception(errmsg)
                
            if xoption:
                if 'L' in f1:
                    f1_loc = len(self.header) - int(f1.strip('L')) - 1
                elif self.containsAny(f1, '-,'):
                    errmsg = self.generateCommandErrorMessage('Target1MultipleFieldNumberError', 'f1', f1)
                    raise Exception(errmsg)
                else:
                    if self.numberExpIsValid(f1):
                        f1_loc = int(f1)
                    else:
                        errmsg = self.generateCommandErrorMessage('Target1FieldNumberSettingError', 'f1', f1)
                        raise Exception(errmsg)
                    
                try:
                    f1_name = self.header[f1_loc]
                except IndexError:
                    errmsg = self.generateCommandErrorMessage('Target1FieldNumberNotFoundError', 'f1', f1)
                    raise Exception(errmsg)                
            else: 
                if self.containsAny(f1, ',?*[]'):
                    errmsg = self.generateCommandErrorMessage('Target1MultipleFieldError', 'f1', f1)
                    raise Exception(errmsg)
                    
                if self.containsAny(f1, ':\\&%#'):
                    errmsg = self.generateCommandErrorMessage('Target1ForbiddenCharacterError', 'f1', f1)
                    raise Exception(errmsg)
                
                if f1 not in self.header:
                    errmsg = self.generateCommandErrorMessage('Target1FieldNotFoundError', 'f1', f1)
                    raise Exception(errmsg)
                
                
                f1_name = f1
            
            f2s = arglist.get('f2')
            f2_list = f2s.split(',')
            
            if '' in f2_list:
                errmsg = self.generateCommandErrorMessage('Target2EmptyError', 'f2', f2s)
                raise Exception(errmsg)
            
            if self.containsAny(f2s, ':\\&%#'):
                errmsg = self.generateCommandErrorMessage('Target2ForbiddenCharacterError', 'f2', f2s)
                raise Exception(errmsg)
            
            if len(f2_list) != len(set(f2_list)):
                errmsg = self.generateCommandErrorMessage('Target2ConflictError', 'f2', f2s)
                raise Exception(errmsg)
            
            if xoption:
                # parse number expression
                targets = []
                for f in f2_list:
                    if not self.numberExpIsValid(f):
                        errmsg = self.generateCommandErrorMessage('Target2FieldNumberSettingError', 'f2', f)
                        raise Exception(errmsg)
                        
                    f = self.parse(f)
                    targets += list(f) if type(f) is range else [f]

                try:
                    f2cols = [(num,self.header[num]) for num in targets]
                except IndexError:
                    errmsg = self.generateCommandErrorMessage('Target2FieldNumberNotFoundError', 'f2', f2s)
                    raise Exception(errmsg)

            else:
                f2cols = []
                
                for elem in f2_list:
                    matched = False
                    for col in self.header:
                        if fn.fnmatch(col, elem):
                            f2cols.append((col, col))
                            matched = True
                            
                    if not matched:
                        errmsg = self.generateCommandErrorMessage('Target2FieldNotFoundError', 'f2', elem)
                        raise Exception(errmsg)
                
                
            ops = arglist.get('c')
            op_list = ops.split(',')
            
            allowed_ops = ['covar', 'ucovar', 'pearson', 'spearman', 'kendall', 
                           'euclid', 'cosine', 'cityblock', 'hamming', 'chi', 
                           'phi', 'jaccard', 'support', 'lift']
            
            if '' in op_list:
                errmsg = self.generateCommandErrorMessage('SimEmptyError', 'c', ops)
                raise Exception(errmsg)
                
            for op in op_list:
                if op not in allowed_ops:
                    errmsg = self.generateCommandErrorMessage('SimNotFoundError', 'c', op)
                    raise Exception(errmsg)
            
            if len(op_list) != len(set(op_list)):
                errmsg = self.generateCommandErrorMessage('SimConflictError', 'c', ops)
                raise Exception(errmsg)
            
                
            
            ts = arglist.pop('t')
            ts_list = ts.split(',')
            
            if '' in ts_list:
                errmsg = self.generateCommandErrorMessage('WindowSizeEmptyError', 't', ts)
                raise Exception(errmsg)
            
            if len(ts_list) != len(set(ts_list)):
                errmsg = self.generateCommandErrorMessage('WindowSizeConflictError', 't', ts)
                raise Exception(errmsg)
            
            for t in ts_list:
                
                try:
                    _t = float(t)
                    
                    if (not _t.is_integer()) or (_t < 2):
                        errmsg = self.generateCommandErrorMessage('WindowSizeValueError', 't', t)
                        raise Exception(errmsg)
                    
                except ValueError:
                    errmsg = self.generateCommandErrorMessage('WindowSizeFormatError', 't', t)
                    raise Exception(errmsg)
                
                
            for op in op_list:
                for t in ts_list:
                    for f2col in f2cols:
                        final_colname = output_rule.replace('&', f'{f1_name}_{f2col[1]}').replace('#',t).replace('%',op)
                        final_cols.append(final_colname)
                        
                        factlist.append({'f': f'{f1},{f2col[0]}', 
                            'a': final_colname, 
                            'c': op,
                            't': t})


        if len(final_cols) != len(set(final_cols)):
            errmsg = self.generateCommandErrorMessage('ResultsColConflictError', 'a, c, f1, f2, t')
            raise Exception(errmsg)

        # factlist is now a list of dictionaries of the fact options:
        # [{'f': 'f1,f2', 'a': 'a1', 'c': 'c1', 't':, 't1'},
        #  {'f': 'f3,f4', 'a': 'a2', 'c': 'c2', 't':, 't2'},
        #  ...]
        for factdict in factlist:
            # arg = args.copy()

            # perform mmvsim on field specified by 'a' field, with skip = 0
            cmd_o <<= nm.mmvsim({'skip': 0, **_args, **factdict})

        # pass output
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}


class PlainText2Csv(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]  

    def run(self, args, inputs):
        def filter(args):
            try:
                from kskp.depo.std.commands.pcmd.src import plaintext2csv 
                plaintext2csv.main(args, sys.stdin, sys.stdout)
                # flushをする
                sys.stdout.flush()
            except Exception as e:
                import traceback
                with open('/dev/stderr', 'w') as fpe:
                    traceback.print_exc(file=fpe)

        # flushをしないと、デバッグ用のprintなども入ってしまう
        sys.stdout.flush()

        cmd = inputs['i'].content
        cmd <<= nm.runfunc(filter, args=args)

        # pass output
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd)
        return {'o': nysol_module_o}


class SelRowCommand(RunfuncCommand):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'mcmd'), Port('u', 'mcmd')]

    def run(self, args, inputs):
        from .src import mod

        import uuid
        import os
        import errno

        FIFO = str(uuid.uuid4())
        try:
            os.mkfifo(FIFO)
        except OSError as oe:
            if oe.errno != errno.EEXIST:
                raise

        f = inputs['i'].content
        f2 = None

        f <<= nm.runfunc(mod, FIFO, args)
        # runfuncの後にm2teeをしないと、f（ここでのport名はo)を使わなかった時にコンソール上に表示されてしまう
        f <<= nm.m2tee()
        f2 <<= nm.m2tee(i=FIFO)

        nysol_module_o= NysolModule()
        nysol_module_o.set_content(f)
        nysol_module_u= NysolModule()
        nysol_module_u.set_content(f2)

        return {'o': nysol_module_o, 'u': nysol_module_u}

class RowRangeCommand(Command):
    """
    指定範囲の行を抽出する
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        def filter(fr, size):
            try:
                # ヘッダ行を出力する
                header = sys.stdin.readline()
                print(header, end='')

                # 取得開始行まで読み飛ばす
                for i in range(fr):
                    line = sys.stdin.readline()

                # 指定範囲の行を標準出力へ出力する
                for j in range(size):
                    line = sys.stdin.readline()
                    print(line, end='')

                # flushをする
                sys.stdout.flush()
            except Exception as e:
                with open('/dev/stderr', 'w') as fpe:
                    import traceback
                    traceback.print_exc(file=fpe)
                    print(f'#ERROR# {str(e)}; RowRangeCommand; ; ; ', file=fpe)
                raise

        # 指定範囲の取得
        offset = int(args.get('offset')) if args.get('offset') else 0
        limit = int(args.get('limit')) if args.get('limit') else 0

        cmd = inputs['i'].content
        cmd <<= nm.runfunc(filter, fr=offset, size=limit)
        # cmd <<= nm.mbest(q=True, fr=offset, size=limit)

        # pass output
        return {'o': NysolModule(cmd)} 

class ConvToUtf8(Command):
    """
    入力データをUTF-8に変換する
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):

        def to_utf8(source_encoding):
            """
            ストリームでcp932→utf8に変換するコマンド
            """
            try:
                import io
                # stdinのencodingがデフォルトでutf-8なので、設定し直す。
                input_stream = io.TextIOWrapper(sys.stdin.buffer, encoding=source_encoding)
                # flush()すると連続でプレビューした時にnm.runs()で処理が帰ってくる見たい？
                input_stream.flush()
                for line in input_stream:
                    # 標準出力するときも自動でutf-8に変換されるので、printだけでいい
                    print(line, end='')
                # flushをする
                sys.stdout.flush()
            except Exception as e:
                with open('/dev/stderr', 'w') as fpe:
                    import traceback
                    traceback.print_exc(file=fpe)
            
        # flushをしないと、デバッグ用のprintなども入ってしまう
        sys.stdout.flush()

        nysol_module = inputs['i']

        if nysol_module.encoding is None or nysol_module.encoding == 'UNKNOWN':
            # 入力データの文字コードが未判定の場合
            # 判定してもわからなかった場合はUTF-8で試してみる
            encoding = 'utf-8'
        else:
            encoding = nysol_module.encoding

        cmd = nysol_module.content
        if encoding != 'utf-8' and encoding != 'ascii':
            cmd <<= nm.runfunc(to_utf8, source_encoding=encoding)
    
        return {'o': NysolModule(cmd)}

class ToListCommand(Command):
    """
    入力データをPython Listに出力する
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'list')]

    def run(self, args, inputs):
        cmd = inputs['i'].content
        # 1行目をヘッダ扱いしない(nfn=True)
        # ヘッダ扱いすると、重複列名や空列名があるとエラーになる
        cmd <<= nm.writelist(nfn=True)

        # pass output
        return {'o': NysolModule(cmd)}
