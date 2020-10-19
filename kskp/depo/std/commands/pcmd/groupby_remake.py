import sys
import copy
import uuid
import os
import nysol.mcmd as nm
import numpy as np
import fnmatch as fn 
import nysol.util.mtemp as mtemp

from math import ceil
from kskp.store import NysolModule
from kskp.core import Command, Port, Tmp

from .script import PCommand

class GroupByRemakeCommand(PCommand):
    # クラス変数
    def const(self, s):
        '''
        function containing all command constants
        commandname : string with Japanese command name
        errmsgs     : dictonary containing the error codes and messages
        paraminfo   : dictionary of each param's validity limits/format etc
        msum_calcs  : list of msummary calculations
        nysol_calcs : list of nysol calculations
        python_calcs: list of python calculations
        funcs       : dict of calcnames paired with their functions
        '''
        if s == 'commandname':
            return '特徴量の計算' # 将来、コマンド名はCmdJSONから取得（？）
        elif s == 'errmsgs':
            return { 'FieldNotFoundError' : '指定した項目名は存在しません。${fieldinput}',
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
            'ResultsColConflictError' : '出力項目名が重複しています。%指定、&指定、ワイルドカード指定など、重複する出力項目名となる設定がないかを、確認してください。',
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
            'EmptyParamError' : '空文字列でパラメータが指定されています。${fieldinput}',
            'ParameterConflictError' : 'パラメータが重複しています。${fieldinput}',
            'ParameterTypeError'  : '${calc} のパラメータへの ${fieldinput} 指定が正しくありません。${correct_type} を指定してください',
            'ParameterOutOfBoundsError' : '${calc} のパラメータへの ${fieldinput} 指定が正しくありません。 ${correct_value} で指定してください',
            'ParameterFormatError' : '${calc} のパラメータへの ${fieldinput} 指定が正しくありません。${correct_format} を指定してください',
            'UnknownParameterError' : '${calc} のパラメータへの ${fieldinput} 指定が正しくありません'
            }
        elif s == 'paraminfo':
            return {
            'value_count' : {'correct_type' : '全ての文字列',
                             'correct_value' : '数値か文字列',
                             'checks': []},
            'sym_looking' : {'correct_type' : '数値', 
                             'correct_value' : '正の数値',
                             'checks': [[self.checkParamOOB, {'low' : 0}]]},
            'large_sd' : {'correct_type' : '数値', 
                          'correct_value' : '正の数値',
                          'checks' : [[self.checkParamOOB, {'low' : 0}]]},
            'ratio_beyond_rsigma' : {'correct_type' : '数値', 
                                     'correct_value' : '正の数値',
                                     'checks' : [[self.checkParamOOB, {'low' : 0}]]},
            'binned_entropy' : {'correct_type' : '数値', 
                                'correct_value' : '２以上の整数',
                                'checks' : [[self.checkParamIsInteger, {}],
                                            [self.checkParamOOB,{'low' : 2}]]},
            'quantile' : {'correct_type' : '数値', 
                          'correct_value' : '０−１の数値',
                          'checks' : [[self.checkParamOOB, {'low_inc' : 0,
                                                            'high_inc': 1}]]},
            'range_count' : {'correct_type' : '数値;数値', 
                             'correct_value' : '全ての数値', 
                             'correct_format' : '数値;数値',
                             'checks': [[self.checkParamGTLT, {}]]},
            'autocorr' : {'correct_type' : '数値', 
                          'correct_value' : '１以上の整数',
                          'checks' : [[self.checkParamIsInteger, {}],
                                      [self.checkParamOOB,{'low' : 1}]]},
            'crossing_m' : {'correct_type' : '数値', 
                            'correct_value' : '全ての数値',
                            'checks' : [[self.checkParamIsNumber, {}]]},
            'peaks' : {'correct_type' : '数値', 
                       'correct_value' : '１以上の整数',
                       'checks' : [[self.checkParamOOB, {'low' : 1}],
                                   [self.checkParamIsInteger, {}]]},
            'imq' : {'correct_type' : '数値', 
                     'correct_value' : '０−１の数値',
                     'checks' : [[self.checkParamOOB, {'low_inc' : 0,
                                                       'high_inc': 1}]]},
            }
        elif s == 'supports_str':
            return [
                    'rows',
                    'miss',
                    'strmin',
                    'strmax',
                    'strucount',
                    'has_dup',
                    'value_count'
                    ]
        elif s == 'msum_calcs':
            return [
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
        elif s == 'nysol_calcs':
            return ['rows',
                    'miss',
                    'strmin',
                    'strmax',
                    'strucount',
                    'hmean',
                    'gmean',
                    'mean_ad',
                    'median_ad',
                    'rms',
                    'repeatdata',
                    'repeatvalues',
                    'ratio_unique',
                    'count_above_mean',
                    'count_below_mean',
                    'has_dup',
                    'has_dup_max',
                    'has_dup_min',
                    'sum_repeatdata',
                    'sum_repeatvalues',
                    'abs_energy',
                    'var_gt_sd',
                    'sym_looking',
                    'large_sd',
                    'value_count',
                    'ratio_beyond_rsigma',
                    'binned_entropy',
                    'quantile',
                    'range_count',
                    'slope',
                    'slope_pearson',
                    'slope_pattern',
                    'mean_second_derivative_central',
                    'mean_change',
                    'mean_abs_change',
                    'abs_sum_changes',
                    'integral',
                    'firstmin',
                    'firstmax',
                    'lastmin',
                    'lastmax',
                    'longest_strike_above_mean',
                    'longest_strike_below_mean',
                    'autocorr',
                    'crossing_m',
                    'peaks',
                    'imq']
        elif s == 'python_calcs':
            return [
                'meanf',
                'varf',
                'fft_agg'
            ] 
        elif s == 'runfunc_calcs':
            return {
                'varf' : self.feature_frequencyvar,
                'meanf': self.feature_meanfrequency
            }
        elif s == 'funcs':
            return {
                # 0 fields (input k, a, fld)
                'rows' : self.feature_rows,
                # 1 field (input k, a, f)
                'miss' : self.feature_miss,
                'strucount' : self.feature_strucount,
                'strmax' : self.feature_strmax,
                'strmin' : self.feature_strmin,
                'has_dup' : self.feature_hasdup,
                'repeatdata' : self.feature_repeatdata,
                'repeatvalues' : self.feature_repeatdata,
                'sum_repeatdata' : self.feature_sumrepeatdata,
                'sum_repeatvalues' : self.feature_sumrepeatvalues,
                'ratio_unique' : self.feature_ratiounique,
                'count_above_mean' : self.feature_countabovemean,
                'count_below_mean' : self.feature_countbelowmean,
                'has_dup_max' : self.feature_hasdupmin,
                'has_dup_min' : self.feature_hasdupmax,
                'hmean' : self.feature_hmean,
                'gmean' : self.feature_gmean,
                'abs_energy' : self.feature_absenergy, 
                'rms' : self.feature_rms,
                'median_ad' : self.feature_medianad,
                'mean_ad' : self.feature_meanad,
                'var_gt_sd' : self.feature_vargtsd,
                # 1 field + parameter (k, n, a ,f)
                'value_count' : self.feature_valuecount,
                'sym_looking' : self.feature_symlooking,
                'large_sd' : self.feature_largesd,
                'ratio_beyond_rsigma' : self.feature_ratiogtrsigma,
                'binned_entropy' : self.feature_binnedentropy,
                'quantile' : self.feature_quantile,
                'range_count': self.feature_rangecount,
                # 1 field + time (input k, a, f, x)
                'slope' : self.feature_slope,
                'slope_pearson' : self.feature_pearson,
                'slope_pattern' : self.feature_pattern,
                'mean_second_derivative_central' : self.feature_M2DC,
                'mean_change' : self.feature_meanchange,
                'mean_abs_change' : self.feature_meanabschange,
                'abs_sum_changes' : self.feature_abssumchanges,
                'integral' : self.feature_integral,
                'meanf' : self.feature_runfuncwrapper,
                'varf' : self.feature_runfuncwrapper,
                'firstmin' : self.feature_firstmin,
                'firstmax' : self.feature_firstmax,
                'lastmin' : self.feature_lastmin,
                'lastmax' : self.feature_lastmax,
                'longest_strike_above_mean' : self.feature_longeststrikeabovemean,
                'longest_strike_below_mean' : self.feature_longeststrikebelowmean,
                # 2+1 fields
                'autocorr' : self.feature_autocorrelation,
                'crossing_m' : self.feature_crossingm,
                'peaks' : self.feature_peaks,
                'imq' : self.feature_imq,
                'end' : None
                }
            # return {
            #     defunct
            #     'energy_ratio_by_chunks' : self.energy_ratio_by_chunks,
            # }

    
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]
 
    def wrapFlow(self, flow_obj):
        '''
        wrap a nysol flow object in a NysolModule object
        '''

        nysol_module = NysolModule()
        nysol_module.set_content(flow_obj)

        return nysol_module
        
    def dumpToFile(self, flow_obj, filepath):
        '''
        Takes a nysol flow object (or list of flow objects) and uses m2tee to 
        dump into a file specified by filepath
        '''
        if isinstance(flow_obj, list):
            flow_obj = nm.m2tee(i = flow_obj, o = filepath.as_posix())
        else:
            flow_obj <<= nm.m2tee(o = filepath.as_posix())

        if self.DEBUG:
            flow_obj <<= nm.m2tee(o = f'debug_predump_{filepath.name}.csv')

        nysol_module = self.wrapFlow(flow_obj)
        self.do_runs(nysol_module)

    def expandWildCards(self, to_expand):
        """
        takes a comma separated string and parses wildcard expressions within.
        
        returns a tuple (exitcode, expansion)
        code 0: executed properly, no errors
        code 1: no match in entire header (FieldNotfoundError)
        """
        expanded = []
        
        for elem in to_expand.split(','):
            matched = False
            for col in self.header:
                if fn.fnmatch(col, elem):
                    expanded += [col]
                    matched = True
                    
            if not matched:
                # notfound error
                return 1, 'FieldNotFoundError'
        
        return 0, expanded
    
    def checkParamIsNumber(self,param):
        '''
        checks if param is a number
        
        if passes, returns None, otherwise, returns 'ParameterTypeError'
        '''
        try:
            param = float(param)
            return None
        except ValueError:
            return 'ParameterTypeError'

    def checkParamIsInteger(self, param):
        '''
        checks if a given param is an integer

        if an integer, returns None, otherwise, returns 'ParameterOutOfBoundsError'
        contains the isnumber check, so if not a number, returns 'ParameterTypeError'
        '''
        not_a_number = self.checkParamIsNumber(param)
        
        if not_a_number is not None: # do the isnumber check
            return not_a_number
            
        param = float(param)
        
        # check if not integer
        if not param.is_integer():
            return 'ParameterOutOfBoundsError'

        return None

    def checkParamOOB(self, param, low = None, low_inc = None, 
                      high = None, high_inc = None):
        '''
        checks if a param is outside the given bounds
        
        returns None if in bounds, otherwise 'ParameterOutOfBoundsError'
        contains the isnumber check, so if not a number, returns 'ParameterTypeError'
        '''
        not_a_number = self.checkParamIsNumber(param)
        
        if not_a_number is not None: # do the isnumber check
            return not_a_number

        param = float(param)
        
        if low_inc is not None:
            if param < low_inc:
                return 'ParameterOutOfBoundsError'

        if low is not None:
            if param <= low:
                return 'ParameterOutOfBoundsError'

        if high_inc is not None:
            if param > high_inc:
                return 'ParameterOutOfBoundsError'

        if high is not None:
            if param >= high:
                return 'ParameterOutOfBoundsError'
        
        return None
            
    def checkParamFormat(self, param, pat):
        '''
        checks if a param matces a regexp format
        
        returns None if ok, ParameterFormatError if not
        '''
        import re
        
        if re.match(pat, param):
            return None

        return 'ParameterFormatError'

    def checkParamGTLT(self, param):
        '''
        takes param of the format a;b and checks if b > a
        
        if ok, returns None, otherwise ParameterFormatError
        contains paramformat check, and raises ParameterFormatError on fail
        '''

        valid_number = '[+,-]?([0-9]+|(([0-9]+[.][0-9]*)|([0-9]*[.][0-9]+))([E,e][+,-]?[0-9]*)?)'

        bad_format = self.checkParamFormat(param, f'^{valid_number};{valid_number}$')
        if bad_format is not None:
            return bad_format

        a, b = param.split(';')
        
        if float(b) < float(a):
            return 'ParameterFormatError'
        
        return None

    def checkParams(self, calc, param):
        '''
        Takes a calc and a parameter value and runs checks to see if the param
        is within limits. 
        Returns None if no error, returns errorcode if there is
        '''

        # get list of checks to perform
        checks = self.const('paraminfo')[calc]['checks']
        # checks is a list of check functions and their parameters

        for check, bounds in checks:
            # each check function returns None if no error, and the error code
            # if there is.
            res = check(param, **bounds)
            
            if res:
                return res
        
        return None
    
    def containsAny(self, exp, str):
        '''
        returns True if exp contains any characters in str
        '''
        return any(char in exp for char in str)

    def findDuplicates(self, raw_list):
        '''
        from a list, find the elements that are repeated
        returns list of repeated elements
        '''
        seen = {}
        dupes = []
        
        for elem in raw_list:
            if elem not in seen:
                seen[elem] = 1
            else:
                if seen[elem] == 1:
                    dupes.append(elem)
                seen[elem] += 1
                
        return dupes 

    def generateCommandErrorMessage(self, errcode, errfield, errinput = '', calc = ''):
        '''
        Function for creating error messages. 
        Pulls out error message templates, command name, and parameter info from
        self.const and then uses input to fill in templates

        generateCommanErrorMessage(errcode, errfield, errinput, calcname)
        TODO figure out how to make this generic, so I can move it up to
             the parent class
        '''
        from string import Template

        errmsgs = self.const('errmsgs')
        commandname = self.const('commandname')
        all_param_info = self.const('paraminfo')

        if calc in all_param_info.keys():
            param_info = all_param_info[calc]
            param_info.pop('checks')
        else:
            param_info = {} 
        
        param_info['calc'] = calc
            
        template_strings = {'fieldinput' : errinput, **param_info}

        message = Template(errmsgs[errcode]).safe_substitute(template_strings)

        return f'【コマンド：{commandname}】【オプション欄：{errfield}】{message}'

    def generateFinalColName(self, args, common_args):
        '''
        given the formatstring and the set of args for the calculation,
        returns the final output column name
        '''
        formatstr = common_args.get('format')
        
        if self.DEBUG:
            print(f'args: {args}')
            print(f'common_args : {common_args}')
            sys.__stderr__.flush()
        
        if 'fld' in args:
            fldname = args['fld']
        else:
            fldname = args['f']

        if 'x' in args:
            fldname += '_' + args['x']
            
        calcname = args['a']
        if 'n' in args:
            calcname += '_' + args['n']

        finalname = formatstr.replace('%', calcname).replace('&', fldname)
        
        return finalname

    def generateFinalColMcatExp(self, formatstr):
        # construct mcal expression to make the finalcol name
        colformat = ['']

        for char in formatstr:
            if char == '&':
                colformat.append('$s{fld}')
                colformat.append('')
            elif char == '%':
                colformat.append('$s{__calcname__}')
                colformat.append('')
            else:
                colformat[-1] += char

        for i, sub in enumerate(colformat):
            if not sub.startswith('$'):
                colformat[i] = f'"{sub}"' 

        mcal_exp = '+'.join(colformat)
        
        if self.DEBUG:
            print(f'finalcol_exp: {mcal_exp}')
            sys.__stderr__.flush()
            
        return mcal_exp

    def simplifyMsummary(self, msum_list):
        '''
        takes the parsed list of msummary calculations from raw arguments, and 
        reduces it to the minimum length list,
        with an exception for 'count', which is put into separate lists
        '''
        # input: [{f: valx, c: sum, a: sum},
        #         {f: valx, c: min, a: min}, ...
        
        # initialize a dict with {colname : [operations]}
        operations = {}

        # initialize count operations with {c_option : targets}
        count_operations = {}
                 
        # first, put all the operations to the same column in one dict
        # {f : val1, c: sum:sum,min:min,max:highest} etc.
        for row in msum_list:
            c_option = f'{row["c"]}:{row["a"]}'
            targetcol = row['f']

            if row['c'] == 'count':
                if c_option in count_operations.keys():
                    if targetcol not in count_operations[c_option]:
                        count_operations[c_option].append(targetcol)
                else:
                    count_operations[c_option] = [targetcol]
            
            else:
                if targetcol in operations.keys():
                    if c_option not in operations[targetcol]:
                        operations[targetcol].append(c_option)
                    else:
                        # raise error
                        errmsg = self.generateCommandErrorMessage('CalcConflictError', 'c', c_option)
                        raise Exception(errmsg)
                    continue
                else:
                    # initialize list
                    operations[targetcol] = [c_option]
        
        # sort operations lists to make sure sum,min == min,sum
        for col, op in operations.items():
            op.sort()
        
        # then, if there are multiple operations with the exact same calcs
        # on different columns, merge them together

        # flip dictionary to find duplicates
        reverse_dict = {}
        for col, op_list in operations.items():
            op_str = ','.join(op_list)
            
            if op_str not in reverse_dict:
                reverse_dict[op_str] = [col]
            else:
                reverse_dict[op_str].append(col)
            
        # finally construct final_list
        # [{'f': 'val1,val2', c: 'sum,min,max'}...]
        final_list = []
        reverse_dict.update(count_operations)

        for op, target_list in reverse_dict.items():
            operation = {}
            
            target_str = ','.join(target_list)
            operation['f'] = target_str
            operation['c'] = op
            
            final_list.append(operation)
        
        return final_list

    def nullifyNonNumber(self, flow, cols):
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

    def nullifyBadTime(self, flow, col, dateformat = 'date'):
        '''
        takes a data with time column, and deletes all rows with a time value
        that does not pass the date format 
        
        details for this regex in https://kskds.docbase.io/posts/1317416
        '''
        if dateformat == 'date':
            # checks if valid date
            flow <<= nm.mcal(a = "__isvalidformat",
                             c= f'regexm($s{{{col}}},"^(((([0-9]{{2}}(([2468][048])|([13579][26])|(0[48])))|((([02468][048])|([13579][26])|(0[048]))(00)))((((0[13578])|(1[02]))((0[1-9])|([1-2][0-9])|(3[01])))|(((0[469])|(11))((0[1-9])|([1-2][0-9])|(30)))|((02)((0[1-9])|([1-2][0-9])))))|([0-9]{{4}}((((0[13578])|(1[02]))((0[1-9])|([0-2][0-9])|(3[01])))|(((0[469])|(11))((0[1-9])|([0-2][0-9])|(30)))|((02)((0[1-9])|(1[0-9])|(2[0-8]))))))((([0-1][0-9])|(2[0-3]))([0-5][0-9]){{2}})([.][0-9]{{1,6}})?$")')

            flow <<= nm.mcal(a = '__int__',
                             c = f'if($s{{__isvalidformat}}=="1",regexstr($s{{{col}}},"^.{{14,14}}"),nulls())')
        
            flow <<= nm.mcal(a = f'__UXT__', 
                    c = 'uxt( s2t($s{__int__}))')
            
            flow <<= nm.mcal(a = '__FLAC__', 
                    c = f'if($s{{__isvalidformat}}=="1",regexstr($s{{{col}}},"[.][0-9]{{1,6}}$"),nulls())')
            
            flow <<= nm.mcal(a = 'finaltime',
                    c = 'if( isnull($s{__FLAC__}), $s{__UXT__}, $s{__UXT__}+$s{__FLAC__} )')
            
            flow <<= nm.mcut(f = '__UXT__,__FLAC__,__isvalidformat', r = True)
        else:
            # checks if valid number
            flow <<= nm.mcal(a = "__isvalidformat",
                             c = f'regexm($s{{{col}}},"^[+,-]?([0-9]+|(([0-9]+[.][0-9]*)|([0-9]*[.][0-9]+))([E,e][+,-]?[0-9]*)?)$")')
            flow <<= nm.mcal(a = 'finaltime',
                             c = f'if($s{{__isvalidformat}}=="1",${{{col}}},nulln())')
            flow <<= nm.mcut(f = '__isvalidformat', r = True)
            
        flow <<= nm.mdelnull(f = 'finaltime')
        flow <<= nm.mcut(f = col, r = True)
        flow <<= nm.mfldname(f = f'finaltime:{col}')
        
        return flow

    def parseArgs(self, raw_args):
        """
        Function for parsing the raw inputs for use.
        
        returns two lists, one for the list of calculations to do, and another
        containing the common parameters for all calculations
        """
        msummary_calcs = []
        nysol_calcs = [] 
        python_calcs = []
        
        # raw_args contents
        # k
        # clist -> 'f', 'fld'
        # fclist
        # nfclist
        # xfclist
        # xfcnlist
        # dateformat -> 'date' or 'num'
        # format -> output columnnames
        # precision
        # nfno -> is this still necessary?
        # batch_size
        
        # compile common parameters
        common_args = {}
       
        common_args['dateformat'] = raw_args.get('dateformat')
        common_args['precision'] = raw_args.get('precision')
        common_args['batch_size'] = raw_args.get('batch_size')
        
        # for backwards compatibility, assign default value of batch size
        if common_args['batch_size'] == None:
            common_args['batch_size'] = 5

        # error handling for common args
        # k errors

        ks = raw_args.get('k') 
        if ks:
            ks_list = ks.split(',')
            

            if '' in ks_list:
                errmsg = self.generateCommandErrorMessage('EmptyKeyFieldError', 'k', ks)
                raise Exception(errmsg)

            expanded_k = []
            
            for k in ks_list:
                
                # check for forbidden characters
                if self.containsAny(k, '%&'):
                    errmsg = self.generateCommandErrorMessage('KeyFieldForbiddenCharacterError', 'k', ks)
                    raise Exception(errmsg)
            
                exitcode, res = self.expandWildCards(k)
                
                if exitcode == 0:
                    expanded_k += res
                    continue
                else:
                    errmsg = self.generateCommandErrorMessage('FieldNotFoundError', 'k', ks)
                    raise Exception(errmsg)

            if self.DEBUG:
                print(f'expanded_k: {expanded_k}')
                sys.__stderr__.flush()
                
            dupes_list = self.findDuplicates(expanded_k)
            if len(dupes_list) > 0: # if duplicates are found
                dupes_str = ','.join(dupes_list)
                errmsg = self.generateCommandErrorMessage('KeyFieldConflictError', 'k', dupes_str)
                raise Exception(errmsg)

            # set manual k input flag
            common_args['manual_k'] = True
            common_args['k'] = ','.join(expanded_k)
        
        else: # if k is empty
            ks_list = []

            # set manual k input flag
            common_args['manual_k'] = False
            common_args['k'] = '__key__'

        # format errors
        formatstr = raw_args.get('format')

        if self.containsAny(formatstr, '*?[],:\\\'\" '):
            errmsg = self.generateCommandErrorMessage('ResultsColForbiddenCharacterError', 'format', formatstr)
            raise Exception(errmsg)

        common_args['format'] = formatstr

        
        # start parsing through the separate args

        all_args = (raw_args.get('clist') + 
                    raw_args.get('fclist') +
                    raw_args.get('nfclist') +
                    raw_args.get('xfclist') + 
                    raw_args.get('xfcnlist'))

        all_fs = set()
        final_columns = []
                       
        for row in all_args:
            
            # ignore rows where all values are empty
            if all([val == '' for val in row.values()]):
                continue

            cs = row.pop('c')
            
            if cs == '':
                errmsg = self.generateCommandErrorMessage('EmptyCalcError', 'c', cs)
                raise Exception(errmsg)
            
            cs_list = cs.split(',')
                
            
            # データセットに対する特徴量
            if 'fld' in row:
                # if a dict contains 'fld', it is an operation on the whole
                # data set. 
               
                fld = row.get('fld') 
                # check if multiple flds specified
                if ',' in fld:
                    errmsg = self.generateCommandErrorMessage('MultipleRowsTargetError', 'fld', fld)
                    raise Exception(errmsg)

                if self.containsAny(fld, '%&'):
                    errmsg = self.generateCommandErrorMessage('TargetFieldForbiddenCharacterError', 'fld', fld)
                    raise Exception(errmsg)

                
                # check for newname setting
                for c in cs_list:
                    if ':' in c:
                        c, a = c.split(':')
                    else:
                        a = c 
                        
                    row['a'] = a
                    
                    all_fs.add(fld)
                    
                    final_columns.append(self.generateFinalColName(row, common_args))
                    
                    nysol_calcs.append({'fld' : fld, 'c' : c, 'a' : a})
                continue

            else: # any other case will have both 'f' and 'c' options

                # first expand the wildcards in f
                fs = row.pop('f') # get list of fs
                fs_list = fs.split(',')

                # check for empty fs
                if '' in fs_list:
                    errmsg = self.generateCommandErrorMessage('EmptyTargetFieldError', 'f', fs)
                    raise Exception(errmsg)
                
                expanded_f = []
                
                for f in fs_list:
                    code, res = self.expandWildCards(f)

                    # check for forbidden characters in f
                    if self.containsAny(f, '%&'):
                        errmsg = self.generateCommandErrorMessage('TargetFieldForbiddenCharacterError', 'f', f)
                        raise Exception(errmsg)

                    if code == 0: # no error
                        expanded_f += res
                        continue
                    elif code == 1: # no match in wildcards
                        errmsg = self.generateCommandErrorMessage(res, 'f', f)
                        raise Exception(errmsg)
                
                # f wildcards for this row are now expanded into list form
                # add expanded wildcard expression to the set of all fs
                all_fs.update(expanded_f)

                # check for duplicates in f
                dupes_list = self.findDuplicates(expanded_f)
                if len(dupes_list) > 0: # if duplicates are found
                    dupes_str = ','.join(dupes_list)
                    errmsg = self.generateCommandErrorMessage('TargetFieldConflictError', 'f', dupes_str)
                    raise Exception(errmsg)


                # check if any element in c requires params
                for c in cs_list:
                    if c in self.const('paraminfo'):
                        # Multiple ParamCalc error
                        if len(cs_list) > 1:
                            errmsg = self.generateCommandErrorMessage('MultipleParamCalcError', 'c', cs)
                            raise Exception(errmsg)

                        # check param values
                        params = row.get('n')
                        # empty param error
                        if not params:
                            errmsg = self.generateCommandErrorMessage('EmptyParamError', 'n', params)
                            raise Exception(errmsg)

                        params_list = params.split(',')
                        if '' in params_list:
                            errmsg = self.generateCommandErrorMessage('EmptyParamError', 'n', params)
                            raise Exception(errmsg)
                        
                        # check for duplicates here
                        dupes_list = self.findDuplicates(params_list)
                        if len(dupes_list) > 0: # if duplicates are found
                            dupes_str = ','.join(dupes_list)
                            errmsg = self.generateCommandErrorMessage('ParamConflictError', 'n', dupes_str)
                            raise Exception(errmsg)
                        
                        # check param values here
                        for n in params_list:
                            errcode = self.checkParams(c, n)
                            if errcode:
                                errmsg = self.generateCommandErrorMessage(errcode, 'n', n, c)
                                raise Exception(errmsg)
                        
                # check for empty strings in c
                if '' in cs_list:
                    errmsg = self.generateCommandErrorMessage('EmptyCalcError', 'c', c)
                    raise Exception(errmsg)
                
                # check for duplicates in c
                dupes_list = self.findDuplicates(cs_list)
                if len(dupes_list) > 0: # if duplicates are found
                    dupes_str = ','.join(dupes_list)
                    errmsg = self.generateCommandErrorMessage('CalcConflictError', 'c', dupes_str)
                    raise Exception(errmsg)

                # if x exists, catch errors
                if 'x' in row:
                    x = row.get('x')
                    xs_list = x.split(',')

                    if self.containsAny(x, '*?[],:\\&%'):
                        errmsg = self.generateCommandErrorMessage('TimeColForbiddenCharacterError', 'x', x)
                        raise Exception(errmsg)
                    
                    for x in xs_list:
                        if x not in self.header:
                            errmsg = self.generateCommandErrorMessage('FieldNotFoundError', 'x', x)
                            raise Exception(errmsg)
                            

                    if '' in xs_list:
                        errmsg = self.generateCommandErrorMessage('EmptyTimeColError', 'x', x)
                        raise Exception(errmsg)
                        


                # then iterate over all specfied c arguments
                for c in cs_list:
                    for f in expanded_f:

                        # set up new name for calc
                        if ':' in c:
                            c, a = c.split(':')
                            if a == '':
                                errmsg = self.generateCommandErrorMessage('EmptyCalcNewNameError', 'c', c)
                                raise Exception(errmsg)
                        else:
                            a = c
                            
                        row['a'] = a

                        n_str = row.get('n') # if n is specified, distribute 
                        if n_str:
                            row.pop('n')
                            ns_list = n_str.split(',')
                            calcs = []
                            for n in ns_list:
                                calcs.append({'c' : c, 'f' : f, 'n' : n, **copy.deepcopy(row)})
                            row['n'] = n_str
                        else:
                            # prepare one calculation dictionary
                            calcs = [{'c' : c, 'f' : f, **row}]
                            
                        for thiscalc in calcs:
                            # append thiscalc to the appropriate list
                            if c in self.const('msum_calcs'):
                                msummary_calcs.append(thiscalc)
                            elif c in self.const('nysol_calcs'):
                                nysol_calcs.append(thiscalc)
                            elif c in self.const('python_calcs'):
                                python_calcs.append(thiscalc)
                            else: # c is not in any list, therefore does not exist
                                errmsg = self.generateCommandErrorMessage('CalcNotFoundError', 'c', c)
                                raise Exception(errmsg) 
                            
                            final_columns.append(self.generateFinalColName(thiscalc, common_args))
                        
        # check if k and fs are overlapping
        kf_overlap = []
        for key in ks_list:
            if key in all_fs:
                kf_overlap.append(key)

        if len(kf_overlap) > 0:
            ks_overlapstr = ','.join(kf_overlap)
            errmsg = self.generateCommandErrorMessage('KeyTargetConflictError', 'k', ks_overlapstr)
            raise Exception(errmsg)
            
        # check if there is an overlap of final columns
        dupes_list = self.findDuplicates(final_columns)
        if len(dupes_list) > 0:
            dupes_str = ','.join(dupes_list)
            errmsg = self.generateCommandErrorMessage('ResultsColConflictError', 'format, c, f, n', dupes_str)
            raise Exception(errmsg)
            
        # reduce/simplify msummary 
        msummary_calcs = self.simplifyMsummary(msummary_calcs)

        # finally, combine the three lists into one 
        parsed_args = []

        for op in msummary_calcs:
            op['type'] = 'msummary'
            parsed_args.append(op)

        for op in nysol_calcs:
            op['type'] = 'nysol'
            parsed_args.append(op)
        
        for op in python_calcs:
            op['type'] = 'python'
            parsed_args.append(op)

        return parsed_args, common_args

    def transformToVertical(self, subcmd, formatstr, k, cols):
        '''
        takes data of the form:
        keys, fld, cols[0], cols[1], ...

        and transforms it to
        keys, final_cols, __val__ 
        '''
        colformat = self.generateFinalColMcatExp(formatstr)
    
        subcmd <<= nm.m2cross(k = f'{k},fld', f= cols, 
                a = '__calcname__,__val__')
        subcmd <<= nm.mcal(a = 'final_cols', c = colformat)
        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd
        
    def cutToRelevantCols(self, subcmd, args, common_args):
        '''
        gets the relevant columns
        '''
        relevant_cols = common_args['k'].split(',')
        if 'f' in args:
            # relevant_cols.append(args['fld'])
        # else:
            relevant_cols.extend(args['f'].split(','))

        if 'x' in args:
            relevant_cols.append(args['x'])

        subcmd <<= nm.mcut(f = relevant_cols)
        
        return subcmd
    
    def run_batches(self, file_to_read, all_calcs, common_args):
        '''
        given the batch size, distributes the operations into batches, and 
        runs each batch, taking note of all the batches filenames
        '''
        file_list = []

        batch_size = int(common_args.pop('batch_size'))
        batches = ceil(len(all_calcs) / batch_size)
        
        # run each batch
        # calculate each from a formatted command list
        for batchnum in range(batches):
            # refresh calulation array
            cmd = [None] * batch_size
            
            # iterate per calc in batch
            for i in range(batch_size):
                calcnum = (batchnum * batch_size) + i
                
                try:
                    # try to get next calculation
                    thiscalc = all_calcs[calcnum]
                except IndexError:
                    # if no more calcs, break out of loop
                    break

                cmd[i] <<= nm.m2tee(i = file_to_read.as_posix())

                # cut out only relevant columns
                cmd[i] = self.cutToRelevantCols(cmd[i], thiscalc, common_args)

                calctype = thiscalc.pop('type')
                if calctype == 'msummary':
                    func = self.feature_msummary
                    # if thiscalc is a count calc, remove nonnumbers
                    if thiscalc['c'].startswith('count'):
                        cmd[i] = self.nullifyNonNumber(cmd[i], thiscalc['f'])
                    
                else:
                    func = self.const('funcs')[thiscalc['c']]
                    # TODO perform checks
                    # if the calc does not support strings (numbers only),
                    # nullify all the nonnumber rows
                    if thiscalc['c'] not in self.const('supports_str'):
                        cmd[i] = self.nullifyNonNumber(cmd[i], thiscalc['f'])

                    # if the calc has a time column, clean up the rows with
                    # invalid time
                    if 'x' in thiscalc:
                        cmd[i] = self.nullifyBadTime(cmd[i], thiscalc['f'],
                                                     common_args['dateformat'])

                # run the desired function
                cmd[i] = func(cmd[i], thiscalc, common_args)
                # output of func is of the form:
                # keys, final_cols, __val__
                
            CALC_RES_TMP = Tmp.create_file()
            
            self.dumpToFile(cmd, CALC_RES_TMP)
            
            file_list.append(CALC_RES_TMP.as_posix())

            
        return file_list

        
    def feature_runfuncwrapper(self, subcmd, args, common_args):
        '''
        wrapper function for runfunc features
        '''
        func = self.const('runfunc_calcs')[args['c']]
        
        subcmd <<= nm.runfunc(func, subcmd=subcmd, args=args, common_args=common_args)
        
        return subcmd
        
    # データセットに対する特徴量
    def feature_rows(self, subcmd, args, common_args):
        '''
        calculate the rows feature
        '''
        k = common_args.get('k')
        
        resultcolname = self.generateFinalColName(args, common_args)
        
        subcmd <<= nm.mcount(k = k, a = '__val__')
        subcmd <<= nm.msetstr(a = 'final_cols', v = resultcolname)
        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        if self.DEBUG:
            subcmd <<= nm.m2tee(o = 'end_of_rows.csv')

        return subcmd

    # １つの変数に対する特徴量
    def feature_msummary(self, subcmd, args, common_args):
        '''
        calculate msummary features
        '''
        opts = {**args}
        opts['k'] = common_args['k']
        k = opts['k']
        opts['precision'] = common_args['precision']
        formatstr = common_args['format']
        

        # prepare list of output cols of msummary
        final_cs = [c.split(':')[-1] for c in args['c'].split(',')]
        
        if self.DEBUG:
            print(f'opts: {opts}')
            
        # calculate
        subcmd <<= nm.msummary(**opts)
        
        subcmd = self.transformToVertical(subcmd, formatstr, k, final_cs)

        
        return subcmd 
    
    def feature_miss(self, subcmd, args, common_args):
        '''
        calculate missing value count feature
        '''
        f = args.get('f')
        k = common_args.get('k')

        resultcolname = self.generateFinalColName(args, common_args)

        allrows = None
        
        allrows <<= nm.mcount(i = subcmd, k = k, a = '__allrows')

        subcmd <<= nm.msummary(k = k, f = f, c = 'count:__count')
        subcmd <<= nm.mnjoin(k = k, m = allrows, f = '__allrows')

        subcmd <<= nm.mcal(a = '__missingcount', c = '${__allrows}-${__count}')
        subcmd <<= nm.mcal(a = '__val__', c = '$s{__missingcount}')
        subcmd <<= nm.msetstr(a = 'final_cols', v = resultcolname)

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    def feature_strucount(self, subcmd, args, common_args):
        '''
        calculates feature strucount
        '''
        fld = args.get('f')
        k = common_args.get('k')

        resultcolname = self.generateFinalColName(args, common_args)

        subcmd <<= nm.muniq(k = f'{k},{fld}') 
        subcmd <<= nm.mcount(k = k, a = '__val__')
        subcmd <<= nm.msetstr(a = 'final_cols', v = resultcolname)
        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    def feature_strmin(self, subcmd, args, common_args):
        '''
        calculate feature strmin
        '''
        fld = args.get('f')
        k = common_args.get('k')

        resultcolname = self.generateFinalColName(args, common_args)

        subcmd <<= nm.mkeybreak(k = k, s = fld)
        subcmd <<= nm.mcal(a = 'fld', c = f'if($s{{top}}=="1","{fld}",nulls())')
        subcmd <<= nm.mcal(a = '__val__', c = f'if($s{{top}}=="1",$s{{{fld}}},nulls())')
        subcmd <<= nm.msel(c = f'$s{{top}}=="1"')

        subcmd <<= nm.msetstr(a = 'final_cols', v = resultcolname)

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    def feature_strmax(self, subcmd, args, common_args):
        '''
        calculate feature strmax
        '''
        fld = args.get('f')
        k = common_args.get('k')

        resultcolname = self.generateFinalColName(args, common_args)

        subcmd <<= nm.mkeybreak(k = k, s = fld)
        subcmd <<= nm.mcal(a = 'fld', c = f'if($s{{bot}}=="1","{fld}",nulls())')
        subcmd <<= nm.mcal(a = '__val__', c = f'if($s{{bot}}=="1",$s{{{fld}}},nulls())')
        subcmd <<= nm.msel(c = f'$s{{bot}}=="1"')

        subcmd <<= nm.msetstr(a = 'final_cols', v = resultcolname)

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd
    
    def feature_hasdup(self, subcmd, args, common_args):
        '''
        calculates the flag feature has duplicate 
        '''
        fld = args.get('f')
        k = common_args.get('k')

        resultcolname = self.generateFinalColName(args, common_args)
        subcmd_o = None

        total = nm.mcount(k = f'{k},{fld}', a = '__dcnt', i = subcmd)

        msummary = nm.msummary(k = k, f = fld, c = 'count:__count',
                                    i = subcmd)

        subcmd_o <<= nm.mcount(k = k, a = '__ddcnt', i = total)
        subcmd_o <<= nm.msetstr(a = 'fld', v = fld)
        subcmd_o <<= nm.mnjoin(k = f'{k},fld', f = '__count', m = msummary)
        subcmd_o <<= nm.mcal(c = '${__ddcnt}!=${__count}', a = '__val__')

        subcmd_o <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd_o <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd_o

    def feature_repeatdata(self, subcmd, args, common_args):
        '''
        calculates feature repeatdata
        '''
        
        fld = args.get('f')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)

        subcmd <<= nm.mcount(k = f'{k},{fld}', a = '__count__')
        subcmd <<= nm.mfldname(f = f'{fld}:___')
        subcmd <<= nm.mcal(a = fld, c = '${__count__}>1')
        subcmd <<= nm.msummary(k = k, f = f'{fld}', 
                            c = 'sum:__sum__,count:__count__')
        subcmd <<= nm.mcal(c = '${__sum__}/${__count__}', a = '__val__',
                                precision = precision)
        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    def feature_repeatvalues(self, subcmd, args, common_args):
        '''
        calculate feature repeatvalues
        '''
        fld = args.get('f')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)

        mcount = None 

        mcount <<= nm.mcount(k = f'{k}', a ='__total__', 
                                i = subcmd)

        subcmd <<= nm.mcount(k = f'{k},{fld}', a = '__count__')
        subcmd <<= nm.mcal(a = '__repeat__', c = 'if(${__count__}>1,${__count__},0)')
        subcmd <<= nm.msum(k = k, f = '__repeat__')

        subcmd <<= nm.mjoin(m = mcount, f = '__total__', k = k)
        subcmd <<= nm.mcal(a = '__val__', c = '${__repeat__}/${__total__}', 
                                precision = precision)
        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    def feature_sumrepeatdata(self, subcmd, args, common_args):
        '''
        calculate feature sum_repeatdata
        '''
        fld = args.get('f')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)

        subcmd <<= nm.mcount(k = f'{k},{fld}', a = '__count__')
        subcmd <<= nm.mcal(c = f'if(${{__count__}}==1,0,${{__count__}}*${{{fld}}})', 
                           a = '__val__')
        subcmd <<= nm.msum(k = k, f = f'__val__', precision = precision)

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    def feature_sumrepeatvalues(self, subcmd, args, common_args):
        '''
        calculate feature sum_repeatvalues
        '''
        fld = args.get('f')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)

        subcmd <<= nm.mcount(k = f'{k},{fld}', a = '__count__')
        subcmd <<= nm.mcal(c = f'if(${{__count__}}==1,0,${{{fld}}})', a = '__val__')
        subcmd <<= nm.msum(k = k, f = f'__val__', precision = precision)

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd
    
    def feature_ratiounique(self, subcmd, args, common_args):
        '''
        calculate feature ratio_unique
        '''
        fld = args.get('f')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)

        msums = None
        
        msums = nm.msummary(i = subcmd, k = k, f = fld, c = 'count,ucount')

        subcmd <<= nm.mnjoin(m = msums, f = 'count,ucount', k = k)
        subcmd <<= nm.mcal(c = '${ucount}/${count}', a = '__val__',
                           precision = precision)
        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd
    
    def feature_countabovemean(self, subcmd, args, common_args):
        '''
        calculate feature count_above_mean
        '''
        fld = args.get('f')
        k = common_args.get('k')

        resultcolname = self.generateFinalColName(args, common_args)

        msums = None
        
        msums = nm.msummary(i = subcmd, k = k, f = fld, c = 'mean')

        subcmd <<= nm.mnjoin(m = msums, f = 'mean', k = k)

        subcmd <<= nm.mcal(c = f'${{{fld}}}>${{mean}}', a = '__val__')
        subcmd <<= nm.msum(k = f'{k}', f = '__val__')
            
        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    def feature_countbelowmean(self, subcmd, args, common_args):
        '''
        calculate feature count_below_mean
        '''
        fld = args.get('f')
        k = common_args.get('k')

        resultcolname = self.generateFinalColName(args, common_args)

        msums = None
        
        msums = nm.msummary(i = subcmd, k = k, f = fld, c = 'mean')

        subcmd <<= nm.mnjoin(m = msums, f = 'mean', k = k)

        subcmd <<= nm.mcal(c = f'${{{fld}}}<${{mean}}', a = '__val__')
        subcmd <<= nm.msum(k = f'{k}', f = '__val__')
            
        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    def feature_hasdupmin(self, subcmd, args, common_args):
        '''
        calculates feature has_dup_min
        '''
        fld = args.get('f')
        k = common_args.get('k')

        resultcolname = self.generateFinalColName(args, common_args)

        subcmd <<= nm.mcount(k = f'{k},{fld}', a = '__dcnt')

        subcmd <<= nm.mbest(k = k, s = f'{fld}%n', size = 1)    
        subcmd <<= nm.mcal(c = '${__dcnt}>1', a = '__val__')

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    def feature_hasdupmax(self, subcmd, args, common_args):
        '''
        calculates feature has_dup_max
        '''
        fld = args.get('f')
        k = common_args.get('k')

        resultcolname = self.generateFinalColName(args, common_args)

        subcmd <<= nm.mcount(k = f'{k},{fld}', a = '__dcnt')

        subcmd <<= nm.mbest(k = k, s = f'{fld}%nr', size = 1)    
        subcmd <<= nm.mcal(c = '${__dcnt}>1', a = '__val__')

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd
    
    def feature_hmean(self, subcmd, args, common_args):
        '''
        calculates feature hmean
        '''
        fld = args.get('f')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)
            
        flags = None 

        flags <<= nm.msummary(i = subcmd, c = 'min', k = k, f = fld)
        flags <<= nm.mcal(a = '__hasnegative', c = '${min}<0')
        flags <<= nm.mcal(a = '__haszero', c = '${min}==0') 

        subcmd <<= nm.mcal(a = f'{fld}_inv', c = f'1/${{{fld}}}')

        subcmd <<= nm.msummary(c = 'sum,count', f = f'{fld}_inv', k = k)

        subcmd <<= nm.mjoin(k = k, m = flags, f = '__hasnegative,__haszero')
            
        subcmd <<= nm.mcal(a = '__val__', c = 'if(${__hasnegative}==1,nulln(),if(${__haszero}==1,0,${count}/${sum}))',
                            precision = precision)

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd
            
    def feature_gmean(self, subcmd, args, common_args):
        '''
        calculates feature gmean
        '''
        fld = args.get('f')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)

        flags = None
        flags <<= nm.msummary(i = subcmd, c = 'min', k = k, f = fld)
        flags <<= nm.mcal(a = '__hasnegative', c = '${min}<0')
        flags <<= nm.mcal(a = '__haszero', c = '${min}==0') 
            
        subcmd <<= nm.mcal(a = f'{fld}_ln', c = f'ln(${{{fld}}})')

        subcmd <<= nm.msummary(c = 'mean', f = f'{fld}_ln', k = k)
            
        subcmd <<= nm.mjoin(k = k, m = flags, f = '__hasnegative,__haszero')

        subcmd <<= nm.mcal(a = '__val__', c = 'if($b{__hasnegative},nulln(),if($b{__haszero},0,exp(${mean})))', 
                        precision = precision)

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    def feature_absenergy(self, subcmd, args, common_args):
        '''
        calculates feature abs_energy
        '''
        fld = args.get('f')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)

        subcmd <<= nm.mcal(c = f'${{{fld}}}*${{{fld}}}', a = f'__tmp{fld}')
        subcmd <<= nm.mcut(f = fld, r = True)
        
        subcmd <<= nm.msum(k = k, f = f'__tmp{fld}:__val__',  
                           precision = precision)

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    def feature_rms(self, subcmd, args, common_args):
        '''
        calculate feature rms
        ''' 
        fld = args.get('f')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)

        subcmd <<= nm.mcal(a = f'{fld}_sq', c = f'${{{fld}}}^2')
        
        # msummary to mean
        subcmd <<= nm.msummary(c = 'mean', f = f'{fld}_sq', k = k)

        # mcal to sqrt
        subcmd <<= nm.mcal(a = '__val__', c = 'sqrt(${mean})',
                        precision = precision)

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    def feature_medianad(self, subcmd, args, common_args):
        '''
        calculate feature median_ad
        '''
        fld = args.get('f')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)
                            
        mediancalc = None

        mediancalc <<= nm.msummary(i = subcmd, c = 'median:__median', f = fld, k = k)

        subcmd <<= nm.mnjoin(k = k, f = '__median', m = mediancalc)

        subcmd <<= nm.mcal(a = f'{fld}_diff', 
                        c = f'abs(${{{fld}}}-${{__median}})')

        subcmd <<= nm.msummary(k = k, c = f'mean:__val__', f = f'{fld}_diff', 
                            precision = precision)

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    def feature_meanad(self, subcmd, args, common_args):
        '''
        calculate feature mean_ad
        '''
        fld = args.get('f')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)
                            
        meancalc = None

        meancalc <<= nm.msummary(i = subcmd, c = 'mean:__mean', f = fld, k = k)

        subcmd <<= nm.mnjoin(k = k, f = '__mean', m = meancalc)

        subcmd <<= nm.mcal(a = f'{fld}_diff', 
                        c = f'abs(${{{fld}}}-${{__mean}})')

        subcmd <<= nm.msummary(k = k, c = f'mean:__val__', f = f'{fld}_diff', 
                               precision = precision)

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd
    
    def feature_vargtsd(self, subcmd, args, common_args):
        '''
        calculate feature var_gt_sd
        '''
        fld = args.get('f')
        k = common_args.get('k')

        resultcolname = self.generateFinalColName(args, common_args)
        
        subcmd <<= nm.msummary(k = k, f = fld, c = 'var:__var,sd:__sd')
            
        subcmd <<= nm.mcal(c = 'if(isnull(${__var}),nullb(),${__var}>${__sd})', 
                           a = '__val__')
        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    # １つの変数に対する特徴量（パラメータあり）
    def feature_valuecount(self, subcmd, args, common_args):
        '''
        calculate feature value_count
        '''
        fld = args.get('f')
        n = args.get('n')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)

        strparam = False
        try:
            n = float(n)
            if n%1 == 0:
                n = int(n)
        except ValueError:
            strparam = True

        if strparam:
            subcmd <<= nm.mcal(a = '__eq', c = f'$s{{{fld}}}=="{n}"')
        else:
            subcmd <<= nm.mcal(a = '__eq', c = f'${{{fld}}}=={n}')
            

        subcmd <<= nm.msum(k = k, f = f'__eq:__val__')


        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    def feature_symlooking(self, subcmd, args, common_args):
        '''
        calculate feature summetry_looking
        '''
        fld = args.get('f')
        n = args.get('n')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)


        msumres = None
        msumres <<= nm.msummary(i = subcmd, k = k, f = fld,
                                c = 'mean:__mean,median:__median,max:__max,min:__min')

        subcmd <<= nm.mnjoin(k = k, f = '__mean,__median,__max,__min',
                                m = msumres)
        # subcmd <<= nm.msummary(f = f, k = k, 
        #             c = 'mean:__mean,median:__median,max:__max,min:__min')
        subcmd <<= nm.mcal(c = '${__max}-${__min}',
                            a = 'max_min')
        subcmd <<= nm.mcal(c = 'abs(${__mean}-${__median})',
                            a = 'mean_median')
        subcmd <<= nm.mcal(c = f'${{mean_median}}<${{max_min}}*{n}', 
                           a = f'__val__', precision = precision)

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    def feature_largesd(self, subcmd, args, common_args):
        '''
        calculate feature large_sd
        '''
        fld = args.get('f')
        n = args.get('n')
        k = common_args.get('k')

        resultcolname = self.generateFinalColName(args, common_args)

        subcmd <<= nm.msummary(f = fld, k = k, 
                    c = 'sd:__sd,max:__max,min:__min')
        subcmd <<= nm.mcal(c = '${__max}-${__min}', a = '__diff')
        subcmd <<= nm.mcal(c = f'${{__sd}}>${{__diff}}*{n}', 
                            a = '__val__')

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    def feature_ratiogtrsigma(self, subcmd, args, common_args):
        '''
        calculate feature ratio_beyond_rsigma
        '''
        fld = args.get('f')
        n = args.get('n')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)

        msums = None
        msums <<= nm.msummary(k = k, f = fld, i = subcmd,
                              c = 'mean:__mean,sd:__sd,count:__count')

        subcmd <<= nm.mnjoin(k = k, m = msums, f = '__mean,__sd,__count')


        subcmd <<= nm.mcal(c = f'(abs(${{{fld}}}-${{__mean}}))>=({n}*${{__sd}})', 
                                a = f'__ratio')

        subcmd <<= nm.msum(k = k, f = f'__ratio')
        subcmd <<= nm.mcal(c = '${__ratio}/${__count}', a = f'__val__', 
                           precision = precision)

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    def feature_binnedentropy(self, subcmd, args, common_args):
        '''
        calculate feature binned_entropy
        '''
        fld = args.get('f')
        n = args.get('n')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)

        msums = nm.msummary(i = subcmd, f = fld, k = k, 
                            c = 'count:__count')

        subcmd <<= nm.mbucket(k = k, f = f'{fld}:__{fld}_no',
                                n = n, rng = True)

        subcmd <<= nm.mcount(k = f'{k},__{fld}_no', a = f'__{fld}hcount')


        subcmd <<= nm.mnjoin(k = k, m = msums, f = 'fld,__count')
        subcmd <<= nm.mcal(c = f'(${{__{fld}hcount}}/${{__count}})*ln(${{__{fld}hcount}}/${{__count}})',
                                a = '__probs')
        subcmd <<= nm.mcut(f = f'{k},fld,__probs')

        subcmd <<= nm.msum(k = f'{k},fld', f = '__probs')
        subcmd <<= nm.mcal(c = '${__probs}*-1', a = '__val__', 
                           precision = precision)

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd
    
    def feature_quantile(self, subcmd, args, common_args):
        '''
        calculate feature quantile
        '''
        fld = args.get('f')
        n = args.get('n')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)

        precalcs = None
        subcmd_o = None

        precalcs <<= nm.mnumber(i = subcmd, s = f'{fld}%n', k = k, 
                                    a = '__qtNo', S = 1)
        precalcs <<= nm.msortf(f = f'{k},__qtNo')

        subcmd_o <<= nm.msummary(f = fld, c = 'count:__count', k = k, i = subcmd)
        subcmd_o <<= nm.mcal(a = '__qtRate', c = f'if(${{__count}}==0,nulln(),{n})')
        subcmd_o <<= nm.mcal(a = '__T', c = '1-${__qtRate}+${__count}*${__qtRate}')
        subcmd_o <<= nm.mcal(a = '__T1', c = 'int(${__T})')
        subcmd_o <<= nm.mcal(a = '__T2', c = 'if(fract(${__T})==0,${__T1},${__T1}+1)')

        subcmd_o <<= nm.mnjoin(k = f'{k},__T1', K = f'{k},__qtNo',
                                f = f'{fld}:__{fld}X1', m = precalcs, n = True)
        subcmd_o <<= nm.mnjoin(k = f'{k},__T2', K = f'{k},__qtNo',
                                f = f'{fld}:__{fld}X2', m = precalcs, n = True)
        subcmd_o <<= nm.mcal(a = '__val__', precision = precision,
                             c = f'if(${{__T1}}==${{__T2}},${{__{fld}X1}},(${{__T2}}-${{__T}})*${{__{fld}X1}}+(${{__T}}-${{__T1}})*${{__{fld}X2}})')

        subcmd_o <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd_o <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd_o

    def feature_rangecount(self, subcmd, args, common_args):
        '''
        calculate feature range_count
        '''
        fld = args.get('f')
        nmin, nmax = args.get('n').split(';')
        k = common_args.get('k')

        resultcolname = self.generateFinalColName(args, common_args)

        subcmd <<= nm.mcal(a = '__inrange',
            c = f'${{{fld}}}>={float(nmin)} && ${{{fld}}} < {float(nmax)}')
        subcmd <<= nm.msum(k = k, f = f'__inrange:__val__')

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd
       
    # ２つの変数に対する特徴量
    def feature_slope(self, subcmd, args, common_args):
        '''
        calculate feature slope
        '''
        fld = args.get('f')
        x = args.get('x')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)

        xy_covar = nm.msim(k = k, i = subcmd, f = f'{x},{fld}', 
                           c = 'covar:__covar')

        subcmd <<= nm.mstats(k = k, c = 'var', f = f'{x}:__Sxx')

        subcmd <<= nm.mjoin(k = k, m = xy_covar, f = '__covar')

        subcmd <<= nm.mcal(c = '${__covar}/${__Sxx}', a = '__val__',
                           precision = precision)

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd
        
    def feature_pearson(self, subcmd, args, common_args):
        '''
        calculate feature slope_pearson
        '''
        fld = args.get('f')
        x = args.get('x')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)

        subcmd <<= nm.msim(k = k, c = 'pearson:__val__', 
                           f = f'{x},{fld}', a = 'fld2,fld',
                           precision = precision)

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd
        
    def feature_pattern(self, subcmd, args, common_args):
        '''
        calculate feature slope_pattern
        '''
        fld = args.get('f')
        x = args.get('x')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)

        subcmd <<= nm.mdelnull(f = fld)
        subcmd <<= nm.mnumber(a = '__order__', I = 1, k = k, S = 0, q = True)

        subcmd <<= nm.msim(k = k, c = 'pearson:__val__', 
                           f = f'__order__,{fld}', a = 'fld2,fld',
                           precision = precision)

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')
        
        if self.DEBUG:
            subcmd <<= nm.m2tee(o = 'debug_end_of_feature_pattern.csv')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    def feature_M2DC(self, subcmd, args, common_args):
        '''
        calculate fature mean second derivative (central approx)
        '''
        fld = args.get('f')
        x = args.get('x')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)

        subcmd <<= nm.mslide(k = k, s = f'{x}%n', f = f'{fld}:__shifted{fld}',
                             t = 2)
        subcmd <<= nm.mcal(c = f'(${{__shifted{fld}2}}-2*${{__shifted{fld}1}}+${{{fld}}})', 
                           a = '__val__')
        subcmd <<= nm.mavg(k = k, f = '__val__', precision = precision)

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd
        
    def feature_meanchange(self, subcmd, args, common_args):
        '''
        calculate feature mean_change
        '''
        fld = args.get('f')
        x = args.get('x')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)

        subcmd <<= nm.mslide(k = k, s = f'{x}%n', f = f'{fld}:__shifted{fld}')
        subcmd <<= nm.mcal(c = f'${{__shifted{fld}}}-${{{fld}}}', a = '__val__')
        subcmd <<= nm.mavg(k = k, f = '__val__', precision = precision)

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    def feature_meanabschange(self, subcmd, args, common_args):
        '''
        calculate feature mean_abs_change
        '''
        fld = args.get('f')
        x = args.get('x')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)

        subcmd <<= nm.mslide(k = k, s = f'{x}%n', f = f'{fld}:__shifted{fld}')
        subcmd <<= nm.mcal(c = f'abs(${{__shifted{fld}}}-${{{fld}}})', a = '__val__')
        subcmd <<= nm.mavg(k = k, f = '__val__', precision = precision)

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    def feature_abssumchanges(self, subcmd, args, common_args):
        '''
        calculate feature abs_sum_changes
        '''
        fld = args.get('f')
        x = args.get('x')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)

        subcmd <<= nm.msortf(f = f'{k},{x}%n')
        subcmd <<= nm.mcal(c = f'abs(${{{fld}}}-#{{{fld}}})', a = f'__absdiff')
            
        subcmd <<= nm.msum(k = k, f = '__absdiff:__val__', 
                           precision = precision) 

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    def feature_integral(self, subcmd, args, common_args):
        '''
        calculates integral via trapezoid rule
        '''
        fld = args.get('f')
        x = args.get('x')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)

        # get keybreak points
        subcmd <<= nm.msortf(f = k)
        subcmd <<= nm.mkeybreak(k = k, s = f'{x}%n')

        # if not top of section, get time step length, else null
        subcmd <<= nm.mcal(a = 'time_step', 
                        c = f'if(isnull(${{top}}),${{{x}}}-#{{{x}}},nulln())')

        # if not top of section, add current and previous value, else null
        subcmd <<= nm.mcal(a = f'{fld}_partial_sum', 
                c = f'if(isnull(${{top}}),${{{fld}}}+#{{{fld}}},nulln())')

        # trapezoid rule: (((partialsum)/2)*step size)
        subcmd <<= nm.mcal(a = f'{fld}_trap', 
                c = f'(${{{fld}_partial_sum}}/2)*${{time_step}}')

        # sum over each key
        subcmd <<= nm.msum(k = k, f = f'{fld}_trap:__val__', 
                           precision = precision)

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    # TODO figure out how to decorate these instead? 
    def feature_meanfrequency(self, subcmd, args, common_args):
        '''
        calculate meanfrequency
        '''
        # body of this method adapted from:
        # github.com/nysol/nysol_python/blob/master/scripts/sample/mkfeature.py
        try:
            import math
            import numpy as np
            
            f = args.get('f')
            x = args.get('x')
            k = common_args.get('k')
            precision = common_args.get('precision')
            
            resultcolname = self.generateFinalColName(args, common_args)

            headerline = True

            for dlist in nm.mstdin().keyblock(f'{k}', f'{x}%n', header = True):
                id = ','.join(dlist[0][:len(k.split(','))])

                if headerline:
                    header = dlist[0]
                    print(f'{k},final_cols,__val__')
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
                            print(f'{id},{resultcolname},')
                        else:
                            y = np.abs(np.fft.rfft(targetcol))

                            mean = y.dot(np.arange(len(y)))/y.sum()

                            # output cleanup goes here
                            if (mean is None) or (mean == '') or (mean ==  'None'):
                                # print empty string
                                print(f'{id},{resultcolname},')
                            else:
                                if np.isfinite(float(mean)):
                                    print(f'{id},{resultcolname},{mean:.{precision}g}')
                                else:
                                    print(f'{id},{resultcolname},')

            sys.__stdout__.flush()#not needed for bigger data

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)
                
    def feature_frequencyvar(self, subcmd, args, common_args):
        '''
        calculate frequencyvariance
        '''
        # body of this method adapted from:
        # github.com/nysol/nysol_python/blob/master/scripts/sample/mkfeature.py
        try:
            import math
            import numpy as np

            print(args, file = sys.stderr)

            f = args.get('f')
            x = args.get('x')
            k = common_args.get('k')
            precision = common_args.get('precision')
            
            resultcolname = self.generateFinalColName(args, common_args)

            headerline = True

            for dlist in nm.mstdin().keyblock(f'{k}', f'{x}%n', header = True):
                id = ','.join(dlist[0][:len(k.split(','))])

                if headerline:
                    header = dlist[0]
                    print(f'{k},final_cols,__val__')
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
                            print(f'{id},{resultcolname},')
                        else:
                            y = np.abs(np.fft.rfft(targetcol))

                            mean = y.dot(np.arange(len(y)))/y.sum()

                            moment2 = y.dot(np.arange(len(y))**2)/y.sum()
                            variance = moment2 - mean ** 2

                            # output cleanup goes here
                            if (variance is None) or (variance == '') or (variance ==  'None'):
                                # print empty string
                                print(f'{id},{resultcolname},')
                            else:
                                if np.isfinite(float(variance)):
                                    print(f'{id},{resultcolname},{variance:.{precision}g}')
                                else:
                                    print(f'{id},{resultcolname},')

            sys.__stdout__.flush()#not needed for bigger data

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def feature_firstmin(self, subcmd, args, common_args):
        '''
        calculate feature firstmin
        '''
        fld = args.get('f')
        x = args.get('x')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)

        msum = nm.msummary(c = 'min:_mintime,range:_timerange', k = k, f = x, 
                             i = subcmd)

        subcmd <<= nm.mbest(k = k, s = f'{fld}%n,{x}%n')

        subcmd <<= nm.mjoin(k = k, m = msum, f = f'_mintime,_timerange')
        subcmd <<= nm.mcal(c = f'(${{{x}}}-${{_mintime}})/${{_timerange}}', 
                           a = '__val__', precision = precision)

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    def feature_firstmax(self, subcmd, args, common_args):
        '''
        calculate feature firstmax
        '''
        fld = args.get('f')
        x = args.get('x')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)

        msum = nm.msummary(c = 'min:_mintime,range:_timerange', k = k, f = x, 
                             i = subcmd)

        subcmd <<= nm.mbest(k = k, s = f'{fld}%nr,{x}%n')

        subcmd <<= nm.mjoin(k = k, m = msum, f = f'_mintime,_timerange')
        subcmd <<= nm.mcal(c = f'(${{{x}}}-${{_mintime}})/${{_timerange}}', 
                           a = '__val__', precision = precision)

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    def feature_lastmin(self, subcmd, args, common_args):
        '''
        calculate feature lastmin
        '''
        fld = args.get('f')
        x = args.get('x')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)

        msum = nm.msummary(c = 'min:_mintime,range:_timerange', k = k, f = x, 
                             i = subcmd)

        subcmd <<= nm.mbest(k = k, s = f'{fld}%n,{x}%nr')

        subcmd <<= nm.mjoin(k = k, m = msum, f = f'_mintime,_timerange')
        subcmd <<= nm.mcal(c = f'(${{{x}}}-${{_mintime}})/${{_timerange}}', 
                           a = '__val__', precision = precision)

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    def feature_lastmax(self, subcmd, args, common_args):
        '''
        calculate feature lastmin
        '''
        fld = args.get('f')
        x = args.get('x')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)

        msum = nm.msummary(c = 'min:_mintime,range:_timerange', k = k, f = x, 
                             i = subcmd)

        subcmd <<= nm.mbest(k = k, s = f'{fld}%nr,{x}%nr')

        subcmd <<= nm.mjoin(k = k, m = msum, f = f'_mintime,_timerange')
        subcmd <<= nm.mcal(c = f'(${{{x}}}-${{_mintime}})/${{_timerange}}', 
                           a = '__val__', precision = precision)

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    def feature_longeststrikeabovemean(self, subcmd, args, common_args):
        '''
        calculate feature longest strike above mean
        '''
        fld = args.get('f')
        x = args.get('x')
        k = common_args.get('k')

        resultcolname = self.generateFinalColName(args, common_args)

        msum = nm.msummary(k = k, f = fld, c = 'mean:__mean', i = subcmd)

        subcmd <<= nm.mnjoin(m = msum, k = k, f = '__mean')

        subcmd <<= nm.msortf(f = f'{k},{x}%n')
        subcmd <<= nm.mcal(c = f'${{__mean}}<=${{{fld}}}', a = '__above')
        subcmd <<= nm.mcount(q = True, k = f'{k},__above', a = '__a_count')
        subcmd <<= nm.mbest(k = k, s = '__above%nr,__a_count%nr', size = 1)
        subcmd <<= nm.mcal(c = 'if(${__above}==0,0,${__a_count})', a = '__val__')

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    def feature_longeststrikebelowmean(self, subcmd, args, common_args):
        '''
        calculate feature longest strike below mean
        '''
        fld = args.get('f')
        x = args.get('x')
        k = common_args.get('k')

        resultcolname = self.generateFinalColName(args, common_args)

        msum = nm.msummary(k = k, f = fld, c = 'mean:__mean', i = subcmd)

        subcmd <<= nm.mnjoin(m = msum, k = k, f = '__mean')

        subcmd <<= nm.msortf(f = f'{k},{x}%n')
        subcmd <<= nm.mcal(c = f'${{__mean}}>=${{{fld}}}', a = '__below')
        subcmd <<= nm.mcount(q = True, k = f'{k},__below', a = '__b_count')
        subcmd <<= nm.mbest(k = k, s = '__below%nr,__b_count%nr', size = 1)
        subcmd <<= nm.mcal(c = 'if(${__below}==0,0,${__b_count})', a = '__val__')

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd
    
    # ２つの変数に対する特徴量（パラメータあり）
    def feature_autocorrelation(self, subcmd, args, common_args):
        '''
        calculate feature autocorr
        '''
        fld = args.get('f')
        n = args.get('n')
        x = args.get('x')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)

        msum = nm.msummary(i = subcmd, k = k, f = fld,
                            c = f'mean:__mean,var:__var,count:__count')

        subcmd <<= nm.mjoin(m = msum, k = k,
                f = 'fld,__mean,__var,__count')

        subcmd <<= nm.mslide(k = k, s = f'{x}%n', t = n, l = True, 
                                f = f'{fld}:__{fld}_L')
        subcmd <<= nm.mcal(c = f'(${{{fld}}}-${{__mean}})*(${{__{fld}_L}}-${{__mean}})', a = f'__{fld}_m')
        subcmd <<= nm.msum(k = k, f = f'__{fld}_m')
        subcmd <<= nm.msetstr(a = '__lag', v = n)
        subcmd <<= nm.mcal(a = '__val__', precision = precision,
            c = f'${{__{fld}_m}}/(${{__count}}-${{__lag}})/${{__var}}')

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd

    def feature_crossingm(self, subcmd, args, common_args):
        '''
        calculate feature crossing_m
        '''
        fld = args.get('f')
        n = args.get('n')
        x = args.get('x')
        k = common_args.get('k')

        resultcolname = self.generateFinalColName(args, common_args)

        subcmd <<= nm.mcal(c = f'${{{fld}}}>{n}', a = '__pos')
        subcmd <<= nm.mslide(k = k, s = f'{x}%n', f = '__pos:__posN')
        subcmd <<= nm.mcal(c = '${__pos}!=${__posN}', a = '__diffT')
        subcmd <<= nm.mcount(k = k + ',__diffT', a = '__cnt')
        subcmd <<= nm.mbest(k = k, s = '__diffT%nr', size = 1)
        subcmd <<= nm.mcal(c = 'if(${__diffT}==0,0,${__cnt})', a = '__val__')

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd
    
    def feature_peaks(self, subcmd, args, common_args):
        '''
        calculate feature peaks
        '''
        fld = args.get('f')
        n = args.get('n')
        x = args.get('x')
        k = common_args.get('k')

        resultcolname = self.generateFinalColName(args, common_args)

        
        mslide = nm.mslide(k = k, s = f'{x}%n', t = n, r = True, 
                                f = f'{fld}:{fld}_up_', i = subcmd)

        subcmd <<= nm.mslide(k = k, s = f'{x}%n', t = n,
                                    f = f'{fld}:{fld}_down_')
        
        subcmd <<= nm.mjoin(k = f'{k},{x}', f = f'{fld}_up_*',
                                m = mslide, n = True)
        subcmd <<= nm.mcal(c = f'max(${{{fld}_up*}},${{{fld}_down_*}})',
                                a = '__rollmax__')
        subcmd <<= nm.mcal(c = f'${{{fld}}}>${{__rollmax__}}',
                                a = '__val__')

        subcmd <<= nm.msum(k = k, f = '__val__')

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd
    
    def feature_imq(self, subcmd, args, common_args):
        '''
        calculate feature imq
        '''
        fld = args.get('f')
        n = args.get('n')
        x = args.get('x')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)

        mcal = None 
        sumabs = None
        
        mcal <<= nm.mcal(c = f'abs(${{{fld}}})', a = f'__abs{fld}', i = subcmd)
        sumabs <<= mcal.msum(k = k, f = f'__abs{fld}')

        msum = nm.msummary(i = subcmd, k = k, f = fld, c = 'count:__count')

        subcmd_o = nm.maccum(k = k, s = f'{x}%n', f = f'__abs{fld}:__abs{fld}_a', 
                               i = mcal)
        subcmd_o <<= nm.mjoin(k = k, f = f'__abs{fld}:__abs{fld}_ttl', m = sumabs)
        subcmd_o <<= nm.mjoin(k = k, f = f'__count', m = msum)
        subcmd_o <<= nm.mcal(c = f'(${{__abs{fld}_a}}/${{__abs{fld}_ttl}})>={n}',
                              a = '__mc')
        subcmd_o <<= nm.mbest(k = k, s = f'__mc%nr,{x}%n', size = 1)
        subcmd_o <<= nm.mcal(c = f'(${{{x}}})/${{__count}}', a = '__val__', 
                             precision = precision)

        subcmd_o <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd_o <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd_o

    def feature_(self, subcmd, args, common_args):
        '''
        template for feature funcs
        '''
        fld = args.get('f')
        n = args.get('n')
        x = args.get('x')
        k = common_args.get('k')
        precision = common_args.get('precision')

        resultcolname = self.generateFinalColName(args, common_args)

        subcmd <<= nm.msetstr(v = resultcolname, a = 'final_cols')

        subcmd <<= nm.mcut(f = f'{k},final_cols,__val__')

        return subcmd
        

    def run(self, args, inputs):
        # debug flag
        self.DEBUG = True
        
        # first off, make copies of the inputs
        args = copy.deepcopy(args)
        inputs = copy.deepcopy(inputs)
        
        # TODO fix tmpfile handling
        initialfile = Tmp.create_file()
        # run everything up til now, and then save into the file
        self.dumpToFile(inputs['i'].content, initialfile)

        # ヘッダ行を取得する
        cmd = nm.m2tee(i = initialfile.as_posix())
        cmd = self.wrapFlow(cmd)
        self.header = self.get_field_names(cmd)

        cmd = nm.m2tee(i = initialfile.as_posix())

        # parse the inputs
        all_calcs, common_args = self.parseArgs(args)

        # if manual_key is False, make new key column 
        manual_key = common_args.get('manual_k')
        if not manual_key:
            cmd <<= nm.mcal(a = common_args['k'], c = '"all"')
        
        # convert null values in key to UUID 
        tmp_key = '!!' + str(uuid.uuid4())
        cmd <<= nm.mnullto(f = common_args['k'], v = tmp_key)
        
        # take only required columns
        relevant_cols = set(common_args['k'].split(','))
        for calc in all_calcs:
            if 'f' in calc:
            #     relevant_cols.add(calc['fld'])
            # else:
                for fld in calc['f'].split(','):
                    relevant_cols.add(fld)

            if 'x' in calc:
                for x in calc['x'].split(','):
                    relevant_cols.add(x)

        cmd <<= nm.mcut(f = list(relevant_cols))
        
        # TODO fix tmpfile handling
        tmpfile = Tmp.create_file()
        self.dumpToFile(cmd, tmpfile)
        
        
        # schedule the batches and calculations
        # get list of tmpfiles made per batch
        batches = self.run_batches(tmpfile, all_calcs, common_args)

        # combine all batches
        cmd = nm.m2tee(i = batches)

        # cross
        cmd <<= nm.mcross(f = '__val__', s = 'final_cols', k = common_args['k'])
        cmd <<= nm.mcut(r = True, f = 'fld')

        # cross reference with original key columns (join)
        # get original key columns
        keys = None
        keys <<= nm.m2tee(i = tmpfile.as_posix())
        keys <<= nm.mcut(f = common_args['k'])
        keys <<= nm.muniq(k = common_args['k'])

        # join original keys with current
        cmd_out = None
        cmd_out <<= nm.mnjoin(i = keys, k = common_args['k'], m = cmd, N = True)
        
        # TODO revert tmp_key back to null
        cmd_out <<= nm.mchgstr(f = common_args['k'], c = f'{tmp_key}:', F = True)
        

        cmd_out = self.wrapFlow(cmd_out)
        
        return {'o' : cmd_out}