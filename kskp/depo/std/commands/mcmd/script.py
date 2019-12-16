# Mコマンド

import nysol.mcmd as nm

from kskp.store import NysolModule
from kskp.core import Command, Port

class MselstrCommand(Command):
    """
    mselstrコマンド
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'mcmd'), Port('u', 'mcmd')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mselstr(args)

        nysol_module_o = NysolModule()
        nysol_module_u = NysolModule()

        nysol_module_o.set_content(cmd_o)
        nysol_module_u.set_content(cmd_o.redirect('u'))
        return {'o': nysol_module_o, 'u': nysol_module_u}

class M2crossCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.m2cross(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

        
class McalCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mcal(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class McatCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('*', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        # 結合順が不定っぽい
        # とりあえず今は不定のまま、時間があったら調べて解決したい

        # 例：
        # A,B     A,B
        # 2,4     4,5
        #
        # 上2つを結合すると、
        #
        # A,B    A,B
        # 2,4    4,5
        # 4,5    2,4

        # のどちらかになる。
        inputs_for_arg_i = []
        from nysol.mcmd.nysollib.core import NysolMOD_CORE
        for key, input in inputs.items():
            if isinstance(input, NysolMOD_CORE):
                inputs_for_arg_i.append(input.content)
            else:
                # 一度nysol_module化する
                f = None
                f <<= nm.m2tee(i=input.content)
                inputs_for_arg_i.append(f)

        args['i'] = inputs_for_arg_i
        cmd_o = nm.m2cat(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class McrossCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mcross(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class McutCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mcut(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

        # import pprint
        # pprint.pprint(inputs['i'])
        # cmd = inputs['i'].content
        # cmd <<= nm.mcut(args)
        # return {'o': NysolModule(cmd)}

class MnumberCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mnumber(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MselCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame'), Port('u', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.msel(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        nysol_module_u= NysolModule()
        nysol_module_u.set_content(cmd_o.redirect('u'))
        return {'o': nysol_module_o, 'u': nysol_module_u}

class MsetstrCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.msetstr(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MsortfCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.msortf(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MsummaryCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.msummary(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MjoinCommand(Command):
    """
    mjoinコマンド（きちんとコマンドをstoreに置いたら消そう）
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame'), Port('m', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        import nysol.mcmd as nm
        args['i'] = inputs['i'].content
        args['m'] = inputs['m'].content
        nysol_module = NysolModule()
        nysol_module.set_content(nm.mjoin(args))
        return {'o': nysol_module}

# class MchkcsvCommand(Command):
#     """
#     Mchkcsvコマンド
#     nysol_pythonにはないので、nm.cmdでNYSOLのmchkcsvを動かしている
#     """
#     def __init__(self):
#         super().__init__()
#         self.i_ports = [Port('i', 'frame')]
#         self.o_ports = [Port('o', 'mcmd')]

#     def run(self, args, inputs):
#         import nysol.mcmd as nm
#         f = None
#         f <<= inputs['i'].content

#         args_string = 'mchkcsv'
#         for key,value in args.items():
#             if isinstance(value, bool):
#                 if value == True:
#                     args_string +=  ' -' + key
#             else:
#                 args_string += ' %s=%s' % (key, value)

#         f <<= nm.cmd(args_string)
#         nysol_module = NysolModule()
#         nysol_module.set_content(f)
#         return {'o': nysol_module}

