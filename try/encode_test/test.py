import nysol.mcmd as nm
import sys
import traceback
import io

def Cp932_to_utf8():
    """
    ストリームでcp932→utf8に変換するコマンド
    """
    try:
        # stdinのencodingがデフォルトでutf-8なので、設定し直す。
        input_stream = io.TextIOWrapper(sys.stdin.buffer, encoding='cp932')
        for line in input_stream:
            # 標準出力するときも自動でutf-8に変換されるので、printだけでいい
            print(line, end='')
    except Exception as e:
        with open('/dev/stderr', 'w') as fpe:
            traceback.print_exc(file=fpe)

def utf8_to_Cp932():
    """
    ストリームでutf-8→cp932に変換するコマンド
    """
    try:
        sys.stdout = open(sys.stdout.fileno(), 'w', encoding='cp932', closefd=False)
        for line in sys.stdin:
            # 改行コードは変えてくれなさそうなのでここで変える
            print(line.strip() + '\r\n', end='')
    except Exception as e:
        with open('/dev/stderr', 'w') as fpe:
            traceback.print_exc(file=fpe)

f = None
f <<= nm.m2tee(i='テスト.csv')
f <<= nm.runfunc(utf8_to_Cp932)
f <<= nm.mcut(f=0,x=True)
f <<= nm.m2tee(o='result.csv')
f.run()
