# 独自コマンド
import sys
import copy
import fnmatch as fn
from pathlib import Path
import nysol.mcmd as nm

from streamcat.core import Command, Port
from streamcat.store import (
    NysolModule,
    FieldForbiddenCharacterException,
    EmptyFieldException,
    FieldConflictException,
    FieldNotFoundException,
    ColumnNameException
)

PCMD_DIR = Path(__file__).resolve().parent


class PCommand(Command):
    """
    独自コマンドのスーパークラス
    TODO: そういえばいつから独自コマンドはpcmdに。。。？
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'mcmd')]
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
        from streamcat.depo.std.commands import FieldNamesCommand
        fldNamesCmd = FieldNamesCommand()
        results = fldNamesCmd.run(args={}, inputs={'fld': nysol_module})
        # 'fld'キーへの入力結果は'fld'キーを指定して取得する
        return results['fld'].datum

    def do_runs(self, nysol_module):
        from streamcat.depo.std.commands import RunsCommand
        runs_cmd = RunsCommand()
        results = runs_cmd.run(args={}, inputs={'pcmd': nysol_module})
        # 'pcmd'キーへの入力結果は'pcmd'キーを指定して取得する
        return results['pcmd'] 

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
    errormessages = {
        # キー列に対するエラー
        'FieldNotFoundError' : '指定した項目名は存在しません。${fieldinput}',
    }
    
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'mcmd')]
        self.o_ports = [Port('o', 'mcmd')]

    def const(self, s):
        if s == 'commandname':
            return '項目順の変更'
        elif s == 'errmsgs':
            return {
                'NoInputError' : '同時に２つの指定欄を省略することはできません。'
            }
         
    def expand_wild_cards(self, to_expand):
        """
        takes a comma separated string and parses wildcard expressions within.
        
        """
        expanded = []
        
        for elem in to_expand.split(','):
            pattern = elem.translate(str.maketrans({'[':'[[]', 
                                                    ']':'[]]'}))

            matched = fn.filter(self.header, pattern)
            
            if not matched:
                # notfound error
                return {'error': 'FieldNotFoundError',
                        'unmatched' : pattern}
            
            expanded.extend(matched)
                    
        
        return expanded

    def contains_any(self, exp, str):
        return any(char in exp for char in str)

    def generate_command_error_message(self, error_type, mistaken_input = '', command_name = '', option_id = ''):
        msg = ''
        if command_name != '':
            msg += f'【コマンド：{command_name}】'
        if option_id != '':
            msg += f'【オプションID：{option_id}】'

        msg += self.const('errmsgs')[error_type]
        
        if mistaken_input == '':
            msg += mistaken_input
        
        return msg

    def run(self, args, inputs):
        f = inputs['i'].content

        self.header = self.get_field_names(inputs['i'])

        _args = copy.deepcopy(args)
        
        _left = _args.get('head')
        _right = _args.get('tail')
        
        if _left:
            for col in _left.split(','):
                if self.contains_any(col, ':%&\\'):
                    raise FieldForbiddenCharacterException(col,
                                                           command_name = self.const('commandname'),
                                                           option_id = 'head')

            _left_list = self.expand_wild_cards(_left)
            if type(_left_list) == dict:
                raise FieldNotFoundException(_left,
                                            command_name = self.const('commandname'),
                                            option_id = 'head')

            if len(_left_list) != len(set(_left_list)):
                raise FieldConflictException(_left,
                                            command_name = self.const('commandname'),
                                            option_id = 'head')
        else:
            _left_list = []
            
            
            
        if _right:
            for col in _right.split(','):
                if self.contains_any(col, ':%&\\'):
                    raise FieldForbiddenCharacterException(col,
                                                           command_name = self.const('commandname'),
                                                           option_id = 'tail')

            _right_list = self.expand_wild_cards(_right)
            if type(_right_list) == dict:
                raise FieldNotFoundException(_right,
                                            command_name = self.const('commandname'),
                                            option_id = 'tail')
            
            if len(_right_list) != len(set(_right_list)):
                raise FieldConflictException(_left,
                                            command_name = self.const('commandname'),
                                            option_id = 'tail')
        else:
            _right_list = []

        
        # if overlap, error
        if _left and _right:
            for col in _left_list:
                if col in _right_list:
                    raise FieldConflictException(col,
                                                command_name = self.const('commandname'),
                                                option_id = 'head, tail')
        
        if (not _left) and (not _right):
            err = self.generate_command_error_message('NoInputError',
                                                  command_name = self.const('commandname'),
                                                  option_id = 'head, tail')
            raise ColumnNameException(err)

        _middle = [col for col in self.header if col not in _left_list + _right_list] 
        _final = _left_list + _middle + _right_list
        f <<= nm.mcut(f = _final)

        nysol_module_o = NysolModule()
        nysol_module_o.set_content(f)
        return {'o': nysol_module_o}


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
    def const(self, s):
        if s == 'commandname':
            return '重複行の抽出'
    
    def __init__(self):
        super().__init__()

    def expand_wild_cards(self, to_expand):
        """
        takes a comma separated string and parses wildcard expressions within.
        
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
                return {'error': 'FieldNotFoundError',
                        'unmatched' : elem}
        
        return expanded

    def contains_any(self, exp, str):
        """
        check for presence of any char in str from input exp. 
        Returns True if anything exists
        """
        return any(char in exp for char in str)

    def run(self, args, inputs):

        COLNUM = '__RowNo_BeginWith1__'
        DUPCOUNT = '__dup_total__'
        DUPNUM = '__dup_no__'
        
        targetcols = args.get('k')
        
        # error checks go here:
        self.header = self.get_field_names(inputs['i'])
        targets_list = []

        if targetcols is None:
            raise EmptyFieldException(command_name = self.const('commandname'), 
                                        option_id = 'k')
            
        for col in targetcols.split(','):
            expanded_list = self.expand_wild_cards(targetcols)

            # ForbiddenCharacterError
            if self.contains_any(col, ':%&\\'):
                raise FieldForbiddenCharacterException(col,
                                                       command_name = self.const('commandname'),
                                                       option_id = 'k')
            
            # check if expandWildCards returned a dict (error signature)
            if type(expanded_list) == dict:
                raise FieldNotFoundException(expanded_list['unmatched'], 
                                            command_name = self.const('commandname'),
                                            option_id = 'k')
                                            
            # FieldConflictError
            if col in targets_list:
                raise FieldConflictException(col,
                                            command_name = self.const('commandname'),
                                            option_id = 'k')
            else:
                targets_list.append(col)
                
        
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
        self.i_ports = [Port('i', 'mcmd')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        """
        実際実行(for override)
        """
        pass


class MultiMcalCommand(PCommand):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'mcmd')]
        self.o_ports = [Port('o', 'mcmd')]

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
        self.i_ports = [Port('i', 'mcmd')]
        self.o_ports = [Port('o', 'mcmd')]

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
        self.i_ports = [Port('i', 'mcmd')]
        self.o_ports = [Port('o', 'mcmd')]

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
        self.i_ports = [Port('i', 'mcmd')]
        self.o_ports = [Port('o', 'mcmd')]

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
    
    def const(self, s):
        if s == 'commandname':
            return '複数の移動窓の類似度の計算'
        elif s == 'errmsgs':
            return {
                
                # キー列に対するエラー
                'KeyConflictError' : '項目名が重複しています。${fieldinput}',
                'KeyNumberConflictError' : '項目番号が重複しています。${fieldinput}',
                'KeyNumberSettingError' : 'キー項目番号の指定は正しくありません。${fieldinput}',
                'KeyFieldNotFoundError' : '指定した項目名は存在しません。${fieldinput}',
                'KeyFieldNumberNotFoundError' : '指定した項目番号は存在しません。${fieldinput}',
                'EmptyKeyFieldError' : '空文字列でキー項目名が指定されています。${fieldinput}',
                'KeyFieldForbiddenCharacterError' : '半角の :　\　&　％　＃ は、キー項目の指定に使用できません。${fieldinput}',
                
                # ソート設定に対するエラー
                'SortFieldConflictError' : '項目名が重複しています。${fieldinput}',
                'SortFieldNumberConflictError' : '項目番号が重複しています。${fieldinput}',
                'SortFieldNumberSettingError' : 'ソート項目番号の指定は正しくありません。${fieldinput}',
                'SortFieldNotFoundError' : '指定した項目名は存在しません。${fieldinput}',
                'SortFieldNumberNotFoundError' : '指定した項目番号は存在しません。${fieldinput}',
                'SortFieldForbiddenCharacterError': '半角の :　\　&　＃ は、ソートの項目名の指定に使用できません。${fieldinput}',
                'EmptySortFieldError' : '空文字列でソートが指定されています。${fieldinput}',
                'SortFieldOrderError' : 'ソート順の指定は正しくありません。指定可能なのは、（%n、%r、%nr）です。${fieldinput}',
                
                # 結果列名設定に対するエラー
                'EmptyResultsColNameError' : '空文字列で結果項目名が指定されてます。${fieldinput}',
                'ResultsColNameForbiddenCharacterError': '半角の :　\　,　*　?　[　] は、結果項目名の指定に使用できません。${fieldinput}',
                
                # 計算対象列に対するエラー
                'Target1FieldNotFoundError' : '指定した項目名は存在しません。${fieldinput}',
                'Target1FieldNumberNotFoundError' : '指定した項目番号は存在しません。${fieldinput}',
                'Target1MultipleFieldError' : '１つ目の計算対象項目指定で、複数の項目名を指定できません。${fieldinput}',
                'Target1MultipleFieldNumberError' : '１つ目の計算対象項目指定で、複数の項目番号を指定できません。${fieldinput}',
                'Target1ForbiddenCharacterError' : '半角の :　\　&　％　＃ は、計算対象項目の指定に使用できません。${fieldinput}',
                'Target1FieldNumberSettingError' : '計算対象項目番号の指定は正しくありません。${fieldinput}',
                'Target1EmptyError' : '空文字列で計算対象項目が指定されています。${fieldinput}',
                
                'Target2ConflictError' : '項目名が重複しています。${fieldinput}',
                'Target2FieldNotFoundError' : '指定した項目名は存在しません。${fieldinput}',
                'Target2FieldNumberNotFoundError' : '指定した項目番号は存在しません。${fieldinput}',
                'Target2FieldNumberSettingError' : '計算対象項目番号の指定は正しくありません。${fieldinput}',
                'Target2ForbiddenCharacterError' : '半角の :　\　&　％　＃ は、計算対象項目の指定に使用できません。${fieldinput}',
                'Target2EmptyError' : '空文字列で計算対象項目が指定されています。${fieldinput}',
                
                # 類似度指定に対するエラー
                'SimConflictError': '類似度が重複しています。${fieldinput}',
                'SimNotFoundError' : '${fieldinput} は、有効な類似度指定子ではありません。',
                'SimEmptyError' : '空文字列で類似度が指定されています。${fieldinput}',
                
                # 期間数指定に対するエラー
                'WindowSizeConflictError' : '対象行数が重複しています。${fieldinput}',
                'WindowSizeFormatError' : '対象行数への ${fieldinput} 指定が正しくありません。２以上の整数を指定してください。',
                'WindowSizeValueError' : '対象行数への ${fieldinput} 指定が正しくありません。２以上の整数で指定してください。',
                'WindowSizeEmptyError' : '空文字列で対象行数が指定されています。${fieldinput}。',

                # 結果列重複エラー
                'ResultsColConflictError' : '出力項目名が重複しています。%指定、&指定、#指定、ワ。ルドカード指定など、重複する出力項目名となる設定がないかを、確認してください。${fieldinput}',
                
                
                'TestError' : 'This is a test'
            }
    
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'mcmd')]
        self.o_ports = [Port('o', 'mcmd')]
        

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

    def number_exp_is_valid(self, exp):
        allowed = set('0123456789-L')
        return set(exp) <= allowed
    
    def number_exp_out_of_range(self, exp):
        keynums = exp.strip('L').split('-')
        for num in keynums:
            if int(num) > len(self.header):
                return True
        
        return False

    def contains_any(self, exp, str):
        return any(char in exp for char in str)

    # def generateCommandErrorMessage(self, *args):
    #     # とりあえず、エラー処理機能は特徴量の計算のコマンドの実装を参照する
    #     # TODO：　親コマンドレベルに機能の実装を移動する
    #     errhandler = GroupBy2Command()
    #     errhandler.commandname = self.commandname
    #     errhandler.errormessages = self.errormessages

    #     return errhandler.generateCommandErrorMessage(*args)

    def generate_command_error_message(self, error_type, option_id = '', mistaken_input = '', command_name = ''):
        from string import Template

        command_name = self.const('commandname')
        
        msg =  f'【コマンド：{command_name}】'
        msg += f'【オプションID：{option_id}】'

        template = self.const('errmsgs')[error_type]

        template_strings = {'fieldinput' : mistaken_input}

        msg += Template(template).safe_substitute(template_strings)
        
        return msg

    def run(self, args, inputs):
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
                    if not self.number_exp_is_valid(key):
                        errmsg = self.generate_command_error_message('KeyNumberSettingError', 'k', key)
                        raise Exception(errmsg)
                    
                    if key == '':
                        errmsg = self.generate_command_error_message('EmptyKeyFieldError', 'k', key)
                        raise Exception(errmsg)

                    if self.number_exp_out_of_range(key):
                        errmsg = self.generate_command_error_message('KeyFieldNumberNotFoundError', 'k', key)
                        raise Exception(errmsg)
                    
                if len(k_list) != len(set(k_list)):
                    errmsg = self.generate_command_error_message('KeyNumberConflictError', 'k', k)
                    raise Exception(errmsg)
                
            else:
                if len(k_list) != len(set(k_list)):
                    errmsg = self.generate_command_error_message('KeyConflictError', 'k', k)
                    raise Exception(errmsg)
                
                for key in k_list:
                    # forbidden characters
                    if self.contains_any(key, ':\\%&#'):
                        errmsg = self.generate_command_error_message('KeyFieldForbiddenCharacterError', 'k', key)
                        raise Exception(errmsg)
                    
                    if key == '':
                        errmsg = self.generate_command_error_message('EmptyKeyFieldError', 'k', key)
                        raise Exception(errmsg)
                        
                    if key not in self.header:
                        errmsg = self.generate_command_error_message('KeyFieldNotFoundError', 'k', key)
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
                    errmsg = self.generate_command_error_message('EmptySortFieldError', 's', s_opt)
                    raise Exception(errmsg)

                if xoption:
                    if not self.number_exp_is_valid(parts[0]):
                        errmsg = self.generate_command_error_message('SortFieldNumberSettingError', 's', s_opt)
                        raise Exception(errmsg)
                    
                    if self.number_exp_out_of_range(parts[0]):
                        errmsg = self.generate_command_error_message('SortFieldNumberNotFoundError', 's', s_opt)
                        raise Exception(errmsg)
                else:
                    if self.contains_any(parts[0], ':\\&#'):
                        errmsg = self.generate_command_error_message('SortFieldForbiddenCharacterError', 's', s_opt)
                        raise Exception(errmsg)
                        
                    if parts[0] not in self.header:
                        errmsg = self.generate_command_error_message('SortFieldNotFoundError', 's', s_opt)
                        raise Exception(errmsg)
                
                if len(parts) > 1:
                    if parts[1] not in ['', 'n', 'r', 'nr']:
                        errmsg = self.generate_command_error_message('SortFieldOrderError', 's', s_opt)
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
                    errmsg = self.generate_command_error_message('SortFieldConflictError', 's', s_opt)
                else:
                    errmsg = self.generate_command_error_message('SortFieldNumberConflictError', 's', s_opt)
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
            
            if self.contains_any(output_rule, ':\\,*?[]'):
                errmsg = self.generate_command_error_message('ResultsColNameForbiddenCharacterError', 'a', output_rule)
                raise Exception(errmsg)
                
        except KeyError:
            errmsg = self.generate_command_error_message('EmptyResultsColNameError', 'a')
            raise Exception(errmsg)
        
        
        for arglist in _args.pop('fctlist'):
            f1 = arglist.get('f1')
            
            if not f1:
                errmsg = self.generate_command_error_message('Target1EmptyError', 'f1', f1)
                raise Exception(errmsg)
                
            if xoption:
                if 'L' in f1:
                    f1_loc = len(self.header) - int(f1.strip('L')) - 1
                elif self.contains_any(f1, '-,'):
                    errmsg = self.generate_command_error_message('Target1MultipleFieldNumberError', 'f1', f1)
                    raise Exception(errmsg)
                else:
                    if self.number_exp_is_valid(f1):
                        f1_loc = int(f1)
                    else:
                        errmsg = self.generate_command_error_message('Target1FieldNumberSettingError', 'f1', f1)
                        raise Exception(errmsg)
                    
                try:
                    f1_name = self.header[f1_loc]
                except IndexError:
                    errmsg = self.generate_command_error_message('Target1FieldNumberNotFoundError', 'f1', f1)
                    raise Exception(errmsg)                
            else: 
                if self.contains_any(f1, ',?*[]'):
                    errmsg = self.generate_command_error_message('Target1MultipleFieldError', 'f1', f1)
                    raise Exception(errmsg)
                    
                if self.contains_any(f1, ':\\&%#'):
                    errmsg = self.generate_command_error_message('Target1ForbiddenCharacterError', 'f1', f1)
                    raise Exception(errmsg)
                
                if f1 not in self.header:
                    errmsg = self.generate_command_error_message('Target1FieldNotFoundError', 'f1', f1)
                    raise Exception(errmsg)
                
                
                f1_name = f1
            
            f2s = arglist.get('f2')
            f2_list = f2s.split(',')
            
            if '' in f2_list:
                errmsg = self.generate_command_error_message('Target2EmptyError', 'f2', f2s)
                raise Exception(errmsg)
            
            if self.contains_any(f2s, ':\\&%#'):
                errmsg = self.generate_command_error_message('Target2ForbiddenCharacterError', 'f2', f2s)
                raise Exception(errmsg)
            
            if len(f2_list) != len(set(f2_list)):
                errmsg = self.generate_command_error_message('Target2ConflictError', 'f2', f2s)
                raise Exception(errmsg)
            
            if xoption:
                # parse number expression
                targets = []
                for f in f2_list:
                    if not self.number_exp_is_valid(f):
                        errmsg = self.generate_command_error_message('Target2FieldNumberSettingError', 'f2', f)
                        raise Exception(errmsg)
                        
                    f = self.parse(f)
                    targets += list(f) if type(f) is range else [f]

                try:
                    f2cols = [(num,self.header[num]) for num in targets]
                except IndexError:
                    errmsg = self.generate_command_error_message('Target2FieldNumberNotFoundError', 'f2', f2s)
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
                        errmsg = self.generate_command_error_message('Target2FieldNotFoundError', 'f2', elem)
                        raise Exception(errmsg)
                
                
            ops = arglist.get('c')
            op_list = ops.split(',')
            
            allowed_ops = ['covar', 'ucovar', 'pearson', 'spearman', 'kendall', 
                           'euclid', 'cosine', 'cityblock', 'hamming', 'chi', 
                           'phi', 'jaccard', 'support', 'lift']
            
            if '' in op_list:
                errmsg = self.generate_command_error_message('SimEmptyError', 'c', ops)
                raise Exception(errmsg)
                
            for op in op_list:
                if op not in allowed_ops:
                    errmsg = self.generate_command_error_message('SimNotFoundError', 'c', op)
                    raise Exception(errmsg)
            
            if len(op_list) != len(set(op_list)):
                errmsg = self.generate_command_error_message('SimConflictError', 'c', ops)
                raise Exception(errmsg)
            
                
            
            ts = arglist.pop('t')
            ts_list = ts.split(',')
            
            if '' in ts_list:
                errmsg = self.generate_command_error_message('WindowSizeEmptyError', 't', ts)
                raise Exception(errmsg)
            
            if len(ts_list) != len(set(ts_list)):
                errmsg = self.generate_command_error_message('WindowSizeConflictError', 't', ts)
                raise Exception(errmsg)
            
            for t in ts_list:
                
                try:
                    _t = float(t)
                    
                    if (not _t.is_integer()) or (_t < 2):
                        errmsg = self.generate_command_error_message('WindowSizeValueError', 't', t)
                        raise Exception(errmsg)
                    
                except ValueError:
                    errmsg = self.generate_command_error_message('WindowSizeFormatError', 't', t)
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
            errmsg = self.generate_command_error_message('ResultsColConflictError', 'a, c, f1, f2, t')
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
        self.i_ports = [Port('i', 'mcmd')]
        self.o_ports = [Port('o', 'mcmd')]  

    def run(self, args, inputs):
        def filter(args):
            try:
                from streamcat.depo.std.commands.pcmd.src import plaintext2csv 
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
        self.i_ports = [Port('i', 'mcmd')]
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
        self.i_ports = [Port('i', 'mcmd')]
        self.o_ports = [Port('o', 'mcmd')]

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