class MchkcsvCommand(Command):
    """
    Mchkcsvコマンド
    nysol_pythonにはないので、nm.cmdでNYSOLのmchkcsvを動かしている
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'text')]
    
    def run(self, args, inputs):
        import sys

        def filter():
            import traceback
            try:
                for line in sys.stdin:
                    # VisするときにMChkcsvの出力をNYSOL Pythonに渡すので、
                    # CSVデータに変換する
                    line = line.rstrip('\n')
                    table = str.maketrans({'"': '""'})
                    line = line.translate(table)
                    print('"' + line + '"', end='')
                    print('')
                # flushをする
                sys.stdout.flush()
            except Exception as e:
                with open('/dev/stderr', 'w') as fpe:
                    traceback.print_exc(file=fpe)

        # flushをしないと、デバッグ用のprintなども入ってしまう
        sys.stdout.flush()

        # チェックのみ実行するオプション
        is_diag = 'diag' in args and args['diag']

        args_str = self.make_args(args)

        cmd = inputs['i'].content
        cmd <<= nm.cmd(args_str)
        if is_diag:
            cmd <<= nm.runfunc(filter)

        # output
        return {'o': NysolModule(cmd)}

    def make_args(self, args):
        args_string = 'mchkcsv'
        for key,value in args.items():
            if isinstance(value, bool):
                if value == True:
                    args_string +=  ' -' + key
            else:
                args_string += ' %s=%s' % (key, value)
        return args_string


class MfldnameCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mfldname(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MdformatCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mdformat(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MshareCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mshare(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MchgnumCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mchgnum(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class McountCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mcount(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}



class MaccumCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.maccum(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class Marff2csvCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.marff2csv(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MavgCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mavg(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MbestCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame'), Port('u', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mbest(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        nysol_module_u= NysolModule()
        nysol_module_u.set_content(cmd_o.redirect('u'))
        return {'o': nysol_module_o, 'u': nysol_module_u}

class MbucketCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mbucket(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MchgstrCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mchgstr(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class McombiCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mcombi(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class McommonCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame'), Port('m', 'frame')]
        self.o_ports = [Port('o', 'frame'), Port('u', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        args['m'] = inputs['m'].content
        cmd_o = nm.mcommon(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        nysol_module_u= NysolModule()
        nysol_module_u.set_content(cmd_o.redirect('u'))
        return {'o': nysol_module_o, 'u': nysol_module_u}

class Mcsv2arffCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mcsv2arff(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MdelnullCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame'), Port('u', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mdelnull(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        nysol_module_u= NysolModule()
        nysol_module_u.set_content(cmd_o.redirect('u'))
        return {'o': nysol_module_o, 'u': nysol_module_u}

class MduprecCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mduprec(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MfsortCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mfsort(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MhashavgCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mhashavg(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MhashsumCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mhashsum(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MkeybreakCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mkeybreak(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MmbucketCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mmbucket(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MmvavgCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mmvavg(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MmvsimCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mmvsim(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MmvstatsCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mmvstats(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MnewnumberCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = []
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        cmd_o = nm.mnewnumber(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MnewrandCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = []
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        cmd_o = nm.mnewrand(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MnewstrCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = []
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        cmd_o = nm.mnewstr(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MnjoinCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame'), Port('m', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        args['m'] = inputs['m'].content
        cmd_o = nm.mnjoin(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MnormalizeCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mnormalize(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MnrcommonCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame'), Port('m', 'frame')]
        self.o_ports = [Port('o', 'frame'), Port('u', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        args['m'] = inputs['m'].content
        cmd_o = nm.mnrcommon(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        nysol_module_u= NysolModule()
        nysol_module_u.set_content(cmd_o.redirect('u'))
        return {'o': nysol_module_o, 'u': nysol_module_u}

class MnrjoinCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame'), Port('m', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        args['m'] = inputs['m'].content
        cmd_o = nm.mnrjoin(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MnulltoCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mnullto(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MpaddingCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mpadding(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MpasteCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame'), Port('m', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        args['m'] = inputs['m'].content
        cmd_o = nm.mpaste(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MproductCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame'), Port('m', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        args['m'] = inputs['m'].content
        cmd_o = nm.mproduct(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MrandCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mrand(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MrjoinCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame'), Port('m', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        args['m'] = inputs['m'].content
        cmd_o = nm.mrjoin(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MsedCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.msed(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MselnumCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame'), Port('u', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mselnum(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        nysol_module_u= NysolModule()
        nysol_module_u.set_content(cmd_o.redirect('u'))
        return {'o': nysol_module_o, 'u': nysol_module_u}

class MselrandCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame'), Port('u', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mselrand(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        nysol_module_u= NysolModule()
        nysol_module_u.set_content(cmd_o.redirect('u'))
        return {'o': nysol_module_o, 'u': nysol_module_u}

class MsepCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.msep(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class Msep2Command(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.msep2(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MshuffleCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mshuffle(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MsimCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.msim(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MslideCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mslide(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MsplitCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.msplit(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MstatsCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mstats(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MsumCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.msum(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class Mtab2csvCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mtab2csv(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MteeCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.m2tee(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MtonullCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mtonull(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MtraCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mtra(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MtrafldCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mtrafld(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MtraflgCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mtraflg(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MuniqCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.muniq(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MvcatCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mvcat(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MvcommonCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame'), Port('m', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        args['m'] = inputs['m'].content
        cmd_o = nm.mvcommon(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MvcountCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mvcount(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MvdelimCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mvdelim(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MvdelnullCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mvdelnull(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MvjoinCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame'), Port('m', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        args['m'] = inputs['m'].content
        cmd_o = nm.mvjoin(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MvnulltoCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mvnullto(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MvreplaceCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame'), Port('m', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        args['m'] = inputs['m'].content
        cmd_o = nm.mvreplace(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MvsortCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mvsort(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MvuniqCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mvuniq(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MwindowCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mwindow(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class Mxml2csvCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i'].content
        cmd_o = nm.mxml2csv(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}
