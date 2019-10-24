# 独自コマンド
import sys
import nysol.mcmd as nm
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
        f <<= inputs['i']

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
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/column_list.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}


class ColumnGroupingNameCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/column_grouping_name.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}


class ColumnBlankNameCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/column_blank_name.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}


class ColumnsToRowsCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/columns_to_rows.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}


class ColumnUniqueNameCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/column_unique_name.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}


class ColumnNameCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/column_name.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}


class GroupbyCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/groupby.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}


class GroupbyColumnsCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/groupby_columns.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}


class CheckDuplicateRowsCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/check_duplicate_rows.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}


class MergeFSCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/merge_FS.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}


class MergeIbutsuCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

        args_string = (PCMD_DIR / 'src/merge_ibutsu.sh').as_posix()
        args_string += self.replace_args(args)

        return {'o': self.module(f, args_string)}


class WinCp932ReadCommand(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        # f = None
        # f <<= inputs['i']

        # args_string = (PCMD_DIR / 'src/windows_cp932_csv_read.sh').as_posix()
        # args_string += self.replace_args(args)

        # return {'o': self.module(f, args_string)}

        # pythonによる変換
        # 不安定なので無効化しておく

        def Cp932_to_utf8():
            """
            ストリームでcp932→utf8に変換するコマンド
            """
            import traceback
            import io
        
            try:
                # stdinのencodingがデフォルトでutf-8なので、設定し直す。
                input_stream = io.TextIOWrapper(sys.stdin.buffer, encoding='cp932')
                for line in input_stream:
                    # 標準出力するときも自動でutf-8に変換されるので、printだけでいい
                    print(line, end='')
                # flushをする
                sys.stdout.flush()
            except Exception as e:
                with open('/dev/stderr', 'w') as fpe:
                    traceback.print_exc(file=fpe)
        
        # flushをしないと、デバッグ用のprintなども入ってしまう
        sys.stdout.flush()
        f = None
        f <<= inputs['i']
        f <<= nm.runfunc(Cp932_to_utf8)
        
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(f)
        
        return {'o': nysol_module_o}


class Utf8ToCp932Command(PCommand):
    def __init__(self):
        super().__init__()

    def run(self, args, inputs):
        f = None
        f <<= inputs['i']

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

class GroupBy2Command(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def rootmeansquare(self, ks, fs, a, precision):
        # k gives key fields
        # f gives target fields
        # a gives output field name

        subcmd = None
        subcmd <<= nm.mstdin()
        # mcal to square
        fs = fs.split(',')

        for f in fs:
            subcmd <<= nm.mcal(a = f'{f}_temp', c = f'${{{f}}}^2',
                               precision = precision)
            subcmd <<= nm.mcut(f = f, r = True)
            subcmd <<= nm.mfldname(f = f'{f}_temp:{f}')
        
        # msummary to sum
        subcmd <<= nm.msummary(c = 'sum,count', f = ','.join(fs), k = ks,
                               precision = precision)

        # mcal to sqrt
        subcmd <<= nm.mcal(a = a, c = 'sqrt(${sum}/${count})',
                           precision = precision)

        # mcut to remove old row
        finalcols = ','.join([ks,'fld',a])
        subcmd <<= nm.mcut(f = finalcols)

        subcmd <<= nm.mstdout()
        subcmd.run()

    def harmonicmean(self, ks, fs, a, precision):
        subcmd = None
        subcmd <<= nm.mstdin()

        fs = fs.split(',')
        for f in fs:
            subcmd <<= nm.mcal(a = f'{f}_inv', c = f'1/${{{f}}}',
                               precision = precision)
            subcmd <<= nm.mcut(f = f, r = True)
            subcmd <<= nm.mfldname(f = f'{f}_inv:{f}')

        subcmd <<= nm.msummary(c = 'sum,count', f = ','.join(fs), k = ks,
                               precision = precision)

        subcmd <<= nm.mcal(a = a, c = '${count}/${sum}', precision = precision)

        finalcols = ','.join([ks,'fld',a])
        subcmd <<= nm.mcut(f = finalcols)
        
        subcmd <<= nm.mstdout()
        subcmd.run()

    def geometricmean(self, ks, fs, a, precision):
        # positive numbers only
        subcmd = None
        subcmd <<= nm.mstdin()

        fs = fs.split(',')
        for f in fs:
            subcmd <<= nm.mcal(a = f'{f}_ln', c = f'ln(abs(${{{f}}}))',
                               precision = precision)
            subcmd <<= nm.mcut(f = f, r = True)
            subcmd <<= nm.mfldname(f = f'{f}_ln:{f}')

        subcmd <<= nm.msummary(c = 'sum,count', f = ','.join(fs), k = ks,
                               precision = precision)

        subcmd <<= nm.mcal(a = a, c = 'exp(${count}/${sum})', 
                           precision = precision)

        finalcols = ','.join([ks,'fld',a])
        subcmd <<= nm.mcut(f = finalcols)
        
        subcmd <<= nm.mstdout()
        subcmd.run()

    def frequencymean(self, ks, fs, a, precision):
        # subcmd = None
        # subcmd <<= nm.mstdin()

        # fs = fs.split(',')
        # for f in fs:
        #     subcmd <<= nm.mcal(a = f'{f}_inv', c = f'1/${{{f}}}',
        #                        precision = precision)
        #     subcmd <<= nm.mcut(f = f, r = True)
        #     subcmd <<= nm.mfldname(f = f'{f}_inv:{f}')

        # subcmd <<= nm.msummary(c = 'sum,count', f = ','.join(fs), k = ks,
        #                        precision = precision)

        # subcmd <<= nm.mcal(a = a, c = '${count}/${sum}', precision = precision)

        # finalcols = ','.join([ks,'fld',a])
        # subcmd <<= nm.mcut(f = finalcols)
        
        # subcmd <<= nm.mstdout()
        # subcmd.run()
        pass

    def meanabsolutedeviation(self, ks, fs, a, precision):
        subcmd = None
        meancalc = None

        subcmd <<= nm.mstdin()

        meancalc <<= nm.msummary(i = subcmd, k = ks, f = fs, c = 'mean')
        meancalc <<= nm.m2cross(f = 'mean', a = 'type,value', k = ks + ',fld')
        meancalc <<= nm.mcal(a = 'colnames', c = '$s{fld}+"_mean"')
        meancalc <<= nm.mcross(f = 'value', s= 'colnames', k = ks)

        flds = fs.split(',')
        fldnames = [f + '_mean' for f in flds]
        subcmd <<= nm.mjoin(k = ks, K = ks, m = meancalc, 
                            f = ','.join(fldnames), o='mjoin.csv')

        for fld in flds:
            subcmd <<= nm.mcal(a = f'{fld}_diff', 
                               c = f'abs(${{{fld}}}-${{{fld+"_mean"}}})')
            subcmd <<= nm.mcut(f = fld, r = True)
            subcmd <<= nm.mfldname(f = f'{fld}_diff:{fld}')

        subcmd <<= nm.msummary(k = ks, c = 'mean', f = fs)
        subcmd <<= nm.mfldname(f = f'mean:{a}')
        subcmd <<= nm.mstdout()
        subcmd.run()
        
    def medianabsolutedeviation(self, ks, fs, a, precision):
        subcmd = None
        meancalc = None

        subcmd <<= nm.mstdin()

        meancalc <<= nm.msummary(i = subcmd, k = ks, f = fs, c = 'median')
        meancalc <<= nm.m2cross(f = 'median', a = 'type,value', k = ks + ',fld')
        meancalc <<= nm.mcal(a = 'colnames', c = '$s{fld}+"_median"')
        meancalc <<= nm.mcross(f = 'value', s= 'colnames', k = ks)

        flds = fs.split(',')
        fldnames = [f + '_median' for f in flds]
        subcmd <<= nm.mjoin(k = ks, K = ks, m = meancalc, 
                            f = ','.join(fldnames), o='mjoin.csv')

        for fld in flds:
            subcmd <<= nm.mcal(a = f'{fld}_diff', 
                               c = f'abs(${{{fld}}}-${{{fld+"_median"}}})')
            subcmd <<= nm.mcut(f = fld, r = True)
            subcmd <<= nm.mfldname(f = f'{fld}_diff:{fld}')

        subcmd <<= nm.msummary(k = ks, c = 'median', f = fs)
        subcmd <<= nm.mfldname(f = f'median:{a}')
        subcmd <<= nm.mstdout()
        subcmd.run()
        pass


        # ## Template
        # subcmd = None
        # subcmd <<= nm.mstdin()

        # subcmd <<= nm.mstdout()
        # subcmd.run()

    def run(self, args, inputs):
        import fnmatch as fn

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

        new_calcs = {
            'rms' : self.rootmeansquare,
            'hmean' : self.harmonicmean,
            'gmean' : self.geometricmean,
            'fmean' : self.frequencymean,
            'mean_ad' : self.meanabsolutedeviation,
            'median_ad' : self.medianabsolutedeviation
            }

        self.header = nm.mread(inputs).getline(header=True)
        self.header = next(self.header)

        k = args.pop('k')

        fclist = []
        all_fs = []
        final_fs = []
        
        # wildcard parsing
        for arglist in args.pop('fclist'):
            fs = [a for a in self.header for target in arglist['f'].split(',') 
                if fn.fnmatch(a, target)]

            cs = arglist['c'].split(',')
            cs_msummary = []
            cs_custom = []

            for i,c in enumerate(cs):
                if ':' in c:
                    final_fs.append(c.split(':')[-1])
                else:
                    final_fs.append(c)
                    
                if c.split(':')[0] not in msummaryoptions:
                    cs_custom.append(cs[i])
                else:
                    cs_msummary.append(cs[i])

            if cs_msummary:
                fclist.append({'f': ','.join(fs), 'c': cs_msummary, 
                               'msummary' : True})
            for c in cs_custom:
                fclist.append({'f': ','.join(fs), 'c': c, 
                               'msummary' : False})

            all_fs += [f for f in fs if f not in all_fs]

        cmd = [None] * len(fclist)
        cmd_o = None

        cmd[-1] <<= nm.mread(inputs)
        # take the wanted columns only (the id column and the value columns)
        cmd[-1] <<= nm.mcut(f = f'{k},{",".join(all_fs)}')

        ##### calculation portion:
        expanded_k = ','.join([k,'fld'])

        for i, fcdict in enumerate(fclist):
            cs = fcdict.pop('c')
            fs = fcdict.pop('f')

            # take the required stats for the required columns
            if fcdict['msummary']:
                if i != len(fclist) - 1:
                    cmd[i] <<= nm.mread(i = cmd[-1])

                cmd[i] <<= nm.msummary(k = k, f = fs, c = cs, a = 'fld',
                        precision = args['precision'])

                cs = [c.split(':')[-1] for c in cs]
            else:
                if ':' in cs:
                    cleft, cright = cs.split(':')
                else:
                    cleft = cs
                    cright = cs

                if i != len(fclist) - 1:
                    cmd[i] <<= nm.mread(i=cmd[-1])
                    
                cmd[i] <<= nm.runfunc(new_calcs[cleft], ks = k, fs = fs, 
                                        a = cright, precision = args['precision'])
                
                cs = [cright]


            # make null columns for each missing column
            for missingcol in final_fs:
                if missingcol not in cs:
                    cmd[i] <<= nm.mcal(a = missingcol, c = 'nulls()')

        # m2cross 
        cmd_o <<= nm.m2cross(i = cmd, k = expanded_k, f= final_fs, 
                a = 'type,value')

        # type is the column listing the calculated quantities
        # value is the column with all the actual values of those quantities

        # delete rows with null values
        cmd_o <<= nm.mdelnull(f = 'value')

        formatstring = args.pop('format')
        colformat = ['']

        for char in formatstring:
            if char == '&':
                colformat.append('$s{fld}')
                colformat.append('')
            elif char == '%':
                colformat.append('$s{type}')
                colformat.append('')
            else:
                colformat[-1] += char

        for i, sub in enumerate(colformat):
            if not sub.startswith('$'):
                colformat[i] = f'"{sub}"' 
        
        # mcal to create the column of unique column names
        cmd_o <<= nm.mcal(a = 'unique_cols', c = '+'.join(colformat))

        # mcross to bring it all back
        cmd_o <<= nm.mcross(f = 'value', s = 'unique_cols', k = k)

        # mcut to remove the extra 'fld' column after mcross
        cmd_o <<= nm.mcut(r = True, f = 'fld', **args)

        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MultiMcalCommand(Command):
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

        cmd_o = None
        first = True

        aclist = args.pop('arglist')
        for acarg in aclist:
            # one mcal will be added to cmd_o for every pair of c and a arguments passed in a list

            if first:
                cmd_o <<= nm.mcal({**inputs, **acarg, **args}) # {'i' : input, 'c': 'cal1', 'a' : 'col1'}
                first = False
            else:
                cmd_o <<= nm.mcal({**acarg,**args})

        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}


class MultiMcalWCCommand(Command):
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

        cmd_o = None
        first = True

        # get header list
        self.header = nm.mread(inputs).getline(header=True)
        self.header = next(self.header)

        xoption = args.pop('x') if 'x' in args else False
        
        targs = args.pop('targets').split(',')
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
            if args['a'].replace('&',a) not in self.header]
        #targets is now a list of column names to hit with calculation

        #iterate over entire list and replace the '&' in c and a inputs with column number/name
        for target in targets_final:
            arg = args.copy()

            arg['a'] = arg['a'].replace('&', target)
            arg['c'] = arg['c'].replace('&',str(target))

            if first:
                cmd_o <<= nm.mcal({**inputs, **arg})
                first = False
            else:
                cmd_o <<= nm.mcal(arg)
        
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}
        

