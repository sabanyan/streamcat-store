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

    def fixtimecolumn(self, flow, col, dateformat = 'date'):
        if dateformat == 'date':
            flow <<= nm.mcal(a = '__INT__', 
                    c = f'uxt( s2t(regexstr($s{{{col}}},"^[0-9]{{14,14}}|^[0-9]{{6,6}}") ) )')
            flow <<= nm.mcal(a = '__FLAC__', 
                    c = f'regexstr($s{{{col}}},"[.][0-9]{{0,6}}$")')
            flow <<= nm.mcal(a = 'uxt',
                    c = 'if( isnull($s{__FLAC__}), $s{__INT__}, $s{__INT__}+$s{__FLAC__} )')
        else:
            flow <<= nm.mfldname(f = f'{col}:uxt')
        
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

            subcmd <<= nm.msummary(k = k, f = f, c = '__count')
            subcmd <<= nm.mjoin(k = k, m = allrows, f = '__allrows', K = k)

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
            targets = [None] * len(fs)
            count = [None] * len(fs)
            subcmd_o = None

            for i, fld in enumerate(fs):

                total[i] <<= nm.mcount(k = f'{k},{fld}', a = '__dcnt', i = subcmd)
                count[i] <<= nm.msummary(k = k, f = fld, c = 'count:__count',
                                            i = subcmd)

                targets[i] <<= nm.mcount(k = k, a = '__ddcnt', i = total[i])
                targets[i] <<= nm.mjoin(k = k, f = '__count', m = count[i])
                targets[i] <<= nm.mcal(c = '${__ddcnt}!=${__count}', a = a)
                targets[i] <<= nm.msetstr(a = 'fld', v = fld)
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
                targets[i] <<= nm.mbest(k = k, f = f'{fld}%n', size = 1)    
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
                targets[i] <<= nm.mbest(k = k, f = f'{fld}%nr', size = 1)    
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

            subcmd <<= nm.msummary(k = k, f = f, c = 'var:__var,sd:__sd')
            subcmd <<= nm.mcal(c = '${__var}>${__sd}', a = a)
            subcmd <<= nm.mcut(f = f'{k},fld,{a}')

            return subcmd

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

            subcmd <<= nm.mstdin()

            for i, fld in enumerate(fs):
                targets[i] <<= nm.mkeybreak(i = subcmd, k = k, s = fld)
                targets[i] <<= nm.mcal(a = 'fld', c = f'if($s{{bot}}=="1","{fld}",nulls())')
                targets[i] <<= nm.mcal(a = a, c = f'if($s{{bot}}=="1",$s{{{fld}}},nulls())')
                targets[i] <<= nm.mdelnull(f = a)

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

            subcmd <<= nm.mstdin()

            for i, fld in enumerate(fs):
                targets[i] <<= nm.mkeybreak(i = subcmd, k = k, s = fld)
                targets[i] <<= nm.mcal(a = 'fld', c = f'if($s{{top}}=="1","{fld}",nulls())')
                targets[i] <<= nm.mcal(a = a, c = f'if($s{{top}}=="1",$s{{{fld}}},nulls())')
                targets[i] <<= nm.mdelnull(f = a)

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
                subcmd <<= nm.mcal(c = f'${{{fld}}}*${{{fld}}}', a = f'__tmp{fld}__')
                subcmd <<= nm.mcut(f = fld, r = True)
                subcmd <<= nm.mfldname(f = f'__tmp{fld}__:{fld}')
            
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

            for i, fld in enumerate(fs):
                targets[i] <<= nm.msummary(k = k, f = fld, i = subcmd, a = '__tmp',
                                           c = 'count:__count,ucount:__ucount')
                targets[i] <<= nm.mcal(c = '${__ucount}/${__count}', a = a)
                targets[i] <<= nm.msetstr(a = 'fld', v = fld)
                targets[i] <<= nm.mcut(f = f'{k},fld,{a}')

            subcmd_o <<= nm.m2cat(i = targets)

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
            msummary = [None] * len(fs)

            subcmd_o = None

            for i, fld in enumerate(fs):
                msummary[i] <<= nm.msummary(i = subcmd, k = k, f = fld, 
                                            c = 'mean:__mean')

                targets[i] <<= nm.mjoin(i = subcmd, m = msummary[i], k = k, 
                                        f = '__mean')
                targets[i] <<= nm.mcal(c = f'${{{fld}}}>${{__mean}}', a = a)
                targets[i] <<= nm.msum(k = k, f = a)
                targets[i] <<= nm.msetstr(a = 'fld', v = fld)
                targets[i] <<= nm.mcut(f = f'{k},fld,{a}')

            subcmd_o <<= nm.m2cat(i = targets)

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
            msummary = [None] * len(fs)

            subcmd_o = None

            for i, fld in enumerate(fs):
                msummary[i] <<= nm.msummary(i = subcmd, k = k, f = fld, 
                                            c = 'mean:__mean')

                targets[i] <<= nm.mjoin(i = subcmd, m = msummary[i], k = k, 
                                        f = '__mean')
                targets[i] <<= nm.mcal(c = f'${{{fld}}}<${{__mean}}', a = a)
                targets[i] <<= nm.msum(k = k, f = a)
                targets[i] <<= nm.msetstr(a = 'fld', v = fld)
                targets[i] <<= nm.mcut(f = f'{k},fld,{a}')

            subcmd_o <<= nm.m2cat(i = targets)

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def symmetry_looking(self,subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')
            n = kwargs.get('n')

            subcmd <<= nm.msummary(f = f, k = k, 
                        c = 'mean:__mean,median:__median,max:__max,min:__min')
            subcmd <<= nm.mcal(c = '${__max}-${__min}',
                               a = 'max_min')
            subcmd <<= nm.mcal(c = 'abs(${__mean}-${__median})',
                               a = 'mean_median')
            subcmd <<= nm.mcal(c = f'${{mean_median}}<${{max_min}}*{n}', 
                               a = f'{a}_{n}')

            subcmd <<= nm.mcut(f = f'{k},fld,{a}_{n}')

            return subcmd

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)
        
    def large_standard_dev(self,subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')
            n = kwargs.get('n')

            subcmd <<= nm.msummary(f = f, k = k, 
                        c = 'sd:__sd,max:__max,min:__min')
            subcmd <<= nm.mcal(c = '${__max}-${__min}', a = '__diff')
            subcmd <<= nm.mcal(c = f'${{__sd}}>${{__diff}}*{n}', 
                               a = f'{a}_{n}')

            subcmd <<= nm.mcut(f = f'{k},fld,{a}_{n}')

            return subcmd

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def value_count(self,subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')
            n = kwargs.get('n')

            fs = f.split(',')
            targets = [None] * len(fs)
            subcmd_o = None

            for i, fld in enumerate(fs):
                targets[i] <<= nm.mcal(c = f'$s{{{fld}}}=="{n}"', a = f'{a}_{n}',
                                       i = subcmd)
                targets[i] <<= nm.msetstr(a = 'fld', v = fld)
                targets[i] <<= nm.msum(k = f'{k}', f = f'{a}_{n}')

            subcmd_o <<= nm.mcut(f = f'{k},fld,{a}_{n}', i = targets)

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def ratio_beyond_rsigma(self,subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')
            n = kwargs.get('n')

            fs = f.split(',')
            targets = [None] * len(fs)
            msummary = None
            subcmd_o = None

            msummary <<= nm.msummary(f = f, c = 'mean:__mean,sd:__sd,count:__count',
                                     k = k, i = subcmd)
            subcmd <<= nm.mnjoin(k = k, m = msummary, f = 'fld,__mean,__sd,__count')

            for i, fld in enumerate(fs):
                targets[i] <<= nm.msel(c = f'$s{{fld}}=="{fld}"', i = subcmd)
                targets[i] <<= nm.mcal(c = f'(abs(${{{fld}}}-${{__mean}}))>=({n}*${{__sd}})', 
                                       a = f'__ratio')

            subcmd_o <<= nm.msum(k = f'{k},fld', f = f'__ratio', i = targets)
            subcmd_o <<= nm.mcal(c = '${__ratio}/${__count}', a = f'{a}_{n}')

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
            import numpy as np
            
            f = kwargs.get('f')
            a = kwargs.get('a')
            x = kwargs.get('x')
            k = kwargs.get('k')
            precision = kwargs.get('precision')

            headerline = True

            for dlist in nm.mstdin().keyblock(f'{k}', x, header = True):
                id = ','.join(dlist[0][:len(k.split(','))])

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

                        print(f'{id},{fld},{mean:.{precision}g}')
            sys.__stdout__.flush()#not needed for bigger data

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def frequencyvar(self, **kwargs):
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

            for dlist in nm.mstdin().keyblock(f'{k}', x, header = True):
                id = ','.join(dlist[0][:len(k.split(','))])

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

                        print(f'{id},{fld},{variance:.{precision}g}')
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
                subcmd <<= nm.mcal(a = fld, 
                    c = f'(${{{fld}_prod_mean}}-(${{{fld}_mean}}*${{uxt_mean}}))/${{uxt_var}}')
            
            subcmd <<= nm.mcross(f = f, s = 'fld', k = k)
            subcmd <<= nm.mcut(f = f'{k},fld,{a}')
            
            return subcmd

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def slopebyorder(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            x = kwargs.get('s')
            k = kwargs.get('k')
            precision = kwargs.get('precision')

            fs = f.split(',')

            # fix "time" column
            ordercol = '__order__'
            subcmd <<= nm.mnumber(k = k, a = f'{ordercol}', s = f'{k},{x}', S = '1')

            for fld in fs: 
                subcmd <<= nm.mcal(a = f'{fld}_prod',c = f'${{{fld}}}*${{{ordercol}}}')
            
            prod_fldnames = ','.join([f'{fld}_prod' for fld in fs])
            
            subcmd <<= nm.msummary(k = k, f = f'{prod_fldnames},{f},{ordercol}',
                                c = 'mean,var')
        
            subcmd <<= nm.m2cross(k = f'{k},fld', f = 'mean,var', a = f'type,{a}')
            subcmd <<= nm.mcal(a = 'tmp_colnames', c = '$s{fld}+"_"+$s{type}')
            subcmd <<= nm.mcross(f = f'{a}', s = 'tmp_colnames', k = k)

            for fld in fs:
                subcmd <<= nm.mcal(a = fld, precision = precision,
                    c = f'(${{{fld}_prod_mean}}-(${{{fld}_mean}}*${{{ordercol}_mean}}))/${{{ordercol}_var}}')
            
            subcmd <<= nm.mcross(f = f, s = 'fld', k = k)
            subcmd <<= nm.mcut(f = f'{k},fld,{a}')

            return subcmd
            
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
                targets[i] <<= nm.mslide(k = k, s = 'uxt', i = subcmd, 
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
                targets[i] <<= nm.mslide(k = k, s = 'uxt', i = subcmd, 
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
                subcmd <<= nm.msortf(f = f'{k},uxt')
                subcmd <<= nm.mcal(c = f'abs(${{{fld}}}-#{{{fld}}}', a = f'__tmp{fld}__')
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

            # subcmd_o <<= nm.mcut(i = targets, f = f'{k},fld,{a}_{n}')

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
            msummary = [None] * len(fs)

            subcmd_o = None

            # fix time column
            subcmd = self.fixtimecolumn(subcmd, x, dateformat)

            for i, fld in enumerate(fs):
                msummary[i] <<= nm.msummary(i = subcmd, k = k, f = fld, 
                                            c = 'mean:__mean')

                targets[i] <<= nm.mjoin(i = subcmd, m = msummary[i], k = k, 
                                        f = '__mean')

                targets[i] <<= nm.msortf(f = f'{k},uxt')
                targets[i] <<= nm.mcal(c = f'${{__mean}}<=${{{fld}}}', a = '__above')
                targets[i] <<= nm.mcount(q = True, k = f'{k},__above', a = '__a_count')
                targets[i] <<= nm.mbest(k = k, s = '__above%nr,__a_count%nr', size = 1)
                targets[i] <<= nm.mcal(c = 'if(${__above}==0,0,${__a_count})', a = a)
                targets[i] <<= nm.msetstr(a = 'fld', v = fld)
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
            msummary = [None] * len(fs)

            subcmd_o = None

            # fix time column
            subcmd = self.fixtimecolumn(subcmd, x, dateformat)

            for i, fld in enumerate(fs):
                msummary[i] <<= nm.msummary(i = subcmd, k = k, f = fld, 
                                            c = 'mean:__mean')

                targets[i] <<= nm.mjoin(i = subcmd, m = msummary[i], k = k, 
                                        f = '__mean')

                targets[i] <<= nm.msortf(f = f'{k},uxt')
                targets[i] <<= nm.mcal(c = f'${{__mean}}<=${{{fld}}}', a = '__below')
                targets[i] <<= nm.mcount(q = True, k = f'{k},__below', a = '__b_count')
                targets[i] <<= nm.mbest(k = k, s = '__below%nr,__b_count%nr', size = 1)
                targets[i] <<= nm.mcal(c = 'if(${__below}==0,0,${__b_count})', a = a)
                targets[i] <<= nm.msetstr(a = 'fld', v = fld)
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
                targets[i] <<= nm.mslide(k = k, s = 'uxt', f = f'{fld}:__shifted{fld}',
                                         t = 2, i = subcmd)
                targets[i] <<= nm.mcal(c = f'(${{__shifted{fld}2}}-2*${{__shifted{fld}1}}+${{{fld}}})/2',
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
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            k = kwargs.get('k')
            x = kwargs.get('x')
            n = kwargs.get('n')
            precision = kwargs.get('precision')

            fs = f.split(',')
            targets = [None] * len(fs)
            mcal = [None] * len(fs)
            msum = [None] * len(fs)
            msummary = [None] * len(fs)

            subcmd_o = None

            # fix time column
            # subcmd = self.fixtimecolumn(subcmd, x, dateformat)

            for i, fld in enumerate(fs):
                mcal[i] <<= nm.mcal(c = f'abs(${{{fld}}})', a = f'__abs{fld}', 
                                    i = subcmd)
                msum[i] <<= mcal[i].msum(k = k, f = f'__abs{fld}')
                msummary[i] <<= nm.msummary(k = k, f = fld, i = subcmd,
                                            c = 'count:__count')

                targets[i] <<= nm.maccum(k = k, s = x, f = f'__abs{fld}:__abs{fld}_a',
                                         i = mcal[i])
                targets[i] <<= nm.mjoin(k = k, f = f'__abs{fld}:__abs{fld}_ttl',
                                        m = msum[i])
                targets[i] <<= nm.mjoin(k = k, f = f'__count', m = msummary[i])
                targets[i] <<= nm.mcal(c = f'(${{__abs{fld}_a}}/${{__abs{fld}_ttl}})>={float(n):.3g}',
                                       a = '__mc')
                targets[i] <<= nm.mbest(k = k, s = f'__mc%nr,{x}%n', size = 1)
                targets[i] <<= nm.mcal(c = f'(${{{x}}} + 1)/${{__count}}', a = f'{a}_{n}',
                                       precision = precision)

                targets[i] <<= nm.msetstr(a = 'fld', v = fld)
                targets[i] <<= nm.mcut(f = f'{k},fld,{a}_{n}')

            subcmd_o <<= nm.m2cat(i = targets)

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def numbercrossing(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            x = kwargs.get('x')
            k = kwargs.get('k')
            n = kwargs.get('n')

            dateformat = kwargs.pop('dateformat')

            subcmd_o = None

            fs = f.split(',')
            targets = [None] * len(fs) 

            # fix time column
            subcmd = self.fixtimecolumn(subcmd, x, dateformat)

            for i, fld in enumerate(fs):
                targets[i] <<= nm.mcal(c = f'${{{fld}}}>{n}', a = '__pos', 
                                   i = subcmd)
                targets[i] <<= nm.mslide(k = k, s = 'uxt', f = '__pos:__posN')
                targets[i] <<= nm.mcal(c = '${__pos}!=${__posN}', a = '__diffT')
                targets[i] <<= nm.mcount(k = k + ',__diffT', a = '__cnt')
                targets[i] <<= nm.mbest(k = k, s = '__diffT%nr', size = 1)
                targets[i] <<= nm.mcal(c = 'if(${__diffT}==0,0,${__cnt})', 
                                      a = f'{a}_{n}')
                targets[i] <<= nm.msetstr(a = 'fld', v = fld)

            subcmd_o <<= nm.mcut(i = targets, f = f'{k},fld,{a}_{n}')

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def countpeaks(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            x = kwargs.get('x')
            k = kwargs.get('k')
            n = kwargs.get('n')

            dateformat = kwargs.pop('dateformat')

            subcmd_o = None

            fs = f.split(',')
            targets = [None] * len(fs) 
            mslide = [None] * len(fs) 

            # fix time column
            subcmd = self.fixtimecolumn(subcmd, x, dateformat)

            for i, fld in enumerate(fs):
                mslide[i] <<= nm.mslide(k = k, s = 'uxt', t = n, r = True, 
                                        f = f'{fld}:{fld}_up_', i = subcmd)

                targets[i] <<= nm.mslide(k = k, s = 'uxt', t = n,
                                         f = f'{fld}:{fld}_down_', i = subcmd)
                
                targets[i] <<= nm.mjoin(k = f'{k},uxt', f = f'{fld}_up_*',
                                        m = mslide[i])
                targets[i] <<= nm.mdelnull(f = f'{fld}_up_*,{fld}_down_*')
                targets[i] <<= nm.mcal(c = f'max(${{{fld}_up*}},${{{fld}_down_*}})',
                                       a = '__rollmax__')
                targets[i] <<= nm.mcal(c = f'${{{fld}}}>${{__rollmax__}}',
                                       a = f'{a}_{n}')

                targets[i] <<= nm.msum(k = k, f = f'{a}_{n}')
                targets[i] <<= nm.mcal(a = 'fld', c = f'"{fld}"')


            subcmd_o <<= nm.mcut(i = targets, f = f'{k},fld,{a}_{n}')

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)

    def autocorrelation(self, subcmd, **kwargs):
        try:
            f = kwargs.get('f')
            a = kwargs.get('a')
            x = kwargs.get('x')
            k = kwargs.get('k')
            n = kwargs.get('n')
            precision = kwargs.get('precision')

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
                            c = 'mean:__mean,var:__var,count:__count')

                    targets[i] <<= nm.mjoin(i = subcmd, m = msummary[i], k = k,
                            f = '__mean,__var,__count')

                    targets[i] <<= nm.mslide(k = k, s = 'uxt', t = n, l = True, 
                                            f = f'{fld}:__{fld}_L')
                    targets[i] <<= nm.mcal(c = f'(${{{fld}}}-${{__mean}})*(${{__{fld}_L}}-${{__mean}})',
                                           a = f'__{fld}_m')
                    targets[i] <<= nm.msum(k = k, f = f'__{fld}_m')
                    targets[i] <<= nm.msetstr(a = '__lag', v = n)
                    targets[i] <<= nm.msetstr(a = 'fld', v = fld)
                    targets[i] <<= nm.mcal(a = f'{a}_{n}', precision = precision,
                        c = f'${{__{fld}_m}}/(${{__count}}-${{__lag}})/${{__var}}')

            subcmd_o <<= nm.mcut(i = targets, f = f'{k},fld,{a}_{n}')

            return subcmd_o

        except Exception as e:
            import traceback
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)
    
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

            for i, fld in enumerate(fs):
                targets[i] <<= nm.mslide(k = k, s = s, f = f'{fld}:{fld}_L', 
                                         n = True, l = True, i = subcmd)
                targets[i] <<= nm.mslide(k = k, s = s, f = f'{fld}:{fld}_L2',
                                         t = int(n)*2, l = True)

                targets[i] <<= nm.mcal(c=f'${{{fld}}}*${{{fld}_L}}*${{{fld}_L2}}',
                                       a = '__tmp')
                targets[i] <<= nm.mcut(f = fld, r = True)
                targets[i] <<= nm.mfldname(f = f'__tmp:{fld}')

            subcmd_o <<= nm.msummary(k = k, c = f'mean:{a}_{n}', f = f, 
                                     i = targets)

            subcmd_o <<= nm.mcut(f = f'{k},fld,{a}_{n}')

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
            'ratio_beyond_rsigma' : self.ratio_beyond_rsigma,
            # 1 field + time (input k, a, f, x)
            'integral' : self.integral,
            'meanf' : self.meanfrequency,
            'varf' : self.frequencyvar,
            'slope' : self.slope,
            '__slope' : self.slopebyorder,
            'firstmin' : self.firstmin,
            'firstmax' : self.firstmax,
            'lastmin' : self.lastmin,
            'lastmax' : self.lastmax,
            'mean_change' : self.meanchange,
            'mean_abs_change' : self.meanabschange,
            'abs_sum_of_changes' : self.abs_sum_of_changes, 
            'autocorr_agg' : self.autocorrelation_agg,
            'longest_strike_above_mean' : self.longeststrikeabovemean,
            'longest_strike_below_mean' : self.longeststrikebelowmean,
            'mean_second_derivative_central' : self.mean2ndderivative_central,
            # 3 fields
            'imq' : self.index_mass_quantile,
            'crossing_m' : self.numbercrossing,
            'peaks' : self.countpeaks,
            'autocorr' : self.autocorrelation,
            'c3' : self.c3
        }

        python_calcs = [
            'meanf',
            'varf'
        ]

        self.header = nm.mread(inputs).getline(header=True)
        self.header = next(self.header)

        k = args.get('k')
        prec = args.pop('precision')
        xs = []

        calclist = []
        all_fs = []
        final_fs = []
        
        allargs = (args.get('clist') + 
                  args.get('fclist') +
                  args.get('nfclist') +
                  args.get('xfclist') + 
                  args.get('sfclist') + 
                  args.get('xfcnlist')+
                  args.get('sfcnlist'))

        # parse inputs into list-of-dictionaries form
        for arglist in allargs:
            if arglist.get('c'):

                x = arglist.get('x')
                s = arglist.get('s')
                if x or s: 
                    arglist['dateformat'] = args['dateformat']
                    if x and x not in xs:
                        xs.append(x)
                    if s: 
                        scols = s.split(',')
                        for col in scols:
                            if col.split('%')[0] not in xs:
                                xs.append(col)

                fs = arglist.get('f')
                if fs:
                    fs = [a for a in self.header 
                        for target in arglist['f'].split(',')
                        if fn.fnmatch(a, target)]
                    all_fs += [f for f in fs if f not in all_fs]
                    arglist['f'] = ','.join(fs)

                cs = arglist.pop('c').split(',')
                cs_msummary = []
                cs_custom_nysol = []

                for i,c in enumerate(cs):
                    if ':' in c:
                        final_fs.append(c.split(':')[-1])
                    elif c:
                        final_fs.append(c)
                    
                    if c.split(':')[0] in msummaryoptions:
                        cs_msummary.append(cs[i])
                    elif c:
                        cs_custom_nysol.append(cs[i])

                if cs_msummary:
                    calclist.append({'c': ','.join(cs_msummary), 
                                'optype' : 'msummary',
                                **arglist})

                ns = arglist.get('n')
                if ns:
                    ns = ns.split(',')

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

        # sys.__stderr__.write(repr(calclist))

        cmd_i = None
        cmd = [None] * len(calclist)
        cmd_o = None

        cmd_i <<= nm.mread(inputs)
        # take the wanted columns only (the key columns and the value columns)
        # generate string of columns to cut

        colstocut = xs + [f for f in all_fs if f not in xs]

        if not k:
            k = '__key__'
            cmd_i <<= nm.mcal(a = k, c = '"all"')

        expanded_k = ','.join([k,'fld'])

        cmd_i <<= nm.mcut(f = f'{k}{","+",".join(colstocut) if len(colstocut) > 0 else ""}')

        ##### calculation portion:

        for i, calcdict in enumerate(calclist):
            # sys.__stderr__.write(repr(calcdict)+'\n')

            cs = calcdict.get('c')
            n = calcdict.get('n')
            optype = calcdict.pop('optype')

            calcdict['precision'] = prec
            calcdict['k'] = k

            # take the required stats for the required columns
            if optype == 'msummary':
                cmd[i] <<= nm.msummary(i = cmd_i, **calcdict)

                final_cs = [c.split(':')[-1] for c in cs.split(',')]

            elif optype == 'custom':
                if ':' in cs:
                    cs, calcdict['a'] = cs.split(':')
                else:
                    calcdict['a'] = cs

                cmd[i] <<= nm.mread(i=cmd_i)

                if cs in python_calcs:
                    cmd[i] <<= nm.runfunc(nysol_calcs[cs], **calcdict)
                else:
                    cmd[i] = nysol_calcs[cs](cmd[i], **calcdict)

                if cs == 'autocorr_agg':
                    final_cs = [f'{calcdict["a"]}_{suff}' for suff in ['mean','median','var']]
                elif n:
                    final_cs = [f'{calcdict["a"]}_{calcdict["n"]}']
                else:
                    final_cs = [calcdict['a']]

            cmd[i] <<= nm.m2cross(k = expanded_k, f= final_cs, 
                    a = '__type__,__val__')

        # cmd_o <<= nm.m2cat(i = cmd)
        cmd_o <<= nm.mdelnull(i = cmd, f = '__val__')

        formatstring = args.pop('format')
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

        cmd_o <<= nm.mcal(a = 'unique_cols', c = '+'.join(colformat))
        cmd_o <<= nm.mcross(f = '__val__', s = 'unique_cols', k = k)
        cmd_o <<= nm.mcut(r = True, f = 'fld', nfno = args.get('nfno'))

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
