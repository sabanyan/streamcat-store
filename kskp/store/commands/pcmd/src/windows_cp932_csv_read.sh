#!/bin/bash -eu
readonly  PROGNAME=$(basename $0 .sh)   # フォルダ名、拡張子を除いたファイル名
readonly  VERSION="0.1"

# == 注意 ==
# i= オプションについて
# 指定を受け付けるが、内部処理は 一切行わない
# 背景： KSKP UI側の挙動に合わせるため

#外部モジュール参照
# MCMD使用

#未実装箇所

#--------------------------------------------------------------
# windows_cp932_csv_read
#--------------------------------------------------------------
# 日本語Windowsファイル（CP932）を、サーバ上のローカルファイルより読込む

function usage() {
    echo "${PROGNAME} ： Windowsファイル読込(Shift-JIS拡張)"
    echo "==========="
    echo " Windowsファイル（Shift-JIS拡張 CP932）を、サーバ上のローカルファイルより読込む。"
    echo " p= f= でローカルファイルを指定しなかった場合は、標準入力より読み込む"
    echo
    echo " p= 入力ファイル名のサーバのローカルパス名を指定する"
    echo " f= 入力ファイル名を指定する。"

    echo " i= 入力ファイル名を指定する。p=とf=が指定されていない時に使われる。省略時は、標準入力を処理する"
    echo " o= 出力ファイル名を指定する。省略時は、標準出力へ書き込む"
    echo
    echo "書式"
    echo "------"
    echo "${PROGNAME} [p=] [f=] [i=] [o=] [--help] [--version]"
    echo

    exit 1
}

# エラー処理
set -e -u -o pipefail   # パイプ処理中にエラー発生で処理を終了する設定
error(){
  echo "#ERROR# Stoped ${PROGNAME}"
  echo "[ ${BASH_SOURCE} : ${LINENO} ] returns not zero status"
  exit 1
}
trap error ERR

# 引数格納用変数
path_name=""    # p=
file_name=""    # f=
input_file=""
output_file=""  # o=

# 参考 引数処理： https://qiita.com/b4b4r07/items/dcd6be0bb9c9185475bb
for OPT in "$@"
do
#  echo $OPT
    case "$OPT" in
        '-h'|'--help' )
            usage
            exit 1
            ;;
        '--version' )
            echo ${VERSION}
            exit 1
            ;;
        'p='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            path_name=${p_value}
            shift 1
            ;;
        'f='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            file_name=${p_value}
            shift 1
            ;;
        'o='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            output_file=${p_value}
            shift 1
            ;;
        'i='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            input_file=${p_value}
            shift 1
            ;;
        '--'|'-' )
            shift 1
            break
            ;;
        -*)
            echo "$PROGNAME: illegal option -- '$(echo $1 | sed 's/^-*//')'" 1>&2
            exit 1
            ;;
        *)
            if [[ ! -z "$1" ]] && [[ ! "$1" =~ ^-+ ]]; then
               shift 1
            fi
            ;;
    esac
done

# 必須パラメータ指定無し
# if [[ -z ${} ]]; then
#     echo "$PROGNAME: specify k= argument" 1>&2
#     echo "Try '$PROGNAME --help' for more information." 1>&2
#     exit 1
# fi

# 準備処理
# p= and f= 指定が無い場合、標準入力をセットする
if [[ -z ${path_name} && -z ${file_name} ]]; then
  # 準備処理
  # i= 指定が無い場合、標準入力をセットする
  if [[ -z "${input_file}" ]]; then
    input_file='/dev/stdin'
  fi
else
  input_file="${path_name}/${file_name}"
fi

# o= 指定が無い場合、標準出力をセットする
if [[ -z ${output_file} ]]; then
  output_file='/dev/stdout'
fi

# データ処理
#   -w   utf-8
#   -Lu  LF
nkf -w -Lu "${input_file}" > "${output_file}"

exit 0