class MvAvgCommand(Command):
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

        cmd_o = None
        cmd_o <<= nm.mread(inputs)

        if ('s' not in args) or (args['s'] == ''):
            args['q'] = True

        xoption = args.pop('x') if 'x' in args else False

        # get index of columns
        self.header = nm.mread(inputs).getline(header=True)
        self.header = next(self.header)

        fatlist = []

        for fatargs in args.pop('fatlist'):
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

        mvavgtype = args.pop('type')
        if mvavgtype != 'simple':
            args[mvavgtype] = True
        if mvavgtype != 'exp' and 'alpha' in args:
            del args['alpha']

        # copy target  column into 'a' field
        for fatdict in fatlist:
            # arg = args.copy()

            cmd_o <<= nm.mcal(a = fatdict['a'], c = f'${{{fatdict["f"]}}}') 
            
            fatdict['f'] = fatdict.pop('a')

            # arg['t'] = fatdict['t']

            # perform mmvavg on field specified by 'a' field, with skip = 0
            cmd_o <<= nm.mmvavg({'skip': 0, **args, **fatdict})

        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}


class MvStatsCommand(Command):
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

        cmd_o = None

        cmd_o <<= nm.mread(inputs)
            
        # sorting parameters
        if 's' not in args or (args['s'] == ''):
            args['q'] = True

        # get index of columns
        self.header = nm.mread(inputs).getline(header=True)
        self.header = next(self.header)

        xoption = args.pop('x') if 'x' in args else False

        # f is a wildcard/number expression
        # a is a colname that may have & in it
        # c specifies the statistic to be taken (list not allowed)
        factlist = []
        for arglist in args.pop('factlist'):
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
            cmd_o <<= nm.mmvstats({'skip': 0, **args, **factdict})

        # pass output
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}


