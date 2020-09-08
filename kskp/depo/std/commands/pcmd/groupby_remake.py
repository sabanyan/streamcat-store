import sys
import copy
import uuid
import nysol.mcmd as nm
import numpy as np
import fnmatch as fn 
import nysol.util.mtemp as mtemp

from kskp.store import NysolModule
from kskp.core import Command, Port

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
        nysol_calcs : dict of nysol calculations paired to their functions
        python_calcs: list of python calculations
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
        elif s == 'paraminfo':
            return {
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
            return {'median_ad' : None}
            # return {
            #     # 0 fields (input k, a, fld)
            #     'rows' : self.rows,
            #     # 1 field (input k, a, f)
            #     'miss' : self.missingdata,
            #     'rms' : self.rootmeansquare,
            #     'hmean' : self.harmonicmean,
            #     'gmean' : self.geometricmean,
            #     'var_gt_sd' : self.variance_larger_than_sd,
            #     'strmax' : self.strmax,
            #     'strmin' : self.strmin,
            #     'strucount' : self.strucount,
            #     'abs_energy' : self.abs_energy, 
            #     'has_dup' : self.hasduplicate,    
            #     'has_dup_max' : self.hasduplicatemin,
            #     'has_dup_min' : self.hasduplicatemax,
            #     'mean_ad' : self.meanabsolutedeviation,
            #     'median_ad' : self.medianabsolutedeviation,
            #     'repeatdata' : self.reoccurringdatapoints,
            #     'repeatvalues' : self.reoccurringvalues,
            #     'sum_repeatdata' : self.sumofreoccurringdatapoints,
            #     'sum_repeatvalues' : self.sumofreoccurringvalues,
            #     'ratio_unique' : self.ratio_value_number_to_series_length,
            #     'count_above_mean' : self.countabovemean,
            #     'count_below_mean' : self.countbelowmean,
            #     'sym_looking' : self.symmetry_looking,
            #     'large_sd' : self.large_standard_dev,
            #     'value_count' : self.value_count,
            #     'range_count' : self.range_count,
            #     'ratio_beyond_rsigma' : self.ratio_beyond_rsigma,
            #     'quantile' : self.quantile,
            #     'binned_entropy' : self.binned_entropy,
            #     # 1 field + time (input k, a, f, x)
            #     'integral' : self.integral,
            #     'meanf' : self.meanfrequency,
            #     'varf' : self.frequencyvar,
            #     'fft_agg' : self.fft_agg,
            #     'slope' : self.slope,
            #     'slope_pearson' : self.pearson,
            #     'firstmin' : self.firstmin,
            #     'firstmax' : self.firstmax,
            #     'lastmin' : self.lastmin,
            #     'lastmax' : self.lastmax,
            #     'mean_change' : self.meanchange,
            #     'mean_abs_change' : self.meanabschange,
            #     'abs_sum_changes' : self.abs_sum_of_changes, 
            #     'autocorr_agg' : self.autocorrelation_agg,
            #     'longest_strike_above_mean' : self.longeststrikeabovemean,
            #     'longest_strike_below_mean' : self.longeststrikebelowmean,
            #     'mean_second_derivative_central' : self.mean2ndderivative_central,
            #     'energy_ratio_by_chunks' : self.energy_ratio_by_chunks,
            #     # 2+1 fields
            #     'imq' : self.index_mass_quantile,
            #     'crossing_m' : self.numbercrossing,
            #     'peaks' : self.countpeaks,
            #     'autocorr' : self.autocorrelation,
            #     'c3' : self.c3,
            #     'time_reversal_asymmetry' : self.time_reversal_asymmetry,
            #     # aggregate functions
            #     'linregress' : self.linear_trend
            # }
        elif s == 'python_calcs':
            return [
                'meanf',
                'varf',
                'fft_agg'
            ]
    

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
        Takes a nysol flow object and uses m2tee to dump into a file specified
        by filepath
        '''
        flow_obj <<= nm.m2tee(o = filepath)

        nysol_module = self.wrapFlow(flow_obj)
        self.do_runs(nysol_module)

    def expandWildCards(self, to_expand):
        """
        takes a comma separated string and parses wildcard expressions within.
        
        returns a tuple (exitcode, expansion)
        code 0: executed properly, no errors
        code 1: no match in entire header (FieldNotfoundError)
        """
        exitcode = 0
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
        '''
        from string import Template

        errmsgs = self.const('errmsgs')
        commandname = self.const('commandname')
        all_param_info = self.const('paraminfo')

        if calc in all_param_info.keys():
            param_info = all_param_info[calc]
        else:
            param_info = {} 
        
        param_info['calc'] = calc
            
        template_strings = {'fieldinput' : errinput, **param_info}

        message = Template(errmsgs[errcode]).safe_substitute(template_strings)

        return f'【コマンド：{commandname}】【オプション欄：{errfield}】{message}'


    def simplifyMsummary(self, msum_list):
        '''
        takes the parsed list of msummary calculations from raw arguments, and 
        reduces it to the minimum length list
        '''
        # input: [{f: valx, c: sum, a: sum},
        #         {f: valx, c: min, a: min}, ...
        
        # initialize a dict with {colname : [operations]}
        operations = {}
         
        # first, put all the operations to the same column in one dict
        # {f : val1, c: sum:sum,min:min,max:highest} etc.
        for row in msum_list:
            c_option = f'{row["c"]}:{row["a"]}'
            targetcol = row['f']
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
        for op, target_list in reverse_dict.items():
            operation = {}
            
            target_str = ','.join(target_list)
            operation['f'] = target_str
            operation['c'] = op
            
            final_list.append(operation)
        
        return final_list

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
        # dateformat -> 'date'
        # format -> output columnnames
        # precision
        # nfno -> is this still necessary?
        
        # compile common parameters
        common_args = {}
       
        common_args['dateformat'] = raw_args.get('dateformat')
        common_args['precision'] = raw_args.get('precision')

        # error handling for common args
        # k errors

        ks = raw_args.get('k') 
        if ks:
            ks_list = ks.split(',')
            
            if self.containsAny(ks, '%&'):
                errmsg = self.generateCommandErrorMessage('KeyFieldForbiddenCharacterError', 'k', ks)
                raise Exception(errmsg)

            if len(ks_list) != len(set(ks_list)):
                errmsg = self.generateCommandErrorMessage('KeyFieldConflictError', 'k', ks)
                raise Exception(errmsg)

            if '' in ks_list:
                errmsg = self.generateCommandErrorMessage('EmptyKeyFieldError', 'k', ks)
                raise Exception(errmsg)

            # set manual k input flag
            self.manual_k = True
            common_args['k'] = ks
        
        else: # if k is empty
            ks_list = []

            # set manual k input flag
            self.manual_k = False

        # format errors
        formatstr = raw_args.get('format')

        if self.containsAny(formatstr, '*?[]'):
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
               
                fld = row.pop('fld') 
                # check if multiple flds specified
                if ',' in fld:
                    errmsg = self.generateCommandErrorMessage('MultipleRowsTargetError', 'fld', row['fld'])
                    raise Exception(errmsg)
                
                # check for newname setting
                for c in cs_list:
                    if ':' in c:
                        c, a = c.split(':')
                    else:
                        a = c 
                    
                    all_fs.add(fld)
                    
                    final_columns.append(formatstr.replace('%', a).replace('&', fld))
                    
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


                # check if any element in c requires params AND cs_list > 1
                # Multiple ParamCalc error
                for c in cs_list:
                    if (c in self.const('paraminfo')) and (len(cs_list) > 1):
                        errmsg = self.generateCommandErrorMessage('MultipleParamCalcError', 'c', cs)
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

                        # prepare one calculation dictionary
                        thiscalc = {'c' : c, 'f' : f, **row}

                        # append thiscalc to the appropriate list
                        if c in self.const('msum_calcs'):
                            msummary_calcs.append(thiscalc)
                        elif c in self.const('nysol_calcs').keys():
                            nysol_calcs.append(thiscalc)
                        elif c in self.const('python_calcs'):
                            python_calcs.append(thiscalc)
                        else: # c is not in any list, therefore does not exist
                            errmsg = self.generateCommandErrorMessage('CalcNotFoundError', 'c', c)
                            raise Exception(errmsg) 
                        
                        final_columns.append(formatstr.replace('%', a).replace('&', f))
                        
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

        
    def run(self, args, inputs):
        # set up tmp file
        # generate tmp file name
        # run everything up til now, and then save into the file

        # ヘッダ行を取得する
        self.header = self.get_field_names(inputs['i'])
        # fix the ordering here. need to figure out the best ordering to 
        # minimize the number of runs etc.

        # parse the inputs
        all_calcs, common_args = self.parseArgs(args)
        
        # is it possible to separate the parsing from the error handling?
        # maybe only some of it
        
        
        # schedule the batches and calculations
        
        cmd_out = self.wrapFlow(inputs['i'].content)
        
        return {'o' : cmd_out}