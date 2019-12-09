#!/bin/bash -eu
readonly  PROGNAME=$(basename $0 .sh)   # フォルダ名、拡張子を除いたファイル名
readonly  VERSION="0.1"

#外部モジュール参照
#   MCMD使用
#   groupby   ･･･ コマンドへのパスは cmd_path= で指定可能

#version履歴

#未実装箇所
#   □ 行番号指定
#   □ 空白を含む列名

#--------------------------------------------------------------
# columns_to_rows
#--------------------------------------------------------------

function usage() {
    echo "${PROGNAME} ： 列項目を行展開してgroupby処理する"
    echo "==========="
    echo " 複数の列項目を、指定した新規列名で、行データへ展開し、"
    echo " 複数の統計量を適用した結果を、新規列名と統計量からなる列名として出力する。"
    echo
    echo " この一連の処理を複数回連続したい場合、f= にバックスラッシュ区切りで指定する。"
    echo " 連続処理を指定する場合、列項目の数は、全ての反復で同じでなければいけない。"
    echo
    echo " f= 新規追加列名:カンマ区切りの複数項目名リスト\..."
    echo "    例 f=A1:x1,x2\A2:y1,y2\A3:z1,z2"
    echo "       x1とx2列よりA1列を作成し、y1とy2列よりA2列を作成し、z1とz2列よりA3列を作成する"
    echo
    echo " k= 集計のキー項目がある場合、項目名をカンマ区切りで指定する"
    echo "    例 k=k1,k2"
    echo " c= 適用する統計量と、対象項目名へ付加する接辞語を指定する"
    echo "    例 c=mean:Ave,count:Num,sum:Sum"
    echo
    echo "  delimiter=    項目名と接辞語との区切り文字を指定する"
    echo "                デフォルトは _"
    echo "  -prefix       接辞語を、項目名の末尾ではなく、先頭に付加する"
    echo
    echo " cmd_path= 外部参照コマンドのパス"
    echo
    echo " i= 入力ファイル名を指定する。省略時は、標準入力を処理する"
    echo " o= 出力ファイル名を指定する。省略時は、標準出力へ書き込む"
    echo
    echo "書式"
    echo "------"
    echo "${PROGNAME} f= c= [k=] [cmd_path=] [i=] [o=]"
    echo " [delimiter= ] [-prefix] [--help] [--version]"
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
list_of_lists=""  # f=
stats_list=""     # c=
keys_list=""      # k=
cmd_path="./kskp/engine/commands/pcmd"     # cmd_path=
prefix=0          # -prefix
delimiter=""      # delimiter=

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
            list_of_lists=${p_value}
            shift 1
            ;;
        'c='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            stats_list=${p_value}
            shift 1
            ;;
        'k='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            keys_list=${p_value}
            shift 1
            ;;
        'delimiter='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            delimiter=${p_value}
            shift 1
            ;;
        'cmd_path='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            cmd_path=${p_value}
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
        '-prefix' )
            prefix=1
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
if [[ -z ${list_of_lists} ]]; then   # f=
    echo "$PROGNAME: specify f= argument" 1>&2
    echo "Try '$PROGNAME --help' for more information." 1>&2
    exit 1
fi
if [[ -z ${stats_list} ]]; then   # a=
    echo "$PROGNAME: specify c= argument" 1>&2
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
# f= opt のパース
#----------------------
readonly D_CHAR='\'   # リストの区切り記号

# -- 入力のパース
# N         リストの数。入力の単位
# array_f   N個の、項目名のカンマ区切り文字列を格納
# array_a   N個の、出力する列名を格納する
# array_n   N個の、各リストの列数を格納する
# -- 出力の生成
# M             リストの数。出力の単位で、列数の 種類の数に相当
# array_gr      M個の、列数を格納。 列数は、ユニークである必要あり
# array_gr_list M個の、対応する array_f の要素番号 のカンマ区切りリストを格納
# n             1種類の 列数を格納

N=0   # 入力のリストの数
declare -a array_f=()
declare -a array_a=()
declare -a array_n=()
declare -a array_tmp=()
M=0
declare -a array_gr=()
declare -a array_gr_list=()
n=0