class RowRandomCommand(Command):
    """
    無作為に行を抽出する
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'mcmd')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        def filter(size):
            import random
            try:
                # ヘッダ行を出力する
                header = sys.stdin.readline()
                print(header, end='')

                # 無作為に行を抽出しバッファメモリに格納する
                # NOTE: https://stackoverflow.com/a/232248/624900
                buffer = []
                line_num = 0
                for line in sys.stdin:
                    n = line_num + 1.0
                    if n <= size:
                        buffer.append(line)
                    elif random.random() < size/n:
                        loc = random.randint(0, size-1)
                        buffer[loc] = line
                    line_num += 1

                # バッファメモリを標準出力へ出力する
                for line in buffer:
                    print(line, end='')

                # flushをする
                sys.stdout.flush()
            except Exception as e:
                with open('/dev/stderr', 'w') as fpe:
                    import traceback
                    traceback.print_exc(file=fpe)
                    print(f'#ERROR# {str(e)}; RowRandomCommand; ; ; ', file=fpe)
                raise

        # 抽出行数の取得
        limit = int(args.get('limit')) if args.get('limit') else 0

        cmd = inputs['i'].content
        cmd <<= nm.runfunc(filter, size=limit)

        # pass output
        return {'o': NysolModule(cmd)}

class ConvToUtf8(Command):
    """
    入力データをUTF-8に変換する
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'mcmd')]
        self.o_ports = [Port('o', 'mcmd')]

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

