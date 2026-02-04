import sys
import copy
import nysol.mcmd as nm
from decimal import Decimal

from streamcat.core import Port, Tmp
from streamcat.store import NysolModule
from .script import PCommand

# shared functions for all IoT Commands
def generate_error_message(commandname, errcode, errfield, fieldinput, template_params={}):
    '''
    Function for creating error messages. 
    Pulls out error message templates, command name, and parameter info from
    self.const and then uses input to fill in templates

    generateCommanErrorMessage(command name, errcode, errfield, errinput, calcname)
    '''
    from string import Template

    errors = {
        # Field Name Errors
        'EmptyFieldNameError': '空文字列の項目名は指定できません。${fieldinput}',
        'FieldNameForbiddenCharacterError' : '半角の *　?　[　]　,　:　\\ は、項目名に使用できません。${fieldinput}',
        'FieldNotFoundError' : '指定した項目名は存在しません。${fieldinput}',
        'TargetFieldConflictError' : '同じ項目名が複数回指定されています。${fieldinput}',
        'FieldNameConflictError' : '追加する項目名は、すでに存在します。既存項目を置き換えていい場合は、上書きのチェックをONにします。置き換えない場合は、重複のない項目名を指定してください。${fieldinput}',
        'OutputNamesFormatError' : '指定された追加する項目の数は9個ではありません。9個の項目名をカンマ区切りで指定してください。${fieldinput}',

        # Time setting errors
        'TimeSettingMismatchError': '時間の指定は、時間軸のデータ型と一致しません。${correct_timeformat} で設定してください。${fieldinput}',

        # parameter errors
        'OutOfBoundsError' : '${errfield} への ${fieldinput} 指定が正しくありません。${correct_bounds} で指定してください。',
        'ParameterTypeError' : '${errfield} への ${fieldinput} 指定が正しくありません。${correct_type} を指定してください。',
        'EmptyParamError' : '空文字列の指定はできません。',
        'TimePrecisionError':'時間軸のデータ型が暦型(YYYYMMDDhhmmss.小数6桁まで)の場合の間隔は、小数6桁までの秒数を指定してください。 ${fieldinput}',

        # interpolation results error
        'InterpolateResultsConflictError' : '出力項目名が重複しています。対象項目、補間方法、結果項目で定まる出力項目名で、重複となる設定がないかを、確認してください。',
        # spans format error
        'SpansFormatError' : '時系列生成設定への指定が正しくありません。[開始1,終了1],[開始2,終了2],... で指定してください。 ${fieldinput}'
        
    }
    
    option_params = {
        'interval' : {
            'correct_bounds' : '正の数値',
            'correct_type' : '数値'
        },
        'start' : {
            'correct_type' : '数値'
        },
        'num' : {
            'correct_bounds' : '正の整数',
            'correct_type' : '数値'
        },
        't_dynamic_interval_num' : {
            'correct_bounds' : '正の数値',
            'correct_type' : '数値'
        },
        't_fixed_time' : {
            'correct_bounds' : '正の数値',
            'correct_type' : '数値'
        },
        'max_num' : {
            'correct_bounds' : '正の数値',
            'correct_type' : '数値'
        },
        'trim_num' : {
            'correct_bounds' : '正の数値',
            'correct_type' : '数値'
        }
    }
    
    template_strings = {'fieldinput' : fieldinput,
                        'errfield' : errfield,
                        **option_params.get(errfield, {}),
                        **template_params}

    message = Template(errors[errcode]).safe_substitute(template_strings)

    return f'【コマンド：{commandname}】【オプション欄：{errfield}】{message}'

class MeasurementPeriodIdentifyCommand(PCommand):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'mcmd')]
        self.o_ports = [Port('o', 'mcmd')]

    def dynamic_methods(self, method, add_flds):
        """
        グループのtopと間隔より、動的に停止区間を判定し、停止開始フラグ項目を追加したフローを返す
        引数
            method      UI設定の値（上位コマンドのargs）
            add_flds    項目名のキー値と項目名の辞書
        前提
            入力データは、Python listでは無く、Nysolの出力を受け取るとする。
            → None、nan、inf は、Nysolが '' に変換済とし、この関数内では、’’のみ対応とする
            → Opt入力欄からは、Pythonの float('nan')、float('inf') は、渡されないとする
        """
        import traceback
        import math

        try:
            headerflg = True

            for line in nm.mstdin().getline(header=True):
                if headerflg:
                    header = line
                    print(','.join(line + [ add_flds['fss'] ]))     # ヘッダー行出力
                    interval_loc = header.index( add_flds['interval'] )
                    top_loc = header.index( add_flds['top'] ) 
                    headerflg = False
                else:
                    # --- dynamic_ave ---
                    if method['c'] == 'dynamic_ave':
                        interval = line[interval_loc]
                        interval = float('nan' if interval == '' else interval)
                        if line[ top_loc ] == '1':  
                            # グループの先頭行
                            sum = interval
                            num = 1
                            ave = sum
                            fes = '0'
                        else:
                            float_check = ['','nan','NaN','NAN','inf','-inf','Inf','-Inf']
                            c_index = math.nan if method['t_dynamic_interval_num'] in float_check else float(method['t_dynamic_interval_num'])
                            if interval / (math.nan if ave == 0 else ave) >= c_index:
                                # 異常値による区分化 発生行
                                sum = interval
                                num = 1
                                ave = sum
                                fes = '0' if math.isnan(interval) else '1'
                            else:
                                sum = sum + interval
                                num = num +  (0 if math.isnan(interval) else 1)
                                ave = sum / num
                                fes = '0'
                    # --- << 追加ロジックを記述 >> 間隔に対する異常検知ロジック ---

                    print(','.join(line + [ fes ] ))

        except Exception as e:
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)
        finally:
            sys.__stdout__.flush()#not needed for bigger data

    def const(self, s):
        res = None

        if s == 'addflds':
            res = {
                'start' : '区間開始'   , 'end' : '区間終了',
                'interval' : '間隔', 
                'fos' : '稼働開始フラグ', 'foe' : '稼働終了フラグ' ,
                'fss' : '停止開始フラグ', 'fse' : '停止終了フラグ' ,
                'ido' : '稼働区間ID'   , 'ids' : '停止区間ID'
                }
        elif s == 'tmpflds':
            res = {
                'top'     : '__top__', 'bot' : '__bot__',
                'uxt'     : '__UXT__', 'int' : '__INT__', 'flac' : '__FLAC__',
                'uxt_sfx' : '_uxt'
                }
        elif s == 'a_opt_seq':
            # Opt欄 a= で入力される項目名の順序
            res = ['start','end','interval','fos','foe','fss','fse','ido','ids']

        return res


    def run(self, args, inputs):
        """
        引数
            overwrite   出力項目の上書き指定
            a           項目追加するカンマ区切りの9項目名
            ｋ          記入型：group
            time        記入型：項目名 *必須
            time_type   選択型：datetime, number
            c           選択型：dynamic_ave, fix
            t_dynamic_interval_num  記入型：数値
            t_fixed_time            記入型：数値
            q           真偽型：non-sorted
        処理
            if c = dynamic...  then  runfunc型  Python関数を使用
            if c = fix         then  Nysolのみ
        """
        # 定数定義
        aflds = self.const('addflds')       # 出力する項目名
        aflds_tmp = self.const('tmpflds')   # 内部で一時的に作成する項目名
        a_opt_seq = self.const('a_opt_seq') # Opt欄 a= で入力される項目名の順序

        args = copy.deepcopy(args)

        # --- 引数チェック ---
        # if parent command exists, take that name
        commandname = args.get('parent_command')
        if commandname is None:
            # if parent command does not exist, this is the parent command
            commandname = 'センサ時系列稼働停止判定'
            args['parent_command'] = commandname

        if 'c' not in args:
            msg = generate_error_message(commandname,
                            'EmptyParamError',
                            'c', '')
            raise Exception( msg )

        if args['c'] == 'dynamic_ave':
            if ('t_dynamic_interval_num' not in args) or (args['t_dynamic_interval_num'] == ''):
                msg = generate_error_message(commandname,
                                'EmptyParamError',
                                't_dynamic_interval_num', '')
                raise Exception(msg)
            
            dynamic_interval = args.get('t_dynamic_interval_num')
            try:
                dynamic_interval = float(dynamic_interval)
            except:
                msg = generate_error_message(commandname,
                                'ParameterTypeError',
                                't_dynamic_interval_num', 
                                args['t_dynamic_interval_num'])
                raise Exception(msg)

            if dynamic_interval <= 0:
                msg = generate_error_message(commandname,
                                'OutOfBoundsError',
                                't_dynamic_interval_num', 
                                args['t_dynamic_interval_num'])
                raise Exception(msg)
                
                
        
        if args['c'] == 'fix':
            if ('t_fixed_time' not in args) or (args['t_fixed_time'] == ''):
                msg = generate_error_message(commandname,
                                'EmptyParamError',
                                't_fixed_time', '')
                raise Exception(msg)

            fixed_interval = args.get('t_fixed_time')
            try:
                fixed_interval = float(fixed_interval)
            except:
                msg = generate_error_message(commandname,
                                'ParameterTypeError',
                                't_fixed_time', 
                                args['t_fixed_time'])
                raise Exception(msg)

            if fixed_interval <= 0:
                msg = generate_error_message(commandname,
                                'OutOfBoundsError',
                                't_fixed_time', 
                                args['t_fixed_time'])
                raise Exception(msg)

        if 'a' in args:
            a_list = args['a'].split(",")
            
            if len(a_list) == 9:
                for i, key in enumerate( a_opt_seq ):
                    this_a = a_list[i]
                    
                    # check for empty
                    if this_a == '':
                        msg = generate_error_message(commandname,
                                        'EmptyFieldNameError',
                                        'a', args['a'])
                        raise Exception(msg)
                        
                    # check for forbidden char
                    elif any(char in this_a for char in '*?[],:\\ '):
                        msg = generate_error_message(commandname,
                                                'FieldNameForbiddenCharacterError',
                                                'a', this_a)
                        raise Exception(msg)

                    aflds[key] = this_a

                # check for conflicts (same column specified)
                if len(a_list) != len(set(a_list)):
                    msg = generate_error_message(commandname,
                                    'TargetFieldConflictError',
                                    'a', args['a'])
                    raise Exception(msg)
                    
                    
            else:
                msg = generate_error_message(commandname,
                                'OutputNamesFormatError',
                                'a', args['a'])
                raise Exception(msg)

        # --- データ処理開始 ---
        time = args.get('time')
        time_type = args['time_type']

        f = None

        header = args.get('header')
        if header is None:
            # get all of the flow before this
            prev_flow = copy.deepcopy(inputs['i'].content)
            
            # put this into a tmpfile
            input_file = Tmp.create_file()
            input_filename = input_file.as_posix()
            
            prev_flow <<= nm.m2tee(o = input_filename)
            
            prev_flow_obj = NysolModule()
            prev_flow_obj.set_content(prev_flow)
            self.do_runs(prev_flow_obj) # run savetotmpfile
            
            # get header
            get_header = nm.m2tee(i = input_filename)
            
            get_header_module = NysolModule()
            get_header_module.set_content(get_header)
            header = self.get_field_names(get_header_module)

            f <<= nm.m2tee(i = input_filename)
        else:
            # if header is passed just read from input
            f <<= copy.deepcopy(inputs['i'].content)
            
        # --- ヘッダー情報が必要なチェック ---
        if 'k' in args:
            keys_list = args['k'].split(',')
           
            # key not found
            for key in keys_list:
                if key not in header:
                    msg = generate_error_message(commandname,
                                    'FieldNotFoundError',
                                    'k', key)
                    raise Exception(msg)

            if len(keys_list) != len(set(keys_list)):
                msg = generate_error_message(commandname,
                                'TargetFieldConflictError',
                                'k', args['k'])
                raise Exception(msg)

        if time is None:
            msg = generate_error_message(commandname,
                            'EmptyFieldNameError',
                            'time', time)
            raise Exception(msg)
        else:
            if time not in header:
                msg = generate_error_message(commandname,
                                'FieldNotFoundError',
                                'time', time)
                raise Exception(msg)

        # --- 出力項目の上書きモード ---
        tg_overwrite = list(aflds.values()) + list(aflds_tmp.values()) + [ time + aflds_tmp['uxt_sfx'] ]
        tg_overwrite = list( set(header) & set(tg_overwrite) )

        if 'overwrite' in args and args['overwrite']:
            f <<= nm.mcut(f= ','.join(tg_overwrite), r= True)
        elif len(tg_overwrite) > 0:
            msg = generate_error_message(commandname,
                            'FieldNameConflictError',
                            'a', ','.join(tg_overwrite))
            raise Exception(msg)

        # --- keybreak処理・sort処理 ---
        if 'k' in args:
            if 'q' not in args:
                if time_type == 'number':
                    f <<= nm.mkeybreak(a= f'{aflds_tmp["top"]},{aflds_tmp["bot"]}', k= args['k'], s= time + '%n')
                else:
                    f <<= nm.mkeybreak(a= f'{aflds_tmp["top"]},{aflds_tmp["bot"]}', k= args['k'], s= time)
            else:
                if time_type == 'number':
                    f <<= nm.mkeybreak(q= True, a= f'{aflds_tmp["top"]},{aflds_tmp["bot"]}', k= args['k'], s= time + '%n')
                else:
                    f <<= nm.mkeybreak(q= True, a= f'{aflds_tmp["top"]},{aflds_tmp["bot"]}', k= args['k'], s= time)
        else:
            if 'q' not in args:
                if time_type == 'number':
                    f <<= nm.msortf(f= time + '%n')
                else:
                    f <<= nm.msortf(f= time)
            f <<= nm.mcal(a= f'{aflds_tmp["top"]}', c= 'if(top(), 1, nulln())')
            f <<= nm.mcal(a= f'{aflds_tmp["bot"]}', c= 'if(bottom(), 1, nulln())')

        # ---- UNIX TIMEに変換 ---
        uxt_fld_name = time
        if time_type == 'datetime':
            f <<= nm.mcal(a= aflds_tmp['int'], c= f'uxt( s2t(regexstr($s{{{time}}},"^[0-9]{{14,14}}|^[0-9]{{6,6}}") ) )')
            f <<= nm.mcal(a= aflds_tmp['flac'], c= f'regexstr($s{{{time}}},"[.][0-9]{{0,6}}$")')
            f <<= nm.mcal(a= aflds_tmp['uxt'], c = f'if( isnull($s{{{aflds_tmp["flac"]}}}), $s{{{aflds_tmp["int"]}}}, $s{{{aflds_tmp["int"]}}}+$s{{{aflds_tmp["flac"]}}} )')
            f <<= nm.mcut(f= f"{aflds_tmp['int']},{aflds_tmp['flac']}", r = True)
            uxt_fld_name = aflds_tmp['uxt']

        # --- 出力項目の処理 ---
        f <<= nm.mcal(a= aflds['start'], c= f'$s{{{time}}}')

        if 'k' in args:
            f <<= nm.mslide(f= f'{time}:{aflds["end"]},{uxt_fld_name}', k=args['k'], t=1, n=True, q=True)
        else:
            f <<= nm.mslide(f= f'{time}:{aflds["end"]},{uxt_fld_name}',              t=1, n=True, q=True) 
            
        f <<= nm.mcal(a= aflds['interval'], c= f'${{{uxt_fld_name}1}} - ${{{uxt_fld_name}}}')

        if time_type == 'datetime':
            f <<= nm.mfldname(f= f"{uxt_fld_name}:{time}{aflds_tmp['uxt_sfx']}")
            f <<= nm.mcut(f= f"{aflds_tmp['uxt']}*", r = True)
        else:
            f <<= nm.mcut(f= f"{aflds_tmp['uxt']}*,{uxt_fld_name}1", r = True)


        """
        停止開始フラグの判定： 間隔の異常値判定方法は、今後、種類を追加する可能性あり
        """
        # method: fix
        if 'c' in args and (args['c'] == 'fix'):
            f <<= nm.mcal(a= aflds['fss'], 
                c=f'if( isnull( ${{{aflds["interval"]}}} ), 0, if( ${{{aflds["interval"]}}} >= {args["t_fixed_time"]}, 1, 0) )')

        # method: dyanamic_ave
        if 'c' in args and (args['c'] == 'dynamic_ave'):
            # 行の値により（動的に）、区分化と累計のリセットを行う runfunc 処理
            f <<= nm.runfunc(self.dynamic_methods, method=args, add_flds={**aflds, **aflds_tmp} )

        # --- 停止区間判定後の後処理 ---
        f <<= nm.mcal(a= aflds['fse'], 
            c=f'if( isnull( #{{{aflds["fss"]}}} ), 0, if( #{{{aflds["fss"]}}} == 1, 1, 0) )')
        f <<= nm.mcal(a= aflds['fos'], 
            c=f'if( ${{{aflds_tmp["top"]}}} == 1 && ${{{aflds["fss"]}}} == 0 || ${{{aflds["fse"]}}} == 1, 1, 0 )')
        f <<= nm.mcal(a= aflds['foe'], 
            c=f'if( ${{{aflds_tmp["bot"]}}} == 1 || ${{{aflds["fss"]}}} == 1, 1, 0 )')
        f <<= nm.mnullto(f= f'{aflds["fos"]},{aflds["foe"]}', v= '0')
        f <<= nm.maccum(f= f'{aflds["fos"]}:{aflds["ido"]},{aflds["fss"]}:{aflds["ids"]}', q= True)
        f <<= nm.mcut(f= f'{aflds_tmp["top"]},{aflds_tmp["bot"]}', r = True)


        nysol_module_o= NysolModule()
        nysol_module_o.set_content(f)
        return {'o': nysol_module_o}