IFS=${D_CHAR} # D_CHAR 区切り処理
  array_f=( ${list_of_lists} ) # 変数は""で囲わない
  N=${#array_f[*]}           # 要素数のカウント
IFS="${DEF_IFS}"

# f= から 出力する列名、列名リスト をパース
for i in ${!array_f[@]}; do
  array_a[$i]=${array_f[$i]%%:*}   # コロン 以降 を最長マッチで削除
  array_f[$i]=${array_f[$i]#*:}    # コロン 前   を最短マッチで削除
  if [[ -z ${array_a[$i]} ]]; then   # f=
      echo "$PROGNAME: specify f= argument" 1>&2
      echo "Try '$PROGNAME --help' for more information." 1>&2
      exit 1
  fi
  if [[ -z ${array_f[$i]} ]]; then   # f=
      echo "$PROGNAME: specify f= argument" 1>&2
      echo "Try '$PROGNAME --help' for more information." 1>&2
      exit 1
  fi

  IFS=, # カンマ区切り処理
  array_tmp=( ${array_f[$i]} )
  IFS="${DEF_IFS}"
  array_n[$i]=${#array_tmp[*]}  # 各リストの列数の格納

  # array_gr、array_gr_list への格納
  new_flg=1
  for j in ${!array_gr[@]}; do
    if [[ ${array_gr[$j]} -eq ${array_n[$i]} ]]; then
        new_flg=0
        if [[ -n ${array_gr_list[$j]} ]]; then
          array_gr_list[$j]="${array_gr_list[$j]},$i"
        else
          array_gr_list[$j]=$i
        fi
    fi
  done  # end of for jj
  if [[ $new_flg -eq 1 ]]; then
    array_gr+=( ${array_n[$i]} )  # 新しい種類の登録
    array_gr_list+=( $i )
  fi
done  # end of for i

# 引数チェック
M=${#array_gr[*]}   # カウント
if [[ $M -ne 1 ]]; then
  echo "$PROGNAME: specify f= argument" 1>&2
  echo "全ての列指定の組で、各列の数が同じはでありません" 1>&2
  echo "Try '$PROGNAME --help' for more information." 1>&2
  exit 1
fi
n=${array_gr[0]}    # 1種類の列数

# #-- test
# echo "Test"
# echo "f= ${list_of_lists}"
# echo "N= ${N}"
# for i in ${!array_f[@]}; do
#   echo "${i} a= ${array_a[$i]}"
#   echo "${i} f= ${array_f[$i]}"
#   echo "${i} n= ${array_n[$i]}"
# done
#
# echo "-- output --"
# for i in ${!array_gr[@]}; do
#   echo "${i} gr= ${array_gr[$i]}"
#   echo "${i} gr_list= ${array_gr_list[$i]}"
# done

#----------------------
# スクリプトの準備
#----------------------
# 定数
readonly NO_NAME="#_NO_#"

# 分析に使用する列名リスト
columns_list_all="${keys_list}"
for i in ${array_gr_list[0]//,/ }; do
  if [[ -n ${columns_list_all} ]]; then
    columns_list_all=${columns_list_all}","${array_f[$i]}
  else
    columns_list_all=${array_f[$i]}
  fi
done

# groupbyに使用する列名リスト
columns_list_groupby="${keys_list}"
for i in ${array_gr_list[0]//,/ }; do
  if [[ -n ${columns_list_groupby} ]]; then
    columns_list_groupby=${columns_list_groupby}","${array_a[$i]}
  else
    columns_list_groupby=${array_a[$i]}
  fi
done

# 新規追加する列名のカンマ区切りリスト
columns_list_add="$(IFS=,; echo "${array_a[*]}")" # カンマ区切りリスト

# ソート文
script_sort=""
if [[ -n keys_list ]]; then
  script_sort="msortf f=${keys_list} |"
fi

# mcal 複数回
script_mcal=""
mcal_a=""
macl_c=""
for j in ${array_gr_list[0]//,/ }; do
  mcal_a="${array_a[$j]}"

  mcal_c=""
  top=1

  IFS=, # カンマ区切り処理
  array_tmp=( ${array_f[$j]} )
  IFS="${DEF_IFS}"

  for i in $(seq 0 $(($n-1)) ); do
    if [[ $top -eq 1 ]]; then
      top=0
    else
      mcal_c="${mcal_c},"
    fi
    mcal_c="${mcal_c}"'if(${'${NO_NAME}'} % '$n'=='$i',${'"${array_tmp[$i]}"'}'  # if文の 真 の場合の処理
  done
  mcal_c="${mcal_c},nulln()"      # 入れ子のif文の最後の else節
  for i in $(seq 1 $n); do  # if文の 終了 ")" をn個追加
    mcal_c="${mcal_c})"
  done

  # mcmd実行文
  if [[ -z ${script_mcal} ]]; then
    script_mcal="mcal a=${mcal_a} c=""'"${mcal_c}"'"
  else
    script_mcal="${script_mcal} | mcal a=${mcal_a} c=""'"${mcal_c}"'"
  fi
done  # end of for j
script_mcal="${script_mcal} | "

# groupby opt指定
groupby_opt=""
if [[ -n ${keys_list} ]]; then
  groupby_opt="k=${keys_list}"
fi
if [[ -n ${delimiter} ]]; then
  groupby_opt="${groupby_opt} delimiter=${delimiter}"
fi
if [[ prefix -eq 1 ]]; then
  groupby_opt="${groupby_opt} -prefix"
fi

echo "groupby_opt=${groupby_opt}"

echo "debug: ${cmd_path}"
echo "debug: ${columns_list_add}"
echo "debug: ${stats_list}"
echo "debug: ${output_file}"
echo "debug: ${groupby_opt}"

#----------------------
# スクリプトの生成
#----------------------
mcut  i="${input_file}" \
      f="${columns_list_all}" | \
eval  ${script_sort} \
mduprec n="${n}" | \
mnumber a="${NO_NAME}" S=0 -q | \
eval  ${script_mcal} \
mcut  f="${columns_list_groupby}" | \
bash  "${cmd_path}/groupby.sh" \
      f="${columns_list_add}" \
      c="${stats_list}" \
      o="${output_file}"  ${groupby_opt}

exit 0