class ConvEncoding(Command):
    """
    入力データを指定した文字コードと改行コードに変換する
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', ['mcmd','matrix'])]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):

        def convert_encoding(source_encoding, source_newline, target_encoding, target_newline):
            """
            指定されたファイルの文字コードと改行コードを変換する

            # errors='replace'
            # 変換できない文字があれば、
            #   UTF-8への変換の場合は�(U+FFFD)に置き換える
            #   CP932への変換の場合は?(3F)に置き換える
            """
            try:
                # 標準入力の文字コードと改行コードの指定
                with open(sys.stdin.fileno(),
                        mode='r',
                        encoding=source_encoding,
                        newline=source_newline,
                        errors='replace',
                        closefd=False) as sys_stdin:
                    # 標準入力への文字コードと改行コードの指定
                    with open(sys.stdout.fileno(),
                            mode='w',
                            encoding=target_encoding,
                            newline=target_newline,
                            errors='replace',
                            closefd=False) as sys_stdout:
                        for line in sys_stdin:
                            # 改行コードを削除する
                            line = line.rstrip(source_newline)
                            # 標準出力へ出力する
                            print(line, file=sys_stdout)
            except Exception as e:
                with open('/dev/stderr', 'w') as fpe:
                    import traceback
                    traceback.print_exc(file=fpe)

        nysol_module = inputs['i']

        if 'target_encoding' not in args:
            raise Exception('target_encodingを指定してください')
        if 'target_newline' not in args:
            raise Exception('target_newlineを指定してください')

        # flushをしないと、デバッグ用のprintなども入ってしまう
        sys.stdout.flush()

        if nysol_module.encoding is None or nysol_module.encoding == 'UNKNOWN':
            # 入力データの文字コードが未判定の場合
            # 判定してもわからなかった場合はUTF-8で試してみる
            source_encoding = 'utf-8'
            source_newline = '\n'
        else:
            source_encoding = nysol_module.encoding
            source_newline = '\r\n'

        cmd = nysol_module.content
        if source_encoding==args['target_newline'] or source_encoding=='ascii':
            target_encoding = nysol_module.encoding
        else:
            # runfuncの入力にリストを指定できないため、m2teeで入力する
            if nysol_module.type == 'matrix':
                cmd = nm.m2tee(i=cmd)
            cmd <<= nm.runfunc( convert_encoding,
                                source_encoding=source_encoding,
                                source_newline=source_newline,
                                target_encoding=args['target_encoding'],
                                target_newline=args['target_newline'])
            target_encoding = args['target_encoding']
    
        ret = NysolModule(cmd)
        ret.encoding = target_encoding
        return {'o': ret}

class AlignColumns(Command):
    """
    CSVのデータ列数をCSVヘッダの列数に揃える
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'mcmd')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        cmd = inputs['i'].content
        cmd <<= nm.runfunc(AlignColumns._align_columns)
        return {'o': NysolModule(cmd)}

    def _align_columns():
        """
        データ列数をCSVヘッダの列数に揃える
        """
        import sys
        try:

            with open(sys.stdin.fileno(), mode='r', newline='', closefd=False) as sys_stdin:
                # ヘッダ行を出力する
                header = sys_stdin.readline()
                print(header, end='')

                # ヘッダの列数を取得する
                num_columns = AlignColumns._count_columns(header)

                for line in sys_stdin:
                    # データ行をヘッダの列数に揃える
                    line = AlignColumns._align_line(line, num_columns)
                    print(line, end='')

            # flushをする
            sys.stdout.flush()
        except Exception as e:
            with open('/dev/stderr', 'w') as fpe:
                import traceback
                traceback.print_exc(file=fpe)

    def _count_columns(header):
        """
        CSV行の列数を数える
        """
        from streamcat.core import SCatBaseModel
        return len(SCatBaseModel.split(header))

    def _align_line(line, num_columns):
        """
        CSV行の列を指定列数に揃える
        """
        from streamcat.core import SCatBaseModel

        line_list = SCatBaseModel.split(line)
        len_line = len(line_list)

        if len_line == num_columns:
            return line
        elif len_line < num_columns:
            # CSV行の最後に空文字を追加する
            line_list[len_line:len_line] = [''] * (num_columns-len_line)
            # listをCSV行の文字列に変換する
            return SCatBaseModel.join(line_list)
        else:
            return AlignColumns.join(line_list[0:num_columns])