class MissingValueInterpolateCommand(PCommand):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'mcmd')]
        self.o_ports = [Port('o', 'mcmd')]

    def interpolate_formula_topbot(self, keys, field, nextfield, methods, iplist, ipflds, args, aflds):
        """
        補間式の作成が、それに必要なデータ区間の両端のみで可能なものについて処理する
            対象手法： linear, next, nearrest
        引数
            keys     : 文字列    カンマ区切りのキーキー項目
            field    : 文字列    対象項目名（1つのみ）
            nextfield: 文字列    対象項目の次行の値を持つ項目名
            methods  : リスト    対象項目に適用する（複数可）
            iplist   : リスト    項目名のワイルドカード展開済の 補間式設定リスト（多重リスト）
                                [ [ 0, 'cubic_spline', '&_補間値', [fs1,fs2,...] ], [ ] ]
            ipflds   : リスト    補間式係数の規定の項目名を定義したリスト
            args     : 辞書      UIで与えられた引数
            aflds    : 辞書      出力項目名
        """
        import traceback
        import math

        try:
            headerflg = True

            # 追加する項目名の登録
            header_adds = []
            dm2 = '_'

            for m in methods:
                for i in [x for x in iplist if (x[1] == m) and (field in x[3]) ]:
                    if 'non_ip' in args:
                        if m == 'next':
                            for j in ['ip_0_next_pre', 'ip_0_next']:
                                tmp_field_name = field + ipflds[j]
                                header_adds.append( tmp_field_name )

                        if m == 'nearest':
                            for j in ['ip_0_near', 'ip_0_near_pre', 'ip_0_near_next']:
                                tmp_field_name = field + ipflds[j]
                                header_adds.append( tmp_field_name )                            

                        if m == 'linear':
                            for j in ['ip_1_1', 'ip_1_0']:
                                tmp_field_name = field + ipflds[j]
                                header_adds.append( tmp_field_name )
                    else:
                        tmp_field_name = i[2].replace('&', field + dm2 + m)
                        header_adds.append(tmp_field_name)


            for kb in nm.mstdin().keyblock(keys, header= True, q= True):
            # 注意： keyblock のキー指定は、実装k=、マニュアルkeys=
            #       将来修正される可能性あるため、第一引数の引数名は明示しない
                if headerflg:
                    header = kb[0]
                    print( ','.join(header + header_adds) )
                    headerflg = False
                else:
                    top_val = kb[0][ header.index(field) ]
                    bot_val = kb[-1][ header.index(nextfield) ]

                    top_flg = kb[0][ header.index(aflds['top']) ] == '1'
                    bot_flg = kb[-1][ header.index(aflds['bot']) ] == '1'

                    top_uxt = kb[0][ header.index( aflds['unix_time'] )]
                    bot_uxt = kb[-1][ header.index( aflds['unix_time_next']) ]
                    bot_pre_uxt = kb[-1][ header.index( aflds['unix_time']) ]

                    top_uxt = float('nan' if top_uxt == '' else top_uxt)
                    bot_uxt = float('nan' if bot_uxt == '' else bot_uxt)
                    bot_pre_uxt = float('nan' if bot_pre_uxt == '' else bot_pre_uxt)

                    
                    # ave_uxt should be null when values are all bad, 
                    # and the current keybreak comprises a full group
                    complete_key = top_flg and bot_flg
                    all_bad = all(val == '' for val in (x[ header.index(field)] for x in kb)) and complete_key
                    if all_bad:
                        ave_uxt = float('nan')
                    else:
                        if math.isnan(bot_uxt):
                            ave_uxt = ( top_uxt + bot_pre_uxt ) / 2
                        else:
                            ave_uxt = ( top_uxt + bot_uxt ) / 2

                    for rows in kb:
                        adds = []
                        now_val = rows[ header.index(field) ]

                        for m in methods:
                            for i in [x for x in iplist if(x[1] == m) and (field in x[3]) ]:
                                if 'non_ip' in args:
                                # 補間式を出力
                                    if m == 'next':
                                        val = top_val
                                        adds.append( '' if str(val) == 'nan' else str(val) )

                                        val = bot_val
                                        adds.append( '' if str(val) == 'nan' else str(val) )

                                    if m == 'nearest':
                                        #追加順： 'ip_0_near', 'ip_0_near_pre', 'ip_0_near_next'
                                        val = ave_uxt
                                        adds.append( '' if str(val) == 'nan' else str(val) )

                                        val = top_val
                                        adds.append( '' if str(val) == 'nan' else str(val) )

                                        val = bot_val
                                        adds.append( '' if str(val) == 'nan' else str(val) )

                                    if m == 'linear':
                                        # 追加順： ['ip_1_1', 'ip_1_0']
                                        if top_val != '' and bot_val != '':
                                            top_val = float('nan' if top_val == '' else top_val)
                                            bot_val = float('nan' if bot_val == '' else bot_val)
                                            ## 桁落ち対策として、式を変形 → 効果不明なため、外す
                                            # if bot_uxt - top_uxt == 0:
                                            #     a = float('nan')
                                            #     b = float('nan')
                                            # elif bot_val + top_val == 0:
                                            #     a = float('nan')
                                            #     b = float('nan')
                                            # elif bot_uxt**2 - top_uxt**2 == 0:
                                            #     a = float('nan')
                                            #     b = float('nan')
                                            # else:
                                            #     # 桁落ち対策で式を変形
                                            #     a = (bot_val**2 - top_val**2) / (bot_val + top_val)
                                            #     a = a / ((bot_uxt**2 - top_uxt**2) / (bot_uxt + top_uxt))
                                            #     b = (top_val**2 - (a * top_uxt)**2) / (top_val + a * top_uxt)
                                            if bot_uxt - top_uxt == 0:
                                                a = float('nan')
                                                b = float('nan')
                                            else:
                                                a = (bot_val - top_val) / (bot_uxt - top_uxt)
                                                b = top_val - a * top_uxt

                                            adds.append( str('' if math.isnan(a) else a) )
                                            adds.append( str('' if math.isnan(b) else b) )
                                        else:
                                            adds.append( '' )
                                            adds.append( '' )
                                else:
                                    # 補間値を出力
                                    if m == 'next':
                                        if now_val == '':
                                            val = bot_val
                                            adds.append( '' if str(val) == 'nan' else str(val) )
                                        else:
                                            val = now_val
                                            adds.append( '' if str(val) == 'nan' else str(val) )

                                    if m == 'nearest':
                                        if now_val == '':
                                            now_uxt = rows[ header.index( aflds['unix_time']) ]
                                            now_uxt = float('nan' if now_uxt == '' else now_uxt)

                                            if now_uxt <= ave_uxt:
                                                val = top_val
                                                adds.append( '' if str(val) == 'nan' else str(val) )
                                            elif now_uxt > ave_uxt:
                                                val = bot_val
                                                adds.append( '' if str(val) == 'nan' else str(val) )
                                            else:
                                                adds.append('')
                                        else:
                                            val = now_val
                                            adds.append( '' if str(val) == 'nan' else str(val) )

                                    if m == 'linear':
                                        if now_val == '':
                                            if top_val != '' and bot_val != '':
                                                now_uxt = rows[ header.index( aflds['unix_time']) ]
                                                now_uxt = float('nan' if now_uxt == '' else now_uxt)
                                                top_val = float('nan' if top_val == '' else top_val)
                                                bot_val = float('nan' if bot_val == '' else bot_val)
                                                if bot_uxt - top_uxt == 0:
                                                    a = float('nan')
                                                else:
                                                ## 桁落ち対策として、式を変形 → 効果不明なため、外す
                                                #     # 桁落ち対策で式を変形
                                                #     a = (bot_val**2 - top_val**2) / (bot_val + top_val)
                                                #     a = a / ((bot_uxt**2 - top_uxt**2) / (bot_uxt + top_uxt))
                                                    a = (bot_val - top_val) / (bot_uxt - top_uxt)

                                                val = a * now_uxt + top_val - a * top_uxt

                                                adds.append( str('' if math.isnan(val) else val) )
                                            else:
                                                adds.append( '' )
                                        else:
                                            val = now_val
                                            adds.append( '' if str(val) == 'nan' else str(val) )

                        print( ','.join( rows + adds) )


        except Exception as e:
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)
        finally:
            sys.__stdout__.flush()#not needed for bigger data



    def const(self, s):
        res = None

        if s == 'ipflds':
            # 補間式の要素名  対象項目に追加して、出力項目名を作成する
            res ={
                'ip_3_3':'__3次補間_3次', 'ip_3_2':'__3次補間_2次', 'ip_3_1':'__3次補間_1次', 'ip_3_0':'__3次補間_0次',
                'ip_3_x':'__3次補間_区間',
                'ip_1_1':'__1次補間_1次', 'ip_1_0':'__1次補間_0次',
                'ip_0_pre' : '__0次補間_前値'  ,
                'ip_0_next': '__0次補間_後値'  , 'ip_0_next_pre' : '__0次補間_後値_前値',
                'ip_0_near': '__0次補間_中間点', 'ip_0_near_pre' : '__0次補間_中間点_前値', 'ip_0_near_next' : '__0次補間_中間点_後値'
                }
        elif s == 'tmpflds':
            res = {
                'top'  : '__top__', 'bot' : '__bot__',
                'uxt'  : '__UXT__', 'int' : '__INT__', 'flac' : '__FLAC__',
                'uxt_sfx' : '_uxt',
                'dumyk': '__k__'  , 'gb_num': '__gb_num__', 
                'rb_id': '__rb_id__', 'rb_id_l': '__rb_id_l__' 
                }
        
        return res

    def make_iplist(self, args_iplist, ipflds, header, parent_command = ''):
        import fnmatch
        
        dm = '_'            # 補間値の出力項目名作成時の区切り文字

        iplist    = []      # ワイルドカード展開済補間設定：[ [ el, 'cubic_spline', '&_補間値', [fs1,fs2,...] ], [ ] ]
        ipoutlist = []      # 出力項目名：補間値  [f1,f2,f3,...]  ※ 項目名__method
        ipaddlist = []      # 出力項目名：補間式  [f1,f2,f3,...]

        if parent_command != '':
            commandname = parent_command
        else:
            commandname = self.commandname

        for elem in range(len(args_iplist)):
            field_list = []
            for field in args_iplist[elem]['ip_f'].split(','):
                matched = fnmatch.filter(header, field)
                
                if matched == []:
                    msg = generate_error_message(commandname,
                                    'FieldNotFoundError',
                                    'ip_f', field)
                    raise Exception(msg)
                
                field_list = field_list + matched
            
            if len(field_list) != len(set(field_list)):
                msg = generate_error_message(commandname,
                                'TargetFieldConflictError',
                                'ip_f', args_iplist[elem]['ip_f'])
                raise Exception(msg)
                

            ip_method = args_iplist[elem]['ip_c']  # 文字列
            ip_outfn  = args_iplist[elem]['ip_a']  # 文字列
            
            if any(char in ip_outfn for char in '*?[],:\\ '):
                msg = generate_error_message(commandname,
                                'FieldNameForbiddenCharacterError',
                                'ip_a', ip_outfn)
                raise Exception(msg)
            
            iplist.append( [elem, ip_method, ip_outfn, field_list] )

            for i in field_list:
                if ip_outfn != '':
                    tmp = args_iplist[elem]['ip_a'].replace('&', i + dm + ip_method)  # 文字列
                    
                    # check if final col already exists
                    if tmp in header:
                        msg = generate_error_message(commandname,
                                        'FieldNameConflictError',
                                        'ip_a', tmp)
                        raise Exception(msg)
                        
                    ipoutlist.append( tmp )

                if   ip_method == 'cubic_spline':
                    ipaddlist.append( i + ipflds['ip_3_3'] )
                    ipaddlist.append( i + ipflds['ip_3_2'] )
                    ipaddlist.append( i + ipflds['ip_3_1'] )
                    ipaddlist.append( i + ipflds['ip_3_0'] )
                    ipaddlist.append( i + ipflds['ip_3_x'] )                    
                elif ip_method == 'linear':
                    ipaddlist.append( i + ipflds['ip_1_1'] )
                    ipaddlist.append( i + ipflds['ip_1_0'] )
                elif ip_method == 'previous':
                    ipaddlist.append( i + ipflds['ip_0_pre'] )
                elif ip_method == 'next':
                    ipaddlist.append( i + ipflds['ip_0_next'] )
                    ipaddlist.append( i + ipflds['ip_0_next_pre'] )
                elif ip_method == 'nearest':
                    ipaddlist.append( i + ipflds['ip_0_near'] )
                    ipaddlist.append( i + ipflds['ip_0_near_pre'] )
                    ipaddlist.append( i + ipflds['ip_0_near_next'] )
        return iplist, ipoutlist, ipaddlist

    def run(self, args, inputs):
        """
        依存
            MeasurementPeriodIdentifyCommand()   内部で使用
        引数
            k           記入型：group
            time        記入型：項目名 *必須
            time_type   選択型：datetime, number
            q           真偽型：non-sorted
            mpi         真偽型：稼働・停止判定を行う
            c           選択型：dynamic_ave, fix
            t_dynamic_interval_num  記入型：数値
            t_fixed_time            記入型：数値
            iplist      リスト型
                ip_f        要素：補間の対象項目
                ip_c        要素：補間方法      cubic_spline,linear,previous,next,nearest
                ip_a        要素：補間の結果項目    &表記で項目名に置換
            max_num     記入型：3次スプライン式の計算時に参照する最大の行数
            trim_num    記入型：3次スプライン式の計算時に誤差とする端点からの件数
            non_ip      真偽型：欠損値の補間はせず、補間式の係数項目を追加する
        廃止 replace     真偽型：結果項目を追加せず、欠損値を補間値で上書きする
            overwrite   真偽型：追加する項目名が存在する場合、エラーとせず、上書きする
            a           追加する項目名 (固定の項目名) (省略可)
        出力
            稼働・停止判定      9項目
                'start','end','interval','fos','foe','fss','fse','ido','ids'
            補間式 (9項目)
                ip_3_3 ...      3次スプラインの係数値。 3次、2次、1次、0次、区間開始
                ip_1_1 ...      1次スプラインの係数値。 1次、0次
                ip_0_pre        前行の値
                ip_0_next       後行の値
                ip_0_near       区間の中間の時間軸の値
                ip_0_near_pre   前行の値
                ip_0_near_next  後行の値
            補間値
                ip_aの展開(複数項目)
        """
        debug = False

        # 定数定義
        dm2= '_'

        ipflds      = self.const('ipflds')    # 補間式の要素名   対象項目に追加する
        aflds_tmp   = self.const('tmpflds')   # 内部で一時的に作成する項目名

        # 実装している補間手法リスト
        #   type A  1行のデータから、補間処理が可能な手法
        #   type B  ブロック単位で、先頭と終端行の情報から、補間処理が可能な手法
        #   type C  理論的に全件を1度に処理する必要あるもで、データを分割した単位で、近似値を計算する手法
        method_type_a = ['previous']
        method_type_b = ['linear', 'next', 'nearest']
        method_type_c = ['cubic_spline']

        
        # initialize command name
        args = copy.deepcopy(args)
        
        # if parent command exists, take that name
        self.commandname = args.get('parent_command')
        if self.commandname is None:
            # if parent command does not exist, this is the parent command
            self.commandname = 'センサ時系列欠損値補間'
            args['parent_command'] = self.commandname

        # --- 出力する項目名 辞書 ---
        # 固定のキー  MeasurementPeriodIdentifyCommand.const('addflds')で定義
        #   'start' : '区間開始'   , 'end' : '区間終了',
        #   'interval' : '間隔', 
        #   'fos' : '稼働開始フラグ', 'foe' : '稼働終了フラグ' ,
        #   'fss' : '停止開始フラグ', 'fse' : '停止終了フラグ' ,
        #   'ido' : '稼働区間ID'   , 'ids' : '停止区間ID'            
        # 動的に追加するキー
        #   'unix_time'     ： time, time_type の指定により、動的に追加する
        #   'ipformulas'     ['xxxx_[ipflss]',''...] ： 対象項目名_補間式の要素名 のリスト
        cmd = MeasurementPeriodIdentifyCommand()
        aflds = cmd.const('addflds')
           
        # --- ヘッダー行だけ取得 ---
        f = None
        header = args.get('header')
        if header is None:
            # get all of the flow before this
            prev_flow = copy.deepcopy(inputs['i'].content)
            
            # put this into a tmpfile
            input_file = Tmp.create_file()
            input_filename = input_file.as_posix()
            
            prev_flow <<= nm.m2tee(o = input_filename)
            
            prev_flow_obj = NysolModule()
            prev_flow_obj.set_content(prev_flow)
            self.do_runs(prev_flow_obj) # run savetotmpfile
            
            # get header
            get_header = nm.m2tee(i = input_filename)
            
            get_header_module = NysolModule()
            get_header_module.set_content(get_header)
            header = self.get_field_names(get_header_module)

            f <<= nm.m2tee(i = input_filename)
        else:
            # if header is passed just read from input
            f <<= copy.deepcopy(inputs['i'].content)

        if debug:
            sys.stderr.write( 'header : ' + ','.join(header) + '\n' )

        # --- 引数チェック ---  補間の設定: 辞書のリスト型
        if 'iplist' in args and len(args['iplist']) > 0:
            for el in range( len(args['iplist']) ):
                if args['iplist'][el]['ip_f'] == '':
                    msg = generate_error_message(self.commandname,
                                    'EmptyFieldNameError',
                                    'ip_f', '')
                    raise Exception(msg)
                
                if 'non_ip' not in args and  args['iplist'][el]['ip_a'] == '':
                    msg = generate_error_message(self.commandname,
                                    'EmptyFieldNameError',
                                    'ip_a', '')
                    raise Exception(msg)
        else:
            msg = generate_error_message(self.commandname,
                            'EmptyParamError',
                            'iplist', '')
            raise Exception(msg)


        
        if debug:
            sys.stderr.write( 'ip_c[0]: ' + args['iplist'][0]['ip_c'] + '\n' )
 
        if 'k' in args:
            key_list = args.get('k').split(',')
            for key in key_list:
                if key not in header:
                    msg = generate_error_message(self.commandname,
                                    'FieldNotFoundError',
                                    'k', key)
                    raise Exception(msg)
            if len(key_list) != len(set(key_list)):
                msg = generate_error_message(self.commandname,
                                'TargetFieldConflictError',
                                'k', args['k'])
                raise Exception(msg)
                 
                    
        time = args.get('time')
        if time is None:
            msg = generate_error_message(self.commandname,
                            'EmptyFieldNameError',
                            'time', '')
            raise Exception(msg)
        elif time not in header:
            msg = generate_error_message(self.commandname,
                            'FieldNotFoundError',
                            'time', time)
            raise Exception(msg)
            
            
            

        # 出力項目名： 動的に追加  unix_time
        time_type = args['time_type']        

        if time_type == 'datetime':
            aflds['unix_time'] = time + aflds_tmp['uxt_sfx']
        else:
            aflds['unix_time'] = time

        # 出力項目名： 動的に追加  補間式
        # 出力項目名： 動的に追加  補間値
        iplist    = []      # ワイルドカード展開済補間設定：[ [ el, 'cubic_spline', '&_補間値', [fs1,fs2,...] ], [ ] ]
        ipoutlist = []      # 出力項目名：補間値  [f1,f2,f3,...]  ※ 項目名__method
        ipaddlist = []      # 出力項目名：補間式  [f1,f2,f3,...]

        iplist, ipoutlist, ipaddlist = self.make_iplist(
                args_iplist=args['iplist'], ipflds=ipflds, header=header)

        aflds['ipformulas'] = ipaddlist
        ipaddlist = None

        # --- データ処理開始 ---
        remove_fields = []          # 後始末用項目名
        keylist= []                 # k=, 稼働停止判定時の稼働区間IDをセット

        sorted = False

        # --- 出力項目名の重複処理 ---
        # header <-->  aflds['ipformulas'], ipoutlist
        if 'non_ip' in args:
            # 補間式を出力
            if len( set(aflds['ipformulas']) ) != len( aflds['ipformulas'] ):
                sys.stderr.write( 'ipformulas: ' + ','.join(aflds['ipformulas']) + '\n' )
                msg = generate_error_message(self.commandname,
                                'InterpolateResultsConflictError',
                                'ip_f,ip_c,ip_a', '')
                raise Exception(msg)

            if 'overwrite' in args:
                # 稼働停止判定の出力項目以外を、削除する
                if time_type == 'datetime':
                    tmp = set(header) & set(aflds['ipformulas'] + [aflds['unix_time']] + [aflds_tmp[x] for x in aflds_tmp]) 
                else:
                    tmp = set(header) & set(aflds['ipformulas']                        + [aflds_tmp[x] for x in aflds_tmp]) 

                if len( tmp ) > 0:
                    sys.stderr.write( 'removed: ' + ','.join(tmp) + '\n' )      
                    f <<= nm.mcut(f= ','.join(tmp), r= True)


            else:
                duplicates = set(header) & set(aflds['ipformulas'])
                if len( duplicates ) > 0:
                    msg = generate_error_message(self.commandname,
                                    'InterpolateResultsConflictError',
                                    'ip_f,ip_c,ip_a', duplicates.join(','))
                    raise Exception(msg)
        else:
            # 補間値を出力
            if len( set(ipoutlist) ) != len( ipoutlist ):
                sys.stderr.write( 'ipoutlist: ' + ','.join(ipoutlist) + '\n' )
                msg = generate_error_message(self.commandname,
                                'InterpolateResultsConflictError',
                                'ip_f,ip_c,ip_a', '')
                raise Exception(msg)

            if 'overwrite' in args:
                # 稼働停止判定の出力項目以外を、削除する
                tmp = set(header) & set(ipoutlist + [aflds['unix_time']] + [aflds_tmp[x] for x in aflds_tmp] ) 
                if len( tmp ) > 0:
                    sys.stderr.write( 'removed: ' + ','.join(tmp) + '\n' )      
                    f <<= nm.mcut(f= ','.join(tmp), r= True)
            else:
                duplicates = set(header) & set(ipoutlist)
                if len( duplicates ) > 0:
                    msg = generate_error_message(self.commandname,
                                    'InterpolateResultsConflictError',
                                    'ip_f,ip_c,ip_a', duplicates.join(','))
                    raise Exception(msg)


        if 'mpi' in args:
            # 稼働停止判定
            nysol_module_o= NysolModule()
            nysol_module_o.set_content(f)

            cmd = MeasurementPeriodIdentifyCommand()
            res = cmd.run(args=args,inputs={'i':nysol_module_o})

            f   = res['o'].content

            sorted = True
        elif time_type == 'datetime':
            # 生成する項目が既にあれば、削除する
            # mcutでは、存在しない項目指定はエラーだが、最後にワイルドカード※ で、回避する
            f <<= nm.mcut(f= f"{aflds['unix_time']}*,{aflds_tmp['int']}*,{aflds_tmp['flac']}*", r= True)

            # UNIX時間の追加
            f <<= nm.mcal(a= aflds_tmp['int'], c= f'uxt( s2t(regexstr($s{{{time}}},"^[0-9]{{14,14}}|^[0-9]{{6,6}}") ) )')
            f <<= nm.mcal(a= aflds_tmp['flac'], c= f'regexstr($s{{{time}}},"[.][0-9]{{0,6}}$")')
            f <<= nm.mcal(a= aflds['unix_time'], c = f'if( isnull($s{{{aflds_tmp["flac"]}}}), $s{{{aflds_tmp["int"]}}}, $s{{{aflds_tmp["int"]}}}+$s{{{aflds_tmp["flac"]}}} )')
            f <<= nm.mcut(f= f"{aflds_tmp['int']},{aflds_tmp['flac']}", r = True)
        else:
            pass

        # --- キー項目の設定 ---
        # key項目の整備  k=が無い場合は、ダミー項目を k= にセットする
        arg_k = None

        if 'k' in args:
            arg_k = args['k']
            keylist.append(arg_k)
        else:
            arg_k = aflds_tmp['dumyk']
            f <<= nm.msetstr(a= arg_k, v= '1')
            keylist.append(arg_k)
            remove_fields.append( arg_k )

        # 停止判定時は、args['k'] へ、稼働区間ID aflds['ido'] を加える
        str_keys = ','.join(keylist)      # mコマンドは、カンマ区切り文字列で与える

        if 'mpi' in args:
            keylist.append(aflds['ido'])
            str_keys = str_keys + ',' + aflds['ido']

        if sorted:
            f <<= nm.mkeybreak(a= f'{aflds_tmp["top"]},{aflds_tmp["bot"]}', k= str_keys, q= True)
        else:
            if time_type == 'datetime':
                tmp = args['time']
            else:
                tmp = args['time'] + '%n'

            f <<= nm.mkeybreak(a= f'{aflds_tmp["top"]},{aflds_tmp["bot"]}', k= str_keys, s= tmp)

        remove_fields.append( aflds_tmp["top"] )
        remove_fields.append( aflds_tmp["bot"] )


        # --- 補間処理 ---
        # iplist： [ [ el, 'cubic_spline', '&_補間値', [fs1,fs2,...] ], [ ] ]

        if debug:
            import pprint
            pprint.pprint(args['iplist'],stream=sys.stderr)


        methods = [ x[1] for x in iplist ]
        if debug:
            sys.stderr.write( 'methods : ' + ','.join(methods) + '\n' )


        # 共通処理： UNIX時間の先1行取得  ※ TypeA 以外で、共通に使用する
        terget_methods = method_type_b + method_type_c  # type_a 以外

        if len( set(methods) & set(terget_methods) ) > 0:
            aflds_tmp['unix_time_next'] = aflds['unix_time'] + '_next'
            f <<= nm.mslide(k= ','.join(keylist),
                            f= f'{aflds["unix_time"]}:{aflds_tmp["unix_time_next"]}',
                            n=True, q=True, l=True)
            remove_fields.append( aflds_tmp['unix_time_next'] )


        # Type A: 理論的にストリーミング処理で実装可能なものを記述する
        if len( set(methods) & set(method_type_a) ) > 0:

            if 'previous' in methods:
                # 補間式 ： 当該行の値
                this_method = 'previous'

                params = [ x for x in iplist if x[1] == this_method ]
                # tmp_flds = [ x for y in params for x in y ]  # 多重の項目リストを、1次元リスト化

                # i is one element in iplist, corresponding to a 'previous value'
                # interpolation calculation
                for i in params:
                    # j refers to one set of output column names (list)
                    for j in i[3]:
                        if 'non_ip' in args:
                            tmp_field_name = j + ipflds['ip_0_pre']
                        else:
                            tmp_field_name = i[2].replace('&', j + dm2 + this_method)

                        top = aflds_tmp['top']
                        f <<= nm.mcal(a= tmp_field_name,
                                c= f'if(isnull($s{{{j}}}), if($s{{{top}}}=="1","",#s{{}}), $s{{{j}}})')

        # Type B: 欠損値が連続する場合にストリーミング処理できないため、欠損値の連続行数に最大値を設定し、この単位内で処理する
        if len( set(methods) & set(method_type_b) ) > 0:
            # --- 読込ブロック単位の設定 ---
            # max_num   : runfunc内の関数で、一度に処理する、最大行数
            # pb_id_tmp_xxx
            # pb_num_xxx
            # pb_id_xxx
            top  = aflds_tmp['top']
            bot  = aflds_tmp['bot']
            max_num = args.get('max_num')

            if max_num is None:
                msg = generate_error_message(self.commandname,
                                'EmptyParamError',
                                'max_num', '')
                raise Exception(msg)

            params = [ x for x in iplist if x[1] in method_type_b ]
            fields = list( set( [x for y in params for x in y[3]] ) )   # 重複なしの対象項目リスト

            for i in fields:
                """
                計算の流れ
                    欠損値無しの行    ･･･ 行ごとに、補間式を算出
                    欠損値のブロック  ･･･ 欠損値の前行の値、欠損ブロックの行、欠損ブロック最後の後値 を元に、補間式、補間値 を算出する
                    ただし、最大行数 を超える場合は、処理するブロックを、最大行数を超えないように、分割する
                処理の流れ
                    対象の数値項目ごとに、
                    上記の計算を行うために、必要な行のブロック単位にIDを付与し、
                    runfuc() にて、補間式・補間値 を算出する
                
                -- 項目の説明 --
                top         グループ項目の先頭行 = 1
                pbid_tmp    欠損の前値〜欠損中の行に、同じ番号を付与する
                                対象項目の当行が、グループ先頭なら 1、欠損でないなら 前値+1、欠損なら 前値 をセット
                pbn         欠損中の行に、連番を付与する
                pbid        欠損の前値〜欠損中のブロックに対して、最大件数の単位で分割した、連番を添えて、IDを付与する
                                値＝[pbid_tmp]-[int(pbn/max_num)] 
                """
                pbid   = 'pb_id_' + i           # 最大行数によるブロック化用のID付与
                pbnext = 'pb_next_' + i         # 対象項目の次行の値
                aflds_tmp[pbid] = pbid
                aflds_tmp[pbnext] = pbnext
                remove_fields.append( pbid )
                remove_fields.append( pbnext )

                pbid_tmp = 'pb_id_tmp_' + i
                pbn = 'pb_id_num_' + i

                f <<= nm.mcal(a= pbid_tmp, c= f'if(isnull(${{{top}}}), if(isnull(${{{i}}}), #{{}}, #{{}}+1), 1)')
                f <<= nm.mcal(a= pbn,      c= f'if(isnull(${{{top}}}), if(${{{pbid_tmp}}}==#{{{pbid_tmp}}}, #{{}}+1, 0) ,0)' )
                f <<= nm.mcal(a= pbid,     c= f'$s{{{pbid_tmp}}} + "-" + n2s(int(${{{pbn}}}/{max_num}) )' )
                del_list = [pbid_tmp, pbn]
                f <<= nm.mcut(f= ','.join(del_list), r= True)                
                f <<= nm.mslide(k= ','.join(keylist), f= f'{i}:{pbnext}', n=True, q=True, l=True)

                methods_input = [ x[1] for x in params if i in x[3] ]

                # --- 補間式の計算 ---
                keys = ','.join( keylist + [pbid] )
                f <<= nm.runfunc(self.interpolate_formula_topbot,
                        keys=keys, field=i, nextfield=pbnext, methods=methods_input, 
                        iplist=iplist, ipflds=ipflds, args=args, aflds={**aflds, **aflds_tmp} )

                if debug:
                    sys.stderr.write( 'TypeB methods : ' + i + ' : ' + ','.join(methods_input) + '\n' )
                    sys.stderr.write( 'TypeB keys    : ' + i + ' : ' +  keys + '\n' )



        # Type C: 理論的にストリーミング処理できないものは近似として、最大の読込行数を設定し、この単位を逐次読込ながら処理を行う
        if len( set(methods) & set(method_type_c) ) > 0:
            methods_input = []    # Type C で処理する手法の中で、Opt欄で指定された 手法のリストを格納する

            if 'cubic_spline' in methods:
                methods_input.append('cubic_spline')


            """
            要件
                ・処理効率：大規模データをブロックに分割して処理する
                ・処理効率：複数列が対象の場合、計算効率向上をしたい
                ・精度：ブロックの両端点で、誤差が生じるため、ブロック間で、一部のデータを重複させて補間式を求める
                ・手順：補間式を求める場合、欠損値は除外して、有効値のみで補間式を求めたあとで、欠損値を計算する
                ・問題：欠損値は、項目ごとに決まるので、複数列で、行を同期した処理は困難

            計算の流れ
              定数
                ・max_num   3次スプライン式の計算時にブロック化する行数
                ・trim_num  3次スプライン式の計算時に誤差とする端点からの件数
              グループ化
                ・top       グループ項目の先頭行 = 1
                ・bot       最終行 = 1
              行ブロックにID付与
                ・gbn       gb_num、グループ内の 0 始まりの連番
                ・rbid      rb_id、max_num単位で行をブロック化し、0 始まりの連番を付与した、行ブロック単位のID
                ・rbid_l    実際に補間式を求める時に使用する行のブロック単位のID。 rbidに、末端、先頭のtrim_num件を重複して付加する
              行単位に付与する属性
                ・rbid_top  rbidブロックの末尾から trim_num 件の行に、 rbid - 1 をセット 

            処理の流れ
              Step 1 ブロック化のために、フラグを設定する
                     mcmd
              Step 2 ブロックごとに、近似誤差対策のために、両端点に、データ行を追加（重複データ）する
                     runfunc  self.rows_generator
              Step 3 ブロックごとに、補間値を算出し、重複データ部分を除外して、出力する
                     runfunc  self.interpolate_formula
            """
            # -- 引数チェック ---
            max_num = None
            trim_num = None

            if 'max_num' in args: 
                max_num = args.get('max_num')
                try:
                    max_num = int( float(max_num.replace(',','')) )
                except Exception as e:
                    msg = generate_error_message(self.commandname,
                                    'ParameterTypeError',
                                    'max_num', args['max_num'])
                    raise Exception(msg)

                if max_num <= 0:
                    msg = generate_error_message(self.commandname,
                                    'OutOfBoundsError',
                                    'max_num', args['max_num'])
                    raise Exception(msg)
                    

            else:
                msg = generate_error_message(self.commandname,
                                'EmptyParamError',
                                'max_num', '')
                raise Exception(msg)

            if 'trim_num' in args: 
                try:
                    trim_num = int( float(args['trim_num'].replace(',','')) )
                except Exception as e:
                    msg = generate_error_message(self.commandname,
                                    'ParameterTypeError',
                                    'trim_num', args['trim_num'])
                    raise Exception(msg)
                finally:
                    pass

                if trim_num <= 0:
                    msg = generate_error_message(self.commandname,
                                    'OutOfBoundsError',
                                    'max_num', args['max_num'])
                    raise Exception(msg)

            else:
                msg = generate_error_message(self.commandname,
                                'EmptyParamError',
                                'trim_num', '')
                raise Exception(msg)


            params = [ x for x in iplist if x[1] in methods_input ]
            fields = list( set( [x for y in params for x in y[3]] ) )   # 重複なしの対象項目リスト

            if len(fields) > 0:
                # --- 読込ブロック単位の設定 ---
                # max_num   : runfunc内の関数で、一度に処理する、最大行数
                # gb_num    : keysのキー単位内での行の連番
                # rb_id     : keysのキー単位内で、max_num単位でのID
                # rb_id_l   : このキー単位で補間式を求める (rb_idの単位の前後に重複行を付加したものの連番)
                top = aflds_tmp['top']      # keybreak にて作成済
                bot = aflds_tmp['bot']      # keybreak にて作成済
                gbn = aflds_tmp['gb_num']
                rbid= aflds_tmp['rb_id']
                rbid_l= aflds_tmp['rb_id_l']

                remove_fields.append( gbn )
                remove_fields.append( rbid )
                remove_fields.append( rbid_l )

                f <<= nm.mcal(a= gbn , c= f'if(isnull(${{{top}}}), #{{}}+1, if( ${{{top}}}==0, 0, 0) )')
                f <<= nm.mcal(a= rbid, c= f'int(${{{gbn}}}/{max_num})')

                # -- 補間式算出用に 一部 重複行 を作成する --
                rg_ags = {}
                rg_ags['max_num'] = max_num
                rg_ags['trim_num'] = trim_num
                rg_ags['top'] = top
                rg_ags['bot'] = bot            
                rg_ags['gbn'] = gbn
                rg_ags['rbid'] = rbid
                rg_ags['rbid_l'] = rbid_l

                f <<= nm.runfunc(self.rows_generator, args=rg_ags)
            
                # --- 補間式の計算 ---
                keys = ','.join( keylist + [rbid_l] )
                f <<= nm.runfunc(self.interpolate_formula, 
                        keys=keys, rbid=rbid, rbid_l=rbid_l, methods=methods_input,
                        iplist=iplist, ipflds=ipflds, args=args, aflds={**aflds, **aflds_tmp} )
        
                if debug:
                    sys.stderr.write( 'TypeC methods : ' + ','.join(methods_input) + '\n' )
                    sys.stderr.write( 'TypeC keys    : ' +  keys + '\n' )
                    sys.stderr.write( 'TypeC time    : ' +  aflds['unix_time'] + '\n' )



        # --- 不要列の削除 ---
        # comment out to see intermediate columns (to see pbid etc)
        if len( remove_fields ) > 0:
            f <<= nm.mcut(f= ','.join(remove_fields), r= True)

        nysol_module_o= NysolModule()
        nysol_module_o.set_content(f)
        return {'o': nysol_module_o}

    def interpolate_formula(self, keys, rbid, rbid_l, methods, iplist, ipflds, args, aflds):
        """
        補間式の作成が、理論上は全件必要だが、近似法として、部分データに分割して求める
            対象手法：  cubic_spline
        pandas活用
        引数
            keys    リスト      キー項目名のリスト。このグループ単位で、補間式の計算を行う。 rbid_l 単位 
            rbid    文字例      補間結果を出力する単位 
            rbid_l  文字例      補間計算を行う単位
            methods リスト      対象手法。 前提：呼出元で、この関数で処理可能な手法のみ指定されていること
            iplist  リスト      項目名のワイルドカード展開済の 補間式設定リスト（多重リスト）
                                [ [ 0, 'cubic_spline', '&_補間値', [fs1,fs2,...] ], [ ] ]
            ipflds  リスト      補間式係数の規定の項目名を定義したリスト
            args    辞書        UIで与えられた引数
            aflds   辞書        出力項目名
        出力

        """
        import traceback
        import pandas as pd
        import numpy as np
        from scipy.interpolate import CubicSpline


        # 3次スプライン補間式の変形
        # 引数
        #   x           リスト      scipy.interpolate.CubicSpline()出力   obj.x  区間の開始のx値のリスト
        #   formulas    多重リスト   scipy.interpolate.CubicSpline()出力   obj.c  PPoly形式の区分3次補間式群の係数
        # 戻値
        #   DataFrame   各区間の xと係数値   列の意味：区間の開始x値, 定数項, 1次の係数, 2次の係数, 3次の係数  
        def deforming_interpolation_coeff(x, formulas):
            x_p = np.array(x[:-1])
            c0 = np.array(formulas[3])
            c1 = np.array(formulas[2])
            c2 = np.array(formulas[1])
            c3 = np.array(formulas[0])

            res = pd.DataFrame(
                np.array( [x_p, c0, c1, c2, c3] ).T,
                columns = ['x_p', 'coef_c0', 'coef_c1', 'coef_c2', 'coef_c3']
                )

            return res

        try:
            header = None
            data = None
            
            # args引数：non_ip      真偽型：欠損値の補間はせず、補間式の係数項目を追加する
            if 'non_ip' in args:
                non_ip = True
            else:
                non_ip = False

            # adflds引数
            time = aflds['unix_time']
            

            # --- 
            # iplist  ワイルドカード展開済補間設定：[ [ el, 'cubic_spline', '&_補間値', [fs1,fs2,...] ], [ ] ]
            #   
            params = [ x for x in iplist if x[1] in methods ]           # methodsで指定されたもののみ抽出
            fields = list( set( [x for y in params for x in y[3]] ) )   # 重複なしの対象項目リスト
 
            cubic_spline_params = [ x for x in iplist if x[1] == 'cubic_spline' ]
            cubic_spline_fields = list( set( [x for y in cubic_spline_params for x in y[3]] ) ) 

            """
            処理の構成




            """
            # 追加する項目名の登録
            header_adds = []
            dm2 = '_'

            for f in fields:
                for m in methods:
                    for i in [x for x in iplist if (x[1] == m) and (f in x[3]) ]:
                        if non_ip:
                            if m == 'cubic_spline':
                                for j in ['ip_3_x','ip_3_3', 'ip_3_2', 'ip_3_1', 'ip_3_0']:
                                    tmp_field_name = f + ipflds[j]
                                    header_adds.append( tmp_field_name )
                        else:
                            tmp_field_name = i[2].replace('&', f + dm2 + m)
                            header_adds.append(tmp_field_name)

            """
            データ構成： pandas
                df_keyblock     1回の反復で取得した入力データを格納し、出力列を追加し、最後にprintする

            補間の方針
                補間値の算出        pandas機能（SciPyのラッパー） interpolate() を使用する
                補間式の係数の算出   SciPy の CubicSpline() を使用する  ※ pandasでは不可のため
                https://pandas.pydata.org/docs/search.html?q=interpolate+   interpolate() マニュアル
                http://purple-apple.hatenadiary.jp/entry/2018/02/26/131258   SciPyでの補間式取得方法

            処理の方針
                ・元データの値は更新せず、新規の列追加のみとする
                ・pandas DataFrame は、コピーせずに元データを変更する  (メモリの節約。適宜 inplace=True 指定）
                ・無効値処理は、都度、計算対象項目の 数値データだけを抽出し、欠損値に置換し、補間処理を行う
                  欠損値の判定、置換は、pandas の機能を使用する   pd.isnull()
                ・スプライン補間は、数値 が前提だが、pandas既定の欠損値と、指定した文字列 を無効と判断する
            """
            is_header = True
            kb_counter = 0      # keyblock の反復数のカウント。 rbid引数とマッチさせて、出力範囲の制御に使用

            for kb in nm.mstdin().keyblock(keys, header= True, q= True):
            # keyblock のキー指定は、実装k=、マニュアルkeys=
            # 将来修正される可能性あるため、第一引数の引数名は明示しない
            # 入力データ： 2重リスト型。 反復1回目： ヘッダ行の2重リスト  反復2回目以降： keyblock単位のデータ行の2重リスト  
            # 欠損値は、'' で与えられる
                
                df = None
                kb_counter = kb_counter + 1

                if is_header:
                    header = kb[0]
                    print( ','.join(header + header_adds) )
                    is_header = False
                else:
                    # 注意： ヘッダー行の作成と、同じ順番で、項目を追加する必要あり
                    # for 実際に指定されている手法別
                    #   for その手法を指定している項目別
                    #       if 補間値 計算 ・・・ 欠損値除外して、補間式計算し、欠損値は補間して出力
                    #       if 補間式 計算 ・・・ 欠損値除外して、補間式計算し、行区間を判定し対応する補間式を出力
                    # 補足： 有効件数の閾値について
                    #   理論的には、有効件数 3件 以上が必要
                    #   ただし、挙動が不安定で SciPyエラーも起きたため、4件以上 を閾値とした

                    for mi in methods:
                        df = pd.DataFrame(kb,columns=header)

                        if 'cubic_spline' in methods:
                            flds_num = 5      # 1つの算出で、出力する項目の数 （3次式 = 4+1）
                            fi_counter = -1   # 補間対象項目 fields の反復数のカウント

                            for fi in cubic_spline_fields:
                                fi_counter = fi_counter + 1
                             
                                if non_ip:  # 補間式 係数
                                    #--------------------------------
                                    # http://purple-apple.hatenadiary.jp/entry/2018/02/26/131258      SciPyでの補間式取得方法 を使用
                                    #--------------------------------

                                    # 時間軸、補間対象列 のdfを作成し、無効値をNaNに変換する
                                    df_target = df[ [time, fi] ] 
                                    df_target[fi]   = pd.to_numeric( df_target[fi],   errors='coerce')
                                    df_target[time] = pd.to_numeric( df_target[time], errors='coerce')

                                    # 無効値の行、有効値の行を、記録する
                                    # 有効： 欠損でない and 時間軸が次の時間と異なる   ※ 時間軸重複時は、先頭のみ有効とする
                                    # 無効： 有効でないもの
                                    valid_data   = None    # 有効値のインデックス
                                    invalid_data = None    # 無効値のインデックス   #.index.values 

                                    valid_data   = df_target[ -(df_target[fi].isnull())  & (df_target[time] != df_target[time].shift(1))  ] 
                                    invalid_data = df_target[  (df_target[fi].isnull())  | (df_target[time] == df_target[time].shift(1))  ]  


                                    # if there are enough points, use CubicSpline
                                    if len(valid_data[time]) >= 4:
                                        cubic_formulas = CubicSpline( valid_data[time], valid_data[fi] ) 
                                        df_coef = deforming_interpolation_coeff(cubic_formulas.x, cubic_formulas.c) 

                                        # スライスで、代入するために、インデック名を、代入先と同じものにする
                                        # 注意： alid_data.index[:-1] ･･･spline補間では、最後のデータの係数は、出力されない  （入力件数 - 1）
                                        df_coef.set_index( valid_data.index[:-1], drop=False, inplace=True)
                                    else:
                                        # if not enough points, produce null output
                                        # df_coef has the same shape as the output of 
                                        # deforming_interpolation_coeff, but all null
                                        df_coef = pd.DataFrame(
                                            np.array( [[np.nan]]*5 ).T,
                                            columns = ['x_p', 'coef_c0', 'coef_c1', 'coef_c2', 'coef_c3'])


                                    # 係数列を追加
                                    df[ header_adds[flds_num * fi_counter]   ] = float('nan')   # 区間開始
                                    df[ header_adds[flds_num * fi_counter+1] ] = float('nan')   # 3次係数
                                    df[ header_adds[flds_num * fi_counter+2] ] = float('nan')   # 2次
                                    df[ header_adds[flds_num * fi_counter+3] ] = float('nan')   # 1次
                                    df[ header_adds[flds_num * fi_counter+4] ] = float('nan')   # 定数

                                    df.loc[ valid_data.index, header_adds[flds_num * fi_counter]   ] = df_coef['x_p']
                                    df.loc[ valid_data.index, header_adds[flds_num * fi_counter+1] ] = df_coef['coef_c3']
                                    df.loc[ valid_data.index, header_adds[flds_num * fi_counter+2] ] = df_coef['coef_c2']
                                    df.loc[ valid_data.index, header_adds[flds_num * fi_counter+3] ] = df_coef['coef_c1']
                                    df.loc[ valid_data.index, header_adds[flds_num * fi_counter+4] ] = df_coef['coef_c0']

                                    # 係数値の前行での補間　注意：inplace=True では、上手くいかないので、代入で実装
                                    df[       [header_adds[flds_num * fi_counter],header_adds[flds_num * fi_counter+1],header_adds[flds_num * fi_counter+2],header_adds[flds_num * fi_counter+3],header_adds[flds_num * fi_counter+4]] 
                                      ] = df[ [header_adds[flds_num * fi_counter],header_adds[flds_num * fi_counter+1],header_adds[flds_num * fi_counter+2],header_adds[flds_num * fi_counter+3],header_adds[flds_num * fi_counter+4]]
                                            ].fillna(method='ffill') 

                                else:       # 補間値
                                    #--------------------------------
                                    # pandas.interpolate() による補間値算出
                                    #   スプライン補間のx軸として、インデックスへ、時間軸を設定する
                                    #   https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.interpolate.html?highlight=interpolate
                                    # 無効値処理
                                    #   pd.to_numeric() にて、数値に変換できないものを、NaNに変換する
                                    #--------------------------------
                                    df[ header_adds[fi_counter] ] = pd.to_numeric( df[fi],   errors='coerce')

                                    if fi_counter < 1:
                                        df[ time ]                = pd.to_numeric( df[time], errors='coerce')
                                        df.set_index(time, drop=False, inplace=True)

                                    # 有効件数： 3件未満は、補間値でなく、元の入力値をセットする
                                    # 時間軸、補間対象列 のdfを作成し、無効値をNaNに変換する
                                    df_target = df[ [time, fi, header_adds[fi_counter]] ] 
                                    df_target[fi]   = pd.to_numeric( df_target[fi],   errors='coerce')

                                    # 欠損値の行、有効値の行を、記録する
                                    valid_data   = None    # 有効値のインデックス
                                    valid_data_not_null = df_target[  ~( df_target[fi].isnull()) == True ] 
                                    valid_data_not_dup  = df_target[ df_target[time] != df_target[time].shift(1) ] 

                                    # if there are enough points, use CubicSpline
                                    # 時間軸に重複ありへの対処
                                    #   時間軸の重複を除外したDataFrameを作成し、Pandasで補間し、結果を元のDataFrameに上書きする
                                    #   重複時間は、同じ値がコピーされる
                                    #   注意：Pandasスプライン補間の機能では、DataFrameの全体で、時間軸に重複ないことが前提になっている
                                    #        スライスのような抽出データに対して補間すると、エラーになる
                                    if len(valid_data_not_null[time]) >= 4:
                                        if len(df[time]) == len(valid_data_not_dup[time]):
                                            df[ header_adds[fi_counter] ].interpolate(method='cubic', axis=0, inplace=True)
                                        else:
                                            valid_data_not_dup.set_index(time, drop=False, inplace=True)
                                            valid_data_not_dup[ header_adds[fi_counter] ].interpolate(method='cubic', axis=0, inplace=True)
                                            df.loc[ df.index, header_adds[fi_counter] ] = valid_data_not_dup[ header_adds[fi_counter] ]
                                    else:
                                        pass
                    
                    if df is not None:
                        # 出力範囲： rbid == rbid_l
                        
                        # replace inf, -inf, nan with ''
                        df.replace([np.inf, -np.inf, np.nan], '', inplace = True)
                        
                        list_df = df[ df[rbid] == df[rbid_l] ].values.tolist()

                        for i in range( len(list_df) ):
                            print(  ','.join( [ str(x) for x in list_df[i] ] ) )


        except Exception as e:
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)
        finally:
            sys.__stdout__.flush()#not needed for bigger data


    def rows_generator(self, args):
        """
        意図
            3次スプラインをブロック分割で計算する上で、
            近似精度の低いブロックの両端を除外した残りのブロックだけ、補間値を出力するために、
            各スプライン計算時のブロックの両端にあたる部分のレコードを複写したデータ（rbid_l）に対して、
            3次スプラインを反復して計算するが、各反復において、両端を除いた残り（rbid）だけ、出力する
        処理
            max_num件数ごとにブロック化された入力データ（ID：rbid）に対して、
            可能な限り、trim_num -> max_num -> trim_num で、1つのブロック（ID: rbid_l、件数：最大で max_num + 2*trim_num件）
            となるように、trim_num件数部分を重複して生成したデータを出力する
        引数
            max_num   文字型（数値）    3次スプライン式の計算時にブロック化する行数
            trim_num  文字型（数値）    3次スプライン式の計算時に誤差とする端点からの件数
            top       文字型（列名）
            bot       文字型（列名）
            gbn       文字型（列名）
            rbid      文字型（列名）
            rbid_l    文字型（列名）
        出力
            入力の全項目 , rbid_l
        """
        import traceback

        try:
            max_num  = args['max_num']
            trim_num = args['trim_num']
            top = args['top']
            bot = args['bot']
            gbn = args['gbn']
            rbid   = args['rbid']
            rbid_l = args['rbid_l'] 

            add_bot = []
            add_top = []

            headerflg = True

            for line in nm.mstdin().getline(header=True):

                if headerflg:
                    header = line
                    print(','.join(line + [rbid_l] ))     # ヘッダー行出力

                    idx_top = header.index( top )
                    idx_bot = header.index( bot )
                    idx_gbn = header.index( gbn )
                    idx_rbid = header.index( rbid )

                    headerflg = False
                else:
                    val_rbid_l = None
                    val_top = line[ idx_top ]
                    val_bot = line[ idx_bot ]
                    val_gbn = line[ idx_gbn ]
                    val_rbid = line[ idx_rbid ]

                    if int(val_gbn)+1  - int(max_num) * int(val_rbid) <= trim_num:
                        if val_rbid == '0':
                            val_rbid_l = val_rbid
                            add_top = []
                            add_bot = []
                        else:
                            # rbid内、先頭から trim_num 行
                            add_bot.append(line)
                            val_rbid_l = str(int(val_rbid) - 1)

                        print(','.join(line + [val_rbid_l] ))

                    elif int(val_gbn)  < int(max_num) * (int(val_rbid) + 1) - trim_num:
                        # rbid内、真ん中の trim_num 行
                        val_rbid_l = val_rbid
                        print(','.join(line + [val_rbid_l] ))

                    else:
                        # rbid内、末尾から trim_num 行
                        add_top.append(line)

                        val_rbid_l = val_rbid
                        print(','.join(line + [val_rbid_l] ))

                    if int(val_gbn)+1  - int(max_num) * int(val_rbid) == trim_num:
                        # 前のrbid 末尾へ行追加、当 rbid 先頭へ行追加                            
                        for j in add_top:
                            val_rbid_l = val_rbid
                            print(','.join(j + [val_rbid_l] ))
                        add_top = []

                        for j in add_bot:
                            val_rbid_l = val_rbid
                            print(','.join(j + [val_rbid_l] ))
                        add_bot = []
                    elif val_bot == '1':
                        add_top = []
                        add_bot = []

        except Exception as e:
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)
        finally:
            sys.__stdout__.flush()#not needed for bigger data

