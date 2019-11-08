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
        f = None
        f <<= inputs['i']

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

    def rows(self, k, precision, **kwargs):
        a = kwargs['a']
        fld = kwargs['fld']
        
        subcmd = None
        subcmd <<= nm.mstdin()

        subcmd <<= nm.mcount(k = k, a = a)
        subcmd <<= nm.mcal(a = 'fld', c = f'"{fld}"')
        subcmd <<= nm.mcut(f = f'{k},fld,{a}')

        subcmd <<= nm.mstdout()
        subcmd.run()

    def missingdata(self, k, precision, **kwargs):
        f = kwargs['f']
        a = kwargs['a']

        subcmd = None
        allrows = None
        subcmd <<= nm.mstdin()
        
        allrows <<= nm.mcount(i = subcmd, k = k, a = 'allrows')

        subcmd <<= nm.msummary(k = k, f = f, c = 'count')
        subcmd <<= nm.mjoin(k = k, m = allrows, f = 'allrows', K = k)

        subcmd <<= nm.mcal(a = 'missingcount', c = '${allrows}-${count}')
        subcmd <<= nm.mcal(a = 'missingpercent', 
                        c = '((${allrows}-${count})/${allrows})*100',
                        precision = 3)
        subcmd <<= nm.mcal(a = a, c = '$s{missingcount}+"("+$s{missingpercent}+"%)"')

        subcmd <<= nm.mcut(f = f'{k},fld,{a}')

        subcmd <<= nm.mstdout()
        subcmd.run()

    def rootmeansquare(self, k, precision, **kwargs):
        f = kwargs['f']
        a = kwargs['a']
        
        # k gives key fields
        # f gives target fields
        # a gives output field name

        subcmd = None
        subcmd <<= nm.mstdin()
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

        subcmd <<= nm.mstdout()
        subcmd.run()

    def harmonicmean(self, k, precision, **kwargs):
        f = kwargs['f']
        a = kwargs['a']
        
        subcmd = None
        subcmd <<= nm.mstdin()

        fs = f.split(',')
        for fld in fs:
            subcmd <<= nm.mcal(a = f'{fld}_inv', c = f'1/${{{fld}}}',
                               precision = precision)
            subcmd <<= nm.mcut(f = fld, r = True)
            subcmd <<= nm.mfldname(f = f'{fld}_inv:{fld}')

        subcmd <<= nm.msummary(c = 'sum,count', f = f, k = k,
                               precision = precision)

        subcmd <<= nm.mcal(a = a, c = '${count}/${sum}', precision = precision)

        finalcols = ','.join([k,'fld',a])
        subcmd <<= nm.mcut(f = finalcols)
        
        subcmd <<= nm.mstdout()
        subcmd.run()

    def geometricmean(self, k, precision, **kwargs):
        f = kwargs['f']
        a = kwargs['a']
        
        # positive numbers only
        subcmd = None
        subcmd <<= nm.mstdin()

        fs = f.split(',')
        for fld in fs:
            subcmd <<= nm.mcal(a = f'{fld}_ln', c = f'ln(abs(${{{fld}}}))',
                               precision = precision)
            subcmd <<= nm.mcut(f = fld, r = True)
            subcmd <<= nm.mfldname(f = f'{fld}_ln:{fld}')

        subcmd <<= nm.msummary(c = 'mean', f = f, k = k,
                               precision = precision)

        subcmd <<= nm.mcal(a = a, c = 'exp(${mean})', 
                           precision = precision)

        finalcols = f'{k},fld,{a}'
        subcmd <<= nm.mcut(f = finalcols)
        
        subcmd <<= nm.mstdout()
        subcmd.run()

    def meanabsolutedeviation(self, k, precision, **kwargs):
        f = kwargs['f']
        a = kwargs['a']
        
        subcmd = None
        meancalc = None

        subcmd <<= nm.mstdin() 

        meancalc <<= nm.msummary(i = subcmd, k = k, f = f, c = 'mean',
                                 precision = precision)
        meancalc <<= nm.m2cross(f = 'mean', a = 'type,value', k = k + ',fld')
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
        subcmd <<= nm.mstdout()
        subcmd.run()
        
    def medianabsolutedeviation(self, k, precision, **kwargs):
        f = kwargs['f']
        a = kwargs['a']
        
        subcmd = None
        meancalc = None

        subcmd <<= nm.mstdin()

        meancalc <<= nm.msummary(i = subcmd, k = k, f = f, c = 'median',
                                 precision = precision)
        meancalc <<= nm.m2cross(f = 'median', a = 'type,value', k = k + ',fld')
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
        subcmd <<= nm.mstdout()
        subcmd.run()

    def strmax(self, k, precision, **kwargs):
        f = kwargs['f']
        a = kwargs['a']

        try:
            fs = f.split(',')
            targets = [None] * len(fs)

            subcmd = None
            subcmd_final = None

            subcmd <<= nm.mstdin()

            for i, fld in enumerate(fs):
                targets[i] <<= nm.mkeybreak(i = subcmd, k = k, s = fld)
                targets[i] <<= nm.mcal(a = 'fld', c = f'if($s{{bot}}=="1","{fld}",nulls())')
                targets[i] <<= nm.mcal(a = a, c = f'if($s{{bot}}=="1",${{{fld}}},nulln())')
                targets[i] <<= nm.mdelnull(f = a)

            subcmd_final <<= nm.m2cat(i = targets)
            subcmd_final <<= nm.mcut(f = f'{k},fld,{a}')
            subcmd_final <<= nm.mstdout()
            subcmd_final.run()

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def strmin(self, k, precision, **kwargs):
        f = kwargs['f']
        a = kwargs['a']

        try:
            fs = f.split(',')
            targets = [None] * len(fs)

            subcmd = None
            subcmd_final = None

            subcmd <<= nm.mstdin()

            for i, fld in enumerate(fs):
                targets[i] <<= nm.mkeybreak(i = subcmd, k = k, s = fld)
                targets[i] <<= nm.mcal(a = 'fld', c = f'if($s{{top}}=="1","{fld}",nulls())')
                targets[i] <<= nm.mcal(a = a, c = f'if($s{{top}}=="1",${{{fld}}},nulln())')
                targets[i] <<= nm.mdelnull(f = a)

            subcmd_final <<= nm.m2cat(i = targets)
            subcmd_final <<= nm.mcut(f = f'{k},fld,{a}')
            subcmd_final <<= nm.mstdout()
            subcmd_final.run()

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)
        pass

    def strucount(self, k, precision, **kwargs):
        f = kwargs['f']
        a = kwargs['a']

        try:
            fs = f.split(',')
            subcmd_start = None
            subcmd = None
            subcmds = [None] * len(fs)
            subcmd_start <<= nm.mstdin()

            for i, fld in enumerate(fs):
                subcmds[i] <<= nm.muniq(i = subcmd_start, k = f'{k},{fld}') 
                subcmds[i] <<= nm.mcount(k = k, a = f'{a}')
                subcmds[i] <<= nm.mcal(a = 'fld', c = f'"{fld}"')
                subcmds[i] <<= nm.mcut(f = f'{k},fld,{a}')

            subcmd <<= nm.m2cat(i = subcmds)
            subcmd <<= nm.mstdout()
            subcmd.run()

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)
        pass

    def integral(self, k, precision, **kwargs):
        f = kwargs['f']
        x = kwargs['x']
        a = kwargs['a']

        dateformat = kwargs.pop('dateformat') 
        fs = f.split(',')

        subcmd = None
        subcmd <<= nm.mstdin()

        # get keybreak points
        subcmd <<= nm.msortf(f = k)
        subcmd <<= nm.mkeybreak(k = k, s = f'{x}%n')
        
        # fix time column
        if dateformat == 'date':
            subcmd <<= nm.mcal(a = '__INT__', 
                    c = f'uxt( s2t(regexstr($s{{{x}}},"^[0-9]{{14,14}}|^[0-9]{{6,6}}") ) )')
            subcmd <<= nm.mcal(a = '__FLAC__', 
                    c = f'regexstr($s{{{x}}},"[.][0-9]{{0,6}}$")')
            subcmd <<= nm.mcal(a = 'uxt',
                    c = 'if( isnull($s{__FLAC__}), $s{__INT__}, $s{__INT__}+$s{__FLAC__} )')
        else:
            subcmd <<= nm.mfldname(f = f'{x}:uxt')
            x = 'uxt'

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

        subcmd <<= nm.mstdout()
        subcmd.run()
        
    def meanfrequency(self, k, precision, **kwargs):
        # body of this method adapted from:
        # github.com/nysol/nysol_python/blob/master/scripts/sample/mkfeature.py
        f = kwargs.get('f')
        x = kwargs.get('x')
        a = kwargs.get('a')

        import numpy as np
        import traceback

        try:
            headerline = True

            for dlist in nm.mstdin().keyblock(f'{k}', x, header = True):
                id = ','.join(dlist[0][1:len(k.split(','))+1])

                if headerline:
                    header = dlist[0]
                    print(f'{k},fld,{a}')
                    headerline = False

                else:
                    for fld in f.split(','):
                        f_loc = header.index(fld)

                        targetcol = [float(xdlist[f_loc]) for xdlist in dlist]

                        y = np.abs(np.fft.rfft(targetcol))**2

                        mean = y.dot(np.arange(len(y)))/y.sum()

                        print(f'{id},{fld},{mean}')
            sys.__stdout__.flush()#not needed for bigger data

        except Exception as e:
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def frequencyvar(self, k, precision, **kwargs):
        # body of this method adapted from:
        # github.com/nysol/nysol_python/blob/master/scripts/sample/mkfeature.py
        f = kwargs.get('f')
        x = kwargs.get('x')
        a = kwargs.get('a')

        import numpy as np
        import traceback

        try:
            headerline = True

            for dlist in nm.mstdin().keyblock(f'{k}', x, header = True):
                id = ','.join(dlist[0][1:len(k.split(','))+1])

                if headerline:
                    header = dlist[0]
                    print(f'{k},fld,{a}')
                    headerline = False

                else:
                    for fld in f.split(','):
                        f_loc = header.index(fld)

                        y = np.abs(np.fft.rfft([float(xdlist[f_loc]) 
                                                for xdlist in dlist]))**2

                        mean = y.dot(np.arange(len(y)))/y.sum()
                        moment2 = y.dot(np.arange(len(y))**2)/y.sum()
                        variance = moment2 - mean ** 2 

                        print(f'{id},{fld},{variance}')
            sys.__stdout__.flush()#not needed for bigger data

        except Exception as e:
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def slope(self, k, precision, **kwargs):
        f = kwargs.get('f')
        x = kwargs.get('x')
        a = kwargs.get('a')

        import traceback
        try:
            dateformat = kwargs.pop('dateformat')

            fs = f.split(',')
            subcmd = None
            subcmd <<= nm.mstdin()

            # fix time column
            if dateformat == 'date':
                subcmd <<= nm.mcal(a = '__INT__', 
                        c = f'uxt( s2t(regexstr($s{{{x}}},"^[0-9]{{14,14}}|^[0-9]{{6,6}}") ) )')
                subcmd <<= nm.mcal(a = '__FLAC__', 
                        c = f'regexstr($s{{{x}}},"[.][0-9]{{0,6}}$")')
                subcmd <<= nm.mcal(a = 'uxt',
                        c = 'if( isnull($s{__FLAC__}), $s{__INT__}, $s{__INT__}+$s{__FLAC__} )', o = 'beforeslope.csv')
            else:
                subcmd <<= nm.mfldname(f = f'{x}:uxt')
                x = 'uxt'

            for fld in fs: 
                subcmd <<= nm.mcal(a = f'{fld}_prod',c = f'${{{fld}}}*${{uxt}}')
            
            prod_fldnames = ','.join([f'{fld}_prod' for fld in fs])
            
            subcmd <<= nm.msummary(k = k, f = f'{prod_fldnames},{f},uxt',
                                c = 'mean,var')
        
            subcmd <<= nm.m2cross(k = f'{k},fld', f = 'mean,var', a = f'type,{a}')
            subcmd <<= nm.mcal(a = 'tmp_colnames', c = '$s{fld}+"_"+$s{type}')
            subcmd <<= nm.mcross(f = f'{a}', s = 'tmp_colnames', k = k)

            for fld in fs:
                subcmd <<= nm.mcal(a = fld, 
                    c = f'(${{{fld}_prod_mean}}-(${{{fld}_mean}}*${{uxt_mean}}))/${{uxt_var}}')
            
            subcmd <<= nm.mcross(f = f, s = 'fld', k = k)
            subcmd <<= nm.mcut(f = f'{k},fld,{a}')
            
            subcmd <<= nm.mstdout()
            subcmd.run()
        except Exception as e:
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def slopeinorder(self, k, precision, **kwargs):
        f = kwargs.get('f')
        s = kwargs.get('s')
        a = kwargs.get('a')

        import traceback
        try:
            fs = f.split(',')
            subcmd = None
            subcmd <<= nm.mstdin()

            # fix "time" column
            subcmd <<= nm.msortf(f = f'{k},{s}')
            ordercol = '__order__'
            subcmd <<= nm.mnumber(k = k, a = f'{ordercol}', q = True, S = '1')

            for fld in fs: 
                subcmd <<= nm.mcal(a = f'{fld}_prod',c = f'${{{fld}}}*${{{ordercol}}}')
            
            prod_fldnames = ','.join([f'{fld}_prod' for fld in fs])
            
            subcmd <<= nm.msummary(k = k, f = f'{prod_fldnames},{f},{ordercol}',
                                c = 'mean,var')
        
            subcmd <<= nm.m2cross(k = f'{k},fld', f = 'mean,var', a = f'type,{a}')
            subcmd <<= nm.mcal(a = 'tmp_colnames', c = '$s{fld}+"_"+$s{type}')
            subcmd <<= nm.mcross(f = f'{a}', s = 'tmp_colnames', k = k)

            for fld in fs:
                subcmd <<= nm.mcal(a = fld, 
                    c = f'(${{{fld}_prod_mean}}-(${{{fld}_mean}}*${{{ordercol}_mean}}))/${{{ordercol}_var}}')
            
            subcmd <<= nm.mcross(f = f, s = 'fld', k = k)
            subcmd <<= nm.mcut(f = f'{k},fld,{a}')
            
            subcmd <<= nm.mstdout()
            subcmd.run()
        except Exception as e:
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

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
            # 0 fields (input k, a, fld)
            'rows' : self.rows,
            # 1 field (input k, a, f)
            'miss' : self.missingdata,
            'rms' : self.rootmeansquare,
            'hmean' : self.harmonicmean,
            'gmean' : self.geometricmean,
            'strmax' : self.strmax,
            'strmin' : self.strmin,            
            'strucount' : self.strucount,
            'mean_ad' : self.meanabsolutedeviation,
            'median_ad' : self.medianabsolutedeviation,
            # 1 field + time (input k, a, f, x)
            'integral' : self.integral,
            'meanf' : self.meanfrequency,
            'varf' : self.frequencyvar,
            'slope' : self.slope,
            '__slope' : self.slopeinorder
        }

        self.header = nm.mread(inputs).getline(header=True)
        self.header = next(self.header)

        k = args.get('k')
        prec = args.pop('precision')
        xs = []

        calclist = []
        all_fs = []
        final_fs = []
        
        # wildcard parsing
        for arglist in args.get('clist') + args.get('fclist') + args.get('xfclist') + args.get('sfclist'):
            if arglist.get('c'):
                fs = arglist.get('f')
                x = arglist.get('x')

                if x: 
                    arglist['dateformat'] = args['dateformat']
                    if x not in xs:
                        xs.append(x)

                if fs:
                    fs = ','.join([a for a in self.header 
                        for target in arglist['f'].split(',')
                        if fn.fnmatch(a, target)])
                    all_fs += [f for f in fs.split(',') if f not in all_fs]
                    arglist['f'] = fs

                cs = arglist.pop('c').split(',')
                cs_msummary = []
                cs_custom = []

                for i,c in enumerate(cs):
                    if ':' in c:
                        final_fs.append(c.split(':')[-1])
                    elif c:
                        final_fs.append(c)
                    
                    if c.split(':')[0] in msummaryoptions:
                        cs_msummary.append(cs[i])
                    elif c:
                        cs_custom.append(cs[i])

                if cs_msummary:
                    calclist.append({'c': ','.join(cs_msummary), 
                                'optype' : 'msummary',
                                **arglist})

                for calc in cs_custom:
                    calclist.append({'c': calc, 
                                'optype' : 'custom',
                                **arglist})

        # sys.__stderr__.write(repr(calclist))

        cmd = [None] * len(calclist)
        cmd_o = None
        cmd[-1] <<= nm.mread(inputs)
        # take the wanted columns only (the key columns and the value columns)
        # generate string of columns to cut
        if xs:
            timecols = ','.join(xs) + ','
        else:
            timecols = ''

        if not k:
            k = '__key__'
            cmd[-1] <<= nm.mcal(a = k, c = '"all"')

        expanded_k = ','.join([k,'fld'])

        cmd[-1] <<= nm.mcut(f = f'{timecols}{k}{","+",".join(all_fs) if len(all_fs) > 0 else ""}')

        ##### calculation portion:

        for i, calcdict in enumerate(calclist):
            cs = calcdict.get('c')
            optype = calcdict.pop('optype')

            # take the required stats for the required columns
            if optype == 'msummary':
                if i != len(calclist) - 1:
                    cmd[i] <<= nm.mread(i = cmd[-1])

                cmd[i] <<= nm.msummary(k = k, precision = prec, **calcdict)

                final_cs = [c.split(':')[-1] for c in cs.split(',')]
                cmd[i] <<= nm.m2cross(k = expanded_k, f = final_cs, 
                        a = 'type,value')

            elif optype == 'custom':
                if ':' in cs:
                    cs, calcdict['a'] = cs.split(':')
                else:
                    calcdict['a'] = cs

                if i != len(calclist) - 1:
                    cmd[i] <<= nm.mread(i=cmd[-1])
                
                cmd[i] <<= nm.runfunc(new_calcs[cs], k = k,
                                      precision = prec,
                                      **calcdict)

                final_cs = [calcdict['a']]
                cmd[i] <<= nm.m2cross(k = expanded_k, f= final_cs, 
                        a = 'type,value')

        cmd_o <<= nm.m2cat(i = cmd)
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
        
        cmd_o <<= nm.mcal(a = 'unique_cols', c = '+'.join(colformat))
        cmd_o <<= nm.mcross(f = 'value', s = 'unique_cols', k = k)
        cmd_o <<= nm.mcut(r = True, f = 'fld', 
                          nfno = args.get('nfno'))

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