class MvSimCommand(Command):
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

        cmd_o = None
        cmd_o <<= nm.mread(inputs)
            
        # sorting parameters
        if 's' not in args or (args['s'] == ''):
            args['q'] = True

        # get index of columns
        self.header = nm.mread(inputs).getline(header=True)
        self.header = next(self.header)

        xoption = args.pop('x') if 'x' in args else False

        # f is a wildcard/number expression
        # a is a colname that may have & in it
        # c specifies the statistic to be taken 
        factlist = []
        for arglist in args.pop('factlist'):
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
                
            for op in ops:
                for t in ts:
                    factlist.append({'f': ','.join(colnames), 
                        'a': aexp.replace('#',t).replace('%',op), 
                        'c': op,
                        't': t})


        # factlist is now a list of dictionaries of the fact options:
        # [{'f': 'f1', 'a': 'a1', 'c': 'c1', 't':, 't1'},
        #  {'f': 'f2', 'a': 'a2', 'c': 'c2', 't':, 't2'},
        #  ...]
        for factdict in factlist:
            # arg = args.copy()

            # perform mmvsim on field specified by 'a' field, with skip = 0
            cmd_o <<= nm.mmvsim({'skip': 0, **args, **factdict})

        # pass output
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
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

        f = inputs['i']
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