class TimeSeriesDataJoinCommand(PCommand):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'mcmd'), Port('m', 'mcmd')]
        self.o_ports = [Port('o', 'mcmd')]
    
    def run(self, args, inputs):
        """
        依存
            MeasurementPeriodIdentifyCommand()  稼働停止判定
            MissingValueInterpolateCommand()    補間値
            ※ unix時間の列が作成されている 
        引数
            join_keys   リスト型
                Ki          要素： 入力 i のキー項目
                km          要素： 入力 m のキー項目
            TIME        記入型：項目名 *必須
            time        記入型：項目名 *必須
            time_type   選択型：datetime, number
            q           真偽型：non-sorted
            mpi         真偽型：稼働・停止判定を行う
            c           選択型：dynamic_ave, fix
            t_dynamic_interval_num  記入型：数値
            t_fixed_time            記入型：数値
            iplist      リスト型
                ip_f        要素：補間の対象項目
                ip_c        要素：補間方法      cubic_spline,linear,previous,next,nearest
                ip_a        要素：補間の結果項目    &表記で項目名に置換
            max_num     記入型：3次スプライン式の計算時に参照する最大の行数
            trim_num    記入型：3次スプライン式の計算時に誤差とする端点からの件数
          ★ non_ip      真偽型：欠損値の補間はせず、補間式の係数項目を追加する ･･･ UI入力なしで True を設定する
          ★ overwrite   真偽型：追加する項目名が存在する場合、エラーとせず、上書きする ･･･ 強制指定
          ★ a           追加する項目名 (固定の項目名) (省略可)
        出力(iへの左結合により、追加項目)
            補間値
                ip_aの展開(複数項目)
        """
        debug = False
        
        flds_tmplist_i = [] # 入力i の一時作成の項目名リスト
        flds_tmplist_m = [] # 入力m の一時作成の項目名リスト
        flds_addlist   = [] # 追加出力する項目名リスト

        unix_time_i = None
        unix_time_m = None
        unix_time_m_next = None
        keys_i = []
        keys_m = []


        # if parent command exists, take that name
        commandname = args.get('parent_command')
        if commandname is None:
            # if parent command does not exist, this is the parent command
            commandname = 'センサ時系列結合'
            args['parent_command'] = commandname

        # --- 処理の流れ ---
        # 入力m ： 補間式の作成  <args へ規定のものをセットする>
        # 入力i ： 時間軸の作成
        # 左結合： mnrjoinで、補間式を結合
        # 補間値： 補間式より値を計算

        # --- Opt整合性チェック ---
        # get all of the flow before this
        prev_flow_i = copy.deepcopy(inputs['i'].content)
        prev_flow_m = copy.deepcopy(inputs['m'].content)
        
        # put this into a tmpfile
        input_file_i = Tmp.create_file()
        input_filename_i = input_file_i.as_posix()
        input_file_m = Tmp.create_file()
        input_filename_m = input_file_m.as_posix()
        
        prev_flow_i <<= nm.m2tee(o = input_filename_i)
        prev_flow_m <<= nm.m2tee(o = input_filename_m)
        
        prev_flow_obj_i = NysolModule()
        prev_flow_obj_i.set_content(prev_flow_i)
        self.do_runs(prev_flow_obj_i) # run savetotmpfile

        prev_flow_obj_m = NysolModule()
        prev_flow_obj_m.set_content(prev_flow_m)
        self.do_runs(prev_flow_obj_m) # run savetotmpfile
        
        # get headers
        # get header for i input
        get_header_i = nm.m2tee(i = input_filename_i)
        
        get_header_module_i = NysolModule()
        get_header_module_i.set_content(get_header_i)
        header_i = self.get_field_names(get_header_module_i)

        # get header for m input
        get_header_m = nm.m2tee(i = input_filename_m)
        
        get_header_module_m = NysolModule()
        get_header_module_m.set_content(get_header_m)
        header_m = self.get_field_names(get_header_module_m)

        fi = nm.m2tee(i = input_filename_i)

               
        fm_mtee = nm.m2tee(i = input_filename_m)
        fm = NysolModule()
        fm.set_content(fm_mtee)


        if debug:
            sys.stderr.write( 'header_i : ' + ','.join(header_i) + '\n' )
            sys.stderr.write( 'header_m : ' + ','.join(header_m) + '\n' )

        iplist    = []      # ワイルドカード展開済補間設定：[ [ el, 'cubic_spline', '&_補間値', [fs1,fs2,...] ], [ ] ]
        ipoutlist = []      # 出力項目名：補間値  [f1,f2,f3,...]  ※ 項目名__method
        ipaddlist = []      # 出力項目名：補間式  [f1,f2,f3,...]

        # 補間式算出： MissingValueInterpolateCommand()
        # Opt設定をパースする make_iplist() 関数で、パース
        cmd = MissingValueInterpolateCommand()
        ipflds = cmd.const('ipflds')
        iplist, ipoutlist, ipaddlist = cmd.make_iplist(
                args_iplist=args['iplist'], ipflds=ipflds, header=header_m,
                parent_command=commandname)

        # 停止判定： MeasurementPeriodIdentifyCommand()
        cmd_mpi = MeasurementPeriodIdentifyCommand()
        aflds = cmd_mpi.const('addflds')

        if debug:
            print(f'iplist: {iplist} \n')


        # --- 引数チェック ---  補間の設定: 辞書のリスト型
        tmp = set(header_m) & set(ipoutlist)
        if len(tmp) > 0:
            # 入力m に、入力m の補間値項目名が、既に存在する場合
            msg = generate_error_message(self.commandname,
                            'InterpolateResultsConflictError',
                            'ip_a', tmp.join(','))
            raise Exception(msg)


        # key項目作成
        keys_m = [ x['Km'] for x in args['join_keys'] ]
        keys_i = [ x['Ki'] for x in args['join_keys'] ]
        
        if keys_m != ['']:
            for key in keys_m:
                if key not in header_m:
                    msg = generate_error_message(commandname,
                                    'FieldNotFoundError',
                                    'Km', key)
                    raise Exception(msg)
            
            if len(keys_m) != len(set(keys_m)):
                msg = generate_error_message(commandname,
                                'TargetFieldConflictError',
                                'Km', '')
                raise Exception(msg)

        if keys_i != ['']:
            for key in keys_i:
                if key not in header_i:
                    msg = generate_error_message(commandname,
                                    'FieldNotFoundError',
                                    'Ki', key)
                    raise Exception(msg)

            if len(keys_i) != len(set(keys_i)):
                msg = generate_error_message(commandname,
                                'TargetFieldConflictError',
                                'Ki', '')
                raise Exception(msg)


        if debug:
            sys.stderr.write( 'keys_i : ' + ','.join(keys_i) + '\n' )
            sys.stderr.write( 'keys_m : ' + ','.join(keys_m) + '\n' )

        # --- 入力m の処理 ---  <区間の補間式を作成する>

        # 補間式算出： MissingValueInterpolateCommand()
        # 参照データm に対して補間式を算出し、mnrjoinで係数を、入力データiへ紐づけて、補間値を計算する
        # 引数
        #   args_m   このコマンドのargsを指定
        #   inputs   参照データm

        # unix時間の項目名取得
        time_m = args.get('time')
        if time_m is None:
            msg = generate_error_message(commandname,
                            'EmptyFieldNameError',
                            'time', '')
            raise Exception(msg)
        else:
            if time_m not in header_m:
                msg = generate_error_message(commandname,
                                'FieldNotFoundError',
                                'time', time_m)
                raise Exception(msg)

        
        time_type = args['time_type']        

        if time_type == 'datetime':
            unix_time_m = time_m + cmd.const('tmpflds')['uxt_sfx'] 
        else:
            unix_time_m = time_m 
        
        unix_time_m_next = unix_time_m + '_next'

        # 補間式計算へ渡す引数の設定
        args_m = {}
        args_m = copy.deepcopy(args)
        args_m['non_ip']    = True
        args_m['overwrite'] = True
        if 'k' in args_m:
            del     args_m['k']        
        if keys_m != ['']:
            args_m['k'] = ','.join(keys_m)     # 補間式算出コマンドのキー項目は k

        # 補間式の計算
        res = cmd.run(args=args_m, inputs={'i':fm})
        fm  = res['o'].content

        # 停止判定時は、k へ、稼働区間ID aflds['ido'] を加える
        # 停止期間は、値を結合させないようにするための設定
        temp_mslide_keys = keys_m
        if 'mpi' in args:
            if temp_mslide_keys == ['']:
                temp_mslide_keys = [aflds['ido']]
            else:
                temp_mslide_keys.append( aflds['ido'] )

        # n=False ： この設定で、外挿を禁止し、内挿だけの区間を生成する
        fm <<= nm.mslide(k= ','.join(temp_mslide_keys),
                         f= f'{unix_time_m}:{unix_time_m_next}',
                         n=False, q=True, l=True)

        # --- 入力i の処理 ---
        # unix時間の項目作成
        time_i = args.get('TIME')
        if time_i is None:
            msg = generate_error_message(commandname,
                            'EmptyFieldNameError',
                            'TIME', '')
            raise Exception(msg)
        else:
            if time_i not in header_i:
                msg = generate_error_message(commandname,
                                'FieldNotFoundError',
                                'TIME', time_i)
                raise Exception(msg)

        if time_type == 'datetime':
            unix_time_i = time_i + cmd.const('tmpflds')['uxt_sfx']
            fld_n_int = '__INT__'
            fld_n_flac = '__FLAC__'

            # 生成する項目が既にあれば、削除する
            # mcutでは、存在しない項目指定はエラーだが、最後にワイルドカード※ で、回避する
            fi <<= nm.mcut(f= f"{unix_time_i}*,{fld_n_int}*,{fld_n_flac}*", r= True)

            # UNIX時間の追加
            fi <<= nm.mcal(a= fld_n_int, c= f'uxt( s2t(regexstr($s{{{time_i}}},"^[0-9]{{14,14}}|^[0-9]{{6,6}}") ) )')
            fi <<= nm.mcal(a= fld_n_flac, c= f'regexstr($s{{{time_i}}},"[.][0-9]{{0,6}}$")')
            fi <<= nm.mcal(a= unix_time_i, c = f'if( isnull($s{{{fld_n_flac}}}), $s{{{fld_n_int}}}, $s{{{fld_n_int}}}+$s{{{fld_n_flac}}} )')
            fi <<= nm.mcut(f= f"{fld_n_int},{fld_n_flac}", r = True)
        else:
            unix_time_i = time_i

        if debug:
            sys.stderr.write( 'k= keys_i : ' + repr(keys_i) + '\n' )
            sys.stderr.write( 'K= keys_m : ' + repr(keys_m) + '\n' )
            sys.stderr.write( 'rf=: ' + unix_time_i + '%n' + '\n' )
            sys.stderr.write( 'R= : ' + unix_time_m + ',' + unix_time_m_next + '\n' )
            sys.stderr.write( 'f= : ' + ','.join(ipaddlist) + '\n' )


        # --- 左結合 ---
        if 'mpi' in args:
            q_opt = True
        else:
            q_opt = False
        
        if debug:
            fm <<= nm.m2tee(o = 'fm_before_mnrjoin.csv')
            fi <<= nm.m2tee(o = 'fi_before_mnrjoin.csv')

        fi <<= nm.mnrjoin(
            m= fm, 
            k= ','.join(keys_i), K= ','.join(keys_m), 
            rf= unix_time_i + '%n',
            R=  unix_time_m + ',' + unix_time_m_next,
            n= True, N= False,
            f= ','.join(ipaddlist),
            q= q_opt
            )

        if not all(key == '' for key in keys_i):
            sortkeys = ','.join(keys_i)+  f',{unix_time_i}%n'
        else:
            sortkeys = unix_time_i + '%n'

        fi <<= nm.msortf(f= sortkeys)

        if debug:
            fi <<= nm.m2tee(o = 'fi_after_mnrjoin.csv')

        # --- 補間値計算 ---
        dm = '_'            # 補間値の出力項目名作成時の区切り文字
        method = None       # 手法
        outname = None      # 出力する補間値の項目名
        # ipval = None        # 補間値

        now_time = unix_time_i  # 補間値を求める時間
        top_time = unix_time_m  # 区間の先頭の時間

        all_outnames = []
        for elem in range(len(iplist)):
            method  = iplist[elem][1]
            outname = iplist[elem][2] # &の置換していない        

            for fld in iplist[elem][3]:
                mcal_c_opt = None
                tmp_name = outname
                tmp_name = tmp_name.replace('&', fld + dm + method)  # 文字列

                all_outnames.append(tmp_name)

                if method == 'previous':
                    ip_0_pre = fld + ipflds['ip_0_pre']
                    mcal_c_opt = f'$s{{{ip_0_pre}}}'
                
                elif method == 'next':
                    # 区間 [,) で、[ の時は、前値、それ以外は 後値
                    ip_0_next_pre = fld + ipflds['ip_0_next_pre']
                    ip_0_next     = fld + ipflds['ip_0_next']
                    mcal_c_opt = f'if(${{{now_time}}}==${{{top_time}}},${{{ip_0_next_pre}}},${{{ip_0_next}}})'

                elif method == 'nearest':
                    # 中点は、前値とする
                    ip_0_near       = fld + ipflds['ip_0_near']
                    ip_0_near_pre   = fld + ipflds['ip_0_near_pre']
                    ip_0_near_next  = fld + ipflds['ip_0_near_next']
                    mcal_c_opt = f'if(${{{now_time}}}>=${{{ip_0_near}}},${{{ip_0_near_pre}}},${{{ip_0_near_next}}})'

                elif method == 'linear':
                    ip_1_1 = fld + ipflds['ip_1_1']     # 傾き
                    ip_1_0 = fld + ipflds['ip_1_0']     # 切片
                    mcal_c_opt = f'${{{now_time}}}*${{{ip_1_1}}}+${{{ip_1_0}}}'

                elif method == 'cubic_spline':                    
                    # now_time に対して、3次式 を計算する
                    ip_3_x = fld + ipflds['ip_3_x']  # 区間開始
                    ip_3_3 = fld + ipflds['ip_3_3']  # 3次係数
                    ip_3_2 = fld + ipflds['ip_3_2']  # 2次係数
                    ip_3_1 = fld + ipflds['ip_3_1']  # 1次係数
                    ip_3_0 = fld + ipflds['ip_3_0']  # 定数項
                    
                    # 係数 * (時間^3)  のように、べき乗を先に計算するように明示する
                    # 計算式： c3*(x-xp)^3 + c2*(x-xp)^2 + c1*(x-xp) + c0
                    #        c 係数   x now_time  xp 区間開始
                    mcal_c_opt = f'${{{ip_3_3}}}*((${{{now_time}}}-${{{ip_3_x}}})^3)+${{{ip_3_2}}}*((${{{now_time}}}-${{{ip_3_x}}})^2)+${{{ip_3_1}}}*(${{{now_time}}}-${{{ip_3_x}}})+${{{ip_3_0}}}'

                if len(all_outnames) != len(set(all_outnames)):
                    msg = generate_error_message(commandname,
                                    'InterpolateResultsConflictError',
                                    'ip_f,ip_c,ip_a', '')
                    raise Exception(msg) 

                fi <<= nm.mcal(
                    a= tmp_name,
                    c= mcal_c_opt,
                    precision= 16
                )


        # --- 不要項目の除外 ---
        remove_flds = ipaddlist
        fi <<= nm.mcut(f= ','.join(ipaddlist), r= True)


        nysol_module_o= NysolModule()
        nysol_module_o.set_content(fi)
        return {'o': nysol_module_o}

