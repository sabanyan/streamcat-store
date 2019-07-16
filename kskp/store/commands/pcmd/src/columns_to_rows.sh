#!/bin/bash -eu
readonly  PROGNAME=$(basename $0 .sh)   # フォルダ名、拡張子を除いたファイル名
readonly  VERSION="1.0"

#外部モジュール参照
# MCMD使用

#version履歴
# 1.0   2019.02.06  初版作成 （空白含む列名対応済）

#未実装箇所
# 未対応：行番号指定

#--------------------------------------------------------------
# columns_to_rows
#--------------------------------------------------------------

function usage() {
    echo "${PROGNAME} ： 列項目の行展開"
    echo "==========="
    echo " f=で指定した複数の列項目に対して、"
    echo " 各項目の行を連結した新たな項目を、"
    echo " a=で指定した名前で作成する"
    echo
    echo " f= 複数の列項目を、カンマ区切りで指定する"
    echo " a= 1つの新規項目名を指定する"
    echo " k= 入力項目よりf=指定以外の項目を出力に含めたい場合に、"
    echo "    カンマ区切りで指定する"
    echo
    echo " 例 f=A,B  a=ADD"
    echo "    ADD列に、A列、B列の値を連結した（行数が2倍に増加）データを生成"
    echo
    echo " i= 入力ファイル名を指定する。省略時は、標準入力を処理する"
    echo " o= 出力ファイル名を指定する。省略時は、標準出力へ書き込む"
    echo
    echo "書式"
    echo "------"
    echo "${PROGNAME} f= a= [k=] [i=] [o=] [--help] [--version]"
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

# 初期設定の記録
readonly DEF_IFS=${IFS}   # bash 環境変数の記録

# 引数格納用変数
columns_list_f="" # f=
column_add=""     # a=
columns_list_k="" # k=

input_file=""   # i=
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
        'f='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            columns_list_f=${p_value}
            shift 1
            ;;
        'a='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            column_add=${p_value}
            shift 1
            ;;
        'k='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            columns_list_k=${p_value}
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
        'o='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            output_file=${p_value}
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

#必須パラメータ指定無し
if [[ -z ${columns_list_f} ]]; then   # f=
    echo "$PROGNAME: specify f= argument" 1>&2
    echo "Try '$PROGNAME --help' for more information." 1>&2
    exit 1
fi
if [[ -z ${column_add} ]]; then   # a=
    echo "$PROGNAME: specify a= argument" 1>&2
    echo "Try '$PROGNAME --help' for more information." 1>&2
    exit 1
fi

# 準備処理
# p= and f= 指定が無い場合、標準入力をセットする
if [[ -z "${input_file}" ]]; then
  input_file='/dev/stdin'
fi

# o= 指定が無い場合、標準出力をセットする
if [[ -z "${output_file}" ]]; then
  output_file='/dev/stdout'
fi

#----------------------
# 列名指定 opt のパース
#----------------------
# nysolコマンドの列名指定用のリスト  空白含む列名、％指定 へ対応する
nysol_list_f=""
nysol_list_k=""
nysol_list_fk=""  # f= k= のカンマ区切り連結
nysol_list_ka=""  # k= a=  〃

IFS=, # 以降 カンマ区切りに変更
  declare -a array_f=(${columns_list_f}) # 変数は""で囲わない
  declare -a array_k=(${columns_list_k}) # 変数は""で囲わない
IFS="${DEF_IFS}"

n=""
if [[ -n "${columns_list_f}" ]]; then
  # 配列に格納した変数名を "" で囲む  ※空白含む列名対策
  for i in ${!array_f[@]}; do
    array_f[$i]="${array_f[$i]}"
  done

  n=${#array_f[*]}              # 要素数のカウント
  nysol_list_f="$(IFS=,; echo "${array_f[*]}")" # カンマ区切りリスト
  nysol_list_fk="${nysol_list_f}"
fi

if [[ -n "${columns_list_k}" ]]; then
  for i in ${!array_k[@]}; do
    array_k[$i]="${array_k[$i]}"
  done

  nysol_list_k="$(IFS=,; echo "${array_k[*]}")" # カンマ区切りリスト
  nysol_list_fk="${nysol_list_fk},${nysol_list_k}"
  nysol_list_ka="${nysol_list_k}"
fi

if [[ -n "${column_add}" ]]; then
  if [[ -n "${columns_list_k}" ]]; then
    nysol_list_ka="${nysol_list_ka},${column_add}"
  else
    nysol_list_ka="${column_add}"
  fi
fi

# 定数
readonly NO_NAME="#_#_NO_#_#"

#----------------------
# mcal 演算式生成
#----------------------
# i=0 i<=$n
# if(${ $NO_NAME } % $n == $i, $!array_f[i], <<if>> ,null()  < )をn個 >
#'if(${'${NO_NAME}'} % '${n}'==0,${D1}, if(${'${NO_NAME}'} % '${n}'==1,${D2}, if(${'${NO_NAME}'} % '${n}'==2,${D3},nulln() )))'
exp=""
top=1
for i in $(seq 0 $(($n-1)) ); do
  if [[ $top -eq 1 ]]; then
    top=0
  else
    exp="${exp},"
  fi
  exp="${exp}"'if(${'${NO_NAME}'} % '$n'=='$i',${'"${array_f[$i]}"'}'  # if文の 真 の場合の処理
done
exp="${exp},nulln()"      # 入れ子のif文の最後の else節
for i in $(seq 1 $n); do  # if文の 終了 ")" をn個追加
  exp="${exp})"
done

# データ処理
mcut    f="${nysol_list_fk}" \
        i="${input_file}" |
mduprec n=${n} |
mnumber a="${NO_NAME}" S=0 -q |
mcal    c="${exp}" \
        a="${column_add}" |
mcut    f="${nysol_list_ka}" \
        o="${output_file}"

exit 0
