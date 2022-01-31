# Mコマンド

from typing import Callable
import nysol.mcmd as nm
from kskp.core import Command, Port
from kskp.store import NysolModule

class MCommand(Command):
    """
    nysol_pythonのMコマンド
    (0入力1出力)
    """
    def __init__(self):
        super().__init__()
        self.i_ports = []
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args:dict, inputs:dict) -> dict:
        cmd = self.mcmd(args)
        return {'o': NysolModule(cmd)}

    @property
    def mcmd(self) -> Callable:
        pass

class MCommandI(MCommand):
    """
    nysol_pythonのMコマンド
    (1入力1出力)
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', ['mcmd','matrix'])]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args:dict, inputs:dict) -> dict:
        cmd = self.mcmd(args, i=inputs['i'].content)
        return {'o': NysolModule(cmd)}

class MCommandA(MCommand):
    """
    nysol_pythonのMコマンド
    (1入力2出力)
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', ['mcmd','matrix'])]
        self.o_ports = [Port('o', 'mcmd'), Port('u', 'mcmd')]

    def run(self, args:dict, inputs:dict) -> dict:
        cmd = self.mcmd(args, i=inputs['i'].content)
        return {'o': NysolModule(cmd), 'u': NysolModule(cmd.redirect('u'))}

class MCommandV(MCommand):
    """
    nysol_pythonのMコマンド
    (2入力1出力)
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', ['mcmd','matrix']), Port('m', ['mcmd','matrix'])]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args:dict, inputs:dict) -> dict:
        cmd = self.mcmd(args, i=inputs['i'].content, m=inputs['m'].content)
        return {'o': NysolModule(cmd)}

class MCommandX(MCommand):
    """
    nysol_pythonのMコマンド
    (2入力2出力)
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', ['mcmd','matrix']), Port('m', ['mcmd','matrix'])]
        self.o_ports = [Port('o', 'mcmd'), Port('u', 'mcmd')]

    def run(self, args:dict, inputs:dict) -> dict:
        cmd = self.mcmd(args, i=inputs['i'].content, m=inputs['m'].content)
        return {'o': NysolModule(cmd), 'u': NysolModule(cmd.redirect('u'))}

# 
# 0入力1出力
# 

class MnewstrCommand(MCommand):
    @property
    def mcmd(self) -> Callable:
        return nm.mnewstr

class MnewnumberCommand(MCommand):
    @property
    def mcmd(self) -> Callable:
        return nm.mnewnumber

class MnewrandCommand(MCommand):
    @property
    def mcmd(self) -> Callable:
        return nm.mnewrand

# 
# 1入力1出力
# 
class M2crossCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.m2cross

class McalCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mcal

class McrossCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mcross

class McutCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mcut

class MnumberCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mnumber

class MsetstrCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.msetstr

class MsortfCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.msortf

class MsummaryCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.msummary

class MfldnameCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mfldname

class MdformatCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mdformat

class MshareCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mshare

class MchgnumCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mchgnum

class McountCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mcount

class MaccumCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.maccum

class Marff2csvCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.marff2csv

class MavgCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mavg

class MbucketCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mbucket

class MchgstrCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mchgstr

class McombiCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mcombi

class Mcsv2arffCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mcsv2arff

class MduprecCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mduprec

class MfsortCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mfsort

class MhashavgCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mhashavg

class MhashsumCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mhashsum

class MkeybreakCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mkeybreak

class MmbucketCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mmbucket

class MmvavgCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mmvavg

class MmvsimCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mmvsim

class MmvstatsCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mmvstats

class MnormalizeCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mnormalize

class MnulltoCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mnullto

class MpaddingCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mpadding

class MrandCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mrand

class MsedCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.msed

class MsepCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.msep