class TimeAxisDataGenerateIn0Command(PCommand):
    def __init__(self):
        super().__init__()
        self.i_ports = []
        self.o_ports = [Port('o', 'mcmd')]
    
    def const(self, s):
        res = None
        if s == 'timeformats':
            res = {
                'datetime'    : '暦型(YYYYMMDDhhmmss.小数6桁まで)',
                'date'        : '暦型(YYYYMMDD)',
                'year_month'  : '暦型(YYYMM)'
            }
        elif s == 'bounds':
            res = {
                'interval' : '正の整数'
            }
        return res

    def datetime_nysol2py(self, t, time_type='datetime'):
        """
        文字列tのNysol形式の日付を、Python datetime型へ変換する。
        time_typeの指定に応じて、文字列tの先頭から該当文字列を切り取り、python datetime型へ変換する。
        引数
            t           文字列      Nysol型の日付文字列
            time_type   文字列      datetime: datetime型の処理、date: date型の処理、year_month: yyyymm型の処理
        戻値
            res     datetime   Python datetime型の日時
        """
        import traceback
        import datetime

        res = None

        try:
            l = len(t)

            if time_type == 'datetime':
                if l == 14:
                    res = datetime.datetime.strptime(t, '%Y%m%d%H%M%S')
                elif l == 15:
                    res = datetime.datetime.strptime(t, '%Y%m%d%H%M%S.')
                elif 21 >= l:
                    res = datetime.datetime.strptime(t[0:21], '%Y%m%d%H%M%S.%f')
                elif l < 14:
                    res = None
            elif time_type == 'date':
                if l == 8:
                    res = datetime.datetime.strptime(t[0:8], '%Y%m%d')
                else:
                    res = None
            elif time_type == 'year_month':
                if l == 6:
                    res = datetime.datetime.strptime(t[0:6], '%Y%m')
                else:
                    res = None                
            else:
                res = None

            return res

        except Exception as e:
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)
        finally:
            res = None

    def time_axis_generator_in0(self, args):
        """
        args[]
            time        文字    引数a で指定された、出力する、時間軸の項目名
            time_type   文字    引数time_type で指定された、出力する、時間軸の形式： datetime, date, year_month,number
            span_list   多重リスト  [ [start,interval,num], ... ]
        """
        import traceback
        import datetime
        from dateutil.relativedelta import relativedelta

        try:
            print(args['time'])

            for l in args['span_list']:
                start    = l[0]
                interval = l[1]
                num      = int(l[2])
                
                if args['time_type'] in ['datetime','date','year_month']:
                    start_py = self.datetime_nysol2py(start, time_type=args['time_type'])
                    interval = float(interval)

                for n in range(num):
                    if args['time_type'] == 'number':
                        val = start + (interval * n)
                    else:
                        if args['time_type'] == 'datetime':
                            val = start_py + datetime.timedelta(seconds= interval * n)
                            val = val.strftime('%Y%m%d%H%M%S.%f') 
                        elif args['time_type'] == 'date':
                            val = start_py + datetime.timedelta(days= interval * n)
                            val = val.strftime('%Y%m%d') 
                        elif args['time_type'] == 'year_month':
                            val = start_py + relativedelta(months= interval * n)
                            val = val.strftime('%Y%m') 
                        else:
                            pass

                    print(val)

        except Exception as e:
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)
        finally:
            sys.__stdout__.flush()#not needed for bigger data

    def run(self, args, inputs):
        """
        依存
            なし
        入力
            なし
        引数
            a           必須    記入型：時間軸の項目名
            time_type   必須    選択型：datetime, date, year_month, number
            interval    必須    記入型：間隔（秒 少数6桁まで）
            start               記入型：開始
            num                 記入型：件数
            r                   真偽：開始・間隔・件数でなく、開始・終了・間隔で生成する
            spans               記入型：[開始,終了],[開始,終了]
        出力
            1つの項目、条件を満たす件数
        
        制約・制限
            引数spans で指定された各期間の長さが270年以上で、マイクロ秒の精度を失う ※timedelta.total_seconds()の仕様 
            
        """
        import datetime
        
        debug = False
        if debug:
            import pprint

        bounds = self.const('bounds')
        timeformats = self.const('timeformats')
        in0_args = {}   # time_axis_generator_in0 への引数辞書
        """
        time        文字    引数a で指定された、出力する、時間軸の項目名
        time_type   文字    引数time_type で指定された、出力する、時間軸の形式： datetime, number
        start       数値    開始
        num         数値    開始を1件とした件数   num >= 1
        span_list   多重リスト  [ [start,interval,num], ... ]
        """

        time = None
        time_type = None
        start = None
        interval = None
        num = None
        span_list = []
        commandname = 'センサ時系列生成（0入力）'

        # --- 引数チェック ----
        if 'a' not in args:
            msg = generate_error_message(commandname, 
                                       'EmptyFieldNameError',
                                       'a', '')
            raise Exception(msg)
        elif any(char in args['a'] for char in '*?[],:\\ '):
            msg = generate_error_message(commandname, 
                                    'FieldNameForbiddenCharacterError',
                                    'a', args['a'])
            raise Exception(msg)
        else:
            time = args['a']
        
        time_type = args['time_type']

        if 'interval' not in args:
            msg = generate_error_message(commandname,
                            'EmptyParamError',
                            'interval', '')
            raise Exception(msg)

        else:
            try:
                interval = args['interval'].replace(',','')

                if time_type in ['date','year_month']:
                    interval = round(float(interval))

                if float(interval) <= 0:
                    raise Exception()
            except Exception as e:
                msg = generate_error_message(commandname,
                                'OutOfBoundsError',
                                'interval', args['interval'])
                raise Exception(msg)
            finally:
                if time_type == 'datetime':
                    interval_list = interval.split('.')

                    # if there is a decimal part,
                    # and it is longer than 7 digits, raise TimePrecisionError
                    if len(interval_list) == 2 and len(interval_list[1]) >= 7:
                        msg = generate_error_message(commandname,
                                        'TimePrecisionError',
                                        'interval', args['interval'])
                        raise Exception(msg)
                elif time_type == 'number':
                    interval = Decimal(interval)
            

        # 開始・間隔・件数 指定時
        if 'r' not in args:
            if 'start' not in args:
                msg = generate_error_message(commandname,
                                'EmptyParamError',
                                'start', '')
                raise Exception(msg)
            else:
                start = args['start'].replace(',','')
                if time_type in ['number']:
                    try:
                        start = Decimal(start)
                        
                    except Exception as e:
                        msg = generate_error_message(commandname,
                                        'ParameterTypeError',
                                        'start', args['start'])
                        raise Exception(msg)
                    finally:
                        pass
                elif self.datetime_nysol2py(start,time_type=time_type) is None:
                    msg = generate_error_message(commandname,
                                    'TimeSettingMismatchError',
                                    'start', args['start'],
                                    {'correct_timeformat': timeformats[time_type]})
                    raise Exception(msg)

            if 'num' not in args:
                msg = generate_error_message(commandname,
                                'EmptyParamError',
                                'num', '')
                raise Exception(msg)
            else:
                try:
                    num = round(float(args['num'].replace(',','')))
                except Exception as e:
                    msg = generate_error_message(commandname,
                        'ParameterTypeError',
                        'num', args['num'])
                    raise Exception(msg)
                if num <= 0:
                    msg = generate_error_message(commandname,
                        'OutOfBoundsError',
                        'num', args['num'])
                    raise Exception(msg)

            span_list = []
            span_list.append( [start,interval,num] )
        else:
        # 開始・終了・間隔 指定時 のパース
            if 'spans' not in args:
                msg = generate_error_message(commandname,
                                'EmptyParamError',
                                'spans', '')
                raise Exception(msg)

            # spans : [開始,終了],[開始,終了],...
            # 各要素の先頭、末尾の空白は除去する
            
            import re
            # test for valid spans format
            valid_spans = r'^\[[^,]+?,[^,]+?\](,\[[^,]+?,[^,]+?\])*$'
            if not re.match(valid_spans, args['spans'].strip()):
                msg = generate_error_message(commandname,
                            'SpansFormatError',
                            'spans', args['spans'])
                raise Exception(msg) 
            
            tmp_span_list = None
            tmp_span_list = [ x.strip('[] ') for x in args['spans'].split('],') ]
            tmp_span_list = sorted( [ x.split(',') for x in tmp_span_list ] )

            # 件数計算
            interval_seconds = None     # datetime, date, year_month 用の定数
            if time_type == 'datetime':
                interval_seconds = float(interval)
            elif time_type == 'date':
                interval_seconds = float(interval) * 24 * 60 * 60
            elif time_type == 'year_month':
                interval_seconds = float(interval) * 30 * 24 * 60 * 60

            for k in tmp_span_list:
                # 入力値のチェク

                # 間隔より件数を計算
                #   数値型   範囲、間隔は実数で、件数は切り捨ての正の整数とする
                #   時刻型   
                #   
                if time_type == 'number':
                    num = 1.0 + (float(k[1]) - float(k[0])) // float(interval)   # 開始の1件 + 切捨ての件数

                    span_list.append( [Decimal(k[0]),interval,num] )
                elif time_type in ['datetime','date','year_month']:
                    dt = []

                    for ke in k:
                        res = self.datetime_nysol2py(ke, time_type=time_type)
                        if res is None:
                            msg = generate_error_message(commandname,
                                            'TimeSettingMismatchError',
                                            'spans', ke,
                                            {'correct_timeformat': timeformats[time_type]})
                            raise Exception(msg)
                        else:
                            dt.append(res)
                    # 制限： timedelta.total_seconds()  270年以上で、マイクロ秒の精度を失う
                    num = 1.0 + (dt[1] - dt[0]).total_seconds() // float(interval_seconds)

                    span_list.append( [k[0],interval,num] )

        if debug:
            pprint.pprint(span_list, stream=sys.stderr)


        f = None

        in0_args['time']        = time
        in0_args['time_type']   = time_type
        in0_args['span_list']   = span_list


        f <<= nm.runfunc(self.time_axis_generator_in0, args=in0_args)

        nysol_module_o= NysolModule()
        nysol_module_o.set_content(f)
        return {'o': nysol_module_o}