class RdbLoaderCommand(Command):
    """
    指定したRDBからデータを取得するLoaderコマンド
    """
    def __init__(self):
        super().__init__()
        self.i_ports = []
        self.o_ports = [Port('o', 'mcmd')]
        self.name = 'rdb_loader'
        self._tmp_file_path = None

    def run(self, args, inputs):
        self._write_log('START')

        # RDBに接続する値を取得する
        if 'dbms' not in args:
            raise Exception('RDB種別の指定が必要です')
        dbms = args['dbms']

        if 'hostname' not in args:
            raise Exception('RDBのホスト名またはIPアドレスの指定が必要です')
        hostname = args['hostname']

        if 'port' not in args:
            raise Exception('RDB接続のポート番号の指定が必要です')
        port = args['port']  

        if 'database' not in args:
            raise Exception('RDB接続のデータベース名の指定が必要です')
        database = args['database']  

        if 'user_id' not in args:
            raise Exception('RDB接続のユーザIDが必要です')
        user_id = args['user_id'] 

        if 'password' not in args or args['password'] is None:
            password = ''
        else:
            password = args['password']

        if 'schema_name' not in args or args['schema_name'] is None:
            schema_name = ''
        else:
            schema_name = args['schema_name']

        if 'table_name' not in args:
            raise Exception('RDB接続の取得元テーブル名が必要です')
        table_name = args['table_name']

        # RDBへの接続URIを作成する
        from ...rdb_conn_info import RdbConnInfo
        connInfo = RdbConnInfo(dbms, hostname, port, database, user_id, password)

        # RDBへ接続する
        engine = RdbLoaderCommand._connect_to_rdb(connInfo)

        # SQL文を作成する
        sql = RdbLoaderCommand._make_sql(schema_name, table_name)

        # SQL文を発行し結果を取得する
        results = RdbLoaderCommand._get_results(engine, sql)

        # Tmpファイル名を決定する
        import uuid
        tmp_dir_path  = '/tmp'
        tmp_file_name = str(uuid.uuid4())
        self._tmp_file_path = tmp_dir_path + '/' + tmp_file_name + ".csv"

        # 結果をファイルに出力する
        def to_str(value):
            if value is None:
                return ''
            else:
                return str(value)

        with open(self._tmp_file_path, 'w') as f:
            is_header = True
            for result in results:
                if is_header:
                    f.write(','.join(result.keys()))
                    f.write('\n')
                    is_header = False
                str_result = map(to_str, result)
                result_line = ','.join(str_result)
                f.write(result_line + '\n')

        # 結果のファイルを入力とするm2teeコマンドを作成する
        cmd = nm.m2tee(i=self._tmp_file_path)

        nysol_module = NysolModule()
        nysol_module.set_content(cmd)
        return {'o': nysol_module}

    @staticmethod
    def _make_sql(schema_name, table_name):
        if schema_name == '':
            schema_and_table_name = table_name
        else:
            schema_and_table_name = schema_name + '.' + table_name
        return f"SELECT * FROM {schema_and_table_name}"

    @staticmethod
    def _connect_to_rdb(rdb_conn_info):
        # データベースへの接続
        from sqlalchemy import create_engine, exc
        # echo=TrueでSQLログがコンソールに出力される
        try:
            engine = create_engine(rdb_conn_info.get_database_uri(), echo=False)
        except exc.SQLAlchemyError as e:
            raise Exception('RDBへの接続に失敗しました %s' % sql)
        return engine

    @staticmethod
    def _get_results(engine, sql):
        """
        SQL文を発行し結果を取得する
        """
        from sqlalchemy import DDL, exc
        try:
            engine.execute('BEGIN')
        except exc.SQLAlchemyError as e:
            engine.execute('ROLLBACK')
            raise Exception('トランザクションの開始に失敗しました')

        try:
            results = engine.execute(sql)
        except exc.SQLAlchemyError as e:
            engine.execute('ROLLBACK')
            raise Exception('SQLの実行に失敗しました %s' % sql)
        finally:
            engine.execute('COMMIT')

        return results

    def _write_log(self, message):
        indent = '  '
        sys.__stderr__.write(indent + self.name + ': <\n')
        sys.__stderr__.write(indent + '  ' + message + '\n')
        sys.__stderr__.write(indent + '>\n')

    def dtor(self):
        self._write_log('DTOR!')
        # Tmpファイルを削除する
        import os
        if self._tmp_file_path is not None and os.path.exists(self._tmp_file_path):
            os.unlink(self._tmp_file_path)
