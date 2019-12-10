import os
import errno
import sys
import traceback

def mod(FIFO, args):
    header = True
    count = 0
    row_count = args['f'] if args.get('f') else 0
    try:
        with open(FIFO, "w") as fifo:
            for line in sys.stdin:
                datum = line.split(',')
                datum_str = ','.join(datum)

                # header
                if header:
                    header = False
                    # headerは標準入力、名前付きパイプ両方に出力する
                    print(datum_str, end='')
                    fifo.write(datum_str)
                    continue

                if count < args.get('f'):
                    print(datum_str, end='')
                else:
                    fifo.write(datum_str)

                count = count + 1

    except Exception as e:
        with open('/dev/stderr', 'w') as fpe:
          traceback.print_exc(file=fpe)