class TimeAxisDataGenerateIn1Command(PCommand):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'mcmd')]
        self.o_ports = [Port('o', 'mcmd')]
    
    def time_axis_generator_in1(self, args):
        """
        引数
            time
            time_type
            interval
            k
        """
        import traceback
        import datetime
        from dateutil.relativedelta import relativedelta

        try:
            time = args['time']
            time_type = args['time_type']
            interval = args['interval']
            k = args['k']
            
            k_num = 0
            if k is not None:
                header = [k,time]
                k_num  = len( k.split(",") )
            else:
                header = [time]

            interval_seconds = None     # datetime, date, year_month 用の定数
            if time_type == 'datetime':
                interval_seconds = float(interval)
            elif time_type == 'date':
                interval_seconds = float(interval) * 24 * 60 * 60
            elif time_type == 'year_month':
                interval_seconds = float(interval) * 30 * 24 * 60 * 60

            headerflg = True
            for line in nm.mstdin().getline(header= True):
                if headerflg:
                    print( ','.join(header) )
                    headerflg = False
                else:
                    cmd = TimeAxisDataGenerateIn0Command()
                    dt = []
                    num = 0

                    k_val  = line[:k_num]     # list型  グループ項目の値
                    time_s = line[k_num]      # 数値型   そのグループの開始時刻
                    time_e = line[k_num+1]    # 数値型   そのグループの終了時刻

                    if time_type == 'number':
                        num = 1.0 + (float(time_e) - float(time_s)) // float(interval)   # 開始の1件 + 切捨ての件数                        
                    elif time_type in ['datetime','date','year_month']:
                        dt = []
                        for ke in [time_s,time_e]:
                            res = cmd.datetime_nysol2py(ke, time_type=time_type)
                            if res is None:
                                pass
                            else:
                                dt.append(res)
                        
                        # 制限： timedelta.total_seconds()  270年以上で、マイクロ秒の精度を失う
                        num = 1.0 + (dt[1] - dt[0]).total_seconds() // float(interval_seconds)

                    # interval間隔の時系列出力
                    val = None
                    num = int(num)
                    for n in range(num):
                        if time_type == 'number':
                            val = str( Decimal(time_s) + interval * n )
                        elif time_type == 'datetime':
                            val = dt[0] + datetime.timedelta(seconds= interval * n)
                            val = val.strftime('%Y%m%d%H%M%S.%f') 
                        elif time_type == 'date':
                            val = dt[0] + datetime.timedelta(days= interval * n)
                            val = val.strftime('%Y%m%d') 
                        elif time_type == 'year_month':
                            val = dt[0] + relativedelta(months= interval * n)
                            val = val.strftime('%Y%m') 
                        else:
                            pass
                        print_list = None
                        if k is not None:
                            print_list = k_val[:]   # deepcopy
                            print_list.append(val)
                        else:
                            print_list = [val]

                        if print_list != []:
                            print(','.join(print_list))

        except Exception as e:
            with open('/dev/stderr', 'w') as fpe:
                traceback.print_exc(file=fpe)
        finally:
            sys.__stdout__.flush()#not needed for bigger data


    def run(self, args, inputs):
        """
        依存
            MeasurementPeriodIdentifyCommand()    停止判定
        入力
            
        引数
            interval    必須    記入型：間隔（単位： 小数6桁までの秒、日、月、数値）
            k                   記入型：グループ化の項目名
            time        必須    記入型：時間軸の項目名
            time_type   必須    選択型：datetime, date, year_month, number
            q                   真偽型：自動並び替えの無効化                   
            mpi                 真偽型：稼働・停止判定を行う
            c                   選択型：dynamic_ave, fix
            t_dynamic_interval_num  記入型：数値
            t_fixed_time            記入型：数値
        出力
            1つの項目、条件を満たす件数
        """
        debug = False
        if debug:
            import pprint

        time = None
        time_type = None
        interval = None

        k = None
        q = None
        mpi = None
        c = None
        t_dynamic_interval_num = None
        t_fixed_time = None

        # get header
        f = None
        header = args.get('header')
        if header is None:
            # get all of the flow before this
            prev_flow = copy.deepcopy(inputs['i'].content)
            
            # put this into a tmpfile
            input_file = Tmp.create_file()
            input_filename = input_file.as_posix()
            
            prev_flow <<= nm.m2tee(o = input_filename)
            
            prev_flow_obj = NysolModule()
            prev_flow_obj.set_content(prev_flow)
            self.do_runs(prev_flow_obj) # run savetotmpfile
            
            # get header
            get_header = nm.m2tee(i = input_filename)
            
            get_header_module = NysolModule()
            get_header_module.set_content(get_header)
            header = self.get_field_names(get_header_module)

            f <<= nm.m2tee(i = input_filename)
        else:
            # if header is passed just read from input
            f <<= copy.deepcopy(inputs['i'].content)
            
            
        # --- 引数チェック ---         
        # if parent command exists, take that name
        commandname = args.get('parent_command')
        if commandname is None:
            # if parent command does not exist, this is the parent command
            commandname = 'センサ時系列生成（1入力）'
            args['parent_command'] = commandname

        # 必須の引数
        if 'time' not in args:
            msg = generate_error_message(commandname,
                            'EmptyFieldNameError',
                            'time', '')
            raise Exception(msg)
        else:
            time = args.get('time')
            if time not in header:
                msg = generate_error_message(commandname,
                                'FieldNotFoundError',
                                'time', time)
                raise Exception(msg)
        
        if 'time_type' not in args:
            msg = generate_error_message(commandname,
                            'EmptyParamError',
                            'time_type', '')
            raise Exception(msg)
        else:
            time_type = args['time_type']

        if 'interval' not in args:
            msg = generate_error_message(commandname,
                            'EmptyParamError',
                            'interval', '')
            raise Exception(msg)
        else:
            interval = args['interval']
            try:
                interval = args['interval'].replace(',','')

                if time_type in ['date','year_month']:
                    interval = round(float(interval))
                elif time_type == 'number':
                    interval = Decimal(interval)
                elif time_type == 'datetime':
                    interval = float(interval)


                if interval <= 0:
                    raise Exception()
            except Exception as e:
                msg = generate_error_message(commandname,
                                'OutOfBoundsError',
                                'interval', args['interval'])
                raise Exception(msg)

        # 省略可の引数
        k = args.get('k')
        if k is not None:
            k_list = k.split(',')
            for key in k_list:
                if key not in header: 
                    msg = generate_error_message(commandname,
                                    'FieldNotFoundError',
                                    'k', key)
                    raise Exception(msg)

            if len(k_list) != len(set(k_list)):
                msg = generate_error_message(commandname,
                                'TargetFieldConflictError',
                                'k', k)
                raise Exception(msg)

        if 'q' in args:
            q = True
        else:
            q = False

        if 'mpi' in args:
            mpi = True
        else:
            mpi = False
                
        if 'c' in args:
            c = args['c']

        # =======================
        # --- 入力i の処理 ---
        # =======================
        """
        Step1: グループ別に、時系列単位で、稼働停止判定
        Step2: グループ別に、区間単位のデータ作成
               抽出条件  稼働開始フラグ=1 or 稼働終了フラグ=1  → 1区間で、2行のデータ
               mslideで、2行の情報を1行に集約し、1行のみを抽出する  ※稼働開始フラグ=1
        Step3: グループ別に、区間単位と指定間隔で、一定間隔の、時系列単位のデータ作成
        """

        t_end_suffix = f'{time}_2'      

        if k is not None:
            f <<= nm.mcut(f= f"{k},{time}")
            if not q:
                f <<= nm.msortf(f= f"{k},{time}%n")
        else:
            f <<= nm.mcut(f= f"{time}")
            if not q:
                f <<= nm.msortf(f= f"{time}%n")

        if mpi:
            # Step1: グループ別に、時系列単位で、稼働停止判定
            cmd = MeasurementPeriodIdentifyCommand()

            # NOTE command must be wrapped in NysolModule object before sent to
            # another command
            nysol_module_o = NysolModule()
            nysol_module_o.set_content(f)

            res = cmd.run(args=args,inputs={'i': nysol_module_o}) 
            f   = res['o'].content
            
            addflds = cmd.const('addflds')
            # 固定のキー  MeasurementPeriodIdentifyCommand.const('addflds')で定義
            #   'start' : '区間開始'   , 'end' : '区間終了',
            #   'interval' : '間隔', 
            #   'fos' : '稼働開始フラグ', 'foe' : '稼働終了フラグ' ,
            #   'fss' : '停止開始フラグ', 'fse' : '停止終了フラグ' ,
            #   'ido' : '稼働区間ID'   , 'ids' : '停止区間ID'    
            f <<= nm.mselstr(f= f"{addflds['fos']},{addflds['foe']}", v= "1")

            # Step2: グループ別に、区間単位のデータ作成
            if k is not None:
                f <<= nm.mslide(f= f"{time}:{t_end_suffix}", q= True, k= f"{k}")
                f <<= nm.mselstr(f= f"{addflds['fos']}", v= "1")
                f <<= nm.mcut(f= f"{k},{time},{t_end_suffix}")
            else:
                f <<= nm.mslide(f= f"{time}:{t_end_suffix}", q= True)
                f <<= nm.mselstr(f= f"{addflds['fos']}", v= "1")
                f <<= nm.mcut(f= f"{time},{t_end_suffix}")

        else:
            # 稼働停止判定をしない場合、Step1 をスキップ
            # Step2: グループ別に、区間単位のデータ作成
            # グループ別の先頭と末行 2行ごと抽出し、2行の情報を1行に集約する
            if k is not None:
                f <<= nm.mkeybreak(k= k, a= "top,bot", q= True)
                f <<= nm.mselstr(f= f"top,bot", v= "1")
                f <<= nm.mslide(f= f"{time}:{t_end_suffix}", q= True, k= f"{k}")
                f <<= nm.mselstr(f= "top", v= "1")
                f <<= nm.mcut(f= f"{k},{time},{t_end_suffix}")
            else:
                f <<= nm.msel(c= "or(top(),bottom())")
                f <<= nm.mslide(f= f"{time}:{t_end_suffix}", q= True)
                f <<= nm.mcut(f= f"{time},{t_end_suffix}")

        # Step3: グループ別に、区間単位と指定間隔で、一定間隔の、時系列単位のデータ作成
        set_args = {}
        set_args['time'] = time
        set_args['time_type'] = time_type
        set_args['interval'] = interval
        set_args['k'] = k

        f <<= nm.runfunc(self.time_axis_generator_in1, args=set_args )

        nysol_module_o= NysolModule()
        nysol_module_o.set_content(f)
        return {'o': nysol_module_o}