class ToListCommand(Command):
    """
    入力データをPython Listに出力する
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'mcmd')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        cmd = inputs['i'].content
        # 1行目をヘッダ扱いしない(nfn=True)
        # ヘッダ扱いすると、重複列名や空列名があるとエラーになる
        cmd <<= nm.writelist(nfn=True)

        return {'o': NysolModule(cmd)}

class ToTListCommand(Command):
    """
    入力データを[列名, 値(1行目), 値(2行目),..]の形式のPython Listに出力する
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'mcmd')]
        self.o_ports = [Port('o', 'mcmd'), Port('u', 'mcmd')]

    def run(self, args, inputs):
        import uuid

        cmd = inputs['i'].content

        # グラフ表示に不要な列を削除してメモリ使用量を低減する
        x_axises = [item['column'] for item in args.get('x_axis', []) if item['column'] is not None]
        y_axises = [item['column'] for item in args.get('y_axis', []) if item['column'] is not None]
        data_columns = args.get('data_column', [])

        # 反復波形図でのみ使用する引数
        event_columns = [args.get('event_column')] if args.get('event_column') else []
        groups = [args.get('group')] if args.get('group') else []

        # 項目名行を取得する
        # NOTE: 一回のnm.runs()実行でデータとmcut前のヘッダを取得するため、ここでデータとヘッダへ2分岐する
        cmd <<= nm.mbest(fr=0, to=sys.maxsize, q=True)
        cmd_u = cmd.redirect('u')
        cmd_u <<= nm.writelist(header=True)

        # nm.mcutは重複列名を指定するとエラーになるので、setを用いて重複列名を一つに纏める
        col_names = ','.join(set(x_axises + y_axises + data_columns + event_columns + groups)) or '*'
        cmd <<= nm.mcut(f=col_names)

        # 重複しない列名を用意する
        seq_col_name = str(uuid.uuid4())[0:8]
        # mcross後の列名重複を避けるため連番キーを付加する
        cmd <<= nm.mnumber(I=1, S=0, a=seq_col_name, e='seq', q=True)

        # hv.Dataset()は{列名 : [値,...]}の形式で入力を受付けるため行列を入れ替える
        cmd <<= nm.mcross(a='fld', f='*', s=f'{seq_col_name}%n', q=True)
        cmd <<= nm.writelist(nfn=True)

        return {'o': NysolModule(cmd), 'u': NysolModule(cmd_u)}

class ToNamedPipeCommand(Command):
    """
    名前付きパイプを作成しそこに結果を出力する
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'mcmd')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        import os
        from streamcat.store import Stream

        named_pipe = ToNamedPipeCommand._create_tmp_named_pipe()
        os.mkfifo(named_pipe)

        cmd = inputs['i'].content
        cmd <<= nm.m2tee(o=named_pipe.as_posix(), nfn=True)

        nysol_module = NysolModule(cmd)
        nysol_module.context['stream'] = Stream(named_pipe)

        return {'o': nysol_module}

    @staticmethod
    def _create_tmp_named_pipe():
        from streamcat.core import Tmp
        import uuid
        # 一意なファイル名を作成する
        file_name  = '__SCATTMP_PIPE_' + str(uuid.uuid4())[0:8]
        # TmpファイルPath
        return Tmp._get_tmp_directory() / file_name