class Msep2Command(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.msep2

class MshuffleCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mshuffle

class MsimCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.msim

class MslideCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mslide

class MsplitCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.msplit

class MstatsCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mstats

class MsumCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.msum

class Mtab2csvCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mtab2csv

class MteeCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.m2tee

class MtonullCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mtonull

class MtraCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mtra

class MtrafldCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mtrafld

class MtraflgCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mtraflg

class MuniqCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.muniq

class MvcatCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mvcat

class MvcountCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mvcount

class MvdelimCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mvdelim

class MvdelnullCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mvdelnull

class MvnulltoCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mvnullto

class MvsortCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mvsort

class MvuniqCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mvuniq

class MwindowCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mwindow

class Mxml2csvCommand(MCommandI):
    @property
    def mcmd(self) -> Callable:
        return nm.mxml2csv

# 
# 1入力2出力
# 
class MselCommand(MCommandA):
    @property
    def mcmd(self) -> Callable:
        return nm.msel

class MselstrCommand(MCommandA):
    @property
    def mcmd(self) -> Callable:
        return nm.mselstr

class MselnumCommand(MCommandA):
    @property
    def mcmd(self) -> Callable:
        return nm.mselnum

class MselrandCommand(MCommandA):
    @property
    def mcmd(self) -> Callable:
        return nm.mselrand

class MbestCommand(MCommandA):
    @property
    def mcmd(self) -> Callable:
        return nm.mbest

class MdelnullCommand(MCommandA):
    @property
    def mcmd(self) -> Callable:
        return nm.mdelnull

# 
# 2入力1出力
#      
class MjoinCommand(MCommandV):
    """
    mjoinコマンド（きちんとコマンドをstoreに置いたら消そう）
    """
    @property
    def mcmd(self) -> Callable:
        return nm.mjoin

class MnjoinCommand(MCommandV):
    @property
    def mcmd(self) -> Callable:
        return nm.mnjoin

class MrjoinCommand(MCommandV):
    @property
    def mcmd(self) -> Callable:
        return nm.mrjoin

class MnrjoinCommand(MCommandV):
    @property
    def mcmd(self) -> Callable:
        return nm.mnrjoin

class MvjoinCommand(MCommandV):
    @property
    def mcmd(self) -> Callable:
        return nm.mvjoin

class MvreplaceCommand(MCommandV):
    @property
    def mcmd(self) -> Callable:
        return nm.mvreplace

class MvcommonCommand(MCommandV):
    @property
    def mcmd(self) -> Callable:
        return nm.mvcommon

class MpasteCommand(MCommandV):
    @property
    def mcmd(self) -> Callable:
        return nm.mpaste

class MproductCommand(MCommandV):
    @property
    def mcmd(self) -> Callable:
        return nm.mproduct

# 
# 2入力2出力
# 
class McommonCommand(MCommandX):
    @property
    def mcmd(self) -> Callable:
        return nm.mcommon

class MnrcommonCommand(MCommandX):
    @property
    def mcmd(self) -> Callable:
        return nm.mnrcommon

# 
# N入力1出力
# 
class McatCommand(MCommand):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('*', ['mcmd','matrix'])]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        from kskp.store import Matrix
        inputs_for_arg_i = []
        for key, input in inputs.items():
            if isinstance(input, (NysolModule, Matrix)):
                inputs_for_arg_i.append(input.content)
            else:
                # 一度nysol_module化する
                cmd = nm.m2tee(i=input.content)
                inputs_for_arg_i.append(cmd)

        if len(inputs_for_arg_i) == 0:
            # 入力データがない場合でも例外を送出しない
            return {'o': NysolModule(nm.m2tee(i='/dev/null'))}

        my_args = args.copy()
        my_args['i'] = inputs_for_arg_i
        cmd_o = nm.m2cat(my_args)
        return {'o': NysolModule(cmd_o)}

# 
# Mchkcsvコマンド
# 
class MchkcsvCommand(MCommand):
    """
    Mchkcsvコマンド
    nysol_pythonにCSV検証機能があるのでそれを利用しているが、おそらく非公開機能だと思われる
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'mcmd')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        def filter():
            import sys
            import nysol.util as util
            try:
                # i=''で入力に標準入力を指定する
                # local=Trueで結果を日本語で表示する
                util.mchkcsv(i='', nfn=args.get('nfn'), local=True)

                # flushをする
                sys.stdout.flush()
            except Exception as e:
                with open('/dev/stderr', 'w') as fpe:
                    import traceback
                    traceback.print_exc(file=fpe)
                    print(f'#ERROR# {str(e)}; TestCommand; ; ; ', file=fpe)
                raise

        cmd = inputs['i'].content
        cmd <<= nm.runfunc(filter)
        return {'o': NysolModule(cmd)}
